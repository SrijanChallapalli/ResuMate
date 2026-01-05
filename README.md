# ResuMate AI

AI-powered Resume-Job Matching web application with ATS-like hybrid scoring. Analyzes resume text against job descriptions to provide accurate match scores, detailed breakdowns, gap detection, and optimization suggestions.

## Security Notice

**IMPORTANT**: This workspace follows high-security practices. All code should be reviewed before execution. See [SECURITY.md](./SECURITY.md) for detailed security documentation.

## Features

### Classic Mode (Default)
- **Hybrid ATS-like Match Score (0-100)**: Combines Keyword Score (55%), Semantic Score (35%), and Evidence Score (10%)
- **Must-Have vs Preferred Detection**: Automatically identifies required vs. preferred skills from job descriptions
- **Cap & Penalty System**: Applies score cap (70) and penalty (12 per skill) for missing must-have requirements
- **Detailed Score Breakdown**: Shows keyword, semantic, and evidence scores with section-level insights
- **Top Matching Keywords**: Identifies skills and keywords that match (with canonical skill normalization)
- **Missing Requirements**: Highlights must-have and preferred skills missing from your resume
- **Evidence Scoring**: Rewards skills used in context (near action verbs) and quantifiable achievements
- **File Upload Support**: Upload PDF or DOCX resumes directly (in addition to text paste)
- **Rewritten Resume Bullets**: Generates 3 FAANG-style resume bullets (deterministic, no LLMs)
- **ATS Optimization Tips**: Actionable advice for Applicant Tracking System compatibility

### Premium Mode (Beta)
- **Industry-Standard Ranking Pipeline**: BM25 keyword scoring (35%) + Semantic Retrieval (35%) + Cross-Encoder Reranking (20%) + Evidence (10%)
- **BM25 Keyword Scoring**: Local probabilistic ranking function for keyword matching
- **Cross-Encoder Reranking**: Fine-grained relevance scoring using cross-encoder/ms-marco-MiniLM-L-6-v2
- **Sigmoid Calibration**: Stabilizes 0-100 scores after penalties for more interpretable results
- **Same Cap & Penalty Logic**: Uses identical must-have detection and penalty system as Classic mode
- **Enhanced Breakdown**: Shows BM25, semantic retrieval, rerank, evidence, raw, constrained, and calibrated scores
- **All Classic Features**: File upload, rewritten bullets, insights, and ATS tips included

## Tech Stack

### Backend
- Python 3.9+ (tested with Python 3.13)
- FastAPI
- sentence-transformers (local models: `all-MiniLM-L6-v2` for bi-encoder, `cross-encoder/ms-marco-MiniLM-L-6-v2` for reranking)
- rank-bm25 (BM25 keyword scoring)
- pypdf & python-docx (for PDF/DOCX file extraction)
- No external APIs, all processing is local

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Vite

## Project Structure

```
ResuMate/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── schemas.py       # Request/Response models
│   │   ├── scoring.py       # Classic hybrid ATS-like scoring algorithm
│   │   ├── premium_scoring/ # Premium ranking pipeline
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py  # Premium scoring orchestrator
│   │   │   ├── bm25.py      # BM25 keyword scoring
│   │   │   ├── reranker.py  # Cross-encoder reranking
│   │   │   └── calibration.py # Sigmoid calibration
│   │   ├── rewrite.py       # Resume bullet rewriting
│   │   ├── file_extractor.py # PDF/DOCX text extraction
│   │   └── skills.json      # Canonical skills dictionary with aliases
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_scoring.py  # Legacy scoring tests
│   │   ├── test_hybrid_scoring.py # Hybrid scoring tests
│   │   ├── test_ats_scoring.py    # ATS-specific tests
│   │   └── test_premium_scoring.py # Premium scoring tests
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── main.tsx
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── index.css
│   │   ├── App.css
│   │   └── components/
│   │       └── reactbits/   # UI components (AnimatedBackground, FolderUpload, etc.)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── SECURITY.md
├── README.md
└── HYBRID_SCORING_CHANGES.md # Detailed algorithm documentation
```

