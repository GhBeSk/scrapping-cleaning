import pandas as pd
import numpy as np
import os

def custom_mean(values):
    values = values[~values.isin(['Did Not Dress', 'Inactive', 'Did Not Play', 'Not With Team', 'Suspended', 'Player Suspended'])]
    if values.empty:
        return None
    val = values.iloc[0]
    if isinstance(val, str) and ".." in val:
        numbers = [float(f".{x}") for x in val.split(".")[1:-1]]
    elif isinstance(val, str) and ":" in val:
        total_minutes = sum([int(minute) + int(second)/60 for minute, second in values.str.split(":")])
        numbers = [total_minutes / len(values)]
    else:
        numbers = values.dropna().astype(float)
    rounding_decimals = 3 if any([perc in str(values.name) for perc in ['FT%', '3P%', 'FG%']]) else 1
    return round(np.mean(numbers), rounding_decimals) if len(numbers) > 0 else None

def clean_csv(input_filename, output_filename):
    df = pd.read_csv(input_filename)
    df.drop(columns=['Tm', 'Unnamed: 5', 'Opp', 'GS', 'Unnamed: 7', 'GmSc'], inplace=True, errors='ignore')
    df['G'] = pd.to_numeric(df['G'].replace('', np.nan), errors='coerce')


    if 'Age' in df.columns:
        # Ensure the 'Age' column is of string type before extracting digits
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'].str.extract('(\d{2})')  # Extract the first two digits
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')  # Convert the extracted string to numeric

    def convert_to_decimal(minutes):
        if ":" in str(minutes):
            min_part, sec_part = str(minutes).split(":")
            return round(float(min_part) + float(sec_part)/60, 1)
        return minutes

    df['MP'] = df['MP'].apply(convert_to_decimal)
    df = df[pd.to_numeric(df['Rk'], errors='coerce').notnull()]
    df['Season'] = (df['Rk'] == '1').cumsum()
    
    earliest_date = pd.to_datetime(df['Date'].dropna().min())
    start_season = earliest_date.year

    # Convert date strings to datetime objects and sort by date to ensure correct order
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values(by='Date', inplace=True)
    df.reset_index(drop=True, inplace=True)  # Reset the index to make sure the index is continuous

    # Calculate the days between games
    df['Days Between Games'] = df['Date'].diff().dt.days
    df['Days Between Games'] = df['Days Between Games'].fillna(0).astype(int)
    
    df['Rest Type'] = 'Normal'  # Default to 'Normal' rest type
    df['Days Rested'] = df['Date'].diff().dt.days.fillna(0).astype(int)

    rest_conditions = ['Did Not Dress', 'Inactive', 'Did Not Play', 'Not With Team', 'Player Suspended', 'Suspended']
    df['Rest Type'] = np.where(df['MP'].isin(rest_conditions), 'Load Management', df['Rest Type'])  # Preset to Load Management

    # Detect sequences of rest and mark them with the number of days rested
    # Check and update Rest Type for sequences of rest
       # Check and update Rest Type for sequences of rest
    for i in range(1, len(df)):
        if df.loc[i, 'MP'] in rest_conditions:
            df.loc[i, 'Rest Type'] = 'Load Management'
            
            # Now check for sequences of rest longer than 3 games
            rest_sequence_start = i
            rest_sequence_count = 1  # We already know there's at least one rest condition
    
            # Look ahead to count consecutive rest conditions
            while i + 1 < len(df) and df.loc[i + 1, 'MP'] in rest_conditions:
                rest_sequence_count += 1
                i += 1  # Move the index forward
    
            # The end of the rest period is where the sequence has stopped
            rest_period_end = rest_sequence_start + rest_sequence_count
    
            # If there are more than 3 consecutive rests, classify all as injured/illness
            if rest_sequence_count > 3:
                for j in range(rest_sequence_start, rest_period_end):
                    df.loc[j, 'Rest Type'] = 'Injured/Illness'
                    # Calculate 'Days Rested' for the last game in the sequence
                    if j == rest_period_end - 1:  
                        next_game_index = j + 1 if j + 1 < len(df) else j
                        df.loc[j, 'Days Rested'] = (df.loc[next_game_index, 'Date'] - df.loc[j, 'Date']).days
                    else:
                        df.loc[j, 'Days Rested'] = 0  # Zero for all but the last game in the sequence
    
            # Identify if the rest sequence is ending and check if we should reclassify the last three games
            if rest_period_end < len(df) and rest_sequence_count > 3:
                # Look at the three games preceding the rest_period_end
                last_three_games = range(rest_period_end - 3, rest_period_end)
                
                # If the game before the sequence was not 'Injured/Illness', then adjust the last three games
                if rest_sequence_start > 0 and df.loc[rest_sequence_start - 1, 'Rest Type'] != 'Injured/Illness':
                    for game_idx in last_three_games:
                        if df.loc[game_idx, 'Rest Type'] == 'Injured/Illness':
                            df.loc[game_idx, 'Rest Type'] = 'Load Management'

    
        for i in range(1, len(df)-1):  # Adjusted range to prevent out-of-bounds
            # Identify Load Management entries that are not Injured/Illness yet
            if df.loc[i, 'Rest Type'] == 'Load Management':
                # Check if it's preceded or followed by Injured/Illness
                if df.loc[i-1, 'Rest Type'] == 'Injured/Illness' or df.loc[i+1, 'Rest Type'] == 'Injured/Illness':
                    df.loc[i, 'Rest Type'] = 'Injured/Illness'
        
    # Initialize 'Days Rested' to zero for all rows
    df['Days Rested'] = 0
    
    # Carry over 'Days Rested' from Load Management and Injury/Illness to the next 'Normal' game
    for i in range(1, len(df)):
        # If it's the first game of the season or there was no game before, set 'Days Rested' to 0
        if df.loc[i, 'Rk'] == '1' or df.loc[i - 1, 'Season'] != df.loc[i, 'Season']:
            df.loc[i, 'Days Rested'] = 0
        else:
            # If the current game is 'Normal', calculate the 'Days Rested' since the last 'Normal' game
            if df.loc[i, 'Rest Type'] == 'Normal':
                last_normal_game_idx = i - 1
                # Accumulate 'Days Rested' only if the previous game was also 'Normal'
                while last_normal_game_idx >= 0 and df.loc[last_normal_game_idx, 'Rest Type'] != 'Normal':
                    last_normal_game_idx -= 1
                # If a 'Normal' game is found before, calculate the days rested
                if last_normal_game_idx >= 0:
                    df.loc[i, 'Days Rested'] = (df.loc[i, 'Date'] - df.loc[last_normal_game_idx, 'Date']).days
                # If no 'Normal' game is found before, it means it's the first game of the season
                else:
                    df.loc[i, 'Days Rested'] = 0
    
    # Set 'Days Rested' to 0 for Load Management and Injury/Illness games
    df.loc[df['Rest Type'].isin(['Load Management', 'Injured/Illness']), 'Days Rested'] = 0

    # Drop the 'Days Between Games' column as it's no longer needed
    df.drop('Days Between Games', axis=1, inplace=True)


    df['Season'] = df['Season'].apply(lambda x: f"{start_season+x-1}-{start_season+x}")
    columns_to_average = ['PTS', 'AST', 'TRB', 'FG%', 'MP', 'FT%', '3P%', 'BLK', 'TOV', 'STL']
    average_stats = df.groupby('Season')[columns_to_average].agg(custom_mean).reset_index()
    average_stats['Games Played'] = df.groupby('Season')['G'].max().reset_index(drop=True)
    column_renaming = {
        'G': 'Game',
        'Date': 'Game Date'
    }
    df.rename(columns=column_renaming, inplace=True)
    df['Game'] = df['Game'].apply(lambda x: int(x) if not pd.isna(x) else np.nan)
    average_stats['Games Played'] = average_stats['Games Played'].apply(lambda x: int(x) if not pd.isna(x) else np.nan)
    for column in ['FT%', '3P%', 'FG%']:
        average_stats[column] = average_stats[column].astype(float).round(3)
    for col in columns_to_average:
        average_stats.rename(columns={col: f"Average {col}"}, inplace=True)
    df['Type'] = 'Regular'
    average_stats['Type'] = 'Average'
    result_df = pd.concat([df, average_stats], ignore_index=True)
    result_df['Game'] = result_df['Game'].apply(lambda x: int(x) if not pd.isna(x) else np.nan)
    result_df['Games Played'] = result_df['Games Played'].apply(lambda x: int(x) if not pd.isna(x) else np.nan)

    result_df.to_csv(output_filename, index=False)

def clean_all_csv_files():
    input_directory = "dataset/csv/"
    output_directory = "cleaned_dataset/"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for filename in os.listdir(input_directory):
        if filename.endswith(".csv"):
            player_id = filename.split('.')[0]
            output_filename = f"{player_id}_cleaned.csv"
            input_filepath = os.path.join(input_directory, filename)
            output_filepath = os.path.join(output_directory, output_filename)
            if not os.path.exists(output_filepath):
                print(f"Cleaning {filename}...")
                clean_csv(input_filepath, output_filepath)
            else:
                print(f"Skipping {filename} as it is already cleaned.")

clean_all_csv_files()

