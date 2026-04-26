import os
import json
import requests
from time import sleep
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from PIL import Image
from io import BytesIO

SAVE_DIR = "nba_players"
os.makedirs(SAVE_DIR, exist_ok=True)
OUTPUT_FILE = "teams_players.json"

# Load existing JSON
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            team_dict = json.loads(content) if content else {}
    except json.JSONDecodeError:
        print("⚠️ Corrupted JSON detected. Starting with an empty dictionary.")
        team_dict = {}
else:
    team_dict = {}


def is_unknown_image(content: bytes) -> bool:
    unknown_path = os.path.join(SAVE_DIR, "unknown.png")
    if not os.path.exists(unknown_path):
        return False
    with open(unknown_path, "rb") as f:
        unknown_bytes = f.read()

    return content == unknown_bytes


def get_player_data(player_id: int):
    try:
        # Basic info
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
        if info['resultSets'][0]['rowSet']:
            pdata = dict(zip(info['resultSets'][0]['headers'], info['resultSets'][0]['rowSet'][0]))
        else:
            pdata = {}

        name = f"{pdata.get('FIRST_NAME', '?')} {pdata.get('LAST_NAME', '?')}"
        from_year = pdata.get("FROM_YEAR", "?")
        to_year = pdata.get("TO_YEAR", "?")
        pos = [p.strip() for p in pdata.get("POSITION", "").split('-') if p]

        # Career stats
        career = playercareerstats.PlayerCareerStats(player_id=player_id).get_dict()
        headers = career["resultSets"][0]["headers"]
        rows = career["resultSets"][0]["rowSet"]
        teams = sorted({
            r[headers.index("TEAM_ABBREVIATION")]
            for r in rows if r[headers.index("TEAM_ABBREVIATION")]
        })

        # Image
        img_filename = f"{name.replace(' ', '_')}.png"
        img_path = os.path.join(SAVE_DIR, img_filename)

        if not os.path.exists(img_path):
            r = requests.get(
                f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png",
                timeout=15
            )
            if r.status_code == 200 and not is_unknown_image(r.content):
                with open(img_path, "wb") as f:
                    f.write(r.content)
            else:
                img_filename = None

        return {
            "name": name,
            "positions": pos,
            "years": f"{from_year}-{to_year}",
            "teams": teams or ["UNK"],
            "image": img_filename
        }

    except Exception as e:
        err = str(e)
        print(f"⚠️ Player {player_id} failed: {err}")

        # Restart condition
        if "Read timed out" in err or "read timeout" in err.lower():
            print("⭕ Restarting due to timeout...")
            return "Restart"

        return None


def save_json(data, filename=OUTPUT_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def build_teams_json():
    all_players = players.get_players()
    print(f"📊 Found {len(all_players)} players")

    processed_names = {p["name"] for t in team_dict.values() for p in t}

    for i, p in enumerate(all_players, 1):
        full_name = p["full_name"]

        if full_name in processed_names:
            print(f"[{i}/{len(all_players)}] 🔶 {full_name} → already exists")
            continue

        pid = p["id"]
        pdata = get_player_data(pid)

        if pdata == "Restart":
            return False

        if pdata:
            for team in pdata["teams"]:
                if team not in team_dict:
                    team_dict[team] = []
                team_dict[team].append({
                    "name": pdata["name"],
                    "positions": pdata["positions"],
                    "years": pdata["years"],
                    "image": pdata["image"]
                })

            save_json(team_dict)
            processed_names.add(full_name)
            print(f"[{i}/{len(all_players)}] 🔷 {pdata['name']} → {pdata['teams']}")
        else:
            print(f"[{i}/{len(all_players)}] ❌ {full_name} → skipped")

        sleep(0.6)

    print(f"\n✅ Finished! Saved to {OUTPUT_FILE}")
    print(f"Results: {len(all_players) - (len(all_players)-len(processed_names))} / {len(all_players)}")
    return True


if __name__ == "__main__":
    success = build_teams_json()