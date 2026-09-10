## 総括

実装順は role 本文 2 件、source SHA pin 2 件、adapter 2 件、既存 originless baseline の planner SHA 追随である。  
最大の異議は、`planner-v4.md:35` だけを削除すると `abort_rate_pct` の trailing comma が残り、入力例が不正 JSON になる点である。`:34` の comma も除く必要がある。  
また親 scope は、planner role bytes を live に読む `test_reflux_originless_compatibility.py` の baseline 追随を漏らしている。厳密な親 scope のままでは受入全走は緑にならない。  
`p3_s4_loop.py` の二重 fail-closed と `_DELTA_PCT_LIVE = False` は一切変更しない。

## 編集計画 (file:line 粒度)

行番号は現在の tree 基準。

1. `.claude/agents/coder-v4-autonomous.md:47`

変更前:

```json
    { "iteration": 1, "result": "fail", "delta_pct": -1.2 }
```

変更後:

```json
    { "iteration": 1, "result": "fail", "delta_pct": null }
```

変更後の行は `.claude/agents/coder-v4-autonomous-sort.md:52` と LF を含めて byte 一致させる。想定 source SHA-256:

```text
ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806
```

2. `.claude/agents/planner-v4.md:34-35`

P1 の「field 削除」を有効な JSON として実装するには 2 行をまとめて編集する。

変更前:

```json
    "abort_rate_pct": 7.9,
    "last_delta_pct": -1.2
```

変更後:

```json
    "abort_rate_pct": 7.9
```

`last_delta_pct` の行だけを消す案は採用しない。`tools/check_codex_agents.py:140-158` が入力例を `json.loads()` するため trailing comma で拒否される。想定 source SHA-256:

```text
523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4
```

3. `orchestrator/codex_roles/review_ledger.py:25`

変更前:

```python
    "coder-v4-autonomous": "4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d",
```

変更後:

```python
    "coder-v4-autonomous": "ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806",
```

4. `orchestrator/codex_roles/review_ledger.py:41`

変更前:

```python
    "planner-v4": "0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",
```

変更後:

```python
    "planner-v4": "523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4",
```

5. `.codex/role-adapters/coder-v4-autonomous.json`

`spec.expected_adapters()` の出力でファイル全体を再生成する。JSON field 単位では次の 4 箇所だけが変わる。

- `:8`, `developer_instructions` 内の物理 file 上の逐語部分:

```text
{ \"iteration\": 1, \"result\": \"fail\", \"delta_pct\": -1.2 }
```

から:

```text
{ \"iteration\": 1, \"result\": \"fail\", \"delta_pct\": null }
```

- `:164`, `review_ledger/source_file_sha256`:

```text
4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d
```

から:

```text
ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806
```

- `:175`, `semantic_digest`:

```text
564287c890c1e29bf2b0e85f118ad5021b8154121eef224d35ccf63cdc0057c7
```

から:

```text
4e8cd61cf2ae1ea8bc63cee16a67e1697dad2e3a93323f935a97d4e724500150
```

- `:183`, `source/sha256`: source SHA と同じ旧値から新値へ。

再生成後の adapter file SHA-256:

```text
70cb1be6d2e067a751b70618ca20d8bf44f23b6c157f0445b9af50854372b54a
```

6. `.codex/role-adapters/planner-v4.json`

同様に全体を期待 bytes から再生成する。変わる field は次の 4 件だけ。

- `:8`, `developer_instructions` 内の物理 file 上の逐語部分:

```text
\"abort_rate_pct\": 7.9,\n    \"last_delta_pct\": -1.2\n
```

から:

```text
\"abort_rate_pct\": 7.9\n
```

- `:124`, `review_ledger/source_file_sha256`:

```text
0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e
```

から:

```text
523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4
```

- `:135`, `semantic_digest`:

```text
ac06f0f644b3e4b0964d39bd2aaa9f116e3e116343b0a33050ddabb3d44bbe1f
```

から:

```text
8721278d422376076116d4e4a91211c7237c1761ef441590879b7d989b55bdfb
```

- `:143`, `source/sha256`: source SHA と同じ旧値から新値へ。

再生成後の adapter file SHA-256:

```text
1b09496016819b12aef99b82034fe19ceccb786e871fbcf7ca9130c4985431ea
```

7. 親 scope 修正が承認された場合の必須追随:
`orchestrator/tests/test_reflux_originless_compatibility.py:574-598`

現在の `_extend_t2145_role_source_baseline(...)` 呼出しと `_assert_same_structure` の間へ、次を挿入する。

