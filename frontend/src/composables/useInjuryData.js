import { ref, computed } from 'vue'
import Papa from 'papaparse'
import { getTeam, getHealthGrade } from '../data/nflTeams'

// Singleton state across components
const isLoading = ref(true)
const loadingMessage = ref('Loading NFL injury records...')
const error = ref(null)

const gameHealthScores = ref([])
const teamWeeklySummaries = ref([])
const playerInjuries = ref([])

const selectedWeek = ref(7) // default to latest available week
const selectedTeam = ref('SF') // default featured team
const selectedView = ref('overview')

// CSV File loader helper with fallback
async function fetchAndParseCsv(fileName) {
  // Try both /api/csv/ (Vite dev middleware) and /data/ (static public)
  const paths = [`/api/csv/${fileName}`, `/data/${fileName}`]
  let text = null
  let lastErr = null

  for (const p of paths) {
    try {
      const res = await fetch(p, { cache: 'no-cache' })
      if (res.ok) {
        text = await res.text()
        break
      }
    } catch (e) {
      lastErr = e
    }
  }

  if (!text) {
    throw new Error(`Failed to load ${fileName}: ${lastErr?.message || 'File not found'}`)
  }

  return new Promise((resolve, reject) => {
    Papa.parse(text, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => resolve(results.data),
      error: (err) => reject(err)
    })
  })
}

