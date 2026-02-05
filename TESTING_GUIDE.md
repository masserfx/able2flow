# 🧪 ANT HILL - Complete Testing Guide

## Quick Start

### 1. Start Services
```bash
# Terminal 1: Backend
cd apps/backend
uv run python main.py

# Terminal 2: Frontend
cd apps/frontend
npm run dev
```

### 2. Run Tests
```bash
# Smoke tests (quick validation)
python3 smoke_test.py

# Performance tests (100 requests per endpoint)
python3 perf_test.py

# Notification tests (create 5 sample notifications)
python3 test_notifications.py 5
```

---

## Test Suite Overview

### 🚀 Smoke Tests (`smoke_test.py`)
**Purpose:** Quick validation that all critical endpoints work
**Duration:** ~10 seconds
**When to run:** After code changes, before commits

**What it tests:**
- ✅ Backend health
- ✅ Tasks & Marketplace endpoints
- ✅ All 4 leaderboard periods
- ✅ Notifications (get, poll, create)
- ✅ Time tracking

**Usage:**
```bash
python3 smoke_test.py

# Expected output:
# 🧪 ANT HILL Smoke Tests
# ==================================================
#
# 1️⃣  Backend Health
#   Testing: Health endpoint... ✅
#
# 2️⃣  Tasks & Marketplace
#   Testing: Get all tasks... ✅
#   Testing: Get marketplace tasks... ✅
#   Testing: Get columns... ✅
# ...
# 📊 Results: 13/13 tests passed
# ✅ All smoke tests passed!
```

---

### ⚡ Performance Tests (`perf_test.py`)
**Purpose:** Measure API latency and ensure performance targets
**Duration:** ~2 minutes (100 req/endpoint)
**When to run:** Before releases, after performance optimizations

**What it tests:**
- 📊 Marketplace API (target: p95 < 100ms)
- 📊 Leaderboard API (target: p95 < 100ms)
- 📊 Notifications Poll (target: p95 < 50ms)
- 📊 Unread Count (target: p95 < 30ms)

**Usage:**
```bash
# Default: 100 requests per endpoint
python3 perf_test.py

# Custom count
python3 perf_test.py 200

# Expected output:
# ⚡ ANT HILL Performance Testing
# ============================================================
# ✅ Backend health check passed
#
# Running 100 requests per endpoint...
#
# 📊 Marketplace Tasks
#   Testing 100 requests.......... Done!
#   📈 Results:
#     Min:    12.45ms
#     Mean:   24.67ms
#     Median: 22.13ms
#     p95: 45.23ms (target: <100ms) ✅
#     p99: 67.89ms (target: <200ms) ✅
#     Max:    89.12ms
#     StdDev: 8.34ms
# ...
# Results: 4/4 endpoints passed
# ✅ All performance targets met!
```

---

### 🔔 Notification Tests (`test_notifications.py`)
**Purpose:** Test real-time notification flow with FOMO effects
**Duration:** ~10 seconds
**When to run:** Testing notification system, polling mechanism

**What it tests:**
- 📢 Notification creation
- 🔔 Toast popups
- 🔊 Sound effects
- 🔴 Unread badge updates
- ⏱️ Polling (10s interval)

**Usage:**
```bash
# Create 5 sample notifications (2s interval)
python3 test_notifications.py 5

# Create 10 notifications
python3 test_notifications.py 10

# Expected behavior:
# - Notifications appear in backend
# - Frontend polls every 10s
# - Toast popups slide in from right
# - Sound plays for each new notification
# - Unread badge increments
```

---

## 🎯 E2E Test Scenarios

### Scenario 1: Complete Marketplace Flow
**File:** `STAGE6_E2E_TESTS.md` → Scenario 1

**Steps:**
1. Open http://localhost:5173
2. Navigate to 🎯 Marketplace
3. Claim a task ("Vzít Task")
4. Verify toast: "🎯 User si vzal task!"
5. Go to Board, find task with 👤 badge
6. Open task modal, start TimeTracker
7. Wait 30s, stop timer
8. Mark as completed
9. Verify toast: "💎 User získal X bodů!"
10. Check 🏆 Leaderboard for updated points

**Expected:**
- ✅ All steps complete without errors
- ✅ Notifications within 10 seconds
- ✅ Points calculated correctly
- ✅ Leaderboard updates

**Manual Test Checklist:**
- [ ] Marketplace loads
- [ ] Can claim task
- [ ] Toast notification appears
- [ ] Task shows in Board with badge
- [ ] TimeTracker works
- [ ] Time accumulates correctly
- [ ] Complete triggers points
- [ ] Leaderboard updates

---

### Scenario 2: Notification Real-Time Flow
**Duration:** ~2 minutes

**Steps:**
1. Open frontend in browser
2. Open notification bell (🔔)
3. Run: `python3 test_notifications.py 3`
4. Wait up to 15 seconds
5. Observe:
   - 3 toast notifications slide in
   - Sound plays for each
   - Unread badge shows "3"
6. Click notification bell
7. Click first notification
8. Verify marked as read
9. Click "Označit vše jako přečtené"
10. Verify badge disappears

**Expected:**
- ✅ Polling works (10s)
- ✅ Toasts appear automatically
- ✅ Sound plays
- ✅ Mark as read functions
- ✅ No duplicate notifications

