## 総括

- E2-2 の確定形を指定 2 ファイルだけに実装しました。
- production 変更は `_rollout_matches_session` のみで、その他の production は不変です。
- E2-3 の全 5 項目をテストへ追加しました。
- 静的検査はすべて rc=0 です。
- Pegasus のメモリ不足と scheduler 認証失敗により pytest は未実走のため、所見は `partial` と判定します。
- commit・stage・docs 編集は行っていません。

## 所見対応表

| レビュー A | 対応 | 状態 |
|---|---|---|
| 所見 1: 未確定行が候補を veto し、別 file を昇格 | 最初の確定可能行で `first_owns_target` を判定し、未確定行を宣言判定から除外。E2-1 の厳密反例も追加 | `partial` — 実装済み・未実走 |
| 所見 4-1: bool の被覆漏れ | `id=False` を既存非 str parameter に追加 | `partial` — 実装済み・未実走 |
| 所見 4-2: 先頭 payload 非 dict | 型 A / 型 B の parameterized test を追加 | `partial` — 実装済み・未実走 |
| 所見 4-3: own 後の子孫宣言 | `[C/C, P/P, C/P]` 相当の回帰を追加 | `partial` — 実装済み・未実走 |
| 所見 4-4: ineligible pin の条件付き配線 | SHA pin を欠かせて `eligible=False` にした型 A / 型 B を追加 | `partial` — 実装済み・未実走 |

`regressed` と判定した項目はありません。ただし pytest 未実走なので `closed` も申告しません。

## 実装した変更

[tools/codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:283)

- raw `index == 0` を廃止。
- `saw_determinable` により最初の確定可能行を識別。
- payload 非 dict、および無効な既存 `id` は直ちに次行へ進め、`declares_target` に寄与させない。
- `_session_meta_rows`、`_find_rollout`、pin fast path、件数検査、SHA 検証、consumer は変更していません。

[orchestrator/tests/test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2346)

- `test_find_rollout_non_string_id_does_not_fall_back_to_root_session[false]`
- `test_find_rollout_non_dict_leader_uses_first_determinable_identity[type-a/type-b]`
- `test_find_rollout_late_descendant_declaration_vetoes_parent_identity`
- `test_find_rollout_ineligible_pin_uses_identity_predicate_on_full_scan[type-a/type-b]`
- `test_find_rollout_undetermined_identity_does_not_promote_duplicate`

変更前後の挙動は次のとおりです。

- E2-1 の 2 file 反例: 変更前は片方を veto して別 file を受理、変更後は候補 2 件として `RC_SESSION`。
- 未確定行の後に確定した自己行がある単一 file: 変更前の誤った veto から、確定行に基づく受理へ変更。
- 無効な `id` しかない file: 引き続き候補 0 件。
- 確定後の子孫宣言: 引き続き veto。
- 通常経路と ineligible pin の全走査: 同じ新述語を適用。
- 有効な identity 行だけからなる既存入力の受理・拒否挙動は不変。

## 実走結果

pytest node の実行到達数は 0 です。すべて `tools/run_tests.py -q --tb=no -rf` 経由で投入しましたが、test process 起動前に `rc=16` となりました。

- 焦点走: 新規 5 test 群と既存近傍 6 node を指定、`rc=16`
- 変更 test file 単独走: `orchestrator/tests/test_codex_reasoning_ab.py`、`rc=16`
- 制約 meta-test: `test_real_repo_group_collection_exactly_matches_canonical_nodes`、`rc=16`

原因は以下です。

- local headroom 約 1.6 GB で runner の最小予算未満。
- `qstat -Q` が `Unknown user-id` で `rc=1` となり、計算ノードへ dispatch 不能。

静的検査は実走済みです。

- 両変更ファイルの AST parse: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0
- 変更ファイル境界検査: 指定 2 ファイルのみ

制約 meta-test は、新規 node が real-repo golden、共有 fixture closure、直列化 marker に意図せず入らないことを検査するものとして選定しましたが、実装済み・未実走です。

## 波及の静的列挙

所有外 production caller は次の 3 系統です。

- [`derive_independent_golden`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:648): author/fix rollout の解決
- [`render_prompt`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:1777): POS/NEG prompt source の解決
- [`collect_run`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3029): thread rollout、receipt、ledger 情報の解決

共有 fixture・consumer test への波及可能性は以下です。

- `_write_rollout` と `_identity_session_meta_bytes` を再利用。既存 helper の変更なし。
- `SESSION_IDS` / `ROLLOUT_SHA256` は `monkeypatch` で復元されるため、他 test への永続的変更なし。
- `benchmark_snapshots` など real-repo 共有 fixture は新規 test から参照しません。
- 既存 pin、scanner、encoding、zero/duplicate、consumer wiring test の期待値は変更していません。
- `collect_run` の複数 meta 行拒否、decode/read failure、SHA fallback の既知挙動は不変です。

## 残る不確実性

- 焦点走、変更 file 単独走、制約 meta-test は環境回復後に親が再走する必要があります。
- 変異 matrix、受入全走、A4 corpus 再測定は親段の責務として未実施です。
- scope 外の R1、R2、R3 は閉じていません。
- 既存の未追跡 `output/insights/2026-08-16_t936-rollout-identity/` には触れていません。