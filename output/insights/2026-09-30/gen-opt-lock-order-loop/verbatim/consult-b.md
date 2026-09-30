## 総括

**条件付き GO。** 新 driver は必要だが、既存方策 driver の複製は不要。現計画のままでは fixture の結果を本番の certified と混同でき、生死確認も driver の実経路を証明しない。モデル結果の受け口と確認方法を局所修正してから実装に進むべき。

## 所見

1. **must-fix — fixture が certified の選択へ流れ得る。** [plan.md §U-B・§U-D](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/plan.md) は fixture と履歴上の表示を定める一方、合格後に `run_campaign` を呼ぶ。履歴に `model_evidence_kind="fixture"` と書くだけでは、campaign の certified を抑止しない。**影響:** 未検査の仕様が certified の選択集合に入る。**修正:** fixture 経路は配線試験専用にし、結果と history の outcome を `fixture-liveness` 等に固定する。本番の certified へ進めるのは、登録済み digest と実物のモデル結果を照合した経路だけにする。

2. **must-fix — U-D は計画した「driver の 1 周」を実証しない。** [plan.md §U-D](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/plan.md) は driver intake の後、起動器が独自に trace build と capability 判定を行う構成である。さらに [source_digest.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:97) は U1 の `include/ycsb.hh` を tracked 変更として許さず、[patchharness.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/patchharness.py:247) は pin 上の clean な checkout を要求する。**影響:** 生死確認のレポートが pipeline への要求伝播や driver history を実証したと誤読される。**修正:** pin 前進までは「patched source の standalone 判定」と「fixture による driver 関数経路の配線試験」を別々に記録する。capability を正規導出できなければ構造化した admission 拒否を記録し、certified と書かない。完全な 1 周は md_15・md_19 着地後に再実走する。

3. **must-fix — モデル結果の完了条件を先に固定し過ぎている。** [plan.md §U-B](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/plan.md) の `complete=True → stop_reason=null` は、既存 checker の [search.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/tools/cc_model_checker/search.py:29) にある `stop_reason="exhausted"` と合わない。また L1・L2・L3 の三つの ID だけでは、[段 A 候補 §5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md:265) の個別窓と L3 全構成の完了を示せない。**影響:** md_19 の正当な結果を拒否するか、不完全な探索を受理する。**修正:** この wave では「独立に登録した仕様 digest・登録場面集合・各場面の完了と反例」を受ける最小アダプタに留める。`stop_reason` と集計 JSON の詳細形は md_19 の実物に合わせ、L3 は登録済み manifest と完了範囲で照合する。

4. **should-fix — U-A は三つの source text と include 解決事実に絞れる。** D5 が読むのは [core.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/core.py:43) の三 file と引用 include の解決結果だけ。通常の [snapshot v1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:129) を一律に拡張する必要はない。**影響:** 通常呼出しの投影 bytes や既存 lock の参照を余計に変える。**修正:** 要求時だけ optional な D5 証拠束を capture・fan-out し、要求なしの v1 serialization を維持する。`transaction.cc` の既存 snapshot 内の位置を暗黙に推定せず、三つを明示的に束縛する。[resolve_evidence](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:2413) と pipeline の再 capture の双方を同じ条件にする。

5. **should-fix — 新 driver は薄い接続層に限定する。** [order_gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/silo_lock_order_gate.py:23) と既存 [方策 driver の部品](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_policy.py:460) は使えるが、方策 driver の axis 固有 schema、設定、履歴、CLI をそのまま使うことはできない。**影響:** driver を無くすと要求つき capability への唯一の入口が欠け、複製を増やすと受理集合と履歴の管理面が増える。**修正:** 新 module は proposal intake、モデル関門、要求つき campaign 呼出し、閉じた history 投影だけを持つ。停止制御や汎用計測部品は再利用し、対照運用一式と独自の互換層を移植しない。

6. **should-fix — 反例 schema の通過を「反例の真偽」と扱わない。** [schema.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/tools/cc_model_checker/schema.py:81) は形を検査するだけであり、[正しさ関門 §4.2・§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-correctness-gate/README.md:231) は反例列の確認とモデル欠陥の区別を求める。**影響:** 偽の反例が候補を失格にし、history の次回入力を誤らせる。**修正:** 現 wave は閉じた field の検証と `model-counterexample` への停止までに留め、失格の確定は md_19 の replay 証拠がある結果に限る。

