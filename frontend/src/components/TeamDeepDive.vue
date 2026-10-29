<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam, getHealthGrade } from '../data/nflTeams'
import { Search, Sparkles } from 'lucide-vue-next'

const { 
  selectedTeam, 
  selectedWeek, 
  availableTeams, 
  availableWeeks,
  upcomingWeek,
  isUpcomingSelected,
  upcomingPlayerPredictionsForSelectedTeam,
  teamWeeklyTrend, 
  playerInjuries,
  teamPowerRankings 
} = useInjuryData()

function getProbColor(prob) {
  const p = Number(prob) || 0
  if (p >= 0.80) return '#34d399' // Emerald
  if (p >= 0.50) return '#fbbf24' // Amber
  if (p >= 0.20) return '#fb923c' // Coral
  return '#f87171' // Rose
}

const rosterSearch = ref('')

const teamInfo = computed(() => getTeam(selectedTeam.value))

const currentTeamRankData = computed(() => {
  return teamPowerRankings.value.find(t => t.team === selectedTeam.value) || {
    rank: 16,
    healthScore: 85,
    grade: getHealthGrade(85),
    isBye: false,
    carriedFromWeek: null,
    startersOut: 0,
    gamesMissed: 0,
    qbStatus: 'Healthy'
  }
})

const isByeWeek = computed(() => currentTeamRankData.value.isBye)

const teamCurrentRoster = computed(() => {
  if (isUpcomingSelected.value) {
    let list = [...upcomingPlayerPredictionsForSelectedTeam.value]
    if (rosterSearch.value.trim()) {
      const q = rosterSearch.value.trim().toLowerCase()
      list = list.filter(p => 
        String(p.player_name || '').toLowerCase().includes(q) ||
        String(p.position || '').toLowerCase().includes(q) ||
        String(p.primary_injury || '').toLowerCase().includes(q) ||
        String(p.report_status || '').toLowerCase().includes(q) ||
        String(p.play_likelihood_label || '').toLowerCase().includes(q)
      )
    }
    return list
  }

  let list = playerInjuries.value.filter(p => {
    const matchTeam = String(p.team).trim().toUpperCase() === selectedTeam.value.toUpperCase()
    const matchWeek = selectedWeek.value === 'all' 
      ? availableWeeks.value.includes(Number(p.week))
      : Number(p.week) === Number(selectedWeek.value)
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
      { name: 'Quarterback', key: 'qb', score: 100 },
      { name: 'Offensive Line', key: 'ol', score: 100 },
      { name: 'Skill Positions', key: 'skill', score: 100 },
      { name: 'Front Seven', key: 'front', score: 100 },
      { name: 'Secondary', key: 'secondary', score: 100 }
    ]
  }

  return [
    { name: 'Quarterback', key: 'qb', score: cur.units.qb ?? 100 },
    { name: 'Offensive Line', key: 'ol', score: cur.units.ol ?? 100 },
    { name: 'Skill Positions', key: 'skill', score: cur.units.skill ?? 100 },
    { name: 'Front Seven', key: 'front', score: cur.units.front ?? 100 },
    { name: 'Secondary', key: 'secondary', score: cur.units.secondary ?? 100 }
  ]
})

function switchToCarriedWeek() {
  if (currentTeamRankData.value.carriedFromWeek) {
    selectedWeek.value = currentTeamRankData.value.carriedFromWeek
  }
}
</script>

