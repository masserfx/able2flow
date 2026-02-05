# 🔔 Stage 5: Notifications & Polling - Test Guide

## ✅ Co bylo implementováno

### Backend
- ✅ **Test endpoint**: `POST /api/notifications/test/create-sample`
- ✅ **Polling endpoint**: `GET /api/notifications/poll?since={timestamp}`
- ✅ **Unread count**: `GET /api/notifications/unread-count`
- ✅ **Auto-notifikace**:
  - Při claim tasku: "🎯 User si vzal task!"
  - Při award points: "💎 User získal X bodů!"

### Frontend
- ✅ **NotificationBell komponent** s 10s polling
- ✅ **Toast system** (slide-in animations, auto-dismiss)
- ✅ **Sound effects** (Web Audio API beep)
- ✅ **FOMO efekt** - toast + sound při nové notifikaci
- ✅ **Unread badge** s pulsing animací
- ✅ **Mark as read** funkce

---

## 🚀 Test Scénáře

### Test 1: Polling & Toast Notifications

**Příprava:**
```bash
# Terminal 1: Spusť backend
cd apps/backend
uv run python main.py

# Terminal 2: Spusť frontend
cd apps/frontend
npm run dev
```

**Test kroky:**
1. Otevři frontend: `http://localhost:5173`
2. Přihlas se (nebo pokračuj bez auth)
3. **Sleduj notification bell** (🔔 v sidebaru)
4. V **novém terminálu** spusť test script:
   ```bash
   chmod +x test_notifications.sh
   ./test_notifications.sh 3
   ```
5. **Očekávané chování:**
   - ⏱️ Po ~10 sekundách se objeví první toast
   - 🔊 Zahraje se zvukový efekt (beep)
   - 🔴 Unread badge ukáže "1"
   - 📱 Toast se automaticky zavře po 4 sekundách
   - 🔁 Proces se opakuje pro další notifikace

**Úspěch = ✅:**
- Toasty se objevují automaticky
- Zvuk funguje
- Unread count se aktualizuje

---

### Test 2: Real-World Flow (Claim → Complete)

**Kroky:**
1. **Vytvoř task v BoardView**
   - Klikni "+ Nový úkol"
   - Název: "Test notification flow"
   - Estimated minutes: 10
   - Priorita: Medium
   - Uložit

2. **Přesuň na marketplace**
   - Přetáhni task do "Backlog" sloupce (nebo jiného sloupce bez assignment)
   - Nebo nastav assigned_to = NULL v DB

3. **Otevři Marketplace** (🎯)
   - Měl by se zobrazit task
   - Měl by mít 1 bod (10 min ÷ 10 = 1)

4. **Vezmi task** ("Vzít Task" button)
   - Task zmizí z marketplace
   - **Očekávaná notifikace**: "🎯 [User] si vzal task!"
   - Toast by se měl objevit do 10 sekund
   - Zvuk by měl zahrát

5. **Otevři task v BoardView**
   - Spusť stopky (▶️)
   - Počkej ~30 sekund
   - Zastav stopky (⏹️)

6. **Označ jako hotovo** (checkbox)
   - **Očekávaná notifikace**: "💎 [User] získal X bodů!"
   - Toast: body + bonus info
   - Zvuk

7. **Check notification bell**
   - Klikni na 🔔
   - Měly by být vidět obě notifikace
   - Unread badge by měl ukazovat 2
   - Klikni na notifikaci → mark as read
   - Badge by se měl snížit na 1

**Úspěch = ✅:**
- Notifikace při claim
- Notifikace při complete
- Toast + sound funguje
- Mark as read funguje

---

### Test 3: Polling Interval (Stress Test)

**Cíl:** Ověřit, že polling není příliš náročný a funguje správně

**Kroky:**
1. Otevři DevTools (F12)
2. Jdi na **Network** tab
3. Filtruj na "poll"
4. **Sleduj:** Měl bys vidět request každých ~10 sekund
5. Vytvoř notifikace:
   ```bash
   ./test_notifications.sh 10
   ```
6. **Check:**
   - Requests jsou každých 10s
   - Response time < 50ms
   - Žádné error 500/404
   - Toast se zobrazuje max pro první notifikaci (ne pro všech 10)

