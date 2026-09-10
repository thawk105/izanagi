## 総括

- **NO-GO**
- **must-fix: 3 件**
- 最重要所見: `failed ⊂ expected` が未固定で、単純な逆向き包含判定が全テストを生存する。
- 新設 node は恒真ではなく、MU-1 は 1193 行の比較だけを理由に赤くなる。
- MU-3 は全ファイル走行で既存 14 node が赤くなり、現状の事前登録では赤集合が未確定である。
- sandbox=read-only のため pytest・変異走行は行わず、コードと保存済み collection から静的に確定した。

### 所見 C-01 — 新設 node は完全一致判定まで到達し、恒真ではない

**主張:** `DW-M01` の単一理由性は MU-1 について成立する。手前の分岐による `"MISMATCH"` ではない。

**根拠:** 新設 node は `timed_out=False`、`artifact_error=None`、`rc=1`、非空 `failed` を渡す（`orchestrator/tests/test_mutation_harness.py:352-359`）。正常 rc は `{0, 1}`（`tools/mutation_harness.py:39`）なので、timeout、artifact、異常 rc、`rc != 0 and not failed`、`rc == 0` の全分岐を通過し、1191–1193 行の集合比較へ到達する（`tools/mutation_harness.py:1180-1193`）。

MU-1 の全ファイル走行時の赤は次の 1 node だけである。

`orchestrator/tests/test_mutation_harness.py::test_failed_nodes_strict_superset_never_counts_as_killed`

既存の互いに素な負例は包含が成立せず、等集合の正例は変異後も KILLED のため赤くならない（`orchestrator/tests/test_mutation_harness.py:205-230,341-362`）。

**成果物への影響:** MU-1 の kill は新設 node の strict-superset 判定だけに帰属でき、冗長 gate を kill 証拠から除外する必要はない。

**分類:** nit（攻撃不成立、修正不要）

**推奨:** MU-1 の期待 node を上記 1 node に固定する。

### 所見 C-02 — MU-3 は全ファイル走行では 14 本の冗長赤を生む

**主張:** MU-3 は確実に殺されるが、「既存 KILLED 系 node」という事前登録では不十分である。常に `"MISMATCH"` にすると、KILLED を経由する多数の運用テストが `main() == 0` や保存 status の不一致で赤くなる。

**根拠:** 等集合の status が `"MISMATCH"` になると `matches_expectation=False` になり、`main()` は 1 を返す（`tools/mutation_harness.py:1299-1311,2088`）。全ファイル走行で赤くなる既存 node は次の 14 本である。

```text
orchestrator/tests/test_mutation_harness.py::test_normal_run_uses_cumulative_replacements_and_full_failed_line
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_different_head
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_different_spec_hash
orchestrator/tests/test_mutation_harness.py::test_resume_reruns_parse_error_and_skips_terminal_record
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_incomplete_running_record_before_runner
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_duplicate_record_id
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_every_missing_terminal_and_baseline_field_before_runner
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_terminal_record_poison[rc-0-status \u304c rc/node/artifact evidence \u3068\u4e0d\u4e00\u81f4]
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_terminal_record_poison[expected_nodes-value1-\u73fe spec/evidence]
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_terminal_record_poison[injection_diff_sha256-0000000000000000000000000000000000000000000000000000000000000000-\u73fe spec/evidence]
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_terminal_record_poison[tool_sha256-0000000000000000000000000000000000000000000000000000000000000000-\u73fe spec/evidence]
orchestrator/tests/test_mutation_harness.py::test_resume_rejects_minimal_forged_terminal_record
orchestrator/tests/test_mutation_harness.py::test_apply_mutation_calls_restore_at_the_production_callsite
orchestrator/tests/test_mutation_harness.py::test_completed_record_is_flushed_before_next_runner_sigkill
```

該当呼出しは `orchestrator/tests/test_mutation_harness.py:205-232,434-609,693-708,795-820`。parametrize 接尾辞は `orchestrator/tests/test_mutation_harness.py:562-570` と保存済み collection（`output/insights/2026-08-05_t452-t453-clock-authority-impl/mutation-result.json:1096`）で確認した。

**成果物への影響:** 赤集合を 1 node として登録したまま全ファイルを走らせると、実赤が期待の真上位集合になり、MU-3 は KILLED でなく MISMATCH と記録される。

**分類:** **must-fix**

**推奨:** mutation runner の対象を新設 node と `test_normal_run_uses_cumulative_replacements_and_full_failed_line` の 2 node に限定する。その場合、MU-1 は新設 node のみ、MU-3 は正例 node のみが赤くなり、両方が単一理由になる。全ファイルを走らせるなら、上記 14 node を登録し、正例以外の 13 node は冗長 gate と明記する。

