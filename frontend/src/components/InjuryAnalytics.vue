<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'

const { 
  injuryDiagnostics, 
  positionImpact, 
  surfaceAnalysis,
  selectedWeek 
} = useInjuryData()

const topInjuries = computed(() => {
  return injuryDiagnostics.value.slice(0, 10)
})

const maxCount = computed(() => {
  return topInjuries.value.length > 0 ? topInjuries.value[0].count : 1
})
</script>

<template>
  <section class="analytics-section">
    <!-- Top Row: Surface Comparison & Diagnoses -->
    <div class="two-col-grid">
      <!-- Playing Surface Comparison -->
      <div class="sharp-panel surface-panel">
        <div class="panel-header">
          <h3 class="panel-title">PLAYING SURFACE CASUALTY COMPARISON</h3>
          <span class="panel-sub mono-val">WEEK {{ selectedWeek }} BREAKDOWN</span>
        </div>

        <div class="surface-cards-grid">
          <div 
            v-for="s in surfaceAnalysis" 
            :key="s.surface"
            class="surface-box"
          >
            <div class="surface-top">
              <span class="surface-name">{{ s.surface }}</span>
              <span class="badge-tag badge-tag-starter mono-val">{{ s.total }} INJURIES</span>
            </div>
            <div class="surface-stats-grid">
              <div class="surf-stat">
                <span class="stat-num mono-val text-rose">{{ s.missed }}</span>
                <span class="stat-lbl mono-val">GAMES MISSED</span>
              </div>
              <div class="surf-stat">
                <span class="stat-num mono-val text-amber">{{ s.starters }}</span>
                <span class="stat-lbl mono-val">STARTERS LOST</span>
              </div>
              <div class="surf-stat">
                <span class="stat-num mono-val text-cyan">{{ s.avgSeverity }}</span>
                <span class="stat-lbl mono-val">AVG PENALTY</span>
              </div>
            </div>
          </div>
        </div>

        <div class="surface-callout mono-val">
          <span>NFLPA SURFACE IMPACT: Lower-extremity non-contact injuries on synthetic turf vs. natural grass stadium surfaces.</span>
        </div>
      </div>

      <!-- Top Primary Injury Diagnoses -->
      <div class="sharp-panel diagnoses-panel">
        <div class="panel-header">
          <h3 class="panel-title">PRIMARY DIAGNOSES FREQUENCY</h3>
          <span class="panel-sub mono-val">TOP REPORTED MEDICAL CONDITIONS</span>
        </div>

        <div class="diagnoses-list">
          <div 
            v-for="inj in topInjuries" 
            :key="inj.name"
            class="diag-item"
          >
            <div class="diag-meta-line">
              <span class="diag-name mono-val">{{ inj.name.toUpperCase() }}</span>
              <span class="diag-num mono-val">{{ inj.count }} PLAYERS</span>
            </div>
            <div class="sharp-meter-track">
              <div 
                class="sharp-meter-fill"
                :style="{
                  width: `${(inj.count / maxCount) * 100}%`,
                  backgroundColor: '#00b0ff'
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Positional Vulnerability Grid -->
    <div class="sharp-panel position-panel">
      <div class="panel-header">
        <h3 class="panel-title">POSITIONAL UNIT VULNERABILITY INDEX</h3>
        <span class="panel-sub mono-val">INJURY VOLUME & STARTER LOSS BY ROSTER UNIT</span>
      </div>

      <div class="positions-grid">
        <div 
          v-for="pos in positionImpact" 
          :key="pos.group"
          class="position-box"
        >
          <div class="pos-top-line">
            <span class="pos-code mono-val">{{ pos.group }}</span>
            <span class="pos-missed mono-val text-rose">{{ pos.missed }} MISSED</span>
          </div>
          <div class="pos-meta-line mono-val">
            <span>{{ pos.total }} TOTAL LOGGED</span>
            <span>•</span>
            <span class="text-amber">{{ pos.starters }} STARTERS</span>
          </div>
          <div class="sharp-meter-track">
            <div 
              class="sharp-meter-fill"
              :style="{
                width: `${Math.min(100, (pos.missed / 20) * 100)}%`,
                backgroundColor: pos.starters > 5 ? '#ff1744' : '#ffc107'
              }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.analytics-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.two-col-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 950px) {
  .two-col-grid {
    grid-template-columns: 1fr;
  }
}

.surface-panel, .diagnoses-panel, .position-panel {
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

.surface-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

@media (max-width: 600px) {
  .surface-cards-grid {
    grid-template-columns: 1fr;
  }
}

.surface-box {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.surface-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.surface-name {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 900;
  color: #ffffff;
}

.surface-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.45rem;
  text-align: center;
}

.surf-stat {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 1.35rem;
  font-weight: 900;
  line-height: 1;
}

.stat-lbl {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 700;
}

.surface-callout {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.65rem 0.85rem;
  font-size: 0.72rem;
  color: var(--accent-cyan);
  line-height: 1.4;
}

.diagnoses-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.diag-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.diag-meta-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
}

.diag-name {
  font-weight: 800;
  color: #ffffff;
}

.diag-num {
  color: var(--text-secondary);
}

.positions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

@media (max-width: 1050px) {
  .positions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .positions-grid {
    grid-template-columns: 1fr;
  }
}

.position-box {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.pos-top-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pos-code {
  font-size: 1rem;
  font-weight: 900;
  color: #ffffff;
}

.pos-missed {
  font-size: 0.78rem;
  font-weight: 800;
}

.pos-meta-line {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.7rem;
  color: var(--text-muted);
}
</style>
