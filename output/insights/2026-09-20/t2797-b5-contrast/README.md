# [T-2797] B-5 生成器対照 — (α) §10 残部品の段階実装と (β) 上限付き試走 (2026-09-20)

wave `dev-wave-t2797-b5-contrast` (branch `worktree-dev-wave-t2797-b5-contrast`)、起点 local main `6a3e15809` → 着手中に `b9904a5f8` へ ff。
依頼の逐語は `verbatim/T-2797-origin.md`、裁定は D2172 項 4 (段階裁定 (A))、共有 3 部品は D2183 で着地済み。
専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/HANDOFF.md`。

**本走は未認可のまま。発効 commit は作らない。** 本 insight は試走の既知結果台帳 (事前登録 §8 / §11 の「試走の結果は主標本へ入れず
閲覧を既知結果台帳へ残す」) を兼ねる。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **事前登録 §10 の「実装が要る」残部品を Codex author で実装した (α)。** random 生成器 (§4.2 逐語: 整数重み `floor(2^128 ln((v+1)/v))`、preimage、
   `L = floor(2^256/M)·M` の引き直し)、sweep の hash 順 B 点 (§4.3)、系列開始 stock の planner 前配置 (§5.4)、session 契約の flag 束縛 (`bench_max_rounds=3` の
   明示) と品質欠測の分類 (§5.3)、B / A 台帳と収束停止の不適用 (§3)、重複の fresh 評価 (slot ごとの identity 分離)、endpoint と再計測 (§6)、
   系列状態の継承検査 (§4.1)、解析 consumer (§6 / §7 + pilot 記述経路)、較正・verify の job body 配線 (B-5 mode) と login 側 launcher。§1・§2。
2. **3 arm とも slot 評価は `p3_s4_loop` CLI の subprocess (§4.1 / §5.1 逐語) で、seam は 4 点** (`--b5-slot` = identity 分離、`--machine-generated-proposal` =
   generator receipt (machine-generated class)、`--b5-sidecar-dir` = `slot-start` / `pipeline-submitted` / `proposal-rejected` の durable 記録、B-5 mode の
   skip 拒否と rounds 明示)。既定経路の argv・identity preimage・`run_campaign` kwargs は bytes 不変 (固定定数 test)。§2。
3. **規律 2 は保存:** 受理文法 (1..1000)・検疫・verify → bench の順・anomaly 即 reject は既存 pipeline のまま。pipeline.py / loop.py / ident.py /
   build_admission.py は変更なし。
4. **試走 (β) の結果と verifier wall (trace+verifier+周辺処理 区間) の実測は §6 (既知結果台帳)。** 上限 53 ≤ 60 論理 session。
5. **変異 matrix (M0〜M28) と受入全走の結果は §5・§7。**

**主張しない。**

- 本走の認可・発効束・総実行 wall 上限 (§8 の裁定パッケージで再提示)。試走の結果を主標本・統計判定に使わない (n = 1、`not-applicable-pilot`)。
- 「LLM が必要と実証した」「K0 arm」「optimal」— scope 外。
- 共通 Tier0 (§3.1) は未実装 (`tier0_status="not-implemented"`)。現行の build 失敗は §3.3 のとおり B 消費。
- 台帳の verify 区間は純 verifier 秒ではない (隣接 `verify_done` の差 = trace 走行 + verifier + 周辺処理)。
- 親の介入不在・実送達は入力の保存と照合で機械保証しない (§4.1 の限界)。
- 8h / 3h の walltime と `SESSION_BUDGET_S = 1800` は試走の暫定管理値 (1 session ≈ 12〜14 分は外挿)。
- D2183 の「同 campaign の stock」は peer (T-2795 pair) の実走で claim 層 (`<identity>.claim` の O_EXCL、解放なし) の衝突が出た。B-5 は slot ごとの identity で
  回避するが、K2 pair 側の修正は本 wave の scope 外。

## 1. 置いたもの

統合 commit 6 本 (起点 main `b9904a5f8` → `c41cfb09f` (A1) → `e57481558` (A2 + A3) → `92b5c4939` (fix1 + README) → `11d46a74a` (fix2 + docs) →
`65272f3c8` (fix3) → `517fd5451` (fix4、受入後))。15 file、+4511 / −27 行。実装面はすべて Codex `role=author` の子 (unit worktree `t2797-unit-{a1,a2,a3,fix1,fix2,fix3}`) が書き、
親は docs 本文と統合 commit だけを担った。

| file | 種別 | 内容 |
|---|---|---|
| `orchestrator/campaign/b5_generator_contrast.py` | 新設 (884 行) | random / sweep 生成器 (§4.2 / §4.3 逐語)、系列台帳 (`b5-generator-contrast-ledger/v1`: `header.json` + `events/NNNNNN-<kind>.json` + `series.json` view)、session / slot の分類、系列 driver (`run_series`)、LLM handshake、endpoint 選択と score、`assert_inherited_inputs`、module CLI (`run-series`) |
| `orchestrator/campaign/b5_generator_contrast_report.py` | 新設 (584 行) | 解析 consumer: §6 の score / floor、§7 の exact sign-flip permutation・Holm 族 6・判定順 1〜8・fallback 対、`purpose="pilot"` の記述経路、台帳の整合検査 (`_validate`) |
| `orchestrator/campaign/p3_s4_loop.py` | +193 / −18 | B-5 seam 4 点: `--b5-slot KEY` (`search_config["b5_slot"]`)、`--machine-generated-proposal` (generator receipt)、`--b5-sidecar-dir` (`slot-start.json` / `pipeline-submitted.json` / `proposal-rejected.json` + rc 3)、B-5 mode の skip 拒否 (`duplicate-skip`、rc 1) と `bench_max_rounds=3` の明示。既定経路は argv・identity preimage・`run_campaign` kwargs とも bytes 不変 |
| `tools/pegasus/p3_s4_loop_pegasus.sh` | +74 / −1 | job body の B-5 mode (`IZANAGI_S4_B5_MODE` と `IZANAGI_S4_B5_*` の env 契約、設定済み空値は rc 2)。既存 3 経路は bytes 不変 |
| `tools/pegasus/b5_contrast_launch.py` | 新設 (272 行) | login 側 launcher: 4 job 固定 (random / sweep-matched / llm / block-stock、53 ≤ 60 論理 session の予算検査)、`qsub -v` の明示列挙、dry-run = 最終 argv、投入対象 checkout の PIN 行を正規表現で読む |
| `tools/pegasus/admission_registry.json` | +6 | launcher を `local-ok` で登録 |
| `tools/pegasus/README.md` | +64 / −5 | §0 宣言表と §7 の B-5 mode (env 契約・handshake・launcher の使い方・前処理拒否 2 経路) |
| `docs/pegasus-runbook.md` | +1 | §7.0 の射影行 (admission drift 検査の同期) |
| `orchestrator/tests/test_b5_generator_contrast.py` | 新設 (921 行) | 生成器の固定 vector (親の独立 script `independent_random_vector.py` と一致)、台帳・分類・driver・handshake・endpoint の正例・負例 |
| `orchestrator/tests/test_b5_generator_contrast_report.py` | 新設 (713 行) | consumer の固定例 (13/4096 系の p、Holm)、pilot 経路、`_validate` の負例 (1 評価で B=10、fitness ≠ median、sidecar だけの attempt) |
| `orchestrator/tests/test_b5_contrast_launch.py` | 新設 (298 行) | launcher の argv・cap・PIN 照合・dry-run |
| `orchestrator/tests/test_p3_s4_loop.py` | +234 | seam 4 点の挙動 test と既定経路の bytes 不変 (固定定数) |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py` | +252 / −3 | job body の B-5 mode の実 shell test (driver 呼出し 1 回、空値 rc 2、旧候補分岐へ落ちない) |
| `orchestrator/tests/test_hooks.py` | +9 | admission 固定表 3 つの同期 |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | +6 (fix4) | process 起動点の exact 目録に `b5_generator_contrast.default_runner` (reviewed な p3_s4_loop CLI を固定 argv・shell 無しで起動する non-CCBench site) を登録 |

