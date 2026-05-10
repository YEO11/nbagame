import tkinter as tk
import json
import threading
import os
from PIL import Image, ImageTk
import unicodedata
import random
import math

# --- CONFIG ---
POSITIONS = ["PG", "SG", "SF", "PF", "C"]

# STYLE  (identical palette to NBA Draft Game)
BG     = "#0A0F1E"
BG2    = "#111827"
BG3    = "#1A2540"
ACCENT = "#F5A623"
TEXT   = "#E8EAF0"
MUTED  = "#6B7FA8"
DANGER = "#E24B4A"
RED    = "#E24B4A"

SLOT_W = 175
SLOT_H = 270

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PLAYER_IMG_DIR = os.path.join(BASE_DIR, "data", "players")


# ── tiny helpers ──────────────────────────────────────────────────────────────
def _sep(parent, color="#2A3A5A", h=1, px=0, py=0):
    tk.Frame(parent, bg=color, height=h).pack(fill="x", padx=px, pady=py)


class NBA2KSimGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NBA 2K Series Simulator")
        self.geometry("1100x850")
        self.resizable(False, False)
        self.configure(bg=BG)

        # 1. Load the full pool
        with open("data/database/popular_players.json", 'r') as f:
            full_pool = json.load(f)

        # 2. Pick CPU Team first
        self.cpu_team = {pos: random.choice(full_pool[pos]) for pos in POSITIONS}

        # 3. Create a Filtered Pool for the User (Excludes CPU players)
        cpu_player_names = {p['name'] for p in self.cpu_team.values()}

        self.pool = {}
        for pos in POSITIONS:
            self.pool[pos] = [p for p in full_pool[pos] if p['name'] not in cpu_player_names]

        # Initialize User variables
        self.player_db    = {}
        self.user_team    = {pos: None for pos in POSITIONS}
        self.current_round = 1
        self.draft_options = {}
        self.is_shuffling  = False

        # image cache so PhotoImage objects stay alive
        self._img_cache = {}

        self._build_ui()

        try:
            self.icon_img = tk.PhotoImage(file="misc/logo.png")
            self.iconphoto(False, self.icon_img)
        except Exception:
            pass

        threading.Thread(target=self.load_all_players, daemon=True).start()
        self.start_round()

    def normalize_name(self, name):
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower().strip()

    # ── Data Loading ──────────────────────────────────────────────────────────
    def load_all_players(self):
        file_path = r"data/database/2k_data.json"

        if not os.path.exists(file_path):
            self._set_status("Error: 2k_data.json missing!", DANGER)
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.player_db  = {}
            total_count = 0

            for pos, players in data.items():
                for p in players:
                    key = self.normalize_name(p["name"])
                    self.player_db[key] = p
                    total_count += 1

        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            self._set_status("Database corrupted", DANGER)

    # ── UI Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── TOP BAR ──
        topbar = tk.Frame(self, bg=BG2, height=50)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="\U0001f3c0  NBA 2K Series Simulator",
                 bg=BG2, fg=ACCENT,
                 font=("Arial Black", 13, "bold")).pack(side="left", padx=18, pady=12)

        self.round_label = tk.Label(topbar, text="ROUND 1 / 5",
                                    bg=BG2, fg=MUTED, font=("Arial", 10))
        self.round_label.pack(side="right", padx=18)

        # ── round progress dots ──
        self.dots_frame = tk.Frame(self, bg=BG)
        self.dots_frame.pack(anchor="w", padx=18, pady=(10, 0))
        self.dot_labels = []
        for _ in range(5):
            d = tk.Label(self.dots_frame, text="\u25cf", bg=BG,
                         fg=BG3, font=("Arial", 10))
            d.pack(side="left", padx=3)
            self.dot_labels.append(d)

        # ── CPU SECTION ──
        cpu_hdr = tk.Frame(self, bg=BG)
        cpu_hdr.pack(fill="x", padx=18, pady=(10, 4))
        tk.Label(cpu_hdr, text="OPPONENT TEAM", bg=BG, fg=DANGER,
                 font=("Arial", 8, "bold")).pack(side="left")
        tk.Label(cpu_hdr, text="\u25cf  CPU", bg=BG, fg=DANGER,
                 font=("Arial", 8)).pack(side="right")

        self.cpu_frame = tk.Frame(self, bg=BG)
        self.cpu_frame.pack(padx=18)
        self.render_team(self.cpu_team, self.cpu_frame, is_cpu=True)

        # ── DIVIDER ──
        _sep(self, "#2A3A5A", h=1, px=60, py=12)

        # ── USER SECTION ──
        user_hdr = tk.Frame(self, bg=BG)
        user_hdr.pack(fill="x", padx=18, pady=(0, 4))
        tk.Label(user_hdr, text="YOUR TEAM", bg=BG, fg=ACCENT,
                 font=("Arial", 8, "bold")).pack(side="left")
        self.pick_hint = tk.Label(user_hdr, text="\u25cf  Picking…", bg=BG,
                                  fg=ACCENT, font=("Arial", 8))
        self.pick_hint.pack(side="right")

        self.user_frame = tk.Frame(self, bg=BG)
        self.user_frame.pack(padx=18)

        # ── STATUS BOX ──
        status_outer = tk.Frame(self, bg=BG2)
        status_outer.pack(fill="x", side="bottom", padx=20, pady=20)

        _sep(status_outer, "#2A3A5A")

        inner = tk.Frame(status_outer, bg=BG2)
        inner.pack(fill="x", padx=18, pady=14)

        self.status_icon = tk.Label(inner, text="\u23f3", bg=BG2,
                                    fg=MUTED, font=("Arial", 16))
        self.status_icon.pack(side="left", padx=(0, 12))

        txt_col = tk.Frame(inner, bg=BG2)
        txt_col.pack(side="left", fill="x", expand=True)

        self.status_label = tk.Label(txt_col, text="Initializing…",
                                     bg=BG2, fg=TEXT,
                                     font=("Arial Black", 12, "bold"),
                                     anchor="w")
        self.status_label.pack(anchor="w")

        self.status_sub = tk.Label(txt_col, text="",
                                   bg=BG2, fg=MUTED,
                                   font=("Arial", 9), anchor="w")
        self.status_sub.pack(anchor="w")

    # ── Image Loading ─────────────────────────────────────────────────────────
    def get_player_image(self, player, size=(SLOT_W - 10, 130)):
        filename = player.get("image")
        path = os.path.join(PLAYER_IMG_DIR, filename) if filename else ""
        cache_key = (path, size)

        if cache_key in self._img_cache:
            return self._img_cache[cache_key]

        if path and os.path.exists(path):
            img = Image.open(path).resize(size, Image.LANCZOS)
        else:
            # placeholder: dark panel with team initial
            img = Image.new('RGBA', size, (26, 37, 64, 255))

        photo = ImageTk.PhotoImage(img)
        self._img_cache[cache_key] = photo
        return photo

    # ── Render ────────────────────────────────────────────────────────────────
    def render_team(self, team_dict, frame, is_cpu=False):
        for w in frame.winfo_children():
            w.destroy()

        pos_color = DANGER if is_cpu else ACCENT
        card_hl   = DANGER if is_cpu else "#2A3A5A"

        for pos in POSITIONS:
            player = team_dict.get(pos)

            # ── outer card shell (fixed size, no propagation) ──
            slot = tk.Frame(frame, bg=BG2, width=SLOT_W, height=SLOT_H,
                            highlightthickness=1,
                            highlightbackground=card_hl)
            slot.pack_propagate(False)
            slot.pack(side="left", padx=6, pady=4)

            # ── position badge — centered across full card width ──
            tk.Label(slot, text=pos, fg=pos_color, bg=BG2,
                     font=("Courier", 9, "bold"),
                     anchor="center").pack(fill="x", pady=(8, 4))

            # separator
            _sep(slot, "#2A3A5A")

            if player:
                # ── vertically centered content area ──
                # A mid-frame that expands to fill leftover height and
                # centres its children along the Y axis.
                mid = tk.Frame(slot, bg=BG2)
                mid.pack(fill="both", expand=True)

                # spacer top
                tk.Frame(mid, bg=BG2).pack(expand=True)

                # player image — centered horizontally via anchor="center"
                img = self.get_player_image(player)
                img_lbl = tk.Label(mid, image=img, bg=BG2, bd=0, anchor="center")
                img_lbl.image = img
                img_lbl.pack(pady=(0, 6))

                # player name
                tk.Label(mid, text=player['name'].upper(),
                         fg=TEXT, bg=BG2,
                         wraplength=SLOT_W - 20,
                         font=("Arial Black", 8),
                         justify="center",
                         anchor="center").pack(fill="x", padx=8)

                # spacer bottom
                tk.Frame(mid, bg=BG2).pack(expand=True)

                # ── bottom action row (always fixed height so card doesn't shift) ──
                bottom = tk.Frame(slot, bg=BG2, height=36)
                bottom.pack(fill="x", padx=10, pady=(0, 8))
                bottom.pack_propagate(False)

                if not is_cpu and self.user_team[pos] is None:
                    if not self.is_shuffling:
                        # Shuffle is over — show SELECT
                        btn = tk.Button(
                            bottom, text="SELECT",
                            bg=ACCENT, fg="#000000",
                            font=("Arial Black", 9, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            activebackground="#FFC142",
                            activeforeground="#000000",
                            command=lambda p=pos, pl=player: self.select_player(p, pl)
                        )
                        btn.place(relx=0, rely=0, relwidth=1, relheight=1)
                    # else: during shuffle — bottom row stays empty (no button)

                elif not is_cpu and self.user_team[pos] is not None:
                    tk.Label(bottom, text="\u2713  LOCKED",
                             fg="#2A3A5A", bg=BG2,
                             font=("Arial", 8, "bold"),
                             anchor="center").place(relx=0, rely=0, relwidth=1, relheight=1)

            else:
                # empty slot — big "?" centred
                tk.Label(slot, text="?", fg="#2A3A5A", bg=BG2,
                         font=("Arial Black", 42),
                         anchor="center").pack(fill="both", expand=True)

    # ── Game Flow ─────────────────────────────────────────────────────────────
    def start_round(self):
        self.round_label.config(text=f"ROUND {self.current_round} / 5")
        self._update_dots()
        self.pick_hint.config(text="\u25cf  Picking…", fg=ACCENT)
        self.is_shuffling = True
        self._set_status("Shuffling options…", MUTED, icon="\U0001f504",
                         sub="Get ready...")
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
            # Re-render once more now that is_shuffling=False so SELECT buttons appear.
            self.render_team(self.draft_options, self.user_frame)
            self._set_status("Select your player!", TEXT, icon="\U0001f3c0",
                             sub="Tap SELECT on the position you want to fill.")

    def select_player(self, pos, player):
        if self.is_shuffling:
            return
        self.user_team[pos] = player
        self.current_round  += 1
        self.render_team(self.user_team, self.user_frame)
        if self.current_round <= 5:
            self.start_round()
        else:
            self.finalize_draft()

    def finalize_draft(self):
        self.pick_hint.config(text="\u2713  Draft complete", fg=ACCENT)
        self._set_status("Draft complete  ·  Simulating series…",
                         ACCENT, icon="\U0001f4ca",
                         sub="Crunching attributes and synergy ratings…")
        threading.Thread(target=self.run_simulation).start()

    # ── Attribute Models ──────────────────────────────────────────────────────
    SCORING_ATTRS = [
        'closeShot', 'midRangeShot', 'threePointShot', 'drivingLayup',
        'drivingDunk', 'standingDunk', 'postFade', 'postHook',
        'postControl', 'freeThrow', 'drawFoul', 'shotIQ', 'offensiveConsistency'
    ]
    PLAYMAKING_ATTRS = [
        'passAccuracy', 'passIQ', 'passVision',
        'ballHandle', 'speedWithBall', 'hands'
    ]
    DEFENSE_ATTRS = [
        'perimeterDefense', 'interiorDefense', 'helpDefenseIQ',
        'defensiveConsistency', 'steal', 'block', 'passPerception'
    ]
    PHYSICAL_ATTRS = [
        'speed', 'agility', 'strength', 'vertical', 'stamina', 'hustle', 'durability'
    ]
    REBOUND_ATTRS  = ['offensiveRebound', 'defensiveRebound']
    IQ_ATTRS       = [
        'shotIQ', 'passIQ', 'helpDefenseIQ',
        'offensiveConsistency', 'defensiveConsistency'
    ]

    POSITION_WEIGHTS = {
        "PG": {"playmaking": 0.40, "scoring": 0.22, "defense": 0.14, "rebound": 0.03, "iq": 0.30},
        "SG": {"playmaking": 0.22, "scoring": 0.30, "defense": 0.18, "rebound": 0.07, "iq": 0.17},
        "SF": {"playmaking": 0.18, "scoring": 0.24, "defense": 0.22, "rebound": 0.18, "iq": 0.20},
        "PF": {"playmaking": 0.12, "scoring": 0.14, "defense": 0.22, "rebound": 0.30, "iq": 0.15},
        "C":  {"playmaking": 0.08, "scoring": 0.10, "defense": 0.24, "rebound": 0.42, "iq": 0.18},
    }

    def get_weight(self, attr_name, position):
        weights = self.POSITION_WEIGHTS.get(position, {})
        if attr_name in self.SCORING_ATTRS:    return weights.get("scoring",    0.2)
        if attr_name in self.PLAYMAKING_ATTRS: return weights.get("playmaking", 0.2)
        if attr_name in self.DEFENSE_ATTRS:    return weights.get("defense",    0.2)
        if attr_name in self.REBOUND_ATTRS:    return weights.get("rebound",    0.2)
        if attr_name in self.IQ_ATTRS:         return weights.get("iq",         0.2)
        return 0.2

    def calculate_team_synergy(self, team_list):
        team_attributes = {}
        for p in team_list:
            name_key    = self.normalize_name(p['name'])
            player_data = self.player_db.get(name_key, {})
            attrs       = player_data.get("attributes", {})
            ovr_factor  = player_data.get("overall", 80) / 100.0
            pos         = p.get('position', 'SF')
            for attr_name, value in attrs.items():
                weight       = self.get_weight(attr_name, pos)
                contribution = value * ovr_factor * weight
                team_attributes[attr_name] = team_attributes.get(attr_name, 0) + contribution
        return team_attributes

    def run_simulation(self):
        user_players = [p for p in self.user_team.values() if p is not None]
        cpu_players  = [p for p in self.cpu_team.values()  if p is not None]

        if len(user_players) < 5 or len(cpu_players) < 5:
            return

        u_team_map = self.calculate_team_synergy(user_players)
        c_team_map = self.calculate_team_synergy(cpu_players)

        u_rating = sum(u_team_map.values()) / len(u_team_map) if u_team_map else 0
        c_rating = sum(c_team_map.values()) / len(c_team_map) if c_team_map else 0

        print(f"🔵 User Team Rating:  {u_rating:.2f}")
        print(f"🔴 CPU  Team Rating:  {c_rating:.2f}")
        print(f"📊 Avg Difference:    {u_rating - c_rating:.2f}  ({'🔵' if u_rating > c_rating else '🔴'})")

        all_keys  = set(u_team_map.keys()) | set(c_team_map.keys())
        print("\nAttribute Difference Map (User - CPU):")
        for attr in sorted(all_keys):
            u_val = u_team_map.get(attr, 0)
            c_val = c_team_map.get(attr, 0)
            diff  = u_val - c_val
            arrow = "🔵" if diff >= 0 else "🔴"
            print(f"  {arrow} {attr:<25} U: {u_val:>6.2f}  C: {c_val:>6.2f}  Δ: {diff:>+7.2f}")

        win_chance = 1 / (1 + math.exp(-0.1 * (u_rating - c_rating)))
        win_chance = max(0.1, min(0.9, win_chance))
        print(f"\n🥊 Series win rate: {(win_chance*100):.2f}%")

        u_wins, c_wins, log = 0, 0, []
        while u_wins < 40 and c_wins < 40:
            if random.random() < win_chance:
                u_wins += 1
                if u_wins > 0 and u_wins % 10 == 0:
                    log.append("W")
            else:
                c_wins += 1
                if c_wins > 0 and c_wins % 10 == 0:
                    log.append("L")

        self.show_results(u_wins // 10, c_wins // 10, log, u_rating)

    def show_results(self, u, c, log, u_pwr):
        prob   = min((u_pwr / 85), 0.99)
        proj_w = round(prob * 82)

        print(f"🏆 Regular Season win rate: {(prob*100):.2f}%")

        result_str = " - ".join(log)
        won        = u == 4

        main_txt = f"SERIES  {u} – {c}   [{result_str}]"
        sub_txt  = f"82-game projection:  {proj_w} – {82 - proj_w}"
        color    = "#4BB543" if won else DANGER
        icon     = "\U0001f3c6" if won else "\U0001f4a5"

        self.after(0, lambda: self._set_status(main_txt, color, icon=icon, sub=sub_txt))
        if won:
            self.after(0, lambda: self.pick_hint.config(text="\U0001f3c6  YOU WIN", fg="#4BB543"))
        else:
            self.after(0, lambda: self.pick_hint.config(text="\U0001f4a5  CPU WINS", fg=DANGER))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_status(self, text, color=TEXT, icon="\u2139", sub=""):
        self.status_label.config(text=text, fg=color)
        self.status_icon.config(text=icon, fg=color)
        self.status_sub.config(text=sub)

    def _update_dots(self):
        for i, d in enumerate(self.dot_labels):
            r = i + 1
            if r < self.current_round:
                d.config(fg=ACCENT)
            elif r == self.current_round:
                d.config(fg="#FFC142")
            else:
                d.config(fg=BG3)

if __name__ == "__main__":
    app = NBA2KSimGame()
    app.mainloop()