**Úspěch = ✅:**
- Polling interval přesně 10s
- Nízká latence (< 50ms)
- Toasty se neškálují exponenciálně

---

### Test 4: Multiple Users Simulation

**Příprava:**
```bash
# Otevři 2 browsery (Chrome + Firefox)
# Nebo 2 incognito okna
```

**Kroky:**
1. **Browser 1**: User "user_petr"
2. **Browser 2**: User "user_jana" (změň v kódu nebo použij jiný user)
3. V **Browser 1**: Vezmi task z marketplace
4. V **Browser 2**: Měla by se objevit notifikace "🎯 Petr si vzal task!"
5. V **Browser 1**: Dokonči task
6. V **Browser 2**: Měla by se objevit "💎 Petr získal X bodů!"

**Úspěch = ✅:**
- Broadcast notifications viditelné pro všechny usery
- Real-time flow funguje (do 10s)

---

### Test 5: Sound Toggle (Optional Enhancement)

**TODO:** Přidat možnost vypnout zvuk

**Implementace:**
```typescript
// localStorage klíč
const soundEnabled = localStorage.getItem('notif_sound') !== 'false'

function playNotificationSound() {
  if (!soundEnabled) return
  // ... existing code
}

// UI toggle v NotificationBell dropdown
<button @click="toggleSound">
  {{ soundEnabled ? '🔊' : '🔇' }}
</button>
```

---

## 🐛 Debugging

### Notifikace se neobjevují

**Check:**
1. Backend běží? `curl http://localhost:8000/health`
2. Frontend console errors?
3. Network tab - polling funguje?
4. DB obsahuje notifikace?
   ```bash
   cd apps/backend
   sqlite3 able2flow.db
   SELECT * FROM notifications ORDER BY created_at DESC LIMIT 5;
   ```

### Toast nefunguje

**Check:**
1. ToastContainer je v App.vue?
2. Console error: "useToast is not defined"?
3. Import správný?

### Zvuk nehraje

**Check:**
1. Browser permission - povoleno audio?
2. Console error: "AudioContext"?
3. Zkus click na stránku před testem (user interaction required)

### Polling interval příliš rychlý/pomalý

**Fix:**
```typescript
// NotificationBell.vue
// Změň interval (aktuálně 10000ms = 10s)
pollingInterval = window.setInterval(pollNotifications, 10000)
```

---

## 📊 Metriky úspěchu

- ✅ Polling interval: 10s ± 1s
- ✅ API latence: < 100ms p95
- ✅ Toast delay: < 500ms po receive
- ✅ Sound delay: < 200ms po receive
- ✅ Unread count accuracy: 100%
- ✅ Mark as read response: < 100ms

---

## 🎯 Quick Test Commands

```bash
# 1. Backend health check
curl http://localhost:8000/health

# 2. Create test notification
curl -X POST http://localhost:8000/api/notifications/test/create-sample

# 3. Check unread count
curl "http://localhost:8000/api/notifications/unread-count?user_id=user_petr"

# 4. Get all notifications
curl "http://localhost:8000/api/notifications/me?user_id=user_petr"

# 5. Poll for new (since 1 minute ago)
TIMESTAMP=$(date -u -v-1M +%Y-%m-%dT%H:%M:%S)
curl "http://localhost:8000/api/notifications/poll?since=$TIMESTAMP&user_id=user_petr"
```

---

## ✅ Stage 5 Completion Checklist

- [x] Polling mechanism implemented (10s)
- [x] Toast notifications with FOMO effect
- [x] Sound effects (Web Audio API)
- [x] Broadcast notifications (claim + points)
- [x] Unread badge with count
- [x] Mark as read functionality
- [x] Test endpoint for easy testing
- [x] Test script (test_notifications.sh)
- [ ] Manual test completed
- [ ] Multiple scenarios verified
- [ ] Performance acceptable

---

## 🚀 Pokračování na Stage 6

Po úspěšném dokončení Stage 5:
1. Mark task #14 as completed
2. Proceed to Stage 6: Testing & Polish
3. E2E testing with browser-mcp
4. Bug fixes and final polish
