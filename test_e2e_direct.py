#!/usr/bin/env python3
"""E2E test ANT HILL aplikace - přímá verze bez shell dependencies"""

import urllib.request
import urllib.error
import json
import time
from datetime import datetime

def make_request(url, timeout=5):
    """Provede HTTP GET request bez použití requests knihovny"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            return {
                'status_code': response.status,
                'data': json.loads(data) if data else None,
                'headers': dict(response.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            'status_code': e.code,
            'data': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'status_code': None,
            'data': None,
            'error': str(e)
        }

def test_backend_health():
    """Test 1: Backend Health Check"""
    print("\n📡 TEST 1: Backend Health Check")
    try:
        result = make_request("http://localhost:8000/health")

        if result['status_code'] == 200 and result['data']:
            if result['data'].get("status") == "ok":
                print("✅ Backend health check - status OK")
                print(f"   Response: {json.dumps(result['data'], indent=2)}")
                return True
            else:
                print("❌ Backend health check - status není OK")
                print(f"   Response: {json.dumps(result['data'], indent=2)}")
                return False
        else:
            print(f"❌ Backend health check - neočekávaný status: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Backend health check - endpoint nedostupný: {e}")
        return False

def test_frontend_availability():
    """Test 2: Frontend Landing Page"""
    print("\n🏠 TEST 2: Frontend Landing Page")
    try:
        result = make_request("http://localhost:5173")

        if result['status_code'] == 200:
            print("✅ Frontend landing page načten")
            print(f"   Status code: {result['status_code']}")
            print(f"   Content-Type: {result['headers'].get('content-type', 'N/A')}")
            return True
        else:
            print(f"❌ Frontend landing page - status: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Frontend landing page - nedostupný: {e}")
        return False

def test_marketplace_api():
    """Test 3: Marketplace API (backend endpoint)"""
    print("\n🎯 TEST 3: Marketplace API")
    try:
        endpoints = [
            "http://localhost:8000/api/tasks",
            "http://localhost:8000/tasks",
            "http://localhost:8000/api/marketplace",
            "http://localhost:8000/marketplace"
        ]

        for endpoint in endpoints:
            result = make_request(endpoint)
            if result['status_code'] == 200 and result['data']:
                data = result['data']
                print(f"✅ Marketplace API dostupné na: {endpoint}")
                print(f"   Počet tasků: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   První task: {data[0].get('title', data[0].get('name', 'N/A'))}")
                return True

        print("❌ Marketplace API - žádný endpoint nenalezen")
        return False
    except Exception as e:
        print(f"❌ Marketplace API - chyba: {e}")
        return False

def test_notification_creation():
    """Test 4: Notification Creation"""
    print("\n🔔 TEST 4: Notification Creation")
    try:
        result = make_request("http://localhost:8000/api/notifications/test/create-sample")

        if result['status_code'] == 200 and result['data']:
            data = result['data']
            if data.get("id"):
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
                    notif_result = make_request(endpoint)
                    if notif_result['status_code'] == 200:
                        notif_data = notif_result['data']
                        print(f"✅ Notifikace načteny z: {endpoint}")
                        print(f"   Počet notifikací: {len(notif_data) if isinstance(notif_data, list) else 'N/A'}")
                        break

                return True
            else:
                print("❌ Notification response neobsahuje ID")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ Notification creation - neočekávaná odpověď: {result.get('error')}")
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
            "http://localhost:8000/api/users/leaderboard",
            "http://localhost:8000/api/users"
        ]

        for endpoint in endpoints:
            result = make_request(endpoint)
            if result['status_code'] == 200 and result['data']:
                data = result['data']
                print(f"✅ Leaderboard API dostupné na: {endpoint}")
                print(f"   Počet uživatelů: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    user = data[0]
                    print(f"   Top uživatel: {user.get('name', user.get('username', 'N/A'))} "
                          f"s {user.get('points', user.get('score', 'N/A'))} body")
                return True

        print("❌ Leaderboard API - žádný endpoint nenalezen")
        return False
    except Exception as e:
        print(f"❌ Leaderboard API - chyba: {e}")
        return False

def test_api_docs():
    """Bonus Test: API Documentation"""
    print("\n📚 BONUS TEST: API Documentation")
    try:
        endpoints = [
            "http://localhost:8000/docs",
            "http://localhost:8000/redoc",
            "http://localhost:8000/openapi.json"
        ]

        for endpoint in endpoints:
            result = make_request(endpoint)
            if result['status_code'] == 200:
                print(f"✅ API dokumentace dostupná na: {endpoint}")
                return True

        print("⚠️ API dokumentace nenalezena (není kritické)")
        return False
    except Exception as e:
        print(f"⚠️ API dokumentace - chyba: {e}")
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

    # Spustit hlavní testy
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

    # Bonus test
    print("\n" + "-" * 60)
    test_api_docs()
    print("-" * 60)

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
    success_rate = 100 * len(results['passed']) // len(tests) if tests else 0
    print(f"📈 Úspěšnost: {len(results['passed'])}/{len(tests)} ({success_rate}%)")
    print("=" * 60)

    # Uložit report
    report_content = f"""
E2E TEST REPORT - ANT HILL
Generated: {datetime.now().isoformat()}

✅ CO FUNGUJE ({len(results['passed'])}/{len(tests)}):
{chr(10).join(['  ✅ ' + item for item in results['passed']])}

❌ CO NEFUNGUJE ({len(results['failed'])}/{len(tests)}):
{chr(10).join(['  ❌ ' + item for item in results['failed']]) if results['failed'] else '  Vše funguje perfektně! 🎉'}

📈 Úspěšnost: {len(results['passed'])}/{len(tests)} ({success_rate}%)

POZNÁMKY:
- Test proběhl bez browser automation (pouze API testy)
- Pro kompletní E2E test včetně UI je potřeba Playwright/Puppeteer
- Všechny testy používají localhost:8000 (backend) a localhost:5173 (frontend)
"""

    report_path = "/Users/lhradek/code/work/flowable/e2e_test_report.txt"
    with open(report_path, "w") as f:
        f.write(report_content)

    print(f"\n📄 Report uložen do: {report_path}")

    # Návratový kód
    return 0 if not results['failed'] else 1

if __name__ == "__main__":
    exit(main())
