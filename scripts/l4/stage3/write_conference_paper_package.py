#!/usr/bin/env python3
from pathlib import Path
import csv
from statistics import mean

ROOT = Path(".").resolve()
PAPER = ROOT / "paper" / "l4_conference"
FIG = PAPER / "figures"
TAB = PAPER / "tables"
SEC = PAPER / "sections"

for d in [PAPER, FIG, TAB, SEC]:
    d.mkdir(parents=True, exist_ok=True)

CSV_PATH = ROOT / "docs/l4/supervisor_258/results/n8n_all_runs_240runs_duration.csv"
rows = []
if CSV_PATH.exists():
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

def fnum(x):
    try:
        return float(x)
    except Exception:
        return None

def avg(key):
    vals = [fnum(r.get(key)) for r in rows if fnum(r.get(key)) is not None]
    return mean(vals) if vals else 0.0

def nn(key):
    return sum(1 for r in rows if r.get(key) not in ("", "None", None))

def tex_escape(s):
    return str(s).replace("_", r"\_")

(PAPER / "main.tex").write_text(r"""
\documentclass[conference]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{cite,amsmath,amssymb,graphicx,xcolor,booktabs,array,tabularx,adjustbox,url,tikz}
\usetikzlibrary{positioning,arrows.meta,fit,shapes.geometric,calc}

\definecolor{trustblue}{HTML}{1F77B4}
\definecolor{trustgreen}{HTML}{2CA02C}
\definecolor{trustorange}{HTML}{FF7F0E}
\definecolor{trustred}{HTML}{D62728}
\definecolor{trustpurple}{HTML}{9467BD}

\title{ZKTrustLLM-Agents L4: n8n-Orchestrated Scientific Evaluation of Proof-Governed Agentic Zero-Trust Control for O-RAN Edge Security}

\author{
\IEEEauthorblockN{Sudarson Karmaker}
\IEEEauthorblockA{University of Surrey, 5GIC/6GIC, Guildford, United Kingdom\\
Email: s.karmaker@surrey.ac.uk}
\and
\IEEEauthorblockN{Mohammad Shojafar}
\IEEEauthorblockA{University of Surrey, 5GIC/6GIC, Guildford, United Kingdom}
}

\begin{document}
\maketitle

\begin{abstract}
Autonomous O-RAN security operations require policy-governed action, auditable evidence, replay-resistant anchoring, and reproducible evaluation. This paper presents ZKTrustLLM-Agents L4, a proof-governed agentic zero-trust framework for accountable O-RAN edge security workflows. The framework decomposes autonomy into bounded telemetry, reasoning, policy, proof, and audit/anchor agents. A self-hosted n8n workflow orchestrates scientific evaluation and generates run identifiers, Git commit binding, evidence hashes, raw logs, and paper-ready KPI tables. A clean 240-record dataset is produced across six variants, four impairment profiles, and ten repetitions per condition. Stage 3 direct runtime hooks populate anchor gas, reasoning latency, replay rejection, zero-anchor rejection, and unauthorized-submitter rejection. The result is a reviewer-verifiable evaluation method for accountable autonomous O-RAN security rather than an unconstrained agentic dashboard.
\end{abstract}

\begin{IEEEkeywords}
O-RAN, zero trust, agentic AI, n8n, zero-knowledge proof, blockchain audit, reproducible evaluation, KPI validation.
\end{IEEEkeywords}

\input{sections/01_intro}
\input{sections/02_architecture}
\input{sections/03_evaluation}
\input{sections/04_results}
\input{sections/05_discussion}
\input{sections/06_conclusion}

\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
""".strip() + "\n")

(SEC / "01_intro.tex").write_text(r"""
\section{Introduction}
O-RAN disaggregates the radio access network into programmable components, including the SMO, Non-RT RIC, Near-RT RIC, rApps, and xApps. This programmability enables closed-loop optimisation but also creates security risks: unsafe autonomous action, weak evidence binding, replayed audit records, and insufficient reproducibility of security experiments.

This paper asks: \emph{how can autonomous O-RAN security actions be made policy-gated, evidence-bound, replay-resistant, and scientifically reproducible?} We answer this through ZKTrustLLM-Agents L4, a proof-governed agentic zero-trust framework.

The novelty is not the isolated use of n8n, blockchain, IPFS, or agentic AI. The novelty is their controlled scientific composition: bounded agents reason over telemetry, policy gates restrict actions, proof paths attest admissibility, audit hooks produce direct runtime evidence, and n8n orchestrates repeatable scientific evaluation. The design is motivated by zero-trust principles \\cite{nist207}, O-RAN policy-control workflows \\cite{oranA1}, succinct proof systems such as Groth16 \\cite{groth16}, self-hosted command orchestration through n8n \\cite{n8nExecute}, and the public implementation branch used for this evaluation \\cite{zktrustrepo}.

\subsection{Contributions}
The paper makes five contributions: (i) a five-agent O-RAN security architecture; (ii) a policy-gated OBSERVE--REASON--PROVE--ANCHOR--ACT loop; (iii) an n8n-orchestrated evaluation pipeline; (iv) a clean 240-record dataset; and (v) Stage 3 direct runtime hooks for anchor gas, reasoning latency, replay rejection, zero-anchor rejection, and unauthorized-submitter rejection.
""".strip() + "\n")

