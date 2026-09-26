#!/bin/sh
set -eu
mkdir -p /state /auth
python -m harness.node init
ip route replace 172.30.0.0/24 dev "$(ip -o -4 addr show | awk '$4 ~ /^172.30.0.2\// {print $2}')"
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
