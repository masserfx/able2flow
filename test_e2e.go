package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Status string `json:"status"`
}

type TestResult struct {
	Passed []string
	Failed []string
}

func testBackendHealth() bool {
	fmt.Println("\n📡 TEST 1: Backend Health Check")
	client := &http.Client{Timeout: 5 * time.Second}

	resp, err := client.Get("http://localhost:8000/health")
	if err != nil {
		fmt.Printf("❌ Backend health check - endpoint nedostupný: %v\n", err)
		return false
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	var health HealthResponse
	if err := json.Unmarshal(body, &health); err != nil {
		fmt.Printf("❌ Backend health check - neplatný JSON: %v\n", err)
		return false
	}

	if health.Status == "ok" {
		fmt.Printf("✅ Backend health check - status OK\n")
		fmt.Printf("   Response: %s\n", string(body))
		return true
	}

	fmt.Printf("❌ Backend health check - status není OK\n")
	return false
}

func testFrontendAvailability() bool {
	fmt.Println("\n🏠 TEST 2: Frontend Landing Page")
	client := &http.Client{Timeout: 5 * time.Second}

	resp, err := client.Get("http://localhost:5173")
	if err != nil {
		fmt.Printf("❌ Frontend landing page - nedostupný: %v\n", err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		fmt.Printf("✅ Frontend landing page načten\n")
		fmt.Printf("   Status code: %d\n", resp.StatusCode)
		fmt.Printf("   Content-Type: %s\n", resp.Header.Get("Content-Type"))
		return true
	}

	fmt.Printf("❌ Frontend landing page - neočekávaný status: %d\n", resp.StatusCode)
	return false
}

func testMarketplaceAPI() bool {
	fmt.Println("\n🎯 TEST 3: Marketplace API")
	client := &http.Client{Timeout: 5 * time.Second}

	endpoints := []string{
		"http://localhost:8000/api/tasks",
		"http://localhost:8000/tasks",
		"http://localhost:8000/api/marketplace",
		"http://localhost:8000/marketplace",
	}

	for _, endpoint := range endpoints {
		resp, err := client.Get(endpoint)
		if err != nil {
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == 200 {
			body, _ := io.ReadAll(resp.Body)
			var data []map[string]interface{}
			if err := json.Unmarshal(body, &data); err == nil {
				fmt.Printf("✅ Marketplace API dostupné na: %s\n", endpoint)
				fmt.Printf("   Počet tasků: %d\n", len(data))
				if len(data) > 0 {
					if title, ok := data[0]["title"].(string); ok {
						fmt.Printf("   První task: %s\n", title)
					}
				}
				return true
			}
		}
	}

	fmt.Println("❌ Marketplace API - žádný endpoint nenalezen")
	return false
}

func testNotificationCreation() bool {
	fmt.Println("\n🔔 TEST 4: Notification Creation")
	client := &http.Client{Timeout: 5 * time.Second}

	resp, err := client.Get("http://localhost:8000/api/notifications/test/create-sample")
	if err != nil {
		fmt.Printf("❌ Notification creation - selhala: %v\n", err)
		return false
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var data map[string]interface{}
	if err := json.Unmarshal(body, &data); err != nil {
		fmt.Printf("❌ Notification response neobsahuje platný JSON: %v\n", err)
		return false
	}

	if id, ok := data["id"]; ok {
		fmt.Printf("✅ Notification vytvořena s ID: %v\n", id)
		fmt.Printf("   Response: %s\n", string(body))

		// Počkat a zkusit načíst notifikace
		fmt.Println("⏳ Čekám 2 sekundy a zkusím načíst notifikace...")
		time.Sleep(2 * time.Second)

		endpoints := []string{
			"http://localhost:8000/api/notifications",
			"http://localhost:8000/notifications",
		}

		for _, endpoint := range endpoints {
			notifResp, err := client.Get(endpoint)
			if err != nil {
				continue
			}
			defer notifResp.Body.Close()

			if notifResp.StatusCode == 200 {
				notifBody, _ := io.ReadAll(notifResp.Body)
				var notifData []interface{}
				if err := json.Unmarshal(notifBody, &notifData); err == nil {
					fmt.Printf("✅ Notifikace načteny z: %s\n", endpoint)
					fmt.Printf("   Počet notifikací: %d\n", len(notifData))
					break
				}
			}
		}
		return true
	}

	fmt.Println("❌ Notification response neobsahuje ID")
	return false
}

func testLeaderboardAPI() bool {
	fmt.Println("\n🏆 TEST 5: Leaderboard API")
	client := &http.Client{Timeout: 5 * time.Second}

	endpoints := []string{
		"http://localhost:8000/api/leaderboard",
		"http://localhost:8000/leaderboard",
		"http://localhost:8000/api/users/leaderboard",
		"http://localhost:8000/api/users",
	}

	for _, endpoint := range endpoints {
		resp, err := client.Get(endpoint)
		if err != nil {
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == 200 {
			body, _ := io.ReadAll(resp.Body)
			var data []map[string]interface{}
			if err := json.Unmarshal(body, &data); err == nil {
				fmt.Printf("✅ Leaderboard API dostupné na: %s\n", endpoint)
				fmt.Printf("   Počet uživatelů: %d\n", len(data))
				if len(data) > 0 {
					name := data[0]["name"]
					points := data[0]["points"]
					if name == nil {
						name = data[0]["username"]
					}
					if points == nil {
						points = data[0]["score"]
					}
					fmt.Printf("   Top uživatel: %v s %v body\n", name, points)
				}
				return true
			}
		}
	}

	fmt.Println("❌ Leaderboard API - žádný endpoint nenalezen")
	return false
}

func main() {
	fmt.Println("============================================================")
	fmt.Println("🚀 E2E TEST ANT HILL APLIKACE")
	fmt.Printf("⏰ Čas: %s\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("============================================================")

	results := TestResult{
		Passed: []string{},
		Failed: []string{},
	}

	tests := []struct {
		name string
		fn   func() bool
	}{
		{"Backend Health", testBackendHealth},
		{"Frontend Availability", testFrontendAvailability},
		{"Marketplace API", testMarketplaceAPI},
		{"Notification Creation", testNotificationCreation},
		{"Leaderboard API", testLeaderboardAPI},
	}

	for _, test := range tests {
		if test.fn() {
			results.Passed = append(results.Passed, test.name)
		} else {
			results.Failed = append(results.Failed, test.name)
		}
	}

	// Final report
	fmt.Println("\n============================================================")
	fmt.Println("📊 E2E TEST REPORT - ANT HILL")
	fmt.Println("============================================================")

	fmt.Printf("\n✅ CO FUNGUJE (%d/%d):\n", len(results.Passed), len(tests))
	for _, item := range results.Passed {
		fmt.Printf("  ✅ %s\n", item)
	}

	fmt.Printf("\n❌ CO NEFUNGUJE (%d/%d):\n", len(results.Failed), len(tests))
	if len(results.Failed) == 0 {
		fmt.Println("  Vše funguje perfektně! 🎉")
	} else {
		for _, item := range results.Failed {
			fmt.Printf("  ❌ %s\n", item)
		}
	}

	successRate := 0
	if len(tests) > 0 {
		successRate = (100 * len(results.Passed)) / len(tests)
	}

	fmt.Println("\n============================================================")
	fmt.Printf("📈 Úspěšnost: %d/%d (%d%%)\n", len(results.Passed), len(tests), successRate)
	fmt.Println("============================================================")

	// Save report
	report := fmt.Sprintf(`
E2E TEST REPORT - ANT HILL
Generated: %s

✅ CO FUNGUJE (%d/%d):
`, time.Now().Format(time.RFC3339), len(results.Passed), len(tests))

	for _, item := range results.Passed {
		report += fmt.Sprintf("  ✅ %s\n", item)
	}

	report += fmt.Sprintf("\n❌ CO NEFUNGUJE (%d/%d):\n", len(results.Failed), len(tests))
	if len(results.Failed) == 0 {
		report += "  Vše funguje perfektně! 🎉\n"
	} else {
		for _, item := range results.Failed {
			report += fmt.Sprintf("  ❌ %s\n", item)
		}
	}

	report += fmt.Sprintf("\n📈 Úspěšnost: %d/%d (%d%%)\n", len(results.Passed), len(tests), successRate)
	report += "\nPOZNÁMKY:\n"
	report += "- Test proběhl bez browser automation (pouze API testy)\n"
	report += "- Pro kompletní E2E test včetně UI je potřeba Playwright/Puppeteer\n"
	report += "- Všechny testy používají localhost:8000 (backend) a localhost:5173 (frontend)\n"

	reportPath := "/Users/lhradek/code/work/flowable/e2e_test_report.txt"
	if err := os.WriteFile(reportPath, []byte(report), 0644); err != nil {
		fmt.Printf("\n⚠️ Chyba při ukládání reportu: %v\n", err)
	} else {
		fmt.Printf("\n📄 Report uložen do: %s\n", reportPath)
	}

	if len(results.Failed) > 0 {
		os.Exit(1)
	}
}
