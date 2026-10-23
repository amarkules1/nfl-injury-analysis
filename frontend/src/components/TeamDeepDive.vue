<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam, getHealthGrade } from '../data/nflTeams'
import { Search } from 'lucide-vue-next'

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

  list.sort((a, b) => {
    if (a.is_starter !== b.is_starter) return b.is_starter ? 1 : -1
    if (a.game_missed !== b.game_missed) return b.game_missed ? 1 : -1
    return String(a.player_name).localeCompare(String(b.player_name))
  })

  return list
})

const unitsData = computed(() => {
  const trend = teamWeeklyTrend.value
  const cur = trend.find(t => t.week === Number(selectedWeek.value)) || trend[trend.length - 1]
  if (!cur) {
    return [
      { name: 'QUARTERBACK', key: 'qb', score: 100 },
      { name: 'OFFENSIVE LINE', key: 'ol', score: 100 },
      { name: 'SKILL POSITIONS', key: 'skill', score: 100 },
      { name: 'FRONT SEVEN', key: 'front', score: 100 },
      { name: 'SECONDARY', key: 'secondary', score: 100 }
    ]
  }

  return [
    { name: 'QUARTERBACK', key: 'qb', score: cur.units.qb ?? 100 },
    { name: 'OFFENSIVE LINE', key: 'ol', score: cur.units.ol ?? 100 },
    { name: 'SKILL POSITIONS', key: 'skill', score: cur.units.skill ?? 100 },
    { name: 'FRONT SEVEN', key: 'front', score: cur.units.front ?? 100 },
    { name: 'SECONDARY', key: 'secondary', score: cur.units.secondary ?? 100 }
  ]
})
</script>

