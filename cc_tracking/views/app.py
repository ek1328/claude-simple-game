"""
views/app.py
------------
App controller (root Tk window).
Owns DataManager and BusinessLogic; wires up views and handles events.
This is the only file that "talks" to all layers.
"""

import sys, os
# Ensure project root (parent of views/) is on sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tkinter as tk

from data import DataManager
from logic import BusinessLogic
from models import Transaction
from views.toolbar import Toolbar
from views.sidebar import Sidebar
from views.main_panel import MainPanel
from views.add_dialog import AddDialog
from views.import_dialog import ImportDialog
from pdf_parser import parse_statement
from views.theme import BG_MAIN, BG_CARD
import views.theme as theme


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("💳 Credit Card Spending Tracker")
        self.configure(bg=BG_MAIN)
        self.minsize(900, 600)
        self._center_window(1180, 740)

        # ── Layers ─────────────────────────────────────────────────────────
        self._data    = DataManager()
        self._logic   = BusinessLogic()

        # ── State ──────────────────────────────────────────────────────────
        self._selected_month: str | None = None
        self._selected_card:  str        = "All Cards"
        self._search_query:   str        = ""
        self._sort_col:       str        = "id"
        self._sort_asc:       bool       = True

        # ── Load data ──────────────────────────────────────────────────────
        self._data.load()

        # ── Build UI ───────────────────────────────────────────────────────
        self._build_ui()

        # ── Initial render ─────────────────────────────────────────────────
        months = self._logic.sorted_months(self._data.transactions)
        if months:
            self._select_month(months[0])
        else:
            self._refresh_sidebar()

        # ── Bring window to front (fixes macOS background launch issue) ─────
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()


    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ── UI layout ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Top bar
        self._toolbar = Toolbar(self, on_add=self._open_add_dialog,
                              on_upload=self._on_upload_statement,
                              on_theme_toggle=self._on_theme_toggle)
        self._toolbar.pack(side="top", fill="x")

        tk.Frame(self, bg=BG_CARD, height=1).pack(fill="x")

        # Paned layout
        paned = tk.PanedWindow(self, orient="horizontal", bg=BG_MAIN,
                               sashwidth=1, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        self._sidebar = Sidebar(paned, on_month_selected=self._select_month)
        paned.add(self._sidebar, minsize=200)

        self._main_panel = MainPanel(
            paned,
            on_sort=self._on_sort,
            on_delete=self._on_delete,
            on_card_filter_changed=self._on_card_filter_changed,
            on_search_changed=self._on_search_changed,
            on_category_changed=self._on_category_changed,
        )
        paned.add(self._main_panel, minsize=500)

    # ── Event handlers ───────────────────────────────────────────────────────

    def _select_month(self, month_key: str) -> None:
        self._selected_month = month_key
        self._refresh_sidebar()
        self._refresh_main_panel()

    def _on_card_filter_changed(self, card: str) -> None:
        self._selected_card = card
        self._refresh_main_panel()

    def _on_search_changed(self, query: str) -> None:
        self._search_query = query
        self._refresh_main_panel()

    def _on_category_changed(self, txn_id: int, new_category: str) -> None:
        for txn in self._data.transactions:
            if txn.id == txn_id:
                txn.category = new_category
                break
        self._data.save()
        self._refresh_sidebar()
        self._refresh_main_panel()



    def _on_sort(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh_main_panel()

    def _on_delete(self, txn_id: int) -> None:
        self._data.delete(txn_id)
        self._refresh_sidebar()
        self._refresh_main_panel()

    def _on_upload_statement(self, filepath: str) -> None:
        from tkinter import messagebox
        try:
            bank, stmt_month_key, parsed = parse_statement(filepath)
        except Exception as exc:
            messagebox.showerror("Parse Error",
                f"Could not read the PDF statement:\n\n{exc}", parent=self)
            return

        if not parsed:
            messagebox.showwarning("No Transactions Found",
                "The parser could not find any transactions in this PDF.\n\n"
                "The statement format may differ from what is expected. "
                "Please add transactions manually.", parent=self)
            return

        ImportDialog(
            self,
            bank=bank,
            stmt_month_key=stmt_month_key,
            parsed=parsed,
            next_id_fn=self._data.next_id,
            on_import=self._on_bulk_import,
        )

    def _on_bulk_import(self, transactions: list) -> None:
        from tkinter import messagebox
        for txn in transactions:
            self._data.add(txn)
        # Jump to the month of the first imported transaction
        if transactions:
            self._select_month(transactions[0].month_key)

    def _open_add_dialog(self) -> None:
        AddDialog(self, next_id=self._data.next_id(),
                  on_submit=self._on_transaction_added,
                  selected_month=self._selected_month or "")

    def _on_transaction_added(self, txn: Transaction) -> None:
        # Force the transaction into the currently selected month
        if self._selected_month:
            txn.statement_month = self._selected_month
        self._data.add(txn)
        self._refresh_sidebar()
        self._refresh_main_panel()

    # ── Refresh helpers ──────────────────────────────────────────────────────

    def _on_theme_toggle(self) -> None:
        # Save state
        month = self._selected_month
        card  = self._selected_card
        sort  = self._sort_col
        asc   = self._sort_asc
        query = self._search_query

        # Switch palette
        theme.toggle()

        # Destroy and rebuild entire UI with fresh imports
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=theme.BG_MAIN)
        self._build_ui()

        # Restore state
        self._selected_month = month
        self._selected_card  = card
        self._sort_col       = sort
        self._sort_asc       = asc
        self._search_query   = query

        self._toolbar.update_theme_icon()
        self._refresh_sidebar()
        if month:
            self._refresh_main_panel()

    def _refresh_sidebar(self) -> None:
        month_totals = self._logic.totals_by_month(self._data.transactions)
        self._sidebar.refresh(month_totals, self._selected_month)

    def _refresh_main_panel(self) -> None:
        if not self._selected_month:
            self._main_panel.clear()
            return

        # Filter
        txns = self._logic.filter_by_month(self._data.transactions, self._selected_month)
        txns = self._logic.filter_by_card(txns, self._selected_card)
        if self._search_query.strip():
            q = self._search_query.lower()
            txns = [t for t in txns if q in t.merchant.lower()]

        # Sort
        txns = self._logic.sort(txns, self._sort_col, self._sort_asc)

        # Aggregate
        card_totals = self._logic.totals_by_card(txns)
        top_cats    = self._logic.top_categories(txns)
        month_label = self._logic.fmt_month(self._selected_month)

        self._main_panel.refresh(month_label, txns, card_totals, top_cats)

        