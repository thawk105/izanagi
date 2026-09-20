# 段 1 brief — [T-2797] B-5 生成器対照 (α) 残部品の段階実装 → (β) launcher 設計と上限付き試走

作成 2026-09-20 19:40 JST。起点 local main `6a3e15809` (fresh worktree、開始 gate rc=0 `startup-gate.log`)。
引数逐語は `verbatim/T-2797-origin.md` (insight へ写す)。

## 研究前進

B-5 (`docs/b5-generator-contrast-preregistration.md` v1、未発効) は論文の「知識付き K2 loop が random / sweep-matched の
2 対照に固定予算下で条件付き優越するか」の実験基盤。本 wave は §10 の「実装が要る」残部品を実装し、D2172 項 4 (β) の上限
(1 workload・3 arm × 1 系列・16 session / arm + block stock 5 = 53 ≤ 60 論理 session) で試走して **verifier wall と
1 session の実所要**を実測し、§11 の総実行 wall 上限・§12 発効束の未確定値 ((γ) 2 の残部・4・6) を**裁定パッケージとして
再提示する材料**を作る。完了判定 = (1) 部品が変異 matrix 付きで main に着地、(2) 試走 53 session 以下の結果が既知結果台帳
(insight) に verifier wall 込みで残る、(3) 裁定パッケージが提示される。本走は未認可のまま (発効 commit を作らない)。

## scope (α) — Codex author (D95) の段階実装、各単位に正例・負例の変異

新 module `orchestrator/campaign/b5_generator_contrast.py` (+ `orchestrator/tests/test_b5_generator_contrast.py`) を主とし、
`p3_s4_loop.py` は必要最小の seam だけ触る (import 方向は b5 → p3_s4_loop、逆は無し = 静的 import 閉包 pin を動かさない)。

| 単位 | 部品 (§10 行) | 中身 |
|---|---|---|
| A1-a | random 生成器 (§4.2) | 整数重み `m_v = floor(2^128 ln((v+1)/v))` を `decimal` (prec 100、prec 130 で床が同一であることを検査) で算出、1000 要素表と sha256、preimage `b5-generator-contrast-v1\|random\|w\|r\|a\|c`、SHA-256 → 256 bit U、`L = floor(2^256/M)·M` の引き直し、累積重みへ写像。commit hash を seed にしない |
| A1-b | sweep の hash 順 B 点 (§4.3) | `EXTENDED_SWEEP_US` ∩ S (0 除外の 28 点、`backoff_extended_sweep.py:55`) を `b5-generator-contrast-v1\|sweep\|w\|r\|v` の SHA-256 昇順 (同 hash は v 昇順) に並べ、先頭 10 点。`MEASUREMENT_SEEDS` 順は使わない |
| A1-c | 系列開始 stock の planner 前配置 (§5.4) | 系列 driver は最初に stock (`_run_stock_control_resolved` を独立 slot の campaign で) を 1 session 測り、台帳に `stock_start` と `current_perf` (median tps) を置く。LLM arm はこれを初回 planner 入力へ渡す (random / sweep は記録のみ、分岐に使わない) |
| A1-d | session 契約の flag 束縛と品質欠測の分類 (§5.3) | 較正動作点 (`calibrated_perf(w)`: 1M / 48 / 3 s / 5 reps) + `--verify-performance` 相当を系列 driver が固定して渡す (`bench_max_rounds=3` 明示)。WAL の bench payload (`pipeline.py:1301` `_run_bench` の `tps` / `unstable` / `rounds` / `settled` / `cv`) から **品質欠測** = `len(tps) != reps ∨ unstable ∨ settled is not True` を分類し台帳へ。品質欠測は B も A も返さず、endpoint 資格なし。pipeline.py / loop.py は変えない |
| A1-e | B / A 台帳と収束停止の不適用 (§3) | 系列 driver は `drive_iteration` (入口 `check_stop`、`MAX_ITER` / `MAX_WALLTIME_S` `p3_s4_loop.py:167`) を通さず `_run_one_iteration_resolved` 相当を slot ごとに呼ぶ。A = 原提案 (空出力・schema・値域・文法・検疫・Tier0 不通過も消費)、B = pipeline 投入 (anomaly・投入後失敗・walltime も消費)。台帳は append-only JSON (atomic write)、物理試行数・retry (§3.3、機械故障のみ +2) を別記 |
| A1-f | 重複の fresh 評価 (§10) | 各 slot の campaign identity に slot key (`search_config["b5_slot"]`) を焼き、同 v でも別 campaign → `_resolve_duplicate` / terminal skip は構造的に発火しない。発火したら台帳に `duplicate-skip` として fail-closed (成功を捏造しない) |
| A1-g | endpoint 選択と再計測 (§6) | 系列内 certified かつ品質欠測でない候補のうち session median 最大 (同値は v 昇順 → slot 昇順) を endpoint に固定 (台帳へ書いてから) → 5 fresh session (別 slot campaign) を同 job で再計測。anomaly は不採用 + fallback 記録。fresh 生成の重複は許す |
| A1-h | 系列状態の継承検査 (§4.1) | LLM arm: 評価 k の planner 入力 whiteboard がその系列の評価 1〜k−1 のちょうど k−1 件であることを台帳から検査する関数 (親が proposal を置く前に呼ぶ、job 側も proposal 受理時に検査) |
| A2 | 解析 consumer (§6 / §7) | `b5_generator_contrast_report.py`: 台帳群 → score / CV / block stock CV / `f(w)`, `δ(w)` / 対差 / 全 2^n 片側 exact permutation / Holm (族 6 固定) / §7.4 の判定順。試走 (n = 1) は対不足で判定不能を返す (記述統計のみ)。合成データで正例・負例 |
| A3 | 較正・verify の job body 配線 + launcher (§10 LLM・共通 job 行) | `tools/pegasus/p3_s4_loop_pegasus.sh` に B-5 mode (env `IZANAGI_S4_B5_ARM` / `_WORKLOAD` / `_SERIES` / `_MODE` (series / block-stock) / `_LEDGER_ROOT` 等) を足し、K2 argv・既定 argv は bytes 不変。B-5 mode は系列 driver 1 起動へ `--calibrated-perf --perf-workload W --verify-performance` を渡す。LLM arm は job 内 handshake (stock → `proposal-k.json` を poll (15 s、上限 45 min) → 評価 → `slot-k.json`)。TJ (`test_p3_s4_loop_job_contract.py`) の逐語 pin・driver 呼出し箇所数を author が更新。login 側 launcher (`tools/pegasus/b5_contrast_launch.py`: env 組立と qsub argv、`--dry-run`) |

