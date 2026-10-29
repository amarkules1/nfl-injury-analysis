# NFL Player Availability & Predicted Play Chance: Logistic Regression Model Specification

This document provides a comprehensive technical overview of the **Predicted Play Chance** machine learning model utilized in the NFL Injury & Health Analytics platform. It details the underlying mathematical formulation, feature engineering, hyperparameters, fitted coefficients, evaluation metrics, and domain-specific calibrations applied to forecast player availability for upcoming NFL games.

---

## 1. Executive Summary

- **Model Type**: Supervised Binary Logistic Regression with $L_2$ regularization (`scikit-learn`).
- **Target Variable**: Player Game Availability ($y \in \{0, 1\}$), where:
  - $y = 1$: Player is active and participates in the scheduled game.
  - $y = 0$: Player misses the game (Inactive, Injured Reserve, PUP, or Sidelined).
- **Primary Training Cohort**: Multi-season player-game observations (2023–2026 through completed weeks) comprising **44,544 player-games**.
- **Model Fit**:
  - **ROC AUC**: **0.9876**
  - **Classification Accuracy**: **94.37%**
  - **Brier Score Loss**: **0.0422**
  - **Log Loss**: **0.1428**
- **Downstream Application**: Predicts individual player availability probabilities which feed into:
  1. **Player Database Explorer**: Displays *PREDICTED PLAY CHANCE* meters and qualitative likelihood tags.
  2. **Team Deep Dive**: Forecasts 32-team availability matrices and highlights game-time decision swing players.
  3. **Matchup Center**: Computes projected net health advantages between scheduled opponents.
  4. **Power Rankings**: Estimates weekly team health ratings prior to official gameday inactives.

---

## 2. Mathematical Formulation

The model estimates the posterior probability that player $i$ plays in week $t$ using the standard logistic (sigmoid) function:

$$P(\text{Play} = 1 \mid \mathbf{x}) = \sigma(z) = \frac{1}{1 + e^{-z}}$$

where the linear log-odds predictor $z$ is:

$$z = \beta_0 + \sum_{j=1}^{p} \beta_j x_j$$

- $\beta_0$: Model intercept (bias term).
- $\mathbf{x} = [x_1, x_2, \dots, x_p]^T$: Vector of standardized continuous features and one-hot encoded categorical indicator variables.
- $\beta_j$: Feature weight (log-odds coefficient).
- $\text{Odds Ratio} (\text{OR}_j) = \exp(\beta_j)$: Represents the multiplicative change in the odds of playing per unit increase in $x_j$, holding all other factors constant.

---

## 3. Data Pipeline & Feature Engineering

Features are computed using week-by-week player injury reports, roster transaction designations, practice logs, and historical game participation.

```
+-----------------------------------------------------------------------------------+
|                              Raw NFL Datasets                                     |
|  - Weekly Rosters (ACT, RES, INA)       - Practice Participation (DNP, LP, FP)    |
|  - Official Injury Reports (Q, D, Out)  - Game Outcomes & Historical Snap Counts  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                             Feature Engineering                                   |
|  - Recency Lag Features (Consecutive missed games, last-3-games missed rate)      |
|  - Report Status Normalization (Unlisted, Questionable, Doubtful, Out, IR-window) |
|  - Practice Participation Extraction (DNP, Limited, Full)                         |
|  - Anatomical Injury Grouping (19 anatomical categories)                          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        Pre-processing & ColumnTransformer                         |
|  - StandardScaler (Numeric: lag rates, consecutive missed games, starter flag)    |
|  - OneHotEncoder (Categorical: injury type, practice status, report status, pos) |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                      Logistic Regression Classifier (C=0.8)                       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                       Domain-Specific NFL Calibration Layer                       |
|  - Friday "Out" Rule Cap (<= 0.02)      - Active + Full Practice Baseline (>= 0.95)|
|  - IR 21-Day Practice Window Scaling    - Questionable/Doubtful Practice Matrix   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                  Predicted Play Probability & Qualitative UI Labels               |
|      (Highly Likely, Probable, Toss-Up / Game-Time Decision, Doubtful, Out)       |
+-----------------------------------------------------------------------------------+
```

### Feature Categories

