#!/usr/bin/env python3
"""apply_bsc_network.py — idempotently add the bscTestnet network to
hardhat.config.js, mirroring the repo's existing getSepoliaAccounts pattern.
Usage: python3 apply_bsc_network.py /path/to/hardhat.config.js
"""
import re, sys, pathlib

cfg = pathlib.Path(sys.argv[1])
src = cfg.read_text()

if "bscTestnet" in src:
    print("hardhat.config.js already has bscTestnet — nothing to do")
    sys.exit(0)

helper = """
function getBscTestnetAccounts() {
  const pk = process.env.BSC_TESTNET_PRIVATE_KEY || "";
  if (/^0x[0-9a-fA-F]{64}$/.test(pk)) return [pk];
  if (/^[0-9a-fA-F]{64}$/.test(pk)) return ["0x" + pk];
  // fall back to the Sepolia deployer key (same EVM key works on BSC testnet)
  return getSepoliaAccounts();
}
"""

network = """    bscTestnet: {
      url:
        process.env.BSC_TESTNET_RPC_URL ||
        "https://bsc-testnet-rpc.publicnode.com",
      accounts: getBscTestnetAccounts(),
      chainId: 97
    },
"""

# insert helper after getSepoliaAccounts function body
m = re.search(r"function getSepoliaAccounts\(\)\s*\{.*?\n\}", src, re.S)
assert m, "could not locate getSepoliaAccounts in hardhat.config.js"
src = src[: m.end()] + "\n" + helper + src[m.end():]

# insert network entry immediately before the sepolia entry (inside networks{})
m2 = re.search(r"(\n\s*sepolia:\s*\{)", src)
assert m2, "could not locate the sepolia network entry"
src = src[: m2.start()] + "\n" + network.rstrip("\n") + src[m2.start():]

cfg.write_text(src)
print("PATCHED: bscTestnet network + getBscTestnetAccounts added")
print("Set BSC_TESTNET_RPC_URL to override the default public RPC if needed;")
print("official endpoints are listed at docs.bnbchain.org (chainId 97).")
