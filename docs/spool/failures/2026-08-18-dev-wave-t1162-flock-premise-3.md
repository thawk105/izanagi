---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1162-flock-premise
seq: 3
---

## 再発

### F217

- **再発: 2026-08-18** — 段 3 敵対レンズ A が web 検索を 3 回使い (events の `web_search` 3 件)、
  `codex_exit_code=0` / 41 model call / 673 秒 / 出力 9983 bytes / `## 総括` あり
  にもかかわらず `evidence_status=invalid` / `accepted=false` で不採用になった。
  入力 376 万 token を消費している。**3 度目の同型発生であり、2026-08-11 の再発で記録した
  「恒久対応がどの dispatch 節にも配線されておらず書き手の記憶に依存している」状態が
  そのまま持続していることの実証である。** 本 wave の親も consult prompt に禁止を書き忘れ、
  Web 禁止を明記した prompt で再走して初めて受理を得た (結論は両走とも同一)。
  機械強制は {{T:codex-web-search-machine-block}} で起票する。
