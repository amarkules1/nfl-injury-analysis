<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { 
  HeartPulse, 
  UserMinus, 
  Flame, 
  Crown, 
  Award, 
  AlertTriangle 
} from 'lucide-vue-next'

const { 
  leagueMetrics, 
  selectedWeek, 
  selectedTeam 
} = useInjuryData()

function selectTeamCard(teamAbbr) {
  if (teamAbbr) {
    selectedTeam.value = teamAbbr
  }
}
</script>

<template>
  <section class="metrics-grid">
    <!-- Card 1: League Health Average -->
    <div class="glass-panel metric-card">
      <div class="metric-header">
        <span class="metric-title">League Avg Health</span>
        <div class="metric-icon-wrap emerald">
          <HeartPulse :size="20" />
        </div>
      </div>
      <div class="metric-body">
        <div class="metric-value-row">
          <span class="metric-huge mono-val">{{ leagueMetrics.avgScore }}</span>
          <span class="metric-denominator">/ 100</span>
        </div>
        <div class="metric-footer">
          <span 
            class="grade-pill"
            :style="{ 
              color: leagueMetrics.avgGrade?.color, 
              backgroundColor: leagueMetrics.avgGrade?.bg,
              borderColor: leagueMetrics.avgGrade?.color 
            }"
          >
            Grade {{ leagueMetrics.avgGrade?.grade }} • {{ leagueMetrics.avgGrade?.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- Card 2: Starters Sidelined -->
    <div class="glass-panel metric-card">
      <div class="metric-header">
        <span class="metric-title">Starters Lost</span>
        <div class="metric-icon-wrap rose">
          <UserMinus :size="20" />
        </div>
      </div>
      <div class="metric-body">
        <div class="metric-value-row">
          <span class="metric-huge mono-val text-rose">{{ leagueMetrics.startersOut }}</span>
          <span class="metric-subtext">depth rank 1</span>
        </div>
        <div class="metric-footer">
          <span class="metric-footer-note">
            High impact starters on IR, PUP or Inactive
          </span>
        </div>
      </div>
    </div>

    <!-- Card 3: Total Games Missed -->
    <div class="glass-panel metric-card">
      <div class="metric-header">
        <span class="metric-title">Total Games Missed</span>
        <div class="metric-icon-wrap amber">
          <AlertTriangle :size="20" />
        </div>
      </div>
      <div class="metric-body">
        <div class="metric-value-row">
          <span class="metric-huge mono-val text-amber">{{ leagueMetrics.totalMissed }}</span>
          <span class="metric-subtext">player-games</span>
        </div>
        <div class="metric-footer">
          <span class="metric-footer-note">
            Across active, IR, PUP & inactive rosters
          </span>
        </div>
      </div>
    </div>

    <!-- Card 4: QB Health Situations -->
    <div class="glass-panel metric-card">
      <div class="metric-header">
        <span class="metric-title">Quarterback Impact</span>
        <div class="metric-icon-wrap violet">
          <Crown :size="20" />
        </div>
      </div>
      <div class="metric-body">
        <div class="metric-value-row">
          <span class="metric-huge mono-val text-violet">{{ leagueMetrics.qbInjuries }}</span>
          <span class="metric-subtext">QBs affected</span>
        </div>
        <div class="metric-footer">
          <span class="metric-footer-note">
            -22.0 team health penalty per lost starting QB
          </span>
        </div>
      </div>
    </div>

    <!-- Card 5: Healthiest Team -->
    <div 
      class="glass-panel metric-card clickable-card"
      @click="leagueMetrics.healthiestTeam && selectTeamCard(leagueMetrics.healthiestTeam.team)"
      title="Click to view team deep dive"
    >
      <div class="metric-header">
        <span class="metric-title">Healthiest Team</span>
        <div class="metric-icon-wrap cyan">
          <Award :size="20" />
        </div>
      </div>
      <div class="metric-body" v-if="leagueMetrics.healthiestTeam">
        <div class="team-spotlight">
          <div 
            class="team-pill-avatar"
            :style="{ 
              backgroundColor: leagueMetrics.healthiestTeam.info.primaryColor,
              color: leagueMetrics.healthiestTeam.info.textColor 
            }"
          >
            {{ leagueMetrics.healthiestTeam.team }}
          </div>
          <div>
            <div class="team-spotlight-name">{{ leagueMetrics.healthiestTeam.info.name }}</div>
            <div class="team-spotlight-score mono-val text-emerald">
              {{ leagueMetrics.healthiestTeam.healthScore }} Index
            </div>
          </div>
        </div>
        <div class="metric-footer">
          <span class="badge badge-starter">Only {{ leagueMetrics.healthiestTeam.startersOut }} Starters Out</span>
        </div>
      </div>
    </div>

    <!-- Card 6: Most Ravaged Team -->
    <div 
      class="glass-panel metric-card clickable-card"
      @click="leagueMetrics.mostInjuredTeam && selectTeamCard(leagueMetrics.mostInjuredTeam.team)"
      title="Click to view team deep dive"
    >
      <div class="metric-header">
        <span class="metric-title">Most Ravaged Team</span>
        <div class="metric-icon-wrap rose">
          <Flame :size="20" />
        </div>
      </div>
      <div class="metric-body" v-if="leagueMetrics.mostInjuredTeam">
        <div class="team-spotlight">
          <div 
            class="team-pill-avatar"
            :style="{ 
              backgroundColor: leagueMetrics.mostInjuredTeam.info.primaryColor,
              color: leagueMetrics.mostInjuredTeam.info.textColor 
            }"
          >
            {{ leagueMetrics.mostInjuredTeam.team }}
          </div>
          <div>
            <div class="team-spotlight-name">{{ leagueMetrics.mostInjuredTeam.info.name }}</div>
            <div class="team-spotlight-score mono-val text-rose">
              {{ leagueMetrics.mostInjuredTeam.healthScore }} Index
            </div>
          </div>
        </div>
        <div class="metric-footer">
          <span class="badge badge-ir">{{ leagueMetrics.mostInjuredTeam.startersOut }} Starters Missing</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1.25rem;
}

