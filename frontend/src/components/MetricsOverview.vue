<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'

const { 
  leagueMetrics, 
  selectedTeam,
  selectedView 
} = useInjuryData()

function selectTeamCard(teamAbbr) {
  if (teamAbbr) {
    selectedTeam.value = teamAbbr
    selectedView.value = 'teams'
  }
}
</script>

<template>
  <section class="metrics-grid">
    <!-- Metric 1: League Average Health Score -->
    <div class="sharp-panel kpi-box">
      <div class="kpi-top">
        <span class="kpi-label">LEAGUE AVG HEALTH</span>
        <span 
          class="badge-tag"
          :style="{ 
            color: leagueMetrics.avgGrade?.color, 
            backgroundColor: leagueMetrics.avgGrade?.bg,
            borderColor: leagueMetrics.avgGrade?.color 
          }"
        >
          GRADE {{ leagueMetrics.avgGrade?.grade }}
        </span>
      </div>
      <div class="kpi-val-row">
        <span class="kpi-huge mono-val">{{ leagueMetrics.avgScore }}</span>
        <span class="kpi-denom">/ 100</span>
      </div>
      <div class="kpi-bottom-meta">
        <span>Baseline: 100.0 healthy roster</span>
      </div>
    </div>

    <!-- Metric 2: Lost Starters -->
    <div class="sharp-panel kpi-box">
      <div class="kpi-top">
        <span class="kpi-label">STARTERS SIDELINED</span>
        <span class="badge-tag badge-tag-out">DEPTH RANK 1</span>
      </div>
      <div class="kpi-val-row">
        <span class="kpi-huge mono-val text-rose">{{ leagueMetrics.startersOut }}</span>
        <span class="kpi-unit">PLAYERS</span>
      </div>
      <div class="kpi-bottom-meta">
        <span>-4.5 pts penalty per starter lost</span>
      </div>
    </div>

    <!-- Metric 3: Total Games Missed -->
    <div class="sharp-panel kpi-box">
      <div class="kpi-top">
        <span class="kpi-label">GAMES MISSED</span>
        <span class="badge-tag badge-tag-ir">IR / INA / PUP</span>
      </div>
      <div class="kpi-val-row">
        <span class="kpi-huge mono-val text-amber">{{ leagueMetrics.totalMissed }}</span>
        <span class="kpi-unit">PLAYER-GAMES</span>
      </div>
      <div class="kpi-bottom-meta">
        <span>Total player absences recorded</span>
      </div>
    </div>

    <!-- Metric 4: Starting QBs Impacted -->
    <div class="sharp-panel kpi-box">
      <div class="kpi-top">
        <span class="kpi-label">STARTING QB CASUALTIES</span>
        <span class="badge-tag badge-tag-q">STARTERS ONLY</span>
      </div>
      <div class="kpi-val-row">
        <span class="kpi-huge mono-val" :class="leagueMetrics.qbInjuries > 0 ? 'text-rose' : 'text-emerald'">
          {{ leagueMetrics.qbInjuries }}
        </span>
        <span class="kpi-unit">STARTING QBs</span>
      </div>
      <div class="kpi-bottom-meta">
        <span>-22.0 pts deduction per lost starting QB</span>
      </div>
    </div>

    <!-- Metric 5: Healthiest Team (With Real Team Logo) -->
    <div 
      class="sharp-panel kpi-box kpi-team-box"
      @click="leagueMetrics.healthiestTeam && selectTeamCard(leagueMetrics.healthiestTeam.team)"
      title="Click to view team deep dive"
    >
      <div class="kpi-top">
        <span class="kpi-label">HEALTHIEST ROSTER</span>
        <span class="badge-tag badge-tag-starter">RANK #1</span>
      </div>
      <div class="kpi-team-row" v-if="leagueMetrics.healthiestTeam">
        <img 
          :src="leagueMetrics.healthiestTeam.info.logo" 
          :alt="leagueMetrics.healthiestTeam.info.name"
          class="team-logo-img"
        />
        <div class="team-details">
          <span class="team-name">{{ leagueMetrics.healthiestTeam.info.name }}</span>
          <div class="score-line">
            <span class="score-bold mono-val text-emerald">{{ leagueMetrics.healthiestTeam.healthScore }}</span>
            <span class="text-muted text-xs">/ 100</span>
          </div>
        </div>
      </div>
      <div class="kpi-bottom-meta" v-if="leagueMetrics.healthiestTeam">
        <span>{{ leagueMetrics.healthiestTeam.startersOut }} starters missing</span>
      </div>
    </div>

    <!-- Metric 6: Most Depleted Team (With Real Team Logo) -->
    <div 
      class="sharp-panel kpi-box kpi-team-box"
      @click="leagueMetrics.mostInjuredTeam && selectTeamCard(leagueMetrics.mostInjuredTeam.team)"
      title="Click to view team deep dive"
    >
      <div class="kpi-top">
        <span class="kpi-label">MOST DEPLETED ROSTER</span>
        <span class="badge-tag badge-tag-out">RANK #32</span>
      </div>
      <div class="kpi-team-row" v-if="leagueMetrics.mostInjuredTeam">
        <img 
          :src="leagueMetrics.mostInjuredTeam.info.logo" 
          :alt="leagueMetrics.mostInjuredTeam.info.name"
          class="team-logo-img"
        />
        <div class="team-details">
          <span class="team-name">{{ leagueMetrics.mostInjuredTeam.info.name }}</span>
          <div class="score-line">
            <span class="score-bold mono-val text-rose">{{ leagueMetrics.mostInjuredTeam.healthScore }}</span>
            <span class="text-muted text-xs">/ 100</span>
          </div>
        </div>
      </div>
      <div class="kpi-bottom-meta" v-if="leagueMetrics.mostInjuredTeam">
        <span>{{ leagueMetrics.mostInjuredTeam.startersOut }} starters sidelined</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1rem;
}

@media (max-width: 1400px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 850px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 550px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.kpi-box {
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 125px;
}

.kpi-team-box {
  cursor: pointer;
  transition: border-color 0.12s ease;
}

.kpi-team-box:hover {
  border-color: var(--accent-cyan);
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.kpi-label {
  font-family: var(--font-display);
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

.kpi-val-row {
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
}

.kpi-huge {
  font-family: var(--font-display);
  font-size: 2.3rem;
  font-weight: 900;
  line-height: 1;
  color: #ffffff;
  letter-spacing: -0.01em;
}

.kpi-denom {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--text-muted);
}

.kpi-unit {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.kpi-bottom-meta {
  font-size: 0.72rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.45rem;
  margin-top: 0.45rem;
  font-family: var(--font-mono);
}

.text-rose {
  color: #ff5252;
}

.text-amber {
  color: #ffd740;
}

.text-emerald {
  color: #00e676;
}

.kpi-team-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.team-logo-img {
  width: 38px;
  height: 38px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
  flex-shrink: 0;
}

.team-details {
  display: flex;
  flex-direction: column;
}

.team-name {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.1;
}

.score-line {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.score-bold {
  font-size: 1.15rem;
  font-weight: 800;
}
</style>
