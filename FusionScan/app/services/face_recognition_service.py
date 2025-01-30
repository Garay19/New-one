import face_recognition
import cv2
import numpy as np
import pickle
from app.models import User, db
from flask import flash

class FaceRecognitionService:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_lrns = []

    def load_known_faces(self):
        """Loads known faces from the database."""
        print("Loading known faces from the database...")
        users = User.query.all()
        print(f"Found {len(users)} users in the database.")
        for user in users:
            if user.face_encodings:
                try:
                    encodings = pickle.loads(user.face_encodings)
                    print(f"Loaded {len(encodings)} encodings for user {user.username}")
                    self.known_face_encodings.extend(encodings)
                    self.known_face_names.extend([user.username] * len(encodings))
                    self.known_face_lrns.extend([user.student_lrn] * len(encodings))
                except Exception as e:
                    print(f"Error loading encodings for user {user.username}: {e}")
            else:
                print(f"No face encodings found for user {user.username}")
        print("Known faces loaded.")

    def preprocess_image(self, image):
        """
        Preprocesses the image for better recognition accuracy.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray

    def capture_and_store_face_encodings(self, user_id, num_encodings=5):
        """
        Captures multiple face encodings from a live video feed and stores them in the database.
        Guides the user to center their face.
        """
        user = User.query.get(user_id)
        if not user:
            print("User not found.")
            return

        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend

        # Check if the camera opened successfully
        if not video_capture.isOpened():
            print("Error: Could not open camera.")
            return

        captured_encodings = []

        while len(captured_encodings) < num_encodings:
            ret, frame = video_capture.read()
            if not ret:
                print("Error capturing frame.")
                break

            print("Original frame shape:", frame.shape)

            # Detect faces using a pre-trained CNN model
            face_locations = face_recognition.face_locations(frame, model="cnn")
            print(f"Face Locations (original): {face_locations}")

            if len(face_locations) == 1:
                top, right, bottom, left = face_locations[0]
                frame_height, frame_width, _ = frame.shape
                center_x = frame_width // 2
                center_y = frame_height // 2
                margin_x = frame_width // 8
                margin_y = frame_height // 8

                print(f"Center X,Y: ({center_x},{center_y}), Left: {left}, Top: {top}, Right: {right}, Bottom: {bottom}")
                print(f"Margins: X={margin_x}, Y={margin_y}")

                # Check if the face is within the center region
                if (center_x - margin_x < left < center_x + margin_x and
                        center_x - margin_x < right < center_x + margin_x and
                        center_y - margin_y < top < center_y + margin_y and
                        center_y - margin_y < bottom < center_y + margin_y):

                    # Preprocess the face region
                    face_image = frame[top:bottom, left:right]
                    preprocessed_face = self.preprocess_image(face_image)

                    # Encode the face directly from the preprocessed image
                    face_encoding = face_recognition.face_encodings(preprocessed_face)

                    if len(face_encoding) > 0:
                        # Increase num_jitters for more robust encoding
                        face_encoding = face_recognition.face_encodings(preprocessed_face, num_jitters=3)
                        captured_encodings.append(face_encoding[0])
                        print(f"Captured encoding {len(captured_encodings)}/{num_encodings}")

                        # Indicate successful capture
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, "Face Centered!", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.putText(frame, f"Capturing {len(captured_encodings)}/{num_encodings}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    else:
                        print("Could not capture encoding from preprocessed image")
                        cv2.putText(frame, "Face Not Detected After Preprocessing!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                else:
                    # Indicate face not centered
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, "Center your face", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            elif len(face_locations) > 1:
                cv2.putText(frame, "Multiple faces detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        if captured_encodings:
            try:
                user.face_encodings = pickle.dumps(captured_encodings)
                db.session.commit()
                print(f"Successfully captured and stored {len(captured_encodings)} face encodings for {user.username}.")
                flash(f"Successfully captured and stored {len(captured_encodings)} face encodings for {user.username}.", "success")
            except Exception as e:
                db.session.rollback()
                print(f"Error storing face encodings for {user.username}: {e}")
                flash(f"Error storing face encodings for {user.username}: {e}", "danger")

    def facial_recognition_process(self, frame):
        """
        Performs facial recognition on a single frame.

        Args:
            frame: The video frame (OpenCV image).

        Returns:
            frame: The processed frame with bounding boxes and names.
            name: The name of the recognized person or "Unknown".
            lrn: The LRN of the recognized person or None
        """
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
        rgb_small_frame, face_locations
    )

        name = "Unknown"
        lrn = None

        if face_encodings:
            if not self.known_face_encodings:
                print("No known faces loaded. Please add users and capture their face encodings.")

            # Draw bounding box for each detected face
            for (top, right, bottom, left) in face_locations:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)  # Red box for unknown faces

                return frame, name, lrn  # Return early with bounding box for unknown faces

        matches = face_recognition.compare_faces(
            self.known_face_encodings, face_encodings[0], tolerance=0.5
        )

        face_distances = face_recognition.face_distance(
            self.known_face_encodings, face_encodings[0]
        )

        if face_distances.size > 0:
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
                lrn = self.known_face_lrns[best_match_index]

                # Draw a rectangle around the face and label for known faces (Green)
                top, right, bottom, left = face_locations[0]
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(
                    frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED
                )
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(
                    frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1
                )
            else:
                    print("No matching faces found in the database.")
        else:
                print("No faces detected in the frame.")

        return frame, name, lrn