# Security Review Checklist

Structured security checklist for code reviews, organized by vulnerability category.

## Input Validation

### All External Input
- [ ] All user input validated before use
- [ ] Input length limits enforced
- [ ] Input type/format validated (numbers, emails, URLs)
- [ ] Allowlists preferred over denylists
- [ ] Unicode/encoding attacks considered

### File Uploads
- [ ] File type validated (not just extension)
- [ ] File size limits enforced
- [ ] Files stored outside webroot
- [ ] Filenames sanitized (no path traversal)
- [ ] Virus scanning for applicable file types

### URLs and Redirects
- [ ] Open redirect vulnerabilities checked
- [ ] SSRF protections (no arbitrary URL fetching)
- [ ] Protocol allowlist (https only where possible)

## Injection Vulnerabilities

### SQL Injection
- [ ] Parameterized queries used (not string concatenation)
- [ ] ORM used correctly (no raw SQL with user input)
- [ ] Stored procedures don't concatenate

### Command Injection
- [ ] No shell commands with user input
- [ ] If unavoidable: strict allowlist, escape properly
- [ ] Subprocess calls use array form (not shell=True)

### Code Injection
- [ ] No `eval()`, `exec()`, `Function()` with user input
- [ ] Template engines auto-escape by default
- [ ] No dynamic `import()` with user input

### XSS (Cross-Site Scripting)
- [ ] Output encoding appropriate for context (HTML, JS, URL, CSS)
- [ ] CSP headers configured
- [ ] No `innerHTML` with user content
- [ ] No `dangerouslySetInnerHTML` without sanitization
- [ ] HttpOnly flag on session cookies

### LDAP/XML/XPath Injection
- [ ] LDAP queries use parameterized methods
- [ ] XML parsers disable external entities (XXE)
- [ ] XPath queries parameterized

## Authentication

### Password Handling
- [ ] Passwords hashed with bcrypt/argon2/scrypt (not MD5/SHA1)
- [ ] Salt unique per password
- [ ] Password strength requirements enforced
- [ ] No password in logs or error messages

### Session Management
- [ ] Session IDs regenerated after login
- [ ] Session timeout implemented
- [ ] Secure and HttpOnly cookie flags
- [ ] Session invalidation on logout
- [ ] No session ID in URL

### Multi-Factor Authentication
- [ ] MFA available for sensitive operations
- [ ] Backup codes handled securely
- [ ] Rate limiting on MFA attempts

### Account Security
- [ ] Account lockout after failed attempts
- [ ] Rate limiting on login attempts
- [ ] Secure password reset flow
- [ ] No username enumeration

## Authorization

### Access Control
- [ ] Authorization checked on every request
- [ ] Server-side authorization (not just UI hiding)
- [ ] Deny by default
- [ ] Principle of least privilege

### Object-Level Authorization
- [ ] User can only access their own data
- [ ] ID parameters validated against session user
- [ ] No IDOR (Insecure Direct Object Reference)

### Function-Level Authorization
- [ ] Admin functions restricted
- [ ] API endpoints check roles
- [ ] Horizontal privilege escalation prevented

## Data Protection

### Sensitive Data Handling
- [ ] PII encrypted at rest
- [ ] Sensitive data not logged
- [ ] Data masked in UI where appropriate
- [ ] Secure deletion when required

### Secrets Management
- [ ] No hardcoded credentials
- [ ] Secrets from environment/vault
- [ ] API keys not in client-side code
- [ ] No secrets in version control

### Encryption
- [ ] TLS 1.2+ for data in transit
- [ ] Strong cipher suites only
- [ ] Certificate validation enabled
- [ ] No self-signed certs in production

## API Security

### API Design
- [ ] Authentication required
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Proper error messages (no stack traces)

### API-Specific
- [ ] CORS configured restrictively
- [ ] No sensitive data in query strings
- [ ] Pagination limits enforced
- [ ] Webhooks verified (signatures)

## Error Handling

### Error Messages
- [ ] No stack traces in production
- [ ] No internal paths revealed
- [ ] No database errors to users
- [ ] Generic error messages externally

### Logging
- [ ] Security events logged
- [ ] No sensitive data in logs
- [ ] Log injection prevented
- [ ] Audit trail for sensitive operations

## Dependencies

### Third-Party Code
- [ ] Dependencies from trusted sources
- [ ] Known vulnerabilities checked (npm audit, Snyk, etc.)
- [ ] Dependency versions pinned
- [ ] Regular dependency updates scheduled

### Supply Chain
- [ ] Lock files committed
- [ ] Integrity hashes verified
- [ ] No arbitrary code execution in build

## Infrastructure

### Configuration
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Unnecessary features disabled
- [ ] Security headers configured (HSTS, CSP, X-Frame-Options)

### Database
- [ ] Least privilege database user
- [ ] No database admin in app connection
- [ ] Connection strings secured

## Common Vulnerability Patterns

### By Language

**JavaScript/TypeScript**
- `eval()`, `Function()`, `setTimeout(string)`
- `innerHTML`, `document.write()`
- Prototype pollution
- RegExp DoS (ReDoS)

**Python**
- `eval()`, `exec()`, `pickle.loads()` with untrusted data
- `shell=True` in subprocess
- YAML `load()` vs `safe_load()`
- Format string vulnerabilities

**Java**
- Deserialization vulnerabilities
- XXE in XML parsers
- Path traversal in file operations
- SQL injection in JPA native queries

**Go**
- SQL string concatenation
- Template injection
- Race conditions in concurrent code
- Unchecked type assertions

**Ruby**
- `send()` with user input
- `constantize` with user input
- Mass assignment vulnerabilities
- Command injection via backticks

### By Framework

**React**
- `dangerouslySetInnerHTML`
- `href="javascript:..."`
- Server-side rendering XSS

**Express/Node**
- Middleware order issues
- Missing rate limiting
- Prototype pollution via body parsers
- Path traversal in static files

**Django/Flask**
- Debug mode in production
- CSRF exemptions
- Raw SQL queries
- Pickle in cache/sessions

## Red Flags to Always Flag

```
# Immediate review required
eval(
exec(
system(
shell=True
dangerouslySetInnerHTML
innerHTML =
verify=False
password = "
secret = "
api_key = "
-----BEGIN PRIVATE KEY-----
-----BEGIN RSA PRIVATE KEY-----
```

## Review Questions

When reviewing security-sensitive code, ask:

1. **What's the worst that could happen if this input is malicious?**
2. **Who can reach this code path?**
3. **What data does this code have access to?**
4. **What can an attacker learn from error messages?**
5. **What happens if this external service is compromised?**
