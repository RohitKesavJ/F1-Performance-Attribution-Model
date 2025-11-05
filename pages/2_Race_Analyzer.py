# This file is `pages/2_Race_Analyzer.py`

import streamlit as st
import fastf1
import fastf1.plotting
import fastf1.core
import fastf1._api
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
import plotly.express as px
from f1_helpers import TEAM_COLORS, COMPOUND_COLORS 

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Detailed Race Analyzer",
    page_icon="📊",
    layout="wide"
)

# Enable the FastF1 cache
try:
    fastf1.Cache.enable_cache('./fastf1_cache')
except Exception as e:
    st.error(f"Error enabling FastF1 cache: {e}")
    st.stop()


# --- 2. CACHED HELPER FUNCTIONS ---

@st.cache_data
def get_race_schedule(year):
    """Gets the race schedule for a given year and caches it."""
    try:
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        return races
    except Exception as e:
        st.error(f"Error fetching schedule for {year}: {e}")
        return []

@st.cache_data
def load_session_data(year, race_name):
    """
    Loads a session's data from the cache and returns the
    key dataframes and a status code.
    """
    try:
        session = fastf1.get_session(year, race_name, 'R')
        session.load()
        return session.laps, session.results, session.event, "SUCCESS"
        
    except (fastf1._api.SessionNotAvailableError, fastf1.core.DataNotLoadedError):
        # Catches the error when data does not exist (future race or cancelled)
        return None, None, None, "NOT_AVAILABLE"
        
    except Exception as e:
        # Catches unexpected errors (e.g., corrupted cache file)
        st.error(f"An unknown error occurred while loading {year} {race_name}: {e}")
        st.warning("Please ensure this data is downloaded via `pull_data.py`.")
        return None, None, None, "ERROR"

# --- 3. APP LAYOUT ---
st.title("📊 Detailed Race Analyzer")
st.markdown("Select a year and a race to perform a deep-dive analysis. **Note: Initial load for a race may take 30-60 seconds.**")

# --- 4. FILTERS ---
years = [2025, 2024, 2023, 2022, 2021]
selected_year = st.sidebar.selectbox("Select Year", years)

race_names = get_race_schedule(selected_year)
if not race_names:
    st.warning(f"Could not find a race schedule for {selected_year}. The season may not have started yet.")
    st.stop()
selected_race = st.sidebar.selectbox("Select Race", race_names)

