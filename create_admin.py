# create_admin.py
from database import db, init_app
from models import User
from werkzeug.security import generate_password_hash
from app import app

with app.app_context():
    username = "admin1"
    password = "Admin1@123"

    existing = User.query.filter_by(username=username).first()
    if existing:
        print("⚠️ Admin already exists!")
    else:
        hashed = generate_password_hash(password)
        admin = User(username=username, password_hash=hashed, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin '{username}' created successfully!")
