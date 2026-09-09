## 総括

競合 2 ファイルを、両側の追加を失わない和集合として解決しました。  
台帳は main 側を土台に producer の add-only 形式で wave 側 326 件を追加しました。  
sweep test は wave 側 1 test、main 側 8 test と補助関数 2 個をすべて保持しました。  
commit、git add、merge abort、reset は行っていません。

## 台帳の解き方と検算

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/acceptance_duration_ledger.json)

- ours: 22,426 件
- theirs: 22,155 件
- 共通: 22,100 件
- ours-only: 326 件
- theirs-only: 55 件
- 和集合: 22,481 件
- ours 側 entry の欠落: 0 件
- theirs 側 entry の欠落: 0 件
- 凍結対象: 426 件、変更 0 件
- placeholder の新規作成: 0 件
- producer `_add_only_bytes` の期待 bytes と完全一致
- `nodeid_count=22481`、canonical top-level key 順、末尾改行を確認

共有 nodeid の値相違は 1,298 件でした。すべて theirs の値を採用しています。進行中 merge では main 側が最新の権威ある測定値であり、wave 側の古い測定値で上書きしないためです。結果を theirs と比較した既存値変更は 0 件、ours と比較した変更はこの 1,298 件だけです。

全 nodeid の列挙は [t1851-duration-value-conflicts.txt](/tmp/t1851-duration-value-conflicts.txt) にあります。1,298 行、SHA-256 は `4828a127fe360eca97e06b0e9074f06028e60a15443798ec523d6c64503eae09` です。

## sweep test の解き方

[test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_backoff_extended_sweep.py)

- base 37 test
- wave 側追加 1 test
- main 側追加 8 test
- 解決後 46 test
- main 側追加の補助関数 2 個も保持
- 各追加定義の AST は元側と一致
- test の削除、改名、skip 化、assert 弱体化なし
- 競合 marker 残存 0 件

## 実走した検査の結果

- `PYTHONPATH=. python3 tools/run_tests.py orchestrator/tests/test_update_acceptance_duration_ledger.py -q`
  - passed 0、failed 0、実行 0
  - infrastructure rc=16。子 process は起動されませんでした。
  - `qstat -Q` が socket 作成失敗 (`errno: 1`)。
  - login node は使用量 17,168,060,416 bytes、実効天井 15,032,385,536 bytes、headroom 0 bytesでした。

- `test_backoff_extended_sweep.py`
  - passed 0、failed 0、実行 0
  - 最初の検査が infrastructure failure になったため、指示どおり停止しました。

- `python3 -c "import json; ..."`
  - passed 1、failed 0
  - JSON parse と 22,481 件の集計一致を確認しました。

- `git diff --check`
  - エラー 0 件

## 残った懸念

pytest 2 系統は計算資源の preflight failure により未実行です。runner が生成した dispatch 一時成果物は除去済みです。`git status` の未解決表示は、git add 禁止に従い指定 2 ファイルだけが `UU` のままです。