import json

JSON_FILE = r"C:\Users\bsyeol\Desktop\NBA_DRAFT_GAME\teams_players.json"

# Load JSON data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_data = {}

for team, players in data.items():
    seen = set()
    unique_players = []

    for player in players:
        name = player.get("name", "").strip()

        # Normalize special characters (e.g., remove accents)
        normalized_name = (
            name.encode("ascii", "ignore").decode("utf-8").lower()
        )

        if normalized_name not in seen:
            seen.add(normalized_name)
            unique_players.append(player)
        else:
            print(f"🗑️ Duplicate found in {team}: {name}")

    cleaned_data[team] = unique_players

# Save the cleaned data back
with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

print("✅ Finished cleaning duplicates from each team.")