@media (max-width: 1400px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 800px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.85rem;
  }
}

@media (max-width: 520px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

.metric-card {
  padding: 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 148px;
}

.clickable-card {
  cursor: pointer;
  transition: transform var(--transition-fast), border-color var(--transition-fast);
}

.clickable-card:hover {
  transform: translateY(-2px);
  border-color: rgba(56, 189, 248, 0.4);
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.metric-title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-icon-wrap.emerald {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-emerald);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.metric-icon-wrap.rose {
  background: rgba(244, 63, 94, 0.15);
  color: var(--accent-rose);
  border: 1px solid rgba(244, 63, 94, 0.3);
}

.metric-icon-wrap.amber {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent-amber);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.metric-icon-wrap.violet {
  background: rgba(139, 92, 246, 0.15);
  color: var(--accent-violet);
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.metric-icon-wrap.cyan {
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-cyan);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.metric-huge {
  font-size: 2.25rem;
  font-weight: 800;
  line-height: 1;
  color: #ffffff;
  font-family: var(--font-display);
}

.metric-denominator {
  font-size: 0.9rem;
  color: var(--text-muted);
  font-weight: 600;
}

.metric-subtext {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.text-rose {
  color: #fb7185;
}

.text-amber {
  color: #fbbf24;
}

.text-violet {
  color: #c084fc;
}

.text-emerald {
  color: #34d399;
}

.metric-footer {
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
}

.metric-footer-note {
  font-size: 0.74rem;
  color: var(--text-muted);
  line-height: 1.3;
}

.grade-pill {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-pill);
  border: 1px solid;
  letter-spacing: 0.03em;
}

.team-spotlight {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.team-pill-avatar {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.team-spotlight-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: #ffffff;
}

.team-spotlight-score {
  font-size: 0.8rem;
  font-weight: 700;
}
</style>
