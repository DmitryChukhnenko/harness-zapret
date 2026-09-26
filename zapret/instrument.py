"""Instrumentation only: upstream still chooses and runs every strategy/probe.

Exact anchors deliberately fail the build if the pinned upstream format changes.
Events use a separate local file so server-controlled stdout cannot forge facts.
"""

import sys
from pathlib import Path


def instrument(text: str) -> str:
    replacements = {
        'BLOCKCHECK2D="$ZAPRET_BASE/blockcheck2.d"': (
            'BLOCKCHECK2D="${BLOCKCHECK2D:-$ZAPRET_BASE/blockcheck2.d}"'
        ),
        "\tlocal code=0 n=0 p pids\n": (
            "\tlocal code=0 n=0 p pids probe_rc\n"
            '\tpython -m harness.trace begin "$2" "$1" "$IPV" '
            '"${HARNESS_STRATEGY:-}" "${script:-baseline}"\n'
        ),
        '\t\t\tif $1 "$IPV" "$2" $3 "$4" ; then\n': (
            '\t\t\t$1 "$IPV" "$2" $3 "$4"; probe_rc=$?\n'
            '\t\t\tpython -m harness.trace attempt "$probe_rc"\n'
            '\t\t\tif [ "$probe_rc" = 0 ]; then\n'
        ),
        '\t\t\t\tcode=$?\n\t\t\t\t[ "$SCANLEVEL" = quick ]': (
            '\t\t\t\tcode=$probe_rc\n\t\t\t\t[ "$SCANLEVEL" = quick ]'
        ),
        "\treturn $code\n}\nws_curl_test()": (
            '\tpython -m harness.trace end "$code"\n\treturn $code\n}\nws_curl_test()'
        ),
        '\t$ws_start "$@"\n': (
            "\tlocal HARNESS_STRATEGY\n"
            '\tHARNESS_STRATEGY=$(python -m harness.trace argv "$@")\n'
            '\t$ws_start "$@"\n'
        ),
        '\tALL_PROXY="$ALL_PROXY" "$CURL"': (
            '\tpython -m harness.trace address "$3"\n\tALL_PROXY="$ALL_PROXY" "$CURL"'
        ),
    }
    # curl_with_subst_ip shifts argv before invoking curl; retain its local IP instead.
    replacements['\tALL_PROXY="$ALL_PROXY" "$CURL"'] = (
        '\tpython -m harness.trace address "$ip"\n\tALL_PROXY="$ALL_PROXY" "$CURL"'
    )
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise ValueError(f"upstream instrumentation anchor mismatch: {old!r}")
        text = text.replace(old, new)
    return text


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(instrument(path.read_text()), encoding="utf-8")
