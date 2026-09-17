---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2293-d2104-docs-addenda
seq: 3
title: [T-2293][T-2687][T-2688][T-2692] D2104 項 3 / 21 / 22 / 30 の追記・手順改訂 — D1875 と D922 の追補 D、rc 表の indeterminate、DW-O18 から hold 登録の一般手順を取り下げて check_docs の pin を追随 (docs + pin 追随、branch worktree-dev-wave-t2293-d2104-docs-addenda、変異 matrix = baseline PASSED・負例 4/4 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「裁定済み D2104 項 3 / 21 / 22 / 30 の 4 件を 1 wave で docs のみ処理する。(a) D1875 の予算 1 を D410 の 2 と
  追記で訂正 (Q2〜Q4 は着手しない)、(b) D922 点 4 を負判定に限定、(c) rc 表へ indeterminate → rc=2、(d) DW-O18 から hold 登録の
  一般手順を取り下げ (削減方向)。決定台帳は fragment、規律 2 を緩めない、本題の 4 追記だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2293-d2104-docs-addenda/README.md`。設計判断は
  {{D:d1875-approved-generation-budget-two}} (D1875 の追補) と {{D:d922-candidate-limit-keeps-positive-proof}} (D922 の追補)。
  F1000 の恒久対応を supersede 追記で確定。統合 commit `76aad5e4c` (docs 4 箇所 + fragment 2 本 + `tools/check_docs.py` の
  DW-O18 逐語 pin + `orchestrator/tests/test_check_docs.py`、Codex author)。
- **引数の前提を覆した新事実 (段 1 実測):** DW-O18 は `tools/check_docs.py` に逐語 pin され、契約 test の合成 fixture・byte 固定
  assert (997)・変異 needle M2 / M11 が旧文言に依存する。「docs のみ」では (d) を満たせないため、pin 追随の 2 file だけを
  Codex author に書かせた (D95)。実装 (`check_branch_landed.py` / `check_branch_rescue.py` / `flaky_test_holds.py`) は不変。
- 段 3 相談 (1 本): real 2 — D922 追補が「期限」にまで正判定優先を一般化していた (deadline は別経路で走行全体を
  `indeterminate` にする) → 射程を候補上限超過に限定、byte assert 997 → 995 の追随漏れ → author prompt に含めた。refuted 5。
  DW-O18 は裁定の逐語「その 1 件の pin 更新を個別に諮る」へ寄せ「上記の制限内で」を足して 997 → 995 bytes。
- 段 6 レビュー 2 本: B (docs 忠実性) GO・must-fix 0・nit 1 (D1875 の残り 3 件と T-2293 の Q2〜Q4 を同一視した説明 → fragment を
  訂正)。A (pin 追随) は launcher が 2 attempt とも `event_invalid` (子が 12,857 行の test file を `cat -n` で全文出力) で
  不受理 → 巨大 file の全文出力を禁じて再投入 (reviewA-2): accepted、GO・must-fix 0・nit 1 (author 報告の check_docs 1 件は統合前の時点差、insight で区別)。未受理版の nit (「各 1 回」→「各 2 回」の負例)
  は変異 M4 として probe 前に登録した。
- 実走: 焦点走 7 file (計算ノード 3992.nqsv) 1245 passed / 8 skipped / 42.3 秒 (skipped は growth hold)、check_docs 違反なし、
  spool_fold --dry-run rc=0、全史 provenance 11,076 件・新規違反なし。
- **変異 matrix (container worktree `.codex/worktrees/t2293-addenda-mutcontainer` = 76aad5e4c、`run_tests.py orchestrator/tests/test_check_docs.py`、
  対象は `tools/check_docs.py` の DW-O18 literal だけ):** probe (観測 node 収集) → 本走 (spec sha256 `d71e8a8c…`) は baseline PASSED (32.4 秒)、負例 4 件 (M1 登録禁止の反転 329 / M2 個別相談句の削除 330 / M3 再投入句の削除 330 / M4 各1回→各2回 329) すべて KILLED で期待 node と観測 node が完全一致 (matching 5/5)、等価 M0 (literal の隣接 2 文字列分割) SURVIVED、MISMATCH 0、TIMEOUT 0、全 anchor 1 箇所。M2 / M3 の +1 は `test_non_attributable_landing_contract_mutations_have_one_finding[M2]` / `[M11]` の専属 kill。各件数は job stdout の `failures=` と一致 (中継上限の欠落なし)。
- 工数: codex 子 5 本 (受理 4) (consult 1、author 1 (+ rc=2 未起動 1: 未 commit の authority docs)、review 3 (reviewA-1 は 2 attempt とも不受理、reviewA-2 と reviewB-1 が受理)、全段 `gpt-6-astra` / `medium`)。
  親の実測: 焦点走 1、provenance full 1、変異 2 走 (probe + 本走)、受入は land 前に 1 回。

## 次の一手差分

### 完了

- [T-2687] D2104 項 21 の追記手番を完了した。D922 点 4 の候補上限超過の扱いを限定し、照合済みの正証拠の `landed` を維持する
  追補 D ({{D:d922-candidate-limit-keeps-positive-proof}}) を記録した。実装は不変。
  remaining: none
  base: cbbede622f9e6545f9d198f6ffa6d95e3b7faa55e175c9f11966dcc1689a9457
- [T-2688] D2104 項 22 の追記手番を完了した。`docs/unreachable-object-ledger.md` の rc 表 `2` 行へ「landed 判定に `indeterminate` が
  1 件でもある場合を含む (D1231)」を追記した。
  remaining: none
  base: 90431049bfb4978d255213861d26f581b1260d5ac4b08f8d950829078242d0e0
- [T-2692] D2104 項 30 の手順改訂手番を完了した。`DW-O18` から hold 登録の一般手順を取り下げ (997 → 995 bytes)、`tools/check_docs.py` の
  逐語 pin と契約 test を追随させ (Codex author)、F1000 の恒久対応を supersede 追記で確定した。
  remaining: none
  base: c415c56a3dc26a3cd097a108f4d08cbb809a3f527c813b128dd152e54faeed07

### 更新

- [T-2293] **P1・Q1 着地 → Q2〜Q4 は保留維持、前提の追記訂正は完了 (D2104 項 3)**: D1875 の「承認済み generation 予算 1」を
  D410 の 2 (実装 `MAX_APPROVED_GENERATIONS = 2`) と訂正する追補 D ({{D:d1875-approved-generation-budget-two}}) を記録した。
  整合のもう一方 (還流設計 D106 残余 1) は未解決のままなので Q2〜Q4 (production FSM・起点専用 entry point・completion / report の
  起点分岐) は着手しない。一括承認はしない。
  base: c76321370bc074f6b9ef4a2afae05e78d40e34e1e5c60a718e10fac0388c55f6
