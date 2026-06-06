# Application Maintenance & Change Log

This changelog tracks all development modifications, feature additions, security enhancements, and legal compliance tasks performed on the **GTU-ITR R&D & IIC Portal**.

---

## [1.1.0] - 2026-06-06
### Added
- Created DPDP 2023-compliant public Privacy Policy page at `/privacy` (`templates/legal/privacy_policy.html`).
- Created public Terms of Service page at `/terms` (`templates/legal/terms_of_service.html`).
- Integrated dynamic glassmorphism Cookie Consent and Data processing banner in the base layout (`templates/base.html`).
- Added user registration consent check on the sign-up form (`templates/auth/register.html`).
- Added student activity registration consent check on the registration page (`templates/posts/register.html`).
- Added an interactive **Legal & Compliance Audit Checklist** dashboard inside the Admin Panel (`templates/admin/index.html`) for Principal review.
- Created project ownership declaration record (`OWNERSHIP.md`).
- Created open-source licenses log (`OPEN_SOURCE_COMPLIANCE.md`).
- Formulated full compliance records: `CHANGELOG.md`, `ARCHITECTURE.md`, `SECURITY_AUDIT.md`, and `DEPLOYMENT.md` inside `legal_records/`.

### Secured
- Injected secure HTTP response headers on all routes (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).
- Configured production HSTS (`Strict-Transport-Security`) headers to enforce SSL.
- Configured remember-me cookie secure flags in production configurations.

---

## [1.0.0] - 2026-06-06
### Added
- Initial development release of the GTU-ITR R&D & IIC Portal.
- Completed multi-role RBAC authentication (Principal, Chairperson, Department Coordinator, Faculty, Student Representative).
- Completed Principal shared activity management dashboards.
- Completed IIC activity registration and form builder (dynamic input allocation, OCR text extractor fallback, and Phi-3 heuristic integration).
- Configured SQLite database with SQLAlchemy migrations.
- Configured automatic MySQL environment database builder.
- Configured export utilities (openpyxl Excel exporter, ReportLab PDF exporter).
- Implemented dashboard metrics, charts, activity feeds, and dark/light modes.
