---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2833-land-eintr-retry
seq: 1
---

## 再発

### F818

- **再発: 2026-09-21** — [T-2833] wave の段 6 で、Codex review 子 2 本が `You've hit your usage limit ... try again at Sep 26th, 2026 7:35 PM` (14:40:51 JST) で
  rc=1・出力 0 になった。今回は段 5 の Codex author が完了し commit 済みだった点が 2026-09-02 と違う。D582 に従い自動再試行せずユーザーへ通知し、
  敵対レビューは独立 context の Claude 子 2 本 (同じ prompt・同じ 2 レンズ、read-only) で代替した (DW-S06-A / DW-O01 の「codex」からの逸脱、
  `output/insights/2026-09-21/t2833-land-eintr-retry/README.md` §3)。must-fix 0 で fix が要らなかったため実装差分は Codex author のまま land できた。
  fix が要る所見が出ていれば、D95 により Claude は代行せず 9/26 まで停止するしかなかった。

## supersede 追記

- F672 **supersede: 2026-09-21** — 恒久対応「未実施」は古い。[T-2833] (D2206 項 1) で `_registered_worktree_paths` の strict resolve を `InterruptedError` のときだけ 1 path あたり最大 5 回 (sleep なし、outer watchdog の armed 区間内) 呼び直す局所修正を入れた (commit `2a29a2381`、`output/insights/2026-09-21/t2833-land-eintr-retry/README.md`)。効果は未実測で、使い切れば同じ文言 `registered worktree path cannot be resolved: [Errno 4] Interrupted system call` の rc=31 が残る。その場合の再発検知は本エントリのまま、復旧は同じ tested tip / landing tip / receipt での再投入 (受入の取り直しは不要、`output/insights/2026-09-21/land-roundtrip-diagnosis/README.md` §3.2)。
