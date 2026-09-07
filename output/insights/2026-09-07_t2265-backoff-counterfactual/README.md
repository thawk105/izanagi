# [T-2265] adaptive backoff の反実仮想対照 — 機構の着地 (実測なし)

2026-09-07。branch `worktree-dev-wave-t2265-backoff-counterfactual`。base `f486ff13c`。

## 0. この wave が主張すること・しないこと

**主張する:** 事前登録された反実仮想試験を次 wave で走らせるために必要な、compile-time の腕・
診断記録・投入経路・登録簿を着地させた。

**主張しない:** **測定は一切していない。** 機序に答えていない。「方向的中 0.50 の反実仮想」は
未測定のままである。本 wave は F660 に従い、機構を着地させる wave と実測する wave を分けた回である。

## 1. 何を作ったか

`patches/cicada-adaptive-counterfactual.patch` (C) は pin `511c9538` + A + B を preimage とする
第 3 の patch で、`cmake/Options.cmake` と `include/backoff.hh` の 2 file だけを触り、
`#include` 行を 1 行も足さない。

| option | 既定 | 意味 |
|---|---|---|
| `CCBENCH_BACKOFF_STEP_POLICY` | 0 | 0 = stock / 1 = 常に反転 / 2 = 更新ごとに 1/2 で無作為に反転 |
| `CCBENCH_BACKOFF_STEP_POLICY_SEED` | 11400714819323198485 | policy 2 の決定的 LCG の種 |

反転点は **1 箇所**で、`#if BACKOFF_STEP_ADAPT` 枝と非 `STEP_ADAPT` 枝の共通の出口の後、
clamp の前にある。反転するのは `new_backoff` に付いた差分の符号だけで、parity 分岐
(`gradient == 0`) が選んだ一歩も含む。**真の勾配のまま更新するもの:** 窓の発火判定・勾配・
`adaptive_step_`・`last_gradient_sign_`・`ceiling_`。

policy 2 の割当は `state = state * 6364136223846793005 + 1442695040888963407 (mod 2^64)` の
bit 63 で、勾配 0・推奨差分 0・clamp のときも毎更新で進める。既定 seed の最初の 16 割当は
`0111001000100110` で、これは実装を読まずに式から独立に再計算して一致を確認した。

## 2. 診断 trace は v=2 へ

既存 12 項目の書式と順序は変えず、record と summary の版を `v=2` にして 4 項目を足した。
すべて `#if BACKOFF_TRACE` の中にあり、性能ビルドからはコンパイル時に完全に消える (絶対規律 1)。

| 項目 | 意味 |
|---|---|
| `recommended_delta_sign` | 反転しなければ適用したはずの差分の符号。parity 分岐を反映するので `gradient_sign` の別名ではない |
| `assigned_invert` | この更新で反転したか (policy 2 では LCG の割当そのもの) |
| `inversion_realized` | 実差分が推奨差分の厳密な符号反転 (大きさも一致) だったか |
| `both_actions_feasible` | **割当を適用する前**に pre-state から求めた、推奨と逆候補の両方が clamp を受けずに適用できるか |

`both_actions_feasible` を割当の前に置いたのは、段 3 の指摘による。`inversion_realized` で
層別すると**処置の後で選ぶ操作**になり偏る (境界では順方向だけが除外され逆方向だけが残る組み合わせが
作れる)。偏らない副解析には割当の前に決まる量が要る。

parser は v=1 と v=2 を版ごとの連言で受理し、版の混在・summary 版の不一致・項目欠け・
v=1 への余分な項目をいずれも拒否する。

## 3. この腕が答える命題・答えない命題

- **policy 1 対 policy 0** が答えるのは「制御器が選んだ向きの方策**全体**が throughput に効くか」
  である。両腕は別走行で最初の更新から状態軌跡が分岐するので、**同一軌跡上の反実仮想ではない。**
- **policy 2** は「同一 pre-state から推奨した一歩と逆の一歩で次窓が変わるか」に近づくが、
  **本 wave では測っていない。**
- **方向的中 0.50 から両腕の throughput 等価は導けない。** clamp の当たり方、上下限の飽和、
  動的上限の縮小 (両腕とも同じ負方向になる)、刻み適応の滞在比、parity の偏りで崩れる。
- driver の `_directional_success` に足した割当別の内訳は**記述統計であって推定量ではない。**
  推定量 (割当についての ITT) は次 wave が事前登録する。
- policy ≠ 0 の cell は現行の直列性認証の exact 2 cell に入らない。次 wave で別途認証が要る。

## 4. 診断入力の受理集合は 1 本だけ拡張した

正しさゲート (認証の exact 2 cell 契約、patch A の hard pin、既存の逐語 pin) は 1 byte も変えていない。
診断走行の exact 述語には 2 本目の literal を足した。これは**受理集合の制御された拡張**であり、
「緩めていない」とは言わない (段 3 の指摘で表現を訂正した)。

```
cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,cw-as-dyn-p1:...:1,cw-as-dyn-p2:...:2
```

Python 側 (`_validate_backoff_trace_contract`) と投入スクリプト側の 2 層に同じ literal を置き、
`,` と `+` の変換以外に差が無いことをテストで固定した。cell 書式は 5 / 11 field を不変のまま
12 field を足し、11 field と明示 policy 0 の 12 field は identity 上も区別する。

## 5. 変異検査

probe → 本走の 2 段 (`tools/mutation_harness.py --runner-mode dispatch`)。

- **probe** (`mutation-probe-spec.json` sha `ec91cd20…` / `mutation-probe-report.json`、repo HEAD c04f9fe65):
  baseline PASSED (773 passed / 63.5s)。**KILLED 16 / MISMATCH 8 / SURVIVED 1**。
  MISMATCH 8 件はすべて `expected - observed` が空、つまり事前登録した node は全部赤になった上で
  さらに赤が増えた型だった。歯が無いのではなく予測した完全集合が狭かった。
