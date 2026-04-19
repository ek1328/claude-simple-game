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
from views.theme import *


class MainPanel(tk.Frame):

    def __init__(self, parent: tk.Widget,
                 on_sort: Callable[[str], None],
                 on_delete: Callable[[int], None],
                 on_card_filter_changed: Callable[[str], None],
                 on_search_changed: Callable[[str], None]):
        super().__init__(parent, bg=BG_MAIN)

        self.on_sort = on_sort
        self.on_delete = on_delete
        self.on_card_filter_changed = on_card_filter_changed
        self.on_search_changed = on_search_changed

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
        self._tree.tag_configure("hint", foreground=FG_SECONDARY)

    # ── Build ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        self._build_stats_row()
        self._build_card_filter()
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x", padx=24, pady=(0, 8))
        self._build_category_row()
        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x", padx=24, pady=(0, 8))
        self._build_table()
        self._build_action_bar()

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=BG_MAIN, pady=18)
        hdr.pack(fill="x", padx=24)
        self._title_label = tk.Label(hdr, text="Select a month →", bg=BG_MAIN,
                                     fg=FG_PRIMARY, font=FONT_TITLE, anchor="w")
        self._title_label.pack(side="left", anchor="s")
        self._total_label = tk.Label(hdr, text="", bg=BG_MAIN,
                                     fg=FG_PRIMARY, font=FONT_TITLE, anchor="e")
        self._total_label.pack(side="right", anchor="s")

    def _build_stats_row(self) -> None:
        self._stats_frame = tk.Frame(self, bg=BG_MAIN)
        self._stats_frame.pack(fill="x", padx=24, pady=(0, 12))

    def _build_card_filter(self) -> None:
        frame = tk.Frame(self, bg=BG_MAIN)
        frame.pack(fill="x", padx=24, pady=(0, 8))

        # Card filter buttons (left)
        tk.Label(frame, text="Card:", bg=BG_MAIN, fg=FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        for value in ["All Cards"] + CARDS:
            rb = tk.Radiobutton(
                frame, text=value, variable=self._card_var, value=value,
                bg=BG_MAIN, fg=FG_SECONDARY, selectcolor=BG_MAIN,
                activebackground=BG_MAIN, activeforeground=FG_BLUE,
                font=FONT_SMALL, indicatoron=False, relief="flat",
                padx=8, pady=3,
                command=lambda: self.on_card_filter_changed(self._card_var.get()),
            )
            rb.pack(side="left", padx=(6, 0))

        # Merchant search box (right)
        search_frame = tk.Frame(frame, bg=BG_CARD, padx=8, pady=4)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=BG_CARD, fg=FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                font=FONT_SMALL, bd=0, relief="flat", width=22)
        search_entry.pack(side="left", padx=(4, 0))
        # Clear button
        clear_btn = tk.Label(search_frame, text="✕", bg=BG_CARD, fg=FG_SECONDARY,
                             font=FONT_SMALL, cursor="hand2")
        clear_btn.pack(side="left", padx=(4, 0))
        clear_btn.bind("<Button-1>", lambda e: self._search_var.set(""))

        self._search_var.trace_add("write", lambda *_: self.on_search_changed(self._search_var.get()))

    def _build_category_row(self) -> None:
        self._cat_frame = tk.Frame(self, bg=BG_MAIN)
        self._cat_frame.pack(fill="x", padx=24, pady=(0, 10))

    def _build_table(self) -> None:
        frame = tk.Frame(self, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        columns = ("date", "merchant", "category", "card", "amount")
        self._tree = ttk.Treeview(frame, columns=columns, show="headings",
                                  height=18, selectmode="browse")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=BG_PANEL, foreground=FG_PRIMARY,
                        fieldbackground=BG_PANEL, rowheight=30,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_HEADER, foreground=FG_SECONDARY,
                        font=FONT_SMALL, relief="flat", borderwidth=0)
        style.map("Treeview",
                  background=[("selected", BG_SELECTED)],
                  foreground=[("selected", FG_PRIMARY)])
        style.map("Treeview.Heading", background=[("active", BG_CARD)])

        headers = {"date": "Date", "merchant": "Merchant", "category": "Category",
                   "card": "Card", "amount": "Amount"}
        widths   = {"date": 100, "merchant": 200, "category": 160, "card": 130, "amount": 130}
        anchors  = {"date": "w", "merchant": "w", "category": "w", "card": "w", "amount": "e"}

        for col in columns:
            self._tree.heading(col, text=headers[col],
                               command=lambda c=col: self.on_sort(c))
            self._tree.column(col, width=widths[col], anchor=anchors[col])

        self._tree.tag_configure("even", background=BG_PANEL)
        self._tree.tag_configure("odd",  background=BG_ROW_ALT)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        self._tree.bind("<Double-1>", self._on_row_double_click)

    def _build_action_bar(self) -> None:
        bar = tk.Frame(self, bg=BG_MAIN)
        bar.pack(fill="x", padx=24, pady=(0, 10))
        self._row_count_label = tk.Label(bar, text="", bg=BG_MAIN,
                                         fg=FG_SECONDARY, font=FONT_SMALL)
        self._row_count_label.pack(side="left")
        tk.Button(bar, text="🗑 Delete", bg=BG_CARD, fg=FG_RED,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._on_delete_clicked).pack(side="right")

    # ── Refresh helpers ─────────────────────────────────────────────────────

    def _refresh_stats(self, txns: List[Transaction], card_totals: Dict[str, float]) -> None:
        for w in self._stats_frame.winfo_children():
            w.destroy()

        stats = [
            ("Transactions", str(len(txns)),                              FG_BLUE),
            ("Avg / txn",    BusinessLogic.fmt_idr(BusinessLogic.average(txns)), FG_SECONDARY),
            ("Highest",      BusinessLogic.fmt_idr(BusinessLogic.highest(txns)), FG_RED),
        ]
        for card in CARDS:
            stats.append((card, BusinessLogic.fmt_idr(card_totals.get(card, 0)), FG_GREEN))

        for label, value, color in stats:
            box = tk.Frame(self._stats_frame, bg=BG_PANEL, padx=14, pady=8)
            box.pack(side="left", padx=(0, 8), pady=4)
            tk.Label(box, text=label, bg=BG_PANEL, fg=FG_SECONDARY, font=FONT_SMALL).pack(anchor="w")
            tk.Label(box, text=value, bg=BG_PANEL, fg=color,         font=FONT_HEADING).pack(anchor="w")

    def _refresh_categories(self, top_cats: List[Tuple[str, float]]) -> None:
        for w in self._cat_frame.winfo_children():
            w.destroy()
        tk.Label(self._cat_frame, text="Top Categories:", bg=BG_MAIN,
                 fg=FG_SECONDARY, font=FONT_SMALL).pack(side="left")
        for cat, amt in top_cats:
            chip = tk.Frame(self._cat_frame, bg=BG_CARD, padx=8, pady=4)
            chip.pack(side="left", padx=(6, 0))
            tk.Label(chip, text=f"{cat.split()[0]}  {BusinessLogic.fmt_idr(amt)}",
                     bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL).pack()

    @staticmethod
    def _fmt_date(iso: str) -> str:
        """Convert YYYY-MM-DD to DD-MM-YYYY."""
        try:
            y, m, d = iso.split("-")
            return f"{d}-{m}-{y}"
        except Exception:
            return iso

    def _refresh_table(self, txns: List[Transaction]) -> None:
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
        tid = int(sel[0])
        # Retrieve displayed values directly from tree
        vals = self._tree.item(sel[0], "values")
        messagebox.showinfo("Transaction Detail",
            f"Date:      {vals[0]}\n"
            f"Merchant:  {vals[1]}\n"
            f"Category:  {vals[2]}\n"
            f"Card:      {vals[3]}\n"
            f"Amount:    {vals[4]}",
            parent=self)

    def _on_delete_clicked(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        if messagebox.askyesno("Delete", "Delete this transaction?", parent=self):
            self.on_delete(tid)

