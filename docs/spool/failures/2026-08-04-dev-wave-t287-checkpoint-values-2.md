---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: dev-wave-t287-checkpoint-values
seq: 2
---

## 新規

### {{F:mutation-harness-realrepo-node}}. 変異 harness が real-repo 直列化 node の期待を表現できない [恒真ゲート]

- 事象: [T-287] の変異本走で、`test_drive_iteration_checkpoint_survives_across_calls` 等
  real-repo 直列化対象の 3 node を kill 集合に含む変異 (M1) を**登録できなかった**。
  素の pytest node id で登録すると突き合わせが `MISMATCH` になり (観測側は `@real-repo` 接尾辞付き)、
  接尾辞を付けて登録すると preflight が「期待 node が pytest collection に実在しない」で停止する。
  2 通りとも fail-closed に倒れ、本走が 2 度中断した。
- 根本原因: `tools/mutation_harness.py` の 2 つの検査が同じ node に**異なる表記**を要求する。
  preflight (`_collect_expected_nodes`) は pytest collection との突き合わせなので素の node id を要求し、
  実測突き合わせ (`_match_key` = `_normalize_node`) は runner が付ける `@real-repo` 接尾辞を
  剥がさずそのまま比較する。`DW-M08` は「事前登録の期待 node と記録 node は突き合わせ前に
  同じ形式へ正規化する」と定めているが、**その正規化を harness 自身が持っていない**。
  結果として、real-repo 直列化対象 node が kill する変異は事前登録の対象外になり、
  その面の変異検査が黙って行われなくなる (恒真化の経路)。
- 恒久対応: {{T:mutation-harness-node-normalization}} で `_normalize_node` に
  runner 接尾辞の正規化を入れ、preflight と突き合わせの表記を一致させる。
  それまでの回避は `DW-M01` / `DW-M03` に従う再照準 —
  real-repo node を巻き込まない単一理由の変異へ差し替え、期待 node は推測せず
  一時変異の実測 (`DW-O19` の復元規律) で確定する。
- 再発検知: 変異本走の `MISMATCH` と preflight 停止。どちらも fail-closed なので黙って通り抜けることは
  ないが、**再照準の理由を台帳に書かないと「その変異は元から無かった」ことになる**。
  [T-287] の逐語は `output/insights/2026-08-04_t287-checkpoint-values/README.md` と
  erratum 台帳 `mutation-ledger-v1-erratum.json` に残した。
