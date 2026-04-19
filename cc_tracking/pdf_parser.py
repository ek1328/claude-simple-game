"""
pdf_parser.py
-------------
Parses credit card PDF statements for BCA, Panin, and Jenius.

Each bank has a different statement layout, so there is one parser class
per bank plus a top-level `parse_statement(filepath)` that auto-detects
the bank and returns a list of ParsedTransaction dicts.

ParsedTransaction shape:
    {
        "date":     "YYYY-MM-DD",
        "merchant": str,
        "amount":   float,       # positive = debit/spending
        "card":     str,         # bank name
        "raw":      str,         # original line, useful for debugging
    }
"""

import re
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber is required: pip install pdfplumber")


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class ParsedTransaction:
    date:     str
    merchant: str
    amount:   float
    card:     str
    raw:      str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_text(filepath: str) -> str:
    """Extract all text from a PDF, page by page."""
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def _parse_amount(raw: str) -> Optional[float]:
    """
    Convert Indonesian/international number strings to float.
    Handles: 1.234.567,89  |  1,234,567.89  |  1234567
    Returns None if unparseable.
    """
    s = raw.strip().lstrip("Rp").strip().replace(" ", "")
    # Indonesian format: dots as thousands, comma as decimal
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        # Western format: commas as thousands, dot as decimal
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_date(day: str, month: str, year: str = None) -> Optional[str]:
    """
    Build an ISO date string from parts.
    month can be a number or Indonesian/English month name.
    """
    MONTHS = {
        "jan": 1,  "feb": 2,  "mar": 3,  "apr": 4,
        "mei": 5,  "may": 5,  "jun": 6,  "jul": 7,
        "agu": 8,  "aug": 8,  "sep": 9,  "okt": 10, "oct": 10,
        "nov": 11, "des": 12, "dec": 12,
    }
    try:
        m = int(month) if month.isdigit() else MONTHS.get(month[:3].lower())
        if not m:
            return None
        y = int(year) if year else datetime.today().year
        if y < 100:
            y += 2000
        return f"{y:04d}-{m:02d}-{int(day):02d}"
    except Exception:
        return None


# ── Bank Parsers ──────────────────────────────────────────────────────────────

class _BCAParser:
    """
    BCA credit card statement parser.

    Real BCA Visa statement format (from pdfplumber extraction):

        DD-MMM  DD-MMM  MERCHANT [CITY] [CC]  AMOUNT  [CR]

    Amount uses DOTS as thousands separator: 1.224.700
    Foreign currency transactions have a continuation line below (ignored):
        17-MAR 18-MAR CLAUDE.AI SUBSCRIPTION ANTHROPIC.COMUS 346.825
        (USD 20,00 X 17.341,25)                               <- skip this line

    Statement date (e.g. "03 APRIL 2026") is used to resolve the year.
    """

    CARD_NAME = "BCA"

    MONTH_MAP = {
        "jan":1, "feb":2, "mar":3, "apr":4, "mei":5, "may":5,
        "jun":6, "jul":7, "agu":8, "aug":8, "sep":9,
        "okt":10,"oct":10,"nov":11,"des":12,"dec":12,
    }

    # Main transaction line: DD-MMM DD-MMM MERCHANT AMOUNT [CR]
    # BCA amount format: dots as thousands separator e.g. 1.224.700
    _RE_TXN = re.compile(
        r"^(\d{2}-[A-Z]{3})\s+"             # txn date DD-MMM
        r"\d{2}-[A-Z]{3}\s+"               # posting date (ignored)
        r"(.+?)\s+"                          # merchant + trailing noise
        r"(\d{1,3}(?:\.\d{3})+)"           # amount: dots-as-thousands e.g. 1.224.700
        r"(\s+CR)?\s*$",                    # optional CR
        re.IGNORECASE,
    )

    # Statement date: "03 APRIL 2026" or "03 APR 2026"
    _RE_STMT_DATE = re.compile(
        r"(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember"
        r"|Jan|Feb|Mar|Apr|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)\s+(\d{4})",
        re.IGNORECASE,
    )

    # Continuation lines with foreign currency breakdown — skip these
    _RE_CONT = re.compile(r"^\((?:USD|SGD|MYR|EUR|GBP|AUD|JPY|HKD)", re.IGNORECASE)

    # Trailing 2-letter country code to strip from merchant
    _RE_COUNTRY = re.compile(r"\s+[A-Z]{2}\s*$")

    def parse(self, text: str) -> List[ParsedTransaction]:
        stmt_year, stmt_month = self._detect_statement_date(text)
        results = []
        lines = text.splitlines()

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip foreign currency continuation lines
            if self._RE_CONT.match(line):
                continue

            m = self._RE_TXN.match(line)
            if not m:
                continue

            txn_date_str, merchant_raw, amount_str, cr = m.groups()
            if cr:
                continue  # skip payments and refunds

            # Resolve date
            day_str, mon_str = txn_date_str.split("-")
            month_num = self.MONTH_MAP.get(mon_str[:3].lower(), 1)
            year = stmt_year if month_num <= stmt_month else stmt_year - 1
            date = f"{year}-{month_num:02d}-{int(day_str):02d}"

            # Parse amount: remove dots (thousands separator)
            amount = float(amount_str.replace(".", ""))
            if amount < 100:
                continue

            merchant = self._clean_merchant(merchant_raw)
            results.append(ParsedTransaction(
                date=date, merchant=merchant,
                amount=amount, card=self.CARD_NAME, raw=line,
            ))

        return results

    def _detect_statement_date(self, text: str):
        """Return (year, month_num) from the statement header date."""
        FULL_MONTHS = {
            "januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
            "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12,
        }
        m = self._RE_STMT_DATE.search(text)
        if m:
            _, month_str, year_str = m.groups()
            month_num = (FULL_MONTHS.get(month_str.lower())
                         or self.MONTH_MAP.get(month_str[:3].lower(), 1))
            return int(year_str), month_num
        today = datetime.today()
        return today.year, today.month

    def _clean_merchant(self, raw: str) -> str:
        """Remove trailing 2-letter country code from merchant name."""
        return self._RE_COUNTRY.sub("", raw.strip()).strip()


