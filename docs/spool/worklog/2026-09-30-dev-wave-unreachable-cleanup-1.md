---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-unreachable-cleanup
seq: 1
title: 到達不能 commit 242 件を固定して仕分け、未記帳 157 件を記帳し D2200 項 2 の 248 件を遷移した — 救出 84・喪失受容 227・消失 2・捨て候補 92 は承認待ち (docs、branch worktree-dev-wave-unreachable-cleanup)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/unreachable-cleanup-2026-09-30/md_1.txt`。一次資料 `output/insights/2026-09-30/unreachable-cleanup/README.md` (承認カードを含む)。
- 依頼の前提の訂正: 「未記帳 231」は `/cleanup-branches` の off 監査の要確認件数で、台帳照合前の数だった。着手時の要確認 238 のうち 86 は既記帳 (D2200 項 2 の対象)、本当の未記帳は 152 (全件 T-2638 の作業木残差)。記帳後の照合で、着手後に別 session の掃除で到達不能になった T-2638 残差 4 件が出たので同じ手順で記帳した。
- 手順の逸脱 1 件 (親裁定): 依頼は「固定 → full 監査」の順だが、固定すると fsck が対象を到達可能と見て full 監査が 0 件になる。固定 ref だけを消した `--mirror --shared` の複製に full 監査をかけ、複製への off 監査が元 repo と完全一致 (2034 / 238 / 1197) することで代役を確かめた。後発 4 件は off 監査だけで分類した (救出が増える側)。
- 依頼外の実行 1 件 (親裁定): D2200 項 2 ([T-2829]) と [T-2840] の記帳は対象 object が本件と重なるため同時に実行した。裁定済みの遷移だけで、`accepted-loss` を AI の判断で付けた entry は 0。
- 段 6 レビュー (read-only 1 本): real 3 (うち 1 は nit)・refuted 4。初版の「scratch はすべて捨て候補」が研究図・provenance・patch を持つ commit を含んでいたので、区分 `rescue-scratch-output` を足して記帳済み 40 件を `pending` → `rescued` へ遷移し、承認カードを中身の種類別に書き直した (一次資料「段 6 レビュー」節)。
- 焦点再レビュー (read-only 1 本): real 1 (後発 4 行の `assessment_reason` が実施していない「full 監査」と書いていた → 「off 監査」へ訂正)・refuted 4。
- 完了照合: `python3 tools/check_branch_rescue.py --ledger-check` (22:40 JST) は未記帳 0、監査完走、rc=3 は捨て候補 `pending` の期限通知 90 件だけ。台帳を読むテスト 3 file (`test_branch_rescue_ledger.py`・`test_check_branch_rescue.py`・`test_check_docs.py`、`tools/run_tests.py` の login 走) は 716 passed・3 skipped。
- 実害 1 件: D2200 で救出と裁定された 2 object が、実行前に失われていた ({{F:ruled-rescue-not-executed}})。
- 「計算ノードは使わない」(md_1) は分類作業の範囲と読み、land の受入は標準経路どおり計算ノードへ投入した (md_1 手順 6 が land を求めるため)。
- セッション異常: (1) 利用上限で 20:1x〜21:4x JST に中断し、同 session で再開した。(2) 台帳生成が `check_branch_rescue.Git.run` の git 1 回 8 秒の固定上限で 2 回落ちた (Lustre 混雑、`count-objects -v` の手測 16.7 秒)。一回限りの tool に上限の引数を Codex fix で足して回避した。(3) 全 worktree の棚卸しが並走 wave の `remove-child` の途中を拾い `snapshot incomplete` で 2 回止まり、撤去終了を待って再実行した。
- 子の工数: Codex author 1・fix 3 (job dir の一回限りの tool、repo 外)、段 6 read-only レビュー 1。
- 計算ノード: 受入のみ。

## 次の一手差分

### 完了

- [T-2829] D2200 項 2 を実行した。`cleanup-20260921-*` 227 は `accepted-loss`、`audit-20260921-*` は現存 19 を `refs/rescue/cleanup-20260921-audit/<oid>` で `rescued`、消失 2 を `object-missing` にした。
  remaining: none
  base: 18e77b77ba3d4cf31fcb3214bc5ab0a1ad537d2050307e135fc1b3596601fc54
- [T-2840] 13 object をすべて記帳した (12 は本件の新規 entry に含まれ、`b3de31e0` は監査外として追記)。解決の残りは {{T:unreachable-discard-approval}} が引き継ぐ。
  remaining: none
  base: 64f9bc7516c7af1e6a91a195d48cabef89d83b262a94ff9a42f126a451a3cc81

### 新規

- {{T:unreachable-discard-approval}} **P3・ユーザー裁定待ち**: 到達不能 object 台帳の捨て候補 92 件 (`unreachable-20260930-*` の `pending`) の一括喪失受容。承認カードは `output/insights/2026-09-30/unreachable-cleanup/README.md` の「承認カード」節 (類型 A script・起動器・設定だけの残差 61・B 中身が main か repo 外の控えに残る 30・C amend 前版 1)。承認なら AI が `accepted-loss` へ遷移し固定 ref `refs/rescue/unreachable-20260930/<oid>` 92 本を外す。それまで固定は残る。
