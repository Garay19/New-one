from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()

def create_admin_user():
    with app.app_context():
        # Check if the admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists.")
            return

        # Get admin credentials from environment variables or use default values
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('ADMIN_PASSWORD', 'adminpassword')

        # Create a new admin user
        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)

        # Add the admin user to the database
        db.session.add(admin)
        db.session.commit()

        print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    create_admin_user()