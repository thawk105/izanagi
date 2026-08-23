---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t080-e2e-optin
seq: 2
---

## 新規

### {{F:optin-test-rots-against-later-ruling}}. 既定 skip にしたテストが後続の裁定に追随せず腐った [テスト代表性] [手順漏れ]

- 事象: `orchestrator/tests/test_s8b_oracle_driver.py` の T-080 stub-free E2E 11 nodeid を
  2026-08-12 に `IZANAGI_T080_E2E=1` の opt-in へ移した。11 日後に初めて走らせたところ 2 件が赤で、
  片方は ccbench pin 不一致を、もう片方は holdout generator の改竄を、public gate が拒否しない
  状態を隠していた。
- 根本原因: opt-in にした**同じ日**に、別の裁定 `rulings-4th-batch-2026-08-12` が
  `orchestrator/campaign/freeze_verification_hold.py` の凍結検証保留を導入した。保留に追随する
  改修は走っているテストにだけ入り、既定 skip になった 11 nodeid は取り残された。
  片方は**同じテスト関数の 3 枝のうち 2 枝だけが対応済み**で、1 枝が取り残される部分適用だった。
- 恒久対応: {{D:t080-e2e-optin-removal}} で opt-in を機構ごと撤去し受入全走へ戻した。
  再導入の抑止は {{D:t080-default-execution-probe}} の実測 probe
  (`test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default`) が担う。
  既定 collection で対象 nodeid が選択され setup へ到達しなければ fail-closed する。
- 再発検知: 上記 probe に加え、変異事前登録 MUT-4 (module 冒頭 `pytestmark` による沈黙) と
  MUT-5 (conftest collection hook による沈黙) を登録し、旧 AST 監査では素通りする経路を
  新 probe が捕らえることを新旧両走で示した。

### {{F:hold-marker-not-exposed-to-caller}}. 凍結保留が呼び手から見えず、保留と検査消失を区別できない [恒真ゲート]

- 事象: `s8b_holdout_freeze.verify()` が作る保留 marker を
  `orchestrator/campaign/s8b_oracle_driver.py` が戻り値ごと捨てるため、public gate の
  `GateDecision.held_checks` は `()` のままになる。保留中の refusal 件数が 1 件少ないことを
  外から見ても、「保留が効いている」のか「verifier の呼び出しごと消えた」のかを区別できない。
- 根本原因: 保留機構は verifier の内側で marker を組み立てるが、public gate へ伝播する経路が
  設計されていない。下流のレポートと台帳からは保留された check_id の参照が消える。
- 恒久対応: (部分) 本 wave では production を変えずに、**driver が holdout verifier を呼び、
  その戻り値が refusal に現れることを結ぶ call-edge witness** をテスト側へ置いた
  (`orchestrator/tests/test_s8b_oracle_driver.py` の
  `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`)。
  変異事前登録 MUT-2 (driver から verifier への呼び出し辺の除去) が発火を確認する。
  **marker を `GateDecision` へ伝播させる production 側の改修は未実施で、ユーザー裁定待ちである。**
- 再発検知: 上記 call-edge witness と MUT-2。伝播欠損そのものの検知は裁定後の改修に依存する。

### {{F:test-temp-root-can-become-real-tree-writer}}. 明示 TMPDIR 次第でテスト fixture 自身が実ツリーの writer になる [測定の交絡]

- 事象: `orchestrator/tests/conftest.py` は明示 `TMPDIR` を無条件に尊重し、
  `tools/pegasus/dispatch_compute.py` も親環境を継承する。`TMPDIR` が実 repo の `output/` 配下を
  指すと、T-080 E2E fixture の `tempfile.mkdtemp` と pytest の `tmp_path` が実 `output/` へ
  untracked file を作る。同 fixture は `git ls-files --others` で `output/` を列挙して copytree
  するため、自己包含と、他 worker の作成・削除による偽赤が起きる。
- 根本原因: 一時 root の位置に対する境界がどこにも無く、fixture が「読む対象」と「書く場所」の
  分離を前提にしていた。
- 恒久対応: (部分) fixture 側に境界検査を置き、**module import 時**に `TMPDIR` / `TEMP` / `TMP` と
  `tempfile.gettempdir()` が実 `output/` 配下なら fail-closed する
  (`orchestrator/tests/test_s8b_oracle_driver.py` の
  `_assert_t080_import_temp_environment`)。pytest が `tmp_path` を作る前に発火する。
  負例は `ROOT/output` の前後 snapshot を比較して無副作用も固定する。
  変異事前登録 MUT-7 (境界検査の無効化) が発火を確認する。
  **受入環境側で temp root を admission する層は未実装で、ユーザー裁定へ返す。**
- 再発検知: 上記 import 時境界検査と MUT-7。
