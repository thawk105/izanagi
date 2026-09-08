## プラン

1. [tools/pegasus/probes/t316_sandbox_backend_probe.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:121) — 既存の module 定数群の直後に、probe が受理する 2 組だけを private 定数として置く。

変更前:

```python
_NETWORK_CONNECT_CATEGORIES = frozenset(
    {"network_direct_ip", "network_proxy", "network"}
)
```

変更後:

```python
_NETWORK_CONNECT_CATEGORIES = frozenset(
    {"network_direct_ip", "network_proxy", "network"}
)
_INERT_CONDITION_GATE_PAIRS = frozenset({
    (
        "stock-inert-preprocess-identical",
        "stock-inert-identity",
    ),
    (
        "stock-inert-preprocess-root-location-only",
        "stock-inert-root-location-only",
    ),
})
```

gate 本体の `status_contract` を参照・移設しない。そこには禁止対象の `requested-default-preprocess-different` も含まれるため、probe 固有の受理境界として 2 組だけを明記する。

2. [tools/pegasus/probes/t316_sandbox_backend_probe.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:323) — `_condition_gate_receipt_summary` の supply entry に scalar の `comparison` を追加する。

変更前:

```python
{
    "arm": supply.arm,
    "record_digest": supply.record_digest,
    "terminal_status": supply.terminal_status,
    "reason_code": supply.reason_code,
},
```

変更後:

```python
{
    "arm": supply.arm,
    "record_digest": supply.record_digest,
    "terminal_status": supply.terminal_status,
    "reason_code": supply.reason_code,
    "comparison": supply.evidence["comparison"],
},
```

`evidence` mapping 全体は出さず、発火した組の第 2 座標だけを結論 field として残す。

3. [tools/pegasus/probes/t316_sandbox_backend_probe.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:346) — gate で再 admission した後に 2 要素 tuple を作り、組集合への membership で判定する。

変更前:

```python
return (
    observed == expected
    ...
    and supply.terminal_status == "green"
    and supply.reason_code == "stock-inert-preprocess-identical"
    and supply.evidence.get("comparison") == "stock-inert-identity"
    and meaning.terminal_status == "unestablished"
    ...
)
```

変更後:

```python
supply_pair = (
    supply.reason_code,
    supply.evidence["comparison"],
)
return (
    observed == expected
    and receipt_summary == _condition_gate_receipt_summary(value)
    and observed.admitted is True
    and supply.driver_id == "tools.pegasus.probes.t316_sandbox_backend_probe"
    and supply.macro == meaning.macro == "BACKOFF_FIXED"
    and supply.terminal_status == "green"
    and supply_pair in _INERT_CONDITION_GATE_PAIRS
    and meaning.terminal_status == "unestablished"
    and meaning.reason_code == "meaning-witness-undeclared"
)
```

`require_condition_gate_family`、`observed == expected`、receipt summary 一致など、既存条件はすべて残す。

4. [orchestrator/tests/test_t316_sandbox_probe.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:137) — test fixture を次のように補強する。

- 既存 `_condition_gate_family(comparison)` は identity 系と legacy vocabulary 負例のため残す。
- `_root_location_only_condition_gate_family(tmp_path)` を直後に追加する。
- `supplied` fixture を `tmp_path` へコピーし、requested/stock 双方の `include/backoff.hh` に同じ `__FILE__` 行を追加する。
- production と同じ driver、`BACKOFF_FIXED=-1`、`stock_comparison=True` で `evaluate_define_supply_effectuation` を実行する。
- reason/comparison が root-location-only の組であることを fixture 内でも assert し、実 record の meaning arm と admission を生成する。
- 禁止された第 3 reason の負例用に、同じ production evaluator から `requested_value=5, default_value=-1` の genuine family を生成する cached helper を追加する。

root-location-only の核:

```python
root = tmp_path / "condition-gate-root-location-only"
shutil.copytree(source_fixture, root)
for header in (
    root / "include/backoff.hh",
    root / "stock/include/backoff.hh",
):
    header.write_text(
        header.read_text(encoding="utf-8")
        + '    static constexpr const char *condition_gate_file = __FILE__;\n',
        encoding="utf-8",
    )
```

これは [test_condition_meaning_gate.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py:646) の既存正例と同じ生成条件であり、root 差分 field を含む genuine issued record を得られる。

5. [orchestrator/tests/test_t316_sandbox_probe.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:185) — `_condition_gate_receipts` は任意の genuine family を受け取れる形にし、supply entry に次を追加する。

```python
"reason_code": supply.reason_code,
"comparison": supply.evidence["comparison"],
```

既存 assertion の緩和・反転はせず、fixture が作る受領証に今回必須となる field を純増させる。

