# 依頼の逐語 (2026-09-20、`/dev-wave` の引数)

[T-2810] (P1、新規、AI 手番、entry 1742) 凍結 v2 g1 の full launch validation を通す。着手直前の local main から fresh
  worktree。一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md` §5。(1) `orchestrator/campaign/s8b_ratified_freeze.py` の
  `_JOURNAL_KEYS` に official run の journal event `reservation-preflight` (producer `s8b_floor_campaign.py`、`floor_liveness.py` が読む) の
  key 集合を allowlist 方式で足す。(2) `_launch_validate` 段階 6 (result の導入集合 == {G}) と D2077 の一方向順序 (result → 候補 → G)
  の矛盾を、α (段階 6 を「chain の祖先で cert C より後」へ改める、推奨) / β (G を result と同 commit で作り直す = D2120 項 2 (b)
  の再裁定が要るので無断で採らない) / γ (floor_source へ導入条件を課さない) の 2 レンズ相談で決め、Codex author (D95)
  で実装する。受理集合の変更なので敵対レビュー + 変異 (正例・負例) を必須にし、規律 2 を緩めない。`docs/phase3-8b-restart-runbook.md` §2 P3
  gate-check を g1 path で再実測し、`_ACTIVATED_G1_REFUSALS` (held 6 node) を実測で更新する。journal 修正後に semantic / binding
  段階で別の不整合が出たら、その事実を記録して止める (全 gate 受理を約束しない)。W-4 spec・W-5・certification は scope
  外。本題の修復だけ、仮想リスク向けの gate・検査・台帳の追加は scope 外。
