## 結論

(P1)〜(P5) をすべて支持する。ただし (P1) は次のように具体化する。

- trigger record の個数は `stage == trigger_gate_binding.WAL_RECORD_STAGE` で数える。
- 唯一の stage record について、`payload` が exact `dict` で `trigger_gate_binding` を持つことを要求する。
- したがって受理には stage と payload の両方が必要になる。一方、payload が壊れた第 2 stage recordも個数に数えるため、2 件以上を誤って受理しない。
- root `kind` / root `trigger_binding` だけの旧形状は stage record 0 件となり FC05C で拒否する。互換層は設けない。

`wal.py`、`trigger_gate_binding.py`、`reflux_result_evidence.py` の変更は不要である。

## consumer の変更

[reflux_formal_consumer.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:32) 付近へ次を追加する。

```python
from . import trigger_gate_binding
from .reflux_ir import TriggerGateIR, encode_wire
from .wal import (
    TRIGGER_BINDING_COMMITMENT_KEY,
    TRIGGER_BINDING_PAYLOAD_KEY,
)
```

[reflux_formal_consumer.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:722) の `_wal_trigger()` は次の Python 本体に置き換える。

```python
def _wal_trigger(records: Sequence[dict]) -> object:
    stage_records = [
        record
        for record in records
        if record.get("stage") == trigger_gate_binding.WAL_RECORD_STAGE
    ]
    if len(stage_records) != 1:
        return None

    payload = stage_records[0].get("payload")
    if (
        type(payload) is not dict
        or TRIGGER_BINDING_PAYLOAD_KEY not in payload
    ):
        return None

    try:
        binding = trigger_gate_binding.validate_record(
            payload[TRIGGER_BINDING_PAYLOAD_KEY],
            require_source=False,
        )
    except trigger_gate_binding.TriggerGateBindingError:
        return None

    return {
        "mask": binding.mask,
        "candidate_wire": encode_wire(TriggerGateIR(binding.mask)),
        TRIGGER_BINDING_COMMITMENT_KEY: trigger_gate_binding.commitment(binding),
    }
```

根拠は次のとおり。

- producer の識別子は `trigger_gate_binding.WAL_RECORD_STAGE == "trigger_binding"` である（`trigger_gate_binding.py:31-32`）。
- producer は `to_record(binding)` を `payload["trigger_gate_binding"]` に置く（`wal.py:1595-1610`）。
- stage だけを個数判定に使うため、2 件目の stage record が payload 欠損でも「1 件」と誤認しない。
- `_resolve_ordered_wal()` は各 record の attempt を `_projection_attempt_id()` で既に確認する（`reflux_result_evidence.py:594-598,651-658`）。同 helper は root と payload の両方を読むため、production trigger の payload attempt と据え置く terminal の root attempt が共存できる。
- `_wal_field()` も root / payload 両対応である（`reflux_formal_consumer.py:785-789`）。ただし terminal の `kind` 検査（同 `823-831`）は今回変更しない。

## FC05C の比較と不正 raw

[reflux_formal_consumer.py:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/campaign/reflux_formal_consumer.py:731) の比較は構造を変えず、次の exact dict 比較を維持する。

```python
_require(
    FormalReasonCode.FC05C,
    _wal_trigger(resolved_item.ordered_wal.records)
    == item.record["trigger_binding"],
)
```

ledger 側は `{mask, candidate_wire, trigger_gate_binding_commitment}` の exact key 集合に制限済みである（`reflux_result_evidence.py:106-108,273-289`）。新しい `_wal_trigger()` も同じ 3 key だけを返すので、dict equality が key 集合と全値を同時に比較する。

`require_source=False` を支持する。

- 実測 production record は `source: null` であり、`True` はその正例を拒否する。
- `validate_record()` は `False` のとき source の null/non-null の双方を構造検査する（`trigger_gate_binding.py:205-239`）。
- source も `to_record()` の canonical JSON に含まれ（同 `172-197`）、`commitment()` が全 canonical bytes を hash する（同 `200-202`）。ledger が別 source を約束していれば commitment 不一致で FC05C になる。
- admission における source 必須性は `wal.validate_trigger_bindings()` が receipt の有無から決めている（`wal.py:1982-2007`）。formal consumer がその責務を重複して持つ必要はない。

不正 raw で `validate_record()` が投げる `TriggerGateBindingError` は `_wal_trigger()` 内で `None` に変換する。ledger の `trigger_binding` は dict なので比較が偽となり、`_require()`（consumer `300-302`）から FC05C になる。例外を捕らない場合、`evaluate_formal_origin()` は `_ContractFailure` しか reason result に変換しない（同 `1012-1018`）ため、P4 を満たさない。

## commitment の同一性

`commitment()` の入力経路は次の一意な鎖である。

