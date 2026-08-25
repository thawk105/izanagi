---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t441-backoff-hole-grammar
seq: 2
---

## 新規

### {{F:mutation-group-suffix-node-mismatch}}. 変異 harness は group 実行される期待 node を完全一致にできない [手順漏れ] [テスト代表性]

- 事象: 変異本走で `t441.p01` が MISMATCH になった。差分は 1 件で、期待側が
  `...::test_drive_iteration_checkpoint_survives_across_calls`、観測側が同じ test の
  `...@real-repo` 付き。**同じ test が同じ理由で落ちており、id の綴りだけが違う。**
- 根本原因: 同じ harness の中で二つの経路が別の形を要求する。**収集前の実在検査は
  接尾辞なしの nodeid を要求して停止し** (接尾辞付きを書くと「pytest collection に実在しない」)、
  **失敗 node の抽出は xdist の group 接尾辞付きで記録する**。したがって group 実行される
  node を期待集合に含む変異は、どちらの綴りで書いても `DW-M08` の完全一致を作れない。
  本 wave は両方の綴りを実走で試し、前者で走行前停止 (rc=2)、後者で MISMATCH を実測した。
- 影響: 検出力そのものは損なわれない (当該 node は実際に落ちている) が、
  matrix の集計が「実質 n/n」という但し書き付きになり、**真の SURVIVED と
  表記由来の MISMATCH を機械で区別できない**。
- 恒久対応: なし (本 wave の scope 外)。現状は erratum として台帳に残し、
  実質 13/13 と明記する運用で凌ぐ。**この F 自体が、次に同型を踏む wave のための
  検知点である** — 抽出側を収集側の形へ正規化するか、比較時に group 接尾辞を
  無視する正規化を入れるかは `tools/mutation_harness.py` の改修として別途裁定へ返す。
- 再発検知: group 実行対象 (`REAL_REPO_SERIAL_NODES` 等) を期待 node に含む変異 spec を
  組んだ wave が、走行前停止か MISMATCH のどちらかで必ず踏む。
