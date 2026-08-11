# [T-756] trace 完全性の commit witness 検査 — 逐語と変異台帳 (2026-08-11)

wave = `dev-wave-t756-trace-v2` / branch `worktree-dev-wave-t756-trace-v2`
実装 commit = `ee81c43115240e1b4550055f101916769623f64a`
fix commit = `c3d2465523e8c6da90dfb9e7ed84cdef3c7b637f`
ccbench pin = `d706650cdb31e442bef45b9b4216951d4fb40969` (**1 bit も変えていない**)

## 何をしたか

`orchestrator/tests/test_verifier.py` が characterization テストで明示ロックしていた既知偽陰性 2 件の
うち、**FN-1 (末尾欠番)** を trace の外にある CCBench 自身の counter (`commit_counts_`) で閉じた。
**FN-2 (trx 尾部欠落 = C 行が R/W 件数を持たない)** は trace 形式そのものの変更を要し、submodule の
gitlink 前進 → 承認定数の追認禁止に当たるため本 wave の権限外で、`verbatim/ruling-package.md` として
ユーザー裁定へ返す。

当初案 (2026-07-02 台帳の「C 行に R/W 件数・終端マーカー」) と機構が違う。FN-1 に対しては
**独立 witness の方が強い** — 終端マーカーは末尾切りしか捕えないが、witness は欠落位置に依らず
thread の trace file が丸ごと消えた場合も捕える。ただし **failure-independent ではない**:
trace と counter は同じ実行体から出るので、両方が同時に落ちる common-mode failure と
個数を保存する破損は検出しない (レンズ L1-7 の指摘を採用)。

## 一次資料

| ファイル | 中身 |
|---|---|
| `verbatim/brief.md` | 段 1 親 brief (DW-O09 の自己訂正を含む) |
| `verbatim/s2b-plan.md` | 段 2 プラン (親 brief の誤り 6 点を指摘) |
| `verbatim/s3-lens1b.md` | 段 3 レンズ 1 (fail-open 面。blocker 2 + must-fix 7) |
| `verbatim/s3-lens2.md` | 段 3 レンズ 2 (不変条件の反例と凍結証拠面。blocker 1 + must-fix 5) |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (採否・brief 訂正・scope 外・変異事前登録) |
| `verbatim/s5-author.md` | 段 5 実装報告 |
| `verbatim/s6-review1b.md` `verbatim/s6-review2b.md` | 段 6 敵対レビュー 2 本 (両方 NO-GO) |
| `verbatim/s6-fix1.md` `verbatim/s6-fix2.md` | fix 2 巡の報告 |
| `verbatim/s6-focus.md` | 焦点再レビュー (production = GO、11 所見 closed) |
| `verbatim/ruling-package.md` | FN-2 を返す裁定パッケージ |
| `mutation-spec*.json` / `mutation-ledger*.json` | 変異 3 走の spec と台帳 |
| `erratum.md` | 変異 1 巡目の MISMATCH 11 件と、その機序 |

## 変異結果 (最終)

- **spec A** (`pipeline.py` 非接触 8 件、runner = test_verifier / test_critic / ladder driver):
  **8/8 KILLED**
- **spec B** (`pipeline.py` 接触 6 件 + drift control、runner = witness/run_trace の control node 14 本):
  **6/6 KILLED + drift control SURVIVED (期待どおり)**
- 合計 **14/14 KILLED**。SURVIVED は drift control の 1 件のみで、これは意味的 no-op を入れて
  「絞った範囲が drift の影響を受けない」ことを示すための正例である。

## 段 3 / 段 6 が捕らえた重要な所見 (採用済み)

1. **共有 parser を正しさ witness の権威にしてはならない** — `calibrator/benchparse.py` は同一 label の
   重複行を last-wins で潰すため、壊れた stdout が静かに別の値になる。専用の厳格 parser を置いた。
2. **不変条件の前提は workload 依存** — 「commit 後に無条件で counter を増やす」のは YCSB だけで、
   `external/ccbench/include/tpcc.hh:110`–`112` ほかは counter 増分の**前**に `quit` を見て return する。
   allowlist 形で機械 pin した。
3. **ladder の正式な correctness 証拠が、同じ run の保存済み witness を使っていなかった** —
   凍結 `verifier.json` は変えず、外側で `run.stdout` と `stats.txns` を照合する gate を足した。
   既存実データ (`480595 == 480595`) で発火して緑になる。
4. **事前登録した変異 2 件は実は生存する** — 判定は `Integrity.clean()` にあり、当初照準した箇所は
   診断メモにしか効かなかった。実効 gate へ再照準した (F28)。
5. **witness は「独立」ではない** — 記述を「trace 外 counter による個数の裏取り」へ限定した。

## 残る限界 (正直に書く)

- **FN-2 は開いている。** C 行が残って R/W 行だけ落ちる部分 trace は依然 certified になりうる。
  `test_characterization_txn_tail_loss_is_false_green` が期待値を変えずに可視化を続ける。
- **witness を渡さない呼び出し経路には旧挙動が残る。** 直接 API と CLI の省略呼び出しでは FN-1 が残る。
  閉じたのは `pipeline.evaluate`、S2 calibration、ladder 証拠の 3 経路である。
- **coverage 系 4 driver** (`s3_lock_coverage` / `s5_permutation_coverage` / `s8a_trigger_coverage` /
  `t152_write_intent_coverage`) の `*_certified` 材料値は witness 未装備。3 本にテストが無く受入で
  検証できないため scope 外とし、裁定へ返す。
- **既存 WAL の witness なし COMMIT** は再評価していない。新 gate は本 commit 以降の run に効く。
