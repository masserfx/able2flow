# 🧪 Stage 6: E2E Testing & Polish

## Test Strategy

### Test Levels
1. **E2E User Flows** - Complete user journeys
2. **Responsive Testing** - Mobile/Tablet/Desktop
3. **Performance Testing** - API latency, render times
4. **Integration Testing** - Component interactions
5. **Bug Hunting** - Edge cases, error states

---

## 🎯 E2E Test Scenarios

### Scenario 1: Complete Marketplace Flow
**User Story:** As a developer, I want to claim a task from marketplace, track time, and earn points

**Steps:**
1. Navigate to http://localhost:5173
2. Click "🎯 Marketplace" in sidebar
3. Verify marketplace loads with tasks
4. Click "Vzít Task" on first available task
5. Verify toast notification appears: "🎯 [User] si vzal task!"
6. Navigate to "▦ Board"
7. Find the claimed task (should have 👤 badge)
8. Click on task to open modal
9. Verify ANT HILL section is visible
10. Click "▶️ Spustit Stopky"
11. Wait 30 seconds
12. Verify timer is running (showing MM:SS)
13. Click "⏹️ Zastavit"
14. Verify time spent updates
15. Check task as completed (checkbox)
16. Verify toast notification: "💎 [User] získal X bodů!"
17. Navigate to "🏆 Leaderboard"
18. Verify user appears in leaderboard with correct points
19. Navigate back to "🎯 Marketplace"
20. Verify task is no longer in marketplace

**Expected Results:**
- All steps complete without errors
- Notifications appear within 10 seconds
- Points calculated correctly
- Leaderboard updates
- Task removed from marketplace

**Performance Targets:**
- Page load < 2s
- API calls < 100ms
- Toast appears < 500ms after API response

---

### Scenario 2: Time Tracking Accuracy
**User Story:** As a developer, I want to accurately track time spent on tasks

**Steps:**
1. Create new task in BoardView
2. Set estimated_minutes = 10
3. Verify points badge shows "1 bod"
4. Assign task to self (via marketplace or directly)
5. Open task modal
6. Start timer
7. Wait exactly 60 seconds (use Date.now())
8. Stop timer
9. Verify time_spent shows ~1 minute (55-65s acceptable)
10. Start timer again
11. Wait 30 seconds
12. Stop timer
13. Verify cumulative time ~90 seconds
14. Complete task
15. Verify bonus calculation (if completed faster than estimate)

**Expected Results:**
- Timer accuracy ±5 seconds
- Cumulative time tracking works
- Bonus points awarded correctly

---

### Scenario 3: Notification System
**User Story:** As a team member, I want to see real-time notifications

**Steps:**
1. Open frontend in Browser 1
2. Click 🔔 notification bell
3. Verify dropdown shows current notifications
4. Run: `python3 test_notifications.py 3`
5. Wait up to 15 seconds
6. Verify 3 toast notifications appear
7. Verify sound plays for each
8. Verify unread badge shows "3"
9. Click notification bell
10. Click on first notification
11. Verify it marks as read (styling changes)
12. Verify unread badge decrements to "2"
13. Click "Označit vše jako přečtené"
14. Verify badge disappears
15. Verify all notifications marked as read

**Expected Results:**
- Polling works (10s interval)
- Toasts appear automatically
- Sound plays
- Mark as read functions correctly
- No duplicate notifications

---

### Scenario 4: Leaderboard Dynamics
**User Story:** As a competitive developer, I want to see my ranking

**Steps:**
1. Navigate to 🏆 Leaderboard
2. Verify current period (Weekly by default)
3. Complete a task worth 5 points
4. Refresh leaderboard
5. Verify points updated
6. Switch to "Denní" tab
7. Verify points match
8. Switch to "Měsíční"
9. Verify cumulative monthly points
10. Switch to "Celkově"
11. Verify all-time points
12. Complete another task (3 points)
13. Refresh
14. Verify all periods updated (+3 points each)

**Expected Results:**
- All periods track correctly
- Points accumulate
- Rankings update
- User summary card shows correct stats

