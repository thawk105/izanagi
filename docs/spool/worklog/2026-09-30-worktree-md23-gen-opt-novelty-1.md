---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-md23-gen-opt-novelty
seq: 1
title: gen-opt で論文が成り立つか (md_23) — 新しさの地図・条件と SOTA の事前登録・R1〜R3 の余地の測定 (261 点、約 1.0 node 時間) と判定: 推せるのは R1 だけで条件付き (docs + insight、branch worktree-md23-gen-opt-novelty)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_23.txt` (19:31 JST 版) と `common-5.txt`。一次資料 `output/insights/2026-09-30/gen-opt-novelty-and-regime/README.md`。
- 結論 (一次資料 §0): 推せる条件は R1 (YCSB hotspot、zipf 0.99・48 thread) だけで条件付き。余地は大 (最良 = Silo の静的 backoff 5 µs 2.28M tps・abort 率 68%、r1 3.59・r2 3.15) だが、
  NeurCC が同種の hotspot YCSB で Silo の最大 4.27 倍を報告している。今の izanagi の hook は T1 (施錠順) と T5 (待ち方) だけで、T5 は学習型 CC の表現範囲と重なり、
  T1 は Cicada の手作りの機構と同じ型なので、範囲外を主張するには T2 (validation)・T3 (実行前の並べ替え)・T6 (組み合わせ) の口が要る。
  R2 (TPC-C 1 warehouse) は stock の 21 構成中 13 構成 (SI の参考 2 構成を含む) が成功 2 回未満 (Silo・MVTO の insert order failed の空転、ERMIA・SI・Cicada の GC の ERR、SS2PL の segfault) で推さない。
  R3 (BoMB) は登録の指標 (短い取引の throughput) では小だが、測れた直列化可能なプロトコルの全構成 (SS2PL は segfault で未観測) で長い取引 L1 が混在時に 3 秒間 commit 0 回 (登録の指標の外、次の登録の候補)。
- 新しさ: N4 (LLM が取引の CC の判断を実装するコードを生成し性能を評価) は ADRS 系 3 本の検出で不成立。N5 (生成物の直列化可能性を探索の反復の中で機械検査) は
  arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲では未検出 (RW2)。OpenAlex は匿名検索の一時停止と時間切れで run1〜run3 とも未完走、DBLP は不使用。
- 事前登録: 検索 (`a28f9111d`)・条件 (`ba6e86342`) を結果前に commit。改訂は結果前に 4 件 (BoMB の起動形、1 走の上限と失敗の扱い、OpenAlex の 503、取得 script の欠陥)。
- セッション異常: (1) 開始時に handoff を home の job dir に作り 19:42 に `/work/SFC/tanab/tmp/md23-gen-opt-novelty-2026-09-30/` へ移した (開始 gate の log は home の path)。
  (2) 20:38 に利用上限で中断し、21 時台に同じ session で再開。(3) 計算ノードで 1 件ずつ欠陥が出る型を 3 回 (TMPDIR → third-party cache → compile 命令の照合) 踏み、build を 4 回投げた。
  (4) plan の初版が smoke の timeout 1 回を variant 全体の見積りに使い 66 job に割れたので、投げずに直した。(5) YCSB と TPC-C 目標の job は見積りの約 2.4 倍 (約 480 秒) で 5 分を超えた。
- 段 6 の read-only review (Codex 1 本): must-fix 5 件を real と裁定し親が文書で直した (R2 の B2 の算法の注記、prior-work の N4 の古い記述、R3 の L1 の全称を SS2PL 未観測に限定、N5 の RW2 の限定語、先行の本数)。判定は変わらない。棄却 2 件 (R3 の指標の差し替えは無い、単独性の確認は各 binary の直前にもある) はレビュー子自身が refuted とした。
- 子の工数: Claude の子 探索 1・原典読み 4・判定 1、Codex author 1・fix 8・review 1。計算ノード 約 1.0 node 時間 (build 約 585 秒・smoke 235 秒・本測定 2,729 秒)。

## 次の一手差分

### 新規

- {{T:gen-opt-paper-regime}} **P1・新規**: gen-opt で論文が成り立つか — md_23 の判定 (`output/insights/2026-09-30/gen-opt-novelty-and-regime/README.md` §4) を受けて方向を決める。
  推せるのは R1 (YCSB hotspot) だけで条件付き: (1) T2・T3・T6 の口を開ける hook と正しさ関門の設計、(2) NeurCC 級の学習型 CC を比べる相手に入れる方法
  (`docs/related-work/README.md` 7.1 の「実測比較は見送り」の再判断)、(3) 手作りの SOTA (Cicada の競合度順の施錠・TsDefer・BCC) の人の試作での並置。
  R3 の長い取引の飢え (測れた直列化可能なプロトコルの全構成で L1 commit 0) を指標にした条件の新規登録は、VHash (別 manager) との担当の切り分けが先。
  R2 は stock の CCBench の TPC-C 1 warehouse の欠陥 (13/21 構成が失敗) の修理が先。
