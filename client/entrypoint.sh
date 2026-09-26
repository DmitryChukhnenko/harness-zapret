#!/bin/sh
set -eu
ip route replace default via 172.31.0.2
exec python -m harness.node serve client
