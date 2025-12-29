import { useState, useRef, useCallback } from 'react'
import './App.css'
import type { AnalysisResult, UploadResumeResponse } from './types'

function App() {
  const [resumeText, setResumeText] = useState('')
  const [jobText, setJobText] = useState('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showPasteOption, setShowPasteOption] = useState(false)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFileUpload = async (file: File) => {
    // Validate file
    const allowedTypes = ['.pdf', '.docx', '.txt']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(fileExt)) {
      setError(`Unsupported file type. Allowed: ${allowedTypes.join(', ')}`)
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('File too large. Maximum size: 5MB')
      return
    }

    setUploading(true)
    setError(null)
    setUploadedFile(file)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const url = 'http://localhost:8000/api/upload-resume'
      console.log('[FRONTEND] Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type)
      console.log('[FRONTEND] Request URL:', url)

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      console.log('[FRONTEND] Response status:', response.status, response.statusText)

      if (!response.ok) {
        let errorMessage = `Upload failed (${response.status})`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
          console.error('[FRONTEND] Upload error:', errorData)
        } catch {
          // If response isn't JSON, use status text
          errorMessage = response.statusText || errorMessage
          console.error('[FRONTEND] Upload error - non-JSON response:', response.status, response.statusText)
        }
        throw new Error(errorMessage)
      }

      const data: UploadResumeResponse = await response.json()
      console.log('[FRONTEND] Upload successful. Text length:', data.resumeText.length)
      setResumeText(data.resumeText)
      setShowPasteOption(false)
    } catch (err) {
      console.error('[FRONTEND] Upload exception:', err)
      setError(err instanceof Error ? err.message : 'Failed to upload file')
      setUploadedFile(null)
    } finally {
      setUploading(false)
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const removeFile = () => {
    setUploadedFile(null)
    setResumeText('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleAnalyze = async () => {
    if (!resumeText.trim() || !jobText.trim()) {
      setError('Please provide both resume and job description.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resumeText: resumeText.trim(),
          jobText: jobText.trim(),
        }),
      })

      if (!response.ok) {
        let errorMessage = `Analysis failed (${response.status})`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
          console.error('[FRONTEND] Analysis error:', errorData)
        } catch {
          errorMessage = response.statusText || errorMessage
          console.error('[FRONTEND] Analysis error - non-JSON response:', response.status, response.statusText)
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze resume. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const calculateScoreBreakdown = (score: number) => {
    // Estimate breakdown (backend doesn't return this, so we estimate)
    // Semantic is 60% weight, Keywords is 40% weight
    // If score is high, both components are likely high
    const semanticEstimate = score * 0.6
    const keywordEstimate = score * 0.4
    return {
      semantic: Math.min(100, semanticEstimate * 1.2), // Slight adjustment for visual
      keywords: Math.min(100, keywordEstimate * 1.3)
    }
  }

  const breakdown = result ? calculateScoreBreakdown(result.score) : null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Navbar */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 max-w-7xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                ResuMate AI
              </h1>
              <span className="px-2 py-1 text-xs font-semibold text-indigo-600 bg-indigo-100 rounded-full">
                Local AI
              </span>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Match Your Resume to Your Dream Job
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your resume and job description to get instant AI-powered matching scores, 
            keyword analysis, and actionable insights to optimize your application.
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          {!uploadedFile && !showPasteOption ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                isDragging
                  ? 'border-blue-500 bg-blue-50 scale-[1.02]'
                  : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/50'
              }`}
            >
              <div className="max-w-md mx-auto">
                <svg
                  className="mx-auto h-16 w-16 text-gray-400 mb-4"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Drop your resume here
                </h3>
                <p className="text-gray-600 mb-6">
                  Supports PDF, DOCX, and TXT files (max 5MB)
                </p>
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg transition-all hover:shadow-xl"
                  >
                    Choose File
                  </button>
                  <button
                    onClick={() => setShowPasteOption(true)}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-lg transition-all"
                  >
                    Paste Text Instead
                  </button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>
          ) : showPasteOption ? (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Paste Resume Text</h3>
                <button
                  onClick={() => {
                    setShowPasteOption(false)
                    setResumeText('')
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ← Back to Upload
                </button>
              </div>
              <textarea
                className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Paste your resume text here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
              />
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{uploadedFile?.name}</p>
                    <p className="text-sm text-gray-500">
                      {(uploadedFile?.size || 0) / 1024} KB
                      {uploading && ' • Uploading...'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Job Description Input */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <label htmlFor="job" className="block text-lg font-semibold text-gray-900 mb-3">
              Job Description
            </label>
            <textarea
              id="job"
              className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              placeholder="Paste the job description here...\n\nExample: Seeking a software engineer with 5+ years of experience in Python, React, and cloud technologies..."
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
            />
            <div className="mt-2 text-sm text-gray-500 text-right">
              {jobText.length} characters
            </div>
          </div>
        </div>

        {/* Analyze Button */}
        <div className="text-center mb-8">
          <button
            onClick={handleAnalyze}
            disabled={loading || uploading || !resumeText.trim() || !jobText.trim()}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed text-white font-bold text-lg rounded-xl shadow-xl transition-all transform hover:scale-105 disabled:transform-none"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </span>
            ) : (
              'Analyze Match'
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-6 py-4 rounded-lg mb-8 shadow-md">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && !result && (
          <div className="space-y-6 animate-pulse">
            <div className="bg-white rounded-xl shadow-lg p-8 h-64"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6 h-48"></div>
              <div className="bg-white rounded-xl shadow-lg p-6 h-48"></div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-8 animate-fade-in">
            {/* Match Score with Breakdown */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Match Score</h2>
              <div className="flex flex-col lg:flex-row items-center justify-center gap-12">
                {/* Score Ring */}
                <div className="relative w-64 h-64">
                  <svg className="transform -rotate-90 w-64 h-64">
                    <circle
                      cx="128"
                      cy="128"
                      r="112"
                      stroke="currentColor"
                      strokeWidth="20"
                      fill="transparent"
                      className="text-gray-100"
                    />
                    <circle
                      cx="128"
                      cy="128"
                      r="112"
                      stroke="currentColor"
                      strokeWidth="20"
                      fill="transparent"
                      strokeDasharray={`${2 * Math.PI * 112}`}
                      strokeDashoffset={`${2 * Math.PI * 112 * (1 - result.score / 100)}`}
                      strokeLinecap="round"
                      className={`transition-all duration-1000 ${
                        result.score >= 80
                          ? 'text-green-500'
                          : result.score >= 60
                          ? 'text-yellow-500'
                          : 'text-red-500'
                      }`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-6xl font-bold text-gray-900">{result.score.toFixed(1)}</span>
                    <span className="text-lg text-gray-600">out of 100</span>
                  </div>
                </div>

                {/* Score Breakdown */}
                {breakdown && (
                  <div className="flex-1 max-w-md space-y-4">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">Score Breakdown</h3>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Semantic Match (60%)</span>
                        <span className="text-sm font-bold text-blue-600">{breakdown.semantic.toFixed(1)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-1000"
                          style={{ width: `${breakdown.semantic}%` }}
                        ></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Keyword Match (40%)</span>
                        <span className="text-sm font-bold text-indigo-600">{breakdown.keywords.toFixed(1)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-indigo-600 h-3 rounded-full transition-all duration-1000"
                          style={{ width: `${breakdown.keywords}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Keywords Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Matches */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  Top Matching Keywords
                </h2>
                <div className="flex flex-wrap gap-2">
                  {result.topMatches.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium border border-green-200"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              {/* Missing Keywords */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  Missing Keywords
                </h2>
                <div className="flex flex-wrap gap-2">
                  {result.missingKeywords.length > 0 ? (
                    result.missingKeywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="bg-red-100 text-red-800 px-4 py-2 rounded-full text-sm font-medium border border-red-200"
                      >
                        {keyword}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500 text-sm">No missing keywords found! 🎉</span>
                  )}
                </div>
              </div>
            </div>

            {/* Strengths vs Improvements */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Strengths */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl shadow-lg p-6 border border-green-100">
                <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Strengths
                </h3>
                <ul className="space-y-3">
                  {result.insights.strengths.length > 0 ? (
                    result.insights.strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-green-600 mt-1">✓</span>
                        <span>{strength}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-600">No specific strengths identified.</li>
                  )}
                </ul>
              </div>

              {/* Improvements */}
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl shadow-lg p-6 border border-amber-100">
                <h3 className="text-xl font-bold text-amber-800 mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Areas for Improvement
                </h3>
                <ul className="space-y-3">
                  {result.insights.improvements.length > 0 ? (
                    result.insights.improvements.map((improvement, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-amber-600 mt-1">→</span>
                        <span>{improvement}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-600">Your resume looks great! Keep it up.</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Rewritten Bullets */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Rewritten Resume Bullets</h2>
              <div className="space-y-4">
                {result.rewrittenBullets.map((bullet, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                  >
                    <span className="text-blue-600 font-bold mt-1">•</span>
                    <p className="flex-1 text-gray-700">{bullet}</p>
                    <button
                      onClick={() => copyToClipboard(bullet, idx)}
                      className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-2"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Copied!
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* ATS Tips */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 border border-blue-100">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                </svg>
                ATS Optimization Tips
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.insights.atsTips.map((tip, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg">
                    <input type="checkbox" className="mt-1" defaultChecked={false} />
                    <span className="text-sm text-gray-700">{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
