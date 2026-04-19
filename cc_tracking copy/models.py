"""
models.py
---------
Pure data classes. No I/O, no UI, no logic — just structure.
"""

from dataclasses import dataclass, field
from datetime import datetime


CARDS = ["BCA", "Panin", "Jenius"]

CATEGORIES = [
    "🍽️ Food & Dining",
    "🛒 Groceries",
    "⛽ Transport",
    "🛍️ Shopping",
    "🏥 Health",
    "✈️ Travel",
    "🎬 Entertainment",
    "💡 Utilities",
    "📱 Subscriptions",
    "🏠 Housing",
    "📚 Education",
    "💼 Other",
]


@dataclass
class Transaction:
    id: int
    date: str             # ISO format: "YYYY-MM-DD" — original transaction date, never changed
    card: str
    category: str
    merchant: str
    amount: float
    note: str = ""
    statement_month: str = ""  # "YYYY-MM" — which statement period this belongs to

    # ── Convenience properties ─────────────────────────────────────────────

    @property
    def month_key(self) -> str:
        """Return 'YYYY-MM' used for sidebar grouping.
        If imported from a PDF, uses statement_month so all transactions
        from e.g. an April statement appear under April — regardless of
        whether individual transaction dates fall in March or April.
        Falls back to the transaction date month for manual entries."""
        return self.statement_month if self.statement_month else self.date[:7]

    @property
    def date_obj(self) -> datetime:
        return datetime.strptime(self.date, "%Y-%m-%d")

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "date":            self.date,
            "card":            self.card,
            "category":        self.category,
            "merchant":        self.merchant,
            "amount":          self.amount,
            "note":            self.note,
            "statement_month": self.statement_month,
        }

    @staticmethod
    def from_dict(d: dict) -> "Transaction":
        return Transaction(
            id=d["id"],
            date=d["date"],
            card=d["card"],
            category=d["category"],
            merchant=d["merchant"],
            amount=float(d["amount"]),
            note=d.get("note", ""),
            statement_month=d.get("statement_month", ""),
        )
    