# GTU-ITR R&D & IIC Portal

An integrated portal for GTU-ITR (Gujarat Technological University - Graduate School of Engineering and Technology) to manage **R&D (Research & Development) Activities** and **IIC (Institution's Innovation Council) Cell** operations.

---

## 🚀 Features

- **Multi-Role Authentication**: Principal, Chairperson, R&D Coordinator, Department Coordinator, Faculty, and Student Representative.
- **R&D Tracking**: Manage research proposals, publications, patents, and faculty development programs.
- **IIC Activities**: Organize events, track innovation metrics, submit proposals, and monitor student startup ideas.
- **AI-Powered Assistance**: Integrated AI-powered system (Phi-3) to assist in proposal drafting and evaluation.
- **Reporting & Exports**: Export metrics and event reports dynamically.

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python) with Flask-Login & CSRF protection
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Responsive HTML/CSS with modern dashboard layouts
- **AI Integration**: HuggingFace transformers (Phi-3 model)
- **Migrations**: Flask-Migrate (Alembic)

---

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sahilbgs/iic-cell-gtu-itr-.git
   cd iic-cell-gtu-itr-
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables**:
   Copy `.env.example` to `.env` and fill in your custom configurations.
   ```bash
   copy .env.example .env
   ```

5. **Initialize and Seed Database**:
   ```bash
   flask init-db
   flask seed-db
   ```

6. **Run the Application**:
   ```bash
   flask run
   ```
   Open `http://127.0.0.1:5000` in your web browser.

---

---

## 🔑 Default Credentials

For quick testing and evaluation, the database seed command creates the following default accounts (all using password: `password123`):

| Role | Email | Name |
| :--- | :--- | :--- |
| **Principal** | `principal@gtu.ac.in` | Principal User |
| **Chairperson** | `chairperson@gtu.ac.in` | Dr. IIC Chairperson |
| **R&D Coordinator** | `rdcoord@gtu.ac.in` | Dr. R&D Coordinator |
| **Dept. Coordinator** | `deptcoord.ce@gtu.ac.in` | Dr. CE Coordinator |
| **Faculty (CE)** | `faculty.ce@gtu.ac.in` | Prof. Arun Mehta |
| **Student Rep** | `student@gtu.ac.in` | Rahul Student |

---

## 🌐 Production Deployment

To run this application securely in a production environment, follow these steps:

### 1. Set Production Environment Variables
In your production environment or `.env` file, configure the following variables:
```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your_strong_random_secret_key
```
> **Note:** The application will **fail to start** in production if `SECRET_KEY` is missing or still set to the default development key. You can generate a secure key using:
> `python -c "import secrets; print(secrets.token_hex(32))"`

### 2. Run with WSGI Server
Do not use `flask run` in production. Werkzeug (the development server) is not designed for production concurrency or security.

* **For Linux Servers (VPS, Cloud)**: Use **Gunicorn** (pre-configured in `requirements.txt`):
  ```bash
  gunicorn wsgi:app
  ```

* **For Windows Local PC Servers (Direct Domain/Local Network)**: Gunicorn does not support Windows natively. Use **Waitress** (pre-configured in `requirements.txt`):
  ```bash
  # Ensure all dependencies including waitress are installed
  pip install -r requirements.txt
  
  # Run the production server on port 5000
  waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
  ```

### 3. Map Local PC to a Public Domain
If you are hosting the app from a local PC and connecting a domain directly, choose one of these methods:
- **Cloudflare Tunnel (Highly Recommended)**:
  - No port forwarding required on your router.
  - Provides automatic free SSL (HTTPS) out of the box.
  - Connect your Cloudflare account, set up a tunnel pointing to `http://localhost:5000`, and bind it to your domain.
- **Port Forwarding (Standard Router Setup)**:
  - Set a static local IP on your host PC (e.g., `192.168.1.100`).
  - Port forward port `80` (HTTP) and `443` (HTTPS) from your router's settings to your host PC's local IP on port `5000`.
  - Update your Domain Registrar DNS settings by creating an `A Record` pointing to your router's public WAN IP address.

---

Developed for the GTU-ITR research ecosystem.
