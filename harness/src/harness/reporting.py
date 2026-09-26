import json
import logging
from typing import Protocol

from harness.storage import write_json


class ReportSink(Protocol):
    def deliver(self, report: dict) -> None: ...


def report(root, run_id, payload, external_sink=None):
    payload = {"run_id": run_id, **payload}
    payload["external_delivery"] = "NOT_CONFIGURED"
    if external_sink:
        try:
            external_sink.deliver(payload)
            payload["external_delivery"] = "DELIVERED"
        except Exception:
            payload["external_delivery"] = "FAILED"
            logging.error("REPORT_DELIVERY_FAILED run_id=%s", run_id)
    write_json(root / "reports" / f"{run_id}.json", payload)
    (root / "reports" / f"{run_id}.md").write_text(
        f"# Run {run_id}\n\nExternal delivery: {payload['external_delivery']}\n\n"
        + "```json\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    return payload
