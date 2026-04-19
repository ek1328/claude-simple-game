"""
main.py
-------
Entry point. Run this file to launch the app:

    python main.py
"""

import sys
import os

# Ensure the project root is always on sys.path,
# regardless of where Python is invoked from.
#ROOT = os.path.dirname(os.path.abspath(__file__))
#if ROOT not in sys.path:
#    sys.path.insert(0, ROOT)

# Make sure sibling modules (models, data, logic) are importable
sys.path.insert(0, os.path.dirname(__file__))


from views.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()