作らなかったもの (段 4 裁定 B13): hash8 衝突の事前網羅、純 verifier 秒の計時 adapter、新 coder entrypoint、alias 群、汎用 retry / 再配置、108 系列 launcher、発効 gate、共通 Tier0。

## 2. 契約 (段 4 裁定 §2 + 段 6 裁定)

正本は `verbatim/s4-adjudication.md` §2 と `verbatim/s6-adjudication.md`。要点だけ書く。

- **slot key と identity:** `b5-generator-contrast-v1|<cohort>|<arm>|<w>|<r>|<kind>|<n>|attempt-<t>` を `--b5-slot` で渡し、`search_config["b5_slot"]` に焼く。campaign identity・claim file (`<identity>.claim`、O_EXCL・解放なし)・protocol digest が slot と物理 attempt ごとに分かれるので、同 slot の retry が残存 claim に拒否されない。同値の再提案は fresh に評価される (重複 skip は B-5 mode で拒否、rc 1)。
- **A / B の消費点:** A (原提案の機会) は空出力・schema・値域・帰属不一致・文法・検疫の不通過も消費する。B (評価) は `pipeline-submitted.json` が書かれた attempt だけ消費する (投入後の build 失敗・anomaly・bench abort・walltime も B)。候補起因の前処理拒否は `proposal-rejected.json` + rc 3 (A のみ)。分類は sidecar と WAL から決定論的に導き、CLI の rc からは導かない。文字列の文法 preflight 拒否は WAL diff-reject 経路 (rc 0) で A のみ消費 — 段 6 焦点再レビューの残件を、durable な証拠 (WAL) がある経路として受け入れ test で固定した。
- **機械故障の retry:** 同論理 slot・attempt+1 で追加 2 回まで。対象は pre-start failure (sidecar が一つも無い失敗) と `{bench,verify}-{probe-error,competing-tenant}` だけ。`indeterminate`・anomaly・品質赤・候補 build 失敗・timeout・分類不能は retry しない。上限到達は `unclassified-missing` (score None、fallback 無し)。
- **品質欠測:** WAL `bench_done` の `len(tps) != reps ∨ unstable ∨ settled is not True`。探索の品質欠測は当該 session の endpoint 資格だけを失い系列は継続、§7.4(2) の系列単位の欠測は score / stock session に限る。
- **LLM arm の handshake:** job が `request-<a>.json` (次評価 k、期待 whiteboard、`current_perf` = 直近の certified かつ品質正常な評価か系列開始 stock) を出し、親が `inputs-<a>.json` と `proposal-<a>.json` (または `.rejected.json` = A 消費) を atomic に置く。job は `assert_inherited_inputs` で whiteboard の順序・値・全 field、`current_perf` / `baseline`、k ≥ 2 の診断の両側存在を検査する。15 s poll、1 機会 2700 s の無応答は `proposal-wait-timeout` (分類不能欠測、retry 無し、系列終了)。全終了枝で `proposal_wait_wall_s` を台帳に載せる。
- **driver の durable 記録:** subprocess 起動前に `slot-attempt-start`。report は終端 event の無い attempt の sidecar から B と物理 attempt を回収する (`submitted-unresolved`)。
- **解析 consumer:** §6 / §7 を実装し、試走は `purpose="pilot"` (`registered_judgment="not-applicable-pilot"`)。`_validate` は B と評価件数・連番、certified の `fitness_tps == bench median`、`logical_sessions` = 投入済み論理 slot 数を検査する。
- **job body と launcher:** `IZANAGI_S4_B5_MODE` で既存 job body に B-5 mode を 1 箇所足す。launcher は 4 job 固定 (random 16 + sweep 16 + llm 16 + block-stock 5 = 53 ≤ 60)。llm は K2 の 3 引数 (`--knowledge-manifest` / `--knowledge-classification` / `--knowledge-de-novo-claim`) 全部が必須。
- **不変:** pipeline.py / loop.py / ident.py / build_admission.py は変更なし。受理文法 (1..1000 の整数リテラル 1 個)・検疫・verify → bench の順・anomaly 即 reject は既存のまま (規律 2)。

