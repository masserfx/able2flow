<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps<{
  points: number | null
  size?: 'small' | 'medium' | 'large'
  variant?: 'default' | 'gradient' | 'minimal'
}>()

const sizeClass = computed(() => {
  switch (props.size) {
    case 'small': return 'badge-small'
    case 'large': return 'badge-large'
    default: return 'badge-medium'
  }
})

const variantClass = computed(() => {
  switch (props.variant) {
    case 'gradient': return 'badge-gradient'
    case 'minimal': return 'badge-minimal'
    default: return 'badge-default'
  }
})

const displayPoints = computed(() => props.points || 0)
</script>

<template>
  <div
    v-if="displayPoints > 0"
    :class="['points-badge', sizeClass, variantClass]"
    :title="`${displayPoints} points`"
  >
    <AppIcon name="gem" :size="14" class="badge-icon" />
    <span class="badge-value">{{ displayPoints }}</span>
  </div>
</template>

<style scoped>
.points-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-weight: 600;
  line-height: 1;
  flex-shrink: 0;
}

/* Sizes */
.badge-small {
  padding: 0.125rem 0.375rem;
  font-size: 0.625rem;
  gap: 0.125rem;
}

.badge-small .badge-icon {
  font-size: 0.625rem;
}

.badge-medium {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.badge-medium .badge-icon {
  font-size: 0.75rem;
}

.badge-large {
  padding: 0.5rem 0.75rem;
  font-size: 1rem;
}

.badge-large .badge-icon {
  font-size: 1rem;
}

/* Variants */
.badge-default {
  background: rgba(122, 162, 247, 0.15);
  border: 1px solid rgba(122, 162, 247, 0.3);
  color: #7aa2f7;
}

.badge-gradient {
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  border: none;
  color: var(--bg-dark);
  box-shadow: 0 2px 8px rgba(122, 162, 247, 0.3);
}

.badge-minimal {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
}

.badge-icon {
  line-height: 1;
}

.badge-value {
  font-variant-numeric: tabular-nums;
}

/* Hover effect */
.badge-gradient:hover {
  box-shadow: 0 4px 12px rgba(122, 162, 247, 0.4);
  transform: translateY(-1px);
  transition: all 0.2s;
}
</style>
