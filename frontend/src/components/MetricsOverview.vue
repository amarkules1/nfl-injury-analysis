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
    <!-- Metric 1: League Average Health -->
    <div class="sharp-panel kpi-box">
      <div class="kpi-top">
        <span class="kpi-label">LEAGUE AVERAGE HEALTH</span>
      </div>
      <div class="kpi-val-row">
        <span class="kpi-huge mono-val">{{ leagueMetrics.avgScore }}</span>
        <span class="kpi-denom mono-val">/ 100</span>
      </div>
      <div class="kpi-bottom-meta mono-val">
        <span>Active 32-team baseline</span>
      </div>
    </div>

    <!-- Metric 2: Healthiest Roster -->
    <div 
      class="sharp-panel kpi-box kpi-clickable"
      @click="leagueMetrics.healthiestTeam && selectTeamCard(leagueMetrics.healthiestTeam.team)"
      title="View team deep dive"
    >
      <div class="kpi-top">
        <span class="kpi-label">HEALTHIEST ROSTER</span>
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
            <span class="text-muted text-xs mono-val">/ 100</span>
          </div>
        </div>
      </div>
      <div class="kpi-bottom-meta mono-val" v-if="leagueMetrics.healthiestTeam">
        <span>{{ leagueMetrics.healthiestTeam.startersOut }} starters missing</span>
      </div>
    </div>

    <!-- Metric 3: Most Depleted Roster -->
    <div 
      class="sharp-panel kpi-box kpi-clickable"
      @click="leagueMetrics.mostInjuredTeam && selectTeamCard(leagueMetrics.mostInjuredTeam.team)"
      title="View team deep dive"
    >
      <div class="kpi-top">
        <span class="kpi-label">MOST DEPLETED ROSTER</span>
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
            <span class="text-muted text-xs mono-val">/ 100</span>
          </div>
        </div>
      </div>
      <div class="kpi-bottom-meta mono-val" v-if="leagueMetrics.mostInjuredTeam">
        <span>{{ leagueMetrics.mostInjuredTeam.startersOut }} starters sidelined</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

@media (max-width: 900px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.kpi-box {
  padding: 1.15rem 1.35rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 120px;
}

.kpi-clickable {
  cursor: pointer;
  transition: border-color 0.12s ease;
}

.kpi-clickable:hover {
  border-color: var(--accent-cyan);
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 0.35rem;
}

.kpi-label {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.kpi-val-row {
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
}

.kpi-huge {
  font-size: 2.4rem;
  font-weight: 700;
  line-height: 1;
  color: #ffffff;
}

.kpi-denom {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.kpi-bottom-meta {
  font-size: 0.72rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.45rem;
  margin-top: 0.45rem;
}

.text-rose {
  color: var(--accent-rose);
}

.text-emerald {
  color: var(--accent-emerald);
}

.kpi-team-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.team-logo-img {
  width: 40px;
  height: 40px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.6));
  flex-shrink: 0;
}

.team-details {
  display: flex;
  flex-direction: column;
}

.team-name {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.15;
}

.score-line {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.score-bold {
  font-size: 1.15rem;
  font-weight: 700;
}
</style>
