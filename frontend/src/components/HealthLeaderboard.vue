<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { 
  Trophy, 
  Search, 
  ArrowUpDown, 
  ChevronRight, 
  Shield, 
  AlertCircle,
  CheckCircle2,
  Filter
} from 'lucide-vue-next'

const { 
  teamPowerRankings, 
  selectedTeam, 
  selectedView,
  selectedWeek 
} = useInjuryData()

const searchQuery = ref('')
const conferenceFilter = ref('ALL') // ALL, AFC, NFC
const sortBy = ref('healthScore') // healthScore, startersOut, gamesMissed
const sortOrder = ref('desc')

function toggleSort(field) {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = field === 'healthScore' ? 'desc' : 'asc'
  }
}

const filteredRankings = computed(() => {
  let list = [...teamPowerRankings.value]

  // Filter by conference
  if (conferenceFilter.value !== 'ALL') {
    list = list.filter(t => t.info?.conference === conferenceFilter.value)
  }

  // Filter by search query
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(t => 
      t.team.toLowerCase().includes(q) ||
      t.info?.name.toLowerCase().includes(q) ||
      t.keyMissing.toLowerCase().includes(q)
    )
  }

  // Sort
  list.sort((a, b) => {
    let valA = a[sortBy.value]
    let valB = b[sortBy.value]
    if (typeof valA === 'string') valA = valA.toLowerCase()
    if (typeof valB === 'string') valB = valB.toLowerCase()

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return list
})

function openTeamDeepDive(teamAbbr) {
  selectedTeam.value = teamAbbr
  selectedView.value = 'teams'
}
</script>

<template>
  <section class="leaderboard-section glass-panel">
    <!-- Header with Filters & Controls -->
    <div class="leaderboard-header">
      <div class="title-wrap">
        <div class="section-icon">
          <Trophy :size="20" />
        </div>
        <div>
          <h2 class="section-title">NFL Team Health Power Rankings</h2>
          <p class="section-sub">
            Rankings based on the 0-100 baseline model. Deductions heavily penalize lost QBs (-22.0) and starters (-4.5).
          </p>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="controls-toolbar">
        <!-- Search Input -->
        <div class="search-box">
          <Search :size="16" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search team or player..." 
            class="input-glass search-input"
          />
        </div>

        <!-- Conference Filter Pills -->
        <div class="conf-filter-pills">
          <button 
            class="filter-pill" 
            :class="{ active: conferenceFilter === 'ALL' }"
            @click="conferenceFilter = 'ALL'"
          >
            All (32)
          </button>
          <button 
            class="filter-pill" 
            :class="{ active: conferenceFilter === 'AFC' }"
            @click="conferenceFilter = 'AFC'"
          >
            AFC
          </button>
          <button 
            class="filter-pill" 
            :class="{ active: conferenceFilter === 'NFC' }"
            @click="conferenceFilter = 'NFC'"
          >
            NFC
          </button>
        </div>
      </div>
    </div>

    <!-- Table Header / Sort Bar -->
    <div class="table-columns-header">
      <div class="col-rank">Rank</div>
      <div class="col-team">Team</div>
      <div 
        class="col-score sortable-col"
        :class="{ active: sortBy === 'healthScore' }"
        @click="toggleSort('healthScore')"
      >
        <span>Health Index</span>
        <ArrowUpDown :size="14" />
      </div>
      <div class="col-qb">QB Status</div>
      <div 
        class="col-starters sortable-col"
        :class="{ active: sortBy === 'startersOut' }"
        @click="toggleSort('startersOut')"
      >
        <span>Starters Missing</span>
        <ArrowUpDown :size="14" />
      </div>
      <div class="col-key-missing">Key Sidelined Starters</div>
      <div class="col-action"></div>
    </div>

    <!-- Rankings List -->
    <div class="rankings-list">
      <div 
        v-for="(team, index) in filteredRankings" 
        :key="team.team"
        class="ranking-row"
        @click="openTeamDeepDive(team.team)"
      >
        <!-- Rank -->
        <div class="col-rank">
          <span 
            class="rank-num mono-val"
            :class="{
              'rank-top': team.rank <= 5,
              'rank-bottom': team.rank >= 28
            }"
          >
            #{{ team.rank }}
          </span>
        </div>

        <!-- Team Identity -->
        <div class="col-team">
          <div 
            class="team-logo-badge"
            :style="{ 
              backgroundColor: team.info.primaryColor,
              color: team.info.textColor 
            }"
          >
            {{ team.team }}
          </div>
          <div class="team-meta">
            <span class="team-full-name">{{ team.info.name }}</span>
            <span class="team-sub-meta">{{ team.info.division }}</span>
          </div>
        </div>

        <!-- Health Score & Bar -->
        <div class="col-score">
          <div class="score-display-row">
            <span 
              class="score-number mono-val"
              :style="{ color: team.grade.color }"
            >
              {{ team.healthScore }}
            </span>
            <span 
              class="grade-chip"
              :style="{ 
                color: team.grade.color, 
                backgroundColor: team.grade.bg,
                borderColor: team.grade.color
              }"
            >
              {{ team.grade.grade }}
            </span>
          </div>
          <!-- Animated Progress Meter -->
          <div class="health-meter-track">
            <div 
              class="health-meter-fill"
              :style="{ 
                width: `${Math.min(100, Math.max(0, team.healthScore))}%`,
                background: `linear-gradient(90deg, ${team.grade.color}88, ${team.grade.color})`
              }"
            ></div>
          </div>
        </div>

        <!-- QB Status -->
        <div class="col-qb">
          <div v-if="team.qbStatus === 'Healthy'" class="qb-healthy">
            <CheckCircle2 :size="15" />
            <span>Healthy</span>
          </div>
          <div v-else class="qb-out-badge">
            <AlertCircle :size="15" />
            <span class="qb-name">{{ team.qbNameOut || team.qbStatus }} (OUT)</span>
          </div>
        </div>

        <!-- Starters Out -->
        <div class="col-starters">
          <span 
            class="starters-count-badge mono-val"
            :class="{ 
              'badge-good': team.startersOut <= 1,
              'badge-warning': team.startersOut >= 2 && team.startersOut <= 4,
              'badge-danger': team.startersOut >= 5
            }"
          >
            {{ team.startersOut }} Lost
          </span>
          <span v-if="team.startersQ > 0" class="starters-q-sub">
            +{{ team.startersQ }} Quest.
          </span>
        </div>

        <!-- Key Missing Starters -->
        <div class="col-key-missing">
          <div v-if="team.keyMissing" class="chips-container">
            <span 
              v-for="name in team.keyMissing.split(',').slice(0, 3)" 
              :key="name" 
              class="player-mini-chip"
            >
              {{ name.trim() }}
            </span>
            <span v-if="team.keyMissing.split(',').length > 3" class="more-chip">
              +{{ team.keyMissing.split(',').length - 3 }} more
            </span>
          </div>
          <span v-else class="text-muted text-sm">— No major starters out —</span>
        </div>

        <!-- Chevron / Action -->
        <div class="col-action">
          <ChevronRight :size="18" class="row-arrow" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.leaderboard-section {
  padding: 1.5rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.leaderboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding-bottom: 0.5rem;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.section-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #fbbf24;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.section-sub {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.controls-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  padding-left: 2.25rem;
  width: 220px;
}

