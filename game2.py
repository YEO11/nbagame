import tkinter as tk
import json
import random
import requests
import threading
import os
from PIL import Image, ImageTk
import unicodedata

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


def normalize_name(name):
    """Removes accents and converts to lowercase for reliable matching."""
    if not name: return ""
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()


class NBA2KSimGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NBA 2K Series Simulator")
        self.geometry("1100x850")
        self.configure(bg=BG)

        # Initialize Database
        self.player_db = {}

        with open("data/popular_players.json", 'r') as f:
            self.pool = json.load(f)

        self.user_team = {pos: None for pos in POSITIONS}
        self.cpu_team = {pos: random.choice(self.pool[pos]) for pos in POSITIONS}

        self.current_round = 1
        self.draft_options = {}
        self.is_shuffling = False

        self._build_ui()

        # Load data in a thread so the UI doesn't freeze at startup
        threading.Thread(target=self.load_all_players, daemon=True).start()

        self.start_round()

    # ---------------- Data Loading ----------------
    def load_all_players(self):
        """Fetches all players from the API using pagination."""
        self.status_label.config(text="Connecting to 2K Database...", fg=MUTED)

        all_fetched_players = []
        cursor = None

        while True:
            try:
                # Prepare parameters - only include cursor if we are on page 2+
                params = {"teamType": "allt", "limit": 100}
                if cursor:
                    params["cursor"] = cursor

                response = requests.get(
                    "https://api.nba2kapi.com/api/players",
                    params=params,
                    headers={'X-API-Key': API_KEY},
                    timeout=10  # Prevents the thread from hanging forever
                )

                # Check for HTTP errors (e.g., 401 Unauthorized, 500 Server Error)
                if response.status_code != 200:
                    print(f"HTTP Error: {response.status_code}")
                    self.status_label.config(text=f"Server Error ({response.status_code})", fg="red")
                    break

                data = response.json()

                if not data.get("success"):
                    print("API Error:", data.get("message", "Unknown error"))
                    self.status_label.config(text="API Key Error / Limit Reached", fg="red")
                    break

                # Extract data
                batch = data.get("data", [])
                all_fetched_players.extend(batch)

                # UI Update: Show progress to the user
                self.status_label.config(
                    text=f"Downloading Database... ({len(all_fetched_players)} players)",
                    fg=MUTED
                )

                # Pagination Logic: Check if there's a next page
                pagination = data.get("pagination", {})
                if not pagination.get("hasMore") or not pagination.get("nextCursor"):
                    break

                cursor = pagination.get("nextCursor")

            except requests.exceptions.RequestException as e:
                print(f"Connection Error: {e}")
                self.status_label.config(text="Connection Lost. Check Internet.", fg="red")
                return

        # Map list to local dictionary for O(1) fast lookup during simulation
        for p in all_fetched_players:
            key = normalize_name(p["name"])
            self.player_db[key] = p

        print(f"Successfully loaded {len(self.player_db)} players.")

        # Final UI Update
        self.status_label.config(text="Database Ready. Start Drafting!", fg=ACCENT)

    # ---------------- UI ----------------
    def _build_ui(self):
        top = tk.Frame(self, bg=BG2, height=60)
        top.pack(fill="x")

        tk.Label(top, text="NBA 2K SERIES SIMULATOR",
                 bg=BG2, fg=ACCENT, font=("Arial Black", 16)).pack(side="left", padx=20)

        self.round_label = tk.Label(top, text=f"ROUND {self.current_round}/5",
                                    bg=BG2, fg=TEXT, font=("Arial", 12, "bold"))
        self.round_label.pack(side="right", padx=20)

        # CPU
        tk.Label(self, text="OPPONENT TEAM", bg=BG, fg="red",
                 font=("Arial", 11, "bold")).pack(pady=10)

        self.cpu_frame = tk.Frame(self, bg=BG)
        self.cpu_frame.pack()
        self.render_team(self.cpu_team, self.cpu_frame, is_cpu=True)

        tk.Frame(self, bg=BG3, height=2).pack(fill="x", padx=100, pady=20)

        # USER
        tk.Label(self, text="YOUR DRAFT", bg=BG, fg=ACCENT,
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
        if self.is_shuffling: return
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
    def scoring(self, s):
        return (s.get('closeShot', 70) * 0.10 + s.get('layup', 70) * 0.10 +
                s.get('drivingDunk', 70) * 0.10 + s.get('midRangeShot', 70) * 0.15 +
                s.get('threePointShot', 70) * 0.20 + s.get('freeThrow', 70) * 0.05 +
                s.get('shotIQ', 70) * 0.15 + s.get('offensiveConsistency', 70) * 0.15)

    def playmaking(self, s):
        return (s.get('ballHandle', 70) * 0.30 + s.get('passAccuracy', 70) * 0.25 +
                s.get('passIQ', 70) * 0.25 + s.get('passVision', 70) * 0.10 +
                s.get('speedWithBall', 70) * 0.10)

    def defense(self, s):
        return (s.get('perimeterDefense', 70) * 0.25 + s.get('interiorDefense', 70) * 0.20 +
                s.get('steal', 70) * 0.15 + s.get('block', 70) * 0.15 +
                s.get('helpDefenseIQ', 70) * 0.15 + s.get('defensiveConsistency', 70) * 0.10)

    def athleticism(self, s):
        return (s.get('speed', 70) * 0.25 + s.get('agility', 70) * 0.20 +
                s.get('vertical', 70) * 0.15 + s.get('strength', 70) * 0.15 +
                s.get('stamina', 70) * 0.25)

    def player_impact(self, s, position):
        base = (self.scoring(s) * 0.35 + self.playmaking(s) * 0.20 +
                self.defense(s) * 0.20 + self.athleticism(s) * 0.15 +
                (s.get('intangibles', 70) * 0.10))

        if position == "PG":
            base += self.playmaking(s) * 0.10
        elif position == "SG":
            base += self.scoring(s) * 0.05
        elif position in ["PF", "C"]:
            base += self.defense(s) * 0.08
        return base

    def simulate_team(self, team_dict, stats_list):
        total = 0
        for (pos, player), s in zip(team_dict.items(), stats_list):
            impact = self.player_impact(s, pos)
            consistency = s.get('offensiveConsistency', 70) / 100
            variance = random.gauss(0, 5 * (1 - consistency))
            total += impact + variance
        return total

    # ---------- SIMULATION ----------
    # Ensure this is aligned with your other "def" statements inside the class
    def fetch_player_data(self, name):
        """Instant local lookup."""
        normalized = normalize_name(name)
        player = self.player_db.get(normalized)

        if player:
            return player

        print(f"Match not found for: {name}")
        # Default fallback stats
        return {"overall": 80, "offensiveConsistency": 75, "threePointShot": 75}

    def run_simulation(self):
        # Safety Check: Filter out None values in case the simulation
        # is triggered before the draft is 100% full.
        user_players = [p for p in self.user_team.values() if p is not None]
        cpu_players = [p for p in self.cpu_team.values() if p is not None]

        if len(user_players) < 5:
            print("Draft not complete!")
            return

        # Now we fetch the data from our loaded dictionary
        user_stats = [self.fetch_player_data(p['name']) for p in user_players]
        cpu_stats = [self.fetch_player_data(p['name']) for p in cpu_players]

        def get_team_power(team, stats, samples=20):
            # Pass the actual team dict keys (positions) to the impact calculator
            return sum(self.simulate_team(team, stats) for _ in range(samples)) / samples

        u_pwr = get_team_power(self.user_team, user_stats)
        c_pwr = get_team_power(self.cpu_team, cpu_stats)

        u_wins, c_wins, log = 0, 0, []
        while u_wins < 4 and c_wins < 4:
            u_s = self.simulate_team(self.user_team, user_stats)
            c_s = self.simulate_team(self.cpu_team, cpu_stats)
            if u_s > c_s:
                u_wins += 1
                log.append("W")
            else:
                c_wins += 1
                log.append("L")

        self.show_results(u_wins, c_wins, log, u_pwr, c_pwr)

    def show_results(self, u, c, log, u_pwr, c_pwr):
        prob = 1 / (1 + pow(10, (c_pwr - u_pwr) / 15))  # Adjusted Elo-style constant
        proj_w = round(prob * 82)

        txt = f"SERIES RESULT: {u}-{c} | {' '.join(log)}\n82-GAME PROJECTION: {proj_w}-{82 - proj_w}"
        color = "#4BB543" if u == 4 else "#FF4B4B"

        self.after(0, lambda: self.status_label.config(text=txt, fg=color, font=("Arial Black", 14)))


if __name__ == "__main__":
    app = NBA2KSimGame()
    app.mainloop()