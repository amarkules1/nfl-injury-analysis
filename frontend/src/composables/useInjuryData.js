import { ref, computed } from 'vue'
import Papa from 'papaparse'
import { getTeam, getHealthGrade, NFL_TEAMS } from '../data/nflTeams'

// Singleton state across components
const isLoading = ref(true)
const loadingMessage = ref('Loading NFL injury records...')
const error = ref(null)

// Selected Season (defaults to current year 2026)
const selectedSeason = ref(2026)
const availableSeasons = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013]

const gameHealthScores = ref([])
const teamWeeklySummaries = ref([])
const playerInjuries = ref([])

// ML Predictions and Upcoming Week Projections
const playerPredictions = ref([])
const upcomingTeamProjections = ref([])
const upcomingMatchupProjections = ref([])

const selectedWeek = ref(6) // default to latest completed week or 'upcoming'
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
      transform: (val) => {
        if (typeof val === 'string') {
          const lower = val.trim().toLowerCase()
          if (lower === 'true') return true
          if (lower === 'false') return false
        }
        return val
      },
      complete: (results) => resolve(results.data),
      error: (err) => reject(err)
    })
  })
}

// Optional CSV loader that returns [] gracefully if file doesn't exist
async function fetchAndParseCsvOptional(fileName) {
  try {
    return await fetchAndParseCsv(fileName)
  } catch (e) {
    return []
  }
}

