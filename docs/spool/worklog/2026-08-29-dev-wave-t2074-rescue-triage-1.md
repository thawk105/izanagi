---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2074-rescue-triage
seq: 1
title: 止まった 5 wave の残骸 7 file を 1 件ずつ裁き、1 件を回収して 4 本を撤去した (code + docs、branch worktree-dev-wave-t2074-rescue-triage、変異 1/1 KILLED)
---

## 本文

止まった 5 つの wave worktree に残っていた未着地差分 7 file を、ユーザーの判定基準
(破棄が既定、要否は「これが無いとどの wave が実際に壊れたか」で決める、実例を挙げられなければ破棄)
で 1 件ずつ裁いた。**着地 1 件、破棄 5 件、着地済み 1 件。**

**依頼の前提を 3 つ覆した。** (1) 7 file はすべて main に実在し、「純粋な未着地 5 file」は
成り立たない。未着地の実体は worktree の未 commit 差分である。(2) 撤去候補 4 branch は
未着地 commit ゼロで、tip はいずれも main の祖先だった。(3) `fix-dev-wave-t2027-timeout` は
S8B の未着地 commit 2 本を持ち稼働 branch からも到達可能なので撤去対象外とした。

file ごとの処遇と理由は次のとおり。詳細と一次資料は
`output/insights/2026-08-29_t2074-rescue-triage/README.md`。

- **着地** `orchestrator/tests/test_growth_test_holds_contract.py` (t2027-timeout-fix、+4/-1) —
  別 session root の受入全走 2 走が、18382 件の収集に対しこの 1 node だけの赤だった。
  一行: これが無いと受入全走が偽の timeout 赤を出し続け、その走が唯一の根拠として与えるはずの
  tested_tip の緑 (land の前提そのもの) が捨てられる。
- **破棄** `orchestrator/tests/flaky_test_holds.py` (t2072-hold-author、+33) —
  root fix `42c62e4dd` の後、最終 tip `5254ac6ed` で baseline rc=0 と変異 m03 の両 node KILLED を
  確認したうえで hold は外され、対象 node は受入母集団へ戻っている。迂回策として役目が終わった。
- **破棄** `orchestrator/tests/test_flaky_test_holds_contract.py` (t2072-hold-author、+45) —
  上の hold row・digest・逐語 field の鏡であり、row を捨てれば独立した検出力がない。
- **破棄** `tools/check_wave_startup.py` (t2032-midflight-author、+26/-5) —
  挙動を 1 bit も変えない help と docstring の言い換えで、しかも文面が壊れている。
  「「midflight は段 5 専用で、開始 gate の代用になる」という保証はしない」は「段 5 専用」を
  肯定せず、{{D:midflight-disclosure-remains-open}} が指す D1179 の決定より意味が後退する。
- **破棄** `orchestrator/tests/test_check_wave_startup.py` (t2032-midflight-author、+73) —
  docstring・help・NOTE に列挙文字列が在ることだけを固定する 73 行。midflight の 6 検査と
  除外集合は既存 test が既に固定しており、新しい挙動 oracle を足していない。
- **着地済み** `orchestrator/tests/test_codex_worker_launch.py` (t2073-rootfix-author) —
  worktree の blob `95c2f0080` が main の blob と同一。判定対象ですらなかった。
- **破棄** `orchestrator/tests/test_s8c_preregistration_invariant.py` (t1434-acceptance-red-fix、+365) —
  main は `ce99cc7d4` で exact 5 node を growth hold 済みで、D1298 は現 regime の単一 loadgroup
  短縮を退ける。加えて高速路 `_candidate_tree_is_head` は dirty candidate を誤って clean と
  判定すると HEAD tree を再利用し、**不正な未 commit 変更を候補 commit へ入れないまま
  不変条件検査を緑にする**。偽緑は絶対規律 2 に反するので、D1298 が無くても着地に値しない。

