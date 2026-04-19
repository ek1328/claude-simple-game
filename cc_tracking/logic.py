"""
logic.py
--------
BusinessLogic handles all computation: filtering, sorting, aggregation.
No UI, no I/O — pure functions over Transaction lists.
"""

from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from models import Transaction


class BusinessLogic:
    """Stateless helper — all methods are pure functions."""

    # ── Filtering ──────────────────────────────────────────────────────────

    @staticmethod
    def filter_by_month(txns: List[Transaction], month_key: str) -> List[Transaction]:
        return [t for t in txns if t.month_key == month_key]

    @staticmethod
    def filter_by_card(txns: List[Transaction], card: Optional[str]) -> List[Transaction]:
        if not card or card == "All Cards":
            return txns
        return [t for t in txns if t.card == card]

    @staticmethod
    def filter_by_search(txns: List[Transaction], query: str) -> List[Transaction]:
        q = query.lower()
        return [t for t in txns
                if q in t.merchant.lower()
                or q in t.category.lower()
                or q in t.card.lower()]

    # ── Sorting ────────────────────────────────────────────────────────────

    @staticmethod
    def sort(txns: List[Transaction], col: str, ascending: bool) -> List[Transaction]:
        """Sort transactions by a named column.
        Default col 'id' preserves original statement insertion order."""
        key_map = {
            "id":       lambda t: t.id,
            "date":     lambda t: t.date,
            "merchant": lambda t: t.merchant.lower(),
            "category": lambda t: t.category,
            "card":     lambda t: t.card,
            "amount":   lambda t: t.amount,
        }
        key = key_map.get(col, lambda t: t.id)
        return sorted(txns, key=key, reverse=not ascending)

    # ── Aggregation ────────────────────────────────────────────────────────

    @staticmethod
    def total(txns: List[Transaction]) -> float:
        return sum(t.amount for t in txns)

    @staticmethod
    def average(txns: List[Transaction]) -> float:
        return BusinessLogic.total(txns) / len(txns) if txns else 0.0

    @staticmethod
    def highest(txns: List[Transaction]) -> float:
        return max((t.amount for t in txns), default=0.0)

    @staticmethod
    def totals_by_month(txns: List[Transaction]) -> Dict[str, float]:
        result: Dict[str, float] = defaultdict(float)
        for t in txns:
            result[t.month_key] += t.amount
        return dict(result)

    @staticmethod
    def totals_by_card(txns: List[Transaction]) -> Dict[str, float]:
        result: Dict[str, float] = defaultdict(float)
        for t in txns:
            result[t.card] += t.amount
        return dict(result)

    @staticmethod
    def totals_by_category(txns: List[Transaction]) -> Dict[str, float]:
        result: Dict[str, float] = defaultdict(float)
        for t in txns:
            result[t.category] += t.amount
        return dict(result)

    @staticmethod
    def top_categories(txns: List[Transaction], n: int = 5) -> List[Tuple[str, float]]:
        totals = BusinessLogic.totals_by_category(txns)
        return sorted(totals.items(), key=lambda x: -x[1])[:n]

    @staticmethod
    def sorted_months(txns: List[Transaction]) -> List[str]:
        """Return unique month keys sorted newest-first."""
        return sorted(BusinessLogic.totals_by_month(txns).keys(), reverse=True)

    # ── Formatting ─────────────────────────────────────────────────────────

    @staticmethod
    def fmt_idr(amount: float) -> str:
        return f"Rp {amount:,.0f}".replace(",", ".")

    @staticmethod
    def fmt_month(month_key: str) -> str:
        y, m = month_key.split("-")
        return datetime(int(y), int(m), 1).strftime("%B %Y")
    