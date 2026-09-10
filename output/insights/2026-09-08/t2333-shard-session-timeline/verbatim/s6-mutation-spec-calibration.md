## 総括

[mutation-spec-t2333.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/mutation-spec-t2333.json:3) の時間値3行だけを変更しました。他ファイルの編集と commit はしていません。

## timeout_seconds が含む時間の範囲 (根拠の file:line)

`timeout_seconds` は dispatch process の起動から終了までを測る外側 timeout です。`Popen` 後に `communicate(timeout=timeout_s)` が待つため、queue 待ち、計算ノード実行、結果回収を含みます。

根拠: [mutation_harness.py:1922](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/mutation_harness.py:1922)、[mutation_harness.py:1994](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/mutation_harness.py:1994)

外側 timeout と dispatch 待機契約の比較も `queue_wait_timeout_s + overall_grace_s` です。

根拠: [mutation_harness.py:1451](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/mutation_harness.py:1451)

## 決めた 3 値とその根拠

- `estimated_run_seconds = 916`
  - queue 待ち上限900秒と実行約16秒の合計です。
- `timeout_seconds = 1200`
  - dispatch 既定の queue 待ち900秒と猶予300秒の合計です。
- `hang_timeout_seconds = 3300`
  - job walltime は既定1時間、3600秒です。300秒の余裕を残し、walltime 未満にしました。

dispatch 既定値: [dispatch_compute.py:67](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/pegasus/dispatch_compute.py:67)

## loader を通したことの確認

`tools.mutation_harness._load_spec` を直接呼び、正常に通りました。

```text
loader=ok mutations=11 estimated=916 timeout=1200 hang_timeout=3300
```