"""
views/add_dialog.py
-------------------
Modal dialog for adding a new transaction.
Calls on_submit(Transaction) when the user confirms.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Callable

from models import Transaction, CARDS, CATEGORIES
import views.theme as _th
from views.theme import FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL


class AddDialog(tk.Toplevel):

    def __init__(self, parent: tk.Widget, next_id: int,
                 on_submit: Callable[[Transaction], None],
                 selected_month: str = ""):
        super().__init__(parent)
        self.next_id        = next_id
        self.on_submit      = on_submit
        self.selected_month = selected_month  # "YYYY-MM" of the active sidebar month

        self.title("Add Transaction")
        self.configure(bg=_th.BG_PANEL)
        self.resizable(False, False)

        # Make this a child of parent — keeps it in front on macOS
        self.transient(parent)

        self._build()
        self._center()

        # grab_set AFTER window is built and centered — blocks all input to parent
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ── Center ──────────────────────────────────────────────────────────────

    def _center(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 420, 480
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── Build ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        tk.Label(self, text="New Transaction", bg=_th.BG_PANEL,
                 fg=_th.FG_PRIMARY, font=FONT_HEADING).pack(pady=(18, 10))

        self._date_var     = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self._merchant_var = tk.StringVar()
        self._amount_var   = tk.StringVar()
        self._card_var     = tk.StringVar(value=CARDS[0])
        self._cat_var      = tk.StringVar(value=CATEGORIES[0])
        self._note_var     = tk.StringVar()

        self._add_entry_row("Date (YYYY-MM-DD)", self._date_var)
        self._add_entry_row("Merchant",          self._merchant_var)
        self._add_entry_row("Amount (Rp)",       self._amount_var)
        self._add_combo_row("Credit Card",       self._card_var, CARDS)
        self._add_combo_row("Category",          self._cat_var,  CATEGORIES)
        self._add_entry_row("Note (optional)",   self._note_var)

        btn = tk.Label(self, text="Add Transaction", bg=_th.FG_BLUE, fg=_th.FG_PRIMARY,
                       font=FONT_HEADING, padx=20, pady=8, cursor="hand2")
        btn.pack(pady=18)
        btn.bind("<Button-1>", lambda e: self._submit())
        btn.bind("<Enter>",    lambda e: btn.config(bg="#0060cc"))
        btn.bind("<Leave>",    lambda e: btn.config(bg=_th.FG_BLUE))

    def _add_entry_row(self, label: str, var: tk.StringVar) -> None:
        frame = tk.Frame(self, bg=_th.BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text=label, bg=_th.BG_PANEL, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL, width=16, anchor="w").pack(side="left")
        tk.Entry(frame, textvariable=var, bg=_th.BG_CARD, fg=_th.FG_PRIMARY,
                 insertbackground=_th.FG_PRIMARY, font=FONT_BODY,
                 bd=0, relief="flat").pack(side="left", fill="x", expand=True, ipady=4)

    def _add_combo_row(self, label: str, var: tk.StringVar, values: list) -> None:
        frame = tk.Frame(self, bg=_th.BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text=label, bg=_th.BG_PANEL, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL, width=16, anchor="w").pack(side="left")
        ttk.Combobox(frame, textvariable=var, values=values,
                     state="readonly", font=FONT_BODY
                     ).pack(side="left", fill="x", expand=True)

    # ── Submit ──────────────────────────────────────────────────────────────

    def _submit(self) -> None:
        try:
            datetime.strptime(self._date_var.get(), "%Y-%m-%d")
            merchant = self._merchant_var.get().strip()
            if not merchant:
                raise ValueError("Merchant name is required.")
            amount = float(
                self._amount_var.get().replace(".", "").replace(",", "")
            )
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError as exc:
            messagebox.showerror("Invalid Input", str(exc), parent=self)
            return

        txn = Transaction(
            id=self.next_id,
            date=self._date_var.get(),
            card=self._card_var.get(),
            category=self._cat_var.get(),
            merchant=merchant,
            amount=amount,
            note=self._note_var.get(),
        )
        self.on_submit(txn)
        self.destroy()
        