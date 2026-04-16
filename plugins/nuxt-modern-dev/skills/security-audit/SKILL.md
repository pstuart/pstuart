---
name: security-audit
description: Security audit checklist for web applications. Use when reviewing security posture, checking for vulnerabilities, or hardening a deployment.
---

# Security Audit

## Web Application Checklist

### Authentication & Authorization
- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA)
- [ ] Session tokens are HTTP-only, Secure, SameSite cookies
- [ ] CSRF protection enabled
- [ ] Rate limiting on login endpoints
- [ ] Account lockout after failed attempts

### Input Validation
- [ ] All user input validated server-side
- [ ] SQL parameterized queries (no string concatenation)
- [ ] XSS prevention (output encoding, CSP headers)
- [ ] File upload validation (type, size, content)
- [ ] Path traversal prevention

### HTTP Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### Secrets Management
- [ ] No secrets in source code or git history
- [ ] Environment variables for configuration
- [ ] API keys rotated periodically
- [ ] .env files in .gitignore

### SSL/TLS
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Valid certificate (not expired)
- [ ] TLS 1.2+ only
- [ ] Strong cipher suites

### Server Hardening
- [ ] Unnecessary ports closed
- [ ] Default credentials changed
- [ ] Software up to date
- [ ] Firewall configured
- [ ] Logs monitored

### Nuxt-Specific
- [ ] Server routes validate authentication
- [ ] No sensitive data in client-side state
- [ ] API routes use proper error handling (no stack traces in production)
- [ ] `nuxt-security` module configured if public-facing

## Generating Reports

Save audit results to `./security-reports/audit-YYYY-MM-DD.md` with:
- Findings summary with severity levels
- Specific file locations for each finding
- Remediation steps for each issue
- Priority ordering (critical > high > medium > low)
