# Hybrid ATS-like Scoring Algorithm - Implementation Summary

## What Changed

### 1. **New Hybrid Scoring Formula**
   - **Previous**: Keyword (60%) + Semantic (40%)
   - **New**: Keyword (55%) + Semantic (35%) + Evidence (10%)
   - Final score: `raw = 0.55*K + 0.35*S + 0.10*E`
   - Applied cap (70 if missing must-haves) and penalty (12 per missing must-have)

### 2. **Enhanced Text Cleaning** (`clean_text`)
   - Added de-hyphenation of line breaks (e.g., "devel-\nop" → "develop")
   - Improved header/footer removal (lines appearing ≥3 times, <80 chars)
   - Returns truncation flag for insights

### 3. **New Skills Dictionary Format** (`backend/app/skills.json`)
   - Simplified format: `{"canonical": ["alias1", "alias2"]}`
   - All keys lowercase for consistency
   - Replaces old nested structure

### 4. **Must-Have vs Preferred Extraction** (`extract_requirements`)
   - Detects must-have requirements from patterns: "required", "must have", "minimum qualifications", etc.
   - Detects preferred requirements from patterns: "preferred", "bonus", "nice to have", etc.
   - Returns separate sets for must-have and preferred skills

### 5. **Rewritten Keyword Score** (`keyword_score`)
   - **Weighted recall-style scoring**:
     - Must-have matches: weight 2.0
     - Preferred matches: weight 1.0
     - Other JD skills: weight 0.5
   - Normalized to 0-100
   - **TF-IDF adjustment**: Jaccard similarity-based adjustment (±10 points)

### 6. **Enhanced Semantic Score** (`semantic_score`)
   - Weighted combination:
     - Whole resume vs JD: 40%
     - Experience section vs JD: 40% (if present)
     - Projects section vs JD: 20% (if present)
   - Redistributes weights if sections missing

### 7. **New Evidence Score** (`evidence_score`)
   - **Context hits**: Skills appearing near action verbs (built, developed, implemented, etc.) within ±6 words
   - **Metrics hits**: Numeric impact patterns (percentages, $, latency, users, multipliers)
   - Formula: `E = min(60, context_hits*10) + min(40, metrics_hits*10)`

### 8. **Cap and Penalty Logic**
   - **Cap**: 70 if any must-have missing, else 100
   - **Penalty**: 12 points per missing must-have skill
   - Final: `clamp(min(raw, cap) - penalty, 0, 100)`

### 9. **Enhanced Response Schema**
   - Added `evidenceScore` to breakdown
   - Added `capApplied`, `mustHavePenalty`, `missingMustHaveCount`
   - Added `preferredMissing` to response
   - Added `wasTruncated` flag

### 10. **Improved Insights Generation**
   - Evidence score feedback
   - Preferred skills insights
   - Cap/penalty explanations
   - Truncation notices

## Files Modified

1. **`backend/app/scoring.py`**: Complete rewrite of scoring logic
2. **`backend/app/skills.json`**: New simplified format (replaces `skills_dict.json`)
3. **`backend/app/main.py`**: Updated to use new scoring and insights
4. **`backend/app/schemas.py`**: Added `preferredMissing` field
5. **`frontend/src/types.ts`**: Updated `ScoreBreakdown` interface
6. **`backend/tests/test_hybrid_scoring.py`**: New comprehensive test suite

## Manual Test Plan

### Test 1: Basic Scoring
**Input:**
- Resume: "Python developer with React experience. Built web apps."
- Job: "Required: Python, React. Looking for a developer."

**Expected:**
- `keywordScore` > 0 (Python and React matched)
- `semanticScore` > 0
- `evidenceScore` > 0 (action verb "Built" present)
- `finalScore` = 0.55*K + 0.35*S + 0.10*E
- No cap applied (all must-haves present)
- No penalty

### Test 2: Must-Have Penalty
**Input:**
- Resume: "Python developer"
- Job: "Required: Python, React, AWS (must have)"

