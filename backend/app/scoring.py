"""
Scoring module for resume-job matching.
Uses embedding similarity (60%) and keyword overlap (40%).
"""
import re
from typing import List, Tuple, Set
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer


class ResumeScorer:
    """Handles resume-job matching scoring."""
    
    def __init__(self, model: SentenceTransformer):
        """Initialize scorer with a sentence transformer model."""
        self.model = model
    
    def extract_keywords(self, text: str, min_length: int = 3) -> Set[str]:
        """
        Extract keywords from text using simple tokenization.
        Filters out common stop words and short tokens.
        """
        # Common stop words to filter
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Tokenize: split on whitespace and punctuation, keep alphanumeric
        tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
        
        # Filter: length >= min_length, not a stop word, not pure numbers
        keywords = {
            token for token in tokens 
            if len(token) >= min_length 
            and token not in stop_words
            and not token.isdigit()
        }
        
        return keywords
    
    def calculate_keyword_overlap(self, resume_keywords: Set[str], job_keywords: Set[str]) -> float:
        """
        Calculate keyword overlap score using Jaccard similarity and TF-IDF-like weighting.
        Returns a score between 0 and 1.
        """
        if not job_keywords:
            return 0.0
        
        # Jaccard similarity
        intersection = resume_keywords & job_keywords
        union = resume_keywords | job_keywords
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Coverage: how many job keywords are matched
        coverage = len(intersection) / len(job_keywords) if job_keywords else 0.0
        
        # Weighted combination: 50% Jaccard, 50% coverage
        overlap_score = (jaccard * 0.5) + (coverage * 0.5)
        
        return min(1.0, overlap_score)
    
    def calculate_embedding_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Calculate cosine similarity between resume and job description embeddings.
        Returns a score between 0 and 1.
        """
        # Truncate very long texts to prevent memory issues
        max_chars = 10000
        resume_truncated = resume_text[:max_chars] if len(resume_text) > max_chars else resume_text
        job_truncated = job_text[:max_chars] if len(job_text) > max_chars else job_text
        
        try:
            # Generate embeddings
            resume_embedding = self.model.encode(resume_truncated, convert_to_numpy=True, normalize_embeddings=True)
            job_embedding = self.model.encode(job_truncated, convert_to_numpy=True, normalize_embeddings=True)
            
            # Cosine similarity (already normalized, so dot product = cosine)
            similarity = np.dot(resume_embedding, job_embedding)
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1, but with normalized embeddings it's 0-1)
            return float(max(0.0, similarity))
        except Exception as e:
            # Fallback to 0 if embedding fails
            print(f"Embedding calculation error: {e}")
            return 0.0
    
    def calculate_match_score(self, resume_text: str, job_text: str) -> Tuple[float, Set[str], Set[str]]:
        """
        Calculate overall match score combining embedding similarity (60%) and keyword overlap (40%).
        Returns: (score, matched_keywords, missing_keywords)
        """
        # Extract keywords
        resume_keywords = self.extract_keywords(resume_text)
        job_keywords = self.extract_keywords(job_text)
        
        # Calculate scores
        embedding_score = self.calculate_embedding_similarity(resume_text, job_text)
        keyword_score = self.calculate_keyword_overlap(resume_keywords, job_keywords)
        
        # Weighted combination: 60% embedding, 40% keyword
        final_score = (embedding_score * 0.6) + (keyword_score * 0.4)
        
        # Find matched and missing keywords
        matched_keywords = resume_keywords & job_keywords
        missing_keywords = job_keywords - resume_keywords
        
        # Convert to 0-100 scale
        score_0_100 = final_score * 100
        
        return score_0_100, matched_keywords, missing_keywords
    
    def get_top_matches(self, matched_keywords: Set[str], limit: int = 10) -> List[str]:
        """Get top matching keywords, sorted by length (longer = more specific)."""
        sorted_keywords = sorted(matched_keywords, key=lambda x: (-len(x), x.lower()))
        return sorted_keywords[:limit]
    
    def get_missing_keywords(self, missing_keywords: Set[str], limit: int = 10) -> List[str]:
        """Get top missing keywords, sorted by length (longer = more specific)."""
        sorted_keywords = sorted(missing_keywords, key=lambda x: (-len(x), x.lower()))
        return sorted_keywords[:limit]

