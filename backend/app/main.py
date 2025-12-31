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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],  # Vite default ports
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
        # Calculate comprehensive ATS-like hybrid match score
        score_result = scorer.score_match(
            request.resumeText,
            request.jobText
        )
        
        final_score = score_result['finalScore']
        top_matches = score_result['topMatches']
        missing = score_result['missingKeywords']
        must_have_missing = score_result.get('mustHaveMissing', [])
        preferred_missing = score_result.get('preferredMissing', [])
        was_truncated = score_result.get('wasTruncated', False)
        
        # Build score breakdown
        score_breakdown = {
            'finalScore': score_result.get('finalScore', 0),
            'keywordScore': score_result.get('keywordScore', 0),
            'semanticScore': score_result.get('semanticScore', 0),
            'evidenceScore': score_result.get('evidenceScore', 0),
            'capApplied': score_result.get('capApplied', False),
            'mustHavePenalty': score_result.get('mustHavePenalty', 0),
            'missingMustHaveCount': score_result.get('missingMustHaveCount', 0)
        }
        
        # Generate insights with new data
        insights = generate_insights(
            final_score, 
            top_matches, 
            missing,
            must_have_missing,
            preferred_missing,
            score_breakdown,
            was_truncated
        )
        
        # Rewrite resume bullets
        rewritten_bullets = rewriter.rewrite_bullets(request.resumeText, count=3)
        
        return AnalyzeResponse(
            score=final_score,
            topMatches=top_matches,
            missingKeywords=missing,
            insights=insights,
            rewrittenBullets=rewritten_bullets,
            scoreBreakdown=score_breakdown,
            mustHaveMissing=must_have_missing if must_have_missing else None,
            preferredMissing=preferred_missing if preferred_missing else None
        )
    
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please check your input.")


def generate_insights(
    score: float, 
    top_matches: List[str], 
    missing: List[str],
    must_have_missing: List[str] = None,
    preferred_missing: List[str] = None,
    score_breakdown: dict = None,
    was_truncated: bool = False
) -> dict:
    """
    Generate insights based on match score, keywords, and ATS analysis.
    Returns strengths, improvements, and ATS tips.
    """
    if must_have_missing is None:
        must_have_missing = []
    if preferred_missing is None:
        preferred_missing = []
    if score_breakdown is None:
        score_breakdown = {}
    
    strengths = []
    improvements = []
    ats_tips = []
    
    # Truncation notice
    if was_truncated:
        improvements.append(
            "Note: Your resume or job description was truncated for processing. "
            "Very long documents may affect scoring accuracy."
        )
    
    # Must-have requirements insights (highest priority)
    if must_have_missing:
        improvements.append(
            f"Missing required skills: {', '.join(must_have_missing[:5])}. "
            "These are must-have requirements and will significantly limit your application. "
            "Add these skills if you have experience with them."
        )
        ats_tips.append(
            "Address missing must-have requirements first. "
            "ATS systems often reject resumes missing required qualifications."
        )
    
    # Preferred skills insights
    if preferred_missing and len(preferred_missing) > 0:
        improvements.append(
            f"Consider adding preferred skills if applicable: {', '.join(preferred_missing[:3])}. "
            "These can strengthen your application."
        )
    
    # Score-based insights
    if score >= 80:
        strengths.append("Excellent match! Your resume aligns strongly with the job requirements.")
    elif score >= 60:
        strengths.append("Good match with room for improvement.")
    else:
        improvements.append("Consider tailoring your resume more closely to the job description.")
    
    # Score breakdown insights
    keyword_score = score_breakdown.get('keywordScore', 0)
    semantic_score = score_breakdown.get('semanticScore', 0)
    evidence_score = score_breakdown.get('evidenceScore', 0)
    
    if keyword_score < 50:
        improvements.append(
            f"Keyword match is low ({keyword_score:.1f}/100). "
            "Add more relevant skills and keywords from the job description."
        )
    elif keyword_score >= 70:
        strengths.append(f"Strong keyword alignment ({keyword_score:.1f}/100).")
    
    if semantic_score < 50:
        improvements.append(
            f"Semantic similarity is low ({semantic_score:.1f}/100). "
            "Consider rephrasing your experience to better match the job description's language."
        )
    elif semantic_score >= 70:
        strengths.append(f"Strong semantic alignment ({semantic_score:.1f}/100).")
    
    if evidence_score < 30:
        improvements.append(
            f"Evidence score is low ({evidence_score:.1f}/100). "
            "Add quantified achievements and show skills used in context with action verbs."
        )
    elif evidence_score >= 60:
        strengths.append(f"Strong evidence of impact ({evidence_score:.1f}/100).")
    
    # Cap and penalty insights
    if score_breakdown.get('capApplied', False):
        improvements.append(
            f"Score capped at 70 due to missing must-have requirements. "
            f"Penalty applied: -{score_breakdown.get('mustHavePenalty', 0):.0f} points."
        )
    
    # Keyword-based insights
    if top_matches:
        must_have_matched = [m for m in top_matches if m in (must_have_missing or [])]
        if must_have_matched:
            strengths.append(f"Strong alignment with required skills: {', '.join(must_have_matched[:3])}")
        else:
            strengths.append(f"Strong alignment with key skills: {', '.join(top_matches[:5])}")
    
    if missing:
        improvements.append(f"Consider adding these skills/keywords: {', '.join(missing[:5])}")
    
    # ATS optimization tips
    ats_tips.extend([
        "Use exact keywords from the job description when possible.",
        "Include both acronyms and full forms (e.g., 'API' and 'Application Programming Interface').",
        "Use standard section headers: 'Experience', 'Education', 'Skills'.",
        "Avoid graphics, tables, or complex formatting that ATS systems can't parse.",
        "Save your resume as a .txt or .docx file for best ATS compatibility.",
        "Use standard date formats (MM/YYYY or Month YYYY).",
        "Include a 'Skills' section with relevant technical terms.",
        "Quantify achievements with numbers, percentages, and metrics.",
        "Show skills in context: use action verbs (built, developed, implemented) near skill names."
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