```python
def _extend_t2249_planner_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2249 planner source pin in live originless output."""
    old = "0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e"
    new = "523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4"
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in journal_rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    report_rows = baseline[
        "reports/*/cells/*/generations/*/roles/planner/"
        "provenance/role_file_sha256"
    ]
    assert report_rows == [[old, 6]]
    report_rows[0][0] = new


_extend_t2249_planner_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)
```

これは保存済み `output/` を変更するものではない。live fixture が記録する reviewed planner source SHA だけを既存 compatibility baseline へ追随させる。先例は同 file `:574-595` の T-2145 auditor 更新である。

編集順序は次で固定する。

1. coder role を `null` へ変更。
2. planner role から field と直前 comma を除去。
3. `sha256sum` で両 source hash を求め、上記値と一致確認。
4. `review_ledger.py:25,41` を更新。
5. `expected_adapters()` が load 可能になった後、対象 adapter 2 件を再生成。
6. adapter の期待 byte 一致と上記 4 field 以外が不変であることを確認。
7. scope 修正を受け入れる場合、originless baseline の追随 helper を追加。
8. focused tests、checker、親の受入全走の順に実走する。

## 動く hash と動かない hash

動く ledger 定数は `SOURCE_FILE_SHA256` の対象 2 entryだけである。

- `spec.py:582-590` は `source.path.read_bytes()` の SHA-256 を `SOURCE_FILE_SHA256[name]` と比較する。本文 bytes が変わるため、coder と planner の 2 entry は必ず動く。
- 他の 12 role の `SOURCE_FILE_SHA256` は動かない。

動かない定数:

- `ROLE_MANIFEST_SHA256`: 不変。`spec.py:566-577` は `manifest.json` の role entry の canonical JSON を算出元とする。role Markdown 本文は算出元に含まれず、manifest も scope 内で変更しない。
- `DESCRIPTION_SHA256`: 不変。`spec.py:584-593` は frontmatter から得た `source.description` だけを hash する。本文だけを変更し、frontmatter は不変。
- `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256`: 不変。`spec.py:550-557` は `spec.DEVELOPER_INSTRUCTION_TEMPLATE` 自体の exact bytes を hash する。今回変わるのは `{body}` へ埋める role 本文であり template ではない。
- `SCHEMA_SHA256`: coder/planner とも input/output の両方が不変。`spec.py:655-672` は manifest の `input_schema` と `output_schema` の canonical JSON を hash する。coder の `whiteboard` は open な array、planner の `current_perf` は open object であり、例中の値または nested key 削除は schema 変更ではない。
- `ROLE_IO_CONTRACTS`: 不変。`spec.py:673-683` が照合する top-level required fields は coder、planner とも変わらない。
- `EXPECTED_ROLE_COUNT`: 不変。role の追加・削除はない。

adapter 側で `semantic_digest` は動く。`spec.py:745-792` の contract に `SOURCE_FILE_SHA256` が `:771` で入り、role body bytes も `:790-791` で直接入るためである。

adapter の完全な変更 field 集合は両 role とも次の 4 件で、それ以外は不変である。

```text
/developer_instructions
/review_ledger/source_file_sha256
/semantic_digest
/source/sha256
```

根拠:

- `developer_instructions`: `spec.py:795-800` が `spec.source.body` を template へ埋め込む。
- `review_ledger/source_file_sha256`: `spec.py:815-834`、特に `:820`。
- `semantic_digest`: `spec.py:745-792` と renderer の `:837`。
- `source/sha256`: `spec.py:803-840`、特に source text hash の `:806` と格納の `:840`。

`source/description`、model、effort、tools、input/output schema、I/O contract、manifest/template/description/schema hashes、policy、consumer、`mode`、`runtime_activation` を含む他の field はすべて不変である。

## adapter 再生成手順

`tools/check_codex_agents.py:349` に隠し `--write` option は残っているが、`:352-358` が必ず error と rc=1 を返すため使用しない。

role Markdown と `SOURCE_FILE_SHA256` の更新後、repository root から次を実行する。stdin script であり、repo 内へ新しい script/probe file は追加しない。

```bash
python3 - <<'PY'
from pathlib import Path

from orchestrator.codex_roles.spec import (
    expected_adapters,
    get_role_spec,
    render_adapter,
)

root = Path.cwd().resolve()
roles = (
    "coder-v4-autonomous",
    "planner-v4",
)
targets = {
    role: root / ".codex" / "role-adapters" / f"{role}.json"
    for role in roles
}

expected = expected_adapters(root)

for role, target in targets.items():
    if target not in expected:
        raise SystemExit(f"expected adapter inventory に無い: {target}")
    if target.is_symlink() or not target.is_file():
        raise SystemExit(f"既存 regular file でない: {target}")
    direct = render_adapter(get_role_spec(role, root))
    if expected[target] != direct:
        raise SystemExit(f"expected_adapters/render_adapter 不一致: {role}")

for target in targets.values():
    target.write_bytes(expected[target].encode("utf-8"))

for target in targets.values():
    if target.read_bytes() != expected[target].encode("utf-8"):
        raise SystemExit(f"write 後の期待 byte 不一致: {target}")
PY
```

