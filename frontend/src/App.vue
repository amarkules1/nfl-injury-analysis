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
import { RotateCcw } from 'lucide-vue-next'

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
    <AppHeader />

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-wrap">
      <div class="sharp-panel loading-box">
        <div class="loader-line"></div>
        <h3 class="loading-head font-display">NFL INJURY INTELLIGENCE</h3>
        <p class="loading-sub mono-val">{{ loadingMessage }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-wrap app-container">
      <div class="sharp-panel error-box">
        <h2 class="font-display text-rose">DATA LOAD FAILURE</h2>
        <p class="mono-val text-muted text-sm">{{ error }}</p>
        <button class="btn-action" @click="loadData(true)">
          <RotateCcw :size="14" />
          <span>RETRY INGESTION</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <main v-else class="app-container">
      <!-- Universal KPI Strip -->
      <MetricsOverview />

      <!-- View Switcher -->
      <div class="view-content">
        <!-- 1. Power Rankings -->
        <div v-if="selectedView === 'overview'" class="view-group">
          <HealthLeaderboard />
          <InjuryAnalytics />
        </div>

        <!-- 2. Matchup Center -->
        <div v-else-if="selectedView === 'matchups'" class="view-group">
          <MatchupCenter />
        </div>

        <!-- 3. Team Deep Dive -->
        <div v-else-if="selectedView === 'teams'" class="view-group">
          <TeamDeepDive />
        </div>

        <!-- 4. Player Database -->
        <div v-else-if="selectedView === 'players'" class="view-group">
          <PlayerExplorer />
        </div>

        <!-- 5. Surface & Trends -->
        <div v-else-if="selectedView === 'analytics'" class="view-group">
          <InjuryAnalytics />
        </div>
      </div>

      <!-- Pro Analytics Footer -->
      <footer class="app-footer">
        <div class="footer-left mono-val">
          <span>NFL INJURY INTELLIGENCE PIPELINE • SEASON 2026</span>
          <span class="footer-sep">|</span>
          <span>OFFICIAL INJURY REPORTS & NFLVERSE INGESTION</span>
        </div>
        <div class="footer-right mono-val">
          <span>SOURCE: <code>data/nfl_injuries_and_missed_games_2026.csv</code></span>
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

.view-content {
  display: flex;
  flex-direction: column;
}

.view-group {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.loading-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 65vh;
  padding: 2rem;
}

.loading-box {
  padding: 2rem 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
  max-width: 420px;
  background: var(--bg-card);
}

.loader-line {
  width: 100%;
  height: 3px;
  background: #171c2b;
  position: relative;
  overflow: hidden;
}

.loader-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 40%;
  height: 100%;
  background: #00e676;
  animation: lineSlide 1.2s infinite ease-in-out;
}

@keyframes lineSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}

.loading-head {
  font-size: 1.35rem;
  letter-spacing: 0.06em;
  color: #ffffff;
}

.loading-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.error-box {
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.85rem;
  max-width: 480px;
  margin: 3rem auto;
}

.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem 0 0.5rem 0;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.72rem;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.footer-sep {
  color: var(--border-accent);
}

code {
  color: var(--accent-cyan);
}
</style>
