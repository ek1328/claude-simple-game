"""
views/main_panel.py
-------------------
Right panel: stats, category chips, card filter, and transaction table.
Receives pre-computed data from the app controller — no logic lives here.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Tuple, Dict

from models import Transaction, CARDS
from logic import BusinessLogic
import views.theme as _th
from views.theme import FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL


class MainPanel(tk.Frame):

    def __init__(self, parent: tk.Widget,
                 on_sort: Callable[[str], None],
                 on_delete: Callable[[int], None],
                 on_card_filter_changed: Callable[[str], None],
                 on_search_changed: Callable[[str], None],
                 on_category_changed: Callable[[int, str], None] = None):
        super().__init__(parent, bg=_th.BG_MAIN)

        self.on_sort = on_sort
        self.on_delete = on_delete
        self.on_card_filter_changed = on_card_filter_changed
        self.on_search_changed = on_search_changed
        self.on_category_changed = on_category_changed
        self._txn_map: dict = {}  # id -> Transaction for double-click lookup

        self._card_var   = tk.StringVar(value="All Cards")
        self._search_var = tk.StringVar()

        self._build()

    # ── Public ─────────────────────────────────────────────────────────────

    def refresh(self,
                month_label: str,
                transactions: List[Transaction],
                card_totals: Dict[str, float],
                top_cats: List[Tuple[str, float]]) -> None:
        """Re-render with fresh data (called by app controller)."""
        total = BusinessLogic.total(transactions)

        self._title_label.config(text=month_label)
        self._total_label.config(text=BusinessLogic.fmt_idr(total))

        self._refresh_stats(transactions, card_totals)
        self._refresh_categories(top_cats)
        self._refresh_table(transactions)
        self._row_count_label.config(text=f"{len(transactions)} transactions")

    def clear_search(self) -> None:
        self._search_var.set("")

    def clear(self) -> None:
        self._title_label.config(text="No data yet")
        self._total_label.config(text="")
        for w in self._stats_frame.winfo_children():
            w.destroy()
        for w in self._cat_frame.winfo_children():
            w.destroy()
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._row_count_label.config(text="")
        self._show_empty_hint()

    def _show_empty_hint(self) -> None:
        """Show a centred prompt when there are no transactions."""
        # Use the tree's parent frame as anchor
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._tree.insert("", "end", iid="hint",
                          values=("", "👆  Click  ↑ Upload Statement  to import your first statement",
                                  "", "", ""),
                          tags=("hint",))
        self._tree.tag_configure("hint", foreground=_th.FG_SECONDARY)

    # ── Build ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        self._build_stats_row()
        self._build_card_filter()
        tk.Frame(self, bg=_th.BG_CARD, height=1).pack(fill="x", padx=24, pady=(0, 8))
        self._build_category_row()
        tk.Frame(self, bg=_th.BG_CARD, height=1).pack(fill="x", padx=24, pady=(0, 8))
        self._build_table()
        self._build_action_bar()

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=_th.BG_MAIN, pady=18)
        hdr.pack(fill="x", padx=24)
        self._title_label = tk.Label(hdr, text="Select a month →", bg=_th.BG_MAIN,
                                     fg=_th.FG_PRIMARY, font=FONT_TITLE, anchor="w")
        self._title_label.pack(side="left", anchor="s")
        self._total_label = tk.Label(hdr, text="", bg=_th.BG_MAIN,
                                     fg=_th.FG_PRIMARY, font=FONT_TITLE, anchor="e")
        self._total_label.pack(side="right", anchor="s")

    def _build_stats_row(self) -> None:
        self._stats_frame = tk.Frame(self, bg=_th.BG_MAIN)
        self._stats_frame.pack(fill="x", padx=24, pady=(0, 12))

    def _build_card_filter(self) -> None:
        frame = tk.Frame(self, bg=_th.BG_MAIN)
        frame.pack(fill="x", padx=24, pady=(0, 8))

        # Card filter buttons (left)
        tk.Label(frame, text="Card:", bg=_th.BG_MAIN, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        for value in ["All Cards"] + CARDS:
            rb = tk.Radiobutton(
                frame, text=value, variable=self._card_var, value=value,
                bg=_th.BG_MAIN, fg=_th.FG_SECONDARY, selectcolor=_th.BG_MAIN,
                activebackground=_th.BG_MAIN, activeforeground=_th.FG_BLUE,
                font=FONT_SMALL, indicatoron=False, relief="flat",
                padx=8, pady=3,
                command=lambda: self.on_card_filter_changed(self._card_var.get()),
            )
            rb.pack(side="left", padx=(6, 0))

        # Merchant search box (right)
        search_frame = tk.Frame(frame, bg=_th.BG_CARD, padx=8, pady=4)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=_th.BG_CARD, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                bg=_th.BG_CARD, fg=_th.FG_PRIMARY, insertbackground=_th.FG_PRIMARY,
                                font=FONT_SMALL, bd=0, relief="flat", width=22)
        search_entry.pack(side="left", padx=(4, 0))
        # Clear button
        clear_btn = tk.Label(search_frame, text="✕", bg=_th.BG_CARD, fg=_th.FG_SECONDARY,
                             font=FONT_SMALL, cursor="hand2")
        clear_btn.pack(side="left", padx=(4, 0))
        clear_btn.bind("<Button-1>", lambda e: self._search_var.set(""))

        self._search_var.trace_add("write", lambda *_: self.on_search_changed(self._search_var.get()))

    def _build_category_row(self) -> None:
        self._cat_frame = tk.Frame(self, bg=_th.BG_MAIN)
        self._cat_frame.pack(fill="x", padx=24, pady=(0, 10))

    def _build_table(self) -> None:
        frame = tk.Frame(self, bg=_th.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        columns = ("date", "merchant", "category", "card", "amount")
        self._tree = ttk.Treeview(frame, columns=columns, show="headings",
                                  height=18, selectmode="browse")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=_th.BG_PANEL, foreground=_th.FG_PRIMARY,
                        fieldbackground=_th.BG_PANEL, rowheight=30,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Treeview.Heading", background=_th.BG_HEADER, foreground=_th.FG_SECONDARY,
                        font=FONT_SMALL, relief="flat", borderwidth=0)
        style.map("Treeview",
                  background=[("selected", _th.BG_SELECTED)],
                  foreground=[("selected", _th.FG_PRIMARY)])
        style.map("Treeview.Heading", background=[("active", _th.BG_CARD)])

        headers = {"date": "Date", "merchant": "Merchant", "category": "Category",
                   "card": "Card", "amount": "Amount"}
        widths   = {"date": 100, "merchant": 200, "category": 160, "card": 130, "amount": 130}
        anchors  = {"date": "w", "merchant": "w", "category": "w", "card": "w", "amount": "e"}

        for col in columns:
            self._tree.heading(col, text=headers[col],
                               command=lambda c=col: self.on_sort(c))
            self._tree.column(col, width=widths[col], anchor=anchors[col])

        self._tree.tag_configure("even", background=_th.BG_PANEL)
        self._tree.tag_configure("odd",  background=_th.BG_ROW_ALT)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        self._tree.bind("<Double-1>", self._on_row_double_click)

    def _build_action_bar(self) -> None:
        bar = tk.Frame(self, bg=_th.BG_MAIN)
        bar.pack(fill="x", padx=24, pady=(0, 10))
        self._row_count_label = tk.Label(bar, text="", bg=_th.BG_MAIN,
                                         fg=_th.FG_SECONDARY, font=FONT_SMALL)
        self._row_count_label.pack(side="left")
        tk.Button(bar, text="🗑 Delete", bg=_th.BG_CARD, fg=_th.FG_RED,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._on_delete_clicked).pack(side="right")

    # ── Refresh helpers ─────────────────────────────────────────────────────

    def _refresh_stats(self, txns: List[Transaction], card_totals: Dict[str, float]) -> None:
        for w in self._stats_frame.winfo_children():
            w.destroy()

        stats = [
            ("Transactions", str(len(txns)),                              _th.FG_BLUE),
            ("Avg / txn",    BusinessLogic.fmt_idr(BusinessLogic.average(txns)), _th.FG_SECONDARY),
            ("Highest",      BusinessLogic.fmt_idr(BusinessLogic.highest(txns)), _th.FG_RED),
        ]
        for card in CARDS:
            stats.append((card, BusinessLogic.fmt_idr(card_totals.get(card, 0)), _th.FG_GREEN))

        for label, value, color in stats:
            box = tk.Frame(self._stats_frame, bg=_th.BG_PANEL, padx=14, pady=8)
            box.pack(side="left", padx=(0, 8), pady=4)
            tk.Label(box, text=label, bg=_th.BG_PANEL, fg=_th.FG_SECONDARY, font=FONT_SMALL).pack(anchor="w")
            tk.Label(box, text=value, bg=_th.BG_PANEL, fg=color,         font=FONT_HEADING).pack(anchor="w")

    def _refresh_categories(self, top_cats: List[Tuple[str, float]]) -> None:
        for w in self._cat_frame.winfo_children():
            w.destroy()
        tk.Label(self._cat_frame, text="Top Categories:", bg=_th.BG_MAIN,
                 fg=_th.FG_SECONDARY, font=FONT_SMALL).pack(side="left")
        for cat, amt in top_cats:
            chip = tk.Frame(self._cat_frame, bg=_th.BG_CARD, padx=8, pady=4)
            chip.pack(side="left", padx=(6, 0))
            tk.Label(chip, text=f"{cat.split()[0]}  {BusinessLogic.fmt_idr(amt)}",
                     bg=_th.BG_CARD, fg=_th.FG_PRIMARY, font=FONT_SMALL).pack()

    @staticmethod
    def _fmt_date(iso: str) -> str:
        """Convert YYYY-MM-DD to DD-MM-YYYY."""
        try:
            y, m, d = iso.split("-")
            return f"{d}-{m}-{y}"
        except Exception:
            return iso

    def _refresh_table(self, txns: List[Transaction]) -> None:
        self._txn_map = {t.id: t for t in txns}
        for row in self._tree.get_children():
            self._tree.delete(row)
        for i, t in enumerate(txns):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=str(t.id),
                              values=(self._fmt_date(t.date), t.merchant, t.category,
                                      t.card, BusinessLogic.fmt_idr(t.amount)),
                              tags=(tag,))

    # ── Events ──────────────────────────────────────────────────────────────

    def _on_row_double_click(self, _event: tk.Event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        tid  = int(sel[0])
        vals = self._tree.item(sel[0], "values")
        self._open_category_editor(tid, vals)

    def _open_category_editor(self, tid: int, vals: tuple) -> None:
        from models import CATEGORIES
        dlg = tk.Toplevel(self)
        dlg.title("Edit Category")
        dlg.configure(bg=_th.BG_PANEL)
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"360x280+{(sw-360)//2}+{(sh-280)//2}")
        dlg.grab_set()
        dlg.focus_force()

        # Transaction info
        tk.Label(dlg, text="Edit Category", bg=_th.BG_PANEL,
                 fg=_th.FG_PRIMARY, font=FONT_HEADING).pack(pady=(18, 4))
        info = tk.Frame(dlg, bg=_th.BG_CARD, padx=14, pady=12)
        info.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(info, text=vals[1], bg=_th.BG_CARD, fg=_th.FG_PRIMARY,
                 font=FONT_HEADING, anchor="w").pack(fill="x")
        tk.Label(info, text=f"{vals[0]}  ·  {vals[4]}", bg=_th.BG_CARD,
                 fg=_th.FG_SECONDARY, font=FONT_BODY, anchor="w").pack(fill="x")

        # Category dropdown
        tk.Label(dlg, text="Category", bg=_th.BG_PANEL, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL).pack(anchor="w", padx=24)
        cat_var = tk.StringVar(value=vals[2])
        ttk.Combobox(dlg, textvariable=cat_var, values=CATEGORIES,
                     state="readonly", font=FONT_BODY
                     ).pack(fill="x", padx=24, pady=(4, 18))

        def save():
            if self.on_category_changed:
                self.on_category_changed(tid, cat_var.get())
            dlg.destroy()

        btn = tk.Label(dlg, text="Save", bg=_th.FG_BLUE, fg=_th.FG_PRIMARY,
                       font=FONT_HEADING, padx=20, pady=8, cursor="hand2")
        btn.pack()
        btn.bind("<Button-1>", lambda e: save())
        btn.bind("<Enter>",    lambda e: btn.config(bg="#0060cc"))
        btn.bind("<Leave>",    lambda e: btn.config(bg=_th.FG_BLUE))
        dlg.bind("<Return>",   lambda e: save())

    def _open_category_editor(self, tid: int, vals: tuple) -> None:
        from models import CATEGORIES
        import views.theme as _th
        from views.theme import FONT_HEADING, FONT_SMALL, FONT_BODY

        dlg = tk.Toplevel(self)
        dlg.title("Edit Category")
        dlg.configure(bg=_th.BG_PANEL)
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.focus_force()

        # Center
        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"360x280+{(sw-360)//2}+{(sh-280)//2}")

        # Header
        tk.Label(dlg, text="Edit Category", bg=_th.BG_PANEL,
                 fg=_th.FG_PRIMARY, font=FONT_HEADING).pack(pady=(18, 4))

        # Transaction info
        info = tk.Frame(dlg, bg=_th.BG_CARD, padx=14, pady=12)
        info.pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(info, text=vals[1], bg=_th.BG_CARD, fg=_th.FG_PRIMARY,
                 font=FONT_HEADING, anchor="w").pack(fill="x")
        tk.Label(info, text=f"{vals[0]}  ·  {vals[4]}", bg=_th.BG_CARD,
                 fg=_th.FG_SECONDARY, font=FONT_BODY, anchor="w").pack(fill="x")

        # Category dropdown
        tk.Label(dlg, text="Category", bg=_th.BG_PANEL, fg=_th.FG_SECONDARY,
                 font=FONT_SMALL).pack(anchor="w", padx=24)
        cat_var = tk.StringVar(value=vals[2])
        combo = tk.ttk.Combobox(dlg, textvariable=cat_var, values=CATEGORIES,
                                 state="readonly", font=FONT_BODY)
        combo.pack(fill="x", padx=24, pady=(4, 18))

        def save():
            new_cat = cat_var.get()
            if self.on_category_changed:
                self.on_category_changed(tid, new_cat)
            dlg.destroy()

        btn = tk.Label(dlg, text="Save", bg=_th.FG_BLUE, fg=_th.FG_PRIMARY,
                       font=FONT_HEADING, padx=20, pady=8, cursor="hand2")
        btn.pack()
        btn.bind("<Button-1>", lambda e: save())
        btn.bind("<Enter>",    lambda e: btn.config(bg="#0060cc"))
        btn.bind("<Leave>",    lambda e: btn.config(bg=_th.FG_BLUE))
        dlg.bind("<Return>",   lambda e: save())

    def _on_delete_clicked(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        if messagebox.askyesno("Delete", "Delete this transaction?", parent=self):
            self.on_delete(tid)
            