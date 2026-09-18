## 変更した file と差分の要点 (file:line)

- `tools/check_branch_rescue.py:38`：根拠4点を含むコメントと `CHECKER_EXIT_GRACE_SECONDS = 2.0` を追加。
- `tools/check_branch_rescue.py:1591`：外側 timeout に終了余裕を加算。その他の production コードは変更していないことを機械照合済み。
- `orchestrator/tests/test_check_branch_rescue.py:145`：実 subprocess 用 helper を追加。
- 同ファイル `:1956`、`:1977`、`:1990`：指定の正例1本・負例2本を追加。既存関数・テストの AST は変更なし。

## 変異 old 文字列の一意性 (grep -c の件数)

`grep -Fc` の結果はすべて **1件**。

- `CHECKER_EXIT_GRACE_SECONDS = 2.0`
- `min(timeout + CHECKER_EXIT_GRACE_SECONDS, overall_remaining)`
- `"--timeout-seconds", str(timeout),`

変異は実行していません。

## 実走した検査と結果 (nodeid・所要・赤の内訳)

- `git diff --check`：成功。
- Python 構文解析・差分範囲照合：成功。
- 新規3本の pytest 直接実行：フックが起動前に拒否。
- `tools/run_tests.py` 経由の新規3本：rc=16、`qstat -Q preflight rc=1`、`child_started=false`。
- 対象ファイル全体の pytest：フックが起動前に拒否。

実走した test nodeid・テスト所要時間はありません。テストの赤は未観測で、回帰の有無は未判定です。

## 波及の静的列挙

- production caller：`tools/check_branch_rescue.py:2072` の既存 `_landed_assessment` 呼出し。
- 所有外 caller・共有 fixture：指定シンボルの再帰検索では検出なし。
- 既存 consumer test：対象ファイル内の JSON 契約、実 checker、未証明 unit、判定不変性の検査。変更なし。
- ファイル名の再帰検索：所有外参照は `orchestrator/tests/acceptance_duration_ledger.json:4135–4214`。
- 関連 meta-test：`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`。実走未了。
- runner の自動生成記録は除去済み。最終 tracked 差分は所有2ファイルのみです。

## 現行挙動と変更後の含意 (2 文)

変更前は外側 timeout が子予算と同値で、親の観測では子の期限 JSON を回収できず `checker-timeout` になっていました。変更後は JSON 検証述語と `overall_remaining` cap を維持し、終了余裕内に届く契約準拠の報告を回収できる範囲が広がります。

## 未実施・未達

新規3本、既存全体、関連 meta-test の実走と所要増分確認は未達です。実 checker の親実測・変異検査・受入全走は親側に残り、docs 編集・commit・push は行っていません。

## 総括

**実装済み・未実走**です。プラン v2 の限定差分と静的検査は完了しましたが、closed とはしません。

自動実行審査の `guard_bash` が Pegasus ログインノードでの pytest を拒否し、代替 runner も計算ノードへの dispatch 前検査に失敗したため、実走結果を取得できませんでした。