`expected_adapters()` は `spec.py:876-881` で全 role を load し、各 adapter を `render_adapter()` へ渡す。したがって ledger 更新前に実行すると `spec.py:587-590` の source pin drift で止まる。これが role、SHA、ledger、adapter の順序を固定する理由である。

再生成後に確認する file hash:

```text
.codex/role-adapters/coder-v4-autonomous.json
70cb1be6d2e067a751b70618ca20d8bf44f23b6c157f0445b9af50854372b54a

.codex/role-adapters/planner-v4.json
1b09496016819b12aef99b82034fe19ceccb786e871fbcf7ca9130c4985431ea
```

加えて coder 行の sibling parity は次で確認する。

```bash
cmp \
  <(sed -n '47p' .claude/agents/coder-v4-autonomous.md) \
  <(sed -n '52p' .claude/agents/coder-v4-autonomous-sort.md)
```

## テスト nodeid

変更ファイル名、定数名、renderer 呼出しの参照を `orchestrator/tests/` から逆引きした focused nodeid:

```text
orchestrator/tests/test_codex_agents.py::test_review_ledger_independently_pins_all_fourteen_sources_and_io_contracts
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation
orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override
orchestrator/tests/test_codex_agents.py::test_backoff_literal_only_contract_has_role_manifest_adapter_parity
orchestrator/tests/test_codex_agents.py::test_direct_role_source_input_shape_parity_covers_top_and_nested_fields
```

参照根拠:

- source/ledger pin: `test_codex_agents.py:134-164`
- renderer byte parity: `:166-168` から checker `:217-246`
- adapter 内 ledger: `:171-203`
- body exact embedding: `:223-237`
- coder role と coder adapter の直接参照: `:1049-1073`
- planner 入力 JSON 例の parse/shape: `:1408-1420`

planner source bytes の実 consumer も走らせる。

```text
orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_harness_rebuild_is_deterministic_control
orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set
```

`p3_autonomous_workload_trial.py:261-266` の `ROLE_FILES` は planner を `planner-v4.md` へ結び、`:680-683` の `FixtureRoleProvider` が実 bytes の SHA を記録する。compatibility test は `test_reflux_originless_compatibility.py:41-73` でその fixture run を再構築し、`:1264-1269` で非 volatile leaf を frozen baseline と比較する。

変更禁止の二重防壁を維持したことの focused 非回帰:

```text
orchestrator/tests/test_p3_s4_loop.py::test_state_from_dict_rejects_nonnull_delta_pct
orchestrator/tests/test_p3_s4_loop.py::test_whiteboard_for_planner_rejects_nonnull_delta_pct
```

それぞれ `p3_s4_loop.py:1292-1296` と `:1123-1129` の独立拒否経路を通る。テストは必ず repository 規律どおり `tools/run_tests.py` 経由で実行し、直接 `pytest` は起動しない。本 plan では実走していない。

## 変異候補

以下の期待集合は、上記の `test_codex_agents.py` focused 6 nodeと originless 2 nodeを同時に指定した mutation run 内での完全集合である。

1. M1-C: coder source と source pin の対を旧値へ戻し、adapter は新値のまま残す。

変異位置:

```text
.claude/agents/coder-v4-autonomous.md:47
orchestrator/codex_roles/review_ledger.py:25
```

期待する赤の完全集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation
orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override
```

source と pin を一緒に戻すため import 時の source-pin gate は通る。coder の whiteboard schema は nested item を閉じていないため `-1.2` 自体も前段では拒否されない。赤理由は「新 adapter が旧 source から導かれる期待 adapter と一致しない」に絞れる。

2. M1-P: planner source と source pin の対を旧値へ戻し、adapter と T-2249 baseline 追随は新値のまま残す。

変異位置:

```text
.claude/agents/planner-v4.md:34-35
orchestrator/codex_roles/review_ledger.py:41
```

field と comma をともに旧形へ戻す。期待する赤の完全集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation
orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override
orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set
```

