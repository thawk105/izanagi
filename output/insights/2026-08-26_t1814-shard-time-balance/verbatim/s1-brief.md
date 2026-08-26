# 段 1 brief — [T-1814] 受入分割 (K=2) の時間不均衡

wave: `dev-wave-t1814-shard-time-balance` / base main `9463bcbcb1541625db59abb97cf6a76934b4c80c`

## scope

1. **同一 tip で K=1 と既定 K=2 を並べて測り、4 層 (queue 待ち / job Elapse / pytest wall /
   外側 wall) を D713 どおり分けて記録する。**
2. **junit の duration を重みにした shard 割付の実装可否を判断する。** 実装するなら
   `tools/acceptance_shards.py` の `allocate()` と付随テストだけ。実装しないなら判定式と
   実測を decisions へ記録する。
3. scope 外: [T-1589] 適応 K、K の既定値変更 (D724)、排他鎖そのものの短縮 (D532 (a)(b))、
   台帳 `orchestrator/tests/acceptance_duration_ledger.json` の再生成。

## 確定済みユーザー裁定 / 上位裁定

- 目標は 5 分以内 (テスト実走と帰属判定の合計。順番待ちは含めない)。
- D713: 4 層を分けて計上。`直列総和 / (48K)` を下界と呼ばない。
- D531: junit duration は共走の競合を含む。前走の重みを硬い予測にしない。
- D724: K の既定は Pegasus LOGIN の受入形で 2。本 wave は既定 K を変えない。
- D746: 走内の投入順は既に所要降順。台帳と読み手は実在する (下表)。
  **D531/D532 の「所要による並べ替えを採らない」は走内投入順についての旧裁定であり、
  D746 が改訂済み。本 wave が触るのはその 1 つ外側の shard 割付という別の層である。**

## 親が実測した前提 (一次資料 = 参照走 `4b40d17f` の shard session)

- 控えの機序主張は**確認された**。`allocate()` は `weight = len(nodeids)` で bin-packing する。
- 直列総和 (junit) は shard-0 = 4215.5 秒、shard-1 = 3257.0 秒。**要素数が完全に均等でも
  仕事量は 958.5 秒 (12.8%) 偏っている。**
- しかし **shard-0 の wall を決めているのは偏りではなく排他鎖である。** `real-repo`
  xdist_group が 1 worker (gw0) を **210.5 秒 / 72 件**占有し、これは分割不能。
  shard-0 の pytest wall 266.89 秒 = 210.5 + 固定費 56.4 秒。
  鎖以外の最遅 worker は 149.4 秒で、鎖より 61 秒短い。
- 4 層: queue 待ち 10 / 8 秒、job Elapse 279 / 182 秒、pytest wall 267.21 / 171.50 秒。
- 台帳による重み付き再割付をオフラインで再現したところ、選択数は 8000/6900 へ動き
  直列総和は 3752/3752 へ揃うが、**gw0 の 210.5 秒は動かない。**

## 親の provisional 裁定 (攻撃対象)

- **(P1)** makespan 模型は `wall_s ≈ 固定費 + max(鎖_s, work_s/48 の LPT 裾)`。
  参照走の 2 shard で残差 56.4 / 39.2 秒。
- **(P2)** `鎖 ≥ 総仕事量 / (48·K)` が成り立つ間、K を上げても分割を balance しても
  makespan は下がらない。参照走では 210.5 ≥ 7472.5/(48x2) = 77.84 で既に成立しており (**初版は分母の K を落として 155.7 と書いた。段 4 で訂正**)、
  **duration 重み割付の期待利得は 0〜17 秒**と見積もる。
- **(P3)** よって scope 2 の既定裁定は「実装しない」。ただし scope 1 の同一 tip 実測が
  (P2) を否定したら覆す。**実測前に確定しない。**
- **(P4)** 実装するなら変更面は `_components()` の `weight` 1 箇所で足り、台帳の読み手は
  D746 と同じ `conftest` 経路を再利用できる。

## 不変条件 (緩めない)

- 受理集合不変。shard の union は全 node、重複なし (`assignment_closure_gate`)。
  テストの削除・skip・selection 縮小で速くしない (規律 2、D747)。
- 台帳が不在・破損・部分欠落でも要素数 packing へ静かに縮退し、選択・skip・受理判定の
  入力にしない (D746 の 5 と同型)。
- 全 shard が同じ割付を独立に導く決定性を保つ。`validate_report_evidence` を緩めない。
- `effective_scheduler` の exact 束縛 (D390/D393)、受入 receipt の argv exact pin、
  既定 K (D724) を変えない。
- 台帳を再生成しない (`test_t1574_changed_suite_ledger_node_delta_is_exact` の exact 差分を
  巻き込む)。

## 成果物影響 (DW-G05)

certified 選択・レポート・試行台帳の値・受理集合・参照は**どの選択肢でも変わらない**。
本 wave が動かすのは受入全走の所要だけである。実装しない場合の影響は
「受入 wall が鎖律速のまま 267 秒級で残る」であり、成果物の値は 1 つも変わらない。

## 成果物の形

- scope 1: 4 層の実測表 (worklog + insights)。
- scope 2: 実装 (`tools/acceptance_shards.py` + テスト) か、decisions の判定式。
- 変異事前登録は段 4。実装差分ゼロでも受入全走は免除しない (DW-S04)。

## 並列分割方針

設計択一 (実装する / しない) が割れうるため軽量版にせず、段 2 (plan) と段 3 (敵対 2 レンズ) を
回す。実装面が出たら段 5 は Codex `role=author` 1 単位 (`tools/acceptance_shards.py` 所有)。
`tools/run_tests.py` は T-1719 / T-1563 が編集中なので触らない。

## 環境

受入・実測は Pegasus LOGIN から計算ノードへ dispatch。所在は worklog、機体固有は環境 runbook。
