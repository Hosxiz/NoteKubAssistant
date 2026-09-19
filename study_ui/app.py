"""
Wrapper to keep running `python app.py` in project root working.
It imports `app` object from `src.app` and runs it.
"""

import os

from src.app import app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
