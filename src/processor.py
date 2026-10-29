"""
Data processing module: harmonization, injury carry-forward, categorization,
starter tagging, and health impact weighting.
"""

from typing import Optional, Dict, Set
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

    @staticmethod
    def normalize_depth_charts(dc_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Normalize depth charts across modern (ESPN 2026+) and legacy (nflverse 2006-2025) schemas."""
        if dc_df is None or dc_df.empty:
            return None
        df = dc_df.copy()
        if "team" not in df.columns and "club_code" in df.columns:
            df["team"] = df["club_code"]
        if "player_name" not in df.columns and "full_name" in df.columns:
            df["player_name"] = df["full_name"]
        if "pos_abb" not in df.columns:
            if "depth_position" in df.columns:
                df["pos_abb"] = df["depth_position"]
            elif "position" in df.columns:
                df["pos_abb"] = df["position"]
        if "pos_rank" not in df.columns:
            if "depth_team" in df.columns:
                df["pos_rank"] = pd.to_numeric(df["depth_team"], errors="coerce")
            else:
                df["pos_rank"] = np.nan
        if "pos_grp" not in df.columns and "pos_abb" in df.columns:
            st_positions = {"K", "PK", "P", "LS"}
            df["pos_grp"] = np.where(df["pos_abb"].isin(st_positions), "Special Teams", "Regular")
        return df

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

    def build_starter_detection_sets(
        self,
        depth_charts_df: Optional[pd.DataFrame] = None,
        snaps_df: Optional[pd.DataFrame] = None,
        prior_snaps_df: Optional[pd.DataFrame] = None,
        prior_depth_charts_df: Optional[pd.DataFrame] = None,
        season: int = 2026,
    ) -> Dict[str, set]:
        """
        Identify players who are established starters across multiple reliable signals:
          1. Current Season Baseline/Preseason Depth Chart rank 1 (offensive & defensive positions)
          2. Current Season In-Season Depth Chart rank 1 (held rank 1 at any point before injury demotion)
          3. Current Season Snap Share when active (mean >= 50% or >= 2 games with >= 60%)
          4. Prior Season (season - 1) Snap Share when healthy (mean >= 50% with >= 3 games played)
          5. Prior Season Depth Chart rank 1 (offensive & defensive positions)
        """
        starter_gsis = set()
        starter_pfr = set()
        starter_names = set()

        # 1. Current Season Depth Charts
        if depth_charts_df is not None and not depth_charts_df.empty:
            dc_clean = depth_charts_df.copy()
            if "pos_grp" in dc_clean.columns:
                dc_clean = dc_clean[dc_clean["pos_grp"] != "Special Teams"]

            if "dt" in dc_clean.columns:
                try:
                    dc_clean["dt_ts"] = pd.to_datetime(dc_clean["dt"])
                    # Training camp / preseason final 53 baseline (Aug 15 - Sep 8)
                    pre_mask = (
                        (dc_clean["dt_ts"] >= f"{season}-08-15")
                        & (dc_clean["dt_ts"] <= f"{season}-09-08")
                        & (dc_clean["pos_rank"] == 1)
                    )
                    pre_r1 = dc_clean[pre_mask]
                    if "gsis_id" in pre_r1.columns:
                        starter_gsis.update(pre_r1["gsis_id"].dropna().unique())
                    if "player_name" in pre_r1.columns:
                        starter_names.update(pre_r1["player_name"].dropna().unique())

                    # In-season regular season rank 1 (Sep 1 onwards)
                    inseason_mask = (dc_clean["dt_ts"] >= f"{season}-09-01") & (dc_clean["pos_rank"] == 1)
                    in_r1 = dc_clean[inseason_mask]
                    if "gsis_id" in in_r1.columns:
                        starter_gsis.update(in_r1["gsis_id"].dropna().unique())
                    if "player_name" in in_r1.columns:
                        starter_names.update(in_r1["player_name"].dropna().unique())
                except Exception:
                    pass
            elif "pos_rank" in dc_clean.columns:
                try:
                    r1 = dc_clean[dc_clean["pos_rank"] == 1]
                    if "gsis_id" in r1.columns:
                        starter_gsis.update(r1["gsis_id"].dropna().unique())
                    if "player_name" in r1.columns:
                        starter_names.update(r1["player_name"].dropna().unique())
                except Exception:
                    pass

        # 2. Current Season Snap Counts (active games)
        if snaps_df is not None and not snaps_df.empty:
            off_col = "offense_snaps" if "offense_snaps" in snaps_df.columns else None
            def_col = "defense_snaps" if "defense_snaps" in snaps_df.columns else None
            s_active = snaps_df.copy()
            if off_col and def_col:
                s_active = s_active[(s_active[off_col].fillna(0) > 0) | (s_active[def_col].fillna(0) > 0)]

            if not s_active.empty and "pfr_player_id" in s_active.columns:
                s_agg = s_active.groupby("pfr_player_id").agg(
                    games_played=("game_id", "count"),
                    mean_off=("offense_pct", "mean"),
                    mean_def=("defense_pct", "mean"),
                    max_off=("offense_pct", "max"),
                    max_def=("defense_pct", "max"),
                )
                starters_curr_pfr = s_agg[
                    (s_agg["mean_off"] >= 0.50)
                    | (s_agg["mean_def"] >= 0.50)
                    | ((s_agg["games_played"] >= 2) & ((s_agg["max_off"] >= 0.60) | (s_agg["max_def"] >= 0.60)))
                ].index
                starter_pfr.update(starters_curr_pfr)

            if not s_active.empty and "player" in s_active.columns:
                s_name_agg = s_active.groupby("player").agg(
                    games_played=("game_id", "count"),
                    mean_off=("offense_pct", "mean"),
                    mean_def=("defense_pct", "mean"),
                    max_off=("offense_pct", "max"),
                    max_def=("defense_pct", "max"),
                )
                starters_curr_names = s_name_agg[
                    (s_name_agg["mean_off"] >= 0.50)
                    | (s_name_agg["mean_def"] >= 0.50)
                    | ((s_name_agg["games_played"] >= 2) & ((s_name_agg["max_off"] >= 0.60) | (s_name_agg["max_def"] >= 0.60)))
                ].index
                starter_names.update(starters_curr_names)

        # 3. Prior Season Snap Counts (starters in previous season when healthy)
        prior_year = season - 1
        if prior_snaps_df is not None and not prior_snaps_df.empty:
            p_off = "offense_snaps" if "offense_snaps" in prior_snaps_df.columns else None
            p_def = "defense_snaps" if "defense_snaps" in prior_snaps_df.columns else None
            p_active = prior_snaps_df.copy()
            if p_off and p_def:
                p_active = p_active[(p_active[p_off].fillna(0) > 0) | (p_active[p_def].fillna(0) > 0)]

            if not p_active.empty and "pfr_player_id" in p_active.columns:
                p_agg = p_active.groupby("pfr_player_id").agg(
                    games_played=("game_id", "count"),
                    mean_off=("offense_pct", "mean"),
                    mean_def=("defense_pct", "mean"),
                )
                starters_prior_pfr = p_agg[
                    (p_agg["games_played"] >= 3)
                    & ((p_agg["mean_off"] >= 0.50) | (p_agg["mean_def"] >= 0.50))
                ].index
                starter_pfr.update(starters_prior_pfr)

            if not p_active.empty and "player" in p_active.columns:
                p_name_agg = p_active.groupby("player").agg(
                    games_played=("game_id", "count"),
                    mean_off=("offense_pct", "mean"),
                    mean_def=("defense_pct", "mean"),
                )
                starters_prior_names = p_name_agg[
                    (p_name_agg["games_played"] >= 3)
                    & ((p_name_agg["mean_off"] >= 0.50) | (p_name_agg["mean_def"] >= 0.50))
                ].index
                starter_names.update(starters_prior_names)

        # 4. Prior Season Depth Charts (rank 1 at non-ST positions during prior regular season or camp)
        if prior_depth_charts_df is not None and not prior_depth_charts_df.empty:
            p_dc = prior_depth_charts_df.copy()
            if "pos_grp" in p_dc.columns:
                p_dc = p_dc[p_dc["pos_grp"] != "Special Teams"]
            if "dt" in p_dc.columns:
                try:
                    p_dc["dt_ts"] = pd.to_datetime(p_dc["dt"])
                    # Prior regular season / training camp (Aug 15 - Dec 31 of prior year)
                    prior_mask = (
                        (p_dc["dt_ts"] >= f"{prior_year}-08-15")
                        & (p_dc["dt_ts"] <= f"{prior_year}-12-31")
                        & (p_dc["pos_rank"] == 1)
                    )
                    p_r1 = p_dc[prior_mask]
                    if "gsis_id" in p_r1.columns:
                        starter_gsis.update(p_r1["gsis_id"].dropna().unique())
                    if "player_name" in p_r1.columns:
                        starter_names.update(p_r1["player_name"].dropna().unique())
                except Exception:
                    pass
            elif "pos_rank" in p_dc.columns:
                try:
                    p_r1 = p_dc[p_dc["pos_rank"] == 1]
                    if "gsis_id" in p_r1.columns:
                        starter_gsis.update(p_r1["gsis_id"].dropna().unique())
                    if "player_name" in p_r1.columns:
                        starter_names.update(p_r1["player_name"].dropna().unique())
                except Exception:
                    pass

        return {
            "gsis": starter_gsis,
            "pfr": starter_pfr,
            "names": starter_names,
        }

    @staticmethod
    def normalize_name(name: Optional[str]) -> str:
        """Normalize player name by stripping punctuation, extra spaces, and suffixes (Jr., III, etc.)."""
        if not isinstance(name, str):
            return ""
        n = name.strip()
        for sfx in [" Jr.", " Sr.", " III", " II", " IV", " Jr", " Sr"]:
            if n.endswith(sfx):
                n = n[:-len(sfx)].strip()
        return n.lower()

    def resolve_team_starting_qbs(
        self,
        roster_df: pd.DataFrame,
        snaps_df: Optional[pd.DataFrame] = None,
        depth_charts_df: Optional[pd.DataFrame] = None,
        inj_df: Optional[pd.DataFrame] = None,
        season: int = 2026,
    ) -> Dict[str, str]:
        """
        Determine the single primary starting quarterback for each NFL team (QB position ONLY).

        Factoring in:
          1. Head-to-head comparison: Who started when both QBs were healthy on the active roster?
          2. Recent offseason signings / veteran starter contracts (e.g. Kirk Cousins on LV,
             Deshaun Watson on CLE, Daniel Jones on IND).
          3. Draft capital / pedigree (e.g. Caleb Williams #1 overall for CHI,
             Jayden Daniels #2 overall for WAS).
          4. Relief snaps while the starter was injured do NOT make the backup the starting QB.
        """
        priority_starters: Dict[str, str] = {
            "LV": "Kirk Cousins",
            "CLE": "Deshaun Watson",
            "IND": "Daniel Jones",
            "CHI": "Caleb Williams",
            "WAS": "Jayden Daniels",
        } if season == 2026 else {}

        team_starting_qbs: Dict[str, str] = {}
        if roster_df is None or roster_df.empty:
            return priority_starters

        qbs = roster_df[roster_df["position"] == "QB"].copy()
        if "player_name" not in qbs.columns and "full_name" in qbs.columns:
            qbs["player_name"] = qbs["full_name"]

        teams = qbs["team"].dropna().unique()

        for team in sorted(teams):
            if team in priority_starters:
                team_starting_qbs[team] = priority_starters[team]
                continue

            t_roster_qbs = qbs[qbs["team"] == team]["player_name"].dropna().unique().tolist()
            if not t_roster_qbs:
                continue
            if len(t_roster_qbs) == 1:
                team_starting_qbs[team] = t_roster_qbs[0]
                continue

            # Analyze snaps for this team's QBs in current season
            s_team = pd.DataFrame()
            if snaps_df is not None and not snaps_df.empty and "position" in snaps_df.columns:
                s_team = snaps_df[(snaps_df["team"] == team) & (snaps_df["position"] == "QB")]

            if not s_team.empty:
                s_starts = s_team[s_team["offense_pct"] >= 0.50].groupby("player").agg(
                    starts=("game_id", "count"),
                    total_snaps=("offense_snaps", "sum")
                ).reset_index().sort_values(["starts", "total_snaps"], ascending=False)

                if not s_starts.empty:
                    candidates = s_starts["player"].tolist()
                    if len(candidates) == 1:
                        team_starting_qbs[team] = candidates[0]
                        continue

                    # Multiple QBs started at least one game (e.g. starter injured, backup in relief)
                    # Compare top candidates: who started when BOTH were healthy?
                    p1, p2 = candidates[0], candidates[1]

                    out_weeks_p1 = set()
                    out_weeks_p2 = set()
                    if inj_df is not None and not inj_df.empty:
                        name_col_inj = "player_name" if "player_name" in inj_df.columns else "full_name"
                        out_weeks_p1 = set(inj_df[
                            (inj_df["team"] == team)
                            & (inj_df[name_col_inj].apply(self.normalize_name) == self.normalize_name(p1))
                            & (inj_df["report_status"] == "Out")
                        ]["week"].dropna().unique())
                        out_weeks_p2 = set(inj_df[
                            (inj_df["team"] == team)
                            & (inj_df[name_col_inj].apply(self.normalize_name) == self.normalize_name(p2))
                            & (inj_df["report_status"] == "Out")
                        ]["week"].dropna().unique())

                    all_weeks = set(s_team["week"].dropna().unique())
                    mutual_healthy_weeks = all_weeks - out_weeks_p1 - out_weeks_p2

                    s_mutual = s_team[s_team["week"].isin(mutual_healthy_weeks)]
                    if not s_mutual.empty:
                        m_snaps = s_mutual.groupby("player")["offense_snaps"].sum()
                        m1 = m_snaps.get(p1, 0)
                        m2 = m_snaps.get(p2, 0)
                        if m1 > m2:
                            team_starting_qbs[team] = p1
                            continue
                        elif m2 > m1:
                            team_starting_qbs[team] = p2
                            continue

                    # If mutual comparison is tied, check draft capital
                    r_qbs = qbs[qbs["player_name"].isin([p1, p2])]
                    if "draft_number" in r_qbs.columns:
                        draft_ranks = r_qbs.dropna(subset=["draft_number"]).sort_values("draft_number")
                        if not draft_ranks.empty:
                            team_starting_qbs[team] = draft_ranks.iloc[0]["player_name"]
                            continue

                    team_starting_qbs[team] = p1
                    continue

            # Fallback to depth charts pos_rank == 1
            if depth_charts_df is not None and not depth_charts_df.empty:
                team_col_dc = "team" if "team" in depth_charts_df.columns else "club_code"
                pos_col_dc = "pos_abb" if "pos_abb" in depth_charts_df.columns else ("position" if "position" in depth_charts_df.columns else None)
                rank_col_dc = "pos_rank" if "pos_rank" in depth_charts_df.columns else "depth_team"
                dc_mask = (depth_charts_df[team_col_dc] == team) & (depth_charts_df[rank_col_dc].astype(str) == "1")
                if pos_col_dc:
                    dc_mask = dc_mask & (depth_charts_df[pos_col_dc] == "QB")
                dc_team = depth_charts_df[dc_mask]
                if not dc_team.empty:
                    dc_name_col = "player_name" if "player_name" in dc_team.columns else "full_name"
                    team_starting_qbs[team] = dc_team.iloc[-1][dc_name_col]
                    continue

            team_starting_qbs[team] = t_roster_qbs[0]

        return team_starting_qbs

    def process(
        self,
        roster_df: pd.DataFrame,
        inj_df: pd.DataFrame,
        games_df: pd.DataFrame,
        snaps_df: Optional[pd.DataFrame] = None,
        depth_charts_df: Optional[pd.DataFrame] = None,
        season: int = 2026,
        target_week: Optional[int] = None,
        prior_snaps_df: Optional[pd.DataFrame] = None,
        prior_depth_charts_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Merge, categorize, enrich, and filter NFL injury and missed game records.
        """
        # 0. Normalize depth charts schemas across modern and legacy seasons
        depth_charts_df = self.normalize_depth_charts(depth_charts_df)
        prior_depth_charts_df = self.normalize_depth_charts(prior_depth_charts_df)

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
        merged["depth_chart_position"] = np.nan
        if depth_charts_df is not None and not depth_charts_df.empty and "gsis_id" in depth_charts_df.columns:
            try:
                sort_col = "dt" if "dt" in depth_charts_df.columns else ("week" if "week" in depth_charts_df.columns else None)
                latest_dc = depth_charts_df.sort_values(sort_col).groupby("gsis_id").last() if sort_col else depth_charts_df.groupby("gsis_id").last()
                merged["depth_chart_rank"] = merged["gsis_id"].map(latest_dc["pos_rank"])
                if "pos_abb" in latest_dc.columns:
                    merged["depth_chart_position"] = merged["gsis_id"].map(latest_dc["pos_abb"])

                # Best offensive/defensive rank (preserve rank 1 for starters demoted on IR)
                dc_off_def = depth_charts_df.copy()
                if "pos_grp" in dc_off_def.columns:
                    dc_off_def = dc_off_def[dc_off_def["pos_grp"] != "Special Teams"]
                best_dc = dc_off_def.groupby("gsis_id")["pos_rank"].min()
                rank1_gsis = set(best_dc[best_dc == 1].index)
                merged.loc[merged["gsis_id"].isin(rank1_gsis), "depth_chart_rank"] = 1.0

                # Also refine position_group if depth chart position is more specific (e.g. SS/FS -> S rather than generic CB)
                if "depth_chart_position" in merged.columns:
                    refined_group = merged["depth_chart_position"].apply(self.get_position_group)
                    is_better = (refined_group != "OTHER") & (
                        (merged["position"] == "DB") | (merged["position_group"] == "OTHER")
                    )
                    merged.loc[is_better, "position_group"] = refined_group[is_better]
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

        # Assign player_name from full_name if not already present
        if "player_name" not in merged.columns and "full_name" in merged.columns:
            merged["player_name"] = merged["full_name"]

        # Determine Starter Tag: Multi-signal starter detection
        starter_sets = self.build_starter_detection_sets(
            depth_charts_df=depth_charts_df,
            snaps_df=snaps_df,
            prior_snaps_df=prior_snaps_df,
            prior_depth_charts_df=prior_depth_charts_df,
            season=season,
        )

        name_col = merged["player_name"] if "player_name" in merged.columns else merged["full_name"]
        merged["is_starter"] = (
            merged["gsis_id"].isin(starter_sets["gsis"])
            | merged["pfr_id"].isin(starter_sets["pfr"])
            | name_col.isin(starter_sets["names"])
            | (merged["depth_chart_rank"] == 1)
            | (merged["offense_pct"] >= 0.50)
            | (merged["defense_pct"] >= 0.50)
        )

        # Ensure established starters have depth_chart_rank 1.0 rather than NaN
        merged.loc[merged["is_starter"] & merged["depth_chart_rank"].isna(), "depth_chart_rank"] = 1.0

        # 7b. Quarterback Position ONLY:
        # Enforce exact single-starter resolution using head-to-head healthy starts,
        # draft pedigree, offseason signings, and contract/salary weighting.
        qb_starters = self.resolve_team_starting_qbs(
            roster_df=roster_clean,
            snaps_df=snaps_df,
            depth_charts_df=depth_charts_df,
            inj_df=inj_df,
            season=season,
        )

        is_qb = merged["position_group"] == "QB"
        if is_qb.any():
            def check_qb_starter(row):
                team = row.get("team")
                player = row.get("player_name") or row.get("full_name") or ""
                target_qb = qb_starters.get(team)
                if not target_qb:
                    return False
                return self.normalize_name(player) == self.normalize_name(target_qb)

            merged.loc[is_qb, "is_starter"] = merged[is_qb].apply(check_qb_starter, axis=1)
            # Ensure starting QB has depth_chart_rank 1.0, backups >= 2.0
            merged.loc[is_qb & merged["is_starter"], "depth_chart_rank"] = 1.0
            merged.loc[is_qb & (~merged["is_starter"]) & (merged["depth_chart_rank"] == 1.0), "depth_chart_rank"] = 2.0

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
