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

Developed for the GTU-ITR research ecosystem.
