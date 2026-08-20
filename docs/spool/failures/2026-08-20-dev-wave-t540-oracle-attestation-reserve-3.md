---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t540-oracle-attestation-reserve
seq: 3
---

## 再発

### F43

- **再発: 2026-08-20** — [T-540] 段6 fix (NaN/Inf 回帰テスト追加、3回目の fix 試行) の
  出力が 492 bytes で 500 bytes 下限に届かず `codex_worker_launch.py` に不受理にされた
  (`accepted=false`, `validator_rc=1`, `codex_exit_code=0`)。sandbox=workspace-write での
  実ファイル書き込み自体は正しい内容 (NaN/Inf 拒否テスト2件) で完了していたが、正式な採用
  記録がないため、4回目の fix へ「現状確認し、既にあれば重複させない」指示で再投入し
  accepted 記録を得た。同日中に既出の2件 (2026-08-18 型の3回目相当) と同型。
