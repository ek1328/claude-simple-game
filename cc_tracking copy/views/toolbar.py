# """
# views/toolbar.py
# ----------------
# Top bar with app title and the "+ Add Transaction" button.
# """

# import tkinter as tk
# from typing import Callable

# from views.theme import *


# class Toolbar(tk.Frame):

#     def __init__(self, parent: tk.Widget, on_add: Callable[[], None]):
#         super().__init__(parent, bg=BG_SIDEBAR, height=52)
#         self.pack_propagate(False)
#         self._build(on_add)

#     def _build(self, on_add: Callable[[], None]) -> None:
#         tk.Label(self, text="💳  Spending Tracker", bg=BG_SIDEBAR,
#                  fg=FG_PRIMARY, font=FONT_HEADING).pack(side="left", padx=20, pady=14)

#         # Use a Label-based button — macOS tk.Button ignores fg with flat relief
#         btn = tk.Label(self, text="+ Add Transaction", bg=FG_BLUE, fg=FG_PRIMARY,
#                        font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
#         btn.pack(side="right", padx=16, pady=10)
#         btn.bind("<Button-1>", lambda e: on_add())
#         btn.bind("<Enter>",    lambda e: btn.config(bg="#0060cc"))
#         btn.bind("<Leave>",    lambda e: btn.config(bg=FG_BLUE))

"""
views/toolbar.py
----------------
Top bar with app title, "+ Add Transaction" and "Upload Statement" buttons.
"""


import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

from views.theme import *


class Toolbar(tk.Frame):

    def __init__(self, parent: tk.Widget,
                 on_add: Callable[[], None],
                 on_upload: Callable[[str], None]):
        super().__init__(parent, bg=BG_SIDEBAR, height=52)
        self.pack_propagate(False)
        self._build(on_add, on_upload)

    def _build(self, on_add: Callable[[], None],
               on_upload: Callable[[str], None]) -> None:
        tk.Label(self, text="💳  Spending Tracker", bg=BG_SIDEBAR,
                 fg=FG_PRIMARY, font=FONT_HEADING).pack(side="left", padx=20, pady=14)

        # + Add Transaction button
        btn_add = tk.Label(self, text="+ Add Transaction", bg=FG_BLUE, fg=FG_PRIMARY,
                           font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_add.pack(side="right", padx=(0, 16), pady=10)
        btn_add.bind("<Button-1>", lambda e: on_add())
        btn_add.bind("<Enter>",    lambda e: btn_add.config(bg="#0060cc"))
        btn_add.bind("<Leave>",    lambda e: btn_add.config(bg=FG_BLUE))

        # Upload Statement button
        btn_upload = tk.Label(self, text="↑ Upload Statement", bg=BG_CARD, fg=FG_PRIMARY,
                              font=FONT_HEADING, padx=14, pady=6, cursor="hand2")
        btn_upload.pack(side="right", padx=(0, 8), pady=10)
        btn_upload.bind("<Button-1>", lambda e: self._pick_pdf(on_upload))
        btn_upload.bind("<Enter>",    lambda e: btn_upload.config(bg="#4a4a4c"))
        btn_upload.bind("<Leave>",    lambda e: btn_upload.config(bg=BG_CARD))

    def _pick_pdf(self, on_upload: Callable[[str], None]) -> None:
        path = filedialog.askopenfilename(
            title="Select Credit Card Statement",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            on_upload(path)
