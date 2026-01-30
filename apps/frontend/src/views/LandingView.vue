<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const generatingPdf = ref(false)

function goToApp() {
  router.push('/dashboard')
}

async function downloadPdf() {
  generatingPdf.value = true

  try {
    // Dynamic import jsPDF
    const { jsPDF } = await import('jspdf')

    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    })

    // Add custom font for Czech diacritics
    doc.setFont('helvetica')

    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 20
    const contentWidth = pageWidth - 2 * margin
    let y = 20

    // Helper for text wrapping
    const addWrappedText = (text: string, fontSize: number, isBold = false) => {
      doc.setFontSize(fontSize)
      doc.setFont('helvetica', isBold ? 'bold' : 'normal')
      const lines = doc.splitTextToSize(text, contentWidth)

      // Check if we need a new page
      if (y + lines.length * fontSize * 0.4 > 280) {
        doc.addPage()
        y = 20
      }

      doc.text(lines, margin, y)
      y += lines.length * fontSize * 0.4 + 5
    }

    // Title
    doc.setFontSize(28)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(122, 162, 247)
    doc.text('Able2Flow', margin, y)
    y += 15

    // Subtitle
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(100, 100, 100)
    doc.text('Task Management + Monitoring + AI-Powered Incident Response', margin, y)
    y += 15

    doc.setTextColor(50, 50, 50)

    // About
    addWrappedText('O aplikaci', 16, true)
    addWrappedText('Able2Flow je moderni aplikace pro spravu ukolu a monitoring systemu. Kombinuje Kanban board s incident managementem a AI-powered analyzou. Aplikace je navrzena pro tymy, ktere potrebuji sledovat jak vyvoj projektu, tak dostupnost sluzeb.', 11)
    y += 5

    // Features
    addWrappedText('Hlavni funkce', 16, true)

    const features = [
      'Kanban Board - Drag & drop sprava ukolu s prioritami a terminy',
      'Multi-projekt podpora - Vice projektu s barevnym rozlisenim',
      'Google Calendar sync - Obousmerna synchronizace s kalendarem',
      'Monitoring - Health checks s automatickym vytvarenim incidentu',
      'AI Triage - Claude AI analyzuje incidenty a navrhuje reseni',
      'SLA Tracking - Sledovani uptime, MTTA/MTTR metrik',
      'Event Sourcing - Kompletni historie zmen s moznosti time travel',
      'Prilohy - Upload souboru k ukolum s nahledem v kanbanu',
      'i18n - Cestina a anglictina',
    ]

    features.forEach(f => {
      doc.setFontSize(10)
      doc.text('• ' + f, margin + 5, y)
      y += 6
    })
    y += 5

    // Tech Stack
    addWrappedText('Technologie', 16, true)
    addWrappedText('Backend: FastAPI, Python 3.11+, SQLite, httpx', 11)
    addWrappedText('Frontend: Vue 3, TypeScript, Vite, Vue Router', 11)
    addWrappedText('Auth: Clerk (Google OAuth)', 11)
    addWrappedText('AI: Anthropic Claude API', 11)
    addWrappedText('Integrace: Google Calendar, Docs, Gmail, Slack', 11)
    y += 5

    // AI Integration
    addWrappedText('AI integrace', 16, true)
    addWrappedText('Aplikace vyuziva Claude AI pro automatickou analyzu incidentu. AI poskytuje: hodnoceni zavaznosti, identifikaci moznych pricin, navrhy reseni (runbook), a confidence score analyzy.', 11)
    y += 5

    // Extensions
    addWrappedText('Moznosti rozsireni', 16, true)
    const extensions = [
      'Google Drive - Upload priloh do cloudu',
      'Google Docs - Propojeni dokumentu s ukoly',
      'Gmail - Vytvareni ukolu z emailu',
      'Slack - Notifikace a slash commands',
      'Webhooks - Integrace s externimi systemy',
    ]
    extensions.forEach(e => {
      doc.setFontSize(10)
      doc.text('• ' + e, margin + 5, y)
      y += 6
    })

    // Footer
    doc.setFontSize(9)
    doc.setTextColor(150, 150, 150)
    doc.text('Able2Flow - https://github.com/masserfx/able2flow', margin, 285)
    doc.text('Generovano: ' + new Date().toLocaleDateString('cs-CZ'), pageWidth - margin - 40, 285)

    // Save
    doc.save('Able2Flow-popis.pdf')
  } catch (e) {
    console.error('Failed to generate PDF:', e)
    alert('Nepodařilo se vygenerovat PDF')
  } finally {
    generatingPdf.value = false
  }
}
</script>

