# 段 6 追補裁定 1 — 2026-10-01 00:35 JST

## 事実
- 焦点走 f2 (fix commit `c33afae78`、39 file): 3,900 passed / 1 failed / 5 skipped。赤は既存の閉包 test
  `orchestrator/tests/test_layer3_report.py::test_verification_producer_keys_and_schema_closure` (5590 行、
  `Extra items in the right set: 'gate_witness'`)。
- この test は `pipeline._execute_verification_repetition` が `verify_payload` に書く全 key を AST で集め、層 3 の
  レポート schema (`orchestrator/campaign/layer3_schema.json` の `verifications.items`、`additionalProperties: false`)
  が全部を知っていることを要求する。条件つきで書く key は `include_qualification_evidence` の分岐だけを別扱いにしている。
- fix 1 (段 6 裁定 1 の A2) で、要求つきの反復だけ `verify_payload["gate_witness"]` を書くようにした。schema に無いので、
  gen-opt の campaign から層 3 のレポートを作ると schema 検証で落ちる (放置時の成果物影響: gen-opt の材料レポートが作れない)。
- 先例: D828 (層 3 schema へ optional property を足すとき `schema_version` を上げず `required` も変えない)、D829 (view 側で producer の key を消して schema に合わせてはならない)。

## 裁定
1. `orchestrator/campaign/layer3_schema.json` の `verifications.items.properties` に optional property `gate_witness` を足す。
   中身は `orchestrator/verifier/report.py` の `result_to_dict` が出す `gate_witness` 節の形に合わせた閉じた object
   (key 集合と型をそのまま。`additionalProperties: false`)。`required`・`schema_version`・他の property は変えない。
2. 閉包 test `test_verification_producer_keys_and_schema_closure` は、`include_qualification_evidence` の分岐と同じ形で
   `require_gate_witness` の分岐 (`if require_gate_witness:`) を条件つき producer key として別扱いにし、その key 集合が
   ちょうど `{"gate_witness"}` であること、それが schema の properties に在ることを assert する。
   gate 節つきの payload で `_view_row` と `build_report` → `_validate_schema` が通る正例を同じ test か新しい test に足す。
   **この test の既存の assert (qualification の扱い、view_only、commit_witness・proof_surfaces の照合) は変えない。**
   許す期待の変更はこの 1 test の上記 2 点だけ。
3. `layer3_report.py` (view・reader) は変えない (D829)。historical schema の導出に影響が出たら変えずに報告して止める。
4. 放置しない理由: gen-opt の certified 行の根拠 (要求・版・D5) を WAL に残すのが A2 の裁定で、層 3 はその WAL を材料レポートにする consumer である。