## 3. 段 2〜4 の所見と裁定

- **段 2 plan (codex read-only、`verbatim/s2-plan.md`):** file:line 粒度で P1〜P9 の設計選択を起草。P9 = 「3 arm とも `p3_s4_loop` CLI を subprocess で slot ごとに起動」が採用の骨格。
- **段 3 敵対相談 A / B (`verbatim/s3-consult-{A,B}.md`):** 独立に同じ 3 点を must-fix と指摘 — (1) BUILD_START の不在は未投入の証拠にならない (投入後・最初の WAL record 前の中断)、(2) 同 slot の subprocess retry は残存 claim (`<identity>.claim` は O_EXCL で解放されない) に拒否される、(3) 45 分無応答は機械故障の証拠にならない。加えて Tier0 未実装の明記 (A5)、継承検査への `current_perf` / `baseline` 追加 (A7)、P9 は 2 seam では完成しない (B3)、launcher の `-v` 明示 (B5)、pin 閉包の追加面 (B9)、`check_stop` spy 変異は P9 と両立しない (B12)、削除候補 (B13) を採用。B10 / B11 (consumer 削減案) は refuted。
- **段 4 裁定 (`verbatim/s4-adjudication.md`):** must-fix 3 点を sidecar `pipeline-submitted.json`・物理 attempt を含む slot key・`proposal-wait-timeout` (分類不能欠測) で閉じ、seam を 4 点に確定。変異 M0〜M19 を実装前に事前登録 (DW-M01)。peer (T-2795 pair、job 13339) の実走で D2183 の同 campaign stock が `ClaimError` (claim not released) で rc=1 になった事実を、slot ごとの identity 分離 (P1) の追加根拠として記録。

## 4. 段 6 レビューと fix

- **review A / B (codex read-only、統合 commit 3 `92b5c4939` 対象、`verbatim/s6-review-{A,B}.md`):** 両方 NO-GO。must-fix 5 件 (A1 候補起因の前処理拒否が系列終了 / 機械 retry に化ける、A2 verify 側の環境故障が候補起因に化ける、A3 job 打切り時の B 過少計上、A6 / B02 `fitness == median` 未検査、B01 1 評価で B=10 を正常受理) と should 8 件 (A4 k ≥ 2 の診断必須、A5 / B03 待機時間の集計、A11 登録重み表の end-to-end vector、A12 探索中の品質欠測の扱い、B04 `logical_sessions`、B05 / B13 docs、B06 launcher の PIN、B07 llm の K2 3 引数、B12 nit)。裁定は `verbatim/s6-adjudication.md`、追加変異 M20〜M28 を fix2 前に事前登録。
- **fix1 (`92b5c4939`):** launcher の admission 登録 (`local-ok`) と `test_hooks` の固定表 3 つ、README §7。
- **fix2 (`11d46a74a`、Codex author 一枚岩):** sidecar `proposal-rejected.json` (rc 3)、`MACHINE_FAILURE_ABORT_REASONS` に verify 側 2 reason、`slot-attempt-start` + report の回収、k ≥ 2 の診断必須、handshake 全終了枝の待機記録、`_validate` の B 件数・連番・fitness == median、`logical_sessions`、launcher の対象 tree PIN、llm CLI の K2 3 引数必須。docs は親: README §0 宣言表 + §7、`docs/pegasus-runbook.md` §7.0 の射影行 (check_docs の admission drift を解消)。
- **焦点再レビュー (`verbatim/s6-focus.md`):** NO-GO の残件 2 — (1) 文字列の文法 preflight 拒否が sidecar / rc 3 に統一されていない、(2) B04 の未投入 stock 計数。親の裁定: (1) は WAL diff-reject 経路 (rc 0) に durable な証拠があり A のみ消費・系列継続の分類が既に決定論的に出るので、sidecar への統一は行わず test で固定 (fix3)。(2) は fix3 で `logical_sessions` = 投入済み論理 slot 数 (runner 0 回は 0) に修正。
- **fix3 (`65272f3c8`):** report の `logical_sessions`、文字列文法 preflight → WAL diff-reject 経路の test、fixture の `score_sessions` 追従。
- **親の実走 (login、各 fix 後):** 変更 test file の焦点 (report 70 / driver 108 / loop 81、TJ 184、TL 585 passed) と consumer 回帰 190 passed。
- **fix4 (`517fd5451`、受入 attempt 1 の赤 2 件の是正、Codex author):** `test_ccbench_spawn_sites.py` の exact 目録 (`_EXPLICIT_NON_CCBENCH_PROCESS_SITES`) に新 module の subprocess 起動点 `default_runner` を登録 (6 行)。焦点走の 21 file にこの目録 test を含めていなかったのが検出漏れの原因 (T-2737 と同型)。author の実走 74 件 = 72 passed / 2 skipped。
- **焦点走 (計算ノード、`focus/run-focus.sh` = 変更 test file + consumer + inventory 4 群 + メタ test の 21 file、`--force-dispatch`):** focus-1 = job 13573 (commit 3) 2475 passed / 10 skipped (121.5 s)、focus-2 = job 13623 (commit 4) 2521 passed / 10 skipped (123.9 s)。commit 5 (fix3、report + test だけ) は親の login 実走で確認し、受入全走 (§7) で計算ノードの証拠を取る。focus-3 = job 14257 (main `9389277b0` 取込み後の tip `e4f4c900c`) 2526 passed / 10 skipped (122.3 s)。

