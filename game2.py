import tkinter as tk
import json
import threading
import os
from PIL import Image, ImageTk
import unicodedata
import random

# --- CONFIG ---
API_KEY = "2k_yq440mfukup3lmaxovd2cqdvf0xzy2z0"
POSITIONS = ["PG", "SG", "SF", "PF", "C"]

# STYLE
BG = "#0A0F1E"
BG2 = "#111827"
BG3 = "#1A2540"
ACCENT = "#F5A623"
TEXT = "#E8EAF0"
MUTED = "#6B7FA8"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_IMG_DIR = os.path.join(BASE_DIR, "data", "players")


class NBA2KSimGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NBA 2K Series Simulator")
        self.geometry("1100x850")
        self.configure(bg=BG)

        # 1. Load the full pool
        with open("data/popular_players.json", 'r') as f:
            full_pool = json.load(f)

        # 2. Pick CPU Team first
        self.cpu_team = {pos: random.choice(full_pool[pos]) for pos in POSITIONS}

        # 3. Create a Filtered Pool for the User (Excludes CPU players)
        cpu_player_names = {p['name'] for p in self.cpu_team.values()}

        self.pool = {}
        for pos in POSITIONS:
            self.pool[pos] = [p for p in full_pool[pos] if p['name'] not in cpu_player_names]

        # Initialize User variables
        self.player_db = {}
        self.user_team = {pos: None for pos in POSITIONS}
        self.current_round = 1
        self.draft_options = {}
        self.is_shuffling = False

        self._build_ui()

        # FIX 4: Load icon before starting background thread
        try:
            self.icon_img = tk.PhotoImage(file="logo.png")
            self.iconphoto(False, self.icon_img)
        except Exception:
            pass  # Skip icon if file missing

        # Load data in a thread
        threading.Thread(target=self.load_all_players, daemon=True).start()

        self.start_round()

    def normalize_name(self, name):
        """Standardizes names to avoid issues with accents and casing."""
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower().strip()

    # ---------------- Data Loading ----------------
    def load_all_players(self):
        """Loads the pre-synced high-rating player pool from the local JSON file."""
        self.status_label.config(text="Loading Local Player Pool...", fg=MUTED)

        file_path = r"data\2k_data.json"

        if not os.path.exists(file_path):
            self.status_label.config(text="Error: 2k_data.json missing!", fg="red")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.player_db = {}
            total_count = 0

            for pos, players in data.items():
                for p in players:
                    # FIX 1: Use self.normalize_name (instance method)
                    key = self.normalize_name(p["name"])
                    self.player_db[key] = p
                    total_count += 1

            self.status_label.config(
                text=f"Database Ready: {total_count} Players Loaded",
                fg=ACCENT
            )

        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            self.status_label.config(text="Database Corrupted", fg="red")

    # ---------------- UI ----------------
    def _build_ui(self):
        top = tk.Frame(self, bg=BG2, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="\U0001f3c0  NBA 2K Series Simulator",
                 bg=BG2, fg=ACCENT, font=("Arial Black", 13, "bold")).pack(side="left", padx=18, pady=12)

        self.round_label = tk.Label(top, text=f"ROUND {self.current_round}/5",
                                    bg=BG2, fg=MUTED, font=("Arial", 9))
        self.round_label.pack(side="right", padx=18)

        # CPU
        tk.Label(self, text="OPPONENT TEAM", bg=BG, fg="red",
                 font=("Arial", 11, "bold")).pack(pady=10)

        self.cpu_frame = tk.Frame(self, bg=BG)
        self.cpu_frame.pack()
        self.render_team(self.cpu_team, self.cpu_frame, is_cpu=True)

        tk.Frame(self, bg=BG3, height=2).pack(fill="x", padx=100, pady=20)

        # USER
        tk.Label(self, text="YOUR TEAM", bg=BG, fg=ACCENT,
                 font=("Arial", 12, "bold")).pack()

        self.user_frame = tk.Frame(self, bg=BG)
        self.user_frame.pack()

        # STATUS
        self.status_box = tk.Frame(self, bg=BG2, height=120)
        self.status_box.pack(fill="x", side="bottom", padx=20, pady=20)

        self.status_label = tk.Label(self.status_box,
                                     text="Initializing...",
                                     bg=BG2, fg=TEXT, font=("Arial", 14))
        self.status_label.pack(expand=True)

    # ---------------- IMAGE LOADING ----------------
    def get_player_image(self, player):
        filename = player.get("image")
        path = os.path.join(PLAYER_IMG_DIR, filename) if filename else ""

        if path and os.path.exists(path):
            img = Image.open(path).resize((180, 135), Image.LANCZOS)
        else:
            img = Image.new('RGBA', (1000, 750), (26, 37, 64, 255))

        return ImageTk.PhotoImage(img)

    # ---------------- RENDER ----------------
    def render_team(self, team_dict, frame, is_cpu=False):
        for w in frame.winfo_children():
            w.destroy()

        for pos in POSITIONS:
            player = team_dict.get(pos)
            slot = tk.Frame(frame, bg=BG2, width=200, height=260,
                            highlightthickness=1, highlightbackground=BG3)
            slot.pack_propagate(False)
            slot.pack(side="left", padx=10)

            tk.Label(slot, text=pos, fg="red" if is_cpu else ACCENT,
                     bg=BG2, font=("Arial Black", 10)).pack(pady=5)

            if player:
                img = self.get_player_image(player)
                img_lbl = tk.Label(slot, image=img, bg=BG2)
                img_lbl.image = img
                img_lbl.pack(pady=5)

                tk.Label(slot, text=player['name'].upper(),
                         fg=TEXT, bg=BG2, wraplength=150,
                         font=("Arial", 9, "bold")).pack()

                if not is_cpu and self.user_team[pos] is None:
                    tk.Button(slot, text="SELECT", bg=ACCENT, fg="black",
                              command=lambda p=pos, pl=player: self.select_player(p, pl)
                              ).pack(fill="x", padx=10, pady=5)
            else:
                tk.Label(slot, text="?", fg=BG3, bg=BG2, font=("Arial Black", 40)).pack(expand=True)

    # ---------------- GAME FLOW ----------------
    def start_round(self):
        self.round_label.config(text=f"ROUND {self.current_round}/5")
        self.is_shuffling = True
        self._shuffle_animation(0)

    def _shuffle_animation(self, count):
        if count < 18:
            for pos in POSITIONS:
                if self.user_team[pos] is None:
                    self.draft_options[pos] = random.choice(self.pool[pos])
                else:
                    self.draft_options[pos] = self.user_team[pos]
            self.render_team(self.draft_options, self.user_frame)
            self.after(40 + count * 6, lambda: self._shuffle_animation(count + 1))
        else:
            self.is_shuffling = False
            self.status_label.config(text="Select your player!", fg=TEXT)

    def select_player(self, pos, player):
        if self.is_shuffling:
            return
        self.user_team[pos] = player
        self.current_round += 1
        self.render_team(self.user_team, self.user_frame)
        if self.current_round <= 5:
            self.start_round()
        else:
            self.finalize_draft()

    def finalize_draft(self):
        self.status_label.config(text="Draft Complete! Simulating series...", fg=ACCENT)
        threading.Thread(target=self.run_simulation).start()

    # ---------- ATTRIBUTE MODELS ----------
    SCORING_ATTRS = ['closeShot', 'midRangeShot', 'threePointShot', 'drivingLayup', 'drivingDunk', 'postFade',
                     'postHook']
    PLAYMAKING_ATTRS = ['passAccuracy', 'passIQ', 'passVision', 'ballHandle', 'speedWithBall']
    DEFENSE_ATTRS = ['perimeterDefense', 'interiorDefense', 'helpDefenseIQ', 'steal', 'block', 'passPerception']
    PHYSICAL_ATTRS = ['speed', 'agility', 'strength', 'vertical', 'stamina', 'hustle']
    REBOUND_ATTRS = ['offensiveRebound', 'defensiveRebound']

    POSITION_WEIGHTS = {
        "PG": {"playmaking": 0.45, "scoring": 0.10, "defense": 0.15, "rebound": 0.10},
        "SG": {"playmaking": 0.20, "scoring": 0.30, "defense": 0.15, "rebound": 0.10},
        "SF": {"playmaking": 0.20, "scoring": 0.25, "defense": 0.20, "rebound": 0.20},
        "PF": {"playmaking": 0.10, "scoring": 0.15, "defense": 0.25, "rebound": 0.20},
        "C": {"playmaking": 0.05, "scoring": 0.20, "defense": 0.25, "rebound": 0.40}
    }

    def get_weight(self, attr_name, position):
        weights = self.POSITION_WEIGHTS.get(position, {})

        if attr_name in self.SCORING_ATTRS:
            return weights.get("scoring", 0.2)
        if attr_name in self.PLAYMAKING_ATTRS:
            return weights.get("playmaking", 0.2)
        if attr_name in self.DEFENSE_ATTRS:
            return weights.get("defense", 0.2)
        if attr_name in self.REBOUND_ATTRS:
            return weights.get("rebound", 0.2)
        return 0.2

    def calculate_team_synergy(self, team_list):
        """Calculates the 'Super Attribute' map for the entire team."""
        team_attributes = {}

        for p in team_list:
            name_key = self.normalize_name(p['name'])
            player_data = self.player_db.get(name_key, {})
            attrs = player_data.get("attributes", {})
            ovr_factor = player_data.get("overall", 80) / 100.0
            pos = p.get('position', 'SF')

            for attr_name, value in attrs.items():
                weight = self.get_weight(attr_name, pos)
                contribution = value * ovr_factor * weight
                team_attributes[attr_name] = team_attributes.get(attr_name, 0) + contribution

        return team_attributes

    def run_simulation(self):
        user_players = [p for p in self.user_team.values() if p is not None]
        cpu_players = [p for p in self.cpu_team.values() if p is not None]

        if len(user_players) < 5 or len(cpu_players) < 5:
            return

        u_team_map = self.calculate_team_synergy(user_players)
        c_team_map = self.calculate_team_synergy(cpu_players)

        u_rating = sum(u_team_map.values()) / len(u_team_map) if u_team_map else 0
        c_rating = sum(c_team_map.values()) / len(c_team_map) if c_team_map else 0

        print(f"🔵 User Team Rating:  {u_rating:.2f}")
        print(f"🔴 CPU  Team Rating:  {c_rating:.2f}")
        print(
            f"📊 Avg Difference:    {u_rating - c_rating:.2f} ({'User advantage' if u_rating > c_rating else 'CPU advantage'})")

        differences = []
        all_keys = set(u_team_map.keys()) | set(c_team_map.keys())

        print("\n Attribute Difference Map (User - CPU):")
        for attr in sorted(all_keys):
            u_val = u_team_map.get(attr, 0)
            c_val = c_team_map.get(attr, 0)
            diff = u_val - c_val
            arrow = "🔵" if diff >= 0 else "🔴"
            print(f"  {arrow} {attr:<25} U: {u_val:>6.2f}  C: {c_val:>6.2f}  Δ: {diff:>+7.2f}")

        for attr in all_keys:
            u_val = u_team_map.get(attr, 0)
            c_val = c_team_map.get(attr, 0)
            differences.append(u_val - c_val)

        avg_diff = sum(differences) / len(differences) if differences else 0

        u_wins, c_wins, log = 0, 0, []

        win_chance = (u_rating / c_rating) * 0.5
        win_chance = max(0.2, min(0.8, win_chance))

        print(win_chance)

        while u_wins < 40 and c_wins < 40:
            if random.random() < win_chance:
                u_wins += 1
                if u_wins > 0 and u_wins % 10 == 0:
                    log.append("W")
            else:
                c_wins += 1
                if c_wins > 0 and c_wins % 10 == 0:
                    log.append("L")

        # FIX 3: Pass avg_diff as both u_pwr and use it to derive c_pwr (0 baseline)
        self.show_results(u_wins//10, c_wins//10, log, u_rating)

    # FIX 3: Corrected signature — avg_diff encodes the user advantage over CPU
    def show_results(self, u, c, log, u_pwr):
        # avg_diff > 0 means user is stronger; treat CPU power as 0 baseline

        prob = u_pwr/100 * 1.1875
        proj_w = round(41 + prob*41)

        print(f"🏆 Win rate: {prob}" )

        result_str = " - ".join(log)
        txt = f"SERIES RESULT: {u}-{c}  [{result_str}]\n82-GAME PROJECTION: {proj_w}-{82 - proj_w}"
        color = "#4BB543" if u == 4 else "#FF4B4B"

        self.after(0, lambda: self.status_label.config(text=txt, fg=color, font=("Arial Black", 14)))


if __name__ == "__main__":
    app = NBA2KSimGame()
    app.mainloop()