<script setup>
import { ref } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { ChevronDown } from 'lucide-vue-next'

const { 
  weekMatchups, 
  selectedWeek, 
  selectedTeam, 
  selectedView 
} = useInjuryData()

const expandedMatchupId = ref(null)

function toggleExpand(id) {
  expandedMatchupId.value = expandedMatchupId.value === id ? null : id
}

function openTeam(teamAbbr) {
  selectedTeam.value = teamAbbr
  selectedView.value = 'teams'
}

const unitLabels = [
  { key: 'qb', label: 'Quarterback' },
  { key: 'ol', label: 'Offensive Line' },
  { key: 'skill', label: 'Skill Positions' },
  { key: 'front', label: 'Front Seven' },
  { key: 'secondary', label: 'Secondary' }
]
</script>

<template>
  <section class="matchup-section">
    <div class="sharp-panel section-bar">
      <div class="bar-title-block">
        <h2 class="section-title">MATCHUP HEALTH ADVANTAGE</h2>
        <span class="bar-subtitle mono-val">Week {{ selectedWeek }} • {{ weekMatchups.length }} Games Scheduled</span>
      </div>
    </div>

    <!-- Matchup Cards Grid -->
    <div class="matchups-grid">
      <div 
        v-for="match in weekMatchups" 
        :key="match.gameId"
        class="sharp-panel match-card"
        :class="{ 'expanded': expandedMatchupId === match.gameId }"
      >
        <!-- Top Bar -->
        <div class="match-top-line">
          <div class="match-meta">
            <span class="date-str mono-val">{{ match.gameDate || 'Week ' + match.week }}</span>
            <span class="divider-slash">/</span>
            <span class="surface-str mono-val">{{ match.surface }}</span>
          </div>

          <!-- Pure colored text advantage - NO box -->
          <div class="advantage-indicator mono-val">
            <span v-if="match.homeAdvantage !== 0" class="text-emerald">
              <strong>{{ match.favoriteTeam }}</strong> +{{ match.absAdvantage }} advantage
            </span>
            <span v-else class="text-muted">Even health</span>
          </div>
        </div>

        <!-- Teams Versus Board -->
        <div class="teams-board">
          <!-- Away Team -->
          <div 
            class="team-side-block" 
            @click="openTeam(match.awayTeam.team)"
            title="Inspect team deep dive"
          >
            <div class="team-header-row">
              <img 
                :src="match.awayTeam.info.logo" 
                :alt="match.awayTeam.info.name"
                class="match-logo"
              />
              <div class="team-headings">
                <span class="team-code">{{ match.awayTeam.team }}</span>
                <span class="team-full">{{ match.awayTeam.info.name }}</span>
                <span class="location-tag mono-val">Away</span>
              </div>
            </div>

            <div class="score-line">
              <span 
                class="score-number mono-val"
                :style="{ color: match.awayTeam.grade.color }"
              >
                {{ match.awayTeam.healthScore }}
              </span>
              <span 
                class="grade-text mono-val"
                :style="{ color: match.awayTeam.grade.color }"
              >
                {{ match.awayTeam.grade.label }}
              </span>
            </div>

            <div class="starters-stat mono-val">
              <span class="text-rose font-bold">{{ match.awayTeam.startersOutCount }}</span> starters out
            </div>
          </div>

          <!-- Center VS Marker -->
          <div class="center-marker">
            <span class="vs-label mono-val">vs</span>
            <div class="vs-rule"></div>
          </div>

          <!-- Home Team -->
          <div 
            class="team-side-block home-side" 
            @click="openTeam(match.homeTeam.team)"
            title="Inspect team deep dive"
          >
            <div class="team-header-row home-reverse">
              <img 
                :src="match.homeTeam.info.logo" 
                :alt="match.homeTeam.info.name"
                class="match-logo"
              />
              <div class="team-headings text-right">
                <span class="team-code">{{ match.homeTeam.team }}</span>
                <span class="team-full">{{ match.homeTeam.info.name }}</span>
                <span class="location-tag home-loc mono-val">Home</span>
              </div>
            </div>

            <div class="score-line home-reverse">
              <span 
                class="grade-text mono-val"
                :style="{ color: match.homeTeam.grade.color }"
              >
                {{ match.homeTeam.grade.label }}
              </span>
              <span 
                class="score-number mono-val"
                :style="{ color: match.homeTeam.grade.color }"
              >
                {{ match.homeTeam.healthScore }}
              </span>
            </div>

            <div class="starters-stat text-right mono-val">
              <span class="text-rose font-bold">{{ match.homeTeam.startersOutCount }}</span> starters out
            </div>
          </div>
        </div>

        <!-- Missing Starters Strip -->
        <div class="starters-strip">
          <div class="strip-side">
            <span class="strip-label mono-val">{{ match.awayTeam.team }} SIDELINED:</span>
            <span v-if="match.awayTeam.keyMissing.length > 0" class="strip-names">
              {{ match.awayTeam.keyMissing.join(', ') }}
            </span>
            <span v-else class="text-dim text-xs mono-val">— None —</span>
          </div>
          <div class="strip-side text-right">
            <span class="strip-label mono-val">{{ match.homeTeam.team }} SIDELINED:</span>
            <span v-if="match.homeTeam.keyMissing.length > 0" class="strip-names">
              {{ match.homeTeam.keyMissing.join(', ') }}
            </span>
            <span v-else class="text-dim text-xs mono-val">— None —</span>
          </div>
        </div>

        <!-- Compare Button -->
        <button class="expand-btn mono-val" @click="toggleExpand(match.gameId)">
          <span>{{ expandedMatchupId === match.gameId ? 'HIDE UNIT RATINGS' : 'COMPARE POSITIONAL UNITS' }}</span>
          <ChevronDown :size="13" :class="{ 'rotate-180': expandedMatchupId === match.gameId }" />
        </button>

        <!-- Expanded Unit Grid -->
        <div v-if="expandedMatchupId === match.gameId" class="units-expanded-box">
          <div 
            v-for="u in unitLabels" 
            :key="u.key"
            class="unit-comp-row"
          >
            <span class="unit-val-left mono-val">{{ match.awayTeam.units[u.key] ?? 100 }}</span>
            <div class="unit-bar-middle">
              <span class="unit-title-text">{{ u.label }}</span>
              <div class="split-meter">
                <div class="meter-half half-left">
                  <div 
                    class="meter-fill-away"
                    :style="{ 
                      width: `${match.awayTeam.units[u.key] ?? 100}%`,
                      backgroundColor: match.awayTeam.info.primaryColor 
                    }"
                  ></div>
                </div>
                <div class="meter-divider"></div>
                <div class="meter-half half-right">
                  <div 
                    class="meter-fill-home"
                    :style="{ 
                      width: `${match.homeTeam.units[u.key] ?? 100}%`,
                      backgroundColor: match.homeTeam.info.primaryColor 
                    }"
                  ></div>
                </div>
              </div>
            </div>
            <span class="unit-val-right mono-val">{{ match.homeTeam.units[u.key] ?? 100 }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.matchup-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-bar {
  padding: 0.85rem 1.25rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.bar-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.matchups-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (max-width: 1050px) {
  .matchups-grid {
    grid-template-columns: 1fr;
  }
}

.match-card {
  padding: 1.15rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.match-top-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
}

.match-meta {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.divider-slash {
  color: var(--border-card);
}

.advantage-indicator {
  font-size: 0.75rem;
  font-weight: 600;
}

.teams-board {
  display: grid;
  grid-template-columns: 1fr 30px 1fr;
  align-items: center;
  gap: 1rem;
}

.team-side-block {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  cursor: pointer;
  padding: 0.45rem;
  border-radius: var(--radius-xs);
  transition: background 0.1s ease;
}

.team-side-block:hover {
  background: var(--bg-card-hover);
}

.team-header-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.home-reverse {
  flex-direction: row-reverse;
}

.text-right {
  text-align: right;
}

.match-logo {
  width: 42px;
  height: 42px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.6));
  flex-shrink: 0;
}

.team-headings {
  display: flex;
  flex-direction: column;
}

.team-code {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1;
  color: #ffffff;
}

.team-full {
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.location-tag {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.home-loc {
  color: var(--accent-cyan);
}

.score-line {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.score-number {
  font-family: var(--font-display);
  font-size: 1.85rem;
  font-weight: 700;
  line-height: 1;
}

.grade-text {
  font-size: 0.78rem;
  font-weight: 600;
}

.starters-stat {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.center-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.vs-label {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.vs-rule {
  width: 1px;
  height: 35px;
  background: var(--border-subtle);
}

.starters-strip {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 0.5rem 0.65rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
}

.strip-side {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.strip-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 600;
}

.strip-names {
  font-size: 0.74rem;
  color: var(--accent-rose);
  line-height: 1.25;
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.4rem;
  cursor: pointer;
  transition: all 0.1s ease;
}

.expand-btn:hover {
  background: var(--bg-card);
  color: #ffffff;
  border-color: var(--border-card);
}

.rotate-180 {
  transform: rotate(180deg);
}

.units-expanded-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle);
}

.unit-comp-row {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  gap: 0.65rem;
}

.unit-val-left {
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffffff;
  text-align: right;
}

.unit-val-right {
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffffff;
  text-align: left;
}

.unit-bar-middle {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.unit-title-text {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
}

.split-meter {
  display: flex;
  height: 4px;
  background: #263147;
}

.meter-half {
  flex: 1;
  height: 100%;
  display: flex;
}

.half-left {
  justify-content: flex-end;
}

.half-right {
  justify-content: flex-start;
}

.meter-fill-away, .meter-fill-home {
  height: 100%;
  transition: width 0.3s ease;
}

.meter-divider {
  width: 2px;
  height: 100%;
  background: #3e4d6d;
}

.text-rose {
  color: var(--accent-rose);
}

.text-emerald {
  color: var(--accent-emerald);
}
</style>
