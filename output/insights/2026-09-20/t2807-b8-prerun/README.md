# [T-2807] B-8 事前登録 v1 の発効前試走 — runner を B-8 の規則へ改版 (v5)、案 A (g_rl / g_rt) を現行 pin `e9e477ca` に厳密適用して trace-enabled build と identity を計算ノードで導出、発効束を揃えて発効 commit + 本走認可を 1 行で再提示する (docs のみ、runner は repo 外)

- wave: `worktree-dev-wave-t2807-b8-prerun` (背景 job、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/`)
- 起点 local main: `f94b61fc8` (着手時 `7baf3f375` から ff、開始 gate rc=0 20:58 JST)。**実装面 (repo 内) の差分 0** (本 README・`verbatim/`・worklog / decisions fragment のみ)。runner v5 (Codex `role=author` + `fix` × 2 作) は repo へ入れず job dir に保全 (§9)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- 依頼: D2186 項 1 (第 26 回裁定、段階認可) の試走手番。(1) D2160 runner を B-8 §4〜§7 の規則へ改版、(2) 案 A を現行 pin へ厳密適用 → trace-enabled build → identity を計算ノードで導出 (結果は判定集合に入れず既知結果台帳へ開示)、(3) 発効束を揃え発効 commit と本走の投入認可を 1 行で再提示。**発効・校正・本走は行っていない**
- **新規の測定投入は計算ノード job 6 本** (試走 v3: `13588.nqsv` g_rl / `13587.nqsv` g_rt、試走 v5: `13657.nqsv` g_rl / `13656.nqsv` g_rt、試走 v4: `13622.nqsv` g_rl / `13621.nqsv` g_rt、gen_S、各 Elapse ≈ 36 S、bench・verifier なし)。性能値は取らない (規律 1)
- 設計判断 (親裁定) は `{{D:t2807-b8-prerun-runner-and-bundle}}`、段 6 の独立レビュー 2 本 + 焦点 2 本の所見と対応は §10

---

## 1. 一行で

**案 A (S-1 最終候補の系側 gate 構成 g_rl / g_rt) は現行 CCBench pin `e9e477ca` へ driver と同じ `git apply` (`patchharness.applied`) で厳密に当たり、gate 述語の hole 書込み (`p3_s4_loop.quarantine`) と trace-enabled build を計算ノードで通し、identity は g_rl = `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`、g_rt = `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` (`src_token` = `source_bytes_sha256`、build 前後で一致、login 事前照合とも一致) と導出された。** 07-16 校正の g_rl `4608a96e…` (旧 pin `d706650c`) とは当然に異なり、期待値にしない (§2.4、規律 7)。runner は D2160 版 (v2、1384 行) から B-8 の規則 (校正 {6, 10} s・適格 wall ≤ 1800 s・§6.1 の順序付き 3 値・§5 の bench 不再生成 (保全済み trace の初回 verifier 再開は維持)・§7 の予算と段下げ・§8 の既知結果台帳・発効束 JSON の sha256 束縛) へ改版した v5 (2103 行、sha256 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`、selftest 166/166。author 1 本 + fix 2 巡) になった。§7 に発効束の全項目と、発効 commit + 本走認可の 1 行再提示を置く。

---

## 2. 段 1 実測 (親、一次資料、login、2026-09-20 20:5x〜21:0x JST)

