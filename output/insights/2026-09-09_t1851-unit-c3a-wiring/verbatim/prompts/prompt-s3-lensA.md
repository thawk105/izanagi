単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **攻撃対象 1 — 段 2 plan**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- **攻撃対象 2 — 親の段 1 brief**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 裁定 2 の原文: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/ruling-package.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 3 レンズ A — 「plan が立たない」という結論を反証しに行く

作業 root は read-only である。**書込み可能な tmp は無い。pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。テストの実走は親が行う。
**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## このレンズの立場

段 2 plan は「現行契約と既存テストを保ったままの C3 実装は成立しない」と結論し、
未裁定 blocker 2 件を挙げた。**あなたの仕事は、この結論を壊しに行くことである。**

- blocker 1: `FloorAttemptReservation.consumption_marker` を launcher の pre-probe 前に用意すると
  holdout inspector の competing 規則 (`s8b_holdout_admission.py:4349-4392,5082-5103,6577-6582,6733-6741`)
  に必ず反する。
- blocker 2: v2 slot の `measurement_ordinal` と terminal evidence の `retry_ordinal` 束縛が食い違い、
  planned と retry の双方で sealed terminal を構築できない
  (`s8b_terminal_evidence.py:760-792,1140-1160`、`s8b_attempt_registry.py:2534-2538,:2367-2370`)。

## 必ず答えること

1. **blocker 1 は real か refuted か。** 該当 assert / 例外の**発火する行**を名指しし、
   campaign が実行時に持つ値でその条件が本当に成立するかを追う。
   **既存の受理集合を 1 bit も広げずに済む構成が実在するなら、それを file:line で示せ。**
   例えば marker 発行と probe の順序を campaign 側の呼び出し順で満たせないか、
   既存の注入 seam や 2 段 API が既にあって plan が見落としていないか。
2. **blocker 2 は real か refuted か。** planned session の `retry_ordinal=None` と
   retry の ordinal を、**契約 v3.1 §1.5 と既存 fixture を変えずに**運べる経路が実在するか。
   `slot_id` の 5 軸のどれが何に束縛されているかを現物で確かめて書け。
3. **9 file の見積りは正しいか。** 過大なら削れる file を、過小なら足りない file を名指しせよ。
   plan が挙げていない consumer・fixture・AST 走査・行番号 pin が波及しないかを探せ。
4. **親 brief 自身の欠陥。** (P1-1) F660 不発火の判定、(P1-2) 5 file 仮定、(P1-3)
   「certified 成果物への到達経路 0 件だから凍結面を動かさない」の 3 つを検査せよ。
   **親は main 側登録簿と `git diff --stat` で実測したと書いている。その実測の一般化が
   正しいかを疑え。**
5. **plan の変異候補 14 件のうち、帰属が成立しないもの・過剰決定なもの**を名指しせよ。
   期待 kill node が実在しない (これから新設する) ことは欠陥ではないが、
   「その変異でしか赤にならない」と言えない候補は指摘せよ。
6. **段 4 の裁定パッケージへ回すべき設計択一**を、択一の形 (a)/(b)/(c) で整理せよ。

## 判定の書き方

各所見に **real / refuted** と、[実測] か [推測] のラベルを付けよ。
[実測] は自分が読んだ file:line か grep 結果に基づくものだけに使う。
成果物影響 (certified 選択・レポート・台帳の値・受理集合・参照がどう変わるか) を 1 行で書けない
所見は **nit** と明記せよ。

## 禁止

- 実装しない。patch も diff も出さない。file を作らない。
- 正しさゲートを緩める方向の提案をしない (検証を甘くして blocker を回避する案は却下として書け)。
- 既存テストの期待値を変える案を「軽微」と書かない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行。blocker 2 件の real/refuted 判定と、結論が変わるかどうか)

## 所見 A-1 ... A-n
(各: real/refuted、[実測]/[推測]、根拠 file:line、成果物影響 1 行、推奨)

## 9 file 見積りの検査

## 親 brief の 3 前提の検査

## 変異候補の帰属検査

## 段 4 へ回す設計択一
```
