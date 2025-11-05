# This is your final, complete app.py file

import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import plotly.express as px
from f1_helpers import TEAM_COLORS # Assuming f1_helpers is in the root directory

# --- 1. CSS INJECTION FUNCTION (FOR SPACING AND LOOK) ---
def local_css(file_name):
    """Function to load and inject local CSS for styling."""
    try:
        # Assumes style.css is in the root folder
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Could not find {file_name}. CSS styling will be default.")

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="F1 Season Analysis (2021-2025)",
    page_icon="🏁",
    layout="wide"
)

# --- 3. CACHE THE DATA LOADING ---
@st.cache_data
def load_data():
    """Loads the master CSV file once and caches it."""
    try:
        # Load the correct 2021-2025 file
        data = pd.read_csv('season_2021-2025_analysis.csv', index_col=0)
        
        # --- FIX: Ensure the Driver column exists for the app logic ---
        if 'Driver' not in data.columns and data.index.name == 'Driver':
            data = data.reset_index()
        # --- END FIX ---
        
        return data
    except FileNotFoundError:
        st.error("Error: 'season_2021-2025_analysis.csv' not found. Please ensure this file was successfully committed to GitHub.")
        # Return an empty DataFrame with the required column names to prevent a crash
        return pd.DataFrame(columns=['Driver', 'TopSpeedST', 'AvgDegradation', 'PositionsGained', 'AvgConsistency', 'Points'])

# Load the master dataframe
master_df = load_data()

# --- Apply CSS and Global Title ---
local_css("style.css") # Load the custom spacing and styling
st.markdown("<h1 style='text-align: center; color: #F91536;'>F1 Performance Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Comparing Car Performance (Chariot) vs. Driver Skill (Charioteer) from 2021-2025.</p>", unsafe_allow_html=True)
st.divider()

# --- 4. DATA FILTERS (The Interactivity) ---
st.sidebar.header("Season Filters")

if not master_df.empty:
    seasons = sorted(master_df['Season'].unique(), reverse=True)
    selected_season = st.sidebar.selectbox("Select Season", seasons)
    
    season_df = master_df[master_df['Season'] == selected_season]
    
    season_teams = sorted(season_df['TeamName'].dropna().unique())
    selected_team = st.sidebar.selectbox("Select Team", ["All Teams"] + season_teams)

    filtered_df = season_df.copy()
    if selected_team != "All Teams":
        filtered_df = filtered_df[filtered_df['TeamName'] == selected_team]
else:
    selected_season = 2025
    filtered_df = pd.DataFrame()

# --- 5. DATA PREPARATION FOR PLOTS ---
if not filtered_df.empty:
    # Prepare data for the Driver Scatter Plot
    driver_perf = filtered_df.groupby('Driver')[['PositionsGained', 'AvgConsistency']].mean()
    driver_teams = filtered_df.drop_duplicates(subset=['Driver'], keep='last')[['Driver', 'TeamName']]
    driver_perf = driver_perf.merge(driver_teams, on='Driver', how='left').dropna()
    
    counts = filtered_df['Driver'].value_counts()
    drivers_to_keep = counts[counts > 5].index
    driver_perf = driver_perf[driver_perf['Driver'].isin(drivers_to_keep)]

# --- 6. F1 METRICS SNAPSHOT ---
if not filtered_df.empty and not filtered_df.groupby('Driver').agg({'Points': 'sum'}).empty:
    st.header(f"Season Snapshot: {selected_season}")
    
    aggregated_driver_df = filtered_df.groupby('Driver').agg(
        TotalPoints=('Points', 'sum'),
        AvgConsistency=('AvgConsistency', 'mean'),
        AvgPositionsGained=('PositionsGained', 'mean')
    ).dropna()

    if not aggregated_driver_df.empty:
        season_leader = aggregated_driver_df['TotalPoints'].idxmax()
        best_consistency_driver = aggregated_driver_df['AvgConsistency'].idxmin()
        best_starter_driver = aggregated_driver_df['AvgPositionsGained'].idxmax()

        col_m1, col_m2, col_m3 = st.columns(3)
        
        col_m1.metric("Season Points Leader", season_leader, f"Total: {aggregated_driver_df.loc[season_leader, 'TotalPoints']:.0f} pts")
        col_m2.metric("Most Consistent Driver", best_consistency_driver, f"{aggregated_driver_df.loc[best_consistency_driver, 'AvgConsistency']:.3f}s StDev (Lower is Better)")
        col_m3.metric("Best Race Starter", best_starter_driver, f"+{aggregated_driver_df.loc[best_starter_driver, 'AvgPositionsGained']:.1f} positions (Avg)")