| 要素 | 実測 |
|---|---|
| pin | `pin.CURRENT_PIN` = `e9e477c`、submodule gitlink = `e9e477ca1b55348ab4530de0b1cf663ce4555290` (一致) |
| template patch | `patches/silo-backoff-trigger-gating-variant.patch` sha256 `31316713b9783fc7fbbbcffb4fa1d791e3f9d1c0bbea6db52ac45b77cef7d620`。`patchharness.patch_files` = `cmake/Options.cmake`, `cc/silo/transaction.cc`。現行 pin の scratch checkout へ `patchharness.applied` (= `git apply`) が rc 0 で当たる (`verbatim/login_identity_precheck.json`) |
| 案 A の構築経路 | `s1_verify_extime_calibration._build_target` と同型: `applied(template)` → `p3_s4_loop.quarantine(sub, predicate, marker_id, source_rel, write=True)` → `source_digest.resolve_evidence(genome, PIN, ccbench_dir, cxx="g++")` → build。genome = `s8a_trigger_sweep._genome(1)` = silo `{BACK_OFF 1, NO_WAIT_LOCKING_IN_VALIDATION 1, NO_WAIT_OF_TICTOC 0, WAL 0, BACKOFF_TRIGGER_GATING 1}`。述語 = `predicate_for(("readvali-locked",))` (g_rl) / `(("readvali-tid",))` (g_rt)、`subset_name` が `g_rl` / `g_rt`。凍結 JSON `entries.<w>.system_gate` の `name` / `flags` / `gate_predicate` と全一致 (script 内 assert) |
| identity (login、build 無し) | g_rl `b0f95b21…a670d`、g_rt `a0219ce0…2f833` (試走と一致、§5) |
| configure の define | `-DCCBENCH_TRACE=1` + `genome.cmake_defines()` = `-DCCBENCH_BACKOFF_TRIGGER_GATING=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (6 個。`buildcache.build(trace=True)` と同じ結合。D2160 の `BACKOFF_NOINLINE` / `BACKOFF_FIXED` は fixed patch 由来で案 A には無い — pin の `Options.cmake` に該当 option 無し) |
| verifier module (HEAD = D2181 改修版、`11f0f1972` / `f29ef5ec1` 着地済み) | 9 file の sha256 は §7 の表 (試走 record と一致) |
| verifier CLI rc | 0 = certified serializable / 1 = anomaly / 3 = indeterminate (integrity 不良で認証不能) / 2 = 使用法・パースエラー |
| D2160 runner v2 | 1384 行、sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5` (= branch `impl-dev-wave-verify-phase-adopted-backoff` の blob `61d5c647`)。`PIN` 旧 `511c9538`、fixed-5/10 の期待値定数、`EXTIMES (3,6,10)`、適格 wall ≤ 600、bench 失敗の attempt-2、timeout 校正 3600 / 本走 1800 |
| gen_S | 21:02 JST に Run 47 / All 177 (混雑) だが、試走 job は投入 1 分で開始した |

---

## 3. runner の改版 — v2 (D2160) → v5 (B-8)

| 箇所 | v2 (D2160) | v5 (B-8) | 規則の出所 |
|---|---|---|---|
| 対象 | fixed-5 / fixed-10 (`BACKOFF_FIXED` 定数) + 期待 identity 定数 | `TARGET = "plan-A"`、`GATES = {g_rl: (readvali-locked,), g_rt: (readvali-tid,)}`、`WORKLOAD_GATE = {balanced: g_rl, write-heavy: g_rt, read-heavy: g_rl}`。それ以外の組は拒否 | 事前登録 §2.1 |
| 期待 identity | runner 定数 | **発効束 JSON (`--bundle`、追補 file) から読み、`calibrate` / `verify` / `reverify` は build 前後の両観測が一致しなければ fail-closed。`prerun` (試走) は期待値照合をせず観測を記録するだけ (build 前後の一致だけ検査)** | §2.4、§12「規則 file と追補 file を分ける」、(P1) |
| 束縛 | `--ruling` の sha256 | `--ruling` (規則 file = 事前登録 v1 本文) と `--bundle` の両 sha256 を全 record へ。`summarize --accept-ruling-sha` / `--accept-bundle-sha` | §0、§12 |
| pin / patch | `511c9538` / `silo-backoff-fixed.patch` | `e9e477ca1b55…5290` / `silo-backoff-trigger-gating-variant.patch` + `quarantine(write=True)` で述語を hole へ | §2.1 |
| extime | {3, 6, 10} | **{6, 10}**、`--extimes` は `6,10` 以外を拒否。共有 `choose_extime` は (3,6,10) を内部固定するため runner 内に同じ選択規則の (6,10) 版 | §4.1 / §4.2 |
| 適格 | wall ≤ 600 | **wall ≤ 1800.0** (1800.0 は適格、1800.001 は不適格)。打ち切り = wall > 1800 / 未完走 / bench 失敗 → その extime 以上を `not_run`。anomaly は打ち切り条件にしない | §4.2、(P4) |
| 対象の extime | 候補ごと ∩ の最大 | 3 workload の適格集合の共通部分の最大値。空なら候補なし (6 s へも 3 s へも丸めない) | §4.2 |
| 予算 | B_hat ≤ 14400、段下げ 10→6→3 | B(E) = Σ_w 8 × (bench + count + verifier + preserve) + F_hat × 6、> 14400 なら ∩ 内で 10 → 6、下げる先が無ければ本走なし | §7、(P6) |
| 判定 | pass / disqualified / undetermined | **§6.1 の順序付き 3 値**: 1. 失格 = 判定集合 (本走 24 ∪ 校正の完走 verdict) に verifier 完走 ∧ (`anomaly_count` ≥ 1 ∨ verdict ≠ `serializable`) が 1 件以上 (rc=3 の `indeterminate` verdict も失格、(P3))。**失格は混入・sha 不一致・規約不適合の有無に関わらず先に評価 ((P11))**。2. pass = 本走 24 がすべて bench 完走・保全済み・verifier 完走・serializable・certified・anomaly 0・identity 一致 (校正 verdict に certified を要求しない、(P5))。3. 未確定 = それ以外 | §6.1、§8 |
| bench 失敗 | attempt-2 を 1 回 | **再生成しない**。bench 失敗 (開始して失敗) は当該 rep を 1 attempt で終端、規約不適合として開示、**校正・本走を問わず 1 件でもあれば pass にならず未確定**。校正で出れば `stage_B_allowed=false` (打ち切りの `not_run` は失敗でない、(P10))。`verify --resume` は既存 rep を 4 分類: bench 失敗 = 終端 / verifier 起動済み = skip / **保全済み・verifier 未開始 = 保全 trace を復元 (sha256 照合) して初回 verifier を 1800 s で走らせ同じ attempt-1 を更新 (bench 不変)** / 保全未完了 = 規約不適合で終端 (v5、焦点 1 巡目の must-fix) | §5、§6.4 |
| job 段の失敗 record | 集計が読まない | `calib/*/result.json` / `verify/*/result.json` (identity 不一致・実行失敗) も規約不適合として開示し pass を妨げる | §2.4、§6.1 |
| verifier hard timeout | 校正 3600 / 本走 1800 / 再検証 3600 | **校正 3600 (§11 の想定) / 本走 1800 (§12・D2186 (5) の上限) / 再検証 3600 (§6.4、D2160 継承)** | (P2) 改訂 |
| 既知結果台帳 | — | `summarize` は `<run>/prerun/**/prerun.json` と bundle の `known_results` を判定集合外の別節に写す。試走 record は `phase="prerun"`、`in_judgment_set=false` | §8、(P7) |
| サブコマンド | calibrate / verify / reverify / summarize / selftest | **+ `prerun`** (setup → hydrate → checkout → applied → quarantine → identity 前 → warmup + build → identity 後 → `prerun.json`。bench・verifier なし) | D2186 項 1 (6) |
| 流用した機構 (不変) | — | setup / hydrate / toolchain (policy `tools/pegasus/mocc_trace_v1_policy.json`、g++-11) / node-local build / 単独性検査 / bench argv / C 行数え直し / zstd 保全 → verifier の順序 / 計時 / 再検証の sha256 照合 / 再開 | D2160 s4-ruling |

