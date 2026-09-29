FROM python:3.12-slim-bookworm AS builder
ARG ZAPRET_REV=00f5aaa36de500971faf6db440dd7d8b25672281
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential pkg-config libnetfilter-queue-dev libmnl-dev zlib1g-dev libluajit-5.1-dev libcap-dev ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git init /opt/zapret2 && cd /opt/zapret2 && git remote add origin https://github.com/bol-van/zapret2.git && git fetch --depth 1 origin "$ZAPRET_REV" && git checkout --detach FETCH_HEAD && test "$(git rev-parse HEAD)" = "$ZAPRET_REV" && make && printf '%s\n' "$ZAPRET_REV" > REVISION

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends curl iproute2 nftables iptables ipset dnsutils dnsmasq-base iputils-ping netcat-openbsd libnetfilter-queue1 libmnl0 libluajit-5.1-2 libcap2 procps bsdextrautils && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/zapret2 /opt/zapret2
WORKDIR /app
COPY pyproject.toml README.md ./
COPY harness/src ./harness/src
RUN pip install --no-cache-dir .
COPY config ./config
COPY zapret/instrument.py /app/instrument.py
RUN python /app/instrument.py /opt/zapret2/blockcheck2.sh
COPY zapret/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["sh", "/entrypoint.sh"]
