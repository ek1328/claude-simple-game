"""
views/theme.py
--------------
Central place for all colours and fonts used across views.
Change a value here and it updates everywhere.
"""

import platform

# ── Colours ────────────────────────────────────────────────────────────────
BG_MAIN      = "#1c1c1e"
BG_SIDEBAR   = "#1c1c1e"
BG_PANEL     = "#2c2c2e"
BG_CARD      = "#3a3a3c"
BG_SELECTED  = "#1a3a5c"
BG_HEADER    = "#2c2c2e"
BG_ROW_ALT   = "#323234"

FG_PRIMARY   = "#ffffff"
FG_SECONDARY = "#8e8e93"
FG_GREEN     = "#32d74b"
FG_RED       = "#ff453a"
FG_BLUE      = "#0a84ff"


# ── Fonts ──────────────────────────────────────────────────────────────────
# if platform.system() == "Darwin":
#     FONT_TITLE   = ("SF Pro Display", 22, "bold")
#     FONT_HEADING = ("SF Pro Display", 13, "bold")
#     FONT_BODY    = ("SF Pro Text", 12)
#     FONT_SMALL   = ("SF Pro Text", 10)
# else:
#     FONT_TITLE   = ("Segoe UI", 20, "bold")
#     FONT_HEADING = ("Segoe UI", 12, "bold")
#     FONT_BODY    = ("Segoe UI", 11)
#     FONT_SMALL   = ("Segoe UI", 9)


# ── Fonts ──────────────────────────────────────────────────────────────────
if platform.system() == "Darwin":
    FONT_TITLE   = ("SF Pro Display", 24, "bold")  # month title + total
    FONT_HEADING = ("SF Pro Display", 15, "bold")  # section headers, buttons
    FONT_BODY    = ("SF Pro Text",    14)           # transaction table rows
    FONT_SMALL   = ("SF Pro Text",    12)           # dates, labels, stat boxes
else:
    FONT_TITLE   = ("Segoe UI", 24, "bold")
    FONT_HEADING = ("Segoe UI", 15, "bold")
    FONT_BODY    = ("Segoe UI", 14)
    FONT_SMALL   = ("Segoe UI", 12)
 