- 版: v2 `c960093d…` (1384 行) → v3 `8a44e23875655d24d515d56b9d334e93b2f7a3b6f8646e85d969060022036ce7` (1785 行、author、selftest 120/120) → v4 `f98360ad0c8256a80c198df84de3ec46219d53e5f9dcfe2f741e76bc84455856` (1968 行、fix 1、selftest 160/160) → **v5 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430` (2103 行、fix 2 = 保全済み・verifier 未開始 rep の初回 verifier 再開経路の復元、selftest PASS 166/166 cases)**。親の login selftest は v3 / v4 / v5 とも実走 (`verbatim/selftest-login*.log`)。
- 変異 matrix は repo 内実装面差分ゼロで免除 (`DW-S04`)。runner の規則は selftest の正例・負例 (境界 1800.0 / 1800.001、打ち切り、∩ 空、段下げ、判定順序の正負例、bench 失敗、混入 + anomaly → 失格、identity 不一致、resume 照合、bundle schema、`--extimes` 拒否) で固定した。

---

## 4. 試走 — 案 A の厳密適用・trace-enabled build・identity 導出 (計算ノード)

投入形: detached submit-tree (`submit-tree-p1` / `p2`、HEAD `f94b61fc8`、submodule 初期化済み) から `tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- python3.10 -B <J>/probe/verify_phase_runner.py prerun --gate <g> --repo-root <tree> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --scratch-root /scr --output-dir <J>/run/<prerun|prerun-v4>/<g> --ruling <tree>/docs/b8-final-candidate-longrun-verify-preregistration.md`。`--bundle` 無し (期待値が無い段階)。

| 版 | gate | request | node | 開始 → 終了 (JST) | Elapse | F_s (setup / hydrate / build) | `src_token` = `source_bytes_sha256` (build 前 = 後) | binary sha256 |
|---|---|---|---|---|---|---|---|---|
| v3 | g_rl | 13588.nqsv | bnode076 | 21:24:34 → 21:25:04 | 36 S | 30.48 (3.6 / 10.8 / 16.1) | `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d` | `56e6b377a245f40ca1fe9989a56853d3dd2d140d52ba1defd56644d700782288` |
| v3 | g_rt | 13587.nqsv | bnode058 | 21:23:47 → 21:24:18 | 36 S | 30.97 (3.5 / 11.4 / 16.0) | `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` | `c1bc65bc12cf9d1e491030095f1e43605ba0e8c32dc002f995050d992f7c97d2` |
| v4 | g_rl | 13622.nqsv | bnode011 | 21:54:47 → 21:55:18 | 36S | 30.99 (3.7 / 11.2 / 16.1) | `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d` | `c9846664e2fe09dd8ec2d84abe8cecf05705134c6a9f98797402849926a44337` |
| v4 | g_rt | 13621.nqsv | bnode001 | 21:49:37 → 21:50:07 | 35S | 30.07 (3.1 / 10.9 / 16.1) | `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` | `8ee8687097f749b9d0b726b21790ab81faefd2349c0f1958ea3fc16027f7551a` |
| v5 | g_rl | 13657.nqsv | bnode041 | 22:20:49 → 22:21:19 | 35S | 30.14 (3.2 / 10.8 / 16.1) | `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d` | `563ebd0b9872f0c22fe803c35ddab32c3cf7f831829f3ffcf3e50624ea7b5b72` |
| v5 | g_rt | 13656.nqsv | bnode022 | 22:14:50 → 22:15:20 | 35S | 30.04 (3.1 / 10.8 / 16.1) | `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` | `f52b9e45f5193aaf7adb26f2f464e6e4f256de9811fab5e8173e80f2942689b7` |

- 共通 (6 record とも): pin `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`tracked_paths` = `cc/silo/transaction.cc`, `cmake/Options.cmake`、`tracked_clean` false (patch + hole 書込み下、正常)、quarantine passed、compiler `/usr/bin/x86_64-linux-gnu-g++-11` `x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、toolchain version_body_sha256 `b713e6ab…`、python `/usr/bin/python3.10` 3.10.12、policy sha256 `66ea7135…`、repo HEAD `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad`、genome canonical `silo|BACKOFF_TRIGGER_GATING=1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。
- **identity は login 事前照合 (build 無し) と全桁一致し、v3 / v4 / v5 の試走 6 record すべてで一致した** (prepare 経路が fix 2 巡で変わっていないことの実測)。binary sha256 は node ごとの別 build で異なる (D2160 と同じ。「同一 binary」は主張しない)。
- 試走 record は `phase="prerun"`、`in_judgment_set=false`。判定集合に入れず既知結果台帳 (§7 の発効束 `known_results`) に開示する。**bench・verifier は走らせていない** (D2186 項 1 (6) の範囲)。

