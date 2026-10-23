<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { 
  Activity, 
  BarChart3, 
  Swords, 
  ShieldAlert, 
  Users, 
  Layers, 
  RotateCw,
  Calendar
} from 'lucide-vue-next'

const { 
  selectedWeek, 
  selectedView, 
  availableWeeks, 
  loadData, 
  isLoading,
  playerInjuries,
  gameHealthScores 
} = useInjuryData()

const totalRecords = computed(() => playerInjuries.value.length)

function refreshData() {
  loadData(true)
}
</script>

<template>
  <header class="app-header glass-panel">
    <div class="header-main-row">
      <!-- Brand & Status -->
      <div class="brand-group">
        <div class="brand-icon-wrapper">
          <Activity class="brand-icon" :size="24" />
          <span class="live-dot"></span>
        </div>
        <div class="brand-text">
          <div class="brand-title-wrap">
            <h1 class="brand-title">NFL INJURY PULSE</h1>
            <span class="season-badge">2026 SEASON</span>
          </div>
          <p class="brand-subtitle">
            Missed games, starter depth impacts & matchup health advantage analytics
          </p>
        </div>
      </div>

      <!-- Live Pipeline Sync & Refresh -->
      <div class="header-actions">
        <div class="data-indicator">
          <span class="data-indicator-dot"></span>
          <span class="data-indicator-text">
            <strong>{{ totalRecords.toLocaleString() }}</strong> records ingested
          </span>
        </div>
        <button 
          class="btn-primary refresh-btn" 
          @click="refreshData" 
          :disabled="isLoading"
          title="Reload freshest CSV outputs from /data"
        >
          <RotateCw :size="16" :class="{ 'spin-anim': isLoading }" />
          <span>{{ isLoading ? 'Refreshing...' : 'Sync CSV' }}</span>
        </button>
      </div>
    </div>

    <!-- Controls Row: Week Selector & View Switcher -->
    <div class="header-controls-row">
      <!-- Week Tabs -->
      <div class="week-selector-group">
        <div class="group-label">
          <Calendar :size="14" />
          <span>Select Week:</span>
        </div>
        <div class="week-pills">
          <button 
            class="week-pill" 
            :class="{ active: selectedWeek === 'all' }"
            @click="selectedWeek = 'all'"
          >
            All Weeks
          </button>
          <button 
            v-for="w in availableWeeks" 
            :key="w"
            class="week-pill"
            :class="{ active: selectedWeek === w }"
            @click="selectedWeek = w"
          >
            W{{ w }}
          </button>
        </div>
      </div>

      <!-- Navigation Views -->
      <nav class="nav-tabs" aria-label="Main Navigation">
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'overview' }"
          @click="selectedView = 'overview'"
        >
          <BarChart3 :size="16" />
          <span>Power Rankings</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'matchups' }"
          @click="selectedView = 'matchups'"
        >
          <Swords :size="16" />
          <span>Matchup Center</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'teams' }"
          @click="selectedView = 'teams'"
        >
          <ShieldAlert :size="16" />
          <span>Team Deep Dive</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'players' }"
          @click="selectedView = 'players'"
        >
          <Users :size="16" />
          <span>Player Database</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'analytics' }"
          @click="selectedView = 'analytics'"
        >
          <Layers :size="16" />
          <span>Surface & Trends</span>
        </button>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  padding: 1.25rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(10, 14, 23, 0.85) 100%);
}

.header-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}

.brand-icon-wrapper {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(16, 185, 129, 0.2));
  border: 1px solid rgba(56, 189, 248, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.25);
}

.live-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent-emerald);
  box-shadow: 0 0 8px var(--accent-emerald);
  animation: pulseGlow 2s infinite ease-in-out;
}

.brand-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.season-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-pill);
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-cyan);
  border: 1px solid rgba(56, 189, 248, 0.35);
  letter-spacing: 0.05em;
}

.brand-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.data-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.04);
  padding: 0.4rem 0.85rem;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-subtle);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.data-indicator-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-emerald);
  box-shadow: 0 0 6px var(--accent-emerald);
}

.refresh-btn {
  font-size: 0.82rem;
  padding: 0.5rem 0.95rem;
}

.spin-anim {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
  flex-wrap: wrap;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.week-selector-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.group-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.week-pills {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(0, 0, 0, 0.25);
  padding: 0.25rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.week-pill {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.week-pill:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.07);
}

.week-pill.active {
  background: var(--accent-cyan);
  color: #04101e;
  font-weight: 700;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(0, 0, 0, 0.25);
  padding: 0.25rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  overflow-x: auto;
}

.nav-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.45rem 0.95rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.nav-tab:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
}

.nav-tab.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

@media (max-width: 900px) {
  .header-controls-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .nav-tabs {
    width: 100%;
  }
}
</style>
