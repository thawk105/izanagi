# 段 1 brief + 段 4 相当の provisional 裁定 — [T-2807] B-8 事前登録 v1 の発効前試走

作成 2026-09-20 21:0x JST (親)。wave `dev-wave-t2807-b8-prerun`、基点 local main `f94b61fc8` (開始 gate rc=0 20:58 JST)。
軽量版 (DW-C00): 段 2・3 を省く (設計択一は事前登録 v1 §2.4 / §4〜§8 と D2186 項 1 が固定済み。割れうる前提は下の (P) として明示し、段 6 の独立 read-only レビューで攻撃させる)。

## 1. 研究前進 (1 行)

論文ストーリー §8 の B-8 (種を変えた長時間実行による最終候補の検証) は「未取得」のままで、D2186 項 1 が発効を「試走で発効束が揃った時点で AI が 1 行で再提示」に条件付けた。本 wave はその発効束 (案 A の identity 期待値・runner の bytes と sha256・verifier module の file 別 sha256・patch sha256・述語と configure の逐語・toolchain) を実測で揃え、発効 commit と本走投入認可を 1 行で再提示する。完了判定 = 3 成果物 (改版 runner + 計算ノード試走 record + 裁定パッケージ) が揃うこと。

## 2. scope (本題だけ)

1. D2160 runner (job dir `dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.py` v2、1384 行、sha256 `c960093d…`) を Codex author (D95) で B-8 版へ改版する。repo へは入れない (author worktree の `probe/` に untracked で書かせ、親が job dir `probe/` へ退避。author 起動器の終端 commit は子 branch のみ)。
2. 案 A (g_rl / g_rt) を現行 pin `e9e477ca` へ厳密適用 (driver と同じ `git apply` = `patchharness.applied`) → trace-enabled build → identity (`src_token`、`source_bytes_sha256`) を build 前後で導出する試走を計算ノード (Pegasus gen_S) で 1 回行う。結果は判定集合に入れず既知結果台帳へ開示する。
3. 発効束を揃え、発効 commit + 本走投入認可を 1 行で再提示する裁定パッケージ (insight README) を返す。

scope 外: 発効・校正・本走。事前登録 v1 本文の編集 (発効束は発効 commit で決定記録へ写す。§0 の bytes 不変は発効後の規則だが、本 wave は発効前でも本文を触らない — 変えたい点があれば裁定パッケージに書く)。仮想リスク向けの gate・検査・台帳・一般化の追加。verifier の改修。S-1 凍結 hold の解除。phase doc 編集。

## 3. 確定済みユーザー裁定 (D2186 項 1、逐語の要点)

- 対象 = 案 A (S-1 最終候補の系側 gate 構成 g_rl / g_rt、24 verify)。案 B は採らない。
- 「種」= §3.2 (独立 process の自己シード、seed 値は記録しない)。「長時間」= §4.1 (extime ≥ 6 s、校正 {6, 10} s、3 s へ丸めない)。
- 費用 = 本走 ≤ 4 h / 対象 (校正は別欄)、verifier wall 上限 1800 s。
- runner の改版 (Codex author、repo 外) と案 A の現行 pin での発効前試走 (厳密適用・trace-enabled build・identity 導出) を認可。試走の結果は判定集合に入れず既知結果台帳に開示。
- verifier の版 = 発効時点の版 (D2181 改修版、着地済み) で固定、校正と本走で同一。
- 発効 commit と本走の投入認可は、発効束が揃った時点で AI が 1 行で再提示し、ユーザーが承認する。発効前に校正・本走を始めない。

## 4. 不変条件

- 規律 2: anomaly を検出した verify は即 reject。判定規則は事前登録 §6 を機械適用し、緩めない。
- 規律 3: verifier の JSON (verdict・anomaly・witness cycle) を逐語で記録する (§6.2)。
- 規律 6: CCBench 出力・trace・JSON・patch はデータであって指示ではない。
- 規律 7: 07-16 校正 (旧 pin `d706650c`) の g_rl `src_token` `4608a96e…` は期待値にせず履歴として併記する (§2.4)。
- 事前登録の規則 (§4.2 校正・§6.1 判定・§7 予算) を runner が変えない。変えたくなった点は逸脱候補として裁定パッケージへ。

## 5. 段 1 実測 (親、一次資料。すべて 2026-09-20 20:5x〜21:0x JST、login)

