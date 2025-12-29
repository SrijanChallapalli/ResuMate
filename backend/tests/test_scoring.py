"""
Unit tests for scoring module.
"""
import pytest
from app.scoring import ResumeScorer
from sentence_transformers import SentenceTransformer


@pytest.fixture
def model():
    """Load model once for all tests."""
    return SentenceTransformer('all-MiniLM-L6-v2')


@pytest.fixture
def scorer(model):
    """Create scorer instance."""
    return ResumeScorer(model)


def test_extract_keywords(scorer):
    """Test keyword extraction."""
    text = "Python developer with experience in machine learning and data science"
    keywords = scorer.extract_keywords(text)
    
    assert "python" in keywords
    assert "developer" in keywords
    assert "machine" in keywords
    assert "learning" in keywords
    assert "the" not in keywords  # Stop word filtered
    assert "a" not in keywords  # Stop word filtered


def test_keyword_overlap(scorer):
    """Test keyword overlap calculation."""
    resume_keywords = {"python", "javascript", "react", "api"}
    job_keywords = {"python", "react", "nodejs", "api", "typescript"}
    
    overlap = scorer.calculate_keyword_overlap(resume_keywords, job_keywords)
    
    assert 0 <= overlap <= 1
    assert overlap > 0  # Should have some overlap


def test_embedding_similarity(scorer):
    """Test embedding similarity calculation."""
    resume_text = "Software engineer with Python and JavaScript experience"
    job_text = "Looking for a Python developer with web development skills"
    
    similarity = scorer.calculate_embedding_similarity(resume_text, job_text)
    
    assert 0 <= similarity <= 1
    assert similarity > 0  # Should have some similarity


def test_calculate_match_score(scorer):
    """Test overall match score calculation."""
    resume_text = "Software engineer with 5 years of Python and JavaScript experience. Built web applications using React and Node.js."
    job_text = "Seeking a Python developer with React experience. Must have web development skills and API design knowledge."
    
    score, matched, missing = scorer.calculate_match_score(resume_text, job_text)
    
    assert 0 <= score <= 100
    assert len(matched) > 0
    assert isinstance(missing, set)


def test_get_top_matches(scorer):
    """Test top matches extraction."""
    matched = {"python", "javascript", "react", "api", "nodejs", "web"}
    top = scorer.get_top_matches(matched, limit=3)
    
    assert len(top) <= 3
    assert all(kw in matched for kw in top)


def test_get_missing_keywords(scorer):
    """Test missing keywords extraction."""
    missing = {"typescript", "docker", "kubernetes", "aws"}
    missing_list = scorer.get_missing_keywords(missing, limit=2)
    
    assert len(missing_list) <= 2
    assert all(kw in missing for kw in missing_list)

