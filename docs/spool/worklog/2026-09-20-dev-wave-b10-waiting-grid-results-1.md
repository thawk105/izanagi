---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-b10-waiting-grid-results
seq: 1
title: B-10 待ち方 grid の正式走 (report phase 978195.nqsv、D1678 で「現行 report で閉じる」) の単独 results 稿を 1 判定の一次資料全体から書き、README の results 表へ 1 行足した — 限定を先頭に置く凍結稿、独立 read-only レビュー 1 本が must-fix 3 (区間の分類・単調性・別 node) を出し焦点再レビュー 2 本で閉じた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-b10-waiting-grid-results)
---

## 本文

- ユーザー依頼は「B-10 待ち方 grid の正式走 (3 族すべて Holm で different、方向は 3 族とも symmetric-modulo が高い側、効果量は全 36 cell が等価域 ±3.0% の
  内側 32 / 境界 4 / 外側 0 / 判定不能 0、3 campaign 135 cell の correctness certified 270/270、D1678 で「現行 report で閉じる」と裁定) の単独 results 稿
  `docs/paper-story/results/2026-09-2x-b10-waiting-grid-formal.md` を一次資料から書き、README の results 表へ 1 行足して land まで (docs のみ、実装差分ゼロ、
  段 6 read-only レビュー 1 本 + 焦点再レビュー)。台帳 ID 未起票。一次資料は D1678 が指す 2026-09-07 の report phase の判定 (report・受領証・事前登録 §9・WAL)
  を段 1 で同定して sha256 束縛。書き方は 2026-09-16 静的 tail 稿と同型: 『本稿が判定しないこと』を最初に、事前登録 §9 の見送り 5 項目 (再訪 = 査読要求) と
  制約 3 つ (D1092 / D1094 / D1097) を限定として列挙、右 tail の 2 cohort と合成しない、機序は指示値の平均に限定。着手直前の local main から fresh worktree。
  scope 外 = 図・追加測定・右 tail 稿の改訂」。
- **稿を作成した。** 成果物は `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` (results 系列の凍結物、file 名の日付は起草日 = 2026-09-20、
  §0.2 に「判定しないこと」を先頭配置、§3 に限定 19 項、§2.6 に全 135 cell、§4 に一次資料の sha256、図は無い) と `docs/paper-story/README.md` の results 表
  1 行。記録 insight は `output/insights/2026-09-20/b10-waiting-grid-results-doc/README.md` (一次資料の実測表・sha256 照合表・機械照合・レビュー逐語)。
  **新しい測定・再解析は 0 件。凍結物 (report 成果物・事前登録・3 campaign の record / lock / WAL・受領証) の bytes は 1 byte も変えていない。**
- 段 1 で親が一次資料を同定して現物を読んだ: report 成果物 2 件 (provenance JSON 606,952 B / report .md 31,133 B、sha256 は記録 insight の値と一致)、
  事前登録の発効版 v4 (commit 77b33e37d、blob ea910de32、35,820 B。§9 は 9 bullet で、D1678 の 5 項目は bullet 1・2・5・9 に対応)、report と 3 workload job の
  受領証・job 結果 (repo 外、driver_rc 全 0)、3 campaign の record 封筒 45 × 3・lock・WAL 135 行 × 3 (verify_done 90 件ずつ全件 certified / serializable /
  anomaly 0)。3 campaign は driver 版が違い (write-heavy 0a07481b8・host 未記録、balanced c7ed56589・bnode015、read-heavy 2a338449b・bnode088)、旧 2 系列は
  D1588 / D1636 の限定受理で集約に入った。対差 54・効果と区間 18 cell・等価域判定 36 cell・135 行の表を record から再計算して全一致、raw p は 2^18 分母の
  6702 / 70 / 2。活動を止める裁定は 0 件 (D1771 / D1834 は report の bytes を変えない、規律 7)。
- 素材: 結果節の書き方は稿 §2.7 — 「48 スレッド Silo / YCSB 3 workload、μ = 2〜100 µs の登録 grid で、`constant` と `symmetric-modulo` の 2 実装の間の
  throughput の差は事前登録した手続きで 3 族とも検出された (`different`)。方向は 3 族とも `symmetric-modulo` が高い側。効果量の 95% 区間は 32 cell で等価域
  ±3.0% の内側、4 cell で境界を跨ぎ、区間全体が外側に出た cell は無い。これは 1 contrast についての主張であり、待ち方の効果一般・用量反応・`binary` を含む
  ladder・直交切り分けの一般化については何も言わない」。「機序」「優劣」「B-10 の閉鎖」「検出力の範囲内」は書かない。
- 段 6 (codex read-only、`gpt-6-astra` / `medium`): **review 1 = must-fix 3 / should-fix 3 / nit 1、「止める」。1〜6 real 採用、7 refuted。** 数値表・判定値・
  sha256 は全一致 (2^18 列挙で raw p を独立再現) で、所見は散文の量化に集中した: 題名の「内側か境界上」は区間の分類を誤る (境界を跨ぐ 4 cell は区間の一部が
  外)、「μ が大きいほど throughput が下がる」は write-heavy で偽、「別 node」は write-heavy の host 未記録で確定不能、README の D1097 の主語、zero-loop の
  名目総待ち量 0、D1588 の失敗系列の開示。focus 1 = closed 6 / partial 1 (balanced の単調性を過剰一般化) + insight の旧表現 → 修正。focus 2 = closed 2、
  新規所見なし、GO。3 巡は `DW-O16` の上限内。
- 変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。三軸語走査の hit は既存 holdout 候補 file 群のみ。`check_docs.py` 違反なし。fold `--dry-run` rc=0。
  受入全走は免除せず、本 fragment の commit 後に同一 tip で投入する (結果は land の受領証と job dir に残し、fragment には書かない)。
- failures fragment 1 本 (F1 の near-miss 再発 = 記録 insight の要約文「別 node」と表を見ずに書いた単調性を散文へ転写し、レビューで凍結前に捕捉)。
- 工数: codex 3 本 (read-only review 1、focus 2)。計算ノード job = 受入のみ。

## 次の一手差分
