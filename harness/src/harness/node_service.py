import os
import signal
import subprocess
import time
from pathlib import Path

from harness.strategy import validate_strategy

ROOT = Path("/state")
PROCESSES = {}


def nft(text):
    result = subprocess.run(
        ["nft", "-f", "-"], input=text, text=True, capture_output=True, timeout=5, check=False
    )
    if result.returncode:
        raise RuntimeError("nftables transaction failed")


def stop(kind="active"):
    process = PROCESSES.pop(kind, None)
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    subprocess.run(
        ["nft", "delete", "table", "inet", f"harness_{kind}"],
        capture_output=True,
        timeout=5,
        check=False,
    )


def start(strategy, kind="active", domains=None):
    args = validate_strategy(strategy) if strategy else []
    stop(kind)
    if not strategy:
        return True
    ROOT.mkdir(parents=True, exist_ok=True)
    hosts = ROOT / "recheck-hosts.txt"
    if not hosts.exists():
        hosts.write_text("")
    queue = 200 if kind == "active" else 201
    host_option = f"--hostlist-exclude={hosts}" if kind == "active" else f"--hostlist={hosts}"
    argv = [
        "/opt/zapret2/nfq2/nfqws2",
        f"--qnum={queue}",
        "--fwmark=0x40000000",
        "--lua-init=@/opt/zapret2/lua/zapret-lib.lua",
        "--lua-init=@/opt/zapret2/lua/zapret-antidpi.lua",
        host_option,
        *args,
    ]
    with (ROOT / f"{kind}.log").open("a") as output:
        process = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT)
    PROCESSES[kind] = process
    time.sleep(0.3)
    if process.poll() is not None:
        raise RuntimeError("nfqws2 failed to start")
    priority = -150 if kind == "active" else -151
    table = f"harness_{kind}"
    nft(f"""table inet {table} {{
      chain output {{ type filter hook output priority {priority}; policy accept;
        meta mark & 0x40000000 == 0 tcp dport {{80,443}} queue num {queue} bypass
      }}
      chain forward {{ type filter hook forward priority {priority}; policy accept;
        meta mark & 0x40000000 == 0 tcp dport {{80,443}} queue num {queue} bypass
      }}
    }}""")
    return True


def service_status():
    process = PROCESSES.get("active")
    return not live_strategy() or (process is not None and process.poll() is None)


def set_exclusions(domains):
    path = ROOT / "recheck-hosts.txt"
    temp = path.with_suffix(".tmp")
    temp.write_text("".join(d + "\n" for d in domains))
    temp.replace(path)
    process = PROCESSES.get("active")
    if process and process.poll() is None:
        os.kill(process.pid, signal.SIGHUP)


def live_strategy():
    path = Path("/state/strategy.conf")
    return path.read_text().rstrip("\n") if path.exists() else ""
