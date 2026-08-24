# [T-1618] xdist controller の 2 経路を分離計測した — 結論と限界

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は探索の妥当性文書
(measurement record) であり、裁定台帳ではない。実行手順と成果物構成は同 directory の
`README.md`、機械可読な正本は `measurement-summary.json` と `measurement-result.json.gz`。

- 起点: `docs/archive/worklog-phase3-0824-886-887.md` entry 887 の T-1618、裁定正本 D746 / D747
- 採用した走: Pegasus gen_S 計算ノード `bnode068`、PBS `0:944810.nqsv`、48 CPU、
  pytest-xdist 3.8.0 (`/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist`)、wall 658 秒
- raw result SHA-256 `312c2560097872d7aa942f4aa3b73580ba83e5cba94c7d92715222fc7968eec9`
  (`measurement-result.json.gz` を展開したもの。親が `gzip -dc | sha256sum` で確認済み)

---

## 0. 一行で

**問われた 2 経路は、61.3 秒の残差を説明しない。** 合わせて約 3.9 秒である。

---

## 1. 何を測ったか

xdist の `LoadGroupScheduling` を実物のまま import し、48 worker の実行を event driven に
replay して、次の 2 経路の CPU を分離した。

- **(A)** `_assign_work_unit` 内の `worker_collection.index(nodeid)` の線形探索
  (`xdist/scheduler/loadscope.py:277`)
- **(B)** `_pending_of` の累積再走査 (同 `:308`)

値は **replay 上で当該実装を O(1) 版へ置き換えたときの CPU 削減量**であり、
「その関数が消費した総 CPU 秒」ではない。field 名も
`marginal_replay_cpu_saving_vs_o1_control_s` としてある。

30 独立ペア、120 sample、ABBA / BAAB 均衡、95% CI。negative control は
CI gate と order gate の両方を通過した (雑音 0.0001 秒台に対し効果は 0.79 から 3.54 秒)。

## 2. 実測値

### (A) `worker_collection.index()`

| controller | N | slot probe 数 | marginal CPU (秒) | 採否 |
|---|---:|---:|---:|---|
| K=1 groupmap 順 (条件付き) | 14467 | 104,654,278 | **1.794** | 非採用 |
| K=1 production reorder (D746 順) | 14467 | 104,654,278 | **3.537** | 非採用 |
| K=2 shard-0 | 7552 | 28,520,128 | 0.786 | 採用 |
| K=2 shard-1 | 7551 | 28,512,576 | 0.790 | 採用 |

K=2 の合計は 1.576 秒 (95% CI 1.566 から 1.587)、最大 shard は 0.790 秒。

### (B) `_pending_of`

K=1 production reorder / protocol-only の呼び手別内訳。

| 呼び手 | marginal CPU (秒) | 呼出し回数 | status |
|---|---:|---:|---|
| `_reschedule.protocol_complete` | **0.3911** | 14,368 | measured-practical-effect |
| `tests_finished` | 0.0073 | 167 | measured-practical-effect |
| `remove_node` | 0.0051 | 48 | measured-practical-effect |
| `_reschedule.initial` | 0.0006 | 48 | inconclusive-ci |
| `has_pending` | 0.0006 | 48 | inconclusive-ci |
| 総量 (all-real − all-oracle) | **0.3928** | | |

呼び手別の値は**加法的内訳ではない** (`caller_values_are_additive_breakdown=false`)。

controller 別の総量は K=1 が 0.365 から 0.422 秒、K=2 が shard あたり 0.095 から 0.114 秒。

### 独立再現

同一 harness を**別の計算ノードで 2 回**走らせた。値は 1 から 3% 以内で一致する。

| 量 | 走 1 (`bnode120` / `0:944585.nqsv`) | 走 2 (`bnode068` / `0:944810.nqsv`) |
|---|---:|---:|
| (A) K=1 groupmap 順 | 1.778 | 1.794 |
| (A) K=1 production reorder | 3.530 | 3.537 |
| (A) K=2 shard-0 | 0.783 | 0.786 |
| (A) K=2 shard-1 | 0.788 | 0.790 |
| (B) K=1 production reorder | 0.381 | 0.393 |

採用したのは走 2 である (走 1 は採否表現に不整合があり、その修正後に走り直した)。
slot probe 数は両走とも完全に同一である。

## 3. 結論

**(A) と (B) は 61.3 秒を説明しない。** K=1 の実 production 順で
(A) 3.54 秒 + (B) 0.39 秒 = 約 3.9 秒である。(A) は (B) の約 9 倍。

なお **61.3 秒は独立に観測された費目ではない。** `229.41 − 12.86 − 155.3` の算術残差であり、
うち 155.3 秒は固定 duration 上の反実仮想 model の出力である。model が 10% ずれれば残差は
45.7 から 76.8 秒へ動く。したがって本文書は「61.3 秒のうち X 秒」という割合を主張しない。

## 4. 副次の発見 3 件

### 4.1 slot probe 数は順序不変だが、時間は順序不変ではない

