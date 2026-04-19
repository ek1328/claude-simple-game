import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
from collections import defaultdict
import calendar

# ── Palette (macOS Stocks dark) ─────────────────────────────────────────────
BG_MAIN      = "#1c1c1e"
BG_SIDEBAR   = "#1c1c1e"
BG_PANEL     = "#2c2c2e"
BG_CARD      = "#3a3a3c"
BG_SELECTED  = "#1a3a5c"
BG_HEADER    = "#2c2c2e"
BG_ROW_ALT  = "#323234"

FG_PRIMARY   = "#ffffff"
FG_SECONDARY = "#8e8e93"
FG_GREEN     = "#32d74b"
FG_RED       = "#ff453a"
FG_BLUE      = "#0a84ff"
FG_ACCENT    = "#0a84ff"

FONT_TITLE   = ("SF Pro Display", 22, "bold")
FONT_HEADING = ("SF Pro Display", 13, "bold")
FONT_BODY    = ("SF Pro Text", 12)
FONT_SMALL   = ("SF Pro Text", 10)
FONT_MONO    = ("SF Mono", 11)

# Fallback fonts for non-Mac
import platform
if platform.system() != "Darwin":
    FONT_TITLE   = ("Segoe UI", 20, "bold")
    FONT_HEADING = ("Segoe UI", 12, "bold")
    FONT_BODY    = ("Segoe UI", 11)
    FONT_SMALL   = ("Segoe UI", 9)
    FONT_MONO    = ("Consolas", 10)

CARDS = ["BCA", "Panin", "Jenius"]
CATEGORIES = ["🍽️ Food & Dining", "🛒 Groceries", "⛽ Transport", "🛍️ Shopping",
              "🏥 Health", "✈️ Travel", "🎬 Entertainment", "💡 Utilities",
              "📱 Subscriptions", "🏠 Housing", "📚 Education", "💼 Other"]

DATA_FILE = os.path.join(os.path.expanduser("~"), "cc_spending_data.json")

# ── Data helpers ─────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
        # Re-seed if card names don't match current config
        cards_in_data = {t["card"] for t in data.get("transactions", [])}
        if cards_in_data and not cards_in_data.issubset(set(CARDS)):
            os.remove(DATA_FILE)
            return seed_data()
        return data
    return seed_data()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def seed_data():
    import random, math
    random.seed(42)
    data = {"transactions": []}
    today = datetime.today()
    descs = {
        "🍽️ Food & Dining":   ["Starbucks","GoFood Order","KFC","Pizza Hut","Sate Khas Senayan"],
        "🛒 Groceries":        ["Ranch Market","Transmart","Indomaret","Alfamart","Grand Lucky"],
        "⛽ Transport":        ["Grab Car","Gojek","MyPertamina","Parking CBD","Toll Gate"],
        "🛍️ Shopping":        ["Tokopedia","Shopee","H&M","Zara","Uniqlo"],
        "🏥 Health":           ["Apotik K24","Halodoc","RS Siloam","Lab Prodia","Gym Member"],
        "✈️ Travel":           ["Traveloka","AirAsia","Hotel Booking","Airbnb","KLIA2"],
        "🎬 Entertainment":    ["Netflix","Disney+","CGV Cinema","Spotify","Steam Game"],
        "💡 Utilities":        ["PLN Token","PAM Water","Indihome","Telkomsel","XL Axiata"],
        "📱 Subscriptions":    ["iCloud+","YouTube Premium","Canva Pro","Notion","Figma"],
        "🏠 Housing":          ["IPL Apartment","Kost Payment","IKEA","ACE Hardware","Mr. DIY"],
        "📚 Education":        ["Udemy Course","Coursera","Ruangguru","Buku Gramedia","Workshop"],
        "💼 Other":            ["ATM Withdrawal","Bank Transfer","Insurance","Donation","Gift"],
    }
    for m in range(6):
        month_date = today.replace(day=1) if m == 0 else \
            (today.replace(day=1).replace(month=today.month - m) if today.month > m
             else today.replace(day=1, month=12 + today.month - m, year=today.year - 1))
        days_in_month = calendar.monthrange(month_date.year, month_date.month)[1]
        for _ in range(random.randint(25, 45)):
            cat = random.choice(CATEGORIES)
            card = random.choice(CARDS)
            day = random.randint(1, days_in_month)
            amt = round(random.uniform(15000, 1_500_000) / 1000) * 1000
            data["transactions"].append({
                "id": len(data["transactions"]),
                "date": f"{month_date.year}-{month_date.month:02d}-{day:02d}",
                "card": card,
                "category": cat,
                "merchant": random.choice(descs[cat]),
                "amount": amt,
                "note": ""
            })
    save_data(data)
    return data