### 所見 C-03 — `failed ⊂ expected` 欠落により逆向き包含変異が生存する

**主張:** この象限は具体的な弱化変異の生存を許すため、非 scope のままでは済まない。

**根拠:** 現行集合例は等集合、互いに素、`expected ⊂ failed` の三つだけである（`orchestrator/tests/test_mutation_harness.py:205-230,341-362`）。したがって次の変異はすべて現行テストを通過する。

```python
failed_keys == expected_keys
# →
failed_keys <= expected_keys
```

同値な `expected_keys >= failed_keys` も生存する。さらに次の複合弱化も生存する。

```python
bool(failed_keys & expected_keys) and len(failed_keys) <= len(expected_keys)
```

等集合では真、互いに素では積集合が空、現行 strict-superset では長さ条件が偽になる一方、非空の `failed ⊂ expected` を誤って KILLED にする。

方向が逆の `failed_keys >= expected_keys`、単独の積集合非空判定は新設 node が殺す。単独の `len(failed_keys) == len(expected_keys)` は同じ要素数の互いに素な既存負例が殺す。

**成果物への影響:** 実赤が期待 node の真部分集合でも KILLED と認定でき、変異台帳の `status` と KILLED 件数が実行結果を偽る。

**分類:** **must-fix**

**推奨:** `expected={one,two}`、`failed={one}`、`rc=1` が `"MISMATCH"` になる直接 node を追加し、上記逆向き包含変異を事前登録する。

### 所見 C-04 — path 成分を捨てる `_match_key` 弱化が生存する

**主張:** 新設 node は parameter suffix の区別は固定するが、異なる test path の同名 node が衝突しないことを固定していない。

**根拠:** 現実装は path と test part の両方を保持するため、今回の `[one]` と `[two]` は異なる key になる（`tools/mutation_harness.py:798-813`）。したがって現実装による誤通過ではない。

一方、次の `_match_key` 差し替えは現行テストを生存する。

```python
def _match_key(node, repo):
    return _normalize_node(node, repo).partition("::")[2]
```

全比較例が同じ `tests/test_gate.py` を使うためである（`orchestrator/tests/test_mutation_harness.py:125,228-230,343-354`）。この変異では、期待 `tests/a.py::test_gate[one]` と実測 `tests/b.py::test_gate[one]` が同じ key になり、誤って KILLED になる。collection の実在検査は `_normalize_node` を使うため、この `_match_key` だけの弱化を遮らない（`tools/mutation_harness.py:976-986`）。

**成果物への影響:** 別ファイルの同名 test が赤でも期待 node の失敗として KILLED に数えられ、変異台帳の node 帰属が偽になる。

**分類:** **must-fix**

**推奨:** 同じ test part を持つ異なる二つの path を expected/failed に与え、MISMATCH を固定する直接 node を追加する。

### 所見 C-05 — impl.md の等集合正例の主張は成立する

**主張:** `test_normal_run_uses_cumulative_replacements_and_full_failed_line` は等集合かつ KILLED の正例を実際に固定している。

**根拠:** spec は期待 node `test_gate[one]` を構築する（`orchestrator/tests/test_mutation_harness.py:111-127,210-219`）。fixture の `VALUE=1` は `[one]` だけを失敗させる（同 `:74-85`）。テストは status `"KILLED"` と failed node が `[one]` だけであることを別々に assert する（同 `:223-230`）。

**成果物への影響:** MU-3 に対する通る正例は既存 node で固定済みであり、正例欠落による過剰拒否の見逃しはない。

**分類:** nit（攻撃不成立、修正不要）

**推奨:** MU-3 の焦点 node としてこの node を明示的に選択する。

### 所見 C-06 — 新設 node 単体の payload・fixture・命名には追加欠陥なし

**主張:** 揮発 payload、共有状態汚染、誤命名による攻撃は成立しない。

**根拠:** 期待値は固定 status と fixture 内の node 文字列だけで、hash・時刻・一時 path を焼き込んでいない（`orchestrator/tests/test_mutation_harness.py:352-362`）。`repo` fixture は `tmp_path` 配下へ独立 repo を作り、環境変数も `monkeypatch` 管理である（同 `:39-108`）。新設 node 本体は repo を書き換えず、名前も「failed が strict superset なら KILLED にしない」という固定内容を表す。現行 `_normalize_node` は `[one]` と `[two]` を保存するため、この入力自体の key 衝突もない（`tools/mutation_harness.py:805-813`）。

**成果物への影響:** この品質面から mutation ledger の値や受理集合が不安定になる経路はない。

**分類:** nit（修正不要）

**推奨:** C-03、C-04 の独立入力追加だけを行い、新設 node 自体は維持する。