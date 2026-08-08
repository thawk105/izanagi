---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t139-addendum-a
seq: 2
---

## 再発

### F57

- **再発: 2026-08-08 ([T-139] 追補 A wave の受入全走)。** 48 worker の全走
  (request `896006`、7,393 件、1216 秒) で
  `test_codex_worker_launch.py::test_manifest_is_appended_while_correlated_session_is_running` が
  1 件落ちた (7372 passed / 1 failed / 20 skipped、gw10)。落ち方は F57 の型どおりで、
  launcher subprocess が `rc=1` / stdout・stderr とも空 (`assert 1 == 0`) である。
  同 file の単独再走 (request `896010`) は **64 passed / 5.28 秒 / rc=0** で再現しない。
  本 wave の差分は `output/insights/` と `docs/spool/` の **docs のみ**で launcher 実装・
  同 test file へ到達しえず、`DW-O18` により帰属しない。
  **新しい情報は、このテスト名の再発が 2026-07-31 (request `874704`) に続く 2 回目であること** —
  F57 の族の中で同じ node が 2 度当たった例は
  `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` に続き 2 例目になり、
  「失敗 node は毎回移動する」より「一部の node が繰り返し当たる」という既存の見立てを補強する。
  なお本走行は親の codex 子をすべて終えてから単独で投入しており、
  2026-08-06 の再発で見立てた「受入の隣で子 process を走らせる」条件は成立していない。
  恒久対応は F57 既載のとおり失敗 artifact 保存による原因分離であり、本 wave では変えていない。