1. `validate_record(raw)` が `TriggerGateBinding` を再構築する（`trigger_gate_binding.py:205-239`）。
2. `commitment(binding)` は `canonical_json(binding)` を SHA-256 化する（同 `190-202`）。
3. `canonical_json()` は `to_record(binding)` を sorted・compact JSON にする（同 `172-197`）。
4. production `log_trigger_binding()` も同じ `to_record(binding)` を WAL payload に書き、同じ `commitment(binding)` を返す（`wal.py:1605-1611`）。
5. 実呼び出し側はその戻り値を直後の `build_start.payload.trigger_gate_binding_commitment` に置く（`test_p3_s4_loop_trigger_gating.py:2361-2367`）。

逐語 record でも、返却値と `commitment(binding)` はともに `3971d4e1...b7029` と実測されている。producer 側の変更は不要である。

## fixture builder の変更

[reflux_origin_fixture_builder.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/reflux_origin_fixture_builder.py:1) の説明は、outer artifact の canonical bytes は引き続き独立計算する一方、trigger commitment は契約そのものなので production binding API から作る、と明確化する。

同ファイル `18` 付近に `trigger_gate_binding` を import し、`336-361` を次の構造にする。

```python
_FIXTURE_TRIGGER_NONCE = "a" * 64


def _fixture_trigger_gate_binding(
    mask: int,
) -> trigger_gate_binding.TriggerGateBinding:
    return trigger_gate_binding.TriggerGateBinding(
        mask=mask,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
        nonce=_FIXTURE_TRIGGER_NONCE,
        source=None,
    )


def _trigger_binding(mask: int) -> dict:
    binding = _fixture_trigger_gate_binding(mask)
    return {
        "mask": mask,
        "candidate_wire": _wire(mask),
        "trigger_gate_binding_commitment": (
            trigger_gate_binding.commitment(binding)
        ),
    }


def _wal_records(build_attempt_id: str, mask: int) -> list[dict]:
    binding = _fixture_trigger_gate_binding(mask)
    return [
        {
            "variant": "fixture-v",
            "stage": trigger_gate_binding.WAL_RECORD_STAGE,
            "env_tag": "fixture-env",
            "ts": 0,
            "payload": {
                "build_attempt_id": build_attempt_id,
                "trigger_gate_binding": trigger_gate_binding.to_record(binding),
            },
        },
        {
            "kind": "abort",
            "build_attempt_id": build_attempt_id,
            "candidate_attributable": True,
            "truncated": False,
            "witness_class_sha256s": [_CONSTRAINT_SHA256],
        },
    ]
```

`candidate_wire` は既存の独立 `_wire()`（同 `81-84`）を維持する。consumer と fixture の双方が `encode_wire()` を共有すると、ビット順反転の共通変異を見逃すためである。

nonce を `"a" * 64` に固定する理由は、fixture が暗号学的 freshness を証明する場ではなく、33 records と frozen baseline の再現可能 bytes が必要だからである。これにより mask 7 の raw binding は producer 逐語 record とも一致する。production の nonce 生成責務は `new_nonce()`（`trigger_gate_binding.py:167-169`）に残る。

旧 `_sha256({"mask", ...})` は raw binding の nonce、predicate、schema、source を約束していなかったため廃止する。raw binding と ledger projection の両方を同じ `TriggerGateBinding` から作り、ledger commitment は必ず `commitment(binding)` から導くのが最小かつ意味的に正しい変更である。

## fixture の canonical 経路

production 形状の trigger record は canonical list 経路をそのまま通る。

- `build_ordered_wal_projection()` は `records = _wal_records(...)` を list のまま `_canonical_bytes(records)` にする（fixture builder `364-378`）。
- repository 生成も同じく `_canonical_bytes(wal_records)` を source bytes にする（同 `584-597`）。
- resolver の `_canonical_wal_interval()` は source が JSON list なら `canonical_json_bytes(value)` を返す（`reflux_result_evidence.py:601-607`）。
- projection 側も `canonical_json_bytes(records)` にされ、両者が exact 比較される（同 `660-662`）。
- `canonical_json_bytes()` は nested `payload`、integer `ts`、raw binding を通常の JSON 値として canonical 化できる（`reflux_origin_artifacts.py:35-67`）。

`ts` は `0.0` ではなく `0` にする。fixture の leaf mutation helper は int を扱える一方、float は未対応だからである（`test_reflux_origin_fixture_builder.py:70-79`）。actual producer 正例が実時刻の float を別途覆う。

## 9 file の波及

grep 対象 9 file の結果と追随は次のとおり。