st.markdown("---") # Visual divider

# --- 7. THE GRAND MODEL ---
st.header(f"The 'Grand Model' ({selected_season})")

with st.expander("❓ What does this model tell me?"):
    st.markdown("""
        This table uses **Linear Regression** to estimate which factors contribute most to scoring points across the season.
        * **Coefficient:** The size of the number indicates its importance.
        * **Positive Coefficient (Green):** The factor helps a driver score more points (e.g., getting a higher position).
        * **Negative Coefficient (Red):** The factor hurts a driver's score (e.g., being inconsistent or driving a high-drag car).
    """)

features = ['TopSpeedST', 'AvgDegradation', 'PositionsGained', 'AvgConsistency']
target = 'Points'
model_df = filtered_df[features + [target]].dropna()

if not model_df.empty and len(model_df) > 5:
    try:
        X = model_df[features]
        y = model_df[target]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = LinearRegression().fit(X_scaled, y)
        
        feature_importance = pd.DataFrame({
            'Feature': features,
            'Coefficient (Impact on Points)': model.coef_
        }).sort_values('Coefficient (Impact on Points)', ascending=False)
        
        st.dataframe(feature_importance, use_container_width=True)
    except Exception as e:
        st.error(f"Could not build the model for this selection: {e}")
else:
    st.warning("Not enough data to build a model for this selection (need more than 5 races/teams).")

# --- 8. PLOTS ---
st.header(f"Driver & Car Performance Breakdown ({selected_season})")

col1, col2 = st.columns(2)

with col1:
    # Title is now cleaner
    st.subheader("Car Performance: Top Speed Trap")
    
    # Use st.expander for the explanation to save vertical space, making it look cleaner
    with st.expander("🤔 What is the 'Top Speed Paradox'?"):
        st.markdown("""
            This chart shows the average **maximum speed** reached by each team. 
            A very high maximum speed often suggests the car is optimized for low drag (low downforce), which is often correlated with poor **cornering** and high **tire wear** (hence, the Paradox).
        """)
    
    st.markdown("##### Average Top Speed (Higher is NOT always better)") # Smaller title for plot
    
    if not filtered_df.empty:
        car_perf = filtered_df.groupby('TeamName')['TopSpeedST'].mean().sort_values(ascending=False).reset_index()
        
        if not car_perf.empty:
            fig = px.bar(
                car_perf,
                x='TopSpeedST',
                y='TeamName',
                orientation='h',
                title=f'Team Speed Rank',
                color='TeamName',
                color_discrete_map=TEAM_COLORS,
                labels={'TopSpeedST': 'Average Speed Trap (km/h)', 'TeamName': ''} # Remove redundant Y-axis label
            )
            fig.update_layout(
                yaxis={'categoryorder':'total ascending'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
        
with col2:
    st.subheader("Driver Skill: Consistency vs. Racecraft") # Main section title
    
    # Keep the Key to Understanding in a single expander
    with st.expander("🔑 Key to Understanding this Chart"):
        st.markdown("""
            * **The Goal:** Drivers in the **Top-Left Quadrant** are ideal.
            * **Consistency (X-axis):** **Lower (left) is better** (less variation in lap times).
            * **Racecraft (Y-axis):** **Higher (top) is better** (more positions gained on Lap 1).
        """)
    
    st.markdown("##### Performance Scatter Plot") # Smaller title for plot
    
    if not filtered_df.empty and not driver_perf.empty:
        # Re-merge to ensure the data is perfectly clean for the chart
        driver_perf_chart = driver_perf.reset_index().copy() 
        
        fig = px.scatter(
            driver_perf_chart,
            x='AvgConsistency',
            y='PositionsGained',
            color='TeamName', 
            color_discrete_map=TEAM_COLORS,
            title=f'Driver Performance Scatter Plot',
            text='Driver', 
            hover_data={'TeamName': True, 'AvgConsistency': ':.3f', 'PositionsGained': ':.1f'}
        )
        fig.update_layout(
            xaxis_title='Avg Lap Consistency (StDev - Lower is Better)',
            yaxis_title='Avg Positions Gained (Higher is Better)',
            template="plotly_dark"
        )
        fig.update_traces(textposition='top center')
        st.plotly_chart(fig, use_container_width=True)