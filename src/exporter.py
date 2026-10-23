"""
Exporter and summary reporting module for NFL injury logs.
"""

from pathlib import Path
from typing import Optional
import pandas as pd


class InjuryExporter:
    """Handles exporting injury datasets to CSV and displaying summary statistics."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, df: pd.DataFrame, season: int, custom_path: Optional[Path] = None) -> Path:
        """
        Export processed DataFrame to CSV.
        Also creates a standard default 'nfl_injuries_and_missed_games.csv' in the output directory.
        """
        if custom_path:
            out_file = Path(custom_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_file = self.output_dir / f"nfl_injuries_and_missed_games_{season}.csv"

        df.to_csv(out_file, index=False)

        # Also write the default latest file if custom_path not specified
        if not custom_path:
            latest_file = self.output_dir / "nfl_injuries_and_missed_games.csv"
            df.to_csv(latest_file, index=False)

        return out_file

    def export_team_weekly_summary(self, df: pd.DataFrame, season: int) -> Path:
        """
        Export an aggregated team-by-team weekly summary of missed games and health deductions.
        """
        summary_rows = []
        for (week, team), group in df.groupby(["week", "team"]):
            missed = group[group["game_missed"] == True]
            injury_missed = group[group["missed_reason_category"].str.startswith("INJURY")]
            scratch_missed = group[group["missed_reason_category"] == "HEALTHY_SCRATCH"]
            susp_missed = group[group["missed_reason_category"] == "SUSPENSION"]
            starters_missed = missed[missed["is_starter"] == True]
            questionable_active = group[group["missed_reason_category"] == "INJURED_PLAYED_QUESTIONABLE"]

            opp = group["opponent"].dropna().iloc[0] if not group["opponent"].dropna().empty else "BYE"
            surface = group["surface"].dropna().iloc[0] if not group["surface"].dropna().empty else "unknown"

            summary_rows.append({
                "season": season,
                "week": week,
                "team": team,
                "opponent": opp,
                "surface": surface,
                "total_players_tracked": len(group),
                "games_missed_total": len(missed),
                "games_missed_injury": len(injury_missed),
                "games_missed_healthy_scratch": len(scratch_missed),
                "games_missed_suspension": len(susp_missed),
                "starters_missed": len(starters_missed),
                "questionable_played": len(questionable_active),
                "total_health_severity_impact": round(group["health_impact_weight"].sum(), 2),
                "key_starters_out": "; ".join(starters_missed["player_name"].head(5).tolist()),
            })

        summary_df = pd.DataFrame(summary_rows)
        out_summary = self.output_dir / f"team_injury_weekly_summary_{season}.csv"
        summary_df.to_csv(out_summary, index=False)
        return out_summary

    def print_summary_report(self, df: pd.DataFrame, season: int, output_path: Path):
        """Print a clear terminal summary of the generated injury log."""
        total_records = len(df)
        weeks = sorted(df["week"].unique().tolist())
        total_missed = df["game_missed"].sum()
        inj_missed = df[df["missed_reason_category"].str.startswith("INJURY")]["game_missed"].sum()
        scratches = (df["missed_reason_category"] == "HEALTHY_SCRATCH").sum()
        suspensions = (df["missed_reason_category"] == "SUSPENSION").sum()
        starters_missed = (df["game_missed"] & df["is_starter"]).sum()

        print("\n" + "=" * 70)
        print(f"[NFL INJURY & MISSED GAMES LOG] (Season {season})")
        print("=" * 70)
        print(f"Output CSV:         {output_path.resolve()}")
        print(f"Weeks Covered:      Weeks {min(weeks)} through {max(weeks)} ({len(weeks)} weeks)")
        print(f"Total Logged Rows:  {total_records:,}")
        print(f"Total Games Missed: {total_missed:,}")
        print(f"  * Injuries (IR / Out / Inactive): {inj_missed:,} ({(inj_missed/total_missed)*100:.1f}%)")
        print(f"  * Healthy Scratches:             {scratches:,} ({(scratches/total_missed)*100:.1f}%)")
        print(f"  * Suspensions / Disciplinary:    {suspensions:,} ({(suspensions/total_missed)*100:.1f}%)")
        print(f"  * Key Starters Missed:           {starters_missed:,}")

        # Top 5 Most Common Diagnosed Injuries
        medical_injuries = df[
            df["primary_injury"].notna()
            & ~df["primary_injury"].str.contains("Not injury|Reserve|Active|Scratch", case=False, na=False)
        ]["primary_injury"].value_counts().head(5)

        if not medical_injuries.empty:
            print("\nMost Common Diagnosed Injuries (Player-Weeks):")
            for rank, (inj_name, count) in enumerate(medical_injuries.items(), 1):
                print(f"  {rank}. {inj_name:<16} : {count:,} occurrences")

        # Top 5 Most Impacted Teams (by total games missed to injury)
        team_inj_impact = (
            df[df["game_missed"] & df["missed_reason_category"].str.startswith("INJURY")]
            .groupby("team")
            .size()
            .sort_values(ascending=False)
            .head(5)
        )

        if not team_inj_impact.empty:
            print("\nTop 5 Most Injured Teams (Player-Games Lost to Injury):")
            for rank, (team_code, count) in enumerate(team_inj_impact.items(), 1):
                print(f"  {rank}. {team_code:<5} : {count} player-games lost")

        print("=" * 70 + "\n")