<template>
  <section class="deep-dive-section">
    <!-- Team Quick Switch Bar -->
    <div class="sharp-panel switch-bar">
      <span class="switch-label mono-val">SELECT TEAM:</span>
      <div class="team-btns-scroll">
        <button 
          v-for="t in availableTeams" 
          :key="t"
          class="team-btn"
          :class="{ active: selectedTeam === t }"
          @click="selectedTeam = t"
        >
          <img :src="getTeam(t).logo" :alt="t" class="mini-logo" />
          <span>{{ t }}</span>
        </button>
      </div>
    </div>

    <!-- Main Team Hero Banner -->
    <div class="sharp-panel team-hero">
      <div class="hero-left">
        <img 
          :src="teamInfo.logo" 
          :alt="teamInfo.name"
          class="hero-team-logo"
        />
        <div class="hero-info">
          <span class="hero-division mono-val">{{ teamInfo.division }} • {{ teamInfo.conference }}</span>
          <h2 class="hero-title">{{ teamInfo.name }}</h2>
          <div class="hero-stats-line mono-val">
            <span>NFL RANK: <strong class="text-white">#{{ currentTeamRankData.rank }}</strong> / 32</span>
            <span class="meta-dot">•</span>
            <span>STARTERS SIDELINED: <strong class="text-rose">{{ currentTeamRankData.startersOut }}</strong></span>
            <span class="meta-dot">•</span>
            <span>
              STARTING QB: 
              <strong :class="currentTeamRankData.qbStatus === 'Healthy' ? 'text-emerald' : 'text-rose'">
                {{ currentTeamRankData.qbStatus.toUpperCase() }}
              </strong>
            </span>
          </div>
        </div>
      </div>

      <div class="hero-right">
        <div class="rating-box">
          <span class="rating-label mono-val">HEALTH RATING</span>
          <div class="rating-num-row">
            <span 
              class="rating-massive mono-val"
              :style="{ color: currentTeamRankData.grade?.color }"
            >
              {{ currentTeamRankData.healthScore }}
            </span>
            <span class="denom mono-val">/ 100</span>
          </div>
          <span 
            class="badge-tag"
            :style="{ 
              color: currentTeamRankData.grade?.color, 
              backgroundColor: currentTeamRankData.grade?.bg,
              borderColor: currentTeamRankData.grade?.color 
            }"
          >
            GRADE {{ currentTeamRankData.grade?.grade }} • {{ currentTeamRankData.grade?.label.toUpperCase() }}
          </span>
        </div>
      </div>
    </div>

    <!-- Units & Trajectory Grid -->
    <div class="metrics-two-col">
      <!-- Positional Unit Health -->
      <div class="sharp-panel unit-panel">
        <div class="panel-header">
          <h3 class="panel-title">POSITIONAL UNIT HEALTH</h3>
          <span class="panel-sub mono-val">WEEK {{ selectedWeek }} EVALUATION</span>
        </div>

        <div class="unit-bars-list">
          <div 
            v-for="u in unitsData" 
            :key="u.key"
            class="unit-item"
          >
            <div class="unit-top">
              <span class="unit-label">{{ u.name }}</span>
              <span class="unit-pct mono-val" :class="u.score < 80 ? 'text-rose' : (u.score < 95 ? 'text-amber' : 'text-emerald')">
                {{ u.score }}%
              </span>
            </div>
            <div class="sharp-meter-track">
              <div 
                class="sharp-meter-fill"
                :style="{ 
                  width: `${u.score}%`,
                  backgroundColor: u.score < 80 ? '#ff1744' : (u.score < 95 ? '#ffc107' : '#00e676')
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Season Trajectory -->
      <div class="sharp-panel trajectory-panel">
        <div class="panel-header">
          <h3 class="panel-title">SEASON HEALTH TRAJECTORY</h3>
          <span class="panel-sub mono-val">WEEKS 1–7 PROGRESSION</span>
        </div>

        <div class="trajectory-cols">
          <div 
            v-for="point in teamWeeklyTrend" 
            :key="point.week"
            class="traj-col"
          >
            <span class="traj-val mono-val">{{ point.score }}</span>
            <div class="traj-track">
              <div 
                class="traj-fill"
                :style="{ 
                  height: `${point.score}%`,
                  backgroundColor: point.score < 75 ? '#ff1744' : (point.score < 90 ? '#ffc107' : '#00e676')
                }"
              ></div>
            </div>
            <span class="traj-wk mono-val">W{{ point.week }}</span>
            <span class="traj-opp mono-val">{{ point.opponent }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Team Active Injury Table -->
    <div class="sharp-panel roster-panel">
      <div class="roster-top">
        <div class="roster-title-block">
          <h3 class="panel-title">{{ teamInfo.name }} INJURY REPORT</h3>
          <span class="badge-tag badge-tag-starter mono-val">{{ teamCurrentRoster.length }} PLAYERS LOGGED</span>
        </div>

        <div class="search-box">
          <Search :size="14" class="search-icon" />
          <input 
            type="text" 
            v-model="rosterSearch" 
            placeholder="FILTER ROSTER..." 
            class="input-sharp roster-input"
          />
        </div>
      </div>

      <div class="table-wrap">
        <table class="sharp-table">
          <thead>
            <tr>
              <th>PLAYER</th>
              <th>POS</th>
              <th>DEPTH STATUS</th>
              <th>DESIGNATED CATEGORY</th>
              <th>DIAGNOSED INJURY</th>
              <th>GAME STATUS</th>
              <th>PRACTICE PARTICIPATION</th>
              <th>PENALTY IMPACT</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="teamCurrentRoster.length === 0">
              <td colspan="8" class="empty-cell mono-val">No injury reports logged for this selection.</td>
            </tr>
            <tr 
              v-for="p in teamCurrentRoster" 
              :key="p.gsis_id || p.player_name"
              class="table-row"
            >
              <td class="player-name-cell">
                <span class="name-text">{{ p.player_name }}</span>
                <span v-if="p.jersey_number" class="jersey-num mono-val">#{{ p.jersey_number }}</span>
              </td>
              <td><span class="pos-tag mono-val">{{ p.position }}</span></td>
              <td>
                <span v-if="p.is_starter" class="badge-tag badge-tag-starter">
                  STARTER (RANK 1)
                </span>
                <span v-else class="text-muted text-xs mono-val">DEPTH</span>
              </td>
              <td>
                <span 
                  class="badge-tag"
                  :class="{
                    'badge-tag-ir': p.missed_reason_category === 'INJURY_IR',
                    'badge-tag-pup': p.missed_reason_category === 'INJURY_PUP',
                    'badge-tag-out': p.missed_reason_category === 'INJURY_RULED_OUT' || p.missed_reason_category === 'INJURY_INACTIVE',
                    'badge-tag-q': p.missed_reason_category === 'INJURED_PLAYED_QUESTIONABLE',
                    'badge-tag-bye': p.missed_reason_category === 'HEALTHY_SCRATCH'
                  }"
                >
                  {{ (p.missed_reason_category || 'ACTIVE').replace('INJURY_', '').replace(/_/g, ' ') }}
                </span>
              </td>
              <td class="diag-text" :class="{ 'text-rose': p.game_missed }">
                {{ p.primary_injury || '—' }}
              </td>
              <td class="mono-val text-xs">
                <span v-if="p.game_missed" class="text-rose font-bold">[MISSED]</span>
                <span v-else class="text-emerald">[DRESSED]</span>
              </td>
              <td class="text-xs text-muted">{{ p.practice_status || 'Full / Active' }}</td>
              <td class="mono-val text-xs font-bold" :class="p.health_impact_weight >= 1 ? 'text-rose' : 'text-amber'">
                -{{ p.health_impact_weight || 0 }} PTS
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.deep-dive-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.switch-bar {
  padding: 0.65rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.switch-label {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--text-muted);
}

