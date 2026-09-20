単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/T-2797-origin.md
- ユーザー裁定 D2172 項 4 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2172-item4.md
- 前 wave の設計判断 D2183 (K2 共有 3 部品、pipeline / loop 不変、stock 成功条件) の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2183.md
- B-5 事前登録の逐語 (§3 予算・停止・失敗、§4 生成器、§5 評価経路、§6 endpoint と score、§7 母集団・floor・判定、§10 照合表、§11〜§12 費用と発効束):
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/prereg-s3.md, prereg-s4.md, prereg-s5.md, prereg-s6.md, prereg-s7.md, prereg-s10.md, prereg-s11-12.md (同 dir)
- repo 内 (worktree の path、read-only。行番号は親が 2026-09-20 に読んだ現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `orchestrator/campaign/p3_s4_loop.py` (3410 行: 定数 :115 PIN / :167–170 MAX_ITER・MAX_WALLTIME_S・CONVERGE_STREAK、dataclass :630–690、
  `planner_context_payload` :1292、`check_stop` :1341、`LoopState` checkpoint :1389–1512、`default_cfg` :1574、`default_perf` :1653、`calibrated_perf` :1661、
  `_resolve_duplicate` :1826、`_stock_capability_resolver` :1917、`_run_stock_control_resolved` :1931、`_run_one_iteration_resolved` :2020、
  `load_proposal_file` :2473、`drive_iteration` :2598 (入口 check_stop :2721)、`main` :2938–3410)、
  `tools/pegasus/p3_s4_loop_pegasus.sh` (621 行: PBS 指示行 :1–6、required_env :17–24、K2 env :54–98、`IZANAGI_S4_STOCK_CONTROL` :100–114、driver 起動 :596–621)、
  `orchestrator/campaign/pipeline.py` (`performance_correctness_workload` :193–223 (reps=perf.reps)、`_run_bench` :1301–1470 (bench payload の `tps`/`unstable`/`rounds`/`settled`/`cv`)、
  verify の repetition ループ :2115–2215、`evaluate` :2585)、`orchestrator/campaign/loop.py` (`_closed_verify_workloads` :153、`run_campaign` :347 (`bench_max_rounds` :371))、
  `orchestrator/campaign/p2_2.py` (:54–57 較正定数、:74 WORKLOADS)、`orchestrator/campaign/backoff_extended_sweep.py` (:55–58 `EXTENDED_SWEEP_US`、:112 `MEASUREMENT_SEEDS`)、
  `orchestrator/campaign/ident.py` (campaign_id の preimage)、`orchestrator/campaign/layout.py` (`exploration_campaign_layout` :594)、
  `orchestrator/tests/test_p3_s4_loop_job_contract.py` (1934 行: 逐語 pin `_assert_static_job_contract` :176–474、STOCK_PINS、stage order :548、driver 呼出し回数 test :1866–)、
  `orchestrator/tests/test_p3_s4_loop.py` (10313 行)、`orchestrator/tests/test_p3_exploration_namespace.py`・`orchestrator/tests/test_p3_b4_wiring_probe.py` (静的 inventory pin: layout 呼出し 11・run_campaign 2・import 閉包 49)、
  `orchestrator/tests/test_campaign.py` (:5418 run_campaign caller inventory、:5500)、`orchestrator/tests/test_official_perf_closure.py` (:44–75 `_REVIEWED_PERF_FILES`、:495–535 perf 述語)、
  `tools/pegasus/admission_registry.json` (:112 job body 登録)、`tools/pegasus/README.md` (§7 :331–420 job body の env 契約)、
  前 wave の insight `output/insights/2026-09-20/t2795-pair-launcher/README.md` (§0〜§2 契約) と K2 round 3 の insight `output/insights/2026-09-19/k2-loop-round3/README.md` (親手番の形、materials/ の planner-context / planner-input / coder-input / proposal の JSON 形)。

## 前置き — この依頼の性質

対象は研究用 repo の CC 合成 campaign の**実験基盤の実装と試走設計**である。セキュリティでも攻撃でもない。B-5 生成器対照
(LLM / random / sweep-matched の 3 arm が同じ hole literal 受理文法・同じ検疫・同じ verify → bench 経路で backoff 値を探索し、条件付き優越を
固定予算下で比較する事前登録) の §10 が「実装が要る」とした残部品を実装し、D2172 項 4 (β) の上限付き試走 (1 workload・3 arm × 1 系列・
16 session / arm + block stock 5 = 53 論理 session) の launcher を設計する。正しさゲート (verifier の anomaly → 即 reject、全 verify pass 通過後
だけ COMMIT) は変えない。既存の fixture / proposal / stock-control 経路の既定挙動・identity は bytes 不変で残す。pipeline.py / loop.py /
ident.py / build_admission.py は変更しない (D2183 の前提を継承)。本走は未認可、発効 commit は作らない。

# 依頼 — 段 2 plan を file:line 粒度で起草する

brief の scope 表 (A1-a〜A1-h、A2、A3) と (β) 試走の順で、実装子 (Codex author、workspace-write、コード・テストのみ編集、commit しない) に
渡せる plan を起草せよ。親の provisional 裁定 (P1)〜(P8) は前提ではなく検査対象である — 現物を読んで支持 / 反証 / 条件付きを判定し、
反証なら代案を file:line で示せ。

## plan に必ず含める項目

1. **module 構成と import 方向。** 新 module `orchestrator/campaign/b5_generator_contrast.py` が p3_s4_loop の何を import して使うか
   (`calibrated_perf` / `default_cfg` / `_run_stock_control_resolved` / `_run_one_iteration_resolved` / `load_proposal_file` / `_stock_capability_resolver` /
   `_require_condition_gate` / `_campaign_cfg_for_site` / `_admit_env_contract` / `_current_site` / `PIN` / `MARKER_ID` ほか) を現物の signature で列挙し、
   private 名 (`_` 始まり) を跨いで呼ぶ是非と、必要なら p3_s4_loop 側に足す最小の public seam (名前・signature・既存関数への委譲) を示せ。
   p3_s4_loop が b5 module を import しない (静的 import 閉包 49 を動かさない) こと、新 module が `run_campaign` を直接呼ぶなら
   `test_campaign.py:5418` の caller inventory を更新する必要があること、新 module が perf 名で分岐すれば `test_official_perf_closure.py` の
   `_REVIEWED_PERF_FILES` に載せる必要があること (述語 :495–535 を読んで判定) を書け。
2. **slot ごとの fresh layout (P1)。** `ident.campaign_id` の preimage (spec_content / ccbench_commit / search_tag / search_config / trial) のどこに
   slot key を焼くか (`search_config["b5_slot"]` = `"b5-generator-contrast-v1|<arm>|<w>|<r>|<kind>|<n>"` 案)、それで同 v の重複が別 campaign になり
   `_resolve_duplicate` / terminal skip が構造的に発火しないことを `loop.run_campaign` の skip 経路と `_resolve_duplicate` :1826 の現物で示せ。
   識別 key 名が既存 key と二義化しないこと (D75)。stock (系列開始・block・endpoint 再計測) の slot key 形も決めよ。
   代案 (評価ごとに fresh submit-tree、T-2746 運用) との比較。
3. **系列 driver と停止の不適用 (P2)。** `run_series(arm, w, r, ...)` が `drive_iteration` を通らず、slot ごとに `_run_one_iteration_resolved`
   (または新 seam) を呼ぶ形。`check_stop` / `MAX_ITER` / `MAX_WALLTIME_S` / `CONVERGE_STREAK` / `REVERSE_STREAK` に触れないこと、`LoopState` /
   checkpoint / whiteboard の扱い (LLM arm では planner への射影に whiteboard が要る — slot ごとの layout に 1 件ずつ入るものを台帳が系列単位で
   束ねる形か、系列 layout を別に持つか) を決めよ。A の消費点 (proposal 受理・schema・値域・文法・検疫・Tier0 のどこで A を数え、B を数えるか) を
   `load_proposal_file` :2473 と `_run_one_iteration_resolved` :2020 の現物の分岐 (grammar reject / diff-quarantine reject / build fail / anomaly /
   bench abort / certified) に対応づけて表にせよ。「Tier0 = コンパイル + 固定スモーク」は現行に無い (§3.1) — 現行の build 失敗 (trace / perf) を
   どちらに数えるかを §3.3 の文 (投入後の build 失敗は B) で決めよ。
4. **session 契約と品質欠測 (P3)。** WAL `bench_done` payload (`tps` list、`unstable`、`rounds`、`settled`、`cv`、`median_tps`) から
   品質欠測 = `len(tps) != perf.reps ∨ unstable ∨ settled is not True` を分類する関数と、それを COMMIT 後に読む位置。品質欠測の session の
   fitness を endpoint 資格から外すこと、B を返さないこと、pipeline は変えないことの是非。`bench_max_rounds=3` の明示渡し (`run_campaign` :371) の要否。
   verify payload の `workload["tag"]` が `legacy` / `performance` の 2 種であること (`--verify-performance` 時) と、anomaly の即 reject が
   既存経路で B 消費・endpoint 不採用へ写ることを確認せよ。
5. **random / sweep 生成器 (A1-a / A1-b、P6)。** `decimal` で `m_v = floor(2^128 × ln((v+1)/v))` を算出する手順 (`Decimal.ln()`、prec の選び方、
   prec 100 と 130 で floor が同一であることの検査、`M = Σ m_v`)、1000 要素表と sha256 の保存形式 (発効束の材料、insight へ写す JSON)、
   preimage `b5-generator-contrast-v1|random|w|r|a|c` → SHA-256 → U (unsigned big-endian) → `L = floor(2^256 / M) × M` の引き直し → 累積重みへの
   写像 (bisect) を関数 signature で示せ。sweep: 28 点 (`EXTENDED_SWEEP_US` から 0 を除く) を `b5-generator-contrast-v1|sweep|w|r|v` の SHA-256 昇順
   (同 hash は v 昇順) → 先頭 10 点。両方とも proposal (`PlannerProposal` / `CoderProposal`、`implementation = f"double now_backoff = {v};"`) へ
   どう変換するか、`assert_value_literal_consistent` / `_assert_coder_value_domain` を通ること。§4.3 の「候補起因の不通過なら次点へ進む」と
   §3.1 の A 消費の対応。
6. **系列開始 stock と current_perf (A1-c) / 継承検査 (A1-h)。** stock を系列の最初に `_run_stock_control_resolved` :1931 で独立 slot campaign に
   評価し、WAL COMMIT の `fitness_tps` を `current_perf` として台帳に置く。planner 入力への写し方 (K2 round 3 の `materials/planner-input-4.json` の
   形: `current_perf` / `leading_indicators` / `whiteboard` / `knowledge_input` / `k2_critic_diagnosis`) と、評価 k の planner 入力 whiteboard が
   台帳の評価 1〜k−1 の射影とちょうど一致することを検査する関数 (親が proposal を置く前に呼ぶ / job 側が proposal 受理時に呼ぶ) の signature。
   stock の成功条件 (certified ∧ source STOCK、D2183) が不成立なら系列を「stock 不成立 = 判定不能」で止めるか続けるか (§6 末尾: stock 自身の
   正しさまたは測定が成立しなければ当該比較は判定不能)。
7. **endpoint と再計測 (A1-g)。** §6 の選択規則 (certified ∧ 品質欠測でない、session median 最大、同値は v 昇順 → slot 昇順) を台帳へ**書いてから**
   5 fresh session (別 slot campaign、同 genome) を同 job で回す。anomaly → 不採用 + fallback 記録。fallback の値 = 同 workload・同 block の block stock
   5 session の median (block stock は別 job なので試走では後段の consumer が結合)。
8. **解析 consumer (A2)。** `orchestrator/campaign/b5_generator_contrast_report.py` (または同 module 内) の入力 (台帳 JSON 群)・出力 (JSON + 表)。
   §7.2 の CV 4 つと `f(w)`、`δ(w)`、精度 gate; §7.3 の対差 `d_r = ln(score_LLM / score_b)`、全 2^n 片側 exact permutation (n ≤ 12 なので全列挙)、
   Holm (族 6 固定、判定不能は p = 1)、fallback 対の主 / 副解析の切替; §7.4 の判定順 1〜8。試走 (n = 1) では 4 (対不足) で止まることを確認し、
   記述統計 (score、fallback 数、certified endpoint 数) だけを出す。合成データでの正例 / 負例の test 案。
9. **job body の B-5 mode と launcher (A3、P4 / P5)。** `p3_s4_loop_pegasus.sh` に足す env 名・値域・拒否 (rc=2、repository path 解決より前)・
   既存 3 経路 (fixture / proposal / stock-control) の argv が bytes 不変であること、B-5 mode で系列 driver を 1 起動する argv
   (`"$PY" -B -m orchestrator.campaign.b5_generator_contrast run-series --arm ... --workload ... --series ... --ledger-root ... --fetchcontent-prebuild-receipt ...`
   と、driver 内部で `--calibrated-perf --perf-workload W --verify-performance` 相当を固定する形)、LLM arm の job 内 handshake (stock → `proposal-<k>.json`
   の poll、間隔・上限・timeout 時の台帳記録 = 機械故障扱いか候補起因か §3.3 で決める、`slot-<k>.json` の書出し、atomic rename での受渡し)、
   `test_p3_s4_loop_job_contract.py` の逐語 pin (:176–474 の required、STOCK_PINS、stage order :548、driver 呼出し回数 :1866–) にどの行を足すか。
   `#PBS -l elapstim_req=03:00:00` は pin されており変えない — 親は qsub CLI `-l elapstim_req=08:00:00` で上書きする (19:26 に probe 13465.nqsv で
   CLI が優先することを実測済み)。login 側 launcher (`tools/pegasus/b5_contrast_launch.py`: submit-tree の HEAD / PIN / clean 検査、env 組立、
   qsub argv、`--dry-run` で argv を印字) の signature と test。別 job body file にする代案 (P5 反証) との比較。
10. **試走の設計 (β)。** 4 job (random / sweep / LLM / block stock) の walltime・順序・並列、1 session の所要見積り (legacy verify + 5 × (3 s trace +
    verifier ≈ 115 s write-heavy) + bench 5 rep + build) と、実測して残す項目 (verifier wall を rep / session ごとに WAL のどの record の差分から取るか、
    `bench_wall_s`、build 区間、job Elapse) を書け。上限 (53 ≤ 60 論理 session、retry §3.3) を driver 定数で守る形。試走結果を主標本に入れない
    (既知結果台帳 = insight) こと。
11. **pin 閉包と test。** 変更・新設 file ごとに、既存 exact pin (TJ 逐語 / 静的 inventory / perf file inventory / admission_registry) への影響と更新行、
    新 test file `orchestrator/tests/test_b5_generator_contrast.py` の test 一覧 (正例・負例、`__main__` harness 付き、subprocess は
    `PYTHONDONTWRITEBYTECODE`)、変異 matrix の候補 (各単位に負例 1 つ以上: 重み表の 1 要素改変、preimage の区切り改変、sweep の順序を数値順に、
    品質欠測の述語緩和、A/B の消費点ずらし、endpoint の同値規則反転、handshake の timeout 分類、job body の B-5 mode 拒否除去 ほか) と
    kill する test の対応。
12. **段階分割。** author の分割 (A1 core → A2 report ∥ A3 job body + launcher) の依存 (台帳 schema・CLI) を plan で固定して並列化できるか、
    直列にすべきかを判定せよ。各 author の所有 file を重複なく列挙せよ。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。各項目は file:line を添え、「支持 / 反証 / 条件付き」を (P) ごとに明記。
- 新規 code は signature と 3〜10 行の骨子まで (全文は書かない)。
- 実行できない検査 (pytest など) は「未実走・静的読解」と明記する。sandbox は read-only で書込可能 tmp が無いため pytest 緑は要求しない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は最終メッセージ本文に全文 (file への書出しは不可)。
- 末尾に `## 総括`: (P1)〜(P8) の判定一覧、author に渡す所有 file 表、未確定事項 (親裁定が要るもの) の列挙。