両 K=1 条件の slot probe は **完全に同一の 104,654,278** である
(= N(N+1)/2、N=14467)。各 nodeid はちょうど 1 回 target になり、そのとき自分より前の
全要素と比較されるため、比較 pair の集合は全順序対そのもので順序に依存しない。

**ところが CPU は 1.794 秒と 3.537 秒で約 2 倍違う。** 比較 pair の集合が同じでも
1 回あたりの費用が違うということで、原因は identity shortcut の配分、cache locality、
分岐予測のいずれかである。本 wave はどれが効いているかまでは決めていない。

**D746 の所要降順は (A) を安くしない。約 2 倍高くする。**
この向きは wave 開始時の親の推測とは逆であり、段 3 の 2 レンズが独立に反証したうえで
実測が確定させた。

### 4.2 (B) の支配項は tail ではなく `_reschedule` である

`tests_finished` は `loop_once` の全 event 後に評価されるが、
`if self.workqueue: return False` で早期脱出する。実測では property 評価 14,611 回のうち
**14,368 回が workqueue 非空で即 return** し、全 worker を走査したのは **8 回だけ**だった。
`workers_scanned_by_event` はほぼ全部 1 である。`has_pending` の scope 走査は 0。

支配項は `_reschedule.protocol_complete` の 14,368 回・2,150,441 scope 走査で、
path B の約 99.6% を占める。**tail の走査は 0.0073 秒しかない。**

### 4.3 K=2 は (A) を shard あたり半分以下にする

K=2 では shard ごとに独立した 48 worker の controller が立つ (24 + 24 ではない)。
slot probe は `Σ n_i(n_i+1)/2` で決まり、実測合計 57,032,704 は K=1 の 54.5% である。
wall に効くのは最大 shard の 0.790 秒。

一方 (B) は一律には縮まない。`has_pending`、正常終了の `remove_node`、tail の
`tests_finished` は controller ごとに発生して二重化するためである。

## 5. 採否と限界

- **`status = reference-only-isolation-unverified`、`authoritative = false`。**
  gen_S は Exclusive submit が OFF で、48 CPU の割当は専有の証拠にならない。
  単独性を証明できないので、値は参考値である
- **K=1 の 2 controller は非採用。理由は 2 つある。**
  (1) **order-effect gate が落ちた。** ABBA block 差から BAAB block 差を引いた系統偏りが
  事前登録した絶対雑音幅 +-0.010 秒に収まらなかった。
  `adoption_gate_results` で落ちている gate は `primary_order_effect` の 1 つだけであり、
  他の 6 gate は通っている。**偏りの大きさは 0.02 秒で、path A の値 1.794 秒と 3.537 秒に
  対して 1% 未満である。1.74 秒の差 (約 2 倍) を覆す量ではない。**
  K=2 の 2 shard は同 gate を通過している
  (2) 歴史的参照走の collection 順を同一 command・HEAD・plugin hash で束縛できていないため、
  `groupmap-order conditional` として扱い歴史値への接続を禁じている
- **K=2 の path B は非採用。** occupancy の exact 一致に失敗した。
  group 割当は両 shard とも完全一致し、item 数の min も一致、median も近いが、
  48 件の完全一致には至らない。実走の割当は実所要のばらつきと worker の完了順に依存し、
  replay は台帳の固定所要を使うので、これは予期される。
  **許容幅は設けなかった** — いま数値を通すために事後に幅を決めるのは
  正しさゲートを緩める方向だからである。差分は raw result に全部残してある
- **K=2 の path A は採用。** aggregate 1.576 秒 [1.566, 1.587]
- **値は CPU であって wall ではない。** replay は worker の実行・execnet・OS pipe・
  pytest hook・terminal 描画を含まない。compressed replay は hot cache 寄りである
  (`hot_replay=true`)。CPU 秒をそのまま wall へ足せない
- **(B) の実 event 列は復元できない。** `tests_finished` の評価回数を決める
  report / warning / logstart / logfinish の到着順は残っていない。
  protocol-only と pass-event を別 scenario として測ってある
- **D747 の「安いテストを減らしても wall に効かない」は本計測では閉じない。**
  削除は (A) の後続位置も (B) の unit 数・event 数・tail も同時に変えるので、
  全件で測った合計から削除後 wall は導けない

## 6. 次の一手 (harness が機械生成した)

`decision_rule.selected_next_experiment = prototype-o1-index-and-run-causal-k2-wall-ab`

K=2 の path A 集計の CI 下限 1.566 秒が事前 threshold 0.5 秒を上回ったため。
ただし `wall_improvement_claimed = false`、`d747_claim_closed = false` である。
**wall がいくら縮むかは因果実験でしか決まらない。**

## 7. 再現

    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/measure.py --pilot
    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/submit_t1618.py

pilot は login node で 10 秒程度、本計測は計算ノードで 660 秒程度。
入力・source・xdist の hash 束縛と単独性証拠は raw result に入っている。
昇格は `promote_result.py --attempt-id <id> --job-id <pbs>` で行い、
生成直後と昇格直前の両方で JSON Schema と leaf からの採否再計算を通す。