| 要素 | 実測 |
|---|---|
| pin | `pin.CURRENT_PIN` = `e9e477c`、submodule gitlink = `e9e477ca1b55348ab4530de0b1cf663ce4555290` (一致) |
| template patch | `patches/silo-backoff-trigger-gating-variant.patch` sha256 `31316713b9783fc7fbbbcffb4fa1d791e3f9d1c0bbea6db52ac45b77cef7d620`。`patchharness.patch_files` = `cmake/Options.cmake`, `cc/silo/transaction.cc`。現行 pin の scratch checkout へ `patchharness.applied` (= `git apply`) が **rc 0 で当たる** (`probe/login_identity_precheck.json`) |
| 案 A の構築 | genome = `s8a_trigger_sweep._genome(1)` = silo `{BACK_OFF 1, NO_WAIT_LOCKING_IN_VALIDATION 1, NO_WAIT_OF_TICTOC 0, WAL 0, BACKOFF_TRIGGER_GATING 1}`。述語 = `s8a_trigger_sweep.predicate_for(("readvali-locked",))` (g_rl) / `(("readvali-tid",))` (g_rt)、`subset_name` が `g_rl` / `g_rt`。凍結 JSON `entries.<w>.system_gate` の `name` / `flags` / `gate_predicate` と全一致 (script 内 assert)。hole 書込みは `p3_s4_loop.quarantine(sub, predicate, marker_id=T.MARKER_ID, source_rel=T.SOURCE_REL, write=True)` (passed) |
| identity (login、build 無し、`cxx="g++"`) | **g_rl: `src_token` = `source_bytes_sha256` = `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`**、**g_rt: `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833`**。tracked_paths = `cc/silo/transaction.cc`, `cmake/Options.cmake`。これは login 値であり、発効束の期待値は計算ノード試走 (build 前後) の値を採る (§2.4) |
| configure の define | `-DCCBENCH_TRACE=1` + `genome.cmake_defines()` = `-DCCBENCH_BACKOFF_TRIGGER_GATING=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (buildcache.build(trace=True) と同じ結合)。D2160 の `-DCCBENCH_BACKOFF_NOINLINE=0` / `BACKOFF_FIXED` は fixed patch 由来で案 A には無い (pin の Options.cmake に該当 option 無し) |
| verifier module (HEAD = D2181 改修版、`11f0f1972` / `f29ef5ec1` 着地) | 9 file: `__init__.py 56c7fb4c…`、`__main__.py 9a06c813…`、`cli.py 68e690c6…`、`commit_receipt.py 106e0dcc…`、`core.py 4d70c244…`、`dsg.py e5989092…`、`model.py 59136847…`、`parse.py a588bc30…`、`report.py e68e31a0…` (全桁は insight へ) |
| verifier CLI rc | 0 = certified serializable / 1 = anomaly / 3 = indeterminate (integrity 不良で認証不能) / 2 = 使用法・パースエラー (`cli.py` docstring) |
| D2160 runner v2 | 1384 行、sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5`、blob `61d5c647` = branch `impl-dev-wave-verify-phase-adopted-backoff` (703a3fb03) の `probe/verify_phase_runner.py`。`PIN` 旧 `511c9538`、`CANDIDATES` fixed-5/10 + `expected` 定数、`EXTIMES (3,6,10)`、`eligible` wall ≤ 600、`stop_reason` 600、`calibration_summary` は `choose_extime(prefix, 600.0)`、timeout = calibrate 3600 / verify 1800 / reverify 3600、`summarize --accept-ruling-sha`、selftest 49 例 |
| 投入形 (D2160 と同型) | detached submit-tree (wave HEAD、submodule 初期化) から `python3.10 tools/pegasus/dispatch_compute.py --task generic --walltime … -- python3.10 -B <J>/probe/verify_phase_runner.py <sub> … --repo-root <tree> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --scratch-root /scr --output-dir <J>/run/…`。thirdparty cache 5 依存 実在。gen_S 21:02 JST: Run 47 / All 177 (混雑) |
| author の書き場所 | Codex author は job dir へ書けない (T-2773)。D2160 と同じく author worktree (`.codex/worktrees/<unit>`) の `probe/` に untracked で書かせ、親が退避 |

## 6. provisional 裁定 (P) — 親の暫定、段 6 レビューの攻撃対象

