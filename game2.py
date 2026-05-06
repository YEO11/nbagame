import tkinter as tk
import json
import random
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


def normalize_name(name):
    """Standardizes names to avoid issues with accents and casing."""
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower().strip()

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
        # We use a set of names for O(1) lookup speed
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

        # Load data in a thread
        threading.Thread(target=self.load_all_players, daemon=True).start()

        self.start_round()

    # ---------------- Data Loading ----------------
    def load_all_players(self):
        """Loads the pre-synced high-rating player pool from the local JSON file."""
        self.status_label.config(text="Loading Local Player Pool...", fg=MUTED)

        file_path = r"data\2k_data.json"

        if not os.path.exists(file_path):
            self.status_label.config(text="Error: synced_players.json missing!", fg="red")
            print("❌ Critical Error: You need to run the sync script first.")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reset local database
            self.player_db = {}
            total_count = 0

            # Flatten the position-based JSON into a lookup dictionary
            for pos, players in data.items():
                for p in players:
                    # Use normalized name as key for fast O(1) lookup
                    key = normalize_name(p["name"])
                    self.player_db[key] = p
                    total_count += 1

            print(f"✅ Successfully loaded {total_count} players.")

            # UI Update
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
                                    bg=BG2, fg=MUTED, font=("Arial", 10))
        self.round_label.pack(side="right", padx=18)

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
    import random

    def run_simulation(self):
        # Ensure draft is complete
        user_players = [p for p in self.user_team.values() if p is not None]
        cpu_players = [p for p in self.cpu_team.values() if p is not None]

        if len(user_players) < 5 or len(cpu_players) < 5:
            print("Draft not complete!")
            return

        # Calculate team strength
        def calculate_strength(player_list, team_label):
            print(f"\n--- {team_label} Ratings ---")
            total_overall = 0
            for p in player_list:
                # Look up in the database
                data = self.player_db.get(normalize_name(p['name']), {"overall": 80})
                rating = data.get("overall", 80)

                # Print individual player rating
                print(f"{p['name']}: {rating}")

                total_overall += rating

            avg = total_overall / len(player_list)
            return avg

        # Calculate and Print
        u_pwr = calculate_strength(user_players, "USER TEAM")
        c_pwr = calculate_strength(cpu_players, "CPU TEAM")

        print("-" * 30)
        print(f"FINAL TEAM POWER -> USER: {u_pwr:.2f} | CPU: {c_pwr:.2f}")
        print("-" * 30)

        u_wins, c_wins, log = 0, 0, []

        # Best of 7 Series
        while u_wins < 4 and c_wins < 4:
            # Game Day Luck (variance)
            u_performance = u_pwr + random.uniform(-3, 3)
            c_performance = c_pwr + random.uniform(-3, 3)

            if u_performance > c_performance:
                u_wins += 1
                log.append("W")
            else:
                c_wins += 1
                log.append("L")

        self.show_results(u_wins, c_wins, log, u_pwr, c_pwr)

    def show_results(self, u, c, log, u_pwr, c_pwr):
        prob = 1 / (1 + pow(10, (c_pwr - u_pwr) / 15))
        proj_w = round(prob * 82)

        txt = f"SERIES RESULT: {u}-{c} \n82-GAME PROJECTION: {proj_w}-{82 - proj_w}"
        color = "#4BB543" if u == 4 else "#FF4B4B"

        self.after(0, lambda: self.status_label.config(text=txt, fg=color, font=("Arial Black", 14)))


if __name__ == "__main__":
    app = NBA2KSimGame()
    app.mainloop()