---

### Scenario 5: Multi-Tab Sync
**User Story:** As a user with multiple tabs open, I want consistent state

**Steps:**
1. Open frontend in Tab 1
2. Open frontend in Tab 2 (same browser)
3. In Tab 1: Claim a task from marketplace
4. In Tab 2: Refresh marketplace
5. Verify task is gone
6. In Tab 1: Complete the task
7. In Tab 2: Wait up to 15 seconds
8. Verify notification appears in Tab 2
9. In Tab 2: Click notification bell
10. Verify notification is there
11. In Tab 1: Mark notification as read
12. In Tab 2: Refresh notifications
13. Verify marked as read in Tab 2

**Expected Results:**
- State syncs across tabs
- Notifications appear in all tabs
- No race conditions
- Consistent data

---

## 📱 Responsive Testing

### Mobile (375px - iPhone SE)
**Test Points:**
- [ ] Navigation menu works (sidebar)
- [ ] Marketplace cards stack vertically
- [ ] "Vzít Task" button accessible
- [ ] Task modal fits screen
- [ ] TimeTracker buttons usable
- [ ] Leaderboard table scrollable
- [ ] Toast notifications fit screen
- [ ] Notification bell accessible
- [ ] No horizontal scroll

**Commands:**
```javascript
// Browser DevTools
window.resizeTo(375, 667)
// Or use DevTools Device Toolbar (Cmd+Shift+M)
```

### Tablet (768px - iPad)
**Test Points:**
- [ ] 2-column layouts work
- [ ] Kanban board scrollable horizontally
- [ ] Marketplace grid (2 columns)
- [ ] Leaderboard readable
- [ ] Modals centered
- [ ] Touch targets ≥44px

### Desktop (1920px)
**Test Points:**
- [ ] Marketplace grid (3-4 columns)
- [ ] Leaderboard full width
- [ ] All features accessible
- [ ] No layout breaks
- [ ] Optimal spacing

---

## ⚡ Performance Testing

### API Performance
**Target:** < 100ms p95

```bash
# Test script
for i in {1..100}; do
  START=$(date +%s%3N)
  curl -s http://localhost:8000/api/tasks/marketplace > /dev/null
  END=$(date +%s%3N)
  DIFF=$((END - START))
  echo "Request $i: ${DIFF}ms"
done | awk '{sum+=$3; count++} END {print "Average:", sum/count "ms"}'
```

**Endpoints to test:**
- GET /api/tasks/marketplace
- GET /api/leaderboard/weekly
- GET /api/notifications/poll
- POST /api/time-tracking/start
- POST /api/time-tracking/stop

**Acceptance Criteria:**
- p50 < 50ms
- p95 < 100ms
- p99 < 200ms

### Frontend Performance
**Metrics:**
- First Contentful Paint < 1.5s
- Time to Interactive < 3s
- Largest Contentful Paint < 2.5s

**Tools:**
- Chrome DevTools Lighthouse
- Network tab (disable cache)
- Performance tab (record + analyze)

---

## 🐛 Bug Hunting Checklist

### Edge Cases
- [ ] Task with 0 estimated_minutes (should show 1 point minimum)
- [ ] Negative time tracking (stop without start)
- [ ] Claim already assigned task (should error)
- [ ] Complete task without assignment (should not award points)
- [ ] Extremely long task titles (truncation)
- [ ] Empty marketplace (empty state)
- [ ] No notifications (empty state)
- [ ] Offline mode (API errors)
- [ ] Multiple simultaneous time trackers (should only allow one active)

### Data Validation
- [ ] Task estimated_minutes accepts only positive integers
- [ ] Points calculation never negative
- [ ] Time tracking duration never negative
- [ ] Notification polling doesn't duplicate
- [ ] Leaderboard handles ties correctly

### UI/UX
- [ ] Loading states visible
- [ ] Error messages clear
- [ ] Success feedback immediate
- [ ] Animations smooth (60fps)
- [ ] Hover states consistent
- [ ] Focus states accessible (keyboard nav)

