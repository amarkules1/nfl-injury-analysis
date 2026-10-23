<script setup>
import { onMounted } from 'vue'
import { useInjuryData } from './composables/useInjuryData'
import AppHeader from './components/AppHeader.vue'
import MetricsOverview from './components/MetricsOverview.vue'
import HealthLeaderboard from './components/HealthLeaderboard.vue'
import MatchupCenter from './components/MatchupCenter.vue'
import TeamDeepDive from './components/TeamDeepDive.vue'
import PlayerExplorer from './components/PlayerExplorer.vue'
import InjuryAnalytics from './components/InjuryAnalytics.vue'
import { Activity, AlertOctagon, RotateCcw } from 'lucide-vue-next'

const { 
  isLoading, 
  loadingMessage, 
  error, 
  selectedView, 
  loadData 
} = useInjuryData()

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="app-layout">
    <!-- Top Header -->
    <AppHeader />

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-overlay animate-fade-in">
      <div class="glass-panel loading-card">
        <div class="spinner-container">
          <Activity class="pulse-icon" :size="38" />
          <div class="spinner-ring"></div>
        </div>
        <h3 class="loading-title">NFL Injury Intelligence</h3>
        <p class="loading-sub">{{ loadingMessage }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container app-container">
      <div class="glass-panel error-card">
        <AlertOctagon :size="48" class="text-rose" />
        <h2>Failed to load NFL injury data</h2>
        <p class="error-text">{{ error }}</p>
        <button class="btn-primary" @click="loadData(true)">
          <RotateCcw :size="16" />
          <span>Try Again</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <main v-else class="app-container">
      <!-- Universal KPI Metrics Row -->
      <MetricsOverview />

      <!-- View Switcher -->
      <transition name="view-fade" mode="out-in">
        <!-- 1. Power Rankings / Overview -->
        <div v-if="selectedView === 'overview'" key="overview" class="view-wrapper">
          <HealthLeaderboard />
          <InjuryAnalytics />
        </div>

        <!-- 2. Matchup Center -->
        <div v-else-if="selectedView === 'matchups'" key="matchups" class="view-wrapper">
          <MatchupCenter />
        </div>

        <!-- 3. Team Deep Dive -->
        <div v-else-if="selectedView === 'teams'" key="teams" class="view-wrapper">
          <TeamDeepDive />
        </div>

        <!-- 4. Player Database -->
        <div v-else-if="selectedView === 'players'" key="players" class="view-wrapper">
          <PlayerExplorer />
        </div>

        <!-- 5. Analytics & Turf Insights -->
        <div v-else-if="selectedView === 'analytics'" key="analytics" class="view-wrapper">
          <InjuryAnalytics />
        </div>
      </transition>

      <!-- App Footer -->
      <footer class="app-footer">
        <div class="footer-left">
          <span>NFL Injury Analysis & Team Health Pipeline • Season 2026</span>
          <span class="footer-divider">•</span>
          <span>Data harmonized via official NFL injury reports & nflverse ecosystem</span>
        </div>
        <div class="footer-right">
          <span>Outputs: <code>data/nfl_injuries_and_missed_games_2026.csv</code></span>
        </div>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.view-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 2rem;
}

.loading-card {
  padding: 2.5rem 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  max-width: 440px;
}

.spinner-container {
  position: relative;
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-icon {
  color: var(--accent-cyan);
  animation: pulseGlow 1.5s infinite ease-in-out;
}

.spinner-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid rgba(56, 189, 248, 0.15);
  border-top-color: var(--accent-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #ffffff;
}

.loading-sub {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.error-card {
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  max-width: 500px;
  margin: 3rem auto;
}

.error-text {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem 0 0.5rem 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.78rem;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.footer-divider {
  opacity: 0.4;
}

code {
  font-family: var(--font-mono);
  background: rgba(255, 255, 255, 0.06);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  color: var(--accent-cyan);
}

/* View transitions */
.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.view-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.view-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
