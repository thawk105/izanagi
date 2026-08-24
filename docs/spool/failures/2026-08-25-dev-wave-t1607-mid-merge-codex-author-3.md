---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1607-mid-merge-codex-author
seq: 3
---

## 再発

### F37

- **再発: 2026-08-25** — 背景 job の待ち手を `dev_wave_wait.py producer ... 2>&1 | tail -3` の形で
  張ったため、通知が報告する exit code が待ち手ではなく `tail` のものになった。変異本走で表面化し、
  「完了 (exit code 0)」の通知後に `.done` も成果物も無く、producer は稼働中だった。
  `| tail` を外して前景で張り直すと `rc=70 producer-timeout` が正しく返った。
  検査 rc だけでなく**待ち手の rc も同じ穴を持つ**。各段で `.done` と
  `check_codex_output.py` を個別に検証していたため偽緑の記録には至っていない (near miss)。
