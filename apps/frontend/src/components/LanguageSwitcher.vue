<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

function toggleLocale() {
  locale.value = locale.value === 'cs' ? 'en' : 'cs'
  localStorage.setItem('locale', locale.value)
}
</script>

<template>
  <button @click="toggleLocale" class="lang-switcher">
    {{ locale === 'cs' ? '🇨🇿 CZ' : '🇬🇧 EN' }}
  </button>
</template>

<style scoped>
.lang-switcher {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-highlight);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lang-switcher:hover {
  background-color: var(--bg-lighter);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.lang-switcher:focus {
  outline: 2px solid var(--accent-cyan);
  outline-offset: 2px;
}
</style>
