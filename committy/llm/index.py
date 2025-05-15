"""LlamaIndex integration for Committy.

This module provides functionality for indexing git diffs and querying
them via LlamaIndex to generate commit messages.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import IndexNode
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configure logger
logger = logging.getLogger(__name__)


# Configure LlamaIndex to use local embeddings
Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2", device="cpu") # TODO remove the device to use gpu by default

class DiffIndexer:
    """Indexer for git diffs using LlamaIndex."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 20):
        """Initialize the diff indexer.
        
        Args:
            chunk_size: Size of text chunks for indexing
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        logger.debug(
            f"Initialized DiffIndexer with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def process_diff(self, diff_data: Dict[str, Any]) -> List[Document]:
        """Process git diff data into documents.
        
        Args:
            diff_data: Dict containing git diff information
            
        Returns:    
            List of LlamaIndex Document objects
        """
        documents = []
        
        # Process summary document
        summary_text = self._build_summary_text(diff_data)
        summary_doc = Document(
            text=summary_text,
            metadata={
                "type": "summary",
                "total_files": diff_data.get("summary", {}).get("total_files", 0),
                "total_additions": diff_data.get("summary", {}).get("total_additions", 0),
                "total_deletions": diff_data.get("summary", {}).get("total_deletions", 0),
            }
        )
        documents.append(summary_doc)
        
        # Process individual file diffs
        for file_info in diff_data.get("files", []):
            file_doc = self._create_file_document(file_info)
            if file_doc:
                documents.append(file_doc)
        
        logger.debug(f"Processed diff into {len(documents)} documents")
        return documents

    def _build_summary_text(self, diff_data: Dict[str, Any]) -> str:
        """Build a summary text from the diff data.
        
        Args:
            diff_data: Dict containing git diff information
            
        Returns:
            Summary text
        """
        summary = diff_data.get("summary", {})
        summary_lines = [
            "# Git Diff Summary",
            f"Total Files Changed: {summary.get('total_files', 0)}",
            f"Total Additions: {summary.get('total_additions', 0)}",
            f"Total Deletions: {summary.get('total_deletions', 0)}",
            f"Languages: {', '.join(summary.get('languages', []))}",
            "",
            "## Changed Files:"
        ]
        
        for file_info in diff_data.get("files", []):
            file_line = f"- {file_info.get('path', 'unknown')} " \
                        f"({file_info.get('change_type', 'modified')}): " \
                        f"{file_info.get('additions', 0)} additions, " \
                        f"{file_info.get('deletions', 0)} deletions"
            summary_lines.append(file_line)
        
        return "\n".join(summary_lines)

    def _create_file_document(self, file_info: Dict[str, Any]) -> Optional[Document]:
        """Create a document for a single file from the diff.
        
        Args:
            file_info: Dict containing file diff information
            
        Returns:
            Document object or None if no content
        """
        path = file_info.get("path", "")
        diff_content = file_info.get("diff_content", "")
        
        if not diff_content:
            logger.debug(f"No diff content for file {path}, skipping")
            return None
        
        # Build document text with file info header
        doc_text = (
            f"# File: {path}\n"
            f"Change Type: {file_info.get('change_type', 'modified')}\n"
            f"Additions: {file_info.get('additions', 0)}\n"
            f"Deletions: {file_info.get('deletions', 0)}\n"
            f"Language: {file_info.get('language', 'unknown')}\n\n"
            f"```diff\n{diff_content}\n```"
        )
        
        return Document(
            text=doc_text,
            metadata={
                "type": "file",
                "path": path,
                "change_type": file_info.get("change_type", "modified"),
                "language": file_info.get("language", "unknown"),
                "extensions": file_info.get("extension", ""),
                "additions": file_info.get("additions", 0),
                "deletions": file_info.get("deletions", 0),
            }
        )

    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Create a vector store index from documents."""
        # Process documents into nodes
        nodes = self.node_parser.get_nodes_from_documents(documents)
        logger.debug(f"Created {len(nodes)} nodes from {len(documents)} documents")
        
        # Create index
        try:
            index = VectorStoreIndex(nodes)
            logger.debug("Created vector store index")
            return index
        except ValueError as e:
            # Handle embedding model errors gracefully
            if "OpenAI" in str(e):
                logger.error("Error with embedding model: Using local embeddings instead")
                Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
                # Try again with local embeddings
                index = VectorStoreIndex(nodes)
                return index
            raise

    def extract_context(self, index: VectorStoreIndex, max_tokens: int = 4000) -> str:
        """Extract relevant context from the index for commit message generation.
        
        This function retrieves the most relevant information from the index 
        while keeping the output within the token limit for the LLM prompt.
        
        Args:
            index: VectorStoreIndex containing diff information
            max_tokens: Maximum tokens to include in context
            
        Returns:
            String containing relevant diff context
        """
        # Create a retriever from the index
        retriever = index.as_retriever(similarity_top_k=10)
        
        # Query for relevant information
        # We use a general query to get a good mix of information
        nodes = retriever.retrieve(
            "What are the most important changes in this diff for a commit message?"
        )
        
        # Process and filter nodes
        result_text = self._format_nodes_for_context(nodes, max_tokens)
        logger.debug(f"Extracted context with approximate length {len(result_text) // 4} tokens")
        
        return result_text

    def _format_nodes_for_context(
        self, nodes: List[IndexNode], max_tokens: int
    ) -> str:
        """Format retrieved nodes into a coherent context string.
        
        Args:
            nodes: List of retrieved nodes
            max_tokens: Maximum tokens to include
            
        Returns:
            Formatted context string
        """
        # First, extract the summary node if it exists
        summary_nodes = [n for n in nodes if n.metadata.get("type") == "summary"]
        file_nodes = [n for n in nodes if n.metadata.get("type") == "file"]
        
        # Sort file nodes by relevance score
        file_nodes.sort(key=lambda n: -n.get_score())
        
        result_parts = []
        estimated_token_length = 0
        token_limit_reached = False
        
        # Start with the summary
        for node in summary_nodes:
            text = node.get_content()
            # Rough estimate: 4 chars ~= 1 token
            token_estimate = len(text) // 4
            if estimated_token_length + token_estimate > max_tokens:
                token_limit_reached = True
                break
            result_parts.append(text)
            estimated_token_length += token_estimate
        
        # Add file nodes until we reach the token limit
        if not token_limit_reached:
            for node in file_nodes:
                text = node.get_content()
                # Rough estimate: 4 chars ~= 1 token
                token_estimate = len(text) // 4
                if estimated_token_length + token_estimate > max_tokens:
                    # If we can't fit the full node, try to at least include the header
                    header_lines = text.split("\n")[:5]  # First 5 lines typically contain the header
                    header_text = "\n".join(header_lines)
                    header_token_estimate = len(header_text) // 4
                    
                    if estimated_token_length + header_token_estimate <= max_tokens:
                        result_parts.append(header_text)
                    
                    break
                
                result_parts.append(text)
                estimated_token_length += token_estimate
        
        # Join all parts with double newlines
        return "\n\n".join(result_parts)


def build_prompt_from_diff(diff_data: Dict[str, Any], max_tokens: int = 4000) -> str:
    """Build a prompt for commit message generation from diff data.
    
    Args:
        diff_data: Dictionary containing git diff information
        max_tokens: Maximum tokens to include in the prompt
        
    Returns:
        Formatted prompt string
    """
    # Create indexer and process diff
    indexer = DiffIndexer()
    documents = indexer.process_diff(diff_data)
    index = indexer.create_index(documents)
    
    # Extract relevant context
    context = indexer.extract_context(index, max_tokens)
    
    # Build the prompt
    prompt = f"""# Git Diff Analysis
You are analyzing the following git diff to generate a commit message following Conventional Commits format.

## Diff Content
{context}

## Instructions
Generate a commit message following the Conventional Commits format:
1. Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore
2. Optional scope in parentheses
3. Description in imperative mood
4. Optional body with details
5. Optional footer for breaking changes or issue references

## Output Format
type(scope): description

body

footer
"""
    
    return prompt