---

## 5. 規則の解釈 (親の provisional 裁定、段 6 レビューで攻撃済み)

- (P1) 期待 identity は発効束 JSON から読む (runner の sha256 自体が発効束の項目なので、定数に埋めると試走 → 発効で runner を 2 度変える)。
- (P2、改訂) verifier hard timeout = 校正 3600 s (§11 が校正の 3600 s timeout を想定) / 本走 1800 s (§12・D2186 項 1 (5) の「上限 1800 s」そのもの) / 再検証 3600 s (§6.4 の 1 回、事前登録は値を置かず D2160 を継承)。当初案 (本走 3600 s) はレビュー A が「親の追加解釈」と指摘し改めた。判定の結果は変わらない (本走 1800 s で未完走 → §6.4 の再検証 1 回で同じ verdict に到達する。変わるのは費用)。
- (P3) rc=3 (`indeterminate` verdict) は完走した CLI 出力であり、§6.1 項 1 の「verdict が `serializable` でない verify」→ 失格。§8 が「anomaly 0 件で `serializable` でない verdict も失格に数える」と明記。D2160 の「pass にも anomaly にも数えない」は採らない。
- (P4) 校正は打ち切り条件 (wall > 1800 / 未完走 / bench 失敗) でだけ打ち切り、anomaly を理由に残 extime を止めない (§7)。失格は `summarize` が判定集合から決める。
- (P5) 適格 (§4.2) は certified を要求、pass (§6.1) は本走 24 に要求し校正 verdict には要求しない (件数と理由を開示)。
- (P6) 予算の式と段下げは §7 のとおり。(P7) 既知結果台帳は判定集合外の別節。(P8) 8 反復 = job-index 2 × 4 反復 (D2160 と同じ)。(P9) 試走は構成別 2 job、bench・verifier なし。
- (P10) §5 の「bench 失敗が 1 件でもあれば pass にならない」は校正・本走を問わず、開始して失敗した bench に適用する (打ち切りの `not_run` は失敗でない)。校正で bench 失敗が出た cohort は pass になれないので本走を投入しない (§6.4 の新 cohort)。
- (P11) 失格 (§6.1 項 1) は混入・sha 不一致・規約不適合の有無に関わらず先に評価する (規律 2 の向き)。

