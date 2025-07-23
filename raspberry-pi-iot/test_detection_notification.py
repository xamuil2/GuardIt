#!/usr/bin/env python3
"""
Test script to simulate a person detection and verify notification delivery to iOS app
"""

import requests
import time

# Server configuration
SERVER_URL = "http://10.103.139.13:8080"

def test_detection_notification():
    """Test the complete detection notification flow"""
    
    print("🧪 Testing Detection Notification System")
    print("=" * 50)
    
    # 1. Check initial status
    print("1. Checking detection status...")
    try:
        response = requests.get(f"{SERVER_URL}/detection/status")
        status = response.json()
        print(f"   Detection enabled: {status['detection_enabled']}")
        print(f"   Camera streaming: {status['camera_streaming']}")
        print(f"   Person detected: {status['detector_status']['person_detected']}")
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
        return
    
    # 2. Enable detection if not already enabled
    if not status['detection_enabled']:
        print("2. Enabling detection...")
        try:
            response = requests.post(f"{SERVER_URL}/detection/enable")
            result = response.json()
            print(f"   ✅ {result['message']}")
        except Exception as e:
            print(f"   ❌ Error enabling detection: {e}")
            return
    else:
        print("2. Detection already enabled ✅")
    
    # 3. Check buzzer status before test
    print("3. Checking buzzer status before test...")
    try:
        response = requests.get(f"{SERVER_URL}/buzzer/status")
        buzzer_status = response.json()
        print(f"   Buzzer active: {buzzer_status['active']}")
        print(f"   Last trigger: {buzzer_status.get('last_trigger', 'None')}")
    except Exception as e:
        print(f"   ❌ Error checking buzzer: {e}")
    
    # 4. Simulate detection by manually triggering buzzer
    print("4. Manually triggering buzzer to simulate detection...")
    try:
        response = requests.post(f"{SERVER_URL}/buzzer/trigger", 
                               json={"duration": 2, "message": "Test Detection Alert!"})
        result = response.json()
        print(f"   ✅ {result['message']}")
        print("   🔊 Buzzer should be sounding for 2 seconds...")
    except Exception as e:
        print(f"   ❌ Error triggering buzzer: {e}")
        return
    
    # 5. Wait and check buzzer status after trigger
    print("5. Waiting 3 seconds then checking buzzer status...")
    time.sleep(3)
    try:
        response = requests.get(f"{SERVER_URL}/buzzer/status")
        buzzer_status = response.json()
        print(f"   Buzzer active: {buzzer_status['active']}")
        print(f"   Last trigger: {buzzer_status.get('last_trigger', 'None')}")
        print(f"   Message: {buzzer_status.get('message', 'None')}")
    except Exception as e:
        print(f"   ❌ Error checking buzzer: {e}")
    
    # 6. Final detection status check
    print("6. Final detection status check...")
    try:
        response = requests.get(f"{SERVER_URL}/detection/status")
        status = response.json()
        print(f"   Active tracks: {status['detector_status']['active_tracks']}")
        print(f"   Last detection time: {status['detector_status']['last_detection_time']}")
    except Exception as e:
        print(f"   ❌ Error checking final status: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("• Manual buzzer trigger simulates detection notification")
    print("• Check your iOS app - it should show the notification")
    print("• The buzzer endpoint acts as the notification system")
    print("• When real detection occurs, it will trigger the same notification flow")

if __name__ == "__main__":
    test_detection_notification()
