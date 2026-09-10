単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (read-only)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **審査対象の差分**: `git diff 21dfbe0f3..HEAD` (base `21dfbe0f3` は local main を取り込んだ merge commit)
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 契約の追記訂正 2 の草稿: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/contract-v3.1-erratum-2.md`
- 実装子の報告 3 本: `out-s5-a1.md`, `out-s5-a2.md`, `out-s5-b.md` (同じ job dir
  `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/`)
- fix 子の報告: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-fix1.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 6 レビュー A — 正しさ防壁と reward hack のレンズ

作業 root は read-only である。**書込み可能な tmp は無い。pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。テストの実走は親が行う。
**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## 攻撃してほしい点

1. **blocker 1 が本当に閉じたか。** campaign は phase 1 の pre-probe が competing のとき
   marker を消費せず launcher を呼ばないか。**実装の code path を追って確かめる。**
   competing 枝で marker が消費される経路 (例外時、resume 時、cut-6 replay 時、finalize-pending 時)
   が 1 本でも残っていないか探せ。
2. **holdout inspector が緩んでいないか。** `s8b_holdout_admission.py` の competing 規則と
   marker 検査に手が入っていないことを差分で確認せよ。もし入っていたら **real の重大所見**である。
3. **恒真な検査。** 新設された test のうち、**その test が守ると謳う性質を壊しても赤にならない**
   ものを探せ。とくに次を疑う。
   - 実 `inspect_floor_holdout_admission_evidence()` を通すと称して stub / synthetic case を使っている
   - 封印 pre-probe の偽装拒否が type 検査だけで、issuer/owner/one-shot のどれかが実際は効かない
   - v5 prefix の被覆検査が「消費された非 competing session」でなく空集合でも通る
   - planned / retry の ordinal 負例が、両軸が同値の fixture のため誤軸でも通る
4. **v5 proof の射程。** result が載せる `attempt_registry` proof は、実際に emit された terminal を
   すべて覆っているか。prefix capture の位置 (最後の terminal の前/後) を code で確かめよ。
5. **受理集合の向き。** 差分全体で、親が裁定した 2 点 (二段化・ordinal 訂正) 以外に
   受理集合を広げた箇所が無いか探せ。**「型検査を外した」「連言を 1 つ落とした」形を特に疑う。**
6. **erratum の主張の検算。** 「旧束縛は retry 側で恒真に 0 を強いる検査だった」「訂正は緩和ではない」
   という 2 つの主張を code で検算せよ。誤りなら **real** として指摘し、正しい表現を提案せよ。

## 判定の書き方

各所見に **real / refuted** と、[実測] か [推測] のラベルを付けよ。
[実測] は自分が読んだ file:line か grep 結果に基づくものだけに使う。
成果物影響 (certified 選択・レポート・台帳の値・受理集合・参照がどう変わるか) を 1 行で書けない
所見は **nit** と明記せよ。

## 禁止

- 実装しない。patch も diff も出さない。file を作らない。
- 「防御的堅牢化」を目的に新しい gate・検査・台帳を足す提案をしない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行)

## 所見 RA-1 ... RA-n
(各: real/refuted、[実測]/[推測]、根拠 file:line、成果物影響 1 行、推奨)

## blocker 1 が閉じたかの判定 (残る経路の全列挙)

## 恒真な検査の判定

## 受理集合を広げた箇所の判定

## erratum の 2 主張の検算
```
