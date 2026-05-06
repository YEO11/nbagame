import requests
import json
import time

# --- CONFIG ---
API_KEY = "2k_yq440mfukup3lmaxovd2cqdvf0xzy2z0"
SEARCH_URL = "https://api.nba2kapi.com/api/players/search"

# 1. PRE-HAND DATA (Manual injection for Shaq, Jokic, Luka)
MANUAL_PLAYERS = {
    "C": [
        {
            "name": "Nikola Jokic",
            "overall": 98,
            "tier": "Galaxy Opal",
            "attributes": {
                "outsideScoring": 92, "insideScoring": 92, "athleticism": 74, "playmaking": 85,
                "rebounding": 88, "defending": 71, "threePointShot": 86, "midRangeShot": 98,
                "closeShot": 99, "passAccuracy": 93, "postControl": 98, "standingDunk": 90
            }
        },
        {
            "name": "Shaquille O'Neal",
            "overall": 98,
            "tier": "Galaxy Opal",
            "attributes": {
                "outsideScoring": 32, "insideScoring": 91, "athleticism": 91, "playmaking": 59,
                "rebounding": 98, "defending": 86, "threePointShot": 26, "standingDunk": 99,
                "strength": 99, "block": 98, "interiorDefense": 98, "speed": 78
            }
        }
    ],
    "PG": [
        {
            "name": "Luka Doncic",
            "overall": 97,
            "tier": "Galaxy Opal",
            "attributes": {
                "outsideScoring": 87, "insideScoring": 84, "athleticism": 78, "playmaking": 93,
                "rebounding": 71, "defending": 61, "threePointShot": 86, "ballHandle": 95,
                "passAccuracy": 95, "speedWithBall": 83, "drivingLayup": 96
            }
        }
    ]
}


def get_tier_name(overall):
    """Fallback to determine 'Badge Color' if the API doesn't provide a specific name."""
    if overall >= 99: return "Dark Matter"
    if overall >= 97: return "Galaxy Opal"
    if overall >= 95: return "Pink Diamond"
    if overall >= 90: return "Diamond"
    return "Amethyst"


def fetch_absolute_best(player_name):
    headers = {'X-API-Key': API_KEY}
    team_types = ["allt", "class", "curr"]
    all_versions = []

    for t_type in team_types:
        params = {"q": player_name, "teamType": t_type, "limit": 5}
        try:
            response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=10)
            res_data = response.json()
            if res_data.get("success") and res_data.get("data"):
                all_versions.extend(res_data["data"])
        except:
            continue

    if not all_versions:
        return None

    best = max(all_versions, key=lambda x: x.get('overall', 0))

    # Clean the data: Only keep Name, Overall, Tier, and Attributes
    return {
        "name": best.get("name"),
        "overall": best.get("overall"),
        "tier": get_tier_name(best.get("overall")),
        "attributes": best.get("attributes", {})
    }


def sync_all():
    # Load original pool
    try:
        with open(r"data\popular_players.json", "r", encoding="utf-8") as f:
            local_pool = json.load(f)
    except FileNotFoundError:
        print("Error: popular_players.json not found in data folder.")
        return

    synced_results = {}

    for pos, players in local_pool.items():
        synced_results[pos] = []
        print(f"\n--- Syncing {pos} ---")

        for p in players:
            name = p['name']

            # Check if we have manual data for this player first
            manual_match = next((m for m in MANUAL_PLAYERS.get(pos, []) if m['name'] == name), None)

            if manual_match:
                synced_results[pos].append(manual_match)
                print(f"⭐ Manual Injection: {name} (Galaxy Opal)")
                continue

            # Otherwise, fetch from API
            print(f"Searching {name}...", end=" ", flush=True)
            api_data = fetch_absolute_best(name)

            if api_data:
                synced_results[pos].append(api_data)
                print(f"✅ Found: {api_data['overall']} OVR")
            else:
                print("❌ Not found.")

            time.sleep(0.1)

    # Final Save
    with open("../data/2k_data.json", "w", encoding="utf-8") as f:
        json.dump(synced_results, f, indent=4, ensure_ascii=False)

    print("\n🔥 All done! '2k_data.json' is ready with clean ratings.")


if __name__ == "__main__":
    sync_all()