# [T-2188] 段 1 brief — 刻み応答の非単調性の機序を切り分ける

2026-09-09 07:35 JST。base `cbcdb6c91` (local main)。branch `worktree-dev-wave-t2188-nonmonotonic-mechanism`。

## 研究前進

進む主張は「Cicada 型 adaptive backoff の刻みに対する非単調な応答 (0.5 µs 最良 / 5〜25 µs 谷 /
100 µs でやや回復) は、更新窓が狭いとき勾配符号がノイズに支配されて歩行が酔歩化することで生じる」の
**真偽判定**である。現在の材料はこの説明と整合するだけで、直接観測が 0 件のまま
`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` §5 が
「機序は確定していない」と明記している。止めているのは `Backoff_` 時系列と勾配符号的中率の実測で、
最小差分は「窓 10 µs での trace を刻み軸に沿って 6 点取り、既存の 2560 µs 窓の trace を対照に置く」こと。
完了判定は「窓 10 µs と窓 2560 µs の**符号的中率**が、事前に決めた向きと差で分離するか否かを、
どちらの結果でも記録できる形で出す」。図は刻み × (符号的中率, 滞在分布, 実効窓幅) の 3 段。

## 引数の前提の実測結果 (2 件、うち 1 件は引数を狭める向き)

1. **「既存の probe 成果物で切り分けられる範囲」は 2 件あり、どちらも未使用である。**
   (a) `output/insights/2026-08-28_t1941-backoff-requested-us/README.md` が、**stock 適応
   (刻み 100 µs / 窓 10 µs / 上限 1000、`BACK_OFF=1, BACKOFF_FIXED=-1`)** の `Backoff_` 滞在分布を
   実測済み (balanced・48 スレッド・1 rep・call 931,274 件、state 0 = 51.555%、100 = 25.571%、
   200 = 6.184% … 1000 = 1.308%、平均要求 135.19 µs/call)。T-2216 §4-bis の歩行 model は
   刻み 100 µs で `P(Backoff_ > 100 µs) = 0.253`・中央値 100 µs を予測しており、**突き合わせは誰も
   していない。実測の最頻値は 0、model の中央値は 100** で、形が違う。
   (b) `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/` に `Backoff_` の時系列 trace が
   26 file ある。record は `window_us / window_commits / backoff_before / backoff_after /
   gradient_sign / step_us / parity_branch / trigger`、`directional_success` (符号的中率) も算出済み。
2. **ただし記録済み trace 26 file は全部が「刻み 1.0 µs・更新間隔 2560 µs」である (実測)。**
   セルは cw / cw-as / cw-as-dyn / cw-as-dyn-p{0,1,2} / cw-as-dyn-c2-p{0,1,2}、24・48 スレッド ×
   3 workload。**窓 10 µs の trace は 1 本も無い。**非単調性は窓 10 µs の下でだけ現れる (D1505) ので、
   **既存 trace だけでは本題は決まらない。**引数の「既存 probe 成果物で切り分けられる範囲」は
   (1) の 2 件であって、機序判定そのものではない。

## scope

- **単位 A (再解析、実装面):** 既存成果物だけで閉じる。(a) T-1941 の滞在分布と T-2216 歩行 model 予測の
  突き合わせ、(b) 既存 trace 26 file から窓 2560 µs 側の符号的中率・窓内 commit 数分布 (Poisson 仮定の
  検査)・実効窓幅分布を出す。**これは窓が広い側の対照であり、単独では機序を決めない。**
- **単位 B (計測経路、実装面):** `--backoff-trace` に第 4 の診断セル集合 (窓 10 µs、刻み
  {0.5, 1, 2, 5, 25, 100} µs、上限 1000、write-heavy、48 スレッド、extime 3 秒、rep 1) を足し、
  Pegasus へ投入して trace を取る。
- **単位 C (記録):** insight + worklog + decisions fragment。
- **scope 外:** 仮想リスク向けの gate・検査・台帳・一般化の追加 (ユーザー明示)。上限軸の再評価、
  balanced/read-heavy への一般化、認証 (規律 2 の下で性能値は非認証のまま)。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1-1) 単位 B は F660 に当たらない。** 根拠: `tools/pegasus/admission_registry.json` (main 側現物) は
  `t2187_adaptive_const_probe.py` / `.pbs` を **path で登録し hash を持たない**。新規実行体は作らない。
  先例として 2026-09-05 の dynamic-backoff wave は同じ file に `TRACE_CELLS_TEXT` を新設して同一 wave 内で
  実測している (artifact `repo_head 27bdca58b…`)。**攻撃してよい: 登録簿以外の防壁が bytes を見ていないか。**
