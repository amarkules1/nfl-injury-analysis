<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { RotateCw } from 'lucide-vue-next'

const { 
  selectedWeek, 
  selectedView, 
  availableWeeks, 
  loadData, 
  isLoading,
  playerInjuries 
} = useInjuryData()

const totalRecords = computed(() => playerInjuries.value.length)

function refreshData() {
  loadData(true)
}
</script>

<template>
  <header class="app-header sharp-panel">
    <!-- Top Branding & Sync Bar -->
    <div class="header-top-row">
      <div class="brand-block">
        <div class="brand-title-line">
          <span class="brand-shield-mark">NFL</span>
          <h1 class="brand-title">INJURY & HEALTH INTELLIGENCE</h1>
          <span class="badge-tag badge-tag-starter">2026 SEASON</span>
        </div>
        <p class="brand-sub">
          Official Injury Report Ingestion • Starter Depth Casualty Tracking • 0–100 Team Health Ratings
        </p>
      </div>

      <div class="header-right-meta">
        <div class="data-stats-pill mono-val">
          <span class="live-status-dot"></span>
          <span><strong>{{ totalRecords.toLocaleString() }}</strong> RECORDS LOGGED</span>
        </div>
        <button 
          class="btn-action refresh-btn" 
          @click="refreshData" 
          :disabled="isLoading"
          title="Sync latest CSV from data/"
        >
          <RotateCw :size="13" :class="{ 'spin-anim': isLoading }" />
          <span>{{ isLoading ? 'SYNCING...' : 'SYNC DATA' }}</span>
        </button>
      </div>
    </div>

    <!-- Controls Row: Week Selector & View Tabs -->
    <div class="header-nav-row">
      <!-- Week Selector -->
      <div class="week-selector">
        <span class="control-label">WEEK:</span>
        <div class="week-btn-group">
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
            W{{ w }}
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
          <span class="tab-index">01</span>
          <span>POWER RANKINGS</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'matchups' }"
          @click="selectedView = 'matchups'"
        >
          <span class="tab-index">02</span>
          <span>MATCHUP CENTER</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'teams' }"
          @click="selectedView = 'teams'"
        >
          <span class="tab-index">03</span>
          <span>TEAM DEEP DIVE</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'players' }"
          @click="selectedView = 'players'"
        >
          <span class="tab-index">04</span>
          <span>PLAYER DATABASE</span>
        </button>
        <button 
          class="nav-tab" 
          :class="{ active: selectedView === 'analytics' }"
          @click="selectedView = 'analytics'"
        >
          <span class="tab-index">05</span>
          <span>SURFACE & TRENDS</span>
        </button>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid var(--border-card);
  padding: 1rem 1.5rem 0 1.5rem;
  background: var(--bg-secondary);
}

.header-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-wrap: wrap;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.brand-title-line {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.brand-shield-mark {
  background: #00e676;
  color: #07080c;
  font-family: var(--font-display);
  font-weight: 900;
  font-size: 0.95rem;
  padding: 0.1rem 0.45rem;
  border-radius: var(--radius-xs);
  letter-spacing: 0.06em;
}

.brand-title {
  font-size: 1.45rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  color: #ffffff;
}

.brand-sub {
  font-size: 0.8rem;
  color: var(--text-muted);
  letter-spacing: 0.02em;
}

.header-right-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.data-stats-pill {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  padding: 0.35rem 0.65rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
  border-radius: var(--radius-xs);
  letter-spacing: 0.04em;
}

.live-status-dot {
  width: 6px;
  height: 6px;
  background: #00e676;
}

.refresh-btn {
  font-size: 0.8rem;
  padding: 0.4rem 0.75rem;
}

.spin-anim {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding-top: 0.65rem;
  padding-bottom: 0.65rem;
  flex-wrap: wrap;
}

.week-selector {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.control-label {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 0.82rem;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.week-btn-group {
  display: flex;
  align-items: center;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
}

.week-btn {
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  transition: all 0.1s ease;
}

.week-btn:last-child {
  border-right: none;
}

.week-btn:hover {
  background: #171c2b;
  color: #ffffff;
}

.week-btn.active {
  background: #00b0ff;
  color: #07080c;
  font-weight: 800;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  overflow-x: auto;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 0.4rem 0.85rem;
  border-radius: var(--radius-xs);
  cursor: pointer;
  transition: all 0.12s ease;
  white-space: nowrap;
}

.tab-index {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
}

.nav-tab:hover {
  background: var(--bg-card);
  color: #ffffff;
}

.nav-tab.active {
  background: var(--bg-card);
  border-color: var(--border-card);
  border-bottom-color: #00b0ff;
  color: #ffffff;
}

.nav-tab.active .tab-index {
  color: #00b0ff;
}

@media (max-width: 900px) {
  .header-nav-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
