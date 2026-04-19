"""
views/edit_dialog.py
--------------------
Full transaction edit dialog — pure tkinter, no external dependencies.
- Custom calendar popup for date picking
- IDR amount field with live thousands-separator formatting
- Editable: date, merchant, amount, card, category, note
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar
from typing import Callable

from models import Transaction, CARDS, CATEGORIES
from views.theme import *


# ── Custom Calendar Popup ────────────────────────────────────────────────────

class _CalendarPopup(tk.Toplevel):
    """Lightweight month-grid calendar popup."""

    def __init__(self, parent, initial_date: date, on_select: Callable[[date], None]):
        super().__init__(parent)
        self.on_select   = on_select
        self._year       = initial_date.year
        self._month      = initial_date.month
        self._selected   = initial_date
        self._alive      = True

        self.overrideredirect(True)
        self.configure(bg=BG_CARD)
        self.attributes("-topmost", True)

        self._build()
        self._position(parent)

        # Poll every 200ms — close if pointer moves outside and button released
        self._poll()

    def _position(self, parent) -> None:
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty() + parent.winfo_height() + 2
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_width(), self.winfo_height()
        x = min(px, sw - w - 4)
        y = min(py, sh - h - 4)
        self.geometry(f"+{x}+{y}")

    def _poll(self) -> None:
        """Close if a click happens outside the popup bounds."""
        if not self._alive:
            return
        try:
            # Get absolute mouse position
            mx = self.winfo_pointerx()
            my = self.winfo_pointery()
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            inside = wx <= mx <= wx + ww and wy <= my <= wy + wh

            # Check if any mouse button is currently pressed outside
            import tkinter
            if not inside:
                # Use event_generate to check — simpler: track via a flag
                pass

            self.after(200, self._poll)
        except Exception:
            pass

    def _build(self) -> None:
        self._frame = tk.Frame(self, bg=BG_CARD, padx=8, pady=8)
        self._frame.pack()
        self._render()
        # Escape key closes
        self.bind_all("<Escape>", lambda e: self._close())
        # Click outside: bind to parent toplevel
        self._toplevel_id = None
        self.after(50, self._arm_outside_click)

    def _arm_outside_click(self) -> None:
        """Arm the outside-click detector after a short delay."""
        def check(event):
            if not self._alive:
                return
            try:
                # Walk widget tree to see if click is inside popup
                w = event.widget
                while w is not None:
                    if w is self or w is self._frame:
                        return  # inside — ignore
                    w = getattr(w, 'master', None)
                # Outside click — close
                self._close()
            except Exception:
                pass

        # Bind to the root window
        root = self.nametowidget(".")
        # Use ButtonRelease so _pick() fires first on day labels
        root.bind("<ButtonRelease-1>", check, add="+")
        self._outside_handler = check
        self._root = root

    def _render(self) -> None:
        for w in self._frame.winfo_children():
            w.destroy()

        hdr = tk.Frame(self._frame, bg=BG_CARD)
        hdr.pack(fill="x", pady=(0, 6))

        def nav(delta_month=0, delta_year=0):
            m = self._month + delta_month
            y = self._year  + delta_year
            while m < 1:  m += 12; y -= 1
            while m > 12: m -= 12; y += 1
            self._month, self._year = m, y
            self._render()

        prev_yr = tk.Label(hdr, text="◀◀", bg=BG_CARD, fg=FG_SECONDARY,
                           font=FONT_SMALL, cursor="hand2")
        prev_yr.pack(side="left")
        prev_yr.bind("<Button-1>", lambda e: nav(delta_year=-1))

        prev_mo = tk.Label(hdr, text="◀", bg=BG_CARD, fg=FG_SECONDARY,
                           font=FONT_SMALL, cursor="hand2")
        prev_mo.pack(side="left", padx=4)
        prev_mo.bind("<Button-1>", lambda e: nav(delta_month=-1))

        title = datetime(self._year, self._month, 1).strftime("%B %Y")
        tk.Label(hdr, text=title, bg=BG_CARD, fg=FG_PRIMARY,
                 font=FONT_HEADING, width=14).pack(side="left", expand=True)

        next_mo = tk.Label(hdr, text="▶", bg=BG_CARD, fg=FG_SECONDARY,
                           font=FONT_SMALL, cursor="hand2")
        next_mo.pack(side="right", padx=4)
        next_mo.bind("<Button-1>", lambda e: nav(delta_month=1))

        next_yr = tk.Label(hdr, text="▶▶", bg=BG_CARD, fg=FG_SECONDARY,
                           font=FONT_SMALL, cursor="hand2")
        next_yr.pack(side="right")
        next_yr.bind("<Button-1>", lambda e: nav(delta_year=1))

        days_hdr = tk.Frame(self._frame, bg=BG_CARD)
        days_hdr.pack(fill="x")
        for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            tk.Label(days_hdr, text=d, bg=BG_CARD, fg=FG_SECONDARY,
                     font=FONT_SMALL, width=3).pack(side="left")

        cal = calendar.monthcalendar(self._year, self._month)
        for week in cal:
            row = tk.Frame(self._frame, bg=BG_CARD)
            row.pack(fill="x")
            for day in week:
                if day == 0:
                    tk.Label(row, text="", bg=BG_CARD, width=3,
                             font=FONT_SMALL).pack(side="left")
                else:
                    is_sel = (day == self._selected.day and
                              self._month == self._selected.month and
                              self._year  == self._selected.year)
                    bg = FG_BLUE if is_sel else BG_CARD
                    fg = "white"  if is_sel else FG_PRIMARY
                    lbl = tk.Label(row, text=str(day), bg=bg, fg=fg,
                                   font=FONT_SMALL, width=3, cursor="hand2")
                    lbl.pack(side="left")
                    lbl.bind("<Button-1>", lambda e, d=day: self._pick(d))
                    lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=FG_BLUE, fg="white"))
                    lbl.bind("<Leave>", lambda e, l=lbl, b=bg, f=fg: l.config(bg=b, fg=f))

    def _pick(self, day: int) -> None:
        self._selected = date(self._year, self._month, day)
        self.on_select(self._selected)
        self._close()

    def _close(self) -> None:
        if not self._alive:
            return
        self._alive = False
        try:
            if hasattr(self, '_root') and hasattr(self, '_outside_handler'):
                self._root.unbind("<ButtonRelease-1>")
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


# ── Edit Dialog ───────────────────────────────────────────────────────────────

class EditDialog(tk.Toplevel):

    def __init__(self, parent: tk.Widget,
                 txn: Transaction,
                 on_save: Callable[[Transaction], None]):
        super().__init__(parent)
        self.txn     = txn
        self.on_save = on_save
        self._selected_date = datetime.strptime(txn.date, "%Y-%m-%d").date()

        self.title("Edit Transaction")
        self.configure(bg=BG_PANEL)
        self.resizable(False, False)
        self.transient(parent)

        self._build()
        self._center()

        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _center(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 460, 540
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        tk.Label(self, text="Edit Transaction", bg=BG_PANEL,
                 fg=FG_PRIMARY, font=FONT_HEADING).pack(pady=(18, 4))
        tk.Label(self, text=self.txn.merchant, bg=BG_PANEL,
                 fg=FG_SECONDARY, font=FONT_SMALL).pack(pady=(0, 14))

        self._build_date_row()
        self._build_entry_row("Merchant",    self.txn.merchant)
        self._build_amount_row()
        self._build_combo_row("Credit Card", CARDS,       self.txn.card)
        self._build_combo_row("Category",    CATEGORIES,  self.txn.category)
        self._build_entry_row("Note",        self.txn.note, attr="_note_var")
        self._build_save_btn()

    # ── Date row ──────────────────────────────────────────────────────────────

    def _build_date_row(self) -> None:
        frame = tk.Frame(self, bg=BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text="Date", bg=BG_PANEL, fg=FG_SECONDARY,
                 font=FONT_SMALL, width=14, anchor="w").pack(side="left")

        # Date display button
        self._date_lbl_var = tk.StringVar(value=self._selected_date.strftime("%d-%m-%Y"))
        date_btn = tk.Label(frame, textvariable=self._date_lbl_var,
                            bg=BG_CARD, fg=FG_PRIMARY, font=FONT_BODY,
                            padx=10, pady=4, cursor="hand2", anchor="w")
        date_btn.pack(side="left", fill="x", expand=True)

        cal_icon = tk.Label(frame, text="📅", bg=BG_CARD, fg=FG_PRIMARY,
                            font=FONT_BODY, cursor="hand2", padx=6)
        cal_icon.pack(side="left")

        # Open calendar on click of either label or icon
        for w in (date_btn, cal_icon):
            w.bind("<Button-1>", lambda e: self._open_calendar(date_btn))

    def _open_calendar(self, anchor_widget) -> None:
        _CalendarPopup(anchor_widget, self._selected_date, self._on_date_picked)

    def _on_date_picked(self, picked: date) -> None:
        self._selected_date = picked
        self._date_lbl_var.set(picked.strftime("%d-%m-%Y"))
        self.lift()
        self.focus_force()

    # ── Generic entry row ─────────────────────────────────────────────────────

    def _build_entry_row(self, label: str, value: str, attr: str = None) -> None:
        frame = tk.Frame(self, bg=BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text=label, bg=BG_PANEL, fg=FG_SECONDARY,
                 font=FONT_SMALL, width=14, anchor="w").pack(side="left")
        var = tk.StringVar(value=value)
        attr_name = attr or f"_{label.lower()}_var"
        setattr(self, attr_name, var)
        tk.Entry(frame, textvariable=var,
                 bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                 font=FONT_BODY, bd=0, relief="flat"
                 ).pack(side="left", fill="x", expand=True, ipady=4)

    # ── Amount row ────────────────────────────────────────────────────────────

    def _build_amount_row(self) -> None:
        frame = tk.Frame(self, bg=BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text="Amount (Rp)", bg=BG_PANEL, fg=FG_SECONDARY,
                 font=FONT_SMALL, width=14, anchor="w").pack(side="left")

        self._amount_var  = tk.StringVar(value=f"{int(self.txn.amount):,}")
        self._formatting  = False
        entry = tk.Entry(frame, textvariable=self._amount_var,
                         bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                         font=FONT_BODY, bd=0, relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._amount_var.trace_add("write", self._on_amount_changed)

    def _on_amount_changed(self, *_) -> None:
        if self._formatting:
            return
        self._formatting = True
        raw = self._amount_var.get().replace(",", "")
        if raw.isdigit():
            self._amount_var.set(f"{int(raw):,}")
        self._formatting = False

    def _get_amount(self) -> float:
        raw = self._amount_var.get().replace(",", "")
        return float(raw) if raw.isdigit() else 0.0

    # ── Combo row ─────────────────────────────────────────────────────────────

    def _build_combo_row(self, label: str, values: list, current: str) -> None:
        frame = tk.Frame(self, bg=BG_PANEL)
        frame.pack(fill="x", padx=24, pady=6)
        tk.Label(frame, text=label, bg=BG_PANEL, fg=FG_SECONDARY,
                 font=FONT_SMALL, width=14, anchor="w").pack(side="left")
        var = tk.StringVar(value=current)
        attr = "_card_var" if label == "Credit Card" else "_cat_var"
        setattr(self, attr, var)
        ttk.Combobox(frame, textvariable=var, values=values,
                     state="readonly", font=FONT_BODY
                     ).pack(side="left", fill="x", expand=True)

    # ── Save button ───────────────────────────────────────────────────────────

    def _build_save_btn(self) -> None:
        btn = tk.Label(self, text="Save Changes", bg=FG_BLUE, fg=FG_PRIMARY,
                       font=FONT_HEADING, padx=20, pady=8, cursor="hand2")
        btn.pack(pady=20)
        btn.bind("<Button-1>", lambda e: self._save())
        btn.bind("<Enter>",    lambda e: btn.config(bg="#0060cc"))
        btn.bind("<Leave>",    lambda e: btn.config(bg=FG_BLUE))
        self.bind("<Return>",  lambda e: self._save())

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            merchant = self._merchant_var.get().strip()
            if not merchant:
                raise ValueError("Merchant name is required.")
            amount = self._get_amount()
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError as exc:
            messagebox.showerror("Invalid Input", str(exc), parent=self)
            return

        updated = Transaction(
            id=self.txn.id,
            date=self._selected_date.strftime("%Y-%m-%d"),
            card=self._card_var.get(),
            category=self._cat_var.get(),
            merchant=merchant,
            amount=amount,
            note=self._note_var.get(),
            statement_month=self.txn.statement_month,
        )
        self.on_save(updated)
        self.destroy()
        