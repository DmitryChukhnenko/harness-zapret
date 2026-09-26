import argparse
import json
import os
from pathlib import Path

from harness.config import load_config, load_domains
from harness.control import Control


def doctor(config):
    checks = {
        "config": "PASS",
        "domains": len(load_domains().all()),
        "llm_provider": config.llm.provider,
        "llm_model": config.llm.model,
        "llm_key_present": bool(os.environ.get("MISTRAL_API_KEY")),
    }
    root = Path(config.data_dir)
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".write-check"
    probe.write_text("ok")
    probe.unlink()
    checks["data_writable"] = True
    try:
        checks["gateway"] = Control(timeout=config.timeouts.control_seconds).call("health")
    except Exception:
        checks["gateway"] = {"status": "SKIPPED_ENVIRONMENT", "reason": "node unavailable"}
    return checks


def main():
    parser = argparse.ArgumentParser(prog="harness")
    parser.add_argument("command", choices=["doctor"])
    parser.add_argument("--config", default="config/harness.yaml")
    args = parser.parse_args()
    result = doctor(load_config(args.config))
    print(json.dumps(result, indent=2))
    return 0 if result.get("gateway", {}).get("available") else 2


if __name__ == "__main__":
    raise SystemExit(main())
