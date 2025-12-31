"""
Unit tests for ATS-like scoring functionality.
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


def test_clean_text(scorer):
    """Test text cleaning and normalization."""
    # Test bullet normalization
    text = "• Item 1\n• Item 2\n· Item 3"
    cleaned = scorer.clean_text(text)
    assert "•" in cleaned
    assert "·" not in cleaned
    
    # Test whitespace normalization
    text = "Python    developer   with   experience"
    cleaned = scorer.clean_text(text)
    assert "   " not in cleaned
    
    # Test truncation
    long_text = "A" * 30000
    cleaned = scorer.clean_text(long_text)
    assert len(cleaned) <= scorer.MAX_TEXT_LENGTH + 100  # Allow for truncation message


def test_split_sections(scorer):
    """Test section detection and splitting."""
    resume = """
    John Doe
    Software Engineer
    
    SKILLS
    Python, JavaScript, React
    
    EXPERIENCE
    Software Engineer at Company X
    - Built web applications
    
    EDUCATION
    BS Computer Science
    """
    
    sections = scorer.split_sections(resume)
    
    assert 'SKILLS' in sections
    assert 'EXPERIENCE' in sections
    assert 'EDUCATION' in sections
    assert 'Python' in sections['SKILLS']
    assert 'Company X' in sections['EXPERIENCE']
    assert 'Computer Science' in sections['EDUCATION']


def test_extract_skills(scorer):
    """Test skill extraction with dictionary and aliases."""
    text = "I have experience with Python, JS, and Node.js. Also worked with PostgreSQL."
    
    skills = scorer.extract_skills(text)
    
    assert 'Python' in skills
    assert 'JavaScript' in skills  # JS should map to JavaScript
    assert 'Node.js' in skills
    assert 'PostgreSQL' in skills


def test_extract_must_haves(scorer):
    """Test must-have requirements extraction."""
    job_text = """
    We are looking for a software engineer.
    
    Required skills:
    - Python (required)
    - React (must have)
    - AWS (minimum qualification)
    
    Nice to have: Docker, Kubernetes
    """
    
    must_haves = scorer.extract_must_haves(job_text)
    
    # Should extract skills from required sections
    assert len(must_haves) > 0
    # Python should be in must-haves
    assert 'Python' in must_haves or 'React' in must_haves


def test_keyword_score(scorer):
    """Test keyword scoring with section weighting."""
    resume = """
    SKILLS
    Python, JavaScript, React
    
    EXPERIENCE
    Built web applications using Python and React
    """
    
    job = "Looking for Python and React developer with JavaScript experience"
    
    sections = scorer.split_sections(resume)
    keyword_score, section_scores = scorer.keyword_score(resume, job, sections)
    
    assert 0 <= keyword_score <= 100
    assert isinstance(section_scores, dict)
    assert 'SKILLS' in section_scores or 'EXPERIENCE' in section_scores


def test_semantic_score(scorer):
    """Test semantic similarity scoring."""
    resume = "Software engineer with Python and JavaScript experience"
    job = "Seeking a Python developer with web development skills"
    
    score = scorer.semantic_score(resume, job)
    
    assert 0 <= score <= 100
    assert score > 0  # Should have some similarity


def test_score_match_comprehensive(scorer):
    """Test comprehensive ATS-like scoring."""
    resume = """
    SKILLS
    Python, JavaScript, React, SQL
    
    EXPERIENCE
    Software Engineer at Tech Corp
    - Built web applications using Python and React
    - Designed REST APIs
    """
    
    job = """
    Required: Python, React, AWS
    Must have: JavaScript experience
    Looking for a software engineer with web development skills.
    """
    
    result = scorer.score_match(resume, job)
    
    assert 'finalScore' in result
    assert 'keywordScore' in result
    assert 'semanticScore' in result
    assert 'sectionScores' in result
    assert 'mustHaveMissing' in result
    assert 'matchedSkills' in result
    assert 'missingSkills' in result
    
    assert 0 <= result['finalScore'] <= 100
    assert 0 <= result['keywordScore'] <= 100
    assert 0 <= result['semanticScore'] <= 100
    
    # Check that scores are weighted correctly
    expected_score = (result['keywordScore'] * scorer.KEYWORD_WEIGHT + 
                     result['semanticScore'] * scorer.SEMANTIC_WEIGHT)
    assert abs(result['finalScore'] - expected_score) < 1.0  # Allow small rounding differences


def test_must_have_penalty(scorer):
    """Test that must-have missing skills cap the score."""
    resume = """
    SKILLS
    Python, JavaScript
    
    EXPERIENCE
    Built applications with Python
    """
    
    job = """
    Required: Python, React, AWS (must have)
    Looking for a developer with these skills.
    """
    
    result = scorer.score_match(resume, job)
    
    # If must-have skills are missing, score should be capped
    if result['mustHaveMissing']:
        assert result['finalScore'] <= scorer.MUST_HAVE_PENALTY_CAP
        assert result['mustHavePenaltyApplied'] is True


def test_section_weights_sum(scorer):
    """Test that section weights sum to approximately 1.0."""
    total_weight = sum(scorer.SECTION_WEIGHTS.values())
    assert abs(total_weight - 1.0) < 0.01  # Allow small floating point differences


def test_scoring_weights_sum(scorer):
    """Test that scoring weights sum to 1.0."""
    total_weight = scorer.KEYWORD_WEIGHT + scorer.SEMANTIC_WEIGHT
    assert abs(total_weight - 1.0) < 0.01


def test_empty_resume(scorer):
    """Test handling of empty or minimal resume."""
    resume = "Minimal text"
    job = "Looking for Python developer"
    
    result = scorer.score_match(resume, job)
    
    assert result['finalScore'] >= 0
    assert result['finalScore'] <= 100
    assert isinstance(result['missingKeywords'], list)


def test_empty_job(scorer):
    """Test handling of empty job description."""
    resume = "Software engineer with Python experience"
    job = "Job description"
    
    result = scorer.score_match(resume, job)
    
    assert result['finalScore'] >= 0
    assert result['finalScore'] <= 100

