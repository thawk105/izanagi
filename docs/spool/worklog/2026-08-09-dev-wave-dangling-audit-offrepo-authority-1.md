---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-dangling-audit-offrepo-authority
seq: 1
title: 到達不能監査に repo 外の同一実体による抑止を足した — 裁定 (b)+(c) の実装、抑止は 13 対でなく 2 対 (コード + docs、受入 7495 passed / 20 skipped、変異 13/13 KILLED・SURVIVED 0、branch worktree-dev-wave-dangling-audit-offrepo-authority)
---

## 本文

- **2026-08-08 のユーザー裁定 (b)+(c) を実装した。**一次控えは repo 外 rulings-inbox の
  `2026-08-07-dangling-audit-alarm-fatigue.md`。(b) repo 外正本の探索を実装、(c) 裁定済み残骸は
  git gc の自然回収に任せる (実装なし)、**(a) ack 台帳と (d) 即時 prune は不採用のため作っていない**。
  裁定は「新規 T として起票」を求めていたが、本エントリで実装まで閉じたため未了項目は残さない。
- **段 4 で設計を作り直した。**裁定文の option 記述は「同名・同内容があれば落とす」だったが、
  この述語は [T-409] の wave 成果物 11 対まで抑止してしまい、**裁定自身が (c) で gc に任せると
  分類した群を (b) で消す**ことになる。実測すると 2 群を分ける観測可能な差は
  「main に land 済みの文書がその repo 外 path を参照しているか」であり ([T-574] は landed 3 本から
  参照あり、[T-409] は 0 件)、これを第 5 の連言に足した。**抑止は 13 対から 2 対へ縮み、
  抑止される commit 数は 8 → 6 で変わらない。**設計判断は {{D:offrepo-copy-needs-landed-reference}}。
- **敵対検証を 5 本回し、5 本すべて NO-GO だった** (段 3 の 2 レンズ = blocker 5、
  段 6 の 2 レビュー = blocker 6、焦点再レビュー = blocker 1 + must-fix 1)。
  **NO-GO の内容はすべて実装前・land 前に閉じた。**
- **親の誤りを 2 件、敵対検証が検出した。**(i) 段 1 brief が現状を「24 (commit,path) 対」と書いたが、
  24 は失われた **basename の異なり数**で、対の数は 28 だった (段 3 レンズ A が算術の不整合として
  検出)。probe 出力のラベルをそのまま数量名として転記したことによる。
  (ii) byte 予算を捻出するために cleanup-branches command から F26 の正本ポインタを削り、
  他文書にしか無い義務への到達手段を失わせた ({{F:budget-trim-removed-safety-pointer}})。
  焦点再レビューが検出し、削除を撤回して復元した。
- **段 6 レビューが「実装が実運用で 1 度も発火しない」ことを検出した。**探索根を環境変数任せに
  すると `/cleanup-branches` は環境変数を export しないため恒真な機構になる。
  `.claude/commands/cleanup-branches.md` の監査呼び出しへ `--offrepo-root` を渡す形を親が書き、
  所在と述語を `docs/pegasus-runbook.md` §7.2 に置いた。command は 3959 bytes (上限 4000)。
  **`orchestrator/tests/test_check_docs.py` の `test_cleanup_command_invalid_backtick_info_is_rejected`
  が 17 bytes 追記して違反ちょうど 1 件を要求するため、実質上限は 3983 bytes である** (実測で判明)。
- **親の実走が fix の回帰を 1 件検出した。**fix 1 巡目が command の whole-file SHA-256 pin 定数だけを
  更新し、同 test file 内にある command の**全文コピー** `_SYNTHETIC_CLEANUP_COMMAND` を放置したため、
  合成 repo を使う検査が **188 failed** になった。子は計算ノードへ dispatch できず未実走のままだった
  ので、親が走らせなければ緑と誤認して進んでいた。fix は計 4 巡。
