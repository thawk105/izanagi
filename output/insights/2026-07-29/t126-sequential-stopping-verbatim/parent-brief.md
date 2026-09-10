# T-126 段1 brief

- 対象はユーザー裁定済み T-126、設計 v2 の (a) near_floor cross-run 再現 SPRT 保守形 1 本だけ。
- bench rep 逐次打ち切り、floor 校正削減、verify seed 逐次停止、bench-only 軽量形は対象外。
- 採否の between-run floor、MWU、reps=5、legacy+S2、anomaly 即 reject は一切変えない。
- 実在発火 artifact は `output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl` の committed pair `41b196c96428` → `e932c4502198` (faster +3.417%、p=0.01219、near_floor=True)。
- 入力 seam は committed BENCH_DONE の `tps` / `median_tps`、COMMIT の `verify_configs`、WAL `ts`、campaign identity、実在 boot-id。
- 成果物は SPRT 純粋判定、正準 series identity、観測済み round 参照の append-only ledger、再開検査、promotion fail-closed gate。
- 各 round は既存 `run_campaign` → full `pipeline.evaluate` を通し、別 campaign identity と round ごとの admission を保つ。
- `reproduced` 以外 (`not-reproduced` / `indeterminate` / `same-boot` / ledger 欠損・不整合) は headline 昇格不可。
- 放置時の成果物影響: near-floor の certified 性能差が単発値だけで headline へ昇格し得て、レポート主張と proof 参照が D19 を満たさない。
- freeze 初期化は必要だが、既存凍結 artifact bytes / generator bytes は変更しない。
- 新 gate の入力実在は上記 artifact と WAL field で確認済み。gate は positive / negative mutation で発火を固定する。
- (P1) 新規の再利用可能 module + 薄い opt-in driver を既定案とする。親の provisional 裁定であり攻撃対象。
- (P2) 新規性能計測は行わず、全系列列挙 + tracked 実 WAL 由来 fixture を本 wave の受入とし、実測 positive control は初回 opt-in 系列へ送る。親の provisional 裁定であり、設計 §8 との整合を攻撃する。
- 受入は worktree の通常テスト環境で、対象 unit / consumer / mutation、関連 suite、全走、Codex/docs/provenance 検査を行う。
- 実装面は隔離済み Codex author worker 1 本へ所有させ、manager はコード・テストを直接編集しない。
- 受理集合・headline gate・proof chain に触るため、独立 plan + 敵対レビュー 2 本 + 実装後レビュー 2 本を省略しない。