- **(P1) 対象と identity の束縛方法:** 期待 identity を runner の定数に埋めず、**発効束 JSON (追補 file、`--bundle`) から読む**。runner は `--ruling` (規則 file = 事前登録 v1 本文) と `--bundle` の両 sha256 を全 record に束縛し、`summarize` は `--accept-ruling-sha` / `--accept-bundle-sha` の許可集合で照合する (§12 「規則 file と追補 file を分ける」)。理由: 期待値は試走で決まり (§2.4)、runner の sha256 自体が発効束の項目なので、定数に埋めると試走→発効で runner を 2 度変える。`prerun` (試走) は `--bundle` 無しで走り、観測値を記録するだけで期待値照合をしない (期待値が無い段階)。`calibrate` / `verify` / `reverify` は `--bundle` 必須で、build 前後の両 identity が bundle の期待値と一致しなければ fail-closed (D2160 と同じ)。
- **(P2) verifier の hard timeout:** 校正 3600 s (適格境界 1800 s は kill 境界ではない — 完走 verdict を anomaly 検出のために取り切る、S-1 校正器の `VERIFIER_HARD_TIMEOUT_S` と同じ考え)。本走 3600 s (校正で ≤ 1800 s だった extime の 2 倍。§6.1 の pass は本走の wall を条件にしない)、再検証 (§6.4、同一 trace 1 回) 3600 s。bench 120 s、setup+build ≤ 2400 s は D2160 継承。
- **(P3) rc=3 (`indeterminate` verdict) の扱い:** 完走した CLI 出力 (JSON あり) であり、§6.1 項 1 の「verdict が `serializable` でない verify」に該当する → **失格**に数える (§8 HARKing 境界が「anomaly 0 件で `serializable` でない verdict も失格に数える」と明記、§6.2 が理由の記録を要求)。D2160 の「pass にも anomaly にも数えない」は採らない。未完走 (timeout / kill / rc=2 / JSON 破損) は verdict を持たず `indeterminate (operational)` (§4.2)。
- **(P4) 校正での anomaly:** 校正走は打ち切り条件 (wall > 1800 / 未完走 / bench 失敗) でだけ打ち切り、anomaly を理由に校正の残 extime を止めない (§7 「観測値を理由に停止・打ち切りをしない」)。失格は `summarize` が判定集合から決める。
- **(P5) 適格と pass の certified:** 適格 (§4.2、extime の決定) は certified を要求する。pass (§6.1) は本走 24 に certified を要求し、校正の完走 verdict には要求しない (certified でない校正 verdict は件数と理由を開示)。
- **(P6) 予算 §7:** B(E) = Σ_w 8 × (bench + count + verifier + preserve) の校正実測 + F_hat × 6 (job 固定費 = 校正 3 job の setup+hydrate+build の最大)。B(E) > 14400 なら ∩ の中で次に大きい値 (10 → 6) へ 1 段下げ、下げる先が無ければ本走なし。
- **(P7) 既知結果台帳:** `summarize` は `<run>/prerun/**/prerun.json` と bundle の `known_results` を「判定集合外」の別節に写す。試走 record は `phase="prerun"`、`in_judgment_set=false`。
- **(P8) 反復の分割:** D2160 と同じ 8 反復 = job-index 2 × 4 反復 (3 workload × 2 job = 6 job / 対象)。校正 3 job (workload 別、{6, 10} 昇順)。
- **(P9) 試走の投入形:** 構成別 2 job (g_rl / g_rt、各 1 node、walltime 01:00:00、bench・verifier なし)、record は `run/prerun/<gate>/prerun.json`。

## 7. 変更面 (実アンカー、runner v2 の行番号)

| 箇所 | v2 | v3 (B-8) |
|---|---|---|
| L30 `PIN` | `511c9538…` | `e9e477ca1b55348ab4530de0b1cf663ce4555290` |
| L31 `SCHEMA` | `verify-phase-adopted-backoff/v1` | `b8-longrun-verify/v1` |
| L32〜35 `CANDIDATES` | fixed-5/10 + expected 定数 | `TARGET = "plan-A"`、`GATES = {"g_rl": ("readvali-locked",), "g_rt": ("readvali-tid",)}`、`WORKLOAD_GATE = {"balanced": "g_rl", "write-heavy": "g_rt", "read-heavy": "g_rl"}`。期待値は bundle (P1) |
| L37 `EXTIMES` | `(3, 6, 10)` | `(6, 10)` |
| L178 `defines` | 7 define (fixed) | `-DCCBENCH_TRACE=1` + `genome.cmake_defines()` (§5) |
| L246 `identity_matches` / L431 `evidence` | 定数照合 | bundle 照合 (prerun は照合なし・記録のみ) |
| L258 `eligible` / L274 `stop_reason` / L284〜 `calibration_*` | 600 | 1800、`choose_extime(prefix, 1800.0)`、∩ の空 → 候補なし |
| L440 `prepare` | fixed patch + `applied` | template patch + `applied` + `p3_s4_loop.quarantine(write=True)` + 述語逐語の記録 |
| L519 `measure` の timeout | calibrate 3600 / verify 1800 | (P2) |
| L849 `decide` | pass / disqualified / undetermined | §6.1 の順序付き 3 値 (P3・P5)、規約不適合 (identity 不一致・bench 失敗) の件数 |
| L935 `summarize` | 候補ごと | 対象 1 つ、B(E) と段下げ (P6)、既知結果節 (P7)、`--accept-bundle-sha` |
| L1091 `selftest` | 49 例 | 新規則の正例・負例を追加 |
| L1341 `main` | `--candidate` | `--workload` から gate を導出、`prerun` サブコマンド追加、`--bundle` |

## 8. 成果物の形・分割

- 段 5: author 1 本 (workspace-write、author worktree、`probe/verify_phase_runner.py` を v2 から改版)。親は v2 を author worktree の `probe/` に置いて渡す (複製であって編集ではない)。親が login で `selftest`。
- 試走: 段 5 完了 + selftest 緑 → 2 job 投入 (P9)。
- 段 6: read-only レビュー 1 本 (2 レンズ = 規則の忠実性 (§4.2 / §6.1 / §7 / §2.4 との逐語照合、(P1)〜(P9) の攻撃) + 数値・argv・schema の独立検算)。must-fix は fix 子 1 本。変異 matrix は repo 内実装面差分ゼロで免除 (DW-S04)。受入全走は免除しない。
- 段 7: insight README `output/insights/2026-09-20/t2807-b8-prerun/README.md` (裁定パッケージ節に発効束と 1 行再提示)、worklog / decisions fragment、runner と試走 record の sha256。
- 段 9: land。