---

## 6. 限定

1. **発効していない。** 本 README と発効束 draft は提示であり、発効 commit・D 番号・本走認可はユーザーの承認後 (§7 の 1 行)。校正・本走は走らせていない。
2. **試走は identity と build の確認だけ。** bench も verifier も走らせていないので、案 A の 6 s / 10 s の verifier 所要・maxrss・完走可否は未知 (§4.3 の見込みは案 B の値)。校正 (発効後) で決まる。
3. **runner は計算ノードで `prerun` 経路だけ実走。** `calibrate` / `verify` / `reverify` / `summarize` の経路は selftest (合成 record) と静的レビューで固定したが、実 trace では未実走。D2160 の v2 が同経路を 30 job 実走した実績を流用しているが、B-8 で変えた箇所 (bench 不再生成、失格の優先評価、job 段 record の集計、hard timeout) は本走で初めて実走する。
4. **binary は node ごとの別 build。** source identity と toolchain の同一性だけを主張する (§2.4)。
5. **setup+hydrate+build の 2400 s は事後検査** (v2 継承)。各段の個別 timeout の和 (hydrate 120 + 依存 build 各 300 + warmup 1200 + build 900 …) は 3600 s を超えうるので、試走の 1 h 予約は上限保証ではなかった (実測 F_s ≈ 31 s)。校正・本走の walltime は §7 の上限式で別に決める。
6. **発効束のうち runner が単独で揃えない項目** (pin と gitlink の一致、raw bytes の保存、承認情報、node 種別、保全先の空き容量、校正 walltime の根拠) は本 README §7 が補う (レビュー B 項目 3)。新しい機械 gate は足さない。
7. **07-16 校正の g_rl `src_token` `4608a96e…` は旧 pin の値** で、現行 identity と一致しない。期待値にせず履歴として併記する (規律 7)。

---

## 7. 発効束 (§12) と裁定パッケージ

### 7.1 発効束の値 (draft、`verbatim/b8-effective-bundle.draft.json` = runner の `--bundle` が読む形。発効 commit で `status` を `effective` にし、D 番号・日付・承認 commit を足す)

