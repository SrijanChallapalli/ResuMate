"""
BM25 keyword scoring for premium analysis.
Uses rank-bm25 library for local, fast keyword matching.
"""
import re
from typing import List
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    """
    Simple tokenization: lowercase, split on whitespace, strip punctuation.
    Returns list of tokens.
    """
    # Convert to lowercase
    text_lower = text.lower()
    # Remove punctuation except word boundaries, split on whitespace
    tokens = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text_lower)
    return tokens


def calculate_bm25_score(resume_text: str, job_text: str) -> float:
    """
    Calculate BM25 score between resume and job description.
    Returns normalized score 0-100.
    
    BM25 is a probabilistic ranking function that considers:
    - Term frequency (TF) in the document
    - Inverse document frequency (IDF) across corpus
    - Document length normalization
    
    We normalize the raw BM25 score to 0-100 using a sigmoid-like scaling.
    """
    # Tokenize both texts
    resume_tokens = tokenize(resume_text)
    job_tokens = tokenize(job_text)
    
    if not resume_tokens or not job_tokens:
        return 0.0
    
    # Create corpus: [resume_tokens, job_tokens]
    # BM25Okapi expects a list of tokenized documents
    corpus = [resume_tokens, job_tokens]
    bm25 = BM25Okapi(corpus)
    
    # Score resume against job description (query)
    # We use job_tokens as the query
    scores = bm25.get_scores(job_tokens)
    # scores[0] is the score of resume (first doc) against job query
    raw_score = scores[0]
    
    # Normalize BM25 score to 0-100
    # BM25 scores are typically in range [-inf, +inf], but for our use case
    # they're usually positive and in a reasonable range.
    # We use a sigmoid-like transformation: 100 * (1 / (1 + exp(-0.1 * (score - 5))))
    # This maps typical BM25 scores (0-20) to 0-100 range
    # Adjust parameters based on observed score distribution
    normalized = 100 / (1 + 2.71828 ** (-0.1 * (raw_score - 5)))
    
    # Clamp to 0-100
    return max(0.0, min(100.0, round(normalized, 1)))
