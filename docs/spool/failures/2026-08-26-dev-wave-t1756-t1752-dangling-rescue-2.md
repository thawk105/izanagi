---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1756-t1752-dangling-rescue
seq: 2
---

## 再発

### F217

- **再発: 2026-08-26** — 段 2 の plan 子が起動 7 分で web 検索を 2 query 使い、親が events を
  見て停止した。成果物が全損する前に止めたため receipt での不採用は観測していない。
  親 prompt に禁止を書き忘れたのが原因で、`DW-C01` の 1 行だけが防壁だった。
  投げ直しでは禁止に加えて、子が git の挙動を調べに行く動機そのものを消すため、
  親が実走した測定結果 (`measurements.md`) を必読資料として渡した。
  **2026-08-11 の再発で見送った reference への配線を再度測ったが、今回も入らない。**
  `docs/dev-wave/operations.md` の `DW-O02` へ最小の 1 文 (39 bytes) を足すと
  L1.5 unique footprint が 9,605 bytes となり予算 9,566 bytes を超える。編集は復元した。
  恒久対応は依然として機械強制されておらず、prompt 生成側の検査を
  {{T:codex-child-web-search-ban}} として起票した。
