"""
views/import_dialog.py
----------------------
Shows parsed transactions from a PDF statement in a review table.
The user can deselect rows they don't want, assign the correct category,
then click "Import Selected" to save them.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List

from models import Transaction, CATEGORIES
from pdf_parser import ParsedTransaction
from logic import BusinessLogic
from views.theme import *


class ImportDialog(tk.Toplevel):

    def __init__(self, parent: tk.Widget,
                 bank: str,
                 stmt_month_key: str,
                 parsed: List[ParsedTransaction],
                 next_id_fn: Callable[[], int],
                 on_import: Callable[[List[Transaction]], None]):
        super().__init__(parent)
        self.bank            = bank
        self.stmt_month_key  = stmt_month_key   # "YYYY-MM" of statement issue date
        self.parsed          = parsed
        self.next_id_fn      = next_id_fn
        self.on_import       = on_import

        self.title(f"Import Statement — {bank}")
        self.configure(bg=BG_PANEL)
        self.geometry("860x560")
        self._center()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Per-row category vars
        self._cat_vars: List[tk.StringVar] = []
        self._check_vars: List[tk.BooleanVar] = []
        self._row_frames: List[tk.Frame] = []
        self._selected_row: int = -1

        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Header
        hdr = tk.Frame(self, bg=BG_PANEL)
        hdr.pack(fill="x", padx=24, pady=(18, 4))
        from logic import BusinessLogic
        stmt_label = BusinessLogic.fmt_month(self.stmt_month_key)
        tk.Label(hdr, text=f"Found {len(self.parsed)} transactions from {self.bank} — {stmt_label}",
                 bg=BG_PANEL, fg=FG_PRIMARY, font=FONT_HEADING).pack(side="left")
        tk.Label(hdr, text="Uncheck rows to skip. Set category per row.",
                 bg=BG_PANEL, fg=FG_SECONDARY, font=FONT_SMALL).pack(side="left", padx=16)

        # Select all / none
        ctrl = tk.Frame(self, bg=BG_PANEL)
        ctrl.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(ctrl, text="Select:", bg=BG_PANEL, fg=FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        self._make_link(ctrl, "All",  lambda: self._toggle_all(True)).pack(side="left", padx=6)
        self._make_link(ctrl, "None", lambda: self._toggle_all(False)).pack(side="left")

        # Scrollable table
        outer = tk.Frame(self, bg=BG_PANEL)
        outer.pack(fill="both", expand=True, padx=24)

        canvas = tk.Canvas(outer, bg=BG_PANEL, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._canvas = canvas   # store ref for scroll_to_row
        self._table = tk.Frame(canvas, bg=BG_PANEL)
        win = canvas.create_window((0, 0), window=self._table, anchor="nw")
        self._table.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))

        self._build_table_header()
        self._build_table_rows()

        # Bind trackpad / mouse wheel scrolling to the canvas
        self._bind_mousewheel(canvas)

        # Keyboard navigation — bind_all so it works regardless of which widget has focus
        self.bind_all("<Up>",   self._on_arrow_key)
        self.bind_all("<Down>", self._on_arrow_key)
        self.focus_set()
        # Select first row by default
        if self.parsed:
            self.after(100, lambda: self._select_row(0))

        # Summary bar
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x", pady=(8, 0))
        self._summary_frame = tk.Frame(self, bg=BG_MAIN)
        self._summary_frame.pack(fill="x", padx=24, pady=(10, 0))
        self._build_summary()

        # Footer
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x", pady=(8, 0))
        footer = tk.Frame(self, bg=BG_PANEL)
        footer.pack(fill="x", padx=24, pady=12)

        self._count_label = tk.Label(footer, text="", bg=BG_PANEL,
                                     fg=FG_SECONDARY, font=FONT_SMALL)
        self._count_label.pack(side="left")
        self._update_count()

        # Cancel
        btn_cancel = tk.Label(footer, text="Cancel", bg=BG_CARD, fg=FG_PRIMARY,
                               font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_cancel.pack(side="right", padx=(8, 0))
        btn_cancel.bind("<Button-1>", lambda e: self._on_close())
        btn_cancel.bind("<Enter>",    lambda e: btn_cancel.config(bg="#4a4a4c"))
        btn_cancel.bind("<Leave>",    lambda e: btn_cancel.config(bg=BG_CARD))

        # Total label next to Import button (updates with checkbox changes)
        self._footer_total_label = tk.Label(footer, text="", bg=BG_PANEL,
                                            fg=FG_GREEN, font=FONT_HEADING)
        self._footer_total_label.pack(side="right", padx=(0, 16))

        # Import
        btn_import = tk.Label(footer, text="↓ Import Selected", bg=FG_BLUE, fg=FG_PRIMARY,
                               font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_import.pack(side="right")
        btn_import.bind("<Button-1>", lambda e: self._do_import())
        btn_import.bind("<Enter>",    lambda e: btn_import.config(bg="#0060cc"))
        btn_import.bind("<Leave>",    lambda e: btn_import.config(bg=FG_BLUE))

    def _bind_mousewheel(self, canvas: tk.Canvas) -> None:
        """Bind trackpad and mouse wheel to scroll the canvas on macOS and Windows."""
        import platform

        def _on_mousewheel(event):
            # macOS: event.delta is in pixels (usually ±1 units of 120)
            # Windows: event.delta is multiples of 120
            if platform.system() == "Darwin":
                canvas.yview_scroll(-1 * event.delta, "units")
            else:
                canvas.yview_scroll(-1 * (event.delta // 120), "units")

        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-1, "units")

        def _on_linux_scroll_down(event):
            canvas.yview_scroll(1, "units")

        # Bind on canvas and all child widgets so scrolling works anywhere in the table
        def _bind_to_widget(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)        # macOS + Windows
            widget.bind("<Button-4>",   _on_linux_scroll_up)   # Linux scroll up
            widget.bind("<Button-5>",   _on_linux_scroll_down)  # Linux scroll down
            for child in widget.winfo_children():
                _bind_to_widget(child)

        _bind_to_widget(canvas)
        _bind_to_widget(self._table)

        # Re-bind whenever new rows are added to the table
        self._table.bind("<Configure>",
            lambda e: _bind_to_widget(self._table), add="+")

    def _build_table_header(self) -> None:
        cols = ["", "Date", "Merchant", "Amount", "Category"]
        widths = [28, 100, 260, 120, 200]
        hdr = tk.Frame(self._table, bg=BG_HEADER)
        hdr.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(hdr, text=col, bg=BG_HEADER, fg=FG_SECONDARY,
                     font=FONT_SMALL, width=0, anchor="w",
                     padx=6, pady=6).pack(side="left", ipadx=w//8)
        tk.Frame(self._table, bg=BG_CARD, height=1).pack(fill="x")

    def _build_table_rows(self) -> None:
        for i, txn in enumerate(self.parsed):
            check_var = tk.BooleanVar(value=True)
            cat_var   = tk.StringVar(value=self._guess_category(txn.merchant))
            self._check_vars.append(check_var)
            self._cat_vars.append(cat_var)

            bg = BG_PANEL if i % 2 == 0 else BG_ROW_ALT
            row = tk.Frame(self._table, bg=bg)
            row.pack(fill="x")
            self._row_frames.append(row)

            # Checkbox
            cb = tk.Checkbutton(row, variable=check_var, bg=bg,
                                 activebackground=bg,
                                 command=lambda idx=i: (self._update_count(), self.focus_set()))
            cb.pack(side="left", padx=4)

            # Date
            tk.Label(row, text=txn.date, bg=bg, fg=FG_SECONDARY,
                     font=FONT_SMALL, anchor="w", width=11).pack(side="left")

            # Merchant
            merchant = txn.merchant[:34] + "…" if len(txn.merchant) > 35 else txn.merchant
            tk.Label(row, text=merchant, bg=bg, fg=FG_PRIMARY,
                     font=FONT_BODY, anchor="w", width=30).pack(side="left")

            # Amount
            tk.Label(row, text=BusinessLogic.fmt_idr(txn.amount), bg=bg,
                     fg=FG_GREEN, font=FONT_MONO if "FONT_MONO" in dir() else FONT_SMALL,
                     anchor="e", width=14).pack(side="left")

            # Category dropdown
            combo = ttk.Combobox(row, textvariable=cat_var, values=CATEGORIES,
                                 state="readonly", font=FONT_SMALL, width=22)
            combo.pack(side="left", padx=6, pady=3)
            combo.bind("<<ComboboxSelected>>", lambda e: self.focus_set())

            # Bind click on row + every child widget AFTER all children are packed
            def _bind_clicks(widget, idx=i):
                widget.bind("<Button-1>", lambda e, x=idx: self._select_row(x))
                for child in widget.winfo_children():
                    _bind_clicks(child, idx)
            _bind_clicks(row)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _select_row(self, index: int) -> None:
        """Highlight a row and move focus to it."""
        if self._selected_row == index:
            return
        # Unhighlight previous
        if 0 <= self._selected_row < len(self._row_frames):
            self._highlight_row(self._selected_row, selected=False)
        self._selected_row = index
        self._highlight_row(index, selected=True)
        self._scroll_to_row(index)
        # Keep keyboard focus on the dialog so arrow keys work
        self.focus_set()

    def _highlight_row(self, index: int, selected: bool) -> None:
        row = self._row_frames[index]
        bg = BG_SELECTED if selected else (BG_PANEL if index % 2 == 0 else BG_ROW_ALT)
        row.config(bg=bg)
        for child in row.winfo_children():
            try:
                child.config(bg=bg)
            except tk.TclError:
                pass  # some widgets (Combobox) don't support bg this way

    def _scroll_to_row(self, index: int) -> None:
        """Ensure the selected row is visible in the canvas."""
        if not self._row_frames or not hasattr(self, "_canvas"):
            return
        self.update_idletasks()
        row     = self._row_frames[index]
        total_h = self._table.winfo_height()
        if total_h == 0:
            return
        row_y        = row.winfo_y()
        row_h        = row.winfo_height()
        frac_top     = row_y / total_h
        frac_bottom  = (row_y + row_h) / total_h
        cur_top, cur_bottom = self._canvas.yview()
        if frac_top < cur_top:
            self._canvas.yview_moveto(frac_top)
        elif frac_bottom > cur_bottom:
            self._canvas.yview_moveto(frac_bottom - (cur_bottom - cur_top))

    def _on_arrow_key(self, event) -> None:
        """Move selection up/down with arrow keys and toggle check with Space."""
        # Only handle if this dialog is the active grab window
        if self.grab_current() != self:
            return
        n = len(self._row_frames)
        if n == 0:
            return
        if event.keysym == "Down":
            new_idx = min(self._selected_row + 1, n - 1)
        elif event.keysym == "Up":
            new_idx = max(self._selected_row - 1, 0)
        elif event.keysym == "space" and self._selected_row >= 0:
            var = self._check_vars[self._selected_row]
            var.set(not var.get())
            self._update_count()
            return
        else:
            return
        if new_idx != self._selected_row:
            self._select_row(new_idx)

    def _make_link(self, parent, text, command):
        lbl = tk.Label(parent, text=text, bg=BG_PANEL, fg=FG_BLUE,
                       font=FONT_SMALL, cursor="hand2")
        lbl.bind("<Button-1>", lambda e: command())
        return lbl

    def _build_summary(self) -> None:
        """Build the summary stat boxes showing totals for selected transactions."""
        for w in self._summary_frame.winfo_children():
            w.destroy()

        selected = [p for p, v in zip(self.parsed, self._check_vars) if v.get()]
        total    = sum(p.amount for p in selected)
        count    = len(selected)
        highest  = max((p.amount for p in selected), default=0)

        stats = [
            ("Selected Total",  BusinessLogic.fmt_idr(total),   FG_GREEN),
            ("Transactions",    str(count),                      FG_BLUE),
            ("Largest Spend",   BusinessLogic.fmt_idr(highest),  FG_RED),
            ("Average / txn",   BusinessLogic.fmt_idr(total / count) if count else "–", FG_SECONDARY),
        ]

        for label, value, color in stats:
            box = tk.Frame(self._summary_frame, bg=BG_PANEL, padx=14, pady=8)
            box.pack(side="left", padx=(0, 8))
            tk.Label(box, text=label, bg=BG_PANEL, fg=FG_SECONDARY,
                     font=FONT_SMALL).pack(anchor="w")
            tk.Label(box, text=value, bg=BG_PANEL, fg=color,
                     font=FONT_HEADING).pack(anchor="w")

    def _toggle_all(self, value: bool) -> None:
        for var in self._check_vars:
            var.set(value)
        self._update_count()

    def _update_count(self) -> None:
        n = sum(v.get() for v in self._check_vars)
        self._count_label.config(text=f"{n} of {len(self.parsed)} selected")
        if hasattr(self, '_summary_frame'):
            self._build_summary()
        if hasattr(self, '_footer_total_label'):
            selected = [p for p, v in zip(self.parsed, self._check_vars) if v.get()]
            total = sum(p.amount for p in selected)
            self._footer_total_label.config(text=f"Total: {BusinessLogic.fmt_idr(total)}")

    def _on_close(self) -> None:
        """Clean up bind_all before closing so keys don't bleed into main window."""
        try:
            self.unbind_all("<Up>")
            self.unbind_all("<Down>")
        except Exception:
            pass
        self.destroy()

    def _center(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 860, 560
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _guess_category(self, merchant: str) -> str:
        """Simple keyword-based category guesser."""
        m = merchant.lower()
        rules = [
            (["grab", "gojek", "uber", "pertamina", "toll", "parking", "spbu"], "⛽ Transport"),
            (["starbucks", "old chang", "tea", "mcdonald", "pizza", "yakiniku",
              "resto", "cafe", "gofood", "warung", "sushi"], "🍽️ Food & Dining"),
            (["indomaret", "alfamart", "don donki", "fp xtra", "niaga lestari", "keki", 
              "jodoh centre", "snl", "diamond spm", "top 100"], "🛒 Groceries"),
            (["netflix", "spotify", "disney", "youtube", "starlink", "adobe",
              "canva", "claude", "figma"], "📱 Subscriptions"),
            (["shopee", "tokopedia", "skechers", "blibli", "adidas", "nike", "dfs", "wrangler", 
              "h&m", "zara", "uniqlo"], "🛍️ Shopping"),
            (["hotel", "traveloka", "airbnb", "airasia", "agoda", "malindo", "holiday inn",
              "garuda", "booking", "ferry"], "✈️ Travel"),
            (["pln", "telkom", "indihome", "pam ", "water", "listrik"], "💡 Utilities"),
            (["apotik", "apotek", "farmasi", "klinik", "pharmacy", "salon",
              "halodoc", "hospital", "nail"], "🏥 Health"),
            (["cgv", "ticketmaster", "sistic", "steam", "apple.com"], "🎬 Entertainment"),
            (["ikea", "azko", "jackson's", "homeware", "sewa"], "🏠 Housing"),
            (["udemy", "coursera", "gramedia", "buku", "course"], "📚 Education"),
        ]
        for keywords, cat in rules:
            if any(k in m for k in keywords):
                return cat
        return "💼 Other"

    # ── Import ────────────────────────────────────────────────────────────────

    def _do_import(self) -> None:
        selected = [
            (p, self._cat_vars[i].get())
            for i, (p, v) in enumerate(zip(self.parsed, self._check_vars))
            if v.get()
        ]
        if not selected:
            messagebox.showwarning("Nothing selected",
                                   "Please select at least one transaction to import.",
                                   parent=self)
            return

        next_id = self.next_id_fn()
        transactions = []
        for i, (p, cat) in enumerate(selected):
            transactions.append(Transaction(
                id=next_id + i,
                date=p.date,                         # original date — never modified
                card=p.card,
                category=cat,
                merchant=p.merchant,
                amount=p.amount,
                note="Imported from PDF",
                statement_month=self.stmt_month_key, # groups under statement month
            ))

        self.on_import(transactions)
        self._on_close()