## 5. 変異 matrix

事前登録は段 4 裁定 §3 (M0〜M19、実装前) と段 6 裁定 §3 (M20〜M28、fix2 前)。harness は `tools/mutation_worktree.py` (独立 clone `mutation-source`、D1009)、
runner は `tools/run_tests.py --force-dispatch` で 5 test file (`test_b5_generator_contrast.py` / `test_b5_generator_contrast_report.py` / `test_b5_contrast_launch.py` /
`test_p3_s4_loop.py` / `test_p3_s4_loop_job_contract.py`) を計算ノードへ dispatch (`-q -rf`)。spec と結果は job dir (repo 外、sha256 で束縛):

| 走 | 対象 commit | spec (sha256) | 結果 (sha256) | 内容 |
|---|---|---|---|---|
| probe | 統合 commit 4 `11d46a74a` | `mutation-spec-probe.json` 6b0de7cdbcd2a01b… | `mutation-probe-results.json` c9d1ed43d6eef47b… | 29 変異 + baseline、全件 SURVIVED 期待で観測 node を集める |
| final | 統合 commit 5 `65272f3c8` | `mutation-spec-final.json` cef75afe76f4122b… | `mutation-final-results.json` 2579d6fe6f886e68… | 30 変異 (M25b 追加) + baseline、期待 node = probe 観測 (M25b は予測 node) |
| final2 | 統合 commit 5 `65272f3c8` | `mutation-spec-final2.json` c96b0113a579533d… | `mutation-final2-results.json` 1fd3c4998e9e754c… | M10 / M11 の再登録・再走 (期待 node = final 走の観測、完全集合) |

**final の集計: baseline PASSED (37.3 s)、KILLED 26 / SURVIVED 2 (M0・M25 = 等価対照、SURVIVED が正) / MISMATCH 2 (M10・M11) / TIMEOUT 0。
final2: baseline PASSED、M10・M11 とも KILLED (期待 = 観測)。** 期待 node は完全一致だけを KILLED と数えている (DW-M08 / F33)。

| ID | 種別 | 位置 (file / 変異) | 期待 | final (commit 5) | 殺した node 数 | 備考 |
|---|---|---|---|---|---|---|
| m0-equivalent-comment | positive | b5_generator_contrast.py | SURVIVED | SURVIVED | 0 | 等価対照 (SURVIVED が正) |
| m1-weights-2pow127 | negative | b5_generator_contrast.py | KILLED | KILLED | 3 |  |
| m2-random-preimage-separator | negative | b5_generator_contrast.py | KILLED | KILLED | 3 |  |
| m3-random-u-le-l | negative | b5_generator_contrast.py | KILLED | KILLED | 1 |  |
| m4-sweep-numeric-order | negative | b5_generator_contrast.py | KILLED | KILLED | 2 |  |
| m5-quality-or-to-and | negative | b5_generator_contrast.py | KILLED | KILLED | 7 |  |
| m6-b-only-on-certified | negative | b5_generator_contrast.py | KILLED | KILLED | 9 |  |
| m7-endpoint-tie-value-desc | negative | b5_generator_contrast.py | KILLED | KILLED | 1 |  |
| m8-score-from-search-max | negative | b5_generator_contrast.py | KILLED | KILLED | 1 |  |
| m9-inheritance-order-ignored | negative | b5_generator_contrast.py | KILLED | KILLED | 2 |  |
| m10-slot-not-in-identity | negative | p3_s4_loop.py | KILLED | MISMATCH | 7 | 観測 = 期待 + test_b5_string_preflight_rejection_uses_wal_and_rc0 (fix3 で追加、probe は commit 4)。final2 (再登録・再走): KILLED (期待 node 7 = 観測 7) |
| m11-machine-guard-exception-removed | negative | p3_s4_loop.py | KILLED | MISMATCH | 9 | 観測 = 期待 + test_b5_string_preflight_rejection_uses_wal_and_rc0 (fix3 で追加、probe は commit 4)。final2 (再登録・再走): KILLED (期待 node 9 = 観測 9) |
| m12-submitted-marker-not-before-campaign | negative | p3_s4_loop.py | KILLED | KILLED | 1 |  |
| m13-jobbody-fallthrough | negative | p3_s4_loop_pegasus.sh | KILLED | KILLED | 84 |  |
| m14-jobbody-empty-mode-accepted | negative | p3_s4_loop_pegasus.sh | KILLED | KILLED | 76 |  |
| m15-timeout-as-rejected | negative | b5_generator_contrast.py | KILLED | KILLED | 2 |  |
| m16-holm-family-five | negative | b5_generator_contrast_report.py | KILLED | KILLED | 4 |  |
| m17-pilot-judged | negative | b5_generator_contrast_report.py | KILLED | KILLED | 1 |  |
| m18-launcher-five-jobs | negative | b5_contrast_launch.py | KILLED | KILLED | 1 |  |
| m19-duplicate-skip-restored | negative | p3_s4_loop.py | KILLED | KILLED | 1 |  |
| m20-no-rejected-sidecar | negative | p3_s4_loop.py | KILLED | KILLED | 6 |  |
| m21-rejected-treated-as-prestart | negative | b5_generator_contrast.py | KILLED | KILLED | 2 |  |
| m22-verify-reasons-not-machine | negative | b5_generator_contrast.py | KILLED | KILLED | 4 |  |
| m23-attempt-start-after-runner | negative | b5_generator_contrast.py | KILLED | KILLED | 2 |  |
| m24-report-no-sidecar-reconcile | negative | b5_generator_contrast_report.py | KILLED | KILLED | 3 |  |
| m25-report-b-count-unchecked | positive | b5_generator_contrast_report.py | SURVIVED | SURVIVED | 0 | 等価対照 (SURVIVED が正) |
| m25b-report-b-count-and-sequence-unchecked | both-layers | b5_generator_contrast_report.py | KILLED | KILLED | 1 | 両層変異、予測 node で登録 (DW-M04) |
| m26-report-fitness-median-unchecked | negative | b5_generator_contrast_report.py | KILLED | KILLED | 3 |  |
| m27-diagnosis-not-required | negative | b5_generator_contrast.py | KILLED | KILLED | 1 |  |
| m28-launcher-own-pin | negative | b5_contrast_launch.py | KILLED | KILLED | 3 |  |

