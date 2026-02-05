<script setup lang="ts">
import { ref, computed, onMounted, inject, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi, type LeaderboardEntry } from '../composables/useApi'
import { useAuth } from '../composables/useAuth'
import AppIcon from '../components/AppIcon.vue'

const { t: _t } = useI18n()
const api = useApi()
const { user } = useAuth()
inject<Ref<number | null>>('currentProjectId', ref(null))

const activeTab = ref<'daily' | 'weekly' | 'monthly' | 'allTime'>('weekly')
const loading = ref(true)
const entries = ref<LeaderboardEntry[]>([])

const currentUserId = computed(() => user.value?.id || 'user_petr')

const currentUserEntry = computed(() => {
  return entries.value.find(e => e.user_id === currentUserId.value)
})

async function loadLeaderboard() {
  loading.value = true
  try {
    switch (activeTab.value) {
      case 'daily':
        entries.value = await api.getDailyLeaderboard()
        break
      case 'weekly':
        entries.value = await api.getWeeklyLeaderboard()
        break
      case 'monthly':
        entries.value = await api.getMonthlyLeaderboard()
        break
      case 'allTime':
        entries.value = await api.getAllTimeLeaderboard()
        break
    }
  } catch (e) {
    console.error('Failed to load leaderboard:', e)
  } finally {
    loading.value = false
  }
}

function getRankIcon(rank: number): string {
  switch (rank) {
    case 1: return 'medal-gold'
    case 2: return 'medal-silver'
    case 3: return 'medal-bronze'
    default: return ''
  }
}

