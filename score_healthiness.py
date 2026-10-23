#!/usr/bin/env python3
"""
Team Game Healthiness Scoring Module.

Scores NFL teams' healthiness (0 to 100 scale) for each game based on:
  - Lost starters (with heavy weighting on starting QB, OL, and elite contributors)
  - Lost depth players (IR, Inactives, Suspensions)
  - Active players playing hurt (Questionable, Doubtful)
  - Unit-level breakdowns (QB, OL, Skill, DL/Front, Secondary)
  - Matchup health advantage (Team Health vs Opponent Health)

Usage:
    pipenv run score
    or:
    python score_healthiness.py [--season YEAR] [--week WEEK] [--input-csv PATH]
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Ensure UTF-8 output encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
from config import DEFAULT_SEASON, DATA_DIR


def parse_args():
    parser = argparse.ArgumentParser(
        description="Score NFL teams' healthiness for each game",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--season",
        type=int,
        default=DEFAULT_SEASON,
        help="Season to score",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Optional week to filter",
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        default=None,
        help="Path to nfl_injuries_and_missed_games CSV (default: data/nfl_injuries_and_missed_games_{season}.csv)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Path to save healthiness scores CSV",
    )
    return parser.parse_args()


class HealthScorer:
    """Calculates team healthiness scores per game from the injury & missed games log."""

    # Penalty weights deducted from 100 base score
    QB_STARTER_OUT_PENALTY = 22.0
    QB_QUESTIONABLE_PENALTY = 7.0
    NON_QB_STARTER_OUT_PENALTY = 4.5
    NON_QB_STARTER_DOUBTFUL_PENALTY = 3.5
    NON_QB_STARTER_QUESTIONABLE_PENALTY = 1.8
    BACKUP_OUT_PENALTY = 1.0
    BACKUP_QUESTIONABLE_PENALTY = 0.4

    def score_team_game(self, team_records: pd.DataFrame) -> Dict:
        """Calculate health metrics for a single team in a single game."""
        score = 100.0

        # Sub-unit baseline health (100 each)
        unit_scores = {
            "QB": 100.0,
            "OL": 100.0,
            "SKILL": 100.0,  # RB, WR, TE
            "FRONT": 100.0,  # DL, EDGE, LB
            "DB": 100.0,     # CB, S
        }

        starters_out_list = []
        starters_q_list = []
        qb_out_name = None
        qb_status = "Healthy"

        for _, row in team_records.iterrows():
            pos_group = str(row.get("position_group", "")).upper()
            is_starter = bool(row.get("is_starter", False))
            is_missed = bool(row.get("game_missed", False))
            report_status = str(row.get("report_status", "")).strip()
            player_name = str(row.get("player_name", "Unknown"))

            # Determine unit mapping
            if pos_group == "QB":
                unit_key = "QB"
            elif pos_group in ["OL", "T", "G", "C"]:
                unit_key = "OL"
            elif pos_group in ["WR", "RB", "TE"]:
                unit_key = "SKILL"
            elif pos_group in ["DL", "LB"]:
                unit_key = "FRONT"
            elif pos_group in ["CB", "S"]:
                unit_key = "DB"
            else:
                unit_key = None

            # Calculate deduction
            deduction = 0.0
            if pos_group == "QB":
                if is_starter:
                    if is_missed:
                        deduction = self.QB_STARTER_OUT_PENALTY
                        qb_status = "Out"
                        qb_out_name = player_name
                        starters_out_list.append(f"{player_name} (QB)")
                        if unit_key:
                            unit_scores[unit_key] -= 60.0
                    elif report_status in ["Questionable", "Doubtful"]:
                        deduction = self.QB_QUESTIONABLE_PENALTY
                        qb_status = report_status
                        starters_q_list.append(f"{player_name} (QB - {report_status})")
                        if unit_key:
                            unit_scores[unit_key] -= 25.0
                else:
                    # Backup QB missed or hurt (standard depth player penalty)
                    if is_missed:
                        deduction = self.BACKUP_OUT_PENALTY
                        if unit_key:
                            unit_scores[unit_key] -= 4.0
                    elif report_status in ["Questionable", "Doubtful"]:
                        deduction = self.BACKUP_QUESTIONABLE_PENALTY
                        if unit_key:
                            unit_scores[unit_key] -= 2.0
            elif is_starter:
                if is_missed:
                    deduction = self.NON_QB_STARTER_OUT_PENALTY
                    starters_out_list.append(f"{player_name} ({pos_group})")
                    if unit_key:
                        unit_scores[unit_key] -= 18.0
                elif report_status == "Doubtful":
                    deduction = self.NON_QB_STARTER_DOUBTFUL_PENALTY
                    starters_q_list.append(f"{player_name} ({pos_group} - Doubtful)")
                    if unit_key:
                        unit_scores[unit_key] -= 12.0
                elif report_status == "Questionable":
                    deduction = self.NON_QB_STARTER_QUESTIONABLE_PENALTY
                    starters_q_list.append(f"{player_name} ({pos_group} - Questionable)")
                    if unit_key:
                        unit_scores[unit_key] -= 8.0
            else:
                # Backup / depth players
                if is_missed:
                    deduction = self.BACKUP_OUT_PENALTY
                    if unit_key:
                        unit_scores[unit_key] -= 4.0
                elif report_status in ["Questionable", "Doubtful"]:
                    deduction = self.BACKUP_QUESTIONABLE_PENALTY
                    if unit_key:
                        unit_scores[unit_key] -= 2.0

            score -= deduction

        # Bound scores to 0-100 range
        final_score = max(10.0, min(100.0, round(score, 1)))
        for k in unit_scores:
            unit_scores[k] = max(0.0, min(100.0, round(unit_scores[k], 1)))

        return {
            "health_score": final_score,
            "qb_status": qb_status,
            "qb_name_out": qb_out_name,
            "starters_out_count": len(starters_out_list),
            "starters_questionable_count": len(starters_q_list),
            "key_missing_starters": "; ".join(starters_out_list[:6]),
            "questionable_starters": "; ".join(starters_q_list[:4]),
            "qb_unit_health": unit_scores["QB"],
            "ol_unit_health": unit_scores["OL"],
            "skill_unit_health": unit_scores["SKILL"],
            "front_unit_health": unit_scores["FRONT"],
            "secondary_unit_health": unit_scores["DB"],
        }

    def score_all_games(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute health scores for every team and game matchup."""
        # Filter out bye weeks
        games_df = df[df["team_had_game"] == True].copy()
        if games_df.empty:
            return pd.DataFrame()

        team_game_stats = {}
        for (season, week, team), group in games_df.groupby(["season", "week", "team"]):
            first_row = group.iloc[0]
            opp = first_row.get("opponent", "UNKNOWN")
            is_home = bool(first_row.get("is_home", False))
            game_id = first_row.get("game_id", f"{season}_{week:02d}_{team}")
            game_date = first_row.get("game_date", "")
            surface = first_row.get("surface", "unknown")

            team_metrics = self.score_team_game(group)
            team_game_stats[(season, week, team)] = {
                "season": season,
                "week": week,
                "game_id": game_id,
                "game_date": game_date,
                "team": team,
                "opponent": opp,
                "is_home": is_home,
                "surface": surface,
                "total_players_logged": len(group),
                "total_games_missed": int(group["game_missed"].sum()),
                **team_metrics,
            }

        # Build paired matchup comparison
        rows = []
        for (season, week, team), t_data in team_game_stats.items():
            opp = t_data["opponent"]
            opp_data = team_game_stats.get((season, week, opp))

            opp_score = opp_data["health_score"] if opp_data else None
            net_advantage = round(t_data["health_score"] - opp_score, 1) if opp_score is not None else None

            row = dict(t_data)
            row["opponent_health_score"] = opp_score
            row["net_health_advantage"] = net_advantage
            rows.append(row)

        res_df = pd.DataFrame(rows)
        return res_df.sort_values(["season", "week", "team"]).reset_index(drop=True)