## Manual Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Node.js 18+ and npm
- 2GB+ free disk space (for ML model download)

### Backend Setup

1. **Navigate to backend directory:**
   ```powershell
   cd backend
   ```

2. **Create a virtual environment (recommended):**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

   **Note**: This will download the sentence-transformers model (~90MB) on first run. This is a one-time download.

5. **Optional: Create .env file (copy from .env.example):**
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` if you need to change the default host/port.

6. **Run the backend server:**
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be available at `http://localhost:8000`

7. **Verify the backend is running:**
   ```powershell
   curl http://localhost:8000/health
   ```

### Frontend Setup

1. **Open a new terminal and navigate to frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Start the development server:**
   ```powershell
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

### Running Tests

**Backend tests:**
```powershell
cd backend
pytest
```

## Usage

1. Start both backend and frontend servers (see setup instructions above)
2. Open `http://localhost:5173` in your browser
3. **Choose Analysis Mode**: Use the tabs in the navbar to switch between "Classic" and "Premium (Beta)"
4. **Option A: Upload Resume File**
   - Click "Choose File" or drag-and-drop a PDF or DOCX resume
   - Paste the job description in the textarea
   - Click "Analyze Match"
5. **Option B: Paste Text**
   - Paste your resume text in the left textarea
   - Paste the job description in the right textarea
   - Click "Analyze Match"
6. Review the results:
   - **Classic Mode**: Match score (0-100) with breakdown:
     - Keyword Score (55%): Weighted skill matching with must-have/preferred detection
     - Semantic Score (35%): Section-weighted embedding similarity
     - Evidence Score (10%): Skills in context + quantifiable achievements
   - **Premium Mode**: Match score (0-100) with enhanced breakdown:
     - BM25 Score (35%): Probabilistic keyword ranking
     - Semantic Retrieval Score (35%): Bi-encoder similarity
     - Cross-Encoder Rerank Score (20%): Fine-grained relevance
     - Evidence Score (10%): Skills in context + quantifiable achievements
     - Calibrated Score: Sigmoid-calibrated final score
   - **Both Modes Include**:
     - Top matching keywords: Canonical skill names that matched
     - Missing requirements: Must-have and preferred skills not in resume
     - Score penalties: Cap (70) and penalty (12 per skill) for missing must-haves
     - Insights and ATS tips: Actionable feedback
     - Rewritten resume bullets: 3 FAANG-style bullets

## Example API Requests

### Classic Mode

**Text Analysis:**
```powershell
curl -X POST "http://localhost:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{
    "resumeText": "SKILLS\nPython, JavaScript, React\n\nEXPERIENCE\nBuilt web applications using Python and React. Improved performance by 50%.",
    "jobText": "Required: Python, React, AWS\nPreferred: Docker\nLooking for a full-stack developer."
  }'
```

**File Upload:**
```powershell
curl -X POST "http://localhost:8000/api/upload-resume" `
  -F "file=@resume.pdf"
```

### Premium Mode (Beta)

**Text Analysis:**
```powershell
curl -X POST "http://localhost:8000/api/analyze-premium" `
  -H "Content-Type: application/json" `
  -d '{
    "resumeText": "SKILLS\nPython, JavaScript, React\n\nEXPERIENCE\nBuilt web applications using Python and React. Improved performance by 50%.",
    "jobText": "Required: Python, React, AWS\nPreferred: Docker\nLooking for a full-stack developer."
  }'
```

**File Upload:**
```powershell
curl -X POST "http://localhost:8000/api/upload-resume-premium" `
  -F "file=@resume.pdf"
```

### Response Structure