## (β) 試走 — D2172 項 4 の上限を逐語で守る

- workload = **write-heavy** (現行 verifier 3 s ≈ 115 s / 9.7 GiB、balanced ≈ 165 s、read-heavy ≈ 400 s = 除外指定)。
- 3 arm × 1 系列 (r = 1)、各 = 系列開始 stock 1 + B = 10 評価 + endpoint 再計測 5 = 16 session; block stock 5 (1 block); 合計 53 ≤ 60 論理 session。
  retry は §3.3 (機械故障のみ、同 slot +2 回まで)。結果は主標本に入れず既知結果台帳 (insight) へ。
- job = 4 本 (random 系列 / sweep 系列 / LLM 系列 / block stock)、各 1 node、gen_S (Elapse 上限 24 h)。walltime は全 arm 同一 08:00:00
  (見積り: 1 session ≈ legacy verify + 5 × (3 s trace + ≈115 s verifier) + bench 5 rep ≈ 12〜14 分 → 16 session ≈ 3.5〜4 h、LLM の親手番 10 × ≈5 分を足して ≈ 5 h、×1.5)、block stock 03:00:00。
- LLM arm = §4.1 の K2 手動 loop (親が planner-v4 / coder-v4-autonomous-k2 / critic を呼ぶ、manifest `396cd559…` = t2182 wal-only、`coder-v4-autonomous-k2`、reflux on、D2155 診断射影)。親は性能を見て助言・修正・再抽選をしない。
- 実測して残す: verifier wall (rep ごと・session ごと)、build 区間、bench wall、session 所要の分布 (max)、job Elapse、queue 待ち、親の LLM 手番の時間。

## 確定済みユーザー裁定 (変えない)

D2172 項 4 (段階裁定 (A)、(β) の上限、(γ) の切り分け、発効 commit は本走認可時)、D2183 (K2 共有 3 部品の形、pipeline / loop 不変、
stock 成功条件 = STOCK 性)、D39 決定 2 の実質改訂は「本走認可時に確認」(試走の driver は不適用を実装するが決定の改訂ではない)、
K0 arm・本走・「LLM が必要と実証した」は scope 外、規律 2 を緩めない、仮想リスク向け gate・検査・台帳・一般化は足さない。
事前登録本文 (`docs/b5-generator-contrast-preregistration.md`) の bytes は触らない (Erratum も本 wave では書かない)。

## 不変条件

