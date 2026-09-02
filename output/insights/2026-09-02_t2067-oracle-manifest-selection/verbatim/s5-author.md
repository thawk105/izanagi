## 実装

変更前は、active g1 が loader を通れば選択 identity 未検査のまま spec 読込へ進んでいました。

[s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067-author/orchestrator/campaign/s8b_oracle_manifest.py:1206) に、load 直後かつ既存 `try` 内で `assert_g1_floor_selection_identity(ratified, root)` を追加しました。`no-active` の既存写像とその他 reason の素通しは維持しています。

既存 4 test は synthetic g1 のまま selection call を記録する stub を追加し、回数と `(active, root)` を検査します。g2 化、`launch_validate`、新 helper、新 reason はありません。

genuine g1 の正負 2 test を [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067-author/orchestrator/tests/test_s8b_oracle_manifest.py:1473) に追加しました。公開 loader と公開 selection API は差し替えず、負例では指定された `_derive_floor_selection_eligibility` だけを差し替えています。

## 検査

以下を正規 runner で試行しました。

- 既存 4 nodeと追加 2 nodeの計 6 node
- `orchestrator/tests/test_s8b_oracle_manifest.py` 全体
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

3 走とも Pegasus の `qstat -Q` preflight が失敗し、child 未起動の `rc=16` でした。したがって実装済み・未実走です。test assertion の赤はありません。

静的検査は成功しました。

- 両 file の AST parse
- `git diff --check`
- 変更対象が指定 2 fileだけであること
- staged fileなし
- 結合文字 U+0300からU+036Fなし
- commit、addとも未実行

## 波及可能性

CLI `main` 経由の g1 manifest 構築は、spec 読込より前に選択不一致を拒否するようになります。非 g1 は公開 helperの早期 returnにより受理挙動不変です。

scope外の `report`、`verdict`、`judge` は依然として選択未検査です。また公開 `build_manifest`、`write_manifest` の迂回口も変更していません。

共有 fixture `test_s8b_ratified_freeze.build_production_emitter_g1` と、その official run path形式への依存を追加しました。静的な consumer test波及候補は oracle manifest、contract、driver、report、judge、verdict、materialization、binding driftguards、holdout admission、experiment numbers、ratified freezeの各 test fileです。

## 総括

変更した file と行数: 2 file、production +1/-0、test +95/-0、合計 +96/-0。  
追加した test の nodeid: `test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`、`test_build_approved_real_g1_rule_mismatch_preserves_selection_reason`。  
実走の有無と結果: 実装済み・未実走。正規 runner 3 走はいずれも child 未起動。  
赤の内訳: infrastructure `rc=16` が3件、test assertion failureは0件。  
波及可能性: CLI g1受理集合を選択準拠へ縮小。scope外 consumerと公開 lower builderの迂回は残存。