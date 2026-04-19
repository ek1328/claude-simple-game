"""
data.py
-------
DataManager handles all persistence (JSON file I/O).
No UI code lives here. No sample data is seeded — the app starts empty.
"""

import json
import os
from typing import List

from models import Transaction, CARDS

# Store data next to the running script, inside a "Data" subfolder
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "Data")
os.makedirs(_DATA_DIR, exist_ok=True)   # create Data/ if it doesn't exist yet
DATA_FILE = os.path.join(_DATA_DIR, "cc_spending_data.json")


class DataManager:
    """Responsible for loading, saving, and seeding transaction data."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self._transactions: List[Transaction] = []

    # ── Public API ─────────────────────────────────────────────────────────

    def load(self) -> List[Transaction]:
        """Load transactions from disk. Returns empty list if no data file exists."""
        if os.path.exists(self.filepath):
            with open(self.filepath) as f:
                raw = json.load(f)
            txns = [Transaction.from_dict(d) for d in raw.get("transactions", [])]
            if self._cards_are_stale(txns):
                # Card names changed — wipe stale data and start fresh
                os.remove(self.filepath)
                txns = []
        else:
            txns = []

        self._transactions = txns
        return self._transactions

    def save(self) -> None:
        """Persist current transactions to disk."""
        payload = {"transactions": [t.to_dict() for t in self._transactions]}
        with open(self.filepath, "w") as f:
            json.dump(payload, f, indent=2)

    def add(self, txn: Transaction) -> None:
        self._transactions.append(txn)
        self.save()

    def delete(self, txn_id: int) -> None:
        self._transactions = [t for t in self._transactions if t.id != txn_id]
        self.save()

    def next_id(self) -> int:
        if not self._transactions:
            return 1
        return max(t.id for t in self._transactions) + 1

    @property
    def transactions(self) -> List[Transaction]:
        return self._transactions

    # ── Private helpers ────────────────────────────────────────────────────

    def _cards_are_stale(self, txns: List[Transaction]) -> bool:
        cards_in_data = {t.card for t in txns}
        return bool(cards_in_data) and not cards_in_data.issubset(set(CARDS))
    
    