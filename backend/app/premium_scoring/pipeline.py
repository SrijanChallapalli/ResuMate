"""
Premium scoring pipeline for ResuMate AI.
Implements: BM25 (35%) + Semantic Retrieval (35%) + Cross-Encoder Reranking (20%) + Evidence (10%)
with must-have cap/penalty and sigmoid calibration.
"""
from typing import Dict, List, Set, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

from app.scoring import ResumeScorer
from .bm25 import calculate_bm25_score
from .reranker import Reranker
from .calibration import sigmoid_calibrate


class PremiumScorer:
    """
    Premium scoring pipeline using industry-standard ranking methods.
    
    Pipeline:
    1. BM25 keyword scoring (35%)
    2. Semantic retrieval via bi-encoder (35%)
    3. Cross-encoder reranking (20%)
    4. Evidence scoring (10%)
    5. Apply must-have cap and penalty
    6. Sigmoid calibration
    """
    
    # Score weights
    BM25_WEIGHT = 0.35
    SEMANTIC_WEIGHT = 0.35
    RERANK_WEIGHT = 0.20
    EVIDENCE_WEIGHT = 0.10
    
    # Must-have constraints (reuse from ResumeScorer)
    MUST_HAVE_PENALTY_PER_SKILL = 12
    MUST_HAVE_CAP = 70
    
    # Reranking config
    RERANK_TOP_K = 5
    
    def __init__(self, bi_encoder: SentenceTransformer, classic_scorer: ResumeScorer):
        """
        Initialize premium scorer.
        
        Args:
            bi_encoder: Sentence transformer for semantic retrieval (all-MiniLM-L6-v2)
            classic_scorer: ResumeScorer instance to reuse shared methods
        """
        self.bi_encoder = bi_encoder
        self.classic_scorer = classic_scorer
        self.reranker = Reranker()
    
    def _extract_snippets(self, resume_text: str, sections: Dict[str, str]) -> List[str]:
        """
        Extract snippets from Experience and Projects sections for reranking.
        Falls back to whole resume chunks if sections are empty.
        
        Returns list of text snippets (bullets/paragraphs).
        """
        snippets = []
        
        # Extract from Experience section
        exp_text = sections.get('EXPERIENCE', '').strip()
        if exp_text:
            # Split by bullets or line breaks
            exp_lines = [line.strip() for line in exp_text.split('\n') if line.strip()]
            # Filter out very short lines (likely headers)
            exp_lines = [line for line in exp_lines if len(line) > 20]
            snippets.extend(exp_lines)
        
        # Extract from Projects section
        proj_text = sections.get('PROJECTS', '').strip()
        if proj_text:
            proj_lines = [line.strip() for line in proj_text.split('\n') if line.strip()]
            proj_lines = [line for line in proj_lines if len(line) > 20]
            snippets.extend(proj_lines)
        
        # Fallback: if no snippets, use whole resume chunks
        if not snippets:
            # Split resume into chunks of ~200 chars
            chunk_size = 200
            for i in range(0, len(resume_text), chunk_size):
                chunk = resume_text[i:i + chunk_size].strip()
                if len(chunk) > 20:
                    snippets.append(chunk)
        
        return snippets[:20]  # Limit to 20 snippets for performance
    
    def _semantic_retrieval_score(self, resume_text: str, job_text: str, sections: Dict[str, str]) -> float:
        """
        Calculate semantic retrieval score using bi-encoder.
        Weighted combination of whole resume, experience, and projects.
        Returns score 0-100.
        """
        max_chars = 10000
        
        # Truncate texts
        resume_truncated = resume_text[:max_chars] if len(resume_text) > max_chars else resume_text
        job_truncated = job_text[:max_chars] if len(job_text) > max_chars else job_text
        
        try:
            # Whole resume vs JD
            whole_embedding = self.bi_encoder.encode(
                resume_truncated, 
                convert_to_numpy=True, 
                normalize_embeddings=True
            )
            job_embedding = self.bi_encoder.encode(
                job_truncated, 
                convert_to_numpy=True, 
                normalize_embeddings=True
            )
            whole_sim = float(np.dot(whole_embedding, job_embedding))
        except Exception as e:
            print(f"Semantic retrieval error: {e}")
            whole_sim = 0.0
        
        # Experience section vs JD
        exp_text = sections.get('EXPERIENCE', '').strip()
        exp_sim = 0.0
        if exp_text:
            exp_truncated = exp_text[:max_chars] if len(exp_text) > max_chars else exp_text
            try:
                exp_embedding = self.bi_encoder.encode(
                    exp_truncated, 
                    convert_to_numpy=True, 
                    normalize_embeddings=True
                )
                exp_sim = float(np.dot(exp_embedding, job_embedding))
            except Exception:
                exp_sim = 0.0
        
        # Projects section vs JD
        proj_text = sections.get('PROJECTS', '').strip()
        proj_sim = 0.0
        if proj_text:
            proj_truncated = proj_text[:max_chars] if len(proj_text) > max_chars else proj_text
            try:
                proj_embedding = self.bi_encoder.encode(
                    proj_truncated, 
                    convert_to_numpy=True, 
                    normalize_embeddings=True
                )
                proj_sim = float(np.dot(proj_embedding, job_embedding))
            except Exception:
                proj_sim = 0.0
        
        # Weighted combination (same as classic scorer)
        total_weight = 0.4
        weighted_sum = 0.4 * whole_sim
        
        if exp_text:
            weighted_sum += 0.4 * exp_sim
            total_weight += 0.4
        else:
            weighted_sum += 0.4 * whole_sim
            total_weight += 0.4
        
        if proj_text:
            weighted_sum += 0.2 * proj_sim
            total_weight += 0.2
        else:
            weighted_sum += 0.2 * whole_sim
            total_weight += 0.2
        
        # Normalize and scale to 0-100
        if total_weight > 0:
            S = 100 * (weighted_sum / total_weight)
        else:
            S = 0.0
        
        return max(0, min(100, round(S, 1)))
    
    def score_match(self, resume_text: str, job_text: str) -> Dict:
        """
        Calculate premium match score using full pipeline.
        Returns dict with score breakdown and metadata.
        """
        # Reuse cleaning and section detection from classic scorer
        resume_clean, resume_truncated = self.classic_scorer.clean_text(resume_text)
        job_clean, job_truncated = self.classic_scorer.clean_text(job_text)
        
        # Split resume into sections
        sections = self.classic_scorer.split_sections(resume_clean)
        
        # Extract requirements (must-have and preferred)
        must_have_skills, preferred_skills = self.classic_scorer.extract_requirements(job_clean)
        
        # 1. BM25 score
        bm25_score = calculate_bm25_score(resume_clean, job_clean)
        
        # 2. Semantic retrieval score
        semantic_score = self._semantic_retrieval_score(resume_clean, job_clean, sections)
        
        # 3. Cross-encoder rerank score
        snippets = self._extract_snippets(resume_clean, sections)
        rerank_score = self.reranker.calculate_rerank_score(snippets, job_clean, top_k=self.RERANK_TOP_K)
        
        # 4. Evidence score (reuse from classic scorer)
        evidence_score = self.classic_scorer.evidence_score(resume_clean)
        
        # Combine scores
        raw = (
            bm25_score * self.BM25_WEIGHT +
            semantic_score * self.SEMANTIC_WEIGHT +
            rerank_score * self.RERANK_WEIGHT +
            evidence_score * self.EVIDENCE_WEIGHT
        )
        
        # Apply cap and penalty (same logic as classic scorer)
        resume_skills = self.classic_scorer.extract_skills(resume_clean)
        missing_must_have = must_have_skills - resume_skills
        missing_count = len(missing_must_have)
        
        cap = self.MUST_HAVE_CAP if missing_count > 0 else 100
        must_have_penalty = self.MUST_HAVE_PENALTY_PER_SKILL * missing_count
        
        constrained = max(0, min(100, min(raw, cap) - must_have_penalty))
        
        # Apply sigmoid calibration
        calibrated_score = sigmoid_calibrate(constrained)
        
        # Extract matched and missing skills
        all_jd_skills = self.classic_scorer.extract_skills(job_clean)
        matched_skills = resume_skills & all_jd_skills
        missing_skills = all_jd_skills - resume_skills
        preferred_missing = preferred_skills - resume_skills
        
        # Prioritize top matches
        top_matches = []
        must_have_matched = resume_skills & must_have_skills
        preferred_matched = resume_skills & preferred_skills
        other_matched = matched_skills - must_have_skills - preferred_skills
        
        top_matches.extend(sorted(must_have_matched, key=lambda x: (-len(x), x.lower())))
        top_matches.extend(sorted(preferred_matched, key=lambda x: (-len(x), x.lower())))
        top_matches.extend(sorted(other_matched, key=lambda x: (-len(x), x.lower())))
        top_matches = top_matches[:10]
        
        # Prioritize missing
        missing_keywords = []
        missing_keywords.extend(sorted(missing_must_have, key=lambda x: (-len(x), x.lower())))
        missing_keywords.extend(sorted(preferred_missing, key=lambda x: (-len(x), x.lower())))
        missing_keywords.extend(sorted(missing_skills - must_have_skills - preferred_skills, key=lambda x: (-len(x), x.lower())))
        missing_keywords = missing_keywords[:10]
        
        return {
            'finalScore': calibrated_score,
            'bm25Score': bm25_score,
            'semanticRetrievalScore': semantic_score,
            'rerankScore': rerank_score,
            'evidenceScore': evidence_score,
            'calibratedScore': calibrated_score,
            'rawScore': raw,
            'constrainedScore': constrained,
            'capApplied': cap < 100,
            'mustHavePenalty': must_have_penalty,
            'missingMustHaveCount': missing_count,
            'mustHaveMissing': sorted(list(missing_must_have)),
            'preferredMissing': sorted(list(preferred_missing)),
            'matchedSkills': sorted(list(matched_skills)),
            'missingSkills': sorted(list(missing_skills)),
            'topMatches': top_matches,
            'missingKeywords': missing_keywords,
            'wasTruncated': resume_truncated or job_truncated
        }