| file | 旧形状への依存 | 追随 |
|---|---|---|
| `test_p3_autonomous_workload_trial.py` | `10347-10385,10622-10629,10710-10780` が repository の全 evidence を formal consumer へ渡し P6Unavailable を期待する。consumer だけ先に変えると FC05C になる | source 編集なし。更新 fixture を使う既存 end-to-end 正例として焦点実行する |
| `test_reflux_origin_topology.py` | `12-30` は recovery envelope だけを利用し WAL を読まない | 変更なし |
| `test_reflux_source_closure.py` | `18-22,102-118` は authority と artifact の利用だけ | 変更なし |
| `test_reflux_origin_binding.py` | `187-250` は authority と artifact の利用だけ | 変更なし |
| `test_reflux_origin_artifacts.py` | `12-54` は result record を opaque JSON として自己 canonical 化するだけ | 変更なし |
| `test_reflux_formal_consumer.py` | `212-214,336-342` は全 fixture の正例。`530`、`551`、`591-593` は旧 trigger layout を直接参照。`289-290` は attempt を root にしか書かない | helper と 3 テストを production shape へ追随し、新規 FC05C テストを追加 |
| `test_reflux_origin_client.py` | `54,82-93` は launch inputs と authority manifest だけ | 変更なし |
| `test_trial_registry.py` | `43,849` は launch admission inputs だけ | 変更なし |
| `test_reflux_origin_fixture_builder.py` | `107-119` の frozen baseline が WAL、provenance、result record digest を pin。`301-326` は canonical interval を検査 | baseline 3 entry 更新。`316-325` に stage/payload shape の明示 assertion を追加 |

直接追随が必要な formal consumer test は次の 4 箇所で閉じる。

- `_rewrite_wal()` の `289-290`: root に key を無条件追加せず、既存 root `build_attempt_id` があれば root、なければ既存 `payload["build_attempt_id"]` を更新する。
- `test_fc05c_rejects_wal_trigger_binding_mismatch()` の `530`: raw の `payload["trigger_gate_binding"]["nonce"]` を別の valid 64 hex に変える。
- FC06 test の `549-552`: ledger projection を raw WAL に代入せず、donor record の projection から production raw binding をコピーする。
- FC07 test の `589-600`: trigger record を手書きせず、現在の projection の production trigger を保存して terminal だけ commit record に差し替える。

## baseline の更新

[reflux_origin_fixture_baseline.json:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/reflux_origin_fixture_baseline.json:7) では、独立再計算した次の 3 entry だけを更新する。

- `build_execution_provenance` (`7-9`): ledger commitment が変わる。
- `build_ordered_wal_projection` (`15-17`): trigger record と source ref digestが変わる。
- `build_result_evidence_record` (`23-25`): 上記 projection digest と ledger commitment が伝播する。

authority、source closure、recovery envelope、launch admission の entry は不変でなければならない。新しい byte 級 hash pin は追加せず、既存 frozen baseline の必要箇所だけを更新する。

## 正例テスト

[test_reflux_formal_consumer.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2257-formal-consumer-wal-shape/orchestrator/tests/test_reflux_formal_consumer.py:525) 付近へ 2 経路を追加する。

- 実 producer 経路:
  - fixture projection の raw binding を `validate_record(..., require_source=False)` で binding に戻す。
  - `CampaignLayout(root=...).ensure()` を作る。
  - `wal.log_trigger_binding()` を実際に呼ぶ。
  - 戻り commitment が ledger の `trigger_gate_binding_commitment` と一致することを確認する。
  - 書かれた JSONL の 1 行を `json.loads` し、fixture terminal とともに `_rewrite_wal()` で projection records に入れる。
  - `_evaluate(case)` が `P6Unavailable` まで到達することを確認する。

- 逐語 literal 経路:
  - `producer-verbatim-record.txt` の最初の `LINE:` にある JSON object を 1 本だけ文字列 literal として保持する。
  - `json.loads` 後、`_rewrite_wal()` が payload の attempt id だけを fixture attempt に合わせる。
  - mask 7、nonce `"a"*64`、predicate、source null は fixture raw と同一なので、ledger commitment も一致する。
  - full evaluation が `P6Unavailable` まで到達することを確認する。

実 producer 用の layout/binding 作成は `test_p3_s4_loop_trigger_gating.py:291-318,2355-2367` の既存パターンを踏襲する。

## 負例テスト

同じ FC05C 群へ次を追加する。

- 旧形状:
  - production trigger を `{"kind": "TriggerGateBinding", "build_attempt_id": ..., "trigger_binding": copy.deepcopy(record["trigger_binding"])}` に置換する。
  - 値は ledger と完全一致させたまま FC05C を期待する。
- stage 不一致:
  - valid payload を保持したまま `stage` を trigger stage 以外に変え、FC05C を期待する。
- duplicate:
  - valid production trigger を 2 本にし、FC05C を期待する。
- raw validation:
  - raw binding に余分な key を 1 個加え、例外漏出ではなく FC05C を期待する。
