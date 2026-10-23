<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { Search, ArrowUpDown, ChevronRight } from 'lucide-vue-next'

const { 
  teamPowerRankings, 
  selectedTeam, 
  selectedView,
  selectedWeek 
} = useInjuryData()

const searchQuery = ref('')
const conferenceFilter = ref('ALL') // ALL, AFC, NFC
const sortBy = ref('healthScore')
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

  if (conferenceFilter.value !== 'ALL') {
    list = list.filter(t => t.info?.conference === conferenceFilter.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(t => 
      t.team.toLowerCase().includes(q) ||
      t.info?.name.toLowerCase().includes(q) ||
      t.keyMissing.toLowerCase().includes(q)
    )
  }

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
  <section class="leaderboard-section sharp-panel">
    <!-- Header Controls -->
    <div class="leaderboard-header">
      <div class="title-block">
        <h2 class="section-title">NFL TEAM HEALTH POWER RANKINGS</h2>
        <span class="count-badge mono-val">32 / 32 TEAMS RANKED</span>
      </div>

      <div class="controls-toolbar">
        <!-- Search Field -->
        <div class="search-box">
          <Search :size="14" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="FILTER TEAM OR PLAYER..." 
            class="input-sharp search-input"
          />
        </div>

        <!-- Conference Pills -->
        <div class="conf-filter-group">
          <button 
            class="conf-btn" 
            :class="{ active: conferenceFilter === 'ALL' }"
            @click="conferenceFilter = 'ALL'"
          >
            ALL (32)
          </button>
          <button 
            class="conf-btn" 
            :class="{ active: conferenceFilter === 'AFC' }"
            @click="conferenceFilter = 'AFC'"
          >
            AFC
          </button>
          <button 
            class="conf-btn" 
            :class="{ active: conferenceFilter === 'NFC' }"
            @click="conferenceFilter = 'NFC'"
          >
            NFC
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table Header -->
    <div class="rankings-table-header">
      <div class="col-rank">RANK</div>
      <div class="col-team">TEAM</div>
      <div 
        class="col-score sortable-col"
        :class="{ active: sortBy === 'healthScore' }"
        @click="toggleSort('healthScore')"
      >
        <span>HEALTH RATING</span>
        <ArrowUpDown :size="12" />
      </div>
      <div class="col-qb">STARTING QB STATUS</div>
      <div 
        class="col-starters sortable-col"
        :class="{ active: sortBy === 'startersOut' }"
        @click="toggleSort('startersOut')"
      >
        <span>STARTERS SIDELINED</span>
        <ArrowUpDown :size="12" />
      </div>
      <div class="col-missing">KEY SIDELINED ASSETS</div>
      <div class="col-action"></div>
    </div>

    <!-- 32 Teams List -->
    <div class="rankings-list">
      <div 
        v-for="team in filteredRankings" 
        :key="team.team"
        class="ranking-row"
        @click="openTeamDeepDive(team.team)"
      >
        <!-- Rank -->
        <div class="col-rank">
          <span 
            class="rank-num mono-val"
            :class="{ 'rank-elite': team.rank <= 5, 'rank-depleted': team.rank >= 28 }"
          >
            #{{ String(team.rank).padStart(2, '0') }}
          </span>
        </div>

        <!-- Real NFL Team Logo & Identity -->
        <div class="col-team">
          <img 
            :src="team.info.logo" 
            :alt="team.info.name"
            class="team-real-logo"
            loading="lazy"
          />
          <div class="team-meta">
            <div class="team-name-row">
              <span class="team-name">{{ team.info.name }}</span>
              <span v-if="team.isBye" class="badge-tag badge-tag-bye">
                BYE (W{{ team.carriedFromWeek }} RATING)
              </span>
            </div>
            <span class="team-sub">{{ team.info.division }} • {{ team.team }}</span>
          </div>
        </div>

        <!-- Health Score & Flat Bar -->
        <div class="col-score">
          <div class="score-line">
            <span 
              class="score-bold mono-val"
              :style="{ color: team.grade.color }"
            >
              {{ team.healthScore }}
            </span>
            <span 
              class="badge-tag"
              :style="{ 
                color: team.grade.color, 
                backgroundColor: team.grade.bg,
                borderColor: team.grade.color
              }"
            >
              GRADE {{ team.grade.grade }}
            </span>
          </div>
          <div class="sharp-meter-track">
            <div 
              class="sharp-meter-fill"
              :style="{ 
                width: `${Math.min(100, Math.max(0, team.healthScore))}%`,
                backgroundColor: team.grade.color 
              }"
            ></div>
          </div>
        </div>

        <!-- Starting QB Status Only -->
        <div class="col-qb">
          <div v-if="team.qbStatus === 'Healthy'" class="qb-tag-healthy">
            <span class="qb-dot-green"></span>
            <span class="qb-text">STARTER HEALTHY</span>
          </div>
          <div v-else-if="team.qbStatus === 'Out'" class="badge-tag badge-tag-out">
            <span>OUT: {{ team.qbNameOut || 'STARTER' }}</span>
          </div>
          <div v-else class="badge-tag badge-tag-q">
            <span>{{ team.qbStatus.toUpperCase() }}: {{ team.qbNameOut || 'STARTER' }}</span>
          </div>
        </div>

        <!-- Starters Out -->
        <div class="col-starters">
          <span 
            class="starters-tag mono-val"
            :class="{ 
              'tag-clean': team.startersOut === 0,
              'tag-mid': team.startersOut >= 1 && team.startersOut <= 3,
              'tag-high': team.startersOut >= 4
            }"
          >
            {{ team.startersOut }} LOST
          </span>
          <span v-if="team.startersQ > 0" class="starters-q mono-val">
            +{{ team.startersQ }} QUEST
          </span>
        </div>

        <!-- Key Missing Assets -->
        <div class="col-missing">
          <div v-if="team.keyMissing" class="chips-wrap">
            <span 
              v-for="name in team.keyMissing.split(';').slice(0, 3)" 
              :key="name" 
              class="asset-chip"
            >
              {{ name.trim() }}
            </span>
            <span v-if="team.keyMissing.split(';').length > 3" class="more-text mono-val">
              +{{ team.keyMissing.split(';').length - 3 }} MORE
            </span>
          </div>
          <span v-else class="text-dim text-xs">— FULL ROSTER ACTIVE —</span>
        </div>

        <!-- Row Chevron -->
        <div class="col-action">
          <ChevronRight :size="15" class="action-arrow" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.leaderboard-section {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.leaderboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
}

