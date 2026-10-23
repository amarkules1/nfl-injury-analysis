<script setup>
import { computed } from 'vue'
import { useInjuryData } from '../composables/useInjuryData'
import { 
  Activity, 
  Layers, 
  ShieldCheck, 
  AlertCircle, 
  Flame, 
  PieChart 
} from 'lucide-vue-next'

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
    <!-- Top Row: Surface Turf vs Grass & Diagnosis Frequency -->
    <div class="two-col-grid">
      <!-- Playing Surface Comparison -->
      <div class="glass-panel surface-card">
        <div class="card-header">
          <div class="header-icon-wrap emerald">
            <Layers :size="20" />
          </div>
          <div>
            <h3 class="card-title">Playing Surface Injury Impact</h3>
            <p class="card-sub">Synthetic Turf vs Natural Grass comparisons for Week {{ selectedWeek }}</p>
          </div>
        </div>

        <div class="surface-cards-grid">
          <div 
            v-for="s in surfaceAnalysis" 
            :key="s.surface"
            class="surface-box"
          >
            <div class="surface-top">
              <span class="surface-name">{{ s.surface }}</span>
              <span class="surface-badge mono-val">{{ s.total }} injuries</span>
            </div>
            <div class="surface-stats-row">
              <div class="surf-stat">
                <span class="stat-value mono-val text-rose">{{ s.missed }}</span>
                <span class="stat-label">Games Missed</span>
              </div>
              <div class="surf-stat">
                <span class="stat-value mono-val text-amber">{{ s.starters }}</span>
                <span class="stat-label">Starters Lost</span>
              </div>
              <div class="surf-stat">
                <span class="stat-value mono-val text-cyan">{{ s.avgSeverity }}</span>
                <span class="stat-label">Avg Penalty Wt</span>
              </div>
            </div>
          </div>
        </div>

        <div class="surface-insight-callout">
          <AlertCircle :size="16" class="text-cyan flex-shrink-0" />
          <p>
            The NFLPA tracks lower-extremity non-contact injuries closely on synthetic turf. Our data captures stadium surface per game to quantify starter absence rates across surface types.
          </p>
        </div>
      </div>

      <!-- Top Primary Injury Diagnoses -->
      <div class="glass-panel diagnoses-card">
        <div class="card-header">
          <div class="header-icon-wrap rose">
            <Activity :size="20" />
          </div>
          <div>
            <h3 class="card-title">Top Injury Diagnoses</h3>
            <p class="card-sub">Body parts and medical reasons leading to sideline designations</p>
          </div>
        </div>

        <div class="diagnoses-list">
          <div 
            v-for="inj in topInjuries" 
            :key="inj.name"
            class="diag-item"
          >
            <div class="diag-meta-row">
              <span class="diag-name">{{ inj.name }}</span>
              <span class="diag-count mono-val">{{ inj.count }} players</span>
            </div>
            <div class="health-meter-track">
              <div 
                class="health-meter-fill"
                :style="{
                  width: `${(inj.count / maxCount) * 100}%`,
                  background: 'linear-gradient(90deg, #38bdf8, #818cf8)'
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Row: Positional Impact Breakdown -->
    <div class="glass-panel position-impact-card">
      <div class="card-header">
        <div class="header-icon-wrap violet">
          <PieChart :size="20" />
        </div>
        <div>
          <h3 class="card-title">Positional Group Vulnerability Index</h3>
          <p class="card-sub">Injury counts and lost starters by NFL unit</p>
        </div>
      </div>

      <div class="positions-grid">
        <div 
          v-for="pos in positionImpact" 
          :key="pos.group"
          class="position-card"
        >
          <div class="pos-top">
            <span class="pos-group-tag mono-val">{{ pos.group }}</span>
            <span class="pos-missed-count mono-val text-rose">{{ pos.missed }} Missed</span>
          </div>
          <div class="pos-substats">
            <span>{{ pos.total }} total on report</span>
            <span>•</span>
            <span class="text-amber font-bold">{{ pos.starters }} starters</span>
          </div>
          <div class="health-meter-track">
            <div 
              class="health-meter-fill"
              :style="{
                width: `${Math.min(100, (pos.missed / 20) * 100)}%`,
                background: pos.starters > 5 ? 'linear-gradient(90deg, #f43f5e, #fb7185)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)'
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
  gap: 1.5rem;
}

.two-col-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 950px) {
  .two-col-grid {
    grid-template-columns: 1fr;
  }
}

.surface-card, .diagnoses-card, .position-impact-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.header-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon-wrap.emerald {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: var(--accent-emerald);
}

.header-icon-wrap.rose {
  background: rgba(244, 63, 94, 0.15);
  border: 1px solid rgba(244, 63, 94, 0.3);
  color: var(--accent-rose);
}

.header-icon-wrap.violet {
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: var(--accent-violet);
}

.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #ffffff;
}

.card-sub {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.surface-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (max-width: 600px) {
  .surface-cards-grid {
    grid-template-columns: 1fr;
  }
}

.surface-box {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.surface-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.surface-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: #ffffff;
}

.surface-badge {
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.08);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-pill);
  color: var(--text-secondary);
}

.surface-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  text-align: center;
}

.surf-stat {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 800;
}

.stat-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
}

.surface-insight-callout {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: rgba(56, 189, 248, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

.flex-shrink-0 {
  flex-shrink: 0;
  margin-top: 2px;
}

/* Diagnoses list */
.diagnoses-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.diag-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.diag-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.82rem;
}

.diag-name {
  font-weight: 600;
  color: #ffffff;
}

.diag-count {
  font-weight: 700;
  color: var(--text-secondary);
}

/* Positions grid */
.positions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
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

.position-card {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pos-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pos-group-tag {
  font-size: 0.9rem;
  font-weight: 800;
  color: #ffffff;
}

.pos-missed-count {
  font-size: 0.82rem;
  font-weight: 700;
}

.pos-substats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
