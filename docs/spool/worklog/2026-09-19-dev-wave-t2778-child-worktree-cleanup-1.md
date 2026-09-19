---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2778-child-worktree-cleanup
seq: 1
title: [T-2778] 子worktreeをmanifestに束縛して段9でwave自身が撤去する恒久対策 (コード + docs、branch worktree-dev-wave-t2778-child-worktree-cleanup)
---

## 本文

- ユーザー裁定 (2026-09-19)「ワークツリーが残って next-tasks / cleanup-branches のたびに費用が増え続けている。恒久対策が要る」で
  1 wave。着手直前の local main `2ba400087` から fresh worktree、稼働 19 木の編集面重複は commit 差分と dirt の両方で 0。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/HANDOFF.md`。
- 設計と却下案は {{D:child-worktree-manifest-cleanup}} (D703 の例外拡張、D2148 項 9 (iii) の部分 supersede)。逐語・変異台帳は
  `output/insights/2026-09-19/t2778-child-worktree-cleanup/README.md`。
- 段 2 plan、段 3 敵対相談 2 本 (正しさ境界・過剰)。採用: caller 指定の統合参照を廃止 (子 HEAD で恒真化)、退避は生 bytes tar +
  patch 3 種、assume-unchanged / skip-worktree・未解決 stage・変換属性・dirty または pin 外の submodule・primary store に無い pin・
  reset 前履歴は fail-closed、登録 CLI・時刻・履歴 pack・子 branch 削除は削除。refuted: 「DW-O28 は 989 bytes 固定」(先例 5fc1d8971)。
  plan の「D2148 項 9 の射影が別 D」は親の射影 script の誤りで、段 3 前に修正した。
- 実測: 稼働中の author / fix 子木のうち親祖先性を確認できた 3 本は親 wave tip の祖先でなく、所有 path の blob は親 tip と一致、
  不一致は報告 `.md` だけ (probe は一致 0)。docs 予算は L1 10623/10625、L1.5 9695/9696、DW-O28 996/1000 で、既存文の空白縮約だけで収容した。
- 段 5 author (4 file、+756 行、新設 31 node)。焦点走 1 は 293 passed / 1 failed (占有 test の後始末 `terminate()` が dispatch で効かず)。
  段 6 敵対レビュー 2 本は両 NO-GO (clean filter の生 bytes、子 admin 配下の submodule store、DW-O28 の `--main-worktree` 欠落、
  committed 差分の退避、m6/m7 の anchor 等)。初回は wave 木で docs 未 commit のため review 段の authority 検査で rc=2 即死し、
  author 子木 + docs.patch 射影で再投入した。fix は 4 巡 (fix2・fix4 は親の実機実走でしか見えない fixture の非現実性: primary module store の
  不在、size を変える clean filter で git status が clean にならない)。fix 巡は author 木を再利用して branch だけ切り manifest を再登録した
  (DW-S05-A の dogfood)。焦点再レビュー 2 巡 (1 巡目 NO-GO 2 件 → 2 巡目 GO)。
- 焦点走 2 (dispatch 10890.nqsv) 269 passed / 1 skipped、焦点走 4 (11171.nqsv) 187 passed。統合木 check_docs rc=0。
  全史 provenance 11,617 件、新規違反なし (既知 56)。
- 変異は独立 clone・dispatch。probe (spec v1、commit 2a8127c4e): 6 KILLED / 1 SURVIVED / **1 MISMATCH** (m4 の期待 node 漏れ、
  焦点再レビューが事前指摘、erratum として保存)。本走 (spec v2、commit c9e4ad77a): baseline 186 passed、7 KILLED / 1 SURVIVED (等価)、
  期待 node 完全一致 8/8、MISMATCH 0、rc=0。
- `2a8127c4e` — 実装統合 (author + fix1 + fix2) と DW-S05-A / DW-O28 の改訂、`c9e4ad77a` — fix3 + fix4。
  最終受入と land の結果は専用 handoff に集約する。
- dev-wave 改善候補は 1 件 (review/focus 段の docs authority 検査は HEAD 照合なので親 docs を先に commit するか子木で走らせる)。
  L1.5 予算 (残 1 byte) で reference へ入らず、D782 の独立 3 例にも達しないため実施せず、insight と memory に記録した。
- 所有契約を固定した author / fix の観測に基づく限定方式であり、probe・scratch・変異 container への成立は未確認 (段 3 所見 B14)。
  既存残骸 19 本と過去 wave の manifest 無し子木は D204 のまま個別指示に残る。

- [T-2778] manifest に束縛された子 worktree の撤去 (`remove-child`) と作成時登録・fix 巡再利用・回収 wave の手順を実装した。

## 次の一手差分

### 完了

- [T-2778] 恒久対策として manifest 束縛の子木撤去を実装し、DW-S05-A / DW-O28 の手順と決定を記録した。段 9 で自 wave の author 子木を同 tool で撤去する。
  remaining: none
  base: 8a792bd036caea09efc49049cedacfbc3ccd23e5f497ee0f77e31f1f22d0e8f6
