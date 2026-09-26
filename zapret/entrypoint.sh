#!/bin/sh
set -eu
mkdir -p /state /auth
python -m harness.node init
dnsmasq --user=root --no-resolv --server=1.1.1.1 --listen-address=127.0.0.1,172.31.0.2 --bind-interfaces --pid-file=/state/dnsmasq.pid
ip route replace 172.30.0.0/24 dev "$(ip -o -4 addr show | awk '$4 ~ /^172.30.0.2\// {print $2}')"
if nft list table ip harness_nat >/dev/null 2>&1; then nft delete table ip harness_nat; fi
if nft list table inet harness_path >/dev/null 2>&1; then nft delete table inet harness_path; fi
nft -f - <<'EOF'
table ip harness_nat {
 chain postrouting { type nat hook postrouting priority srcnat; policy accept;
  ip saddr 172.31.0.0/24 ip daddr != {172.30.0.0/24,172.31.0.0/24} masquerade
 }
}
table inet harness_path {
 counter client_forward {}
 chain forward { type filter hook forward priority filter; policy accept;
  ip saddr 172.31.0.3 counter name client_forward
 }
}
EOF
exec python -m harness.node serve gateway
