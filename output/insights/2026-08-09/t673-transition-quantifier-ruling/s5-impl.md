実装済み・未実走です。指定された 5 ファイルだけを新規作成し、本番コード・既存テスト・docs は変更せず、commit も作成していません。

### 作成ファイルと nodeid

- [test_t673_probe_b1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_t673_probe_b1.py) — 150 行

  - `::test_generation_quantifier_rejects_tail_downgrade[M2]`
  - 同 `[M4]`, `[M8]`, `[M16]`, `[M32]`, `[M64]`
  - `::test_successor_quantifier_rejects_tail_false[M2]`
  - 同 `[M4]`, `[M8]`, `[M16]`, `[M32]`, `[M64]`
  - `::test_generation_quantifier_rejects_downgrade_at_varied_position[first]`
  - 同 `[middle]`, `[last]`
  - `::test_successor_quantifier_rejects_false_at_varied_position[first]`
  - 同 `[middle]`, `[last]`

- [test_t673_probe_b2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_t673_probe_b2.py) — 115 行

  - `::test_generation_quantifier_property_rejects_tail_downgrade`
  - `::test_successor_quantifier_property_rejects_tail_false`

- [test_t673_probe_c1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_t673_probe_c1.py) — 149 行

  - `::test_activation_transition_quantifier_loops_are_direct_and_unsliced`

- [test_t673_probe_c3.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_t673_probe_c3.py) — 59 行

  - `::test_successor_rows_sentinel_rejects_slice_access`
  - `::test_transition_gate_iterates_successor_rows_without_slicing`

- [test_t673_probe_aprime.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_t673_probe_aprime.py) — 89 行

  - `::test_generation_quantifier_rejects_eighth_env_downgrade`
  - `::test_successor_quantifier_rejects_eighth_env_false`

合計 562 行、25 node です。

### 閉じない族

- B1: 最大 M=64 の有限掃引なので `[:N]` の `N >= 64`、M>64、任意位置全域は閉じません。
- B2: 生成領域が M=2〜64 のため `N >= 64` と M>64 は閉じません。Hypothesis 未導入時は意図どおり collection error です。
- C1: helper/islice/alias 内部や mutating helper による truncation、callback 弱化、caller 側量化は閉じません。変数 rename や無害な iterator wrapperには偽陽性になります。
- C3: 量化点 G の `successor_rows[:N]` は検出しますが、ローカル `changed` に sentinel を注入できないため量化点 P は閉じません。slice を使わない helper truncation も射程外です。
- A′: M=8 の末尾 witness のみなので、`N >= 8`、9 env 以上、末尾以外の位置族は閉じません。

### 静的確認と波及可能性

- 5 ファイルの AST 構文解析、test node 抽出、self-run harness の存在を静的確認しました。
- 本番実装と既存テストの SHA-256 は着手前後で一致しています。
- `_chain`、`_validate`、`activation`、`REPO_ROOT` は sibling importです。helper の改名・signature変更は候補 collection/testへ波及します。
- C1 は本番の private 関数名・変数名・loop 構造に依存します。
- C3 は private gate の signature と tuple subclass を受け入れる現行契約に依存します。
- B2 は Hypothesis のない通常環境で全体 collection を赤くします。skip には縮退しません。
- 5 ファイルとも plain-runner meta-test 用 `_run()` を持ちます。
- loader/issuer integration、既存 fixture、共有 helper、本番の受理・拒否集合は変更していません。xfail・skip・期待値緩和も追加していません。

## 総括

- B1、B2、C1、C3、A′を独立した 5 テストファイルとして実装しました。
- 本番・既存テスト・docs は不変、commit なしです。
- B1/B2/A′は有限 frontier、C1は別構文、C3は量化点Pを閉じません。
- 状態は「実装済み・未実走」であり、緑は主張しません。
- 親が最初に測るべき一手は、queue確認後に既存 A の4-node baselineを `tools/run_tests.py --force-dispatch` で取得することです。