"""
views/toolbar.py
----------------
Top bar with app title, theme toggle, Upload Statement, + Add Transaction.
"""

import tkinter as tk
from tkinter import filedialog
from typing import Callable

import views.theme as _th
from views.theme import FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL
import views.theme as theme


class Toolbar(tk.Frame):

    def __init__(self, parent: tk.Widget,
                 on_add: Callable[[], None],
                 on_upload: Callable[[str], None],
                 on_theme_toggle: Callable[[], None]):
        super().__init__(parent, bg=_th.BG_SIDEBAR, height=52)
        self.pack_propagate(False)
        self.on_theme_toggle = on_theme_toggle
        self._build(on_add, on_upload)

    def _build(self, on_add, on_upload) -> None:
        tk.Label(self, text="💳  Spending Tracker", bg=_th.BG_SIDEBAR,
                 fg=_th.FG_PRIMARY, font=FONT_HEADING).pack(side="left", padx=20, pady=14)

        # + Add Transaction
        btn_add = tk.Label(self, text="+ Add Transaction", bg=_th.FG_BLUE, fg=_th.FG_PRIMARY,
                           font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_add.pack(side="right", padx=(0, 16), pady=10)
        btn_add.bind("<Button-1>", lambda e: on_add())
        btn_add.bind("<Enter>",    lambda e: btn_add.config(bg="#0060cc"))
        btn_add.bind("<Leave>",    lambda e: btn_add.config(bg=_th.FG_BLUE))

        # Upload Statement
        btn_upload = tk.Label(self, text="↑ Upload Statement", bg=_th.BG_CARD, fg=_th.FG_PRIMARY,
                              font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_upload.pack(side="right", padx=(0, 8), pady=10)
        btn_upload.bind("<Button-1>", lambda e: self._pick_pdf(on_upload))
        btn_upload.bind("<Enter>",    lambda e: btn_upload.config(bg="#4a4a4c"))
        btn_upload.bind("<Leave>",    lambda e: btn_upload.config(bg=_th.BG_CARD))

        # Theme toggle
        icon = "☀️" if theme.current_mode() == "dark" else "🌙"
        self._theme_btn = tk.Label(self, text=icon, bg=_th.BG_SIDEBAR,
                                   font=FONT_HEADING, cursor="hand2", padx=8)
        self._theme_btn.pack(side="right", pady=10)
        self._theme_btn.bind("<Button-1>", lambda e: self.on_theme_toggle())

    def update_theme_icon(self) -> None:
        icon = "☀️" if theme.current_mode() == "dark" else "🌙"
        self._theme_btn.config(text=icon)

    def _pick_pdf(self, on_upload) -> None:
        path = filedialog.askopenfilename(
            title="Select Credit Card Statement",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            on_upload(path)
            