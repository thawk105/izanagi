---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: dw-codex-model-sol
seq: 2
---

## 再発

### F223

- **再発: 2026-09-23** — model 移行 wave ({{D:dev-wave-codex-model-sol}}) の段 5 author 1 回目が、所有 file の `orchestrator/tests/test_check_docs.py` を `cat` で全体表示し、5756 / 5779 行の非 NFC 文字を含む event 行 (約 47 万 byte) で `evidence_status=invalid`・`launcher_rc=1`・`outcome=not_accepted` になった (codex exit 0、12 call、約 3 分、差分自体は裁定どおり)。同じ unit で base から branch を切り直し、prompt に「5740〜5800 行を表示しない・全体を `cat` しない」を足した 2 回目は `accepted` (12 call)。[T-855] (非 NFC 行の正規化と機械検査) は見送り台帳にあり未実装で、同ファイルを所有・編集する wave では prompt への行範囲禁止が今も唯一の回避策である。
