---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t2103-producer-auth-layer
seq: 1
---

## {{D:producer-auth-layer-not-the-frozen-closure}}. raw-record producer の認証は closure 拡張でなく raw assembly 層に置く

**決定:** D1345 が求めた比較実験を実施した結果、**5-file pin を広げる案は採らない。**
同じ拒否能力を raw assembly 層が半分以下の変更閉包で達成するためである。
本 wave では認証層の本採用実装は行わず、比較結果と非保証だけを確定する。

実測 (base commit `3e6fe8d97ec104e2bfa86125b3af33a319bf5bd1`、
`output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json`)。
分子は層を分離しうる C1 系 3 件 + R 系 3 件の計 6 件。

| 候補 | 増分 KILLED | production file | pin site | test 波及 |
|---|---:|---:|---:|---:|
| issuer | 0 / 6 | 2 | 1 | 2 |
| raw assembly | 3 / 6 | 2 | 1 | 2 |
| 一時的 6-member expanded closure prototype | 3 / 6 | 4 | 3 | 5 |

**理由:**

- **拒否能力は raw assembly と closure 拡張で同一である。** ともに 3/6 で、
  殺した case 集合も同じ (C1 系 3 件) である。差がついたのは変更閉包だけである。
- D1345 は pin 拡張を「比較の結果それが最小と示された場合を除き採らない」と定めた。
  最小ではないことが実測で示されたため、条件は満たされない。
- issuer は 0/6 である。issuance 後に producer が差し替わる形を観測できない。
  これは issuer 自身が非保証に記している性質と一致する。
- R 系 3 件は 3 候補とも `BASELINE_REJECTED` であった。baseline と prototype の観測が
  `evidence_binding:source_rederivation` で完全一致しており、拒否しているのは既存 gate であって
  新設 guard ではない。どの候補にも増分を与えない。
- 全 6 件を殺す候補は無い。D 系 3 件 (assembly 後に判断値だけを書き換える形) は 3 候補共通の穴であり、
  post-assembly の end-to-end authenticity はどの候補も与えない。これは別 task の領域である。
- 過剰拒否は起きていない。POS-1 は 3 候補とも受理され、候補が有効な状態でも既存 producer test
  29 node は 3 候補とも緑である。

**却下した選択肢:**

- **5-file pin を広げる** — 同じ拒否能力に対し production file が 2 倍、pin site が 3 倍、
  test 波及が 2.5 倍かかる。凍結 closure を動かす費用を最小性なしに払うことになる。
- **issuer に置く** — 増分 KILLED が 0 である。issuance 後の交代を観測できない。
- **比較せず現状維持** — 別 producer 由来の記録を verdict が識別できない欠陥が残る。

## {{D:b4-production-analysis-path-returns-no-valid-analysis}}. B-4 の production 分析経路は現時点でいかなる入力でも有効な分析を返さない

**決定:** この事実を記録し、認証層の測定は `floor=0` を供給した条件下の値であると明記する。
production の挙動を変える修正は本 wave では行わない。

**理由:**

- `orchestrator/campaign/p3_b4_material_report.py:225` は `evaluate_b4_artifacts` へ `floor=None` を渡す。
  `orchestrator/campaign/p3_b4_analysis_contract.py:323-325` は `None` の floor に対し
  `FLOOR_DOMAIN_ERROR` を立てる。したがって block 数や入力の正当性によらず
  `analysis_invalid` になる。
- これは事故ではなく既知の設計である。同 module の docstring が
  「`floor=None` を凍結 evaluator へ渡し、結果の protocol violation を報告する」と明記し、
  報告 field に `floor_availability: "absent"`、`expected_analysis_reason: "floor_domain_error"`、
  `authoritative_floor_artifact` を持つ。権威ある floor 成果物が未発行だからである。
- この定数は全 78 phase・全候補・全変異・正例でも同一に発火するため、拒否能力について
  1 bit の情報も持たない。既存 gate の拒否として数えると測定が構造的に不可能になる。
- 併せて、closure receipt には production の呼び手が存在しないことも実測した。
  `generate_verified_analysis_source_closure_receipt` を呼ぶのは test だけであり、
  material report は receipt を渡さずに evaluator を呼ぶ。D1530 が言う「未接続の interface」と
  同型である。

**却下した選択肢:**

- **floor 不在を「既存 gate による拒否」と数える** — 定数を信号と取り違え、全 case が
  BASELINE_REJECTED になって測定が成立しない。実際に一度そうなった。
- **本 wave で production の floor を配線する** — 権威ある floor 成果物の発行が前提であり、
  本 wave の scope 外である。D1530 に従い、実 producer の接続と同じ変更単位で閉じる。
