<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { Search, ArrowUpDown, ChevronRight } from 'lucide-vue-next'

const { 
  teamPowerRankings, 
  selectedTeam, 
  selectedView 
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
        <h2 class="section-title">TEAM HEALTH POWER RANKINGS</h2>
        <span class="count-text mono-val">32 TEAMS RANKED</span>
      </div>

      <div class="controls-toolbar">
        <div class="search-box">
          <Search :size="14" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search team or player..." 
            class="input-sharp search-input"
          />
        </div>

        <div class="conf-filter-group">
          <button 
            class="conf-btn" 
            :class="{ active: conferenceFilter === 'ALL' }"
            @click="conferenceFilter = 'ALL'"
          >
            ALL
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

        <!-- Team Logo & Name -->
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
              <!-- Plain text tag - NO box, NO highlight -->
              <span v-if="team.isBye" class="text-tag-bye mono-val">
                BYE (W{{ team.carriedFromWeek }} RATING)
              </span>
            </div>
            <span class="team-sub mono-val">{{ team.info.division }}</span>
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
            <!-- Plain text grade - NO box, NO highlight -->
            <span 
              class="grade-plain-text mono-val"
              :style="{ color: team.grade.color }"
            >
              Grade {{ team.grade.grade }}
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

        <!-- Starting QB Status Only - Plain Text -->
        <div class="col-qb">
          <span v-if="team.qbStatus === 'Healthy'" class="text-tag-starter mono-val">
            STARTER HEALTHY
          </span>
          <span v-else-if="team.qbStatus === 'Out'" class="text-tag-out mono-val">
            OUT: {{ team.qbNameOut || 'STARTER' }}
          </span>
          <span v-else class="text-tag-q mono-val">
            {{ team.qbStatus.toUpperCase() }}: {{ team.qbNameOut || 'STARTER' }}
          </span>
        </div>

        <!-- Starters Out - Plain Text -->
        <div class="col-starters">
          <span 
            class="starters-plain-text mono-val"
            :class="{ 
              'text-emerald': team.startersOut === 0,
              'text-amber': team.startersOut >= 1 && team.startersOut <= 3,
              'text-rose': team.startersOut >= 4
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
              class="asset-plain-text"
            >
              {{ name.trim() }}
            </span>
            <span v-if="team.keyMissing.split(';').length > 3" class="more-text mono-val">
              +{{ team.keyMissing.split(';').length - 3 }} more
            </span>
          </div>
          <span v-else class="text-dim text-xs mono-val">— Full roster active —</span>
        </div>

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
  align-items: baseline;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.count-text {
  font-size: 0.75rem;
  color: var(--text-muted);
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
  font-size: 0.8rem;
}

.conf-filter-group {
  display: flex;
  align-items: center;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
}

.conf-btn {
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  transition: all 0.1s ease;
}

.conf-btn:last-child {
  border-right: none;
}

.conf-btn:hover {
  color: #ffffff;
  background: var(--bg-card);
}

.conf-btn.active {
  background: var(--accent-cyan);
  color: #07090e;
  font-weight: 700;
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
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.04em;
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
  gap: 0.25rem;
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
  border-color: var(--border-card);
}

.ranking-row:hover .action-arrow {
  color: var(--accent-cyan);
  transform: translateX(2px);
}

.rank-num {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-muted);
}

.rank-elite {
  color: var(--accent-emerald);
}

.rank-depleted {
  color: var(--accent-rose);
}

.col-team {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.team-real-logo {
  width: 36px;
  height: 36px;
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
  align-items: baseline;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.team-name {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
}

.team-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
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
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1;
}

.grade-plain-text {
  font-size: 0.75rem;
  font-weight: 600;
}

.col-qb {
  display: flex;
  align-items: center;
}

.col-starters {
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
}

.starters-plain-text {
  font-size: 0.75rem;
  font-weight: 700;
}

.starters-q {
  font-size: 0.7rem;
  color: var(--accent-amber);
}

.text-rose {
  color: var(--accent-rose);
}

.text-amber {
  color: var(--accent-amber);
}

.text-emerald {
  color: var(--accent-emerald);
}

.chips-wrap {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.asset-plain-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.asset-plain-text::after {
  content: ',';
}

.asset-plain-text:last-of-type::after {
  content: '';
}

.more-text {
  font-size: 0.7rem;
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