**Classic Mode Response:**
```json
{
  "score": 65.2,
  "topMatches": ["python", "react"],
  "missingKeywords": ["aws", "docker"],
  "mustHaveMissing": ["aws"],
  "preferredMissing": ["docker"],
  "scoreBreakdown": {
    "finalScore": 65.2,
    "keywordScore": 75.0,
    "semanticScore": 68.5,
    "evidenceScore": 20.0,
    "capApplied": true,
    "mustHavePenalty": 12,
    "missingMustHaveCount": 1
  },
  "insights": {
    "strengths": ["Strong keyword alignment (75.0/100).", "Strong alignment with required skills: python, react"],
    "improvements": ["Missing required skills: aws. Add these skills if you have experience with them.", "Evidence score is low (20.0/100). Add quantified achievements."],
    "atsTips": ["Address missing must-have requirements first.", "Show skills in context: use action verbs (built, developed, implemented) near skill names."]
  },
  "rewrittenBullets": [...]
}
```

**Premium Mode Response:**
```json
{
  "score": 67.8,
  "topMatches": ["python", "react"],
  "missingKeywords": ["aws", "docker"],
  "mustHaveMissing": ["aws"],
  "preferredMissing": ["docker"],
  "premiumBreakdown": {
    "bm25Score": 72.5,
    "semanticRetrievalScore": 70.2,
    "rerankScore": 65.0,
    "evidenceScore": 20.0,
    "calibratedScore": 67.8,
    "rawScore": 68.5,
    "constrainedScore": 56.5,
    "capApplied": true,
    "mustHavePenalty": 12,
    "missingMustHaveCount": 1
  },
  "insights": {...},
  "rewrittenBullets": [...],
  "wasTruncated": false
}
```

## How It Works

### Classic Mode: Hybrid ATS-like Scoring Algorithm

The classic scoring system uses a three-component hybrid approach designed to mimic real ATS behavior:

1. **Keyword Score (K) - 55%**
   - Weighted recall-style scoring:
     - Must-have skills: weight 2.0
     - Preferred skills: weight 1.0
     - Other job skills: weight 0.5
   - TF-IDF adjustment (±10 points) based on Jaccard similarity
   - Uses canonical skill dictionary with alias matching (e.g., "JS" → "javascript", "Node" → "node.js")
   - Normalized to 0-100

2. **Semantic Score (S) - 35%**
   - Section-weighted cosine similarity using sentence-transformers:
     - Whole resume vs JD: 40%
     - Experience section vs JD: 40% (if present)
     - Projects section vs JD: 20% (if present)
   - Weights redistribute if sections are missing
   - Uses local `all-MiniLM-L6-v2` model (no external API calls)

3. **Evidence Score (E) - 10%**
   - **Context hits (60 max)**: Skills appearing near action verbs (built, developed, implemented, etc.) within ±6 words
   - **Metrics hits (40 max)**: Numeric impact patterns (percentages, $, latency, users, multipliers)
   - Formula: `E = min(60, context_hits*10) + min(40, metrics_hits*10)`

4. **Final Score Calculation**
   - Raw score: `0.55*K + 0.35*S + 0.10*E`
   - **Cap**: 70 if any must-have skill is missing, else 100
   - **Penalty**: 12 points per missing must-have skill
   - Final: `clamp(min(raw, cap) - penalty, 0, 100)`

### Text Processing

- **Text Normalization**: De-hyphenation, whitespace normalization, bullet character standardization
- **Section Detection**: Automatically parses SKILLS, EXPERIENCE, PROJECTS, EDUCATION, CERTIFICATIONS sections
- **Skill Extraction**: Uses curated dictionary (`skills.json`) with 50+ canonical skills and aliases
- **Requirement Extraction**: Detects must-have vs. preferred skills from job descriptions using pattern matching

### Must-Have vs Preferred Detection

The system automatically identifies:
- **Must-have requirements**: Patterns like "required", "must have", "minimum qualifications", "essential"
- **Preferred requirements**: Patterns like "preferred", "bonus", "nice to have", "pluses"

### Rewriting Engine