---

### Scenario 3: Time Tracking Accuracy
**Duration:** ~2 minutes

**Steps:**
1. Create task with estimated_minutes = 10
2. Verify PointsBadge shows "1 bod"
3. Claim task to self
4. Open task modal
5. Start timer
6. Wait exactly 60 seconds
7. Stop timer
8. Verify time_spent ~60s (±5s)
9. Start timer again
10. Wait 30s, stop
11. Verify cumulative ~90s
12. Complete task
13. Check bonus calculation

**Expected:**
- ✅ Timer accuracy ±5 seconds
- ✅ Cumulative tracking works
- ✅ Bonus points correct

---

## 📱 Responsive Testing

### Mobile (375px)
```bash
# Open DevTools (F12)
# Toggle Device Toolbar (Cmd+Shift+M or Ctrl+Shift+M)
# Select "iPhone SE" or custom 375x667
```

**Test:**
- [ ] Sidebar navigation works
- [ ] Marketplace cards stack vertically
- [ ] "Vzít Task" button accessible
- [ ] Task modal fits screen
- [ ] TimeTracker usable
- [ ] Toast notifications fit
- [ ] No horizontal scroll

### Tablet (768px)
```bash
# Device Toolbar → iPad
```

**Test:**
- [ ] 2-column layouts
- [ ] Kanban horizontal scroll
- [ ] Touch targets ≥44px
- [ ] Readable leaderboard

### Desktop (1920px)
```bash
# Default desktop view
```

**Test:**
- [ ] 3-4 column grid
- [ ] All features accessible
- [ ] Optimal spacing

---

## ⚡ Performance Targets

### Backend API
| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| Marketplace | <30ms | <100ms | <200ms |
| Leaderboard | <30ms | <100ms | <200ms |
| Notifications Poll | <20ms | <50ms | <100ms |
| Unread Count | <15ms | <30ms | <50ms |
| Time Tracking Start | <30ms | <80ms | <150ms |

### Frontend
| Metric | Target |
|--------|--------|
| First Contentful Paint | <1.5s |
| Time to Interactive | <3s |
| Largest Contentful Paint | <2.5s |

**Measure with:**
- Chrome DevTools Lighthouse
- Network tab (disable cache)
- Performance tab

---

## 🐛 Common Issues

### "Connection refused" error
**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# If not running:
cd apps/backend
uv run python main.py
```

### "Frontend not loading"
**Solution:**
```bash
# Check frontend dev server
curl http://localhost:5173

# If not running:
cd apps/frontend
npm run dev
```

### "No notifications appearing"
**Solution:**
1. Check backend logs for errors
2. Open DevTools → Network tab
3. Look for `/api/notifications/poll` requests (every 10s)
4. Verify responses have new notifications
5. Check browser console for errors

### "Points not calculating"
**Solution:**
1. Check task has `estimated_minutes` set
2. Verify task was completed (not just closed)
3. Check backend logs for "awarding points"
4. Query DB:
   ```bash
   cd apps/backend
   sqlite3 able2flow.db
   SELECT * FROM user_points WHERE user_id='user_petr';
   ```

---

## 📊 Test Results Template

```markdown
## Test Run: 2024-01-XX 14:30

### Environment
- Backend: main branch (commit abc123)
- Frontend: main branch (commit def456)
- Browser: Chrome 120.0.6099.129
- OS: macOS 14.2

### Test Results
#### Smoke Tests
✅ PASSED - 13/13 tests

#### Performance Tests
✅ PASSED - All endpoints < p95 targets
- Marketplace: p95 = 47ms
- Leaderboard: p95 = 53ms
- Notifications: p95 = 18ms

#### E2E Scenarios
✅ Scenario 1: Complete Marketplace Flow - PASSED
✅ Scenario 2: Notification Real-Time - PASSED
✅ Scenario 3: Time Tracking - PASSED

#### Responsive
✅ Mobile (375px) - PASSED
✅ Tablet (768px) - PASSED
✅ Desktop (1920px) - PASSED

### Issues Found
None

### Notes
- All features working as expected
- Performance excellent
- Ready for production
```

---

## ✅ Stage 6 Completion Checklist

### Testing
- [ ] Smoke tests pass
- [ ] Performance tests pass
- [ ] All 5 E2E scenarios tested
- [ ] Responsive tested (3 breakpoints)
- [ ] No critical bugs

### Polish
- [ ] Loading states visible
- [ ] Error messages clear
- [ ] Animations smooth
- [ ] Consistent styling
- [ ] Accessibility checked

### Documentation
- [ ] README updated
- [ ] API docs complete
- [ ] Test guide reviewed
- [ ] Deployment instructions

### Ready for Production
- [ ] All tests green
- [ ] Performance acceptable
- [ ] No blocking bugs
- [ ] Team approval

---

## 🚀 Next Steps

After Stage 6:
1. **Deploy to staging**
2. **User acceptance testing**
3. **Production deployment**
4. **Monitor metrics**
5. **Gather feedback**
6. **Iterate!**

---

## 📚 Additional Resources

- **STAGE6_E2E_TESTS.md** - Detailed E2E test scenarios
- **STAGE5_TESTING.md** - Notification system testing
- **STAGE4-6 Plan** - Original implementation plan
- **API Documentation** - http://localhost:8000/docs (when running)
