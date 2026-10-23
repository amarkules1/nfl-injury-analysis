<script setup>
import { ref, computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { 
  Swords, 
  MapPin, 
  ShieldAlert, 
  ArrowRight, 
  Check, 
  AlertTriangle,
  ChevronDown,
  Layers
} from 'lucide-vue-next'

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

// Unit labels mapping
const unitLabels = [
  { key: 'qb', label: 'Quarterback' },
  { key: 'ol', label: 'Offensive Line' },
  { key: 'skill', label: 'Skill (RB/WR/TE)' },
  { key: 'front', label: 'Front 7 (DL/LB)' },
  { key: 'secondary', label: 'Secondary (DB)' }
]
</script>

<template>
  <section class="matchup-center-section">
    <!-- Header -->
    <div class="glass-panel section-header">
      <div class="header-text">
        <div class="icon-wrap">
          <Swords :size="20" />
        </div>
        <div>
          <h2 class="title">Matchup Health Advantage Center</h2>
          <p class="subtitle">
            Head-to-head roster health comparison for Week {{ selectedWeek }}. Net advantage computes injury-adjusted edges.
          </p>
        </div>
      </div>
      <div class="matchup-count-pill">
        <span>{{ weekMatchups.length }} Matchups Logged</span>
      </div>
    </div>

    <!-- Empty State if no matchups for selected week -->
    <div v-if="weekMatchups.length === 0" class="glass-panel empty-state">
      <AlertTriangle :size="36" class="text-amber" />
      <h3>No scheduled games found for this selection</h3>
      <p>Select a specific week from the top bar (e.g., Week 1 through 7) to inspect head-to-head games.</p>
    </div>

    <!-- Matchup Cards Grid -->
    <div v-else class="matchups-grid">
      <div 
        v-for="match in weekMatchups" 
        :key="match.gameId"
        class="glass-panel matchup-card"
        :class="{ 'expanded': expandedMatchupId === match.gameId }"
      >
        <!-- Top Metadata Bar -->
        <div class="card-top-bar">
          <div class="game-date-meta">
            <span class="mono-val date-text">{{ match.gameDate || 'Week ' + match.week }}</span>
            <span class="surface-tag">
              <Layers :size="12" />
              <span>{{ match.surface }}</span>
            </span>
          </div>

          <!-- Advantage Badge -->
          <div 
            class="net-advantage-pill"
            :class="{
              'adv-home': match.homeAdvantage > 0,
              'adv-away': match.homeAdvantage < 0,
              'adv-even': match.homeAdvantage === 0
            }"
          >
            <span v-if="match.homeAdvantage !== 0">
              <strong>{{ match.favoriteTeam }}</strong> +{{ match.absAdvantage }} Health Edge
            </span>
            <span v-else>Even Roster Health</span>
          </div>
        </div>

        <!-- H2H Teams Comparison Block -->
        <div class="teams-versus-container">
          <!-- Away Team -->
          <div 
            class="team-side away-side"
            @click="openTeam(match.awayTeam.team)"
            title="Click to view team deep dive"
          >
            <div class="team-header-row">
              <div 
                class="team-circle-badge"
                :style="{ 
                  backgroundColor: match.awayTeam.info.primaryColor,
                  color: match.awayTeam.info.textColor 
                }"
              >
                {{ match.awayTeam.team }}
              </div>
              <div class="team-names">
                <span class="team-abbr">{{ match.awayTeam.team }}</span>
                <span class="team-full">{{ match.awayTeam.info.name }}</span>
                <span class="role-tag">Away</span>
              </div>
            </div>

            <div class="health-score-huge-wrap">
              <span 
                class="health-score-huge mono-val"
                :style="{ color: match.awayTeam.grade.color }"
              >
                {{ match.awayTeam.healthScore }}
              </span>
              <span 
                class="grade-tag"
                :style="{ 
                  color: match.awayTeam.grade.color, 
                  backgroundColor: match.awayTeam.grade.bg,
                  borderColor: match.awayTeam.grade.color
                }"
              >
                Grade {{ match.awayTeam.grade.grade }}
              </span>
            </div>

            <div class="starters-lost-stat">
              <span class="stat-num mono-val">{{ match.awayTeam.startersOutCount }}</span>
              <span class="stat-label">Starters Out</span>
            </div>
          </div>

          <!-- Center VS Divider -->
          <div class="center-vs-divider">
            <span class="vs-text">VS</span>
            <div class="vs-line"></div>
          </div>

          <!-- Home Team -->
          <div 
            class="team-side home-side"
            @click="openTeam(match.homeTeam.team)"
            title="Click to view team deep dive"
          >
            <div class="team-header-row home-reverse">
              <div 
                class="team-circle-badge"
                :style="{ 
                  backgroundColor: match.homeTeam.info.primaryColor,
                  color: match.homeTeam.info.textColor 
                }"
              >
                {{ match.homeTeam.team }}
              </div>
              <div class="team-names text-right">
                <span class="team-abbr">{{ match.homeTeam.team }}</span>
                <span class="team-full">{{ match.homeTeam.info.name }}</span>
                <span class="role-tag home-tag">Home</span>
              </div>
            </div>

            <div class="health-score-huge-wrap home-reverse">
              <span 
                class="grade-tag"
                :style="{ 
                  color: match.homeTeam.grade.color, 
                  backgroundColor: match.homeTeam.grade.bg,
                  borderColor: match.homeTeam.grade.color
                }"
              >
                Grade {{ match.homeTeam.grade.grade }}
              </span>
              <span 
                class="health-score-huge mono-val"
                :style="{ color: match.homeTeam.grade.color }"
              >
                {{ match.homeTeam.healthScore }}
              </span>
            </div>

            <div class="starters-lost-stat home-reverse">
              <span class="stat-num mono-val">{{ match.homeTeam.startersOutCount }}</span>
              <span class="stat-label">Starters Out</span>
            </div>
          </div>
        </div>

        <!-- Key Missing Starters Preview -->
        <div class="key-injuries-summary">
          <div class="side-injuries">
            <span class="injuries-label">{{ match.awayTeam.team }} Out:</span>
            <div v-if="match.awayTeam.keyMissing.length > 0" class="chips-row">
              <span 
                v-for="p in match.awayTeam.keyMissing" 
                :key="p"
                class="injury-chip away-chip"
              >
                {{ p }}
              </span>
            </div>
            <span v-else class="healthy-note">No starters sidelined</span>
          </div>

          <div class="side-injuries text-right">
            <span class="injuries-label">{{ match.homeTeam.team }} Out:</span>
            <div v-if="match.homeTeam.keyMissing.length > 0" class="chips-row justify-end">
              <span 
                v-for="p in match.homeTeam.keyMissing" 
                :key="p"
                class="injury-chip home-chip"
              >
                {{ p }}
              </span>
            </div>
            <span v-else class="healthy-note">No starters sidelined</span>
          </div>
        </div>

        <!-- Expand / Toggle Button for Unit Breakdown -->
        <button class="expand-btn" @click="toggleExpand(match.gameId)">
          <span>{{ expandedMatchupId === match.gameId ? 'Hide Unit Breakdown' : 'Compare Positional Units' }}</span>
          <ChevronDown 
            :size="16" 
            :class="{ 'rotate-180': expandedMatchupId === match.gameId }" 
          />
        </button>

        <!-- Expanded Unit Comparison Table -->
        <div v-if="expandedMatchupId === match.gameId" class="expanded-units-panel animate-fade-in">
          <div class="unit-bars-title">
            <span>Unit Health Comparison (0 - 100 Index)</span>
          </div>

          <div 
            v-for="u in unitLabels" 
            :key="u.key"
            class="unit-row"
          >
            <!-- Away unit score -->
            <div class="unit-team-val left-val mono-val">
              {{ match.awayTeam.units[u.key] ?? 100 }}
            </div>

            <!-- Comparative Bars -->
            <div class="unit-bars-center">
              <div class="unit-label-text">{{ u.label }}</div>
              <div class="dual-bar-container">
                <!-- Away Bar (extends leftwards) -->
                <div class="bar-half left-half">
                  <div 
                    class="bar-fill-away"
                    :style="{ 
                      width: `${match.awayTeam.units[u.key] ?? 100}%`,
                      backgroundColor: match.awayTeam.info.primaryColor 
                    }"
                  ></div>
                </div>
                <!-- Divider -->
                <div class="dual-divider"></div>
                <!-- Home Bar (extends rightwards) -->
                <div class="bar-half right-half">
                  <div 
                    class="bar-fill-home"
                    :style="{ 
                      width: `${match.homeTeam.units[u.key] ?? 100}%`,
                      backgroundColor: match.homeTeam.info.primaryColor 
                    }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Home unit score -->
            <div class="unit-team-val right-val mono-val">
              {{ match.homeTeam.units[u.key] ?? 100 }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.matchup-center-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-header {
  padding: 1.25rem 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.header-text {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--accent-cyan);
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

.matchup-count-pill {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-subtle);
  padding: 0.35rem 0.85rem;
  border-radius: var(--radius-pill);
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.empty-state h3 {
  font-size: 1.25rem;
  color: #ffffff;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.matchups-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

@media (max-width: 1050px) {
  .matchups-grid {
    grid-template-columns: 1fr;
  }
}

.matchup-card {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.game-date-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.date-text {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 600;
}

.surface-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  text-transform: capitalize;
}

.net-advantage-pill {
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-pill);
}

.adv-home, .adv-away {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.adv-even {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.teams-versus-container {
  display: grid;
  grid-template-columns: 1fr 40px 1fr;
  align-items: center;
  gap: 1rem;
}

.team-side {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.team-side:hover {
  background: rgba(255, 255, 255, 0.04);
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

.team-circle-badge {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.95rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
  flex-shrink: 0;
}

.team-names {
  display: flex;
  flex-direction: column;
}

.team-abbr {
  font-size: 1.15rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.2;
}

.team-full {
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.role-tag {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
}

.home-tag {
  color: var(--accent-cyan);
}

.health-score-huge-wrap {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.health-score-huge {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
}

.grade-tag {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-pill);
  border: 1px solid;
}

.starters-lost-stat {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.stat-num {
  font-weight: 700;
  color: #ffffff;
}

.center-vs-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.vs-text {
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.vs-line {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
}

.key-injuries-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.side-injuries {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.injuries-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.chips-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.justify-end {
  justify-content: flex-end;
}

.injury-chip {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

.away-chip, .home-chip {
  background: rgba(239, 68, 68, 0.14);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.healthy-note {
  font-size: 0.72rem;
  color: #34d399;
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.45rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.rotate-180 {
  transform: rotate(180deg);
}

.expanded-units-panel {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.unit-bars-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.unit-row {
  display: grid;
  grid-template-columns: 45px 1fr 45px;
  align-items: center;
  gap: 0.75rem;
}

.unit-team-val {
  font-size: 0.85rem;
  font-weight: 700;
  color: #ffffff;
}

.left-val {
  text-align: right;
}

.right-val {
  text-align: left;
}

.unit-bars-center {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.unit-label-text {
  font-size: 0.72rem;
  color: var(--text-secondary);
  text-align: center;
  font-weight: 600;
}

.dual-bar-container {
  display: flex;
  align-items: center;
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-pill);
  overflow: hidden;
  position: relative;
}

.bar-half {
  flex: 1;
  height: 100%;
  display: flex;
}

.left-half {
  justify-content: flex-end;
}

.right-half {
  justify-content: flex-start;
}

.bar-fill-away, .bar-fill-home {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width 0.5s ease;
}

.dual-divider {
  width: 2px;
  height: 100%;
  background: rgba(255, 255, 255, 0.4);
  z-index: 2;
}
</style>
