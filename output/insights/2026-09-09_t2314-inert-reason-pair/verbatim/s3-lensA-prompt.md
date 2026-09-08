単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md`
  — 親の段 1 brief。**これ自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-d1625.md`
  — 確定済みユーザー裁定 D1625 の逐語。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md`
  — 段 2 のプラン。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
  — 変更対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py`
  — gate 本体。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`
  — test。読めなければ即停止。

## 依頼 — レンズ A: 正しさ境界

プランを**守らずに攻撃**せよ。実装はするな。書込み可能な tmp が無いので pytest 緑は要求しない。
静的検査で足りる。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

この wave は **受理集合を意図的に広げる**。広げすぎ・広げ足りない・別経路で骨抜きになる、の 3 方向を
すべて疑え。具体的に探すもの:

1. **受理集合が D1625 の 2 組を超えて広がる経路。** プランの新しい述語が、gate の第 3 の理由コード
   `requested-default-preprocess-different`、あるいは組を跨いだ交叉 (reason=A × comparison=B) を
   通してしまう形になっていないか。集合・辞書・`in` 判定の書き方を実コードで検算せよ。
2. **exact 性の劣化。** 元の述語は `==` の連鎖だった。プランがそれを `in`・部分一致・truthy 判定・
   `startswith`・正規表現へ落としていないか。`evidence.get("comparison")` が `None` のときに
   通ってしまう形になっていないか。
3. **他層による mask。** probe の述語を通す/落とすことが実際に S6 verdict を変えるか。
   `require_condition_gate_family` が先に同じ入力を弾くなら、probe 側の述語は恒真であり、
   この変更は「受理集合を広げた」ことにならない。**gate が組の不整合を先に弾く範囲を実コードで
   特定し、probe の述語が独立に効く入力が実在するかを示せ。**存在しないなら、それが最大の所見だ。
4. **記録の追加が防壁を弱めないか。** `_condition_gate_receipt_summary` へ field を足すと、
   `_condition_gate_family_valid` の `receipt_summary == _condition_gate_receipt_summary(value)` は
   何を検査しなくなるか。受領証から issuer capability や evidence が復元できるようになっていないか
   (現行 docstring の主張を検算せよ)。
5. **親 brief 自身の誤り。** brief が挙げた不変条件・成果物影響・(P1) の provisional 裁定・
   「pin 閉包は空」「到達可能性は実測済み」という**親自身の実測値とその一般化**を疑え。
   親が 1 例から族へ一般化していないか。

## 禁止

- gate 本体の変更を提案しない。新しい gate・検査・台帳・互換層・一般化を提案しない。
- 既存テストの期待値の変更・緩和・反転・skip・削除を提案しない。
- commit・git 操作・docs 編集・ファイル書き換えをしない。
- scope 外の real 所見は「裁定パッケージ候補」と明記して返す。実装したふりをしない。

## 出力形式

```
## 所見
（1 件ずつ。所見 ID / 対象 file:line / なぜ壊れるか / 具体的な入力例 / 重大度）

## 親 brief への反証
（brief の前提・実測値・一般化のうち、誤り・過大なもの）

## 裁定パッケージ候補
（scope 外だが real なもの）

## 総括
（3〜6 行）
```
