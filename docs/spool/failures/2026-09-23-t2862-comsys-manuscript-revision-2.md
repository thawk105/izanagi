---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: t2862-comsys-manuscript-revision
seq: 2
---

## 再発

### F223

- **再発: 2026-09-23** — [T-2862] の段 6 read-only レビューで、子が `manuscript.pdf` を `pdftotext` で読み、参考文献の「Vũ」(tex 側は ASCII の `V\~{u}`) が u + U+0303 の分解列で `command_execution` の event 行に載り、`evidence_status=invalid` で不採用になった (10 model call・191 秒)。非 NFC の出所は tracked file ではなく PDF の文字抽出が作った派生出力なので、本 F の再発検知の後半 (tracked file の棚卸し) では見つからない。events.jsonl の NFC 判定で 36 行目を特定し、prompt で PDF の文字抽出を禁じた 2 回目 (別 job-id) は受理された。