source/pin と JSON parse は前段を通る。最初の 3 件は stale adapter、最後は live planner provenance SHA が T-2249 baseline と異なることが理由であり、別経路だがどちらも同じ source-byte rollback に帰属できる。

3. M2-C/M2-P: 各 adapter の `developer_instructions` 内だけを旧本文へ戻す。

変異位置:

```text
.codex/role-adapters/coder-v4-autonomous.json:8
.codex/role-adapters/planner-v4.json:8
```

各変異の期待赤集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override
```

strict JSON load は通り、期待 byte と exact body embedding で拒否される。前後に同じ入力を拒否する別 semantic layer はなく、原因は埋め込み本文 drift に絞れる。

4. M3-C/M3-P: 各 adapter の `review_ledger/source_file_sha256` だけを旧値へ戻す。

変異位置:

```text
.codex/role-adapters/coder-v4-autonomous.json:164
.codex/role-adapters/planner-v4.json:124
```

各変異の期待赤集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation
```

source/ledger の load と JSON parse は通る。adapter metadata equality が直接の赤理由となる。

5. M4-C/M4-P: 各 adapter の `source/sha256` だけを旧値へ戻す。

変異位置:

```text
.codex/role-adapters/coder-v4-autonomous.json:183
.codex/role-adapters/planner-v4.json:143
```

各変異の期待赤集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
```

この field 専用 assertion はなく、renderer byte parity が唯一の拒否層である。赤理由は一つだが field 固有の診断ではない。

6. M5-C/M5-P: 各 adapter の `semantic_digest` だけを旧値へ戻す。

変異位置:

```text
.codex/role-adapters/coder-v4-autonomous.json:175
.codex/role-adapters/planner-v4.json:135
```

各変異の期待赤集合:

```text
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
```

これも renderer byte parity が唯一の拒否層であり、原因は単一 field drift に絞れる。

7. M6: T-2249 originless baseline 追随 call を除去する。

変異位置:

```text
orchestrator/tests/test_reflux_originless_compatibility.py:574-598 の追加 block
```

期待赤の完全集合:

```text
orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set
```

deterministic-control は current/current を比較するので通り、pre-wave baseline 比較だけが planner provenance SHA 差で赤になる。拒否理由は一つに絞れる。

注意点として、coder source、ledger pin、adapter の全 surface を一緒に旧 bytes へ戻す lockstep 変異は既存 focused testsを生存する見込みである。既存テストは coder 例の `delta_pct is None` を独立 literal として pin していない。新規検査を scope 外とする以上、この coordinated semantic rollback を KILLED と登録してはならない。

## 親 brief への異議

1. `brief.md:19` と P1 は意味上の「`last_delta_pct` field を存在させない」という裁定としては妥当。ただし物理編集を `planner-v4.md:35` の行削除だけとする記述は誤り。`:34` の comma 除去が不可欠である。

2. `brief.md:39-41` の「凍結 baseline は動かない」は保存済み `output/` については正しいが、live fixture を再構築する `test_reflux_originless_compatibility.py` には当てはまらない。同 test の baseline は planner SHA を非 volatile leaf として保持し、既存 T-2145 更新も `:574-595` で明示追随している。T-2249 planner SHA にも同じ追随が必要である。

3. `brief.md:49` の「4 file」は物理 file 数として誤り。親の列挙だけでも role 2、ledger 1、adapter 2 の計 5 fileであり、originless baseline 追随を含めると 6 fileになる。

4. runtime leak の表現には限定が必要である。`p3_s4_loop.py:1133-1159` は whiteboard、任意 knowledge input、policy hint を生成するが、`current_perf` と `leading_indicators` の合成は明示的に責務外である。今回直すのは、loop 自体の漏出経路ではなく role の入力契約例と将来の埋め込み prompt である。

5. 現行 autonomous workload trial の coder は `p3_autonomous_workload_trial.py:263-265` の trigger-gating roleであり、`coder-v4-autonomous.md` ではない。planner は同 file `:261-263` で実 consumer を持つ。このため originless baseline 追随が必要なのは planner SHA だけである。

## 未確定・要裁定

- P1 を「`:35` 削除」に加えて「`:34` の trailing comma 除去を含む」と確定する必要がある。含めない場合は不正 JSON となり実装不能。
- 親 scope を `test_reflux_originless_compatibility.py` の既存 baseline 追随まで広げる必要がある。広げない場合、受入全走緑という brief 自身の完了条件と両立しない。
- coder の `delta_pct: null` を独立に pin する新規 semantic test は現 scope では追加しない。そのため全 surface の coordinated rollback は SURVIVED と扱う。これも KILLED 必須にするなら、検査新設を禁じた scope の別裁定が必要。