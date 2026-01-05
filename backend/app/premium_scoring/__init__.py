"""
Premium scoring module for ResuMate AI.
Implements industry-standard ranking pipeline: BM25 + Semantic Retrieval + Cross-Encoder Reranking + Evidence + Calibration.
"""
from .pipeline import PremiumScorer

__all__ = ['PremiumScorer']
