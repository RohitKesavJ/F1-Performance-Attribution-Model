# F1 Performance Attribution Model (2021–2025)

##  Project Overview

**F1 Performance Attribution Model** is a full-stack data science project that quantifies one of Formula 1’s oldest debates:  
**How much of a team’s success comes from the car ("The Chariot") versus the driver ("The Charioteer")?**

The project builds an **automated data pipeline** using Python’s **FastF1** library to process raw telemetry, engineer advanced racing metrics, and employ **statistical modeling** to derive a data-driven answer.  
The findings are showcased through an **interactive Streamlit dashboard**.

---

##  Key Findings — The Grand Model’s Answer

The **Linear Regression** model reveals:

| Feature | Category | Coefficient (Impact on Points) | Conclusion |
|----------|-----------|-------------------------------|-------------|
| AvgConsistency | Driver Skill (Charioteer) | **-1.08** | Most important. High inconsistency is the largest penalty. |
| TopSpeedST | Car Performance (Chariot) | **-0.52** | The Speed Trap. High top speed is negatively correlated with points (indicating high drag / low downforce). |
| AvgDegradation | Car Performance (Chariot) | **-0.49** | Key car flaw. High tire wear severely hurts final position. |
| PositionsGained | Driver Skill (Charioteer) | **+0.11** | Minor factor. Good starts help, but consistency matters more. |

---

## Analysis & Visual Showcase

### 1. Driver Skill: Consistency is King
- **Metric:** Average Lap Consistency (X-axis) is the most critical driver metric.  
- **Observation:** The elite drivers live in the **Top-Left Quadrant** (low inconsistency, high positions gained).  
- **Goal Quadrant:** *Top-Left* — e.g., VER, NOR, HAM.  
- Drivers who win the championship consistently dominate this axis.

---

### 2. Car Performance: The Top Speed Paradox
- The **fastest cars** (e.g., Williams, Haas) often exhibit **lower overall race performance**.  
- This is because teams running **low-downforce setups** achieve higher top speeds but sacrifice tire longevity and corner stability.

---

### 3. Teammate Battle (Telemetry Deep Dive)
- The Streamlit dashboard allows users to **compare two teammates’ telemetry** (Speed, Throttle, Brake).  
- This reveals subtle differences in **driving style and corner entry/exit behavior** — turning data into visual storytelling.

---

##  Project Architecture & Automation

The system is built as a modular, **automated pipeline** that runs end-to-end with minimal manual input.

| Component | Technology | Role |
|------------|-------------|------|
| **Data Source** | FastF1 Library / F1 API Feeds | Provides raw timing, telemetry, and session data (2021–2025). |
| **ETL Pipeline** | `weekly_pull.py`, `master_analysis.py` | Automates data download and feature generation. |
| **Data Store** | Local Cache (`fastf1_cache/`) & Master CSV | Stores gigabytes of raw and processed telemetry. |
| **Statistical Model** | Scikit-learn (`LinearRegression`) | Quantifies the weight of each feature vs. final points. |
| **Frontend** | Streamlit, Plotly, Custom CSS | Interactive web dashboard for visual analysis. |

---

##  Automation Status

The project is designed to run **fully automatically**:

- `weekly_pull.py` checks for new races each week.  
- `master_analysis.py` processes and updates the main dataset (`season_2021–2025_analysis.csv`).  
- `run_update.bat` orchestrates both scripts for a one-command refresh.

---

##  Getting Started Locally

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/F1-Performance-Attribution-Model.git
cd F1-Performance-Attribution-Model
2. Set Up a Virtual Environment
bash
Copy code
python -m venv venv
.\venv\Scripts\activate
3. Install Dependencies
bash
Copy code
pip install -r requirements.txt
4. Run the Data Pipeline (One-time Setup)
Ensure all historical data is downloaded and cached.

bash
Copy code
.\run_update.bat
5. Launch the Streamlit Dashboard
bash
Copy code
streamlit run app.py
📁 Repository Structure
bash
Copy code
F1-Performance-Attribution-Model/
│
├── app.py                     # Streamlit dashboard
├── weekly_pull.py             # Automatic weekly data fetcher
├── master_analysis.py         # Core feature engineering and modeling script
├── run_update.bat             # Combined automation script
├── requirements.txt           # Python dependencies
├── fastf1_cache/              # Local telemetry cache
└── season_2021-2025_analysis.csv

License & Contributors
This project is licensed under the MIT License — see the LICENSE file for details.

Author: Rohit Kesav J. (Data Science & Model Development)

Collaborations via pull requests are welcome.