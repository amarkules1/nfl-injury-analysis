<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam, getHealthGrade } from '../data/nflTeams'
import { 
  ShieldAlert, 
  TrendingUp, 
  UserCheck, 
  UserX, 
  Search, 
  Activity, 
  ShieldCheck,
  ChevronRight
} from 'lucide-vue-next'

const { 
  selectedTeam, 
  selectedWeek, 
  availableTeams, 
  teamWeeklyTrend, 
  playerInjuries,
  teamPowerRankings 
} = useInjuryData()

const rosterSearch = ref('')

const teamInfo = computed(() => getTeam(selectedTeam.value))

const currentTeamRankData = computed(() => {
  return teamPowerRankings.value.find(t => t.team === selectedTeam.value) || {
    rank: 16,
    healthScore: 85,
    grade: getHealthGrade(85),
    startersOut: 0,
    gamesMissed: 0,
    qbStatus: 'Healthy'
  }
})

// Current week player roster records for selected team
const teamCurrentRoster = computed(() => {
  let list = playerInjuries.value.filter(p => {
    const matchTeam = String(p.team).trim().toUpperCase() === selectedTeam.value.toUpperCase()
    const matchWeek = selectedWeek.value === 'all' ? true : Number(p.week) === Number(selectedWeek.value)
    return matchTeam && matchWeek
  })

  if (rosterSearch.value.trim()) {
    const q = rosterSearch.value.trim().toLowerCase()
    list = list.filter(p => 
      String(p.player_name || '').toLowerCase().includes(q) ||
      String(p.position || '').toLowerCase().includes(q) ||
      String(p.primary_injury || '').toLowerCase().includes(q) ||
      String(p.missed_reason_category || '').toLowerCase().includes(q)
    )
  }

  // Sort: Starters first, then missed games, then name
  list.sort((a, b) => {
    if (a.is_starter !== b.is_starter) return b.is_starter ? 1 : -1
    if (a.game_missed !== b.game_missed) return b.game_missed ? 1 : -1
    return String(a.player_name).localeCompare(String(b.player_name))
  })

  return list
})

// Unit metrics for selected team in current week
const unitsData = computed(() => {
  const trend = teamWeeklyTrend.value
  const cur = trend.find(t => t.week === Number(selectedWeek.value)) || trend[trend.length - 1]
  if (!cur) {
    return [
      { name: 'Quarterback', key: 'qb', score: 100 },
      { name: 'Offensive Line', key: 'ol', score: 100 },
      { name: 'Skill (WR/RB/TE)', key: 'skill', score: 100 },
      { name: 'Front 7 (DL/LB)', key: 'front', score: 100 },
      { name: 'Secondary (DB)', key: 'secondary', score: 100 }
    ]
  }

  return [
    { name: 'Quarterback', key: 'qb', score: cur.units.qb ?? 100 },
    { name: 'Offensive Line', key: 'ol', score: cur.units.ol ?? 100 },
    { name: 'Skill (WR/RB/TE)', key: 'skill', score: cur.units.skill ?? 100 },
    { name: 'Front 7 (DL/LB)', key: 'front', score: cur.units.front ?? 100 },
    { name: 'Secondary (DB)', key: 'secondary', score: cur.units.secondary ?? 100 }
  ]
})
</script>

