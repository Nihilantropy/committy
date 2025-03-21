"""Core engine for AutoCommit."""

from autocommit.git import diff
from autocommit.llm import model

def process():
    """Process the git diff and generate a commit message."""
    current_diff = diff.get_diff()
    return model.generate_commit_message(current_diff)