**erratum 1 (M10 / M11):** probe を統合 commit 4 で走らせ、fix3 (commit 5) が `test_b5_string_preflight_rejection_uses_wal_and_rc0` を足した後に
期待 node を再検証せず final を走らせた (DW-M07 の「fix 最終 commit で期待 node を再検証」を probe 側で省いた)。final の観測は期待の上位集合
(差は当該 test 1 本だけ、両方 rc=1) で、殺し漏れではなく登録の不足。初回結果は消さず (final の JSON に残る)、final2 で完全集合を再登録して再走した。

**erratum 2 (M25 → M25b):** M25 (report `_validate` の「B と evaluation 件数の照合」だけを外す) は probe で SURVIVED。連番検査 (`b` が 1..b) が件数の
不一致も同時に捕まえるため単独では等価変異だった。段 6 裁定の登録 (「1 評価で B=10 → invalid」) は件数条項でなく連番条項が殺していたので、M25 を等価対照
(positive) に再分類し、両条項を同時に外す M25b を両層変異として予測 node `test_one_evaluation_cannot_claim_B10_m25` で登録 (DW-M04) → final で当該 node に KILLED。

**変異が検出力を持つ範囲の限界:** M13 / M14 (job body) は 84 / 76 node を落とすが、これは TJ の実 shell test が B-5 mode の分岐を全経路で踏むため。
report の変異 (M16 / M17 / M24 / M25b / M26) は固定 fixture 上の検査で、実台帳での検出力は §6 の pilot report 実走で補う。

## 6. 試走 (β) — 既知結果台帳

**主標本には入れない (D2172 項 4 (β)、事前登録 §8 / §11)。n = 1 系列 / arm、`purpose="pilot"`、`registered_judgment="not-applicable-pilot"`。**
台帳の原本は `ledgers/<arm>/` (header / series / events / proposals の写し、sha256 は `pilot/MANIFEST.sha256`)、report は `pilot/report-pilot-final.json`
(sha256 e30afbe0621d63a90db3243afb10fbe91d80c1f39203dec380c82b6f79919005)、session ごとの所要は `pilot/timing-table.md`、集計は `pilot/cost-summary.txt`。

### 6.1 投入

| 項目 | 値 |
|---|---|
| 投入 | 2026-09-20 22:01 JST、login 側 `submit_pilot.py` (launcher API `validate_submit_tree` / `pilot_jobs` / `launch` を import、dry-run → submit)、`pilot/qsub-pilot.log` |
| submit-tree | 統合 commit 4 `11d46a74a` (ledger header `repo_head`)、ccbench PIN 511c9538、hydrate 済み・clean |
| job | random 13636.nqsv (bnode013) / sweep-matched 13637 / llm 13638 (bnode029) / block-stock 13639、queue gen_S、`qsub -v` で env を明示列挙 |
| workload | write-heavy (rr5 / skew 0.9 / rmw=false / records 1,000,000 / threads 48 / extime 3 s / reps 5、較正済み動作点)。verifier 所要が最短の workload として選択 (read-heavy を避ける) |
| verify | legacy 1 回 + 同動作点 trace 5 回 (`--verify-performance`)、全 session で 6 走 serializable・anomalies 0 |
| 予算 | 3 arm × (系列開始 stock 1 + 探索 B=10 + endpoint 再計測 5) + block stock 5 = 53 論理 session ≤ 60、A = 30 / arm |
| cohort / slot key | `t2797-beta-v1`、`b5-generator-contrast-v1|t2797-beta-v1|<arm>|write-heavy|1|<kind>|<n>|attempt-<t>` |
| 生成器の凍結値 | random: 重み表 sha256 876b1b4798fbf79dfefaffd9ccefceaf0beb16cb8561cc5ea4e28745bbd20bdd (M = 2350927428781729131458637903205781083070、Python 3.10.12 decimal)、preimage `b5-generator-contrast-v1|random|write-heavy|1|<a>|<c>`。sweep: `EXTENDED_SWEEP_US` ∩ [1,1000] の 28 点を sha256 順 (write-heavy 系列 1: 8, 25, 600, 50, 100, 200, 12, 250, 150, 2, 800, 75, 300, 6, 5, 700, 10, 3, 15, 560, 1, 400, 900, 4, 500, 1000, 20, 35)。親の独立実装 `independent_random_vector.py` (job dir) と module の値列は一致 |
| LLM arm の構成 | K2 宣言アーム: planner-v4 / coder-v4-autonomous-k2 / critic は `.claude/agents/*.md` の `model: opus`・`effort: high` (planner / coder は tool 無し、critic は Read / Grep / Glob / Bash) を Agent tool の fresh subagent で起動、親 (manager) は Claude Opus 5 (1M) / effort xhigh。knowledge manifest = t2182 の `knowledge-manifest-wal-only.json` (sha256 396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e)、classification `known_result_conditioned_derivative`、leakproof 射影 `llm/leakproof-context-b5.md` (sha256 d72bfe20…)。D2155 の還流 = 直前評価の critic 診断 4 節を `k2_critic_diagnosis` として planner / coder の入力に逐語 (source_sha256 束縛、k ≥ 2 で必須)。各巡の prompt・出力の逐語は `llm/round-<a>/`、`llm/critic-<k>/`、`llm/verbatim/` |