.team-btns-scroll {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  overflow-x: auto;
}

.team-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.25rem 0.55rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.1s ease;
}

.mini-logo {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.team-btn:hover {
  background: #171c2b;
  color: #ffffff;
}

.team-btn.active {
  background: #00b0ff;
  border-color: #00b0ff;
  color: #07080c;
  font-weight: 900;
}

.team-hero {
  padding: 1.5rem 1.75rem;
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

.hero-team-logo {
  width: 72px;
  height: 72px;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.7));
  flex-shrink: 0;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.hero-division {
  font-size: 0.72rem;
  color: var(--accent-cyan);
}

.hero-title {
  font-size: 2.2rem;
  font-weight: 900;
  color: #ffffff;
  line-height: 1;
}

.hero-stats-line {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 0.35rem;
  flex-wrap: wrap;
}

.meta-dot {
  color: var(--border-accent);
}

.hero-right {
  display: flex;
  align-items: center;
}

.rating-box {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.rating-label {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.rating-num-row {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.rating-massive {
  font-family: var(--font-display);
  font-size: 2.75rem;
  font-weight: 900;
  line-height: 1;
}

.denom {
  font-size: 0.95rem;
  color: var(--text-muted);
}

.metrics-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 900px) {
  .metrics-two-col {
    grid-template-columns: 1fr;
  }
}

.unit-panel, .trajectory-panel {
  padding: 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-size: 1.05rem;
  font-weight: 900;
  color: #ffffff;
}

.panel-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.unit-bars-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.unit-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.unit-label {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 0.04em;
}

.unit-pct {
  font-size: 0.82rem;
  font-weight: 800;
}

.trajectory-cols {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.65rem;
  height: 160px;
  align-items: flex-end;
  padding-top: 0.5rem;
}

.traj-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  gap: 0.3rem;
}

.traj-val {
  font-size: 0.72rem;
  font-weight: 800;
  color: #ffffff;
}

.traj-track {
  width: 20px;
  flex: 1;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: flex-end;
}

.traj-fill {
  width: 100%;
  transition: height 0.4s ease;
}

.traj-wk {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--text-secondary);
}

.traj-opp {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.roster-panel {
  padding: 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.roster-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
  gap: 1rem;
  flex-wrap: wrap;
}

.roster-title-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.65rem;
  color: var(--text-muted);
}

.roster-input {
  padding-left: 2rem;
  width: 220px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.table-wrap {
  overflow-x: auto;
}

.sharp-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.sharp-table th {
  padding: 0.55rem 0.75rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-card);
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.sharp-table td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.82rem;
}

.table-row:hover {
  background: var(--bg-card-hover);
}

.player-name-cell {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.name-text {
  font-weight: 700;
  color: #ffffff;
}

.jersey-num {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.pos-tag {
  font-size: 0.72rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.1rem 0.35rem;
  font-weight: 800;
}

.diag-text {
  color: var(--text-secondary);
  font-weight: 600;
}

.empty-cell {
  text-align: center;
  padding: 2.5rem;
  color: var(--text-muted);
}
</style>
