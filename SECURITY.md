# Security Documentation - ResuMate AI

## Threat Model Checklist

### Attack Surface Analysis

#### 1. Input Validation & Injection
- **Risk**: User-provided resume/job text may contain malicious payloads
- **Mitigation**: 
  - Text-only input (no file uploads)
  - Input truncation limits (max 50KB per field)
  - No code execution on user input
  - Sanitize output to prevent XSS

#### 2. Trust Boundaries
- **Frontend ↔ Backend**: API communication over HTTP (local dev) / HTTPS (production)
- **Backend ↔ ML Model**: Local sentence-transformers, no external API calls
- **No External Services**: All processing happens locally
- **No Database**: Stateless API, no persistent storage of user data

#### 3. Dependency Risks
- **Python Dependencies**: 
  - FastAPI (well-audited, widely used)
  - sentence-transformers (HuggingFace, reputable)
  - Exact version pinning in requirements.txt
- **Node Dependencies**:
  - React, TypeScript, Vite (standard tooling)
  - Tailwind CSS (CSS framework, no runtime risk)
  - Version pinning in package.json
- **Supply Chain**: No obscure packages, no remote install scripts

#### 4. Secrets & Credentials
- **No Secrets Required**: Local ML model, no API keys
- **Environment Variables**: Only for optional config (port, host)
- **.env.example**: Placeholders only, no real values
- **Logging**: Never log user input or environment variables

#### 5. Execution Safety
- **No Auto-Execution**: All commands must be manually run by user
- **No Postinstall Scripts**: package.json has no lifecycle hooks
- **No Git Hooks**: No pre-commit or other automated execution
- **No Background Jobs**: All processes are explicit and user-controlled

#### 6. Data Privacy
- **No Persistence**: No database, no file storage of user data
- **In-Memory Only**: All processing happens in memory, data discarded after response
- **No Analytics**: No tracking, no telemetry, no external data transmission

#### 7. Network Security
- **Local Development**: HTTP on localhost only
- **Production Considerations**: 
  - Must use HTTPS
  - CORS properly configured
  - Rate limiting recommended
  - Input size limits enforced

#### 8. Model Security
- **Local Model**: sentence-transformers runs locally, no data sent externally
- **Model Caching**: Model loaded once at startup, cached in memory
- **Resource Limits**: Input truncation prevents memory exhaustion

### Security Best Practices Implemented

1. **Input Sanitization**: All user input is treated as untrusted
2. **Output Encoding**: Frontend properly escapes user-generated content
3. **No Eval/Exec**: No dynamic code execution
4. **Minimal Dependencies**: Only essential, well-audited packages
5. **Version Pinning**: Exact versions in lockfiles
6. **No Secrets in Code**: All sensitive config via environment variables
7. **Stateless Design**: No session management, no persistent storage

### Auditing AI-Generated Code

When reviewing AI-generated code in this repository:

1. **Check for Hidden Execution**: Look for eval(), exec(), subprocess calls
2. **Verify No Auto-Run**: Check package.json, setup.py, any config files
3. **Review Dependencies**: Ensure all packages are legitimate and pinned
4. **Input Validation**: Verify all user input is validated and sanitized
5. **Output Safety**: Ensure no XSS vulnerabilities in frontend rendering
6. **Network Calls**: Verify no unexpected external API calls
7. **File Operations**: Ensure no unauthorized file system access

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