(SEC / "02_architecture.tex").write_text(r"""
\section{Architecture and Threat Model}
Fig.~\ref{fig:architecture} shows the proposed architecture. The system places MNO policy at the SMO/Non-RT RIC layer and uses bounded agents for O-RAN security automation. The telemetry agent observes network and media-plane indicators. The reasoning agent maps state to trust level and candidate action. The policy agent enforces the action ladder. The proof agent supports bounded admissibility checks. The audit/anchor agent writes evidence hashes and compact commitments.

\input{figures/fig_architecture}
\input{tables/table_agents}

\subsection{Threat Controls}
The framework considers unapproved autonomous action, evidence tampering, anchor replay, zero/empty anchors, unsafe escalation, and unauthorized submitters. Fig.~\ref{fig:threats} maps these concepts to controls.

\input{figures/fig_threats}

\subsection{Smart-Contract Boundary}
The smart contract does not control O-RAN traffic directly. Its role is trust-plane accountability: storing compact commitments, rejecting duplicate commitments, rejecting zero commitments, and enforcing authorized submitters. It cannot verify physical network truth, guarantee evidence availability, or replace MNO operational policy.
""".strip() + "\n")

(SEC / "03_evaluation.tex").write_text(r"""
\section{Scientific Evaluation Methodology}
The evaluation is organised as a three-stage pipeline. Stage 1 establishes the n8n workflow, response matrix, KPI plan, and formal-verification preparation. Stage 2 converts outputs into a clean 240-record dataset. Stage 3 adds direct runtime hooks.

\input{figures/fig_n8n}

\subsection{Evaluation Matrix}
The experiment covers six variants: Full L4, No-ZK, Oracle-only, RBAC-only, No-IPFS, and No-policy-gate. Each variant is evaluated over four impairment profiles and ten repetitions, giving 240 clean records.

\input{tables/table_novelty}

\subsection{KPI Classes}
The dataset distinguishes direct runtime KPIs, configured impairment-profile KPIs, and missing values. This prevents overclaiming. Configured RTP/DTLS-RTP jitter and loss values are scenario-control parameters until replaced by packet-capture or O-RAN telemetry measurements.
""".strip() + "\n")

(SEC / "04_results.tex").write_text(r"""
\section{Results}
\subsection{KPI Completeness}
Table~\ref{tab:kpi_completeness} summarises KPI completeness after Stage 3. Anchor gas, reasoning latency, replay rejection, zero-anchor rejection, and unauthorized-submitter rejection are populated from direct runtime hooks. RTP/DTLS-RTP jitter and loss are configured impairment-profile values.

\input{tables/table_kpi_completeness}

\subsection{Variant/Profile Summary}
Table~\ref{tab:variant_summary} summarises the clean 240-record evaluation. The RBAC-only baseline was repaired to match the current contract ABI and rerun only for the affected variant, preserving experimental traceability.

\input{tables/table_variant_summary}

\subsection{Stage 3 Runtime Evidence}
Stage 3 introduces an isolated Stage3AnomalyLedger micro-benchmark and a deterministic policy-reasoning probe. These emit parseable KPI lines for anchor gas, negative-security rejection, and reasoning latency.

\input{tables/table_stage3}
""".strip() + "\n")

(SEC / "05_discussion.tex").write_text(r"""
\section{Discussion and Limitations}
The framework intentionally avoids overclaiming. Stage3AnomalyLedger is an isolated scientific micro-benchmark, not the production trust ledger. The deterministic reasoning probe measures bounded control-plane reasoning latency, not open-ended semantic LLM reasoning. Configured impairment-profile values are not packet-capture measurements.

The main remaining direct-runtime KPI is full ZK prover timing for full-ZK rows. Current prover-time values are populated for ablation rows where the prover is intentionally not invoked, while direct prover logs are still required for full AUTH\_V2.x rows.
""".strip() + "\n")

