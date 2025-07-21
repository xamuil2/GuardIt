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
        
        self.models = {}
        self._initialize_models()
        
        self.current_model = 'hog'
        
        logger.info("GuardIt Person Detector initialized")
    
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
        
        current_time = time.time() * 1000
        
        detected, boxes, confidence = self.detect_person(frame)
        
        alert_triggered = False
        
        if detected and confidence >= self.detection_threshold:
            if (current_time - self.last_detection_time) > self.detection_cooldown:
                alert_triggered = True
                self.last_detection_time = current_time
                self.person_detected = True
                logger.info(f"🚨 Person detected! Confidence: {confidence:.2f}")
            else:
                logger.debug(f"Person detected but in cooldown period")
        
        processed_frame = self._draw_detections(frame, boxes, detected, confidence)
        
        if (current_time - self.last_cleanup_time) > self.cleanup_interval:
            self._cleanup_tracks(current_time)
            self.last_cleanup_time = current_time
        
        return alert_triggered, processed_frame
    
    def _draw_detections(self, frame, boxes, detected, confidence):
        
        frame_copy = frame.copy()
        
        for box in boxes:
            x1, y1, x2, y2 = box
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_copy, f"Person ({confidence:.2f})", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        status_text = f"Detection: {self.current_model.upper()} | "
        status_text += f"Detected: {len(boxes)} persons" if detected else "No detection"
        
        cv2.putText(frame_copy, status_text, (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
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
        
        return {
            'enabled': self.detection_enabled,
            'current_model': self.current_model,
            'available_models': list(self.models.keys()),
            'person_detected': self.person_detected,
            'last_detection_time': self.last_detection_time,
            'active_tracks': len(self.person_tracks)
        }
