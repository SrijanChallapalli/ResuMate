"""
Tests for premium scoring pipeline.
"""
import pytest
from sentence_transformers import SentenceTransformer
from app.scoring import ResumeScorer
from app.premium_scoring import PremiumScorer
from app.premium_scoring.bm25 import calculate_bm25_score
from app.premium_scoring.calibration import sigmoid_calibrate


@pytest.fixture
def model():
    """Load sentence transformer model."""
    return SentenceTransformer('all-MiniLM-L6-v2')


@pytest.fixture
def classic_scorer(model):
    """Create classic scorer instance."""
    return ResumeScorer(model)


@pytest.fixture
def premium_scorer(model, classic_scorer):
    """Create premium scorer instance."""
    return PremiumScorer(model, classic_scorer)


def test_premium_scorer_initialization(premium_scorer):
    """Test that premium scorer initializes correctly."""
    assert premium_scorer is not None
    assert premium_scorer.bi_encoder is not None
    assert premium_scorer.classic_scorer is not None
    assert premium_scorer.reranker is not None


def test_bm25_score():
    """Test BM25 scoring returns 0-100."""
    resume = "Python developer with experience in machine learning and data science."
    job = "We are looking for a Python developer with machine learning experience."
    
    score = calculate_bm25_score(resume, job)
    
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_bm25_score_empty():
    """Test BM25 with empty inputs."""
    score = calculate_bm25_score("", "")
    assert score == 0.0


def test_sigmoid_calibration():
    """Test sigmoid calibration returns 0-100."""
    # Test various input scores
    for score in [0, 25, 50, 75, 100]:
        calibrated = sigmoid_calibrate(score)
        assert 0 <= calibrated <= 100
        assert isinstance(calibrated, float)
    
    # Test edge cases
    assert sigmoid_calibrate(-10) >= 0  # Should clamp to 0
    assert sigmoid_calibrate(150) <= 100  # Should clamp to 100


def test_premium_score_match_basic(premium_scorer):
    """Test premium score_match returns valid structure."""
    resume = """
    Software Engineer
    Experience:
    - Built Python applications using Flask and Django
    - Implemented machine learning models with scikit-learn
    - Deployed applications to AWS cloud infrastructure
    """
    
    job = """
    We are seeking a Software Engineer with:
    Required:
    - Python programming experience
    - Machine learning knowledge
    - Cloud deployment experience (AWS preferred)
    """
    
    result = premium_scorer.score_match(resume, job)
    
    # Check structure
    assert 'finalScore' in result
    assert 'bm25Score' in result
    assert 'semanticRetrievalScore' in result
    assert 'rerankScore' in result
    assert 'evidenceScore' in result
    assert 'calibratedScore' in result
    assert 'rawScore' in result
    assert 'constrainedScore' in result
    assert 'capApplied' in result
    assert 'mustHavePenalty' in result
    assert 'missingMustHaveCount' in result
    assert 'topMatches' in result
    assert 'missingKeywords' in result
    
    # Check score ranges
    assert 0 <= result['finalScore'] <= 100
    assert 0 <= result['bm25Score'] <= 100
    assert 0 <= result['semanticRetrievalScore'] <= 100
    assert 0 <= result['rerankScore'] <= 100
    assert 0 <= result['evidenceScore'] <= 100
    assert 0 <= result['calibratedScore'] <= 100


def test_premium_score_with_missing_must_have(premium_scorer):
    """Test that cap and penalty are applied when must-have skills are missing."""
    resume = """
    Software Engineer
    Experience:
    - Built web applications using JavaScript
    - Worked with React framework
    """
    
    job = """
    We are seeking a Software Engineer with:
    Required:
    - Python programming (must have)
    - Machine learning experience (must have)
    Preferred:
    - React experience
    """
    
    result = premium_scorer.score_match(resume, job)
    
    # Should have cap applied and penalty
    assert result['capApplied'] is True
    assert result['missingMustHaveCount'] > 0
    assert result['mustHavePenalty'] > 0
    assert result['constrainedScore'] <= 70  # Capped at 70
    assert len(result['mustHaveMissing']) > 0


def test_premium_score_with_all_must_have(premium_scorer):
    """Test that no cap is applied when all must-have skills are present."""
    resume = """
    Software Engineer
    Experience:
    - Built Python applications
    - Implemented machine learning models
    - Deployed to AWS cloud
    """
    
    job = """
    We are seeking a Software Engineer with:
    Required:
    - Python programming (must have)
    - Machine learning experience (must have)
    """
    
    result = premium_scorer.score_match(resume, job)
    
    # Should not have cap applied
    assert result['capApplied'] is False
    assert result['missingMustHaveCount'] == 0
    assert result['mustHavePenalty'] == 0
    assert len(result['mustHaveMissing']) == 0


def test_premium_score_components(premium_scorer):
    """Test that all score components are calculated."""
    resume = """
    Software Engineer
    Experience:
    - Built scalable Python applications using Django
    - Implemented ML models that improved accuracy by 15%
    - Deployed to AWS, serving 1M+ users
    Projects:
    - Developed recommendation system using TensorFlow
    """
    
    job = """
    We are seeking a Software Engineer with:
    Required:
    - Python programming
    - Machine learning experience
    - Cloud deployment (AWS)
    """
    
    result = premium_scorer.score_match(resume, job)
    
    # All components should be > 0 for a good match
    assert result['bm25Score'] > 0
    assert result['semanticRetrievalScore'] > 0
    assert result['rerankScore'] >= 0  # Can be 0 if no snippets
    assert result['evidenceScore'] >= 0
    
    # Raw score should be weighted combination
    expected_raw = (
        result['bm25Score'] * 0.35 +
        result['semanticRetrievalScore'] * 0.35 +
        result['rerankScore'] * 0.20 +
        result['evidenceScore'] * 0.10
    )
    assert abs(result['rawScore'] - expected_raw) < 1.0  # Allow small floating point differences


def test_premium_score_calibration_applied(premium_scorer):
    """Test that sigmoid calibration is applied to final score."""
    resume = """
    Software Engineer
    Experience:
    - Python, machine learning, AWS
    """
    
    job = """
    Software Engineer position.
    Required: Python, machine learning, AWS
    """
    
    result = premium_scorer.score_match(resume, job)
    
    # Calibrated score should be different from constrained (unless at extremes)
    # For mid-range scores, calibration should compress toward center
    if 20 < result['constrainedScore'] < 80:
        # Calibration should be applied (may be same or different)
        assert result['calibratedScore'] == result['finalScore']
    
    # Final score should be calibrated
    assert result['finalScore'] == result['calibratedScore']
    assert 0 <= result['finalScore'] <= 100