7. **nit — inventory と変異は実在する入口だけ追記する。** [plan.md §inventory・§変異候補](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/plan.md) の新 driver 登録は、CLI が authority を発行し `run_campaign` を直接呼ぶ実装なら必要。[test_campaign.py:5509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_campaign.py:5509) 等は AST 件数も固定する。**影響:** 先取りした件数は検査を赤にし、不要な台帳行は実際の呼出し位置を曖昧にする。**修正:** 実装後の call site 数だけ追記する。新 test の plain runner allowlist と duration ledger は実際に作った nodeid と測定値だけを登録する。

8. **should-fix — 生死確認は一つの名前つき対照から始められる。** [計画 §U-D](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/plan.md) の 1 対照×2 workload は約 2〜3 分という見積りで、[md_14 実測](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-30/gen-opt-gate-verifier/README.md:180) の「build＋2 workload＋判定」117〜130 秒とも大筋で整合する。ただし「driver 接続の生死」だけなら RMW ありの 1 run が最小。**影響:** 2 run 自体は受理集合を変えないが、接続不良が分かった後の計算を増やす。**修正:** まず 1 build・RMW あり 1 run で入口と理由コードを確かめる。RMW なしは両 workload の照合を成果物に求める場合に追加する。

## (P) への賛否

- **P1:** 賛成。driver の明示要求と flag 由来の強制を併用し、要求なしの既存経路は維持する。
- **P2:** 反対。`cc-model-result/1` の詳細を md_19 より先に固定せず、最小の消費契約だけ決める。
- **P3:** 賛成。結果 file の自己申告 digest を期待値にしない。未登録時の本番拒否は必須。
- **P4:** 条件付き賛成。軸単位の仕様一つは妥当だが、三層の ID だけで探索完了を代表させない。
- **P5:** 条件付き賛成。名前つき対照の一周に新 role は不要。LLM が生成した候補による本評価まで完了したとは記さない。
- **P6:** 条件付き賛成。計数 build は本 wave の接続から外せるが、[軸の記録 §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-30/gen-opt-lock-order-axis/README.md:58) どおり [T-2896] の効果評価前には要る。
- **P7:** 賛成。D5 の述語を変えず取得元を snapshot に束縛するなら、意味の版 2 を据え置ける。
- **P8:** 賛成。ただし起動器の standalone 成功を pipeline の実走成功と呼ばない。

## 変異の帰属

- `driver の True を落とす`：flag=1 なら pipeline 側の強制が遮る。spy は driver の配線漏れを検出できても、**certified が誤って増える単一理由の変異ではない**。flag 強制も同時に落とす結合変異と区別する。
- `pipeline の flag 強制を削る`：driver が True を渡す通常経路では赤にならない。明示要求なし・flag=1 の別 caller で検査する。
- `local / fan-out の片経路で要求を落とす`：flag から再導出する実装なら遮られる。実際の消費点で `gate_witness_required` と certified の両方を確認する。
- `反例の余分な field を history に通す`：入口 schema が先に拒否する fixture では history 投影の変異が到達不能。validated dataclass を使う正常入力から、投影だけを変異させて確認する。
- `snapshot D5 を disk に戻す`：capture 後改変 fixture では source 再照合が先に拒否し得る。capability 判定の直前に snapshot と disk を意図的に分け、その層だけを検査する。

## scope 外に返すべきもの

- md_19：結果の実 schema、登録場面 manifest、完了範囲、反例 replay 証拠を確定し、消費側アダプタと照合する。
- md_15：U1 と Silo 修正を含む pin へ進め、正規の `SourceEvidence`・`BuildAdmission` を通る実走を可能にする。
- [T-2896]：並べ替えを使った取引数の計数と、LLM 候補の本評価を行う。本 wave の fixture 生死確認をその成果に昇格させない。

以上は静的点検であり、build・test・計測は実行していない。