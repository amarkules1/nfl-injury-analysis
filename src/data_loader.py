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

    def _read_cached_file(self, parquet_cache: Path, csv_cache: Path, force_refresh: bool) -> Optional[pd.DataFrame]:
        """Attempt reading parquet cache, falling back to CSV cache on any error or missing engine."""
        if self._is_cache_valid(parquet_cache, force_refresh):
            try:
                return pd.read_parquet(parquet_cache)
            except Exception:
                if self._is_cache_valid(csv_cache, force_refresh):
                    try:
                        return pd.read_csv(csv_cache)
                    except Exception:
                        pass
        elif self._is_cache_valid(csv_cache, force_refresh):
            try:
                return pd.read_csv(csv_cache)
            except Exception:
                pass
        return None

    def fetch_live_injuries_espn(self, season: int = DEFAULT_SEASON) -> pd.DataFrame:
        """
        Fetch up-to-the-minute official NFL injury reports for all 32 teams from ESPN API.
        Enriches records with GSIS IDs, standard team codes, and practice status.
        Gracefully returns an empty DataFrame if network or parsing fails.
        """
        import json
        import ssl

        ctx = ssl.create_default_context()
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except Exception:
            ctx = ssl._create_unverified_context()

        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Graceful fallback if offline or unreachable
            return pd.DataFrame()

        # Determine target week using active weekly roster
        try:
            roster_df = self.load_rosters(season=season)
            target_week = int(roster_df["week"].max()) if not roster_df.empty and "week" in roster_df.columns else 8
            w_roster = roster_df[roster_df["week"] == target_week]
        except Exception:
            w_roster = pd.DataFrame()
            target_week = 8

        team_map = {
            "WSH": "WAS",
            "LA": "LAR",
            "OAK": "LV",
            "SD": "LAC",
        }

        def normalize_name(name):
            if not isinstance(name, str):
                return ""
            n = name.strip()
            for sfx in [" Jr.", " Sr.", " III", " II", " IV", " Jr", " Sr"]:
                if n.endswith(sfx):
                    n = n[:-len(sfx)].strip()
            return n.lower().replace("'", "").replace(".", "")

        id_to_player = {}
        name_team_to_player = {}
        last_team_to_players = {}

        if not w_roster.empty:
            for _, row in w_roster.iterrows():
                team = row.get("team", "")
                p_info = {
                    "gsis_id": row.get("gsis_id"),
                    "position": row.get("position"),
                    "first_name": row.get("first_name"),
                    "last_name": row.get("last_name"),
                    "full_name": row.get("full_name"),
                    "team": team,
                }
                espn_id = str(row.get("espn_id") or "")
                if espn_id and espn_id != "nan":
                    id_to_player[espn_id] = p_info

                fn = normalize_name(row.get("full_name"))
                name_team_to_player[(team, fn)] = p_info

                ln = normalize_name(row.get("last_name"))
                last_team_to_players.setdefault((team, ln), []).append(p_info)

        def parse_practice_status(comment: str, status: str):
            c = comment.lower()
            if any(phrase in c for phrase in [
                "didn't participate", "did not participate", "did not practice",
                "didn't practice", "sat out", "missed practice", "held out",
                "was held out", "dnp", "non-participant", "did not take part"
            ]):
                return "Did Not Participate In Practice"
            if any(phrase in c for phrase in [
                "limited participant", "limited participation", "was limited",
                "limited in practice", "limited at practice", "limited reps", "limited on",
                "limited wednesday", "limited thursday", "limited friday"
            ]):
                return "Limited Participation in Practice"
            if any(phrase in c for phrase in [
                "full participant", "full participation", "practiced in full",
                "full practice", "upgraded to full", "practiced without restriction"
            ]):
                return "Full Participation in Practice"
            if status == "Doubtful":
                return "Did Not Participate In Practice"
            if status == "Questionable":
                return "Limited Participation in Practice"
            return None

        records = []
        for team_item in data.get("injuries", []):
            for item in team_item.get("injuries", []):
                stat = item.get("status")
                details = item.get("details") or {}
                inj = details.get("type")
                if not inj and stat == "Active":
                    continue

                ath = item.get("athlete") or {}
                pname = ath.get("displayName") or ""
                fname = ath.get("firstName") or ""
                lname = ath.get("lastName") or ""
                espn_id = str(ath.get("id") or "")
                pos = (ath.get("position") or {}).get("abbreviation") or ""
                raw_team = (ath.get("team") or {}).get("abbreviation") or ""
                team = team_map.get(raw_team, raw_team)

                comm = (item.get("shortComment") or "") + " " + (item.get("longComment") or "")
                prac = parse_practice_status(comm, stat)

                matched = id_to_player.get(espn_id)
                if not matched:
                    matched = name_team_to_player.get((team, normalize_name(pname)))
                if not matched:
                    candidates = last_team_to_players.get((team, normalize_name(lname)), [])
                    if len(candidates) == 1:
                        matched = candidates[0]

                gsis_id = matched["gsis_id"] if matched else None
                if matched and not pos:
                    pos = matched["position"]

                records.append({
                    "season": season,
                    "season_type": "REG",
                    "game_type": "REG",
                    "team": team,
                    "week": target_week,
                    "gsis_id": gsis_id,
                    "position": pos,
                    "full_name": pname,
                    "first_name": fname,
                    "last_name": lname,
                    "report_primary_injury": inj,
                    "report_secondary_injury": None,
                    "report_status": stat if stat in ["Questionable", "Doubtful", "Out"] else None,
                    "practice_primary_injury": inj,
                    "practice_secondary_injury": None,
                    "practice_status": prac,
                })

        return pd.DataFrame(records)

    def load_injuries(self, season: int = DEFAULT_SEASON, force_refresh: bool = False, fetch_live: bool = True) -> pd.DataFrame:
        """
        Load weekly injury reports for the specified season.
        Contains report status (Out/Questionable/Doubtful), practice status, primary and secondary injury.
        Automatically pulls live official NFL injury reports for the active/upcoming week across all 32 teams.
        """
        parquet_cache = self.cache_dir / f"injuries_{season}.parquet"
        csv_cache = self.cache_dir / f"injuries_{season}.csv"

        df = self._read_cached_file(parquet_cache, csv_cache, force_refresh)
        if df is None:
            # Try downloading Parquet first
            url_parquet = DATA_URLS["injuries_parquet"].format(season=season)
            if self._download_file(url_parquet, parquet_cache):
                try:
                    df = pd.read_parquet(parquet_cache)
                except Exception:
                    pass

            # Fallback to CSV
            if df is None:
                url_csv = DATA_URLS["injuries_csv"].format(season=season)
                if self._download_file(url_csv, csv_cache):
                    df = pd.read_csv(csv_cache)

        if df is None:
            raise FileNotFoundError(f"Could not load injuries data for season {season} from {url_parquet} or {url_csv}")

        # Fetch and merge live injury reports for upcoming/active week across all 32 teams
        if fetch_live:
            try:
                live_df = self.fetch_live_injuries_espn(season=season)
                if not live_df.empty:
                    df = pd.concat([df, live_df], ignore_index=True)
                    has_gsis = df["gsis_id"].notna()
                    with_gsis = df[has_gsis].drop_duplicates(subset=["season", "week", "team", "gsis_id"], keep="last")
                    without_gsis = df[~has_gsis].drop_duplicates(subset=["season", "week", "team", "full_name"], keep="last")
                    df = pd.concat([with_gsis, without_gsis], ignore_index=True)
                    try:
                        df.to_parquet(parquet_cache, index=False)
                    except Exception:
                        pass
            except Exception:
                pass

        # Check for local supplementary injury reports (if any custom manual file exists)
        from config import DATA_DIR
        supplement_candidates = [
            self.cache_dir / f"injuries_supplement_{season}.csv",
            DATA_DIR / f"injuries_supplement_{season}.csv",
        ]
        for supp_path in supplement_candidates:
            if supp_path.exists():
                try:
                    supp_df = pd.read_csv(supp_path)
                    if not supp_df.empty:
                        df = pd.concat([df, supp_df], ignore_index=True)
                        has_gsis = df["gsis_id"].notna()
                        with_gsis = df[has_gsis].drop_duplicates(subset=["season", "week", "team", "gsis_id"], keep="last")
                        without_gsis = df[~has_gsis].drop_duplicates(subset=["season", "week", "team", "full_name"], keep="last")
                        df = pd.concat([with_gsis, without_gsis], ignore_index=True)
                except Exception:
                    pass

        return df

    def load_rosters(self, season: int = DEFAULT_SEASON, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load week-by-week player roster designations.
        Contains status (ACT, RES, INA, DEV, EXE, CUT), status_description_abbr (R01, R04, etc.),
        and player metadata.
        """
        parquet_cache = self.cache_dir / f"roster_weekly_{season}.parquet"
        csv_cache = self.cache_dir / f"roster_weekly_{season}.csv"

        cached_df = self._read_cached_file(parquet_cache, csv_cache, force_refresh)
        if cached_df is not None:
            return cached_df

        url_parquet = DATA_URLS["roster_parquet"].format(season=season)
        if self._download_file(url_parquet, parquet_cache):
            try:
                return pd.read_parquet(parquet_cache)
            except Exception:
                pass

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

        df_all = self._read_cached_file(parquet_cache, csv_cache, force_refresh)
        if df_all is None:
            if self._download_file(DATA_URLS["games_parquet"], parquet_cache):
                try:
                    df_all = pd.read_parquet(parquet_cache)
                except Exception:
                    pass
            if df_all is None and self._download_file(DATA_URLS["games_csv"], csv_cache):
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

        cached_df = self._read_cached_file(parquet_cache, csv_cache, force_refresh)
        if cached_df is not None:
            return cached_df

        url_parquet = DATA_URLS["depth_charts_parquet"].format(season=season)
        if self._download_file(url_parquet, parquet_cache):
            try:
                return pd.read_parquet(parquet_cache)
            except Exception:
                pass

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
