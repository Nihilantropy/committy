"""Tests for the benchmark module."""

import pytest
from unittest.mock import patch, MagicMock

from committy.llm.benchmark import PromptBenchmark


class TestPromptBenchmark:
    """Tests for the PromptBenchmark class."""
    
    def test_init(self):
        """Test initialization with default values."""
        benchmark = PromptBenchmark()
        assert benchmark.model_config is not None
        assert "model" in benchmark.model_config
    
    def test_calculate_similarity(self):
        """Test calculating similarity between messages."""
        benchmark = PromptBenchmark()
        
        # Test with identical messages
        similarity = benchmark._calculate_similarity(
            "feat: add new feature",
            "feat: add new feature"
        )
        assert similarity == 1.0
        
        # Test with completely different messages
        similarity = benchmark._calculate_similarity(
            "feat: add new feature",
            "fix: correct bug xyz"
        )
        assert similarity < 0.3
        
        # Test with somewhat similar messages
        similarity = benchmark._calculate_similarity(
            "feat: add user authentication",
            "feat: implement user authentication system"
        )
        assert 0.3 < similarity < 0.8
        
        # Test with empty messages
        similarity = benchmark._calculate_similarity("", "")
        assert similarity == 0.0
    
    # Add other tests for PromptBenchmark methods here...