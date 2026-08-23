---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-t080-e2e-optin
seq: 1
---

## {{D:t080-e2e-optin-removal}}. T-080 stub-free E2E の opt-in を撤去し受入全走へ戻す

**決定:** `orchestrator/tests/test_s8b_oracle_driver.py` の T-080 stub-free E2E
(6 function / 展開後 11 nodeid) の `IZANAGI_T080_E2E=1` opt-in を機構ごと撤去し、
既定の受入全走で実行する。opt-in のまま「いつか回す」で残す形は採らない。

**理由:**
- **opt-in にした理由は既に解消している。** 導入 (commit fe34c90f、2026-08-12) の理由は
  依存物の不在ではなく実走コストで、fixture 構築 1 回 213.40 秒・4 key 合計 899.69 秒だった。
  その律速は T-080 receipt 履歴検査の per-commit git 起動であり、**同じ wave の D313 が
  batch 化して畳んでいる。**
- **走らないテストは実際に腐った。** 11 日間走らなかった間に 2 件が赤になった。原因は両件とも
  同日の裁定 `rulings-4th-batch-2026-08-12` が入れた凍結検証保留への追随漏れで、
  片方は同じテストの他 2 枝が保留対応済みなのに 1 枝だけ取り残される部分適用だった。
  **opt-in にしていなければ当日に露見していた。**
- **費用は予算内である。** 計算ノード gen_S の xdist 実測で、11 nodeid の call 時間合計は
  492.17 秒 / 最長単一 nodeid 51.43 秒。対象は排他 group に属さないため排他鎖に載らず、
  既存の最長単一テストより短い。
- 数値目標の扱いは D312 に従う。閾値の跨ぎで設計を決めず、閾値のために検査を弱めない。

**却下した選択肢:**
- **受入とは別 gate で定期実行する** — 定期実行の基盤が repo に無い (D220)。本 wave で
  現在の repo を独立走査して再確認した (hook のみで CI / cron / timer は無い)。
  作れば opt-in の改名にしかならず、「走らないテスト」を別名で残す。
- **検出力が重複しているとみて削除する** — 直接 helper 検査は実 repo・public `verify_receipt`・
  public driver gate を通す E2E と受理集合が異なる。部分削除でも受理集合を実際に縮める。
- **`REAL_REPO_SERIAL_NODES` へ 11 nodeid を登録する** — 登録すると展開後 11 node 全部が
  単一 worker へ直列化され、その worker が critical path になる。受入予算と両立しない。

## {{D:t080-default-execution-probe}}. 既定実行の保証は静的 decorator 監査でなく実測 probe で行う

**決定:** 重いテスト群が既定で走ることの保証は、AST による decorator 監査ではなく、
**既定 collection を実際に走らせて対象 nodeid が選択され setup へ到達することを実測する
positive control** で行う。AST による consumer 集合と parametrize 値の exact pin は併置して残す。

**理由:**
- 静的な decorator 監査は関数 decorator しか見ない。module 冒頭の `pytestmark`、
  定義後の `.pytestmark` 代入、`GROWTH_TEST_HOLDS` 登録、conftest の
  `pytest_collection_modifyitems`、autouse fixture / `pytest_runtest_setup` の `pytest.skip()`、
  deselect、`pytest.param(marks=...)` は**すべて素通りする**。
  同じ群が既に一度腐っている以上、素通りする経路を残す保証は意味がない。
- 判定は子 pytest の rc ではなく **report の内容**で行う。全 node の rc を対象 node の判定へ
  流用すると、無関係な setup 失敗で受入全体を赤にする過剰拒否になる。
- probe は実履歴・共有 submodule を読むため、**probe の node だけ**を実 repo 直列群へ登録する。

**主張の限界 (これ以上に強く書かない):**
- probe の子環境は受入全走の xdist worker 環境と同値ではない。**受入環境に固有の条件で
  黙らせる細工は probe を通る。** 受入そのものでない probe に受入での実行を証明させることは
  原理的にできない。保証の範囲は「既定 collection での沈黙の検出」に限る。
- probe は `--setup-only` なのでテスト本体を実行しない。**本体の骨抜き
  (先頭 `return`、本体内 `pytest.skip()`) は検出できない。** 骨抜きを検出する機構は変異 matrix である。
