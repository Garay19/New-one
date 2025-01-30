from datetime import datetime, timedelta
from app.models import db, Attendance, User

class DataService:
    def record_attendance(self, user_id, status, temperature):
        """Records attendance for a user if not recorded recently."""
        last_attendance = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.timestamp.desc()).first()
        if not last_attendance or (datetime.utcnow() - last_attendance.timestamp) > timedelta(seconds=5):
            attendance = Attendance(user_id=user_id, status=status, temperature=temperature)
            db.session.add(attendance)
            db.session.commit()

    def get_user_by_id(self, user_id):
        """Retrieves a user by their ID."""
        return User.query.get(user_id)

    def delete_user_by_id(self, user_id):
        """Deletes a user and their associated attendance records by ID."""
        user = User.query.get(user_id)
        if user:
            Attendance.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()

    def restart_all_attendance(self):
        """Resets all attendance records for the current day."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        Attendance.query.filter(Attendance.timestamp >= today_start).delete()
        db.session.commit()