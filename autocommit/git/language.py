"""Utilities for language detection in git diffs."""

import os
import logging
from typing import Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Language detection by file extension
EXTENSION_TO_LANGUAGE = {
    # Programming languages
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".rs": "Rust",
    ".scala": "Scala",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    
    # Web
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",
    ".svelte": "Svelte",
    
    # Data/Config
    ".json": "JSON",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".csv": "CSV",
    ".tsv": "TSV",
    
    # Shell/Scripts
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".bat": "Batch",
    ".ps1": "PowerShell",
    
    # Documentation
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".tex": "LaTeX",
    ".txt": "Text",
    
    # Other
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".dockerfile": "Dockerfile",
    ".makefile": "Makefile",
    ".cmake": "CMake",
    ".r": "R",
    ".dart": "Dart",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl Module",
    ".ex": "Elixir",
    ".exs": "Elixir Script",
    ".elm": "Elm",
    ".erl": "Erlang",
    ".clj": "Clojure",
    ".fs": "F#",
    ".hs": "Haskell",
    ".tf": "Terraform",
    ".sol": "Solidity"
}

# Special filenames to language mapping
FILENAME_TO_LANGUAGE = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
    ".gitignore": "GitIgnore",
    ".dockerignore": "DockerIgnore",
    ".env": "Environment Variables",
    "package.json": "npm Package",
    "requirements.txt": "Python Requirements",
    "go.mod": "Go Module",
    "build.gradle": "Gradle",
    "pom.xml": "Maven POM",
    "Gemfile": "Ruby Gemfile",
    "Cargo.toml": "Rust Cargo"
}


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language based on file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language or None if unknown
    """
    if not file_path:
        return None
    
    # Check if the file is a special file
    basename = os.path.basename(file_path)
    if basename in FILENAME_TO_LANGUAGE:
        language = FILENAME_TO_LANGUAGE[basename]
        logger.debug(f"Detected language for {file_path}: {language} (by filename)")
        return language
    
    # Check by extension
    _, ext = os.path.splitext(file_path.lower())
    if not ext:
        logger.debug(f"No extension found for {file_path}")
        return None
    
    language = EXTENSION_TO_LANGUAGE.get(ext)
    if language:
        logger.debug(f"Detected language for {file_path}: {language} (by extension {ext})")
        return language
    
    logger.debug(f"Unknown language for extension {ext} in file {file_path}")
    return None


def analyze_path_for_context(file_path: str) -> Dict[str, str]:
    """Analyze file path for contextual information.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with contextual information
    """
    path_parts = file_path.split(os.path.sep)
    basename = os.path.basename(file_path)
    _, extension = os.path.splitext(basename)
    
    # Detect potential components or modules
    modules = []
    if len(path_parts) > 1:
        # Look for common directory names that indicate components
        for part in path_parts[:-1]:  # Exclude the filename
            if part.lower() in ["src", "lib", "app", "test", "tests", "docs"]:
                modules.append(part)
            elif len(part) > 0 and not part.startswith("."):
                modules.append(part)
    
    # Detect if it's a test file
    is_test = False
    if "test" in basename.lower() or "spec" in basename.lower():
        is_test = True
    elif len(path_parts) > 1 and (
        "test" in path_parts or "tests" in path_parts or "spec" in path_parts
    ):
        is_test = True
    
    # Detect if it's documentation
    is_doc = False
    if extension in [".md", ".rst", ".txt", ".adoc"]:
        is_doc = True
    elif len(path_parts) > 1 and "doc" in path_parts:
        is_doc = True
    
    # Detect if it's config
    is_config = False
    if basename.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".config")):
        is_config = True
    elif basename in [".gitignore", ".dockerignore", ".editorconfig", "Dockerfile"]:
        is_config = True
    
    return {
        "modules": ",".join(modules),
        "is_test": "true" if is_test else "false",
        "is_doc": "true" if is_doc else "false",
        "is_config": "true" if is_config else "false"
    }