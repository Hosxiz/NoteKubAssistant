"""
Wrapper to keep running `python app.py` in project root working.
It imports `app` object from `src.app` and runs it.
"""

from src.app import app


if __name__ == "__main__":
    app.run(debug=True)
