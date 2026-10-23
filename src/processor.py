"""
Data processing module: harmonization, injury carry-forward, categorization,
starter tagging, and health impact weighting.
"""

from typing import Optional
import numpy as np
import pandas as pd

from config import (
    ROSTER_STATUS_MAP,
    INJURY_RESERVE_CODES,
    SUSPENSION_CODES,
    OTHER_RESERVE_CODES,
    POSITION_GROUPS,
    HEALTH_SEVERITY_WEIGHTS,
)


class InjuryProcessor:
    """Processes, merges, categorizes, and enriches NFL injury and roster data."""

    def __init__(self):
        pass

    def prepare_team_games(self, games_df: pd.DataFrame, season: int) -> pd.DataFrame:
        """
        Create a team-level schedule lookup DataFrame with opponent, surface, and location.
        """
        if games_df.empty or "home_team" not in games_df.columns:
            return pd.DataFrame()

        df_season = games_df[games_df["season"] == season].copy()
        needed_cols = ["game_id", "season", "week", "game_type", "gameday", "home_team", "away_team", "roof", "surface"]
        available_cols = [c for c in needed_cols if c in df_season.columns]

        # Home team perspective
        home = df_season[available_cols].copy()
        home = home.rename(columns={"home_team": "team", "away_team": "opponent", "gameday": "game_date"})
        home["is_home"] = True

        # Away team perspective
        away = df_season[available_cols].copy()
        away = away.rename(columns={"away_team": "team", "home_team": "opponent", "gameday": "game_date"})
        away["is_home"] = False

        team_games = pd.concat([home, away], ignore_index=True)
        team_games["team_had_game"] = True
        return team_games

    def build_injury_history_map(self, inj_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a historical map of each player's latest known diagnosed injury.
        Used to carry forward primary injuries to weeks where a player is on IR.
        """
        if inj_df.empty:
            return pd.DataFrame(columns=["combined_primary_injury", "combined_secondary_injury"])

        valid_inj = inj_df[inj_df["report_primary_injury"].notna() | inj_df["practice_primary_injury"].notna()].copy()
        if valid_inj.empty:
            return pd.DataFrame(columns=["combined_primary_injury", "combined_secondary_injury"])

        valid_inj["combined_primary_injury"] = valid_inj["report_primary_injury"].fillna(valid_inj["practice_primary_injury"])
        valid_inj["combined_secondary_injury"] = valid_inj["report_secondary_injury"].fillna(valid_inj["practice_secondary_injury"])

        # Filter out non-injury entries like resting player when determining past injury
        is_medical = ~valid_inj["combined_primary_injury"].astype(str).str.contains("Not injury related", case=False, na=False)
        medical_inj = valid_inj[is_medical]

        if not medical_inj.empty:
            last_known = medical_inj.sort_values("week").groupby("gsis_id").last()
            return last_known[["combined_primary_injury", "combined_secondary_injury"]]
        return pd.DataFrame(columns=["combined_primary_injury", "combined_secondary_injury"])

    def get_position_group(self, position: Optional[str]) -> str:
        """Map individual position to broad positional unit group."""
        if not isinstance(position, str) or not position.strip():
            return "OTHER"
        return POSITION_GROUPS.get(position.strip().upper(), "OTHER")

    def categorize_record(self, row: pd.Series) -> dict:
        """
        Determine whether a game was missed, the standardized reason category,
        human-readable detail string, and health impact weight.
        """
        status = str(row.get("status", "")).strip()
        status_code = str(row.get("status_description_abbr", "")).strip()
        report_status = str(row.get("report_status", "")).strip() if pd.notna(row.get("report_status")) else ""
        primary_injury = str(row.get("primary_injury", "")).strip() if pd.notna(row.get("primary_injury")) else ""
        team_had_game = bool(row.get("team_had_game", True))

        # Check for bye week
        if not team_had_game:
            return {
                "game_missed": False,
                "missed_reason_category": "BYE_WEEK",
                "missed_reason_detail": f"Team on Bye Week ({row.get('roster_status_desc', 'Roster')})",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["HEALTHY"],
            }

        # 1. RESERVE LIST (RES)
        if status == "RES":
            game_missed = True
            weight = HEALTH_SEVERITY_WEIGHTS["MISSED_GAME"]

            has_diag = bool(primary_injury and "Undisclosed" not in primary_injury and "Reserve" not in primary_injury)
            if status_code in ["R01", "R48"]:
                cat = "INJURY_IR"
                desc = f"Reserve/Injured (IR) - {primary_injury}" if has_diag else "Reserve/Injured (IR)"
            elif status_code in ["R04", "R49"]:
                cat = "INJURY_PUP"
                desc = f"Reserve/PUP - {primary_injury}" if has_diag else "Reserve/Physically Unable to Perform (PUP)"
            elif status_code in ["R05", "R47"]:
                cat = "INJURY_NFI"
                desc = f"Reserve/Non-Football Injury - {primary_injury}" if has_diag else "Reserve/NFI"
            elif status_code == "R27":
                cat = "INJURY_NFIL"
                desc = f"Reserve/Non-Football Illness - {primary_injury}" if has_diag else "Reserve/NFIL"
            elif status_code in SUSPENSION_CODES:
                cat = "SUSPENSION"
                desc = f"Reserve/Suspended ({row.get('roster_status_desc', 'League Suspension')})"
            elif status_code == "R03":
                cat = "HOLDOUT_DID_NOT_REPORT"
                desc = "Reserve/Did Not Report (Contract Holdout)"
            elif status_code == "R06":
                cat = "LEFT_SQUAD"
                desc = "Reserve/Left Squad"
            elif status_code == "R02":
                cat = "RETIRED"
                desc = "Reserve/Retired"
            else:
                cat = "OTHER_RESERVE"
                desc = f"Reserve List ({status_code})"

            return {
                "game_missed": game_missed,
                "missed_reason_category": cat,
                "missed_reason_detail": desc,
                "health_impact_weight": weight,
            }

        # 2. COMMISSIONER'S EXEMPT LIST (EXE)
        if status == "EXE" or status_code == "E02":
            return {
                "game_missed": True,
                "missed_reason_category": "COMMISSIONER_EXEMPT",
                "missed_reason_detail": "Commissioner's Exempt List",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["MISSED_GAME"],
            }

        # 3. PRACTICE SQUAD INJURED (P02)
        if status == "DEV" and status_code == "P02":
            return {
                "game_missed": False,  # Not on 53-man roster, but injured
                "missed_reason_category": "INJURY_PRACTICE_SQUAD",
                "missed_reason_detail": f"Practice Squad / Injured - {primary_injury}" if primary_injury else "Practice Squad / Injured",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["MISSED_GAME"],
            }

        # 4. GAMEDAY INACTIVES (INA)
        if status == "INA":
            game_missed = True
            weight = HEALTH_SEVERITY_WEIGHTS["MISSED_GAME"]

            is_rest_personal = "not injury related" in primary_injury.lower() or "personal" in primary_injury.lower()
            if report_status == "Out":
                cat = "INJURY_RULED_OUT"
                desc = f"Gameday Inactive - Ruled Out ({primary_injury})" if primary_injury else "Gameday Inactive - Ruled Out"
            elif report_status in ["Questionable", "Doubtful"] or (primary_injury and not is_rest_personal):
                cat = "INJURY_INACTIVE"
                desc = f"Gameday Inactive - Injured ({primary_injury})" if primary_injury else "Gameday Inactive - Injured"
            elif is_rest_personal:
                cat = "REST_PERSONAL_INACTIVE"
                desc = f"Gameday Inactive - {primary_injury}"
            else:
                cat = "HEALTHY_SCRATCH"
                desc = "Gameday Inactive (Healthy Scratch / Coach Decision)"

            return {
                "game_missed": game_missed,
                "missed_reason_category": cat,
                "missed_reason_detail": desc,
                "health_impact_weight": weight,
            }

        # 5. ACTIVE ROSTER ON INJURY REPORT (ACT or unassigned)
        if report_status == "Out":
            return {
                "game_missed": True,
                "missed_reason_category": "INJURY_RULED_OUT",
                "missed_reason_detail": f"Ruled Out - {primary_injury}" if primary_injury else "Ruled Out for Game",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["MISSED_GAME"],
            }
        elif report_status == "Doubtful":
            return {
                "game_missed": False,
                "missed_reason_category": "INJURED_PLAYED_DOUBTFUL",
                "missed_reason_detail": f"Active - Doubtful ({primary_injury})" if primary_injury else "Active - Doubtful",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["DOUBTFUL_ACTIVE"],
            }
        elif report_status == "Questionable":
            return {
                "game_missed": False,
                "missed_reason_category": "INJURED_PLAYED_QUESTIONABLE",
                "missed_reason_detail": f"Active - Questionable ({primary_injury})" if primary_injury else "Active - Questionable",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["QUESTIONABLE_ACTIVE"],
            }
        elif "not injury related" in primary_injury.lower() or "personal" in primary_injury.lower():
            return {
                "game_missed": False,
                "missed_reason_category": "REST_PERSONAL_ACTIVE",
                "missed_reason_detail": f"Active - {primary_injury}",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["HEALTHY"],
            }
        elif primary_injury or pd.notna(row.get("practice_status")):
            prac_status = str(row.get("practice_status", "")).strip()
            return {
                "game_missed": False,
                "missed_reason_category": "INJURED_PLAYED_PRACTICE_ONLY",
                "missed_reason_detail": f"Active - Monitored ({primary_injury or prac_status})",
                "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["MONITORED_PRACTICE"],
            }

        # Fallback / edge cases
        return {
            "game_missed": False,
            "missed_reason_category": "OTHER",
            "missed_reason_detail": "Other / Uncategorized Status",
            "health_impact_weight": HEALTH_SEVERITY_WEIGHTS["HEALTHY"],
        }

    def process(
        self,
        roster_df: pd.DataFrame,
        inj_df: pd.DataFrame,
        games_df: pd.DataFrame,
        snaps_df: Optional[pd.DataFrame] = None,
        depth_charts_df: Optional[pd.DataFrame] = None,
        season: int = 2026,
        target_week: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Merge, categorize, enrich, and filter NFL injury and missed game records.
        """
        # 1. Clean games schedule
        team_games = self.prepare_team_games(games_df, season)

        # 2. Prepare injury carry-forward map
        injury_history = self.build_injury_history_map(inj_df)

        # 3. Clean roster data
        roster_clean = roster_df.copy()
        if "game_type" in roster_clean.columns:
            roster_clean = roster_clean.drop(columns=["game_type"])

        # Map human-readable roster status descriptions
        roster_clean["roster_status_desc"] = (
            roster_clean["status_description_abbr"].map(ROSTER_STATUS_MAP).fillna(roster_clean["status_description_abbr"])
        )

        # Map position group
        roster_clean["position_group"] = roster_clean["position"].apply(self.get_position_group)

        # Join team games with roster
        if not team_games.empty:
            merged = roster_clean.merge(team_games, on=["season", "week", "team"], how="left")
            merged["team_had_game"] = merged["team_had_game"].fillna(False)
        else:
            merged = roster_clean.copy()
            merged["team_had_game"] = True
            merged["opponent"] = np.nan
            merged["is_home"] = np.nan
            merged["game_date"] = np.nan
            merged["surface"] = np.nan
            merged["roof"] = np.nan
            merged["game_id"] = np.nan

        # 4. Clean injury report data
        inj_clean = inj_df.copy()
        if "game_type" in inj_clean.columns:
            inj_clean = inj_clean.drop(columns=["game_type"])
        inj_clean["on_injury_report"] = True

        # Merge roster with weekly injury reports
        merged = merged.merge(
            inj_clean,
            on=["season", "week", "team", "gsis_id"],
            how="outer",
            suffixes=("_roster", "_inj"),
        )

        # Harmonize common columns across roster and injury reports
        for col in ["full_name", "first_name", "last_name", "position"]:
            r_col = f"{col}_roster"
            i_col = f"{col}_inj"
            if r_col in merged.columns and i_col in merged.columns:
                merged[col] = merged[r_col].fillna(merged[i_col])
                merged = merged.drop(columns=[r_col, i_col])

        # Fill missing position group if populated from injury report
        if "position_group" in merged.columns:
            merged["position_group"] = merged["position_group"].fillna(merged["position"].apply(self.get_position_group))

        # 5. Determine Primary & Secondary Injury with Carry-Forward
        # Priority: report_primary_injury -> practice_primary_injury -> carry-forward from IR -> default
        merged["primary_injury"] = merged["report_primary_injury"].fillna(merged["practice_primary_injury"])
        merged["secondary_injury"] = merged["report_secondary_injury"].fillna(merged["practice_secondary_injury"])
        merged["injury_source"] = np.where(merged["primary_injury"].notna(), "injury_report", "none")

        # Carry forward previous injuries for Reserve players
        if not injury_history.empty:
            is_reserve = merged["status"] == "RES"
            needs_carry_forward = is_reserve & merged["primary_injury"].isna()
            carried_primary = merged["gsis_id"].map(injury_history["combined_primary_injury"])
            carried_secondary = merged["gsis_id"].map(injury_history["combined_secondary_injury"])

            merged.loc[needs_carry_forward & carried_primary.notna(), "primary_injury"] = carried_primary
            merged.loc[needs_carry_forward & carried_secondary.notna(), "secondary_injury"] = carried_secondary
            merged.loc[needs_carry_forward & carried_primary.notna(), "injury_source"] = "carried_forward_ir"

        # For remaining reserve players with no prior injury record:
        res_no_inj = (merged["status"] == "RES") & merged["primary_injury"].isna()
        merged.loc[res_no_inj, "primary_injury"] = "Undisclosed / Reserve"
        merged.loc[res_no_inj, "injury_source"] = "roster_status"

        # 6. Starter Detection (via depth charts or snap share)
        merged["depth_chart_rank"] = np.nan
        if depth_charts_df is not None and not depth_charts_df.empty and "gsis_id" in depth_charts_df.columns:
            try:
                latest_dc = depth_charts_df.sort_values("dt").groupby("gsis_id").last()["pos_rank"]
                merged["depth_chart_rank"] = merged["gsis_id"].map(latest_dc)
            except Exception:
                pass

        # 7. Merge Snap Counts
        merged["total_snaps"] = 0
        merged["offense_snaps"] = 0
        merged["defense_snaps"] = 0
        merged["st_snaps"] = 0
        merged["offense_pct"] = 0.0
        merged["defense_pct"] = 0.0

        if snaps_df is not None and not snaps_df.empty and "pfr_player_id" in snaps_df.columns:
            snaps_clean = snaps_df.copy()
            snaps_clean["total_snaps_calc"] = (
                snaps_clean["offense_snaps"].fillna(0)
                + snaps_clean["defense_snaps"].fillna(0)
                + snaps_clean["st_snaps"].fillna(0)
            )
            # Match by pfr_id or name
            snaps_subset = snaps_clean[[
                "season", "week", "team", "pfr_player_id",
                "offense_snaps", "defense_snaps", "st_snaps",
                "offense_pct", "defense_pct", "total_snaps_calc"
            ]]
            merged = merged.merge(
                snaps_subset,
                left_on=["season", "week", "team", "pfr_id"],
                right_on=["season", "week", "team", "pfr_player_id"],
                how="left",
            )
            for col in ["offense_snaps", "defense_snaps", "st_snaps", "offense_pct", "defense_pct"]:
                if f"{col}_y" in merged.columns:
                    merged[col] = merged[f"{col}_y"].fillna(0)
                    merged = merged.drop(columns=[f"{col}_x", f"{col}_y"])
            if "total_snaps_calc" in merged.columns:
                merged["total_snaps"] = merged["total_snaps_calc"].fillna(0)
                merged = merged.drop(columns=["total_snaps_calc"])
            if "pfr_player_id" in merged.columns:
                merged = merged.drop(columns=["pfr_player_id"])

        # Determine Starter Tag: pos_rank == 1 or snap share >= 50%
        merged["is_starter"] = (
            (merged["depth_chart_rank"] == 1)
            | (merged["offense_pct"] >= 0.50)
            | (merged["defense_pct"] >= 0.50)
        )

        # 8. Filter to Relevant Records (Injuries & Missed Games)
        is_reserve = merged["status"] == "RES"
        is_exempt = merged["status"] == "EXE"
        is_inactive = merged["status"] == "INA"
        is_inj_reported = (
            merged["report_status"].notna()
            | merged["report_primary_injury"].notna()
            | merged["practice_primary_injury"].notna()
        )
        is_practice_limited = merged["practice_status"].isin([
            "Did Not Participate In Practice",
            "Limited Participation in Practice"
        ])
        is_ps_injured = (merged["status"] == "DEV") & (merged["status_description_abbr"] == "P02")

        relevant_mask = (
            is_reserve
            | is_exempt
            | is_inactive
            | is_inj_reported
            | is_practice_limited
            | is_ps_injured
        )

        filtered = merged[relevant_mask].copy()

        # If a specific week was requested, filter by week
        if target_week is not None:
            filtered = filtered[filtered["week"] == target_week].copy()

        # 9. Apply Categorization, Detail Description & Health Impact Weights
        categories = filtered.apply(self.categorize_record, axis=1)
        cat_df = pd.DataFrame(categories.tolist(), index=filtered.index)
        filtered = pd.concat([filtered, cat_df], axis=1)

        # 10. Select and Order Output Columns
        output_columns = [
            "season",
            "week",
            "game_id",
            "game_date",
            "team",
            "opponent",
            "is_home",
            "surface",
            "team_had_game",
            "player_name",
            "first_name",
            "last_name",
            "position",
            "position_group",
            "depth_chart_position",
            "depth_chart_rank",
            "is_starter",
            "jersey_number",
            "years_exp",
            "gsis_id",
            "pfr_id",
            "roster_status",
            "roster_status_code",
            "roster_status_desc",
            "report_status",
            "practice_status",
            "primary_injury",
            "secondary_injury",
            "injury_source",
            "game_missed",
            "missed_reason_category",
            "missed_reason_detail",
            "health_impact_weight",
            "total_snaps",
            "offense_snaps",
            "defense_snaps",
            "st_snaps",
            "offense_pct",
            "defense_pct",
        ]

        # Rename columns to match output format
        if "full_name" in filtered.columns and "player_name" not in filtered.columns:
            filtered["player_name"] = filtered["full_name"]
        if "status" in filtered.columns and "roster_status" not in filtered.columns:
            filtered["roster_status"] = filtered["status"]
        if "status_description_abbr" in filtered.columns and "roster_status_code" not in filtered.columns:
            filtered["roster_status_code"] = filtered["status_description_abbr"]

        existing_cols = [c for c in output_columns if c in filtered.columns]
        result = filtered[existing_cols].copy()

        # Sort logically by week, team, position_group, player_name
        sort_cols = [c for c in ["season", "week", "team", "position_group", "player_name"] if c in result.columns]
        if sort_cols:
            result = result.sort_values(sort_cols, ascending=[True, True, True, True, True]).reset_index(drop=True)

        return result
