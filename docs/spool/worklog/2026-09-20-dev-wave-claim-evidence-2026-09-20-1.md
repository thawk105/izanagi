---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-claim-evidence-2026-09-20
seq: 1
title: 論文の claim-evidence 稿 2026-09-20 版を 2026-09-19 版の 5 節と一次資料から全面再導出した — 3 表 43 行・限定 L01〜L53、段 6 read-only レビューの所見 12 件 (must-fix 8) と焦点再レビューの残 2 件を反映 (docs のみ、branch dev-wave-claim-evidence-2026-09-20)
---

## 本文

- 依頼は「論文の claim-evidence 稿 2026-09-20 版 `docs/paper-story/claim-evidence/2026-09-20.md` を作る (docs のみ)。着手直前の local main
  から fresh worktree。README の『claim-evidence 系列』節の規則 (append-only、最新版 = 2026-09-19 版の §3 / §6 / §7 / §8 / §9 全体から
  作り直す、出所は一次資料だけ、版の履歴表に登録しない)。3 表と限定レジストリ (L01〜L28 を継承し A-2 observed-positive・A-6・T-1998・
  A-1 attempt-0001・B-10 cohort 1/2・検証相・B-7 fixed5 の限定を追加採番)、limitations 節の統制稿を更新。未着地の図・結果 (fig10・cohort 2
  後継図・裁定待ち T-2792 / T-2795 / T-2797) は完成済みとして取り込まない。README の系列表へ 1 行、README は受入の owned-path に入れない。
  段 6 は独立 read-only レビュー 1 本 (D2148 項 11)。新規計測・gate・台帳の追加は scope 外」。**全面再導出であり、前稿 (2026-08-26) の差分
  改訂ではない。** 前稿・版 9 本・`results/` 13 稿・`figures/` は 1 byte も変えていない。新規計測ゼロ。
- 導出の起点は local main `b7f970dfa` (2026-09-20、entry 1711 までの fold を含む)。入力は 2026-09-19 版 (blob `bde3c0c66`) の 5 節 +
  README の stale 注記 11 件が指す一次資料 (A-1 attempt-0002 の gate 拒否 D2156、B-10 cohort 2 D2157、K2 3 巡目、B-4 w1 実投入、
  chain land 2 度目の不成立、mocc 軽量 witness 4 arm と wave 2 D2159、B-5 事前登録 v1 D2158、A-2 nodes=5 整合、検証相 D2160、
  B-7 fixed5 D2162)。値は certification.json / result.json / calibration JSON / `tally.json` / policy JSON と results 稿 8 本の権威 bytes
  記録から取り、稿が引く repo 内 path 93 件と repo 外 path 9 件の実在を確認した。一次資料は
  `output/insights/2026-09-20/claim-evidence-20260920/README.md` (prompt・出力の逐語は同 `verbatim/`)。
- 稿の形: 前稿の §1〜§6 の骨格 + §7 (前稿との対応表)。claim 行は C1〜C17b を継承し C18〜C37・C15c を新設 (計 43 行)、限定は L01〜L28 を
  継承し L29〜L53 を新設。(c) の閉語彙は前稿の 6 値に「固定条件で certified な correctness」を足した 7 値 (2026-09-19 版 §9 の 7 種に
  一致)。前稿 C12 (単回 4 cell) は A-2 の正式 protocol 完走で置き換わったため行として残さず L24 と §7 で保持 (親の裁定 (P1))。
- 段構成は軽量版 (段 2・3 省略、段 5 = 親の docs 編集、変異 matrix は実装面ゼロで免除)。**段 6 は D2148 項 11 の read-only レビュー 1 本
  (Codex gpt-6-astra、medium、38 call、688 秒) が NO-GO・所見 12 件 (must-fix 8 / should-fix 2 / nit 1 / refuted 1) を返し、親が一次資料で
  検算して 1〜11 を real、12 を refuted とした。** 最重要は (i) B-7 fixed5 の correctness を legacy だけに縮めていた誤り (権威 bytes は
  6 cell とも legacy 1 + performance 5 = 36 記録)、(ii) 検証相の「30 verify」「未完走 2 件」が候補ごとの数であること、(iii) C2 (A-2 / A-6 の
  correctness) の (c) が稿自身の第 5 種と不一致、(iv) A-1 attempt-0002 の認可 (D2156) と「再認可は未判定」の衝突、(v) C15c が静的候補 (a) の
  再現まで書いていた過剰帰属 (t2774 §1 は「cycle 形は候補 (a) と整合」まで)、(vi) 2026-09-19 版 §7 からの脱落 5 件 (D1529 / D2090 /
  D1637 / 調整済み adaptive / 定数 K の積モデル) → L04 の復元と L51〜L53。fix 後の焦点再レビュー 1 本 (18 call、341 秒) は closed 10 /
  partial 1 / regressed 1 で NO-GO、残る 2 件 (§7 冒頭の「前稿 C11 は執筆時点で既に偽」は保存済み 7 件についての限定として読めば真で
  断定しすぎ、§6 の「落とした項目は無い」の残存) は親が real と裁定して直し、禁止句の残存 0 件・行 43・L 53・path 実在・`check_docs`・
  `git diff --check` を再走して閉じた (DW-O16、3 巡目は起動せず)。
- 素材: **claim-evidence 稿の全面再導出では、版の §9 の分類 (7 種) と稿の (c) 欄の閉語彙を一致させないと、同じ観測が「実証済み」と
  「固定条件の correctness」に分かれて数えられる** (所見 4)。**results 稿を 1 本ずつ読んでも、統制稿へ束ねるときに「legacy 小設定」の
  限定を別形式の走行 (fixed5 は legacy 1 + performance 5) へ広げる誤りが起きる** (所見 1)。**前稿の記述を「執筆時点の誤り」と認定する
  には、その記述の読み (保存集合についての限定か、機構一般の制限か) を分けてからでないと断定しすぎになる** (焦点所見 1)。
- 検査: `check_docs.py` 違反なし (5 回)、三軸語走査 rc=0 (両 holdout hit 0、陽性対照 227)、引用 D の実在、path 93 件 (欠 1 = 保存 branch
  上の g1 候補、稿がそう書く)、gitlink `511c9538`、A-2 / A-6 policy の `nodes` = 5。逐語 2 本の行末空白は可逆最小正規化 (原文 sha256 は
  insight §7)。受入全走は記録 commit 後の tip で投入する (結果は land の受領証)。
- 工数: codex 子 2 本 (review 1、focus 1)、author / fix 子 0。計算ノード job は受入全走のみ。push はしない。
- near-miss: 親が handoff の時刻を `date` で採らず推定で書き、直後の実測で 7〜11 分ずれた (F1 型、実害なし。failures fragment に再発として
  追記)。

## 次の一手差分
