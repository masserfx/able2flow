#!/usr/bin/env python3
"""
Test script for ANT HILL Notifications System
Usage: python3 test_notifications.py [count]
"""

import sys
import time
import requests

API_URL = "http://localhost:8000/api"

def create_test_notification():
    """Create a sample notification via test endpoint."""
    try:
        response = requests.post(f"{API_URL}/notifications/test/create-sample")
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    print("🧪 Testing ANT HILL Notification System")
    print("=" * 50)
    print()
    print(f"Creating {count} sample notifications...")
    print()

    success_count = 0
    for i in range(1, count + 1):
        print(f"[{i}/{count}] Creating notification...")

        result = create_test_notification()
        if result:
            print(f"✅ Success: {result.get('title')}")
            success_count += 1
        else:
            print("❌ Failed to create notification")

        # Wait 2 seconds between notifications (simulating real-time flow)
        if i < count:
            print("   Waiting 2 seconds...")
            time.sleep(2)

        print()

    print("=" * 50)
    print(f"✅ Test completed! ({success_count}/{count} successful)")
    print()
    print("📊 You should now see:")
    print(f"  - {success_count} notifications in the notification bell")
    print("  - Toast popups appearing (if frontend is running)")
    print("  - Sound effects playing")
    print("  - Unread badge showing count")
    print()
    print("🔍 Check the frontend at: http://localhost:5173")
    print("🔔 Click the notification bell icon to see all notifications")

if __name__ == "__main__":
    main()
