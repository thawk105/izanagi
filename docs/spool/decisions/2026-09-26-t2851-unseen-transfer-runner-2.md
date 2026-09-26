---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: t2851-unseen-transfer-runner
seq: 2
---

## {{D:t2851-transfer-runner-contract}}. 未知条件への転移の実行器と解析器 — 事前登録 v1 §11 と TPC-C 版 §5 を新しい 2 module に置き、選定と発効は入力として受け、留保 cell は発効の記録なしに走らせない

**決定:** `orchestrator/campaign/t2851_transfer_runner.py` (実行) と `t2851_transfer_analysis.py` (解析) を次の契約で置く。
`orchestrator/campaign/pipeline.py`・`orchestrator/calibrator/runner.py`・verifier は呼ぶだけで変えない。事前登録 2 本 (D2223・D2228) の本文は変えない。

1. **選定をしない。** 対象探索群、全 (課題, 手法, 独立探索) → identity の対応、選択規則、参照 (YCSB silo の R0〜R2、MOCC と TPC-C の 3 択と参照)、到達可能性、
   各 identity の binary (性能用と検証用の path・sha256、検証用を compile した CCBench source root) と環境値 (env_tag・clocks_per_us・numactl) を凍結入力として受け取る。
   実行器は網羅・排他・学習 cell ⊆ 登録錨・binary 対応だけを検査し、正規化 JSON と sha256、測る identity 集合、比較の一覧、族ごとの M を出す。
2. **M** は族ごとに、cell 内で重複除去した (候補 identity, 強い参照 identity) の数 (同 identity の組を除く)。欠測・失格・未確定で減らさない。
   R0 比・参照どうし・silo の bal-rmw1 は記述。TPC-C は段ごとに別族で、R* を (a) で固定した protocol だけが主要族を持つ。
3. **留保 cell** の実行と検証は、発効の記録 (decision_id と凍結記録の sha256、TPC-C は段と認定経路) を受けたときだけ許し、欠ければ測定前に拒否する。
   発効束の他の項目は審査しない。実行前に凍結記録を入力から再生成し、派生 field を含めて完全一致を要求する。binary の内容 sha256 を実行時に照合する。
4. **検証**は性能と別の trace-enabled binary で、verifier の判定条件を変えずに certified / disqualified / indeterminate へ写す。
   YCSB は `pipeline._run_trace` と `verifier.core.verify_trace_dir(..., ccbench_root=<凍結した source root>)`。TPC-C は認定経路を実行器へ接続するまで indeterminate を記録する。
5. 登録文に明記の無い選択: block 番号は 1..32。

**理由:**
- 測定の発効 (D2223 項 2) と選定は別の決定である。実行器が選定を含むと、発効前に選定が既成事実になる。
- 段 6 の review と焦点再レビューの所見 (契約の不一致、M の系列重複、凍結の派生 field の改変、cohort 1 の一部省略による別日判定の迂回、環境値の暗黙依存) を、
  主要表の値・分類・受理集合への影響で裁定した結果である。
- 計算ノードの生死確認で、`ccbench_root` を渡さないと証明面が unavailable になり YCSB の検証が certified に到達しないことを実測した (fixture test では検出できなかった)。

**却下した選択肢:**
- **発効束の全項目を実行器が審査する gate** — ユーザー指示の scope 外 (仮想リスク向けの gate)。留保 cell の解禁に要る最小の接続だけを置いた。
- **binary 内容 sha256 の実行時照合をやめる** — 両 cohort で同じ identity の build を使う規則 (v1 §5) の束縛が失われる。
- **TPC-C の認定経路への接続を本単位で行う** — 裁定時点で経路が未着地で、発火条件を満たす成果物を名指しできなかった (DW-G04)。別単位にした。
- **build を実行器に含める** — buildcache は YCSB target 固定で、TPC-C と Pegasus の依存準備を抱えると scope を超える。binary は凍結入力で受ける。
