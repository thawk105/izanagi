# 段 4 裁定 + plan v2 — [T-244] 還流設計 wave (2026-08-01)

## 1. 判定サマリ

段 3 は両レンズとも **NO-GO**。BLOCKER 主張 11 件 (A: 5、B: 6) と MAJOR 6 件。
**すべて real と裁定する。refuted はゼロ。** 親 brief の前提 3 件も反証された (下記 §3)。

これは設計 wave であり、**所見そのものが成果物**である。plan v1 を「反証された案」として捨てるのでなく、
所見を折り込んだ設計 draft v1 として land する。

## 2. 親が独立に裏取りした事実 (子の主張を鵜呑みにしない)

| 主張 | 裏取り | 判定 |
|---|---|---|
| `run_trial(providers=/drive=/preview=)` の注入が実在 | `p3_autonomous_workload_trial.py:1002-1004` を実読 | real |
| formal consumer が origin proof を要求しない | `orchestrator/campaign/layer3_report.py` は campaign dir と `loop_state.json`/WAL を射影するだけ | real |
| 多世代 artifact は実在するが failure→constraint の発火証拠ではない | `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json` は iteration 2 で **2 件とも `success`** | real |
| `records_by_stage` は last-wins | `wal.py:586-601` の docstring が明記 | real |
| gateable atom は 5 種 | `axis_trigger_gating.py` の `GATEABLE_REASONS` (insert/scan は YCSB 不発で除外済み) | real |
| D106 残余 1 の supersede 注記が本文で「D112」と誤記 | `docs/decisions.md:4869` (見出しは D114、D112 は無関係な [T-118]) | real・本 wave で訂正 |

## 3. 親 brief の誤り (段 3 が反証、採用)

1. **「cross-generation チャネルは 2 本だけ」は偽。** `current_metrics` が outcome から更新され
   (`:951-953`)、次世代 planner の `current_perf`/`leading_indicators` と coder の `baseline` に入る
   (`:815-825`, `:843-860`)。**絶対 throughput を含む第 3 のチャネル**である。親 brief は §3.1 で
   この field を列挙しながら §3.2 で「2 本だけ」と書いており、自己矛盾していた。
