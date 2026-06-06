# Security Controls & Audit Record

This document records the security controls, password handling, data validation policies, and defensive mitigations implemented in the **GTU-ITR R&D & IIC Portal** to protect users and satisfy legal security requirements.

## 1. Password Hashing & Authentication
- **Hashing Algorithm**: We utilize Werkzeug's `generate_password_hash` and `check_password_hash` functions.
- **Underlying Crypto**: Matches modern secure defaults (currently PBKDF2 with a SHA256 HMAC and a minimum of 600,000 iterations, or bcrypt depending on the environment setup).
- **Plain-text Prevention**: The database table `users` contains only the `password_hash` column. The user model does not store plain-text passwords or clear-text caches.

## 2. Forms, Inputs & XSS Protection
- **CSRF Protection**: Flask-WTF is integrated with WTForms. Every POST, PUT, and DELETE action requires validation of a unique `csrf_token` token injected in a hidden input or an HTTP request header (`X-CSRFToken` for AJAX requests).
- **Template Escaping**: The Jinja2 templating engine is configured with auto-escaping enabled on all `.html` extensions. This renders user-submitted text as plain characters, preventing Cross-Site Scripting (XSS).
- **Database Injection (SQLi)**: SQLAlchemy ORM is used for database access. Parameterized queries are automatically generated for all queries, eliminating SQL injection vectors.
- **Upload Validation**: File uploads (for publications and activity reports) validate extensions against a restricted whitelist (`pdf`, `docx`, `doc`, `txt`, `png`, `jpg`, `jpeg`). Filenames are sanitized using `werkzeug.utils.secure_filename`.

## 3. Session & Transport Security
- **Secure Transport (SSL/HTTPS)**: In production, we configure HSTS (`Strict-Transport-Security`) headers to force all connections over TLS/HTTPS.
- **Session Cookie Flags**:
  - `SESSION_COOKIE_HTTPONLY = True`: Blocks scripts from reading session identifiers, protecting sessions from XSS harvesting.
  - `SESSION_COOKIE_SECURE = True`: Forces browsers to only send cookies over SSL/HTTPS.
  - `SESSION_COOKIE_SAMESITE = 'Lax'`: Protects cookies against Cross-Site Request Forgery (CSRF) in navigation.
  - `REMEMBER_COOKIE_HTTPONLY = True` & `REMEMBER_COOKIE_SECURE = True`: Protects persistent authentication sessions.

## 4. HTTP Security Headers
On every response, the server injects the following security headers:
- `Content-Security-Policy`: Restricts scripts and styles to trusted domains (`self`, Google Fonts, Lucide icons on `unpkg.com`, Chart.js on `cdn.jsdelivr.net`).
- `X-Frame-Options: DENY`: Prevents UI redressing and clickjacking.
- `X-Content-Type-Options: nosniff`: Instructs browsers not to sniff MIME types away from declared Content-Types.
- `Referrer-Policy: strict-origin-when-cross-origin`: Controls referrer leaks.
