## 総括

対象テスト 1 file だけを修正しました。  
module-scope fixture は publication 生成のみを担当し、評価と document 構築は test call 段階へ移動しました。  
document と inputs は遅延生成後にキャッシュされ、実 `invoke()` は on/off 各 1 回のままです。  
実走は 2 回とも `rc=16` で child が起動せず、テスト所要は未計測です。

## 直した構造

- fixture の保持値を publication evidence だけに限定しました。[test_p3_b4_material_report.py:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_material_report.py:40)
- fixture から `_load_and_evaluate`、`build_material_report_document`、assembly・binding・analysis の assert を除去しました。[test_p3_b4_material_report.py:53](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_material_report.py:53)
- `_inputs()` と `_document()` を遅延キャッシュとして追加しました。例外時は代入が完了しないため、例外は test call 段階で発生します。[test_p3_b4_material_report.py:151](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_material_report.py:151)
- 正常経路の assert を専用 positive-control node へ移しました。[test_p3_b4_material_report.py:169](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_material_report.py:169)
- AST 検査で fixture 内に対象呼び出し・assert が無いこと、専用 node に存在することを確認しました。変更された tracked file もこの 1 file だけで、`git diff --check` は問題ありません。

## 正常経路を通る node の一覧

明示的な正常経路 positive control:

- `test_normal_path_assembles_binds_evaluates_and_builds_document`

別目的ながら正常 publication の評価経路も呼ぶ node:

- `test_artifact_availability_is_frozen_once_per_planned_leaf`
- `test_m13_lexical_dotdot_alias_reaches_resolved_campaign_comparison`
- `test_cli_clean_subprocess_runs_twice_and_refuses_overwrite` の初回 subprocess

M03 変異時は専用 positive-control node の `_document()` 呼び出し中に例外が出るため、fixture setup の `ERROR` ではなく test call の `FAILED` に帰属する構造です。ただし変異実走による確認は未完です。

## 実走結果

コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_material_report.py
```

- 初回: `rc=16`、`child_started=false`、wrapper 約 0.20 秒
- 許可された再試行: `rc=16`、`child_started=false`、wrapper 約 0.01 秒
- 原因: `qstat -Q preflight rc=1`
- 実走範囲: なし
- passed/failed: 判定なし
- テスト所要秒: 未計測

## 受理・拒否挙動の変化

無いです。production file と既存期待値は変更していません。変わったのは、対象機構の失敗を fixture setup error ではなく個別 test node の call failure として帰属できるテスト構造だけです。

## 未完・未解決

- 対象 file 全体の実走
- 実測所要
- M03 を含む登録変異が canonical stdout に `FAILED ` 行として現れることの実走確認

いずれも dispatch infrastructure の `rc=16` 解消後に再確認が必要です。