- **本走** (`mutation-spec.json` sha `736fb48a…` / `mutation-report.json`、repo HEAD 607c4c842):
  baseline PASSED。**KILLED 24 / MISMATCH 0 / SURVIVED 1 (意図した等価変異)**。25/25 一致。

**冗長 gate の扱い:** `test_ccbench_spawn_sites.py` の deferred gate 台帳 3 node は sink を
**行番号**で照合するので、driver を書き換える変異では意味と無関係に必ず一緒に赤くなる。
M15 / M16 / M17 / M18 / M21 の完全集合にはこれが含まれるが、**単独変異の独立証拠には数えない**
(DW-M03)。詳細は `mutation-notes.md`。

erratum: (1) 1 回目の投入は `--spec` が試験対象 checkout の内側にあり rc=2。checkout 外の写しへ
変更した。(2) 2 回目は baseline 赤で中止した。原因は台帳の行番号 pin が実装 fix で失効していたこと
であり、実装の欠陥ではない。(3) probe の観測で `expected_nodes` を確定させた版に `note` field を
足したところ harness の field 集合検査が拒否した (完全一致を要求する)。注記を
`mutation-notes.md` へ移した。

## 6. 段 6 の実測と、そこで見つかったもの

**子は 3 単位とも sandbox の `qstat -Q` 失敗 (rc=16) で pytest を 1 件も走らせられなかった。
親の焦点走が本 wave の最初の実測である。** 初回は赤 32 件だった。

| 赤 | 正体 | 直した先 |
|---|---|---|
| probe 認証系 23 件 | patch C が `#define` 本体でトークン貼り合わせ (`##`) を使い、`source_digest` の T-148 防壁が発火して認証経路が全停止 | patch C (防壁は迂回せず、二段の stringification と constexpr の十進 parser へ) |
| 遷移テスト 5 件 | 場面生成器が常に throughput 1,000,000 を作るのに負勾配用の前値が 2.0 しかなく、負勾配を指定しても**実勾配が正**になっていた | テスト側 (前値を 2,000,000.0 に。**実装は触っていない**) |
| 裸マクロ 1 件 | patch C の `IZANAGI_` マクロが未登録 | gate を path 単位免除ではなく**path ごとの許容 token exact 集合**へ (段 6 レビューの指摘) |
| 台帳 3 件 | 行番号 pin の失効 | 実装確定後の現物へ当て直し |

段 6 のレビューは「実装を赤に合わせて変えるな」を明記した。反転点・割当・実行可能性・実現判定の
位置と定義は裁定どおりであることが行単位で確認され、誤っていたのはテストの場面設定の側だった。

もう 1 件、**前処理検査の照合語が広すぎた**: `6364136223846793005ULL` は libstdc++ の
`mt19937_64` の定義にも現れるため policy 0 の出力にも出る。親の実測 (policy 0 = 乗数 1 / 加数 0 /
状態 0 / seed 0、policy 2 = 2 / 1 / 4 / 2) で patch は正しく検査語が誤りと確定し、
式ごと照合する形へ直した。

## 7. 成果物

- patch: `patches/cicada-adaptive-counterfactual.patch` (A+B の上に重ねる。`patches/README.md` 参照)
- 遷移テスト: `orchestrator/tests/test_dynamic_backoff_transitions.py` (68 件。policy 3 値 ×
  step_adapt × dyn_ceiling × trace の 24 構成 compile を含む)
- driver: `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` (12 field cell、trace v2 の
  parse、2 本目の exact literal、A→B→C の patch stack、schema v3)
- 登録簿: `orchestrator/campaign/condition_meaning_gate.py` / `screening_driver.py`
- 図生成器: `tools/plotting/plot_dynamic_backoff.py` (A+B と A+B+C の両方を versioned に受理。
  **既存 A+B 証拠の再生成を壊さないことだけが本 wave の scope**)
- 変異台帳: `mutation-spec.json` / `mutation-report.json` (+ probe 版)、`mutation-notes.md`
- 段 2 プラン・段 3 相談 2 本・段 4 裁定・段 6 レビュー 2 本・段 6 補正裁定・
  DW-O13 の実測: `verbatim/`

## 8. 未了と次の一手

- **測定は次 wave。** その最初の成果物は**新規の事前登録**であり、結果を見る前に次を凍結する:
  主推定量 (割当についての ITT)、等価域とその根拠、層 (workload / threads / 推奨符号 /
  割当前の境界可否 / 時間 block)、除外規則 (**処置後の clamp・action 0・outcome を見た除外は禁止**)、
  独立 seed の一覧と本数、run を cluster とする分散、目標検出力、停止規則。
- 旧事前登録 (±3%、7 腕、run 単位) は更新単位の ITT を覆わない。反実仮想 literal の走行には
  `counterfactual_preregistration: "pending"` が記録される。
- policy ≠ 0 の cell の直列性認証。
- 図が新 cell と新 event 項目を理解する改修。
- 別 session ([T-2266] 系) の実測によれば、**格子の上端 999 µs でも abort の抑制が飽和していない**
  (write-heavy で 100 µs の 0.1374 から 999 µs の 0.0424 まで単調減)。反実仮想の腕を
  **効く領域で**測る regime 選択の根拠になる。一次資料は
  `output/insights/2026-09-07_t2266-tail-measurement/README.md`。
- D1515 の再訪条件 (機序の直接確認) は**まだ満たしていない**。満たすのは policy 2 の腕 +
  新規事前登録 + 複数の独立 seed による試験である。