### 6.2 結果 (perf build、5 rep 中央値、abort 率は中央値 rep)

| arm | 系列開始 stock | 探索 1〜10 (値 → tps) | endpoint | 再計測 5 回 | score (中央値) | endpoint CV |
|---|---|---|---|---|---|---|
| random | 1,364,741 | 698→1,144,149 / 1→3,100,429 / 5→4,023,520 / 364→1,478,556 / 70→2,626,605 / 24→3,498,831 / 299→1,593,341 / 3→3,802,659 / 226→1,769,621 / 6→4,056,140 | 6 (評価 10) | 4,045,121 / 4,029,655 / 4,034,491 / 4,045,006 / 4,065,302 | **4,045,006** | 0.34% |
| sweep-matched | 1,373,430 | 8→3,998,376 / 25→3,457,141 / 600→1,215,542 / 50→2,918,390 / 100→2,356,641 / 200→1,848,744 / 12→3,907,863 / 250→1,706,227 / 150→2,055,271 / 2→3,417,972 | 8 (評価 1) | 4,002,540 / 3,971,590 / 3,994,455 / 4,021,554 / 4,005,258 | **4,002,540** | 0.46% |
| llm (K2) | 1,381,041 | 20→3,612,341 / 10→3,978,814 / 5→3,965,995 / 2→3,481,872 / 15→3,769,653 / 8→4,012,680 / 4→3,882,770 / 12→3,893,987 / 6→3,996,828 / 9→3,989,117 | 8 (評価 6) | 4,004,090 / 4,014,473 / 4,011,941 / 4,011,506 / 3,969,903 | **4,011,506** | 0.46% |
| block stock (適応 backoff) | — | 1,359,618 / 1,361,152 / 1,370,819 / 1,354,442 / 1,365,665 (5 session) | — | — | 記述統計 CV 0.46% | — |

- 3 arm とも A = 10 / B = 10 / 論理 16 session / 物理 16 attempt、前処理拒否 0、品質欠測 0 (全 session rounds 1・settled)、機械故障 retry 0、`series-end b-complete`。report の `invalid` / `disqualified` / `corrections` / `reconciled_attempts` はすべて空。
- 3 arm の score は 4,002,540〜4,045,006 で、between-run floor 3.0% の内側 (最大差 1.06%)。stock (適応 backoff、≈1.36〜1.38M) 比では全 arm +190% 前後。**n = 1 なので優劣は言えない** (§7 の統計は本走でのみ)。
- LLM arm の系列は abort 率が固定 backoff 値に対して 9 点すべてで単調 (2 µs 63.4% → 20 µs 28.8%)、throughput は 5〜10 µs で floor 内の平坦域、4 µs 以下で abort 支配の崖 (2 µs −13%)、12 µs 以上で待機支配の低下 (15 µs −6%、20 µs −10%) — critic 診断 (`llm/verbatim/critic-<k>.md`) の帰属で、perf 欠測のため cache 側の機序は分離できていない。random arm は 10 点中 4 点 (698 / 364 / 299 / 226) が 1.1〜1.8M の低域に落ち、sweep arm は sha 順の 1 点目 (8) が最良だった。
- 53 session 中 36 で rep 1 が 5 反復中の最大値 (LLM arm は 16 / 16、random 11 / 16、sweep 8 / 16、block stock 1 / 5)。abort 率が高く throughput が 3.5M 超の候補でほぼ常に出て、1.1〜2.6M の候補や適応 backoff では出ない。median 採用なので fitness は動かないが、run 内 CV を押し上げる。原因は本 wave では特定しない (calibrator 側の確認事項として §8)。
- llc_miss_rate / ipc は全 session で欠測 (gen_S の計算ノードに perf が無い、preflight rc=2)。

### 6.3 所要 (verifier wall の実測、D2172 項 4 (β) の要求)

集計は `pilot/cost-summary.txt`、session ごとの内訳は `pilot/timing-table.md` (subprocess wall / verify 区間 / legacy / performance rep 1 / rep 2〜5 / bench / bench 周辺 / build)。台帳の verify 区間は隣接 `verify_done` の差 = trace 走行 + verifier + 周辺処理で、純 verifier 秒ではない。

| 項目 | 実測 |
|---|---|
| job Elapse (NQSV) | random 17,286 s (22:01:37 → 02:49:39) / sweep 17,269 s / llm 21,259 s (22:07:50 → 04:02:05、親の handshake 待ち ≈ 7,360 s を含む) / block-stock 5,447 s。合計 61,261 s = 17.0 h の node 時間 |
| session の subprocess wall (53 session) | min 499 / 中央値 1,024 / max 1,521 s、合計 53,805 s (14.95 h) |
| うち home 共有 lock の待ち (推定: performance rep 1 − rep 2〜5 の中央値、bench 周辺 − bench 本体) | 合計 ≈ 31,575 s (8.8 h、wall の 59%)。verify pass 側 max 829 s、bench 側 max 1,058 s |
| 固有費 (wall − lock 待ち推定) | min 217 / 中央値 498 / max 509 s、合計 22,230 s (6.18 h)。abort 率 ≥ 30% の候補は中央値 502 s (performance rep 2〜5 が 84〜91 s)、< 30% は 263 s (34〜48 s)。**他 3 job 終了後の llm session 7 本 (評価 9〜10、score 1〜5) は 499〜510 s で lock 待ち ≈ 0** — 固有費の直接実測 |
| 内訳 (固有費) | build 15〜17 s、legacy verify 7〜16 s、performance verify 5 rep × 34〜91 s (候補の abort 率に依存)、bench 本体 16.8〜17.0 s |
| LLM arm の親手番 | 10 巡、proposal 公開まで 10〜13 分 / 巡 (critic 4〜5 分、planner ≈1 分、coder ≈1 分、親の保存・検査・prompt 生成)。request → proposal の handshake 待ち合計 ≈ 7,360 s (job Elapse − subprocess wall の和)。1 機会 2,700 s の上限に対し最大 ≈ 13 分 |
| 先行見積りとの差 | 事前の外挿 (12〜14 分 / session) は lock 待ち込みの wall (10.7〜25.4 分) に対しては下限側、固有費 (3.6〜8.5 分) に対しては上限側だった |