**Expected:**
- `missingMustHaveCount` = 2 (React, AWS)
- `capApplied` = true
- `mustHavePenalty` = 24 (12 * 2)
- `finalScore` ≤ 70 (cap applied)
- `mustHaveMissing` contains "react" and "aws"

### Test 3: Preferred Skills
**Input:**
- Resume: "Python developer"
- Job: "Required: Python. Preferred: Docker, Kubernetes"

**Expected:**
- `preferredMissing` contains "docker" and "kubernetes"
- No cap applied (must-haves present)
- `finalScore` reflects preferred skills in keyword score

### Test 4: Evidence Score
**Input:**
- Resume: "Built Python applications. Improved performance by 50%. Served 1M users."

**Expected:**
- `evidenceScore` ≥ 30 (action verbs + metrics)
- Context hits from "Built Python"
- Metrics hits from "50%", "1M users"

### Test 5: Skill Aliases
**Input:**
- Resume: "JS, Node, Postgres developer"
- Job: "Required: JavaScript, Node.js, PostgreSQL"

**Expected:**
- Skills normalized correctly
- `matchedSkills` contains canonical names
- `topMatches` shows matched skills

### Test 6: Text Truncation
**Input:**
- Resume: "A" * 30000 (very long text)
- Job: "Python developer"

**Expected:**
- `wasTruncated` = true
- Insights mention truncation
- Scoring still works (may be less accurate)

### Test 7: Section Weighting (Semantic)
**Input:**
- Resume: "EXPERIENCE\nBuilt Python apps\nPROJECTS\nReact portfolio"
- Job: "Python and React developer"

**Expected:**
- `semanticScore` uses weighted combination
- Experience section weighted higher
- Projects section included if present

### Test 8: De-hyphenation
**Input:**
- Resume: "Developed machine learn-\ning algorithms"

**Expected:**
- Text cleaned to "machine learning" (no hyphen)
- Skills extracted correctly

## Sample API Request/Response

### Request
```json
{
  "resumeText": "SKILLS\nPython, JavaScript, React\n\nEXPERIENCE\nBuilt web applications using Python and React. Improved performance by 50%.",
  "jobText": "Required: Python, React, AWS\nPreferred: Docker\nLooking for a full-stack developer."
}
```

### Expected Response Structure
```json
{
  "score": 65.2,
  "topMatches": ["python", "react"],
  "missingKeywords": ["aws", "docker"],
  "insights": {
    "strengths": ["Strong keyword alignment (75.0/100).", "Strong alignment with required skills: python, react"],
    "improvements": ["Missing required skills: aws. Add these skills if you have experience with them.", "Evidence score is low (20.0/100). Add quantified achievements."],
    "atsTips": ["Address missing must-have requirements first.", "Show skills in context: use action verbs (built, developed, implemented) near skill names."]
  },
  "rewrittenBullets": [...],
  "scoreBreakdown": {
    "finalScore": 65.2,
    "keywordScore": 75.0,
    "semanticScore": 68.5,
    "evidenceScore": 20.0,
    "capApplied": true,
    "mustHavePenalty": 12,
    "missingMustHaveCount": 1
  },
  "mustHaveMissing": ["aws"],
  "preferredMissing": ["docker"]
}
```

## Testing Commands

```bash
# Run unit tests
cd backend
python -m pytest tests/test_hybrid_scoring.py -v

# Test specific functionality
python -m pytest tests/test_hybrid_scoring.py::test_must_have_penalty_and_cap -v

# Manual API test (with server running)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"resumeText": "Python developer", "jobText": "Required: Python, React"}'
```

## Backward Compatibility

- Legacy method `calculate_match_score()` still works
- Old response fields preserved
- New fields are optional (backward compatible)
- Frontend updated to handle new structure

## Notes

- All skill names normalized to lowercase
- Multi-word phrases matched before single tokens
- Evidence score rewards quantified achievements
- Cap and penalty ensure missing must-haves are penalized appropriately
- Explainability: detailed breakdown in `scoreBreakdown` and `insights`
