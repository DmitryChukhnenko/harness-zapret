import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from harness.budget import allocate
from harness.storage import write_json


def prepare_modules(config):
    from harness.node_runtime import archive_facts

    root = Path("/state/modules")
    state_path = Path("/state/budget.json")
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"disabled": {}, "reset_after": {}}
    )
    disabled_at = {key: datetime.fromisoformat(value) for key, value in state["disabled"].items()}
    now = datetime.now(UTC)
    from datetime import timedelta

    for source, disabled in list(disabled_at.items()):
        if now >= disabled + timedelta(days=config.budget.module_reenable_days):
            del disabled_at[source]
            state["reset_after"][source] = now.isoformat()
    facts = [
        f
        for f in archive_facts()
        if f.source not in state["reset_after"]
        or f.timestamp > datetime.fromisoformat(state["reset_after"][f.source])
    ]
    allocation = allocate(facts, disabled_at, now, config)
    disabled = {source for _, source in allocation["disabled"]}
    active = {source for _, source in allocation["active"]}
    # A script active for any protocol stays enabled for every protocol.
    disabled -= active
    source_root = Path("/opt/zapret2/blockcheck2.d/standard")
    target = root / "standard"
    target.mkdir(parents=True, exist_ok=True)
    for include in source_root.glob("*.inc"):
        shutil.copyfile(include, target / include.name)
    for source in source_root.glob("*.sh"):
        observed_name = str(target / source.name)
        destination = target / source.name
        if observed_name in disabled:
            destination.unlink(missing_ok=True)
        else:
            shutil.copyfile(source, destination)
    state["disabled"] = {source: disabled_at.get(source, now).isoformat() for source in disabled}
    write_json(state_path, state)
    return root
