---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t756-trace-v2
seq: 1
title: [T-756] trace 完全性の commit witness を入れた — 末尾欠番の偽陰性を trace 外 counter で閉じ、trace 形式変更が要る残り半分は裁定へ返した (コード + docs、変異 14/14 KILLED + drift control SURVIVED、branch worktree-dev-wave-t756-trace-v2)
---

## 本文

[T-755] Q1 (a) の裁定に従う単独 wave。CCBench (`external/ccbench`) は **1 bit も変えていない**
(gitlink = `d706650cdb31e442bef45b9b4216951d4fb40969` のまま)。

**負債は 2 件に割れ、必要な権限が違うと実装して初めて判明した。**

- **FN-1 (末尾欠番)** — 欠番検査が `expected = max(txid)+1` なので txid 最大側の trx が丸ごと消えると
  欠番 0 と数えられ certified になる。**AI の権限内で閉じた。** trace の外にある CCBench 自身の
  counter (`commit_counts_`) を verifier へ渡し、trace 内の committed txn 数と不一致なら
  integrity 違反として `certified` を落とす。
- **FN-2 (trx 尾部欠落)** — C 行が R/W 件数を持たないため R/W だけ落ちた trx を区別できない。
  **trace 形式そのものの変更 = submodule `izanagi-trace` の commit → gitlink 前進**を要し、
  承認定数 `CCBENCH_FULL_SHA` / `pin.CURRENT_PIN` の追認禁止・`origin/izanagi-trace` への push
  (人間手番)・floor campaign の live gate に当たる。**権限外なので裁定パッケージで返す**
  (`output/insights/2026-08-11_t756-commit-witness/verbatim/ruling-package.md`)。

当初案 (2026-07-02 台帳の「C 行に R/W 件数・終端マーカー」) と機構が違う。FN-1 に対しては独立
witness の方が強い (欠落位置に依らず thread file 丸ごとの欠落も捕える) が、**failure-independent
ではない** — trace と counter は同じ実行体から出るので common-mode failure と個数保存型の破損は
検出しない。記述は「trace 外 counter による個数の裏取り」に限定した (レンズ L1-7)。

**再凍結コストは D16 注記より小さいと実測した。** `known_axes_freeze.json` /
`floor_protocol.json` は `ccbench_pin` を**記録**しているが現 gitlink と照合する live 検査は無く、
照合が発火するのは (a) 承認定数の always-on テストと (b) 新しい floor protocol を凍結するときだけ。
**floor の実機再測は不要**で、要るのは承認定数 2 個の更新承認と submodule の push である。

**敵対検証が捕らえた主なもの (全件 real と裁定):**

1. **共有 parser を正しさ witness の権威にしてはならない** — `calibrator/benchparse.py` は同一 label の
   重複行を last-wins で潰す。壊れた stdout が静かに別の値になるため専用の厳格 parser を置いた。
2. **不変条件の前提が workload 依存だった** — 「commit 後に無条件で counter を増やす」のは YCSB だけで、
   `include/tpcc.hh:110`–`112` ほかは counter 増分の**前**に `quit` を見て return する。allowlist で pin。
3. **ladder の正式な correctness 証拠が、同じ run の保存済み witness を使っていなかった** (blocker)。
   凍結 `verifier.json` は変えず外側で照合する gate を足した。既存実データで発火して緑になる。
4. **事前登録した変異 2 件は実は生存する** (blocker)。判定は `Integrity.clean()` にあり、当初照準した
   箇所は診断メモにしか効かなかった。実効 gate へ再照準した。
5. **既存 characterization をその場で反転していた** (blocker)。元 nodeid・元 assert を復元し、
   witness 付きは別 node として並置した (witness を渡さない optional API の後方互換の証拠)。

**静的レビュー 4 本が全員取りこぼし、実測だけが捕らえた制約が 2 件ある。**

- `orchestrator/verifier/report.py` は**編集できない**。凍結 ladder evidence が現行 bytes 一致を
  要求する (`driver` と `policy` だけが歴史 drift 許容という非対称契約)。段 5 が編集して赤になり、
  fix 1 で完全復帰させた。witness の構造化は既存 key (`integrity.clean` / `notes`) と pipeline の
  WAL payload で表現する形に変えた。
- `orchestrator/campaign/pipeline.py` は enforcement source closure 8 path の 1 つで、
  **未 commit のままではテストが必ず 40 件赤くなる** (disk bytes と記録 commit blob の照合)。
  同じ機序が**変異検査の帰属も壊す** — 一時変異させるだけで無関係な 26 件が落ちるため、
  runner 範囲を drift 非感受な control node へ絞り、drift control (意味的 no-op) を 1 件置いて
  SURVIVED を実測してから kill を数えた。詳細は同 insights の `erratum.md`。

