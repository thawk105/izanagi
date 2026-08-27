plan v2 の実装は完了しました。pytest 実走だけは Pegasus scheduler 認証エラーで子プロセスを開始できず、未実走です。

### 変更内容

- [acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q-author/tools/acceptance_launcher.py)
  - main/tip runner bytes 等値拒否だけを削除。
  - tip 読取、tested-main 実行、実行後 main 再読、binding report、receipt main digest は維持。
- [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q-author/tools/dev_wave_land.py)
  - main/tip runner blob ID 等値条件だけを削除。
  - D987 を追加し、最後の incorporated main と tested main の runner blob を比較。
  - 初回 locked preflight 後・provenance 実行前と、provenance 成功後の再 preflight 後に検査。
  - 欠落・非blob・不一致は恒久的な generic acceptance rejection、Git lookup failure は retryable。
- テスト
  - main!=tip の launcher 正負例、main 再読 drift。
  - real waiter/launcher/main-digest receipt/real land E2E。tip runner は rc=97 の失敗 source。
  - 2段 forward-main の「最後だけ変更」拒否と「途中変更後に最終復元」受理。
  - main/tip 片側欠落・tree の3独立 nodeid。
  - provenance rc=16 の mask 分類、checker lookup retryable、D987 再検査回数。

差分は4ファイルのみ、328 insertions / 46 deletionsです。commit は作成していません。

### 検証結果

- `git diff --check`: 成功
- 所有4 path の AST parse: 成功
- U+0300〜U+036F: 0件
- `git status --short`: 所有4 path だけ変更

`python3 tools/run_tests.py ...` は5回試行しましたが、すべて rc=16でした。

- 原因: `qstat -Q` が `EACCTAUTH Unknown user-id`
- dispatch receipt: `child_started=false`
- pytest 実走 nodeid: 0
- 回帰赤・期待赤: 子未起動のため判定なし
- infrastructure 赤: rc=16
- 未実走: 変更2 test file、real waiter E2E、D987正負例、consumer/meta-test、変異probe

### 所有外波及

- tracked な所有外変更はありません。
- 指定 runner が ignored の `output/pegasus-dispatch/` に失敗 receipt を生成しました。
- 静的検索で、所有外の `orchestrator/tests/acceptance_duration_ledger.json` に改名前 nodeid が7件残っています。所有4 path契約により更新していません。
- waiter、acceptance shards、resume-boundary、schedule-order 系 consumer/meta-test は参照を列挙しましたが未実走です。

## 総括

D987を含む plan v2 は所有4 path内で実装済みです。ただし scheduler 認証障害によりテストは「実装済み・未実走」であり、green 完了とは報告しません。