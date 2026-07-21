#!/usr/bin/env python3
"""analyze_consensus_comparison.py — derive the PoS vs DPoS-family paper
artifacts STRICTLY from measured summary.json files. If either network's
evidence is missing, this script fails: no number in the manuscript can
originate anywhere except a recorded run.

Usage:
  python3 analyze_consensus_comparison.py \
      runtime_artifacts/consensus/sepolia/<stamp>/summary.json \
      runtime_artifacts/consensus/bscTestnet/<stamp>/summary.json \
      <output_dir>
"""
import hashlib, json, sys
from pathlib import Path

def sha256(p): 
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p, expect):
    d = json.loads(Path(p).read_text())
    assert d["network"] == expect, f"{p}: expected network {expect}, got {d['network']}"
    assert d["repeats"] >= 10, f"{p}: fewer than 10 repeats — collect more data first"
    return d

def s_ms(v):  # ms -> seconds string
    return f"{v/1000:.2f}"

def main(sep_p, bsc_p, out_p):
    sep, bsc = load(sep_p, "sepolia"), load(bsc_p, "bscTestnet")
    out = Path(out_p); out.mkdir(parents=True, exist_ok=True)

    def gas(d):
        vs = d["anchor_gas_values"]
        return vs[0] if d["anchor_gas_constant"] else "varies: " + ",".join(vs)
    def neg(d):
        n = d["negative_security"]
        return all(n.values())
    def ibs(d):
        b = d.get("observed_interblock_seconds")
        return f"{b['median']}" if b else "n/a"

    rows = [("Ethereum Sepolia (PoS, Gasper)", sep),
            ("BNB Smart Chain testnet (PoSA / DPoS family)", bsc)]

    tex = [
        r"% AUTO-DERIVED from measured consensus benchmark evidence by",
        r"% analyze_consensus_comparison.py — regenerate, never hand-edit.",
        r"\begin{table*}[!t]",
        r"\caption{Consensus-layer sensitivity of the Stage3AnomalyLedger audit"
        r" micro-benchmark: identical bytecode on Ethereum Sepolia"
        r" (Proof-of-Stake) and BNB Smart Chain testnet (Proof-of-Staked-"
        r"Authority, delegated-staking BFT family). Inclusion latency is"
        r" submit-to-first-confirmation wall clock under prevailing testnet"
        r" load; gas is consensus-independent EVM execution cost; results are"
        r" not mainnet or production performance claims.}",
        r"\label{tab:consensus}",
        r"\centering\footnotesize",
        r"\begin{tabular}{lcccccccc}",
        r"\toprule",
        r"Network (consensus) & Chain ID & $R$ & Anchor gas & Deploy gas &"
        r" Incl.\ lat.\ median (s) & Incl.\ lat.\ P95 (s) &"
        r" Obs.\ inter-block median (s) & Replay/zero/unauth.\ rej. \\",
        r"\midrule",
    ]
    for label, d in rows:
        L = d["inclusion_latency_ms"]
        tex.append(
            f"{label} & {d['chain_id']} & {d['repeats']} & {gas(d)} & "
            f"{d['deploy_gas']} & {s_ms(L['median'])} & {s_ms(L['p95'])} & "
            f"{ibs(d)} & {'true/true/true' if neg(d) else r'\\textbf{CHECK}'} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    (out / "table_consensus.tex").write_text("\n".join(tex))

    sL, bL = sep["inclusion_latency_ms"], bsc["inclusion_latency_ms"]
    fig = rf"""% AUTO-DERIVED from measured consensus benchmark evidence — regenerate, never hand-edit.
\begin{{figure}}[!t]
\centering
\begin{{tikzpicture}}
\begin{{axis}}[
  width=\columnwidth, height=5.0cm, ybar, bar width=14pt,
  ymin=0, ylabel={{Inclusion latency (s)}},
  symbolic x coords={{Sepolia (PoS), BSC testnet (PoSA)}}, xtick=data,
  legend style={{at={{(0.5,1.02)}}, anchor=south, legend columns=2, font=\scriptsize}},
  nodes near coords, nodes near coords style={{font=\tiny}},
  enlarge x limits=0.45, axis lines*=left, ymajorgrids, grid style={{black!12}},
]
\addplot+[fill=blue!55]  coordinates {{(Sepolia (PoS),{sL['median']/1000:.2f}) (BSC testnet (PoSA),{bL['median']/1000:.2f})}};
\addplot+[fill=orange!70] coordinates {{(Sepolia (PoS),{sL['p95']/1000:.2f}) (BSC testnet (PoSA),{bL['p95']/1000:.2f})}};
\legend{{Median, P95}}
\end{{axis}}
\end{{tikzpicture}}
\caption{{Measured submit-to-first-confirmation latency of the identical audit
anchor transaction on Ethereum Sepolia (PoS) and BNB Smart Chain testnet
(PoSA/DPoS family), $R={sep['repeats']}$ and $R={bsc['repeats']}$ repeats
respectively. Latency reflects public-testnet inclusion under prevailing
load, not economic finality or mainnet performance.}}
\label{{fig:consensus-latency}}
\end{{figure}}
"""
    (out / "fig_consensus_latency.tex").write_text(fig)

    manifest = {
        "derived_from": {str(sep_p): sha256(sep_p), str(bsc_p): sha256(bsc_p)},
        "outputs": {p.name: sha256(p) for p in sorted(out.iterdir())
                    if p.is_file() and p.name != "DERIVATION_MANIFEST.json"},
        "derivation": "Deterministic transformation of measured public-testnet "
                      "evidence; no simulation, no re-execution.",
    }
    (out / "DERIVATION_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"OK: derived {len(manifest['outputs'])} artifacts into {out}")
    print(f"  Sepolia:    gas={gas(sep)}  median={s_ms(sL['median'])}s  P95={s_ms(sL['p95'])}s  neg={neg(sep)}")
    print(f"  BSCtestnet: gas={gas(bsc)}  median={s_ms(bL['median'])}s  P95={s_ms(bL['p95'])}s  neg={neg(bsc)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
