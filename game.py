import json
from random import choice
from time import sleep

JSON_file = r"C:\Users\백승열\Desktop\NBA_DRAFT_GAME\teams_players.json"

TEAM_NAMES = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BRK": "Brooklyn Nets",
    "CHI": "Chicago Bulls",
    "CHO": "Charlotte Hornets",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}



# Load team data
with open(JSON_file, "r", encoding="utf-8") as f:
    teams_data = json.load(f)

team_initials = list(TEAM_NAMES.keys())

# Number of players (humans)
N = int(input("# of players: "))

# Initialize each player's positions (independent copies)
positions_template = {"PG": '', "SG": '', "SF": '', "PF": '', "C": ''}
player_teams = {i: positions_template.copy() for i in range(1, N + 1)}

# Draft rounds
for round_num in range(1, 6):
    print(f"\n===== ROUND {round_num} =====")
    sleep(1)
    for p in range(1, N + 1):
        random_team = choice(team_initials)
        full_name = TEAM_NAMES[random_team]
        print(f"\nPlayer {p}, your random team is: {full_name} ({random_team})")
        sleep(1)

        # Show available players from that team
        team_players = teams_data[random_team]
        # print("\nAvailable players:")
        # for player in team_players:  # Show first 10 for simplicity
        #     print(" -", player["name"])
        # print()

        selected_player = input("Choose a player: ")

        # Validation: Check if selected player exists in that team
        team_player_names = [player["name"] for player in team_players]
        while selected_player not in team_player_names:
            selected_player = input("Invalid player. Choose again: ")

        selected_position = input("Position (PG/SG/SF/PF/C): ").upper()
        while selected_position not in positions_template.keys():
            selected_position = input("Invalid position. Try again: ").upper()

        player_teams[p][selected_position] = selected_player

        # Show current team status
        print(f"\nPlayer {p}'s current team:")
        for pos in positions_template.keys():
            print(f"{pos}: {player_teams[p][pos]}")
