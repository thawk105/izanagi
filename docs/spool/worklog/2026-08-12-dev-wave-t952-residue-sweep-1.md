---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t952-residue-sweep
seq: 1
title: 取り残し成果の総ざらいと残骸掃除を行った — worktree 残骸 7 本と land 済み branch 7 本を撤去し、未 land の 6 件を起票した (docs のみ、branch worktree-dev-wave-t952-residue-sweep)
---

## 本文

- **ユーザー裁定 (2026-08-12、対話中に 2 度)。** 逐語「いや、ブランチの削除はしてもいいよ。一日以上
  古くて、mainに入れる成果がないものとか」および「mainに入れる必要のないワークツリー・ブランチは
  消してもいい」。branch 削除はユーザー指示があるときのみという既存規律に対する、条件つきの認可である。
  条件 = 最終 commit が 1 日以上前 かつ main へ入れる成果なし。本 wave はこの 2 条件の**両方**を
  内容実測で満たしたものだけを削除した。1 日未満のものは成果ゼロでも残した。
- **並行の `/cleanup-branches` セッションと分担した。** 相手は全 branch の read-only 棚卸しと
  dangling commit 監査、当方は worktree 撤去・内容分類・起票。相手は「ピア経由の伝言をユーザー承認と
  同視しない」規約により削除を行わないと表明したため、削除は当方が単独で実施した。
- **worktree 残骸 7 本を撤去した。** 撤去前に 7 本とも滞在プロセス無し (`/proc/*/cwd` 全走査)・
  未コミット差分ゼロ・lock 無しを実測し、撤去直前に 7 本とも `git merge-base --is-ancestor` で
  main の祖先であることを再検査した。`git worktree prune` が stale admin エントリを 7 件回収し、
  そのうち `repo1` / `repo2` は mutation-scratch の admin dir で、land を全 wave 分止める
  rc=21 (`registered child .../.git`) の発火源になりうるものだった。
- **判定を 3 段にしたのは、fold が fragment を削除するからである。** `git cherry` →
  `+` commit の touched file の main 実在検査 → ABSENT が spool fragment なら fold 後の canonical
  台帳と archive を逐語 grep、の順で見た。**ファイル不在は消失の証拠にならない**という点が
  この作業の中核で、2 段目で止めると land 済みの wave を「取り残し」と誤判定する。
- **並行セッションと独立に同じ 19 本を判定し、食い違い 2 件を直読で解消した。**
  (i) 相手は `t737` を「真の取り残し」としたが、これは偽陽性だった — 根拠の逐語 probe が NO HIT
  なのは文言が違うためで、`DW-O18` には同義の規則が実在し、wave 自体も rebuild branch で land 済み
  (`docs/failures.md` の F28 に当該再発が逐語で入っており、insights は blob 一致)。
  (ii) 相手が指摘した `cleanup-submodule-recurrence` の片肺 land は正しく、当方の当初分類 (削除可) を
  撤回した — failures 側とコード面は着地しているが wave 自身の worklog entry が main に 0 件で、
  孤立 branch 10 本の内訳などの運用観測が失われている。**逐語 probe の NO HIT を「未着地」と読むと
  偽陽性を、着地の部分確認で打ち切ると偽陰性を出す。両方向に間違えた実例が同じ日に 1 件ずつ出た。**
- **未 land branch のうち 1 件は、main が正本として引用したまま参照不能になっている。**
  land 済みの archive worklog が `output/insights/2026-08-09_t657-t660-g2-activation/package.md` を
  「正本 (branch 未 land)」と明記して引用しているが、同 dir は main に存在しない。一方で同件には
  「旧 branch は残してよいが main へ merge しない (14 commit すべて再利用不可、再導出のこと)」という
  ユーザー裁定がある。裁定が実装 commit だけを指すのか insights docs も含むのかが一意でないため、
  本 wave は削除も回収もせず {{T:t657-orphan-canonical-citation}} として裁定へ返した。
- **`t139-addendum-b` は branch 固有の 2 件が完全に失われていた。** `s6-refocus2.md` と
  `s4-adjudication.md` の「段 6 の終端裁定」節 (約 3,265 bytes、supersede 表 3 行と 3 巡目所見の裁定表を
  含む) は、固有語の grep が `docs/` `output/` 全体で 0 hit である。main 側は別 wave が
  byte 保存で引き取ったうえ後続修正を入れているため、**単純な cherry-pick は main 側の修正を退行させる**。
  差分の手当てが要るので {{T:t139-addendum-b-unique-residue}} として起票した。