<template>
  <div class="landing">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="logo">Able2Flow</h1>
        <p class="tagline">Task Management + Monitoring + AI-Powered Incident Response</p>
        <div class="hero-actions">
          <button class="btn-primary" @click="goToApp">
            Spustit aplikaci →
          </button>
          <button class="btn-secondary" @click="downloadPdf" :disabled="generatingPdf">
            {{ generatingPdf ? 'Generuji...' : '📄 Stáhnout PDF' }}
          </button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="mockup-window">
          <div class="mockup-header">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
          </div>
          <div class="mockup-content">
            <div class="mockup-sidebar"></div>
            <div class="mockup-board">
              <div class="mockup-column" v-for="i in 4" :key="i">
                <div class="mockup-card" v-for="j in (5-i)" :key="j"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features">
      <h2>Hlavní funkce</h2>
      <div class="features-grid">
        <div class="feature-card">
          <span class="feature-icon">📋</span>
          <h3>Kanban Board</h3>
          <p>Drag & drop správa úkolů s prioritami, termíny a štítky. Více projektů s barevným rozlišením.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">📅</span>
          <h3>Google Calendar</h3>
          <p>Obousměrná synchronizace úkolů s kalendářem. Změny v kalendáři se automaticky projeví v aplikaci.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">🔍</span>
          <h3>Monitoring</h3>
          <p>Health checks služeb s automatickým vytvářením incidentů při výpadku. Response time tracking.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">🤖</span>
          <h3>AI Triage</h3>
          <p>Claude AI analyzuje incidenty, navrhuje závažnost, identifikuje příčiny a doporučuje řešení.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">📊</span>
          <h3>SLA Tracking</h3>
          <p>Sledování uptime, MTTA/MTTR metrik. Health score 0-100 pro celkový přehled systému.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">🕐</span>
          <h3>Event Sourcing</h3>
          <p>Kompletní historie změn s možností time travel. Obnova entit do předchozího stavu.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">📎</span>
          <h3>Přílohy</h3>
          <p>Upload souborů k úkolům (obrázky, dokumenty, archivy). Náhled příloh přímo v kanban kartě.</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon">🌍</span>
          <h3>i18n</h3>
          <p>Plná podpora češtiny a angličtiny včetně diakritiky. Přepínání jazyka jedním kliknutím.</p>
        </div>
      </div>
    </section>

    <!-- Tech Stack Section -->
    <section class="tech-stack">
      <h2>Technologie</h2>
      <div class="tech-grid">
        <div class="tech-group">
          <h3>Backend</h3>
          <ul>
            <li><strong>FastAPI</strong> - Moderní Python framework</li>
            <li><strong>SQLite</strong> - Jednoduchá databáze</li>
            <li><strong>httpx</strong> - Async HTTP klient</li>
            <li><strong>Pydantic</strong> - Validace dat</li>
          </ul>
        </div>
        <div class="tech-group">
          <h3>Frontend</h3>
          <ul>
            <li><strong>Vue 3</strong> - Composition API</li>
            <li><strong>TypeScript</strong> - Type safety</li>
            <li><strong>Vite</strong> - Rychlý build tool</li>
            <li><strong>Vue Router</strong> - SPA navigace</li>
          </ul>
        </div>
        <div class="tech-group">
          <h3>Integrace</h3>
          <ul>
            <li><strong>Clerk</strong> - Autentizace</li>
            <li><strong>Google APIs</strong> - Calendar, Docs</li>
            <li><strong>Slack API</strong> - Notifikace</li>
            <li><strong>Claude AI</strong> - Incident triage</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- AI Section -->
    <section class="ai-section">
      <div class="ai-content">
        <h2>🤖 AI-Powered Incident Triage</h2>
        <p>
          Able2Flow využívá <strong>Anthropic Claude API</strong> pro automatickou analýzu incidentů.
          AI systém poskytuje:
        </p>
        <ul>
          <li>🎯 <strong>Severity Assessment</strong> - Automatické hodnocení závažnosti</li>
          <li>🔍 <strong>Root Cause Analysis</strong> - Identifikace možných příčin</li>
          <li>📝 <strong>Runbook Generation</strong> - Návrhy kroků k řešení</li>
          <li>📊 <strong>Confidence Score</strong> - Míra jistoty analýzy</li>
        </ul>
      </div>
      <div class="ai-demo">
        <div class="ai-card">
          <div class="ai-header">Claude AI Analysis</div>
          <div class="ai-body">
            <div class="ai-line"><span class="label">Severity:</span> <span class="value critical">CRITICAL</span></div>
            <div class="ai-line"><span class="label">Confidence:</span> <span class="value">87%</span></div>
            <div class="ai-line"><span class="label">Root Cause:</span></div>
            <div class="ai-text">Database connection pool exhausted due to slow queries...</div>
            <div class="ai-line"><span class="label">Suggested Action:</span></div>
            <div class="ai-text">1. Restart DB connection pool<br>2. Identify slow queries<br>3. Add query timeout</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Extensions Section -->
    <section class="extensions">
      <h2>Možnosti rozšíření</h2>
      <div class="extensions-grid">
        <div class="extension-card planned">
          <span class="status">Plánováno</span>
          <h3>📁 Google Drive</h3>
          <p>Upload příloh do cloudu, sdílené složky pro projekty</p>
        </div>
        <div class="extension-card planned">
          <span class="status">Plánováno</span>
          <h3>📄 Google Docs</h3>
          <p>Propojení dokumentů s úkoly, vytváření docs z tasků</p>
        </div>
        <div class="extension-card planned">
          <span class="status">Plánováno</span>
          <h3>✉️ Gmail</h3>
          <p>Vytváření úkolů z emailů, notifikace</p>
        </div>
        <div class="extension-card ready">
          <span class="status">Připraveno</span>
          <h3>💬 Slack</h3>
          <p>Notifikace do kanálů, slash commands</p>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta">
      <h2>Začněte používat Able2Flow</h2>
      <p>Open source řešení pro správu úkolů a monitoring</p>
      <div class="cta-buttons">
        <button class="btn-primary large" @click="goToApp">
          Spustit aplikaci
        </button>
        <a href="https://github.com/masserfx/able2flow" target="_blank" class="btn-secondary large">
          ⭐ GitHub
        </a>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <p>Able2Flow © 2026 |
        <a href="https://github.com/masserfx/able2flow" target="_blank">GitHub</a> |
        <router-link to="/dashboard">Dashboard</router-link>
      </p>
    </footer>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  background: linear-gradient(180deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
  color: var(--text-primary);
}

