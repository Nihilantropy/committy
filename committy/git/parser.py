"""Parser for git diff output."""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from committy.git.models import FileChange, GitDiff
from committy.git.language import detect_language

# Configure logger
logger = logging.getLogger(__name__)

# Regular expressions for parsing git diff output
FILE_HEADER_PATTERN = re.compile(r"^diff --git a/(.*) b/(.*)$")
FILE_MODE_PATTERN = re.compile(r"^(new|deleted) file mode \d+$")
RENAME_PATTERN = re.compile(r"^rename (from|to) (.*)$")
BINARY_FILE_PATTERN = re.compile(r"^Binary files")
CHUNK_HEADER_PATTERN = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")


def parse_diff(diff_text: str) -> GitDiff:
    """Parse git diff output into a structured format.
    
    Args:
        diff_text: Output from 'git diff' command
        
    Returns:
        GitDiff object containing parsed information
    """
    git_diff = GitDiff()
    
    if not diff_text or not diff_text.strip():
        logger.warning("Empty diff text provided")
        git_diff.calculate_summary()
        return git_diff
    
    # Split diff into sections for each file
    file_sections = split_diff_by_file(diff_text)
    
    for section in file_sections:
        file_change = parse_file_section(section)
        if file_change:
            git_diff.files.append(file_change)
    
    # Calculate summary information
    git_diff.calculate_summary()
    
    logger.info(
        f"Parsed diff with {git_diff.summary.total_files} files, "
        f"{git_diff.summary.total_additions} additions, "
        f"{git_diff.summary.total_deletions} deletions"
    )
    
    return git_diff


def split_diff_by_file(diff_text: str) -> List[str]:
    """Split a complete diff into sections for each file.
    
    Args:
        diff_text: Complete diff output
        
    Returns:
        List of diff sections, one per file
    """
    logger.debug("\n" + "="*80)
    logger.debug("SPLITTING GIT DIFF BY FILE")
    logger.debug("="*80)
    logger.debug(f"Input diff length: {len(diff_text)} characters")
    
    lines = diff_text.split("\n")
    logger.debug(f"Number of lines in diff: {len(lines)}")
    
    sections = []
    current_section = []
    file_count = 0
    
    for line_num, line in enumerate(lines):
        # If we find a new file header and we already have a section, save it
        if FILE_HEADER_PATTERN.match(line) and current_section:
            file_count += 1
            section_text = "\n".join(current_section)
            sections.append(section_text)
            logger.debug(f"\nSaved file section #{file_count} with {len(current_section)} lines")
            current_section = []
        
        # Add line to current section
        current_section.append(line)
    
    # Add the last section if there is one
    if current_section:
        file_count += 1
        section_text = "\n".join(current_section)
        sections.append(section_text)
        logger.debug(f"\nSaved final file section #{file_count} with {len(current_section)} lines")
    
    # Print complete content of each file section
    # print("\nCOMPLETE FILE SECTIONS:")
    # for i, section in enumerate(sections):
    #     # Extract file path from section
    #     section_lines = section.split("\n")
    #     file_path = "unknown"
    #     for line in section_lines:
    #         match = FILE_HEADER_PATTERN.match(line)
    #         if match:
    #             file_path = match.group(1)
    #             break
        
    #     print(f"\n{'='*40}")
    #     print(f"FILE SECTION #{i+1}: {file_path}")
    #     print(f"{'='*40}")
    #     print(section)
    #     print(f"{'='*40}")
    #     print(f"End of file section #{i+1}\n")
    
    # # Print summary
    # print("\nSUMMARY:")
    # print(f"Split diff into {len(sections)} file sections")
    
    return sections

def parse_file_section(section: str) -> Optional[FileChange]:
    """Parse a diff section for a single file.
    
    Args:
        section: Diff section for a single file
        
    Returns:
        FileChange object or None if could not be parsed
    """
    lines = section.split("\n")
    
    # Get file paths
    file_path = None
    for line in lines:
        match = FILE_HEADER_PATTERN.match(line)
        if match:
            file_path = match.group(1)
            break
    
    if not file_path:
        logger.warning("Could not determine file path from diff section")
        return None
    
    # Determine change type
    change_type = "modified"
    for line in lines:
        if re.match(r"^new file", line):
            change_type = "added"
            break
        elif re.match(r"^deleted file", line):
            change_type = "deleted"
            break
        elif re.match(r"^rename from", line):
            change_type = "renamed"
            break
    
    # Check for binary files
    for line in lines:
        if BINARY_FILE_PATTERN.match(line):
            logger.info(f"Binary file detected: {file_path}")
            return FileChange(
                path=file_path,
                change_type=change_type,
                additions=0,
                deletions=0,
                language=detect_language(file_path) or "binary",
                diff_content="[Binary file]",
                extension=os.path.splitext(file_path)[1]
            )
    
    # For deleted files, don't include the full diff content
    if change_type == "deleted":
        file_ext = os.path.splitext(file_path)[1]
        language = detect_language(file_path) or "unknown"
        total_lines = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        
        # Include minimal information about the deletion
        diff_content = f"[File '{file_path}' with {total_lines} lines has been deleted]"
        
        logger.info(f"File deletion detected: {file_path} ({total_lines} lines)")
        
        return FileChange(
            path=file_path,
            change_type="deleted",
            additions=0,
            deletions=total_lines,
            language=language,
            diff_content=diff_content,
            extension=file_ext
        )
    
    # For other change types, proceed as normal
    # Count additions and deletions and extract diff content
    additions, deletions = 0, 0
    start_content_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("+++") or line.startswith("---"):
            # This is part of the file headers, not the content
            continue
        
        if start_content_idx == -1 and line.startswith("@@"):
            # Start of the content
            start_content_idx = i
        
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    
    # Extract the diff content (starting from the first chunk header)
    diff_content = ""
    if start_content_idx != -1:
        diff_content = "\n".join(lines[start_content_idx:])
    
    # Detect language
    language = detect_language(file_path) or "unknown"
    extension = os.path.splitext(file_path)[1]
    
    return FileChange(
        path=file_path,
        change_type=change_type,
        additions=additions,
        deletions=deletions,
        language=language,
        diff_content=diff_content,
        extension=extension
    )


def count_lines_by_type(diff_content: str) -> Tuple[int, int]:
    """Count added and deleted lines in a diff content.
    
    Args:
        diff_content: Diff content for a file
        
    Returns:
        Tuple of (additions, deletions)
    """
    additions = 0
    deletions = 0
    
    for line in diff_content.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    
    return additions, deletions


def extract_changed_files(diff_text: str) -> List[str]:
    """Extract the list of changed files from a diff.
    
    Args:
        diff_text: Output from 'git diff' command
        
    Returns:
        List of file paths
    """
    files = []
    
    for line in diff_text.split("\n"):
        match = FILE_HEADER_PATTERN.match(line)
        if match:
            files.append(match.group(1))
    
    return files