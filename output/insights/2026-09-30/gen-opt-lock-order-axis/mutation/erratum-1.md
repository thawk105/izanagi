# 変異 erratum 1 — M5 の期待 node から実行順依存の巻き添え node を外す (2026-09-30)

- 初回本走: tag m2、out-m2.json、spec sha256 a9c8388c207d8df7f31f609b6fbe1a36c23dcf61025fa30409882799fd8474b0、対象 2148b469a。
  結果 KILLED 5 (M1・M2・M3・M4・M6、期待 node と完全一致)、MISMATCH 1 (M5)。初回結果は消さない。
- M5 (gate が文法検査より前に source を書く) の観測: dispatch の pytest では
  `test_silo_lock_order_gate.py::test_gate_rejects_grammar_before_write`、
  `test_silo_lock_order_gate.py::test_gate_rejects_compile_before_write`、
  `test_silo_lock_order_template.py::test_real_patch_gate_rejects_forbidden_field_without_write` の 3 件が赤。
  期待に含めていた `test_silo_lock_order_template.py::test_touch_markers_api_and_quarantine` は緑。
- 原因: 期待 node は login の自走 probe (probe-p1.json) の観測から取った。自走は同じ process で test を名前順に走らせるので、
  M5 の変異下で `test_real_patch_gate_rejects_forbidden_field_without_write` が module 共有 fixture の transaction.cc を
  書き換えたまま残し、後で走る `test_touch_markers_api_and_quarantine` がそれを読んで赤になった。pytest の並列 worker では
  順序と process が違うので起きない。これは変異の直接の検出ではなく実行順に依存する巻き添えで、期待 node に入れたのは誤り
  (DW-M08、期待赤を順序・タイミングに依存させない)。
- 訂正: M5 の期待 node を上の 3 件にする (受理集合の変化 = 拒否されるべき候補で source が書かれることを直接見る test だけ)。
  他の変異の期待は変えない。spec-final-2.json で 6 変異とも再走する。
- 付記: 巻き添えが起きるのは変異下だけ (無変異では拒否 test は source を書かない)。無変異の production の挙動には関係しない。