.title-block {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.section-title {
  font-size: 1.35rem;
  font-weight: 900;
  color: #ffffff;
}

.count-badge {
  font-size: 0.72rem;
  color: var(--accent-cyan);
  background: rgba(0, 176, 255, 0.1);
  border: 1px solid rgba(0, 176, 255, 0.25);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-xs);
  letter-spacing: 0.05em;
}

.controls-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
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

.search-input {
  padding-left: 2rem;
  width: 220px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.conf-filter-group {
  display: flex;
  align-items: center;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
}

.conf-btn {
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: all 0.1s ease;
}

.conf-btn:last-child {
  border-right: none;
}

.conf-btn:hover {
  color: #ffffff;
  background: #171c2b;
}

.conf-btn.active {
  background: var(--accent-cyan);
  color: #07080c;
  font-weight: 900;
}

/* Header Columns */
.rankings-table-header {
  display: grid;
  grid-template-columns: 55px 260px 180px 180px 150px 1fr 30px;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0.85rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

.sortable-col {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  user-select: none;
}

.sortable-col:hover, .sortable-col.active {
  color: var(--accent-cyan);
}

/* Ranking Rows */
.rankings-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ranking-row {
  display: grid;
  grid-template-columns: 55px 260px 180px 180px 150px 1fr 30px;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0.85rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: all 0.1s ease;
}

.ranking-row:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-accent);
}

.ranking-row:hover .action-arrow {
  color: var(--accent-cyan);
  transform: translateX(2px);
}

.rank-num {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-muted);
}

.rank-elite {
  color: #00e676;
}

.rank-depleted {
  color: #ff5252;
}

.col-team {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.team-real-logo {
  width: 38px;
  height: 38px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.6));
  flex-shrink: 0;
}

.team-meta {
  display: flex;
  flex-direction: column;
}

.team-name-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.team-name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.02em;
}

.team-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.col-score {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.score-line {
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
}

.score-bold {
  font-size: 1.25rem;
  font-weight: 900;
  line-height: 1;
}

.col-qb {
  display: flex;
  align-items: center;
}

.qb-tag-healthy {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  color: #00e676;
}

.qb-dot-green {
  width: 6px;
  height: 6px;
  background: #00e676;
  border-radius: 0;
}

.col-starters {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.starters-tag {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.15rem 0.45rem;
  border: 1px solid;
  border-radius: var(--radius-xs);
}

.tag-clean {
  background: rgba(0, 230, 118, 0.1);
  color: #00e676;
  border-color: rgba(0, 230, 118, 0.3);
}

.tag-mid {
  background: rgba(255, 193, 7, 0.1);
  color: #ffd740;
  border-color: rgba(255, 193, 7, 0.3);
}

.tag-high {
  background: rgba(255, 23, 68, 0.1);
  color: #ff5252;
  border-color: rgba(255, 23, 68, 0.35);
}

.starters-q {
  font-size: 0.7rem;
  color: var(--accent-amber);
}

.chips-wrap {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.asset-chip {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  padding: 0.1rem 0.45rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-family: var(--font-body);
}

.more-text {
  font-size: 0.68rem;
  color: var(--accent-cyan);
}

.action-arrow {
  color: var(--text-muted);
  transition: transform 0.1s ease;
}

@media (max-width: 1100px) {
  .rankings-table-header, .ranking-row {
    grid-template-columns: 45px 200px 140px 140px 120px 1fr 25px;
    gap: 0.65rem;
  }
}

@media (max-width: 850px) {
  .rankings-table-header {
    display: none;
  }
  .ranking-row {
    grid-template-columns: 1fr;
    gap: 0.65rem;
  }
}
</style>
