単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **攻撃対象 1 — 段 2 plan**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- **攻撃対象 2 — 親の段 1 brief**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 裁定台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md`
  (D1341, D1114, D1194, D1660, D1661, D1703 を引くこと)
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 3 レンズ B — 提案が正しさ防壁と受理集合をどう動かすか

作業 root は read-only である。**書込み可能な tmp は無い。pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。テストの実走は親が行う。
**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## このレンズの立場

レンズ A は「blocker が本当に blocker か」を攻める。**あなたは別の面を攻める** —
plan と親 brief が提案する変更が、**正しさ防壁を弱め、受理集合を黙って広げ、
恒真な保証を作り、あるいは死んだ gate を land させないか**を検査する。

## 必ず答えること

1. **受理集合の向き。** plan が挙げる 2 つの blocker 解消案
   (a: v2 だけ「launcher が予約のため消費した competing attempt」を認める、
   b: launcher API を二段化して probe 後に marker を発行する) は、
   受理集合を**広げる**か**狭める**か。widen する側は D1660 の
   「受理集合は狭まる方向にしか動かない」と衝突しないか。file:line で示せ。
2. **恒真化の危険。** plan の負例 11 件のうち、**その変異を当てても赤にならないもの**を探せ。
   特に「新設する admission の対になる正例・負例の片方が赤」のように**実体を名指ししていない**
   負例を疑え。正例・負例は実体を名指しし依存先を stub しない、が要求である。
3. **死んだ gate。** plan は C3a (配線・v5 producer) と C3b (実 campaign・値域記録) の分割を
   推奨する。**C3a だけが branch に載った状態で、謳うだけで発火しない保証が生まれないか。**
   D1114 (b) の「先行 land すると死んだ gate になる」と D1341 の同時 land 要求に照らして検査せよ。
   本 branch は land しない unlanded checkpoint であることを踏まえて判定せよ。
4. **v5 producer の射程。** plan は `RESULT_SCHEMA` を global に v5 化せず
   `PRODUCTION_RESULT_SCHEMA` を追加する案を出す。この二重化で
   **consumer が v4 を読み続けたまま producer だけ v5 になる不整合**が生まれないか。
   `s8b_ratified_freeze.py`、`s8b_holdout_admission.py`、`s8b_floor_stats.py` の
   consumer 側 exact key 検査を現物で確かめよ。
5. **pin 閉包の抜け。** plan の pin 列挙に無い pin を探せ。whole-file sha256、行番号、
   role 名、xdist group 名、nodeid、AST 走査、key→path 束縛のどれかで張られたものを
   **path 検索以外の手段で**探すこと。plan は「whole-file hash pin は 0 件」と書いている。
   これを検算せよ。
6. **値域 receipt の誠実さ。** plan は `gate-input-values.json` に exact type・key set・
   列挙値・min/max・件数・出所 path と SHA-256 を書くとする。
   **この receipt が「実環境の値域を供給した」と主張できる条件**は何か。
   1 回の campaign で観測した値域を母集合として一般化してよいか (観測 regime と適用対象の一致)。
   主張できないなら、成果物へ書くべき限界の文言を提案せよ。
7. **親 brief の不変条件 4 件**が、plan の提案で守られるかを 1 件ずつ判定せよ。

## 判定の書き方

各所見に **real / refuted** と、[実測] か [推測] のラベルを付けよ。
[実測] は自分が読んだ file:line か grep 結果に基づくものだけに使う。
成果物影響を 1 行で書けない所見は **nit** と明記せよ。

## 禁止

- 実装しない。patch も diff も出さない。file を作らない。
- 「防御的堅牢化」を目的に新しい gate・検査・台帳を足す提案をしない。
  現目的・実在欠陥・受入要件に必要で、既存策の不足を資料か実測で確認できる場合だけ推奨せよ。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行)

## 所見 B-1 ... B-n
(各: real/refuted、[実測]/[推測]、根拠 file:line、成果物影響 1 行、推奨)

## 受理集合の向きの判定

## 恒真化の危険がある負例

## 死んだ gate の判定

## consumer 不整合の判定

## pin 閉包の抜け

## 値域 receipt が主張できる条件と限界の文言案

## 親 brief の不変条件 4 件の判定
```