The rewriting engine is **deterministic** and uses:
- Template-based verb strengthening (replaces weak verbs with strong action verbs)
- Quantification placeholders (adds impact statements if missing)
- FAANG-style formatting

**No LLMs are used** - all rewriting is rule-based.

### Premium Mode: Industry-Standard Ranking Pipeline

The premium mode uses a four-component ranking pipeline with cross-encoder reranking and sigmoid calibration:

1. **BM25 Keyword Score (35%)**
   - Probabilistic ranking function using rank-bm25
   - Considers term frequency (TF) and inverse document frequency (IDF)
   - Document length normalization
   - Normalized to 0-100 using sigmoid transformation

2. **Semantic Retrieval Score (35%)**
   - Same bi-encoder approach as Classic mode
   - Section-weighted cosine similarity using `all-MiniLM-L6-v2`
   - Whole resume (40%) + Experience (40%) + Projects (20%)

3. **Cross-Encoder Reranking Score (20%)**
   - Fine-grained relevance scoring using `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Reranks top K snippets (K=5) from Experience/Projects sections
   - Falls back to whole resume chunks if sections are empty
   - Normalized to 0-100

4. **Evidence Score (10%)**
   - Reuses same evidence logic as Classic mode
   - Skills in context + quantifiable achievements

5. **Score Combination & Calibration**
   - Raw score: `0.35*BM25 + 0.35*Semantic + 0.20*Rerank + 0.10*Evidence`
   - **Cap**: 70 if any must-have missing, else 100 (same as Classic)
   - **Penalty**: 12 points per missing must-have (same as Classic)
   - Constrained: `clamp(min(raw, cap) - penalty, 0, 100)`
   - **Sigmoid Calibration**: `100 / (1 + exp(-0.08 * (constrained - 50)))`
   - Final score: Calibrated score

The premium pipeline provides more sophisticated ranking while maintaining the same must-have detection and penalty logic as Classic mode.

## Security Considerations

- All processing happens locally (no data sent to external services)
- No persistent storage (data is processed in-memory and discarded)
- Input validation and sanitization on all user inputs
- CORS configured for local development only
- See [SECURITY.md](./SECURITY.md) for detailed threat model

## Troubleshooting

### Backend Issues

- **Model download fails**: Check internet connection. The model downloads automatically on first import (~90MB).
- **Port already in use**: Change the port in the uvicorn command or `.env` file
- **Import errors**: Ensure virtual environment is activated and dependencies are installed
- **File upload fails**: Ensure `python-multipart` is installed (`pip install python-multipart`)
- **PDF/DOCX extraction fails**: Ensure `pypdf` and `python-docx` are installed
- **Premium mode fails**: Ensure `rank-bm25` is installed (`pip install rank-bm25>=0.2.2`)
- **Python 3.13 compatibility**: If you encounter `distutils` errors, ensure you're using updated package versions from `requirements.txt`

### Frontend Issues

- **Cannot connect to backend**: Ensure backend is running on `http://localhost:8000`
- **CORS errors**: Check that backend CORS middleware allows `http://localhost:5173`
- **Build errors**: Delete `node_modules` and re-run `npm install`

## Development Notes

- Backend uses FastAPI with automatic API documentation at `http://localhost:8000/docs`
- Frontend uses Vite for fast hot-reload development
- All dependencies are pinned to exact versions for security
- No postinstall scripts or auto-execution hooks
- Skills dictionary (`backend/app/skills.json`) can be extended with new skills and aliases
- See [HYBRID_SCORING_CHANGES.md](./HYBRID_SCORING_CHANGES.md) for detailed algorithm documentation

## Testing

Run the comprehensive test suite:

```powershell
cd backend
pytest tests/test_hybrid_scoring.py -v
pytest tests/test_ats_scoring.py -v
pytest tests/test_file_extractor.py -v
pytest tests/test_premium_scoring.py -v
```

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, review the code and security documentation. All execution must be manual and explicit.