export function useInjuryData() {
  async function loadData(force = false) {
    if (!force && gameHealthScores.value.length > 0) return

    isLoading.value = true
    error.value = null

    try {
      loadingMessage.value = 'Ingesting game healthiness scores...'
      const games = await fetchAndParseCsv('team_game_healthiness_scores_2026.csv')

      loadingMessage.value = 'Ingesting team weekly summaries...'
      const summaries = await fetchAndParseCsv('team_injury_weekly_summary_2026.csv')

      loadingMessage.value = 'Ingesting 4,600+ player injury and missed game records...'
      const players = await fetchAndParseCsv('nfl_injuries_and_missed_games_2026.csv')

      gameHealthScores.value = games
      teamWeeklySummaries.value = summaries
      playerInjuries.value = players

      // Set default selected week to max available week
      const weeks = [...new Set(games.map(g => Number(g.week)).filter(Boolean))].sort((a, b) => a - b)
      if (weeks.length > 0) {
        selectedWeek.value = weeks[weeks.length - 1]
      }
    } catch (err) {
      console.error('Error loading injury data:', err)
      error.value = err.message || 'Failed to load NFL injury data'
    } finally {
      isLoading.value = false
    }
  }

  // Available weeks
  const availableWeeks = computed(() => {
    const weeks = [...new Set(gameHealthScores.value.map(g => Number(g.week)).filter(Boolean))]
    return weeks.sort((a, b) => a - b)
  })

  const latestWeek = computed(() => {
    return availableWeeks.value.length > 0 ? availableWeeks.value[availableWeeks.value.length - 1] : 7
  })

  // Available teams
  const availableTeams = computed(() => {
    const set = new Set()
    for (const g of gameHealthScores.value) {
      if (g.team) set.add(String(g.team).trim().toUpperCase())
    }
    return [...set].sort()
  })

  // Game scores for currently selected week
  const currentWeekGameScores = computed(() => {
    if (selectedWeek.value === 'all') return gameHealthScores.value
    return gameHealthScores.value.filter(g => Number(g.week) === Number(selectedWeek.value))
  })

  // Team power rankings (sorted by health score)
  const teamPowerRankings = computed(() => {
    const weekScores = currentWeekGameScores.value
    // If 'all', average per team
    const teamMap = new Map()

    for (const row of weekScores) {
      const t = String(row.team).trim().toUpperCase()
      if (!teamMap.has(t)) {
        teamMap.set(t, {
          team: t,
          info: getTeam(t),
          scores: [],
          startersOut: 0,
          startersQ: 0,
          gamesMissed: 0,
          qbStatus: row.qb_status || 'Healthy',
          qbNameOut: row.qb_name_out || null,
          keyMissing: row.key_missing_starters || '',
          surface: row.surface || 'grass',
          qbUnit: row.qb_unit_health ?? 100,
          olUnit: row.ol_unit_health ?? 100,
          skillUnit: row.skill_unit_health ?? 100,
          frontUnit: row.front_unit_health ?? 100,
          secUnit: row.secondary_unit_health ?? 100
        })
      }
      const item = teamMap.get(t)
      if (typeof row.health_score === 'number') {
        item.scores.push(row.health_score)
      }
      item.startersOut = Math.max(item.startersOut, Number(row.starters_out_count) || 0)
      item.startersQ = Math.max(item.startersQ, Number(row.starters_questionable_count) || 0)
      item.gamesMissed = Math.max(item.gamesMissed, Number(row.total_games_missed) || 0)
      if (row.qb_status && row.qb_status !== 'Healthy') {
        item.qbStatus = row.qb_status
        item.qbNameOut = row.qb_name_out
      }
    }

    const list = []
    for (const [t, data] of teamMap.entries()) {
      const avgScore = data.scores.length > 0
        ? data.scores.reduce((a, b) => a + b, 0) / data.scores.length
        : 100
      const rounded = Number(avgScore.toFixed(1))
      list.push({
        ...data,
        healthScore: rounded,
        grade: getHealthGrade(rounded)
      })
    }

    list.sort((a, b) => b.healthScore - a.healthScore)
    return list.map((item, idx) => ({ ...item, rank: idx + 1 }))
  })

  // Matchups for current week (grouped by game_id)
  const weekMatchups = computed(() => {
    const scores = currentWeekGameScores.value
    const gameMap = new Map()

    for (const row of scores) {
      const gid = row.game_id || `${row.season}_${row.week}_${row.team}_${row.opponent}`
      if (!gameMap.has(gid)) {
        gameMap.set(gid, {
          gameId: gid,
          week: row.week,
          gameDate: row.game_date,
          surface: row.surface || 'grass',
          homeTeam: null,
          awayTeam: null,
          netAdvantage: 0
        })
      }
      const g = gameMap.get(gid)
      const isHome = row.is_home === true || row.is_home === 'True' || row.is_home === 1

      const entry = {
        team: row.team,
        info: getTeam(row.team),
        healthScore: Number(Number(row.health_score || 100).toFixed(1)),
        grade: getHealthGrade(row.health_score || 100),
        qbStatus: row.qb_status || 'Healthy',
        qbNameOut: row.qb_name_out || null,
        startersOutCount: row.starters_out_count || 0,
        startersQCount: row.starters_questionable_count || 0,
        keyMissing: (row.key_missing_starters || '').split(',').map(s => s.trim()).filter(Boolean),
        questionableStarters: (row.questionable_starters || '').split(',').map(s => s.trim()).filter(Boolean),
        units: {
          qb: row.qb_unit_health ?? 100,
          ol: row.ol_unit_health ?? 100,
          skill: row.skill_unit_health ?? 100,
          front: row.front_unit_health ?? 100,
          secondary: row.secondary_unit_health ?? 100
        },
        netHealthAdvantage: Number(Number(row.net_health_advantage || 0).toFixed(1))
      }

      if (isHome) {
        g.homeTeam = entry
      } else {
        g.awayTeam = entry
      }
    }

    return Array.from(gameMap.values()).map(match => {
      // If one team was missing home flag, ensure both filled
      if (!match.homeTeam && match.awayTeam) match.homeTeam = match.awayTeam
      if (!match.awayTeam && match.homeTeam) match.awayTeam = match.homeTeam

      const homeScore = match.homeTeam?.healthScore ?? 100
      const awayScore = match.awayTeam?.healthScore ?? 100
      const diff = Number((homeScore - awayScore).toFixed(1))

      return {
        ...match,
        homeAdvantage: diff,
        favoriteTeam: diff > 0 ? match.homeTeam?.team : (diff < 0 ? match.awayTeam?.team : 'EVEN'),
        absAdvantage: Math.abs(diff)
      }
    })
  })

  // Executive League KPI metrics
  const leagueMetrics = computed(() => {
    const pList = selectedWeek.value === 'all'
      ? playerInjuries.value
      : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))

    const rankings = teamPowerRankings.value
    if (rankings.length === 0) {
      return {
        avgScore: 0,
        totalMissed: 0,
        startersOut: 0,
        qbInjuries: 0,
        healthiestTeam: null,
        mostInjuredTeam: null
      }
    }

    const avgScore = Number((rankings.reduce((acc, t) => acc + t.healthScore, 0) / rankings.length).toFixed(1))
    const totalMissed = pList.filter(p => p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1).length
    const startersOut = pList.filter(p => (p.is_starter === true || p.is_starter === 'True' || p.is_starter === 1) && (p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1)).length
    const qbInjuries = pList.filter(p => p.position_group === 'QB' && (p.game_missed || p.report_status)).length

    return {
      avgScore,
      avgGrade: getHealthGrade(avgScore),
      totalMissed,
      startersOut,
      qbInjuries,
      healthiestTeam: rankings[0],
      mostInjuredTeam: rankings[rankings.length - 1],
      totalPlayersLogged: pList.length
    }
  })

  // Diagnostics distribution (top primary injury body parts)
  const injuryDiagnostics = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value
      : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))

    const counts = {}
    for (const p of list) {
      const inj = (p.primary_injury || 'Undisclosed').trim()
      // Filter out resting/non-injury
      if (inj.toLowerCase().includes('not injury') || inj.toLowerCase().includes('resting')) continue
      counts[inj] = (counts[inj] || 0) + 1
    }

    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
  })

  // Position group distribution
  const positionImpact = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value
      : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))

    const counts = {}
    for (const p of list) {
      const pos = (p.position_group || 'OTHER').trim().toUpperCase()
      if (!counts[pos]) counts[pos] = { total: 0, missed: 0, starters: 0 }
      counts[pos].total++
      if (p.game_missed === true || p.game_missed === 'True' || p.game_missed === 1) {
        counts[pos].missed++
      }
      if (p.is_starter === true || p.is_starter === 'True' || p.is_starter === 1) {
        counts[pos].starters++
      }
    }

    return Object.entries(counts)
      .map(([group, data]) => ({ group, ...data }))
      .sort((a, b) => b.missed - a.missed)
  })

  // Surface breakdown (Turf vs Grass)
  const surfaceAnalysis = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value
      : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))

    const surfMap = {}
    for (const p of list) {
      let surf = (p.surface || 'Unknown').toLowerCase()
      if (surf.includes('turf') || surf.includes('fieldturf') || surf.includes('astroturf') || surf.includes('matrix')) {
        surf = 'Synthetic Turf'
      } else if (surf.includes('grass')) {
        surf = 'Natural Grass'
      } else {
        surf = 'Other / Dome'
      }

      if (!surfMap[surf]) surfMap[surf] = { total: 0, missed: 0, starters: 0, totalImpact: 0 }
      surfMap[surf].total++
      if (p.game_missed) surfMap[surf].missed++
      if (p.is_starter) surfMap[surf].starters++
      surfMap[surf].totalImpact += Number(p.health_impact_weight) || 0
    }

    return Object.entries(surfMap).map(([surface, data]) => ({
      surface,
      ...data,
      avgSeverity: data.total > 0 ? Number((data.totalImpact / data.total).toFixed(2)) : 0
    }))
  })

  // Team weekly trend (for selected team)
  const teamWeeklyTrend = computed(() => {
    if (!selectedTeam.value) return []
    const t = selectedTeam.value.toUpperCase()
    const records = gameHealthScores.value
      .filter(g => String(g.team).toUpperCase() === t)
      .sort((a, b) => Number(a.week) - Number(b.week))

    return records.map(r => ({
      week: Number(r.week),
      score: Number(r.health_score || 100),
      opponent: r.opponent,
      isHome: r.is_home,
      qbStatus: r.qb_status,
      startersOut: r.starters_out_count || 0,
      units: {
        qb: r.qb_unit_health ?? 100,
        ol: r.ol_unit_health ?? 100,
        skill: r.skill_unit_health ?? 100,
        front: r.front_unit_health ?? 100,
        secondary: r.secondary_unit_health ?? 100
      }
    }))
  })

  return {
    isLoading,
    loadingMessage,
    error,
    gameHealthScores,
    teamWeeklySummaries,
    playerInjuries,
    selectedWeek,
    selectedTeam,
    selectedView,
    availableWeeks,
    latestWeek,
    availableTeams,
    teamPowerRankings,
    weekMatchups,
    leagueMetrics,
    injuryDiagnostics,
    positionImpact,
    surfaceAnalysis,
    teamWeeklyTrend,
    loadData
  }
}