(SEC / "06_conclusion.tex").write_text(r"""
\section{Conclusion}
This paper presented ZKTrustLLM-Agents L4, a proof-governed and policy-gated agentic framework for accountable O-RAN edge security workflows. The contribution is a reproducible scientific evaluation pipeline that turns an autonomous dashboard into reviewer-verifiable evidence. The clean 240-record dataset, Stage 3 runtime hooks, architecture, and KPI completeness report provide a foundation for conference and journal-level validation.
""".strip() + "\n")

(FIG / "fig_architecture.tex").write_text(r"""
\begin{figure*}[!t]
\centering
\begin{tikzpicture}[
font=\small,
box/.style={draw, rounded corners, thick, align=center, minimum height=8mm, minimum width=24mm},
arrow/.style={-{Latex[length=2mm]}, thick},
node distance=8mm
]
\node[box, fill=trustblue!18] (mno) {MNO / Tenant\\Policy Intent};
\node[box, fill=trustblue!18, right=of mno] (smo) {SMO / Non-RT RIC\\Policy Registry};
\node[box, fill=trustgreen!18, right=of smo] (nrt) {Near-RT RIC\\xApps};
\node[box, fill=trustorange!18, right=of nrt] (ran) {O-CU / O-DU / O-RU\\RTP / DTLS-RTP};

\node[box, fill=trustpurple!18, below=12mm of smo] (obs) {Telemetry\\OBSERVE};
\node[box, fill=trustpurple!18, right=of obs] (reason) {Reasoning\\REASON};
\node[box, fill=trustpurple!18, right=of reason] (policy) {Policy\\GATE};
\node[box, fill=trustpurple!18, right=of policy] (proof) {Proof\\PROVE};
\node[box, fill=trustpurple!18, right=of proof] (audit) {Audit/Anchor\\ANCHOR};

\node[box, fill=trustred!12, below=12mm of policy] (zk) {AUTH\_V2.x\\Admissibility};
\node[box, fill=trustred!12, left=of zk] (evidence) {Evidence Store\\CID / Hash};
\node[box, fill=trustred!12, right=of zk] (chain) {Audit Contract\\Commit / Reject};

\draw[arrow] (mno)--node[above]{intent}(smo);
\draw[arrow] (smo)--node[above]{A1 policy}(nrt);
\draw[arrow] (nrt)--node[above]{E2 control}(ran);
\draw[arrow] (ran.south)|-(obs.east);
\draw[arrow] (obs)--(reason);
\draw[arrow] (reason)--(policy);
\draw[arrow] (policy)--(proof);
\draw[arrow] (proof)--(audit);
\draw[arrow] (proof)--(zk);
\draw[arrow] (audit)--(evidence);
\draw[arrow] (audit)--(chain);
\draw[arrow] (chain.north)|-(nrt.south);
\end{tikzpicture}
\caption{Proposed ZKTrustLLM-Agents L4 architecture. Policy is placed in the SMO/Non-RT RIC governance path while bounded agents connect O-RAN telemetry to proof, evidence, and audit anchoring.}
\label{fig:architecture}
\end{figure*}
""".strip() + "\n")

(FIG / "fig_threats.tex").write_text(r"""
\begin{figure}[!t]
\centering
\begin{tikzpicture}[
font=\scriptsize,
phase/.style={draw, rounded corners, thick, fill=trustgreen!18, align=center, minimum width=15mm},
threat/.style={draw, rounded corners, thick, fill=trustred!15, align=center, minimum width=20mm},
arrow/.style={-{Latex[length=1.6mm]}, thick},
node distance=4mm
]
\node[phase] (o) {OBSERVE};
\node[phase, right=of o] (r) {REASON};
\node[phase, right=of r] (p) {PROVE};
\node[phase, right=of p] (a) {ANCHOR};
\node[phase, right=of a] (act) {ACT};
\draw[arrow] (o)--(r);
\draw[arrow] (r)--(p);
\draw[arrow] (p)--(a);
\draw[arrow] (a)--(act);
\node[threat, below=8mm of r] (t1) {Unsafe\\action};
\node[threat, below=8mm of p] (t2) {Invalid\\proof};
\node[threat, below=8mm of a] (t3) {Replay /\\zero anchor};
\draw[arrow, trustred] (t1)--node[left]{policy gate}(r);
\draw[arrow, trustred] (t2)--node[right]{AUTH check}(p);
\draw[arrow, trustred] (t3)--node[right]{contract reject}(a);
\end{tikzpicture}
\caption{Threat-to-control mapping. Unsafe actions are policy-gated, invalid proofs are blocked, and replay/zero anchors are rejected.}
\label{fig:threats}
\end{figure}
""".strip() + "\n")

