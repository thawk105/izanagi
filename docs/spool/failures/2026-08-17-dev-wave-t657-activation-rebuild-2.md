---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t657-activation-rebuild
seq: 2
---

## 再発

### F37

- **再発: 2026-08-17** — 親が焦点走を `run_tests.py ... -q 2>&1 | tail -15` で投げ、報告された exit code 0 が `tail` のものだった。dispatch epilogue しか残らず pytest の集計行が切り落とされていたため偽緑には至っていない (near miss、2026-08-04 と同型で 3 例目)。パイプを外し出力を file へ落として rc を別 file へ取る形へ組み直したところ、真の rc=0 と 651 passed / 3 skipped を確認できた。恒久対応は F37 既存のとおり変わらない。
