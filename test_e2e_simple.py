#!/usr/bin/env python3
"""E2E test ANT HILL aplikace - verze bez browser automation"""

import requests
import time
import json
from datetime import datetime

def test_backend_health():
    """Test 1: Backend Health Check"""
    print("\n📡 TEST 1: Backend Health Check")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        data = response.json()

        if data.get("status") == "ok":
            print("✅ Backend health check - status OK")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print("❌ Backend health check - status není OK")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return False
    except Exception as e:
        print(f"❌ Backend health check - endpoint nedostupný: {e}")
        return False

def test_frontend_availability():
    """Test 2: Frontend Landing Page"""
    print("\n🏠 TEST 2: Frontend Landing Page")
    try:
        response = requests.get("http://localhost:5173", timeout=5)

        if response.status_code == 200:
            print("✅ Frontend landing page načten")
            print(f"   Status code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            return True
        else:
            print(f"❌ Frontend landing page - neočekávaný status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend landing page - nedostupný: {e}")
        return False

def test_marketplace_api():
    """Test 3: Marketplace API (backend endpoint)"""
    print("\n🎯 TEST 3: Marketplace API")
    try:
        # Zkusím najít tasks endpoint
        endpoints = [
            "http://localhost:8000/api/tasks",
            "http://localhost:8000/tasks",
            "http://localhost:8000/api/marketplace",
            "http://localhost:8000/marketplace"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Marketplace API dostupné na: {endpoint}")
                    print(f"   Počet tasků: {len(data) if isinstance(data, list) else 'N/A'}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   První task: {data[0].get('title', 'N/A')}")
                    return True
            except:
                continue

        print("❌ Marketplace API - žádný endpoint nenalezen")
        return False
    except Exception as e:
        print(f"❌ Marketplace API - chyba: {e}")
        return False

def test_notification_creation():
    """Test 4: Notification Creation"""
    print("\n🔔 TEST 4: Notification Creation")
    try:
        response = requests.get(
            "http://localhost:8000/api/notifications/test/create-sample",
            timeout=5
        )
        data = response.json()

        if data and data.get("id"):
            print(f"✅ Notification vytvořena s ID: {data.get('id')}")
            print(f"   Response: {json.dumps(data, indent=2)}")

            # Počkat chvíli a zkusit načíst notifikace
            print("⏳ Čekám 2 sekundy a zkusím načíst notifikace...")
            time.sleep(2)

            # Zkusit načíst notifikace
            notifications_endpoints = [
                "http://localhost:8000/api/notifications",
                "http://localhost:8000/notifications"
            ]

            for endpoint in notifications_endpoints:
                try:
                    notif_response = requests.get(endpoint, timeout=5)
                    if notif_response.status_code == 200:
                        notif_data = notif_response.json()
                        print(f"✅ Notifikace načteny z: {endpoint}")
                        print(f"   Počet notifikací: {len(notif_data) if isinstance(notif_data, list) else 'N/A'}")
                        break
                except:
                    continue

            return True
        else:
            print("❌ Notification response neobsahuje ID")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return False
    except Exception as e:
        print(f"❌ Notification creation - selhala: {e}")
        return False

def test_leaderboard_api():
    """Test 5: Leaderboard API"""
    print("\n🏆 TEST 5: Leaderboard API")
    try:
        endpoints = [
            "http://localhost:8000/api/leaderboard",
            "http://localhost:8000/leaderboard",
            "http://localhost:8000/api/users/leaderboard"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Leaderboard API dostupné na: {endpoint}")
                    print(f"   Počet uživatelů: {len(data) if isinstance(data, list) else 'N/A'}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Top uživatel: {data[0].get('name', 'N/A')} s {data[0].get('points', 'N/A')} body")
                    return True
            except:
                continue

        print("❌ Leaderboard API - žádný endpoint nenalezen")
        return False
    except Exception as e:
        print(f"❌ Leaderboard API - chyba: {e}")
        return False

def main():
    """Hlavní test runner"""
    print("=" * 60)
    print("🚀 E2E TEST ANT HILL APLIKACE")
    print(f"⏰ Čas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {
        "passed": [],
        "failed": []
    }

    # Spustit testy
    tests = [
        ("Backend Health", test_backend_health),
        ("Frontend Availability", test_frontend_availability),
        ("Marketplace API", test_marketplace_api),
        ("Notification Creation", test_notification_creation),
        ("Leaderboard API", test_leaderboard_api)
    ]

    for test_name, test_func in tests:
        result = test_func()
        if result:
            results["passed"].append(test_name)
        else:
            results["failed"].append(test_name)

    # Finální report
    print("\n" + "=" * 60)
    print("📊 E2E TEST REPORT - ANT HILL")
    print("=" * 60)

    print(f"\n✅ CO FUNGUJE ({len(results['passed'])}/{len(tests)}):")
    for item in results["passed"]:
        print(f"  ✅ {item}")

    print(f"\n❌ CO NEFUNGUJE ({len(results['failed'])}/{len(tests)}):")
    if not results["failed"]:
        print("  Vše funguje perfektně! 🎉")
    else:
        for item in results["failed"]:
            print(f"  ❌ {item}")

    print("\n" + "=" * 60)
    print(f"📈 Úspěšnost: {len(results['passed'])}/{len(tests)} ({100*len(results['passed'])//len(tests)}%)")
    print("=" * 60)

    # Uložit report
    report_content = f"""
E2E TEST REPORT - ANT HILL
Generated: {datetime.now().isoformat()}

✅ CO FUNGUJE ({len(results['passed'])}/{len(tests)}):
{chr(10).join(['  ✅ ' + item for item in results['passed']])}

❌ CO NEFUNGUJE ({len(results['failed'])}/{len(tests)}):
{chr(10).join(['  ❌ ' + item for item in results['failed']]) if results['failed'] else '  Vše funguje perfektně! 🎉'}

📈 Úspěšnost: {len(results['passed'])}/{len(tests)} ({100*len(results['passed'])//len(tests)}%)
"""

    with open("e2e_test_report.txt", "w") as f:
        f.write(report_content)

    print("\n📄 Report uložen do: e2e_test_report.txt")

if __name__ == "__main__":
    main()