---

## 🎨 Polish Checklist

### Visual
- [ ] Consistent spacing (8px grid)
- [ ] Color palette consistent (Tokyo Night)
- [ ] Typography hierarchy clear
- [ ] Icons aligned
- [ ] Gradients smooth
- [ ] Shadows consistent

### Interactions
- [ ] Hover states on all buttons
- [ ] Loading spinners on async actions
- [ ] Disabled states clear
- [ ] Animations not too fast/slow
- [ ] Toast auto-dismiss timing good
- [ ] Modal backdrop dismisses on click

### Accessibility
- [ ] Alt text on images
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation works
- [ ] Focus visible
- [ ] Color contrast WCAG AA
- [ ] Screen reader friendly

### Error Handling
- [ ] API errors show user-friendly messages
- [ ] Network errors handled gracefully
- [ ] Form validation clear
- [ ] Retry mechanisms where appropriate
- [ ] Fallback for missing data

---

## 📊 Test Results Template

```markdown
## Test Run: [Date/Time]

### Environment
- Backend: [version/commit]
- Frontend: [version/commit]
- Browser: [Chrome 120 / Firefox 121 / Safari 17]
- OS: [macOS 14.2 / Windows 11 / Ubuntu 22.04]

### Scenario Results
- ✅ Scenario 1: Complete Marketplace Flow - PASSED
- ✅ Scenario 2: Time Tracking Accuracy - PASSED
- ❌ Scenario 3: Notification System - FAILED (reason)
- ✅ Scenario 4: Leaderboard Dynamics - PASSED
- ✅ Scenario 5: Multi-Tab Sync - PASSED

### Performance Results
- API p50: 35ms ✅
- API p95: 87ms ✅
- FCP: 1.2s ✅
- TTI: 2.8s ✅

### Bugs Found
1. [BUG-001] Timer continues after stop on slow connection
2. [BUG-002] Notification bell badge shows "NaN" when no notifications

### Polish Items
1. Add loading spinner to "Vzít Task" button
2. Improve toast animation timing
3. Add empty state illustration to marketplace
```

---

## 🚀 Automation Scripts

### Quick Smoke Test
```bash
#!/bin/bash
# smoke_test.sh

echo "🧪 Running smoke tests..."

# 1. Health check
curl -f http://localhost:8000/health || exit 1

# 2. Can get marketplace
curl -f http://localhost:8000/api/tasks/marketplace || exit 1

# 3. Can get leaderboard
curl -f http://localhost:8000/api/leaderboard/weekly || exit 1

# 4. Can create notification
curl -f -X POST http://localhost:8000/api/notifications/test/create-sample || exit 1

echo "✅ Smoke tests passed!"
```

### Performance Test
```python
#!/usr/bin/env python3
# perf_test.py

import requests
import time
import statistics

def test_endpoint(url, count=100):
    latencies = []
    for _ in range(count):
        start = time.time()
        requests.get(url)
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    return {
        'p50': statistics.median(latencies),
        'p95': statistics.quantiles(latencies, n=20)[18],
        'p99': statistics.quantiles(latencies, n=100)[98],
        'mean': statistics.mean(latencies)
    }

endpoints = [
    'http://localhost:8000/api/tasks/marketplace',
    'http://localhost:8000/api/leaderboard/weekly',
    'http://localhost:8000/api/notifications/me?user_id=user_petr',
]

for url in endpoints:
    print(f"\n📊 Testing: {url}")
    results = test_endpoint(url)
    print(f"  p50: {results['p50']:.2f}ms")
    print(f"  p95: {results['p95']:.2f}ms")
    print(f"  p99: {results['p99']:.2f}ms")
```

---

## ✅ Stage 6 Completion Criteria

- [ ] All 5 E2E scenarios pass
- [ ] Responsive works on 3 breakpoints
- [ ] Performance targets met (API < 100ms p95)
- [ ] No critical bugs
- [ ] Polish checklist complete
- [ ] Documentation updated
- [ ] Ready for production