<template>
  <section class="team-deep-dive-section">
    <!-- Team Switcher Carousel Bar -->
    <div class="team-switcher-bar glass-panel">
      <div class="switcher-label">
        <span>Team:</span>
      </div>
      <div class="teams-scroll-row">
        <button 
          v-for="t in availableTeams" 
          :key="t"
          class="team-switch-btn"
          :class="{ active: selectedTeam === t }"
          @click="selectedTeam = t"
          :style="{
            borderColor: selectedTeam === t ? getTeam(t).primaryColor : 'transparent',
            boxShadow: selectedTeam === t ? `0 0 12px ${getTeam(t).primaryColor}66` : 'none'
          }"
        >
          <span 
            class="badge-dot" 
            :style="{ backgroundColor: getTeam(t).primaryColor }"
          ></span>
          <span>{{ t }}</span>
        </button>
      </div>
    </div>

    <!-- Main Team Hero Banner -->
    <div 
      class="glass-panel team-hero-card"
      :style="{
        background: `linear-gradient(135deg, ${teamInfo.primaryColor}22 0%, rgba(15, 23, 42, 0.9) 60%)`
      }"
    >
      <div class="hero-left">
        <div 
          class="team-large-badge"
          :style="{ 
            backgroundColor: teamInfo.primaryColor,
            color: teamInfo.textColor,
            boxShadow: `0 8px 24px ${teamInfo.primaryColor}55`
          }"
        >
          {{ teamInfo.abbr }}
        </div>
        <div class="hero-title-group">
          <div class="division-tag">{{ teamInfo.division }} • {{ teamInfo.conference }}</div>
          <h2 class="team-title-text">{{ teamInfo.name }}</h2>
          <div class="hero-substats">
            <span class="substat">
              NFL Rank: <strong class="text-white">#{{ currentTeamRankData.rank }}</strong> of 32
            </span>
            <span class="substat-divider">•</span>
            <span class="substat">
              Starters Sidelined: <strong class="text-rose">{{ currentTeamRankData.startersOut }}</strong>
            </span>
            <span class="substat-divider">•</span>
            <span class="substat">
              QB Status: 
              <strong :class="currentTeamRankData.qbStatus === 'Healthy' ? 'text-emerald' : 'text-rose'">
                {{ currentTeamRankData.qbStatus }}
              </strong>
            </span>
          </div>
        </div>
      </div>

      <!-- Health Score Spotlight -->
      <div class="hero-right">
        <div class="team-score-card">
          <div class="score-label">Health Index</div>
          <div class="score-val-wrap">
            <span 
              class="score-massive mono-val"
              :style="{ color: currentTeamRankData.grade?.color }"
            >
              {{ currentTeamRankData.healthScore }}
            </span>
            <span class="denom">/ 100</span>
          </div>
          <div 
            class="grade-large-pill"
            :style="{ 
              color: currentTeamRankData.grade?.color, 
              backgroundColor: currentTeamRankData.grade?.bg,
              borderColor: currentTeamRankData.grade?.color 
            }"
          >
            Grade {{ currentTeamRankData.grade?.grade }} • {{ currentTeamRankData.grade?.label }}
          </div>
        </div>
      </div>
    </div>

    <!-- Middle Row: Unit Breakdown & Health Trajectory -->
    <div class="team-metrics-grid">
      <!-- Unit Breakdown -->
      <div class="glass-panel unit-breakdown-card">
        <div class="card-inner-header">
          <h3 class="card-title">Positional Unit Health</h3>
          <span class="card-sub">Week {{ selectedWeek }} evaluations</span>
        </div>

        <div class="unit-meters-list">
          <div 
            v-for="u in unitsData" 
            :key="u.key"
            class="unit-meter-item"
          >
            <div class="unit-meter-top">
              <span class="unit-name">{{ u.name }}</span>
              <span class="unit-score mono-val" :class="u.score < 80 ? 'text-rose' : (u.score < 95 ? 'text-amber' : 'text-emerald')">
                {{ u.score }}%
              </span>
            </div>
            <div class="health-meter-track">
              <div 
                class="health-meter-fill"
                :style="{ 
                  width: `${u.score}%`,
                  background: u.score < 80 
                    ? 'linear-gradient(90deg, #f43f5e, #e11d48)' 
                    : (u.score < 95 ? 'linear-gradient(90deg, #f59e0b, #d97706)' : 'linear-gradient(90deg, #10b981, #059669)')
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Weekly Health Trend Curve -->
      <div class="glass-panel trend-card">
        <div class="card-inner-header">
          <div class="title-with-icon">
            <TrendingUp :size="18" class="text-cyan" />
            <h3 class="card-title">Season Health Trajectory</h3>
          </div>
          <span class="card-sub">Week-by-week score progression</span>
        </div>

        <div class="trend-bars-wrapper">
          <div 
            v-for="point in teamWeeklyTrend" 
            :key="point.week"
            class="trend-col"
          >
            <div class="trend-score-top mono-val">{{ point.score }}</div>
            <div class="trend-bar-track">
              <div 
                class="trend-bar-fill"
                :style="{ 
                  height: `${point.score}%`,
                  backgroundColor: point.score < 75 ? '#f43f5e' : (point.score < 90 ? '#f59e0b' : '#10b981')
                }"
              ></div>
            </div>
            <div class="trend-week-label mono-val">W{{ point.week }}</div>
            <div class="trend-opp-sub">{{ point.opponent }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Injury Roster Table -->
    <div class="glass-panel team-roster-card">
      <div class="roster-header">
        <div class="title-with-count">
          <h3 class="card-title">{{ teamInfo.name }} Injury & Missed Games Log</h3>
          <span class="roster-badge">{{ teamCurrentRoster.length }} Players Listed</span>
        </div>

        <!-- Search input -->
        <div class="search-box">
          <Search :size="15" class="search-icon" />
          <input 
            type="text" 
            v-model="rosterSearch" 
            placeholder="Search roster..." 
            class="input-glass roster-input"
          />
        </div>
      </div>

      <div class="roster-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Unit Role</th>
              <th>Roster Status</th>
              <th>Diagnosed Injury</th>
              <th>Missed Game?</th>
              <th>Practice Status</th>
              <th>Impact Weight</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="teamCurrentRoster.length === 0">
              <td colspan="8" class="empty-row">No injury reports logged for this selection.</td>
            </tr>
            <tr 
              v-for="p in teamCurrentRoster" 
              :key="p.gsis_id || p.player_name"
              class="table-row"
            >
              <!-- Player -->
              <td class="player-cell">
                <span class="player-name">{{ p.player_name }}</span>
                <span v-if="p.jersey_number" class="player-jersey mono-val">#{{ p.jersey_number }}</span>
              </td>

              <!-- Position -->
              <td>
                <span class="pos-badge mono-val">{{ p.position }}</span>
              </td>

              <!-- Role / Starter -->
              <td>
                <span 
                  v-if="p.is_starter" 
                  class="badge badge-starter"
                >
                  Starter (Rank 1)
                </span>
                <span v-else class="text-muted text-sm">Depth</span>
              </td>

              <!-- Roster Status -->
              <td>
                <span 
                  class="badge"
                  :class="{
                    'badge-ir': p.missed_reason_category === 'INJURY_IR',
                    'badge-pup': p.missed_reason_category === 'INJURY_PUP',
                    'badge-out': p.missed_reason_category === 'INJURY_RULED_OUT' || p.missed_reason_category === 'INJURY_INACTIVE',
                    'badge-scratch': p.missed_reason_category === 'HEALTHY_SCRATCH',
                    'badge-questionable': p.missed_reason_category === 'INJURED_PLAYED_QUESTIONABLE'
                  }"
                >
                  {{ p.roster_status_desc || p.roster_status || 'Active' }}
                </span>
              </td>

              <!-- Diagnosed Injury -->
              <td>
                <span class="injury-name" :class="{ 'text-rose': p.game_missed }">
                  {{ p.primary_injury || 'None reported' }}
                </span>
              </td>

              <!-- Missed Game -->
              <td>
                <span v-if="p.game_missed" class="missed-yes">
                  <UserX :size="14" />
                  <span>Missed</span>
                </span>
                <span v-else class="missed-no">
                  <UserCheck :size="14" />
                  <span>Dressed</span>
                </span>
              </td>

              <!-- Practice Status -->
              <td>
                <span class="text-sm text-secondary">{{ p.practice_status || 'Full' }}</span>
              </td>

              <!-- Impact Weight -->
              <td class="mono-val text-sm">
                <span :class="p.health_impact_weight >= 1 ? 'text-rose' : 'text-amber'">
                  -{{ p.health_impact_weight || 0 }} pts
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.team-deep-dive-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.team-switcher-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  overflow-x: auto;
}

