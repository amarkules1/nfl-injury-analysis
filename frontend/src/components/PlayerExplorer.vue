<script setup>
import { ref, computed, watch } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam } from '../data/nflTeams'
import { Search, Download, ChevronLeft, ChevronRight, ArrowUpDown, Sparkles } from 'lucide-vue-next'

const { 
  playerInjuries, 
  playerPredictions,
  upcomingWeek,
  isUpcomingSelected,
  availableTeams, 
  availableWeeks,
  selectedWeek,
  selectedTeam,
  selectedView,
  teamPowerRankings 
} = useInjuryData()

const searchQuery = ref('')
const filterTeam = ref('ALL')
const filterPosition = ref('ALL')
const filterCategory = ref('ALL')
const onlyStarters = ref(false)
const onlyMissed = ref(false)

const sortBy = ref('health_impact_weight')
const sortOrder = ref('desc')

const currentPage = ref(1)
const pageSize = ref(25)

watch([searchQuery, filterTeam, filterPosition, filterCategory, onlyStarters, onlyMissed], () => {
  currentPage.value = 1
})

watch(isUpcomingSelected, (upcoming) => {
  if (upcoming && sortBy.value === 'offense_pct') {
    sortBy.value = 'play_probability'
    sortOrder.value = 'asc'
  } else if (!upcoming && sortBy.value === 'play_probability') {
    sortBy.value = 'health_impact_weight'
    sortOrder.value = 'desc'
  }
})

const positionGroups = ['ALL', 'QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'CB', 'S', 'ST']

const missedCategories = [
  'ALL',
  'INJURY_IR',
  'INJURY_PUP',
  'INJURY_RULED_OUT',
  'INJURY_INACTIVE',
  'INJURED_PLAYED_QUESTIONABLE',
  'HEALTHY_SCRATCH',
  'SUSPENSION',
  'COMMISSIONER_EXEMPT'
]

function toggleSort(field) {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = 'desc'
  }
}

function getProbColor(prob) {
  const p = Number(prob)
  if (p >= 0.8) return '#10b981' // green
  if (p >= 0.5) return '#eab308' // amber
  if (p >= 0.2) return '#f97316' // orange
  return '#f43f5e' // rose
}

const predictionsMap = computed(() => {
  const map = new Map()
  for (const pred of playerPredictions.value) {
    const t = String(pred.team || '').trim().toUpperCase() === 'LAR' ? 'LA' : String(pred.team || '').trim().toUpperCase()
    const name = String(pred.player_name || '').trim().toLowerCase()
    const key = `${pred.week}_${t}_${name}`
    map.set(key, pred)
  }
  return map
})

const filteredTeamOnBye = computed(() => {
  if (filterTeam.value === 'ALL' || selectedWeek.value === 'all') return null
  const targetTeam = filterTeam.value === 'LAR' ? 'LA' : filterTeam.value
  const teamData = teamPowerRankings.value.find(t => t.team === targetTeam)
  return teamData?.isBye ? teamData : null
})

