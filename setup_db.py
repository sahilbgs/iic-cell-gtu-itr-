import os
from app import create_app
from extensions import db
from models.user import User
from models.department import Department

def setup_database():
    print("==================================================")
    print(" GTU-ITR Portal - Database Setup & Seeding Script")
    print("==================================================")
    
    # Load app with current environment config
    config_name = os.environ.get('FLASK_ENV', 'development')
    print(f"Environment: {config_name}")
    
    # Temporarily bypass production SECRET_KEY check for setup script
    if config_name == 'production' and not os.environ.get('SECRET_KEY'):
        print("[WARNING] Injecting temporary SECRET_KEY to allow DB setup in production mode...")
        os.environ['SECRET_KEY'] = 'temporary-setup-key'
        
    app = create_app(config_name)
    
    with app.app_context():
        # 1. Create all tables
        print("\n[1/3] Creating database tables...")
        db.create_all()
        print("  [OK] Tables created successfully.")
        
        # 2. Seed Departments
        print("\n[2/3] Seeding departments...")
        departments = [
            Department(name='Computer Engineering', code='CE', hod_name='Dr. Rajesh Patel'),
            Department(name='Information Technology', code='IT', hod_name='Dr. Priya Shah'),
            Department(name='Mechanical Engineering', code='ME', hod_name='Dr. Amit Kumar'),
            Department(name='Civil Engineering', code='CIV', hod_name='Dr. Suresh Joshi'),
            Department(name='Electrical Engineering', code='EE', hod_name='Dr. Neha Gupta'),
            Department(name='Electronics & Communication', code='EC', hod_name='Dr. Vikram Singh'),
        ]
        
        dept_added = 0
        for dept in departments:
            existing = Department.query.filter_by(code=dept.code).first()
            if not existing:
                db.session.add(dept)
                dept_added += 1
                
        db.session.commit()
        if dept_added > 0:
            print(f"  [OK] {dept_added} new departments added.")
        else:
            print("  - Departments already exist. Skipping.")

        # 3. Seed Users
        print("\n[3/3] Seeding default users...")
        ce_dept = Department.query.filter_by(code='CE').first()
        it_dept = Department.query.filter_by(code='IT').first()
        
        # Safely get IDs if departments exist
        ce_id = ce_dept.id if ce_dept else None
        it_id = it_dept.id if it_dept else None

        users_data = [
            ('admin@gmail.com', 'Admin User', 'MASTER_ADMIN', None, 'System Administrator', '44113290'),
            ('principal@gtu.ac.in', 'Principal User', 'PRINCIPAL', None, 'Principal', 'password123'),
            ('chairperson@gtu.ac.in', 'Dr. IIC Chairperson', 'CHAIRPERSON', ce_id, 'IIC Chairperson', 'password123'),
            ('rdcoord@gtu.ac.in', 'Dr. R&D Coordinator', 'RD_COORDINATOR', it_id, 'R&D Coordinator', 'password123'),
            ('hod.ce@gtu.ac.in', 'Dr. CE HOD', 'HOD', ce_id, 'HOD', 'password123'),
            ('faculty.ce@gtu.ac.in', 'Prof. Arun Mehta', 'FACULTY', ce_id, 'Assistant Professor', 'password123'),
            ('faculty.it@gtu.ac.in', 'Prof. Sneha Desai', 'FACULTY', it_id, 'Associate Professor', 'password123'),
            ('student@gtu.ac.in', 'Rahul Student', 'STUDENT_REP', ce_id, 'Student Rep', 'password123'),
        ]
        
        users_added = 0
        for email, name, role, dept_id, desig, pwd in users_data:
            existing = User.query.filter_by(email=email).first()
            if not existing:
                u = User(email=email, full_name=name, role=role, department_id=dept_id, designation=desig)
                u.set_password(pwd)
                db.session.add(u)
                users_added += 1
            else:
                existing.set_password(pwd)
                existing.role = role

        db.session.commit()
        
        if users_added > 0:
            print(f"  [OK] {users_added} new users added/updated.")
        else:
            print("  - Users already exist. Updated credentials.")

        print('\n==================================================')
        print('[SUCCESS] Database is fully setup and ready to use!')
        print('==================================================')

if __name__ == '__main__':
    setup_database()
