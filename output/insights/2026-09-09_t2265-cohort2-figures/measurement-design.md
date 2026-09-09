# [T-2265] cohort 2 の図に使う観測長 6 秒 performance 測定 — 投入前に固定した設計

この文書は**性能値を 1 つも見る前に** commit する。目的は、腕・観測長・block 数・実行順・
停止規則・図に使う診断の選び方を、結果に触れる前に固定して残すことである。

**この文書は事前登録ではない。** `docs/dynamic-backoff-preregistration.md` と
`docs/backoff-counterfactual-cohort2-preregistration.md` はどちらも凍結済みで、
本 wave はその bytes を 1 byte も変えていない。本文書は新しい判定規則も等価域も作らない。

---

## 1. 名乗り — この測定が何であって何でないか

**未認証の、記述的な companion 測定である。**

- **凍結された観測長 3 秒の判定を置き換えない。再確認もしない。反証もしない。**
  `docs/dynamic-backoff-preregistration.md` §3 は観測長 3 秒・結果 schema v2 で凍結されており、
  そこで出た H1–H7 の判定は本測定と無関係にそのまま残る。
- **cohort 2 の腕の「trace 無効版」ではない。** ここで測る 7 腕のうち `cw-as-dyn` は
  時間 cap が 10240 µs である。cohort 2 の 3 腕は時間 cap が 9223372036854775807 µs で、
  **別の並行性制御設定**である。したがって本測定の値を、cohort 2 の局所 ITT の主判定
  (推奨方向の実用優越 +4.900%) の性能側の裏づけとして読んではならない。
- **性能値は未認証である。** 直列性の検査を通していない (絶対規律 1・2)。
  variant の採用根拠にしない。

## 2. なぜ観測長 6 秒で測るのか

cohort 2 の図の生成器 `tools/plotting/plot_dynamic_backoff.py` は、cohort 2 の診断成果物と
組にする performance 成果物に対し観測長 6 秒を要求する (`expected_extime_s = 6 if
terminal_contract`)。既存の 7 本 (観測長 3 秒・schema v2) では図が生成できない。
**図を描くためだけの要件であり、新しい問いを立てたのではない。**

## 3. 測定条件 (投入前に固定)

| 項目 | 値 |
| --- | --- |
| 腕 | `none`, `stock`, `tuned`, `tuned-u10240`, `cw`, `cw-as`, `cw-as-dyn` の 7 腕 |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 6, 12, 18, 24, 30, 36, 42, 48 |
| records | 1,000,000 |
| 観測長 | 6 秒、1 job あたり 1 rep |
| 反復 | 7 job = 7 block。1 job が 7 腕 x 3 workload x 8 threads = 168 点を回す |
| 腕の実行順 | rep i (0..6) は 7 腕の巡回順を開始位置 i から回す。順序と hostname を成果物へ記録する |
| build | trace-disabled (`BACKOFF_TRACE=0`)、perf 計測なし |
| ccbench | pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` + patch A + patch B + patch C |
| 投入元 | commit `8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235` を指す tracked-clean な checkout |
| walltime | `elapstim_req = 01:00:00` |
| 出力 | `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/` |

投入元の commit を `8bdf173cc` に固定するのは科学上の要請ではなく、**図の生成器が全入力の
identity 一致を要求するため**である。cohort 2 の診断成果物がその commit で作られている。

## 4. 停止規則と欠測規則 (投入前に固定)

- 7 本を同時に投入する。**結果を見てから job を足さない。**
- job ID を受け取った rep は自動再投入しない。node 障害・遅さ・測定値・分散を理由に
  置き換えない。qsub が job ID を返す前に失敗した場合だけ、job が成立していないことを
  確認したうえで未投入の rep を投入してよい。
- complete な成果物が 7 本なら 7 本、6 本なら 6 本で図を描く。**5 本以下なら描かない。**
- complete の定義: 成果物 JSON が 168 点の完全格子を持ち、観測長 6 秒・schema v3 で、
  巡回順と identity が診断と整合すること。途中 journal は使わない。

## 5. 図に使う診断成果物 (図を 1 枚も描く前に固定)

`/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/stage1-rep0-0_985851.nqsv.json`

規則は「job ID 昇順の先頭」である。12 本は同時投入され全件完走した集合であり、この規則は
軌跡・event 数・方向的中率・描画結果のいずれにも依存しない。

**ただしこれは事前凍結ではない。** 12 本は既に存在し、主判定の解析も済んでいる。
本文書が固定するのは「診断図を 1 枚も描く前に、結果非依存の規則を選んで動かさない」ことである。

## 6. 束縛が外付けであること (正直に書く)

成果物 JSON の `prereg_sha256` は、driver が常に `docs/dynamic-backoff-preregistration.md` の
bytes から作る。図の provenance が出す登録参照もその値だけである。
**したがって本文書の SHA は成果物にも provenance にも入らない。**

束縛は次の 2 つで外付けに取る。

- 投入台帳 `submitted-jobs.txt` に本文書の commit SHA と sha256 を書き、その後に投入する。
- insight にも同じ SHA と、投入した job ID の一覧を書く。

**この外付けの束縛は、成果物だけを見た第三者には辿れない。** その限界を承知のうえで、
成果物側の機構を足さない (足しても発火しないため)。
