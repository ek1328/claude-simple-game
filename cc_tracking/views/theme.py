"""
views/theme.py
--------------
Central place for all colours and fonts.
Supports dark and light palettes — call apply(mode) to switch live.
"""

import platform
import tkinter as tk
from tkinter import ttk

# ── Font definitions ──────────────────────────────────────────────────────────
if platform.system() == "Darwin":
    FONT_TITLE   = ("SF Pro Display", 24, "bold")
    FONT_HEADING = ("SF Pro Display", 15, "bold")
    FONT_BODY    = ("SF Pro Text",    14)
    FONT_SMALL   = ("SF Pro Text",    12)
else:
    FONT_TITLE   = ("Segoe UI", 22, "bold")
    FONT_HEADING = ("Segoe UI", 14, "bold")
    FONT_BODY    = ("Segoe UI", 13)
    FONT_SMALL   = ("Segoe UI", 11)

# ── Palettes ──────────────────────────────────────────────────────────────────
_DARK = {
    "BG_MAIN":     "#1c1c1e",
    "BG_SIDEBAR":  "#1c1c1e",
    "BG_PANEL":    "#2c2c2e",
    "BG_CARD":     "#3a3a3c",
    "BG_SELECTED": "#1a3a5c",
    "BG_HEADER":   "#2c2c2e",
    "BG_ROW_ALT":  "#323234",
    "FG_PRIMARY":  "#ffffff",
    "FG_SECONDARY":"#8e8e93",
    "FG_GREEN":    "#32d74b",
    "FG_RED":      "#ff453a",
    "FG_BLUE":     "#0a84ff",
}

_LIGHT = {
    "BG_MAIN":     "#f2f2f7",
    "BG_SIDEBAR":  "#e5e5ea",
    "BG_PANEL":    "#ffffff",
    "BG_CARD":     "#e9e9eb",
    "BG_SELECTED": "#cce0ff",
    "BG_HEADER":   "#f2f2f7",
    "BG_ROW_ALT":  "#f5f5f7",
    "FG_PRIMARY":  "#000000",
    "FG_SECONDARY":"#6c6c70",
    "FG_GREEN":    "#248a3d",
    "FG_RED":      "#d70015",
    "FG_BLUE":     "#0071e3",
}

# ── Active palette (start dark) ───────────────────────────────────────────────
_current = "dark"

def _apply_palette(p: dict) -> None:
    import views.theme as _t
    for k, v in p.items():
        setattr(_t, k, v)

_apply_palette(_DARK)

# ── Public API ────────────────────────────────────────────────────────────────

def current_mode() -> str:
    return _current

def toggle() -> str:
    """Switch palette. Reload of view modules handled by caller."""
    global _current
    _current = "light" if _current == "dark" else "dark"
    _apply_palette(_DARK if _current == "dark" else _LIGHT)
    return _current

def _apply_ttk_style() -> None:
    """Re-apply ttk Treeview colours to match current palette."""
    import views.theme as _t
    style = ttk.Style()
    style.configure("Treeview",
                    background=_t.BG_PANEL,
                    foreground=_t.FG_PRIMARY,
                    fieldbackground=_t.BG_PANEL,
                    rowheight=30,
                    font=FONT_BODY,
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=_t.BG_HEADER,
                    foreground=_t.FG_SECONDARY,
                    font=FONT_SMALL,
                    relief="flat",
                    borderwidth=0)
    style.map("Treeview",
              background=[("selected", _t.BG_SELECTED)],
              foreground=[("selected", _t.FG_PRIMARY)])
    style.map("Treeview.Heading",
              background=[("active", _t.BG_CARD)])
    