| §12 の項目 | 値 | 出所 |
|---|---|---|
| 本走認可の日付・D 番号・承認 commit | **未 (ユーザー承認後)** | — |
| 対象の択 | **案 A** (g_rl: balanced / read-heavy、g_rt: write-heavy、24 verify) | D2186 項 1 (1) |
| 本書 (事前登録 v1) の raw bytes SHA-256 | `6ccb18c73b80ba42031f1373d48baa2e3fe441e0370a208836a6d75a9504f7c5` (51,974 bytes、commit `1a97b9841` 以降不変) | `sha256sum`、試走 record の `ruling_sha256` と一致 |
| CCBench pin | `e9e477ca1b55348ab4530de0b1cf663ce4555290` = `pin.CURRENT_PIN` (`e9e477c`) = submodule gitlink (一致を親が実測) | §2 |
| patch の bytes と sha256 | `patches/silo-backoff-trigger-gating-variant.patch` `31316713b9783fc7fbbbcffb4fa1d791e3f9d1c0bbea6db52ac45b77cef7d620` (repo tracked) | §2 |
| gate 述語・flags の逐語 | g_rl: `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset \|\| izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;`、g_rt: `… kReadValiTid;`。flags `{BACK_OFF 1, NO_WAIT_LOCKING_IN_VALIDATION 1, NO_WAIT_OF_TICTOC 0, WAL 0, BACKOFF_TRIGGER_GATING 1}` | 凍結 JSON、試走 record |
| configure の逐語 | define 6 個 (§2)。argv 全文は試走 record `bindings.configure_argv` (`verbatim/prerun-v4-*.json`) | 試走 record |
| toolchain | g++-11 `x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、version_body_sha256 `b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0`、python 3.10.12、policy `tools/pegasus/mocc_trace_v1_policy.json` sha256 `66ea7135c6d84cfd09013f33da23d8ca8015dcb547e34db7c802644f4986acd6` | 試走 record |
| **identity の期待値** | **g_rl `src_token` = `source_bytes_sha256` = `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`、g_rt = `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833`** | 試走 v3 / v4 / v5 (build 前後) + login 事前照合、全桁一致 |
| verifier module の file 別 sha256 (D2181 改修版) | `__init__.py 56c7fb4ca9b54425422cdabe41f3c454dc977d3ac02cd177e9d4738f4fe948bd`、`__main__.py 9a06c813eccbc750ca412d717ee14010ffb859d2ae1afaaebf0f38577436b701`、`cli.py 68e690c6370617aabe95a26ecef1d55df0f5bfda74336ae822b2513bca0fba91`、`commit_receipt.py 106e0dcc4e10a9664869b0244c92c25094cd126c1cd5952f973c27e9aba0ba7f`、`core.py 4d70c244848fc7410bd1a724cad7aa0f7f856ddfeb43717d8d8abb45385e42d0`、`dsg.py e5989092476a6208e5631c63b12cc66d64945cbe307514b074c1a7f0fc6365aa`、`model.py 59136847b040e70002ee73f1b1de52a9ac2545e7beb36f60d95a0a43596067fb`、`parse.py a588bc3095fefb5f107be16de5976ed726c84bcfbe9a5a1f5d670951515f23af`、`report.py e68e31a0c8ac5315bd0134be741241e7dd142d69e33e4f986f7674e6d3f27dbd` | HEAD `f94b61fc8` と試走 record (一致) |
| runner の bytes と sha256 | v5 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430` (2103 行)、bytes は job dir `probe/verify_phase_runner.py` (repo 外、regular file、複製 `probe/verify_phase_runner.v5.py`)。規則 file (`--ruling`) = 事前登録 v1 本文、追補 file (`--bundle`) = 発効束 JSON、と分離 | 親の sha256sum |
| 環境 | Pegasus gen_S (1 CPU 48 physical core、DRAM 128 GiB、ユーザー上限約 115 GiB)、各 job 1 node、単独性検査 = runner が bench・verifier 直前に `p2_2._assert_single_tenant()` (runbook §7)、trace 保全先 = job dir `run/` (`/work` lustre、空き 81 TB @ 21:4x JST) | runbook §1、`df` |
| 校正 job の walltime と根拠 | **提案 03:30:00 (12,600 s)**。上限式 = setup+hydrate+build 上限 2400 + Σ_{6,10} (bench 120 + count + preserve + verifier hard 3600) + 終了余裕 300、count / preserve は D2160 校正 read-heavy 6 s の実測 (32.2 + 45.5 s) を 10 s へ線形外挿して 2 extime 分 ≈ 200 s → ≈ 10,340 s ≤ 12,600 s。D2160 校正の最大 Elapse 4063 S × 3 倍 = 12,189 s ≤ 12,600 s | §7、D2160 §7.4 |
| 既知結果台帳 (§8) の差分 | + 試走 v3 / v4 / v5 の 6 record (identity 導出のみ、verdict なし、判定集合外) | 本 README §4 |

### 7.2 発効 commit と本走認可の 1 行再提示 (ユーザー裁定)

