---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1316-acceptance-recovery-ruling
seq: 1
title: 受入 lease 取得後・受入 command 投入前に落ちる型からの回復経路について設計択一を裁定パッケージとして作成した (docs、branch worktree-dev-wave-t1316-acceptance-recovery-ruling)
---

## 本文

- [T-1316] (lease 取得後・受入 command 投入前に main が進み `--merge-message-file` を
  持たず lease を失う型、実測 t1180・F365) について、実装せず設計択一の裁定パッケージを
  作成した。段 2 (plan 1 本) と段 3 (敵対レンズ 2 本、正しさ境界 / 実効性・網羅性) が計 11 件の
  所見を出し、親は 9 件 real・2 件 refuted と裁定した。refuted の 2 件はいずれも
  「P1 が owned-path-overlap 等の正当な fail-closed 経路を誤って救う」という懸念で、
  コード・既存テストが反証した。
- 親の provisional 案 (P1: merge-message-file を投入時点の main 状態に関わらず常時同梱すれば
  コード変更ゼロで race を閉じる) は「特定の欠落 sub-race は閉じる」ことが段 3 で反証できな
  かった一方、(a) 運用規約は機械強制されず、既存の近い規約 (`docs/pegasus-runbook.md:921-922`、
  ただし preclaim 相当に限定され postclaim race は対象外) があっても t1180 は発生した実績が
  ある、(b) D486 の attempt 2 で main がさらに進む複合レースは閉じない、ことが段 3 レンズ A・B
  双方で独立に確認された。
- 推奨は二段構え。**P2 (`--merge-message-file` を必須化し claim 前に検証済み snapshot を取る、
  コード変更あり) を恒久策**、**P1 (運用規約の即時是正) を暫定 mitigation** として次回
  `/rulings` へ提出する。P1 の docs 追記は段 8 self-improvement routing が必須かつ、
  `.claude/commands/dev-wave.md` (実測 9,492/9,500 bytes)・`docs/skill-self-improvement.md`
  (実測 5,963/6,000 bytes) の予算がほぼ満杯であることも明記した。
- 段 3 が見つけた、同じ「lease 取得後・受入 command 投入前に retry せず release する」構造を
  持つが引き金が異なる残余のうち、具体的に切り出せる 2 件を新規起票する。3 件目
  (owned-path-overlap・merge-message-provenance・commit-message-postcheck 等の兄弟 failure
  経路一覧) は `DW-G03` の独立 2 例に届かないため起票せず、裁定パッケージ内の記録に留めた。
- 裁定パッケージ本体は `output/insights/2026-08-19_t1316-acceptance-recovery-ruling/
  ruling-package.md`、段 2 plan と段 3 レンズ A/B の逐語記録は同 directory `verbatim/`。
- 子の工数 (`.pid`/`.done` の mtime 差から実測): plan 1 本 約 11 分、敵対相談 2 本
  (レンズ A 約 11 分、レンズ B 約 10 分)。3 本とも `check_codex_output.py` rc=0。

## 次の一手差分

### 更新

- [T-1316] **P1・裁定パッケージ提出済み**: 設計択一 (P1 暫定 / P2 恒久 / P3 却下 / 現状維持
  非推奨) を `output/insights/2026-08-19_t1316-acceptance-recovery-ruling/ruling-package.md`
  にまとめ、次回 `/rulings` セッションへ提出する。本 wave は実装していない。
  base: faedc49ef919c1b737a35b699cf4cfba8c31fad658c4c4ca6a11eaf597c236ed

### 新規

- {{T:accept-attempt2-race}} **P2・新規**: 受入待ち手の D486 attempt 2 で、self-claim 前に
  main がさらに進むと `claim-self-unverified` になり、有効な merge-message-file があっても
  回復しない (`tools/dev_wave_wait.py:2875-2881`、`tools/wave_land_window.py:733-761`、
  既存テスト `orchestrator/tests/test_dev_wave_wait.py:10125-10138`)。[T-1316] の P1/P2 は
  いずれもこの複合レースを閉じない。詳細は R-B (`output/insights/
  2026-08-19_t1316-acceptance-recovery-ruling/ruling-package.md`)。
  成果物影響 = 未計測 (実害の観測例はまだ無い、attempt 2 が発火する頻度自体が低い)。
- {{T:accept-merge-author-classifier}} **P3・新規**: `merge-message-provenance`
  (`tools/dev_wave_wait.py:3816-3825`) は merge の 3 方向結合結果に実装面 path が両親と
  異なる形で含まれると、固定 trailer では Codex `role=author` 要件を満たせず rc=70 で落ちる
  (`tools/check_ai_provenance.py:1231-1261`, `1344-1349`)。過去に 1 度実際に発生し
  known-violation registry で事後救済された実績がある (`_DW8C_ACCEPTANCE_MERGE_NOTE`,
  `tools/check_ai_provenance.py:213-219`)。既存の `owned-path-overlap` は部分的な緩和に
  留まる。[T-1316] の P1/P2 いずれを採っても増減しない既存リスク。詳細は R-B (同上)。
  成果物影響 = 直さない場合、稀に (`owned-path-overlap` の宣言漏れ時) 受入 lease を
  同様に喪失しうるが発生率は未計測。
