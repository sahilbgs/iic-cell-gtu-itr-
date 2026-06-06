# Open-Source License Compliance Log

This document lists all third-party open-source libraries, packages, and assets used in the **GTU-ITR R&D & IIC Portal**, along with their licenses, to ensure full open-source compliance.

## 1. Backend Python Dependencies (pip)

All dependencies installed in the virtual environment are check-verified to ensure they do not use restrictive copyleft licenses (e.g. GPLv3 without exception) that would force open-sourcing the proprietary portal code.

| Dependency Name | Version | Primary License | Compliance Notes |
| :--- | :--- | :--- | :--- |
| **Flask** | 3.1.1 | BSD-3-Clause | Permissive license. Fully compliant. |
| **Flask-SQLAlchemy** | 3.1.1 | BSD-3-Clause | Permissive license. Fully compliant. |
| **Flask-Login** | 0.6.3 | MIT | Permissive license. Fully compliant. |
| **Flask-WTF** | 1.2.2 | BSD-3-Clause | Permissive license. Fully compliant. |
| **Flask-Mail** | 0.10.0 | BSD-3-Clause | Permissive license. Fully compliant. |
| **Flask-Migrate** | 4.1.0 | MIT | Permissive license. Fully compliant. |
| **SQLAlchemy** | 2.0.41 | MIT | Permissive license. Fully compliant. |
| **anthropic** | 0.52.0 | MIT | Permissive license. Fully compliant. |
| **reportlab** | 4.4.0 | BSD-3-Clause | Permissive license. Fully compliant. |
| **openpyxl** | 3.1.5 | MIT | Permissive license. Fully compliant. |
| **python-dotenv** | 1.1.0 | BSD-3-Clause | Permissive license. Fully compliant. |
| **Werkzeug** | 3.1.3 | BSD-3-Clause | Permissive license. Fully compliant. |
| **WTForms** | 3.2.1 | BSD-3-Clause | Permissive license. Fully compliant. |
| **gunicorn** | 23.0.0 | MIT | Permissive license. Fully compliant. |

## 2. Frontend Libraries (CDN & Assets)

Frontend assets are loaded dynamically via secure Content Delivery Networks (CDNs) under permissive licenses.

| Dependency Name | Provider | Primary License | Purpose |
| :--- | :--- | :--- | :--- |
| **Lucide Icons** | unpkg.com | ISC | SVG iconography for navigation and dashboard buttons. |
| **Chart.js** | jsdelivr.net | MIT | Interactive statistics and R&D charts on the dashboard. |
| **Inter Font** | Google Fonts | SIL Open Font License 1.1 | Body typography. |
| **Outfit Font** | Google Fonts | SIL Open Font License 1.1 | Heading and title typography. |

## 3. Compliance Summary
- **No GPL/Copyleft Violations**: All dependencies use MIT, BSD, ISC, or Apache-style permissive licenses. No source-code contamination issues exist.
- **Header Attribution**: Open-source notices are maintained inside the virtual environment package directories (`venv/Lib/site-packages`).