# --- 5. ON-DEMAND ANALYSIS ---
if st.sidebar.button("Analyze Race"):
    
    with st.spinner(f"Loading {selected_year} {selected_race} data..."):
        laps, results, event, status = load_session_data(selected_year, selected_race)

    # --- STATUS HANDLING ---
    if status == "NOT_AVAILABLE":
        st.info(f"The race ({selected_year} {selected_race}) has not happened yet, or the data is not yet available on the server.")
    
    elif status == "ERROR":
        st.error("Failed to load session. See error message above.")

    elif status == "SUCCESS":
        st.success(f"Data for {event['EventName']} loaded!")
        
        # --- ANALYSIS 1: Telemetry Battle (WITH EXPLANATION & FIX) ---
        st.header("Teammate Telemetry Battle (Fastest Laps)")
        
        # Visual Expander for Explanation
        with st.expander("🤔 What is Telemetry and how do I read this?"):
            st.markdown("""
                Telemetry is the **raw data** sent from the car's sensors. Comparing teammates' fastest laps reveals **driving style** differences:
                * **Speed (Top Chart):** Shows the overall pace advantage.
                * **Throttle/Brake (Middle/Bottom Charts):** Reveals how aggressive (binary ON/OFF) or smooth (gradual changes) a driver is. A **smoother driver** is often faster over a long race run.
                * **The Goal:** Look for differences in **Brake Points** and **Throttle Application** after a corner exit.
            """)
        
        teams_list = sorted(laps['Team'].dropna().unique())
        selected_team_telemetry = st.selectbox("Select Team for Telemetry", teams_list)
        
        drivers = sorted(laps[laps['Team'] == selected_team_telemetry]['Driver'].unique())
        
        if len(drivers) >= 2:
            try:
                col1, col2 = st.columns(2)
                driver_1 = col1.selectbox("Select Driver 1", drivers, index=0)
                driver_2 = col2.selectbox("Select Driver 2", drivers, index=1)
            
                d1_lap = laps.pick_drivers(driver_1).pick_fastest()
                d2_lap = laps.pick_drivers(driver_2).pick_fastest()
                
                # --- FIX: Check for NoneType before processing data ---
                if d1_lap is None or d2_lap is None:
                    st.warning(f"Telemetry unavailable: One or both drivers ({driver_1}, {driver_2}) did not record a complete fastest lap to generate data from.")
                    st.stop()
                # --- END FIX ---
                
                d1_tel = d1_lap.get_car_data().add_distance()
                d2_tel = d2_lap.get_car_data().add_distance()
                
                d1_tel['Driver'] = driver_1
                d2_tel['Driver'] = driver_2
                
                telemetry_data = pd.concat([d1_tel, d2_tel])
                
                team_color = TEAM_COLORS.get(selected_team_telemetry, "grey")
                color_map = {driver_1: team_color, driver_2: "cyan"} 

                # --- Use Expander for charts to clean up vertical space ---
                with st.expander("View Telemetry Charts", expanded=True):
                    fig_speed = px.line(telemetry_data, x="Distance", y="Speed", color="Driver",
                                        color_discrete_map=color_map, title=f"Speed: {driver_1} vs {driver_2}")
                    st.plotly_chart(fig_speed, use_container_width=True)
                    
                    fig_throttle = px.line(telemetry_data, x="Distance", y="Throttle", color="Driver",
                                            color_discrete_map=color_map, title=f"Throttle: {driver_1} vs {driver_2}")
                    st.plotly_chart(fig_throttle, use_container_width=True)
                    
                    fig_brake = px.line(telemetry_data, x="Distance", y="Brake", color="Driver",
                                        color_discrete_map=color_map, title=f"Brake: {driver_1} vs {driver_2}")
                    st.plotly_chart(fig_brake, use_container_width=True)
                
            except Exception as e:
                st.warning(f"Could not generate teammate plot: {e}")
        else:
            st.warning(f"Not enough drivers in {selected_team_telemetry} for comparison.")

        # --- ANALYSIS 2: Tyre Degradation (WITH EXPLANATION) ---
        st.header("Tyre Degradation Analysis")
        
        # Visual Expander for Explanation
        with st.expander("📉 What is Tyre Degradation?"):
            st.markdown("""
                This chart analyzes the **wear rate** of a specific tire compound over a race stint.
                * **The Trendline (Line):** Shows the average pace loss per lap. A **flatter line** (closer to horizontal) means **better tyre management** (low degradation).
                * **The Dots (Scatter):** Show individual lap times. If they are very scattered, the driver is **inconsistent**.
            """)
        
        driver_list = sorted(laps['Driver'].dropna().unique())
        selected_driver_deg = st.selectbox("Select Driver for Degradation", driver_list)
        
        try:
            winner_abbr = results.iloc[0]['Abbreviation']
            winner_laps = laps.pick_drivers(winner_abbr)
            
            # Use selected driver if selected, otherwise use race winner
            if selected_driver_deg:
                 winner_laps = laps.pick_drivers(selected_driver_deg)
                 winner_abbr = selected_driver_deg

            compounds = winner_laps['Compound'].dropna().unique()
            st.markdown(f"Analyzing stints for: **{winner_abbr}**")
            
            for compound in compounds:
                if compound is None: continue
                
                stint_laps = winner_laps[winner_laps['Compound'] == compound]
                clean_laps = stint_laps.pick_wo_box().pick_track_status('1').copy() 

                if len(clean_laps) < 3:
                    st.write(f"Not enough clean laps for {winner_abbr} on {compound} tires.")
                    continue

                clean_laps.loc[:, 'LapTimeSeconds'] = clean_laps['LapTime'].dt.total_seconds()
                final_laps = clean_laps[clean_laps['LapTimeSeconds'] < clean_laps['LapTimeSeconds'].mean() + 5].copy()

                if len(final_laps) > 2:
                    final_laps.loc[:, 'StintLap'] = final_laps['LapNumber'] - final_laps['Stint'].min() + 1
                    
                    fig = px.scatter(
                        final_laps,
                        x="StintLap",
                        y="LapTimeSeconds",
                        title=f"{winner_abbr} - '{compound}' Stint",
                        trendline="ols",
                        hover_data=['LapNumber', 'LapTimeSeconds']
                    )
                    fig.update_traces(marker=dict(color=COMPOUND_COLORS.get(compound, 'grey')))
                    fig.update_layout(
                        xaxis_title='Lap Number in Stint (Higher is More Wear)',
                        yaxis_title='Lap Time (s)',
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate degradation plot: {e}")