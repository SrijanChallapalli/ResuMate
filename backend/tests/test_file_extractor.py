"""
Unit tests for file extraction module.
"""
import pytest
from app.file_extractor import FileExtractor


def test_validate_file():
    """Test file validation."""
    # Valid file
    is_valid, error = FileExtractor.validate_file("resume.pdf", 1024 * 1024)  # 1MB
    assert is_valid is True
    assert error is None
    
    # Invalid extension
    is_valid, error = FileExtractor.validate_file("resume.exe", 1024)
    assert is_valid is False
    assert "Unsupported" in error
    
    # File too large
    is_valid, error = FileExtractor.validate_file("resume.pdf", 10 * 1024 * 1024)  # 10MB
    assert is_valid is False
    assert "too large" in error
    
    # Empty file
    is_valid, error = FileExtractor.validate_file("resume.txt", 0)
    assert is_valid is False
    assert "empty" in error


def test_sanitize_filename():
    """Test filename sanitization."""
    # Normal filename
    assert FileExtractor.sanitize_filename("resume.pdf") == "resume.pdf"
    
    # Path traversal attempt
    assert FileExtractor.sanitize_filename("../../../etc/passwd") == "passwd"
    
    # Dangerous characters
    assert "<>" not in FileExtractor.sanitize_filename("resume<>file.pdf")
    
    # Long filename
    long_name = "a" * 300 + ".pdf"
    sanitized = FileExtractor.sanitize_filename(long_name)
    assert len(sanitized) <= 255


def test_extract_text_from_txt():
    """Test TXT extraction."""
    content = b"Software engineer with 5 years of experience.\n\nPython, JavaScript, React."
    text = FileExtractor.extract_text_from_txt(content)
    assert "Software engineer" in text
    assert "Python" in text


def test_extract_text_truncation():
    """Test that extracted text is truncated to max length."""
    # Create content longer than max
    long_content = b"A" * (FileExtractor.MAX_EXTRACTED_TEXT + 1000)
    text = FileExtractor.extract_text_from_txt(long_content)
    assert len(text) <= FileExtractor.MAX_EXTRACTED_TEXT