const filteredPlayers = computed(() => {
  let list = []

  if (selectedWeek.value === 'all') {
    list = playerInjuries.value.filter(p => availableWeeks.value.includes(Number(p.week)))
  } else if (selectedWeek.value === 'upcoming') {
    const targetWeek = upcomingWeek.value
    list = playerInjuries.value.filter(p => Number(p.week) === Number(targetWeek))
    if (list.length === 0 && playerPredictions.value.length > 0) {
      list = playerPredictions.value.filter(p => Number(p.week) === Number(targetWeek))
    }
  } else {
    list = playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))
  }

  // Merge ML predictions onto player records
  const predMap = predictionsMap.value
  list = list.map(p => {
    const t = String(p.team || '').trim().toUpperCase() === 'LAR' ? 'LA' : String(p.team || '').trim().toUpperCase()
    const name = String(p.player_name || '').trim().toLowerCase()
    const pred = predMap.get(`${p.week}_${t}_${name}`)
    if (pred) {
      return {
        ...p,
        play_probability: pred.play_probability,
        play_likelihood_label: pred.play_likelihood_label
      }
    }
    return p
  })

  if (filterTeam.value !== 'ALL') {
    const targetTeam = filterTeam.value === 'LAR' ? 'LA' : filterTeam.value
    list = list.filter(p => {
      const pTeam = String(p.team || '').trim().toUpperCase() === 'LAR' ? 'LA' : String(p.team || '').trim().toUpperCase()
      return pTeam === targetTeam
    })
  }

  if (filterPosition.value !== 'ALL') {
    list = list.filter(p => String(p.position_group || p.position || '').trim().toUpperCase() === filterPosition.value)
  }

  if (filterCategory.value !== 'ALL') {
    list = list.filter(p => p.missed_reason_category === filterCategory.value)
  }

  if (onlyStarters.value) {
    list = list.filter(p => p.is_starter === true || p.is_starter === 'True' || p.is_starter === 1)
  }

  if (onlyMissed.value) {
    if (isUpcomingSelected.value) {
      list = list.filter(p => 
        p.game_missed === true || 
        p.game_missed === 'True' || 
        p.game_missed === 1 || 
        (p.play_probability !== undefined && Number(p.play_probability) < 0.5) ||
        ['Out', 'Doubtful'].includes(p.report_status)
      )
    } else {
      list = list.filter(p => p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1)
    }
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p => 
      String(p.player_name || '').toLowerCase().includes(q) ||
      String(p.primary_injury || '').toLowerCase().includes(q) ||
      String(p.team || '').toLowerCase().includes(q) ||
      String(p.position || '').toLowerCase().includes(q) ||
      String(p.missed_reason_detail || '').toLowerCase().includes(q) ||
      String(p.report_status || '').toLowerCase().includes(q) ||
      String(p.play_likelihood_label || '').toLowerCase().includes(q)
    )
  }

  const sorted = [...list].sort((a, b) => {
    let valA = a[sortBy.value]
    let valB = b[sortBy.value]
    if (valA === undefined || valA === null) valA = ''
    if (valB === undefined || valB === null) valB = ''

    if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    } else {
      const numA = Number(valA)
      const numB = Number(valB)
      if (!isNaN(numA) && !isNaN(numB)) {
        valA = numA
        valB = numB
      }
    }

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return sorted
})

const totalPages = computed(() => Math.ceil(filteredPlayers.value.length / pageSize.value) || 1)

const paginatedPlayers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredPlayers.value.slice(start, start + pageSize.value)
})