- 規律 2: anomaly 1 件で即 reject、B を消費、bench 値を採らない (既存 `pipeline.evaluate` の verify → bench 順を変えない)。
- 規律 1: trace-disabled の性能値だけ、verify は別 build・別 run (既存経路)。
- `build_admission.py` / `pipeline.py` / `loop.py` / `ident.py` / `source_digest.py` / `condition_meaning_gate.py` は変更なし。
- 既定 argv (K2 / fixture / stock-control) と既定 identity preimage は bytes 不変 (TJ の pin と固定定数 test で証明)。
- 台帳は成功を捏造しない: identity 不一致・skip・snapshot 拒否は fail 側。fallback を機械故障で埋めない。
- 事前登録の数値 (B = 10、A = 30、N_eval = 5、28 点、log-uniform 重み、preimage 形式) を driver の定数として持ち、CLI で上書きしない。

## 前提の実測 (brief 前)

- 稼働中 `dev-wave-t2795-k2-pair` は main `6a3e15809` そのもの、対象 2 file の差分 0 (19:10)。同 wave は pair job `13339.nqsv` を 19:12 に投入済 (配線規模、STOCK 成立の初実測はそこから得られる — 本 wave の試走はそれを待たない)。
- `p3_s4_loop.PIN` = `511c9538…` (T-2304 の pin 前進後も独立 full OID は据え置き、entry 1747)。submit-tree は ccbench を PIN へ checkout する (peer の `setup-submit-trees.sh` と同型)。
- gen_S: 46 run / 143 req (97 待ち、19:16)、Elapse 上限 86400 s。login load 17。
- pin 閉包: 変更前 sha256 (`5e7ef15f…` / `318fae02…` / `a3648f09…`) の hit 0 (output 含む)。path pin = TJ 逐語 7 + 呼出し箇所数、`test_p3_exploration_namespace.py` / `test_p3_b4_wiring_probe.py` (静的 inventory 11 / 2 / 49)、`test_campaign.py:5418` (run_campaign caller 2)、`test_official_perf_closure.py:60` (perf file inventory、新 module が perf 名で分岐すれば追加要)、`tools/pegasus/admission_registry.json:112` (job body 登録、同 file 拡張なら不変)。
- `--verify-performance` は legacy 1 + performance `reps` = 5 回の verify (`pipeline.py:193, 2180`)。§5.5 は回数を定めない。**1 session の verifier 費用の 5/6 がここ** → 裁定パッケージの費用項 (削減は D2183 の形の変更なので本 wave では変えない)。
- `pipeline._run_bench` は `unstable` を abort にせず COMMIT に残す (`require_all_reps` は qualification policy 専用) → 品質欠測は台帳側の分類で担う (P3)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) slot ごとの fresh layout は search_config の slot key で identity を分ける (fresh submit-tree を評価ごとに切らない)。
- (P2) 系列 driver は `drive_iteration` を迂回し `check_stop` を呼ばない。B 完走の保証は台帳 + driver のループで機械化する。
- (P3) 品質欠測は WAL bench payload からの分類 (pipeline は変えない)。品質欠測 session は endpoint 資格なし・B は返さない。
- (P4) LLM arm は job 内 handshake (§5.4 の「同 job」を満たす唯一の形)。random / sweep は 1 job に系列全体 (stock + 10 + endpoint 5)。
- (P5) job body は既存 file に B-5 mode を足す (別 file にしない = 300 行の preamble を複製しない)。TJ pin は author が更新。
- (P6) `decimal` prec 100 の重み表 + prec 130 での床同一検査。
- (P7) consumer は n = 1 で判定不能 (対不足) を返し記述統計だけ出す。
- (P8) 試走 workload = write-heavy。walltime 08:00:00 全 arm 同一、block stock 03:00:00。

## 成果物の形

- 実装 commit (Codex author、`AI-Agent:` trailer) + 変異 matrix + 焦点走 + 受入 + land。
- 試走: job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/` (submit-tree、evidence、台帳、LLM 手番の材料)、
  insight `output/insights/2026-09-20/t2797-b5-contrast/` (既知結果台帳、verifier wall、裁定パッケージ、逐語)。
- spool fragment: worklog (T-2797 / T-1872 更新)、decisions (設計判断)、failures (該当時)。

## 分割方針

段 2 plan 1 本 (read-only) → 段 3 consult 2 本 (レンズ A: 事前登録 §3〜§7 の逐語適合と正しさ境界、レンズ B: launcher / job 契約 /
pin 閉包 / 過剰実装) → 段 4 裁定 → 段 5 author: A1 (core module + tests) → A2 (report) ∥ A3 (job body + launcher + TJ) →
段 6 review 2 本 + fix + 変異 matrix + 焦点走 → 試走投入 (4 job) → 待機中に docs → 記録 → 受入 → land。
軽量版でない理由: 設計択一が割れる (P1〜P5)・実装面が広い・試走が実機を使う。
