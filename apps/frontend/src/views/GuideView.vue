<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppIcon from '../components/AppIcon.vue'

const { t: _t } = useI18n()
const activeSection = ref(0)

const sections = [
  {
    icon: 'target',
    title: 'Marketplace',
    subtitle: 'Vyber si úkol',
    steps: [
      { num: 1, text: 'Otevři sekci "Trh s Úkoly" v navigaci vlevo' },
      { num: 2, text: 'Prohlédni dostupné úkoly seřazené podle bodů' },
      { num: 3, text: 'Klikni na "Vzít Task" u úkolu, který tě zajímá' },
      { num: 4, text: 'Úkol se přiřadí tobě a zmizí z marketplace' },
    ],
    tip: 'Úkoly s vyššími body = více práce, ale lepší pozice na žebříčku!',
    color: '#7aa2f7',
  },
  {
    icon: 'timer',
    title: 'Time Tracking',
    subtitle: 'Měř svůj čas',
    steps: [
      { num: 1, text: 'Otevři svůj přiřazený úkol na Nástěnce' },
      { num: 2, text: 'V sekci "ANT HILL - Gamifikace" klikni Spustit' },
      { num: 3, text: 'Pracuj na úkolu - timer běží na pozadí' },
      { num: 4, text: 'Klikni Zastavit až dokončíš práci' },
    ],
    tip: 'Dokončíš-li rychleji než odhad (o 20%+), dostaneš bonus body!',
    color: '#bb9af7',
  },
  {
    icon: 'gem',
    title: 'Body & Bonusy',
    subtitle: 'Jak získat body',
    stepIcons: ['zap', 'running', 'calendar', 'fire'],
    steps: [
      { num: 0, text: 'Základní body: 1 bod = 10 minut odhadovaného času' },
      { num: 0, text: 'Speed bonus (+20%): Dokončení pod 80% odhadovaného času' },
      { num: 0, text: 'Deadline bonus (+10%): Dokončení před termínem' },
      { num: 0, text: 'Priority bonus: Critical +5, High +3 extra bodů' },
    ],
    tip: 'Příklad: 2h task = 12 bodů + speed bonus 2 + deadline 1 = 15 bodů!',
    color: '#e0af68',
  },
  {
    icon: 'trophy',
    title: 'Leaderboard',
    subtitle: 'Soutěž s kolegy',
    stepIcons: ['chart', 'calendar', 'medal-gold', 'chart-up'],
    steps: [
      { num: 0, text: 'Otevři "Žebříček" pro přehled nejlepších' },
      { num: 0, text: 'Přepínej mezi Denní / Týdenní / Měsíční / Celkový' },
      { num: 0, text: 'Sleduj svou pozici a body ostatních' },
      { num: 0, text: 'Každý týden se žebříček resetuje - nová šance!' },
    ],
    tip: 'Denní žebříček se resetuje o půlnoci, týdenní v neděli.',
    color: '#9ece6a',
  },
  {
    icon: 'bell',
    title: 'Notifikace',
    subtitle: 'Buď v obraze',
    stepIcons: ['priority-critical', 'megaphone', 'volume', 'check-circle'],
    steps: [
      { num: 0, text: 'Červená badge na zvonečku = nepřečtené notifikace' },
      { num: 0, text: 'Toast popup se objeví při nových událostech' },
      { num: 0, text: 'Zvukový signál upozorní na důležité změny' },
      { num: 0, text: 'Klikni na notifikaci pro označení jako přečtená' },
    ],
    tip: 'Notifikace zahrnují: přiřazení tasků, získání bodů, dokončení úkolů.',
    color: '#f7768e',
  },
  {
    icon: 'clipboard',
    title: 'Nástěnka',
    subtitle: 'Kanban board',
    stepIcons: ['board', 'user', 'search', 'sparkles'],
    steps: [
      { num: 0, text: 'Přetahuj úkoly mezi sloupci: Backlog → To Do → In Progress → Done' },
      { num: 0, text: 'Tvoje úkoly mají badge s tvým avatarem' },
      { num: 0, text: 'Klikni na úkol pro detail, odhad a time tracking' },
      { num: 0, text: 'Přesun do "Done" automaticky přidělí body' },
    ],
    tip: 'Nastav odhad (minuty) před zahájením práce pro správný výpočet bodů.',
    color: '#73daca',
  },
]

const workflow = [
  { step: 1, label: 'Marketplace', desc: 'Vyber task', icon: 'target' },
  { step: 2, label: 'Odhad', desc: 'Nastav minuty', icon: 'clock' },
  { step: 3, label: 'Tracking', desc: 'Spusť timer', icon: 'play' },
  { step: 4, label: 'Dokončení', desc: 'Zastav & hotovo', icon: 'check-circle' },
  { step: 5, label: 'Body!', desc: 'Získej odměnu', icon: 'gem' },
]
</script>