- mask-only mismatch:
  - ledger と execution provenance の `mask` だけを 31 に揃え、wire と commitment は WAL の mask 7 のままにして FC05C を期待する。
- commitment-only mismatch:
  - ledger と execution provenance の commitment だけを別の valid SHA-256 に揃え、FC05C を期待する。

旧形状テストは恒真ではない。旧 consumer、または「production と旧形状の両方を受ける」変異では、旧 record の `trigger_binding` が ledger と exact 一致して FC05C を通過し、残りの fixture も正しいため `P6Unavailable` に到達する。その結果、FC05C を期待するこの新テストだけが赤になる。既存の production 正例は両受け変異でも通り、既存 mismatch 負例も値不一致を拒否し続けるため、互換受理集合の拡大を検出できない。

## 変異の事前登録案

| 変異 | 殺すテスト | 識別理由 |
|---|---|---|
| root `kind` / `trigger_binding` を再び受理する | 新規「旧形状を FC05C」 | 旧値を ledger と一致させるため、互換受理時だけ P6Unavailable へ抜ける |
| selector を payload key の有無だけにする | 新規「非 trigger stage」 | raw と ledger は一致し、stage 判定を落とした場合だけ通る |
| mask の比較を落とす | 新規「ledger mask-only mismatch」 | wire、commitment、provenance は一致させ、FC05C の mask 差だけを残す |
| commitment の比較を落とす | 更新 `test_fc05c_rejects_wal_trigger_binding_mismatch` の valid nonce 差、または commitment-only test | mask と wire は同じで、派生 commitment だけが異なる |
| binding record が 2 本なら先頭を返す | 新規 duplicate test | 2 本とも valid・同値なので先頭返却変異だけが通る |
| wire のビット順を逆にする | 既存 `test_exact_fixture_contract_reaches_only_p6_unavailable` と 2 正例 | fixture `_wire()` は独立 LSB-first。mask 7 は `"11100"`、反転は `"00111"` で非対称なので殺せる |
| `validate_record()` を呼ばず既知 field だけを読む | 新規 raw extra-key test | correct 実装は exact raw key 集合で拒否し、手動射影変異は余分な key を無視して通る |
| stage record のうち payload が valid な最初の 1 件だけを返す | duplicate の一方を payload 不正にした追加 parameter case | stage 個数を先に数える correct 実装だけが必ず FC05C にする |

mask-only 変異が FC05C を通ると後段 FC06 で落ちる可能性があるが、テストは reason code を FC05C に固定するため変異を殺せる。commitment-only 変異は後段に同じ検査がないため、比較削除時は P6Unavailable まで到達する。

## 実装子の path allowlist

実装子が触ってよい path は、ちょうど次の 5 本とする。

- `orchestrator/campaign/reflux_formal_consumer.py`
- `orchestrator/tests/reflux_origin_fixture_builder.py`
- `orchestrator/tests/test_reflux_formal_consumer.py`
- `orchestrator/tests/test_reflux_origin_fixture_builder.py`
- `orchestrator/tests/reflux_origin_fixture_baseline.json`

`orchestrator/campaign/wal.py`、`orchestrator/campaign/trigger_gate_binding.py`、`orchestrator/campaign/reflux_result_evidence.py` は変更不要かつ scope 外である。これらの変更が必要になる事実は静的検査では見つからなかった。

## P1〜P5 の判断

- P1: 支持する。stage 個数を先に確定してから payload と raw を検査する点だけ明文化する。
- P2: 支持する。旧形状は値が正しくても FC05C。両受け禁止。
- P3: 支持する。terminal record と `terminal.get("kind")` は据え置く。
- P4: 支持する。`TriggerGateBindingError` を `None` に閉じ、既存 FC05C に落とす。
- P5: 支持する。producer 実呼び出しと逐語 literal の両方を full projection 経路で検査する。

## 検証計画

この read-only 段では pytest を実走しておらず、緑は主張しない。親は実装後、少なくとも formal consumer、fixture builder、p3 autonomous public-origin の各 test を `tools/run_tests.py` 経由で実行し、その後に fixture builder 利用 9 file を受入対象へ含める。

静的確認では、旧形状の直接参照は fixture builder 本体と `test_reflux_formal_consumer.py:530,551,591-593` に閉じており、producer-side 修理を要する箇所はない。

## 総括

- `_wal_trigger()` は唯一の trigger stage record の raw binding を検証し、ledger の exact 3 key へ射影する。
- fixture は production stage/payload 形状と canonical commitment を持ち、terminal は変更しない。
- producer 実呼び出し、逐語 literal、旧形状拒否、個数・field・raw validation の負例を追加する。
- 変更面は consumer と test/fixture の 5 pathだけで、`wal.py` を含む producer 側は不変とする。