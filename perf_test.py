#!/usr/bin/env python3
"""
Performance testing script for ANT HILL API
Tests API endpoint latency and throughput
"""

import requests
import time
import statistics
import sys
from typing import Dict, List

API_URL = "http://localhost:8000/api"

def test_endpoint(url: str, count: int = 100, method: str = "GET", json_data: dict = None) -> Dict:
    """Test endpoint performance."""
    latencies: List[float] = []
    errors = 0

    print(f"  Testing {count} requests...", end="", flush=True)

    for i in range(count):
        try:
            start = time.time()
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=json_data, timeout=5)
            else:
                raise ValueError(f"Unsupported method: {method}")

            latency = (time.time() - start) * 1000
            latencies.append(latency)

            if response.status_code >= 400:
                errors += 1

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(".", end="", flush=True)

        except Exception as e:
            errors += 1
            print(f"E", end="", flush=True)

    print(" Done!")

    if not latencies:
        return {
            'error': 'All requests failed',
            'errors': errors,
            'count': count
        }

    sorted_latencies = sorted(latencies)
    p50_idx = int(len(sorted_latencies) * 0.50)
    p95_idx = int(len(sorted_latencies) * 0.95)
    p99_idx = int(len(sorted_latencies) * 0.99)

    return {
        'count': count,
        'errors': errors,
        'min': min(latencies),
        'max': max(latencies),
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'p50': sorted_latencies[p50_idx],
        'p95': sorted_latencies[p95_idx],
        'p99': sorted_latencies[p99_idx],
        'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0
    }

def check_target(value: float, target: float, name: str) -> bool:
    """Check if value meets target."""
    status = "✅" if value < target else "❌"
    print(f"    {name}: {value:.2f}ms (target: <{target}ms) {status}")
    return value < target

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print("⚡ ANT HILL Performance Testing")
    print("=" * 60)
    print()

    # Test health endpoint first
    try:
        response = requests.get(f"{API_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed!")
            print("   Make sure backend is running: cd apps/backend && uv run python main.py")
            sys.exit(1)
        print("✅ Backend health check passed")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure backend is running on http://localhost:8000")
        sys.exit(1)

    print()
    print(f"Running {count} requests per endpoint...")
    print()

    endpoints = [
        {
            'name': 'Marketplace Tasks',
            'url': f'{API_URL}/tasks/marketplace',
            'method': 'GET',
            'target_p95': 100,
            'target_p99': 200
        },
        {
            'name': 'Weekly Leaderboard',
            'url': f'{API_URL}/leaderboard/weekly',
            'method': 'GET',
            'target_p95': 100,
            'target_p99': 200
        },
        {
            'name': 'Notifications Poll',
            'url': f'{API_URL}/notifications/poll?since=2024-01-01T00:00:00&user_id=user_petr',
            'method': 'GET',
            'target_p95': 50,
            'target_p99': 100
        },
        {
            'name': 'Unread Count',
            'url': f'{API_URL}/notifications/unread-count?user_id=user_petr',
            'method': 'GET',
            'target_p95': 30,
            'target_p99': 50
        },
    ]

    results = []
    all_passed = True

    for endpoint in endpoints:
        print(f"📊 {endpoint['name']}")
        result = test_endpoint(endpoint['url'], count, endpoint['method'])

        if 'error' in result:
            print(f"  ❌ {result['error']}")
            all_passed = False
            continue

        print(f"  📈 Results:")
        print(f"    Min:    {result['min']:.2f}ms")
        print(f"    Mean:   {result['mean']:.2f}ms")
        print(f"    Median: {result['median']:.2f}ms")

        # Check targets
        p95_ok = check_target(result['p95'], endpoint['target_p95'], 'p95')
        p99_ok = check_target(result['p99'], endpoint['target_p99'], 'p99')

        print(f"    Max:    {result['max']:.2f}ms")
        print(f"    StdDev: {result['stdev']:.2f}ms")

        if result['errors'] > 0:
            print(f"  ⚠️  Errors: {result['errors']}/{result['count']}")
            all_passed = False

        if not (p95_ok and p99_ok):
            all_passed = False

        results.append({
            'endpoint': endpoint['name'],
            'result': result,
            'passed': p95_ok and p99_ok and result['errors'] == 0
        })

        print()

    # Summary
    print("=" * 60)
    print("📊 Summary")
    print()

    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)

    for r in results:
        status = "✅ PASS" if r['passed'] else "❌ FAIL"
        print(f"  {status} - {r['endpoint']}")

    print()
    print(f"Results: {passed_count}/{total_count} endpoints passed")

    if all_passed:
        print()
        print("✅ All performance targets met!")
        sys.exit(0)
    else:
        print()
        print("❌ Some endpoints failed to meet performance targets")
        sys.exit(1)

if __name__ == "__main__":
    main()