<template>
  <section class="deep-dive-section">
    <!-- Team Quick Switch Bar -->
    <div class="sharp-panel switch-bar">
      <span class="switch-label mono-val">TEAM</span>
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
          <div class="hero-top-tags">
            <span class="hero-division mono-val">{{ teamInfo.division }}</span>
            <span v-if="isUpcomingSelected" class="model-tag mono-val">
              <Sparkles :size="12" /> Week {{ upcomingWeek }} ML Health Projection
            </span>
            <span v-else-if="isByeWeek" class="text-tag-bye mono-val">
              Week {{ selectedWeek }} Bye (Carried from W{{ currentTeamRankData.carriedFromWeek }})
            </span>
          </div>
          <h2 class="hero-title">{{ teamInfo.name }}</h2>
          <div class="hero-stats-line mono-val">
            <span>{{ isUpcomingSelected ? 'Projected NFL Rank:' : 'NFL Rank:' }} <strong class="text-white">#{{ currentTeamRankData.rank }}</strong> / 32</span>
            <span class="meta-dot">•</span>
            <span>{{ isUpcomingSelected ? 'Projected Starters at Risk:' : 'Starters Sidelined:' }} <strong class="text-rose">{{ currentTeamRankData.startersOut }}</strong></span>
            <span class="meta-dot">•</span>
            <span>
              Starting QB: 
              <strong :class="currentTeamRankData.qbStatus === 'Healthy' ? 'text-emerald' : 'text-rose'">
                {{ currentTeamRankData.qbStatus }}
              </strong>
            </span>
          </div>
        </div>
      </div>

      <div class="hero-right">
        <div class="rating-box">
          <span class="rating-label mono-val">
            {{ isUpcomingSelected ? `PROJECTED HEALTH (WK ${upcomingWeek})` : (isByeWeek ? `HEALTH RATING (W${currentTeamRankData.carriedFromWeek})` : 'HEALTH RATING') }}
          </span>
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
            class="grade-plain-text mono-val"
            :style="{ color: currentTeamRankData.grade?.color }"
          >
            {{ currentTeamRankData.grade?.label }}
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
          <span class="panel-sub mono-val">
            {{ isByeWeek ? `Carried from Week ${currentTeamRankData.carriedFromWeek} (Bye)` : `Week ${selectedWeek} Evaluation` }}
          </span>
        </div>

        <div class="unit-bars-list">
          <div 
            v-for="u in unitsData" 
            :key="u.key"
            class="unit-item"
          >
            <div class="unit-top">
              <span class="unit-label">{{ u.name }}</span>
              <span class="unit-pct mono-val" :style="{ color: getHealthGrade(u.score).color }">
                {{ u.score }}%
              </span>
            </div>
            <div class="sharp-meter-track">
              <div 
                class="sharp-meter-fill"
                :style="{ 
                  width: `${u.score}%`,
                  backgroundColor: getHealthGrade(u.score).color
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Season Trajectory -->
      <div class="sharp-panel trajectory-panel">
        <div class="panel-header">
          <h3 class="panel-title">SEASON HEALTH PROGRESSION</h3>
          <span class="panel-sub mono-val">Weeks 1–{{ availableWeeks.length > 0 ? availableWeeks[availableWeeks.length - 1] : 6 }}</span>
        </div>

        <div class="trajectory-cols">
          <div 
            v-for="point in teamWeeklyTrend" 
            :key="point.week"
            class="traj-col"
            :class="{ 'traj-bye-col': point.isBye }"
          >
            <span class="traj-val mono-val">{{ point.score }}</span>
            <div class="traj-track" :class="{ 'track-bye': point.isBye }">
              <div 
                class="traj-fill"
                :style="{ 
                  height: `${point.score}%`,
                  backgroundColor: point.isBye ? '#4b5568' : getHealthGrade(point.score).color
                }"
              ></div>
            </div>
            <span class="traj-wk mono-val">W{{ point.week }}</span>
            <span class="traj-opp mono-val" :class="{ 'text-amber': point.isBye }">
              {{ point.opponent }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Team Active Injury Table -->
    <div class="sharp-panel roster-panel">
      <div class="roster-top">
        <div class="roster-title-block">
          <div class="roster-badge-group">
            <h3 class="panel-title">{{ teamInfo.name }} {{ isUpcomingSelected ? `WEEK ${upcomingWeek} AVAILABILITY FORECAST` : 'INJURY REPORT' }}</h3>
            <span v-if="isUpcomingSelected" class="model-badge mono-val">
              <Sparkles :size="12" /> LOGISTIC REGRESSION MODEL
            </span>
          </div>
          <span v-if="!isByeWeek || isUpcomingSelected" class="roster-count-text mono-val">
            {{ teamCurrentRoster.length }} players {{ isUpcomingSelected ? 'analyzed' : 'listed' }}
          </span>
          <span v-else class="text-tag-bye mono-val">
            Scheduled Bye Week
          </span>
        </div>

        <div class="search-box" v-if="!isByeWeek || isUpcomingSelected">
          <Search :size="14" class="search-icon" />
          <input 
            type="text" 
            v-model="rosterSearch" 
            :placeholder="isUpcomingSelected ? 'Search forecast...' : 'Search roster...'" 
            class="input-sharp roster-input"
          />
        </div>
      </div>

      <!-- Prominent Bye Week Notice when team did not have a game -->
      <div v-if="isByeWeek && !isUpcomingSelected" class="bye-week-box">
        <div class="bye-box-title">
          <span class="text-tag-bye mono-val font-bold">NO INJURY REPORT FOR BYE WEEKS</span>
          <span class="bye-box-heading">{{ teamInfo.name }} had a scheduled Bye in Week {{ selectedWeek }}</span>
        </div>
        <p class="bye-box-text">
          Official NFL injury reports and gameday inactives are not generated during a club's bye week. 
          The team's health index (<strong>{{ currentTeamRankData.healthScore }}</strong>) and unit evaluations are carried forward from <strong>Week {{ currentTeamRankData.carriedFromWeek }}</strong>.
        </p>
        <div class="bye-box-actions" v-if="currentTeamRankData.carriedFromWeek">
          <button class="btn-action mini-action" @click="switchToCarriedWeek">
            <span>View Week {{ currentTeamRankData.carriedFromWeek }} Injured Roster</span>
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="table-wrap">
        <table class="sharp-table">
          <thead>
            <tr v-if="isUpcomingSelected">
              <th>PLAYER</th>
              <th>POS</th>
              <th>DEPTH STATUS</th>
              <th>REPORT STATUS</th>
              <th>DIAGNOSED INJURY</th>
              <th>PRACTICE PARTICIPATION</th>
              <th>PREDICTED PLAY CHANCE</th>
            </tr>
            <tr v-else>
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
            <tr v-if="isByeWeek && !isUpcomingSelected">
              <td colspan="8" class="empty-cell bye-table-msg mono-val">
                No official injury report published for Week {{ selectedWeek }} (Bye Week). Ratings carried from Week {{ currentTeamRankData.carriedFromWeek }}.
              </td>
            </tr>
            <tr v-else-if="teamCurrentRoster.length === 0">
              <td :colspan="isUpcomingSelected ? 7 : 8" class="empty-cell mono-val">
                {{ isUpcomingSelected ? 'No injury/practice concerns listed for this team in upcoming week.' : 'No injury reports logged for this selection.' }}
              </td>
            </tr>
            <tr 
              v-else-if="isUpcomingSelected"
              v-for="p in teamCurrentRoster" 
              :key="p.player_name + p.position"
              class="table-row"
            >
              <td class="player-name-cell">
                <span class="name-text">{{ p.player_name }}</span>
              </td>
              <td><span class="pos-tag mono-val">{{ p.position }}</span></td>
              <td>
                <span v-if="p.is_starter === true || p.is_starter === 'True' || p.is_starter === 'true'" class="text-tag-starter mono-val">
                  Starter
                </span>
                <span v-else class="text-muted text-xs mono-val">Depth</span>
              </td>
              <td>
                <span 
                  class="mono-val text-xs"
                  :class="{
                    'text-tag-ir': p.roster_status === 'RES' && (!p.practice_status || String(p.practice_status).includes('Did Not Participate')),
                    'text-tag-active': (p.roster_status === 'RES' && p.practice_status && String(p.practice_status).includes('Full')) || p.roster_status === 'ACT',
                    'text-tag-q': (p.roster_status === 'RES' && p.practice_status && String(p.practice_status).includes('Limited')) || p.report_status === 'Questionable',
                    'text-tag-out': p.report_status === 'Out' || p.roster_status === 'INA',
                    'text-tag-doubtful': p.report_status === 'Doubtful'
                  }"
                >
                  {{ p.report_status || (p.roster_status === 'RES' ? (p.practice_status && String(p.practice_status).includes('Full') ? 'IR (Practice Full)' : (p.practice_status && String(p.practice_status).includes('Limited') ? 'IR (Practice Window)' : 'Injured Reserve')) : (p.roster_status === 'ACT' ? 'Active Roster' : p.roster_status || '—')) }}
                </span>
              </td>
              <td class="diag-text" :class="{ 'text-rose': Number(p.play_probability) < 0.5 }">
                {{ p.primary_injury || '—' }}
              </td>
              <td class="text-xs text-muted">
                {{ p.practice_status || (p.roster_status === 'RES' ? 'Not Practicing (IR)' : 'Not Listed') }}
              </td>
              <td>
                <div class="prob-cell">
                  <div class="prob-meter-row">
                    <div class="prob-track">
                      <div 
                        class="prob-fill" 
                        :style="{ 
                          width: `${Math.round(Number(p.play_probability) * 100)}%`,
                          backgroundColor: getProbColor(p.play_probability)
                        }"
                      ></div>
                    </div>
                    <span class="prob-num mono-val" :style="{ color: getProbColor(p.play_probability) }">
                      {{ Math.round(Number(p.play_probability) * 100) }}%
                    </span>
                  </div>
                  <span class="prob-label mono-val" :style="{ color: getProbColor(p.play_probability) }">
                    {{ p.play_likelihood_label }}
                  </span>
                </div>
              </td>
            </tr>
            <tr 
              v-else
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
                <span v-if="p.is_starter" class="text-tag-starter mono-val">
                  Starter
                </span>
                <span v-else class="text-muted text-xs mono-val">Depth</span>
              </td>
              <td>
                <span 
                  class="mono-val text-xs"
                  :class="{
                    'text-tag-ir': p.missed_reason_category === 'INJURY_IR',
                    'text-tag-pup': p.missed_reason_category === 'INJURY_PUP',
                    'text-tag-out': p.missed_reason_category === 'INJURY_RULED_OUT' || p.missed_reason_category === 'INJURY_INACTIVE',
                    'text-tag-q': p.missed_reason_category === 'INJURED_PLAYED_QUESTIONABLE',
                    'text-tag-bye': p.missed_reason_category === 'HEALTHY_SCRATCH'
                  }"
                >
                  {{ (p.missed_reason_category || 'ACTIVE').replace('INJURY_', '').replace(/_/g, ' ') }}
                </span>
              </td>
              <td class="diag-text" :class="{ 'text-rose': p.game_missed }">
                {{ p.primary_injury || '—' }}
              </td>
              <td class="mono-val text-xs">
                <span v-if="p.game_missed" class="text-rose font-bold">Missed</span>
                <span v-else class="text-emerald">Dressed</span>
              </td>
              <td class="text-xs text-muted">{{ p.practice_status || 'Full / Active' }}</td>
              <td class="mono-val text-xs font-bold" :class="p.health_impact_weight >= 1 ? 'text-rose' : 'text-amber'">
                -{{ p.health_impact_weight || 0 }} pts
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
  font-weight: 700;
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
  font-weight: 600;
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
  background: var(--bg-card);
  color: #ffffff;
}

