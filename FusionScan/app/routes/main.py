import os
import cv2
from flask import Blueprint, render_template, Response, current_app, send_from_directory, flash, redirect, url_for, request, jsonify
from flask_login import login_required
from app.services.data_service import DataService
from app.services.thermal_scanning_service import get_temperature_from_arduino
from app.utils.decorators import admin_required
from app import db
from app.models import User, Attendance
import pandas as pd
from datetime import datetime

main_bp = Blueprint('main', __name__)

data_service = DataService()

@main_bp.route('/')
@login_required
def index():
    users = User.query.all()
    attendance_data = []
    for user in users:
        attendance_record = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.timestamp.desc()).first()
        attendance_data.append({
            'user': user,
            'attendance': attendance_record
        })
    return render_template('index.html', attendance_data=attendance_data)

def generate_frames():
    camera = cv2.VideoCapture(0)
    
    # Get the application context before the loop
    app = current_app._get_current_object()
    
    while True:
        success, frame = camera.read()
        if not success:
            print("Error reading from camera.")
            break
        else:
            # Create an application context for this request
            with app.app_context():
                frame, name, lrn = current_app.face_recognition_service.facial_recognition_process(frame)
                temperature = get_temperature_from_arduino(app)
                print(f"Temperature from Arduino: {temperature}")

                if temperature is not None:
                    if name != "Unknown":
                        user = User.query.filter_by(username=name).first()
                        if user:
                            status = "Present" if temperature < 37.5 else "Anomaly"
                            data_service.record_attendance(user.id, status, temperature)

                            # Display temperature on the frame
                            temp_text = f"Temp: {temperature:.1f}°C"
                            cv2.putText(frame, temp_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                # Display a message if no faces are detected or no known faces are loaded
                if name == "Unknown":
                    if not current_app.face_recognition_service.known_face_encodings:
                        cv2.putText(frame, "No known faces loaded!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    else:
                        cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error encoding frame to JPEG.")
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@main_bp.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@main_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    data_service.delete_user_by_id(user_id)
    flash('User and their attendance records have been deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@main_bp.route('/restart_attendance', methods=['POST'])
@admin_required
def restart_attendance():
    data_service.restart_all_attendance()
    flash('All attendance records for today have been cleared.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/export_attendance')
@admin_required
def export_attendance():
    attendance_records = Attendance.query.all()
    data = []
    for record in attendance_records:
        user = User.query.get(record.user_id)
        data.append({
            'Timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Username': user.username if user else 'Unknown',
            'LRN': user.student_lrn if user else 'N/A',
            'Status': record.status,
            'Temperature': record.temperature
        })

    df = pd.DataFrame(data)

    # Sort by 'Timestamp' in descending order (most recent first)
    df.sort_values(by='Timestamp', ascending=False, inplace=True)

    # Format the 'Timestamp' column for better readability
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %I:%M:%S %p')

    # Reorder columns to have 'Timestamp' as the first column
    df = df[['Timestamp', 'Username', 'LRN', 'Status', 'Temperature']]

    filename = f"Attendance_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    df.to_excel(filepath, index=False, engine='xlsxwriter')
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@main_bp.route('/get_temperature')
@login_required
def get_temperature():
    temperature = get_temperature_from_arduino()
    if temperature is None:
        return jsonify({'error': 'Could not retrieve temperature'}), 500
    return jsonify({'temperature': temperature})