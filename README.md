# NFL Injury & Missed Games Analysis

A Python and Pandas pipeline designed to log, categorize, and analyze all NFL player injuries and games missed (IR, PUP, NFI, Inactives, Suspensions, Exempt list, and Healthy Scratches) across every week of the NFL season.

This project feeds directly into team "healthiness" index models, allowing game-by-game injury impact scoring and matchup health comparisons.

---

## Features

- **Automated Weekly Ingestion**: Automatically pulls official NFL weekly injury reports, weekly rosters, schedules, and snap counts from the automated `nflverse` data ecosystem.
- **Injury Carry-Forward**: In the NFL, players placed on Injured Reserve (IR) or PUP do not receive daily practice injury reports. This pipeline automatically carries forward each player's diagnosed body part (e.g. Knee, Hamstring, Ankle, Achilles) across all subsequent weeks on IR.
- **Granular Missed Game Categorization**:
  - `INJURY_IR`: Reserve / Injured (`R01`, `R48`)
  - `INJURY_PUP`: Physically Unable to Perform (`R04`, `R49`)
  - `INJURY_NFI_NFIL`: Non-Football Injury or Illness (`R05`, `R27`, `R47`)
  - `INJURY_RULED_OUT`: Officially ruled Out on game injury report
  - `INJURY_INACTIVE`: Gameday Inactive (`INA`) with injury report designation
  - `HEALTHY_SCRATCH`: Gameday Inactive (`INA`) with no injury designation (coach's decision)
  - `SUSPENSION`: League or club disciplinary suspensions (`R40`, `R30`, `R33`)
  - `COMMISSIONER_EXEMPT`: Commissioner's Exempt List (`EXE`, `E02`)
  - `REST_OR_PERSONAL`: Veteran rest or personal excused absences
  - `INJURED_PLAYED_QUESTIONABLE`: On injury report as Questionable, active/playing hurt
  - `INJURED_PLAYED_DOUBTFUL`: On injury report as Doubtful, active/playing hurt
  - `INJURED_PLAYED_PRACTICE_ONLY`: Monitored on practice injury report, active for game
- **Starter Identification**: Merges official depth charts and in-game snap counts (offense & defense snap percentages) to highlight lost starters vs. depth players.
- **Game Healthiness Scoring**: Includes a built-in scoring engine (`score_healthiness.py`) that calculates 0-100 team health ratings and head-to-head matchup health advantages.

---

## Installation & Setup

This project uses **Pipenv** for reproducible dependency management.

```bash
# 1. Clone or navigate to the repository
cd nfl-injury-analysis

# 2. Install dependencies via Pipenv
pipenv install
```

### Dependencies
- **Python**: `>= 3.12`
- **pandas**: Data manipulation and tabular analysis
- **pyarrow**: Fast Parquet file format support
- **requests**: HTTP and data download handling

---

## How to Run & Rerun Weekly

Run the update pipeline with Pipenv:

```bash
pipenv run update
```

Or run directly with Python:

```bash
python update_injury_log.py
```

### Command Line Options

```bash
# Update a specific season (default: current season, e.g. 2026)
pipenv run python update_injury_log.py --season 2026

# Update / filter to a specific week
pipenv run python update_injury_log.py --week 7

# Bypass cache and re-download fresh data
pipenv run python update_injury_log.py --force-refresh

# Specify custom output path
pipenv run python update_injury_log.py --output data/custom_injury_log.csv
```

---

## Output CSVs & Data Dictionary

Output files are stored in the [`data/`](file:///c:/dev/python_projects/nfl-injury-analysis/data/) directory:

1. **`data/nfl_injuries_and_missed_games_2026.csv`** (and standard `data/nfl_injuries_and_missed_games.csv`):
   The primary log of every player injury and missed game record.

### Key Columns

| Column | Type | Description |
| :--- | :--- | :--- |
| `season` | `int` | NFL season year (e.g. 2026) |
| `week` | `int` | Week number (1 to 18) |
| `game_id` | `str` | NFL game ID (e.g. `2026_01_ARI_LAC`) |
| `game_date` | `str` | Date of the game (YYYY-MM-DD) |
| `team` | `str` | Team abbreviation (e.g. `SF`, `KC`, `BAL`) |
| `opponent` | `str` | Opposing team abbreviation |
| `is_home` | `bool` | `True` if home game, `False` if away |
| `surface` | `str` | Playing surface (`grass`, `fieldturf`, `a_turf`, etc.) |
| `team_had_game` | `bool` | `True` if team played, `False` if Bye week |
| `player_name` | `str` | Full player name |
| `position` | `str` | Player position (e.g. `QB`, `WR`, `CB`, `T`) |
| `position_group` | `str` | Broad unit (`QB`, `RB`, `WR`, `TE`, `OL`, `DL`, `LB`, `CB`, `S`, `ST`) |
| `depth_chart_rank` | `int` | Depth chart rank (`1` = Starter, `2` = Backup) |
| `is_starter` | `bool` | `True` if starter (depth rank 1 or snap share >= 50%) |
| `roster_status` | `str` | Roster status (`ACT`, `RES`, `INA`, `DEV`, `EXE`, `CUT`) |
| `roster_status_code` | `str` | NFL code (`R01`, `R04`, `R40`, `E02`, `A01`, etc.) |
| `roster_status_desc` | `str` | Human readable description (`Reserve / Injured (IR)`, `Active`, etc.) |
| `report_status` | `str` | Gameday designation (`Out`, `Doubtful`, `Questionable`, or blank) |
| `practice_status` | `str` | Practice status (`Did Not Participate`, `Limited`, `Full`) |
| `primary_injury` | `str` | Diagnosed body part / reason (`Knee`, `Hamstring`, `Ankle`, etc.) |
| `injury_source` | `str` | Source: `injury_report`, `carried_forward_ir`, or `roster_status` |
| `game_missed` | `bool` | `True` if player missed the game, `False` if dressed/active |
| `missed_reason_category` | `str` | Standardized category (e.g. `INJURY_IR`, `HEALTHY_SCRATCH`, etc.) |
| `missed_reason_detail` | `str` | Human-readable summary (e.g. `Reserve/Injured (IR) - Knee`) |
| `health_impact_weight` | `float` | Severity penalty weight (1.0 = missed game, 0.35 = Questionable, etc.) |
| `total_snaps` | `int` | Total snaps played in game (0 if missed game) |
| `offense_pct` | `float` | Offensive snap percentage (0.0 to 1.0) |
| `defense_pct` | `float` | Defensive snap percentage (0.0 to 1.0) |

2. **`data/team_injury_weekly_summary_2026.csv`**:
   Aggregated team-by-team weekly stats showing total players missed, starters lost, and health penalties.

---

## Scoring Team Healthiness

To score each team's healthiness (0 to 100 scale) and compute matchup health advantages:

```bash
pipenv run score
```

Or:

```bash
python score_healthiness.py --season 2026
```

### How the Health Index Works
- **Baseline**: Each team starts at 100.0 (fully healthy 53-man roster).
- **Starting Quarterback Lost**: `-22.0` penalty (the single most important position).
- **Non-QB Starter Lost**: `-4.5` penalty per starter on IR, Inactive, or Suspended.
- **Starters Playing Hurt**: `-1.8` for Questionable, `-3.5` for Doubtful.
- **Backup / Depth Missed**: `-1.0` penalty per depth player.
- **Net Advantage**: `Team Health Score - Opponent Health Score` for each scheduled game.

Outputs: **`data/team_game_healthiness_scores_2026.csv`**

---

## Running Automated Tests

Run the test suite to verify data harmonization, status categorization, carry-forward logic, and health scoring:

```bash
pipenv run test
```

---

## Automation: Weekly Scheduled Run

To run this pipeline automatically every Tuesday morning after Monday Night Football:

### Option A: Cron (Linux / macOS / WSL)
```cron
# Run every Tuesday at 6:00 AM
0 6 * * 2 cd /path/to/nfl-injury-analysis && pipenv run update && pipenv run score
```

### Option B: Windows Task Scheduler
Create a basic task triggering every Tuesday running:
- **Program**: `pipenv`
- **Arguments**: `run update`
- **Start in**: `c:\dev\python_projects\nfl-injury-analysis`

---

## Interactive Vue Frontend Dashboard

A dedicated Vue 3 + Vite visual analytics frontend is included in [`frontend/`](file:///c:/dev/python_projects/nfl-injury-analysis/frontend/) to explore the generated CSV logs and team health indices.

### Features
- **League Health Power Rankings**: 0-100 team health ratings across all 32 teams with letter grades (A+ to F).
- **Matchup Health Center**: Head-to-head game cards showing net injury advantage, surface types, and unit-by-unit health meters (QB, OL, Skill, Front 7, Secondary).
- **Team Deep Dive**: Weekly health trend curves, starter casualty breakdowns, and full team injury rosters.
- **Player Injury Database**: Instant search, position and status filters across all 4,600+ player-week records, with CSV export.
- **Surface & Trend Insights**: Synthetic turf vs. natural grass injury comparisons and body part diagnosis breakdowns.

### Launching the Dashboard

From the project root:
```bash
npm run dev
```

Or from the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/` in your browser. Live CSV updates from `data/` will automatically sync on refresh.
