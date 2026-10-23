import { ref, computed } from 'vue'
import Papa from 'papaparse'
import { getTeam, getHealthGrade, NFL_TEAMS } from '../data/nflTeams'

// Singleton state across components
const isLoading = ref(true)
const loadingMessage = ref('Loading NFL injury records...')
const error = ref(null)

const gameHealthScores = ref([])
const teamWeeklySummaries = ref([])
const playerInjuries = ref([])

const selectedWeek = ref(6) // default to latest completed week (hide current week)
const selectedTeam = ref('SF') // default featured team
const selectedView = ref('overview')

// CSV File loader helper with fallback
async function fetchAndParseCsv(fileName) {
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
      loadingMessage.value = 'Ingesting team health scores...'
      const games = await fetchAndParseCsv('team_game_healthiness_scores_2026.csv')

      loadingMessage.value = 'Ingesting weekly summaries...'
      const summaries = await fetchAndParseCsv('team_injury_weekly_summary_2026.csv')

      loadingMessage.value = 'Ingesting player injury logs...'
      const players = await fetchAndParseCsv('nfl_injuries_and_missed_games_2026.csv')

      gameHealthScores.value = games
      teamWeeklySummaries.value = summaries
      playerInjuries.value = players

      const allWeeks = [...new Set(games.map(g => Number(g.week)).filter(Boolean))].sort((a, b) => a - b)
      // Hide current week where games haven't happened yet (latest week in data)
      const maxWeek = allWeeks.length > 0 ? allWeeks[allWeeks.length - 1] : 7
      const completedWeeks = allWeeks.filter(w => w < maxWeek)
      if (completedWeeks.length > 0) {
        selectedWeek.value = completedWeeks[completedWeeks.length - 1]
      }
    } catch (err) {
      console.error('Error loading injury data:', err)
      error.value = err.message || 'Failed to load NFL injury data'
    } finally {
      isLoading.value = false
    }
  }

  // Available completed weeks (hides current week where games haven't happened yet)
  const availableWeeks = computed(() => {
    const allWeeks = [...new Set(gameHealthScores.value.map(g => Number(g.week)).filter(Boolean))].sort((a, b) => a - b)
    if (allWeeks.length <= 1) return allWeeks
    const maxWeek = allWeeks[allWeeks.length - 1]
    return allWeeks.filter(w => w < maxWeek)
  })

  const latestWeek = computed(() => {
    return availableWeeks.value.length > 0 ? availableWeeks.value[availableWeeks.value.length - 1] : 6
  })

  // All 32 NFL Teams always available
  const availableTeams = computed(() => {
    return Object.keys(NFL_TEAMS).sort()
  })

  // Game scores for currently selected week
  const currentWeekGameScores = computed(() => {
    if (selectedWeek.value === 'all') {
      return gameHealthScores.value.filter(g => availableWeeks.value.includes(Number(g.week)))
    }
    return gameHealthScores.value.filter(g => Number(g.week) === Number(selectedWeek.value))
  })

  // Complete 32-Team Power Rankings with strict prior-week carry-forward on bye weeks
  const teamPowerRankings = computed(() => {
    const all32 = Object.keys(NFL_TEAMS)
    const isAllWeeks = selectedWeek.value === 'all'
    const curWeekNum = Number(selectedWeek.value)

    const list = all32.map(teamAbbr => {
      const info = getTeam(teamAbbr)
      const allTeamGames = gameHealthScores.value
        .filter(g => String(g.team).trim().toUpperCase() === teamAbbr)
        .sort((a, b) => Number(a.week) - Number(b.week))

      if (isAllWeeks) {
        // Average over completed season weeks (hide current week)
        const completedTeamGames = allTeamGames.filter(g => availableWeeks.value.includes(Number(g.week)))
        const validScores = completedTeamGames.map(g => Number(g.health_score)).filter(s => !isNaN(s))
        const avgScore = validScores.length > 0
          ? validScores.reduce((a, b) => a + b, 0) / validScores.length
          : 100
        const latest = completedTeamGames[completedTeamGames.length - 1] || {}
        const rounded = Number(avgScore.toFixed(1))

        return {
          team: teamAbbr,
          info,
          healthScore: rounded,
          grade: getHealthGrade(rounded),
          isBye: false,
          byeWeek: null,
          carriedFromWeek: null,
          startersOut: latest.starters_out_count || 0,
          startersQ: latest.starters_questionable_count || 0,
          gamesMissed: latest.total_games_missed || 0,
          qbStatus: latest.qb_status || 'Healthy',
          qbNameOut: latest.qb_name_out || null,
          keyMissing: latest.key_missing_starters || '',
          surface: latest.surface || 'grass',
          qbUnit: latest.qb_unit_health ?? 100,
          olUnit: latest.ol_unit_health ?? 100,
          skillUnit: latest.skill_unit_health ?? 100,
          frontUnit: latest.front_unit_health ?? 100,
          secUnit: latest.secondary_unit_health ?? 100
        }
      }

      // Specific week selected
      const weekGame = allTeamGames.find(g => Number(g.week) === curWeekNum)

      if (weekGame) {
        // Team played this week
        const score = Number(Number(weekGame.health_score || 100).toFixed(1))
        return {
          team: teamAbbr,
          info,
          healthScore: score,
          grade: getHealthGrade(score),
          isBye: false,
          byeWeek: null,
          carriedFromWeek: null,
          startersOut: Number(weekGame.starters_out_count) || 0,
          startersQ: Number(weekGame.starters_questionable_count) || 0,
          gamesMissed: Number(weekGame.total_games_missed) || 0,
          qbStatus: weekGame.qb_status || 'Healthy',
          qbNameOut: weekGame.qb_name_out || null,
          keyMissing: weekGame.key_missing_starters || '',
          surface: weekGame.surface || 'grass',
          qbUnit: weekGame.qb_unit_health ?? 100,
          olUnit: weekGame.ol_unit_health ?? 100,
          skillUnit: weekGame.skill_unit_health ?? 100,
          frontUnit: weekGame.front_unit_health ?? 100,
          secUnit: weekGame.secondary_unit_health ?? 100
        }
      } else {
        // Team is on BYE in this week!
        // Factor in bye weeks: strictly use their team ratings from the PREVIOUS played week!
        const priorGames = allTeamGames
          .filter(g => Number(g.week) < curWeekNum)
          .sort((a, b) => Number(b.week) - Number(a.week))

        // Preceding game (e.g. Week 5 for Week 6 DET)
        const prevGame = priorGames[0] || allTeamGames[0] || {}
        const prevScore = Number(Number(prevGame.health_score || 100).toFixed(1))
        const prevWeekNum = prevGame.week ? Number(prevGame.week) : curWeekNum - 1

        return {
          team: teamAbbr,
          info,
          healthScore: prevScore,
          grade: getHealthGrade(prevScore),
          isBye: true,
          byeWeek: curWeekNum,
          carriedFromWeek: prevWeekNum,
          startersOut: Number(prevGame.starters_out_count) || 0,
          startersQ: Number(prevGame.starters_questionable_count) || 0,
          gamesMissed: Number(prevGame.total_games_missed) || 0,
          qbStatus: prevGame.qb_status || 'Healthy',
          qbNameOut: prevGame.qb_name_out || null,
          keyMissing: prevGame.key_missing_starters || '',
          surface: prevGame.surface || 'grass',
          qbUnit: prevGame.qb_unit_health ?? 100,
          olUnit: prevGame.ol_unit_health ?? 100,
          skillUnit: prevGame.skill_unit_health ?? 100,
          frontUnit: prevGame.front_unit_health ?? 100,
          secUnit: prevGame.secondary_unit_health ?? 100
        }
      }
    })

    list.sort((a, b) => b.healthScore - a.healthScore)
    return list.map((item, idx) => ({ ...item, rank: idx + 1 }))
  })

  // Matchups for current week
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
        keyMissing: (row.key_missing_starters || '').split(';').map(s => s.trim()).filter(Boolean),
        questionableStarters: (row.questionable_starters || '').split(';').map(s => s.trim()).filter(Boolean),
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
      ? playerInjuries.value.filter(p => availableWeeks.value.includes(Number(p.week)))
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
    const qbInjuries = rankings.filter(t => t.qbStatus !== 'Healthy').length

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

  // Diagnostics distribution
  const injuryDiagnostics = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value
      : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value))

    const counts = {}
    for (const p of list) {
      const inj = (p.primary_injury || 'Undisclosed').trim()
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

  // Surface breakdown
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

  // Team weekly trend (incorporating bye weeks seamlessly)
  const teamWeeklyTrend = computed(() => {
    if (!selectedTeam.value) return []
    const t = selectedTeam.value.toUpperCase()
    const allTeamGames = gameHealthScores.value
      .filter(g => String(g.team).toUpperCase() === t)
      .sort((a, b) => Number(a.week) - Number(b.week))

    const weeks = availableWeeks.value
    let lastKnownScore = 100
    let lastKnownUnits = { qb: 100, ol: 100, skill: 100, front: 100, secondary: 100 }
    let lastKnownStartersOut = 0
    let lastKnownQbStatus = 'Healthy'

    return weeks.map(w => {
      const match = allTeamGames.find(g => Number(g.week) === w)
      if (match) {
        lastKnownScore = Number(Number(match.health_score || 100).toFixed(1))
        lastKnownUnits = {
          qb: match.qb_unit_health ?? 100,
          ol: match.ol_unit_health ?? 100,
          skill: match.skill_unit_health ?? 100,
          front: match.front_unit_health ?? 100,
          secondary: match.secondary_unit_health ?? 100
        }
        lastKnownStartersOut = match.starters_out_count || 0
        lastKnownQbStatus = match.qb_status || 'Healthy'

        return {
          week: w,
          score: lastKnownScore,
          opponent: match.opponent,
          isHome: match.is_home,
          isBye: false,
          qbStatus: lastKnownQbStatus,
          startersOut: lastKnownStartersOut,
          units: { ...lastKnownUnits }
        }
      } else {
        // Bye week: carry forward previous week score and units!
        return {
          week: w,
          score: lastKnownScore,
          opponent: 'BYE',
          isHome: false,
          isBye: true,
          qbStatus: lastKnownQbStatus,
          startersOut: lastKnownStartersOut,
          units: { ...lastKnownUnits }
        }
      }
    })
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
