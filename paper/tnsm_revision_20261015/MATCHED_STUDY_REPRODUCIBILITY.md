# Reproduce the completed study without new model calls

Run from the repository root. Python 3.10+ is sufficient for the independent standard-library audit. The frozen analyzer also requires Pydantic 2.13.x; collection used 2.13.4 and independent reanalysis used 2.13.5. Use a separate environment if required. None of the commands below starts inference or executes network actions.

```bash
python3 scripts/l4/tnsm_revision/audit_matched_inference_evidence.py
python3 scripts/l4/tnsm_revision/build_matched_inference_tables.py
python3 -m unittest discover -s test/l4/tnsm_revision -p 'test_*.py' -v
python3 -m unittest discover -s test/l4/tnsm_revision/matched_ablation -p 'test_*.py' -v
node test/l4/tnsm_revision/test_review_payload_v2.cjs
```

To reproduce the original analyzer, first extract the immutable author archive into a new temporary directory. The independent audit above validates archive identity and paths before this step. This extraction also rejects links and unusual archive members.

```bash
python3 - <<'PYCODE'
from pathlib import Path, PurePosixPath
import hashlib, tempfile, tarfile, subprocess, sys
archive = Path('paper/tnsm_revision_20261015/evidence/inputs/TNSM_12002_Matched_Ablation_Evidence_20261016T194059Z.tar.gz')
assert hashlib.sha256(archive.read_bytes()).hexdigest() == '7ea6792f45aa6663e98869e81626f69bb37c58c1c4de161691545c70780bdd95'
destination = Path(tempfile.mkdtemp(prefix='tnsm-matched-audit-'))
with tarfile.open(archive, 'r:gz') as tar:
    names = set()
    for member in tar.getmembers():
        p = PurePosixPath(member.name)
        assert not p.is_absolute() and '..' not in p.parts
        assert member.isfile() or member.isdir()
        assert member.name not in names
        names.add(member.name)
    tar.extractall(destination, filter='data')
subprocess.run([sys.executable, str(destination/'scripts/l4/tnsm_revision/matched_ablation/analyze.py'), '--input', str(destination/'full_01'), '--report-dir', str(destination/'reproduced_analysis')], check=True)
import json
assert json.loads((destination/'reproduced_analysis/analysis.json').read_text()) == json.loads((destination/'full_01_analysis/analysis.json').read_text())
print('Exact frozen analysis reproduced:', destination)
PYCODE
```

Python 3.12+ supports the extraction filter used here. The full and pilot protocol/manifests, journal, inputs, requests, responses and original analysis remain inside that archive. The four frozen harness files are not amended by the post hoc audit. Source hashes and collection identity stay unchanged.

The source protocol in `docs/l4/matched_ablation/PROTOCOL.md` describes defaults before the pilot. The actual frozen full protocol has assessor cap 5,000 and role cap 8,192; its hash and prospective amendment are authoritative. Read `MATCHED_STUDY_AUDIT.md` before interpreting results or the analyzer's publication-eligibility flag.

Do not rerun `launch.py run --live` to reproduce retained statistics. That would create new paid observations and must use a new prospective study name/protocol. The existing evidence must never be overwritten or selectively replaced.
