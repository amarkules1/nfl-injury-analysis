"""
Unit tests for the Player Availability Prediction Model and Projections.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from src.prediction_model import PlayerPlayPredictor


class TestPredictionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = PlayerPlayPredictor()

    def test_normalize_practice_status(self):
        self.assertEqual(self.predictor.normalize_practice_status("Full Participation in Practice"), "full")
        self.assertEqual(self.predictor.normalize_practice_status("Limited Participation in Practice"), "limited")
        self.assertEqual(self.predictor.normalize_practice_status("Did Not Participate In Practice"), "dnp")
        self.assertEqual(self.predictor.normalize_practice_status(None), "none")
        self.assertEqual(self.predictor.normalize_practice_status(""), "none")

    def test_normalize_report_status(self):
        self.assertEqual(self.predictor.normalize_report_status("Questionable", "ACT"), "questionable")
        self.assertEqual(self.predictor.normalize_report_status("Doubtful", "ACT"), "doubtful")
        self.assertEqual(self.predictor.normalize_report_status("Out", "INA"), "out")
        self.assertEqual(self.predictor.normalize_report_status(None, "RES"), "reserve_ir")
        self.assertEqual(self.predictor.normalize_report_status(None, "RES", "Full Participation in Practice"), "reserve_practicing_full")
        self.assertEqual(self.predictor.normalize_report_status(None, "RES", "Limited Participation in Practice"), "reserve_practicing_limited")
        self.assertEqual(self.predictor.normalize_report_status(None, "ACT"), "unlisted")

    def test_brian_branch_full_practice_probability(self):
        csv_path = Path("frontend/public/data/player_play_predictions_2026.csv")
        self.assertTrue(csv_path.exists())
        df = pd.read_csv(csv_path)
        branch = df[(df["player_name"] == "Brian Branch") & (df["week"] == 7)]
        self.assertFalse(branch.empty, "Brian Branch must exist in week 7 predictions")
        prob = float(branch.iloc[0]["play_probability"])
        self.assertGreaterEqual(prob, 0.80, "Brian Branch practicing in full must have >= 80% play probability")
        self.assertEqual(branch.iloc[0]["play_likelihood_label"], "Highly Likely")

    def test_normalize_injury_type(self):
        self.assertEqual(self.predictor.normalize_injury_type("Hamstring"), "hamstring")
        self.assertEqual(self.predictor.normalize_injury_type("Left Knee Sprain"), "knee")
        self.assertEqual(self.predictor.normalize_injury_type("Right Ankle"), "ankle")
        self.assertEqual(self.predictor.normalize_injury_type("Concussion protocol"), "concussion")
        self.assertEqual(self.predictor.normalize_injury_type("Not injury related - resting player"), "rest_personal")
        self.assertEqual(self.predictor.normalize_injury_type(None), "none")

    def test_predictions_csv_integrity(self):
        csv_path = Path("frontend/public/data/player_play_predictions_2026.csv")
        self.assertTrue(csv_path.exists(), "player_play_predictions_2026.csv must exist in public data")
        df = pd.read_csv(csv_path)
        self.assertIn("play_probability", df.columns)
        self.assertIn("play_likelihood_label", df.columns)
        self.assertIn("is_starter", df.columns)
        self.assertTrue((df["play_probability"] >= 0.0).all())
        self.assertTrue((df["play_probability"] <= 1.0).all())

    def test_team_projections_csv_integrity(self):
        csv_path = Path("frontend/public/data/upcoming_team_health_projections_2026.csv")
        self.assertTrue(csv_path.exists(), "upcoming_team_health_projections_2026.csv must exist")
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 32, "All 32 NFL clubs must have health projections")
        self.assertIn("projected_health_score", df.columns)
        self.assertTrue((df["projected_health_score"] >= 0).all())
        self.assertTrue((df["projected_health_score"] <= 100).all())

    def test_matchup_projections_csv_integrity(self):
        csv_path = Path("frontend/public/data/upcoming_matchup_projections_2026.csv")
        self.assertTrue(csv_path.exists(), "upcoming_matchup_projections_2026.csv must exist")
        df = pd.read_csv(csv_path)
        self.assertIn("net_health_advantage", df.columns)
        self.assertIn("home_projected_health", df.columns)
        self.assertIn("away_projected_health", df.columns)


if __name__ == "__main__":
    unittest.main()