export function useInjuryData() {
  async function loadData(force = false) {
    if (!force && gameHealthScores.value.length > 0) return

    isLoading.value = true
    error.value = null

    try {
      const s = selectedSeason.value
      loadingMessage.value = `Ingesting team health scores (${s})...`
      const games = await fetchAndParseCsv(`team_game_healthiness_scores_${s}.csv`)

      loadingMessage.value = `Ingesting weekly summaries (${s})...`
      const summaries = await fetchAndParseCsv(`team_injury_weekly_summary_${s}.csv`)

      loadingMessage.value = `Ingesting player injury logs (${s})...`
      const players = await fetchAndParseCsv(`nfl_injuries_and_missed_games_${s}.csv`)

      // Attempt loading ML predictions and projections for upcoming week
      const preds = await fetchAndParseCsvOptional(`player_play_predictions_${s}.csv`)
      const teamProjs = await fetchAndParseCsvOptional(`upcoming_team_health_projections_${s}.csv`)
      const matchProjs = await fetchAndParseCsvOptional(`upcoming_matchup_projections_${s}.csv`)

      gameHealthScores.value = games
      teamWeeklySummaries.value = summaries
      playerInjuries.value = players
      playerPredictions.value = preds
      upcomingTeamProjections.value = teamProjs
      upcomingMatchupProjections.value = matchProjs

      const allWeeks = [...new Set(games.map(g => Number(g.week)).filter(Boolean))].sort((a, b) => a - b)

      if (teamProjs.length > 0) {
        const uWeek = Number(teamProjs[0].week)
        const completedWeeks = allWeeks.filter(w => w < uWeek)
        if (selectedWeek.value === 'upcoming') {
          // stay on upcoming
        } else if (completedWeeks.length > 0) {
          selectedWeek.value = completedWeeks[completedWeeks.length - 1]
        } else {
          selectedWeek.value = 'upcoming'
        }
      } else {
        if (allWeeks.length > 0) {
          selectedWeek.value = allWeeks[allWeeks.length - 1]
        }
      }
    } catch (err) {
      console.error('Error loading injury data:', err)
      error.value = err.message || 'Failed to load NFL injury data'
    } finally {
      isLoading.value = false
    }
  }

  async function setSeason(newSeason) {
    if (selectedSeason.value === newSeason) return
    selectedSeason.value = newSeason
    await loadData(true)
  }

  // Upcoming week number if model predictions are present
  const upcomingWeek = computed(() => {
    if (upcomingTeamProjections.value.length > 0) {
      return Number(upcomingTeamProjections.value[0].week)
    }
    return null
  })

  const hasUpcomingProjections = computed(() => {
    return upcomingTeamProjections.value.length > 0
  })

  const isUpcomingSelected = computed(() => {
    return selectedWeek.value === 'upcoming'
  })

  // Available completed weeks
  const availableWeeks = computed(() => {
    const allWeeks = [...new Set(gameHealthScores.value.map(g => Number(g.week)).filter(Boolean))].sort((a, b) => a - b)
    if (hasUpcomingProjections.value && upcomingWeek.value) {
      return allWeeks.filter(w => w < upcomingWeek.value)
    }
    return allWeeks
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
    if (selectedWeek.value === 'upcoming') {
      return []
    }
    return gameHealthScores.value.filter(g => Number(g.week) === Number(selectedWeek.value))
  })

  // Complete 32-Team Power Rankings (supporting both Completed Weeks and Upcoming Week Model Projections)
  const teamPowerRankings = computed(() => {
    const all32 = Object.keys(NFL_TEAMS)

    // A. Model Projections for Upcoming Week
    if (isUpcomingSelected.value && upcomingTeamProjections.value.length > 0) {
      const projMap = new Map()
      for (const p of upcomingTeamProjections.value) {
        projMap.set(String(p.team).trim().toUpperCase(), p)
      }

      const list = all32.map(teamAbbr => {
        const info = getTeam(teamAbbr)
        const proj = projMap.get(teamAbbr)
        const score = proj ? Number(Number(proj.projected_health_score).toFixed(1)) : 85.0
        const grade = getHealthGrade(score)

        return {
          team: teamAbbr,
          info,
          healthScore: score,
          grade,
          isBye: !proj,
          byeWeek: null,
          isUpcoming: true,
          startersOut: 0,
          startersQ: 0,
          gamesMissed: 0,
          qbStatus: 'Projected',
          qbNameOut: null,
          keyMissing: proj?.key_missing_starters || '',
          swingPlayers: proj?.swing_players || '',
          surface: 'grass',
          qbUnit: proj?.qb_unit_health ?? 100,
          olUnit: proj?.ol_unit_health ?? 100,
          skillUnit: proj?.skill_unit_health ?? 100,
          frontUnit: proj?.front_unit_health ?? 100,
          secUnit: proj?.secondary_unit_health ?? 100
        }
      })

      list.sort((a, b) => b.healthScore - a.healthScore)
      return list.map((item, idx) => ({ ...item, rank: idx + 1 }))
    }

    // B. Completed Weeks (Historical Actuals)
    const isAllWeeks = selectedWeek.value === 'all'
    const curWeekNum = Number(selectedWeek.value)

    const list = all32.map(teamAbbr => {
      const info = getTeam(teamAbbr)
      const allTeamGames = gameHealthScores.value
        .filter(g => String(g.team).trim().toUpperCase() === teamAbbr)
        .sort((a, b) => Number(a.week) - Number(b.week))

      if (isAllWeeks) {
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
          isUpcoming: false,
          startersOut: Number(latest.starters_out_count) || 0,
          startersQ: Number(latest.starters_questionable_count) || 0,
          gamesMissed: Number(latest.total_games_missed) || 0,
          qbStatus: latest.qb_status || 'Healthy',
          qbNameOut: latest.qb_name_out || null,
          keyMissing: latest.key_missing_starters || '',
          swingPlayers: '',
          surface: latest.surface || 'grass',
          qbUnit: latest.qb_unit_health ?? 100,
          olUnit: latest.ol_unit_health ?? 100,
          skillUnit: latest.skill_unit_health ?? 100,
          frontUnit: latest.front_unit_health ?? 100,
          secUnit: latest.secondary_unit_health ?? 100
        }
      }

      // Single week match
      const gameThisWeek = allTeamGames.find(g => Number(g.week) === curWeekNum)

      if (gameThisWeek) {
        const score = Number(Number(gameThisWeek.health_score || 100).toFixed(1))
        return {
          team: teamAbbr,
          info,
          healthScore: score,
          grade: getHealthGrade(score),
          isBye: false,
          byeWeek: null,
          isUpcoming: false,
          startersOut: Number(gameThisWeek.starters_out_count) || 0,
          startersQ: Number(gameThisWeek.starters_questionable_count) || 0,
          gamesMissed: Number(gameThisWeek.total_games_missed) || 0,
          qbStatus: gameThisWeek.qb_status || 'Healthy',
          qbNameOut: gameThisWeek.qb_name_out || null,
          keyMissing: gameThisWeek.key_missing_starters || '',
          swingPlayers: '',
          surface: gameThisWeek.surface || 'grass',
          qbUnit: gameThisWeek.qb_unit_health ?? 100,
          olUnit: gameThisWeek.ol_unit_health ?? 100,
          skillUnit: gameThisWeek.skill_unit_health ?? 100,
          frontUnit: gameThisWeek.front_unit_health ?? 100,
          secUnit: gameThisWeek.secondary_unit_health ?? 100
        }
      } else {
        // Bye week carry-forward
        const priorGames = allTeamGames
          .filter(g => Number(g.week) < curWeekNum)
          .sort((a, b) => Number(b.week) - Number(a.week))

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
          isUpcoming: false,
          startersOut: Number(prevGame.starters_out_count) || 0,
          startersQ: Number(prevGame.starters_questionable_count) || 0,
          gamesMissed: Number(prevGame.total_games_missed) || 0,
          qbStatus: prevGame.qb_status || 'Healthy',
          qbNameOut: prevGame.qb_name_out || null,
          keyMissing: prevGame.key_missing_starters || '',
          swingPlayers: '',
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

  // Matchups for current week or upcoming week
  const weekMatchups = computed(() => {
    // A. Upcoming Week Matchups (Model Projections)
    if (isUpcomingSelected.value && upcomingMatchupProjections.value.length > 0) {
      return upcomingMatchupProjections.value.map(m => {
        const homeScore = Number(Number(m.home_projected_health).toFixed(1))
        const awayScore = Number(Number(m.away_projected_health).toFixed(1))
        const diff = Number(Number(m.net_health_advantage).toFixed(1))
        const fav = diff > 0 ? m.home_team : (diff < 0 ? m.away_team : 'EVEN')

        return {
          gameId: m.game_id,
          week: m.week,
          gameDate: m.game_date || `Week ${m.week}`,
          surface: m.surface || 'grass',
          isUpcoming: true,
          homeTeam: {
            team: m.home_team,
            info: getTeam(m.home_team),
            healthScore: homeScore,
            grade: getHealthGrade(homeScore),
            qbStatus: 'Projected',
            qbNameOut: null,
            startersOutCount: 0,
            startersQCount: 0,
            keyMissing: (m.home_missing_starters || '').split(';').map(s => s.trim()).filter(Boolean),
            swingPlayers: (m.home_swing_players || '').split(';').map(s => s.trim()).filter(Boolean),
            questionableStarters: (m.home_swing_players || '').split(';').map(s => s.trim()).filter(Boolean),
            units: { qb: 85, ol: 85, skill: 85, front: 85, secondary: 85 },
            netHealthAdvantage: diff
          },
          awayTeam: {
            team: m.away_team,
            info: getTeam(m.away_team),
            healthScore: awayScore,
            grade: getHealthGrade(awayScore),
            qbStatus: 'Projected',
            qbNameOut: null,
            startersOutCount: 0,
            startersQCount: 0,
            keyMissing: (m.away_missing_starters || '').split(';').map(s => s.trim()).filter(Boolean),
            swingPlayers: (m.away_swing_players || '').split(';').map(s => s.trim()).filter(Boolean),
            questionableStarters: (m.away_swing_players || '').split(';').map(s => s.trim()).filter(Boolean),
            units: { qb: 85, ol: 85, skill: 85, front: 85, secondary: 85 },
            netHealthAdvantage: -diff
          },
          homeAdvantage: diff,
          favoriteTeam: fav,
          absAdvantage: Math.abs(diff)
        }
      })
    }

    // B. Completed Weeks Matchups
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
          isUpcoming: false,
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
        swingPlayers: [],
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
      : (selectedWeek.value === 'upcoming'
          ? playerInjuries.value.filter(p => Number(p.week) === upcomingWeek.value)
          : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value)))

    const totalTracked = pList.length
    const totalMissed = pList.filter(p => p.game_missed).length
    const startersMissed = pList.filter(p => p.game_missed && p.is_starter).length

    const injuryMissed = pList.filter(p => 
      p.game_missed && 
      p.missed_reason_category && 
      !['HEALTHY_INACTIVE', 'SUSPENSION', 'REST_PERSONAL'].includes(p.missed_reason_category)
    ).length

    const currentRankings = teamPowerRankings.value
    const scores = currentRankings.map(t => t.healthScore)
    const leagueAverage = scores.length > 0 ? Number((scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)) : 80.0

    return {
      totalTracked,
      totalMissed,
      startersMissed,
      injuryMissed,
      healthyScratches: totalMissed - injuryMissed,
      leagueAverageHealth: leagueAverage,
      avgScore: leagueAverage,
      healthiestTeam: currentRankings[0] || null,
      mostDepletedTeam: currentRankings[currentRankings.length - 1] || null,
      mostInjuredTeam: currentRankings[currentRankings.length - 1] || null
    }
  })

  // Top Diagnosed Injuries
  const injuryDiagnostics = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value.filter(p => availableWeeks.value.includes(Number(p.week)))
      : (selectedWeek.value === 'upcoming'
          ? playerInjuries.value.filter(p => Number(p.week) === upcomingWeek.value)
          : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value)))

    const counts = {}
    for (const p of list) {
      const inj = p.primary_injury
      if (inj && !['Not injury related', 'Undisclosed / Reserve'].includes(inj)) {
        counts[inj] = (counts[inj] || 0) + 1
      }
    }

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, count]) => ({ name, count }))
  })

  // Positional Impact Distribution
  const positionImpact = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value.filter(p => availableWeeks.value.includes(Number(p.week)))
      : (selectedWeek.value === 'upcoming'
          ? playerInjuries.value.filter(p => Number(p.week) === upcomingWeek.value)
          : playerInjuries.value.filter(p => Number(p.week) === Number(selectedWeek.value)))

    const posMap = {}
    for (const p of list) {
      const grp = p.position_group || 'OTHER'
      if (!posMap[grp]) posMap[grp] = { total: 0, missed: 0, starters: 0 }
      posMap[grp].total++
      if (p.game_missed) posMap[grp].missed++
      if (p.is_starter) posMap[grp].starters++
    }

    return Object.entries(posMap)
      .map(([group, data]) => ({ group, ...data }))
      .sort((a, b) => b.missed - a.missed)
  })

  // Surface Health Impact
  const surfaceAnalysis = computed(() => {
    const list = selectedWeek.value === 'all'
      ? playerInjuries.value.filter(p => availableWeeks.value.includes(Number(p.week)))
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
        // Bye week: carry forward previous week score and units
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

  // Player Play Probability Predictions for Featured Team in Upcoming Week
  const upcomingPlayerPredictionsForSelectedTeam = computed(() => {
    if (!selectedTeam.value || playerPredictions.value.length === 0) return []
    const t = selectedTeam.value.toUpperCase()
    const targetW = upcomingWeek.value

    const list = playerPredictions.value.filter(p => {
      const matchT = String(p.team).trim().toUpperCase() === t
      const matchW = targetW ? Number(p.week) === targetW : true
      return matchT && matchW
    })

    // Sort: starters first, then lowest probability (most uncertain / swing players first)
    list.sort((a, b) => {
      if (a.is_starter !== b.is_starter) return b.is_starter ? 1 : -1
      return Number(a.play_probability) - Number(b.play_probability)
    })
    return list
  })

  return {
    isLoading,
    loadingMessage,
    error,
    selectedSeason,
    availableSeasons,
    setSeason,
    gameHealthScores,
    teamWeeklySummaries,
    playerInjuries,
    playerPredictions,
    upcomingTeamProjections,
    upcomingMatchupProjections,
    upcomingWeek,
    hasUpcomingProjections,
    isUpcomingSelected,
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
    upcomingPlayerPredictionsForSelectedTeam,
    loadData
  }
}