class _PaninParser:
    """
    Panin Bank credit card statement parser.

    Real Panin Platinum statement format (from pdfplumber extraction):

        MM/DD  MM/DD  MERCHANT [CITY] [COUNTRY] [FOREIGN (CCY)]  Rp.  AMOUNT  [CR]

    Examples:
        03/16 03/17 POLISK-HO BATAM IDN Rp. 386,000
        03/18 03/19 HOT CRUSH KUALA LUMPUR MYS 74.80 (MYR) Rp. 329,444
        03/17 03/17 Payment at Panin BIFAS Rp. 31,000,000 CR   <- skip

    The statement date header (e.g. "13 APR 2026") is used to resolve the year
    for each MM/DD transaction date.
    """

    CARD_NAME = "Panin"

    # Main transaction line: MM/DD  MM/DD  <merchant stuff>  Rp.  AMOUNT  [CR]
    _RE_TXN = re.compile(
        r"^(\d{2}/\d{2})\s+"          # transaction date MM/DD
        r"\d{2}/\d{2}\s+"             # posting date (ignored)
        r"(.+?)\s+"                     # merchant + location (cleaned later)
        r"Rp\.\s*([\d,]+)"            # Rp. AMOUNT  (comma = thousands sep)
        r"(\s+CR)?\s*$",               # optional CR marker
        re.IGNORECASE,
    )

    # Detect statement date to infer year: "13 APR 2026" or "13 APR 2026"
    _RE_STMT_DATE = re.compile(
        r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)\s+(\d{4})",
        re.IGNORECASE,
    )

    # Noise patterns to strip from merchant name
    _COUNTRY_RE = re.compile(r"\s+(IDN|SGP|MYS|USD|SGD|GBP|EUR|AUS|HKG|JPN|KOR|THA|AUS)\b.*$", re.IGNORECASE)
    _FOREIGN_RE = re.compile(r"\s+[\d.]+\s*\([A-Z]{3}\)\s*", re.IGNORECASE)

    MONTH_MAP = {
        "jan":1,"feb":2,"mar":3,"apr":4,"mei":5,"may":5,
        "jun":6,"jul":7,"agu":8,"aug":8,"sep":9,
        "okt":10,"oct":10,"nov":11,"des":12,"dec":12,
    }

    def parse(self, text: str) -> List[ParsedTransaction]:
        # Step 1: detect statement year and month from header
        stmt_year, stmt_month = self._detect_statement_date(text)

        results = []
        for line in text.splitlines():
            line = line.strip()
            m = self._RE_TXN.match(line)
            if not m:
                continue
            txn_date_str, merchant_raw, amount_str, cr = m.groups()
            if cr:
                continue  # skip payments and credits

            # Parse MM/DD and resolve year
            mm, dd = txn_date_str.split("/")
            year = self._resolve_year(int(mm), stmt_year, stmt_month)
            date = f"{year}-{int(mm):02d}-{int(dd):02d}"

            merchant = self._clean_merchant(merchant_raw)
            amount   = float(amount_str.replace(",", ""))

            if amount < 100:
                continue  # skip tiny noise amounts

            results.append(ParsedTransaction(
                date=date, merchant=merchant,
                amount=amount, card=self.CARD_NAME, raw=line,
            ))
        return results

    def _detect_statement_date(self, text: str):
        """Return (year, month) from the statement print date."""
        m = self._RE_STMT_DATE.search(text)
        if m:
            _, month_str, year_str = m.groups()
            return int(year_str), self.MONTH_MAP.get(month_str[:3].lower(), 1)
        today = datetime.today()
        return today.year, today.month

    def _resolve_year(self, txn_month: int, stmt_year: int, stmt_month: int) -> int:
        """
        If the transaction month is greater than the statement month,
        the transaction belongs to the previous year
        (e.g. statement is APR 2026 but txn is DEC -> DEC 2025).
        """
        if txn_month > stmt_month:
            return stmt_year - 1
        return stmt_year

    def _clean_merchant(self, raw: str) -> str:
        """Remove foreign currency amounts and trailing country/city noise."""
        s = self._FOREIGN_RE.sub(" ", raw)   # strip "74.80 (MYR)"
        s = self._COUNTRY_RE.sub("", s)      # strip "KUALA LUMPUR MYS ..."
        return s.strip()


