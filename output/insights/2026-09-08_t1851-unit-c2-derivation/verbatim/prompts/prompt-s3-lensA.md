単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **攻撃対象 1 — 親の段 1 brief**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s1-brief.md`
- **攻撃対象 2 — 段 2 の plan**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s2-plan.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`
- 過去の失敗の型: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md`

# 段 3 レンズ A — 正しさ境界

**plan を守らせない。壊しに行く。** plan と**親の brief 自身**の両方が攻撃対象である。
親の実測値と、その実測から親が引いた一般化も検査対象に含む。

作業 root は read-only で、書込み可能な tmp は無い。**pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。**走らせていないものを緑と書かないこと。**
**file を 1 つも作れない。成果物は最終メッセージの本文へ全文を書くこと。**
予算が尽きそうなら**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 親が段 2 の投入**後**に見つけた事実 (plan 子はこれを渡されていない)

plan 子へ渡した親の実測表には、次の 2 点が**入っていなかった**。
**plan がこの 2 点を独立に見つけているか、見落としたまま組み立てられているかを判定すること。**
見落としたまま組み立てられているなら、plan の分割・変異照準・閉包がどこまで無効になるかを言うこと。

1. **runner の rep observation 生成は 2 箇所あり、別々の公開関数に属する。**
   `orchestrator/calibrator/runner.py:990` (`capture_measure_point()`、def `:803`) と
   `runner.py:1203` (`measure_point()`、def `:1057`)。例外捕捉は `:965` `:978` `:1170` `:1184` の 4 箇所、
   集約 note は `:1029` と `:1247` の 2 箇所。
   **床値 campaign が実際に呼ぶのは `measure_point` の方である**
   (`orchestrator/campaign/s8b_floor_campaign.py:93` の import と `:7865` `:7871` の呼び出し)。
   `capture_measure_point` を使うのは launcher (`s8b_floor_attempt_launcher.py:158-160`) だが、
   その launcher に production 呼び手は 0 件である。
2. **6 key の exact 集合 gate は 2 本ある。**
   (a) campaign の `complete` 述語 `s8b_floor_campaign.py:1947-1950`、
   (b) **有効性判定側の `orchestrator/campaign/s8b_floor_stats.py:63`
   (`_REP_OBSERVATION_KEYS` frozenset) と `:486` の `set(observation) != _REP_OBSERVATION_KEYS`。**
   (b) は親の brief 初版に無かった。

## このレンズが見るもの — 正しさ境界だけ

**受理集合が広がる方向の変化を全部見つける。** 実効性・保守性・美しさは別レンズが見るので書かない。

1. **`complete` 述語 (`orchestrator/campaign/s8b_floor_campaign.py:1947-1950`) の exact key 等値を
   7 key へ広げる変更で、いま拒否されている observation が受理されるようにならないか。**
   なるなら、どの入力でそうなるかを具体値で示すこと。
2. **`exec_failures` と `rep_integrity_failures` の分離 (契約 3 節) が、plan の実装で本当に
   保たれるか。** 片方がもう片方から導けてしまう経路があれば示すこと。
3. **自然文 note を算出から外したあと、外部由来の文字列が別経路で信頼側へ入らないか**
   (絶対規律 6)。例外 message を新 key に載せる案があるなら、その message が
   どこまで運ばれ、何を根拠に信頼されるかを追うこと。
4. **証跡 carrier 欠落の padding 経路 (`s8b_floor_campaign.py:1898-1913`) が、
   7 key 化で「成功既定」へ倒れないか。** いま unknown/incomplete として扱われているものが
   complete 側へ移る変更があれば、それは規律 2 違反である。
5. **runner の 2 入口 (`measure_point` def `:1057` / `capture_measure_point` def `:803`) の
   うち片方だけを直す案が出ているなら、経路によって等値束縛が成立したりしなかったりする
   状態が生まれないかを検査すること。**
6. **v1 (非 v2) 側の event key 集合・受理集合が 1 bit も動かないこと** (契約 1 節) を、
   plan の変更面から独立に確かめること。
7. **恒真になる検査**を探すこと。plan が足す assert のうち、
   **変更前のコードでも必ず通るもの**があれば名指しすること
   (謳うだけで発火しない保証は絶対規律 6 の監査発火条件そのものである)。

## 親の brief への攻撃 (省略しないこと)

- brief 4 節の実測表の file:line を**自分で開いて照合**し、外れているものを名指しすること。
- brief 5 節の pin 閉包に**漏れ**がないか。とくに「伝播しない」と親が書いた結論
  (凍結 fixture の 6 key が hardcode digest へ伝播しない) を独立に検算すること。
- brief 6 節の (P1)〜(P4) の provisional 裁定のうち、**正しさ境界の観点で誤っているもの**を
  名指しすること。

## 過去の型の再発検査

`docs/failures.md` の型タグを攻撃面に含めること。とくに
**説明と実装の食い違い・consumer 取り残し・恒真な保証**を疑うこと。
該当する F 番号があれば引くこと。

## 禁止

- plan を擁護しない。「概ね妥当」で終わらない。
- file を作らない。`git` の状態を変えない。
- 走らせていないテストを緑と書かない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う。本文へ全文を書く)

## 受理集合が広がる箇所
## exec_failures と rep_integrity_failures の分離の破れ
## 未信頼文字列の侵入経路
## padding 経路の倒れ方
## runner 2 入口の非対称
## 恒真になる検査
## 親 brief の誤り
## 過去の型の再発
## blocker と nit の仕分け
## 総括
