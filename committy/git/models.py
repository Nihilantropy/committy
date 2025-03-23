"""Data models for git diff information."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FileChange:
    """Represents a changed file in a git diff."""
    
    path: str
    change_type: str  # "added", "modified", "deleted", "renamed", etc.
    additions: int
    deletions: int
    language: str
    diff_content: str
    extension: Optional[str] = None
    
    def as_dict(self) -> Dict:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary containing file change information
        """
        return {
            "path": self.path,
            "change_type": self.change_type,
            "additions": self.additions,
            "deletions": self.deletions,
            "language": self.language,
            "diff_content": self.diff_content,
            "extension": self.extension
        }


@dataclass
class DiffSummary:
    """Summary information about a git diff."""
    
    total_files: int
    total_additions: int
    total_deletions: int
    languages: List[str] = field(default_factory=list)
    
    def as_dict(self) -> Dict:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary containing diff summary information
        """
        return {
            "total_files": self.total_files,
            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "languages": self.languages
        }


@dataclass
class GitDiff:
    """Represents a complete git diff with all changed files."""
    
    files: List[FileChange] = field(default_factory=list)
    summary: Optional[DiffSummary] = None
    
    def calculate_summary(self) -> None:
        """Calculate summary information from file changes."""
        total_files = len(self.files)
        total_additions = sum(f.additions for f in self.files)
        total_deletions = sum(f.deletions for f in self.files)
        languages = list(set(f.language for f in self.files if f.language))
        
        self.summary = DiffSummary(
            total_files=total_files,
            total_additions=total_additions,
            total_deletions=total_deletions,
            languages=languages
        )
    
    def as_dict(self) -> Dict:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary containing git diff information
        """
        if not self.summary:
            self.calculate_summary()
            
        return {
            "files": [f.as_dict() for f in self.files],
            "summary": self.summary.as_dict() if self.summary else None
        }