1. **Prior Availability History (Dynamic Lag Features)**:
   - `consecutive_games_missed` (Integer): Number of consecutive games missed immediately prior to the upcoming game. Captures multi-week layoff inertia.
   - `missed_rate_last_3` (Float, $[0.0, 1.0]$): Proportion of the team's preceding 3 games missed by the player. Captures short-term availability volatility.
   - `missed_last_game` (Binary $\{0, 1\}$): Indicator if the player missed the immediately preceding week.
   - `is_starter` (Binary $\{0, 1\}$): Whether the player is designated as the primary starter on the depth chart.

2. **Official Friday Injury Report Status (`report_status`)**:
   - `unlisted`: Player is not listed on the official game injury status report (standard active).
   - `questionable`: Listed as Questionable (uncertain availability).
   - `doubtful`: Listed as Doubtful (unlikely to play).
   - `out`: Ruled Out on the final game injury report.
   - `reserve_ir`: Player is on Reserve/Injured with no designated practice window.
   - `reserve_practicing_full`: Player is on IR but designated to return and practicing in full.
   - `reserve_practicing_limited`: Player is on IR with limited practice participation.

3. **Practice Participation (`practice_status`)**:
   - `full`: Full Participation in Practice across sessions leading into the game.
   - `limited`: Limited Participation in Practice (reps restricted).
   - `dnp`: Did Not Participate In Practice.
   - `none`: No official practice report filed (healthy scratch, unlisted, or non-practicing reserve).

4. **Primary Diagnosed Injury Type (`injury_type`)**:
   - Grouped into 19 key anatomical categories: `knee`, `ankle`, `hamstring`, `shoulder`, `concussion`, `groin`, `calf`, `quad`, `foot`, `back`, `neck`, `hip`, `illness`, `chest`, `ribs`, `hand`, `wrist`, `thumb`, `elbow`, plus `rest_personal`, `undisclosed_reserve`, and `other`.

5. **Position Group (`position_group`)**:
   - Positional categories: `QB`, `RB`, `WR`, `TE`, `OL`, `DL`, `LB`, `CB`, `S`, `ST`. Positional physical demands impact return-to-play thresholds (e.g. QBs and DBs often have distinct thresholds compared to offensive linemen).

---

## 4. Hyperparameters & Training Configuration

The model is trained using `scikit-learn` with the following configuration:

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Algorithm** | `LogisticRegression` | Provides calibrated, continuous probability estimates $[0, 1]$ directly suitable for risk modeling. |
| **Regularization ($C$)** | `0.8` ($L_2$ penalty) | Slight regularization to prevent overfitting on low-sample injury types while retaining high responsiveness to practice status. |
| **Solver** | `lbfgs` | Fast, stable quasi-Newton optimization for multiclass/binary logistic regression. |
| **Class Weight** | `balanced` | Automatically adjusts weights inversely proportional to class frequencies to prevent bias toward the majority class (Missed Games). |
| **Max Iterations** | `1000` | Guarantees full numerical convergence across one-hot feature expansions. |
| **Random State** | `42` | Ensures deterministic, reproducible coefficient estimation. |

---

## 5. Model Fit Statistics & Evaluation

### Training Cohort Distribution

- **Total Sample Size**: **44,544** player-game records.
- **Class 1 (Played)**: 14,262 (32.0%)
- **Class 0 (Missed Game)**: 30,282 (68.0%)

### Summary Performance Metrics

| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **ROC AUC** | **0.9876** | Near-perfect separation between players who play and players who sit. |
| **Accuracy** | **94.37%** | Correctly classifies 94.4 out of every 100 player availability instances. |
| **Brier Score Loss** | **0.0422** | Mean squared difference between predicted probability and actual binary outcome; values $< 0.05$ indicate excellent probabilistic calibration. |
| **Log Loss (Cross-Entropy)** | **0.1428** | Low penalization on confidence errors, reflecting well-calibrated posterior probabilities. |

### Confusion Matrix

$$\begin{pmatrix} \text{True Missed (0)} & \text{False Played (1)} \\ \text{False Missed (0)} & \text{True Played (1)} \end{pmatrix} = \begin{pmatrix} 28{,}625 & 1{,}657 \\ 851 & 13{,}411 \end{pmatrix}$$

