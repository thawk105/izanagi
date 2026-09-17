# Coder Leakproof Context — Phase 3 Segment 4

**このファイルは coder agent に直接渡す。勝ち筋値・利得・性能数値は物理削除してある。**

---

## Background: CCBench と Backoff 軸

**CCBench** は並行制御 (Concurrency Control) ベンチマーク。複数ベンチマークアルゴリズム (SILO, Masstree, Tictoc, Cicada など) が提供され、各々の「abort を許す代わり restart を高速化する」戦略を測る。

**Cicada** = CC の一種 (in-memory OLTP 用)。abort 時に **adaptive exponential backoff** を使用 — 各トランザクションが restart 前に「待機時間」を挟み、その間に競合が落ち着くのを期待する。

**SILO** = Cicada と似た in-memory OLTP CC。Cicada と異なり backoff はよりシンプル。

**Backoff 軸** = CCBench で SILO の backoff パラメータを変える。「abort 後の待機時間が長い/短い」で throughput-latency tradeoff が生じる。

---

## Segment 4 の目標

Backoff 値をチューニングして、**既知の baseline より性能を改善する** のか、それとも **baseline が既に最適に近い** のかを検証する。

coder は planner からの「方向ヒント」(値ではなく「増やす」「減らす」「両方試す」) を受けて、具体的な backoff 値を提案し、その値が実測でどう効くかを検証する。

---

## Backoff の直感的理解

- **abort が多い (contention が高い) workload**:
  - abort 後、競合相手 (lock holder) が同じ resource に急いでアクセスし直す可能性が高い
  - →「少し待つ」ことで「競合相手の実行が終わるのを期待」できる
  - →「待機時間が長い」と競合が減り、スループット ↑

- **abort が少ない (contention が低い) workload**:
  - abort そのものが稀 (ほぼ競合なし) なため、待機時間を増やしてもメリットない
  - →「待機時間が短い」が latency penalty が小さく、スループット ↑

---

## Cicada の適応メカニズム (参考)

Cicada は実行中に abort 率を観測し、backoff を自動調整する。

- abort 率が高い → backoff を増やす (exponential)
- abort 率が低い → backoff を減らす

この適応は「ある workload に対して収束する傾向」を持つが、**最適値は workload の特性に依存** する。

Segment 4 は「Cicada の適応では到達しない値」や「別の backoff 値の方が性能が出る」可能性を調査する。

---

## Measurement Setup (coder が参考にする workload 定義)

適用版: 2026-09-17 改訂以降に開始する走行。`orchestrator/campaign/p3_s4_loop.py` の `default_perf()` (bench) と、
段 4 の 3 driver の verify 構成に一致させてある。それ以前に開始した走行の入力は当時の版であり、
本改訂で読み替えない。

### Standard Contention Workload (bench、配線規模)
```
100k_records / t4_threads / skew0.9_zipfian_access / rr50_readratio /
rmw0_readmodifywrite / max_ope10_ops_per_tx / extime1_execution_time_seconds / reps2
```

解説:
- `100k`: 100,000 レコード の key-value store
- `t4`: 4 スレッド で実行
- `skew0.9`: Zipf 分布の skew 0.9 (少数の hot key へ access が集中する高 contention)
- `rr50`: 操作の 50% が read、50% が write
- `rmw0`: read-modify-write を無効にし、write は blind write
- `max_ope10`: 1 transaction あたり 10 操作 (CCBench の既定値)
- `extime1`: 1 rep の計測時間 1 秒
- `reps2`: 1 測定あたり 2 rep

これは kickoff と同じ配線規模であり、性能比較用に calibrator が決めた規模ではない。性能比較に
入る段では、calibrator が決めた records / threads / reps に差し替えられる。

### Measurement Methodology (coder の提案値は以下で検証される)

1. **Build:** 提案値を hole へ挿入して build する (trace 版と perf 版の 2 本)
2. **Verify:** verifier が trace 版の correctness trace を読み、serializability を検査する。
   段 4b (backoff 軸) は小規模高 contention の correctness workload (200 records / 4 threads /
   rmw / max_ope 5 / extime 1、1 rep)。sort 軸と trigger-gating 軸は、それに加えて S2 構成
   (1m records / 48 threads / extime 3) の pass も通す。**anomaly が出た候補は即 reject であり、
   性能は測られない**
3. **Bench:** perf 版を上の workload で 2 rep 計測する。安定性判定により再計測されることがある
4. **Result:** 有効な rep の throughput の中央値 (2 rep なら算術平均) を代表値とし、baseline と
   比較する

