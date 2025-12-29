# ResuMate AI

AI-powered Resume-Job Matching web application. Analyzes resume text against job descriptions to provide match scores, keyword analysis, and optimization suggestions.

## Security Notice

**IMPORTANT**: This workspace follows high-security practices. All code should be reviewed before execution. See [SECURITY.md](./SECURITY.md) for detailed security documentation.

## Features

- **Match Score (0-100)**: Combines embedding similarity (60%) and keyword overlap (40%)
- **Top Matching Keywords**: Identifies skills and keywords that match
- **Missing Keywords**: Highlights important keywords from the job description not in your resume
- **Rewritten Resume Bullets**: Generates 3 FAANG-style resume bullets (deterministic, no LLMs)
- **ATS Optimization Tips**: Actionable advice for Applicant Tracking System compatibility

## Tech Stack

### Backend
- Python 3.9+
- FastAPI
- sentence-transformers (local model: `all-MiniLM-L6-v2`)
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
│   │   ├── scoring.py       # Match scoring logic
│   │   └── rewrite.py       # Resume bullet rewriting
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_scoring.py  # Unit tests
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── main.tsx
│   │   ├── index.css
│   │   └── App.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── SECURITY.md
└── README.md
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
3. Paste your resume text in the left textarea
4. Paste the job description in the right textarea
5. Click "Analyze Match"
6. Review the results:
   - Match score (0-100)
   - Top matching keywords
   - Missing keywords
   - Insights and ATS tips
   - Rewritten resume bullets

## Example API Request

You can also use the API directly with curl:

```powershell
curl -X POST "http://localhost:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{
    "resumeText": "Software engineer with 5 years of Python and JavaScript experience. Built web applications using React and Node.js.",
    "jobText": "Seeking a Python developer with React experience. Must have web development skills and API design knowledge."
  }'
```

## How It Works

### Scoring Algorithm

1. **Embedding Similarity (60%)**: Uses sentence-transformers to create semantic embeddings of both texts and calculates cosine similarity
2. **Keyword Overlap (40%)**: Extracts keywords from both texts, filters stop words, and calculates Jaccard similarity + coverage

### Rewriting Engine

The rewriting engine is **deterministic** and uses:
- Template-based verb strengthening (replaces weak verbs with strong action verbs)
- Quantification placeholders (adds impact statements if missing)
- FAANG-style formatting

**No LLMs are used** - all rewriting is rule-based.

## Security Considerations

- All processing happens locally (no data sent to external services)
- No persistent storage (data is processed in-memory and discarded)
- Input validation and sanitization on all user inputs
- CORS configured for local development only
- See [SECURITY.md](./SECURITY.md) for detailed threat model

## Troubleshooting

### Backend Issues

- **Model download fails**: Check internet connection. The model downloads automatically on first import.
- **Port already in use**: Change the port in the uvicorn command or `.env` file
- **Import errors**: Ensure virtual environment is activated and dependencies are installed

### Frontend Issues

- **Cannot connect to backend**: Ensure backend is running on `http://localhost:8000`
- **CORS errors**: Check that backend CORS middleware allows `http://localhost:5173`
- **Build errors**: Delete `node_modules` and re-run `npm install`

## Development Notes

- Backend uses FastAPI with automatic API documentation at `http://localhost:8000/docs`
- Frontend uses Vite for fast hot-reload development
- All dependencies are pinned to exact versions for security
- No postinstall scripts or auto-execution hooks

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, review the code and security documentation. All execution must be manual and explicit.