**規律違反を 1 件、自分の wave の中で犯して merge 時に捕らえた。** 実装 commit は既存テスト
`test_run_trace_parses_abort_from_stdout` を削除していた (`_run_trace` の返り値を型付きにする際、
witness 版へ whole-function replacement した形)。**既存テストの削除は禁止事項だが、段 6 の敵対
レビュー 2 本と焦点再レビューの 3 本すべてが「テスト削除なし」と誤って報告した。** main 側に同テストが
残っていたため受入直前の merge で差分として現れ、DW-O17 が要求する merge の Codex `role=author`
検証が独立に捕らえて復元した (期待値は不変。返り値を属性参照へ、binary 名を YCSB allowlist へ
合わせただけ)。**「両親と異なる実装面を持つ merge には Codex author を立てる」という契約が、
形式要件ではなく実益を出した実例である。**

**受入・実測 (すべて計算ノード dispatch):** 焦点走 4 回 (41 failed → 914 → 929 → 930 passed)、
変異 3 走 (1 巡目 MISMATCH 11 / KILLED 3 → spec A 8/8 KILLED → spec B 6/6 KILLED +
drift control SURVIVED)。**合計 14/14 KILLED。SURVIVED は drift control の 1 件だけ。**
変異 harness の起動前検査が 2 回止めてくれた (期待 node の非実在、`category` の未知値) ため、
2 時間の空走を 1 回回避できた。

## 次の一手差分

### carry

- [T-757]
- [T-758]

### 更新

- [T-755] **P1・裁定済み (2026-08-11 /rulings、Q1〜Q3 全問 (a))。Q1 (a) の trace v2 単独 wave は
  本エントリで land 済み (FN-1 分)。残るのは Q2 (移植初手 = mocc) と Q3 (案 B 偵察を解禁しない) を
  前提とする **protocol 移植 wave** で、その前提として {{T:trace-v2-cpp-pin-approval}} の新 pin 承認が
  先に要る。移植先ごとに「commit 後 counter の終了契約」を個別に証明する必要がある
  (YCSB 以外は counter 増分前に `quit` を見て return するため)。
  正本 = `dev-wave-jobs/dev-wave-s1-design-choice/ruling-package.md`
  base: 9078a4fe7387e297e1c46209b45f3acc32e7809f3fecaf8c54121bd302d85330

- [T-756] **P1・FN-1 は本エントリで land 済み。FN-2 は {{T:trace-v2-cpp-pin-approval}} へ分離**:
  `test_characterization_tail_txid_gap_is_false_green` は元 assert のまま残し (witness を渡さない
  optional API の後方互換の証拠)、witness 付きの indeterminate 検査を別 node として並置した。
  `test_characterization_txn_tail_loss_is_false_green` は**期待値を変えず** FN-2 の可視化を続ける。
  base: f66209cbc02bd37d9f47f769413d71e2dddbe354900220d05b4554bd48c79111

### 新規

- {{T:trace-v2-cpp-pin-approval}} **P1・ユーザー裁定待ち**: FN-2 (C 行 R/W 件数 + txn 終端マーカー)
  の C++ 側。`include/trace.hh` と `cc/silo/transaction.cc` (+ `cc/si/transaction.cc`) の変更は
  submodule `izanagi-trace` 行きで gitlink 前進を伴い、承認定数 2 個の更新承認と push が人間手番。
  提案手順は 4 段 (AI が local commit + 旧 pin 対新 pin の TRACE=0 翻訳単位同一検査 → 報告 →
  ユーザーが push と承認 → 別 wave が gitlink 前進と v1 拒否化)。Q1〜Q3 の 3 問付き。
  正本 = `output/insights/2026-08-11_t756-commit-witness/verbatim/ruling-package.md`

- {{T:legacy-commit-witness-backfill}} **P2・ユーザー裁定待ち**: 既存 WAL の witness なし COMMIT の
  扱い。新 gate は本 commit 以降の run にしか効かず、`replay.py` / `guided.py` 経由で旧 certified と
  fitness が現行の選択材料に残る。三択 = (a) verifier-policy epoch を campaign identity に入れて
  再評価 / (b) `legacy-no-commit-witness` として現行 certified 選択から除外 / (c) 現状維持を明記。
  受理集合と campaign identity を変える判断なので AI は実装しない

- {{T:coverage-driver-commit-witness}} **P3**: coverage 系 4 driver
  (`s3_lock_coverage` / `s5_permutation_coverage` / `s8a_trigger_coverage` /
  `t152_write_intent_coverage`) の `*_certified` 材料値が witness 未装備。うち 3 本にテストが無く
  受入で検証できないため本 wave では scope 外にした。既発行 insights の材料値はこの限界を持つ

- {{T:mutation-runner-drift-scope}} **P2**: enforcement source closure
  (`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の 8 path) を変異させる wave の runner 作法。
  一時変異が `verify_live_contract_loader_binding` を破って無関係な約 26 node を赤にするため、
  runner を drift 非感受な node へ絞り drift control を 1 件置く。本 wave の実測が独立 1 例目
