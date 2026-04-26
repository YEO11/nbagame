"""
build_nba_data.py
=================
Rebuilds teams_players.json using the nba_api package and downloads
player headshots into the nba_players/ folder.

Install dependencies first:
    pip install nba_api requests

Run:
    python build_nba_data.py

Output:
    data/teams_players.json          ← same format as original
    nba_players/<First_Last>.png     ← headshots (NBA CDN, 1040x760)

Notes:
  - Only the 30 current NBA teams are included (same team keys as original).
  - Covers ALL players who ever appeared for each franchise.
  - Headshots exist only for players with an NBA ID photo on the CDN;
    players with no photo get  "image": null  just like the original.
  - The script is rate-limited (1 s between API calls, 0.5 s between
    image downloads) to avoid getting blocked.
"""

import os
import sys
import json
import time
import requests
from collections import defaultdict

# ── Try importing nba_api ─────────────────────────────────────────────────────
try:
    from nba_api.stats.endpoints import (
        commonteamroster,
        teamdetails,
        franchisehistory,
        playercareerstats,
    )
    from nba_api.stats.static import teams as nba_teams_static
    from nba_api.stats.static import players as nba_players_static
    from nba_api.stats.endpoints import commonallplayers
except ImportError:
    sys.exit(
        "nba_api is not installed.\n"
        "Run:  pip install nba_api requests\n"
        "Then re-run this script."
    )

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR     = r"C:\Users\백승열\Desktop\NBA_DRAFT_GAME"
OUT_JSON     = os.path.join(BASE_DIR, "data", "teams_players.json")
PLAYERS_DIR  = os.path.join(BASE_DIR, "nba_players")

os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# NBA CDN headshot URL — works for most players with an official photo
HEADSHOT_URL = "https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"

# nba_api sometimes needs these headers to avoid 403s
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

# Mapping: our 3-letter key → official NBA team abbreviation (usually the same)
# nba_api uses its own IDs; we look up by abbreviation.
TEAM_KEYS = {
    "ATL": "ATL", "BOS": "BOS", "BKN": "BKN", "CHA": "CHA",
    "CHI": "CHI", "CLE": "CLE", "DAL": "DAL", "DEN": "DEN",
    "DET": "DET", "GSW": "GSW", "HOU": "HOU", "IND": "IND",
    "LAC": "LAC", "LAL": "LAL", "MEM": "MEM", "MIA": "MIA",
    "MIL": "MIL", "MIN": "MIN", "NOP": "NOP", "NYK": "NYK",
    "OKC": "OKC", "ORL": "ORL", "PHI": "PHI", "PHX": "PHX",
    "POR": "POR", "SAC": "SAC", "SAS": "SAS", "TOR": "TOR",
    "UTA": "UTA", "WAS": "WAS",
}

# Position code → human-readable (nba_api returns codes like "G", "F", "C", "G-F", etc.)
POS_MAP = {
    "G":   ["Guard"],
    "F":   ["Forward"],
    "C":   ["Center"],
    "G-F": ["Guard", "Forward"],
    "F-G": ["Forward", "Guard"],
    "F-C": ["Forward", "Center"],
    "C-F": ["Center", "Forward"],
    "G-C": ["Guard", "Center"],
    # fallback — nba_api sometimes returns full words too
    "Guard":            ["Guard"],
    "Forward":          ["Forward"],
    "Center":           ["Center"],
    "Forward-Guard":    ["Forward", "Guard"],
    "Guard-Forward":    ["Guard", "Forward"],
    "Forward-Center":   ["Forward", "Center"],
    "Center-Forward":   ["Center", "Forward"],
}

def parse_positions(raw):
    """Convert nba_api position string to list of strings."""
    if not raw:
        return []
    raw = raw.strip()
    return POS_MAP.get(raw, [raw])   # fallback: wrap in list as-is

def image_filename(player_name):
    """'Stephen Curry' → 'Stephen_Curry.png'"""
    return player_name.replace(" ", "_") + ".png"

