---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: worktree-dev-wave-t2140-b4-floor-procedure
seq: 2
---

## 再発

### F37

- **再発: 2026-09-02** — [T-2140] wave の親が焦点走を `run_tests.py ... | tail -20` で投げ、
  表示された `exited with code 0` が `tail` の rc だと気づかずに一度緑と読んだ。記録前に自分で
  誤りに気づき、rc をファイルへ落とす runner script で走らせ直して真の rc=0
  (694 passed / 3 skipped) を得たので、偽緑の記録には至っていない (near miss)。
  同日の provenance 監査でも同じ形をとったが、こちらは 2026-08-09 の裁定で `dev_wave_land.py` の
  全史監査へ機械強制済みであり land 側で捕まる。**機械強制が及んでいないのは焦点走の側である。**
  `DW-O17` は単独 rc を既に要求しており規約の不足ではないので、手順は増補しない。
