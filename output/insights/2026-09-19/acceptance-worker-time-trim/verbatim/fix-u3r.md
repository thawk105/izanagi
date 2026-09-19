## 所見別の対応表

以下、R＝`orchestrator/tests/test_run_tests_preflight.py`、RT＝`tools/run_tests.py`。

| 所見 | 対応 | 根拠 |
|---|---|---|
| A4/B4 | **closed**：R:1405 に `_small_login_repo` 引数を追加（4 parameter 全体） | LOCAL は RT:2540 の実 fingerprint → RT:2382、2157/2172 →既存 `run_scope` → RT:2554–2559 の CHILD_RC return。DISPATCH は R の既存 preflight 3 stub と `Mock(return_value=7)` を使用。RT:2309 で mock が選ばれ、実 `_default_dispatch` の RT:1322 には非到達。RT:1558–1567 で `child_started=False` となり、RT:1616–1619 の記録開始にも非到達。 |

## 変更面

[対象ファイル:1405](/work/1/SFC/tanab/izanagi/.codex/worktrees/awtt-u3r-author/orchestrator/tests/test_run_tests_preflight.py:1405) の **1行追加のみ**です。

- `py_compile`：成功。
- HEAD `2d52301a3` との AST 比較：test 関数数 **114 → 114**。対象関数の引数追加以外は全 AST 一致。
- テキスト比較でも1行追加だけと確認。期待値・本文・parametrize・fixture・正例は不変。
- R:477／R:2314 の指定2テストは除外を維持。
- `git diff --check`：成功。`git add`／`git commit` は未実行。

## RecordingSession の確認

RT:1029 の root は import 時束縛のままです。auto-record=`0` では RT:2155–2157 の非記録経路になります。未設定でも LOCAL の scope stub は記録を開始せず、task-run ID は R:64–69 で除去されるため、RT:1138–1140／1165–1166 で記録・終了処理が戻ります。DISPATCH も上表のとおり記録開始に入りません。

## 未実走・未確認

pytest・性能測定は未実施で、親の計算ノード検証待ちです。直接 fingerprint 検証も未実施です。継承された手順は小 repo 作成時に `git add`／`git commit` を必要とし、今回の絶対禁止に抵触するため実行していません。

## 総括

A4/B4 の修正を1行で反映しました。
静的経路、構文、AST・テキスト差分を確認しました。
実走結果と削減時間は未確認です。