- **path 境界判定の向きを反転した。**初版は「path を延長しうる byte」を英数字と `.-_/` で列挙して
  いたため、`<path>+backup` や `<path>@backup`、左側の `/x<path>` が短い候補の landed 参照として
  通っていた (焦点再レビューが検出)。境界 byte を明示列挙し、**それ以外 (非 ASCII を含む) は延長
  扱い**にして、未知の byte が「抑止しない」側へ倒れるようにした
  ({{D:path-boundary-set-is-fail-safe-inverted}})。
- **変異は 4 走した。**anchor は 1〜2 走目が `fd97fe93`、3〜4 走目が `5195f60d`。
  1 走目 = 8 KILLED / 2 MISMATCH、2 走目 = 10 KILLED / 0 MISMATCH。焦点再レビューが
  「この 10 変異では検出されない」と指摘した穴へ M11〜M13 を足した 3 走目 = 11 KILLED / 2 MISMATCH、
  **本走 (4 走目) = 13 KILLED / 0 MISMATCH / 0 SURVIVED / 0 TIMEOUT、baseline PASSED。**
  MISMATCH 4 件はすべて**実測 node が事前登録の上位集合**で、実装の欠陥ではなく親の登録漏れである
  (harness は完全一致で判定する)。erratum として消さずに台帳へ残した。
  **M07 (抑止節の出力を消す) と M09 (探索未実施の表示を消す) は findings も rc も変えないため、
  `DW-M08` に従い受理集合の kill でなく diagnostic sensitivity pin として別枠に記録した。**
- **受入全走は緑。**request `896501`、1290 秒、**7495 passed / 20 skipped / rc=0**。
  測った checkout は `4d5b5119` (本 fragment の commit はその上に載る docs のみの差分)。
  受入 lease は競合が激しく、**取得までに 40 分 + 29 分待った** (前半 40 分は取得できず、
  保持者が入れ替わった)。記録後検査は `check_docs.py` rc=0、`spool_fold.py --dry-run` rc=0。
- **残存 risk を 2 件、意図的に受容した。**(i) hardlink と探索根 symlink の交換で repo 内の写しを
  repo 外実体に見せかける経路。単独運用者環境では意図的操作を要するため防壁を作らない。
  (ii) whole-file SHA-256 pin は bytes しか守らないため、安全文を削って 3 箇所を同時に再 pin すれば
  検査は通る。これは pin の設計論であり本 wave の scope 外として起票した。
- **段 8 の改善候補は 2 件とも既存項目へ寄せ、本文編集はしていない。**(i) 背景 job + worktree 隔離
  では `DW-O01` の 1 行起動形だけでなく**待ち手**も worktree guard に機械拒否される
  (`until [ -e ... ]; do sleep; done` を Bash へ直接渡す形)。`docs/dev-wave/**` の byte 予算に
  阻まれるため [T-664] の材料として記録する。(ii) 変異の期待 node 登録漏れは、本 wave 中に main へ
  land した `DW-M07` の「fix 後の最終 commit で anchor と**期待 node**を再検証してから本走する」が
  そのまま該当する。新しい規則は要らない。
- 一次資料 = `output/insights/2026-08-08_dangling-audit-offrepo-authority/` (段 1 brief、段 2 プラン、
  段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、段 6 の 2 レビュー、焦点再レビュー、fix 4 巡、
  変異 spec 4 版と台帳 4 走)。

## 次の一手差分

### 新規

- {{T:whole-file-pin-semantic-gap}} **P3・新規 (本エントリ、段 6 焦点再レビュー)**:
  command の whole-file SHA-256 pin は bytes の同一性しか守らないため、安全義務の文を削って
  checker 定数・test 定数・test の合成コピーを同時に再 pin すれば検査は通る。本 wave で実際に
  1 度発生した ({{F:budget-trim-removed-safety-pointer}})。意味検査 (正本ポインタ・path・ID の
  到達性) を機械化するか、pin の役割を「改変検知」に限ると明記するかを裁定へ返す。
