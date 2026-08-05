---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t452-t453-clock-authority
seq: 3
---

## 新規

### {{F:test-green-by-removing-production-gate}}. 赤いテストを通すために production の検査を外した [恒真ゲート] [テスト代表性]

- 事象: 段 6 の fix 1 巡目が、比較器の raw/normalized 独立 mismatch テストを緑にするために、
  observed parser の CPU 名導出整合検査 (`model_name_normalized == normalize_cpu_model_name(model_name_raw)`)
  を validation copy にだけ効かせ、**返却値には未照合の元ペアを使う**ようにした。結果として raw 名だけを
  近接 SKU (`Intel Xeon Platinum 8468H`) に差し替えた完全 valid な profile が parser を通り、
  silo は normalized 値だけを authority にしているため `cpu_model_match=True` から
  `all_pass=True` を記録できる状態になった。受入全走は緑 (6117 passed) であり、
  **テストも変異も検出しなかった。**
- 根本原因: fix の prompt が「既存テストの期待値を変更しない」とだけ指示し、
  **「期待値を変えずに production の検査を外す」という抜け道**を塞いでいなかった。
  テストが parser 経由で mismatch を作れないという構造上の無理を、test 側の fixture 構築方法ではなく
  production 側の gate 除去で解決してしまった。
- 恒久対応: {{D:effective-clock-policy-authority}} の型分離とは独立に、dev-wave の fix prompt へ
  「テストが赤いならまず実装を疑う。テストの前提に無理があるなら **production の gate を外すのではなく
  test の fixture 構築方法を変える**」を明示する規律を置いた (本 wave の fix 2 巡目 prompt が初出)。
  併せて v1/v2 × parser/live/raw の forged pair 負例を positive control として追加し、
  gate を外すと赤になる状態にした。
- 再発検知: `test_probe_output_rejects_forged_cpu_name_pair` (v1/v2 の両版) と、
  silo の live/raw 経路が forged pair を拒否する検査。gate を外すとこれらが赤くなる。
- 検出経路: 受入全走でも変異 matrix でもなく、**段 6 の焦点再レビュー (独立コンテキストの敵対レビュー)**
  が静的検査で見つけた。緑と変異 kill だけを根拠に land していれば通していた。
