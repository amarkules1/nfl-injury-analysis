# Ubuntu Server Cron Automation Guide: NFL Injury Analysis

This guide provides step-by-step instructions for automating the **NFL Injury & Missed Games Analysis Pipeline** to run every hour via `cron` on an **Ubuntu Linux server**, updating all prediction and health data files directly into your specified target directory.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites on Ubuntu Server](#2-prerequisites-on-ubuntu-server)
3. [Server Directory Setup & Permissions](#3-server-directory-setup--permissions)
4. [Setting Up the Hourly Cron Job](#4-setting-up-the-hourly-cron-job)
   - [Method A: Production Wrapper Script (Recommended)](#method-a-production-wrapper-script-recommended)
   - [Method B: Direct Crontab Entry](#method-b-direct-crontab-entry)
5. [Generated Data Files](#5-generated-data-files)
6. [Testing & Verification](#6-testing--verification)
7. [Log Management & Logrotate](#7-log-management--logrotate)
8. [Troubleshooting & FAQ](#8-troubleshooting--faq)

---

## 1. Architecture Overview

When the pipeline runs hourly with the `--output-dir` argument:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Ubuntu Cron Daemon (fires at minute 0 of every hour: 0 * * * *)              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
             ┌───────────────────────────────────────────────────┐
             │  scripts/run_hourly_update.sh (with flock lock)   │
             └─────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Pipenv Environment: update_injury_log.py                                    │
│  1. Ingest official nflverse datasets + Live ESPN injury reports            │
│  2. Harmonize player roles, starter designations, and missed game logs       │
│  3. Calculate team game healthiness scores                                   │
│  4. Run ML Logistic Regression play probability model for upcoming week      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Target Directory (e.g. /var/data/nfl-injuries or /data/nfl_updates)         │
│  * nfl_injuries_and_missed_games_2026.csv                                    │
│  * nfl_injuries_and_missed_games.csv                                         │
│  * team_injury_weekly_summary_2026.csv                                       │
│  * team_game_healthiness_scores_2026.csv                                     │
│  * player_play_predictions_2026.csv                                          │
│  * upcoming_team_health_projections_2026.csv                                 │
│  * upcoming_matchup_projections_2026.csv                                     │
│  (Default project directories and frontend public folders are bypassed)       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites on Ubuntu Server (Installing Python 3.12 Alongside Python 3.8)

Ubuntu 20.04 LTS (and systems with Python 3.8 default) will fail with:
```text
E: Unable to locate package python3.12
E: Couldn't find any package by glob 'python3.12'
```
**Why this occurs**: The deadsnakes PPA only provides pre-compiled `python3.12` packages for newer Ubuntu releases (Ubuntu 22.04 LTS and 24.04 LTS). On Ubuntu 20.04 (`focal`), binary packages for Python 3.12 are not published in the PPA.

> [!CAUTION]
> **Never modify or overwrite Ubuntu's system `/usr/bin/python3` symlink.** Core Ubuntu OS packages (including `apt` and system daemons) depend strictly on Python 3.8. Instead, use one of the two methods below to install Python 3.12 side-by-side into `/usr/local/bin/python3.12`.

Choose **Option A** (faster standalone install) or **Option B** (standard source compilation):

---

### Option A: Fast Standalone Install via `uv` (Recommended: ~10 Seconds, No Compiling)

Astral's `uv` tool can download and manage pre-compiled standalone Python 3.12 binaries directly:

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
export PATH="${HOME}/.local/bin:${PATH}"

# 2. Download and install Python 3.12
uv python install 3.12

# 3. Create a system symlink in /usr/local/bin for all users and cron
sudo ln -sf $(uv python find 3.12) /usr/local/bin/python3.12

# 4. Verify Python 3.12 is available
python3.12 --version
# Output: Python 3.12.x
```

---

### Option B: Compile Python 3.12 from Official Source (~2 Minutes)

If you prefer building from the official python.org source code, `make altinstall` installs `python3.12` into `/usr/local/bin` without touching your system's default Python 3.8:

```bash
# 1. Install required build libraries
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
libncurses5-dev libnss3-dev libreadline-dev libffi-dev libsqlite3-dev \
libbz2-dev libgdbm-dev liblzma-dev tk-dev uuid-dev wget curl ca-certificates

# 2. Download and extract Python 3.12 source
cd /tmp
wget https://www.python.org/ftp/python/3.12.8/Python-3.12.8.tgz
tar -xf Python-3.12.8.tgz
cd Python-3.12.8

# 3. Configure and compile using all CPU cores
./configure --enable-optimizations
make -j $(nproc)

# 4. Install using 'altinstall' (CRITICAL: prevents overwriting /usr/bin/python3)
sudo make altinstall

# 5. Verify Python 3.12 installation
python3.12 --version
# Output: Python 3.12.8
```

---

### Step 2.2: Install Pip and Pipenv for Python 3.12

Once `/usr/local/bin/python3.12` is installed via either Option A or B:

```bash
# Bootstrap pip for Python 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo /usr/local/bin/python3.12

# Install Pipenv using Python 3.12
sudo /usr/local/bin/python3.12 -m pip install --upgrade pipenv

# Verify pipenv is installed
pipenv --version
```

---

### Step 2.3: Deploy Repository & Initialize Virtual Environment with Python 3.12

Navigate to your repository directory:

```bash
cd /opt/nfl-injury-analysis

# If an older virtual environment was created with Python 3.8, remove it:
pipenv --rm 2>/dev/null || true

# Explicitly bind Pipenv to Python 3.12
pipenv --python /usr/local/bin/python3.12 install

# Verify the virtualenv is running Python 3.12
pipenv run python --version
# Expected Output: Python 3.12.x
```

---

## 3. Server Directory Setup & Permissions

Create the external folder where you want data files to be saved (e.g., `/var/data/nfl-injuries` or `/srv/nfl-data`):

```bash
# Choose your preferred destination folder
TARGET_DIR="/var/data/nfl-injuries"

# Create the folder
sudo mkdir -p "${TARGET_DIR}"

# Grant ownership to the user running the cron job (e.g. ubuntu)
sudo chown -R ubuntu:ubuntu "${TARGET_DIR}"
sudo chmod -R 775 "${TARGET_DIR}"
```

---

## 4. Setting Up the Hourly Cron Job

### Method A: Production Wrapper Script (Recommended)

Cron environments execute with a stripped-down `PATH` and without interactive shell profile variables. Using the pre-built wrapper script [`scripts/run_hourly_update.sh`](file:///c:/dev/python_projects/nfl-injury-analysis/scripts/run_hourly_update.sh) guarantees that:
- `PATH` includes user and system binary paths (`~/.local/bin`, `/usr/bin`, etc.).
- Concurrency locking via `flock` prevents multiple hourly jobs from overlapping if a network download takes extra time.
- All output is automatically logged with timestamps.

#### Step 1: Make the script executable

```bash
chmod +x /opt/nfl-injury-analysis/scripts/run_hourly_update.sh
```

#### Step 2: Open crontab for editing

```bash
crontab -e
```

#### Step 3: Add the hourly cron schedule

Add the following line to run at the start of every hour (minute 0), passing your target update directory:

```cron
# Run NFL Injury Pipeline at minute 0 of every hour
0 * * * * /opt/nfl-injury-analysis/scripts/run_hourly_update.sh /var/data/nfl-injuries
```

> [!TIP]
> If you wish to run it at a different interval (for example, every 30 minutes), change `0 * * * *` to `*/30 * * * *`.

---

### Method B: Direct Crontab Entry

If you prefer a single-line command directly in your `crontab` without using the wrapper script:

```bash
crontab -e
```

Add the following configuration:

```cron
# Set PATH so cron can find pipenv and python3
PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin

# Run hourly at minute 0
0 * * * * cd /opt/nfl-injury-analysis && /usr/bin/flock -n /tmp/nfl_update.lock pipenv run python update_injury_log.py --output-dir /var/data/nfl-injuries >> /opt/nfl-injury-analysis/logs/cron_update.log 2>&1
```

---

## 5. Generated Data Files

Every hourly run saves the following CSV files exclusively to your target directory (`/var/data/nfl-injuries`):

| File Name | Description |
| :--- | :--- |
| **`nfl_injuries_and_missed_games_2026.csv`** | Complete season log of all injuries, statuses, practice participation, and health impact weights. |
| **`nfl_injuries_and_missed_games.csv`** | Standard alias to the latest injury log. |
| **`team_injury_weekly_summary_2026.csv`** | Aggregated team-level weekly summary with starter missed counts and total health impact severity. |
| **`team_game_healthiness_scores_2026.csv`** | Healthiness ratings (0–100%) and unit scores (QB, OL, Skill, Front, Secondary) for all games. |
| **`player_play_predictions_2026.csv`** | Machine learning logistic regression play probability ($0.0$–$1.0$) and categorical label for every player. |
| **`upcoming_team_health_projections_2026.csv`** | Projected team health scores, swing players, and confirmed missing starters for upcoming games. |
| **`upcoming_matchup_projections_2026.csv`** | Head-to-head matchup health advantages and key swing player matchups for the upcoming week. |

---

## 6. Testing & Verification

Before waiting for the cron job to trigger, test the execution manually from the terminal as the `ubuntu` user:

```bash
# 1. Run the wrapper script manually
/opt/nfl-injury-analysis/scripts/run_hourly_update.sh /var/data/nfl-injuries

# 2. Verify exit status
echo $?
# Output should be: 0

# 3. Check that files exist in the target folder
ls -la /var/data/nfl-injuries

# 4. Check the execution log
cat /opt/nfl-injury-analysis/logs/hourly_update_$(date +'%Y%m%d').log
```

---

## 7. Log Management & Logrotate

To prevent log files from growing indefinitely, configure Ubuntu's `logrotate`:

```bash
sudo nano /etc/logrotate.d/nfl-injury-analysis
```

Add the following configuration:

```text
/opt/nfl-injury-analysis/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
```

Test your logrotate configuration:

```bash
sudo logrotate -d /etc/logrotate.d/nfl-injury-analysis
```

---

## 8. Troubleshooting & FAQ

### Issue 1: `pipenv: command not found` in Cron
**Cause**: Cron runs with a default minimal environment (`/usr/bin:/bin`) and cannot find `pipenv` in `~/.local/bin`.  
**Fix**: Ensure `PATH` is exported at the top of your crontab or use the wrapper script [`scripts/run_hourly_update.sh`](file:///c:/dev/python_projects/nfl-injury-analysis/scripts/run_hourly_update.sh), which explicitly sets `export PATH="/home/${USER}/.local/bin:${PATH}"`.

### Issue 2: `Permission denied` on Target Directory
**Cause**: The cron user does not have write permissions to the destination folder.  
**Fix**:
```bash
sudo chown -R $(whoami):$(whoami) /var/data/nfl-injuries
chmod 775 /var/data/nfl-injuries
```

### Issue 3: SSL Certificate Verification Failed on Data Fetch
**Cause**: Missing CA root certificates on Ubuntu.  
**Fix**:
```bash
sudo apt install -y ca-certificates
sudo update-ca-certificates
```

### Issue 4: How to verify that the cron daemon is active
Check the status of the cron service:
```bash
sudo systemctl status cron
```
Inspect recent cron trigger attempts in the system log:
```bash
grep CRON /var/log/syslog
```

### Issue 5: `Couldn't find any package by glob 'python3.12'` / `Python 3.12 was not found`
**Cause**: On Ubuntu 20.04 LTS (`focal`), the deadsnakes PPA no longer publishes binary packages for Python 3.12 because Focal reached standard support EOL.  
**Fix**: Install Python 3.12 via standalone `uv` or compile from source via `make altinstall` (see [Section 2](#2-prerequisites-on-ubuntu-server-installing-python-312-alongside-python-38)), then bind Pipenv to the resulting binary:
```bash
# Point Pipenv to the compiled/standalone binary
cd /opt/nfl-injury-analysis
pipenv --rm 2>/dev/null || true
pipenv --python /usr/local/bin/python3.12 install
```

