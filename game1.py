import tkinter as tk
from tkinter import ttk
import json
import random
import os
from PIL import Image, ImageTk

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
JSON_PATH    = os.path.join(BASE_DIR, "data", "player_data.json")
LOGOS_DIR    = os.path.join(BASE_DIR, "data", "logos")
PLAYERS_DIR  = os.path.join(BASE_DIR, "data", "players")
NUM_PLAYERS  = 2
POSITIONS    = ["PG", "SG", "SF", "PF", "C"]

# Identified from screenshot (left-to-right, top-to-bottom)
LOGO_FILES = {
    "BOS": "image_2.png",   # Boston Celtics
    "BKN": "image_3.png",   # Brooklyn Nets
    "NYK": "image_4.png",   # New York Knicks
    "PHI": "image_5.png",   # Philadelphia 76ers
    "TOR": "image_6.png",   # Toronto Raptors
    "CHI": "image_7.png",   # Chicago Bulls
    "CLE": "image_8.png",   # Cleveland Cavaliers
    "DET": "image_9.png",   # Detroit Pistons
    "IND": "image_10.png",  # Indiana Pacers
    "MIL": "image_11.png",  # Milwaukee Bucks
    "ATL": "image_12.png",  # Atlanta Hawks
    "CHA": "image_13.png",  # Charlotte Hornets
    "MIA": "image_14.png",  # Miami Heat
    "ORL": "image_15.png",  # Orlando Magic
    "WAS": "image_16.png",  # Washington Wizards
    "DEN": "image_17.png",  # Denver Nuggets
    "MIN": "image_18.png",  # Minnesota Timberwolves
    "OKC": "image_19.png",  # Oklahoma City Thunder
    "POR": "image_20.png",  # Portland Trail Blazers
    "UTA": "image_21.png",  # Utah Jazz
    "GSW": "image_22.png",  # Golden State Warriors
    "LAC": "image_23.png",  # Los Angeles Clippers
    "LAL": "image_24.png",  # Los Angeles Lakers
    "PHX": "image_25.png",  # Phoenix Suns
    "SAC": "image_26.png",  # Sacramento Kings
    "DAL": "image_27.png",  # Dallas Mavericks
    "HOU": "image_28.png",  # Houston Rockets
    "MEM": "image_29.png",  # Memphis Grizzlies
    "NOP": "image_30.png",  # New Orleans Pelicans
    "SAS": "image_31.png",  # San Antonio Spurs
}

TEAM_NAMES = {
    "ATL": "Atlanta Hawks",        "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",        "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",        "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",     "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",      "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",      "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",      "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder","ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",   "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers","SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",            "WAS": "Washington Wizards",
}

TEAM_COLORS = {
    "ATL": "#E03A3E", "BOS": "#007A33", "BKN": "#AAAAAA", "CHA": "#00788C",
    "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#FEC524",
    "DET": "#C8102E", "GSW": "#FFC72C", "HOU": "#970C2F", "IND": "#FDBB30",
    "LAC": "#C8102E", "LAL": "#FDB927", "MEM": "#5D76A9", "MIA": "#F9A01B",
    "MIL": "#EEE1C6", "MIN": "#78BE20", "NOP": "#C8A956", "NYK": "#F58426",
    "OKC": "#007cc2", "ORL": "#C4CED4", "PHI": "#006BB6", "PHX": "#E56020",
    "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#F3688B",
    "UTA": "#F9A01B", "WAS": "#E31837",
}

# ─── PALETTE ──────────────────────────────────────────────────────────────────
BG     = "#0A0F1E"
BG2    = "#111827"
BG3    = "#1A2540"
ACCENT = "#F5A623"
TEXT   = "#E8EAF0"
MUTED  = "#6B7FA8"
DANGER = "#E24B4A"

ROULETTE_STEPS = 22

# ─── DATA ─────────────────────────────────────────────────────────────────────
with open(JSON_PATH, "r", encoding="utf-8") as f:
    ALL_TEAMS = json.load(f)

