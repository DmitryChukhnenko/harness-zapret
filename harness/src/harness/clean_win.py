"""The sole definition of a clean win (SPEC T-5.2)."""


def clean_win(fact, min_distinct_addresses=2):
    if fact.record_type != "probe":
        return False, "not_a_strategy_probe"
    if not fact.frontend_addresses:
        return False, "no_recorded_addresses"
    if fact.verdict != "OPEN" or fact.success_count != fact.attempt_count:
        return False, "not_all_attempts_succeeded"
    if fact.frontend_address_count < min_distinct_addresses:
        return False, "insufficient_distinct_addresses"
    return True, "clean_win"
