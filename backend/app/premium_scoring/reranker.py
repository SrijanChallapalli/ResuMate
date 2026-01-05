"""
Cross-encoder reranking for premium analysis.
Uses sentence-transformers CrossEncoder for fine-grained relevance scoring.
"""
from typing import List, Tuple
from sentence_transformers import CrossEncoder
import numpy as np


class Reranker:
    """Cross-encoder reranker for resume-job matching."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize cross-encoder model.
        Model is cached as singleton to avoid reloading per request.
        """
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self) -> CrossEncoder:
        """Lazy load model (singleton pattern)."""
        if self._model is None:
            self._model = CrossEncoder(self.model_name)
        return self._model
    
    def rerank_snippets(
        self, 
        resume_snippets: List[str], 
        job_text: str, 
        top_k: int = 5
    ) -> Tuple[List[str], List[float]]:
        """
        Rerank resume snippets against job description using cross-encoder.
        
        Args:
            resume_snippets: List of resume text snippets (bullets/sections)
            job_text: Job description text
            top_k: Number of top snippets to return
        
        Returns:
            (top_snippets, scores): Top K snippets and their relevance scores
        """
        if not resume_snippets or not job_text:
            return [], []
        
        # Create pairs: (snippet, job_text) for each snippet
        pairs = [(snippet, job_text) for snippet in resume_snippets]
        
        # Get relevance scores from cross-encoder
        # Scores are typically in range [-inf, +inf], often [-10, 10]
        try:
            scores = self.model.predict(pairs)
            scores = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
        except Exception as e:
            print(f"Reranking error: {e}")
            # Fallback: return snippets as-is with neutral scores
            return resume_snippets[:top_k], [0.0] * min(len(resume_snippets), top_k)
        
        # Sort by score (descending) and get top K
        scored_pairs = list(zip(resume_snippets, scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        
        top_snippets = [snippet for snippet, _ in scored_pairs[:top_k]]
        top_scores = [score for _, score in scored_pairs[:top_k]]
        
        return top_snippets, top_scores
    
    def calculate_rerank_score(
        self, 
        resume_snippets: List[str], 
        job_text: str, 
        top_k: int = 5
    ) -> float:
        """
        Calculate overall rerank score from top snippets.
        Returns normalized score 0-100.
        
        Strategy:
        1. Rerank all snippets
        2. Take top K scores
        3. Average them and normalize to 0-100
        """
        if not resume_snippets or not job_text:
            return 0.0
        
        _, scores = self.rerank_snippets(resume_snippets, job_text, top_k=top_k)
        
        if not scores:
            return 0.0
        
        # Average top K scores
        avg_score = sum(scores) / len(scores)
        
        # Normalize cross-encoder score to 0-100
        # Cross-encoder scores are typically in range [-10, 10]
        # We use sigmoid: 100 / (1 + exp(-0.3 * (score - 0)))
        # This maps [-10, 10] to approximately [0, 100]
        normalized = 100 / (1 + 2.71828 ** (-0.3 * avg_score))
        
        # Clamp to 0-100
        return max(0.0, min(100.0, round(normalized, 1)))