lock 待ちの帰属 (`pipeline.py` の performance tag verify pass が `bench_lock()` 下で回り、`p3_s4_loop_pegasus.sh` が `IZANAGI_BENCH_LOCK` を設定しないため
home 共有の `~/.izanagi/bench.lock` を 4 job が取り合う) は decisions fragment `{{D:b5-pilot-execution-facts}}` に記録。B-10 / A-5 の job body は `$TMPDIR/bench.lock` を設定している (先例)。

## 7. 受入全走・検査

- 受入全走 (`tools/dev_wave_wait.py acceptance`、門番付き script `run-acceptance-gated.sh` (t2288 → t2795 の写し)、post-claim の main 取込み込み、shards 3):
  - attempt 1 (tag final、tested main `9389277b0`、tip `e4f4c900c`、04:21〜04:29 JST): rc=70、赤 2 件 = `test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites` / `::test_reviewed_process_launch_inventory_is_recursive_and_exact` (本 wave 起因、§4 の fix4 で是正)。
  - attempt 2 (tag final2、tested main `3dbe5a41e` (12 commit 前進を自動 merge)、tested tip `088bbdec7`、04:40〜04:52 JST): **child-green、26,739 passed / 69 skipped、red 0、flake 0** (受領証 `acceptance-receipt-final2-1.json`、scheduler loadgroup)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`): 本 wave の insight に hit 0。rc=1 は 2026-09-17 着地済みの既存 4 file
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) の既知 hit で本 wave 由来ではない。
- `git diff --check` (逐語 4 file の可逆正規化後に緑)・`python3 tools/check_docs.py` (記録 commit 前と main 取込み後に「違反なし」)・provenance 全史監査 (記録 commit 後 12,043 件で新規違反なし、rc 0)。land の全史監査は `dev_wave_land.py` が lock 内で再走する。

## 8. 裁定パッケージ (本走認可に向けて再提示する項)

D2172 項 4 (γ) で試走後に決めるとされた 2 の残部・4・6 と、試走で判明した運用事実を、**発効 commit は作らずに**再提示する。本走の認可・発効束の固定はユーザーの裁定。

### 8.1 (γ) 2 の残部 — 凍結する実験構成の実値 (試走で使った実物)

| 項目 (事前登録 §12) | 試走の実値 | 本走で固定する際の注意 |
|---|---|---|
| LLM のモデル exact ID と推論設定 | role 子は `.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md` の `model: opus` / `effort: high`、親は Claude Opus 5 (1M) / effort xhigh。Agent tool の返答に exact model ID は載らない | 発効束には agent 定義 file の sha256 と親 session の model 設定 (`~/.claude/settings.json` の `model` / `effortLevel`) を組で記録する。exact ID の機械記録が要るなら別途手段が要る (本 wave では作らない) |
| 全役割の prompt | `llm/round-<a>/{planner,coder}-prompt.md`、`llm/critic-<k>/critic-prompt.md` (生成器は job dir の `llm_round.py`、template の sha256 は `llm/MANIFEST.sha256` の各 prompt で束縛) | template を repo の tool にするか、job dir の script を発効束に写すかを決める |
| 知識射影 | `llm/leakproof-context-b5.md` (sha256 d72bfe20…)、knowledge manifest 396cd559… (t2182、WAL のみ、3 variant) | K2 の知識源を本走でも同じ manifest にするか |
| 入力 schema・初回入力・欠測時の表現 | `llm/round-1/planner-prompt.md` の JSON (current_perf / k2_critic_diagnosis (k ≥ 2) / knowledge_input / leading_indicators (null 欠測) / whiteboard)、`request-<a>.json` の `current_perf_source` | 欠測は null と「0 でも差なしでもない」の但し書きで表現した (parent_disclosures) |
| D2155 の還流 | critic 診断 4 節の逐語 + source_sha256、k ≥ 2 で両側 (planner / coder) 必須 (`assert_inherited_inputs`) | — |
| random 分布・sweep 順序 | §6.1 の凍結値 | 本走の系列 (w, r) ごとに sweep 順序は sha256 で決まる (module `sweep_order`)、random の重み表は共通 |
| n = 12 | 試走は 1 系列 (n = 1) | 本走の 108 系列 (3 workload × 3 arm × 12) の schedule を発効束へ |

### 8.2 (γ) 4 — 費用と総実行 wall 上限

事前登録 §11 は「総実行 wall の管理上限は試走の実測所要への倍率で決める」と定める。倍率はユーザーが決める。試走の実測は次のとおり。

- **1 論理 session の固有費 (lock 待ちを除く): 217〜509 s、中央値 498 s。** abort 率の高い候補 (write-heavy の平坦域 5〜12 µs) は ≈ 500 s、低い候補は ≈ 260 s。上限として **510 s / session** を使うと、1,773 論理 session × 510 s ≈ 904,000 s ≈ **251 時間の node 時間**。retry (機械故障 +2) と品質再測定 (最大 3 round) は別計上 (試走では 0)。
- **並列化の前提:** 現行 job body のまま並列 job を流すと home 共有 lock で performance verify pass (5 rep) と bench が job を跨いで直列化され、並列度を上げても総 wall は縮まない (試走 4 job で wall の 59% が lock 待ち)。**本走の job body は `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` (B-10 / A-5 と同じ node-local) を設定する必要がある** (実装は本 wave の scope 外、別 wave)。node-local lock なら N job 並列で総 wall ≈ 251 h / N (+ queue 待ち)。
- **1 系列 (16 session) の job Elapse:** 試走は 17,269〜21,259 s (lock 待ち込み)。lock 待ちが無ければ 16 × 510 s ≈ 8,200 s に、LLM arm では親手番の待ち (10 巡 × 10〜13 分 ≈ 7,000〜7,800 s) が加わる。gen_S の Elapse 上限 86,400 s は 1 系列 / job なら十分。
- **LLM arm の親 (人間または AI) の手番:** 108 系列 × 10 巡 = 1,080 巡、1 巡 10〜13 分 (critic の診断 4〜5 分が最長) → 直列なら ≈ 180〜235 時間の親 wall。並列系列に対して親が巡を pipeline できる設計 (handshake は job ごとに独立) だが、その運用 (親を何本立てるか、1 機会 2,700 s の timeout との整合) は未設計。**これが本走の律速になりうる** — 試走の 1 系列でも親手番の待ちが job Elapse の 35% を占めた。
- **queue 待ち:** 試走は投入 (22:01:24) から 13 秒で 3 job、6 分 25 秒で llm job が RUN (日曜夜間)。別欄に記録するのみ。
- 縮小案 (n = 9 等) は結果を見る前に別仕様として固定する規則 (§11)。本 wave では提案しない。

### 8.3 (γ) 6 — 本走の対象 commit

- (α) の部品は本 wave の land commit (段 9 で確定、統合 commit 5 `65272f3c8` + 記録 commit を main へ取り込んだもの) に存在する。**本走の対象 commit はそれ以降の main** とし、8.2 の job body 変更 (node-local lock、必要なら job ごとの submit-tree) を含めた commit を改めて名指す。
- 試走の campaign.lock は exact-63 grammar で記録されている。着地済みの t2344 (main `285477c00` 以降) で v2 authority grammar が exact-85 になったため、試走 campaign を最新 checkout の certified 経路で読み直すことはできない (HISTORICAL_RAW のみ)。台帳 event と report は campaign.lock を読まないので既知結果台帳としては完結する。
- `hooks/guard_bash.py` は main の `admission_registry.json` を読むので、launcher `tools/pegasus/b5_contrast_launch.py` は land 後に初めて Bash から直接起動できる (試走は job dir の `submit_pilot.py` が API を import した)。

### 8.4 試走で判明し、本走前に裁定か確認が要る事項

1. **perf カウンタ欠測:** gen_S の計算ノード (bnode013 / bnode029) に perf が無く llc_miss_rate / ipc が全 session null。本走でも同じなら critic の機序帰属は throughput / abort / CV の 3 指標に限られる。受容するか、perf のあるノード種を要求するか。
2. **rep 1 の系統的高値:** 53 session 中 36 (LLM arm は 16 / 16) で rep 1 が最大 (+0.85〜+6.0%、abort 率が高いほど大きい)。median 採用で fitness には効かないが、CV ゲートに近づく候補 (abort 60% 超) がある。calibrator 側で warm-up の要否を確認する事項 (本 wave では変えない)。
3. **同 job 直列評価への between-run floor 3.0% の適用根拠:** 系列内の tie 判定は別 run で較正した floor に依存する。本走では endpoint 再計測 5 回 (別 campaign) が同値の 2 回目以降の測定になる (試走の endpoint CV は 0.34〜0.46%)。
4. **LLM arm の同一値再提案:** harness は受ける (fresh 評価、`duplicate-skip` は B-5 mode で拒否) が、試走の planner / coder は方向契約 (increase / decrease) の下で同一値を選ばなかった。方向契約に「同値再評価」を足すかは本走の凍結構成の問題。
5. **共通 Tier0 (§3.1) は未実装** (`tier0_status="not-implemented"`)。試走では build 失敗が 0 だったので発火していない。
6. **1 つの submit-tree から 4 job を同時に流した際の cache 公開競合:** 試走では落ちなかった (先着の公開を後続が cache hit) が一般保証ではない。本走の launcher は job ごとに submit-tree を分けるか、競合を検査する。

## 9. 一次資料

- 依頼・brief・追補・裁定: `verbatim/T-2797-origin.md`、`verbatim/brief.md`、`verbatim/brief-addendum-1.md`、`verbatim/s4-adjudication.md`、`verbatim/s6-adjudication.md`
- codex 入出力: `verbatim/s2-plan{-prompt,}.md`、`verbatim/s3-consult-{A,B}{-prompt,}.md`、`verbatim/s5-author-{A1,A2,A3}{-prompt,}.md`、
  `verbatim/s6-review-{A,B}{-prompt,}.md`、`verbatim/s6-fix{1,2}{-prompt,}.md`
- 試走の台帳・report・所要: `ledgers/<arm>/` (header / series / events / proposals)、`pilot/` (report-pilot-final.json、timing-table.md、cost-summary.txt、evidence/<arm>/{job.stderr,compute-result.json,reservation.json}、submit_pilot.py.txt、qsub-pilot.log、MANIFEST.sha256)
- LLM arm の逐語: `llm/` (round-<a>/ の prompt・request・proposal、critic-<k>/ の prompt、verbatim/ の planner・coder・critic 出力、leakproof-context-b5.md、MANIFEST.sha256)
- 変異: `mutation/` (spec 3 本、結果要約 3 本)
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/` (HANDOFF.md、codex artifact、focus、mutation 結果 JSON 全文、submit-tree、ledgers の slots / handshake、evidence の job.stdout、materials/llm の入力 JSON)
