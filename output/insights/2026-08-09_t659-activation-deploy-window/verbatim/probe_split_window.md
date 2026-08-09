# 分裂窓 probe (逐語)

元 repo path は
`output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py`。
SHA-256 `0128696a79035139ffaba3732cd3b20400eb231fb3124af98496665d70da455d` は、
`.md` 全体や fence 内文字列ではなく、移行前の元 `.py` bytes の digest である。

本移行は履歴 artifact の実装面是正であり、probe に証拠能力を与えるものではない。probe は既存テストより
弱く、[T-659] の裁定で証拠から外されている。実体は repo へ置かない。repo 外の byte 同一控えは
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py`。

```python
#!/usr/bin/env python3
"""[T-659] 分裂窓 probe: record 発行後・head 更新前の fresh load を temp copy 上で実測する。

live directory には一切書かない。repo の record 1 を temp へ copy し、
pegasus g2 への遷移 record 2 を build して置き、
(A) pinned head=1 (現行定数のまま) での load → fail-closed の逐語を観測
(B) pinned head=2 (更新後) での load → 受理を観測
"""
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "orchestrator"))
from campaign import env_contract as contract
from campaign import env_contract_activation as activation

live = REPO / "orchestrator/campaign/env_contract_activations"
state = contract.current_activation_state()
print(f"current head: serial={state.activation_serial} hash={state.activation_state_sha256[:16]}...")

rows = []
for env_tag in sorted(contract.GENERATIONS):
    gen = 2 if env_tag == "pegasus" else 1
    entry = contract.GENERATIONS[env_tag][gen - 1]
    rows.append(activation.ActiveContract(
        env_tag=env_tag, generation=gen,
        contract_sha256=entry.contract.contract_sha256,
    ))
doc = activation.build_activation_record(
    activation_serial=state.activation_serial + 1,
    previous_activation_state_sha256=state.activation_state_sha256,
    active_contracts=rows,
)
raw = activation.canonical_record_bytes(doc) + b"\n"

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
    tdir = Path(tmp) / "activations"
    shutil.copytree(live, tdir)
    (tdir / f"{doc['activation_serial']:08d}.json").write_bytes(raw)

    print("\n--- (A) fresh process, head 定数未更新 (expected head=1) ---")
    try:
        activation.load_activation_state(
            tdir,
            registered_contracts=contract._REGISTERED_CONTRACT_CATALOG,
            is_valid_registered_successor=contract._is_valid_activation_successor,
            expected_head_serial=contract._ACTIVATION_HEAD_SERIAL,
            expected_head_state_sha256=contract._ACTIVATION_HEAD_STATE_SHA256,
        )
        print("UNEXPECTED: 受理された (fail-open!)")
    except activation.ActivationRecordError as exc:
        print(f"fail-closed: ActivationRecordError: {exc}")

    print("\n--- (B) head 定数更新後 (expected head=2) ---")
    try:
        st = activation.load_activation_state(
            tdir,
            registered_contracts=contract._REGISTERED_CONTRACT_CATALOG,
            is_valid_registered_successor=contract._is_valid_activation_successor,
            expected_head_serial=doc["activation_serial"],
            expected_head_state_sha256=doc["activation_state_sha256"],
        )
        print(f"accepted: serial={st.activation_serial} active={[(r.env_tag, r.generation) for r in st.active_contracts]}")
    except activation.ActivationRecordError as exc:
        print(f"UNEXPECTED reject: {exc}")

    print("\n--- (C) 逆向き窓: head 定数だけ先に 2、record 未配備 (record 1 のみ) ---")
    tdir2 = Path(tmp) / "activations_old"
    shutil.copytree(live, tdir2)
    try:
        activation.load_activation_state(
            tdir2,
            registered_contracts=contract._REGISTERED_CONTRACT_CATALOG,
            is_valid_registered_successor=contract._is_valid_activation_successor,
            expected_head_serial=doc["activation_serial"],
            expected_head_state_sha256=doc["activation_state_sha256"],
        )
        print("UNEXPECTED: 受理された (fail-open!)")
    except activation.ActivationRecordError as exc:
        print(f"fail-closed: ActivationRecordError: {exc}")
```
