# A-2 正式 certification の結果節 — 正しい identity で取り直した attempt は `observed-positive` (2026-09-07)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** 同系列は append-only であり、
2026-09-04 の稿と 2026-09-07 の `reject` の稿はいずれも 1 byte も変えずに残る。それらが書いているのは
attempt `t2022-20260828c` という**別の attempt** についての事実である。本稿が書くのは
attempt `t2364-20260907b` という**新しい attempt** についての事実であり、前者を無効にするものではない
(絶対規律 7)。

---

## 0. 位置づけ — 何を書き、何を書かないか

- **書くもの:** attempt `t2364-20260907b` (2026-09-07) の 4 cell について、権威 bytes が持つ
  `cells[].performance.median_tps`・`effects`・`status`、それらの cell で実際に効いていた条件、
  status から言えることと言えないこと、表、限定の一覧。
- **書かないもの:** 旧 attempt の判定の取り消し (規律 7)、旧系列との差の原因の断定、
  研究として成功か失敗かの宣告 (D12)、read-heavy についての主張 (A-6 として未取得)、
  この効果が他の workload・他の機体へ転移するという主張。
- **`observed-positive` は protocol の status であって、研究の成功宣告ではない。** protocol は
  「adopted 側 cell の median throughput が同一 workload の stock 側 cell を上回るか」を
  2 workload の論理積で問い、その答えが「上回った」だった、という事実である。

---

## 1. 何が旧 attempt と違うのか — 測っている条件が違う

旧 attempt `t2022-20260828c` は、**patch が当たっていない stock の CCBench 木**で走っていた。
静的量を渡す `BACKOFF_FIXED` は cmake の argv には載ったが、pin の CCBench に対応する option 定義が
無いため build の条件にならず、実際に効いた条件差は内蔵 backoff の有効/無効だけだった
(D1645、F707 の再発)。

本 attempt は、D1644 が定めた **pin + patch に束縛した `src_token`** で cell の identity を計算する
driver で走っている。driver は patch を当てた隔離木に対して `source_digest.resolve_evidence` を
cell ごとに評価し、その token で期待値を作り、**stock cell は `stock`、adopted cell は非 `stock`** で
あることを fails-closed で要求する。

一次資料の `certification.json` は 4 cell すべてについて次を記録している。

| cell | role | `src_token` | `source_binding_status` |
|---|---|---|---|
| `rr5-stock` | stock | `stock` | `bound` |
| `rr5-fixed10` | adopted | `955b452a332d…` (非 `stock`) | `bound` |
| `rr50-stock` | stock | `stock` | `bound` |
| `rr50-fixed5` | adopted | `21def77c944b…` (非 `stock`) | `bound` |

**したがって本 attempt では、adopted cell が patch の当たった木で build されたことが記録から言える。**
旧 attempt でこれが言えなかったことこそが D1645 の訂正の理由だった。

---

## 2. 結果

### 2.1 性能 — 2 つの独立 campaign で、adopted は stock を上回った

| workload | cell | role | 要求 genome | median (tps) | mean (tps) | 95% CI 半幅 | 変動係数 | abort 率 |
|---|---|---|---|---|---|---|---|---|
| rr5 (write-heavy) | `rr5-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` | 2,438,295 | 2,462,838.6 | 99,765.6 | 0.0326 | 0.7845 |
| rr5 (write-heavy) | `rr5-fixed10` | adopted | `BACKOFF_FIXED=10`, `BACK_OFF=1` | 3,987,794 | 4,004,505.0 | 45,583.8 | 0.0092 | 0.3833 |
| rr50 (balanced) | `rr50-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` | 3,756,230 | 3,808,422.0 | 138,475.2 | 0.0293 | 0.6850 |
| rr50 (balanced) | `rr50-fixed5` | adopted | `BACKOFF_FIXED=5`, `BACK_OFF=1` | 4,297,929 | 4,302,525.0 | 58,456.7 | 0.0109 | 0.4615 |

median 比の効果は **rr5 が +63.5485%、rr50 が +14.4213%** である。図生成器はこの 2 つを
一次資料から独立に再計算し、権威の値と一致することを記録している (`effect_crosschecks` の
`authority_matches` が両方 `true`)。

outer status は 2 workload の論理積であり、**`observed-positive`** である。

**平均の信頼区間は標本を記述するものであって、効果・判定・median の信頼区間ではない。**
本成果物は有意性の判定を行わない。

### 2.2 正しさ — 別走行で 4 cell すべて certified

正しさは trace-enabled の別走行から来る。4 cell すべてが `certified` で、
legacy の反復は 1 回、performance 側の反復は 5 回である。**これは性能の認証ではない。**
L01 により、この証拠は point-key trace に限られる。D1257 により、正しさ側の argv は
既存 pipeline では独立に記録されていない。

### 2.3 測定条件

48 threads、1,000,000 records、Zipf 0.9、read-modify-write 無効、max operations 10、3 秒、
5 反復、CCBench pin `511c953`、perf 不使用、性能は trace-disabled build。

2 つの campaign は独立の request である。

| workload | request | ホスト | 記録時刻 (UTC) |
|---|---|---|---|
| rr5 | `981476.nqsv` | `bnode077` | 2026-09-07T12:12:55.607184+00:00 |
| rr50 | `981477.nqsv` | `bnode085` | 2026-09-07T12:12:55.388302+00:00 |

izanagi 側の source commit は `31ec382a7841e188e46f93e8de4261c964facfb2` である。

---

## 3. 限定 (この結果が言わないこと)

- **read-heavy については何も言わない。** A-6 として未取得である。
- **他の workload・他の機体・他の CCBench pin へ転移するとは言わない。** 測ったのは
  この 2 つの workload、この pin、この機体だけである。
- **旧 attempt の判定を取り消すものではない。** 旧 attempt は別の条件 (patch 無しの木) を測った
  別の事実であり、記録として残る (絶対規律 7)。両者を前後比較として読んではならない。
- **条件関門について言えるのは記録までである。** raw manifest は `use_class="paper"` かつ
  `admitted=true` と記録する canonical な admission record を 4 cell 分束縛しているが、
  元の supply / meaning records は成果物に保存されていない。したがって
  「関門を実施し通過した」ではなく「そう記録された受領証が束縛されている」と書く。
- **abort 率は記述的な先行指標である。** cell あたり 1 点の集計値で、信頼区間を持たず、
  因果の機序を主張しない。
- **2 つの workload の縦軸は独立に目盛られている。** panel の高さを比較してはならない。

---

## 4. 一次資料

- 認証成果物: `output/insights/2026-09-07_t2364-paper-story-a2-certification/`
  (`certification.json` は `paper-story-a2-certification-result/v4`、
  `raw-manifest.json` は `paper-story-a2-full-raw-manifest/v4`)
- 図: `docs/paper-story/figures/fig6_a2_certification_observed_positive.png` / `.pdf` /
  `.provenance.json`
- 計測の durable authority: attempt `t2364-20260907b` の WAL と raw cell
  (図の provenance の `external_inputs` に root 相対 path と SHA-256 が 12 件記録されている)
- 取り直しを塞いでいた阻害要因とその修正: commit `31ec382a7`
