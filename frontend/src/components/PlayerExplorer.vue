<script setup>
import { ref, computed, watch } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam } from '../data/nflTeams'
import { Search, Download, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-vue-next'

const { 
  playerInjuries, 
  availableTeams, 
  selectedWeek,
  selectedTeam,
  selectedView 
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

const filteredPlayers = computed(() => {
  let list = playerInjuries.value

  if (selectedWeek.value !== 'all') {
    list = list.filter(p => Number(p.week) === Number(selectedWeek.value))
  }

  if (filterTeam.value !== 'ALL') {
    list = list.filter(p => String(p.team).trim().toUpperCase() === filterTeam.value)
  }

  if (filterPosition.value !== 'ALL') {
    list = list.filter(p => String(p.position_group).trim().toUpperCase() === filterPosition.value)
  }

  if (filterCategory.value !== 'ALL') {
    list = list.filter(p => p.missed_reason_category === filterCategory.value)
  }

  if (onlyStarters.value) {
    list = list.filter(p => p.is_starter === true || p.is_starter === 'True' || p.is_starter === 1)
  }

  if (onlyMissed.value) {
    list = list.filter(p => p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p => 
      String(p.player_name || '').toLowerCase().includes(q) ||
      String(p.primary_injury || '').toLowerCase().includes(q) ||
      String(p.team || '').toLowerCase().includes(q) ||
      String(p.position || '').toLowerCase().includes(q) ||
      String(p.missed_reason_detail || '').toLowerCase().includes(q)
    )
  }

  const sorted = [...list].sort((a, b) => {
    let valA = a[sortBy.value]
    let valB = b[sortBy.value]
    if (valA === undefined || valA === null) valA = ''
    if (valB === undefined || valB === null) valB = ''

    if (typeof valA === 'string') valA = valA.toLowerCase()
    if (typeof valB === 'string') valB = valB.toLowerCase()

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
  link.setAttribute('download', `nfl_injuries_export_week_${selectedWeek.value}.csv`)
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
        <h2 class="section-title">PLAYER INJURY & MISSED GAMES DATABASE</h2>
        <span class="count-tag mono-val">{{ filteredPlayers.length.toLocaleString() }} RECORDS MATCHING</span>
      </div>

      <button class="btn-action" @click="exportFilteredCsv" title="Export CSV">
        <Download :size="14" />
        <span>EXPORT CSV</span>
      </button>
    </div>

    <!-- Filters Bar -->
    <div class="filter-strip">
      <div class="search-box">
        <Search :size="14" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="SEARCH PLAYER, INJURY..." 
          class="input-sharp search-field"
        />
      </div>

      <div class="filter-group">
        <label class="filter-lbl mono-val">TEAM:</label>
        <select v-model="filterTeam" class="input-sharp select-field mono-val">
          <option value="ALL">ALL (32)</option>
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
          <span>STARTERS ONLY</span>
        </label>
        <label class="check-label mono-val">
          <input type="checkbox" v-model="onlyMissed" />
          <span>MISSED GAME ONLY</span>
        </label>
      </div>
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
            <th>DESIGNATED STATUS</th>
            <th class="cursor-sort" @click="toggleSort('primary_injury')">
              <div class="th-sort"><span>DIAGNOSED INJURY</span><ArrowUpDown :size="11" /></div>
            </th>
            <th>PRACTICE</th>
            <th class="cursor-sort" @click="toggleSort('offense_pct')">
              <div class="th-sort"><span>SNAP %</span><ArrowUpDown :size="11" /></div>
            </th>
            <th class="cursor-sort" @click="toggleSort('health_impact_weight')">
              <div class="th-sort"><span>IMPACT WT</span><ArrowUpDown :size="11" /></div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedPlayers.length === 0">
            <td colspan="10" class="empty-cell mono-val">No records match your filters.</td>
          </tr>
          <tr 
            v-for="p in paginatedPlayers" 
            :key="`${p.season}_${p.week}_${p.gsis_id || p.player_name}`"
            class="table-row"
          >
            <td class="mono-val text-muted text-xs font-bold">W{{ p.week }}</td>
            <td class="player-cell">
              <span class="player-fullname">{{ p.player_name }}</span>
              <span v-if="p.years_exp" class="exp-text mono-val">{{ p.years_exp }}Y EXP</span>
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
              <span v-if="p.is_starter" class="badge-tag badge-tag-starter">
                STARTER #{{ p.depth_chart_rank || 1 }}
              </span>
              <span v-else class="text-muted text-xs mono-val">
                DEPTH {{ p.depth_chart_rank ? '#' + p.depth_chart_rank : '' }}
              </span>
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
            <td class="diag-text" :class="{ 'text-rose font-bold': p.game_missed }">
              {{ p.primary_injury || '—' }}
            </td>
            <td class="text-xs text-muted">{{ p.practice_status || 'Full / Active' }}</td>
            <td class="mono-val text-xs">
              <span v-if="p.game_missed" class="text-rose font-bold">0% (OUT)</span>
              <span v-else-if="p.offense_pct > 0" class="text-emerald font-bold">
                {{ Math.round(p.offense_pct * 100) }}% OFF
              </span>
              <span v-else-if="p.defense_pct > 0" class="text-cyan font-bold">
                {{ Math.round(p.defense_pct * 100) }}% DEF
              </span>
              <span v-else class="text-muted">
                {{ p.total_snaps || 0 }} SNAPS
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
        <span class="text-muted text-xs mono-val">ROWS PER PAGE:</span>
        <select v-model="pageSize" class="input-sharp select-mini mono-val">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>

      <div class="page-controls">
        <span class="page-status mono-val text-xs">
          PAGE <strong>{{ currentPage }}</strong> OF <strong>{{ totalPages }}</strong>
        </span>
        <button 
          class="btn-action mini-btn" 
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <ChevronLeft :size="13" />
          <span>PREV</span>
        </button>
        <button 
          class="btn-action mini-btn" 
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          <span>NEXT</span>
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
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-wrap: wrap;
  gap: 1rem;
}

.header-titles {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.35rem;
  font-weight: 900;
  color: #ffffff;
}

.count-tag {
  font-size: 0.72rem;
  color: var(--accent-cyan);
  background: rgba(0, 176, 255, 0.1);
  border: 1px solid rgba(0, 176, 255, 0.25);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-xs);
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
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.filter-lbl {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 700;
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
  font-weight: 700;
  cursor: pointer;
}

.check-label input {
  accent-color: var(--accent-cyan);
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
  font-weight: 700;
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
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.2rem 0.45rem;
  color: #ffffff;
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 800;
}

.cell-logo {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.team-pill-btn:hover {
  border-color: var(--accent-cyan);
}

.pos-box {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.1rem 0.35rem;
  font-weight: 800;
  font-size: 0.72rem;
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
</style>
