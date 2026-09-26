import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from harness.config import load_config, load_domains
from harness.control import Control
from harness.storage import Storage, write_json


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
    api = Control(timeout=config.timeouts.control_seconds)
    for name, verb in [("gateway", "health"), ("client", "client_health")]:
        try:
            checks[name] = api.call(verb)
        except Exception:
            checks[name] = {"status": "SKIPPED_ENVIRONMENT", "reason": "node unavailable"}
    routes = checks["client"].get("route", [])
    checks["topology"] = (
        "PASS" if len(routes) == 1 and routes[0].get("gateway") == "172.31.0.2" else "UNKNOWN"
    )
    if checks["topology"] == "PASS":
        try:
            checks["path_probe"] = Control(timeout=30).call("path_probe")
            checks["topology"] = checks["path_probe"]["status"]
        except Exception:
            checks["topology"] = "UNKNOWN"
    return checks


def main():
    parser = argparse.ArgumentParser(prog="harness")
    parser.add_argument(
        "command",
        choices=[
            "doctor",
            "run",
            "sweep",
            "ingest",
            "analyze",
            "summarize",
            "llm",
            "recheck",
            "deploy",
            "watchdog",
            "rollback",
            "reconcile",
            "report",
            "acceptance",
            "pipeline",
            "llm-eval",
        ],
    )
    parser.add_argument("--config", default="config/harness.yaml")
    parser.add_argument("--run-id")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--since", help="timezone-aware ISO timestamp")
    parser.add_argument("--provider", choices=["mistral", "mock"])
    parser.add_argument("--live", action="store_true", help="explicit paid API evaluation")
    parser.add_argument(
        "--initialize", action="store_true", help="initialize expected config snapshot"
    )
    args = parser.parse_args()
    config = load_config(args.config)
    if args.provider:
        config.llm.provider = args.provider
    from harness import pipeline as stages

    try:
        command = args.command
        if command == "doctor":
            result = doctor(config)
        elif command == "llm-eval":
            if args.live:
                from harness.evaluation import live_evaluation

                result = live_evaluation(config)
            else:
                from harness.acceptance import acceptance

                result = acceptance(config.data_dir)
        elif command in {"sweep", "run"}:
            result = {"run_id": stages.run_sweep(config)}
        elif command == "ingest":
            from harness.runner import ingest

            since = datetime.fromisoformat(args.since) if args.since else None
            if since and since.tzinfo is None:
                raise ValueError("--since must include timezone")
            result = ingest(config.data_dir, args.run_id, args.rebuild, since)
        elif command == "pipeline":
            result = stages.pipeline(config, args.run_id)
        elif command in {"analyze", "summarize", "llm", "recheck"}:
            run_id = stages.resolve_run(config.data_dir, args.run_id)
            function = (
                stages.analyze if command in {"analyze", "summarize"} else getattr(stages, command)
            )
            result = function(config, run_id)
        elif command == "deploy":
            if not args.run_id:
                raise ValueError("deploy requires the completed recheck --run-id")
            result = stages.deploy(config, args.run_id)
        elif command in {"watchdog", "rollback"}:
            result = stages.control(config, long=True).call(
                "restore_backup" if command == "rollback" else "watchdog"
            )
        elif command == "reconcile":
            from harness.reconcile import reconcile

            store = Storage(config.data_dir)
            api = stages.control(config)
            if args.initialize:
                write_json(store.root / "state" / "expected.json", api.call("get_config"))
            result = reconcile(store.root, api)
        elif command == "report":
            run_id = stages.resolve_run(config.data_dir, args.run_id)
            result = json.loads((Path(config.data_dir) / "reports" / f"{run_id}.json").read_text())
        else:
            from harness.acceptance import acceptance

            result = acceptance(config.data_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if command == "doctor" and (
            not result["gateway"].get("available") or result["topology"] != "PASS"
        ):
            return 2
        return 1 if result.get("status") == "FAIL" else 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "error_type": type(exc).__name__,
                    "message": "Operation failed; inspect configuration and local reports.",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