.conf-filter-pills {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.2rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.filter-pill {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  border-radius: 5px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-pill:hover {
  color: #ffffff;
}

.filter-pill.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

/* Columns header */
.table-columns-header {
  display: grid;
  grid-template-columns: 70px 240px 180px 180px 150px 1fr 40px;
  align-items: center;
  gap: 1rem;
  padding: 0.65rem 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sortable-col {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-fast);
}

.sortable-col:hover, .sortable-col.active {
  color: var(--accent-cyan);
}

/* Ranking rows */
.rankings-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ranking-row {
  display: grid;
  grid-template-columns: 70px 240px 180px 180px 150px 1fr 40px;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ranking-row:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(56, 189, 248, 0.3);
  transform: translateX(4px);
}

.ranking-row:hover .row-arrow {
  color: var(--accent-cyan);
  transform: translateX(3px);
}

.rank-num {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-muted);
}

.rank-top {
  color: #34d399;
}

.rank-bottom {
  color: #f87171;
}

.col-team {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.team-logo-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.82rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  flex-shrink: 0;
}

.team-meta {
  display: flex;
  flex-direction: column;
}

.team-full-name {
  font-weight: 700;
  font-size: 0.92rem;
  color: #ffffff;
}

.team-sub-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.col-score {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.score-display-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-number {
  font-size: 1.2rem;
  font-weight: 800;
}

.grade-chip {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  border: 1px solid;
}

.col-qb {
  display: flex;
  align-items: center;
}

.qb-healthy {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #34d399;
  font-size: 0.82rem;
  font-weight: 600;
}

.qb-out-badge {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 700;
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-starters {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.starters-count-badge {
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-pill);
}

.badge-good {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.starters-q-sub {
  font-size: 0.75rem;
  color: var(--accent-amber);
  font-weight: 600;
}

.chips-container {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.player-mini-chip {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-pill);
  padding: 0.15rem 0.55rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.more-chip {
  font-size: 0.72rem;
  color: var(--accent-cyan);
  font-weight: 600;
}

.row-arrow {
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

@media (max-width: 1100px) {
  .table-columns-header, .ranking-row {
    grid-template-columns: 50px 180px 130px 120px 110px 1fr 30px;
    gap: 0.65rem;
    padding: 0.75rem 0.85rem;
  }
}

@media (max-width: 850px) {
  .table-columns-header {
    display: none;
  }
  .ranking-row {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
}
</style>
