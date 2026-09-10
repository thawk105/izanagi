## 総括

- 裁定 A2・A5 と erratum E1 に整合する実装を、指定された 2 ファイルだけへ反映した。
- 型 A/B、逆順型 B、片側 veto、無効な `id`、真の重複、pin 経路をテスト化した。
- 再矛盾は検出していない。production の no-touch 領域も差分なし。
- pytest は実行基盤の `qstat -Q` 失敗により開始できず、実装済み・未実走である。
- docs 編集、commit、既存の未追跡 `output/insights/...` への操作は行っていない。

## 実装した変更

変更前の受理・拒否挙動:

- 任意の `session_meta` 行で `id == X` または `session_id == X` なら候補として受理していた。
- このため子 C/P も親 P の候補となり、型 A/B の親検索は 2 件として拒否された。
- `id` が null、数値、空文字でも `session_id == X` により受理された。
- 真の重複 P/P は従来どおり 2 件として拒否された。

変更後:

- [tools/codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:283) に、裁定どおり `owns_X ∧ (first_owns_X ∨ ¬declares_X)` を実装した。
- `id` 欠落時だけ `session_id` へ fallback し、null・数値・空文字は同一性を与えない。
- 型 A/B 正順では親と子を正しく分離する。逆順型 B と片側追記は 2 件拒否、真の重複も拒否を維持する。
- `_rollout_matches_session` と `_find_rollout` の第 2 引数を `target_session_id` に改名した。全 caller が positional であり、payload 側の `session_id` は変更していない。
- `_session_meta_rows`、pin fast path、全走査、件数検査、`_verify_rollout_sha`、消費側は変更していない。

[テストファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:1978) には以下を実装した。

- 既存 10 variant のうち `distinct-fields` だけを 0 件拒否へ反転し、テスト名を改名。
- 型 A、型 B 正順、型 B 逆順、片側 veto、真の重複。
- null・0・空文字の 3 variant。
- pin 経路の型 A/B と、SHA 検証成功後だけ fast path が返る検査。

## 実走結果

実走できた pytest nodeid は 0 件。すべて実装済み・未実走である。

- 焦点範囲: `orchestrator/tests/test_codex_reasoning_ab.py -k "find_rollout"`
  - 指定 flags: `-q --tb=no -rf`
  - `tools/run_tests.py` rc 16。pytest 開始前に `qstat -Q preflight rc=1`。
- collection-only: 対象テストファイル全体
  - rc 16、収集開始前に同じ preflight 失敗。
- 洗い出した制約 meta-test:
  - `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_growth_test_holds_contract.py::test_every_held_module_has_exact_top_level_guard_binding`
  - `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - 3 node 同時投入は rc 16、実走 0 件。
- `qstat -Q` 自体は rc 1、socket 作成失敗。queue-state は観測不能を可用扱いするため dispatch が選ばれた。
- 静的検査 `git diff --check`: rc 0。追加行に 88 桁超過なし。
- 親が行うファイル全走・repo 全走の代替にはしていない。

## 波及の静的列挙

- 所有外 production caller:
  - `derive_independent_golden`: author/fix1/fix2 の pin 解決。
  - `render_prompt`: POS/NEG の pin 解決。
  - `collect_run`: thread ID の全走査解決。
- 全 caller は第 2 positional argument。`session_id=` keyword caller は確認されなかった。
- 共有 fixture:
  - `benchmark_snapshots`、`_session_meta_bytes`、`_write_rollout`、`_install_rollout_pin` は変更なし。
  - 新 helper は追加した rollout 同一性テストだけが使用する。
- consumer test:
  - 既存の pin、SHA mismatch、全走査、0/2 件拒否、encoding、parse-count 系へ波及しうる。
  - real-repo collection meta-testは新規テストが誤って共有 fixture closureへ入らないことの確認先。
- 初期状態から存在した未追跡 `output/insights/2026-08-16_t936-rollout-identity/` は未変更。

## 残る不確実性

- pytest と collection が開始していないため、動的挙動・構文・nodeid 収集は未確認。
- 実 corpus を直接使う A4 probe、全走、受入、変異 matrix は親の段 6 作業として残る。
- 裁定 R1〜R4 は scope 外のまま。特に複数 `session_meta` を消費側が拒否する残余は変更していない。
- commit は作成していない。