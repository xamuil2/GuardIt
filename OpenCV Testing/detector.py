import cv2
import numpy as np
import time
import pygame
from collections import deque
from datetime import datetime
import os
from pathlib import Path

# Initialize pygame for sound alerts
pygame.mixer.init()

class MultiModelPersonDetector:
    def __init__(self):
        self.models = {
            'hog': 'HOG + SVM (OpenCV)',
            'yolo': 'YOLOv8 (Ultralytics)',
            'mobilenet': 'MobileNet SSD (OpenCV DNN)',
            'cascade': 'Haar Cascade (OpenCV)',
            'background_subtraction': 'Background Subtraction + Contours'
        }
        self.current_model = 'yolo'
        self.model_objects = {}
        self._initialize_models()
        self.person_tracks = {}
        self.track_id = 0
        self.approach_threshold = 0.3
        self.oscillation_threshold = 3
        self.pacing_alert_window = 10
        self.pacing_tracks = {}
        self.last_alert_time = 0
        self.alert_cooldown = 5
        self.detection_count = 0
        self.approach_alerts = 0
        self.pacing_alerts = 0
        self.fps_history = deque(maxlen=30)
        self.detection_confidence = deque(maxlen=30)
        self.notification_message = None
        self.notification_start_time = 0
        self.notification_duration = 3
        self.notification_flash = False
        self.notification_flash_interval = 0.3
        self.last_flash_time = 0
        self.close_alert_distance = 0.45
        self.close_alert_time = 2
        self.close_tracks = {}

    def _initialize_models(self):
        # Load the models for each detection method
        # 1. HOG + SVM
        try:
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.model_objects['hog'] = hog
            print("✓ HOG + SVM initialized")
        except Exception as e:
            print(f"✗ HOG + SVM failed: {e}")

        # 2. YOLOv8
        try:
            from ultralytics import YOLO
            import torch
            device = 'mps' if hasattr(torch, 'backends') and torch.backends.mps.is_available() else 'cpu'
            yolo_model = YOLO('yolov8n.pt')
            yolo_model.to(device)
            self.model_objects['yolo'] = yolo_model
            print(f"✓ YOLOv8 initialized on device: {device}")
        except Exception as e:
            print(f"✗ YOLOv8 failed: {e}")

        # 3. MobileNet SSD
        try:
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            config_path = model_dir / "MobileNetSSD_deploy.prototxt"
            weights_path = model_dir / "MobileNetSSD_deploy.caffemodel"
            if config_path.exists() and weights_path.exists():
                net = cv2.dnn.readNetFromCaffe(str(config_path), str(weights_path))
                self.model_objects['mobilenet'] = net
                print("✓ MobileNet SSD initialized")
            else:
                print("✗ MobileNet SSD files not found (download required)")
        except Exception as e:
            print(f"✗ MobileNet SSD failed: {e}")

        # 4. Haar Cascade
        try:
            cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_fullbody.xml')
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                self.model_objects['cascade'] = cascade
                print("✓ Haar Cascade initialized")
            else:
                print("✗ Haar Cascade file not found")
        except Exception as e:
            print(f"✗ Haar Cascade failed: {e}")

        # 5. Background Subtraction
        try:
            bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
            self.model_objects['background_subtraction'] = bg_subtractor
            print("✓ Background Subtraction initialized")
        except Exception as e:
            print(f"✗ Background Subtraction failed: {e}")

    def detect_people(self, frame):
        # Detect people in the frame using the currently selected model
        if self.current_model == 'hog':
            return self._detect_people_hog(frame)
        elif self.current_model == 'yolo':
            return self._detect_people_yolo(frame)
        elif self.current_model == 'mobilenet':
            return self._detect_people_mobilenet(frame)
        elif self.current_model == 'cascade':
            return self._detect_people_cascade(frame)
        elif self.current_model == 'background_subtraction':
            return self._detect_people_background_subtraction(frame)
        # Always return two values
        return np.array([]), np.array([])

    def _detect_people_hog(self, frame):
        # HOG + SVM (OpenCV) person detection
        boxes, weights = self.model_objects['hog'].detectMultiScale(frame, winStride=(8, 8))
        return boxes, weights

    def _detect_people_yolo(self, frame):
        # YOLOv8 (Ultralytics) person detection
        results = self.model_objects['yolo'].predict(frame, classes=[0])
        boxes = []
        weights = []
        for result in results:
            for detection in result.boxes:
                x1, y1, x2, y2 = map(int, detection.xyxy[0])
                boxes.append([x1, y1, x2, y2])
                weights.append(float(detection.conf[0]) if hasattr(detection, 'conf') else 1.0)
        return np.array(boxes), np.array(weights)

    def _detect_people_mobilenet(self, frame):
        # MobileNet SSD (OpenCV DNN) person detection
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self.model_objects['mobilenet'].setInput(blob)
        detections = self.model_objects['mobilenet'].forward()
        boxes = []
        weights = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.2:  # Confidence threshold
                x1 = int(detections[0, 0, i, 3] * frame.shape[1])
                y1 = int(detections[0, 0, i, 4] * frame.shape[0])
                x2 = int(detections[0, 0, i, 5] * frame.shape[1])
                y2 = int(detections[0, 0, i, 6] * frame.shape[0])
                boxes.append([x1, y1, x2, y2])
                weights.append(confidence)
        return np.array(boxes), np.array(weights)

    def _detect_people_cascade(self, frame):
        # Haar Cascade (OpenCV) person detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes = self.model_objects['cascade'].detectMultiScale(gray, 1.1, 4)
        weights = np.ones(len(boxes))  # No confidence scores from cascade
        return boxes, weights

    def _detect_people_background_subtraction(self, frame):
        # Background Subtraction + Contours
        fg_mask = self.model_objects['background_subtraction'].apply(frame)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        weights = []
        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Minimum contour area to filter out noise
                (x, y, w, h) = cv2.boundingRect(contour)
                boxes.append([x, y, x + w, y + h])
                weights.append(1.0)
        return np.array(boxes), np.array(weights)

    def track_people(self, boxes, frame):
        # Update tracking for detected people
        for box in boxes:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            detected_point = (center_x, center_y)

            # Find the closest track to the detected person
            closest_track_id = None
            min_distance = float("inf")
            for track_id, track in self.person_tracks.items():
                track_point = track[-1]  # Get the last point of the track
                distance = np.linalg.norm(np.array(detected_point) - np.array(track_point))
                if distance < min_distance:
                    min_distance = distance
                    closest_track_id = track_id

            # If the detected person is close to an existing track, update the track
            if closest_track_id is not None and min_distance < 50:
                self.person_tracks[closest_track_id].append(detected_point)
            else:
                # New detection, create a new track
                self.track_id += 1
                self.person_tracks[self.track_id] = [detected_point]

        # Remove old tracks
        current_time = time.time()
        for track_id in list(self.person_tracks.keys()):
            if current_time - self.person_tracks[track_id][-1][0] > 5:
                del self.person_tracks[track_id]

    def alert_close_proximity(self, frame):
        # Alert if two or more people are close to each other
        close_pairs = []
        boxes = [track[-1] for track in self.person_tracks.values()]

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                x1, y1, x2, y2 = boxes[i] + boxes[j]
                distance = np.linalg.norm(np.array([(x1 + x2) / 2, (y1 + y2) / 2]) - np.array([(x1 + x2) / 2, (y1 + y2) / 2]))
                if distance < self.close_alert_distance:
                    close_pairs.append((i, j))

        # Draw boxes and alert for close pairs
        for i, j in close_pairs:
            x1, y1, x2, y2 = boxes[i] + boxes[j]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "Close Proximity Alert!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    def track_movement(self, boxes, frame_center):
        """Track person movement and detect patterns"""
        current_time = time.time()
        frame_height, frame_width = frame_center

        alerts = []
        active_track_ids = set()

        for box in boxes:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Find closest existing track or create new one
            min_distance = float('inf')
            closest_track = None

            for track_id, track_data in self.person_tracks.items():
                if track_data['positions']:
                    last_pos = track_data['positions'][-1]
                    dist = np.sqrt((center_x - last_pos[0])**2 + (center_y - last_pos[1])**2)
                    if dist < min_distance and dist < 100:  # Maximum movement threshold
                        min_distance = dist
                        closest_track = track_id

            if closest_track is None:
                # Create new track
                self.track_id += 1
                self.person_tracks[self.track_id] = {
                    'positions': deque(maxlen=30),  # Keep last 30 positions
                    'timestamps': deque(maxlen=30),
                }
                closest_track = self.track_id

            # Update track
            track = self.person_tracks[closest_track]
            track['positions'].append((center_x, center_y))
            track['timestamps'].append(current_time)

            active_track_ids.add(closest_track)

            # Close distance alert logic only
            distance = self.calculate_distance_to_camera(box)
            if closest_track not in self.close_tracks:
                self.close_tracks[closest_track] = {
                    'start_time': None,
                    'last_seen': current_time,
                    'alerted': False
                }
            close_track = self.close_tracks[closest_track]
            close_track['last_seen'] = current_time
            if distance < self.close_alert_distance:
                if close_track['start_time'] is None:
                    close_track['start_time'] = current_time
                elif not close_track['alerted'] and (current_time - close_track['start_time'] >= self.close_alert_time):
                    alerts.append(f"Person {closest_track} is too close to the camera! (Dist: {distance:.2f})")
                    close_track['alerted'] = True
            else:
                close_track['start_time'] = None
                close_track['alerted'] = False

        # Clean up old tracks
        tracks_to_remove = []
        for track_id, close_track in self.close_tracks.items():
            if track_id not in active_track_ids and current_time - close_track['last_seen'] > 5:
                tracks_to_remove.append(track_id)

        for track_id in tracks_to_remove:
            if track_id in self.person_tracks:
                del self.person_tracks[track_id]
            if track_id in self.close_tracks:
                del self.close_tracks[track_id]

        return alerts

    def draw_detections(self, frame, boxes, alerts):
        """Draw bounding boxes and information on frame"""
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Show distance above each box
            distance = self.calculate_distance_to_camera(box)
            cv2.putText(frame, f"Dist: {distance:.2f}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        # Display current model
        cv2.putText(frame, f"Model: {self.models[self.current_model]}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        # Display FPS
        if self.fps_history:
            avg_fps = np.mean(list(self.fps_history))
            cv2.putText(frame, f"FPS: {avg_fps:.1f}",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        # Display alerts
        for i, alert in enumerate(alerts):
            cv2.putText(frame, alert, (10, 90 + i*30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # Display statistics
        stats = [
            f"People detected: {len(boxes)}",
            f"Total detections: {self.detection_count}",
            f"Approach alerts: {self.approach_alerts}",
            f"Pacing alerts: {self.pacing_alerts}"
        ]
        for i, stat in enumerate(stats):
            cv2.putText(frame, stat, (10, frame.shape[0] - 120 + i*20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        # On-screen notification overlay (flashing)
        if self.notification_message:
            now = time.time()
            elapsed = now - self.notification_start_time
            if elapsed < self.notification_duration:
                # Flashing effect
                if now - self.last_flash_time > self.notification_flash_interval:
                    self.notification_flash = not self.notification_flash
                    self.last_flash_time = now
                if self.notification_flash:
                    overlay = frame.copy()
                    h, w = frame.shape[:2]
                    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1)
                    alpha = 0.4
                    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                    cv2.putText(frame, self.notification_message, (int(w*0.1), int(h*0.5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 6, cv2.LINE_AA)
            else:
                self.notification_message = None
        return frame

    def calculate_distance_to_camera(self, box):
        """Estimate distance from camera to detected person"""
        # Assuming box is in [x1, y1, x2, y2] format
        # Calculate the width of the detected person in the image
        person_width_pixels = box[2] - box[0]

        # Assuming a constant real-world width for a person (e.g., 0.5 meters)
        REAL_PERSON_WIDTH = 0.5  # meters

        # Focal length estimation (this should be calibrated for your camera)
        FOCAL_LENGTH = 800  # pixels (example value, needs calibration)

        # Distance calculation using the formula:
        # distance = (REAL_PERSON_WIDTH * FOCAL_LENGTH) / person_width_pixels
        distance = (REAL_PERSON_WIDTH * FOCAL_LENGTH) / person_width_pixels if person_width_pixels > 0 else 0

        return distance

    def trigger_notification(self, message):
        """Trigger an on-screen notification"""
        self.notification_message = message
        self.notification_start_time = time.time()
        self.notification_flash = True
        self.last_flash_time = time.time()

    def run(self):
        # Main detection and tracking loop
        cap = cv2.VideoCapture(0)
        time.sleep(2)  # Allow camera to warm up

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect people in the frame
            boxes = self.detect_people(frame)

            # Track detected people
            self.track_people(boxes, frame)

            # Alert for close proximity
            self.alert_close_proximity(frame)

            # Track movement
            self.track_movement(boxes, frame.shape[:2])

            # Display the frame with detections and alerts
            cv2.imshow("People Detection and Tracking", frame)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Switch detection model
                model_keys = list(self.models.keys())
                current_index = model_keys.index(self.current_model)
                self.current_model = model_keys[(current_index + 1) % len(model_keys)]
                print(f"Switched to model: {self.models[self.current_model]}")

        cap.release()
        cv2.destroyAllWindows()
