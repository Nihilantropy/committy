"""Tests for the LlamaIndex integration."""

import pytest
from unittest.mock import MagicMock, patch

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import IndexNode, NodeWithScore

from autocommit.llm.index import DiffIndexer, build_prompt_from_diff


class TestDiffIndexer:
    """Tests for the DiffIndexer class."""
    
    def test_init(self):
        """Test initializing the DiffIndexer."""
        indexer = DiffIndexer(chunk_size=256, chunk_overlap=10)
        assert indexer.chunk_size == 256
        assert indexer.chunk_overlap == 10
        assert indexer.node_parser is not None
    
    def test_process_diff(self):
        """Test processing a diff into documents."""
        diff_data = {
            "files": [
                {
                    "path": "test.py",
                    "change_type": "modified",
                    "additions": 5,
                    "deletions": 2,
                    "language": "Python",
                    "diff_content": "@@ -1,3 +1,6 @@\n def test():\n-    return 1\n+    return 2\n+\n+def new_function():\n+    return 3",
                    "extension": ".py"
                }
            ],
            "summary": {
                "total_files": 1,
                "total_additions": 5,
                "total_deletions": 2,
                "languages": ["Python"]
            }
        }
        
        indexer = DiffIndexer()
        documents = indexer.process_diff(diff_data)
        
        # Check that we got the expected number of documents
        assert len(documents) == 2
        
        # Check summary document
        summary_doc = documents[0]
        assert summary_doc.metadata["type"] == "summary"
        assert "Git Diff Summary" in summary_doc.text
        assert "Total Files Changed: 1" in summary_doc.text
        
        # Check file document
        file_doc = documents[1]
        assert file_doc.metadata["type"] == "file"
        assert file_doc.metadata["path"] == "test.py"
        assert file_doc.metadata["language"] == "Python"
        assert "# File: test.py" in file_doc.text
        assert "```diff" in file_doc.text
    
    def test_build_summary_text(self):
        """Test building summary text from diff data."""
        diff_data = {
            "summary": {
                "total_files": 2,
                "total_additions": 10,
                "total_deletions": 5,
                "languages": ["Python", "JavaScript"]
            },
            "files": [
                {
                    "path": "src/main.py",
                    "change_type": "modified",
                    "additions": 8,
                    "deletions": 3
                },
                {
                    "path": "src/utils.js",
                    "change_type": "added",
                    "additions": 2,
                    "deletions": 2
                }
            ]
        }
        
        indexer = DiffIndexer()
        summary_text = indexer._build_summary_text(diff_data)
        
        assert "Total Files Changed: 2" in summary_text
        assert "Total Additions: 10" in summary_text
        assert "Total Deletions: 5" in summary_text
        assert "Languages: Python, JavaScript" in summary_text
        assert "src/main.py (modified): 8 additions, 3 deletions" in summary_text
        assert "src/utils.js (added): 2 additions, 2 deletions" in summary_text
    
    def test_create_file_document(self):
        """Test creating a document for a file diff."""
        file_info = {
            "path": "src/main.py",
            "change_type": "modified",
            "additions": 5,
            "deletions": 2,
            "language": "Python",
            "diff_content": "@@ -1,3 +1,6 @@\n def test():\n-    return 1\n+    return 2\n+\n+def new_function():\n+    return 3",
            "extension": ".py"
        }
        
        indexer = DiffIndexer()
        document = indexer._create_file_document(file_info)
        
        assert document is not None
        assert document.metadata["path"] == "src/main.py"
        assert document.metadata["language"] == "Python"
        assert document.metadata["change_type"] == "modified"
        assert document.metadata["additions"] == 5
        assert document.metadata["deletions"] == 2
        assert "# File: src/main.py" in document.text
        assert "```diff" in document.text
        assert "@@ -1,3 +1,6 @@" in document.text
    
    def test_create_file_document_empty_content(self):
        """Test creating a document with empty diff content."""
        file_info = {
            "path": "src/main.py",
            "change_type": "modified",
            "additions": 0,
            "deletions": 0,
            "language": "Python",
            "diff_content": "",
            "extension": ".py"
        }
        
        indexer = DiffIndexer()
        document = indexer._create_file_document(file_info)
        
        assert document is None
    
    @patch("llama_index.core.VectorStoreIndex")
    def test_create_index(self, mock_index):
        """Test creating an index from documents."""
        # Setup mock
        mock_index.return_value = MagicMock(spec=VectorStoreIndex)
        
        # Create test documents
        doc1 = Document(text="Test document 1", metadata={"type": "summary"})
        doc2 = Document(text="Test document 2", metadata={"type": "file"})
        
        # Create indexer and call method
        indexer = DiffIndexer()
        result = indexer.create_index([doc1, doc2])
        
        # Check that index was created
        assert result is not None
        assert mock_index.called
    
    def test_format_nodes_for_context(self):
        """Test formatting nodes into context text."""
        # Create mock nodes
        node1 = NodeWithScore(
            node=IndexNode(
                text="Summary text",
                metadata={"type": "summary"}
            ),
            score=0.9
        )
        node2 = NodeWithScore(
            node=IndexNode(
                text="File content 1",
                metadata={"type": "file", "path": "file1.py"}
            ),
            score=0.8
        )
        node3 = NodeWithScore(
            node=IndexNode(
                text="File content 2",
                metadata={"type": "file", "path": "file2.py"}
            ),
            score=0.7
        )
        
        # Set up indexer and call method
        indexer = DiffIndexer()
        result = indexer._format_nodes_for_context([node1, node2, node3], max_tokens=1000)
        
        # Check result
        assert "Summary text" in result
        assert "File content 1" in result
        assert "File content 2" in result
    
    def test_format_nodes_for_context_token_limit(self):
        """Test formatting nodes with token limit."""
        # Create mock nodes
        node1 = NodeWithScore(
            node=IndexNode(
                text="Summary text",
                metadata={"type": "summary"}
            ),
            score=0.9
        )
        # Create a long text that should exceed the token limit
        long_text = "A" * 1000  # Approximately 250 tokens
        node2 = NodeWithScore(
            node=IndexNode(
                text=long_text,
                metadata={"type": "file", "path": "file1.py"}
            ),
            score=0.8
        )
        
        # Set up indexer and call method with a low token limit
        indexer = DiffIndexer()
        result = indexer._format_nodes_for_context([node1, node2], max_tokens=100)
        
        # Check result
        assert "Summary text" in result
        assert len(result) < 500  # Should be truncated


@patch('autocommit.llm.index.DiffIndexer')
def test_build_prompt_from_diff(mock_indexer_class):
    """Test building a prompt from diff data."""
    # Setup mocks
    mock_indexer = MagicMock()
    mock_indexer_class.return_value = mock_indexer
    
    mock_documents = [Document(text="Test doc")]
    mock_indexer.process_diff.return_value = mock_documents
    
    mock_index = MagicMock()
    mock_indexer.create_index.return_value = mock_index
    
    mock_indexer.extract_context.return_value = "Extracted context"
    
    # Call function
    diff_data = {"files": [], "summary": {"total_files": 0}}
    result = build_prompt_from_diff(diff_data)
    
    # Check that methods were called
    assert mock_indexer.process_diff.called
    assert mock_indexer.create_index.called
    assert mock_indexer.extract_context.called
    
    # Check prompt structure
    assert "# Git Diff Analysis" in result
    assert "Extracted context" in result
    assert "## Instructions" in result
    assert "## Output Format" in result