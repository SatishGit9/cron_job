import requests
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get configuration values from environment variables
DATABASE_NAME = os.getenv("DATABASE_NAME", "database.db")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

# Function to connect to the SQLite database and create necessary tables
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            player_name TEXT,
            country TEXT,
            date_added TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS country_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            last_added_date TIMESTAMP
        )
    ''')
    return conn

def fetch_players_grouped_by_country():
    try:
        response = requests.get(API_URL, params={"apikey": API_KEY})
        response.raise_for_status()
        
        # Print the entire response to verify the content
        response_json = response.json()
        print("API Response JSON:", response_json)

        if "data" not in response_json:
            print("No 'data' field in response:", response_json)
            return {}

        players = response_json["data"]
        if not players:
            print("No player data in 'data' field:", response_json)
            return {}

        # Process and group players by country
        country_groups = {}
        for player in players:
            country = player.get("country")
            if country:
                if country not in country_groups:
                    country_groups[country] = []
                country_groups[country].append(player)
        return country_groups

    except requests.RequestException as e:
        print("Error fetching player data:", e)
        return {}


# Function to get the next country to add based on the last added date
def get_next_country_to_add(country_groups):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the last country added from the country_tracker table
    cursor.execute("SELECT country FROM country_tracker ORDER BY last_added_date DESC LIMIT 1")
    last_country = cursor.fetchone()
    last_country = last_country[0] if last_country else None

    # Get the list of countries in alphabetical order
    country_list = sorted(country_groups.keys())

    # Find the index of the last added country, and get the next one
    if last_country and last_country in country_list:
        last_index = country_list.index(last_country)
        next_country = country_list[(last_index + 1) % len(country_list)]
    else:
        # Start from the first country if none have been added yet
        next_country = country_list[0]

    cursor.close()
    conn.close()
    return next_country

# Function to insert players from a specific country into the database
def insert_players_from_country(country, players):
    conn = get_db_connection()
    cursor = conn.cursor()

    for player in players:
        player_id = player.get("id")
        player_name = player.get("name")
        date_added = datetime.now()

        # Insert player into the database
        cursor.execute(
            "INSERT INTO players (player_id, player_name, country, date_added) VALUES (?, ?, ?, ?)",
            (player_id, player_name, country, date_added)
        )

    # Update the country tracker to record the last added country and date
    cursor.execute(
        "INSERT INTO country_tracker (country, last_added_date) VALUES (?, ?)",
        (country, datetime.now())
    )

    conn.commit()
    print(f"Added {len(players)} players from {country} to the database.")

    cursor.close()
    conn.close()

# Main function to fetch, group, and store players from one country daily
def fetch_and_store_one_country_daily():
    country_groups = fetch_players_grouped_by_country()
    if not country_groups:
        print("No player data fetched.")
        return

    next_country = get_next_country_to_add(country_groups)
    players_to_add = country_groups.get(next_country, [])
    
    if players_to_add:
        insert_players_from_country(next_country, players_to_add)
    else:
        print(f"No players found for country {next_country}.")
