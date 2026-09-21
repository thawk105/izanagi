---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-paper-b8-pass-ja
seq: 2
---

## 再発

### F818

- **再発: 2026-09-21** — docs-only の論文草稿 wave (branch `worktree-dev-wave-paper-b8-pass-ja`) の段 6 read-only レビュー 2 本が、各 14 model call・約 110 秒で
  `You've hit your usage limit ... try again at Sep 26th` を受け、F818 と同じ署名 (出力 0 byte・`f45_missing_output`・`codex_exit_code=1`) で終了した。
  events 末尾の `turn.failed` の本文で枠切れと確かめ、D582 に従い自動再試行せずユーザーへ報告した。wave は元から docs-only で凍結境界は効かないが、
  `DW-C00` が一次資料を再抽出する docs-only wave に残せと言う**独立 read-only レビュー 1 本に、Codex 以外の経路が正本に無い**。今回は同じ prompt を
  Claude の独立 context の子 (Edit / Write を持たない Plan 型、model = opus。無指定は guard_agent が拒否する) のレビュー 2 本と焦点再レビュー 1 本で代替し、
  must-fix 1 件 (判定集合 30 枠を本走の条件へ丸ごと帰属させる要約) を含む real 所見 20 件 (採用 19) を得た。代替の独立性は Codex と同等と主張せず、
  成果物 README (`output/insights/2026-09-21/paper-results-ja-b/README.md` §4) に明記した。代替経路の正本化は段構成の変更なので実装せず、同 README §7 に候補として記録した。
