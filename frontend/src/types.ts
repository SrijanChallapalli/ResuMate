/**
 * Shared TypeScript types for ResuMate AI
 */

export interface AnalysisResult {
  score: number
  topMatches: string[]
  missingKeywords: string[]
  insights: {
    strengths: string[]
    improvements: string[]
    atsTips: string[]
  }
  rewrittenBullets: string[]
  // New ATS-like fields (optional for backward compatibility)
  scoreBreakdown?: {
    finalScore: number
    keywordScore: number
    semanticScore: number
    evidenceScore: number
    capApplied: boolean
    mustHavePenalty: number
    missingMustHaveCount: number
  }
  mustHaveMissing?: string[]
  preferredMissing?: string[]
}

export interface UploadResumeResponse {
  resumeText: string
  meta: {
    filename: string
    pages?: number
    textLength: number
  }
}

export interface ScoreBreakdown {
  semantic: number  // 60% weight
  keywords: number  // 40% weight
}

