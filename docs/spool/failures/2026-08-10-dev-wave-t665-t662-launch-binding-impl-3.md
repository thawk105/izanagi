---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t665-t662-launch-binding-impl
seq: 3
---

## 新規

### {{F:derived-oracle-circular-test}}. 派生関数を期待値の出所にしたテストは、その派生関数の変異を検出できない [恒真ゲート] [検出力]

- 事象: docs 権威から起動値を導出する機構で、`derive_launch` の段 6 effort を別の許容値へ
  置換する変異が生存した。対象テストは 623 passed / 0 failed で全緑、段 3 と段 6 の
  敵対レビュー計 4 本も通過した後だった。**束縛の中核主張がテストで証明されていなかった。**
- 根本原因: 2 本のテストが期待値を `derive_launch(snapshot_authority(...), ...)` から取っていた。
  派生関数そのものを変異させると期待値も一緒に動くため、比較が恒真になる。
  静的レビューはこの循環を「期待値を hardcode していない良いテスト」と読んで見逃した。
- 恒久対応: {{D:derived-value-test-needs-independent-oracle}}。
  実体は `orchestrator/tests/test_dev_wave_launch_authority.py` の
  `test_review_effort_matches_independent_docs_cross_check` /
  `test_focus_effort_matches_independent_docs_cross_check` /
  `test_all_stage_models_match_independent_docs_cross_check` で、
  docs 節から独立に抽出した値と派生値の一致を要求する。
- 再発検知: 同 3 本を変異 matrix の期待 node として登録する。派生関数の値を固定値へ置換する
  変異 (本 wave の M08 / M08c) が KILLED になることを再走で確認した。

### {{F:documented-route-not-executable}}. 文書化した起動 route が実際には起動できない [手順漏れ]

- 事象: `DW-O01` を新しい dispatcher 経路へ差し替えた直後、その契約どおりに段 6 の
  レビュー 2 本を起動したところ両方 rc=2 で即死した。**契約に従うと codex 子が 1 本も起動できない
  状態を land しかけた。**
- 根本原因: 2 つ重なっていた。(i) 文書の route 行が必須引数を欠いていた。
  (ii) dispatcher が生成 path の directory を作らず、launcher の `_preflight_run` が
  `receipt.parent` / `manifest.parent` の実在を検査した**後で** `artifact_dir` を作る順序のため、
  receipt と manifest を artifact_dir の中に置く構成では必ず先に落ちる。
- 恒久対応: dispatcher が生成 path の directory を先に作る
  (`tools/dev_wave_codex.py`。launcher の parent 実在検査は緩めない)。
  文書の route 行は実行可能な参照へ直し、残りの引数は `--help` に従うと明記した。
- 再発検知: 中間 directory が無い状態からの起動を `orchestrator/tests/test_dev_wave_codex.py` の
  回帰テストに置いた。あわせて、land する起動経路は wave 内で実際に 1 度使う (dogfood)。
  **この欠陥は段 3 と段 6 の静的レビュー計 4 本では出ず、実起動で初めて出た。**
