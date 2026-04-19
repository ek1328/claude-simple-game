"""
views/sidebar.py
----------------
Left panel: month list with mini spend bars and search.
Calls back into the app via on_month_selected(month_key).
"""

import tkinter as tk
from typing import Callable, Dict, List

from logic import BusinessLogic
from views.theme import *


class Sidebar(tk.Frame):

    def __init__(self, parent: tk.Widget, on_month_selected: Callable[[str], None]):
        super().__init__(parent, bg=BG_SIDEBAR, width=240)
        self.on_month_selected = on_month_selected
        self._selected_month: str | None = None

        self._build()

    # ── Public ─────────────────────────────────────────────────────────────

    def refresh(self, month_totals: Dict[str, float], selected_month: str | None) -> None:
        """Re-render the month list with updated totals."""
        self._selected_month = selected_month
        query = self._search_var.get().lower()

        months = sorted(month_totals.keys(), reverse=True)
        if query:
            months = [m for m in months if query in BusinessLogic.fmt_month(m).lower()]

        # Clear existing rows
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not months:
            self._build_empty_state()
            self._total_label.config(text="No transactions yet")
            return

        max_total = max(month_totals.values(), default=1)

        for i, mk in enumerate(months):
            total = month_totals[mk]
            self._build_month_row(mk, total, max_total, i)

        grand_total = sum(month_totals[m] for m in months)
        self._total_label.config(text=f"Total shown: {BusinessLogic.fmt_idr(grand_total)}")

    def _build_empty_state(self) -> None:
        frame = tk.Frame(self._list_frame, bg=BG_SIDEBAR)
        frame.pack(fill="both", expand=True, pady=40)
        tk.Label(frame, text="📂", bg=BG_SIDEBAR, fg=FG_SECONDARY,
                 font=("SF Pro Display" if __import__("platform").system() == "Darwin"
                       else "Segoe UI", 32)).pack()
        tk.Label(frame, text="No data yet", bg=BG_SIDEBAR,
                 fg=FG_PRIMARY, font=FONT_HEADING).pack(pady=(8, 4))
        tk.Label(frame, text="Upload a statementto get started",
                 bg=BG_SIDEBAR, fg=FG_SECONDARY, font=FONT_SMALL,
                 justify="center").pack()

    # ── Build ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_search()
        self._build_section_label()
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x", padx=12)
        self._build_scrollable_list()
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x")
        self._total_label = tk.Label(self, text="", bg=BG_SIDEBAR,
                                     fg=FG_SECONDARY, font=FONT_SMALL, pady=8)
        self._total_label.pack()

    def _build_search(self) -> None:
        frame = tk.Frame(self, bg=BG_SIDEBAR, pady=10)
        frame.pack(fill="x", padx=12)
        tk.Label(frame, text="🔍", bg=BG_SIDEBAR, fg=FG_SECONDARY,
                 font=FONT_BODY).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_changed())
        tk.Entry(frame, textvariable=self._search_var,
                 bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                 font=FONT_BODY, bd=0, relief="flat"
                 ).pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=4)

    def _build_section_label(self) -> None:
        tk.Label(self, text="MONTHLY OVERVIEW", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=FONT_SMALL
                 ).pack(anchor="w", padx=16, pady=(6, 4))

    def _build_scrollable_list(self) -> None:
        container = tk.Frame(self, bg=BG_SIDEBAR)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=BG_SIDEBAR, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=BG_SIDEBAR)
        self._window_id = self._canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        self._list_frame.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._window_id, width=e.width))

    def _build_month_row(self, mk: str, total: float, max_total: float, index: int) -> None:
        is_selected = mk == self._selected_month
        bg = BG_SELECTED if is_selected else (BG_CARD if index % 2 == 0 else BG_SIDEBAR)

        row = tk.Frame(self._list_frame, bg=bg, cursor="hand2")
        row.pack(fill="x", pady=1)

        inner = tk.Frame(row, bg=bg, padx=14, pady=10)
        inner.pack(fill="x")

        tk.Label(inner, text=BusinessLogic.fmt_month(mk), bg=bg,
                 fg=FG_PRIMARY, font=FONT_HEADING, anchor="w").pack(fill="x")

        bottom = tk.Frame(inner, bg=bg)
        bottom.pack(fill="x")

        # Mini bar
        CANVAS_W = 80
        bar = tk.Canvas(bottom, width=CANVAS_W, height=6, bg=bg, bd=0, highlightthickness=0)
        bar.pack(side="left", pady=(4, 0))
        fill_w = max(4, int(CANVAS_W * total / max_total))
        bar.create_rectangle(0, 0, CANVAS_W, 6, fill=BG_CARD, outline="")
        bar.create_rectangle(0, 0, fill_w, 6,
                             fill=FG_GREEN if total < 5_000_000 else FG_RED, outline="")

        tk.Label(bottom, text=BusinessLogic.fmt_idr(total), bg=bg,
                 fg=FG_GREEN, font=FONT_SMALL, anchor="e").pack(side="right")

        # Bind click on all child widgets
        for widget in [row, inner, bottom, *inner.winfo_children(), *bottom.winfo_children()]:
            widget.bind("<Button-1>", lambda e, m=mk: self.on_month_selected(m))

    # ── Callbacks ───────────────────────────────────────────────────────────

    def _on_search_changed(self) -> None:
        # Trigger a refresh from the app with the existing totals
        # by pretending the month was re-selected (app will call refresh)
        if self._selected_month:
            self.on_month_selected(self._selected_month)
