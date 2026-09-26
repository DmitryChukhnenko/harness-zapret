"""Strategy text is tokenized once; subprocess calls always use argument arrays."""

import re
import shlex


def validate_strategy(strategy):
    if not isinstance(strategy, str) or not strategy or len(strategy) > 8192:
        raise ValueError("invalid strategy length")
    if re.search(r"[\x00-\x1f\x7f`$;&|<>\\]", strategy):
        raise ValueError("interpreter-significant character in deployment strategy")
    args = shlex.split(strategy, posix=True)
    if not args or any(not arg.startswith("--") for arg in args):
        raise ValueError("strategy must consist of --option[=value] arguments")
    forbidden = {
        "--lua-init",
        "--daemon",
        "--pidfile",
        "--qnum",
        "--uid",
        "--user",
        "--debug",
        "--hostlist",
        "--hostlist-exclude",
        "--hostlist-auto",
        "--ipset",
        "--ipset-exclude",
        "--blob",
        "--new",
    }
    if any(arg.split("=", 1)[0] in forbidden or "@" in arg or "/" in arg for arg in args):
        raise ValueError("strategy cannot change execution, files or profile boundaries")
    return args


def operations(strategy):
    result = set()
    for token in validate_strategy(strategy):
        name, _, value = token.partition("=")
        result.add(name)
        if name == "--lua-desync":
            parts = value.split(":")
            result.add(f"lua:{parts[0]}")
            result.update(f"lua:{parts[0]}:{p.split('=', 1)[0]}" for p in parts[1:])
    return result


def corpus_dictionary(facts):
    dictionary = set()
    for fact in facts:
        if fact.record_type == "probe":
            try:
                dictionary.update(operations(fact.strategy))
            except ValueError:
                continue
    return dictionary


def validate_expansion(strategy, dictionary, observed):
    if strategy in observed:
        raise ValueError("strategy already measured")
    if operations(strategy) - dictionary:
        raise ValueError("unknown corpus operation or parameter")
    return strategy