> **B-8 事前登録 v1 (raw sha256 `6ccb18c7…`) を、対象 = 案 A (identity g_rl `b0f95b21…a670d` / g_rt `a0219ce0…2f833`、pin `e9e477ca`、patch `31316713…`、verifier 9 file sha256 = §7.1、runner v5 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`) の発効束で発効し、校正 3 job (workload 別 {6, 10} s、walltime 03:30:00) → §4.2 / §7 の規則が機械的に決める extime での本走 6 job (24 verify、≤ 4 h / 対象、verifier hard timeout 本走 1800 s) の投入を認可する — 承認なら「承認」の 1 語で足りる。**

- 承認後に AI が行う手順: (1) 発効 commit (発効束 JSON を `effective` にし D 番号・日付・承認 commit を足し、insight へ置く) を作り、その固定 checkout (detached submit-tree) を校正・本走の `--repo-root` にする。(2) 校正 3 job を投入し `summarize` で extime と B(E) を出す (発効の**後**に決まる値、§12)。(3) `stage_B_allowed` なら本走 6 job を投入し、`summarize` の 3 値判定を得る。(4) 結果は §8 / §6.3 の書き方で results 稿・論文ストーリー §8 へ。
- 承認しない場合の選択肢: (b) 発効束の項目 (P2 の timeout 3 値、校正 walltime 03:30:00) だけを変えて再提示、(c) 据え置き (B-8 未取得のまま)。
- 事前登録 v1 本文は編集していない (発効前でも bytes 不変。逸脱候補は無い — 段 6 レビュー A の「逸脱一覧」は v4 で全件閉じた、§10)。

---

## 8. 記録先と繰延べ

- 発効束の値は本 README §7.1 と `verbatim/b8-effective-bundle.draft.json`。発効時の記録先は D 番号 (ユーザー裁定) と発効 commit。
- `docs/paper-story/2026-09-20.md` §8 B-8 の仕分け (2)「数値 seed・乱数列の独立性は記録できない」→「独立 process の自己シード」への限定明記は D2186 項 1 (2) が「発効時に」と定めた。本 wave では書かない (発効 commit の wave が行う)。
- runner v4 は repo へ入れない (D95: Codex author 作、使い捨て、job dir に保全、sha256 で同定)。

---

## 9. 一次資料

すべて job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/` 配下 (repo には本 README と `verbatim/` の逐語だけを入れる。runner 本体と diff は実装面 (.py / .diff) なので repo へ写さず sha256 で同定)。

| 資料 | path | 備考 |
|---|---|---|
| runner v5 | `probe/verify_phase_runner.py` (= `probe/verify_phase_runner.v5.py`) | sha256 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`、2103 行 |
| runner v4 / v3 / v2 | `probe/verify_phase_runner.v4.py` (`f98360ad…`)、`probe/verify_phase_runner.v3.py` (`8a44e238…`)、D2160 job dir `dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.py` (`c960093d…`) | diff `refs/runner-v2-v3.diff` (1339 行)、`refs/runner-v3-v4.diff` (666 行)、`refs/runner-v4-v5.diff` (205 行)、`refs/runner-v2-v5.diff` (1861 行) |
| 試走 record | `run/prerun/<gate>/prerun.json` (v3)、`run/prerun-v4/<gate>/prerun.json` (v4)、`run/prerun-v5/<gate>/prerun.json` (v5) | `verbatim/prerun-v3-<gate>.json`、`verbatim/prerun-v4-<gate>.json`、`verbatim/prerun-v5-<gate>.json` |
| dispatch log | `run/prerun-<gate>.log`、`run/prerun-v4-<gate>.log`、`run/prerun-v5-<gate>.log` | request ID・node・Elapse |
| login 事前照合 | `probe/login_identity_precheck.py` → `.json` | `verbatim/login_identity_precheck.json` |
| 発効束 draft | `refs/b8-effective-bundle.draft.json` | `verbatim/b8-effective-bundle.draft.json` |
| selftest | `probe/selftest-login.log` (v3、120/120)、`probe/selftest-login-v4.log` (v4、160/160)、`probe/selftest-login-v5.log` (v5、PASS 166/166 cases) | `verbatim/` |
| brief / 裁定 | `s1-brief.md`、`rulings-stage6.md` | `verbatim/` |
| Codex 子の報告 | `codex/s5-author.md`、`codex/s6-review-A.md`、`codex/s6-review-B.md`、`codex/s6-fix-1.md` (停止)、`codex/s6-fix-1b.md`、`codex/s6-focus.md`、`codex/s6-fix-2.md`、`codex/s6-focus-2.md` | `verbatim/codex/` |
| 起動 gate | `startup-gate.log` (fresh rc=0 20:58)、`midflight-gate-author.log` | — |

`verbatim/` の写しのうち `s1-brief.md` (親) と `codex/s6-review-A.md` (Codex) は、結合文字 U+0302 (`F` + circumflex の記法) を `F_hat` に置換してある (`DW-O02` の U+0300〜U+036F 禁止。可視文字は不変、原本は job dir の同名 file)。他の写しは byte 同一。Codex 逐語のうち `codex/s6-review-A.md` と `codex/s6-focus.md` は行末 2 space (Markdown の改行記法) を原文のまま保持しており、`git diff --cached --check` がこれを trailing whitespace として挙げる (可視文字不変。D2160 wave の insight と同じ扱い)。

---

## 10. 段 6 の独立レビュー (Codex、read-only、`gpt-6-astra` / medium)

| 段 | 子 | 受理 | 要点 |
|---|---|---|---|
| 5 author | `codex/s5-author.md` | accepted | v3 1785 行、selftest 120/120。差異 2 点を自ら開示: (1) 共有 `choose_extime` が (3,6,10) 固定 → runner 内 (6,10) 版、**(2) 事前登録 §5「bench を再生成しない」と親 prompt の attempt-2 許可 (D2160 の規則の写し、親の誤り) の不一致** |
| 6 レビュー A (規則の忠実性・過剰削除・brief 攻撃) | `codex/s6-review-A.md` | accepted、NO-GO | must 3: 校正の bench 失敗が pass を妨げない / 判定集合外 record の混入が失格より優先 / bench 再生成。should 2: (P2) 本走 3600 s は親の追加解釈 / D2186 逐語 file が見出しで切れていた (親の sed 範囲ミス)。不成立 = rc=3・certified・1800 境界・予算式・identity 束縛・構築経路・削除・P7・P9・author 報告 |
| 6 レビュー B (実行経路・schema・selftest 実効性) | `codex/s6-review-B.md` | accepted、NO-GO | must 2: bench 再生成 / job 段の identity 不一致 record を集計が読まない。should 4: 校正計画分岐の未被覆と fixture の phase 誤り / 期待 define の自己参照と負例の二重理由 / resume 照合に `in_judgment_set` 無し / 2400 s は事後検査 (v2 継承、記録のみ)。不成立 = import 13 群・prerun 経路・bindings・v2 残骸 (動作箇所なし)・保全復元 |
| 6 fix 1 | `codex/s6-fix-1.md` | accepted (改版なし) | 起動器の終端 commit で runner が tracked になっており、親 prompt の「tracked を編集しない」と衝突して編集前に停止 (親の prompt の誤り)。prompt を直して 1b で再投入 |
| 6 fix 1b | `codex/s6-fix-1b.md` | accepted | v4 1968 行 `f98360ad…`、所見 9 件 (must 4 + should 4 + selftest 追加) すべて closed (行番号付き)。selftest 160/160 (既存 120 維持 + 40 追加)、AST・`--help` 6 件 rc=0。§5 が列挙する trace 欠落・witness 不一致も bench 失敗として扱う。B6 (2400 s 事後検査) は裁定どおり据え置き |
| 6 焦点再レビュー 1 | `codex/s6-focus.md` | accepted、NO-GO | closed 7 / partial 1 / regressed 0。**新規 must-fix F1: v4 が「bench 完走・保全済み・verifier 未開始」の rep (walltime kill 等) の初回 verifier 再開経路を削った回帰** (v3 にあった。§5 の bench 不再生成とは別経路)。should F2: 焦点 prompt が停止巡の `s6-fix-1.md` を指した (親の path 誤り)。発効束 draft は指定検算項目すべて一致 (runner sha は v4 実体と一致) |
| 6 fix 2 | `codex/s6-fix-2.md` | accepted | v5 2103 行 `4ff6652a…`。`verify --resume` を 4 分類 ((a) bench 失敗 = 終端 / (b) verifier 起動済み = skip / (c) 保全済み・未開始 = `restore` (sha256 / bytes 照合) → 再構築 checkout の identity 照合 → 初回 verifier 1800 s、同じ attempt-1 を更新、`resumed_verifier` 記録 / (d) 保全未完了 = `trace_missing` で終端・規約不適合)。`reverify` は未開始を `verify --resume` へ案内。selftest 166/166 (4 分類の spy 検査)。判定規則・timeout 不変 |
| 6 焦点再レビュー 2 | `codex/s6-focus-2.md` | accepted、**GO** | closed 9 (F1 + v4 で閉じた 8 件の維持) / partial 0 / regressed 0、新規所見 0。(c) は本番の `restore` → `run_verifier` を通し、spy で restore → verify の順・timeout 1800・出力先同一を検査 (bench 再生成 callback は呼ばれれば失敗)。`prepare` / `prerun_record` / `configure_argv` / `preserve` / `restore` / `timed_process` / `run_verifier` は v3 / v4 / v5 で AST 一致。発効束 draft は identity・verifier 9 file・patch・pipeline・toolchain・define・genome・pin・python・repo HEAD・試走 binary / hostname / 完了時刻・事前登録 sha すべて一致、runner sha は v5 実体と一致。「本走の発効認可を意味しない」 |

親の裁定は `rulings-stage6.md` (`verbatim/`、§0 レビュー A / B、§3 焦点 1、§4 焦点 2)。所見のうち real = must 5 (A/B 4 + 焦点 1) + should 6 (fix へ 5、記録のみ 1)、refuted = 攻撃不成立の全項目。fix は 2 巡 (3 巡上限内)。


## dev-wave 改善候補 (段 8)

- (1) 前 wave の規則 (D2160 の bench attempt-2) を author prompt に写して事前登録 §5 と矛盾させた。author が開示しレビュー 2 本が must-fix にした (防壁は機能)。規則差し替え wave の brief に「先例 runner の規則 → 本 wave の規則」の対応表を置く運用 (D2160 s4-ruling §1 と同型)。docs 変更なし、memory へ。
- (2) fix prompt の「tracked を編集しない」は起動器の終端 commit (D2044 項 16) 後の対象 file と衝突する。fix prompt 定型は「対象 file は commit 済み (tracked) で唯一の編集対象」。memory `codex-child-discipline` の同型項へ追記。
- (3) 逐語射影を sed の行範囲で切って見出しだけになった。memory「逐語射影は行範囲でなく見出しで切る」の再発 → memory 追記のみ。
