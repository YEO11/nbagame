import requests
import json
import time
from misc.api import API_KEY

# --- CONFIG ---
SEARCH_URL = "https://api.nba2kapi.com/api/players/search"
IMAGE_URL = ""

# 1. PRE-HAND DATA (Manual injection for Shaq, Jokic, Luka)
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
    with open("../data/database/2k_data.json", "w", encoding="utf-8") as f:
        json.dump(synced_results, f, indent=4, ensure_ascii=False)

    print("\n🔥 All done! '2k_data.json' is ready with clean ratings.")


if __name__ == "__main__":
    sync_all()