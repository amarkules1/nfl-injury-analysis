"""
NFL Player Play Likelihood Prediction & Upcoming Week Health Projection Model.

Builds and evaluates a machine learning regression model (Logistic Regression) to predict
the probability a player plays in their game in the upcoming week based on:
  1. Recent games played or missed (consecutive games missed, missed last game, missed rate last 3 games)
  2. Injury report status (Questionable, Doubtful, Out, Unlisted)
  3. Practice participation reports (Did Not Participate, Limited, Full, Not Listed)
  4. Diagnosed injury types (Knee, Hamstring, Ankle, Concussion, Shoulder, etc.)
  5. Roster status (Active, Reserve/IR, Inactive)

Uses these predicted player probabilities to project:
  - Team Healthiness Scores for the upcoming week
  - Unit-level projected health (QB, OL, Skill, Front, DB)
  - Upcoming week matchup health advantage and swing players
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss, accuracy_score

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR, DEFAULT_SEASON


class PlayerPlayPredictor:
    """Logistic regression model predicting player game availability and team health projections."""

    TOP_INJURIES = [
        "knee", "ankle", "hamstring", "shoulder", "concussion",
        "groin", "calf", "quad", "foot", "back", "neck",
        "hip", "illness", "chest", "ribs", "hand", "wrist", "thumb", "elbow"
    ]

    def __init__(self):
        self.model_pipeline: Optional[Pipeline] = None
        self.feature_columns: List[str] = []

    @staticmethod
    def normalize_injury_type(injury: Optional[str]) -> str:
        """Categorize raw injury string into standard injury category."""
        if not isinstance(injury, str) or not injury.strip():
            return "none"
        inj = injury.strip().lower()
        if "not injury related" in inj or "rest" in inj or "personal" in inj:
            return "rest_personal"
        if "reserve" in inj or "undisclosed" in inj:
            return "undisclosed_reserve"
        for top_inj in PlayerPlayPredictor.TOP_INJURIES:
            if top_inj in inj:
                return top_inj
        return "other"

    @staticmethod
    def normalize_practice_status(status: Optional[str]) -> str:
        """Map practice report status to standard category."""
        if not isinstance(status, str) or not status.strip():
            return "none"
        st = status.strip().lower()
        if "did not participate" in st or "dnp" in st:
            return "dnp"
        if "limited" in st or "lp" in st:
            return "limited"
        if "full" in st or "fp" in st:
            return "full"
        return "none"

    @staticmethod
    def normalize_report_status(status: Optional[str], roster_status: Optional[str], practice_status: Optional[str] = None) -> str:
        """Map game injury report status & pre-game roster status."""
        rst = str(roster_status or "").upper()
        pst = str(practice_status or "").lower()

        if isinstance(status, str) and status.strip():
            st = status.strip().lower()
            if "out" in st:
                return "out"
            if "doubtful" in st:
                return "doubtful"
            if "questionable" in st:
                return "questionable"

        if rst == "RES":
            if "full" in pst or "fp" in pst:
                return "reserve_practicing_full"
            elif "limited" in pst or "lp" in pst:
                return "reserve_practicing_limited"
            else:
                return "reserve_ir"

        return "unlisted"

    def compute_recent_game_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute player's recent game history leading into each week:
          - missed_last_game: Did the player miss the team's immediately prior game?
          - consecutive_games_missed: How many consecutive games prior to this week did the player miss?
          - missed_rate_last_3: Fraction of team's last 3 games missed.
        """
        records = []
        # Sort by player and week
        df_sorted = df.sort_values(["season", "team", "player_name", "week"]).copy()

        for (season, team, player), group in df_sorted.groupby(["season", "team", "player_name"]):
            group = group.sort_values("week")
            missed_history = []

            for idx, row in group.iterrows():
                # History before this current game
                if len(missed_history) == 0:
                    missed_last = 0
                    consec_missed = 0
                    rate_last_3 = 0.0
                else:
                    missed_last = 1 if missed_history[-1] else 0
                    # Count consecutive missed from tail
                    consec = 0
                    for m in reversed(missed_history):
                        if m:
                            consec += 1
                        else:
                            break
                    consec_missed = consec
                    recent_3 = missed_history[-3:]
                    rate_last_3 = sum(recent_3) / len(recent_3)

                is_missed = bool(row.get("game_missed", False))
                missed_history.append(is_missed)

                records.append({
                    "row_index": idx,
                    "missed_last_game": missed_last,
                    "consecutive_games_missed": consec_missed,
                    "missed_rate_last_3": rate_last_3,
                    "prior_games_tracked": len(missed_history) - 1,
                })

        rec_df = pd.DataFrame(records).set_index("row_index")
        cols_to_drop = [c for c in rec_df.columns if c in df.columns]
        base_df = df.drop(columns=cols_to_drop) if cols_to_drop else df
        return base_df.join(rec_df)

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series], pd.DataFrame]:
        """Extract and clean feature matrix X, target y, and aligned data."""
        data = self.compute_recent_game_features(df)

        if "team_had_game" in data.columns:
            data = data[data["team_had_game"] == True].copy()

        X = pd.DataFrame(index=data.index)
        X["missed_last_game"] = data["missed_last_game"].fillna(0).astype(int)
        X["consecutive_games_missed"] = data["consecutive_games_missed"].fillna(0).astype(int)
        X["missed_rate_last_3"] = data["missed_rate_last_3"].fillna(0.0).astype(float)
        X["is_starter"] = data["is_starter"].fillna(False).astype(int)

        X["injury_type"] = data["primary_injury"].apply(self.normalize_injury_type)
        X["practice_status"] = data["practice_status"].apply(self.normalize_practice_status)
        X["report_status"] = data.apply(
            lambda r: self.normalize_report_status(r.get("report_status"), r.get("roster_status"), r.get("practice_status")), axis=1
        )
        X["position_group"] = data["position_group"].fillna("OTHER").astype(str)

        # Target: 1 = Played in game, 0 = Missed game
        y = None
        if "game_missed" in data.columns:
            y = (1 - data["game_missed"].astype(int)).astype(int)

        return X, y, data

    def train(self, historical_dfs: List[pd.DataFrame]):
        """Train the regression model on historical player-game records."""
        combined_df = pd.concat(historical_dfs, ignore_index=True)
        X, y, _ = self.prepare_features(combined_df)

        numeric_features = ["missed_last_game", "consecutive_games_missed", "missed_rate_last_3", "is_starter"]
        categorical_features = ["injury_type", "practice_status", "report_status", "position_group"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
            ]
        )

        clf = LogisticRegression(
            C=0.8,
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42,
        )

        pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ])

        pipeline.fit(X, y)
        self.model_pipeline = pipeline

        # Evaluation metrics on training data
        y_prob = pipeline.predict_proba(X)[:, 1]
        y_pred = pipeline.predict(X)
        auc = roc_auc_score(y, y_prob)
        brier = brier_score_loss(y, y_prob)
        acc = accuracy_score(y, y_pred)

        print("\n[Player Availability Regression Model Trained]")
        print(f"   Training Samples: {len(X):,} player-games")
        print(f"   ROC AUC Score:    {auc:.4f}")
        print(f"   Accuracy:         {acc * 100:.2f}%")
        print(f"   Brier Score Loss: {brier:.4f}")

    def predict_play_probabilities(self, df_upcoming: pd.DataFrame) -> pd.DataFrame:
        """
        Generate play probabilities for each player in upcoming games.
        Returns enriched DataFrame with play_probability and qualitative labels.
        """
        if self.model_pipeline is None:
            raise RuntimeError("Model must be trained before predicting.")

        X, _, data = self.prepare_features(df_upcoming)
        probs = self.model_pipeline.predict_proba(X)[:, 1]

        res = data.copy()
        res["team"] = res["team"].replace({"LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV", "WSH": "WAS"})
        res["play_probability"] = np.round(probs, 3)

        # Apply strict domain calibrations based on NFL rules and practice participation reality
        
        # 1. Ruled Out on official Friday injury report: strictly cannot play under NFL rules
        is_ruled_out = res["report_status"].astype(str).str.lower().str.contains("out", na=False)
        res.loc[is_ruled_out, "play_probability"] = 0.02

        # 2. Reserve / IR or Reserve / PUP players:
        is_res = res["roster_status"] == "RES"
        
        # 2a. On IR with NO practice participation or DNP -> Shut down on IR, cannot play (0.02)
        has_no_practice = (
            res["practice_status"].isna() | 
            (res["practice_status"].astype(str).str.strip() == "") | 
            res["practice_status"].astype(str).str.contains("Did Not Participate", case=False, na=False)
        )
        res.loc[is_res & has_no_practice, "play_probability"] = 0.02

        # 2b. On IR with Full Practice -> 21-day practice window open, full reps, expected activation
        is_res_full = is_res & res["practice_status"].astype(str).str.contains("Full Participation", case=False, na=False) & ~is_ruled_out
        res.loc[is_res_full, "play_probability"] = np.clip(np.maximum(res.loc[is_res_full, "play_probability"], 0.85), 0.80, 0.95)

        # 2c. On IR with Limited Practice -> 21-day practice window open, limited reps, game-time activation decision
        is_res_limited = is_res & res["practice_status"].astype(str).str.contains("Limited Participation", case=False, na=False) & ~is_ruled_out
        res.loc[is_res_limited, "play_probability"] = np.clip(res.loc[is_res_limited, "play_probability"], 0.40, 0.52)

        # 3. Active Roster (ACT) players:
        is_act = res["roster_status"] == "ACT"
        
        # 3a. Healthy / Unlisted + Full Practice (or healthy active) -> >= 95%
        is_healthy = is_act & res["report_status"].isna() & ~res["practice_status"].astype(str).str.contains("Did Not Participate", case=False, na=False)
        res.loc[is_healthy, "play_probability"] = np.maximum(res.loc[is_healthy, "play_probability"], 0.95)

        # 3b. Questionable + Full Practice -> historically ~82% play rate
        is_q_full = (res["report_status"] == "Questionable") & res["practice_status"].astype(str).str.contains("Full Participation", case=False, na=False)
        res.loc[is_q_full, "play_probability"] = np.clip(np.maximum(res.loc[is_q_full, "play_probability"], 0.82), 0.78, 0.90)

        # 3c. Questionable + Limited Practice -> historically ~58% play rate (game-time decision)
        is_q_limited = (res["report_status"] == "Questionable") & res["practice_status"].astype(str).str.contains("Limited Participation", case=False, na=False)
        res.loc[is_q_limited, "play_probability"] = np.clip(res.loc[is_q_limited, "play_probability"], 0.52, 0.65)

        # 3d. Questionable + DNP -> historically ~35% play rate
        is_q_dnp = (res["report_status"] == "Questionable") & res["practice_status"].astype(str).str.contains("Did Not Participate", case=False, na=False)
        res.loc[is_q_dnp, "play_probability"] = np.clip(res.loc[is_q_dnp, "play_probability"], 0.28, 0.40)

        # 3e. Doubtful + DNP -> < 5% play rate
        is_doubtful_dnp = (res["report_status"] == "Doubtful") & res["practice_status"].astype(str).str.contains("Did Not Participate", case=False, na=False)
        res.loc[is_doubtful_dnp, "play_probability"] = np.minimum(res.loc[is_doubtful_dnp, "play_probability"], 0.05)

        # 3f. Doubtful + Limited -> ~15-20% play rate
        is_doubtful_limited = (res["report_status"] == "Doubtful") & res["practice_status"].astype(str).str.contains("Limited Participation", case=False, na=False)
        res.loc[is_doubtful_limited, "play_probability"] = np.clip(res.loc[is_doubtful_limited, "play_probability"], 0.12, 0.22)

        # Categorical likelihood label
        def get_likelihood_label(p):
            if p >= 0.80:
                return "Highly Likely"
            elif p >= 0.60:
                return "Probable / Leaning Play"
            elif p >= 0.40:
                return "Toss-Up / Game-Time Decision"
            elif p >= 0.15:
                return "Doubtful"
            else:
                return "Out / Sidelined"

        res["play_likelihood_label"] = res["play_probability"].apply(get_likelihood_label)
        return res

    def project_upcoming_team_health(
        self,
        predicted_players_df: pd.DataFrame,
        games_df: pd.DataFrame,
        season: int,
        upcoming_week: int,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calculate expected team healthiness scores and matchup previews for upcoming week games
        based on probabilistic player availability.
        """
        # Filter to upcoming week players
        w_players = predicted_players_df[predicted_players_df["week"] == upcoming_week].copy()
        w_players["team"] = w_players["team"].replace({"LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV", "WSH": "WAS"})

        # Deduplicate players (keep lowest probability or active record if duplicates exist)
        w_players = w_players.sort_values("play_probability").groupby(["team", "player_name"]).first().reset_index()

        team_projections = {}
        for team, group in w_players.groupby("team"):
            score = 100.0
            unit_scores = {
                "QB": 100.0,
                "OL": 100.0,
                "SKILL": 100.0,
                "FRONT": 100.0,
                "DB": 100.0,
            }

            key_swing_players = []
            confirmed_out_starters = []

            for _, row in group.iterrows():
                pos_grp = str(row.get("position_group", "")).upper()
                is_starter = bool(row.get("is_starter", False))
                p_play = float(row.get("play_probability", 1.0))
                p_miss = 1.0 - p_play
                p_name = str(row.get("player_name", "Unknown"))
                rep_stat = str(row.get("report_status", "")).strip()

                # Unit mapping
                unit_key = None
                if pos_grp == "QB":
                    unit_key = "QB"
                elif pos_grp in ["OL", "T", "G", "C"]:
                    unit_key = "OL"
                elif pos_grp in ["WR", "RB", "TE"]:
                    unit_key = "SKILL"
                elif pos_grp in ["DL", "LB"]:
                    unit_key = "FRONT"
                elif pos_grp in ["CB", "S"]:
                    unit_key = "DB"

                # Expected Penalty calculation
                if pos_grp == "QB" and is_starter:
                    # Expected lost game penalty + expected active-hurt penalty
                    expected_penalty = (p_miss * 22.0) + (p_play * (7.0 if rep_stat in ["Questionable", "Doubtful"] else 0.0))
                    score -= expected_penalty
                    if unit_key:
                        unit_scores[unit_key] -= (p_miss * 60.0) + (p_play * 25.0 if rep_stat in ["Questionable", "Doubtful"] else 0.0)

                    if p_miss > 0.80:
                        confirmed_out_starters.append(f"{p_name} (QB)")
                    elif 0.20 <= p_miss <= 0.80:
                        key_swing_players.append(f"{p_name} (QB: {int(p_play*100)}% chance)")

                elif is_starter:
                    expected_penalty = (p_miss * 4.5) + (p_play * (1.8 if rep_stat == "Questionable" else (3.5 if rep_stat == "Doubtful" else 0.0)))
                    score -= expected_penalty
                    if unit_key:
                        unit_scores[unit_key] -= (p_miss * 18.0) + (p_play * (8.0 if rep_stat == "Questionable" else (12.0 if rep_stat == "Doubtful" else 0.0)))

                    if p_miss > 0.80:
                        confirmed_out_starters.append(f"{p_name} ({pos_grp})")
                    elif 0.20 <= p_miss <= 0.80:
                        key_swing_players.append(f"{p_name} ({pos_grp}: {int(p_play*100)}% chance)")

                else:
                    # Depth / backup player expected penalty
                    expected_penalty = (p_miss * 1.0) + (p_play * (0.4 if rep_stat in ["Questionable", "Doubtful"] else 0.0))
                    score -= expected_penalty
                    if unit_key:
                        unit_scores[unit_key] -= (p_miss * 4.0)

            # Bound health scores to [10.0, 100.0]
            final_score = max(10.0, min(100.0, round(score, 1)))
            for k in unit_scores:
                unit_scores[k] = max(0.0, min(100.0, round(unit_scores[k], 1)))

            team_projections[team] = {
                "season": season,
                "week": upcoming_week,
                "team": team,
                "is_bye": False,
                "carried_from_week": None,
                "projected_health_score": final_score,
                "key_missing_starters": "; ".join(confirmed_out_starters[:6]),
                "swing_players": "; ".join(key_swing_players[:5]),
                "qb_unit_health": unit_scores["QB"],
                "ol_unit_health": unit_scores["OL"],
                "skill_unit_health": unit_scores["SKILL"],
                "front_unit_health": unit_scores["FRONT"],
                "secondary_unit_health": unit_scores["DB"],
            }

        # Ensure all 32 NFL teams are present in team_projections (including bye teams)
        all_32_teams = [
            "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
            "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
            "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
            "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"
        ]

        prior_week_scores = {}
        prior_scores_file = DATA_DIR / f"team_game_healthiness_scores_{season}.csv"
        if prior_scores_file.exists():
            try:
                prior_df = pd.read_csv(prior_scores_file)
                for t in all_32_teams:
                    t_rows = prior_df[prior_df["team"] == t].sort_values("week")
                    if not t_rows.empty:
                        last_row = t_rows.iloc[-1]
                        prior_week_scores[t] = {
                            "score": float(last_row.get("team_healthiness_score", 85.0)),
                            "carried_week": int(last_row.get("week", upcoming_week - 1)),
                            "qb": float(last_row.get("qb_unit_health", 85.0)),
                            "ol": float(last_row.get("ol_unit_health", 85.0)),
                            "skill": float(last_row.get("skill_unit_health", 85.0)),
                            "front": float(last_row.get("front_unit_health", 85.0)),
                            "secondary": float(last_row.get("secondary_unit_health", 85.0)),
                        }
            except Exception:
                pass

        for t in all_32_teams:
            if t not in team_projections:
                prior_data = prior_week_scores.get(t, {})
                team_projections[t] = {
                    "season": season,
                    "week": upcoming_week,
                    "team": t,
                    "is_bye": True,
                    "carried_from_week": prior_data.get("carried_week", upcoming_week - 1),
                    "projected_health_score": prior_data.get("score", 85.0),
                    "key_missing_starters": "Scheduled Bye Week",
                    "swing_players": "Scheduled Bye Week",
                    "qb_unit_health": prior_data.get("qb", 85.0),
                    "ol_unit_health": prior_data.get("ol", 85.0),
                    "skill_unit_health": prior_data.get("skill", 85.0),
                    "front_unit_health": prior_data.get("front", 85.0),
                    "secondary_unit_health": prior_data.get("secondary", 85.0),
                }

        team_proj_df = pd.DataFrame(list(team_projections.values()))

        # Matchup Projections using official schedule
        matchup_rows = []
        if not games_df.empty and "week" in games_df.columns:
            w_games = games_df[(games_df["season"] == season) & (games_df["week"] == upcoming_week)].copy()
            for _, g in w_games.iterrows():
                home = g.get("home_team")
                away = g.get("away_team")
                gameday = g.get("gameday", "")

                home_proj = team_projections.get(home, {
                    "projected_health_score": 85.0,
                    "key_missing_starters": "",
                    "swing_players": "",
                    "qb_unit_health": 85.0,
                    "ol_unit_health": 85.0,
                    "skill_unit_health": 85.0,
                    "front_unit_health": 85.0,
                    "secondary_unit_health": 85.0,
                })
                away_proj = team_projections.get(away, {
                    "projected_health_score": 85.0,
                    "key_missing_starters": "",
                    "swing_players": "",
                    "qb_unit_health": 85.0,
                    "ol_unit_health": 85.0,
                    "skill_unit_health": 85.0,
                    "front_unit_health": 85.0,
                    "secondary_unit_health": 85.0,
                })

                h_score = home_proj["projected_health_score"]
                a_score = away_proj["projected_health_score"]
                net_adv = round(h_score - a_score, 1)

                matchup_rows.append({
                    "season": season,
                    "week": upcoming_week,
                    "game_id": g.get("game_id", f"{season}_{upcoming_week:02d}_{away}_{home}"),
                    "game_date": gameday,
                    "home_team": home,
                    "away_team": away,
                    "home_projected_health": h_score,
                    "away_projected_health": a_score,
                    "net_health_advantage": net_adv,
                    "home_missing_starters": home_proj["key_missing_starters"],
                    "away_missing_starters": away_proj["key_missing_starters"],
                    "home_swing_players": home_proj["swing_players"],
                    "away_swing_players": away_proj["swing_players"],
                    "surface": g.get("surface", "unknown"),
                    "roof": g.get("roof", "unknown"),
                })

        matchup_df = pd.DataFrame(matchup_rows)
        return team_proj_df, matchup_df


def run_pipeline(season: int = DEFAULT_SEASON):
    """Run training and generate predictions and upcoming projections for season."""
    print(f"\n[Running Player Play Likelihood & Health Projection Pipeline - Season {season}]")

    # Load historical datasets for training
    training_seasons = [2023, 2024, 2025, 2026]
    hist_dfs = []
    for s in training_seasons:
        p = DATA_DIR / f"nfl_injuries_and_missed_games_{s}.csv"
        if p.exists():
            df_s = pd.read_csv(p)
            # If current season, train only on completed weeks
            if s == season:
                max_w = df_s["week"].max()
                df_s = df_s[df_s["week"] < max_w]
            hist_dfs.append(df_s)

    if not hist_dfs:
        raise FileNotFoundError("No historical injury logs found to train prediction model.")

    predictor = PlayerPlayPredictor()
    predictor.train(hist_dfs)

    # Load current season data
    curr_path = DATA_DIR / f"nfl_injuries_and_missed_games_{season}.csv"
    if not curr_path.exists():
        raise FileNotFoundError(f"Dataset for season {season} not found at {curr_path}")
    curr_df = pd.read_csv(curr_path)

    upcoming_week = int(curr_df["week"].max())
    print(f"Target Upcoming Week for Prediction: Week {upcoming_week}")

    # Generate predictions
    predicted_df = predictor.predict_play_probabilities(curr_df)

    # Save player predictions
    out_preds = DATA_DIR / f"player_play_predictions_{season}.csv"
    pred_cols = [
        "season", "week", "team", "player_name", "position", "position_group",
        "is_starter", "roster_status", "report_status", "practice_status",
        "primary_injury", "play_probability", "play_likelihood_label"
    ]
    pred_export = predicted_df[[c for c in pred_cols if c in predicted_df.columns]].copy()
    pred_export.to_csv(out_preds, index=False)
    print(f"[OK] Player play predictions saved to: {out_preds}")

    # Load games schedule for matchup projections
    from src.data_loader import DataLoader
    loader = DataLoader()
    games_df = loader.load_games(season=season)

    # Generate team projections and matchup predictions
    team_proj_df, matchup_proj_df = predictor.project_upcoming_team_health(
        predicted_players_df=predicted_df,
        games_df=games_df,
        season=season,
        upcoming_week=upcoming_week,
    )

    out_teams = DATA_DIR / f"upcoming_team_health_projections_{season}.csv"
    team_proj_df.to_csv(out_teams, index=False)
    print(f"[OK] Upcoming team health projections saved to: {out_teams}")

    out_matchups = DATA_DIR / f"upcoming_matchup_projections_{season}.csv"
    matchup_proj_df.to_csv(out_matchups, index=False)
    print(f"[OK] Upcoming matchup projections saved to: {out_matchups}")

    # Mirror to frontend public and dist data folders
    for dest_dir in [
        PROJECT_ROOT / "frontend" / "public" / "data",
        PROJECT_ROOT / "frontend" / "dist" / "data",
    ]:
        if dest_dir.exists():
            try:
                pred_export.to_csv(dest_dir / f"player_play_predictions_{season}.csv", index=False)
                team_proj_df.to_csv(dest_dir / f"upcoming_team_health_projections_{season}.csv", index=False)
                matchup_proj_df.to_csv(dest_dir / f"upcoming_matchup_projections_{season}.csv", index=False)
                print(f"[OK] Synced projections to frontend: {dest_dir}")
            except Exception:
                pass

    # Display Top Highlights
    print("\n" + "=" * 70)
    print(f"UPCOMING WEEK {upcoming_week} PROJECTED HEALTH RANKINGS (Top 5 & Bottom 5):")
    sorted_teams = team_proj_df.sort_values("projected_health_score", ascending=False)
    for rank, (_, row) in enumerate(sorted_teams.head(5).iterrows(), 1):
        print(f"  {rank}. {row['team']:<5} : {row['projected_health_score']:.1f}%")

    print("\nMOST VULNERABLE / INJURY-STRAINED TEAMS (Upcoming Week):")
    for rank, (_, row) in enumerate(sorted_teams.tail(5).iterrows(), 1):
        print(f"  {rank}. {row['team']:<5} : {row['projected_health_score']:.1f}% | Missing: {row['key_missing_starters'][:40]}")

    print("\nSAMPLE UPCOMING MATCHUPS WITH PROJECTED HEALTH ADVANTAGE:")
    for _, m in matchup_proj_df.head(4).iterrows():
        sign = "+" if m["net_health_advantage"] > 0 else ""
        print(f"  {m['away_team']} ({m['away_projected_health']}%) @ {m['home_team']} ({m['home_projected_health']}%) -> {m['home_team']} Adv: {sign}{m['net_health_advantage']}%")
        if m["home_swing_players"] or m["away_swing_players"]:
            print(f"     Swing: {m['home_team']}: {m['home_swing_players'][:40]} | {m['away_team']}: {m['away_swing_players'][:40]}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    s = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SEASON
    run_pipeline(s)