/* Hero Section */
.hero {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  padding: 4rem;
  align-items: center;
  max-width: 1920px;
  margin: 0 auto;
}

.hero-content {
  max-width: 600px;
}

.logo {
  font-size: 4rem;
  font-weight: 800;
  background: linear-gradient(135deg, #7aa2f7 0%, #bb9af7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 1rem 0;
}

.tagline {
  font-size: 1.5rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
  line-height: 1.4;
}

.hero-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary {
  background: linear-gradient(135deg, #7aa2f7 0%, #7dcfff 100%);
  color: var(--bg-darker);
  border: none;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(122, 162, 247, 0.3);
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 2px solid var(--border-color);
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.btn-secondary:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.large {
  padding: 1.25rem 2.5rem;
  font-size: 1.2rem;
}

/* Mockup */
.hero-visual {
  display: flex;
  justify-content: center;
}

.mockup-window {
  background: var(--bg-lighter);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  width: 100%;
  max-width: 600px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.mockup-header {
  padding: 0.75rem 1rem;
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: #f7768e; }
.dot.yellow { background: #e0af68; }
.dot.green { background: #9ece6a; }

.mockup-content {
  display: flex;
  padding: 1rem;
  gap: 1rem;
  min-height: 300px;
}

.mockup-sidebar {
  width: 50px;
  background: var(--bg-dark);
  border-radius: 8px;
}

.mockup-board {
  flex: 1;
  display: flex;
  gap: 0.75rem;
}

.mockup-column {
  flex: 1;
  background: var(--bg-dark);
  border-radius: 8px;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mockup-card {
  height: 40px;
  background: var(--bg-lighter);
  border-radius: 6px;
  border-left: 3px solid var(--accent-blue);
}

.mockup-column:nth-child(2) .mockup-card { border-color: var(--accent-yellow); }
.mockup-column:nth-child(3) .mockup-card { border-color: var(--accent-purple); }
.mockup-column:nth-child(4) .mockup-card { border-color: var(--accent-green); }

/* Features Section */
.features {
  padding: 6rem 4rem;
  max-width: 1920px;
  margin: 0 auto;
}

.features h2, .tech-stack h2, .ai-section h2, .extensions h2, .cta h2 {
  font-size: 2.5rem;
  text-align: center;
  margin-bottom: 3rem;
  color: var(--text-primary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.feature-card {
  background: var(--bg-lighter);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 2rem;
  transition: transform 0.2s, border-color 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent-blue);
}

.feature-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  margin: 0 0 0.75rem 0;
  color: var(--text-primary);
}

.feature-card p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Tech Stack */
.tech-stack {
  padding: 6rem 4rem;
  background: var(--bg-lighter);
  max-width: 1920px;
  margin: 0 auto;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.tech-group {
  background: var(--bg-dark);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid var(--border-color);
}

.tech-group h3 {
  font-size: 1.5rem;
  margin: 0 0 1.5rem 0;
  color: var(--accent-blue);
}

.tech-group ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tech-group li {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.tech-group li:last-child {
  border-bottom: none;
}

.tech-group li strong {
  color: var(--text-primary);
}

/* AI Section */
.ai-section {
  padding: 6rem 4rem;
  max-width: 1920px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.ai-content {
  max-width: 600px;
}

.ai-content p {
  font-size: 1.2rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.ai-content ul {
  list-style: none;
  padding: 0;
}

.ai-content li {
  padding: 0.75rem 0;
  font-size: 1.1rem;
  color: var(--text-secondary);
}

.ai-demo {
  display: flex;
  justify-content: center;
}

.ai-card {
  background: var(--bg-lighter);
  border: 1px solid var(--accent-purple);
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(187, 154, 247, 0.2);
}

.ai-header {
  background: linear-gradient(135deg, #bb9af7 0%, #7aa2f7 100%);
  color: var(--bg-darker);
  padding: 1rem 1.5rem;
  font-weight: 600;
}

.ai-body {
  padding: 1.5rem;
}

.ai-line {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.ai-line .label {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.ai-line .value {
  color: var(--text-primary);
  font-weight: 600;
}

.ai-line .value.critical {
  color: #f7768e;
}

.ai-text {
  background: var(--bg-dark);
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  line-height: 1.5;
}

/* Extensions */
.extensions {
  padding: 6rem 4rem;
  background: var(--bg-lighter);
  max-width: 1920px;
  margin: 0 auto;
}

.extensions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.extension-card {
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 2rem;
  position: relative;
}

.extension-card .status {
  position: absolute;
  top: 1rem;
  right: 1rem;
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-weight: 600;
}

.extension-card.planned .status {
  background: rgba(224, 175, 104, 0.2);
  color: #e0af68;
}

.extension-card.ready .status {
  background: rgba(158, 206, 106, 0.2);
  color: #9ece6a;
}

.extension-card h3 {
  font-size: 1.25rem;
  margin: 0 0 0.75rem 0;
}

.extension-card p {
  color: var(--text-secondary);
  margin: 0;
}

/* CTA */
.cta {
  padding: 6rem 4rem;
  text-align: center;
  max-width: 1920px;
  margin: 0 auto;
}

.cta p {
  font-size: 1.25rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

/* Footer */
.landing-footer {
  padding: 2rem 4rem;
  text-align: center;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
}

.landing-footer a {
  color: var(--accent-blue);
  text-decoration: none;
}

.landing-footer a:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 1400px) {
  .features-grid, .extensions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
    text-align: center;
    padding: 2rem;
  }

  .hero-content {
    max-width: 100%;
  }

  .hero-actions {
    justify-content: center;
  }

  .ai-section {
    grid-template-columns: 1fr;
  }

  .tech-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .features-grid, .extensions-grid {
    grid-template-columns: 1fr;
  }

  .logo {
    font-size: 2.5rem;
  }

  .tagline {
    font-size: 1.1rem;
  }
}
</style>
