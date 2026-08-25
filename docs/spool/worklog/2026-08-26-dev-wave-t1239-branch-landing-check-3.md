---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1239-branch-landing-check
seq: 3
title: [T-1239] 取り残し branch の着地判定を機械検査にし、worktree 残骸 11 本を退避した (コード + テスト、branch worktree-dev-wave-t1239-branch-landing-check)
---

## 本文

- **wave 実行中に対象 branch 9 本のうち 8 本が別経路で削除された。** 依頼時 (2026-08-25 20:16) に
  存在した 9 本のうち、残ったのは `worktree-cleanup-branches-20260825` だけである。
  削除の結果は親の正解データと一致した — 親が唯一「真に未着地」と判定したのがその 1 本で、
  他 8 本は着地済みだった。**tip commit 7 件は object として生存しているが main から到達不能**で、
  `git gc` で失われうる。依頼の「削除候補の一覧と根拠を出すところまで」という射程は、
  8 本については事後確認に変わった。
- **この出来事が設計要求を 1 つ確定させた。** 判定器の初版は local branch 名しか受け取らず、
  branch 消失後は何も判定できなかった。取り残しの実体は削除後には到達不能 commit であり、
  判定が最も要るのは削除の直前と直後である。commit-ish を受ける経路を段 6 の fix 第 2 巡で足した。
  既存の `tools/audit_dangling_commits.py` は「既存ファイルへの変更・削除・同名別内容・gitlink 更新」を
  検出対象外と明記しており、この穴を埋めない。
- **段 2 のプランは親の暫定案 (P2) を根拠つきで否定した。** 親は「file ごとに blob 一致・
  fold receipt・逐語一致のいずれかが成立すれば landed」という無条件の選言を提案したが、
  プランは spool を receipt 専用にし、変更の種類ごとに証明規則を分ける形へ改めた。親は採用した。
- **段 3 の敵対相談 2 本は独立に同じ blocker を出した** — fold receipt に無いことを未着地の
  証拠にしてはならない。親は独立に実測してこれを裏取りしていた
  (`worktree-roadmap-workload-hint` の decisions fragment は receipt に無いが D568 として着地済み。
  fold 前に別 wave 名へ `git mv` され whole-file sha が変わったため。F82 の 4 度目に経緯がある)。
  **そのまま fold していれば D568 を二重採番していた。**
- **段 6 の最大の所見は親の実データ実走が出した。** 合成テスト 26 件が全緑の実装を 9 本へ当てると
  8 本が `indeterminate` になり、`not-landed` は 0 件だった。原因は
  merge commit の証明義務が裁定 A1 の「全親に対する差の積集合」でなく**和集合**だったことで、
  `worktree-t1458-side-ccbench-provenance-fix` では真の義務 0 file の merge に 17 file が課されていた。
  **敵対レビュー 2 本はどちらもこれを指摘しなかった。**
- 一方、**敵対レビューは親が見つけられなかった blocker を 6 件出した。** 不正な fold receipt bullet で
  `landed` になる (しかも実装子が書いたテスト自身が不正な receipt を作って `landed` を期待していた)、
  履歴を書き換える経路で closure を空に偽装できる、候補上限に達しただけで取得済み候補を照合せずに
  諦める、receipt 済み fragment の削除を証明できない、既定 60 秒での実 repo 完走が未証明
  (branch あたり約 1,500 Git child)、ref の終了時競合。
- **事前登録した変異 10 件のうち 3 件が無効だった** (F28 の再発)。新設 tool の wave では
  段 4 の裁定時にコードが存在せず、`DW-M01` の「コードで確認する」を規則名の水準でしか行えない。
  段 6 のレビューへレンズ項目として渡して実装直後に落とし、M2 を取り下げ M2' を新設、M4→M4'、M8→M8' へ
  再照準した。fix 第 2・3 巡で M11・M12 を足し、最終の登録は 12 件である。
- 修正は 3 巡回した (上限)。第 1 巡で F1〜F17、第 2 巡で赤 1 件と commit-ish 対応、
  第 3 巡で fragment の identity 単位 (frontmatter の `title:`) を probe へ入れた。
  第 3 巡は親の実測が発火させた — 着地済みの worklog fragment と未着地の fragment が
  どちらも「5 単位中 1 単位一致」で同じ無関係な file を指し、区別できなかった。
