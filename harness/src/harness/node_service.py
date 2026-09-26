from pathlib import Path


def live_strategy():
    path = Path("/state/strategy.conf")
    return path.read_text().rstrip("\n") if path.exists() else ""
