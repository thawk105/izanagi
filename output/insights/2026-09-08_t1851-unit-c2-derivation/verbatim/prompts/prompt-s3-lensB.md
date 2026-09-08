単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **攻撃対象 1 — 親の段 1 brief**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s1-brief.md`
- **攻撃対象 2 — 段 2 の plan**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s2-plan.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`
- 過去の失敗の型: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md`

# 段 3 レンズ B — 閉包・帰属・射程の正直さ

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
   (b) は親の brief 初版に無かった。**同種の見落としが他に無いかを、
   親とは違う手 (exact 集合比較・件数 assert・AST 走査・canonical bytes literal) で探すこと。**

## 親が実測した baseline (再測不要)

main 取り込み後の焦点走 14 file は **2,198 passed / 11 skipped / 0 failed** (201 秒)。
対象は `test_calibrator` / `test_s8b_floor_campaign` / `test_s8b_floor_stats` /
`test_s8b_terminal_evidence` / `test_s8b_holdout_freeze` / `test_s8b_oracle_driver` /
`test_s8b_oracle_manifest` / `test_s8b_oracle_report` / `test_floor_pair_driver` /
`test_official_perf_closure` / `test_t671_source_binding` /
`test_s8b_floor_attempt_launcher` / `test_s8b_attempt_registry` /
`test_attempt_registry_core_s8b_profile`。
**この 14 file に入っていない consumer test があれば名指しすること。**

## このレンズが見るもの — 閉包・帰属・射程

正しさ境界そのものは別レンズが見る。こちらは**取り残しと、主張と実体の食い違い**を見る。

1. **pin 閉包が本当に閉じているか。**
   rep observation の key 集合を 6 から 7 へ変えたとき赤くなる箇所を、
   plan と親 brief が挙げた以外に**自分で全部見つける**こと。
   識別子検索だけでは閉じないと契約 9 節が言っている。
   **file 全体の sha256 golden・件数 assert・AST 走査・exact frozenset・
   canonical bytes の literal** を別々の手で探すこと。
   - `orchestrator/tests/test_official_perf_closure.py` の
     `_REVIEWED_PERF_FILES` (`:44`) / `_production_perf_files()` (`:533`) / 集合等値 (`:905`)
   - `orchestrator/tests/test_t671_source_binding.py` の 63 path exact tuple と件数 (`:267-269`)
   - `orchestrator/tests/s8b_v2_freeze_fixture.py:155-163` の 6 key literal と、その 4 consumer
   - `missing_perf_events` を参照する 12 file それぞれ
2. **consumer 取り残し。** 6 key を前提に書かれた読み手のうち、
   plan が触っていないものを列挙すること。
3. **射程の正直さ。** 契約 9 節は
   「`launch_floor_attempt()` の production 呼び手は 0 件。実値域は C2 が供給する」と書く。
   plan が言う「供給」が、**実際に何を実測して何を主張することになるのか**を
   1 文で言い切らせること。**測っていないものを測ったと書く余地がないか**を検査する。
   親の provisional 裁定 (P1) は「配線は別単位に残す」である。
   これで契約 9 節を満たせるのか、満たせないのかを**どちらかに倒すこと**。
4. **変異の帰属。** plan の変異照準について、
   **その変異を殺すと主張する test が、本当にその変異でだけ赤くなるか**を検査すること。
   他の gate が同じ回に赤を出すなら、その変異はその test の正例になっていない。
   **通常経路で殺せないものを「殺せる」と書いていないか**を疑うこと。
5. **実装子の分割が排他か。** 同じ file を 2 本の子が持つ案になっていないか。
   直列にすべきものを並列にしていないか。
6. **成果物影響 (DW-G05)。** plan の各 must-fix について、
   放置したとき成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
   どう変わるかを 1 行で言えるか。言えないものは nit へ落とすこと。

## 親の brief への攻撃 (省略しないこと)

- brief 4 節の実測表の file:line を**自分で開いて照合**し、外れているものを名指しすること。
  親は一度この表を訂正している (runner の入口が 2 つあることを最初に見落とした)。
  **同種の見落としが他に無いかを疑うこと。**
- brief 5 節の「凍結 fixture の 6 key は hardcode digest へ伝播しない」という結論を
  **独立に検算**すること。伝播するなら具体的な file:line と digest constant 名を出すこと。
- brief 6 節の (P1)〜(P4) のうち、**閉包・射程の観点で誤っているもの**を名指しすること。

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

## pin 閉包の残り (file:line)
## consumer 取り残し
## 射程の正直さ — 契約 9 節を満たすか
## 変異の帰属が成立しない件
## 実装子分割の破れ
## 成果物影響を言えない must-fix
## 親 brief の誤り
## 過去の型の再発
## blocker と nit の仕分け
## 総括
