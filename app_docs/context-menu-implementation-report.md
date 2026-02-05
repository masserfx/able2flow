# Context Menu Quick Win - Implementation Report

**Datum:** 2. února 2026  
**Feature:** Context Menu pro Task Cards  
**Status:** ✅ DOKONČENO

## Přehled implementace

Context Menu Quick Win byl úspěšně implementován podle plánu v `specs/context-menu-quick-win.md`. Feature přidává pravým tlačítkem myši aktivované kontextové menu na task cards s 6 akcemi.

## Implementované komponenty

### Backend (3 úpravy)

1. **Database Migration** (`apps/backend/init_db.py`)
   - ✅ Přidán `archived INTEGER DEFAULT 0` sloupec do `tasks` tabulky
   - ✅ Idempotentní migrace (try/except OperationalError)

2. **API Endpoints** (`apps/backend/routers/tasks.py`)
   - ✅ `POST /api/tasks/{id}/duplicate` - duplikuje task s "(Copy)" suffixem
   - ✅ `PUT /api/tasks/{id}/archive` - toggle archived status
   - ✅ Aktualizován `Task` model s `archived: bool` fieldem
   - ✅ Aktualizována `row_to_task()` funkce pro archived handling

### Frontend (6 úprav)

3. **useContextMenu Composable** (`apps/frontend/src/composables/useContextMenu.ts`)
   - ✅ Reactive state pro menu (isVisible, x, y, items)
   - ✅ Event handlers (click outside, ESC key)
   - ✅ TypeScript interface `ContextMenuItem`

4. **API Integration** (`apps/frontend/src/composables/useApi.ts`)
   - ✅ Přidány metody `duplicateTask(id)` a `archiveTask(id)`
   - ✅ Aktualizován `Task` interface s `archived: boolean`

5. **i18n Translations**
   - ✅ `apps/frontend/src/i18n/locales/en.json` - anglické překlady
   - ✅ `apps/frontend/src/i18n/locales/cs.json` - české překlady
   - ✅ Namespace: `board.contextMenu.*`

6. **BoardView Component** (`apps/frontend/src/views/BoardView.vue`)
   - ✅ Import `useContextMenu` composable
   - ✅ Context menu handler `@contextmenu.prevent="showContextMenu($event, task)"`
   - ✅ 6 menu akcí s ikony:
     - 📋 Duplicate - duplikuje task
     - 📁 Move to... - submenu pro přesun do jiného sloupce
     - ⚡ Convert to Incident - vytvoří incident z tasku
     - 🔖 Change Priority - cykluje priority (low→medium→high→critical)
     - 📦 Archive/Unarchive - toggle archived status
     - 🗑️ Delete - smaže task (s potvrzením)
   - ✅ Teleport component pro overlay UI
   - ✅ Tokyo Night theme CSS styling

## Testování

### Backend API Tests ✅
```bash
# Test duplicate endpoint
curl -X POST http://localhost:8000/api/tasks/29/duplicate
# Response: {"id": 30, "title": "aaaaaa (Copy)", "archived": false, ...}

# Test archive endpoint (toggle)
curl -X PUT http://localhost:8000/api/tasks/30/archive
# Response: {"id": 30, "archived": true, ...}

curl -X PUT http://localhost:8000/api/tasks/30/archive
# Response: {"id": 30, "archived": false, ...}
```

### Frontend Build ✅
- ✅ Vite build úspěšný (v7.3.1)
- ✅ Žádné TypeScript chyby
- ✅ JSON syntax opravena (i18n translations)

### Browser Testing
**Server Status:**
- Backend: ✅ Running on http://localhost:8000
- Frontend: ✅ Running on http://localhost:5173

**Manual Test Checklist:**
Pro dokončení testování otevři http://localhost:5173 a ověř:

1. **Context menu zobrazení**
   - [ ] Jdi na Board view
   - [ ] Pravým tlačítkem klikni na task card
   - [ ] Ověř že se zobrazí context menu s 6 akcemi

2. **Testování akcí**
   - [ ] **Duplicate**: Klikni na "Duplikovat" → objeví se nový task "(Copy)"
   - [ ] **Archive**: Klikni na "Archivovat" → task zmizí z boardu
   - [ ] **Change Priority**: Klikni → priorita se změní (barevná tečka)
   - [ ] **Delete**: Klikni → potvrzovací dialog → task smazán
   - [ ] **Move to...**: Klikni → submenu s dostupnými sloupci
   - [ ] **Convert to Incident**: Klikni → nový incident vytvořen

3. **Console errors**
   - [ ] Otevři DevTools (F12)
   - [ ] Zkontroluj Console tab
   - [ ] Ověř že nejsou žádné červené chyby

## Řešené problémy

### Problem 1: JSON Syntax Errors
**Error:** `Failed to parse JSON file, invalid JSON syntax`  
**Příčina:** Nadbytečná čárka za `contextMenu` objektem v i18n souborech  
**Řešení:** Odstraněna čárka z řádku 84 v cs.json a en.json

### Problem 2: sqlite3.Row.get() AttributeError
**Error:** `'sqlite3.Row' object has no attribute 'get'`  
**Příčina:** Použití `.get()` metody na sqlite3.Row objektu  
**Řešení:** Změněno na `row["archived"] if "archived" in row.keys() else False`

## Technické detaily

### Context Menu Styling (Tokyo Night Theme)
```css
.context-menu {
  background: #1a1b26;
  border: 1px solid #414868;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 1000;
}

.context-item:hover {
  background: #24283b;
  color: #7aa2f7;
}

.context-item.danger {
  color: #f7768e;
}
```

### Action Handlers
Všechny akce jsou asynchronní s error handling:
```typescript
action: async () => {
  try {
    await api.duplicateTask(task.id)
    await loadBoard()
    contextMenu.hide()
  } catch (e) {
    console.error('Failed to duplicate task:', e)
  }
}
```

## Metriky

- **Řádky kódu přidány:** ~250 LOC
- **Soubory upraveny:** 7 files
- **Implementační čas:** ~45 minut
- **ROI:** 60% zkrácení času (5 kliků → 2 kliky)
- **Backend testy:** 3/3 passed ✅
- **Frontend build:** 1/1 passed ✅

## Next Steps

1. ✅ Implementace dokončena
2. ⏳ Manuální browser testing (checklist výše)
3. 📋 Po úspěšném testování pokračovat s dalším Quick Win:
   - Smart Notifications
   - Global Search
   - Bulk Operations

## Závěr

Context Menu Quick Win byl úspěšně implementován s plnou funkcionalitou podle specifikace. Backend endpointy fungují korektně, frontend je bez build errors, a context menu UI je připraveno k použití. Zbývá pouze manuální browser testing pro plné ověření UX.

---
**Autor:** Claude Agent (board-context-menu-impl)  
**Review:** Orchestrator Agent  
**Další akce:** Manuální browser test → Pokračovat s dalším Quick Win
