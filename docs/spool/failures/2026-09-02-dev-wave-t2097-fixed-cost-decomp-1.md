---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2097-fixed-cost-decomp
seq: 1
---

## 新規

### {{F:probe-injection-perturbed-suite}}. 計測 probe の置き場と注入方法が測定対象そのものを壊した [計測汚染]

- 事象: 受入 1 shard の残差を測る probe を計算ノードへ投入した 2 回とも、対象の走が赤で止まった。
  1 回目 (job 966024) は probe 2 file を worktree 直下に置いたため
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` が
  未追跡 file を検出して落ち、10 arm 中 1 arm で停止した。2 回目 (job 966221) は probe を repo 外へ
  移した後も `PYTHONPATH` と `PYTEST_PLUGINS` を注入したため、実行環境を検査するテストが落ちた。
  対照 arm の赤 3 件に対し計装 arm は 56 failed + 2 error (`test_run_tests_preflight.py` 47 件ほか)。
- 根本原因: (a) 置き場の判断を「特定 directory を避ける」で行い、**作業ツリー全体**を走査する
  検査の存在を確認しなかった。(b) plugin を読み込ませる手段として環境変数を使い、その環境変数が
  production の実行環境の一部として検査される対象であることを確認しなかった。
  どちらも「probe が測定対象へ与える影響」を推定で済ませ、実測で確かめる前に本走へ投入した。
- 恒久対応: probe は repo 外に置き、plugin の import 直後に注入した環境変数を production の姿へ
  復元する。復元できたかを process ごとに検査して記録する
  ({{D:residual-is-startup-collection}} の測定はこの形で成立した)。
- 再発検知: 計装 arm と対照 arm の**赤 nodeid 集合の一致**を測定の受理条件に含める。
  一致しなければ、その計装値は測定対象を代表していない。

### {{F:compute-node-openssl-dependent-red}}. 受入の赤が当たった計算ノードの openssl 版で変わる [テスト代表性]

- 事象: `test_mocc_trace_pair.py::test_anchor_v3_accepts_external_signed_pin_manifest` と
  `test_anchor_v3_rejects_invalid_external_pin_signature` が bnode011 / bnode013 / bnode032 で
  `pkeyutl: Option unknown option -rawin` により落ちる。基準走の bnode026 では通っていた。
- 根本原因: 同テストが `openssl pkeyutl -rawin` を能力判定なしで呼ぶ。`-rawin` は OpenSSL 3 系の
  option であり、上記 3 機体は 1.1.1q である。計算ノードの openssl 版が均一でない。
- 恒久対応: 未着手。**本 wave の scope 外なので直していない。** 対処方針 (能力判定して skip するか、
  署名経路を版非依存にするか、機体側を揃えるか) は裁定が要る。
- 再発検知: 受入 artifact に実行機体の `openssl version` を残せば、機体依存の赤を実行差分と
  取り違えずに済む。本 wave の probe は arm ごとにこれを記録している。