- **worktree 残骸 11 本を退避した。** `.codex/worktrees/` の t1563 系で、いずれも detached HEAD、
  lock 理由が空、age 5.5〜9.3 時間。1 本ずつ直前に占有を測り直し (全件 `unoccupied`、
  走査母数 2,299〜2,317)、抱えていた未コミット差分 25 件すべての blob が main の履歴に
  存在することを確認してから、削除でなく `dev-wave-jobs/orphaned-worktree-residue/t1239-20260826/` へ
  退避して `git worktree prune` した。worktree は 49 本から 38 本になった。
  この撤去が共有木の untracked 集合を変えることを**事前でなく事後に確認した** (F537 の再発として記録)。
- 孤立していた fragment 2 通 (`cleanup-branches-20260825` の failures と worklog) を、
  **ファイル名も `wave:` も変えずそのまま**本 wave の branch へ運んだ。改名は R100 の rename として
  fold の owned-path 検査に当たり land を止める既知の型 (F82 の 4 度目) であり、
  他 wave の slug を参照しない限り re-home は不要である。sha256 が原本と一致することを確認した。
  なお同 fragment の F526 supersede 追記は canonical に別内容の supersede が既にあり、
  fold 後は同じ日付の supersede が 2 行並ぶ。歴史記録としては両方とも実測であり、取り消さない。
- 子の工数: codex 8 本 (plan 1・consult 2・author 1・review 2・fix 3)。全て `launcher_rc=0`。
- 変異 matrix は本 wave では未実施。段 6 の fix 3 巡で実装が大きく変わったため、
  最終 commit に対する本走は段 7 の記録 commit 後に行う。

## 次の一手差分

### 完了

- [T-1239] 取り残し branch の着地判定を `tools/check_branch_landed.py` として機械検査にした。
  判定材料 3 点のうち patch の指紋と台帳の task ID 検索は非決定の観測へ降ろし、
  決定的証拠を exact tree state と fold receipt に限った。判定対象は commit closure。
  実データ 8 件で 4 件が `landed`、4 件が `indeterminate`。
  remaining: none
  base: 44fda4ea0a31d3b8f065a0733d5fc52636c41b43a5c5739adbfd9340fecb95e5

### 新規

- {{T:cleanup-branches-landed-wiring}} **P2・ユーザー裁定待ち**: 内容として着地済みだが
  main の祖先でない branch を `/cleanup-branches` の削除対象へ入れるか。
  現行 §2 は `ahead=0 のみ削除`で、`git branch -d` も非祖先 branch を拒否するため、
  判定器が `landed` と言っても運用は何も変わらない。削除するなら `-D` でなく
  expected-tip の CAS (`git update-ref -d refs/heads/<name> <tip>`) と直前再検査を組み合わせる。
  **削除権限の拡大にあたるため本 wave では実装しない。**
  入口は 3,949 bytes で上限まで残り 34 bytes しかなく、記述は reference 側へ要る。
- {{T:spool-fragment-body-comparator}} **P2・新規**: fold receipt に無い fragment が
  着地済みかを決定的に判定する本文比較器。re-home 追跡と placeholder 採番の canonical 化が要る。
  現行は非決定の `ledger_probe` で手掛かりを出すだけで、`not-landed` を返せない。
- {{T:dangling-commit-rescue-t1239}} **P1・ユーザー裁定待ち**: 2026-08-25 深夜の branch 削除で
  main から到達不能になった 7 commit (`39407cfd` / `b3611129` / `15b5c389` / `fe56f5f7` /
  `a6a9f2b7` / `028a5e2d` / `500f47a6`) の救出可否。本 wave の判定器では
  4 件が `landed`、3 件が `indeterminate` (いずれも spool fragment 由来)。
  `git gc --prune` で失われうる。
- {{T:originless-baseline-liveness}} **P3・新規**: 再生成される不透明 baseline
  (`test_reflux_originless_compatibility.py` の 1 行) の着地を判定する限定 comparator の要否。
  現行は `indeterminate` に残す。一般的な「生成物を除外する」規則は作らない。
- {{T:shared-untracked-change-preflight}} **P2・新規**: 共有 main checkout の untracked 集合を
  変える操作の直前に `pgrep -af mutation_worktree.py` を要求する事前検査。
  現在は台帳と memory だけが防壁で、機械検査を持たない (F537 の再発で実測)。
