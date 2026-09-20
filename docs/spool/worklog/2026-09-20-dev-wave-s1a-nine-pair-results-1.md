---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-s1a-nine-pair-results
seq: 1
title: S-1a (系側 gate 構成 g_rl / g_rt 対 既知軸最良 3 種の直接比較 9 対、family 判定 不成立) の単独 results 稿を S-1 登録追試 1 本走の一次資料全体から書き、README の results 表へ 1 行足した — 「判定しないこと」を先頭に置き、実施回数と主張範囲を分け、既知軸集合が合成未探索の下界であることを併記 (docs のみ、branch worktree-dev-wave-s1a-nine-pair-results)
---

## 本文

- ユーザー依頼は「S-1a (合成軸 = 系側 gate 構成 g_rl / g_rt が既知軸最良を超えるか、9 対の直接比較、判定 = 非有意・不成立) の単独 results 稿
  `docs/paper-story/results/2026-09-2x-s1a-nine-pair-direct-comparison.md` を一次資料から書き、README の results 表へ 1 行足して land まで
  (docs のみ、実装差分ゼロ、軽量版だが一次資料から不在・数値を書き起こす稿なので段 6 read-only レビュー 1 本 + 焦点再レビュー)。台帳 ID 未起票。
  一次資料 = `output/reports/s1_direct_comparison/report.json` (sha256 `491ad38d…`) と report.md、fig4 provenance、S-1 事前登録 (凍結 source、読むだけ)、
  関連 D。書き方は A-6 単独稿と同型: 『本稿が判定しないこと』を最初に置き、限定を番号で列挙、実施回数と主張範囲を分け、『既知軸最良を超えなかった』を
  『合成が無価値』と読まない、適格率次元の発見再現性は未実証と併記 (確定文言どおり)。値は一次資料から逐語で取り推定しない。着手直前の local main から
  fresh worktree。scope 外 = 図の作り直し・新しい測定・他稿の改訂」。