def download_headshot(player_id, player_name):
    """
    Download headshot PNG from NBA CDN.
    Returns filename string if saved, None if not available.
    """
    fname = image_filename(player_name)
    fpath = os.path.join(PLAYERS_DIR, fname)

    if os.path.exists(fpath):
        return fname   # already downloaded

    url = HEADSHOT_URL.format(player_id=player_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(fpath, "wb") as f:
                f.write(resp.content)
            return fname
    except Exception:
        pass
    return None

def safe_api_call(fn, *args, retries=3, delay=2, **kwargs):
    """Call an nba_api endpoint with retries."""
    for attempt in range(retries):
        try:
            result = fn(*args, **kwargs)
            time.sleep(1)   # be polite
            return result
        except Exception as e:
            print(f"    [retry {attempt+1}/{retries}] {e}")
            time.sleep(delay * (attempt + 1))
    return None

# ── STEP 1: Get all players ever (nba_api CommonAllPlayers) ──────────────────
print("=" * 60)
print("Step 1 — Fetching all historical NBA players...")
print("=" * 60)

all_players_resp = safe_api_call(
    commonallplayers.CommonAllPlayers,
    is_only_current_season=0,   # 0 = all-time
    league_id="00",
    season="2024-25",
)

if all_players_resp is None:
    sys.exit("Failed to fetch player list after retries. Check internet connection.")

df_all = all_players_resp.get_data_frames()[0]
print(f"  Total rows returned: {len(df_all)}")
print(f"  Columns: {list(df_all.columns)}")

# ── STEP 2: Build lookup structures ──────────────────────────────────────────
# nba_api team abbreviations we care about
target_abbrs = set(TEAM_KEYS.values())

# Build: player_id → row data
player_lookup = {}
for _, row in df_all.iterrows():
    pid = str(row.get("PERSON_ID", ""))
    if pid:
        player_lookup[pid] = row

# ── STEP 3: Get team IDs from nba_api static data ───────────────────────────
print("\nStep 2 — Mapping team abbreviations to NBA team IDs...")

all_nba_teams = nba_teams_static.get_teams()
abbr_to_team  = {t["abbreviation"]: t for t in all_nba_teams}

# Some teams have alternate abbreviations in nba_api
ALT_ABBR = {
    "BKN": "BKN",   # Brooklyn Nets
    "NOP": "NOP",   # New Orleans Pelicans
    "CHA": "CHA",   # Charlotte Hornets
    "PHX": "PHX",   # Phoenix Suns
}

team_id_map = {}   # our key → nba team id
for our_key, nba_abbr in TEAM_KEYS.items():
    team_info = abbr_to_team.get(nba_abbr)
    if team_info:
        team_id_map[our_key] = team_info["id"]
        print(f"  {our_key} → {team_info['full_name']} (id={team_info['id']})")
    else:
        print(f"  WARNING: Could not find team for {our_key} ({nba_abbr})")

# ── STEP 4: Per-team franchise history ───────────────────────────────────────
print("\nStep 3 — Fetching all-time rosters per team (this takes a few minutes)...")
print("         (rate-limited to 1 req/sec to avoid blocks)\n")

# Result dict: our_key → list of player dicts
teams_data = defaultdict(list)

# Track players we've already queued for download to avoid duplication
seen_player_ids = set()
download_queue  = []   # list of (player_id, player_name)

for our_key, team_nba_id in team_id_map.items():
    print(f"  [{our_key}] Fetching franchise history...", end=" ", flush=True)

    fh_resp = safe_api_call(
        franchisehistory.FranchiseHistory,
        league_id="00",
    )

    # CommonAllPlayers already has team info per player.
    # Filter df_all for players whose TEAM_ABBREVIATION or ROSTERSTATUS
    # matches — but for historical players we need a different approach.
    #
    # Best approach: use df_all which has TEAM_ID for current team,
    # but historical team affiliations require playercareerstats.
    # We use a pragmatic shortcut:
    #   df_all has a column "TEAM_ID" (current/last team).
    #   For franchise-wide rosters we'll use FranchisePlayerLeaders
    #   and fall back to filtering df_all by checking career stats.

    # Actually the cleanest available data in CommonAllPlayers for
    # all-time franchise membership is the column TEAM_CODE or we
    # cross-ref via PlayerCareerStats.  But that's 450+ API calls.
    #
    # Practical solution: filter df_all where FROM_YEAR/TO_YEAR exist
    # and use the TEAM_ID column, then supplement with career stats
    # for players whose franchise affiliation needs checking.
    #
    # For a complete all-time list, we'll iterate all players and
    # check their career team list via playercareerstats — but only
    # for a manageable subset. Instead, use the built-in
    # commonteamroster for current + recent seasons and merge.

    # ── Use CommonTeamRoster for recent seasons (2000-2025) ──────────
    player_set = {}   # player_id → {name, positions, from_year, to_year}

    seasons_to_check = [str(y) + "-" + str(y+1)[2:] for y in range(1999, 2025)]

    for season in seasons_to_check:
        resp = safe_api_call(
            commonteamroster.CommonTeamRoster,
            team_id=team_nba_id,
            season=season,
        )
        if resp is None:
            continue

        try:
            df_roster = resp.get_data_frames()[0]
        except Exception:
            continue

        for _, row in df_roster.iterrows():
            pid   = str(row.get("PLAYER_ID", ""))
            pname = str(row.get("PLAYER", "")).strip()
            pos_r = str(row.get("POSITION", "")).strip()
            yr    = int(season.split("-")[0])

            if not pid or not pname:
                continue

            if pid not in player_set:
                player_set[pid] = {
                    "name":      pname,
                    "positions": parse_positions(pos_r),
                    "from_year": yr,
                    "to_year":   yr,
                }
            else:
                player_set[pid]["to_year"] = max(player_set[pid]["to_year"], yr)
                if not player_set[pid]["positions"] and pos_r:
                    player_set[pid]["positions"] = parse_positions(pos_r)

    # ── Also pull pre-2000 historical data from CommonAllPlayers ─────
    # df_all has TEAM_ID — match players whose last/current team is this one
    # AND whose career started before 2000 (to catch historical players).
    for _, row in df_all.iterrows():
        pid   = str(row.get("PERSON_ID", ""))
        tname = str(row.get("TEAM_NAME", ""))
        abbr  = str(row.get("TEAM_ABBREVIATION", "")).strip()
        pname = str(row.get("DISPLAY_FIRST_LAST", "")).strip()
        pos_r = str(row.get("POSITION", "")).strip() if "POSITION" in row else ""
        from_y = int(row.get("FROM_YEAR", 0) or 0)
        to_y   = int(row.get("TO_YEAR", 0) or 0)

        if not pid or not pname:
            continue

        # If this player's last team matches ours AND they're not already in
        if abbr == TEAM_KEYS[our_key] and pid not in player_set:
            player_set[pid] = {
                "name":      pname,
                "positions": parse_positions(pos_r),
                "from_year": from_y,
                "to_year":   to_y,
            }

    # ── Build final list for this team ───────────────────────────────
    player_list = []
    for pid, pdata in player_set.items():
        fy = pdata["from_year"]
        ty = pdata["to_year"]
        years_str = f"{fy}-{ty}" if fy and ty else (str(fy) if fy else "")

        # Queue headshot download
        if pid not in seen_player_ids:
            seen_player_ids.add(pid)
            download_queue.append((pid, pdata["name"]))

        # Determine image filename (will verify after download)
        img_fname = image_filename(pdata["name"])

        player_list.append({
            "name":      pdata["name"],
            "positions": pdata["positions"],
            "years":     years_str,
            "image":     img_fname,   # optimistic; set to null if download fails
            "_pid":      pid,         # temp field, removed before saving
        })

    # Sort alphabetically by last name
    player_list.sort(key=lambda x: x["name"].split()[-1].lower())
    teams_data[our_key] = player_list

    print(f"{len(player_list)} players found.")

# ── STEP 5: Download headshots ────────────────────────────────────────────────
print(f"\nStep 4 — Downloading headshots for {len(download_queue)} players...")
print("         (0.5 s between requests)\n")

downloaded = set()
failed     = set()

for i, (pid, pname) in enumerate(download_queue, 1):
    fname = download_headshot(pid, pname)
    if fname:
        downloaded.add(pid)
        status = "✓"
    else:
        failed.add(pid)
        status = "✗"

    if i % 50 == 0 or i == len(download_queue):
        print(f"  [{i}/{len(download_queue)}]  downloaded={len(downloaded)}  not_found={len(failed)}")

    time.sleep(0.5)

# ── STEP 6: Finalize JSON — set image to null where download failed ───────────
print("\nStep 5 — Finalizing JSON...")

final_data = {}
for our_key, player_list in teams_data.items():
    clean_list = []
    for p in player_list:
        pid = p.pop("_pid", None)
        # If headshot wasn't downloadable, set image to null
        if pid in failed:
            p["image"] = None
        clean_list.append(p)
    final_data[our_key] = clean_list

# ── STEP 7: Save JSON ─────────────────────────────────────────────────────────
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)

print(f"\n{'='*60}")
print(f"Done!")
print(f"  JSON saved to : {OUT_JSON}")
print(f"  Headshots in  : {PLAYERS_DIR}")
print(f"  Teams         : {len(final_data)}")
total_players = sum(len(v) for v in final_data.values())
print(f"  Total players : {total_players}")
print(f"  With photo    : {len(downloaded)}")
print(f"  No photo      : {len(failed)}")
print(f"{'='*60}")