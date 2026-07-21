# Integrating the PoS/Roll-DPoS comparison into the journal manuscript

Use `docs/journal/pos_rolldpos_comparison_section.tex` after the existing blockchain
or public-testnet evaluation subsection and before the global limitations section.

The section is already claim-safe: if the strict measured-evidence output is absent,
it prints an explicit statement that no numerical comparison is claimed. Do not
replace that guard with hand-entered values.

Add these packages to the journal preamble if they are not already present:

```tex
\usepackage{booktabs,adjustbox,tikz,pgfplots}
\pgfplotsset{compat=1.18}
```

Add the three official-source BibTeX entries named `ethereumNetworks`,
`iotexRollDpos`, and `iotexTestnet` from
`paper/l4_conference/references.bib` to the journal bibliography.

After three measured sessions pass the analysis gate, keep this relative layout in
the manuscript project:

```text
derived_consensus/
  results_pos_rolldpos.tex
  table_pos_rolldpos.tex
  fig_pos_rolldpos_latency.tex
```

Archive `summary.json`, `DERIVATION_MANIFEST.json`, all input `benchmark.json`
files, and their `SHA256SUMS.txt` records with the reproducibility evidence. The
generated table, figure, and paragraph must never be edited manually; rerun the
analysis when evidence changes.

Suggested contribution sentence after the evidence exists:

```tex
\item A paired, multi-session consensus-sensitivity study executes identical audit-
anchor bytecode and matched transactions on Ethereum Sepolia (PoS protocol) and
IoTeX testnet (Roll-DPoS), with deterministic derivation of first-inclusion latency,
gas, block-cadence, and negative-security results from hashed raw evidence.
```

Do not describe Sepolia as representative of Ethereum mainnet: Ethereum's official
documentation states that Sepolia has a permissioned validator set. Do not call BSC
“DPoS”; its official mechanism is PoSA. Do not use “finality latency” for the
`wait(1)` measurement.
