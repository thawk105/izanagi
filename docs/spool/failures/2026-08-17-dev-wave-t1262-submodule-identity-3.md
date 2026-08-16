---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1262-submodule-identity
seq: 3
---

## 新規

### {{F:force-color-leaks-into-test-subprocess}}. 親セッションの FORCE_COLOR が子 process の出力を汚し無関係な node を落とす [環境汚染] [偽赤]

- 事象: 焦点走で `test_growth_test_holds_contract.py::test_plain_pytest_delegating_runner_is_not_over_rejected`
  が 1 件だけ落ちた。この node は `orchestrator/tests/test_env_attestation.py` を subprocess として
  起動し、その出力を `(\d+) passed(?:,| in )` で照合するが、出力が
  `\x1b[1m103 passed\x1b[0m, ` の形になり "passed" の直後に reset 列が挟まって正規表現が外れた。
- 根本原因: Claude Code の背景 job 環境が `FORCE_COLOR=3` を export しており、それが
  `run_tests.py` → pytest → subprocess pytest まで継承される。pytest は pipe 出力でも
  `FORCE_COLOR` があれば着色する。**差分にも repo にも原因はない。**
- 恒久対応: 焦点走・受入走を起動する script で `env -u FORCE_COLOR -u COLORTERM` を前置する
  ({{D:submodule-raw-bytes-identity}} の wave で実測により確立)。
  memory `report-progress-every-10-minutes` と同じ層の運用規律として
  `docs/dev-wave/operations.md` の親テスト節 (`DW-O18`) へ寄せる候補。
- 再発検知: `env -u FORCE_COLOR` を外した走行で当該 node が落ちることを実測で確認済み
  (同一 checkout・同一 commit で色あり/色なしを 1 回ずつ実行し、前者だけが落ちる)。

### {{F:seal-time-inventory-hits-post-seal-allowlist}}. 封緘前の repository へ封緘後用の判定を当てて 66 node を落とした [順序誤り] [信頼境界の取り違え]

- 事象: 段 6 の fix 1 巡目で local config の allowlist 検査を repository 列挙処理へ移した結果、
  計算ノードでの焦点走が `66 failed / 545 passed / 3 errors` になった。理由はすべて
  `snapshot repository local config is not allowlisted: <path>: ['branch.*', 'remote.*', ...]`。
- 根本原因: 封緘処理は**自分が config section を削除する前に** repository を列挙する。
  そこへ封緘後用の厳格な allowlist が当たると、まだ正当に残っている transport 設定で必ず落ちる。
  **認証の境界は封緘処理ではなく検証時点である**という区別が実装に無かった。
- 恒久対応: {{D:submodule-config-allowlist-seal-boundary}} — 封緘前後で allowlist の厳しさを
  分け、封緘処理だけが builder 側の緩い集合を使う。外部 program を起動しうる key は封緘前でも拒否する。
- 再発検知: 封緘前の木に対して列挙しても allowlist が誤発火しないこと、かつ封緘後の同じ木では
  transport key が拒否されることを、単独理由で固定する node を置いた。