function exportFilteredCsv() {
  const rows = filteredPlayers.value
  if (rows.length === 0) return

  const headers = Object.keys(rows[0])
  const csvContent = [
    headers.join(','),
    ...rows.map(r => 
      headers.map(h => {
        let val = r[h]
        if (val === null || val === undefined) val = ''
        val = String(val).replace(/"/g, '""')
        return `"${val}"`
      }).join(',')
    )
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  const weekLabel = isUpcomingSelected.value ? `week_${upcomingWeek.value}_forecast` : `week_${selectedWeek.value}`
  link.setAttribute('download', `nfl_injuries_export_${weekLabel}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function openTeam(teamAbbr) {
  selectedTeam.value = teamAbbr
  selectedView.value = 'teams'
}
</script>

<template>
  <section class="sharp-panel explorer-panel">
    <div class="explorer-header">
      <div class="header-titles">
        <h2 class="section-title">PLAYER INJURY DATABASE</h2>
        <span v-if="isUpcomingSelected" class="model-badge mono-val">
          <Sparkles :size="12" /> WEEK {{ upcomingWeek }} AVAILABILITY FORECAST
        </span>
        <span class="count-tag mono-val">{{ filteredPlayers.length.toLocaleString() }} records</span>
      </div>

      <button class="btn-action" @click="exportFilteredCsv" title="Export CSV">
        <Download :size="14" />
        <span>Export CSV</span>
      </button>
    </div>

    <!-- Predictive Model Notice Banner for Upcoming Week -->
    <div v-if="isUpcomingSelected" class="projections-banner mono-val">
      <Sparkles :size="14" class="banner-sparkle" />
      <span><strong>Week {{ upcomingWeek }} Availability Forecast:</strong> Player availability likelihoods generated by the machine learning model based on official injury designations, practice participation trends, and prior game availability.</span>
    </div>

    <!-- Filters Bar -->
    <div class="filter-strip">
      <div class="search-box">
        <Search :size="14" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Search player, injury..." 
          class="input-sharp search-field"
        />
      </div>

      <div class="filter-group">
        <label class="filter-lbl mono-val">TEAM:</label>
        <select v-model="filterTeam" class="input-sharp select-field mono-val">
          <option value="ALL">All (32)</option>
          <option v-for="t in availableTeams" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label class="filter-lbl mono-val">POS:</label>
        <select v-model="filterPosition" class="input-sharp select-field mono-val">
          <option v-for="pos in positionGroups" :key="pos" :value="pos">{{ pos }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label class="filter-lbl mono-val">CATEGORY:</label>
        <select v-model="filterCategory" class="input-sharp select-field mono-val">
          <option v-for="cat in missedCategories" :key="cat" :value="cat">
            {{ cat.replace('INJURY_', '').replace(/_/g, ' ') }}
          </option>
        </select>
      </div>

      <div class="toggles-strip">
        <label class="check-label mono-val">
          <input type="checkbox" v-model="onlyStarters" />
          <span>Starters Only</span>
        </label>
        <label class="check-label mono-val">
          <input type="checkbox" v-model="onlyMissed" />
          <span>{{ isUpcomingSelected ? 'Projected Out / At Risk' : 'Missed Game Only' }}</span>
        </label>
      </div>
    </div>

    <!-- Bye Week Notice in Explorer -->
    <div v-if="filteredTeamOnBye" class="bye-explorer-notice">
      <span class="text-tag-bye mono-val font-bold">SCHEDULED BYE WEEK:</span>
      <span class="bye-notice-body">
        <strong>{{ getTeam(filterTeam).name }}</strong> had a scheduled Bye in Week {{ isUpcomingSelected ? upcomingWeek : selectedWeek }}. 
        The NFL does not publish official injury reports for teams on bye. 
        <span v-if="filteredTeamOnBye.carriedFromWeek">
          (Team health rating of <strong>{{ filteredTeamOnBye.healthScore }}</strong> is carried forward from Week {{ filteredTeamOnBye.carriedFromWeek }}).
        </span>
      </span>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <table class="sharp-table">
        <thead>
          <tr>
            <th class="cursor-sort" @click="toggleSort('week')">
              <div class="th-sort"><span>WK</span><ArrowUpDown :size="11" /></div>
            </th>
            <th class="cursor-sort" @click="toggleSort('player_name')">
              <div class="th-sort"><span>PLAYER</span><ArrowUpDown :size="11" /></div>
            </th>
            <th>TEAM</th>
            <th class="cursor-sort" @click="toggleSort('position')">
              <div class="th-sort"><span>POS</span><ArrowUpDown :size="11" /></div>
            </th>
            <th>DEPTH ROLE</th>
            <th>{{ isUpcomingSelected ? 'REPORT / STATUS' : 'DESIGNATED STATUS' }}</th>
            <th class="cursor-sort" @click="toggleSort('primary_injury')">
              <div class="th-sort"><span>DIAGNOSED INJURY</span><ArrowUpDown :size="11" /></div>
            </th>
            <th>PRACTICE</th>
            <th v-if="isUpcomingSelected" class="cursor-sort" @click="toggleSort('play_probability')">
              <div class="th-sort"><span>PREDICTED PLAY CHANCE</span><ArrowUpDown :size="11" /></div>
            </th>
            <th v-else class="cursor-sort" @click="toggleSort('offense_pct')">
              <div class="th-sort"><span>SNAP %</span><ArrowUpDown :size="11" /></div>
            </th>
            <th class="cursor-sort" @click="toggleSort('health_impact_weight')">
              <div class="th-sort"><span>IMPACT WT</span><ArrowUpDown :size="11" /></div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedPlayers.length === 0">
            <td colspan="10" class="empty-cell mono-val">
              <span v-if="filteredTeamOnBye">
                No injury reports published for {{ getTeam(filterTeam).name }} in Week {{ isUpcomingSelected ? upcomingWeek : selectedWeek }} (Bye Week).
              </span>
              <span v-else>
                No records match your filters.
              </span>
            </td>
          </tr>
          <tr 
            v-for="p in paginatedPlayers" 
            :key="`${p.season}_${p.week}_${p.team}_${p.gsis_id || p.player_name}`"
            class="table-row"
          >
            <td class="mono-val text-muted text-xs">W{{ p.week }}</td>
            <td class="player-cell">
              <span class="player-fullname">{{ p.player_name }}</span>
              <span v-if="p.years_exp" class="exp-text mono-val">{{ p.years_exp }}y exp</span>
            </td>
            <td>
              <button 
                class="team-pill-btn" 
                @click="openTeam(p.team)"
                title="View team deep dive"
              >
                <img :src="getTeam(p.team).logo" :alt="p.team" class="cell-logo" />
                <span class="mono-val">{{ p.team }}</span>
              </button>
            </td>
            <td><span class="pos-box mono-val">{{ p.position }}</span></td>
            <td>
              <span v-if="p.is_starter === true || p.is_starter === 'True' || p.is_starter === 'true' || p.is_starter === 1" class="text-tag-starter mono-val">
                Starter
              </span>
              <span v-else class="text-muted text-xs mono-val">
                Depth {{ p.depth_chart_rank ? '#' + p.depth_chart_rank : '' }}
              </span>
            </td>
            <td>
              <span 
                class="mono-val text-xs"
                :class="{
                  'text-tag-ir': p.missed_reason_category === 'INJURY_IR' || p.roster_status === 'RES',
                  'text-tag-pup': p.missed_reason_category === 'INJURY_PUP',
                  'text-tag-out': p.report_status === 'Out' || p.missed_reason_category === 'INJURY_RULED_OUT' || p.missed_reason_category === 'INJURY_INACTIVE' || p.roster_status === 'INA',
                  'text-tag-doubtful': p.report_status === 'Doubtful',
                  'text-tag-q': p.report_status === 'Questionable' || p.missed_reason_category === 'INJURED_PLAYED_QUESTIONABLE',
                  'text-tag-active': (p.roster_status === 'ACT' && !p.report_status) || p.missed_reason_category === 'INJURED_PLAYED_PRACTICE_ONLY',
                  'text-tag-bye': p.missed_reason_category === 'HEALTHY_SCRATCH'
                }"
              >
                {{ 
                  isUpcomingSelected && p.report_status 
                    ? p.report_status 
                    : (p.missed_reason_category || (p.roster_status === 'RES' ? 'INJURED_RESERVE' : (p.roster_status === 'ACT' ? 'ACTIVE' : p.roster_status || 'ACTIVE'))).replace('INJURY_', '').replace(/_/g, ' ') 
                }}
              </span>
            </td>
            <td class="diag-text" :class="{ 'text-rose': isUpcomingSelected ? (p.play_probability !== undefined && Number(p.play_probability) < 0.5) : p.game_missed }">
              {{ p.primary_injury || '—' }}
            </td>
            <td class="text-xs text-muted">{{ p.practice_status || 'Full / Active' }}</td>
            <td v-if="isUpcomingSelected">
              <div class="prob-cell" v-if="p.play_probability !== undefined && p.play_probability !== null">
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
              <span v-else class="text-muted text-xs mono-val">—</span>
            </td>
            <td v-else class="mono-val text-xs">
              <span v-if="p.game_missed" class="text-rose">0% (Out)</span>
              <span v-else-if="p.offense_pct > 0" class="text-emerald">
                {{ Math.round(p.offense_pct * 100) }}% Off
              </span>
              <span v-else-if="p.defense_pct > 0" class="text-cyan">
                {{ Math.round(p.defense_pct * 100) }}% Def
              </span>
              <span v-else class="text-muted">
                {{ p.total_snaps || 0 }} snaps
              </span>
            </td>
            <td class="mono-val text-xs font-bold" :class="p.health_impact_weight >= 1 ? 'text-rose' : 'text-amber'">
              -{{ p.health_impact_weight || 0 }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination-bar">
      <div class="page-size-wrap">
        <span class="text-muted text-xs mono-val">ROWS:</span>
        <select v-model="pageSize" class="input-sharp select-mini mono-val">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>

      <div class="page-controls">
        <span class="page-status mono-val text-xs">
          Page <strong>{{ currentPage }}</strong> of <strong>{{ totalPages }}</strong>
        </span>
        <button 
          class="btn-action mini-btn" 
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <ChevronLeft :size="13" />
          <span>Prev</span>
        </button>
        <button 
          class="btn-action mini-btn" 
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          <span>Next</span>
          <ChevronRight :size="13" />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.explorer-panel {
  padding: 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.explorer-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-wrap: wrap;
  gap: 1rem;
}

.header-titles {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
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

.count-tag {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.projections-banner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.85rem;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: var(--radius-xs);
  color: #c4b5fd;
  font-size: 0.76rem;
  line-height: 1.4;
}

.banner-sparkle {
  color: #a78bfa;
  flex-shrink: 0;
}

.filter-strip {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.55rem 0.75rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
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

.search-field {
  padding-left: 2rem;
  width: 240px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.filter-lbl {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.select-field {
  padding: 0.35rem 0.55rem;
  font-size: 0.75rem;
}

.toggles-strip {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-left: auto;
}

.check-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.check-label input {
  accent-color: var(--accent-cyan);
}

.bye-explorer-notice {
  background: var(--bg-primary);
  border-left: 2px solid var(--accent-amber);
  padding: 0.65rem 0.85rem;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
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

.th-sort {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.cursor-sort {
  cursor: pointer;
  user-select: none;
}

.cursor-sort:hover {
  color: var(--accent-cyan);
}

.sharp-table td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.82rem;
}

.table-row:hover {
  background: var(--bg-card-hover);
}

.player-cell {
  display: flex;
  flex-direction: column;
}

.player-fullname {
  font-weight: 600;
  color: #ffffff;
}

.exp-text {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.team-pill-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: transparent;
  border: none;
  color: #ffffff;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0;
}

.cell-logo {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.team-pill-btn:hover {
  color: var(--accent-cyan);
}

.pos-box {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.diag-text {
  color: var(--text-secondary);
}

.empty-cell {
  text-align: center;
  padding: 2.5rem;
  color: var(--text-muted);
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

.text-tag-ir {
  color: #f43f5e;
  font-weight: 700;
}

.text-tag-pup {
  color: #fb923c;
  font-weight: 700;
}

.text-tag-out {
  color: #f43f5e;
  font-weight: 700;
}

.text-tag-doubtful {
  color: #fb923c;
  font-weight: 700;
}

.text-tag-q {
  color: #eab308;
  font-weight: 700;
}

.text-tag-active {
  color: #34d399;
}

.text-tag-starter {
  color: var(--accent-cyan);
  font-weight: 700;
  font-size: 0.72rem;
}

.text-tag-bye {
  color: var(--accent-amber);
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid var(--border-subtle);
  flex-wrap: wrap;
  gap: 1rem;
}

.page-size-wrap {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.select-mini {
  padding: 0.25rem 0.45rem;
  font-size: 0.72rem;
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.page-status {
  color: var(--text-muted);
}

.mini-btn {
  padding: 0.25rem 0.55rem;
  font-size: 0.75rem;
}

.mini-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.text-rose {
  color: var(--accent-rose);
}

.text-emerald {
  color: var(--accent-emerald);
}

.text-cyan {
  color: var(--accent-cyan);
}

.text-amber {
  color: var(--accent-amber);
}
</style>
