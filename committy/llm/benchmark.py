"""Benchmark module for evaluating prompt performance.

This module provides utilities for testing and evaluating the performance of
different prompt templates on real-world git diffs.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple

from committy.git.parser import parse_diff
from committy.llm.index import build_prompt_from_diff
from committy.llm.ollama import OllamaClient, get_default_model_config
from committy.llm.prompts import (
    get_prompt_for_diff,
    detect_likely_change_type,
    enhance_commit_message
)

# Configure logger
logger = logging.getLogger(__name__)


class PromptBenchmark:
    """Benchmark for evaluating prompt performance."""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """Initialize the benchmark.
        
        Args:
            model_config: Model configuration dictionary. If None, uses default.
        """
        self.model_config = model_config or get_default_model_config()
        self.ollama_client = OllamaClient()
        logger.info(f"Initialized benchmark with model: {self.model_config['model']}")
    
    def evaluate_diff(self, diff_text: str, expected_message: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a single diff and generate a commit message.
        
        Args:
            diff_text: Git diff text to evaluate
            expected_message: Optional expected commit message for comparison
            
        Returns:
            Dictionary with evaluation results
        """
        # Parse the diff
        git_diff = parse_diff(diff_text)
        diff_data = git_diff.as_dict()
        
        # Build the context using LlamaIndex
        context = self._build_context(diff_data)
        
        # Detect likely change type
        change_type = detect_likely_change_type(context)
        
        # Get prompts for different templates
        results = {}
        
        # Test the enhanced template
        enhanced_prompt = get_prompt_for_diff(context)
        enhanced_message = self._generate_message(enhanced_prompt)
        enhanced_message = enhance_commit_message(enhanced_message)
        results["enhanced"] = {
            "prompt": enhanced_prompt,
            "message": enhanced_message
        }
        
        # If we detected a change type, also test the specialized template
        if change_type:
            specialized_prompt = get_prompt_for_diff(context, change_type)
            specialized_message = self._generate_message(specialized_prompt)
            specialized_message = enhance_commit_message(specialized_message)
            results["specialized"] = {
                "prompt": specialized_prompt,
                "message": specialized_message,
                "change_type": change_type
            }
        
        # Compare with expected message if provided
        if expected_message:
            results["expected"] = expected_message
            
            # Calculate similarity scores
            for template_type in results:
                if template_type != "expected":
                    results[template_type]["similarity"] = self._calculate_similarity(
                        results[template_type]["message"],
                        expected_message
                    )
        
        return results
    
    def evaluate_test_suite(self, test_suite_path: str) -> Dict[str, Any]:
        """Evaluate a test suite of diffs.
        
        The test suite should be a JSON file with the following structure:
        {
            "tests": [
                {
                    "name": "Test name",
                    "diff": "Git diff content",
                    "expected_message": "Expected commit message"
                },
                ...
            ]
        }
        
        Args:
            test_suite_path: Path to the test suite JSON file
            
        Returns:
            Dictionary with evaluation results for each test
        """
        # Load the test suite
        with open(test_suite_path, "r") as f:
            test_suite = json.load(f)
        
        results = {}
        
        # Evaluate each test
        for test in test_suite.get("tests", []):
            test_name = test.get("name", "Unnamed test")
            diff = test.get("diff", "")
            expected_message = test.get("expected_message")
            
            logger.info(f"Evaluating test: {test_name}")
            
            test_results = self.evaluate_diff(diff, expected_message)
            results[test_name] = test_results
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        results["summary"] = summary
        
        return results
    
    def _build_context(self, diff_data: Dict[str, Any]) -> str:
        """Build context from diff data.
        
        Args:
            diff_data: Dictionary with git diff information
            
        Returns:
            Context string for prompting
        """
        # Use LlamaIndex to extract context
        return build_prompt_from_diff(diff_data)
    
    def _generate_message(self, prompt: str) -> str:
        """Generate a commit message using the LLM.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Generated commit message
        """
        try:
            logger.debug("Generating commit message")
            message = self.ollama_client.generate(prompt, self.model_config)
            return message.strip()
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            return f"Error: {str(e)}"
    
    def _calculate_similarity(self, message1: str, message2: str) -> float:
        """Calculate similarity between two commit messages.
        
        Args:
            message1: First commit message
            message2: Second commit message
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity calculation based on common words
        words1 = set(message1.lower().split())
        words2 = set(message2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))
    
    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for the test results.
        
        Args:
            results: Dictionary with test results
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_tests": 0,
            "enhanced": {
                "total_similarity": 0.0,
                "count": 0
            },
            "specialized": {
                "total_similarity": 0.0,
                "count": 0,
                "type_counts": {}
            }
        }
        
        # Calculate statistics
        for test_name, test_results in results.items():
            if test_name == "summary":
                continue
            
            summary["total_tests"] += 1
            
            # Enhanced template
            if "enhanced" in test_results and "similarity" in test_results["enhanced"]:
                summary["enhanced"]["total_similarity"] += test_results["enhanced"]["similarity"]
                summary["enhanced"]["count"] += 1
            
            # Specialized template
            if "specialized" in test_results and "similarity" in test_results["specialized"]:
                summary["specialized"]["total_similarity"] += test_results["specialized"]["similarity"]
                summary["specialized"]["count"] += 1
                
                # Count change types
                change_type = test_results["specialized"].get("change_type", "unknown")
                summary["specialized"]["type_counts"][change_type] = summary["specialized"]["type_counts"].get(change_type, 0) + 1
        
        # Calculate averages
        if summary["enhanced"]["count"] > 0:
            summary["enhanced"]["average_similarity"] = summary["enhanced"]["total_similarity"] / summary["enhanced"]["count"]
        
        if summary["specialized"]["count"] > 0:
            summary["specialized"]["average_similarity"] = summary["specialized"]["total_similarity"] / summary["specialized"]["count"]
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save benchmark results to a file.
        
        Args:
            results: Dictionary with benchmark results
            output_path: Path to save the results
        """
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_path}")

    def _calculate_similarity(self, message1: str, message2: str) -> float:
        """Calculate similarity between two commit messages.
        
        Args:
            message1: First commit message
            message2: Second commit message
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity calculation based on common words
        words1 = set(message1.lower().split())
        words2 = set(message2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))


def create_test_suite(diffs_directory: str, output_path: str) -> None:
    """Create a test suite from a directory of diff files.
    
    Args:
        diffs_directory: Path to directory containing diff files and expected messages
        output_path: Path to save the test suite
    """
    test_suite = {"tests": []}
    
    # Find all .diff files
    for filename in os.listdir(diffs_directory):
        if filename.endswith(".diff"):
            test_name = os.path.splitext(filename)[0]
            diff_path = os.path.join(diffs_directory, filename)
            expected_path = os.path.join(diffs_directory, f"{test_name}.expected.txt")
            
            # Read diff content
            with open(diff_path, "r") as f:
                diff_content = f.read()
            
            # Read expected message if it exists
            expected_message = None
            if os.path.exists(expected_path):
                with open(expected_path, "r") as f:
                    expected_message = f.read()
            
            # Add to test suite
            test_suite["tests"].append({
                "name": test_name,
                "diff": diff_content,
                "expected_message": expected_message
            })
    
    # Save test suite
    with open(output_path, "w") as f:
        json.dump(test_suite, f, indent=2)
    
    logger.info(f"Created test suite with {len(test_suite['tests'])} tests at {output_path}")


def main(test_suite_path: str, output_path: str) -> None:
    """Run the benchmark on a test suite.
    
    Args:
        test_suite_path: Path to the test suite JSON file
        output_path: Path to save the results
    """
    benchmark = PromptBenchmark()
    results = benchmark.evaluate_test_suite(test_suite_path)
    benchmark.save_results(results, output_path)
    
    # Print summary
    summary = results["summary"]
    print(f"Total tests: {summary['total_tests']}")
    
    if "average_similarity" in summary["enhanced"]:
        print(f"Enhanced template average similarity: {summary['enhanced']['average_similarity']:.2f}")
    
    if "average_similarity" in summary["specialized"]:
        print(f"Specialized template average similarity: {summary['specialized']['average_similarity']:.2f}")
        
        print("Change type counts:")
        for change_type, count in summary["specialized"]["type_counts"].items():
            print(f"  {change_type}: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark prompt performance")
    parser.add_argument("--create", help="Create test suite from directory of diff files")
    parser.add_argument("--run", help="Run benchmark on test suite")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.create:
        create_test_suite(args.create, args.output)
    elif args.run:
        main(args.run, args.output)
    else:
        parser.print_help()