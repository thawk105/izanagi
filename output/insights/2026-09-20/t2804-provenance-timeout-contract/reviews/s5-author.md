## 変更一覧

許可された 4 ファイルだけを変更しました。

- `tools/dev_wave_land.py:3555`：480 秒の定数化、絶対 monotonic 期限の env 上書き、timeout 文面の定数参照。
- `tools/check_ai_provenance.py:55,2892`：定数・根拠コメント、有限値 parser、期限と queue 予算の導出、投入前拒否、例外時を含む終端ログ。
- `orchestrator/tests/test_check_ai_provenance.py:6825`：指定の新規テスト 10 種、31 ケース。
- `orchestrator/tests/test_dev_wave_land.py:4820,5835,9954,10010,12138`：指定 pin 改訂、stderr 非転送、継承期限の上書き検査。

終端ログは依頼本文の `deadline_at_margin_s` を採用しました。

## 実走した検査

以下を実行しました。各選択式に一致する全 node が対象です。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_check_ai_provenance.py', '-q', '-rf', '-k', 'outer_deadline']))"
```

31 passed / 0 failed、549 deselected。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_dev_wave_land.py', '-q', '-rf', '-k', 'provenance or cumulative_wait_budget_arithmetic']))"
```

39 passed / 0 failed、326 deselected。既存の flaky-hold 集計は matched=1、skipped=1 を出力しました。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_t2337_dispatch_timeout_overrides.py', 'orchestrator/tests/test_plain_runner_coverage.py', '-q', '-rf']))"
```

両ファイル全件：24 passed / 0 failed。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_check_ai_provenance.py', '-q', '-rf', '-k', 'dispatch or login or scope or every_checker_main_call']))"
```

78 passed / 0 failed、502 deselected。上記新規テストとの重複を含みます。

失敗 node はありません。`git diff --check` も成功しました。

## 所有外への波及

- checker の `_default_dispatch` は `_invoke_dispatch` が選択し、`main` の force／headroom_short／cap_oom から到達します。所有外の直接 consumer は `test_t2337_dispatch_timeout_overrides.py:191,216`。
- land の `_run_provenance_checker` の本番呼出元は `_audit_provenance_history:3602`。所有外 caller は検索で見つかりませんでした。
- 新 env 名の検索結果は本番 2 ファイルの定義のみ。既存名との衝突なし。
- 共有 fixture は変更なし。新 fixture は新規テスト専用です。
- `main`、`_invoke_dispatch`、D612 parser、`_run_bounded_scope`、`_launch_local_scope` は変更前とのソース一致を確認しました。dispatcher も未変更です。

## 現行の受理・拒否挙動と変更後

- env 未設定時の dispatch kwargs と local scope 経路は不変。
- 不正 env は rc=16、有限の過去期限は残余不足として投入前拒否。
- 合成 queue 予算 `<16` は拒否、`==16` は投入。D612 Q=0 と新 env の併用は拒否へ変化。
- queue 上限超過帯と `(deadline_at, K]` の完了帯で成功集合が縮小し、land の retryable 集合が増加。
- 同じ返却 rc の分類は不変。RUN／collection の hold latch と receipt 永続化の非保証は残ります。

## 制約 meta-test

- `test_t2337_*` と `test_plain_runner_coverage.py`：全件成功、変更なし。
- checker の site 明示、dispatcher rc 整合、scope 実装間 parity：上記 78 passed に含まれます。
- `__main__` harness を静的確認：checker は pytest 全件、land は `test_*` 列挙。land 新規テストは引数不要で列挙対象です。harness 自体の全件実行は未実施。

## 未実装・未実走

契約の未実装項目はありません。2 ファイルの全件走、段 6 の変異 matrix、Pegasus L1〜L3、後段時間 h の実測は未実施です。

## 総括

C-2804 のコードと指定テストを実装し、実走した検査はすべて成功しました。変更は 4 ファイルに限定し、stage・commit・stash・branch 操作は行っていません。