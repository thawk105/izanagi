単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (read-only)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **審査対象の差分**: `git diff 21dfbe0f3..HEAD` (base `21dfbe0f3` は local main を取り込んだ merge commit)
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 段 3 レンズ B の pin 列挙: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s3-lensB.md`
- 段 2 plan の pin 列挙: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s2-plan.md`
- 実装子の報告 3 本と fix 子の報告 (同じ job dir): `out-s5-a1.md`, `out-s5-a2.md`, `out-s5-b.md`, `out-fix1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 6 レビュー B — pin・consumer・回帰のレンズ

作業 root は read-only である。**書込み可能な tmp は無い。pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。テストの実走は親が行う。
**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## 攻撃してほしい点

1. **行番号 pin。** `orchestrator/tests/test_ccbench_spawn_sites.py:895-910,2642-2720` が
   `s8b_floor_campaign.py` の**行番号 4707 と 8636** を pin する。
   差分後もその行に同じ実体があるかを**現物で確かめよ**。
   ずれていれば **real の受入赤**である。
2. **perf inventory。** `test_official_perf_closure.py` の `_REVIEWED_PERF_FILES` と AST 集合等値、
   role 別 guard が差分で落ちないか。新しい perf 述語の直接 call が入っていないか。
3. **凍結 bytes と `FORMULA_ID`。** 23 件の凍結成果物と `FORMULA_ID` に差分が無いことを確認せよ。
4. **既存期待値の変更。** 親が許した 4 箇所
   (`test_s8b_terminal_evidence.py` の fixture、`test_s8b_attempt_registry.py` の fixture と
   transplant 負例、`test_s8b_floor_attempt_launcher.py` の planned helper) **以外**で
   既存 test の期待値が変わっていないか、差分を 1 行ずつ確認せよ。
   反転・緩和・skip・xfail・deselect・削除が 1 つでもあれば **real の重大所見**である。
5. **所有外 consumer への波及。** 差分が触れた symbol の呼び手を repo 全体で列挙し、
   差分に入っていない consumer / fixture / AST 走査 test が壊れないか判定せよ。
   とくに `s8b_holdout_admission.py`、`s8b_holdout_freeze.py`、`s8b_ratified_freeze.py`、
   `s8b_floor_stats.py`、`attempt_registry_core.py` の consumer を見よ。
6. **揮発 payload。** 新設 test の期待値に working tree hash、時刻、pid、`artifact_sha256` の実値など
   揮発するものが焼き込まれていないか。
7. **受入所要台帳。** 差分が新設した test nodeid を**全列挙**せよ (親が add-only で登録するのに使う)。
   件数も書け。
8. **v4 consumer の到達不能。** production result が v5 になったことで、
   `s8b_holdout_freeze.py` / `s8b_ratified_freeze.py` の v4 exact key 要求に対して
   **silent acceptance ではなく fail-closed な到達不能**になっていることを確認せよ。
   silent に受理される経路があれば **real** である。

## 判定の書き方

各所見に **real / refuted** と、[実測] か [推測] のラベルを付けよ。
成果物影響を 1 行で書けない所見は **nit** と明記せよ。

## 禁止

- 実装しない。patch も diff も出さない。file を作らない。
- 「防御的堅牢化」を目的に新しい gate・検査・台帳を足す提案をしない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行)

## 所見 RB-1 ... RB-n
(各: real/refuted、[実測]/[推測]、根拠 file:line、成果物影響 1 行、推奨)

## 行番号 pin 4707 / 8636 の検算

## 既存期待値の変更の全列挙 (許可 4 箇所との照合)

## 所有外 consumer への波及

## 新設 test nodeid の全列挙と件数

## v4 consumer の到達不能の判定
```