VALID_KEYS = [k for k in LOGO_FILES if k in ALL_TEAMS]

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def luminance(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299*r + 0.587*g + 0.114*b

def fg_for(hex_color):
    return "#000000" if luminance(hex_color) > 145 else "#FFFFFF"

def load_logo_img(team_key, size):
    fname = LOGO_FILES.get(team_key)
    if not fname:
        return None
    path = os.path.join(LOGOS_DIR, fname)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)

def load_player_img(player_name, size=(80, 80)):
    """Tries First_Last.png in nba_players folder."""
    fname = player_name.replace(" ", "_") + ".png"
    path = os.path.join(PLAYERS_DIR, fname)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


# ─── APPLICATION ──────────────────────────────────────────────────────────────
class NBADraftApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NBA Draft Game")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.minsize(920, 800)
        self.geometry("980x730")

        self._logo_cache = {}

        self.rosters        = {p: {pos: None for pos in POSITIONS} for p in range(1, NUM_PLAYERS+1)}
        self.current_player = 1
        self.current_round  = 1
        self.total_rounds   = 5
        self.current_team   = None
        self.sel_player     = None
        self.sel_pos        = None

        self._build_ui()
        self._render_rosters()
        self._start_turn()

        self.icon_img = tk.PhotoImage(file="logo.png")
        self.iconphoto(False, self.icon_img)

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        topbar = tk.Frame(self, bg=BG2, height=50)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="\U0001f3c0  NBA Draft Simulation", bg=BG2, fg=ACCENT,
                 font=("Arial Black", 13, "bold")).pack(side="left", padx=18, pady=12)
        self.lbl_topstatus = tk.Label(topbar, text="", bg=BG2, fg=MUTED,
                                      font=("Arial", 10))
        self.lbl_topstatus.pack(side="right", padx=18)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # ── LEFT
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        # round dots
        dots_row = tk.Frame(left, bg=BG)
        dots_row.pack(anchor="w", pady=(0, 6))
        self.dot_labels = []
        for _ in range(self.total_rounds):
            d = tk.Label(dots_row, text="\u25cf", bg=BG, fg=BG3, font=("Arial", 10))
            d.pack(side="left", padx=3)
            self.dot_labels.append(d)

        # roulette
        self.frm_roulette = tk.Frame(left, bg=BG2, height=165)
        self.frm_roulette.pack(fill="x")
        self.frm_roulette.pack_propagate(False)

        self.lbl_turn = tk.Label(left, text="", bg=BG, fg=MUTED, font=("Arial", 10))
        self.lbl_turn.pack(anchor="w", pady=(8, 0))
        self.lbl_team = tk.Label(left, text="", bg=BG, fg=TEXT,
                                 font=("Arial Black", 18, "bold"))
        self.lbl_team.pack(anchor="w")

        tk.Label(left, text="Search player", bg=BG, fg=MUTED,
                 font=("Arial", 9)).pack(anchor="w", pady=(12, 2))

        entry_frame = tk.Frame(left, bg=BG3)
        entry_frame.pack(fill="x")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.entry = tk.Entry(entry_frame, textvariable=self.search_var,
                              bg=BG3, fg=TEXT, insertbackground=ACCENT,
                              font=("Arial", 13), bd=0, highlightthickness=0,
                              relief="flat", disabledbackground=BG3)
        self.entry.pack(fill="x", ipady=9, ipadx=12)
        tk.Frame(left, bg="#2A3A5A", height=1).pack(fill="x")

        lb_wrap = tk.Frame(left, bg=BG3)
        lb_wrap.pack(fill="x")
        sb = tk.Scrollbar(lb_wrap, bg=BG2, troughcolor=BG2,
                          activebackground=BG3, width=7, relief="flat")
        sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(lb_wrap, yscrollcommand=sb.set,
                                  bg=BG3, fg=TEXT,
                                  selectbackground="#1E3A5A",
                                  selectforeground=ACCENT,
                                  font=("Arial", 10), bd=0,
                                  highlightthickness=0, relief="flat",
                                  activestyle="none", height=7,
                                  exportselection=False)
        self.listbox.pack(fill="x")
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        self.frm_card = tk.Frame(left, bg=BG2)
        self.frm_card.pack(fill="x", pady=(8, 0))

        tk.Label(left, text="Place at position:", bg=BG, fg=MUTED,
                 font=("Arial", 9)).pack(anchor="w", pady=(12, 3))
        pos_row = tk.Frame(left, bg=BG)
        pos_row.pack(anchor="w")
        self.pos_btns = {}
        for pos in POSITIONS:
            btn = tk.Button(pos_row, text=pos, width=5, height=1,
                            bg=BG3, fg=TEXT, font=("Arial", 11, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            activebackground=ACCENT, activeforeground="#000",
                            command=lambda p=pos: self._select_pos(p))
            btn.pack(side="left", padx=4)
            self.pos_btns[pos] = btn

        self.btn_confirm = tk.Button(left, text="\u2713  Confirm Pick",
                                     bg=ACCENT, fg="#000000",
                                     font=("Arial Black", 12, "bold"),
                                     relief="flat", bd=0, padx=0, pady=10,
                                     cursor="hand2", state="disabled",
                                     command=self._confirm_pick)
        self.btn_confirm.pack(fill="x", pady=(12, 0))
        self.lbl_err = tk.Label(left, text="", bg=BG, fg=DANGER, font=("Arial", 9))
        self.lbl_err.pack(anchor="w")

        # ── RIGHT (rosters)
        right = tk.Frame(body, bg=BG, width=230)
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)
        tk.Label(right, text="ROSTERS", bg=BG, fg=MUTED,
                 font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 8))
        self.frm_rosters = tk.Frame(right, bg=BG)
        self.frm_rosters.pack(fill="both", expand=True)

    # ── TURN / ROULETTE ───────────────────────────────────────────────────────
    def _start_turn(self):
        self.current_team = None
        self.sel_player   = None
        self.sel_pos      = None
        self.entry.config(state="disabled")
        self.search_var.set("")
        self.listbox.delete(0, "end")
        self._clear_card()
        self.lbl_err.config(text="")
        self.btn_confirm.config(state="disabled")
        self._refresh_pos_buttons()
        self.lbl_topstatus.config(
            text=f"Round {self.current_round} / {self.total_rounds}   \u2022   Player {self.current_player}'s turn")
        self.lbl_turn.config(text=f"Player {self.current_player}'s pick")
        self.lbl_team.config(text="", fg=TEXT)
        self._update_dots()
        self._render_rosters()

        final = random.choice(VALID_KEYS)
        seq   = [random.choice(VALID_KEYS) for _ in range(ROULETTE_STEPS - 1)]
        seq.append(final)
        self._roulette_step(seq, 0, final)

    def _roulette_step(self, seq, idx, final):
        for w in self.frm_roulette.winfo_children():
            w.destroy()

        key   = seq[idx]
        color = TEAM_COLORS.get(key, "#334155")
        inner = tk.Frame(self.frm_roulette, bg=color)
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)

        logo = self._get_logo(key, (130, 130))
        if logo:
            lbl = tk.Label(inner, image=logo, bg=color, bd=0)
            lbl.image = logo
            lbl.pack(expand=True, pady=12)
        else:
            tk.Label(inner, text=key, bg=color, fg=fg_for(color),
                     font=("Arial Black", 36, "bold")).pack(expand=True)

        if idx < len(seq) - 1:
            t = idx / (len(seq) - 1)
            delay = int(30 + t * t * 200)
            self.after(delay, lambda: self._roulette_step(seq, idx + 1, final))
        else:
            self.after(350, lambda: self._reveal_team(final))

    def _reveal_team(self, key):
        self.current_team = key
        color = TEAM_COLORS.get(key, ACCENT)
        self.lbl_team.config(text=TEAM_NAMES.get(key, key), fg=color)
        self.entry.config(state="normal")
        self.entry.focus_set()
        self._fill_list("")

    # ── SEARCH ────────────────────────────────────────────────────────────────
    def _on_search(self, *_):
        if not self.current_team:
            return
        q = self.search_var.get().strip().lower()
        self._fill_list(q)
        self.sel_player = None
        self._clear_card()
        self._update_confirm()

    def _fill_list(self, query):
        self.listbox.delete(0, "end")
        for p in ALL_TEAMS.get(self.current_team, []):
            if query in p["name"].lower():
                self.listbox.insert("end", p["name"])

    def _on_listbox_select(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        self.sel_player = name
        self._show_card(name)
        self._update_confirm()

    # ── PLAYER CARD ───────────────────────────────────────────────────────────
    def _clear_card(self):
        for w in self.frm_card.winfo_children():
            w.destroy()

    def _show_card(self, name):
        self._clear_card()
        players = ALL_TEAMS.get(self.current_team, [])
        pdata   = next((p for p in players if p["name"] == name), None)
        if not pdata:
            return

        team_color = TEAM_COLORS.get(self.current_team, ACCENT)
        card = tk.Frame(self.frm_card, bg=BG2)
        card.pack(fill="x", ipady=6)

        img = load_player_img(name, (100, 76))
        if img:
            lbl_img = tk.Label(card, image=img, bg=BG2, bd=0)
            lbl_img.image = img
            lbl_img.pack(side="left", padx=(10, 0), pady=8)

        info = tk.Frame(card, bg=BG2)
        info.pack(side="left", padx=12, pady=6, fill="x", expand=True)

        tk.Label(info, text=name, bg=BG2, fg=team_color,
                 font=("Arial Black", 13, "bold"), anchor="w",
                 wraplength=240, justify="left").pack(anchor="w")

        pos_str = "  \u00b7  ".join(pdata.get("positions", []) or ["\u2014"])
        tk.Label(info, text=pos_str, bg=BG2, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(anchor="w")

        years = pdata.get("years", "")
        if years:
            tk.Label(info, text=years, bg=BG2, fg=MUTED,
                     font=("Arial", 9), anchor="w").pack(anchor="w")

    # ── POSITION BUTTONS ──────────────────────────────────────────────────────
    def _refresh_pos_buttons(self):
        roster = self.rosters[self.current_player]
        for pos, btn in self.pos_btns.items():
            if roster[pos] is not None:
                btn.config(bg="#0D1526", fg="#2A3A5A", state="disabled", cursor="arrow")
            elif pos == self.sel_pos:
                btn.config(bg=ACCENT, fg="#000000", state="normal", cursor="hand2")
            else:
                btn.config(bg=BG3, fg=TEXT, state="normal", cursor="hand2")

    def _select_pos(self, pos):
        if self.rosters[self.current_player][pos] is not None:
            return
        self.sel_pos = pos
        self._refresh_pos_buttons()
        self._update_confirm()

    def _update_confirm(self):
        ready = bool(self.sel_player and self.sel_pos)
        self.btn_confirm.config(state="normal" if ready else "disabled")

    # ── CONFIRM PICK ──────────────────────────────────────────────────────────
    def _confirm_pick(self):
        if not self.sel_player or not self.sel_pos:
            return
        self.rosters[self.current_player][self.sel_pos] = {
            "name": self.sel_player,
            "team": self.current_team,
        }
        self.current_player += 1
        if self.current_player > NUM_PLAYERS:
            self.current_player = 1
            self.current_round += 1
        if self.current_round > self.total_rounds:
            self._show_final()
        else:
            self._start_turn()

    # ── ROSTER SIDEBAR ────────────────────────────────────────────────────────
    def _render_rosters(self):
        for w in self.frm_rosters.winfo_children():
            w.destroy()
        for p in range(1, NUM_PLAYERS + 1):
            active = (p == self.current_player)
            hbg    = BG3 if active else BG2
            card   = tk.Frame(self.frm_rosters, bg=hbg)
            card.pack(fill="x", pady=(0, 10))

            hdr = tk.Frame(card, bg=hbg)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"Player {p}", bg=hbg,
                     fg=ACCENT if active else TEXT,
                     font=("Arial", 10, "bold")).pack(side="left", padx=10, pady=(8, 4))
            if active:
                tk.Label(hdr, text="\u25cf picking", bg=hbg, fg=ACCENT,
                         font=("Arial", 8)).pack(side="right", padx=10)

            tk.Frame(card, bg="#2A3A5A", height=1).pack(fill="x")

            for pos in POSITIONS:
                slot = self.rosters[p][pos]
                row  = tk.Frame(card, bg=hbg)
                row.pack(fill="x", padx=10, pady=2)
                tk.Label(row, text=pos, bg=hbg, fg=MUTED,
                         font=("Courier", 8, "bold"), width=4,
                         anchor="w").pack(side="left")
                if slot:
                    clr = TEAM_COLORS.get(slot["team"], ACCENT)
                    tk.Label(row, text=slot["name"], bg=hbg, fg=clr,
                             font=("Arial", 9), anchor="w",
                             wraplength=160, justify="left").pack(side="left", padx=(4, 0))
                else:
                    tk.Label(row, text="\u2014", bg=hbg, fg="#2A3A5A",
                             font=("Arial", 9)).pack(side="left", padx=(4, 0))
            tk.Frame(card, bg=hbg, height=4).pack()

    # ── ROUND DOTS ────────────────────────────────────────────────────────────
    def _update_dots(self):
        for i, d in enumerate(self.dot_labels):
            r = i + 1
            if r < self.current_round:
                d.config(fg=ACCENT)
            elif r == self.current_round:
                d.config(fg="#FFC142")
            else:
                d.config(fg=BG3)

    # ── LOGO CACHE ────────────────────────────────────────────────────────────
    def _get_logo(self, key, size):
        ck = (key, size)
        if ck not in self._logo_cache:
            self._logo_cache[ck] = load_logo_img(key, size)
        return self._logo_cache[ck]

    # ── FINAL SCREEN ──────────────────────────────────────────────────────────
    def _show_final(self):
        for w in self.winfo_children():
            w.destroy()
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(outer, text="\U0001f3c6  Draft Complete!", bg=BG, fg=ACCENT,
                 font=("Arial Black", 22, "bold")).pack(pady=(0, 4))
        tk.Label(outer, text="Final Rosters", bg=BG, fg=MUTED,
                 font=("Arial", 10)).pack(pady=(0, 16))

        grid = tk.Frame(outer, bg=BG)
        grid.pack(fill="both", expand=True)

        for p in range(1, NUM_PLAYERS + 1):
            col = tk.Frame(grid, bg=BG2)
            col.pack(side="left", fill="both", expand=True, padx=8)
            tk.Label(col, text=f"Player {p}", bg=BG2, fg=ACCENT,
                     font=("Arial Black", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
            tk.Frame(col, bg=BG3, height=1).pack(fill="x")

            for pos in POSITIONS:
                slot = self.rosters[p][pos]
                row  = tk.Frame(col, bg=BG2)
                row.pack(fill="x", padx=16, pady=6)
                tk.Label(row, text=pos, bg=BG2, fg=MUTED,
                         font=("Courier", 9, "bold"), width=4,
                         anchor="w").pack(side="left")
                if slot:
                    clr = TEAM_COLORS.get(slot["team"], ACCENT)
                    nf  = tk.Frame(row, bg=BG2)
                    nf.pack(side="left", padx=(8, 0), fill="x", expand=True)
                    logo_s = self._get_logo(slot["team"], (28, 28))
                    if logo_s:
                        ll = tk.Label(nf, image=logo_s, bg=BG2, bd=0)
                        ll.image = logo_s
                        ll.pack(side="left", padx=(0, 5))
                    tk.Label(nf, text=slot["name"], bg=BG2, fg=clr,
                             font=("Arial", 11, "bold"), anchor="w",
                             wraplength=200, justify="left").pack(side="left")
                else:
                    tk.Label(row, text="\u2014 empty \u2014", bg=BG2, fg=BG3,
                             font=("Arial", 11)).pack(side="left", padx=(8, 0))

        tk.Button(outer, text="\u25b6  Play Again",
                  bg=ACCENT, fg="#000000",
                  font=("Arial Black", 12, "bold"),
                  relief="flat", bd=0, padx=32, pady=10,
                  cursor="hand2", command=self._restart).pack(pady=(20, 0))

    def _restart(self):
        for w in self.winfo_children():
            w.destroy()
        self.rosters        = {p: {pos: None for pos in POSITIONS} for p in range(1, NUM_PLAYERS+1)}
        self.current_player = 1
        self.current_round  = 1
        self.current_team   = None
        self.sel_player     = None
        self.sel_pos        = None
        self._logo_cache    = {}
        self._build_ui()
        self._render_rosters()
        self._start_turn()


if __name__ == "__main__":
    app = NBADraftApp()
    app.mainloop()
