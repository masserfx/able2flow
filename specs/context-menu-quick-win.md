# Plan: Quick Actions Context Menu

## Task Description
Implementovat right-click context menu pro task cards v BoardView, který poskytne rychlý přístup k častým akcím (Duplicate, Move, Change Priority, Archive, Delete, Convert to Incident) bez nutnosti otevírat TaskModal.

## Objective
Snížit počet kroků potřebných k provedení akce z 5 kliků (klik na card → open modal → navigate → action → confirm) na 2 kliky (right-click → action). Expected improvement: 60% rychlejší workflow.

## Problem Statement
Uživatelé musí otevřít TaskModal pro každou akci s taskem, což zpomaluje produktivitu. Časté operace jako duplicate, delete, nebo změna priority vyžadují příliš mnoho interakcí. Right-click context menu poskytne zkratku přímo z BoardView.

## Solution Approach
1. **Frontend Composable:** Vytvořit `useContextMenu` composable pro reusable context menu logiku
2. **BoardView Integration:** Přidat @contextmenu event handler na task cards
3. **UI Component:** Context menu s Teleport pattern (renderuje do body)
4. **Actions:** Implementovat 6 akcí s i18n support
5. **Backend Support:** Přidat missing API endpoints (duplicate, archive)

---

## Relevant Files

### Existing Files to Modify:

#### Frontend:
- **apps/frontend/src/views/BoardView.vue** - Přidat context menu na task cards
- **apps/frontend/src/composables/useApi.ts** - Přidat duplicateTask() a archiveTask() metody
- **apps/frontend/src/i18n/locales/en.json** - Anglické translations pro context menu
- **apps/frontend/src/i18n/locales/cs.json** - České translations pro context menu

#### Backend:
- **apps/backend/routers/tasks.py** - Přidat POST /tasks/{id}/duplicate a PUT /tasks/{id}/archive endpoints
- **apps/backend/init_db.py** - Migration pro "archived" column v tasks table

### New Files to Create:

- **apps/frontend/src/composables/useContextMenu.ts** - Reusable context menu composable
- **apps/frontend/src/components/ContextMenu.vue** - Context menu UI komponenta (optional, může být inline v BoardView)

---

## Implementation Phases

### Phase 1: Backend Foundation (1-2 hodiny)
- Přidat "archived" column do tasks table (migration)
- Implementovat POST /tasks/{id}/duplicate endpoint
- Implementovat PUT /tasks/{id}/archive endpoint

### Phase 2: Frontend Core (2-3 hodiny)
- Vytvořit useContextMenu composable
- Implementovat context menu UI (Teleport pattern)
- Přidat @contextmenu handler do BoardView

### Phase 3: Integration & Polish (1-2 hodiny)
- Implementovat action handlers (duplicate, move, delete, archive, convert)
- Přidat i18n translations
- CSS styling (Tokyo Night theme)
- Testing & bug fixes

---

## Step by Step Tasks

### 1. Backend: Add "archived" Column Migration
- Otevřít `apps/backend/init_db.py`
- V `_run_migrations()` přidat:
  ```python
  try:
      cursor.execute("ALTER TABLE tasks ADD COLUMN archived INTEGER DEFAULT 0")
      logger.info("Migration: Added archived column to tasks")
  except sqlite3.OperationalError:
      pass
  ```

### 2. Backend: Add Duplicate Task Endpoint
- Otevřít `apps/backend/routers/tasks.py`
- Přidat nový endpoint:
  ```python
  @router.post("/{task_id}/duplicate", response_model=Task)
  def duplicate_task(task_id: int) -> dict:
      """Duplicate a task with new title."""
      with get_db() as conn:
          cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
          original = cursor.fetchone()
          if not original:
              raise HTTPException(status_code=404, detail="Task not found")
          
          # Create duplicate with "(Copy)" suffix
          cursor = conn.execute(
              """INSERT INTO tasks 
              (title, description, column_id, project_id, priority, completed, position, created_at)
              VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
              (
                  f"{original['title']} (Copy)",
                  original['description'],
                  original['column_id'],
                  original['project_id'],
                  original['priority'],
                  original['position'] + 1,
                  datetime.now().isoformat()
              )
          )
          conn.commit()
          new_id = cursor.lastrowid
          
          cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
          return row_to_task(cursor.fetchone())
  ```

### 3. Backend: Add Archive Task Endpoint
- V `apps/backend/routers/tasks.py` přidat:
  ```python
  @router.put("/{task_id}/archive", response_model=Task)
  def archive_task(task_id: int) -> dict:
      """Archive or unarchive a task."""
      with get_db() as conn:
          cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
          task = cursor.fetchone()
          if not task:
              raise HTTPException(status_code=404, detail="Task not found")
          
          new_archived_state = 0 if task['archived'] else 1
          conn.execute(
              "UPDATE tasks SET archived = ? WHERE id = ?",
              (new_archived_state, task_id)
          )
          conn.commit()
          
          cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
          return row_to_task(cursor.fetchone())
  ```

