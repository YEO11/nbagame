"""
merge_json.py
=============
Merges two teams_players.json files into one, saved to data/teams_players.json.

Sources:
  A  →  <project root>/teams_players.json        (original, 76 teams)
  B  →  <project root>/data/teams_players.json   (nba_api rebuilt, 30 teams)

Merge rules (per team, per player):
  - Players matched by name (case-insensitive, stripped).
  - image   : prefer non-null; if both non-null, prefer B (newer download).
  - years   : take the widest range (earliest from_year – latest to_year).
  - positions: union of both lists, preserving order (B first, then A extras).
  - name    : prefer B's casing (cleaner from nba_api).

Result is saved to:
  <project root>/data/teams_players.json   (overwrites B)
A backup of B is written first to:
  <project root>/data/teams_players_backup.json
"""

import json
import os
import shutil

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR  = r"C:\Users\백승열\Desktop\NBA_DRAFT_GAME"
PATH_A    = os.path.join(BASE_DIR, "teams_players.json")          # root copy
PATH_B    = os.path.join(BASE_DIR, "data", "teams_players.json")  # data/ copy  ← output goes here
PATH_BAK  = os.path.join(BASE_DIR, "data", "teams_players_backup.json")

# ── LOAD ──────────────────────────────────────────────────────────────────────
print("Loading files...")

with open(PATH_A, "r", encoding="utf-8") as f:
    data_a = json.load(f)

with open(PATH_B, "r", encoding="utf-8") as f:
    data_b = json.load(f)

print(f"  File A (root)  : {len(data_a)} teams, "
      f"{sum(len(v) for v in data_a.values())} players")
print(f"  File B (data/) : {len(data_b)} teams, "
      f"{sum(len(v) for v in data_b.values())} players")

# ── BACKUP B ──────────────────────────────────────────────────────────────────
shutil.copy2(PATH_B, PATH_BAK)
print(f"\nBackup saved → {PATH_BAK}")

# ── HELPER: parse year range ───────────────────────────────────────────────────
def parse_years(years_str):
    """'1990-1994' → (1990, 1994).  Returns (None, None) if unparseable."""
    if not years_str:
        return None, None
    parts = str(years_str).split("-")
    try:
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        if len(parts) == 1:
            y = int(parts[0])
            return y, y
    except ValueError:
        pass
    return None, None

def merge_years(y_a, y_b):
    """Return the widest year range string from two year strings."""
    fa, ta = parse_years(y_a)
    fb, tb = parse_years(y_b)

    froms = [x for x in [fa, fb] if x is not None]
    tos   = [x for x in [ta, tb] if x is not None]

    if not froms:
        return ""
    f = min(froms)
    t = max(tos) if tos else f
    return f"{f}-{t}"

def merge_positions(pos_b, pos_a):
    """Union of positions: B first, then any from A not already present."""
    seen   = set(p.lower() for p in pos_b)
    result = list(pos_b)
    for p in pos_a:
        if p.lower() not in seen:
            result.append(p)
            seen.add(p.lower())
    return result

def merge_player(p_b, p_a):
    """Merge two player dicts (same person). B is the 'newer' source."""
    name  = p_b["name"] or p_a["name"]

    # image: prefer non-null; if both non-null prefer B
    img_b = p_b.get("image")
    img_a = p_a.get("image")
    if img_b:
        image = img_b
    elif img_a:
        image = img_a
    else:
        image = None

    years = merge_years(p_b.get("years", ""), p_a.get("years", ""))
    positions = merge_positions(
        p_b.get("positions") or [],
        p_a.get("positions") or [],
    )

    return {
        "name":      name,
        "positions": positions,
        "years":     years,
        "image":     image,
    }

# ── MERGE ─────────────────────────────────────────────────────────────────────
print("\nMerging...")

merged = {}

# Collect all team keys from both files
all_keys = sorted(set(list(data_a.keys()) + list(data_b.keys())))

stats = {"teams": 0, "added_from_a": 0, "added_from_b": 0, "merged": 0}

for key in all_keys:
    players_a = data_a.get(key, [])
    players_b = data_b.get(key, [])

    # Build lookup by lowercase name for fast dedup
    # Start with B as the base (preferred source)
    by_name = {}   # lower_name → player dict

    for p in players_b:
        k = p["name"].strip().lower()
        by_name[k] = dict(p)   # copy
        stats["added_from_b"] += 1

    for p in players_a:
        k = p["name"].strip().lower()
        if k in by_name:
            # Merge the two records
            by_name[k] = merge_player(by_name[k], p)
            stats["merged"] += 1
            stats["added_from_b"] -= 1   # was counted above; don't double count
        else:
            by_name[k] = dict(p)
            stats["added_from_a"] += 1

    # Sort alphabetically by last name (then first name as tiebreak)
    def sort_key(player):
        parts = player["name"].strip().split()
        last  = parts[-1].lower() if parts else ""
        first = parts[0].lower()  if len(parts) > 1 else ""
        return (last, first)

    final_list = sorted(by_name.values(), key=sort_key)
    merged[key] = final_list
    stats["teams"] += 1

total_players = sum(len(v) for v in merged.values())

# ── SAVE ──────────────────────────────────────────────────────────────────────
with open(PATH_B, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=4)

print(f"\n{'='*55}")
print(f"  Saved → {PATH_B}")
print(f"  Teams         : {stats['teams']}")
print(f"  Total players : {total_players}")
print(f"  From A only   : {stats['added_from_a']}")
print(f"  From B only   : {stats['added_from_b']}")
print(f"  Merged (both) : {stats['merged']}")
print(f"{'='*55}")
print("Done!")