function getRankClass(rank: number): string {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-default'
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

watch(activeTab, loadLeaderboard)

onMounted(loadLeaderboard)
</script>

<template>
  <div class="leaderboard-view">
    <header class="page-header">
      <div class="header-content">
        <h1><AppIcon name="trophy" :size="28" /> {{ $t('leaderboard.title') }}</h1>
        <p class="subtitle">{{ $t('leaderboard.subtitle') }}</p>
      </div>

      <button class="refresh-btn" @click="loadLeaderboard">
        <AppIcon name="refresh" :size="16" /> {{ $t('common.refresh') }}
      </button>
    </header>

    <!-- Current User Summary -->
    <div v-if="currentUserEntry" class="user-summary-card">
      <div class="summary-header">
        <div class="user-avatar large">
          {{ getInitials(currentUserEntry.user_name) }}
        </div>
        <div class="summary-info">
          <h3>{{ currentUserEntry.user_name }}</h3>
          <p class="rank-text">{{ $t('leaderboard.yourRank') }}: #{{ currentUserEntry.rank }}</p>
        </div>
      </div>
      <div class="summary-stats">
        <div class="stat-item">
          <div class="stat-value">{{ currentUserEntry.total_points }}</div>
          <div class="stat-label">{{ $t('leaderboard.totalPoints') }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ currentUserEntry.tasks_completed }}</div>
          <div class="stat-label">{{ $t('leaderboard.tasksCompleted') }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ currentUserEntry.bonus_points }}</div>
          <div class="stat-label">{{ $t('leaderboard.bonusPoints') }}</div>
        </div>
      </div>
    </div>

    <!-- Period Tabs -->
    <div class="period-tabs">
      <button
        :class="['tab-btn', { active: activeTab === 'daily' }]"
        @click="activeTab = 'daily'"
      >
        <AppIcon name="calendar" :size="16" /> {{ $t('leaderboard.daily') }}
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'weekly' }]"
        @click="activeTab = 'weekly'"
      >
        <AppIcon name="chart" :size="16" /> {{ $t('leaderboard.weekly') }}
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'monthly' }]"
        @click="activeTab = 'monthly'"
      >
        <AppIcon name="chart-up" :size="16" /> {{ $t('leaderboard.monthly') }}
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'allTime' }]"
        @click="activeTab = 'allTime'"
      >
        <AppIcon name="star" :size="16" /> {{ $t('leaderboard.allTime') }}
      </button>
    </div>

    <div v-if="loading" class="loading">
      {{ $t('common.loading') }}
    </div>

    <!-- Empty State -->
    <div v-else-if="entries.length === 0" class="empty-state">
      <AppIcon name="target" :size="64" class="empty-icon" />
      <h3>{{ $t('leaderboard.noData') }}</h3>
      <p>{{ $t('leaderboard.noDataDesc') }}</p>
    </div>

    <!-- Leaderboard Table -->
    <div v-else class="leaderboard-table">
      <div
        v-for="entry in entries"
        :key="entry.user_id"
        :class="[
          'leaderboard-entry',
          getRankClass(entry.rank),
          { 'current-user': entry.user_id === currentUserId }
        ]"
      >
        <!-- Rank Badge -->
        <div class="rank-badge">
          <AppIcon v-if="entry.rank <= 3" :name="getRankIcon(entry.rank)" :size="36" class="rank-emoji" />
          <span v-else class="rank-number">{{ entry.rank }}</span>
        </div>

        <!-- User Info -->
        <div class="user-info">
          <div class="user-avatar">
            <img
              v-if="entry.avatar_url"
              :src="entry.avatar_url"
              :alt="entry.user_name"
            />
            <span v-else>{{ getInitials(entry.user_name) }}</span>
          </div>
          <div class="user-details">
            <div class="user-name">{{ entry.user_name }}</div>
            <div class="user-email">{{ entry.user_email }}</div>
          </div>
        </div>

        <!-- Stats -->
        <div class="entry-stats">
          <div class="stat">
            <span class="stat-label">{{ $t('leaderboard.points') }}</span>
            <span class="stat-value points">{{ entry.points_earned }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">{{ $t('leaderboard.bonus') }}</span>
            <span class="stat-value bonus">+{{ entry.bonus_points }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">{{ $t('leaderboard.tasks') }}</span>
            <span class="stat-value tasks">{{ entry.tasks_completed }}</span>
          </div>
        </div>

        <!-- Total Points -->
        <div class="total-points">
          <div class="total-value">{{ entry.total_points }}</div>
          <div class="total-label">{{ $t('leaderboard.total') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard-view {
  padding: 0;
  min-height: calc(100vh - 4rem);
}

.page-header {
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-content h1 {
  margin: 0;
  font-size: 2rem;
  background: linear-gradient(135deg, #f7ba2c 0%, #ea580c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.5rem 0 0 0;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: var(--bg-highlight);
  border-color: var(--accent-blue);
  color: var(--text-primary);
}

/* User Summary Card */
.user-summary-card {
  background: linear-gradient(135deg, rgba(122, 162, 247, 0.1) 0%, rgba(187, 154, 247, 0.1) 100%);
  border: 1px solid rgba(122, 162, 247, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bg-dark);
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-avatar.large {
  width: 60px;
  height: 60px;
  font-size: 1.25rem;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.summary-info h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.rank-text {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: var(--bg-lighter);
  border-radius: 8px;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--accent-blue);
  line-height: 1;
}

.stat-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Period Tabs */
.period-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  background: var(--bg-lighter);
  padding: 0.25rem;
  border-radius: 8px;
  overflow-x: auto;
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: var(--bg-highlight);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--accent-blue);
  color: var(--bg-dark);
}

.loading {
  text-align: center;
  color: var(--text-muted);
  padding: 4rem;
  font-size: 1.125rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-secondary);
  font-size: 1.25rem;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}

/* Leaderboard Table */
.leaderboard-table {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-bottom: 2rem;
}

.leaderboard-entry {
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 1.5rem;
  align-items: center;
  transition: all 0.3s;
}

.leaderboard-entry:hover {
  border-color: var(--accent-blue);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.leaderboard-entry.current-user {
  background: rgba(122, 162, 247, 0.1);
  border-color: var(--accent-blue);
}

/* Rank Badges */
.rank-badge {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rank-emoji {
  font-size: 2rem;
}

.rank-number {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-muted);
}

.rank-gold {
  position: relative;
}

.rank-gold::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #f7ba2c 0%, #ea580c 100%);
  border-radius: 0 4px 4px 0;
}

.rank-silver::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #9ca3af 0%, #6b7280 100%);
  border-radius: 0 4px 4px 0;
}

.rank-bronze::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #cd7f32 0%, #8b4513 100%);
  border-radius: 0 4px 4px 0;
}

/* User Info */
.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-details {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 1rem;
}

.user-email {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

/* Entry Stats */
.entry-stats {
  display: flex;
  gap: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 1rem;
  font-weight: 600;
}

.stat-value.points {
  color: #7aa2f7;
}

.stat-value.bonus {
  color: #9ece6a;
}

.stat-value.tasks {
  color: #bb9af7;
}

/* Total Points */
.total-points {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: var(--bg-dark);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.total-label {
  margin-top: 0.25rem;
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Responsive */
@media (max-width: 1024px) {
  .entry-stats {
    gap: 1rem;
  }

  .stat {
    gap: 0.125rem;
  }

  .stat-label {
    font-size: 0.6rem;
  }

  .stat-value {
    font-size: 0.875rem;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .refresh-btn {
    width: 100%;
  }

  .header-content h1 {
    font-size: 1.5rem;
  }

  .user-summary-card {
    padding: 1rem;
  }

  .summary-stats {
    gap: 0.75rem;
  }

  .stat-item {
    padding: 0.75rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .period-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .tab-btn {
    font-size: 0.8rem;
    padding: 0.625rem 0.875rem;
  }

  .leaderboard-entry {
    grid-template-columns: auto 1fr;
    gap: 1rem;
    padding: 0.875rem 1rem;
  }

  .entry-stats {
    grid-column: 1 / -1;
    justify-content: space-around;
    margin-top: 0.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
  }

  .total-points {
    grid-column: 1 / -1;
    flex-direction: row;
    justify-content: space-between;
    padding: 0.625rem 1rem;
  }

  .user-avatar {
    width: 36px;
    height: 36px;
    font-size: 0.8rem;
  }

  .user-avatar.large {
    width: 48px;
    height: 48px;
    font-size: 1rem;
  }

  .rank-badge {
    width: 36px;
    height: 36px;
  }

  .rank-emoji {
    font-size: 1.5rem;
  }

  .rank-number {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .header-content h1 {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8rem;
  }

  .tab-btn {
    font-size: 0.75rem;
    padding: 0.5rem 0.75rem;
  }

  .user-name {
    font-size: 0.875rem;
  }

  .user-email {
    font-size: 0.7rem;
  }

  .entry-stats {
    gap: 0.75rem;
  }
}
</style>
