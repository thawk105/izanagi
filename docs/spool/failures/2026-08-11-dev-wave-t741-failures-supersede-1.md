---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t741-failures-supersede
seq: 1
---

## 再発

### F138

- **再発: 2026-08-11** — 本 wave の変異 7 件のうち 2 件 (M02 暦日検査の無効化、M05 target
  不存在検査の無効化) が MISMATCH。いずれも赤は出ており検出は成立していたが、登録した期待 node が
  1 件ずつ不足していた。実際には同じ不正入力を使う consumer 側のテスト
  (`test_spool_guard_reports_failure_supersede_issue`) と CLI 側のテスト
  (`test_cli_dry_run_reports_failure_supersede_semantic_issue_without_writes`) も同時に赤くなる。
  観測集合で再登録して再走し 2/2 KILLED。初回台帳は erratum として保持している。
  **恒久対応の内容は変わらないが、3 例目まで機械強制が無いことが顕在化した** — 同じ不正 fixture を
  複数層のテストが共有する設計では、層の数だけ赤 node が増えるのが正常である。

## supersede 追記

- F196 **supersede: 2026-08-11** — 恒久対応末尾の「runbook §7.3 の待ち手契約自体の改訂は本 wave の scope 外であり、裁定へ返す」は F197 で実施済み ([T-732] 裁定 (a)、待ち手内 merge が §7.3 の正本)。