- **稿を作成した。** 成果物は `docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md` (results 系列の凍結物、§0 に「判定しないこと」8 項を先頭配置、
  §1 何を測ったか (事前登録の HARKing 境界・18 cell と 9 対の定義・判定規則・実行 identity・hard gate)、§2 結果 (9 対・12 cell の 8 標本・効果量と CV・
  ブロック効果・正しさ・Holm 族 4・retry と時間台帳)、§3 他の記録との関係 7 項、§4 限定 19 件 (レビュー後に 2 件追加)、§5 一次資料の sha256 表と値の出所、図は fig4 の既存物) と
  `docs/paper-story/README.md` の results 表 1 行 (K2 行の直後)。**新しい測定は 0 件。凍結物 (report・freeze・provenance・図・4 campaign・事前登録・
  S' 最終報告・確定文言) の bytes は 1 byte も変えていない。**
- 段 1 で親が一次資料の現物を全部読んだ: report.json (9 比較行の gate1 / gate2 / p / 効果量、`families.s1a` = 不成立 p 1.0、hard gate 全 pass、時間台帳
  22,943.7 s / 43,200 s)、fig4 provenance (12 cell × 8 標本、`freeze_proof` の 3 pointer 差、`claim` 9 / 3 / 6)、measurement_freeze (18 cell の genome・gate 述語・
  comparator・注記)、正典 4 campaign の WAL (develop 127 / floor 1,009 / block 505 × 2 行、全 session attempt 0・success/certified、build 306 件の configure
  flag 同一・`-DCCBENCH_TRACE=0`、bench 288 件の argv 同一・`perf stat` 下、verify 324 件すべて serializable/certified/anomaly 0)、時間台帳 335 entries
  (`machine-failure-retry` 6 件 = 120.65 s はすべて develop v1 `…-7bccdf1a` の build-error)、事前登録 (層 1 (i)〜(iv 付属)・層 2・承認記録・族 4 追記)、
  S' 最終報告、確定文言 §3 付記、worklog 2026-07-16 (1)(2)。sha256 は provenance の記録値と現物で全件一致。
- 素材: 結果節の主判定文は稿 §0 — 「S-1 登録追試 (2026-07-16、旧環境 linux-baremetal) の直接比較 9 対では、系側 gate 構成 g_rl / g_rt の中央値は sort_best に
  対して 3 workload とも +55.5%〜+98.4% で判定境界 +3% を超えたが、p2_2_flag_opt に対して −9.3%〜−55.1%、backoff_fixed_best に対して −36.0%〜−51.9% で
  超えず、家族連言 (9 対すべて成立) を満たさないため S-1a は不成立である (family p = 1.0)。これは結果既知の事前登録付き追試の出力であり、新しい否定的
  発見でも、合成が無価値であることの証明でもない。適格率次元の発見再現性は未実証のままである」。gate (2) (block 間の方向一致) は 9 対とも通過し、
  負けた 6 対は 8 対 8 標本が完全分離 (確率優越 0.0)。`floor_cmp` は 18 の floor CV がすべて 3.0% 未満なので 9 対とも下限 3.0% で決まる。
- 素材: 旧環境の値である (CCBench `d706650`、`clocks_per_us` 1,800、gcc-13、`perf stat` 下)。`backoff_fixed_best` の genome 値 (5 / 10 / 2 µs) は A-2 / A-6 の
  採用値と同じ数値だが同じ測定ではなく、前後比較しない (規律 7、D496)。事前登録 (iv 付属) の検証相 (8 独立反復 × 3 workload) の記録は一次資料に無く、
  report.md も「独立な検証相を持たない」と明記。develop v1 (`…-7bccdf1a`、24 start / 15 commit) は tracked だが provenance の inputs に無く、出所にしない。
- 親の provisional 裁定 3 件: (P1) S-1b は §3 の関係記述のみ、(P2) 台帳の retry 6 件を `started_iso` で v1 に帰属し index → cell の対応は worklog の記録による、
  (P3) 現行コードとの差 (plot 生成器・s1_stats・freeze 生成器の sha) は事実として書き判定を無効にしない。
- 段 6 (read-only codex 1 本、`gpt-6-astra` / `medium`、25 call、629 秒、2 レンズを 1 本で): **NO-GO、所見 9 = must-fix 3 / should-fix 4 / nit 1 / refuted 1。
  real 8 件を全件採用した。** 数値・判定・sha256 は全件一致 (§2.1 の 9 行、§2.2 の 96 標本の median / mean 独立再計算、§2.3 の 63 値、freeze 18 cell、WAL の段別件数、
  306 accepted session、時間台帳 335 件、§5.1 の 22 file + 現行 3 file の sha256)。must-fix は (1) §2.4「ブロック効果は中央値差より 1〜2 桁小さい」が誤り (最小比は
  write-heavy 対 p2_2_flag_opt の 174,173 対 21,627 = 約 8.05 倍) で「判定を左右しない」が頑健性の言い過ぎ → 絶対値範囲と大小関係だけを書き頑健性は主張しない、
  (2) §0 の必須併記が原文の言い換えで「S-1b の成立はこの限界を解消しない」を落としていた → 確定文言 §3 付記と S' 最終報告 §4 の 2 文を逐語で置く、
  (3) develop v1 の数値 (24 start / 15 commit) と index → cell の対応を figures/README・worklog の散文から引きながら「一次資料から作った」と宣言していた →
  親が v1 の WAL を集計して検算 (151 行、index 3 / 9 / 15 = 3 workload の backoff_fixed_best、各 attempt 0〜2 が build-error → abandoned、sha256 `d620ff91…`)
  し §5.1 の出所に入れ、時刻の前後だけでなく index・attempt・reason の一致で帰属した。should-fix は fig4 provenance の inputs (lock + 現行 freeze を含む 6 entry)、
  検定力の限定 (事前登録 層 1 (iii) の「prospective power は未保証と明記する」を §1.3 と限定 18 へ)、校正費用の台帳上の位置が未特定 (335 = 324 + 6 + 5 で校正 entry
  なし、限定 19)、「反復 attempt は無い」の絶対断定を「凍結資料に記録された本走は 1 回、第 2 の本走は資料から特定していない」へ。refuted 1 件 (gate 述語の読み・
  (P1)・(P3)) はレビュー自身が裏付けを確認し現行維持。焦点再レビュー 1 本 (13 call、217 秒): **closed 8 / partial 1 / regressed 0、GO**。partial は README 行が
  省略引用に「原文どおり」と付けていた点 (新規 should-fix 1) → 「原文の逐語引用は稿 §0・§3.2」へ直した。逐語は job dir `codex/` (review 1 + focus 1)。
- 段 4 の provisional 裁定 (P2) の「正典開始より前」という時刻条件だけでは v1 への帰属の十分条件にならない、というレビューの指摘は正しい。v1 の WAL 自体を読めば
  index・attempt・reason・時刻が全 6 件一致するので、稿はその整合で帰属している。
- 変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。三軸語走査 (`s8b_holdout_freeze search`) は hit 4 file がすべて main 既存の g1 凍結物で、本 wave の新規 file は
  含まない。`check_docs.py` 違反なし。fold `--dry-run` planned。受入全走は免除せず、本 fragment の commit 後に同一 tip で投入する (結果は land の受領証と job dir に
  残し、fragment には書かない)。
- 門番 script の leader 判定が他 wave の codex 子の argv (prompt 文字列) を偽 leader に数えた (実 leader 0、13:5x JST 実測) ので本 wave の写しでは argv 先頭一致に直した。
- 工数: codex 2 本 (read-only review 1 = 25 call / 629 秒、focus 1 = 13 call / 217 秒、いずれも gpt-6-astra / medium)。計算ノード job = 受入のみ。

## 次の一手差分
