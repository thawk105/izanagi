# 段 6 裁定 — [md_17] レビュー A (正しさ境界・帰属) / B (過剰・削除) (2026-09-29 16:2x JST)

入力: review-a.md (A1)、review-b.md (B1〜B3)。両方 check_codex_output rc=0。

| ID | 裁定 | 採否と内容 |
|---|---|---|
| A1 α の v3 帰属で表を照合していない | real (must-fix) | 採用。既存 skip-read-recheck の事象行に `table` が無く、起動器は `event.table is None` で表照合を省いていた。修正 (Codex fix、起動器): 保存済み raw trace から、事象の txn (tx_wts → C 行の txid) が事象の key を事象の a_wts の版で読んだ R 行を探し、その表を一意に復元して witness の rw 辺の表と照合する。R が 0 件・複数表なら帰属不能に数える。J1 原本 (`runs/j1-a/`) を再計算する offline mode で行い、再走しない。 |
| B2 β の巡回の帰属が機械可読でない | real (should) | 採用。同じ fix で、β の run の判定器 witness を β の事象 (表・key・a_wts = 読んだ版・b_wts = 次の版の txn の wts) と照合した結果を JSON に残す。事前登録の β の合否 (orphan read) は変えない。巡回の帰属は観測値として記録する。 |
| B1 GC 異常の原因を delete に確定しすぎ | real (should) | 採用 (親の docs 修正)。一次資料・README・fragment で、再現条件を「F cell × thread 4」に限定し、「trace の有無に依らず再現」までを事実、delete 競合の機序は仮説と書く。修理 item は原因の特定から始める。 |
| B3 起動器に今回使わない job・cell | real (nit) | 採用 (親の docs)。一次資料に、計測に使った job は L0-TPCC・GC-PROBE・J1-TPCC の 3 つ (J1-FOCUS と YCSB 系は不使用) と起動器の sha256 を書く。起動器は変えない。 |

## fix の事前登録 (DW-M01、fix 前)

- 再帰属の期待 (観測値をそのまま記録し、外れても判定を緩めない): α は代表 witness 20 件のうち、表まで照合して帰属が成り立つ witness が 1 件以上 (完了判定 R4 の条件)。20 件全部とは限らない。
- 検出力の確認 (fix 子が手作りの入力で行う): 事象の表と辺の表を食い違わせると、その witness は帰属不能になる。R が複数表に当たる入力は帰属不能になる。
- β の巡回照合の期待: 判定器の witness 1 件 (cycle [5, 397]) の rw 辺が、β の事象 1 件以上と (表 8・key・読んだ版 = a_wts・次の版 = b_wts) で一致する (親が raw で照合済みの 1 例と同じ)。

fix の単位は起動器 1 file (所有は repo 外で owned_paths 外)。子の worktree は cicvext-b に新 branch を切って使う。既存テストは無関係 (repo 内の実装面を変えない)。
