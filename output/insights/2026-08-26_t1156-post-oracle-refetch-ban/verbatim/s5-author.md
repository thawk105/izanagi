## 実装した変更 (file:line)

- [buildcache.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:747)
  - exact schema の `post_oracle_dependency_binding` capability を追加。
  - `SHA256SUMS` 本体 hash、宣言 file の hash、file 集合、HEAD、`config.h`、archive を configure 前後で照合。
  - capability 時だけ `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を exact 1 本追加。
  - configure 後に `CMakeCache.txt` の実効値 `BOOL=ON` を確認してから build。
  - capability 時だけ manifest authority と policy ID を identity に追加。

- [s8b_floor_campaign.py:2134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:2134)
  - `sort_best` の oracle receipt から manifest/config authority を取得し、正式な `buildcache.build_v2` 経路へ capability を渡すよう変更。

- [test_buildcache_v2.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:727)
  - flag 1/0 本と generic base-only 正例。
  - HEAD/config 不変の別 file 改変拒否。
  - configure 前 config 不一致と `_run` 0 回。
  - CMake 実効値 OFF の build 前拒否。
  - capability 有無による identity 分離。
  - flag token は test 内の literal を使用。

## 実走した検査 (nodeid と結果)

pytest の実走成功は 0 件です。以下は実装済み・未実走です。

- `test_v2_post_oracle_flag_is_exact_one_and_generic_base_only_stays_zero`
- `test_v2_post_oracle_manifest_rejects_changed_declared_non_config_file`
- `test_v2_post_oracle_config_mismatch_refuses_before_configure`
- `test_v2_post_oracle_effective_disconnected_off_refuses_before_build`
- `test_v2_post_oracle_policy_separates_only_bound_identity`
- 制約 meta-test: `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`

`tools/run_tests.py` 経由で試行しましたが、Pegasus dispatch が `qstat -Q rc=1`、`child_started=false`、runner rc 16 となり、pytest process は起動していません。

静的検査は成功しました。

- 3 file の AST parse
- `git diff --check`
- U+0300 から U+036F の不在
- `git status` が許可された 3 file の変更のみであること

## 受理集合の変化

変更前は、canonical base と旧 2-key receiptを渡す generic build は archive 任意で受理され、configure に再 populate 禁止 flagはありませんでした。非 base build も同様に受理され、材料検査は主に build 後でした。

変更後も、capability を渡さない generic base-only build と非 base build の argv、identity、受理条件は従来どおりです。

明示 capability を渡した場合だけ、次を拒否します。

- manifest authority、宣言 file、HEAD、config、archive の不一致
- 宣言外の material regular file
- configure 後の実効 disconnected 値が exact `ON` でない場合
- capability と併記された旧 FetchContent 引数の不一致

Git metadata は HEAD で、archive は run-local archive binding で独立に束縛しています。

## 所有外への波及可能性

- `pipeline.py` の非 capability caller は変更なしです。
- A1/A2 の非 base exact argv consumer は静的には不変ですが未実走です。
- `test_s8b_floor_campaign.py` の注入 build seam は従来引数を維持します。正式な `buildcache.build_v2` 経路に対する capability 配線の追加 assertion は所有外です。
- `test_real_repo_serialization.py` は更新した共有 fixture helper を importします。追加された合成 `SHA256SUMS` の影響確認は未実走です。

## 実装しなかったもの と 理由

裁定どおり X1 から X5 は実装していません。

- masstree build 中の再生成禁止
- mimalloc / googletest の内容束縛
- cross-base hit の historical argv 改修
- process 間 lock / private snapshot
- resume / durable manifest migration

また、`CMAKE_TOOLCHAIN_FILE` の環境除去、実行 argv と記録 argv の完全一致検査、既存事後検知の削除や緩和は行っていません。docs、handoff、commit、push もありません。

## 総括

裁定 §2 の 5 点と §3 の変異を殺すテストを、許可された 3 file のみに実装しました。静的検査は通過していますが、Pegasus dispatch infrastructure failure のため pytest は未実走です。親で queue 復旧後に上記 nodeid、制約 meta-test、関連 consumer 範囲の再実走が必要です。