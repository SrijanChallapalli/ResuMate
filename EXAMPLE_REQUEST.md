# Example API Requests

## Using curl (PowerShell)

### Basic Analysis Request

```powershell
curl -X POST "http://localhost:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{
    "resumeText": "Software engineer with 5 years of Python and JavaScript experience. Built web applications using React and Node.js. Led a team of 3 developers to deliver a scalable microservices architecture.",
    "jobText": "Seeking a Python developer with React experience. Must have web development skills, API design knowledge, and experience with microservices. Leadership experience preferred."
  }'
```

### Using Invoke-WebRequest (PowerShell Alternative)

```powershell
$body = @{
    resumeText = "Software engineer with 5 years of Python and JavaScript experience. Built web applications using React and Node.js."
    jobText = "Seeking a Python developer with React experience. Must have web development skills and API design knowledge."
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

## Expected Response

```json
{
  "score": 75.5,
  "topMatches": [
    "python",
    "javascript",
    "react",
    "developer",
    "web",
    "applications"
  ],
  "missingKeywords": [
    "api",
    "design",
    "microservices"
  ],
  "insights": {
    "strengths": [
      "Good match with room for improvement.",
      "Strong alignment with key terms: python, javascript, react, developer, web"
    ],
    "improvements": [
      "Consider adding these keywords: api, design, microservices"
    ],
    "atsTips": [
      "Use exact keywords from the job description when possible.",
      "Include both acronyms and full forms (e.g., 'API' and 'Application Programming Interface').",
      "..."
    ]
  },
  "rewrittenBullets": [
    "Developed scalable web applications using React and Node.js, delivering measurable impact.",
    "Led cross-functional development initiatives, resulting in improved performance.",
    "Built high-performance systems, enabling scalable solutions."
  ]
}
```

## Health Check

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

