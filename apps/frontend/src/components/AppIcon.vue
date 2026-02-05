<script setup lang="ts">
defineProps<{
  name: string
  size?: number
}>()
</script>

<template>
  <svg
    class="app-icon"
    :width="size || 20"
    :height="size || 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <!-- Navigation -->
    <template v-if="name === 'dashboard'">
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
    </template>

    <template v-else-if="name === 'board'">
      <rect x="2" y="3" width="5.5" height="18" rx="1.5" />
      <rect x="9.25" y="3" width="5.5" height="13" rx="1.5" />
      <rect x="16.5" y="3" width="5.5" height="8" rx="1.5" />
    </template>

    <template v-else-if="name === 'target'">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'trophy'">
      <path d="M6 9V4h12v5a6 6 0 0 1-12 0Z" />
      <path d="M6 6H4a1 1 0 0 0-1 1v1a3 3 0 0 0 3 3" />
      <path d="M18 6h2a1 1 0 0 1 1 1v1a3 3 0 0 1-3 3" />
      <path d="M12 15v2" />
      <path d="M8 21h8" />
      <path d="M9 21v-4h6v4" />
    </template>

    <template v-else-if="name === 'pulse'">
      <circle cx="12" cy="12" r="9" stroke-dasharray="2 3" />
      <path d="M12 7v5l3 3" />
      <circle cx="12" cy="5" r="1" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'monitor'">
      <path d="M2 12h3l3-7 4 14 3-7h7" />
    </template>

    <template v-else-if="name === 'zap'">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10" fill="none" />
    </template>

    <template v-else-if="name === 'list'">
      <path d="M4 6h16" />
      <path d="M4 10h16" />
      <path d="M4 14h12" />
      <path d="M4 18h8" />
    </template>

    <template v-else-if="name === 'book'">
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v17H6.5a2.5 2.5 0 0 0 0 5H20" />
      <path d="M8 7h6" />
      <path d="M8 11h4" />
    </template>

    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </template>

    <!-- Logo -->
    <template v-else-if="name === 'logo'">
      <path d="M12 2L3 7v10l9 5 9-5V7l-9-5Z" />
      <path d="M12 22V12" />
      <path d="M3 7l9 5 9-5" />
    </template>

    <!-- Actions -->
    <template v-else-if="name === 'play'">
      <polygon points="6 3 20 12 6 21" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'stop'">
      <rect x="4" y="4" width="16" height="16" rx="2" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'timer'">
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l2.5 2.5" />
      <path d="M12 5V3" />
      <path d="M10 2h4" />
      <path d="M20 7l1-1" />
    </template>

    <!-- Gamification -->
    <template v-else-if="name === 'gem'">
      <path d="M6 3h12l4 6-10 12L2 9l4-6Z" />
      <path d="M2 9h20" />
      <path d="M12 21L8.5 9 6 3" />
      <path d="M12 21l3.5-12L18 3" />
      <path d="M10 3l2 6 2-6" />
    </template>

    <template v-else-if="name === 'medal-gold'">
      <circle cx="12" cy="14" r="6" fill="#e0af68" stroke="#e0af68" stroke-width="1.5" />
      <circle cx="12" cy="14" r="3.5" fill="none" stroke="#1a1b26" stroke-width="1" />
      <path d="M9 2l3 8 3-8" stroke="#e0af68" />
      <text x="12" y="16" text-anchor="middle" fill="#1a1b26" font-size="6" font-weight="bold" stroke="none">1</text>
    </template>

    <template v-else-if="name === 'medal-silver'">
      <circle cx="12" cy="14" r="6" fill="#a9b1d6" stroke="#a9b1d6" stroke-width="1.5" />
      <circle cx="12" cy="14" r="3.5" fill="none" stroke="#1a1b26" stroke-width="1" />
      <path d="M9 2l3 8 3-8" stroke="#a9b1d6" />
      <text x="12" y="16" text-anchor="middle" fill="#1a1b26" font-size="6" font-weight="bold" stroke="none">2</text>
    </template>

    <template v-else-if="name === 'medal-bronze'">
      <circle cx="12" cy="14" r="6" fill="#ff9e64" stroke="#ff9e64" stroke-width="1.5" />
      <circle cx="12" cy="14" r="3.5" fill="none" stroke="#1a1b26" stroke-width="1" />
      <path d="M9 2l3 8 3-8" stroke="#ff9e64" />
      <text x="12" y="16" text-anchor="middle" fill="#1a1b26" font-size="6" font-weight="bold" stroke="none">3</text>
    </template>

    <!-- Notifications -->
    <template v-else-if="name === 'bell'">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </template>

    <template v-else-if="name === 'bell-off'">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke-opacity="0.4" />
      <line x1="3" y1="3" x2="21" y2="21" />
    </template>

    <!-- Status -->
    <template v-else-if="name === 'check-circle'">
      <circle cx="12" cy="12" r="9" />
      <path d="M9 12l2 2 4-4" />
    </template>

    <template v-else-if="name === 'check'">
      <path d="M5 12l5 5L20 7" />
    </template>

    <template v-else-if="name === 'alert-triangle'">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <circle cx="12" cy="16.5" r="0.5" fill="currentColor" stroke="none" />
    </template>

    <!-- Priority dots -->
    <template v-else-if="name === 'priority-critical'">
      <circle cx="12" cy="12" r="8" fill="#f7768e" stroke="#f7768e" />
      <path d="M12 8v4" stroke="#1a1b26" stroke-width="2" />
      <circle cx="12" cy="15" r="0.8" fill="#1a1b26" stroke="none" />
    </template>

    <template v-else-if="name === 'priority-high'">
      <circle cx="12" cy="12" r="8" fill="#ff9e64" stroke="#ff9e64" />
      <path d="M8 14l4-5 4 5" stroke="#1a1b26" stroke-width="2" fill="none" />
    </template>

    <template v-else-if="name === 'priority-medium'">
      <circle cx="12" cy="12" r="8" fill="#e0af68" stroke="#e0af68" />
      <path d="M7 12h10" stroke="#1a1b26" stroke-width="2" />
    </template>

    <template v-else-if="name === 'priority-low'">
      <circle cx="12" cy="12" r="8" fill="#9ece6a" stroke="#9ece6a" />
      <path d="M8 10l4 5 4-5" stroke="#1a1b26" stroke-width="2" fill="none" />
    </template>

    <!-- Files -->
    <template v-else-if="name === 'file'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
      <polyline points="14 2 14 8 20 8" />
    </template>

    <template v-else-if="name === 'file-image'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
      <polyline points="14 2 14 8 20 8" />
      <circle cx="10" cy="14" r="2" />
      <path d="M20 17l-3-3-5 5" />
    </template>

    <template v-else-if="name === 'file-text'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="12" y2="17" />
    </template>

    <template v-else-if="name === 'file-spreadsheet'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
      <polyline points="14 2 14 8 20 8" />
      <path d="M8 13h8M8 17h8M12 13v4" />
    </template>

    <template v-else-if="name === 'file-archive'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
      <polyline points="14 2 14 8 20 8" />
      <path d="M10 12h1M10 15h1M10 18h1" />
    </template>

    <template v-else-if="name === 'paperclip'">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.49" />
    </template>

    <!-- Misc -->
    <template v-else-if="name === 'refresh'">
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </template>

    <template v-else-if="name === 'calendar'">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </template>

    <template v-else-if="name === 'chart'">
      <path d="M18 20V10M12 20V4M6 20v-6" stroke-width="2.5" />
    </template>

    <template v-else-if="name === 'chart-up'">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </template>

    <template v-else-if="name === 'star'">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26" />
    </template>

    <template v-else-if="name === 'users'">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </template>

    <template v-else-if="name === 'user'">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </template>

    <template v-else-if="name === 'mail'">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <polyline points="22 4 12 13 2 4" />
    </template>

    <template v-else-if="name === 'message'">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10Z" />
    </template>

    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </template>

    <template v-else-if="name === 'globe'">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10Z" />
    </template>

    <template v-else-if="name === 'robot'">
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <circle cx="9" cy="14" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="15" cy="14" r="1.5" fill="currentColor" stroke="none" />
      <path d="M12 2v4" />
      <circle cx="12" cy="2" r="1" fill="currentColor" stroke="none" />
      <path d="M2 14h2M20 14h2" />
    </template>

    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </template>

    <template v-else-if="name === 'folder'">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v11Z" />
    </template>

    <template v-else-if="name === 'clipboard'">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" />
    </template>

    <template v-else-if="name === 'plus'">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </template>

    <template v-else-if="name === 'trash'">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </template>

    <template v-else-if="name === 'download'">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </template>

    <template v-else-if="name === 'sparkles'">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Z" fill="currentColor" stroke="none" />
      <path d="M19 13l.75 2.25L22 16l-2.25.75L19 19l-.75-2.25L16 16l2.25-.75L19 13Z" fill="currentColor" stroke="none" />
      <path d="M5 17l.5 1.5L7 19l-1.5.5L5 21l-.5-1.5L3 19l1.5-.5L5 17Z" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'megaphone'">
      <path d="M3 11l18-5v14L3 15v-4Z" />
      <path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" />
    </template>

    <template v-else-if="name === 'volume'">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19" fill="currentColor" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </template>

    <template v-else-if="name === 'arrow-down'">
      <line x1="12" y1="5" x2="12" y2="19" />
      <polyline points="19 12 12 19 5 12" />
    </template>

    <template v-else-if="name === 'fire'">
      <path d="M12 22c4.97 0 8-3.03 8-7 0-3-2-5.5-4-8-.5 2.5-2 4.5-4 4.5S8 9.5 7 7c-1.5 2-3 5-3 8 0 3.97 3.03 7 8 7Z" fill="currentColor" />
      <path d="M12 22c2 0 4-1.5 4-4 0-1.5-1-2.5-2-4-.5 1-1 2-2 2s-1.5-1-2-2c-1 1.5-2 2.5-2 4 0 2.5 2 4 4 4Z" fill="var(--bg-dark, #1a1b26)" stroke="none" />
    </template>

    <template v-else-if="name === 'running'">
      <circle cx="14" cy="4" r="2" fill="currentColor" stroke="none" />
      <path d="M18 10l-3-3-4 1-4 4 2 2 3-3" stroke-width="2" />
      <path d="M11 12l-3 8M13 16l5 5" stroke-width="2" />
    </template>

    <template v-else-if="name === 'eye'">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z" />
      <circle cx="12" cy="12" r="3" />
    </template>

    <template v-else-if="name === 'ant'">
      <ellipse cx="12" cy="15" rx="4" ry="5" />
      <ellipse cx="12" cy="8" rx="3" ry="3" />
      <circle cx="10.5" cy="7.5" r="0.7" fill="currentColor" stroke="none" />
      <circle cx="13.5" cy="7.5" r="0.7" fill="currentColor" stroke="none" />
      <path d="M9 6l-3-4M15 6l3-4" />
      <path d="M8 13l-4-1M16 13l4-1" />
      <path d="M8 17l-3 2M16 17l3 2" />
    </template>

    <!-- Fallback dot -->
    <template v-else>
      <circle cx="12" cy="12" r="2" fill="currentColor" />
    </template>
  </svg>
</template>

<style scoped>
.app-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
