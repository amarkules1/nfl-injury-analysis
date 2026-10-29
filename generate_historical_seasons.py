"""
Batch generator for historical NFL injury datasets and healthiness scores (2013-2026).
Ensures all seasons with complete details are processed and synced to frontend/public/data.
"""

import sys
import shutil
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR
from src.data_loader import DataLoader
from src.processor import InjuryProcessor
from src.exporter import InjuryExporter
from score_healthiness import HealthScorer

SEASONS_TO_PROCESS = [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014]


def process_season(season: int, loader: DataLoader, processor: InjuryProcessor, exporter: InjuryExporter, scorer: HealthScorer):
    print(f"\n--- Processing Season {season} ---")
    injuries_df = loader.load_injuries(season=season)
    rosters_df = loader.load_rosters(season=season)
    games_df = loader.load_games(season=season)
    snaps_df = loader.load_snap_counts(season=season)
    depth_charts_df = loader.load_depth_charts(season=season)

    prior_season = season - 1
    prior_snaps_df = loader.load_snap_counts(season=prior_season)
    prior_depth_charts_df = loader.load_depth_charts(season=prior_season)

    processed_df = processor.process(
        roster_df=rosters_df,
        inj_df=injuries_df,
        games_df=games_df,
        snaps_df=snaps_df,
        depth_charts_df=depth_charts_df,
        season=season,
        prior_snaps_df=prior_snaps_df,
        prior_depth_charts_df=prior_depth_charts_df,
    )

    main_csv = exporter.export_csv(processed_df, season=season)
    sum_csv = exporter.export_team_weekly_summary(processed_df, season=season)
    print(f"Exported main log ({len(processed_df)} rows) and weekly summary.")

    # Score healthiness
    scores_df = scorer.score_all_games(processed_df)
    score_csv = DATA_DIR / f"team_game_healthiness_scores_{season}.csv"
    scores_df.to_csv(score_csv, index=False)
    print(f"Scored {len(scores_df)} team-games.")

    # Copy to frontend/public/data
    frontend_dir = PROJECT_ROOT / "frontend" / "public" / "data"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(main_csv, frontend_dir / main_csv.name)
    shutil.copy(sum_csv, frontend_dir / sum_csv.name)
    shutil.copy(score_csv, frontend_dir / score_csv.name)
    print(f"Synced {season} files to {frontend_dir.name}/.")


def main():
    loader = DataLoader()
    processor = InjuryProcessor()
    exporter = InjuryExporter(output_dir=DATA_DIR)
    scorer = HealthScorer()

    # Also sync already generated seasons if in data/
    frontend_dir = PROJECT_ROOT / "frontend" / "public" / "data"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    for p in DATA_DIR.glob("*.csv"):
        shutil.copy(p, frontend_dir / p.name)

    for yr in SEASONS_TO_PROCESS:
        try:
            process_season(yr, loader, processor, exporter, scorer)
        except Exception as e:
            print(f"[ERROR] Failed to process season {yr}: {e}")

    print("\n[Done] All historical seasons batch generation completed.")


if __name__ == "__main__":
    main()
