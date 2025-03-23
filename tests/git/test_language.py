"""Tests for language detection utilities."""

import pytest

from committy.git.language import detect_language, analyze_path_for_context


class TestLanguageDetection:
    """Tests for language detection utilities."""
    
    def test_detect_language_by_extension(self):
        """Test detecting language by file extension."""
        assert detect_language("file.py") == "Python"
        assert detect_language("file.js") == "JavaScript"
        assert detect_language("file.jsx") == "JavaScript (React)"
        assert detect_language("file.ts") == "TypeScript"
        assert detect_language("file.tsx") == "TypeScript (React)"
        assert detect_language("file.java") == "Java"
        assert detect_language("file.c") == "C"
        assert detect_language("file.cpp") == "C++"
        assert detect_language("file.html") == "HTML"
        assert detect_language("file.css") == "CSS"
        assert detect_language("file.md") == "Markdown"
        assert detect_language("file.json") == "JSON"
        assert detect_language("file.yml") == "YAML"
        assert detect_language("file.go") == "Go"
        assert detect_language("file.rs") == "Rust"
    
    def test_detect_language_by_filename(self):
        """Test detecting language by filename."""
        assert detect_language("Dockerfile") == "Dockerfile"
        assert detect_language("Makefile") == "Makefile"
        assert detect_language(".gitignore") == "GitIgnore"
        assert detect_language("package.json") == "npm Package"
        assert detect_language("requirements.txt") == "Python Requirements"
        assert detect_language("go.mod") == "Go Module"
        assert detect_language("Cargo.toml") == "Rust Cargo"
    
    def test_detect_language_case_insensitive(self):
        """Test that detection is case insensitive for extensions."""
        assert detect_language("file.PY") == "Python"
        assert detect_language("file.Js") == "JavaScript"
        assert detect_language("file.HTML") == "HTML"
    
    def test_detect_language_with_path(self):
        """Test detecting language with a full path."""
        assert detect_language("/path/to/file.py") == "Python"
        assert detect_language("src/components/Button.jsx") == "JavaScript (React)"
        assert detect_language("project/backend/server.go") == "Go"
    
    def test_detect_language_unknown(self):
        """Test detecting language for unknown extensions."""
        assert detect_language("file.xyz") is None
        assert detect_language("file_with_no_extension") is None
        assert detect_language("") is None
        assert detect_language(None) is None
    
    def test_analyze_path_for_context_modules(self):
        """Test analyzing path for module context."""
        result = analyze_path_for_context("src/components/Button.jsx")
        assert result["modules"] == "src,components"
        
        result = analyze_path_for_context("backend/api/users/auth.py")
        assert result["modules"] == "backend,api,users"
    
    def test_analyze_path_for_context_test_files(self):
        """Test detecting test files."""
        result = analyze_path_for_context("tests/test_api.py")
        assert result["is_test"] == "true"
        
        result = analyze_path_for_context("src/components/__tests__/Button.spec.js")
        assert result["is_test"] == "true"
        
        result = analyze_path_for_context("src/App.js")
        assert result["is_test"] == "false"
    
    def test_analyze_path_for_context_doc_files(self):
        """Test detecting documentation files."""
        result = analyze_path_for_context("docs/README.md")
        assert result["is_doc"] == "true"
        
        result = analyze_path_for_context("api/USAGE.rst")
        assert result["is_doc"] == "true"
        
        result = analyze_path_for_context("src/api.js")
        assert result["is_doc"] == "false"
    
    def test_analyze_path_for_context_config_files(self):
        """Test detecting configuration files."""
        result = analyze_path_for_context("config.json")
        assert result["is_config"] == "true"
        
        result = analyze_path_for_context(".gitignore")
        assert result["is_config"] == "true"
        
        result = analyze_path_for_context("Dockerfile")
        assert result["is_config"] == "true"
        
        result = analyze_path_for_context("src/app.js")
        assert result["is_config"] == "false"