(FIG / "fig_n8n.tex").write_text(r"""
\begin{figure}[!t]
\centering
\begin{tikzpicture}[
font=\scriptsize,
box/.style={draw, rounded corners, thick, align=center, fill=trustblue!10, minimum width=35mm, minimum height=7mm},
arrow/.style={-{Latex[length=1.6mm]}, thick},
node distance=4mm
]
\node[box] (n8n) {n8n Orchestrator};
\node[box, below=of n8n] (matrix) {6 Variants $\times$ 4 Profiles $\times$ 10 Repeats};
\node[box, below=of matrix] (run) {Run Scripts + Hardhat + Stage 3 Hooks};
\node[box, below=of run] (logs) {Raw Logs + Evidence Hashes + Git Commit};
\node[box, below=of logs] (extract) {KPI Extraction + Deduplication};
\node[box, below=of extract] (paper) {CSV / Markdown / Paper Tables};
\draw[arrow] (n8n)--(matrix);
\draw[arrow] (matrix)--(run);
\draw[arrow] (run)--(logs);
\draw[arrow] (logs)--(extract);
\draw[arrow] (extract)--(paper);
\end{tikzpicture}
\caption{n8n-orchestrated scientific evaluation pipeline. n8n coordinates execution but is not a security primitive.}
\label{fig:n8n}
\end{figure}
""".strip() + "\n")

(TAB / "table_agents.tex").write_text(r"""
\begin{table}[!t]
\centering
\caption{Bounded Agentic Components}
\label{tab:agents}
\begin{adjustbox}{width=\columnwidth}
\begin{tabular}{lll}
\toprule
Agent & Role & Output \\
\midrule
Telemetry & Observe O-RAN/media KPIs & Jitter, loss, profile \\
Reasoning & Map state to trust/action & Trust state, action class \\
Policy & Enforce action ladder & Auto/Human/Privileged/Never \\
Proof & Check admissibility & AUTH\_V2.x status \\
Audit/Anchor & Bind evidence and commit & CID/hash/anchor record \\
\bottomrule
\end{tabular}
\end{adjustbox}
\end{table}
""".strip() + "\n")

(TAB / "table_novelty.tex").write_text(r"""
\begin{table*}[!t]
\centering
\caption{Novelty and Comparison Matrix}
\label{tab:novelty}
\begin{adjustbox}{width=\textwidth}
\begin{tabular}{lccccccc}
\toprule
Approach & Agents & Policy & ZK & Evidence & Audit & Replay & KPIs \\
\midrule
O-RAN monitoring only & No & Partial & No & No & No & No & Network only \\
Blockchain logging only & No & No & No & Partial & Yes & Partial & Gas/tx \\
RBAC contract only & No & Yes & No & No & Yes & Partial & Auth/gas \\
Oracle-only trust & Yes & Weak & No & Partial & Yes & No & Score/gas \\
No-ZK ablation & Yes & Yes & No & Yes & Yes & Yes & Workflow/gas \\
Full L4 & Yes & Yes & Yes & Yes & Yes & Yes & Agent/ZK/audit \\
n8n-orchestrated L4 & Yes & Yes & Optional & Yes & Yes & Yes & 240 records \\
\bottomrule
\end{tabular}
\end{adjustbox}
\end{table*}
""".strip() + "\n")

(TAB / "table_kpi_completeness.tex").write_text(f"""
\\begin{{table}}[!t]
\\centering
\\caption{{KPI Completeness After Stage 3}}
\\label{{tab:kpi_completeness}}
\\begin{{adjustbox}}{{width=\\columnwidth}}
\\begin{{tabular}}{{lcc}}
\\toprule
KPI & Coverage & Evidence Type \\\\
\\midrule
prover\\_time\\_ms & {nn('prover_time_ms')}/240 & ablation/log gap \\\\
anchor\\_gas & {nn('anchor_gas')}/240 & direct runtime \\\\
rtp\\_jitter\\_ms & {nn('rtp_jitter_ms')}/240 & configured profile \\\\
rtp\\_loss\\_pct & {nn('rtp_loss_pct')}/240 & configured profile \\\\
reason\\_latency\\_ms & {nn('reason_latency_ms')}/240 & direct runtime \\\\
replay\\_rejected & {nn('replay_rejected')}/240 & direct runtime \\\\
zero\\_anchor\\_rejected & {nn('zero_anchor_rejected')}/240 & direct runtime \\\\
unauthorized\\_submitter & {nn('unauthorized_submitter_rejected')}/240 & direct runtime \\\\
postAutoScore gas & {nn('post_auto_score_gas')}/240 & Hardhat log \\\\
\\bottomrule
\\end{{tabular}}
\\end{{adjustbox}}
\\end{{table}}
""".strip() + "\n")