---

## Whiteboard Memory (coder が参考にできる評価済み提案)

段 4 では以下のような記録が whiteboard に蓄積される (planner が提案時に参考)：

```
[評価済み提案 (値なし、理由のみ)]
- 提案 1: 方向「増加」「magnitude small」→ 実装: ...→ 結果: 棄却 (理由: contention 低い workload では効果なし)
- 提案 2: 方向「増加」「magnitude medium」→ 実装: ... → 結果: 棄却 (理由: 別の軸 (lock-sort) の方が効果大きい)
- 提案 3: ...
```

**記録されない内容:**
- 具体的な値 (50, 65, 100 など) — 値を見ると「この値が出た」が「答えを読んだ」に化ける
- 性能差分 (+0.5%, +2%, など) — 利得を見ると同様
- 「stock 適応が X us で安定」などの機序 (勝ち筋の説明)

---

## Coder への指示 (prompt template)

```
以下の情報を用いて、backoff 値の提案を考えてください：

1. Template 仕様: [エージェント定義 (coder-v4-autonomous.md) の出力節 — axis=silo-backoff-magnitude の場合、implementation は `double now_backoff = <value と数値一致する接尾辞なしの数値 literal 1 個>;` の**ちょうど 1 文** (D836 / D901 条項 1)。計算式・呼び出し・括弧・後続の文は受理されない]
2. Planner の方向ヒント: {direction} / {magnitude} (「増加」「低下」「両方探索」)
3. Leading indicators: [メインセッションが射影した leading_indicators (JSON inline)]
4. 現行 baseline: [メインセッションが射影した baseline (JSON inline)]
5. 評価済み提案: [whiteboard の却下設計・ただし値なし]

出力: 
{
  "proposal": {
    "axis": "silo-backoff-magnitude",
    "value": <数値>,
    "justification": "...",
    "implementation": "double now_backoff = <数値 literal 1 個>;",
    "confidence": "high" | "medium" | "low"
  }
}

禁止事項:
- output/docs/insights の参照 (段 3/段 4 の実験結果を見ない)
- decisions.md や phase3.md の「この値が best」という記述の参考
- 過去 campaign の WAL や grid fitness (「この値の neighborhood を explore」となり coder の自律性が失われる)
```

---

## 段 4 の検証サイクル

1. **planner:** leading-indicator を見て「増加」「低下」の方向 + magnitude を提案
2. **coder:** 本 context + planner の方向 → 具体値を提案 (structured output)
3. **orchestrator (Python):**
   - coder の提案を template に挿入 → edit
   - diff 検疫 (frame-altered / hole-escape 検査)
   - build + verify + bench
4. **critic:** 結果を見て「次の方向」を推奨 (方向のみ、値なし)
5. **whiteboard:** 提案・結果・却下理由を記録 (値なし)
6. **停止条件:** 
   - コンバージ (同じ方向を N 回提案) → 段 4 完了
   - 予算尽き (iteration 5-10 回) → 中間結果を段 6 へ
   - 矛盾検出 (verifier red / critic が「探索不可能」) → 終了

---

## 注記: 何が削除されているか

このファイルを作成する際、以下は**意図的に除去**されています (リーク制御)：

1. **output/insights/2026-06-22_p2-case-study-backoff-synthesis.md** — P2 での backoff 最適化の詳細・利得・スイープ結果
2. **backoff-sweep campaign reports** — 複数値を試した時の性能カーブ・最大値
3. **phase3.md 残存リスク節** — 「勝ち筋は X us の付近」という記載
4. **main-experiment §24/§59** — baseline との比較・予想される利得
5. **decisions.md の具体値** — D21/D22 の「Cicada の適応値は Y us」などの説明

これらは coder の自律性を検証するため、見えないようにしています。planner が「方向」だけを提案し、coder がそこから具体値を**独立して**思考することが、LLM の合成能力を実証する鍵です。

---

## 参考: なぜ値を隠すのか (philosophical notes)

この実験の問いは「**LLM が性能最適化を自律的に合成できるのか**」です。

もし coder が：
- 勝ち筋値を読んで → その値の neighborhood を search → 性能改善

という流れなら、「LLM が最適化した」のではなく「LLM が答えのそばを explore した」に過ぎません。

主実験は「LLM の独立した提案」「機械 sweep」「random baseline」の 3 者を比較し、LLM 特有の価値があるのかを問います。その問いを汚さないため、値・利得・勝ち筋の機序は遮断します。
