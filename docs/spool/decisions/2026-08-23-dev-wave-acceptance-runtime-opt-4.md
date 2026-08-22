---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-acceptance-runtime-opt
seq: 4
---

## {{D:acceptance-wall-measured-on-dedicated-node}}. 受入 wall の基準値を専有に近い計算ノードの実測へ更新し、指定テストの既定 skip 化はユーザー再裁定へ返す

**決定:**

1. 受入 pytest wall の現行基準値を **168.57 秒** とする (2026-08-23 04:03、Pegasus gen_S、
   request 937260.nqsv、HEAD 3aba1320、26 failed / 14256 passed / 96 skipped)。
   記録済みテスト相 (setup + call + teardown) の合計は **5917.79 秒 / 8351 相**、
   48 worker での理想化した仕事量下限は **123.29 秒**。**この 1 走は単独性を事前確認していないため
   provisional とする** (`docs/pegasus-runbook.md` の gen_S は `Exclusive submit = OFF`)。
2. 前 wave の {{D:acceptance-wall-model-needs-refresh}} が置いた「wall 220〜274 秒」は
   2026-08-22 の混雑下の値であり、専有に近い条件では再現しない。両者は同じ機構の別条件の
   実測として併存させ、どちらか一方を唯一の基準にしない。
3. `orchestrator/tests/test_real_repo_serialization.py` の
   `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` を
   growth-test hold registry へ登録して既定 skip にする案は、**本 wave では実装せず、
   下記の交換レートを添えてユーザー再裁定へ返す**。親は不採用にしない。
4. 受入の所要は **pytest wall / 赤の非帰属再検証 wall / 受入全体 wall** の 3 層に分けて記録する。
   「5 分以内」の達成度を pytest wall だけで語らない。

**交換レート (再裁定の材料):**

- 得るもの: 均等配分モデルで wall **0.576 秒** (= 27.65 / 48)。**これは実測ではない。**
  worker 別の配置記録が profile に無いため、実際の差は対象が非 critical worker にあれば 0 秒、
  critical worker の末尾にあれば 27.65 秒近くまで振れる。対象の占有率は記録済みテスト相の
  **0.467%** で、最長の単一テスト (92.28 秒) でもない。
- 失うもの (同ファイル `:803` が残っても回復しない検査):
  (a) `--ff` で lastfailed を注入した後の最終 collection 順、
  (b) `--nf` で cached nodeids を注入した後の最終 collection 順、
  (c) priority node が parameterize されたときの canonical node 境界の合成対照。
  これらが破れると受入の passed/failed/skipped と赤の attributable/non-attributable 判定が
  false green / false red になりうる。
- 要する実装: registry 本体と exact pin に加え、`orchestrator/tests/test_hold_inventory.py` の
  期待値群と `tools/hold_inventory.py` の layer-level `ruling` (単数 field のため新旧 2 つの
  裁定を表現できない) の schema 裁定。実装面 4 ファイル以上。
- 既存 hold は全件 `measured_seconds=None` である。本件を登録するなら 27.65 秒の provenance と
  上記 collateral を明示した上で登録する。`correctness_gate=True` という metadata が付くこと自体を
  安全の根拠にしない (D532、絶対規律 2)。

**検出力を保つ代替 (記録のみ、本 wave では実装しない):**

対象テストの 3 回の全件 collection のうち、base を先に走らせて nodeid seed を作り、
その後の `--ff` と `--nf` の 2 subprocess だけを有界並列にする形は受理集合を変えない
(各呼出しは全件 collection・別の一時 plugin/report/cache を使い、collection を狭めていない)。
ただし helper が親環境をそのまま継承するため task-run sidecar の共有 race を先に断ち、
逐次版との report 同値性と negative control を確かめる必要がある。
期待短縮は対象テスト内で約 9 秒、wall では約 0.19 秒であり、単独では投資に見合わない。
1 回の pytest 呼出しへ畳む形は `--ff` / `--nf` の別 hook chain を実行しなくなるため採らない。

**理由:**

- 一次資料は `--durations=0` の全走 profile (job dir `s2/durations-before.txt`)。
  記録済みテスト相の合計は独立に再集計でき、対象テストは 27.65 秒、同ファイル `:803` は 8.96 秒。
  費用は 1 ファイルあたり最大 8.6% (510.2 秒) と広く分散し、単一テストの除外で動く量が無い。
- 前 wave が根拠にした 87.46 秒との差は**混雑を含む未切り分け**である。HEAD が異なり、
  総 item 数も 14364 対 14378 と違い、skip 集合は比較していない。混雑だけに帰せない。
- D312 (数値目標は達成目標であって合否判定ではない、設計択一は実際の交換レートで判断し、
  割れるならユーザーへ諮る) に従い、モデル値 0.576 秒だけで除外を棄却しない。
- 効果量 0.576 秒に対し走行間変動は 168〜274 秒と 2 桁大きい。現条件では A/B 実測に検出力が無く、
  前 wave が置いた「実際に対象を除外した A/B」という再訪条件は本 wave では満たせない。

**却下した選択肢:**

- モデル値だけで除外を棄却し、記録を閉じる — ユーザー裁定の一方的な拒否になる。
- 混雑下の 87.46 秒をそのまま機構の構造的費用として扱い、除外を実装する — 交換レートを誤らせる。
- 単発の A/B 1 往復で決着させる — 効果量が走行間変動より 2 桁小さく、結論を支えられない。
- 5 分上限の達成度を pytest wall だけで報告する — 赤の非帰属再検証が 41 分以上を要しており、
  受入全体では上限を大きく超えている。

再訪条件: worker 別の schedule 記録 (worker ID・開始・終了) が取れるようになったとき、
または記録済みテスト相の合計が 48 worker で 300 秒に達する水準 (約 14400 秒) へ近づいたとき。
