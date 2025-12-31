"""
Request/Response schemas for the ResuMate API.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class AnalyzeRequest(BaseModel):
    """Request schema for resume-job matching analysis."""
    resumeText: str = Field(..., min_length=10, max_length=50000, description="Resume text content")
    jobText: str = Field(..., min_length=10, max_length=50000, description="Job description text content")

    @field_validator('resumeText', 'jobText')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Sanitize and validate text input."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        # Remove null bytes and control characters (except newlines and tabs)
        cleaned = ''.join(char for char in v if ord(char) >= 32 or char in '\n\t')
        return cleaned.strip()


class AnalyzeResponse(BaseModel):
    """Response schema for resume-job matching analysis."""
    score: float = Field(..., ge=0, le=100, description="Match score from 0-100")
    topMatches: List[str] = Field(..., description="Top matching skills/keywords")
    missingKeywords: List[str] = Field(..., description="Missing skills/keywords from job description")
    insights: dict = Field(..., description="Analysis insights including strengths, improvements, and ATS tips")
    rewrittenBullets: List[str] = Field(..., description="Three rewritten resume bullets in FAANG style")
    # Enhanced ATS-like fields
    scoreBreakdown: Optional[dict] = Field(None, description="Detailed score breakdown with keyword, semantic, evidence scores, cap, and penalty")
    mustHaveMissing: Optional[List[str]] = Field(None, description="Must-have requirements missing from resume")
    preferredMissing: Optional[List[str]] = Field(None, description="Preferred skills missing from resume")


class UploadResumeResponse(BaseModel):
    """Response schema for resume file upload."""
    resumeText: str = Field(..., description="Extracted resume text")
    meta: dict = Field(..., description="File metadata (filename, pages, textLength)")