<template>
  <div class="guide">
    <!-- Hero -->
    <header class="guide-hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="hero-title">
          <AppIcon name="ant" :size="48" class="hero-icon" />
          ANT HILL
        </h1>
        <p class="hero-subtitle">Gamifikovaný systém správy úkolů</p>
        <p class="hero-desc">
          Pull-based marketplace, kde si sám vybíráš úkoly,
          sleduješ čas a sbíráš body na žebříčku.
        </p>
      </div>
    </header>

    <!-- Workflow Pipeline -->
    <section class="workflow-section">
      <h2 class="section-title">Jak to funguje</h2>
      <div class="workflow-pipeline">
        <div
          v-for="(w, i) in workflow"
          :key="i"
          class="workflow-step"
          :style="{ animationDelay: `${i * 0.15}s` }"
        >
          <div class="step-icon"><AppIcon :name="w.icon" :size="28" /></div>
          <div class="step-label">{{ w.label }}</div>
          <div class="step-desc">{{ w.desc }}</div>
          <div v-if="i < workflow.length - 1" class="step-arrow">→</div>
        </div>
      </div>
    </section>

    <!-- Detail Sections -->
    <section class="sections-grid">
      <div
        v-for="(section, index) in sections"
        :key="index"
        class="section-card"
        :class="{ active: activeSection === index }"
        :style="{
          '--accent': section.color,
          animationDelay: `${index * 0.1}s`
        }"
        @click="activeSection = index"
      >
        <div class="card-header">
          <AppIcon :name="section.icon" :size="28" class="card-icon" />
          <div>
            <h3 class="card-title">{{ section.title }}</h3>
            <p class="card-subtitle">{{ section.subtitle }}</p>
          </div>
        </div>

        <div class="card-body" v-if="activeSection === index">
          <div class="steps-list">
            <div
              v-for="(step, si) in section.steps"
              :key="si"
              class="step-item"
              :style="{ animationDelay: `${si * 0.08}s` }"
            >
              <span class="step-badge">
                <AppIcon v-if="section.stepIcons" :name="section.stepIcons[si] ?? ''" :size="16" />
                <template v-else>{{ step.num }}</template>
              </span>
              <span class="step-text">{{ step.text }}</span>
            </div>
          </div>
          <div class="tip-box">
            <AppIcon name="sparkles" :size="18" class="tip-icon" />
            <span class="tip-text">{{ section.tip }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Points Calculator -->
    <section class="calculator-section">
      <h2 class="section-title">Kalkulačka bodů</h2>
      <div class="calc-grid">
        <div class="calc-card">
          <div class="calc-header">Malý task</div>
          <div class="calc-time">30 min</div>
          <div class="calc-points">3 body</div>
          <div class="calc-bonus">+ speed bonus: 1</div>
        </div>
        <div class="calc-card">
          <div class="calc-header">Střední task</div>
          <div class="calc-time">1 hodina</div>
          <div class="calc-points">6 bodů</div>
          <div class="calc-bonus">+ speed bonus: 1, deadline: 1</div>
        </div>
        <div class="calc-card featured">
          <div class="calc-header">Velký task</div>
          <div class="calc-time">3 hodiny</div>
          <div class="calc-points">18 bodů</div>
          <div class="calc-bonus">+ speed: 4, deadline: 2, priority: 5</div>
        </div>
      </div>
    </section>

    <!-- Keyboard Shortcuts -->
    <section class="shortcuts-section">
      <h2 class="section-title">Tipy pro efektivitu</h2>
      <div class="tips-grid">
        <div class="tip-card">
          <AppIcon name="target" :size="24" class="tip-card-icon" />
          <h4>Ráno si vyber</h4>
          <p>Začni den výběrem tasků z marketplace. Ranní úkoly = méně konkurence.</p>
        </div>
        <div class="tip-card">
          <AppIcon name="timer" :size="24" class="tip-card-icon" />
          <h4>Přesné odhady</h4>
          <p>Realističtější odhad = větší šance na speed bonus (pod 80%).</p>
        </div>
        <div class="tip-card">
          <AppIcon name="fire" :size="24" class="tip-card-icon" style="color: #f7768e" />
          <h4>Critical tasky</h4>
          <p>Critical priority dává +5 bonusových bodů. Vyplatí se je řešit přednostně.</p>
        </div>
        <div class="tip-card">
          <AppIcon name="chart-up" :size="24" class="tip-card-icon" />
          <h4>Konzistence</h4>
          <p>Pravidelné dokončování menších tasků > občasný velký. Denní žebříček odměňuje aktivitu.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.guide {
  max-width: 960px;
  margin: 0 auto;
  padding-bottom: 3rem;
}

/* Hero */
.guide-hero {
  position: relative;
  padding: 3rem 2rem;
  margin: -1.5rem -1.5rem 2rem;
  overflow: hidden;
  border-radius: 0 0 24px 24px;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(122, 162, 247, 0.15) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(187, 154, 247, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(224, 175, 104, 0.08) 0%, transparent 40%),
    linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
  z-index: 0;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  animation: fadeSlideUp 0.6s ease-out;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}

.hero-icon {
  font-size: 2.2rem;
  margin-right: 0.5rem;
}

.hero-subtitle {
  font-size: 1.1rem;
  font-weight: 200;
  color: var(--accent-blue);
  margin: 0 0 1rem;
  letter-spacing: 0.05em;
}

.hero-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.6;
}

