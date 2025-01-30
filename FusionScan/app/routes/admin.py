from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.forms import RegistrationForm
from app.models import User
from app.utils.decorators import admin_required
from app.services.face_recognition_service import FaceRecognitionService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@admin_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, student_lrn=form.student_lrn.data, strand=form.strand.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('New user added successfully! Proceed to capture face encodings.', 'success')
        return redirect(url_for('admin.capture_face', user_id=user.id))
    return render_template('admin/add_user.html', title='Add User', form=form)

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = RegistrationForm(obj=user)  # Pre-populate the form with user data
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.student_lrn = form.student_lrn.data
        user.strand = form.strand.data
        if form.password.data:  # Update password only if a new one is provided
            user.set_password(form.password.data)
        db.session.commit()
        flash('User details updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/capture_face/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def capture_face(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot capture face encodings for admin users.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    face_recognition_service = FaceRecognitionService()

    if request.method == 'POST':
        try:
            # Call capture_and_store_face_encodings and handle potential errors
            face_recognition_service.capture_and_store_face_encodings(user_id)
            flash('Face encodings captured and stored successfully.', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/capture_face.html', user=user)