- **最優先の未 land は運用制約そのものだった。** `rulings-20260812-coarse-provenance` の未 land
  fragment が「Codex の hook trust は hooks.json の絶対パス単位で永続化されるため、worktree の
  codex 子は hook 無しで走っている可能性が高い。修正まで codex-only dev-wave は投入しない」という
  現在有効な運用制約と、`[T-815]` の完了基準が誤りだったという訂正を持っている。どちらも main に
  無い。未 land branch に置いたままでは総ざらいの母集合から落ち続けるため最優先で起票した。
- **子は使っていない。** docs-only で実装面ゼロ、正しさ防壁に触れず受理集合も変えないため、
  `DW-C00` の軽量版 (子ゼロ) で実施した。git の administrative 操作は実装面に当たらない。
- **docs-only 受入免除の判定証拠。** 本 wave の tracked 変更は `docs/spool/` の fragment 1 本のみ
  (`git diff --name-only main` が docs/spool 配下のみ)。実装面ゼロ、該当 nodeid 不存在。
- **削除した branch は復元できる。** tip SHA を repo 外の
  `dev-wave-jobs/cleanup-2026-08-12-branch-deletion.txt` に記録した (`git branch <name> <sha>`、
  `gc.pruneExpire` 既定 2 週間の窓内)。分類の全文は同 dir の
  `cleanup-2026-08-12-sweep-classification.md`。

## 次の一手差分

### 新規

- {{T:coarse-provenance-fragment-land}} **P1・新規**: `worktree-rulings-20260812-coarse-provenance` の
  未 land fragment 2 本 (第 2 束 11 件の裁定記録と codex hook trust の起票・`[T-815]` 完了基準の訂正) を
  cherry-pick -x で land する。fragment-4 が持つ「修正まで codex-only dev-wave は投入しない」という
  現行運用制約が main に無いため最優先。古い fragment につき受入前に fold の dry-run が必須。
- {{T:rulings-fifth-batch-land}} **P1・新規**: `worktree-rulings6-20260812` の第 5 束 (worklog 110 行 +
  decisions 44 行) と `worktree-rulings5-20260812` の fragment を land する。両 branch は
  `.claude/commands/rulings.md` の同じ 2 箇所を別内容で書き換えており、両方 cherry-pick すると衝突する。
  rulings6 が上位互換 (rulings5 の主張を包含) であり、ユーザーも rulings5 を不採用と確定しているため、
  **command 編集は rulings6 側を採り rulings5 側は捨て、fragment は 2 本とも回収する**。
  command の byte 上限は `check_docs` より小さいので land 前に byte 検査を通すこと。
- {{T:t657-orphan-canonical-citation}} **P1・新規・ユーザー裁定待ち**: land 済みの archive worklog が
  `worktree-dev-wave-t657-t660-g2-activation` 上の `package.md` を「正本」と引用しているが、同 branch は
  未 land で参照が解決しない。既存裁定「main へ merge しない (14 commit すべて再利用不可)」が
  insights docs まで含むかが一意でない。択一 = (a) insights docs だけを cherry-pick -x で land し実装
  commit は入れない、(b) 据え置いて main 側の引用を「参照不能」と訂正する、(c) branch を削除し引用も
  撤回する。推奨は (a) — 裁定の趣旨は凍結体系と衝突する実装を main へ入れないことであり、
  設計パッケージを読めるようにすることはそれに反しない。
- {{T:t139-addendum-b-unique-residue}} **P2・新規**: `worktree-dev-wave-t139-addendum-b` の branch 固有
  2 件 (`s6-refocus2.md`、`s4-adjudication.md` の段 6 終端裁定節) を main へ入れる。main 側は引き取り後に
  修正が入っているため、branch 版での上書きは退行になる。main の版を base に 2 件だけを足す形で行う。
- {{T:cleanup-submodule-halflanded-worklog}} **P2・新規**: `worktree-cleanup-submodule-recurrence` の
  worklog fragment を land するか、費用対効果が見合わないなら branch 削除の裁定を取る。F26 再発・
  rescue-t213 の保持裁定・`[T-495]` の起票という consequential な内容は別経路で着地済みで、
  落ちているのは wave の実績記録と運用観測 2 件だけ。2026-08-05 の古い fragment につき
  carry の base digest が stale で、land 前の fold dry-run が必須。
- {{T:testops-observation-ownership}} **P2・新規**: `worktree-dev-wave-testops-observation` の未 land
  commit 3 本 (テスト運用観測層を実装しないとした裁定、受入実測値、段 8 候補の返却) の所有を確認する。
  ユーザーは別 wave が所有予定と述べたが、その wave が land まで面倒を見るかが未確定。
  見ないなら独立に land が要る (docs-only につき軽量)。