**着地させる 1 件は再実装していない。** 同内容が既に commit `aaffa71a6` として存在し、
`worktree-dev-wave-t2027-t2043-external-input` から到達可能で main には未着地だったので、
cherry-pick で逐語回収した。D720 の 2 条件を両方確かめた — 未着地は `git cherry` と
`merge-base --is-ancestor` で、現況妥当性は caller 数 12・受入 log 2 本・assert の現物読みで
検証した。合成の余地はゼロで、cherry-pick 後の blob は元 commit の blob と byte 同一、
main の blob は元 commit の親 blob と同一だった。したがって段 5 の Codex 実装子は起動していない。
実装面の author は `aaffa71a6` の trailer が記録する codex `role=author` であり、
親は実装面を 1 byte も書いていない。

**erratum:** 回収した commit message の「its accept and reject sets are unchanged」は厳密には
正しくない。変わらないのは 4 つの assert が固定する機能的な正しさ集合であり、実時間を含む生の
実行受入集合は 10 秒から 120 秒へ広がる。message は原著者の記録なので書き換えず逐語で回収し、
訂正を insight へ置いた (D720 の (a) 群)。絶対規律 2 には触れない — assert は 1 つも飛ばず、
120 秒を超える hang は引き続き赤である。

段 3 相当の独立レビュー 1 本 (read-only codex、gpt-5.6-sol、xhigh) を回した。7 件を親の処遇表を
見る前に独立導出して **7/7 一致**。所見 7 件はすべて real と裁定して採用した。処遇は動かず、
変わったのは (a) 受入集合の言い方、(b) 項目 2・3 の破棄根拠を「root fix が着地した」から
「hold 撤去後に受入母集団で緑を出し続けている」へ差し替え、(c) 項目 7 に偽緑という独立の破棄理由を
追加、(d) 実装を再実装から既存 commit の回収へ変更、(e) 撤去前検査の追加、
(f) D1179 の未履行を次の一手へ送ること、の 6 点である。

段 6 の敵対レビュー子は起動していない。実装面が 4 行で、その 4 行への敵対レビューは段 3 相当の
consult が既に実施済み (固定される 4 性質の列挙、規律 2 への抵触判定、repo 内の代替機構 3 種の
検討まで到達) であり、合成が恒等なので合成起因の新しい攻撃面が無く、fix すべき所見が
1 件も残らなかったためである。変異 matrix と受入全走は縮約していない。

**撤去は損失ゼロを 3 通りで確かめてから行った。** (1) 4 branch の tip がすべて main の祖先で
あることが snapshot に依存しない完全証明である。(2) 5 worktree に untracked file はゼロで、
ignored は `__pycache__` と `output/pegasus-dispatch/` だけ。stash 2 本はどちらも対象外 branch の
もの。(3) 救出写し 7 件が worktree の現物と sha256 で一致。
`check_branch_rescue.py` は `deletion_loss_closure` を complete かつ 0 件と出したが、
`root_snapshot` は `complete=false` のままだった。原因は `root-snapshot-moved` の 1 件だけで、
走査中 61 秒の間に稼働中の別 wave 3 本が ref を進めたためである。道具単独では損失ゼロを主張せず、
根拠は (1) に置いた。

変異 harness 2 本の観測対象は `/proc/<pid>/cwd` で確認し、いずれも自分の worktree であって
主 checkout ではないことを撤去前に確かめた。

## 次の一手差分

### 新規

- {{T:midflight-guarantee-disclosure}} **P3・新規**: D1179 が課した `--help` と `NOTE:` への
  明記義務のうち未履行の 2 点 — 肯定形の保証範囲 (段 5 直前の再測と提示だけ) と、
  古い anchor のまま実装子を投入しないことは保証しないという限界 — を実装する。
  破棄した救出差分は文面が壊れていたので使わない。詳細は
  {{D:midflight-disclosure-remains-open}}。
