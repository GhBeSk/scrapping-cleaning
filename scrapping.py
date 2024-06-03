import time
import os
import pandas as pd
import json
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.ERROR)
BASE_URL = "https://www.basketball-reference.com/players"

def fetch_player_seasons_data(player_ids, start_season, end_season):
    try:
        for player_id in player_ids:
            print(f"Scraping data for player {player_id}...")
            html_file_path = f"dataset/html/{player_id}.html"
            csv_file_path = f"dataset/csv/{player_id}.csv"
            
            # Check if HTML and CSV files already exist for the player
            if os.path.exists(html_file_path) and os.path.exists(csv_file_path):
                print(f"Skipping {player_id} as data is already scraped.")
                continue
    
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                user_agent_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                context = browser.new_context(user_agent=user_agent_string)
                page = context.new_page()
    
                # Handling Dialogs
                def handle_dialog(dialog):
                    print(f"Dialog message: {dialog.message}")
                    dialog.dismiss()
    
                page.on("dialog", handle_dialog)
    
                all_tables_html = ""  # To accumulate HTML content
    
                for year in range(start_season, end_season + 1):
                    first_letter = player_id[0]
                    url = f"{BASE_URL}/{first_letter}/{player_id}/gamelog/{year}"
                    
                    retries = 3
                    while retries:
                        try:
                            page.goto(url, wait_until="domcontentloaded")
                            time.sleep(10)  # Additional delay for JavaScript to load content
                        
                            # Accumulate rendered page HTML
                            all_tables_html += page.content()
                            break
    
                        except Exception as e:
                            retries -= 1
                            if retries == 0:
                                logging.error(f"Error while fetching data for {year}: {e}")
                                break
                            print(f"Error encountered. Retrying {3 - retries + 1}/3 ...")
                            time.sleep(10)
    
                    time.sleep(4)  # Sleep to ensure less than 15 requests per minute
    
                browser.close()
    
                # Ensure directories exist
                if not os.path.exists("dataset/html"):
                    os.makedirs("dataset/html")
                if not os.path.exists("dataset/csv"):
                    os.makedirs("dataset/csv")
    
                # Write the accumulated HTML content to a file specific to the player
                with open(html_file_path, "w", encoding="utf-8") as f:
                    f.write(all_tables_html)
    
                    # Try to extract and save CSV
                try:
                    print(f"Extracting CSV data for player {player_id}...")
                    extract_specific_table_from_html_to_csv(html_file_path, csv_file_path, "pgl_basic")
                    print(f"CSV data extraction completed for player {player_id}.")
                except ValueError as e:
                    print(f"No tables found for player {player_id}. Deleting HTML file and continuing.")
                    # Delete the HTML file if no tables were found
                    if os.path.exists(html_file_path):
                        os.remove(html_file_path)
                    continue  # Continue to the next player ID
                except Exception as e:
                    print(f"An error occurred while extracting data for player {player_id}: {e}")
                    continue  # Continue to the next player ID
    except KeyboardInterrupt:
            print("Interrupt received! Finishing the current player's scraping and data extraction before stopping.")
            # Extract and save CSV for the current player before exiting
            extract_specific_table_from_html_to_csv(html_file_path, csv_file_path, "pgl_basic")
            print("Exiting after completing the current player's data extraction.")

def extract_specific_table_from_html_to_csv(html_filename, csv_filename, table_id):
    # Use lxml's HTML parser to parse the file
    with open(html_filename, 'r', encoding="utf-8") as f:
        content = f.read()
        tables = pd.read_html(content, attrs={"id": table_id})

    # Since multiple tables with the same id might be present, we concatenate them
    final_df = pd.concat(tables, ignore_index=True)
    
    # Save the concatenated DataFrame to a CSV file
    final_df.to_csv(csv_filename, index=False)


# Load player IDs from the .json file
with open('player_id_to_name_mapping.json', 'r') as file:
    data = json.load(file)
    player_ids = list(data.keys())
    
# Call the function with desired parameters
start_season = 2010
end_season = 2020
fetch_player_seasons_data(player_ids, start_season, end_season)



