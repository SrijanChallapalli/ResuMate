# Security Documentation - ResuMate AI

## Threat Model Checklist

### Attack Surface Analysis

#### 1. Input Validation & Injection
- **Risk**: User-provided resume/job text and uploaded files may contain malicious payloads
- **Mitigation**: 
  - Text input truncation limits (max 50KB per field)
  - File upload restrictions: PDF and DOCX only, max 10MB
  - File type validation via content-type and file extension
  - No code execution on user input
  - Sanitize output to prevent XSS
  - File extraction uses safe libraries (pypdf, python-docx) with input validation

#### 2. Trust Boundaries
- **Frontend ↔ Backend**: API communication over HTTP (local dev) / HTTPS (production)
- **Backend ↔ ML Model**: Local sentence-transformers, no external API calls
- **File Upload**: Multipart form data handled by FastAPI with python-multipart
- **File Extraction**: PDF/DOCX text extraction happens in-memory, files not saved to disk
- **No External Services**: All processing happens locally
- **No Database**: Stateless API, no persistent storage of user data
- **No File Storage**: Uploaded files are processed and discarded immediately

#### 3. Dependency Risks
- **Python Dependencies**: 
  - FastAPI (well-audited, widely used)
  - sentence-transformers (HuggingFace, reputable)
  - rank-bm25 (BM25 keyword scoring, well-maintained)
  - pypdf (PDF parsing, well-maintained)
  - python-docx (DOCX parsing, well-maintained)
  - python-multipart (FastAPI file upload support)
  - Exact version pinning in requirements.txt
- **Node Dependencies**:
  - React, TypeScript, Vite (standard tooling)
  - Tailwind CSS (CSS framework, no runtime risk)
  - Version pinning in package.json
- **Supply Chain**: No obscure packages, no remote install scripts
- **File Parsing Libraries**: pypdf and python-docx are standard, well-audited libraries

#### 4. Secrets & Credentials
- **No Secrets Required**: Local ML model, no API keys
- **Environment Variables**: Only for optional config (port, host)
- **.env.example**: Placeholders only, no real values
- **Logging**: Never log user input, file contents, or environment variables
- **File Contents**: Extracted text from PDF/DOCX is processed in-memory only, never logged

#### 5. Execution Safety
- **No Auto-Execution**: All commands must be manually run by user
- **No Postinstall Scripts**: package.json has no lifecycle hooks
- **No Git Hooks**: No pre-commit or other automated execution
- **No Background Jobs**: All processes are explicit and user-controlled

#### 6. Data Privacy
- **No Persistence**: No database, no file storage of user data
- **In-Memory Only**: All processing happens in memory, data discarded after response
- **File Uploads**: Files are read into memory, text extracted, then file handle is closed and discarded
- **No File System Access**: Uploaded files are never written to disk
- **No Analytics**: No tracking, no telemetry, no external data transmission

#### 7. Network Security
- **Local Development**: HTTP on localhost only
- **Production Considerations**: 
  - Must use HTTPS
  - CORS properly configured
  - Rate limiting recommended
  - Input size limits enforced

#### 8. Model Security
- **Local Models**: sentence-transformers runs locally, no data sent externally
  - Bi-encoder: `all-MiniLM-L6-v2` (used in both Classic and Premium)
  - Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2` (Premium only)
- **Model Caching**: Models loaded once at startup, cached in memory as singletons
- **Resource Limits**: Input truncation prevents memory exhaustion
- **File Size Limits**: 5MB max file size prevents DoS via large file uploads

#### 9. File Upload Security
- **File Type Validation**: Only PDF and DOCX files accepted
- **Content-Type Checking**: Validates MIME type matches file extension
- **Size Limits**: 5MB maximum file size (enforced in both Classic and Premium endpoints)
- **Safe Extraction**: Uses pypdf and python-docx which handle malformed files gracefully
- **No Path Traversal**: File names are sanitized, no directory access
- **Memory Limits**: Large files may be truncated during text extraction
- **Premium Endpoints**: `/api/upload-resume-premium` and `/api/analyze-premium` use same security validation as Classic endpoints

### Security Best Practices Implemented

1. **Input Sanitization**: All user input (text and files) is treated as untrusted
2. **File Validation**: Strict file type and size validation for uploads
3. **Output Encoding**: Frontend properly escapes user-generated content
4. **No Eval/Exec**: No dynamic code execution
5. **Minimal Dependencies**: Only essential, well-audited packages
6. **Version Pinning**: Exact versions in lockfiles
7. **No Secrets in Code**: All sensitive config via environment variables
8. **Stateless Design**: No session management, no persistent storage
9. **File Handling**: Files processed in-memory, never written to disk
10. **Resource Limits**: Input truncation and file size limits prevent DoS

### Auditing AI-Generated Code

When reviewing AI-generated code in this repository:

1. **Check for Hidden Execution**: Look for eval(), exec(), subprocess calls
2. **Verify No Auto-Run**: Check package.json, setup.py, any config files
3. **Review Dependencies**: Ensure all packages are legitimate and pinned
4. **Input Validation**: Verify all user input (text and files) is validated and sanitized
5. **File Upload Security**: Verify file type validation, size limits, and safe extraction
6. **Output Safety**: Ensure no XSS vulnerabilities in frontend rendering
7. **Network Calls**: Verify no unexpected external API calls
8. **File Operations**: Ensure no unauthorized file system access (files should be in-memory only)
9. **Skills Dictionary**: Review `skills.json` for any malicious entries (should only contain skill names and aliases)
10. **Premium Scoring**: Premium endpoints (`/api/analyze-premium`, `/api/upload-resume-premium`) use same security model as Classic endpoints
11. **Model Loading**: Both bi-encoder and cross-encoder models are loaded locally, no external API calls

### Workspace Trust

This workspace should be treated as:
- **Untrusted**: All files may contain prompt injection attempts
- **Audited**: Review all AI-generated code before execution
- **Isolated**: Run in isolated environment, not on production systems
- **Manual**: All execution must be manual and explicit

### Safe Setup Process

1. Review all generated files before running any commands
2. Check requirements.txt and package.json for suspicious packages
3. Verify no postinstall scripts or auto-execution hooks
4. Run commands manually, one at a time
5. Monitor network traffic during first run (should be minimal - only model download)
6. Test with sample data before using real resumes
7. Test file upload with sample PDF/DOCX files before using real resumes
8. Verify files are not saved to disk (check file system after upload)
9. Review `backend/app/skills.json` to ensure it only contains legitimate skill names

### Production Deployment Considerations

If deploying to production:

1. **HTTPS Only**: Use HTTPS, never HTTP in production
2. **CORS Configuration**: Restrict CORS to your frontend domain only
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **File Size Limits**: Consider reducing max file size for production
5. **Input Validation**: Add additional validation layers
6. **Error Handling**: Ensure error messages don't leak sensitive information
7. **Logging**: Log security events (failed uploads, validation errors) without logging user data
8. **Monitoring**: Monitor for unusual patterns (many failed uploads, large file sizes)