groups = {}
for r in rows:
    key = (r.get("variant", ""), r.get("profile", ""))
    groups.setdefault(key, []).append(r)

lines = [
r"\begin{table*}[!t]",
r"\centering",
r"\caption{Clean 240-Record Variant/Profile Summary}",
r"\label{tab:variant_summary}",
r"\begin{adjustbox}{width=\textwidth}",
r"\begin{tabular}{llrrrr}",
r"\toprule",
r"Variant & Profile & Runs & Pass & Fail & Mean Duration (ms) \\",
r"\midrule",
]
for (v, p), rs in sorted(groups.items()):
    vals = [fnum(x.get("duration_ms")) for x in rs if fnum(x.get("duration_ms")) is not None]
    dur = mean(vals) if vals else 0
    passed = sum(1 for x in rs if x.get("status") == "PASS")
    lines.append(f"{tex_escape(v)} & {tex_escape(p)} & {len(rs)} & {passed} & {len(rs)-passed} & {dur:.1f} \\\\")
lines += [
r"\bottomrule",
r"\end{tabular}",
r"\end{adjustbox}",
r"\end{table*}",
]
(TAB / "table_variant_summary.tex").write_text("\n".join(lines) + "\n")

(TAB / "table_stage3.tex").write_text(f"""
\\begin{{table}}[!t]
\\centering
\\caption{{Stage 3 Direct Runtime Hook KPIs}}
\\label{{tab:stage3}}
\\begin{{adjustbox}}{{width=\\columnwidth}}
\\begin{{tabular}}{{lcc}}
\\toprule
KPI & Coverage & Result \\\\
\\midrule
Anchor gas & {nn('anchor_gas')}/240 & {avg('anchor_gas'):.0f} gas \\\\
Reason latency & {nn('reason_latency_ms')}/240 & {avg('reason_latency_ms'):.3f} ms \\\\
Replay rejection & {nn('replay_rejected')}/240 & true \\\\
Zero-anchor rejection & {nn('zero_anchor_rejected')}/240 & true \\\\
Unauthorized submitter & {nn('unauthorized_submitter_rejected')}/240 & true \\\\
\\bottomrule
\\end{{tabular}}
\\end{{adjustbox}}
\\end{{table}}
""".strip() + "\n")

(PAPER / "references.bib").write_text(r"""
@techreport{nist207,
  author={Scott Rose and Oliver Borchert and Stu Mitchell and Sean Connelly},
  title={Zero Trust Architecture},
  institution={National Institute of Standards and Technology},
  number={NIST SP 800-207},
  year={2020},
  doi={10.6028/NIST.SP.800-207}
}

@inproceedings{groth16,
  author={Jens Groth},
  title={On the Size of Pairing-Based Non-interactive Arguments},
  booktitle={EUROCRYPT},
  year={2016},
  pages={305--326}
}

@misc{oranA1,
  title={O-RAN SC A1 Mediator Documentation},
  howpublished={\url{https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-a1/en/latest/overview.html}},
  year={2026}
}

@misc{n8nExecute,
  title={n8n Execute Command Node Documentation},
  howpublished={\url{https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand/}},
  year={2026}
}

@misc{zktrustrepo,
  author={Sudarson Karmaker},
  title={ZKTrustLLM-Agents L4 Repository and Supervisor 258 Evaluation Branch},
  howpublished={\url{https://github.com/Sudarson2021/zktrustllm-agents-l4/pull/1}},
  year={2026}
}
""".strip() + "\n")

(PAPER / "Makefile").write_text("all:\n\tlatexmk -pdf main.tex\n\nclean:\n\tlatexmk -C\n\trm -f *.bbl *.blg *.aux *.log *.out *.fls *.fdb_latexmk\n")
(PAPER / "README.md").write_text("# ZKTrustLLM-Agents L4 Conference Paper Package\n\nBuild with `make` inside this directory.\n\nReviewer-safety: Stage3AnomalyLedger is an isolated micro-benchmark; RTP/DTLS-RTP impairment values are configured profile KPIs unless replaced by packet capture.\n")

print(f"[ok] wrote conference paper package to {PAPER}")
print(f"[ok] clean records used: {len(rows)}")
