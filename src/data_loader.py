"""
Data loading and caching module for NFL datasets (injuries, rosters, schedules, snap counts, depth charts).
"""

import os
import time
from pathlib import Path
from typing import Optional
import urllib.request
import pandas as pd

from config import DATA_URLS, CACHE_DIR, DEFAULT_SEASON


class DataLoader:
    """Handles fetching and caching NFL datasets from nflverse releases."""

    def __init__(self, cache_dir: Path = CACHE_DIR, cache_ttl_hours: int = 12):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_hours * 3600

    def _is_cache_valid(self, cache_file: Path, force_refresh: bool) -> bool:
        """Check if local cache file is present and within TTL."""
        if force_refresh or not cache_file.exists():
            return False
        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < self.cache_ttl_seconds

    def _download_file(self, url: str, target_file: Path) -> bool:
        """Download remote file to target location with browser headers."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NFL-Injury-Analysis/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(target_file, "wb") as out:
                out.write(resp.read())
            return True
        except Exception as e:
            return False

    def load_injuries(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load weekly injury reports for the specified season.
        Contains report status (Out/Questionable/Doubtful), practice status, primary and secondary injury.
        """
        parquet_cache = self.cache_dir / f"injuries_{season}.parquet"
        csv_cache = self.cache_dir / f"injuries_{season}.csv"

        if self._is_cache_valid(parquet_cache, force_refresh):
            return pd.read_parquet(parquet_cache)
        if self._is_cache_valid(csv_cache, force_refresh):
            return pd.read_csv(csv_cache)

        # Try downloading Parquet first
        url_parquet = DATA_URLS["injuries_parquet"].format(season=season)
        if self._download_file(url_parquet, parquet_cache):
            return pd.read_parquet(parquet_cache)

        # Fallback to CSV
        url_csv = DATA_URLS["injuries_csv"].format(season=season)
        if self._download_file(url_csv, csv_cache):
            return pd.read_csv(csv_cache)

        raise FileNotFoundError(f"Could not load injuries data for season {season} from {url_parquet} or {url_csv}")

    def load_rosters(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load week-by-week player roster designations.
        Contains status (ACT, RES, INA, DEV, EXE, CUT), status_description_abbr (R01, R04, etc.),
        and player metadata.
        """
        parquet_cache = self.cache_dir / f"roster_weekly_{season}.parquet"
        csv_cache = self.cache_dir / f"roster_weekly_{season}.csv"

        if self._is_cache_valid(parquet_cache, force_refresh):
            return pd.read_parquet(parquet_cache)
        if self._is_cache_valid(csv_cache, force_refresh):
            return pd.read_csv(csv_cache)

        url_parquet = DATA_URLS["roster_parquet"].format(season=season)
        if self._download_file(url_parquet, parquet_cache):
            return pd.read_parquet(parquet_cache)

        url_csv = DATA_URLS["roster_csv"].format(season=season)
        if self._download_file(url_csv, csv_cache):
            return pd.read_csv(csv_cache)

        raise FileNotFoundError(f"Could not load weekly roster data for season {season}")

    def load_games(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load schedules and games information including home/away, surface, roof, and dates.
        """
        parquet_cache = self.cache_dir / "games.parquet"
        csv_cache = self.cache_dir / "games.csv"

        df_all = None
        if self._is_cache_valid(parquet_cache, force_refresh):
            df_all = pd.read_parquet(parquet_cache)
        elif self._is_cache_valid(csv_cache, force_refresh):
            df_all = pd.read_csv(csv_cache)
        else:
            if self._download_file(DATA_URLS["games_parquet"], parquet_cache):
                df_all = pd.read_parquet(parquet_cache)
            elif self._download_file(DATA_URLS["games_csv"], csv_cache):
                df_all = pd.read_csv(csv_cache)

        if df_all is None:
            raise FileNotFoundError("Could not load NFL schedules/games data")

        # Filter to requested season if present
        if "season" in df_all.columns:
            return df_all[df_all["season"] == season].copy()
        return df_all

    def load_snap_counts(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load weekly player snap counts (offense, defense, special teams).
        Optional / supplementary data.
        """
        csv_cache = self.cache_dir / f"snap_counts_{season}.csv"

        if self._is_cache_valid(csv_cache, force_refresh):
            return pd.read_csv(csv_cache)

        url_csv = DATA_URLS["snaps_csv"].format(season=season)
        if self._download_file(url_csv, csv_cache):
            return pd.read_csv(csv_cache)

        # Snap counts may not yet be published for a very new week; return empty DataFrame
        return pd.DataFrame()

    def load_depth_charts(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load depth charts to identify starter vs backup depth rank.
        Optional / supplementary data.
        """
        parquet_cache = self.cache_dir / f"depth_charts_{season}.parquet"
        csv_cache = self.cache_dir / f"depth_charts_{season}.csv"

        if self._is_cache_valid(parquet_cache, force_refresh):
            return pd.read_parquet(parquet_cache)
        if self._is_cache_valid(csv_cache, force_refresh):
            return pd.read_csv(csv_cache)

        url_parquet = DATA_URLS["depth_charts_parquet"].format(season=season)
        if self._download_file(url_parquet, parquet_cache):
            return pd.read_parquet(parquet_cache)

        url_csv = DATA_URLS["depth_charts_csv"].format(season=season)
        if self._download_file(url_csv, csv_cache):
            return pd.read_csv(csv_cache)

        return pd.DataFrame()

    def detect_latest_available_season(self) -> int:
        """Detect the latest season available in nflverse datasets."""
        for candidate_year in [2027, 2026, 2025, 2024]:
            try:
                url = DATA_URLS["injuries_parquet"].format(season=candidate_year)
                req = urllib.request.Request(url, headers={"User-Agent": "NFL-Injury-Analysis/1.0"}, method="HEAD")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        return candidate_year
            except Exception:
                continue
        return DEFAULT_SEASON