- **True Negatives** (Correctly predicted Out/Missed): **28,625**
- **True Positives** (Correctly predicted Active/Played): **13,411**
- **False Positives** (Predicted to Play, but Missed): **1,657** (3.7% of total)
- **False Negatives** (Predicted to Miss, but Played): **851** (1.9% of total)

### Detailed Classification Report

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Missed Game ($y=0$)** | **0.97** | **0.95** | **0.96** | 30,282 |
| **Played Game ($y=1$)** | **0.89** | **0.94** | **0.91** | 14,262 |
| **Macro Average** | **0.93** | **0.94** | **0.94** | 44,544 |
| **Weighted Average** | **0.95** | **0.94** | **0.94** | 44,544 |

---

## 6. Fitted Model Parameters & Coefficients

The intercept and key coefficients estimated by the regression pipeline are presented below. Positive coefficients increase the likelihood of playing ($\text{OR} > 1.0$), while negative coefficients decrease the likelihood ($\text{OR} < 1.0$).

- **Fitted Intercept ($\beta_0$)**: `-2.6559`

### Complete Parameter Estimates

| Feature Name | Coefficient ($\beta$) | Odds Ratio ($\exp(\beta)$) | Effect on Availability |
| :--- | :---: | :---: | :--- |
| `report_status_unlisted` | **+5.1515** | **172.70** | Strongest positive driver: Healthy active players not listed on injury reports. |
| `report_status_questionable` | **+3.3723** | **29.15** | Substantial positive baseline vs. Out/IR; refined further by practice volume. |
| `practice_status_full` | **+1.0204** | **2.77** | Full practice reps multiply play odds by nearly $2.8\times$. |
| `injury_type_rest_personal` | **+0.9774** | **2.66** | Veteran rest / non-injury absences rarely keep players out on gameday. |
| `injury_type_illness` | **+0.5238** | **1.69** | Illnesses have high gameday clearance rates compared to structural injuries. |
| `injury_type_foot` | **+0.3959** | **1.49** | Mild foot ailments where player participates typically play through. |
| `injury_type_wrist` | **+0.3316** | **1.39** | Upper extremity splints/casts permit participation for non-QBs. |
| `position_group_RB` | **+0.1609** | **1.17** | Running backs show modest resilience when active on Friday. |
| `position_group_TE` | **+0.1474** | **1.16** | Tight ends with full practice generally suit up. |
| `practice_status_limited` | **+0.0557** | **1.06** | Neutral-to-slight positive baseline; hinges heavily on gameday pregame warmups. |
| `position_group_LB` | **+0.0055** | **1.01** | Linebackers mirror baseline defensive return rates. |
| `position_group_WR` | **-0.0411** | **0.96** | Wide receiver speed cuts make questionable statuses slightly more fragile. |
| `position_group_OL` | **-0.0854** | **0.92** | Linemen playing through joint injuries have modest risk. |
| `is_starter` | **-0.1187** | **0.89** | Starters carrying serious designations are slightly more protected by coaching staffs. |
| `injury_type_hamstring` | **-0.1591** | **0.85** | High reinjury risk leads to conservative medical staff gating. |
| `position_group_S` | **-0.2081** | **0.81** | Safeties require open-field change-of-direction. |
| `injury_type_concussion` | **-0.2417** | **0.79** | Strict 5-step NFL concussion protocol gating reduces return likelihood. |
| `position_group_DL` | **-0.2537** | **0.78** | Defensive front players with lower leg ailments face conservative holds. |
| `position_group_CB` | **-0.3004** | **0.74** | Cornerbacks tracking elite receivers require peak deceleration; conservative gating. |
| `missed_last_game` | **-0.3060** | **0.74** | Missing the prior week dampens probability by $\sim 26\%$. |
| `consecutive_games_missed` | **-0.5254** | **0.59** | Each additional consecutive game on the sideline cuts odds by $41\%$. |
| `report_status_reserve_practicing_limited` | **-0.5441** | **0.58** | 21-day practice window activated, but limited reps suggest incomplete rehab. |
| `report_status_reserve_practicing_full` | **-0.5497** | **0.58** | 21-day practice window open; requires roster cut/move to activate. |
| `missed_rate_last_3` | **-0.6650** | **0.51** | High recent missed rate cuts play odds in half. |
| `position_group_QB` | **-1.1040** | **0.33** | Quarterbacks carrying injury flags rarely play at suboptimal throwing/mobility states. |
| `injury_type_undisclosed_reserve` | **-1.1068** | **0.33** | Administrative/reserve designations heavily favor sitting. |
| `practice_status_dnp` | **-1.2641** | **0.28** | Did Not Participate in practice cuts odds of playing by over $71\%$. |
| `practice_status_none` | **-1.4688** | **0.23** | Complete lack of practice reps signals scratch or non-active roster status. |
| `report_status_doubtful` | **-1.5345** | **0.22** | Official Doubtful designation cuts play odds by $78\%$. |
| `report_status_reserve_ir` | **-3.4138** | **0.03** | Standard Reserve/Injured status (no practice) strictly prevents playing. |
| `injury_type_none` | **-3.4527** | **0.03** | Captured predominantly on inactive healthy scratches or non-roster reserve. |
| `report_status_out` | **-4.1386** | **0.02** | Official Out status on Friday report; virtually zero play likelihood. |