/* Section titles */
.section-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 2.5rem 0 1.25rem;
  letter-spacing: -0.01em;
}

/* Workflow Pipeline */
.workflow-section {
  margin: 2rem 0;
}

.workflow-pipeline {
  display: flex;
  align-items: flex-start;
  gap: 0;
  overflow-x: auto;
  padding: 1rem 0;
}

.workflow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  min-width: 120px;
  flex: 1;
  animation: fadeSlideUp 0.5s ease-out both;
}

.step-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--bg-highlight);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 0.75rem;
  transition: all 0.3s;
}

.workflow-step:hover .step-icon {
  border-color: var(--accent-blue);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(122, 162, 247, 0.2);
}

.step-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
}

.step-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.step-arrow {
  position: absolute;
  right: -12px;
  top: 18px;
  font-size: 1.2rem;
  color: var(--text-muted);
  font-weight: 200;
}

/* Section Cards */
.sections-grid {
  display: grid;
  gap: 0.75rem;
}

.section-card {
  background: var(--bg-card, var(--bg-highlight));
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s;
  animation: fadeSlideUp 0.5s ease-out both;
}

.section-card:hover {
  border-color: var(--accent);
}

.section-card.active {
  border-color: var(--accent);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15), 0 0 0 1px var(--accent);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  font-size: 1.75rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-darker);
  border-radius: 12px;
  flex-shrink: 0;
}

.card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-primary);
}

.card-subtitle {
  margin: 0.125rem 0 0;
  font-size: 0.8rem;
  font-weight: 200;
  color: var(--text-muted);
}

.card-body {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: fadeSlideLeft 0.3s ease-out both;
}

.step-badge {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  flex-shrink: 0;
}

.step-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.tip-box {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-top: 1rem;
  padding: 0.875rem 1rem;
  background: rgba(224, 175, 104, 0.08);
  border: 1px solid rgba(224, 175, 104, 0.2);
  border-radius: 10px;
}

.tip-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.tip-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Calculator */
.calculator-section {
  margin: 2rem 0;
}

.calc-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.calc-card {
  background: var(--bg-highlight);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s;
}

.calc-card:hover {
  transform: translateY(-2px);
}

.calc-card.featured {
  border-color: var(--accent-blue);
  background: linear-gradient(135deg, var(--bg-highlight), rgba(122, 162, 247, 0.08));
  box-shadow: 0 4px 20px rgba(122, 162, 247, 0.15);
}

.calc-header {
  font-size: 0.8rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.calc-time {
  font-size: 1.5rem;
  font-weight: 200;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.calc-points {
  font-size: 1.75rem;
  font-weight: 900;
  color: var(--accent-blue);
  margin-bottom: 0.5rem;
}

.calc-bonus {
  font-size: 0.7rem;
  color: var(--accent-green, #9ece6a);
  line-height: 1.4;
}

/* Tips Grid */
.shortcuts-section {
  margin: 2rem 0;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.tip-card {
  background: var(--bg-highlight);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.25rem;
  transition: all 0.3s;
}

.tip-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
}

.tip-card-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.75rem;
}

.tip-card h4 {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--text-primary);
}

.tip-card p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Animations */
@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeSlideLeft {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .guide-hero {
    padding: 2rem 1rem;
    margin: -1rem -1rem 1.5rem;
  }

  .hero-title {
    font-size: 1.75rem;
  }

  .workflow-pipeline {
    gap: 0.25rem;
  }

  .workflow-step {
    min-width: 80px;
  }

  .step-arrow {
    display: none;
  }

  .calc-grid {
    grid-template-columns: 1fr;
  }

  .tips-grid {
    grid-template-columns: 1fr;
  }
}
</style>
