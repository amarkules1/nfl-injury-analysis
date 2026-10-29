<script setup>
import { useInjuryData } from '../composables/useInjuryData'
import { Calendar, Sparkles } from 'lucide-vue-next'

const { 
  selectedSeason,
  availableSeasons,
  setSeason,
  selectedWeek, 
  selectedView, 
  availableWeeks,
  upcomingWeek,
  hasUpcomingProjections,
  isUpcomingSelected
} = useInjuryData()

function onSeasonChange(e) {
  setSeason(Number(e.target.value))
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand Line & Season Picker -->
      <div class="brand-row">
        <div class="brand-title-wrap">
          <h1 class="brand-title">NFL INJURY INTELLIGENCE</h1>
          <span class="season-sub mono-val">Health Power Rankings & Predictive Analytics</span>
        </div>

        <!-- Season Picker Dropdown -->
        <div class="season-picker-wrap">
          <Calendar :size="14" class="season-icon" />
          <label for="season-select" class="season-label mono-val">SEASON</label>
          <select 
            id="season-select" 
            class="season-select mono-val"
            :value="selectedSeason"
            @change="onSeasonChange"
          >
            <option v-for="s in availableSeasons" :key="s" :value="s">
              {{ s }} {{ s === 2026 ? '(Current)' : '' }}
            </option>
          </select>
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
            <!-- Upcoming Week Predictive Model button -->
            <button
              v-if="hasUpcomingProjections && upcomingWeek"
              class="week-btn upcoming-model-btn"
              :class="{ active: isUpcomingSelected }"
              @click="selectedWeek = 'upcoming'"
              title="Machine Learning Model: Player Play Likelihood & Health Projections"
            >
              <Sparkles :size="12" class="sparkle-icon" />
              UPCOMING (WK {{ upcomingWeek }})
            </button>
          </div>
        </div>

        <!-- Navigation Tabs -->
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
  gap: 1rem;
  flex-wrap: wrap;
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

.season-picker-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  padding: 0.35rem 0.75rem;
}

.season-icon {
  color: var(--accent-cyan);
}

.season-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.season-select {
  background: transparent;
  border: none;
  color: #ffffff;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  outline: none;
  padding-right: 0.25rem;
}

.season-select option {
  background: #1c2334;
  color: #ffffff;
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
  display: flex;
  align-items: center;
  gap: 0.3rem;
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

.upcoming-model-btn {
  color: #a78bfa;
  font-weight: 700;
}

.upcoming-model-btn:hover {
  color: #c4b5fd;
  background: rgba(167, 139, 250, 0.12);
}

.upcoming-model-btn.active {
  background: #8b5cf6;
  color: #ffffff;
}

.sparkle-icon {
  color: inherit;
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
