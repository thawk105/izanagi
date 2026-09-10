# 正例 record を得た probe script の逐語

親が job dir (`dev-wave-jobs/<wave>/refs/probe_real_record.py`、repo 外) で実走した script の逐語である。
repo 内へ `.py` として置くと provenance の実装面判定 (所在不問の Python) に掛かるため、`.md` へ貼る (先例: [T-664] wave)。
出力は同 dir の `producer-verbatim-record.txt` の 2 行で、テストはその bytes を literal に持つ。

```python
"""Write one trigger_binding record with the production producer and print the verbatim line."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.getcwd())

from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.reflux_ir import parse_wire
from orchestrator.campaign.trigger_gate_binding import (
    TriggerGateBinding, expected_predicate_sha256, commitment,
)

root = tempfile.mkdtemp(prefix="t2257-probe-", dir=os.environ.get("CLAUDE_JOB_DIR", "/tmp") + "/tmp")
lay = CampaignLayout(root=os.path.join(root, "campaign")).ensure()
ir = parse_wire("11100")
binding = TriggerGateBinding(ir.mask, expected_predicate_sha256(ir.mask), "a" * 64, source=None)
c = wal.log_trigger_binding(lay, "probe-v", "probe-env", "probe-attempt-0001", binding)
wal.log(lay, "probe-v", "build_start", "probe-env", {
    "build_attempt_id": "probe-attempt-0001",
    wal.TRIGGER_BINDING_COMMITMENT_KEY: c,
})
print("wal_file:", lay.wal_file)
with open(lay.wal_file, encoding="utf-8") as f:
    for line in f:
        print("LINE:", line.rstrip("\n"))
print("commitment:", c, c == commitment(binding))
recs, issues, trunc = wal.read_records_collected(lay)
print("parsed:", [(r.stage, sorted(r.payload)) for r in recs], issues, trunc)
```

**模擬と実の差 (DW-S01):** layout は tmp dir 上の `CampaignLayout` だが、**書き手は production 関数
`wal.log_trigger_binding()` / `wal.log()` そのもの**であり、record の bytes を作る経路は模擬していない。
この probe の出力は仮説ではなく、production producer の出力そのものである。probe が測っていないのは
campaign 実走の文脈 (どの局面で何回呼ばれるか) で、consumer の受理集合の判断には使っていない。
