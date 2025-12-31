"""
ATS-like hybrid scoring module for resume-job matching.
Implements: K (Keyword/Skill) 55% + S (Semantic) 35% + E (Evidence) 10%
"""
import re
import json
import os
from typing import List, Tuple, Set, Dict, Optional
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer


class ResumeScorer:
    """Handles ATS-like hybrid resume-job matching scoring."""
    
    # Section weights (for semantic scoring)
    SECTION_WEIGHTS = {
        'SKILLS': 0.35,
        'EXPERIENCE': 0.40,
        'PROJECTS': 0.20,
        'EDUCATION': 0.05,
        'CERTIFICATIONS': 0.05,
        'OTHER': 0.05
    }
    
    # Final score weights
    KEYWORD_WEIGHT = 0.55
    SEMANTIC_WEIGHT = 0.35
    EVIDENCE_WEIGHT = 0.10
    
    # Must-have penalty
    MUST_HAVE_PENALTY_PER_SKILL = 12
    MUST_HAVE_CAP = 70
    
    MAX_TEXT_LENGTH = 25000
    
    def __init__(self, model: SentenceTransformer):
        """Initialize scorer with a sentence transformer model."""
        self.model = model
        self.skill_dict = self._load_skill_dict()
        self._alias_to_canonical = self._build_alias_map()
    
    def _load_skill_dict(self) -> Dict[str, List[str]]:
        """Load skills dictionary from JSON file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            skills_path = os.path.join(script_dir, 'skills.json')
            with open(skills_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load skills dictionary: {e}")
            return {}
    
    def _build_alias_map(self) -> Dict[str, str]:
        """Build mapping from aliases to canonical skill names."""
        alias_map = {}
        for canonical, aliases in self.skill_dict.items():
            # Store canonical as lowercase for consistency
            canonical_lower = canonical.lower()
            alias_map[canonical_lower] = canonical_lower  # Store as lowercase
            for alias in aliases:
                alias_map[alias.lower()] = canonical_lower
        return alias_map
    
    def clean_text(self, text: str) -> Tuple[str, bool]:
        """
        Normalize and clean text (especially from PDFs).
        Returns: (cleaned_text, was_truncated)
        """
        if not text:
            return "", False
        
        was_truncated = False
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
            was_truncated = True
        
        # Normalize various bullet characters to standard bullet
        text = re.sub(r'[•·▪▫‣⁃]\s*', '• ', text)
        
        # Normalize various dashes/hyphens
        text = re.sub(r'[–—]\s*', '- ', text)
        
        # De-hyphenate line breaks (e.g., "devel-\nop" -> "develop")
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Normalize whitespace (but preserve intentional line breaks)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Normalize spaces within line
            line = re.sub(r'[ \t]+', ' ', line.strip())
            if line:
                cleaned_lines.append(line)
        
        # Remove repeated header/footer lines (frequency-based)
        if len(cleaned_lines) > 10:
            line_counts = Counter(cleaned_lines)
            # Remove lines appearing >= 3 times and shorter than ~80 chars
            cleaned_lines = [
                line for line in cleaned_lines
                if not (line_counts[line] >= 3 and len(line) < 80)
            ]
        
        return '\n'.join(cleaned_lines), was_truncated
    
    def split_sections(self, resume_text: str) -> Dict[str, str]:
        """
        Detect and split resume into sections.
        Returns dict mapping section names to text content.
        """
        sections = {
            'SKILLS': '',
            'EXPERIENCE': '',
            'PROJECTS': '',
            'EDUCATION': '',
            'CERTIFICATIONS': '',
            'OTHER': ''
        }
        
        # Section heading patterns (case-insensitive)
        section_patterns = {
            'SKILLS': r'^(skills?|technical\s+skills?|core\s+skills?|competencies?)(\s*:|\s*$|$)',
            'EXPERIENCE': r'^(experience|work\s+experience|employment|professional\s+experience|career)(\s*:|\s*$|$)',
            'PROJECTS': r'^(projects?|personal\s+projects?|side\s+projects?|portfolio)(\s*:|\s*$|$)',
            'EDUCATION': r'^(education|academic|qualifications?|degrees?)(\s*:|\s*$|$)',
            'CERTIFICATIONS': r'^(certifications?|certificates?|licenses?|credentials?)(\s*:|\s*$|$)'
        }
        
        lines = resume_text.split('\n')
        current_section = 'OTHER'
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                if current_content:
                    sections[current_section] += '\n'.join(current_content) + '\n'
                    current_content = []
                continue
            
            # Check if this line is a section header
            matched_section = None
            for section_name, pattern in section_patterns.items():
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    matched_section = section_name
                    break
            
            if matched_section:
                # Save previous section content
                if current_content:
                    sections[current_section] += '\n'.join(current_content) + '\n'
                    current_content = []
                current_section = matched_section
            else:
                # Add to current section
                current_content.append(line_stripped)
        
        # Save last section
        if current_content:
            sections[current_section] += '\n'.join(current_content) + '\n'
        
        return sections
    
    def extract_skills(self, text: str, skill_dict: Optional[Dict] = None) -> Set[str]:
        """
        Extract skills using dictionary and aliases.
        Matches multi-word phrases first, then single tokens with word boundaries.
        Returns set of canonical skill names (lowercase).
        """
        if skill_dict is None:
            skill_dict = self.skill_dict
        
        if not skill_dict:
            return set()
        
        text_lower = text.lower()
        found_skills = set()
        
        # Sort by length (longest first) to match multi-word phrases first
        sorted_skills = sorted(skill_dict.items(), key=lambda x: (-len(x[0]), x[0]))
        
        for canonical, aliases in sorted_skills:
            canonical_lower = canonical.lower()
            
            # Check canonical name (word boundary or phrase)
            if ' ' in canonical:
                # Multi-word phrase
                pattern = r'\b' + re.escape(canonical_lower) + r'\b'
            else:
                # Single word
                pattern = r'\b' + re.escape(canonical_lower) + r'\b'
            
            if re.search(pattern, text_lower):
                found_skills.add(canonical_lower)
                continue
            
            # Check aliases
            for alias in aliases:
                alias_lower = alias.lower()
                if ' ' in alias:
                    pattern = r'\b' + re.escape(alias_lower) + r'\b'
                else:
                    pattern = r'\b' + re.escape(alias_lower) + r'\b'
                
                if re.search(pattern, text_lower):
                    found_skills.add(canonical_lower)
                    break
        
        return found_skills
    
    def extract_requirements(self, job_text: str) -> Tuple[Set[str], Set[str]]:
        """
        Extract must-have and preferred requirements from job description.
        Returns: (must_have_skills, preferred_skills)
        """
        lines = job_text.split('\n')
        must_have_lines = []
        preferred_lines = []
        
        # Patterns for must-have
        must_have_patterns = [
            r'required',
            r'must\s+have',
            r'minimum\s+qualifications?',
            r'we\s+require',
            r'you\s+have',
            r'essential'
        ]
        
        # Patterns for preferred
        preferred_patterns = [
            r'preferred',
            r'bonus',
            r'nice\s+to\s+have',
            r'plus'
        ]
        
        for line in lines:
            line_lower = line.lower()
            # Check for must-have patterns
            if any(re.search(pattern, line_lower) for pattern in must_have_patterns):
                must_have_lines.append(line)
            # Check for preferred patterns
            elif any(re.search(pattern, line_lower) for pattern in preferred_patterns):
                preferred_lines.append(line)
        
        # If no explicit must-have section found, check first 500 chars
        if not must_have_lines:
            must_have_text = job_text[:500]
        else:
            must_have_text = ' '.join(must_have_lines)
        
        preferred_text = ' '.join(preferred_lines) if preferred_lines else ''
        
        # Extract skills from each
        must_have_skills = self.extract_skills(must_have_text)
        preferred_skills = self.extract_skills(preferred_text)
        
        return must_have_skills, preferred_skills
    
    def keyword_score(self, resume_text: str, job_text: str, 
                     must_have: Set[str], preferred: Set[str]) -> float:
        """
        Calculate keyword/skill score K using weighted recall-style scoring.
        Returns score 0-100.
        """
        # Extract all skills
        resume_skills = self.extract_skills(resume_text)
        all_jd_skills = self.extract_skills(job_text)
        other_jd_skills = all_jd_skills - must_have - preferred
        
        # Weighted recall-style scoring
        def score_component(found: Set[str], total: Set[str], weight: float) -> float:
            if not total:
                return 0.0
            return weight * (len(found) / len(total))
        
        # Calculate components
        must_have_score = score_component(resume_skills & must_have, must_have, 2.0)
        preferred_score = score_component(resume_skills & preferred, preferred, 1.0)
        other_score = score_component(resume_skills & other_jd_skills, other_jd_skills, 0.5)
        
        K_raw = must_have_score + preferred_score + other_score
        
        # Calculate max possible (only include components with total > 0)
        max_possible = 0.0
        if must_have:
            max_possible += 2.0
        if preferred:
            max_possible += 1.0
        if other_jd_skills:
            max_possible += 0.5
        
        # Normalize to 0-100
        if max_possible > 0:
            K = 100 * (K_raw / max_possible)
        else:
            K = 0.0
        
        # Add TF-IDF adjustment (+/- up to 10 points)
        resume_tokens = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', resume_text.lower()))
        job_tokens = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', job_text.lower()))
        
        # Simple stopwords filter
        stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can'}
        resume_tokens = {t for t in resume_tokens if t not in stopwords and len(t) >= 3}
        job_tokens = {t for t in job_tokens if t not in stopwords and len(t) >= 3}
        
        # Jaccard similarity
        if job_tokens:
            intersection = resume_tokens & job_tokens
            union = resume_tokens | job_tokens
            jaccard = len(intersection) / len(union) if union else 0.0
        else:
            jaccard = 0.0
        
        # TF-IDF adjustment: (overlap - 0.05) * 100 clipped to [-10, +10]
        tfidf_adjust = max(-10, min(10, (jaccard - 0.05) * 100))
        
        K = max(0, min(100, K + tfidf_adjust))
        
        return round(K, 1)
    
    def semantic_score(self, resume_text: str, job_text: str, sections: Dict[str, str]) -> float:
        """
        Calculate semantic similarity using embeddings.
        Weighted combination of whole resume, experience, and projects.
        Returns score 0-100.
        """
        max_chars = 10000
        
        # Whole resume vs JD
        resume_truncated = resume_text[:max_chars] if len(resume_text) > max_chars else resume_text
        job_truncated = job_text[:max_chars] if len(job_text) > max_chars else job_text
        
        try:
            whole_embedding = self.model.encode(resume_truncated, convert_to_numpy=True, normalize_embeddings=True)
            job_embedding = self.model.encode(job_truncated, convert_to_numpy=True, normalize_embeddings=True)
            whole_sim = float(np.dot(whole_embedding, job_embedding))
        except Exception as e:
            print(f"Embedding calculation error: {e}")
            whole_sim = 0.0
        
        # Experience section vs JD
        exp_text = sections.get('EXPERIENCE', '').strip()
        exp_sim = 0.0
        if exp_text:
            exp_truncated = exp_text[:max_chars] if len(exp_text) > max_chars else exp_text
            try:
                exp_embedding = self.model.encode(exp_truncated, convert_to_numpy=True, normalize_embeddings=True)
                exp_sim = float(np.dot(exp_embedding, job_embedding))
            except Exception:
                exp_sim = 0.0
        
        # Projects section vs JD
        proj_text = sections.get('PROJECTS', '').strip()
        proj_sim = 0.0
        if proj_text:
            proj_truncated = proj_text[:max_chars] if len(proj_text) > max_chars else proj_text
            try:
                proj_embedding = self.model.encode(proj_truncated, convert_to_numpy=True, normalize_embeddings=True)
                proj_sim = float(np.dot(proj_embedding, job_embedding))
            except Exception:
                proj_sim = 0.0
        
        # Weighted combination
        # whole: 0.4, experience: 0.4 (if present), projects: 0.2 (if present)
        total_weight = 0.4
        weighted_sum = 0.4 * whole_sim
        
        if exp_text:
            weighted_sum += 0.4 * exp_sim
            total_weight += 0.4
        else:
            # Redistribute experience weight to whole
            weighted_sum += 0.4 * whole_sim
            total_weight += 0.4
        
        if proj_text:
            weighted_sum += 0.2 * proj_sim
            total_weight += 0.2
        else:
            # Redistribute projects weight
            weighted_sum += 0.2 * whole_sim
            total_weight += 0.2
        
        # Normalize and scale to 0-100
        if total_weight > 0:
            S = 100 * (weighted_sum / total_weight)
        else:
            S = 0.0
        
        return max(0, min(100, round(S, 1)))
    
    def evidence_score(self, resume_text: str) -> float:
        """
        Calculate evidence score E (0-100).
        Rewards skills used in context and measurable impact.
        """
        text_lower = resume_text.lower()
        
        # Action verbs near skills
        action_verbs = [
            'built', 'developed', 'implemented', 'designed', 'optimized',
            'deployed', 'migrated', 'improved', 'created', 'architected',
            'engineered', 'delivered', 'launched', 'scaled', 'enhanced'
        ]
        
        context_hits = 0
        # Look for action verbs within +/- 6 words of canonical skills
        for canonical in self.skill_dict.keys():
            canonical_lower = canonical.lower()
            # Create pattern: action verb within 6 words of skill
            found_context = False
            for verb in action_verbs:
                # Pattern: verb ... (up to 6 words) ... skill OR skill ... (up to 6 words) ... verb
                pattern1 = rf'\b{verb}\b\s+(?:\w+\s+){{0,6}}\b{re.escape(canonical_lower)}\b'
                pattern2 = rf'\b{re.escape(canonical_lower)}\b\s+(?:\w+\s+){{0,6}}\b{verb}\b'
                if re.search(pattern1, text_lower) or re.search(pattern2, text_lower):
                    found_context = True
                    break  # Count each skill once
            if found_context:
                context_hits += 1
        
        # Metrics/impact patterns
        metrics_patterns = [
            r'\d+\s*%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\s*(?:ms|milliseconds|seconds|minutes|hours)',  # Latency
            r'\d+\s*(?:users|clients|customers|requests)',  # User counts
            r'\d+x\s*(?:faster|improvement|increase)',  # Multipliers
            r'(?:reduced|increased|improved|decreased)\s+by\s+\d+',  # Impact phrases
            r'\d+\s*(?:million|billion|thousand)',  # Large numbers
        ]
        
        metrics_hits = 0
        for pattern in metrics_patterns:
            if re.search(pattern, text_lower):
                metrics_hits += 1
        
        # Calculate E: min(60, context_hits*10) + min(40, metrics_hits*10)
        context_score = min(60, context_hits * 10)
        metrics_score = min(40, metrics_hits * 10)
        E = max(0, min(100, context_score + metrics_score))
        
        return round(E, 1)
    
    def score_match(self, resume_text: str, job_text: str) -> Dict:
        """
        Calculate comprehensive ATS-like hybrid match score.
        Returns dict with score breakdown, must-have info, and matched/missing skills.
        """
        # Clean and normalize text
        resume_clean, resume_truncated = self.clean_text(resume_text)
        job_clean, job_truncated = self.clean_text(job_text)
        
        # Split resume into sections
        sections = self.split_sections(resume_clean)
        
        # Extract requirements
        must_have_skills, preferred_skills = self.extract_requirements(job_clean)
        
        # Calculate component scores
        K = self.keyword_score(resume_clean, job_clean, must_have_skills, preferred_skills)
        S = self.semantic_score(resume_clean, job_clean, sections)
        E = self.evidence_score(resume_clean)
        
        # Calculate raw score
        raw = (K * self.KEYWORD_WEIGHT) + (S * self.SEMANTIC_WEIGHT) + (E * self.EVIDENCE_WEIGHT)
        
        # Apply cap and penalty
        resume_skills = self.extract_skills(resume_clean)
        missing_must_have = must_have_skills - resume_skills
        missing_count = len(missing_must_have)
        
        cap = self.MUST_HAVE_CAP if missing_count > 0 else 100
        must_have_penalty = self.MUST_HAVE_PENALTY_PER_SKILL * missing_count
        
        final = max(0, min(100, min(raw, cap) - must_have_penalty))
        
        # Extract matched and missing skills
        all_jd_skills = self.extract_skills(job_clean)
        matched_skills = resume_skills & all_jd_skills
        missing_skills = all_jd_skills - resume_skills
        preferred_missing = preferred_skills - resume_skills
        
        # Prioritize top matches: must-have first, then preferred, then others
        top_matches = []
        must_have_matched = resume_skills & must_have_skills
        preferred_matched = resume_skills & preferred_skills
        other_matched = matched_skills - must_have_skills - preferred_skills
        
        top_matches.extend(sorted(must_have_matched, key=lambda x: (-len(x), x.lower())))
        top_matches.extend(sorted(preferred_matched, key=lambda x: (-len(x), x.lower())))
        top_matches.extend(sorted(other_matched, key=lambda x: (-len(x), x.lower())))
        top_matches = top_matches[:10]
        
        # Prioritize missing: must-have first, then preferred, then others
        missing_keywords = []
        missing_keywords.extend(sorted(missing_must_have, key=lambda x: (-len(x), x.lower())))
        missing_keywords.extend(sorted(preferred_missing, key=lambda x: (-len(x), x.lower())))
        missing_keywords.extend(sorted(missing_skills - must_have_skills - preferred_skills, key=lambda x: (-len(x), x.lower())))
        missing_keywords = missing_keywords[:10]
        
        return {
            'finalScore': round(final, 1),
            'keywordScore': K,
            'semanticScore': S,
            'evidenceScore': E,
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
    
    # Legacy methods for backward compatibility
    def calculate_match_score(self, resume_text: str, job_text: str) -> Tuple[float, Set[str], Set[str]]:
        """
        Legacy method for backward compatibility.
        Returns: (score, matched_keywords, missing_keywords)
        """
        result = self.score_match(resume_text, job_text)
        matched_set = set(result['matchedSkills'])
        missing_set = set(result['missingSkills'])
        return result['finalScore'], matched_set, missing_set
    
    def get_top_matches(self, matched_keywords: Set[str], limit: int = 10) -> List[str]:
        """Get top matching keywords, sorted by length."""
        sorted_keywords = sorted(matched_keywords, key=lambda x: (-len(x), x.lower()))
        return sorted_keywords[:limit]
    
    def get_missing_keywords(self, missing_keywords: Set[str], limit: int = 10) -> List[str]:
        """Get top missing keywords, sorted by length."""
        sorted_keywords = sorted(missing_keywords, key=lambda x: (-len(x), x.lower()))
        return sorted_keywords[:limit]
