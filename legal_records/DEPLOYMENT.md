# Pre-Launch Verification & Deployment Manual

This document details the server setup, SSL configuration, database backup scripts, and launch checklists required before deploying the **GTU-ITR R&D & IIC Portal** to production.

## 1. Pre-Launch Legal Verification Checklist
Before enabling the portal for public registrations:
- [ ] Ensure `FLASK_ENV` is set to `production` (enables secure cookies and debug=False).
- [ ] Confirm `SECRET_KEY` in `.env` has been changed from default to a randomly generated 64-character hex string.
- [ ] Confirm `/privacy` (Privacy Policy) and `/terms` (Terms of Service) are fully rendered and correct.
- [ ] Verify the Cookie Consent banner triggers on clean browser cache.
- [ ] Verify the registration consent checkboxes prevent form submissions if unchecked.

## 2. Server & SSL (HTTPS) Configuration
The portal must run exclusively under HTTPS:
- **Reverse Proxy**: We recommend deploying behind a reverse proxy (e.g. **Nginx** or **Apache**) configured with TLS/SSL.
- **SSL Certificates**: Utilize Let's Encrypt (free, automated) or a custom institutional certificate.
- **Nginx Config Block Example**:
  ```nginx
  server {
      listen 80;
      server_name iic.gtu.ac.in;
      return 301 https://$host$request_uri; # Force HTTPS redirect
  }

  server {
      listen 443 ssl http2;
      server_name iic.gtu.ac.in;

      ssl_certificate /etc/letsencrypt/live/iic.gtu.ac.in/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/iic.gtu.ac.in/privkey.pem;
      
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers HIGH:!aNULL:!MD5;

      location / {
          proxy_pass http://127.0.0.1:5000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```

## 3. Database Backups Configuration
To prevent data loss and satisfy legal record-keeping guidelines, database backups must be scheduled periodically.

### A. For SQLite deployments (Default Development/Staging)
Schedule a cron job or task scheduler to run a file copy of the database:
- **Windows PowerShell Script**:
  ```powershell
  $dbSource = "c:\Users\sahil\OneDrive\Desktop\iic cell\instance\gtu_portal.db"
  $backupDir = "D:\backups\gtu_portal"
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  Copy-Item $dbSource -Destination "$backupDir\gtu_portal-$timestamp.db"
  ```

### B. For MySQL/MariaDB deployments (Recommended Production)
Use `mysqldump` to perform structural and data backups daily:
- **Daily Backup Command**:
  ```bash
  mysqldump -u root -p iic_cell_gtu > /var/backups/gtu_portal/db-backup-$(date +%F).sql
  ```