class _JeniusParser:
    """
    Jenius (BTPN) credit card / e-card statement parser.

    Jenius statements (exported from app or email) typically use:
        DD MMM YYYY  |  MERCHANT  |  IDR AMOUNT
    or CSV-like layout with pipe/tab delimiters.
    """

    CARD_NAME = "Jenius"

    # Pipe-delimited or spaced
    _RE = re.compile(
        r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)\s+(\d{4})"
        r"[\s|]+"
        r"(.+?)"
        r"[\s|]+"
        r"(?:IDR\s*)?([\d.,]+)"
        r"(\s+CR)?",
        re.IGNORECASE,
    )

    def parse(self, text: str) -> List[ParsedTransaction]:
        results = []
        for line in text.splitlines():
            m = self._RE.search(line)
            if not m:
                continue
            day, month, year, merchant, amount_str, cr = m.groups()
            if cr:
                continue
            amount = _parse_amount(amount_str)
            date   = _normalize_date(day, month, year)
            if not amount or not date:
                continue
            results.append(ParsedTransaction(
                date=date, merchant=merchant.strip(),
                amount=amount, card=self.CARD_NAME, raw=line,
            ))
        return results


# ── Generic fallback parser ───────────────────────────────────────────────────

class _GenericParser:
    """
    Fallback: tries common date + amount patterns regardless of bank.
    Used when the bank cannot be detected from the PDF text.
    """

    CARD_NAME = "Unknown"

    _RE = re.compile(
        r"(\d{1,2})[/\-\s]"
        r"(\d{1,2}|Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)[/\-\s]"
        r"(\d{2,4})\s+"
        r"(.+?)\s+"
        r"([\d.,]{4,})"
        r"(\s+CR)?",
        re.IGNORECASE,
    )

    def __init__(self, card_name: str = "Unknown"):
        self.CARD_NAME = card_name

    def parse(self, text: str) -> List[ParsedTransaction]:
        results = []
        for line in text.splitlines():
            m = self._RE.search(line)
            if not m:
                continue
            day, month, year, merchant, amount_str, cr = m.groups()
            if cr:
                continue
            amount = _parse_amount(amount_str)
            date   = _normalize_date(day, month, year)
            if not amount or not date or amount < 1000:
                continue
            results.append(ParsedTransaction(
                date=date, merchant=merchant.strip(),
                amount=amount, card=self.CARD_NAME, raw=line,
            ))
        return results


# ── Bank detection ────────────────────────────────────────────────────────────

def _detect_bank(text: str) -> str:
    """Guess the bank from keywords in the PDF text."""
    t = text.lower()
    if "bca" in t or "bank central asia" in t:
        return "BCA"
    if "panin" in t or "bank pan indonesia" in t:
        return "Panin"
    if "jenius" in t or "btpn" in t or "bank tabungan pensiunan" in t:
        return "Jenius"
    return "Unknown"


# ── Public API ────────────────────────────────────────────────────────────────

def parse_statement(filepath: str) -> tuple[str, str, List[ParsedTransaction]]:
    """
    Parse a credit card PDF statement.

    Returns:
        (bank_name, statement_month_key, list_of_ParsedTransaction)
        statement_month_key is "YYYY-MM" of the statement issue date.

    Raises:
        ValueError  if the file cannot be read or no transactions found.
        ImportError if pdfplumber is not installed.
    """
    if not os.path.exists(filepath):
        raise ValueError(f"File not found: {filepath}")

    text = _extract_text(filepath)
    if not text.strip():
        raise ValueError("Could not extract text from PDF. It may be scanned/image-based.")

    bank = _detect_bank(text)

    parsers = {
        "BCA":    _BCAParser(),
        "Panin":  _PaninParser(),
        "Jenius": _JeniusParser(),
    }

    parser = parsers.get(bank, _GenericParser(bank))
    transactions = parser.parse(text)

    # If the primary parser found nothing, try the generic fallback
    if not transactions and bank != "Unknown":
        transactions = _GenericParser(bank).parse(text)

    # Detect statement issue month from parser if available, else use today
    stmt_year, stmt_month = (
        parser._detect_statement_date(text)
        if hasattr(parser, "_detect_statement_date")
        else (datetime.today().year, datetime.today().month)
    )
    stmt_month_key = f"{stmt_year}-{stmt_month:02d}"

    return bank, stmt_month_key, transactions
