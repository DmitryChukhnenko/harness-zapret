"""Private, append-only blockcheck event channel, separate from raw server output."""

import json
import os
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path


def main():
    operation, *args = sys.argv[1:]
    if operation == "argv":
        print(shlex.join(args))
        return
    path = os.environ.get("HARNESS_EVENTS")
    if path:
        with Path(path).open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {"event": operation, "args": args, "timestamp": datetime.now(UTC).isoformat()}
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
