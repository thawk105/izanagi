# [T-2265] 反実仮想 ITT の事前登録と実測 — 段 1 brief

wave `t2265-backoff-itt`、branch `worktree-dev-wave-t2265-backoff-itt`、base main `cf4273f56`。
一次資料は `output/insights/2026-09-07_t2265-backoff-counterfactual/README.md` (機構の着地、実測なし)。

## scope

1. **新規事前登録** `docs/backoff-counterfactual-preregistration.md` (親が書く docs)。反実仮想の結果を
   1 つも見る前に凍結し、主推定量・等価域とその根拠・層・除外規則・seed 一覧・分散・検出力・停止規則を固定する。
2. **driver 実装** (Codex `role=author`、既登録 path の中だけ): (a) policy 2 の seed を引数化して artifact へ
   記録、(b) 反実仮想 cell の artifact の `counterfactual_preregistration` を `"pending"` から新事前登録の
   sha256 束縛へ、(c) 事前登録した推定量を artifact から計算する解析 module。いずれもテスト付き。
3. **実測**: 診断 (trace 有効) job を seed ごとに、性能 (trace 無効) job を block ごとに、既登録の
   `.pbs` から直列投入する。
4. **記録**: insight README + worklog fragment。

## 不変条件

- **規律 1**: trace 有効 build の値は `throughput_scope=diagnostic_only` / `headline_eligible=false` のまま
  扱い、性能主張に使わない。性能値は trace 無効 build からだけ取る。
- **規律 2**: 認証の exact 2 cell 契約・patch A の hard pin・既存の逐語 pin を 1 byte も変えない。
  policy≠0 の直列性認証は本 wave の scope 外で、次の一手へ起票する。性能値はすべて未認証と明記する。
- **除外規則**: 処置後の量 (clamp の当たり、実適用差分 0、`inversion_realized`、outcome) による除外を禁止する。
- **F660**: 新規 Pegasus 実行体を作らない。main 側 `tools/pegasus/admission_registry.json` の現物で
  `t2187_adaptive_const_probe.py` / `.pbs` が両方 `dispatch-required` として登録済みであることを確認した。
  投入はこの 2 path だけを使い、絶対 path での迂回をしない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない (ユーザー裁定)。

## 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1-1) 主推定量**: policy 2 の run 内で、更新 i の割当 Z_i ∈ {順, 逆} に対する次窓 log throughput 変化
  Y_i = ln(T_{i+1}/T_i) の平均差 (割当についての ITT)。cluster = run。Z_i は先行状態と独立なので無条件対比だけが
  厳密な因果対比であり、pre-state による層別は先行割当に対して処置後である。
- **(P1-2) 主層 = write-heavy 48 threads。** 既存 v1 trace の実測 (job 978021) で、この regime だけ backoff が
  0 の床を離れ (中央値 5〜6 µs、最大 17〜21 µs)、gradient 0 が 0.1〜0.3% しかなく、ほぼ全更新で腕が発火する。
  他 regime は backoff 0〜1 µs に張り付き、更新の 39〜51% が gradient 0 で腕が届かない。
- **(P1-3) 等価域 ±3%** (log 比 ±0.02956)。既存 run 単位の等価域と同じ幅にし、「1 更新の ITT ≈ 常時反転の
  run 単位効果」という近似 (carryover が 1 窓を超えない) を仮定として明記する。
- **(P1-4) 反復**: 診断は独立 seed 12 本 = 12 job (1 job ≈ 136 秒の実測)、性能は 7 block = 7 job。
- **(P1-5) 二次解析**: `recommended_delta_sign`・`both_actions_feasible` による層別は記述的二次とする。
- **(P1-6) 性能側の cell 集合**: 既存 grid 契約が `none` 1 本と stock control 1 本を要求するので
  `none + stock + p0 + p1 + p2` の 5 cell にする (契約は変えない)。

## 成果物の形

事前登録 doc 1 本 / driver + 解析 module の diff とテスト / job 成果物 (`izanagi-job-evidence` 配下) /
判定表を含む insight README / worklog fragment。

## 分割方針

実装面は編集 file が重なるので段 5 は 1 単位。設計択一が割れ受理集合も変わるので軽量版にせず、
段 2・3 と段 6 のレビュー子を省かない。
