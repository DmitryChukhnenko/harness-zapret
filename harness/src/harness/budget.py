from collections import defaultdict
from datetime import timedelta

from harness.clean_win import clean_win


def allocate(facts, disabled_at, now, config):
    groups = defaultdict(list)
    for fact in facts:
        if fact.record_type == "probe":
            groups[(fact.protocol, fact.source)].append(fact)
    active, disabled = [], []
    for protocol in sorted({key[0] for key in groups}):
        modules = sorted(key for key in groups if key[0] == protocol)
        kept = []
        for key in modules:
            sample = groups[key]
            since = disabled_at.get(key[1])
            expired = since and now >= since + timedelta(days=config.budget.module_reenable_days)
            recent = [f for f in sample if since is None or f.timestamp > since]
            no_wins = not any(
                clean_win(f, config.measurement.min_distinct_addresses)[0] for f in recent
            )
            eliminate = len(recent) >= config.budget.zero_win_elimination_threshold and no_wins
            if (since and not expired) or (eliminate and not expired):
                disabled.append(key)
            else:
                kept.append(key)
        if not kept:
            survivor = modules[0]
            disabled.remove(survivor)
            kept.append(survivor)
        active.extend(kept)
    return {"active": active, "disabled": disabled}