.switcher-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.teams-scroll-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  overflow-x: auto;
  padding-bottom: 2px;
}

.team-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 0.35rem 0.65rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.team-switch-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.team-switch-btn.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: #ffffff;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.team-hero-card {
  padding: 1.75rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  flex-wrap: wrap;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.team-large-badge {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  font-weight: 900;
  flex-shrink: 0;
}

.hero-title-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.division-tag {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.team-title-text {
  font-size: 2rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.1;
}

.hero-substats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
  flex-wrap: wrap;
}

.substat-divider {
  color: var(--text-muted);
}

.hero-right {
  display: flex;
  align-items: center;
}

.team-score-card {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.score-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.score-val-wrap {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.score-massive {
  font-size: 2.75rem;
  font-weight: 900;
  line-height: 1;
}

.denom {
  font-size: 1rem;
  color: var(--text-muted);
}

.grade-large-pill {
  font-size: 0.78rem;
  font-weight: 800;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-pill);
  border: 1px solid;
  letter-spacing: 0.03em;
}

.team-metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .team-metrics-grid {
    grid-template-columns: 1fr;
  }
}

.unit-breakdown-card, .trend-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card-inner-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
}

.card-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.unit-meters-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.unit-meter-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.3rem;
  font-size: 0.82rem;
}

.unit-name {
  font-weight: 600;
  color: var(--text-primary);
}

.unit-score {
  font-weight: 700;
}

/* Trend bars */
.trend-bars-wrapper {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.75rem;
  height: 170px;
  align-items: flex-end;
  padding-top: 1rem;
}

.trend-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  gap: 0.35rem;
}

.trend-score-top {
  font-size: 0.75rem;
  font-weight: 700;
  color: #ffffff;
}

.trend-bar-track {
  width: 24px;
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.trend-bar-fill {
  width: 100%;
  border-radius: 4px;
  transition: height 0.6s ease;
}

.trend-week-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.trend-opp-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 600;
}

/* Roster Table */
.team-roster-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.roster-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.title-with-count {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.roster-badge {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-subtle);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  color: var(--accent-cyan);
  font-weight: 600;
}

.roster-input {
  width: 220px;
}

.roster-table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.data-table th {
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.data-table td {
  padding: 0.85rem 1rem;
  font-size: 0.85rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.player-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.player-name {
  font-weight: 700;
  color: #ffffff;
}

.player-jersey {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.pos-badge {
  background: rgba(255, 255, 255, 0.07);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
}

.injury-name {
  font-weight: 600;
  color: var(--text-secondary);
}

.missed-yes {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: #f87171;
  font-weight: 700;
  font-size: 0.8rem;
}

.missed-no {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: #34d399;
  font-weight: 600;
  font-size: 0.8rem;
}

.empty-row {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
}
</style>