## 決めた点と根拠

1. 受理集合は probe 内の `frozenset[tuple[str, str]]` とする。理由コード集合と comparison 集合を別々に検査しないため、二つの交叉は membership で確実に弾かれる。第 3 reason は定数に存在しないので、gate admission が green でも probe では不受理になる。

2. 親の provisional 案どおり、supply receipt entry へ `comparison` を明示する。理由コードだけでも現行 gate 表から組を逆算できるが、それでは受領証単体が第 2 座標を保持せず、D1625 の「発火した組を記録する」を弱く解釈することになる。scalar の `comparison` なら issuer capability や詳細 evidence を漏らさず、既存の `"evidence" not in item` も維持できる。

3. root-location-only 正例は、既存 `_condition_gate_family("stock-inert-root-location-only")` では作れない。同 helper は reason を identity に固定した record の comparison だけを差し替えるため、gate の [status_contract:3691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3691) で `admission-contract-invalid` になる。fixture をコピーして `__FILE__` を双方に加え、production evaluator に reason、comparison、root 差分 evidence、issuer capability を一緒に発行させる必要がある。

4. 参照関係は静的 AST と明示参照から引いた。gate 本体の既存 test は変更しない。root-location-only の生成方法を参照する既存 node は `orchestrator/tests/test_condition_meaning_gate.py::test_inert_root_location_only_difference_is_green[BACKOFF_FIXED=-1]` である。

## 追加・変更する test

追加位置は [test_t316_sandbox_probe.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:869) の condition-gate test 群内、legacy vocabulary test の前後とする。

- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[identity]`

  Genuine identity family と、`comparison` を含む手書き receipt summary を渡し、S6 が `go` になることを確認する。旧経路の退行と receipt への comparison 追加漏れを殺す。

- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`

  `tmp_path` 上で生成した genuine root-location-only family を使う。reason/comparison、admission、receipt の comparison を明示確認して S6 `go` を要求する。現行の 1 組固定変異を殺す。

- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`

  二つの genuine family から reason 側と evidence/comparison 側を交叉させる。通常の再 admission で不受理になることに加え、`require_condition_gate_family` をその test 内だけ admission replay seam に差し替えても `_condition_gate_family_valid` が `False` になることを確認する。後者により、gate の先行拒否だけで test が通る空振りを避け、probe を「reason は二択、comparison も二択」という直積判定へ変える変異を殺す。

- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_requested_default_preprocess_difference`

  Production evaluator が発行し、gate 自体は admit する genuine `requested-default-preprocess-different` family を渡す。probe は `S6_CONDITION_GATE_UNPROVEN` を返すことを要求し、gate の 3 行すべてを probe の受理集合へ流用する変異を殺す。

変更する既存 fixture は `_condition_gate_receipts` の supply entry への `comparison` 純増だけであり、既存 test 本体の期待値、skip、判定方向は変更しない。

## 波及と未解決

`_condition_gate_receipts → _good_s6` の直接 consumer:

- `test_stage_judges_reject_injected_bad_observations`
- `test_s6_injected_success_without_condition_records_is_not_go`
- `test_s6_unissued_condition_records_cannot_replace_live_family`
- `test_s6_receipt_summary_must_match_live_condition_conclusions`
- `test_s6_rejects_legacy_stock_identity_vocabulary`
- `test_injected_observer_flows_through_judge_and_overall`
- `test_r3_1_coverage_does_not_overclaim`

`_good_s6 → _good_stages` の推移的 consumer:

- `test_s5_build_system_side_effect_keeps_overall_no_go_with_write_absence`
- `test_each_s3_category_failure_reaches_stage_and_overall`
- `test_s3_scratch_positive_control_failure_reaches_stage_and_overall`
- `test_each_s5_category_failure_reaches_stage_and_overall`
- `test_containment_discharge_when_all_containment_stages_go`
- `test_performance_discharge_when_s7_go`
- `test_containment_discharge_requires_each_containment_stage_go`
- `test_performance_discharge_requires_s7_go`

`test_r3_1_coverage_does_not_overclaim` の既存 `"evidence" not in item` はそのまま残り、新しい scalar `comparison` と両立する。gate 本体および gate test への変更はない。未解決の設計判断はない。pytest は依頼どおり実行せず、親の実測対象とする。

## 総括

probe 固有の受理条件を、D1625 の 2 組だけからなる tuple 集合へ置き換える。  
受領証には supply の `comparison` を明示し、`evidence` mapping 自体は出さない。  
root-location-only 正例は `__FILE__` を含むコピー fixture から genuine record を発行して作る。  
二つの交叉と第 3 reason を独立に拒否する test を追加し、gate 本体は一切変更しない。