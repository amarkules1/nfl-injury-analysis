<script setup>
import { useInjuryData } from '../composables/useInjuryData'

const { 
  selectedWeek, 
  selectedView, 
  availableWeeks 
} = useInjuryData()
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand Line -->
      <div class="brand-row">
        <div class="brand-title-wrap">
          <h1 class="brand-title">NFL INJURY INTELLIGENCE</h1>
          <span class="season-sub mono-val">2026 Regular Season</span>
        </div>
      </div>

      <!-- Controls & Tabs -->
      <div class="controls-row">
        <!-- Week Selector -->
        <div class="week-selector">
          <span class="control-label mono-val">WEEK</span>
          <div class="week-pills">
            <button 
              class="week-btn" 
              :class="{ active: selectedWeek === 'all' }"
              @click="selectedWeek = 'all'"
            >
              ALL
            </button>
            <button 
              v-for="w in availableWeeks" 
              :key="w"
              class="week-btn"
              :class="{ active: selectedWeek === w }"
              @click="selectedWeek = w"
            >
              {{ w }}
            </button>
          </div>
        </div>

        <!-- Navigation Tabs (NO NUMBERS) -->
        <nav class="nav-tabs" aria-label="Dashboard Views">
          <button 
            class="nav-tab" 
            :class="{ active: selectedView === 'overview' }"
            @click="selectedView = 'overview'"
          >
            POWER RANKINGS
          </button>
          <button 
            class="nav-tab" 
            :class="{ active: selectedView === 'matchups' }"
            @click="selectedView = 'matchups'"
          >
            MATCHUP CENTER
          </button>
          <button 
            class="nav-tab" 
            :class="{ active: selectedView === 'teams' }"
            @click="selectedView = 'teams'"
          >
            TEAM DEEP DIVE
          </button>
          <button 
            class="nav-tab" 
            :class="{ active: selectedView === 'players' }"
            @click="selectedView = 'players'"
          >
            PLAYER DATABASE
          </button>
        </nav>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-secondary);
  padding: 1.25rem 1.75rem 0.85rem 1.75rem;
}

.header-inner {
  max-width: 1650px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-title-wrap {
  display: flex;
  align-items: baseline;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.brand-title {
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #ffffff;
}

.season-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.week-selector {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.control-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.week-pills {
  display: flex;
  align-items: center;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
}

.week-btn {
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 0.74rem;
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  transition: all 0.1s ease;
}

.week-btn:last-child {
  border-right: none;
}

.week-btn:hover {
  color: #ffffff;
  background: var(--bg-card);
}

.week-btn.active {
  background: var(--accent-cyan);
  color: #07090e;
  font-weight: 700;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  overflow-x: auto;
}

.nav-tab {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.45rem 0.85rem;
  border-radius: var(--radius-xs);
  cursor: pointer;
  transition: all 0.12s ease;
  white-space: nowrap;
}

.nav-tab:hover {
  color: #ffffff;
  background: var(--bg-card);
}

.nav-tab.active {
  color: #ffffff;
  background: var(--bg-card);
  border-color: var(--border-card);
  border-bottom: 2px solid var(--accent-cyan);
}

@media (max-width: 900px) {
  .controls-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
