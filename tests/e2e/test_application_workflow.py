"""End-to-end tests for the complete application workflow."""

import os
import subprocess
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

from committy.cli.main import main


class TestApplicationWorkflow:
    """End-to-end tests for the complete application workflow."""
    
    @pytest.fixture
    def git_repo(self):
        """Create a temporary git repository for testing."""
        # Create a temporary directory
        repo_dir = tempfile.mkdtemp()
        
        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],
                cwd=repo_dir,
                check=True,
                capture_output=True
            )
            
            # Configure git user
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_dir,
                check=True,
                capture_output=True
            )
            
            # Return the repo directory
            yield repo_dir
        finally:
            # Clean up
            shutil.rmtree(repo_dir)
    
    def test_dry_run_workflow_with_mocks(self, git_repo):
        """Test the end-to-end dry run workflow with mocks."""
        # Create a test file
        test_file = os.path.join(git_repo, "test.py")
        with open(test_file, "w") as f:
            f.write("def test():\n    return True\n")
        
        # Stage the file
        subprocess.run(
            ["git", "add", "test.py"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )
        
        # Change working directory to the repo
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)
            
            # Create patches for the application
            with patch("committy.cli.main.process_diff") as mock_process:
                # Setup mocks
                mock_process.return_value = (True, "feat(test): add test function")
                
                # Run the application with dry-run
                with patch("sys.argv", ["committy", "--dry-run"]):
                    result = main()
                
                # Verify result
                assert result == 0
                
                # Verify process_diff was called
                mock_process.assert_called_once()
        finally:
            # Restore working directory
            os.chdir(original_dir)
    
    def test_analyze_workflow_with_mocks(self, git_repo):
        """Test the end-to-end analyze workflow with mocks."""
        # Create a test file
        test_file = os.path.join(git_repo, "test.py")
        with open(test_file, "w") as f:
            f.write("def test():\n    return True\n")
        
        # Stage the file
        subprocess.run(
            ["git", "add", "test.py"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )
        
        # Change working directory to the repo
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)
            
            # Create patches for the application
            with patch("committy.cli.main.display_diff_analysis") as mock_analyze:
                # Run the application with analyze
                with patch("sys.argv", ["committy", "--analyze"]):
                    result = main()
                
                # Verify result
                assert result == 0
                
                # Verify display_diff_analysis was called
                mock_analyze.assert_called_once()
        finally:
            # Restore working directory
            os.chdir(original_dir)
    
    @patch("committy.cli.main.engine.generate_commit_message")
    @patch("committy.cli.main.prompt_confirmation")
    def test_full_commit_workflow_with_mocks(self, mock_prompt, mock_generate, git_repo):
        """Test the full commit workflow with mocks."""
        # Create a test file
        test_file = os.path.join(git_repo, "test.py")
        with open(test_file, "w") as f:
            f.write("def test():\n    return True\n")
        
        # Stage the file
        subprocess.run(
            ["git", "add", "test.py"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )
        
        # Change working directory to the repo
        original_dir = os.getcwd()
        try:
            os.chdir(git_repo)
            
            # Setup mocks
            mock_generate.return_value = "feat(test): add test function"
            mock_prompt.return_value = (True, "feat(test): add test function")
            
            # Run the application
            with patch("sys.argv", ["committy"]):
                result = main()
            
            # Verify result
            assert result == 0
            
            # Verify a commit was created
            git_log = subprocess.run(
                ["git", "log", "--oneline"],
                cwd=git_repo,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            assert "feat(test): add test function" in git_log
        finally:
            # Restore working directory
            os.chdir(original_dir)
    
    def test_different_change_types_with_mocks(self, git_repo):
        """Test the application with different change types."""
        # Define tests for different change types
        change_types = ["feat", "fix", "docs", "refactor"]
        
        for change_type in change_types:
            # Create a test file
            test_file = os.path.join(git_repo, f"{change_type}_test.py")
            with open(test_file, "w") as f:
                f.write(f"def {change_type}_test():\n    return True\n")
            
            # Stage the file
            subprocess.run(
                ["git", "add", f"{change_type}_test.py"],
                cwd=git_repo,
                check=True,
                capture_output=True
            )
            
            # Change working directory to the repo
            original_dir = os.getcwd()
            try:
                os.chdir(git_repo)
                
                # Create patches for the application
                with patch("committy.cli.main.process_diff") as mock_process:
                    # Setup mocks
                    mock_process.return_value = (True, f"{change_type}(test): add {change_type} test")
                    
                    # Run the application with dry-run
                    with patch("sys.argv", ["committy", "--dry-run"]):
                        result = main()
                    
                    # Verify result
                    assert result == 0
                    
                    # Verify process_diff was called
                    mock_process.assert_called_once()
            finally:
                # Restore working directory
                os.chdir(original_dir)
                
                # Commit the change to prepare for the next test
                subprocess.run(
                    ["git", "commit", "-m", f"{change_type}(test): add {change_type} test"],
                    cwd=git_repo,
                    check=True,
                    capture_output=True
                )