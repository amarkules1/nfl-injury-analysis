"""
Configuration and constants for NFL Injury & Missed Games Analysis.
"""

from pathlib import Path
from typing import Dict, Set

# Base Directories
PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure output and cache directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Default Season (can be overridden via CLI)
DEFAULT_SEASON = 2026

# nflverse release base URLs
NFLVERSE_BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download"

DATA_URLS = {
    "injuries_parquet": f"{NFLVERSE_BASE_URL}/injuries/injuries_{{season}}.parquet",
    "injuries_csv": f"{NFLVERSE_BASE_URL}/injuries/injuries_{{season}}.csv",
    "roster_parquet": f"{NFLVERSE_BASE_URL}/weekly_rosters/roster_weekly_{{season}}.parquet",
    "roster_csv": f"{NFLVERSE_BASE_URL}/weekly_rosters/roster_weekly_{{season}}.csv",
    "games_csv": f"{NFLVERSE_BASE_URL}/schedules/games.csv",
    "games_parquet": f"{NFLVERSE_BASE_URL}/schedules/games.parquet",
    "snaps_csv": f"{NFLVERSE_BASE_URL}/snap_counts/snap_counts_{{season}}.csv",
    "depth_charts_parquet": f"{NFLVERSE_BASE_URL}/depth_charts/depth_charts_{{season}}.parquet",
    "depth_charts_csv": f"{NFLVERSE_BASE_URL}/depth_charts/depth_charts_{{season}}.csv",
}

# Mapping for status_description_abbr (NFL Shield roster designation codes)
ROSTER_STATUS_MAP: Dict[str, str] = {
    "A01": "Active",
    "P01": "Practice Squad",
    "P02": "Practice Squad / Injured",
    "P03": "International Practice Squad",
    "P06": "Practice Squad / Exempt",
    "P07": "Practice Squad / Veteran",
    "R01": "Reserve / Injured (IR)",
    "R02": "Reserve / Retired",
    "R03": "Reserve / Did Not Report",
    "R04": "Reserve / Physically Unable to Perform (PUP)",
    "R05": "Reserve / Non-Football Injury (NFI)",
    "R06": "Reserve / Left Squad",
    "R23": "Reserve / Future",
    "R27": "Reserve / Non-Football Illness (NFIL)",
    "R30": "Reserve / Commissioner Suspension (1 Year)",
    "R33": "Reserve / Club Suspension",
    "R40": "Reserve / Suspension (< 1 Year)",
    "R47": "Reserve / Non-Football Injury (DFR)",
    "R48": "Reserve / Injured (Designated for Return)",
    "R49": "Reserve / PUP (Designated for Return)",
    "E02": "Exempt / Commissioner Permission",
    "W03": "Waivers / No Recall",
    "I01": "Inactive",
}

# Reserve codes that represent injuries/medical issues
INJURY_RESERVE_CODES: Set[str] = {
    "R01",  # IR
    "R48",  # IR-DFR
    "R04",  # PUP
    "R49",  # PUP-DFR
    "R05",  # NFI
    "R47",  # NFI-DFR
    "R27",  # NFIL
    "P02",  # Practice Squad Injured
}

# Reserve codes that represent suspensions / disciplinary
SUSPENSION_CODES: Set[str] = {
    "R40",  # Suspension < 1 Year
    "R30",  # Commissioner Suspension 1 Year
    "R33",  # Club Suspension
}

# Reserve codes that represent other non-injury reasons
OTHER_RESERVE_CODES: Set[str] = {
    "R03",  # Did not report (holdouts)
    "R06",  # Left squad
    "R02",  # Retired
    "E02",  # Exempt list
}

# Position Groups
POSITION_GROUPS: Dict[str, str] = {
    "QB": "QB",
    "RB": "RB", "FB": "RB", "HB": "RB",
    "WR": "WR",
    "TE": "TE",
    "T": "OL", "OT": "OL", "LT": "OL", "RT": "OL", "G": "OL", "OG": "OL", "LG": "OL", "RG": "OL", "C": "OL", "OL": "OL",
    "DE": "DL", "LDE": "DL", "RDE": "DL", "DT": "DL", "LDT": "DL", "RDT": "DL", "NT": "DL", "EDGE": "DL", "DL": "DL",
    "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB", "SLB": "LB", "WLB": "LB",
    "CB": "CB", "LCB": "CB", "RCB": "CB", "NB": "CB", "DB": "CB",
    "S": "S", "FS": "S", "SS": "S",
    "K": "ST", "PK": "ST", "P": "ST", "LS": "ST",
}

# Health Severity Score default weights for downstream healthiness calculations
# (0.0 = 100% healthy, 1.0 = 100% lost game)
HEALTH_SEVERITY_WEIGHTS = {
    "MISSED_GAME": 1.00,        # Out / IR / PUP / NFI / Inactive / Suspended
    "DOUBTFUL_ACTIVE": 0.75,     # On injury report as Doubtful (extreme limitation)
    "QUESTIONABLE_ACTIVE": 0.35, # On injury report as Questionable (compromised / playing hurt)
    "MONITORED_PRACTICE": 0.10,  # Monitored on injury report / DNP in practice, but played
    "HEALTHY": 0.00,
}