### 4. Frontend: Create useContextMenu Composable
- Vytvořit `apps/frontend/src/composables/useContextMenu.ts`:
  ```typescript
  import { ref, onMounted, onUnmounted } from 'vue'

  export interface ContextMenuPosition {
    x: number
    y: number
  }

  export function useContextMenu() {
    const isVisible = ref(false)
    const position = ref<ContextMenuPosition>({ x: 0, y: 0 })

    function show(event: MouseEvent) {
      event.preventDefault()
      position.value = {
        x: event.clientX,
        y: event.clientY
      }
      isVisible.value = true
    }

    function hide() {
      isVisible.value = false
    }

    function handleClickOutside() {
      if (isVisible.value) {
        hide()
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && isVisible.value) {
        hide()
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
      document.addEventListener('keydown', handleEscape)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    })

    return {
      isVisible,
      position,
      show,
      hide
    }
  }
  ```

### 5. Frontend: Add Context Menu to BoardView
- Otevřít `apps/frontend/src/views/BoardView.vue`
- Najít task card rendering (pravděpodobně v `v-for` loopu)
- Přidat `@contextmenu` event handler:
  ```vue
  <div 
    class="task-card"
    @contextmenu="showContextMenu($event, task)"
  >
  ```

### 6. Frontend: Implement Context Menu UI
- V `BoardView.vue` přidat context menu template:
  ```vue
  <script setup>
  import { useContextMenu } from '../composables/useContextMenu'
  
  const contextMenu = useContextMenu()
  const selectedTask = ref(null)
  
  function showContextMenu(event: MouseEvent, task: Task) {
    selectedTask.value = task
    contextMenu.show(event)
  }
  </script>

  <template>
    <!-- Existing board content -->

    <!-- Context Menu - Teleported to body -->
    <Teleport to="body">
      <div
        v-if="contextMenu.isVisible.value"
        class="context-menu"
        :style="{
          left: contextMenu.position.value.x + 'px',
          top: contextMenu.position.value.y + 'px'
        }"
        @click.stop
      >
        <div class="context-item" @click="handleDuplicate">
          <span class="icon">📋</span>
          {{ $t('contextMenu.duplicate') }}
        </div>
        <div class="context-item" @click="handleMove">
          <span class="icon">📁</span>
          {{ $t('contextMenu.move') }}
        </div>
        <div class="context-item" @click="handleConvert">
          <span class="icon">⚡</span>
          {{ $t('contextMenu.convertToIncident') }}
        </div>
        <div class="context-item submenu">
          <span class="icon">🔖</span>
          {{ $t('contextMenu.changePriority') }} ▶
        </div>
        <div class="context-divider" />
        <div class="context-item" @click="handleArchive">
          <span class="icon">📦</span>
          {{ $t('contextMenu.archive') }}
        </div>
        <div class="context-item danger" @click="handleDelete">
          <span class="icon">🗑️</span>
          {{ $t('contextMenu.delete') }}
        </div>
      </div>
    </Teleport>
  </template>
  ```

### 7. Frontend: Implement Action Handlers
- V `BoardView.vue` přidat action functions:
  ```typescript
  async function handleDuplicate() {
    if (!selectedTask.value) return
    try {
      await api.duplicateTask(selectedTask.value.id)
      await loadTasks()
      contextMenu.hide()
    } catch (e) {
      console.error('Failed to duplicate task:', e)
    }
  }

  async function handleArchive() {
    if (!selectedTask.value) return
    try {
      await api.archiveTask(selectedTask.value.id)
      await loadTasks()
      contextMenu.hide()
    } catch (e) {
      console.error('Failed to archive task:', e)
    }
  }

  async function handleDelete() {
    if (!selectedTask.value) return
    if (!confirm($t('board.deleteConfirm', { title: selectedTask.value.title }))) {
      return
    }
    try {
      await api.deleteTask(selectedTask.value.id)
      await loadTasks()
      contextMenu.hide()
    } catch (e) {
      console.error('Failed to delete task:', e)
    }
  }
  ```

### 8. Frontend: Add API Methods to useApi
- Otevřít `apps/frontend/src/composables/useApi.ts`
- Přidat metody:
  ```typescript
  async duplicateTask(taskId: number): Promise<Task> {
    const response = await api.post(`/tasks/${taskId}/duplicate`)
    return response.data
  }

  async archiveTask(taskId: number): Promise<Task> {
    const response = await api.put(`/tasks/${taskId}/archive`)
    return response.data
  }
  ```

### 9. Frontend: Add i18n Translations
- **en.json:**
  ```json
  "contextMenu": {
    "duplicate": "Duplicate Task",
    "move": "Move to Project...",
    "convertToIncident": "Convert to Incident",
    "changePriority": "Change Priority",
    "archive": "Archive",
    "delete": "Delete"
  }
  ```

- **cs.json:**
  ```json
  "contextMenu": {
    "duplicate": "Duplikovat úkol",
    "move": "Přesunout do projektu...",
    "convertToIncident": "Převést na incident",
    "changePriority": "Změnit prioritu",
    "archive": "Archivovat",
    "delete": "Smazat"
  }
  ```

