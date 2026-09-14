単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/2026-09-14.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い)。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## レビュー対象

親が新規追加した `docs/paper-story/2026-09-14.md` (約 207 KB、§0〜§9。§10 は本レビューの後に書く) と、
親が更新した `docs/paper-story/README.md` の 3 箇所 (版の履歴表・最新版の訂正一覧・
「最新スナップショット以後に確定したこと」)。**既存の版・`results/`・`figures/`・`claim-evidence/` は
1 byte も変えていない。**

## レンズ A — 一次資料との照合、母集合、射程

お前のレンズは **「本文の数値・日付・判定・識別子・path が一次資料と一致するか」
「母集合と射程を取り違えていないか」「一次資料が言っていないことを言っていないか」** である。

**特に次を照合せよ。**

1. **数値。** A-2 の 4 cell の median と `effects`、A-6 の 2 cell の median と `effects`、
   balanced stock-inline 対の 5 標本 / median / cv / ratio / improvement_percent、
   P2-4 の 3 値と分母、P2-5 の A と p、S' の 4 判定、B-10 の 3 族 Holm p、
   走行間ばらつきの 3 workload の CV、A-1 の n / df / t 臨界、
   静的 1000 µs と 999 µs の差の 3 値。**1 つずつ権威 bytes と突き合わせよ。**
2. **識別子。** attempt ID、request ID、campaign ID、commit SHA、D 番号、T 番号、
   schema 版、pin。**存在しない D 番号・T 番号を引いていないか。**
3. **path。** 本文が引く `output/insights/` の path が実在するか。
   **2026-09-08 以降の記録は `output/insights/<日付>/<slug>/` の形である。**
   旧形式と新形式を取り違えていないか。
4. **母集合と役割。** 「4 cell とも certified」の内訳、stock cell と adopted cell の genome、
   「3 workload」が何を指すか、「2 workload の論理積」の扱い。
   **親は前版の母集合の誤りを訂正したと主張している。その訂正自体が正しいかを確かめよ。**
5. **射程。** 各裁定 (D番号) の決定内容を、本文が広げて引いていないか。**特に
   D1645 の解除条件、D1936 項21 の対象、D1829 の射程、D1678 が閉じた範囲、D1870、D1986 項5、
   D1858 を逐語で確かめよ。**
6. **正しさの緑の染み出し。** correctness certified を性能の文・表・要約へ持ち込んでいないか。
7. **凍結物の非接触。** 本文が既存の版・`results/`・`figures/` の内容を書き換えたかのように
   書いていないか。**逆に、既に `figures/README.md` にある fig6 の記述と食い違っていないか。**

## 出力形式 (この見出しをそのまま使う)

## 所見

各所見を次の形で書く。番号 / 対象 (§と該当箇所) / 主張 / 一次資料の path または D 番号 /
確度 (高・中・低) / must-fix か nit か / 是正案 1 文。**確度の根拠を必ず書け。**
**照合して一致した主要な数値も、件数と代表例だけ「照合済み」として報告せよ。**

## land 可否

GO / NO-GO と、その理由を 3 行以内。

## 総括

10 行以内。最も重い所見 1 件を名指しする。
