import cv2
import numpy as np
import time
from collections import deque
import threading
import logging

logger = logging.getLogger(__name__)

class GuardItPersonDetector:

    def __init__(self):
        self.detection_enabled = True
        self.person_detected = False
        self.last_detection_time = 0
        self.detection_cooldown = 2000
        self.detection_threshold = 0.3
        self.person_tracks = {}
        self.track_id = 0
        self.last_cleanup_time = 0
        self.cleanup_interval = 5000
        
        # Proximity detection settings
        self.proximity_alert_enabled = True
        self.last_proximity_alert_time = 0
        self.proximity_cooldown = 2000  # 2 seconds between proximity alerts
        self.close_distance_threshold = 0.4  # Objects closer than 40% of frame trigger alert (more sensitive)
        self.minimum_object_size = 0.08  # Lower minimum size ratio (more sensitive)
        
        self.models = {}
        self._initialize_models()
        
        self.current_model = 'hog'
        
        logger.info("GuardIt Person Detector initialized with proximity detection")
    
    def _initialize_models(self):
        
        try:
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.models['hog'] = hog
            logger.info("✅ HOG + SVM detector loaded")
        except Exception as e:
            logger.warning(f"❌ Failed to load HOG detector: {e}")
        
        try:
            import os
            cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_fullbody.xml')
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                self.models['cascade'] = cascade
                logger.info("✅ Haar Cascade detector loaded")
        except Exception as e:
            logger.warning(f"❌ Failed to load Haar Cascade: {e}")
        
        try:
            bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
            self.models['background'] = bg_subtractor
            logger.info("✅ Background Subtraction detector loaded")
        except Exception as e:
            logger.warning(f"❌ Failed to load Background Subtraction: {e}")
    
    def detect_person(self, frame):
        
        if not self.detection_enabled or self.current_model not in self.models:
            return False, [], 0.0
        
        try:
            if self.current_model == 'hog':
                return self._detect_hog(frame)
            elif self.current_model == 'cascade':
                return self._detect_cascade(frame)
            elif self.current_model == 'background':
                return self._detect_background(frame)
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return False, [], 0.0
        
        return False, [], 0.0
    
    def _detect_hog(self, frame):
        
        try:
            height, width = frame.shape[:2]
            scale_factor = min(640 / width, 480 / height)
            if scale_factor < 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                frame_resized = cv2.resize(frame, (new_width, new_height))
            else:
                frame_resized = frame
                scale_factor = 1.0
            
            boxes, weights = self.models['hog'].detectMultiScale(
                frame_resized, 
                winStride=(8, 8),
                padding=(8, 8),
                scale=1.05,
                useMeanshiftGrouping=False
            )
            
            if len(boxes) > 0:
                if scale_factor != 1.0:
                    boxes = boxes / scale_factor
                    boxes = boxes.astype(int)
                
                converted_boxes = []
                for (x, y, w, h) in boxes:
                    converted_boxes.append([x, y, x + w, y + h])
                
                max_confidence = float(np.max(weights)) if len(weights) > 0 else 1.0
                return True, converted_boxes, max_confidence
        
        except Exception as e:
            logger.error(f"HOG detection error: {e}")
        
        return False, [], 0.0
    
    def _detect_cascade(self, frame):
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            height, width = gray.shape
            scale_factor = min(640 / width, 480 / height)
            if scale_factor < 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray_resized = cv2.resize(gray, (new_width, new_height))
            else:
                gray_resized = gray
                scale_factor = 1.0
            
            boxes = self.models['cascade'].detectMultiScale(
                gray_resized, 
                scaleFactor=1.1, 
                minNeighbors=3,
                minSize=(30, 30)
            )
            
            if len(boxes) > 0:
                if scale_factor != 1.0:
                    boxes = boxes / scale_factor
                    boxes = boxes.astype(int)
                
                converted_boxes = []
                for (x, y, w, h) in boxes:
                    converted_boxes.append([x, y, x + w, y + h])
                
                return True, converted_boxes, 0.8
        
        except Exception as e:
            logger.error(f"Cascade detection error: {e}")
        
        return False, [], 0.0
    
    def _detect_background(self, frame):
        
        try:
            fg_mask = self.models['background'].apply(frame)
            
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boxes = []
            for contour in contours:
                if cv2.contourArea(contour) > 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = h / w if w > 0 else 0
                    if 1.5 <= aspect_ratio <= 4.0:
                        boxes.append([x, y, x + w, y + h])
            
            if len(boxes) > 0:
                return True, boxes, 0.7
        
        except Exception as e:
            logger.error(f"Background detection error: {e}")
        
        return False, [], 0.0
    
    def process_detection(self, frame):
        """Enhanced detection with proximity alerts"""
        current_time = time.time() * 1000
        
        detected, boxes, confidence = self.detect_person(frame)
        
        alert_triggered = False
        proximity_alert = False
        
        # Standard person detection alert
        if detected and confidence >= self.detection_threshold:
            if (current_time - self.last_detection_time) > self.detection_cooldown:
                alert_triggered = True
                self.last_detection_time = current_time
                self.person_detected = True
                logger.info(f"🚨 Person detected! Confidence: {confidence:.2f}")
            else:
                logger.debug(f"Person detected but in cooldown period")
        
        # Proximity detection alert
        if detected and self.proximity_alert_enabled:
            proximity_alert = self._check_proximity_alert(frame, boxes, current_time)
        
        # Draw detections on frame
        processed_frame = self._draw_detections(frame, boxes, detected, confidence, proximity_alert)
        
        # Cleanup old tracks
        if (current_time - self.last_cleanup_time) > self.cleanup_interval:
            self._cleanup_tracks(current_time)
            self.last_cleanup_time = current_time
        
        # Return both alert types
        return alert_triggered or proximity_alert, processed_frame
    
    def _check_proximity_alert(self, frame, boxes, current_time):
        """Check if any detected object is too close to the camera"""
        if not boxes:
            return False
            
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_width * frame_height
        
        # Check each detected object for proximity
        for box in boxes:
            x1, y1, x2, y2 = box
            
            # Calculate object dimensions and area
            obj_width = x2 - x1
            obj_height = y2 - y1
            obj_area = obj_width * obj_height
            
            # Calculate size ratio relative to frame
            size_ratio = obj_area / frame_area
            
            # Calculate approximate distance based on object size
            # Larger objects in frame = closer to camera
            if size_ratio > self.minimum_object_size:
                # More aggressive proximity detection
                # If object takes up more than threshold of screen = too close
                if size_ratio > self.close_distance_threshold:
                    if (current_time - self.last_proximity_alert_time) > self.proximity_cooldown:
                        self.last_proximity_alert_time = current_time
                        logger.warning(f"🚨 PROXIMITY ALERT! Object too close - Size ratio: {size_ratio:.3f} > {self.close_distance_threshold:.3f}")
                        return True
                    else:
                        logger.debug(f"Object too close (size: {size_ratio:.3f}) but in proximity cooldown")
        
        return False
    
    def _draw_detections(self, frame, boxes, detected, confidence, proximity_alert=False):
        """Enhanced drawing with proximity indicators"""
        frame_copy = frame.copy()
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_width * frame_height
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            
            # Calculate object size for proximity indication
            obj_width = x2 - x1
            obj_height = y2 - y1
            obj_area = obj_width * obj_height
            size_ratio = obj_area / frame_area
            
            # Choose color based on proximity
            if size_ratio > self.close_distance_threshold:
                # Red for objects that are too close
                color = (0, 0, 255)
                thickness = 3
                proximity_text = "TOO CLOSE!"
            elif size_ratio > (self.close_distance_threshold * 0.6):  # 60% of threshold
                # Orange for moderately close objects
                color = (0, 165, 255)
                thickness = 2
                proximity_text = "CLOSE"
            else:
                # Green for distant objects
                color = (0, 255, 0)
                thickness = 2
                proximity_text = "SAFE"
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, thickness)
            
            # Draw detection info
            cv2.putText(frame_copy, f"Person ({confidence:.2f})", 
                       (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw proximity info
            cv2.putText(frame_copy, f"{proximity_text} ({size_ratio:.2f})", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Status text
        status_text = f"Detection: {self.current_model.upper()} | "
        status_text += f"Detected: {len(boxes)} persons" if detected else "No detection"
        
        cv2.putText(frame_copy, status_text, (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Proximity alert indicator
        if proximity_alert:
            cv2.putText(frame_copy, "⚠️ PROXIMITY ALERT ACTIVE ⚠️", (10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame_copy
    
    def _cleanup_tracks(self, current_time):
        
        tracks_to_remove = []
        for track_id, track_data in self.person_tracks.items():
            if hasattr(track_data, 'last_seen'):
                if (current_time - track_data['last_seen']) > 10000:
                    tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.person_tracks[track_id]
    
    def enable_detection(self):
        
        self.detection_enabled = True
        logger.info("Person detection enabled")
    
    def disable_detection(self):
        
        self.detection_enabled = False
        logger.info("Person detection disabled")
    
    def set_model(self, model_name):
        
        if model_name in self.models:
            self.current_model = model_name
            logger.info(f"Switched to {model_name} detection model")
            return True
        else:
            logger.warning(f"Model {model_name} not available")
            return False
    
    def get_status(self):
        """Enhanced status with proximity detection info"""
        return {
            'enabled': self.detection_enabled,
            'current_model': self.current_model,
            'available_models': list(self.models.keys()),
            'person_detected': self.person_detected,
            'last_detection_time': self.last_detection_time,
            'active_tracks': len(self.person_tracks),
            'proximity_alert_enabled': self.proximity_alert_enabled,
            'proximity_threshold': self.close_distance_threshold,
            'last_proximity_alert': self.last_proximity_alert_time
        }
    
    def set_proximity_threshold(self, threshold):
        """Set proximity alert threshold (0.0 - 1.0)"""
        if 0.0 <= threshold <= 1.0:
            self.close_distance_threshold = threshold
            logger.info(f"Proximity threshold set to {threshold}")
            return True
        return False
    
    def enable_proximity_alerts(self):
        """Enable proximity-based alerts"""
        self.proximity_alert_enabled = True
        logger.info("Proximity alerts enabled")
        
    def disable_proximity_alerts(self):
        """Disable proximity-based alerts"""
        self.proximity_alert_enabled = False
        logger.info("Proximity alerts disabled")