---

## 7. NFL Domain Calibrations & Regulatory Overrides

Pure empirical regression can occasionally produce non-zero probabilities for players who are legally ineligible under NFL competition bylaws (e.g. an unactivated player on IR or a player designated "Out" on the Friday injury report). To eliminate impossible predictions, the model applies **strict domain rule calibrations**:

```
                         [Raw Logistic Model Output: P_raw]
                                        │
                                        ▼
             ┌──────────────────────────────────────────────────────┐
             │       NFL Bylaw & Gameday Protocol Gating Rules      │
             └──────────────────────────────────────────────────────┘
                       │                               │
       Is Ruled Out on Friday Report?        Is Player on Reserve/IR?
             ├── Yes ──> P = 0.02                     ├── No Practice ──> P = 0.02
             │                                        ├── Full Reps   ──> P = [0.80, 0.95]
             └── No                                   └── Limited     ──> P = [0.40, 0.52]
                       │
       Is Player on Active Roster (ACT)?
             ├── Questionable + Full Practice    ──> P = [0.78, 0.90] (Hist ~82%)
             ├── Questionable + Limited Practice ──> P = [0.52, 0.65] (Game-Time Decision)
             ├── Questionable + DNP              ──> P = [0.28, 0.40] (Doubtful Lean)
             ├── Doubtful + DNP                  ──> P <= 0.05
             └── Unlisted + Practicing           ──> P >= 0.95
```

1. **Rule 1: Friday Ruled "Out"**
   - Under NFL reporting bylaws, players designated "Out" on the Friday injury report cannot suit up on Sunday/Monday.
   - **Calibration**: `play_probability` is capped at strictly **$0.02$** ($2\%$).

2. **Rule 2: Reserve / Injured (IR) & Reserve / PUP**
   - **IR with No Practice / DNP**: Player has not been designated for return. **Calibration**: **$0.02$**.
   - **IR with Full Practice Participation**: Player has entered the 21-day practice window and logged full reps. Historically, $\sim 88\%$ of players logging a full Friday practice while on the return window are formally activated to the 53-man roster by the Saturday 4:00 PM ET deadline. **Calibration**: Clipped to **$[0.80, 0.95]$**.
   - **IR with Limited Practice Participation**: Player is testing the injury during the 21-day window but has not logged full contact reps. **Calibration**: Clipped to **$[0.40, 0.52]$** (Toss-Up / Game-Time Decision).

3. **Rule 3: Active Roster (ACT) Injury Interaction Matrix**
   - **Healthy / Unlisted with Practice**: Player is not on the injury report. **Calibration**: Floor of **$0.95$**.
   - **Questionable + Full Practice**: Player is listed as Questionable but participated in full Friday reps. Historical NFL league-wide return rate is $\sim 82\%$. **Calibration**: Clipped to **$[0.78, 0.90]$**.
   - **Questionable + Limited Practice**: Player is limited in practice. Historical return rate is $\sim 58\%$ (true game-time decision). **Calibration**: Clipped to **$[0.52, 0.65]$**.
   - **Questionable + DNP**: Player did not practice on Friday but team did not rule them out. Historical return rate is $\sim 35\%$. **Calibration**: Clipped to **$[0.28, 0.40]$**.
   - **Doubtful + DNP**: Historical return rate across the NFL is $< 4\%$. **Calibration**: Capped at **$0.05$**.
   - **Doubtful + Limited Practice**: Player has minimal reps. **Calibration**: Clipped to **$[0.12, 0.22]$**.

