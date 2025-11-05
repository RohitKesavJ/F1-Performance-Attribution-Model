# This is your new weekly_pull.py
import fastf1
import fastf1._api  # Import the api module to catch the specific error
import logging
import os
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

cache_dir = './fastf1_cache'
if not os.path.exists(cache_dir):
    logging.error("Cache directory not found!")
    exit()

fastf1.Cache.enable_cache(cache_dir)
logging.info(f"Cache enabled at: {cache_dir}")

# --- THIS IS THE SMART PART ---
# Automatically get the current year
CURRENT_YEAR = datetime.date.today().year
logging.info(f"Checking for new data for the {CURRENT_YEAR} season...")
# ------------------------------

SESSIONS = ['Qualifying', 'Race']

try:
    schedule = fastf1.get_event_schedule(CURRENT_YEAR)
    
    # Get all races that should have happened by now
    # This will check all 2025 races since your clock is set to Nov 2025
    races_to_check = schedule[schedule['EventDate'] < datetime.datetime.now()]
    
    for i, event in races_to_check.iloc[1:].iterrows(): 
        if event['EventFormat'] == 'testing':
             continue

        logging.info(f"--- Checking Event: {event['EventName']} ({CURRENT_YEAR}) ---")
        for session_name in SESSIONS:
            try:
                session = fastf1.get_session(CURRENT_YEAR, event['EventName'], session_name)
                session.load() 
                logging.info(f"Data for {session_name} is up to date.")
            
            # --- THIS IS THE NEW CODE ---
            # This "catches" the error when data doesn't exist yet
            except fastf1._api.SessionNotAvailableError:
                logging.warning(f"Data for {session_name} is not yet available on the server. Skipping.")
                continue  # Move to the next session
            # --- END NEW CODE ---
            
            except Exception as e:
                # This catches other errors, like the rate limit
                logging.warning(f"Could not load {session_name}: {e}")

    logging.info(f"--- Data check for {CURRENT_YEAR} complete. ---")

except Exception as e:
    logging.error(f"Could not get schedule for {CURRENT_YEAR}: {e}")