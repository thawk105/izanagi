## F1 — 限定 cleanup

[tools/check_acceptance_reds.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:383)

- 検証済み nonce directory と exact fallback receipt の除去後、exact `output/pegasus-dispatch` に `rmdir()` を1回だけ実施。
- 空でなければ異物を残して `InvalidInput`、最終 rc=2。
- 再帰削除は検証済み nonce 内だけ。root の glob・再帰削除はない。
- 非空 root の異物を保持したまま拒否するテストを追加。[test_check_acceptance_reds.py:1637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:1637)
- `test_ignored_artifact_from_node_fails_closed` は無変更。

## F2 — cleanup fixture

[test_check_acceptance_reds.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:41)

fixture の `.gitignore` に実 repo と同じ `output/pegasus-dispatch/` を追加しました。空 root が残れば絶対指紋 gate に `!! output/pegasus-dispatch/` として現れ、既存の cleanup 正例が失敗します。期待値変更ではなく入力条件の補正です。

## F3 — 環境正規化

[tools/check_acceptance_reds.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:55)、[test_check_acceptance_reds.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:1513)

collection と rerun の双方で次を除去します。

- `IZANAGI_RUN_GROWTH_HELD_TESTS`: growth-held node の skip/実行を変えるため。
- `IZANAGI_T080_E2E`: T-080 E2E node の skip/実行を変えるため。

次は保持します。

- `IZANAGI_TEST_NPROC`: worker 並列度だけを変え、collection 集合や skip 判定を変えない。
- `IZANAGI_TEST_TRIGGER`: task-run 記録用で、テスト側では autouse fixture が隔離する。選択集合を変えない。

既存の3つの `PYTEST_*` 正規化も維持しています。

## F4 — M4 の単一理由性

[tools/check_acceptance_reds.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:218)

location 判定の集約を採用しました。root 一致、containment、symlink、canonical path、preferred/fallback shape、submission location を `location_valid` にまとめ、拒否条件を [同ファイル:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:269) の1箇所にしました。

既存 M4 fixture は有効な nonce、schema、request、stdout、footer を生成します。この条件だけを恒偽化すれば nonce gate を通り、別の receipt-location gateによる先取りはありません。

## F5 — dispatch timeout

[tools/check_acceptance_reds.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:25)、[test_check_acceptance_reds.py:1479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:1479)

`4200.0` から `5100.0` 秒へ変更しました。内訳は queue 900 + RUN 3600 + grace 300 + accounting 60 = 4860 秒で、外側に240秒の余裕を持たせています。git command は従来どおり120秒です。

## F6 — 監査 field

[tools/check_acceptance_reds.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:68)、[同ファイル:1465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:1465)

dangling な `receipt_path` を `deleted_receipt_path` へ改名しました。発行済み checker receipt は、削除済み artifact の旧位置であることを明示し、監査鍵として nonce、request ID、stdout SHA-256 を保持します。削除動作は維持しています。

## 実走結果

指定コマンドはテスト開始前に失敗しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
rc=16
```

したがって焦点 file は実装済み・未実走であり、緑とは申告しません。

静的検査結果:

- AST parse、禁止結合文字検査、`git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 変更は指定された2ファイルのみ
- commit、docs 編集なし

## 残った赤

テスト assertion の赤は未観測です。焦点走自体が infrastructure rc=16 のため未実行です。

`__pycache__` の実データ blocker は指示どおり未修正です。compute producer の allowlist 修正が裁定されるまで、親の実データ走は引き続き指紋 gate で rc=2 になり得ます。

## 波及可能性

- 所有外 producer: `tools/pegasus/dispatch_compute.py` の tests allowlist と v2 receipt schemaに依存。変更なし。
- 共有 fixture: `committed_repo` を使う同 test file 全体で、空の dispatch root も ignored artifact として検出される。
- consumer: checker receipt の `collections[*].receipt_path` は `deleted_receipt_path` に変更。現行 `tools/`・`orchestrator/` 内に当該 schema の caller／consumer は見つからなかった。
- meta-test: test file 名や追加 node を列挙する外部制約は見つからなかった。

## 総括

F1〜F6 を指定2ファイル内へ実装し、指紋 gate と ignored artifact 防壁は弱めていません。  
dispatch root は空の場合だけ削除し、異物があれば保持して rc=2 へ閉じます。  
正本 checker と静的検査は成功しました。  
焦点 pytest は基盤 rc=16 のため未実走で、親による実走が必要です。