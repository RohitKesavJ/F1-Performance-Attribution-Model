import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import logging
import os
from scipy import stats

# --- 1. SETUP ---
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Enable and configure the cache
cache_dir = './fastf1_cache'
if not os.path.exists(cache_dir):
    logging.error("Cache directory not found! Please run setup_cache.py first.")
    exit()
fastf1.Cache.enable_cache(cache_dir)
logging.info(f"Cache enabled at: {cache_dir}")

# --- 2. ANALYSIS FUNCTIONS ---
# (These functions are unchanged)

def get_top_speeds(laps):
    """
    Analyzes the top speed trap speed for each driver.
    Returns a DataFrame with 'Driver' as the index.
    """
    try:
        driver_top_speeds = laps.groupby('Driver')['SpeedST'].max()
        return driver_top_speeds.to_frame(name='TopSpeedST')
    except Exception as e:
        logging.warning(f"Could not analyze top speeds: {e}")
        return pd.DataFrame()

def get_start_performance(session):
    """
    Analyzes positions gained/lost at the start.
    Returns a DataFrame with 'Driver' as the index.
    """
    try:
        # Get grid data
        results_data = session.results
        grid_df = results_data[['Abbreviation', 'GridPosition', 'TeamName']]
        
        # Get lap 1 data
        lap_1_data = session.laps.pick_laps(1) 
        lap_1_df = lap_1_data[['Driver', 'Position']]
        
        # Merge (using the correct, different keys)
        start_analysis = pd.merge(
            grid_df,
            lap_1_df,
            left_on='Abbreviation', 
            right_on='Driver'       
        )
        
        # Calculate
        start_analysis = start_analysis[start_analysis['GridPosition'] > 0]
        start_analysis['Position'] = pd.to_numeric(start_analysis['Position'])
        start_analysis['PositionsGained'] = start_analysis['GridPosition'] - start_analysis['Position']
        
        # Set 'Driver' as the index for easy merging later
        return start_analysis.set_index('Driver')[['PositionsGained']]
    except Exception as e:
        logging.warning(f"Could not analyze start performance: {e}")
        return pd.DataFrame()

def get_stint_performance(laps):
    """
    Analyzes average degradation and consistency for each driver
    over all their clean stints. Returns a DataFrame.
    """
    driver_stints = []
    drivers = laps['Driver'].unique()
    
    for driver in drivers:
        driver_laps = laps.pick_drivers(driver)
        stints = driver_laps['Stint'].unique()
        
        driver_degs = []
        driver_cons = []
        
        for stint in stints:
            try:
                laps_stint = driver_laps[driver_laps['Stint'] == stint]
                
                # Use the built-in filters
                clean_laps = laps_stint.pick_wo_box().pick_track_status('1')
                
                if len(clean_laps) < 3:
                    continue # Not enough data
                
                clean_laps['LapTimeSeconds'] = clean_laps['LapTime'].dt.total_seconds()
                final_laps = clean_laps[clean_laps['LapTimeSeconds'] < clean_laps['LapTimeSeconds'].mean() + 5]
                
                if len(final_laps) < 3:
                    continue
                    
                # Get Consistency
                consistency = final_laps['LapTimeSeconds'].std()
                driver_cons.append(consistency)
                
                # Get Degradation
                final_laps['StintLap'] = final_laps['LapNumber'] - final_laps['Stint'].min() + 1
                res = stats.linregress(final_laps['StintLap'], final_laps['LapTimeSeconds'])
                degradation = res.slope
                driver_degs.append(degradation)
            
            except Exception:
                continue # Skip stint if error
        
        # Average the performance over all stints
        if driver_degs:
            driver_stints.append({
                'Driver': driver,
                'AvgDegradation': np.mean(driver_degs),
                'AvgConsistency': np.mean(driver_cons)
            })
            
    if not driver_stints:
        return pd.DataFrame()
        
    return pd.DataFrame.from_records(driver_stints).set_index('Driver')


# --- 3. THE MAIN LOOP (THIS IS THE UPDATED PART) ---
def main():
    """
    Main function to loop through all races, analyze, and save.
    """
    all_race_data = [] # This will hold all our DataFrames
    
    # --- CHANGE 1: List all the years you downloaded ---
    YEARS_TO_ANALYZE = [2025,2024, 2023, 2022, 2021] 
    
    # --- CHANGE 2: Loop over the list of years ---
    for year in YEARS_TO_ANALYZE:
        logging.info(f"========== PROCESSING YEAR: {year} ==========")
        
        schedule = fastf1.get_event_schedule(year) # Use 'year' variable
        
        for i, event in schedule.iloc[1:].iterrows(): # Skip pre-season testing
            if event['EventFormat'] == 'testing':
                continue
                
            logging.info(f"--- Processing Race: {event['EventName']} ({year}) ---")
            
            try:
                session = fastf1.get_session(year, event['EventName'], 'R') # Use 'year' variable
                session.load()
                laps = session.laps
                
                # --- Run all our analysis functions ---
                top_speeds = get_top_speeds(laps)
                start_perf = get_start_performance(session)
                stint_perf = get_stint_performance(laps)
                
                # --- Get final results ---
                results = session.results
                results = results.rename(columns={'Abbreviation': 'Driver'})
                results = results[['Driver', 'TeamName', 'Position', 'Points']]
                
                # --- Combine all data for this race ---
                race_df = results.set_index('Driver').join(
                    [top_speeds, start_perf, stint_perf]
                )
                
                # Add event info
                race_df['RaceName'] = event['EventName']
                race_df['RaceDate'] = event['EventDate']
                
                # --- CHANGE 3: Add a 'Season' column ---
                # This is essential for your web app filters!
                race_df['Season'] = year
                
                all_race_data.append(race_df)
                logging.info(f"Successfully processed {event['EventName']}")
                
            except Exception as e:
                logging.error(f"Could not process {event['EventName']} ({year}): {e}")
            
    # --- 4. SAVE FINAL RESULTS ---
    logging.info("All races processed. Concatenating and saving...")
    
    master_df = pd.concat(all_race_data)
    
    # --- CHANGE 4: Update the output filename ---
    output_file = 'season_2021-2025_analysis.csv'
    master_df.to_csv(output_file)
    
    logging.info(f"--- Analysis Complete! ---")
    logging.info(f"Master DataFrame saved to: {output_file}")
    print(master_df.head()) # Print first 5 rows

# This makes the script runnable
if __name__ == "__main__":
    main()