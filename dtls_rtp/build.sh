#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

cc -Wall -Wextra -O2 \
  dtls_rtp_proxy.c \
  -o dtls_rtp_proxy \
  $(pkg-config --cflags --libs openssl)

echo "Built dtls_rtp/dtls_rtp_proxy"