- **(P1-2) 窓 10 µs で trace を取ると観測者効果が本題を壊しうる。** 更新頻度が 256 倍になり、
  ring への store も 256 倍になる。**陽性対照を必ず置く: trace 付き走行の throughput が、刻み 25 µs 付近で
  既知の谷 (1.24〜1.38 M tps、48 スレッド write-heavy) を再現するか。**再現しなければ trace が現象を
  壊しており、その事実を結論として記録する (説明を作文しない)。
- **(P1-3) ring 容量 65536 は窓 10 µs では溢れる。** 3 秒 × 名目 10 µs = 約 30 万更新。保持されるのは
  **末尾 65536 件**で `dropped` が立つ。定常統計としては許容だが「走行末尾約 0.65 秒の標本」であることを
  限界として明記する。**攻撃してよい: 末尾偏りが符号的中率を系統的に動かさないか。**
- **(P1-4) 単位 A の (a) は workload が違う。** T-1941 は balanced、T-2216 の model と谷は write-heavy。
  **比較は形 (最頻値・裾) に限り、値の一致・不一致を機序の判定に使わない。**
- **(P1-5) 編集面が稼働中の別 wave と衝突する。** [T-2213] の wave が今まさに
  `t2187_adaptive_const_probe.py` の build 地点を condition meaning gate へ配線している (ListAgents で実測)。
  親の暫定裁定は「衝突は許容し、変更を定数追加 + 受理分岐 1 本に閉じて region を離す」。

## 不変条件

- 規律 1: trace build と性能計測 build は別ビルド・別 run。trace は `BACKOFF_TRACE` のコンパイル時除去で、
  性能ビルドの symbol/string count 0 を driver が既に検査する。**この検査を緩めない。**
- 規律 2: 本 wave の値はすべて **非認証** (`certified: false`、`headline_eligible: false`、
  `throughput_scope: diagnostic_only`)。variant 採用・headline・formal B-10・floor・fitness に使わない。
- 規律 3: 判定は「どちらの結果でも記録する」形にし、閾値と向きを**結果を見る前に**書く。
- 規律 4: 標本は最小 (1 workload × 48 スレッド × 6 刻み × extime 3 秒 × rep 1)。
- 規律 7: 既存測定 (T-1941、T-2216、既存 trace) は現行コードとの差だけを理由に無効化しない。
- 凍結: `_validate_backoff_trace_contract` の受理集合と `.pbs` の `*_TRACE_CELLS_RAW` 群は
  `test_two_layer_trace_literals_are_byte_identical` が **順序込みで exact pin** している。
  反実仮想 2 集合の事前登録 sha 束縛 (`docs/backoff-counterfactual-preregistration.md`、
  `…-cohort2-…`) には**触れない** — 新集合は `TRACE_CELLS_TEXT` と同じ「事前登録束縛なし」の型にする。

## 変更面 (実アンカー)

| path | anchor | 変更の性質 |
|---|---|---|
| `tools/pegasus/probes/t2187_adaptive_const_probe.py` | `TRACE_CELLS_TEXT` (367)、`_validate_backoff_trace_contract` (3045)、`_artifact_contract_metadata` (3089) | 定数追加 + 受理分岐 1 本 + 軸の許容 |
| `tools/pegasus/probes/t2187_adaptive_const_probe.pbs` | `*_TRACE_CELLS_RAW=` 群 | RAW literal 1 本追加 (順序末尾) |
| `orchestrator/tests/test_t2187_adaptive_const_probe.py` | `test_two_layer_trace_literals_are_byte_identical` (2905)、`test_backoff_trace_mode_requires_exact_diagnostic_axes` | pin 更新 + 新受理/拒否の対 |
| `orchestrator/campaign/` (新規 1 file 想定) | — | 単位 A/B の解析器 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新 nodeid | main 取り込み後に 1 回 |

## 成果物の形

`output/insights/2026-09-09_t2188-nonmonotonic-mechanism/` に README + figures + verbatim。
worklog 1 エントリ。decisions fragment (機序の判定と、判定できなかった場合はその範囲)。

## 並列分割方針

単位 A (再解析器) と単位 B (trace 契約 + 投入) は編集面が交わらないので実装子 2 本を並列。
段 2 は plan 子 1 本、段 3 は敵対相談 2 レンズ (レンズ 1 = 観測者効果と標本偏り、
レンズ 2 = 受理集合と凍結 pin の閉包)。

## 受入・実測環境

受入全走は login node (`tools/run_tests.py`)。実測は Pegasus 計算ノード、
所在と作法は `docs/pegasus-runbook.md`、環境契約は `docs/orchestrator-design.md`。
