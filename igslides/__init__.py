"""igslides — generate Fortune University Instagram carousel slides from JSON.

Two styles are supported:
  * "mythos"  — the flashy, dark, red/white all-caps "AI facts" style
  * "twitter" — the tweet-screenshot style (white card + verified badge)

Usage:
    python -m igslides content/example_mythos.json
    python -m igslides content/            # render every *.json in a folder
"""

__version__ = "0.1.0"
