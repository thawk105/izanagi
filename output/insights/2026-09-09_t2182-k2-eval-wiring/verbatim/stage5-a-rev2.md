## 実装した内容

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-a/orchestrator/campaign/p3_s4_loop.py:330) で `buildcache._v2_commands` から offline configure token を導出。
- prebuild receipt がある場合だけ `configure_args` を condition gate に渡し、receipt がない既存経路は空のまま維持。
- A-2 は実装せず、driver の argv 受理集合も変更していません。
- 禁止対象ファイル、docs、親 worktree は変更していません。commit も未作成です。

## 新設したテストと実走結果

- M1 正例: [test_prebuild_offline_tokens_reach_real_condition_gate_configure_argv](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-a/orchestrator/tests/test_p3_s4_loop.py:7853)
- M2 負例: [test_without_prebuild_real_condition_gate_configure_args_remain_empty](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-a/orchestrator/tests/test_p3_s4_loop.py:7892)

両テストは `capture_define_inputs` と `evaluate_define_supply_effectuation` の実体を通り、CMake 起動境界の実 argv を観測します。

実走は未完了です。個別 nodeid、2 件同時、test file 全体を自走 harness で試しましたが、すべて `qstat -Q preflight rc=1`、dispatch rc=16 で子テストが起動しませんでした。したがって緑とは申告しません。

静的検査は成功しました。

- AST parse: PASS
- `git diff --check`: PASS
- test 名重複なし、必須 nodeid 2 件を確認
- U+0300〜U+036F: 検出なし
- 変更ファイル: 上記 2 ファイルのみ

## 保証の含意

prebuild receipt がある場合、4 個の FetchContent token と、非空時の `CMAKE_PREFIX_PATH` が campaign build と同じ生成器から condition gate の configure argv に届くことを保証します。

Pegasus 上での評価完走、依存物自体の正しさ、または新しい receipt 検証は保証しません。

正例は、base、masstree、mimalloc、googletest の各 directory と dependency prefix を渡した走行で、condition gate と campaign build の 5 token が完全一致するケースです。

## 波及可能性

- caller: `drive_iteration` と main の fixture/proposal 両経路。receipt なしの `run_one_iteration` は従来どおりです。
- shared fixture: condition gate を止める既存 autouse fixture。新設テスト内だけ実体へ戻しています。
- consumer test: source 順序検査、既存 prebuild transport、campaign build argv 検査。
- `buildcache._v2_commands` の将来の private API 変更は本配線へ波及しますが、token 突き合わせテストで検出する設計です。

## 総括

A-1 は実装済み・未実走です。自走 harness の dispatch infrastructure が復旧後、上記 2 nodeidと `orchestrator/tests/test_p3_s4_loop.py` 全体の再実走が必要です。