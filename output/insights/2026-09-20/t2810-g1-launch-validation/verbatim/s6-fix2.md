## 変更の要約

[s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl/orchestrator/campaign/s8b_ratified_freeze.py:3631) の段階 6 の指定 block のみ変更しました（10 行追加・1 行削除）。

`generation_number` からの path 生成を、G の追加 path のうち `_GEN_RE` に一致するものの選択へ置換しました。個数が 1 以外なら個数入り detail で拒否し、1 個なら既存の導入集合 `{G}` 検査へ進みます。追補 1 の理由もコメントに記載しました。

## 受理集合の含意

- **受理:** 世代文書を 1 file 追加し、その導入集合が `{G}` の場合。現物 g1、独立 fixture、production emitter の各世代はこの条件に該当します。scope 射影でも G 自身の文書を選ぶため、g2 の G に g1 文書を要求しません。
- **拒否:** wrong_g=A、世代文書を追加しない commit、merge G は一致 path が 0 個。2 file 追加は 2 個として拒否します。
- **拒否:** 同一 bytes の削除・再作成は導入集合が `{G}` と一致しません。異なる bytes の履歴は既存 helper が拒否します。

個数違反と導入集合不一致は、いずれも `binding-chain-mismatch` / `generation-introduction` です。

## 不変の範囲

journal、artifact 区間 helper、cert 検査、段階 7、docstring、全 test は変更していません。変更前からの reservation／binding の受理、`i = C = G^` の受理も維持します。

共通の `_launch_validate` を使う `launch_validate` と `reverify_published_freeze` に適用されます。journal consumer、driftguards の共用定数参照、fixture default は不変です。

差分は指定 file のみ。commit・docs・job dir への書込みは行っていません。

## 実走結果

指定コマンドは **10 passed / 1 failed、rc=1**。以下の nodeid はすべて `orchestrator/tests/test_s8b_ratified_verify.py::` 配下です。

| nodeid | 結果 |
|---|---|
| `test_t2810_launch_positive[default/certificate/bound/unbound]` | 4 passed |
| `test_t2810_artifact_lineage_rejected[before-cert/merge/multiple]` | 3 passed |
| `test_t2810_artifact_interval_positive[intermediate/branch-join]` | 2 passed |
| `test_t2810_generation_introduction_independent` | passed |
| `test_floor_source_introduction_must_be_exact_generation_commit` | fixture 構築失敗、検査本体は未実走 |

別途実行した `test_generation_two_rejected_before_artifact_io` も **rc=1、検査本体は未実走**。両 sealed fixture は socket の `PermissionError: Operation not permitted` で停止しました。

直接呼出し・メモリ上の変異確認は **rc=0**：

- 独立負例：`DIRECT_CALL_PASS`
- 通常の wrong_g=A：`binding-chain-mismatch / generation-introduction`
- 新 block 除去後：`scan-exemption-invalid / active-chain-mismatch`

関連 meta-test は **6 passed、rc=0**（plain runner 3 件、session key pin、直接構築禁止、machine contract 関数集合）。`git diff --check` も成功しました。

## 総括

追補 1 の修正を working tree に残しました。独立 fixture と拒否 cause の契約は確認済みです。sealed fixture の既存負例と g2 回帰の成功確認は、親の焦点走 2 に残ります。