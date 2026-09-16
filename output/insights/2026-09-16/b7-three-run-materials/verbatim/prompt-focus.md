単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

**再レビュー対象**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節の表 (2026-09-16 の行)

**前回の所見 (これを 1 件ずつ閉じたか判定する)**

3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/review-a-out.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/review-b-out.md`

**照合に使う一次資料**

5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json`
10. `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b` 配下の
    `jobs/rr5/raw/rr5-stock.json`、`jobs/rr5/raw/rr5-fixed10.json`、`jobs/rr50/raw/rr50-stock.json`、
    `jobs/rr50/raw/rr50-fixed5.json`、および rr5 / rr50 それぞれの campaign の `runs/wal.jsonl`
11. `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` 配下の
    `jobs/rr95/raw/rr95-stock.json`、`jobs/rr95/raw/rr95-fixed2.json`、および rr95 の campaign の `runs/wal.jsonl`
12. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json`
13. 同 root の `reservation.json` と、campaign `backoff-sweep-silo-balanced-sweep-0dd37c05` の `runs/wal.jsonl`
14. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/t1998-balanced-stock-inline-preregistration.md`
15. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md`
16. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md`
17. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`

## 依頼

**前回の 2 本のレビューが出した所見を、親が全件反映した。反映が本当に閉じたかを判定する。**

1. **所見ごとの対応表を作る。** review-a と review-b が挙げた所見を 1 件ずつ列挙し、
   `closed | partial | regressed` を付ける。**表を作らずに「閉じた」と言わない。**
   review-a の所見 (解析回数、表の行数、`同名 field`、事前登録 §9 引用の無表示省略、
   事前登録 §7 引用の非逐語、arm 別 source digest の帰属) と、review-b の所見
   (限定 19 の広すぎる採用禁止、A-5 限定の欠落、事前登録 §8 の identity 実値、
   D1631 の全体再導出範囲) が対象である。
2. **親が新しく書いた派生値を原データから再計算して照合する。** 親は今回、次を新しく書いた。
   **どれも原データから計算し直して確かめる。**
   - §2.3 の「8 arm とも `標本標準偏差 (分母 n−1) / 標本平均` が campaign WAL の `cv` と
     倍精度の全桁で一致した」。
   - §2.3 の「A-6 の 1.18% / 1.06% を生標本から母標準偏差 / median で計算すると
     1.1827% / 1.0560% になる」。
   - §4.3 の「raw JSON と campaign WAL の SHA-256 が raw manifest の束縛と 6 件 + 3 件すべて一致した」。
   - §2.2 の「8 arm すべてについて 2 つ以上の記録が同じ並びを持つ」。
   - §2.4 の「6 cell とも `correctness.legacy` が 1 要素、`correctness.performance` が 5 要素、
     `build_evidence.performance_trace_disabled_build` が `true`」。
   - §1.4 の arm 別 source bytes SHA-256 2 件が campaign WAL の `build_start` にあること。
3. **「すべて」「だけ」「例外なく」「一致した」という量化が本当に全数か**を確かめる。
   数えたうえで、外れがあれば名指しする。
4. **反映の過程で新しく壊れた箇所 (regressed) が無いか。** 特に §2.2・§2.3・§2.4・§4.2・§4.3 は
   大きく書き換わっている。重複、矛盾、消し残し、番号のずれを探す。
5. **入口 README の 1 行**の「限定 20 件」「3 走行・4 対比較・8 arm」が本文の実数と合うか**数える**。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- 数値を版 (`docs/paper-story/2026-09-14.md`) や既存稿から取らない。出所は一次資料だけとする。
- 所見が無いなら「無い」と根拠つきで書く。再計算したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 所見ごとの対応表
## 派生値の再計算
## 量化の全数確認
## 新しく壊れた箇所
## 入口 README の 1 行
## 総括
