<script setup>
import { ref, computed, watch } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { getTeam } from '../data/nflTeams'
import { 
  Search, 
  Download, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  User, 
  UserMinus, 
  SlidersHorizontal,
  ArrowUpDown
} from 'lucide-vue-next'

const { 
  playerInjuries, 
  availableWeeks, 
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

// Reset to page 1 on filter changes
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

  // Week filter
  if (selectedWeek.value !== 'all') {
    list = list.filter(p => Number(p.week) === Number(selectedWeek.value))
  }

  // Team filter
  if (filterTeam.value !== 'ALL') {
    list = list.filter(p => String(p.team).trim().toUpperCase() === filterTeam.value)
  }

  // Position filter
  if (filterPosition.value !== 'ALL') {
    list = list.filter(p => String(p.position_group).trim().toUpperCase() === filterPosition.value)
  }

  // Category filter
  if (filterCategory.value !== 'ALL') {
    list = list.filter(p => p.missed_reason_category === filterCategory.value)
  }

  // Starters only
  if (onlyStarters.value) {
    list = list.filter(p => p.is_starter === true || p.is_starter === 'True' || p.is_starter === 1)
  }

  // Missed game only
  if (onlyMissed.value) {
    list = list.filter(p => p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1)
  }

  // Text search
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

  // Sort
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
  <section class="player-explorer-section glass-panel">
    <!-- Header & Action Row -->
    <div class="explorer-header">
      <div class="header-left">
        <div class="icon-wrap">
          <User :size="20" />
        </div>
        <div>
          <h2 class="title">Player Injury & Missed Games Database</h2>
          <p class="subtitle">
            Comprehensive register of 4,600+ player-week records with snap shares, body parts, and IR carry-forwards.
          </p>
        </div>
      </div>

      <div class="header-actions">
        <span class="match-count mono-val">
          <strong>{{ filteredPlayers.length.toLocaleString() }}</strong> records matching
        </span>
        <button class="btn-primary" @click="exportFilteredCsv" title="Export current filtered results to CSV">
          <Download :size="16" />
          <span>Export Filtered CSV</span>
        </button>
      </div>
    </div>

    <!-- Filter Toolbar Controls -->
    <div class="filter-toolbar">
      <!-- Search Input -->
      <div class="search-wrap">
        <Search :size="16" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Search by player name, injury..." 
          class="input-glass search-field"
        />
      </div>

      <!-- Team Filter Dropdown -->
      <div class="filter-item">
        <label>Team:</label>
        <select v-model="filterTeam" class="input-glass select-field">
          <option value="ALL">All Teams (32)</option>
          <option v-for="t in availableTeams" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>

      <!-- Position Group Dropdown -->
      <div class="filter-item">
        <label>Position:</label>
        <select v-model="filterPosition" class="input-glass select-field">
          <option v-for="pos in positionGroups" :key="pos" :value="pos">{{ pos }}</option>
        </select>
      </div>

      <!-- Missed Category Dropdown -->
      <div class="filter-item">
        <label>Status / Category:</label>
        <select v-model="filterCategory" class="input-glass select-field">
          <option v-for="cat in missedCategories" :key="cat" :value="cat">
            {{ cat.replace('INJURY_', '').replace(/_/g, ' ') }}
          </option>
        </select>
      </div>

      <!-- Checkbox Toggles -->
      <div class="toggles-group">
        <label class="toggle-label">
          <input type="checkbox" v-model="onlyStarters" />
          <span>Starters Only</span>
        </label>
        <label class="toggle-label">
          <input type="checkbox" v-model="onlyMissed" />
          <span>Missed Game Only</span>
        </label>
      </div>
    </div>

    <!-- Table Container -->
    <div class="table-container">
      <table class="player-table">
        <thead>
          <tr>
            <th class="cursor-pointer" @click="toggleSort('week')">
              <div class="th-content">
                <span>Wk</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
            <th class="cursor-pointer" @click="toggleSort('player_name')">
              <div class="th-content">
                <span>Player</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
            <th>Team</th>
            <th class="cursor-pointer" @click="toggleSort('position')">
              <div class="th-content">
                <span>Pos</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
            <th>Depth / Role</th>
            <th>Designated Status</th>
            <th class="cursor-pointer" @click="toggleSort('primary_injury')">
              <div class="th-content">
                <span>Diagnosed Injury</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
            <th>Practice Status</th>
            <th class="cursor-pointer" @click="toggleSort('offense_pct')">
              <div class="th-content">
                <span>Snap %</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
            <th class="cursor-pointer" @click="toggleSort('health_impact_weight')">
              <div class="th-content">
                <span>Impact Wt</span>
                <ArrowUpDown :size="13" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedPlayers.length === 0">
            <td colspan="10" class="empty-state-cell">
              No players match your active search filters.
            </td>
          </tr>
          <tr 
            v-for="p in paginatedPlayers" 
            :key="`${p.season}_${p.week}_${p.gsis_id || p.player_name}`"
            class="player-row"
          >
            <!-- Week -->
            <td class="mono-val text-muted text-sm font-bold">W{{ p.week }}</td>

            <!-- Player Name -->
            <td>
              <div class="player-identity">
                <span class="player-fullname">{{ p.player_name }}</span>
                <span v-if="p.years_exp" class="exp-tag">{{ p.years_exp }} yr exp</span>
              </div>
            </td>

            <!-- Team -->
            <td>
              <button 
                class="team-cell-btn" 
                @click="openTeam(p.team)"
                title="View team deep dive"
                :style="{
                  backgroundColor: `${getTeam(p.team).primaryColor}22`,
                  borderColor: getTeam(p.team).primaryColor,
                  color: '#ffffff'
                }"
              >
                {{ p.team }}
              </button>
            </td>

            <!-- Position -->
            <td>
              <span class="position-tag mono-val">{{ p.position }}</span>
            </td>

            <!-- Depth / Role -->
            <td>
              <span v-if="p.is_starter" class="badge badge-starter">
                Starter (Rank {{ p.depth_chart_rank || 1 }})
              </span>
              <span v-else class="text-muted text-xs">
                Depth {{ p.depth_chart_rank ? '#' + p.depth_chart_rank : '' }}
              </span>
            </td>

            <!-- Designated Status -->
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
                {{ (p.missed_reason_category || 'ACTIVE').replace('INJURY_', '').replace(/_/g, ' ') }}
              </span>
            </td>

            <!-- Diagnosed Injury -->
            <td>
              <span 
                class="injury-diag"
                :class="{ 'text-rose font-bold': p.game_missed, 'text-secondary': !p.game_missed }"
              >
                {{ p.primary_injury || '—' }}
              </span>
            </td>

            <!-- Practice Status -->
            <td>
              <span class="text-xs text-secondary">
                {{ p.practice_status || 'Full / Active' }}
              </span>
            </td>

            <!-- Snaps -->
            <td class="mono-val text-sm">
              <span v-if="p.game_missed" class="text-muted">0% (Out)</span>
              <span v-else-if="p.offense_pct > 0" class="text-emerald font-bold">
                {{ Math.round(p.offense_pct * 100) }}% Off
              </span>
              <span v-else-if="p.defense_pct > 0" class="text-cyan font-bold">
                {{ Math.round(p.defense_pct * 100) }}% Def
              </span>
              <span v-else class="text-muted">
                {{ p.total_snaps || 0 }} snaps
              </span>
            </td>

            <!-- Impact Weight -->
            <td class="mono-val font-bold">
              <span :class="p.health_impact_weight >= 1 ? 'text-rose' : 'text-amber'">
                -{{ p.health_impact_weight || 0 }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div class="pagination-footer">
      <div class="page-size-selector">
        <span class="text-muted text-sm">Rows per page:</span>
        <select v-model="pageSize" class="input-glass select-mini">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>

      <div class="pagination-nav">
        <span class="page-info mono-val text-sm text-secondary">
          Page <strong>{{ currentPage }}</strong> of <strong>{{ totalPages }}</strong>
        </span>
        <button 
          class="btn-ghost pagination-btn" 
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <ChevronLeft :size="16" />
          <span>Previous</span>
        </button>
        <button 
          class="btn-ghost pagination-btn" 
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
        >
          <span>Next</span>
          <ChevronRight :size="16" />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.player-explorer-section {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.explorer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: var(--accent-violet);
  display: flex;
  align-items: center;
  justify-content: center;
}

.title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.subtitle {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.match-count {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.85rem 1rem;
  background: rgba(0, 0, 0, 0.25);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-muted);
}

.search-field {
  padding-left: 2.25rem;
  width: 250px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
}

.select-field {
  padding: 0.45rem 0.75rem;
  background: rgba(15, 23, 42, 0.8);
  font-size: 0.82rem;
}

.toggles-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 600;
  cursor: pointer;
}

.toggle-label input {
  accent-color: var(--accent-cyan);
  cursor: pointer;
}

.table-container {
  overflow-x: auto;
}

.player-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.player-table th {
  padding: 0.75rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.th-content {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  color: var(--accent-cyan);
}

.player-table td {
  padding: 0.75rem 0.85rem;
  font-size: 0.85rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.player-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.player-identity {
  display: flex;
  flex-direction: column;
}

.player-fullname {
  font-weight: 700;
  color: #ffffff;
}

.exp-tag {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.team-cell-btn {
  border: 1px solid;
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  font-weight: 800;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.team-cell-btn:hover {
  transform: scale(1.05);
}

.position-tag {
  background: rgba(255, 255, 255, 0.07);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
}

.injury-diag {
  font-size: 0.85rem;
}

.empty-state-cell {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
}

.pagination-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.select-mini {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.pagination-nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pagination-btn {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