.team-btn.active {
  background: var(--accent-cyan);
  border-color: var(--accent-cyan);
  color: #07090e;
  font-weight: 700;
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

.hero-top-tags {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.hero-division {
  font-size: 0.75rem;
  color: var(--accent-cyan);
}

.hero-title {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.1;
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
  color: var(--border-card);
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
  font-size: 0.68rem;
  color: var(--text-muted);
}

.rating-num-row {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.rating-massive {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}

.denom {
  font-size: 0.9rem;
  color: var(--text-muted);
}

.grade-plain-text {
  font-size: 0.75rem;
  font-weight: 600;
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
  font-size: 1rem;
  font-weight: 700;
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
  font-weight: 600;
  color: var(--text-primary);
}

.unit-pct {
  font-size: 0.82rem;
  font-weight: 700;
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

.traj-bye-col {
  opacity: 0.75;
}

.traj-val {
  font-size: 0.72rem;
  font-weight: 700;
  color: #ffffff;
}

.traj-track {
  width: 18px;
  flex: 1;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: flex-end;
}

.track-bye {
  border: 1px dashed var(--border-card);
}

.traj-fill {
  width: 100%;
  transition: height 0.4s ease;
}

.traj-wk {
  font-size: 0.72rem;
  font-weight: 700;
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
  align-items: baseline;
  gap: 0.75rem;
}

.roster-count-text {
  font-size: 0.75rem;
  color: var(--text-muted);
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
}

/* Bye Week Notice */
.bye-week-box {
  background: var(--bg-primary);
  border-left: 2px solid var(--accent-amber);
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.bye-box-title {
  display: flex;
  align-items: baseline;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.bye-box-heading {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.95rem;
  color: #ffffff;
}

.bye-box-text {
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

.bye-box-actions {
  margin-top: 0.35rem;
}

.mini-action {
  font-size: 0.75rem;
  padding: 0.35rem 0.75rem;
}

.bye-table-msg {
  color: var(--text-muted);
  font-size: 0.78rem;
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
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
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
  font-weight: 600;
  color: #ffffff;
}

.jersey-num {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.pos-tag {
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.diag-text {
  color: var(--text-secondary);
}

.empty-cell {
  text-align: center;
  padding: 2.5rem;
  color: var(--text-muted);
}

.text-rose {
  color: var(--accent-rose);
}

.text-emerald {
  color: var(--accent-emerald);
}

.text-amber {
  color: var(--accent-amber);
}

.roster-badge-group {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.model-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--accent-cyan);
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.25);
  padding: 0.2rem 0.55rem;
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--accent-cyan);
  background: rgba(34, 211, 238, 0.08);
  border: 1px solid rgba(34, 211, 238, 0.2);
  padding: 0.15rem 0.45rem;
}

.text-tag-doubtful {
  color: #fb923c;
  font-weight: 700;
}

.text-tag-active {
  color: #34d399;
}

.prob-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 140px;
}

.prob-meter-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.prob-track {
  flex: 1;
  height: 6px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.prob-num {
  font-size: 0.78rem;
  font-weight: 700;
  min-width: 34px;
  text-align: right;
}

.prob-label {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
</style>
