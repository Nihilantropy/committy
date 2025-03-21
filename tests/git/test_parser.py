"""Tests for the git diff parser."""

import pytest

from autocommit.git.parser import (
    parse_diff,
    split_diff_by_file,
    parse_file_section,
    count_lines_by_type,
    extract_changed_files
)


class TestParser:
    """Tests for the git diff parser."""
    
    def test_parse_empty_diff(self):
        """Test parsing an empty diff."""
        git_diff = parse_diff("")
        assert len(git_diff.files) == 0
        assert git_diff.summary is not None
        assert git_diff.summary.total_files == 0
    
    def test_parse_diff(self):
        """Test parsing a diff with multiple files."""
        diff_text = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def test():
-    return 1
+    return 2
+    # Added comment
 
diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,2 @@
+def new_function():
+    return 3
"""
        
        git_diff = parse_diff(diff_text)
        
        assert len(git_diff.files) == 2
        assert git_diff.summary.total_files == 2
        assert git_diff.summary.total_additions == 4
        assert git_diff.summary.total_deletions == 1
        
        # Check first file
        file1 = git_diff.files[0]
        assert file1.path == "file1.py"
        assert file1.change_type == "modified"
        assert file1.additions == 2
        assert file1.deletions == 1
        assert file1.language == "Python"
        assert "@@ -1,3 +1,4 @@" in file1.diff_content
        
        # Check second file
        file2 = git_diff.files[1]
        assert file2.path == "file2.py"
        assert file2.change_type == "added"
        assert file2.additions == 2
        assert file2.deletions == 0
        assert file2.language == "Python"
        assert "@@ -0,0 +1,2 @@" in file2.diff_content
    
    def test_split_diff_by_file(self):
        """Test splitting a diff into sections per file."""
        diff_text = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def test():
-    return 1
+    return 2
+    # Added comment

diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,2 @@
+def new_function():
+    return 3"""
        
        sections = split_diff_by_file(diff_text)
        
        assert len(sections) == 2
        assert "diff --git a/file1.py b/file1.py" in sections[0]
        assert "diff --git a/file2.py b/file2.py" in sections[1]
    
    def test_parse_file_section_modified(self):
        """Test parsing a modified file section."""
        section = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def test():
-    return 1
+    return 2
+    # Added comment"""
        
        file_change = parse_file_section(section)
        
        assert file_change is not None
        assert file_change.path == "file1.py"
        assert file_change.change_type == "modified"
        assert file_change.additions == 2
        assert file_change.deletions == 1
        assert file_change.language == "Python"
        assert file_change.extension == ".py"
    
    def test_parse_file_section_added(self):
        """Test parsing an added file section."""
        section = """diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,2 @@
+def new_function():
+    return 3"""
        
        file_change = parse_file_section(section)
        
        assert file_change is not None
        assert file_change.path == "file2.py"
        assert file_change.change_type == "added"
        assert file_change.additions == 2
        assert file_change.deletions == 0
        assert file_change.language == "Python"
        assert file_change.extension == ".py"
    
    def test_parse_file_section_deleted(self):
        """Test parsing a deleted file section."""
        section = """diff --git a/file3.py b/file3.py
deleted file mode 100644
index 1234567..0000000
--- a/file3.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    # This will be removed
-    return 4"""
        
        file_change = parse_file_section(section)
        
        assert file_change is not None
        assert file_change.path == "file3.py"
        assert file_change.change_type == "deleted"
        assert file_change.additions == 0
        assert file_change.deletions == 3
        assert file_change.language == "Python"
        assert file_change.extension == ".py"
    
    def test_parse_file_section_binary(self):
        """Test parsing a binary file section."""
        section = """diff --git a/image.png b/image.png
new file mode 100644
index 0000000..1234567
Binary files /dev/null and b/image.png differ"""
        
        file_change = parse_file_section(section)
        
        assert file_change is not None
        assert file_change.path == "image.png"
        assert file_change.change_type == "added"
        assert file_change.additions == 0
        assert file_change.deletions == 0
        assert file_change.diff_content == "[Binary file]"
        assert file_change.extension == ".png"
    
    def test_parse_file_section_invalid(self):
        """Test parsing an invalid file section."""
        section = """Something that is not a git diff"""
        
        file_change = parse_file_section(section)
        
        assert file_change is None
    
    def test_count_lines_by_type(self):
        """Test counting added and deleted lines in diff content."""
        diff_content = """@@ -1,3 +1,5 @@
 unchanged line
-deleted line 1
-deleted line 2
+added line 1
+added line 2
+added line 3
 another unchanged line"""
        
        additions, deletions = count_lines_by_type(diff_content)
        
        assert additions == 3
        assert deletions == 2
    
    def test_extract_changed_files(self):
        """Test extracting list of changed files from a diff."""
        diff_text = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 def test():
-    return 1
+    return 2

diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,2 @@
+def new_function():
+    return 3"""
        
        files = extract_changed_files(diff_text)
        
        assert len(files) == 2
        assert files[0] == "file1.py"
        assert files[1] == "file2.py"