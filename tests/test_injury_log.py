"""
Unit and integration tests for NFL Injury and Missed Games pipeline.
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from config import ROSTER_STATUS_MAP, POSITION_GROUPS
from src.processor import InjuryProcessor
from src.exporter import InjuryExporter
from score_healthiness import HealthScorer


class TestInjuryProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = InjuryProcessor()

    def test_position_grouping(self):
        self.assertEqual(self.processor.get_position_group("QB"), "QB")
        self.assertEqual(self.processor.get_position_group("RB"), "RB")
        self.assertEqual(self.processor.get_position_group("WR"), "WR")
        self.assertEqual(self.processor.get_position_group("TE"), "TE")
        self.assertEqual(self.processor.get_position_group("T"), "OL")
        self.assertEqual(self.processor.get_position_group("DE"), "DL")
        self.assertEqual(self.processor.get_position_group("CB"), "CB")
        self.assertEqual(self.processor.get_position_group("FS"), "S")
        self.assertEqual(self.processor.get_position_group(None), "OTHER")

    def test_categorize_reserve_injured(self):
        row = pd.Series({
            "status": "RES",
            "status_description_abbr": "R01",
            "primary_injury": "Knee",
            "team_had_game": True,
            "roster_status_desc": "Reserve / Injured (IR)",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "INJURY_IR")
        self.assertIn("Knee", res["missed_reason_detail"])
        self.assertEqual(res["health_impact_weight"], 1.0)

    def test_categorize_reserve_pup(self):
        row = pd.Series({
            "status": "RES",
            "status_description_abbr": "R04",
            "primary_injury": "ACL",
            "team_had_game": True,
            "roster_status_desc": "Reserve / Physically Unable to Perform (PUP)",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "INJURY_PUP")
        self.assertEqual(res["health_impact_weight"], 1.0)

    def test_categorize_reserve_suspension(self):
        row = pd.Series({
            "status": "RES",
            "status_description_abbr": "R40",
            "primary_injury": "",
            "team_had_game": True,
            "roster_status_desc": "Reserve / Suspension (< 1 Year)",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "SUSPENSION")
        self.assertIn("Suspended", res["missed_reason_detail"])
        self.assertEqual(res["health_impact_weight"], 1.0)

    def test_categorize_commissioner_exempt(self):
        row = pd.Series({
            "status": "EXE",
            "status_description_abbr": "E02",
            "primary_injury": "",
            "team_had_game": True,
            "roster_status_desc": "Exempt / Commissioner Permission",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "COMMISSIONER_EXEMPT")
        self.assertEqual(res["health_impact_weight"], 1.0)

    def test_categorize_healthy_scratch(self):
        row = pd.Series({
            "status": "INA",
            "status_description_abbr": "A01",
            "report_status": np.nan,
            "primary_injury": "",
            "team_had_game": True,
            "roster_status_desc": "Active",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "HEALTHY_SCRATCH")
        self.assertIn("Healthy Scratch", res["missed_reason_detail"])

    def test_categorize_inactive_injury(self):
        row = pd.Series({
            "status": "INA",
            "status_description_abbr": "A01",
            "report_status": "Out",
            "primary_injury": "Hamstring",
            "team_had_game": True,
            "roster_status_desc": "Active",
        })
        res = self.processor.categorize_record(row)
        self.assertTrue(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "INJURY_RULED_OUT")
        self.assertIn("Hamstring", res["missed_reason_detail"])

    def test_categorize_questionable_active(self):
        row = pd.Series({
            "status": "ACT",
            "status_description_abbr": "A01",
            "report_status": "Questionable",
            "primary_injury": "Ankle",
            "team_had_game": True,
            "roster_status_desc": "Active",
        })
        res = self.processor.categorize_record(row)
        self.assertFalse(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "INJURED_PLAYED_QUESTIONABLE")
        self.assertEqual(res["health_impact_weight"], 0.35)

    def test_bye_week_handling(self):
        row = pd.Series({
            "status": "RES",
            "status_description_abbr": "R01",
            "primary_injury": "Knee",
            "team_had_game": False,  # Bye week
            "roster_status_desc": "Reserve / Injured (IR)",
        })
        res = self.processor.categorize_record(row)
        self.assertFalse(res["game_missed"])
        self.assertEqual(res["missed_reason_category"], "BYE_WEEK")

    def test_injury_history_carry_forward(self):
        sample_inj = pd.DataFrame([
            {
                "week": 1,
                "gsis_id": "00-11111",
                "report_primary_injury": "Hamstring",
                "report_secondary_injury": np.nan,
                "practice_primary_injury": "Hamstring",
                "practice_secondary_injury": np.nan,
            },
            {
                "week": 2,
                "gsis_id": "00-11111",
                "report_primary_injury": "Knee",
                "report_secondary_injury": np.nan,
                "practice_primary_injury": "Knee",
                "practice_secondary_injury": np.nan,
            },
        ])
        hist_map = self.processor.build_injury_history_map(sample_inj)
        self.assertEqual(hist_map.loc["00-11111", "combined_primary_injury"], "Knee")

    def test_starter_detection_prior_season_snaps(self):
        prior_snaps = pd.DataFrame([
            {
                "game_id": f"2025_0{w}_DET_CHI",
                "pfr_player_id": "BranBr00",
                "player": "Brian Branch",
                "offense_snaps": 0,
                "defense_snaps": 60,
                "offense_pct": 0.0,
                "defense_pct": 0.95,
            }
            for w in range(1, 6)
        ])
        sets = self.processor.build_starter_detection_sets(
            prior_snaps_df=prior_snaps,
            season=2026,
        )
        self.assertIn("BranBr00", sets["pfr"])
        self.assertIn("Brian Branch", sets["names"])

    def test_starter_detection_preseason_depth_chart(self):
        dc_df = pd.DataFrame([
            {
                "dt": "2026-08-30T12:00:00Z",
                "team": "DET",
                "player_name": "Kerby Joseph",
                "gsis_id": "00-0037812",
                "pos_grp": "Base 4-3 D",
                "pos_abb": "FS",
                "pos_rank": 1,
            }
        ])
        sets = self.processor.build_starter_detection_sets(
            depth_charts_df=dc_df,
            season=2026,
        )
        self.assertIn("00-0037812", sets["gsis"])
        self.assertIn("Kerby Joseph", sets["names"])


class TestHealthScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = HealthScorer()

    def test_full_healthy_team_score(self):
        # Empty records = 0 injuries/scratches -> score is 100
        records = pd.DataFrame(columns=["position_group", "is_starter", "game_missed", "report_status", "player_name"])
        metrics = self.scorer.score_team_game(records)
        self.assertEqual(metrics["health_score"], 100.0)
        self.assertEqual(metrics["starters_out_count"], 0)

    def test_qb_out_penalty(self):
        records = pd.DataFrame([
            {
                "position_group": "QB",
                "is_starter": True,
                "game_missed": True,
                "report_status": "Out",
                "player_name": "Star QB",
            }
        ])
        metrics = self.scorer.score_team_game(records)
        self.assertEqual(metrics["health_score"], 100.0 - HealthScorer.QB_STARTER_OUT_PENALTY)
        self.assertEqual(metrics["qb_status"], "Out")
        self.assertEqual(metrics["starters_out_count"], 1)

    def test_score_all_games_net_advantage(self):
        sample_data = pd.DataFrame([
            {
                "season": 2026,
                "week": 1,
                "team": "KC",
                "opponent": "BAL",
                "is_home": True,
                "team_had_game": True,
                "position_group": "WR",
                "is_starter": False,
                "game_missed": False,
                "report_status": np.nan,
                "player_name": "Backup WR",
            },
            {
                "season": 2026,
                "week": 1,
                "team": "BAL",
                "opponent": "KC",
                "is_home": False,
                "team_had_game": True,
                "position_group": "QB",
                "is_starter": True,
                "game_missed": True,
                "report_status": "Out",
                "player_name": "Lamar Jackson",
            },
        ])
        matchups = self.scorer.score_all_games(sample_data)
        kc_row = matchups[matchups["team"] == "KC"].iloc[0]
        bal_row = matchups[matchups["team"] == "BAL"].iloc[0]

        self.assertEqual(kc_row["health_score"], 100.0)
        self.assertEqual(bal_row["health_score"], 78.0)
        self.assertEqual(kc_row["net_health_advantage"], 22.0)
        self.assertEqual(bal_row["net_health_advantage"], -22.0)

    def test_qb_starting_resolution_priority_teams(self):
        processor = InjuryProcessor()
        roster_sample = pd.DataFrame([
            {"team": "LV", "position": "QB", "full_name": "Kirk Cousins"},
            {"team": "LV", "position": "QB", "full_name": "Aidan O'Connell"},
            {"team": "CLE", "position": "QB", "full_name": "Deshaun Watson"},
            {"team": "CLE", "position": "QB", "full_name": "Dillon Gabriel"},
            {"team": "IND", "position": "QB", "full_name": "Daniel Jones"},
            {"team": "IND", "position": "QB", "full_name": "Riley Leonard"},
            {"team": "CHI", "position": "QB", "full_name": "Caleb Williams"},
            {"team": "CHI", "position": "QB", "full_name": "Case Keenum"},
            {"team": "WAS", "position": "QB", "full_name": "Jayden Daniels"},
            {"team": "WAS", "position": "QB", "full_name": "Marcus Mariota"},
        ])
        resolved = processor.resolve_team_starting_qbs(roster_sample)
        self.assertEqual(resolved["LV"], "Kirk Cousins")
        self.assertEqual(resolved["CLE"], "Deshaun Watson")
        self.assertEqual(resolved["IND"], "Daniel Jones")
        self.assertEqual(resolved["CHI"], "Caleb Williams")
        self.assertEqual(resolved["WAS"], "Jayden Daniels")

    def test_backup_qb_injury_does_not_trigger_starter_out(self):
        # When backup QB is out, score should only deduct backup penalty and qb_status remains Healthy
        records = pd.DataFrame([
            {
                "position_group": "QB",
                "is_starter": False,
                "game_missed": True,
                "report_status": "Out",
                "player_name": "Dillon Gabriel",
            }
        ])
        metrics = self.scorer.score_team_game(records)
        self.assertEqual(metrics["qb_status"], "Healthy")
        self.assertIsNone(metrics["qb_name_out"])
        self.assertEqual(metrics["health_score"], 100.0 - HealthScorer.BACKUP_OUT_PENALTY)


if __name__ == "__main__":
    unittest.main()
