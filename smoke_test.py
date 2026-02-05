#!/usr/bin/env python3
"""
Smoke tests for ANT HILL
Quick validation that all critical endpoints work
"""

import requests
import sys

API_URL = "http://localhost:8000/api"
BASE_URL = "http://localhost:8000"

def test(name: str, fn):
    """Run a test and print result."""
    try:
        print(f"  Testing: {name}...", end=" ")
        fn()
        print("✅")
        return True
    except AssertionError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 ANT HILL Smoke Tests")
    print("=" * 50)
    print()

    tests_passed = 0
    tests_total = 0

    # Health Check
    print("1️⃣  Backend Health")
    tests_total += 1
    if test("Health endpoint", lambda: check_health()):
        tests_passed += 1
    print()

    # Tasks & Marketplace
    print("2️⃣  Tasks & Marketplace")
    tests_total += 3

    def check_tasks():
        r = requests.get(f"{API_URL}/tasks")
        assert r.status_code == 200, f"Status {r.status_code}"
        assert isinstance(r.json(), list), "Response not a list"

    def check_marketplace():
        r = requests.get(f"{API_URL}/tasks/marketplace")
        assert r.status_code == 200, f"Status {r.status_code}"
        assert isinstance(r.json(), list), "Response not a list"

    def check_columns():
        r = requests.get(f"{API_URL}/columns")
        assert r.status_code == 200, f"Status {r.status_code}"
        assert isinstance(r.json(), list), "Response not a list"

    if test("Get all tasks", check_tasks):
        tests_passed += 1
    if test("Get marketplace tasks", check_marketplace):
        tests_passed += 1
    if test("Get columns", check_columns):
        tests_passed += 1
    print()

    # Leaderboard
    print("3️⃣  Leaderboard")
    tests_total += 4

    for period in ['daily', 'weekly', 'monthly', 'all-time']:
        def check_leaderboard(p=period):
            r = requests.get(f"{API_URL}/leaderboard/{p}")
            assert r.status_code == 200, f"Status {r.status_code}"
            assert isinstance(r.json(), list), "Response not a list"

        if test(f"Get {period} leaderboard", check_leaderboard):
            tests_passed += 1
    print()

    # Notifications
    print("4️⃣  Notifications")
    tests_total += 4

    def check_notifications():
        r = requests.get(f"{API_URL}/notifications/me?user_id=user_petr")
        assert r.status_code == 200, f"Status {r.status_code}"
        assert isinstance(r.json(), list), "Response not a list"

    def check_unread_count():
        r = requests.get(f"{API_URL}/notifications/unread-count?user_id=user_petr")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert 'unread_count' in data, "Missing unread_count"
        assert isinstance(data['unread_count'], int), "unread_count not int"

    def check_poll():
        r = requests.get(f"{API_URL}/notifications/poll?since=2024-01-01T00:00:00&user_id=user_petr")
        assert r.status_code == 200, f"Status {r.status_code}"
        assert isinstance(r.json(), list), "Response not a list"

    def check_create_test():
        r = requests.post(f"{API_URL}/notifications/test/create-sample")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert 'id' in data, "Missing notification id"

    if test("Get notifications", check_notifications):
        tests_passed += 1
    if test("Get unread count", check_unread_count):
        tests_passed += 1
    if test("Poll notifications", check_poll):
        tests_passed += 1
    if test("Create test notification", check_create_test):
        tests_passed += 1
    print()

    # Time Tracking
    print("5️⃣  Time Tracking")
    tests_total += 1

    def check_active_log():
        r = requests.get(f"{API_URL}/time-tracking/active?user_id=user_petr")
        assert r.status_code == 200, f"Status {r.status_code}"
        # Can be null if no active tracking

    if test("Get active time log", check_active_log):
        tests_passed += 1
    print()

    # Summary
    print("=" * 50)
    print(f"📊 Results: {tests_passed}/{tests_total} tests passed")
    print()

    if tests_passed == tests_total:
        print("✅ All smoke tests passed!")
        print("🚀 System is ready for E2E testing")
        sys.exit(0)
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed")
        print("🔧 Fix issues before proceeding to E2E tests")
        sys.exit(1)

def check_health():
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    assert data['status'] in ['ok', 'degraded'], f"Status: {data['status']}"
    assert data['database'] == 'ok', f"Database: {data['database']}"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