def main():
    args = parse_args()
    input_path = Path(args.input_csv) if args.input_csv else DATA_DIR / f"nfl_injuries_and_missed_games_{args.season}.csv"
    if not input_path.exists():
        input_path = DATA_DIR / "nfl_injuries_and_missed_games.csv"

    if not input_path.exists():
        print(f"[ERROR] Input injury log not found at: {input_path}")
        print("Please run 'pipenv run update' first to generate the injury log.")
        sys.exit(1)

    print(f"\n[Scoring Team Healthiness for Season {args.season}]")
    print(f"Reading from: {input_path}")

    df = pd.read_csv(input_path)
    if args.week:
        df = df[df["week"] == args.week]

    scorer = HealthScorer()
    scores_df = scorer.score_all_games(df)

    output_path = Path(args.output_csv) if args.output_csv else DATA_DIR / f"team_game_healthiness_scores_{args.season}.csv"
    scores_df.to_csv(output_path, index=False)

    public_data_dir = DATA_DIR.parent / "frontend" / "public" / "data"
    if public_data_dir.exists():
        try:
            scores_df.to_csv(public_data_dir / f"team_game_healthiness_scores_{args.season}.csv", index=False)
        except Exception:
            pass

    print(f"[OK] Healthiness scores generated for {len(scores_df)} team-games.")
    print(f"[OK] Saved to: {output_path.resolve()}\n")

    # Display Top 5 Healthiest and Least Healthy Team-Games
    print("=" * 70)
    print(f"HEALTHIEST TEAMS (Average Health Score - Season {args.season}):")
    avg_health = scores_df.groupby("team")["health_score"].mean().sort_values(ascending=False)
    for rank, (team, h_score) in enumerate(avg_health.head(5).items(), 1):
        print(f"  {rank}. {team:<5} : {h_score:.1f} / 100")

    print(f"\nMOST INJURY-DEPLETED TEAMS (Average Health Score - Season {args.season}):")
    for rank, (team, h_score) in enumerate(avg_health.tail(5).items(), 1):
        print(f"  {rank}. {team:<5} : {h_score:.1f} / 100")

    # Sample Recent Game Matchup Health
    latest_week = scores_df["week"].max()
    latest_games = scores_df[(scores_df["week"] == latest_week) & (scores_df["is_home"] == True)].head(3)
    if not latest_games.empty:
        print(f"\nSAMPLE WEEK {latest_week} MATCHUP HEALTH COMPARISONS:")
        for _, g in latest_games.iterrows():
            home = g["team"]
            away = g["opponent"]
            h_score = g["health_score"]
            a_score = g["opponent_health_score"]
            diff = g["net_health_advantage"]
            sign = "+" if diff > 0 else ""
            print(f"  {away} ({a_score}) @ {home} ({h_score}) -> {home} Net Health Adv: {sign}{diff}")
            if g["key_missing_starters"]:
                print(f"    * {home} Missing Starters: {g['key_missing_starters']}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
