#!/usr/bin/env python3
"""
CLI script to fetch, process, and log NFL player injuries and games missed.
Can be executed weekly to update the dataset with latest games and transactions.

Usage:
    pipenv run update
    or:
    python update_injury_log.py [--season YEAR] [--week WEEK] [--force-refresh] [--output PATH]
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from config import DEFAULT_SEASON, DATA_DIR, CACHE_DIR
from src.data_loader import DataLoader
from src.processor import InjuryProcessor
from src.exporter import InjuryExporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="NFL Injury & Missed Games Weekly Log Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--season",
        type=int,
        default=DEFAULT_SEASON,
        help="NFL season year to process (e.g., 2026, 2025)",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Specific NFL week to filter (default: all available weeks so far this season)",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass local cache and re-download latest data from nflverse",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom destination path for the output CSV file",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=str(CACHE_DIR),
        help="Directory to store cached nflverse files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_DIR),
        help="Directory where output CSV files are written",
    )
    parser.add_argument(
        "--skip-scoring",
        action="store_true",
        help="Skip calculating team game healthiness scores",
    )
    parser.add_argument(
        "--skip-predictions",
        action="store_true",
        help="Skip running machine learning upcoming week predictions",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    start_time = time.time()

    print("\n[NFL Injury & Missed Games Data Pipeline]")
    print(f"   Season:        {args.season}")
    if args.week:
        print(f"   Target Week:   Week {args.week}")
    else:
        print("   Target Week:   All available weeks so far")
    print(f"   Force Refresh: {args.force_refresh}")

    loader = DataLoader(cache_dir=Path(args.cache_dir))
    processor = InjuryProcessor()
    exporter = InjuryExporter(output_dir=Path(args.output_dir))

    # 1. Fetch Datasets
    print("\n[1/4] Loading official NFL datasets...")
    try:
        t0 = time.time()
        injuries_df = loader.load_injuries(season=args.season, force_refresh=args.force_refresh)
        print(f"   [OK] Injury reports loaded:   {len(injuries_df):,} rows ({time.time()-t0:.2f}s)")
    except Exception as e:
        print(f"   [ERROR] Failed to load injuries for {args.season}: {e}")
        sys.exit(1)

    try:
        t0 = time.time()
        rosters_df = loader.load_rosters(season=args.season, force_refresh=args.force_refresh)
        print(f"   [OK] Weekly rosters loaded:   {len(rosters_df):,} rows ({time.time()-t0:.2f}s)")
    except Exception as e:
        print(f"   [ERROR] Failed to load weekly rosters for {args.season}: {e}")
        sys.exit(1)

    try:
        t0 = time.time()
        games_df = loader.load_games(season=args.season, force_refresh=args.force_refresh)
        print(f"   [OK] Schedules & games loaded: {len(games_df):,} rows ({time.time()-t0:.2f}s)")
    except Exception as e:
        print(f"   [WARN] Could not load games schedule: {e}")
        games_df = None

    try:
        t0 = time.time()
        snaps_df = loader.load_snap_counts(season=args.season, force_refresh=args.force_refresh)
        if not snaps_df.empty:
            print(f"   [OK] Snap counts loaded:      {len(snaps_df):,} rows ({time.time()-t0:.2f}s)")
        else:
            print("   [INFO] Snap counts not yet available for current week (continuing with roster & injury data)")
            snaps_df = None
    except Exception:
        snaps_df = None

    try:
        t0 = time.time()
        depth_charts_df = loader.load_depth_charts(season=args.season, force_refresh=args.force_refresh)
        if not depth_charts_df.empty:
            print(f"   [OK] Depth charts loaded:     {len(depth_charts_df):,} rows ({time.time()-t0:.2f}s)")
        else:
            depth_charts_df = None
    except Exception:
        depth_charts_df = None

    # Load prior season baseline data for accurate starter detection on injured players
    prior_season = args.season - 1
    try:
        t0 = time.time()
        prior_snaps_df = loader.load_snap_counts(season=prior_season, force_refresh=args.force_refresh)
        if not prior_snaps_df.empty:
            print(f"   [OK] Prior season ({prior_season}) snaps loaded: {len(prior_snaps_df):,} rows ({time.time()-t0:.2f}s)")
        else:
            prior_snaps_df = None
    except Exception:
        prior_snaps_df = None

    try:
        t0 = time.time()
        prior_depth_charts_df = loader.load_depth_charts(season=prior_season, force_refresh=args.force_refresh)
        if not prior_depth_charts_df.empty:
            print(f"   [OK] Prior season ({prior_season}) depth charts: {len(prior_depth_charts_df):,} rows ({time.time()-t0:.2f}s)")
        else:
            prior_depth_charts_df = None
    except Exception:
        prior_depth_charts_df = None

    # 2. Process, Harmonize, and Categorize
    print("\n[2/4] Processing and categorizing injuries, missed games, and health impacts...")
    t0 = time.time()
    processed_df = processor.process(
        roster_df=rosters_df,
        inj_df=injuries_df,
        games_df=games_df,
        snaps_df=snaps_df,
        depth_charts_df=depth_charts_df,
        season=args.season,
        target_week=args.week,
        prior_snaps_df=prior_snaps_df,
        prior_depth_charts_df=prior_depth_charts_df,
    )
    print(f"   [OK] Successfully harmonized and categorized {len(processed_df):,} records ({time.time()-t0:.2f}s)")

    # 3. Export to CSV
    print("\n[3/4] Exporting to CSV...")
    custom_out = Path(args.output) if args.output else None
    csv_path = exporter.export_csv(processed_df, season=args.season, custom_path=custom_out)
    print(f"   [OK] Main dataset saved to: {csv_path}")

    # Export weekly team summary
    summary_path = exporter.export_team_weekly_summary(processed_df, season=args.season)
    print(f"   [OK] Team weekly summary saved to: {summary_path}")

    # 4. Score Team Healthiness
    if not args.skip_scoring:
        print("\n[4/5] Scoring team game healthiness...")
        try:
            from score_healthiness import HealthScorer
            scorer = HealthScorer()
            scores_df = scorer.score_all_games(processed_df)
            scores_out = Path(args.output_dir) / f"team_game_healthiness_scores_{args.season}.csv"
            scores_df.to_csv(scores_out, index=False)

            # Mirror to frontend public and dist folders
            for dest_dir in [
                Path(args.output_dir).parent / "frontend" / "public" / "data",
                Path(args.output_dir).parent / "frontend" / "dist" / "data",
            ]:
                if dest_dir.exists():
                    try:
                        scores_df.to_csv(dest_dir / f"team_game_healthiness_scores_{args.season}.csv", index=False)
                    except Exception:
                        pass
            print(f"   [OK] Healthiness scores saved for {len(scores_df)} team-games: {scores_out}")
        except Exception as e:
            print(f"   [WARN] Could not score healthiness: {e}")

    # 5. Run Predictive Model for Upcoming Week
    if not args.skip_predictions:
        print("\n[5/5] Running predictive model for upcoming week...")
        try:
            from src.prediction_model import run_pipeline as run_prediction_pipeline
            run_prediction_pipeline(season=args.season)
        except Exception as e:
            print(f"   [WARN] Could not run prediction pipeline: {e}")

    # Pipeline Complete
    print("\n[Pipeline Complete]")
    exporter.print_summary_report(processed_df, season=args.season, output_path=csv_path)

    elapsed = time.time() - start_time
    print(f"[Done] Finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
