# 親が段 1・段 6 で走らせた実測 script の逐語

`output/insights/` 直下の `.py` は AI provenance の実装面判定対象であり、Codex `role=author` を
要求する ([T-596] の裁定で現状維持)。本 wave のこれらは `DW-S01` が親へ課す前提実測と、
`DW-M04` / `DW-M08` が親へ課す変異 anchor・node の突き合わせのための測定器であって、
production の実装面ではない。Codex author を偽らずに逐語を残すため、
実行可能な原本を wave の job directory に置き、内容をここへ code block として凍結する。

原本の所在: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/`


## `s1-probe.py`

段 1 の生死実験 driver。合成 registry と合成 chain を `validate_activation_records` へ直接渡し、現行 loader の受理集合を測る。

```python
#!/usr/bin/env python3
"""段 1 前提実測: 現行 activation loader が遷移をどこまで受理するかを測る。

合成 registry と合成 record chain を validate_activation_records へ直接渡す。
production artifact は一切触らない (読み書きしない)。
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve()
REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import env_contract_activation as act  # noqa: E402


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


# 合成 registry: 2 env、各 3 世代まで登録済み。
REGISTRY = {
    "alpha": tuple((g, _hash(f"alpha-g{g}")) for g in (1, 2, 3)),
    "beta": tuple((g, _hash(f"beta-g{g}")) for g in (1, 2, 3)),
}


def rows(alpha_gen: int, beta_gen: int) -> list[act.ActiveContract]:
    return [
        act.ActiveContract(env_tag="alpha", generation=alpha_gen,
                           contract_sha256=_hash(f"alpha-g{alpha_gen}")),
        act.ActiveContract(env_tag="beta", generation=beta_gen,
                           contract_sha256=_hash(f"beta-g{beta_gen}")),
    ]


def chain(pairs: list[tuple[int, int]]) -> list[tuple[str, bytes]]:
    """(alpha_gen, beta_gen) の列から canonical な record chain bytes を作る。"""
    records: list[tuple[str, bytes]] = []
    previous: str | None = None
    for index, (a, b) in enumerate(pairs, start=1):
        document = act.build_activation_record(
            activation_serial=index,
            previous_activation_state_sha256=previous,
            active_contracts=rows(a, b),
        )
        raw = act.canonical_record_bytes(document) + b"\n"
        records.append((f"{index:08d}.json", raw))
        previous = document["activation_state_sha256"]
    return records


def probe(name: str, pairs: list[tuple[int, int]]) -> None:
    records = chain(pairs)
    head_doc_hash = None
    # 末尾 record の state hash を head として渡す (正しい head を与えたうえで
    # 遷移そのものが受理されるかだけを測る)。
    import json
    tail = json.loads(records[-1][1].decode())
    head_doc_hash = tail["activation_state_sha256"]
    try:
        state = act.validate_activation_records(
            records,
            registered_contracts=REGISTRY,
            expected_head_serial=len(records),
            expected_head_state_sha256=head_doc_hash,
        )
    except act.ActivationRecordError as exc:
        print(f"{name}: REJECTED — {exc}")
        return
    current = {row.env_tag: row.generation for row in state.active_contracts}
    print(f"{name}: ACCEPTED — serial={state.activation_serial} current={current}")


print(f"repo = {REPO}")
probe("A 単一 record (serial 1 のみ)          ", [(1, 1)])
probe("B no-op (両 env 据置)                  ", [(1, 1), (1, 1)])
probe("C 正常前進 (alpha +1, beta 据置)       ", [(1, 1), (2, 1)])
probe("D 相殺 (+2, -1)                        ", [(1, 2), (3, 1)])
probe("E skip 単独 (alpha +2)                 ", [(1, 1), (3, 1)])
probe("F downgrade 単独 (alpha -1)            ", [(2, 1), (1, 1)])
probe("G 連鎖末尾で no-op                     ", [(1, 1), (2, 1), (2, 1)])
probe("G2 連鎖途中で no-op (末尾は正当前進)   ", [(1, 1), (1, 1), (2, 1)])
probe("I 3 record の正当な前進 g1->g2->g3     ", [(1, 1), (2, 1), (3, 1)])
probe("J 相殺 (+1, -1)                        ", [(1, 2), (2, 1)])


# H (訂正): 段 3 レンズ A/B の指摘どおり、旧 H は C と同一入力だった。
# 本来測るべき「generation は +1 だが hash が前世代のまま」を直接組み立てる。
def probe_wrong_hash() -> None:
    import json
    first = act.build_activation_record(
        activation_serial=1,
        previous_activation_state_sha256=None,
        active_contracts=rows(1, 1),
    )
    second = act.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=[
            act.ActiveContract(env_tag="alpha", generation=2,
                               contract_sha256=_hash("alpha-g1")),  # 旧世代の hash
            act.ActiveContract(env_tag="beta", generation=1,
                               contract_sha256=_hash("beta-g1")),
        ],
    )
    records = [
        ("00000001.json", act.canonical_record_bytes(first) + b"\n"),
        ("00000002.json", act.canonical_record_bytes(second) + b"\n"),
    ]
    try:
        act.validate_activation_records(
            records,
            registered_contracts=REGISTRY,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )
    except act.ActivationRecordError as exc:
        print(f"H generation +1 だが hash は旧世代        : REJECTED — {exc}")
        return
    print("H generation +1 だが hash は旧世代        : ACCEPTED")


probe_wrong_hash()
```

## `verify-anchors.py`

変異 spec の置換 anchor が対象ファイル中で一意かを実測する (`DW-M04`)。同一 file への複数置換は累積適用したうえで一意性を測る。

```python
#!/usr/bin/env python3
"""変異 spec の置換 anchor が対象ファイル中で一意かを実測する (DW-M04)。"""
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
bad = 0
for mutation in spec["mutations"]:
    # 累積適用: 同一 file への複数置換は、前の置換を適用した後の内容で一意性を測る。
    contents: dict[str, str] = {}
    for index, replacement in enumerate(mutation["replacements"]):
        rel = replacement["file"]
        if rel not in contents:
            contents[rel] = (repo / rel).read_text(encoding="utf-8")
        count = contents[rel].count(replacement["old"])
        status = "OK" if count == 1 else "NG"
        if count != 1:
            bad += 1
        print(f"{status} {mutation['id']} r{index} {rel} count={count}")
        contents[rel] = contents[rel].replace(replacement["old"], replacement["new"], 1)
print(f"non-unique={bad}")
sys.exit(1 if bad else 0)
```

## `compare-nodes.py`

事前登録の期待 node と台帳の記録 node を正規化して突き合わせる (`DW-M08` / F33)。期待が記録に含まれない変異があれば非 0 で終わる。

```python
#!/usr/bin/env python3
"""事前登録の期待 node と記録 node を同じ形式へ正規化して突き合わせる (DW-M08/F33)。"""
import json
import sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
ledger = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected_by_id = {m["id"]: set(m["expected_nodes"]) for m in spec["mutations"]}
recorded = {}
for entry in ledger["mutations"]:
    nodes = entry.get("failed_nodes") or entry.get("observed_nodes") or []
    recorded[entry["id"]] = (entry.get("status"), entry.get("rc"), set(nodes))

problems = 0
for mutation_id, expected in expected_by_id.items():
    status, rc, observed = recorded[mutation_id]
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    verdict = "期待⊆記録" if not missing else "期待に記録されない node がある"
    if missing:
        problems += 1
    print(f"{mutation_id}: status={status} rc={rc} 記録={len(observed)} 期待={len(expected)} → {verdict}")
    if missing:
        print(f"  MISSING: {missing}")
    if extra:
        print(f"  EXTRA  : {[n.split('::')[-1] for n in extra]}")
print(f"\n期待が記録に含まれない変異の数 = {problems}")
sys.exit(1 if problems else 0)
```