2. **「理由は 1 bit も渡っていない」は射程過大。** whiteboard の `result` は 3 状態 =
   最大 `log2(3) ≈ 1.585 bit/世代 の failure 条件付き情報である。さらに `reverse_recommended` は
   critic が rejection 理由入り digest から作る**理由条件付き 1 bit**で、停止判定に効く。
   正しい言い方は「**機序 (なぜ壊れたか) の自然文は generator へ 0 bit だが、失敗の有無は既に流れている**」。
3. **「制約強制点が既に存在する」は過大表現。** `check_syntax_contract()` は禁止識別子 5 個の
   regex blacklist であり、5-bit mask を強制する面ではない。coder parser は任意の一行 C++ を受理する
   (`:261-284`)。正しい言い方は「**pre-build で候補を機械拒否する面は在るが、それは名前の blacklist であって
   mask enforcement ではない**」。

## 4. 段 2 プランに対する裁定

| plan の要素 | 裁定 |
|---|---|
| 候補表現を固定 5-bit IR へ閉じる | **採用** (設計 draft の中核) |
| 動的 constraint 文を `gating_spec` へ追記 (親 (P3)) | **不採用** — 文自体が最大 `log2(5) ≈ 2.32 bit` の理由チャネル。親の (P3) は反証された |
| constraint を hidden・単調に保つ | **採用**。ただし「hidden」は auditor への実効 diff と低エントロピー SHA で破れる (A1/B1) → **実効 diff と raw/effective SHA を untrusted role から遮断する**条件付き |
| producer = trusted machine のみ | **採用** |
| `Imax=2 / Qmax=2 / Kmax=1` | **未裁定へ送る** — 値の正当化が無く、origin 分割で回収されうる (B2)。設計 draft には「候補値」として書き、確定させない |
| campaign より上位の origin へ予算を束ねる | **採用**。ただし ledger の一意な所在・issuer 検証・削除耐性・単一 in-flight・CAS・crash replay が未定義 (A4/A9/B5) → **設計 draft の必須要件として明記** |
| translator = 単一 red の singleton relaxation を禁止化 | **名乗りを訂正して採用** — 「failure reason constraint」でなく **failed-singleton no-good cut** と呼ぶ (A8/B3)。因果帰属が機械実証されるまで規律 3 の「なぜ」を満たしたと主張しない |
| `reflux-control` WAL stage | 採用 (設計要件として)。`WAL_STAGES` 未収載である事実を明記 |
| D116 を「設計確定」にする | **不採用** (B6)。D116 は**採用済みの軸選択と多世代開放の前提条件**だけを確定し、設計本文は draft のまま insights に置く |
| 軸 (iii) を任意補強のまま置く | **格上げ** — 両レンズが独立に「singleton oracle が残る」と指摘した。(iii) 候補 batch 凍結を**多世代開放の必須前提**に格上げする。ユーザー裁定「(iii) は後置可」は禁止ではないため、これは裁定と両立する |

## 5. plan v2 (本 wave で land するもの)

1. `output/insights/2026-08-01_t244-reflux-design/README.md` — 設計 draft v1。必須 7 項目、脅威モデル、
   bit 会計 (上界が未定義な面の列挙を含む)、多世代開放の前提条件、real 所見 17 件の反映、未裁定択一。
2. `docs/decisions.md` に **D116** — 軸選択の裁定 (ユーザー、worklog (102))、A〜D 不採用の維持と再開条件、
   **多世代開放の前提条件リスト**、no-good cut への名乗り訂正、設計本文の所在。「設計確定」とは書かない。
3. D106 残余 1 の「D112」誤記を **D114** へ訂正 (一次資料と食い違う既存 docs、F1 型)。
4. `docs/phase3.md` / D114 保証の限界 / `docs/phase3-s8c-autonomous-trial-runbook.md` /
   `docs/phase3-main-experiment.md` の「未解決」記述を、**閉じずに正確化**する。共通文言:
   「軸と前提条件は D116 で確定した。設計本文は draft、機械配線・多世代運転・効果実証は未了であり、
   D114 の承認上限 1 を維持する」。
5. worklog 末尾エントリ + 次の一手。

## 6. 実装しない (docs-only) の再確認

`DW-G04`: 発火条件を満たす artifact path / 計測 ID を書けるのは **cap-lift guard** だけ (計測 ID `V7`、
`output/insights/2026-08-01_t244-generation-gate/mutation-ledger.json`)。しかしその guard が要求すべき
「前提の充足」は本 wave で未裁定の択一 (I/Q/K、origin authority、(iii) の必須化) に依存するため、
**今実装すると未裁定の設計を既成事実にする**。よって実装せず、guard の実装可否を裁定パッケージへ送る。
還流機構本体は発火 artifact が無く、`DW-G04` により設計メモに留める (段 2・段 3 とも同結論)。

**したがって段 5・6 に実装子は無い。docs 本文は親が書く (凍結境界の docs-only 例外)。**
変異 matrix と受入全走のうち**変異は対象外** (`DW-S04`: 実装差分が無い)。受入は
`check_docs.py` + pytest 全走 (Pegasus gen_S 計算ノード) を行う。

## 7. 裁定パッケージ (ユーザーへ返す択一)

1. **予算値** `Imax/Qmax/Kmax` を `2/2/1` で採るか、軸 (iii) の batch freeze を必須にしてから決めるか。
   → 推奨: **(iii) を必須前提にしたうえで値を再導出する** (両レンズが独立に指摘)。
2. **origin authority** を tracked registry (repo 内) で担うか、別 service/ACL へ分離するか。
   → 推奨: repo 内 tracked registry から始め、「同一 UID の caller からの秘匿」は残余として明示する。
3. **cap-lift の機械束縛** (計測 ID `V7` を前提充足検査へ拡張する) を実装するか。
   → 推奨: 択一 1・2 の確定後に独立 wave で実装する。
4. **formal consumer gate** (`layer3_report.py` 等が origin proof を要求する) を入れるか。
   受理集合の変更なので D96 手続が要る。
5. **診断 run の分離** (no-build `dry-pass` や runbook 配線確認を予算から外す) の扱い。
