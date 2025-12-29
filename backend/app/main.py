"""
FastAPI application for ResuMate AI.
Provides resume-job matching analysis endpoint.
"""
import os
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from app.schemas import AnalyzeRequest, AnalyzeResponse, UploadResumeResponse
from app.scoring import ResumeScorer
from app.rewrite import ResumeRewriter
from app.file_extractor import FileExtractor

# Initialize FastAPI app
app = FastAPI(
    title="ResuMate AI API",
    description="AI-powered resume-job matching service",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and processors (loaded once at startup)
model: SentenceTransformer = None
scorer: ResumeScorer = None
rewriter: ResumeRewriter = None


@app.on_event("startup")
async def startup_event():
    """Load ML model and initialize processors on startup."""
    global model, scorer, rewriter
    
    try:
        # Load sentence transformer model (local, no external API)
        print("Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully.")
        
        scorer = ResumeScorer(model)
        rewriter = ResumeRewriter()
        
    except Exception as e:
        print(f"Error loading model: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ResuMate AI",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


@app.post("/api/upload-resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and extract text from resume file (PDF, DOCX, or TXT).
    
    Returns extracted text and metadata.
    """
    try:
        # Log request details (without file content)
        filename = file.filename or "unknown"
        content_type = file.content_type or "unknown"
        print(f"[UPLOAD] Route hit: /api/upload-resume")
        print(f"[UPLOAD] Filename: {filename}, Content-Type: {content_type}")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        print(f"[UPLOAD] File size: {file_size} bytes")
        
        # Handle missing filename (can happen with drag-drop)
        if not file.filename:
            # Try to infer from content-type or use default
            if content_type == "application/pdf":
                filename = "resume.pdf"
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                filename = "resume.docx"
            elif content_type == "text/plain":
                filename = "resume.txt"
            else:
                filename = "resume.txt"  # Default fallback
            print(f"[UPLOAD] Filename was None, using inferred: {filename}")
        
        # Validate file
        is_valid, error_msg = FileExtractor.validate_file(filename, file_size)
        if not is_valid:
            print(f"[UPLOAD] Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Extract text
        try:
            print(f"[UPLOAD] Extracting text from {filename}")
            extracted_text, meta = FileExtractor.extract_text(file_content, filename)
            print(f"[UPLOAD] Extraction successful. Text length: {len(extracted_text)} chars")
        except ValueError as e:
            print(f"[UPLOAD] Extraction ValueError: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"[UPLOAD] Extraction error: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract text from file. Please try a different file format.")
        
        return UploadResumeResponse(
            resumeText=extracted_text,
            meta=meta
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD] Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="File upload failed. Please try again.")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_resume_job(request: AnalyzeRequest):
    """
    Analyze resume-job match.
    
    Returns:
    - Match score (0-100)
    - Top matching keywords
    - Missing keywords
    - Insights (strengths, improvements, ATS tips)
    - Rewritten resume bullets
    """
    if not model or not scorer or not rewriter:
        raise HTTPException(status_code=503, detail="Model not loaded. Please wait for startup.")
    
    try:
        # Calculate match score
        score, matched_keywords, missing_keywords = scorer.calculate_match_score(
            request.resumeText,
            request.jobText
        )
        
        # Get top matches and missing keywords
        top_matches = scorer.get_top_matches(matched_keywords, limit=10)
        missing = scorer.get_missing_keywords(missing_keywords, limit=10)
        
        # Generate insights
        insights = generate_insights(score, top_matches, missing)
        
        # Rewrite resume bullets
        rewritten_bullets = rewriter.rewrite_bullets(request.resumeText, count=3)
        
        return AnalyzeResponse(
            score=round(score, 1),
            topMatches=top_matches,
            missingKeywords=missing,
            insights=insights,
            rewrittenBullets=rewritten_bullets
        )
    
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please check your input.")


def generate_insights(score: float, top_matches: List[str], missing: List[str]) -> dict:
    """
    Generate insights based on match score and keywords.
    Returns strengths, improvements, and ATS tips.
    """
    strengths = []
    improvements = []
    ats_tips = []
    
    # Score-based insights
    if score >= 80:
        strengths.append("Excellent match! Your resume aligns strongly with the job requirements.")
    elif score >= 60:
        strengths.append("Good match with room for improvement.")
    else:
        improvements.append("Consider tailoring your resume more closely to the job description.")
    
    # Keyword-based insights
    if top_matches:
        strengths.append(f"Strong alignment with key terms: {', '.join(top_matches[:5])}")
    
    if missing:
        improvements.append(f"Consider adding these keywords: {', '.join(missing[:5])}")
    
    # ATS optimization tips
    ats_tips.extend([
        "Use exact keywords from the job description when possible.",
        "Include both acronyms and full forms (e.g., 'API' and 'Application Programming Interface').",
        "Use standard section headers: 'Experience', 'Education', 'Skills'.",
        "Avoid graphics, tables, or complex formatting that ATS systems can't parse.",
        "Save your resume as a .txt or .docx file for best ATS compatibility.",
        "Use standard date formats (MM/YYYY or Month YYYY).",
        "Include a 'Skills' section with relevant technical terms.",
        "Quantify achievements with numbers, percentages, and metrics."
    ])
    
    # Additional score-specific tips
    if score < 50:
        ats_tips.append("Consider a complete resume rewrite to better match the job description.")
    elif score < 70:
        ats_tips.append("Add more relevant keywords and skills from the job description.")
    
    return {
        "strengths": strengths,
        "improvements": improvements,
        "atsTips": ats_tips
    }