### 10. Frontend: Add CSS Styling
- V `BoardView.vue` přidat styles:
  ```css
  .context-menu {
    position: fixed;
    background: var(--bg-lighter);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    min-width: 200px;
    padding: 4px;
    z-index: 1000;
  }

  .context-item {
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    color: var(--text-primary);
    transition: background 0.2s;
  }

  .context-item:hover {
    background: var(--bg-highlight);
  }

  .context-item.danger {
    color: var(--accent-red);
  }

  .context-item.danger:hover {
    background: rgba(247, 118, 142, 0.1);
  }

  .context-divider {
    height: 1px;
    background: var(--border-color);
    margin: 4px 0;
  }

  .icon {
    font-size: 1rem;
  }
  ```

### 11. Testing
- Backend: Test duplicate endpoint: `curl -X POST http://localhost:8000/api/tasks/1/duplicate`
- Backend: Test archive endpoint: `curl -X PUT http://localhost:8000/api/tasks/1/archive`
- Frontend: Right-click na task card → verify menu appears
- Frontend: Test každou akci (duplicate, archive, delete)
- Frontend: Test Escape key closes menu
- Frontend: Test click outside closes menu

---

## Testing Strategy

### Unit Tests (Optional)
- `useContextMenu.test.ts` - Test show/hide logic, keyboard handlers
- Backend endpoint tests pro duplicate a archive

### Manual Testing Checklist
1. ✅ Right-click opens context menu at cursor position
2. ✅ Menu displays 6 actions s ikonkami
3. ✅ Duplicate vytvoří kopii s "(Copy)" suffix
4. ✅ Archive toggles archived state
5. ✅ Delete confirmace dialog zobrazí
6. ✅ Escape key zavře menu
7. ✅ Click outside zavře menu
8. ✅ i18n funguje (CS + EN)
9. ✅ CSS styling odpovídá Tokyo Night theme
10. ✅ No console errors

---

## Acceptance Criteria

- [ ] Right-click na task card otevře context menu
- [ ] Context menu má 6 actions: Duplicate, Move, Convert, Change Priority, Archive, Delete
- [ ] Duplicate vytvoří kopii tasku s "(Copy)" v názvu
- [ ] Archive toggles "archived" flag (task zůstává v boardu, jen označen)
- [ ] Delete zobrazí confirm dialog a smaže task
- [ ] Menu se zavře po kliknutí na akci
- [ ] Menu se zavře po Escape key
- [ ] Menu se zavře po kliknutí mimo
- [ ] i18n translations fungují (CS + EN)
- [ ] Time-to-action: 5 clicks → 2 clicks (60% improvement)
- [ ] Žádné console errors

---

## Validation Commands

```bash
# Backend tests
cd /Users/lhradek/code/work/flowable

# 1. Apply DB migration
uv run python apps/backend/init_db.py | grep archived

# 2. Start backend
cd apps/backend && uv run uvicorn main:app --reload &

# 3. Test duplicate endpoint
curl -X POST http://localhost:8000/api/tasks/1/duplicate | jq

# 4. Test archive endpoint
curl -X PUT http://localhost:8000/api/tasks/1/archive | jq

# 5. Verify archived column
sqlite3 apps/backend/starter.db "SELECT id, title, archived FROM tasks LIMIT 5;"

# Frontend tests
cd /Users/lhradek/code/work/flowable/apps/frontend

# 6. Start frontend
npm run dev

# 7. Manual browser test
# - Navigate to http://localhost:5173/board
# - Right-click on task card
# - Verify context menu appears
# - Test each action
```

---

## Notes

### Implementation Complexity: Medium (3 dny → estimated ~6 hodin)

### Dependencies:
- No new npm packages needed
- No new Python packages needed

### Success Metrics:
- **Primary:** Time-to-action: 5 clicks → 2 clicks (60% improvement)
- **Secondary:** User satisfaction +40%
- **Tertiary:** Context menu adoption rate: target 70% of power users

### Future Enhancements (Post Quick Win):
1. **Submenu for Change Priority** - Expandable submenu s Low/Medium/High/Critical
2. **Move to Project** - Modal picker pro výběr destination project
3. **Keyboard Shortcuts** - Cmd+D pro duplicate, Cmd+Backspace pro delete
4. **Batch Operations** - Multi-select tasks + context menu pro bulk actions
5. **Custom Actions** - User-defined context menu items

### Edge Cases:
- **Right-click na archived task:** Show "Unarchive" místo "Archive"
- **Menu překračuje viewport:** Auto-adjust position (left/right/top/bottom)
- **Dlouhý task title:** Truncate v confirm dialog
- **Offline mode:** Disable actions pokud není API dostupné

---

## Rollback Plan

If feature causes issues:
1. Remove `@contextmenu` handler z BoardView
2. Backend endpoints zůstanou (no harm if unused)
3. `archived` column stays (backward compatible - default 0)
4. Revert commits: `git revert <commit-hash>`