def get_month_key(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.year}-{d.month:02d}"

def fmt_idr(amount):
    return f"Rp {amount:,.0f}".replace(",", ".")

def month_label(key):
    y, m = key.split("-")
    return datetime(int(y), int(m), 1).strftime("%B %Y")

# ── Main App ─────────────────────────────────────────────────────────────────
class SpendingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("💳 Credit Card Spending Tracker")
        self.configure(bg=BG_MAIN)
        self.geometry("1180x740")
        self.minsize(900, 600)

        self.data = load_data()
        self.selected_month = None
        self.selected_card = tk.StringVar(value="All Cards")
        self.sort_col = "date"
        self.sort_asc = True

        self._build_ui()
        self._populate_sidebar()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self, bg=BG_SIDEBAR, height=52)
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="💳  Spending Tracker", bg=BG_SIDEBAR,
                 fg=FG_PRIMARY, font=FONT_HEADING).pack(side="left", padx=20, pady=14)

        btn_add = tk.Button(topbar, text="＋ Add Transaction", bg=FG_BLUE, fg="white",
                            font=FONT_SMALL, bd=0, padx=12, pady=5, cursor="hand2",
                            command=self.open_add_dialog, relief="flat")
        btn_add.pack(side="right", padx=16, pady=10)

        sep = tk.Frame(self, bg="#3a3a3c", height=1)
        sep.pack(fill="x")

        # Main panes
        paned = tk.PanedWindow(self, orient="horizontal", bg=BG_MAIN,
                               sashwidth=1, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # Left sidebar
        self.sidebar = tk.Frame(paned, bg=BG_SIDEBAR, width=240)
        paned.add(self.sidebar, minsize=200)

        # Right panel
        self.right = tk.Frame(paned, bg=BG_MAIN)
        paned.add(self.right, minsize=500)

        self._build_sidebar()
        self._build_right_panel()

    def _build_sidebar(self):
        # Search bar
        search_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR, pady=10)
        search_frame.pack(fill="x", padx=12)
        tk.Label(search_frame, text="🔍", bg=BG_SIDEBAR, fg=FG_SECONDARY,
                 font=FONT_BODY).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._populate_sidebar())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                font=FONT_BODY, bd=0, relief="flat")
        search_entry.pack(side="left", fill="x", expand=True, padx=(6,0), ipady=4)

        tk.Label(self.sidebar, text="MONTHLY OVERVIEW", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(6,4))

        sep = tk.Frame(self.sidebar, bg=BG_CARD, height=1)
        sep.pack(fill="x", padx=12)

        # Scrollable month list
        list_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        list_frame.pack(fill="both", expand=True)

        self.month_canvas = tk.Canvas(list_frame, bg=BG_SIDEBAR, bd=0,
                                      highlightthickness=0)
        sb = tk.Scrollbar(list_frame, orient="vertical",
                          command=self.month_canvas.yview)
        self.month_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.month_canvas.pack(side="left", fill="both", expand=True)

        self.month_list_frame = tk.Frame(self.month_canvas, bg=BG_SIDEBAR)
        self.month_canvas_window = self.month_canvas.create_window(
            (0, 0), window=self.month_list_frame, anchor="nw")
        self.month_list_frame.bind("<Configure>", self._on_list_configure)
        self.month_canvas.bind("<Configure>",
            lambda e: self.month_canvas.itemconfig(
                self.month_canvas_window, width=e.width))

        # Bottom total
        sep2 = tk.Frame(self.sidebar, bg=BG_CARD, height=1)
        sep2.pack(fill="x")
        self.sidebar_total = tk.Label(self.sidebar, text="", bg=BG_SIDEBAR,
                                      fg=FG_SECONDARY, font=FONT_SMALL, pady=8)
        self.sidebar_total.pack()

    def _on_list_configure(self, event):
        self.month_canvas.configure(scrollregion=self.month_canvas.bbox("all"))

    def _build_right_panel(self):
        # Header
        hdr = tk.Frame(self.right, bg=BG_MAIN, pady=18)
        hdr.pack(fill="x", padx=24)

        self.title_label = tk.Label(hdr, text="Select a month →", bg=BG_MAIN,
                                    fg=FG_PRIMARY, font=FONT_TITLE, anchor="w")
        self.title_label.pack(side="left", anchor="s")

        self.total_label = tk.Label(hdr, text="", bg=BG_MAIN,
                                    fg=FG_PRIMARY, font=("SF Pro Display" if platform.system()=="Darwin" else "Segoe UI", 22, "bold"), anchor="e")
        self.total_label.pack(side="right", anchor="s")

        # Stats row
        self.stats_frame = tk.Frame(self.right, bg=BG_MAIN)
        self.stats_frame.pack(fill="x", padx=24, pady=(0, 12))

        # Card filter
        filter_frame = tk.Frame(self.right, bg=BG_MAIN)
        filter_frame.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(filter_frame, text="Card:", bg=BG_MAIN, fg=FG_SECONDARY,
                 font=FONT_SMALL).pack(side="left")
        for label in ["All Cards"] + CARDS:
            short = label.split()[0] if label != "All Cards" else "All Cards"
            rb = tk.Radiobutton(filter_frame, text=short, variable=self.selected_card,
                                value=label, bg=BG_MAIN, fg=FG_SECONDARY,
                                selectcolor=BG_MAIN, activebackground=BG_MAIN,
                                activeforeground=FG_BLUE, font=FONT_SMALL,
                                indicatoron=False, relief="flat", padx=8, pady=3,
                                command=self._refresh_right)
            rb.pack(side="left", padx=(6,0))

        sep = tk.Frame(self.right, bg=BG_CARD, height=1)
        sep.pack(fill="x", padx=24, pady=(0,8))

        # Category breakdown row
        self.cat_frame = tk.Frame(self.right, bg=BG_MAIN)
        self.cat_frame.pack(fill="x", padx=24, pady=(0, 10))

        sep2 = tk.Frame(self.right, bg=BG_CARD, height=1)
        sep2.pack(fill="x", padx=24, pady=(0,8))

        # Transaction table
        tbl_frame = tk.Frame(self.right, bg=BG_MAIN)
        tbl_frame.pack(fill="both", expand=True, padx=24, pady=(0,16))

        columns = ("date", "merchant", "category", "card", "amount")
        self.tree = ttk.Treeview(tbl_frame, columns=columns, show="headings",
                                 height=18, selectmode="browse")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=BG_PANEL, foreground=FG_PRIMARY,
                        fieldbackground=BG_PANEL, rowheight=30,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_HEADER, foreground=FG_SECONDARY,
                        font=FONT_SMALL, relief="flat", borderwidth=0)
        style.map("Treeview", background=[("selected", BG_SELECTED)],
                  foreground=[("selected", FG_PRIMARY)])
        style.map("Treeview.Heading", background=[("active", BG_CARD)])

        headers = {"date":"Date", "merchant":"Merchant", "category":"Category",
                   "card":"Card", "amount":"Amount"}
        widths   = {"date":100, "merchant":200, "category":160, "card":180, "amount":120}
        anchors  = {"date":"w", "merchant":"w", "category":"w", "card":"w", "amount":"e"}

        for col in columns:
            self.tree.heading(col, text=headers[col],
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths[col], anchor=anchors[col])

        self.tree.tag_configure("odd",  background=BG_PANEL)
        self.tree.tag_configure("even", background=BG_ROW_ALT)
        self.tree.tag_configure("neg",  foreground=FG_RED)
        self.tree.tag_configure("pos",  foreground=FG_GREEN)

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Bottom action bar
        action_bar = tk.Frame(self.right, bg=BG_MAIN)
        action_bar.pack(fill="x", padx=24, pady=(0,10))
        self.row_count_label = tk.Label(action_bar, text="", bg=BG_MAIN,
                                        fg=FG_SECONDARY, font=FONT_SMALL)
        self.row_count_label.pack(side="left")
        tk.Button(action_bar, text="🗑 Delete", bg=BG_CARD, fg=FG_RED,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._delete_selected).pack(side="right")

    # ── Sidebar population ────────────────────────────────────────────────────
    def _populate_sidebar(self):
        for w in self.month_list_frame.winfo_children():
            w.destroy()

        txns = self.data["transactions"]
        month_totals = defaultdict(float)
        for t in txns:
            month_totals[get_month_key(t["date"])] += t["amount"]

        query = self.search_var.get().lower()
        months = sorted(month_totals.keys(), reverse=True)
        if query:
            months = [m for m in months if query in month_label(m).lower()]

        total_all = sum(month_totals[m] for m in months)
        self.sidebar_total.config(text=f"Total shown: {fmt_idr(total_all)}")

        for i, mk in enumerate(months):
            total = month_totals[mk]
            is_sel = mk == self.selected_month
            bg = BG_SELECTED if is_sel else (BG_CARD if i % 2 == 0 else BG_SIDEBAR)

            row = tk.Frame(self.month_list_frame, bg=bg, cursor="hand2")
            row.pack(fill="x", padx=0, pady=1)

            inner = tk.Frame(row, bg=bg, padx=14, pady=10)
            inner.pack(fill="x")

            tk.Label(inner, text=month_label(mk), bg=bg, fg=FG_PRIMARY,
                     font=FONT_HEADING, anchor="w").pack(fill="x")

            bottom = tk.Frame(inner, bg=bg)
            bottom.pack(fill="x")

            # Mini bar chart
            canvas_w = 80
            bar = tk.Canvas(bottom, width=canvas_w, height=6, bg=bg,
                            bd=0, highlightthickness=0)
            bar.pack(side="left", pady=(4,0))
            max_t = max(month_totals.values()) if month_totals else 1
            pct = total / max_t
            fill_w = max(4, int(canvas_w * pct))
            bar.create_rectangle(0, 0, canvas_w, 6, fill=BG_CARD, outline="")
            bar.create_rectangle(0, 0, fill_w, 6,
                                 fill=FG_GREEN if total < 5_000_000 else FG_RED,
                                 outline="")

            tk.Label(bottom, text=fmt_idr(total), bg=bg, fg=FG_GREEN,
                     font=FONT_SMALL, anchor="e").pack(side="right")

            for w in [row, inner, bottom]:
                w.bind("<Button-1>", lambda e, m=mk: self._select_month(m))
            for child in inner.winfo_children():
                child.bind("<Button-1>", lambda e, m=mk: self._select_month(m))

        if not self.selected_month and months:
            self._select_month(months[0])

    def _select_month(self, mk):
        self.selected_month = mk
        self._populate_sidebar()
        self._refresh_right()

    # ── Right panel refresh ───────────────────────────────────────────────────
    def _refresh_right(self):
        if not self.selected_month:
            return
        mk = self.selected_month
        card_filter = self.selected_card.get()

        txns = [t for t in self.data["transactions"]
                if get_month_key(t["date"]) == mk
                and (card_filter == "All Cards" or t["card"] == card_filter)]

        total = sum(t["amount"] for t in txns)

        self.title_label.config(text=month_label(mk))
        self.total_label.config(text=fmt_idr(total), fg=FG_PRIMARY)

        # Stats cards
        for w in self.stats_frame.winfo_children():
            w.destroy()
        stats = [
            ("Transactions", str(len(txns)), FG_BLUE),
            ("Avg / txn", fmt_idr(total/len(txns)) if txns else "–", FG_SECONDARY),
            ("Highest", fmt_idr(max((t["amount"] for t in txns), default=0)), FG_RED),
        ]
        # Per-card breakdown
        for card in CARDS:
            c_txns = [t for t in txns if t["card"] == card]
            c_total = sum(t["amount"] for t in c_txns)
            short = card.split()[0]
            stats.append((short, fmt_idr(c_total), FG_GREEN))

        for label, val, color in stats:
            box = tk.Frame(self.stats_frame, bg=BG_PANEL, padx=14, pady=8)
            box.pack(side="left", padx=(0,8), pady=4)
            tk.Label(box, text=label, bg=BG_PANEL, fg=FG_SECONDARY,
                     font=FONT_SMALL).pack(anchor="w")
            tk.Label(box, text=val, bg=BG_PANEL, fg=color,
                     font=FONT_HEADING).pack(anchor="w")

        # Category mini-bars
        for w in self.cat_frame.winfo_children():
            w.destroy()
        cat_totals = defaultdict(float)
        for t in txns:
            cat_totals[t["category"]] += t["amount"]
        top_cats = sorted(cat_totals.items(), key=lambda x: -x[1])[:5]
        max_cat = top_cats[0][1] if top_cats else 1

        tk.Label(self.cat_frame, text="Top Categories:", bg=BG_MAIN,
                 fg=FG_SECONDARY, font=FONT_SMALL).pack(side="left")
        for cat, amt in top_cats:
            pct = int(60 * amt / max_cat)
            chip = tk.Frame(self.cat_frame, bg=BG_CARD, padx=8, pady=4)
            chip.pack(side="left", padx=(6,0))
            tk.Label(chip, text=f"{cat.split()[0]}  {fmt_idr(amt)}",
                     bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL).pack()

        # Sort
        def sort_key(t):
            v = t.get(self.sort_col, "")
            return v if isinstance(v, str) else -v
        txns_sorted = sorted(txns, key=sort_key, reverse=not self.sort_asc)

        # Populate tree
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, t in enumerate(txns_sorted):
            tags = ["even" if i % 2 == 0 else "odd"]
            short_card = t["card"].split()[0] + " …" + t["card"][-4:] if len(t["card"]) > 12 else t["card"]
            self.tree.insert("", "end", iid=str(t["id"]),
                             values=(t["date"], t["merchant"], t["category"],
                                     t["card"].split()[0], fmt_idr(t["amount"])),
                             tags=tags)
        self.row_count_label.config(text=f"{len(txns)} transactions")

    def _sort_by(self, col):
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col
            self.sort_asc = True
        self._refresh_right()

    # ── Add transaction dialog ─────────────────────────────────────────────────
    def open_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Transaction")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("420x440")
        dlg.grab_set()

        fields = {}

        def row(label, widget_fn, **kw):
            fr = tk.Frame(dlg, bg=BG_PANEL)
            fr.pack(fill="x", padx=24, pady=6)
            tk.Label(fr, text=label, bg=BG_PANEL, fg=FG_SECONDARY,
                     font=FONT_SMALL, width=14, anchor="w").pack(side="left")
            w = widget_fn(fr, **kw)
            w.pack(side="left", fill="x", expand=True)
            return w

        tk.Label(dlg, text="New Transaction", bg=BG_PANEL, fg=FG_PRIMARY,
                 font=FONT_HEADING).pack(pady=(18,10))

        # Date
        date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        fields["date"] = row("Date (YYYY-MM-DD)",
            lambda p, **kw: tk.Entry(p, textvariable=date_var, bg=BG_CARD,
                fg=FG_PRIMARY, insertbackground=FG_PRIMARY, font=FONT_BODY,
                bd=0, relief="flat", **kw))

        # Merchant
        merch_var = tk.StringVar()
        fields["merchant"] = row("Merchant",
            lambda p, **kw: tk.Entry(p, textvariable=merch_var, bg=BG_CARD,
                fg=FG_PRIMARY, insertbackground=FG_PRIMARY, font=FONT_BODY,
                bd=0, relief="flat", **kw))

        # Amount
        amt_var = tk.StringVar()
        fields["amount"] = row("Amount (Rp)",
            lambda p, **kw: tk.Entry(p, textvariable=amt_var, bg=BG_CARD,
                fg=FG_PRIMARY, insertbackground=FG_PRIMARY, font=FONT_BODY,
                bd=0, relief="flat", **kw))

        # Card
        card_var = tk.StringVar(value=CARDS[0])
        row("Credit Card",
            lambda p, **kw: ttk.Combobox(p, textvariable=card_var,
                values=CARDS, state="readonly", font=FONT_BODY, **kw))

        # Category
        cat_var = tk.StringVar(value=CATEGORIES[0])
        row("Category",
            lambda p, **kw: ttk.Combobox(p, textvariable=cat_var,
                values=CATEGORIES, state="readonly", font=FONT_BODY, **kw))

        # Note
        note_var = tk.StringVar()
        fields["note"] = row("Note (optional)",
            lambda p, **kw: tk.Entry(p, textvariable=note_var, bg=BG_CARD,
                fg=FG_PRIMARY, insertbackground=FG_PRIMARY, font=FONT_BODY,
                bd=0, relief="flat", **kw))

        def submit():
            try:
                datetime.strptime(date_var.get(), "%Y-%m-%d")
                amt = float(amt_var.get().replace(".", "").replace(",", ""))
                if not merch_var.get().strip():
                    raise ValueError("Merchant required")
            except Exception as e:
                messagebox.showerror("Invalid Input", str(e), parent=dlg)
                return
            new_id = max((t["id"] for t in self.data["transactions"]), default=0) + 1
            self.data["transactions"].append({
                "id": new_id,
                "date": date_var.get(),
                "card": card_var.get(),
                "category": cat_var.get(),
                "merchant": merch_var.get().strip(),
                "amount": amt,
                "note": note_var.get()
            })
            save_data(self.data)
            dlg.destroy()
            self._populate_sidebar()
            self._refresh_right()

        tk.Button(dlg, text="Add Transaction", bg=FG_BLUE, fg="white",
                  font=FONT_HEADING, bd=0, relief="flat", padx=20, pady=8,
                  cursor="hand2", command=submit).pack(pady=18)

    # ── Row actions ───────────────────────────────────────────────────────────
    def _on_row_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        txn = next((t for t in self.data["transactions"] if t["id"] == tid), None)
        if txn:
            messagebox.showinfo("Transaction Detail",
                f"Date:      {txn['date']}\n"
                f"Merchant:  {txn['merchant']}\n"
                f"Category:  {txn['category']}\n"
                f"Card:      {txn['card']}\n"
                f"Amount:    {fmt_idr(txn['amount'])}\n"
                f"Note:      {txn.get('note','–')}", parent=self)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        if messagebox.askyesno("Delete", "Delete this transaction?", parent=self):
            self.data["transactions"] = [
                t for t in self.data["transactions"] if t["id"] != tid]
            save_data(self.data)
            self._populate_sidebar()
            self._refresh_right()

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SpendingApp()
    app.mainloop()
    