---

## 8. Categorical Likelihood Labels & UI Visuals

The continuous probability $P(\text{Play})$ is mapped into human-readable decision tiers displayed in the dashboard:

| Probability Range | Label in UI | Visual Color | Interpretation |
| :---: | :---: | :---: | :--- |
| **$\ge 80.0\%$** | `Highly Likely` | **Emerald (`#10b981`)** | Expected to play; starter or regular depth asset available for full or near-full snap counts. |
| **$60.0\% - 79.9\%$** | `Probable / Leaning Play` | **Green/Amber (`#84cc16`)** | Favorable prognosis; player participated in practice and is leaning toward suiting up. |
| **$40.0\% - 59.9\%$** | `Toss-Up / Game-Time Decision` | **Amber (`#eab308`)** | True 50/50 availability. Player designated Questionable with limited reps; decision made in pregame warmups. |
| **$15.0\% - 39.9\%$** | `Doubtful` | **Orange (`#f97316`)** | Unfavorable prognosis. DNP or severe restriction; high likelihood of gameday deactivation. |
| **$< 15.0\%$** | `Out / Sidelined` | **Rose (`#f43f5e`)** | Sidelined. Confirmed out, shut down on IR/PUP, or non-active roster status. |

---

## 9. Downstream Health Score Projections

Individual predicted probabilities aggregate into team-level metrics:

1. **Projected Lost Starters**:
   $$\text{Starters at Risk} = \sum_{i \in \text{Starters}} \left(1 - P_i(\text{Play})\right)$$

2. **Projected Team Healthiness Score**:
   Starting with a baseline of $100.0$, expected penalty weights are deducted:
   $$\text{Projected Score} = 100 - \sum_{i} \left(1 - P_i(\text{Play})\right) \cdot w_i$$
   where $w_i$ is the positional penalty weight ($22.0$ for starting QB, $4.5$ for starting non-QB, $1.0$ for key backup).

3. **Positional Unit Breakdown**:
   Aggregates probabilities across positional clusters (QB, Offensive Line, Skill Positions, Front Seven, Secondary) to identify specific unit vulnerabilities.

4. **Projected Matchup Health Advantage**:
   $$\Delta \text{Health} = \text{Projected Health}_{\text{Home}} - \text{Projected Health}_{\text{Away}}$$
   Quantifies the net health disparity entering each scheduled matchup.

---

## 10. Summary Verification & Files

- **Source Implementation**: [`src/prediction_model.py`](file:///c:/dev/python_projects/nfl-injury-analysis/src/prediction_model.py)
- **Unit Tests**: [`tests/test_prediction_model.py`](file:///c:/dev/python_projects/nfl-injury-analysis/tests/test_prediction_model.py)
- **Generated Datasets**:
  - `data/player_play_predictions_2026.csv`
  - `data/upcoming_team_health_projections_2026.csv`
  - `data/upcoming_matchup_projections_2026.csv`
- **Frontend Consumer Components**:
  - [`frontend/src/components/PlayerExplorer.vue`](file:///c:/dev/python_projects/nfl-injury-analysis/frontend/src/components/PlayerExplorer.vue)
  - [`frontend/src/components/TeamDeepDive.vue`](file:///c:/dev/python_projects/nfl-injury-analysis/frontend/src/components/TeamDeepDive.vue)
  - [`frontend/src/components/MatchupCenter.vue`](file:///c:/dev/python_projects/nfl-injury-analysis/frontend/src/components/MatchupCenter.vue)
  - [`frontend/src/components/HealthLeaderboard.vue`](file:///c:/dev/python_projects/nfl-injury-analysis/frontend/src/components/HealthLeaderboard.vue)

