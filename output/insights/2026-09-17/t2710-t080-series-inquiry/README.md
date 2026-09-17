---
authority: none
default_effect: no-state-change
---

# t080 e2e 群の別系列化 — 採否を諮り直すための 3 材料と裁定パッケージ (2026-09-17)

依頼は [T-2710] (D2104 項 28、調査手番): 受理集合は変えず (D2068 維持)、`growth_test_holds.py` 保留の実 repo 直接検査は
復帰させず、(1) fixture 検査と実 repo 直接検査の被覆対応表、(2) 別系列へ移した場合の利用時拒否の実効性 (負例で実測)、
(3) 移動後の最遅 shard wall の見積もりを出し、insight + 裁定パッケージにする。**実装差分ゼロ** (probe は job dir に置き repo へ
入れていない)。**結論: 3 材料は揃ったが、別系列化を採るための「受理集合が同値に保たれる」条件は未成立。本 wave では採らず、
親の推奨は毎走維持 + peer [T-2750] の実測待ち。採否はユーザー裁定へ返す (§5)。**

## 一次資料

| 区分 | 所在 |
|---|---|
| 基準 | local main `38353207f` (fresh worktree、clean、startup gate rc=0)。受入成果物 session `895f300a…` (T-2236 の after 走、2026-09-17)、台帳 T-2236 refresh 後 (24,379 entry) |
| 段 1 親 brief | `stage1-brief.md` (訂正前。訂正は `stage4-ruling.md` §2) |
| 段 2 plan (codex read-only) | `stage2-plan.md` |
| 段 3 敵対レンズ A (検出力・受理集合) / B (実効性・費用) | `stage3-lensA.md` / `stage3-lensB.md` |
| 段 4 裁定 | `stage4-ruling.md` |
| 親 probe の出力 (script は job dir、repo 外) | `probe-outputs/` (allocate 再計算 v1/v2、worker 占有、lock mode、判定器負例、束縛失効回数、production verify 実走) |
| 既裁定 | D700 / D701 (opt-in 撤去と既定実行 probe)、D2002 / D2003 (別系列化の 4 条件・collection 不縮小)、D2068、D2104 項 28-29、D358、F485 |

## 0. M (t080 e2e 群) の定義

M = D700 / D701 の **6 function / 11 node** (`orchestrator/tests/test_s8b_oracle_driver.py`、fixture `_t080_stub_free_e2e_repo` の consumer、
`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5` と D701 probe `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default`
の期待集合と一致)。台帳合計 2,302 秒、最長 240 秒。JUnit 実測 (session `895f300a`) は合計 2,539.2 秒、最長 252.5 秒。

| # | node (parametrize id 略) | 台帳 | JUnit |
|---|---|---:|---:|
| M1 | `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` | 240 | 246.5 |
| M2〜M5 | `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact / holdout-artifact / ccbench-current / unknownness-layer2]` | 230 / 220 / 240 / 220 | 237.5 / 233.3 / 252.5 / 233.1 |
| M6 | `test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5` | 220 | 228.5 |
| M7〜M9 | `test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer / extra-r-path / modify-revert]` | 220 / 220 / 230 | 232.9 / 233.0 / 235.1 |
| M10 | `test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28` | 220 | 231.0 |
| M11 | `test_never_issued_generator_tamper_reaches_public_driver_gate_g7` | 42 | 175.9 |

M′ = M + `test_t080_shared_base_builds_real_builder_once_across_processes` (台帳 150、JUnit 173.8 秒、実 builder を `issue_receipt=False`
で 1 回通す) の 12 node。shared-base 群は全部で 13 node だが実 builder を通すのはこの 1 node だけで、snapshot 群 (3 node、2.4〜57 秒) と
`temp_roots_fail_closed` (41 秒、builder 入口で停止) は base を構築しない。M の node は `REAL_REPO_ACCESS_BY_NODE` に無く timed real-repo lock を
持たないが、**実 repo に依存しないわけではない**: base 構築は git 可視の `output/` を fixture へ複製し、M11 は実 `ROOT` の git 履歴と
`external/ccbench` の HEAD を読む。

## 1. 材料 1 — 被覆対応表 (fixture e2e / 保留中の実 repo 直接検査 / 毎走に残る単体検査)

前提: **列 (b) の保留検査は collection に残るが受入では skipped** (`conftest.py::pytest_collection_modifyitems` が skip marker を付ける)。
依頼は復帰させないので、列 (b) の検出力は「現在ゼロ・復帰すれば代替になりうるか」の欄である。列 (c) は毎走で実行される非 e2e の検査。
「M 固有」= 別系列へ移すと **per-run 受入から消える**検出力。plan の初期表をレンズ A が 1 行ずつ検算し、「重複」は述語 (helper) 単位に限る
と確定した (`stage3-lensA.md` A1)。

| 検出対象 (変異) | (a) M: production 経路 / assert | (b) 保留中の実 repo 直接検査 (受入では skipped) | (c) 毎走に残る単体検査 | M 固有 (移すと per-run から消える) |
|---|---|---|---|---|
| known-axes raw bytes 改竄 | M2: `verify_receipt` → `_load_artifact`。HELD 中は active-valid + held marker、`HELD=False` で単一 `known_axes.artifact_bytes` | known-axes one-byte 検査 (保留表)。同 public 経路の重複は未証明 | `test_t080_freeze_migration.py::test_artifact_raw_bytes_are_checked_before_semantic_parse_m08` は `_load_artifact` 直接呼出し、同 reason | 正規発行済み fixture + verifier 全体で「単一原因」になること、hold/release の両挙動 |
| holdout raw bytes 改竄 | M3: 同経路、`holdout.artifact_bytes` | `test_verify_{cli,direct_cli}_accepts_active_t080_receipt_exact_match` は CLI 正常系でこの変異を assert しない | 同 m08 の holdout 枝 | 同上 |
| current ccbench 不一致 | M4: 実 submodule の checkout-only と committed gitlink の 2 状態を `verify_receipt` で、`HELD=False` で単一 `known_axes.ccbench_current` | known-axes foreign-pin 検査 (保留表)。結合被覆は未証明 | `test_ccbench_current_and_basis_gitlink_have_independent_reasons_m11_m12` は helper 直接 (HEAD 取得は stub) | 実 receipt・履歴・worktree の結合 |
| holdout unknownness layer2 (三軸 conjunction file を fixture root に置く) | M5: `verify_receipt` → `_verify_holdout_live_scan` → **production scanner が fixture 全体を列挙**、単一 `holdout.unknownness_layer2`、observation 無し | `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control` は実 repo を `search_repository` で走査 (hit 台帳一致 + positive control >0、refusal reason の assert 無し)。s8c の wave scan も production scan | `MT:527` は scanner を stub (式・候補・規約の変異)、`HT:702` は明示 2 file を渡し `rr20: holdout hit` を検査 | **実列挙 (git 可視 output の複製を含む) から public verifier の exact reason までの結合** — レンズ A: 「検証条件は重複」は広すぎ、同じ入力変異・入口・refusal の重複は無い |
| user commit trailer | M7: `verify_receipt` → `inspect_receipt_history`、単一 `receipt.user_commit_trailer` | 対応 node 無し | `test_invalid_r_trailer_is_rejected_exactly` は合成 repo で `inspect_receipt_history` 直接、reason の包含 | full-valid base で他 reason が混ざらないこと |
| introduction diff (extra R path) | M8: 同経路、単一 `receipt.introduction_diff` | 無し | `test_invalid_r_topology_keeps_independent_ccbench_refusal_j4` は history 単一 refusal、後段 verifier は `_patch_full_gate_to_pass` 下 | stub-free 全結合 |
| modify → revert (履歴改変) | M9: 有効 receipt の 1 項目を変えて戻し、単一 `receipt.history_mutated`、observation 無し | 無し | `test_state_modify_then_revert_is_issued_but_missing` は元 receipt `{}` で history + schema の 2 refusal | 拒否集合が異なる (単一原因) |
| post-R delete の draft 拒否 | M10: 隔離 subprocess で現行 runtime loader を経た `draft_receipt` → `_capture_draft_basis`、`receipt.invalid` + detail `issued-but-missing` | 無し | `test_draft_precondition_rejects_head_mismatch_dirty_and_post_r_reissue` は `_capture_draft_basis` 直接 | 公開 draft 入口 + 現行 runtime loader の結合 |
| never-issued generator tamper | M11: `driver.gate_check` → `s8b_holdout_freeze.verify` の call-edge witness、HELD 中は floor/budget のみ、解除時は known pin + generator hash + floor/budget の exact 集合。**実 `ROOT` の git 履歴から recorded bytes を探し、実 `external/ccbench` HEAD と known pin の不一致を assert** | `ODT:3450` は正常 receipt の gate、`:5054` は CLI 拒否 transport。generator 変異は assert しない | `ODT:4729` は `_verify_source` 直接 (hash 文言)、`HT:803` は入力 file 集合を注入した `verify` | never-issued 分岐から public gate への実到達 + **実 ccbench checkout との比較** (レンズ A A2: 独立項目) |
| draft → validate → finalize → commit → verifier → public gate (正常系) | M1: builder subprocess で発行、`verify_receipt` active-valid、17 observation、`gate_check` は floor/budget の exact 拒否 (allowed=False) | `ODT:3450` は実 repo の既発行 receipt の 17 observation、`HT:1367/1381` は CLI の held 表示 | `MT:630` は static gate 群を stub | 正常発行の全結合 (単体は stub) |
| report の envelope 再導出・current receipt 欠落 | M1 後半: `_campaign_t080_observation` の envelope 同一と、削除後の malformed exact issue | `ODT:3450` の独立検算は別の性質 | 同一経路の重複未証明 | M 固有として計上 |
| §1.4 の 9 helper 直接検査 | M6: `_verify_known_closure` / `_verify_holdout_closure` / `_verify_metadata_closure` / `_verify_known_schema` / `_verify_known_pairing` / `_verify_ccbench_basis` / `_verify_reconstruction_static` / `_validate_positive_control` / `_classify_ancestry` を fixture 上で直接呼び exact reason | 無し | `_verify_ccbench_basis` (`MT:1179`) と `_classify_ancestry` (`MT:1210`) は同 helper・同 reason の重複あり。他 7 件は別 helper か重複未証明 | 発行済み fixture の実 blob / 実 positive-control file に対する exact reason |

**読み方 (D700 の「直接 helper 検査と e2e は受理集合が異なる」の具体化):** 述語 (bytes / pin / 履歴 / hash) 単位の重複は列 (c) に存在するが、
M が守るのは「production が正規に発行した receipt を持つ忠実な repo 複製の上で、stub なしに verifier 全体と public gate を通して単一原因の
拒否が出る」ことであり、これは (b) (c) のどちらも代替しない。特に M5 の**実列挙経路** (git 可視 output の複製 → production scanner) は、
D2068 が whitelist 案を却下した理由そのものの拒否経路で、per-run 受入から外すと「前回系列完走後に land された output/ の conjunction
file」を受入時に検出する経路が無くなる (レンズ A B2)。

## 2. 材料 2 — 利用時拒否の実効性 (負例で実測)

### 2-1. 現行 repo に判定器は無い (実測)

- CI workflow / cron / systemd timer は不在 (`.github` 無し、tracked file に timer/service/workflow 無し)。`SANCTIONED_EXCLUSIONS` は空。
  D700 却下理由 (i)「定期実行基盤の不在」は現在も真。
- production の verify CLI を worktree で実走 (`python3 -m orchestrator.campaign.t080_freeze_migration verify --path output/t080-migration/legacy-freeze-repin.receipt.json`、
  HEAD `38353207f`、login node): **state `active-valid`、held marker 3 本、rc=0、所要 135.5 秒、RSS 957 MB**。系列記録の有無は
  一切参照されない (`probe-outputs/verify-probe.log`)。

### 2-2. 最小判定器の負例実測 (repo 外 probe、production 配線なし)

D2002 条件 1〜3 を満たす最小の完走記録 (`schema_version / series_version / target_commit / expected_nodeids / selected / finished /
terminal / pytest_rc / started_utc / finished_utc`) と判定 R1〜R6 を repo 外 probe に書き、HEAD `38353207f` で走らせた。

| case | 内容 | 期待 | 結果 |
|---|---|---|---|
| P1 | 1h 前完了・commit 一致・11 node 全 passed | accept | accept |
| N1 | 記録不在 | reject | R1:record-missing |
| N2 | 25h 前完了 (期限切れ) | reject | R6:expired |
| N3 | target_commit 不一致 | reject | R3:target-commit |
| N4 | selected が 10/11 | reject | R4:selected-mismatch |
| N5 | rc=0 だが finished ≠ selected | reject | R4:finished-selected-mismatch |
| N6 | 1 件 failed | reject | R5:not-all-passed |
| N7 | rc=0 だが 1 件 skipped (F485 型の沈黙) | reject | R5:not-all-passed |
| N8 | series_version 不一致 | reject | R2:series-version |
| N9 | 完了時刻が未来 | reject | R6:finished-in-future |
| N10 | 記録内では整合だが M 定義が縮んでいる | reject | R4:expected-mismatch |
| N11 | 必須 key 欠落 (job ID だけ) | reject | R1:record-keys |

負例 11/11 拒否、正例 1/1 受理 (`probe-outputs/probe_series_gate.out.txt`、`series-gate-probe/summary.json`)。

### 2-3. 実効性は部分的 (レンズ B、real)

上の結果は**判定器を通った場合**の判定精度であり、D2002 条件 3 の実効性は未成立。理由:

1. **迂回路が複数残る。** migration CLI 直叩き (`t080_freeze_migration.py:2539`)、driver の Python API (`run_block` は公開 `gate_check` を経ず
   専用 gate、`s8b_oracle_driver.py:599/679/1318/1394`)、adapter への古い resolution の注入 (`static_gate_adapter:2424`)、floor の
   `receipt_verify_fn` 差し替え (`s8b_floor_campaign.py:1419〜1467`)、report の `inspect_receipt_history` 直接利用
   (`s8b_oracle_report.py:243/2364`)、旧受入受領証の land 再利用 (`dev_wave_wait.py:3634`、`dev_wave_land.py:1203`)。
   判定は「共通判定ロジック 1 個、呼出し境界は複数」が要り、**診断 (系列自身・修理) → 検証済み利用への昇格境界は未設計**。
2. **判定器は HEAD 完全一致で、closure 束縛の成立証拠に転用できない** (レンズ A B3)。terminal も node 別でなく集計件数。
3. **真正性:** 手書き JSON の正例が通っても、runner 由来の完走事実を証明したことにはならない。

### 2-4. 束縛先と費用 (main first-parent、read-only git)

| 束縛先 | 24h (15 遷移) | 7 日 (126 遷移) | 1 日あたり | 単一計算ノード占有/日 (1 走 250 秒 + 前処理 0〜65 秒と仮定) |
|---|---:|---:|---:|---:|
| HEAD (完全 SHA) | 15 | 126 | 18.0 | 75〜95 分 |
| closure A = `orchestrator` + `tools` + `external` の tree OID | 6 | 59 | 8.4 | 35〜44 分 |
| closure B = A + `output` | 11 | 96 | 13.7 | 57〜72 分 |

- HEAD 束縛は docs-only の land (HEAD~1 → HEAD は 9 file 全部 `docs/`、3 tree OID 同一) でも失効する。
- **closure A / B とも完全閉包でない** (レンズ B): A は `output/` (fixture が複製する git 可視 file) を含まず、A/B とも
  `docs/phase3-8b-descriptor-design.md` (builder の明示入力) を含まず、tree OID は非 ignored untracked・`external/ccbench` の実 checkout
  状態・hold の版を表さない。**「docs-only なら関連しない」は一般化できない。**
- 同期 (受入と並列) なら全体 ≈ max(毎走 251〜255、別系列 ≈316) で 300 秒未満の利得は消える。非同期 (land 後) なら完走まで新版を有効化
  しない順序契約が要る。起動主体・失敗回収・独立期限検知 (利用の無い期間も) は未設計。

## 3. 材料 3 — 移動後の最遅 shard wall の見積もり

### 3-1. 現行の実測 (session `895f300a…`、T-2236 の after 走)

| shard | selected | JUnit wall | test span | span 外 | real-repo lock union | 最忙 worker |
|---|---:|---:|---:|---:|---:|---:|
| shard-0 | 3,908 | 337.9 秒 | 272.3 秒 | 65.5 秒 | 231.9 秒 (173 区間) | 272.3 秒 (2 item) |
| shard-1 | 11,415 | 249.2 秒 | 171.5 秒 | 77.7 秒 | 0 | 171.5 秒 |
| shard-2 | 9,274 | 204.1 秒 | 125.4 秒 | 78.7 秒 | 0 | 125.4 秒 |

- **M の重い 10 node は上位 10 worker を 1 本ずつ占める (占有データからの証明):** M1〜M10 の JUnit は 228.5〜252.5 秒で、1 worker に 2 本
  入ると最大占有 272.3 秒を超えるので別 worker に 1 本ずつ入る。占有 ≥228.5 秒の worker はちょうど 10 本 (272.3 / 265.7 / 253.9 / 252.6 /
  245.3 / 241.4 / 239.5 / 236.3 / 236.3 / 235.2、各 2 item)。M11 (175.9 秒) は 11〜14 番目 (188.7 / 187.4 / 185.8 / 177.8) のどれか。
  よって**この走の割付で M を除いた残りの最忙 chain は 185.8〜188.7 秒**。中身は
  `test_s8c_preregistration_predicates::test_repository_candidate_uses_real_s8c_budget_module` 184.8 秒、
  `test_t080_shared_base_builds_real_builder_once_across_processes` 173.8 秒、
  `test_s1_known_axes_freeze::test_historical_oracle_nonadapter_reaches_current_semantics` 173.0 秒 (各 1 本)。
- **real-repo lock union は直列化の下限ではない:** read は `LOCK_SH`、writer (排他) node は 4 本で台帳合計 0.2 秒、173 区間は最大 22 本が
  同時保持 (区間長の和 1,916.8 秒 vs union 231.9 秒)、単独保持は 28.4 秒。plan の β′ (union 維持で 292〜327 秒) は感度表示に留める。

### 3-2. 台帳による割付の再計算 (`tools/acceptance_shards.py::allocate` を現物 import、台帳は現物)

| 実行母集合 | shard-0 | shard-1 | shard-2 | 最大 | 均等 | shard-0 の最長 node (台帳) | M の配置 |
|---|---:|---:|---:|---:|---:|---|---|
| C (現行、file 粒度) | 7,501.5 | 5,328.3 | 5,328.3 | 7,501.5 | 6,052.7 | 240 (M1) | 11 / 0 / 0 |
| U = C − M | 5,285.4 | 5,285.4 | 5,285.4 | 5,285.4 | 5,285.4 | 170 (`test_repository_candidate_uses_real_s8c_budget_module`) | — |
| U′ = C − M′ | 5,235.4 | 5,235.4 | 5,235.4 | 5,235.4 | 5,235.4 | 170 (同上) | — |
| 仮想 (T-2750 候補 a): `test_s8b_oracle_driver.py` の group 無し node を node 粒度の成分に、M 維持 | 6,052.7 | 6,052.7 | 6,052.7 | 6,052.7 | 6,052.7 | shard-1/2 に 240 (M) | 0 / 6 / 5 |
| 同分割 + U = C − M | 5,285.4 | 5,285.4 | 5,285.4 | 5,285.4 | 5,285.4 | 150 (shared_base_builds、shard-2) | — |

- C の予測 7,501.5 / 5,328.3 / 5,328.3 は T-2236 の記録と一致。現行は file 粒度なので M を除いても同 file の残り 136 node (real-repo 6 を含む)
  は shard-0 の大成分 (25 file、4 group) に残る (成分重み 7,501.5 → 5,199.5)。
- 仮想行は親の初回 probe が nodeid を書き換えて台帳参照を壊し 5,165×3 を出した誤りを、レンズ B の指摘で修正した値 (v2)。

### 3-3. wall への換算 (すべて 1 session からのモデル値、実走ではない)

| モデル | shard-0 | shard-1 | shard-2 | 最遅 |
|---|---:|---:|---:|---:|
| α: wall × (予測負荷′ / 予測負荷) | 238.0 | **247.2** | 202.4 | 247.2 (shard-1) |
| β: span 外 65.5 + この走の残り最忙 chain 185.8〜188.7 (shard-0)、shard-1/2 は α | **251〜254** | 247.2 | 202.4 | 251〜254 (shard-0) |
| M′ | α 235.8 / β ほぼ同じ (次の床 184.8 秒が残る) | 244.9 | 200.5 | 245〜254 |
| T-2750 分割のみ (M 維持) | 65.5 + 240〜252.5 (最長 M node が critical path に残る) | — | — | 305〜318 級 |

- **感度: 228〜265 秒** (当日の shard-0 wall 337.9〜351 秒 = +1.8〜3.9% を機械的に付けた幅)。**信頼区間ではなく、「300 秒を切る」とは断定
  しない** (D357: node 秒は仕事量の代理にならない、D2068: 単発測定は根拠にならない)。M 除外後は他成分が shard-0 へ流入し、worker 割付も
  変わる (β の chain は変更後の再現ではない)。
- 別系列化の独自利得は「最長 node (240〜252 秒) を毎走の実行経路から外すこと」。T-2750 の成分粒度変更は負荷を均すが最長 node は残す。
  両方なら負荷 5,285×3・最長 150 秒。

## 4. D700 却下理由の現状

| 却下理由 (2026-08-23) | 現状 |
|---|---|
| (i) 定期実行基盤が repo に無い | **変わらず真** (CI/cron/timer 不在)。D2002 は外部 scheduler を認めるが、起動主体・失敗回収・独立期限検知が無いと F485 に戻る |
| (ii) opt-in の改名になる | D2002 の 4 条件が**実効化**すれば異なる挙動になる。ただし現状は模擬判定器 11/11 だけで、production 全境界・昇格境界・真正性は未成立 |
| (iii) 直接 helper 検査と e2e は受理集合が異なる | §1 の表で具体化: 述語単位の重複はあるが、stub-free の発行・verifier 全体・public gate・実列挙・実 ccbench の結合は M 固有 |
| D701 probe | 別系列化を止めない (module 単位の collect-only + setup-only なので D2003 型の実行分割を通る)。D701 の「主張の限界」節が予見した種類の限界。維持は必要だが M 本体完走の保証にはならない |

## 5. 裁定パッケージ (ユーザーへ返す)

| 選択肢 | 必要な条件・実装 | 費用 (仮定つき) | 毎走から失うもの | 見積もり (最遅 shard) |
|---|---|---|---|---|
| **(a) 毎走維持 (親の推奨)** | 無し | 現行 337.9〜351 秒を継続 | 無し | 現行のまま |
| (b) T-2750 (成分粒度 file → node) を先に実測 | allocator の成分単位変更 (peer wave 稼働中)、D358 維持 | 別 wave | 無し (受理集合不変) | 負荷 6,052.7×3 に均等化するが 240 秒 node が残る → 305〜318 秒級 (モデル値) |
| (c) 別系列化 (条件付き) | (1) 完走記録 schema と runner 由来の真正な発行 (node 別 terminal)、(2) 独立期限検知 (24h、利用の無い期間も)、(3) 利用時拒否を全境界 + 診断→検証済み利用の昇格境界、(4) 関連入力の閉包定義 (git 可視 output・docs 入力・untracked・ccbench checkout・hold 版) と関連変更時の焦点走、(5) gate 4 を `U = C − M` へ (gate 2/3 は C 全体で維持)、(6) D701 維持 + M 本体完走の terminal 証跡、(7) hold 解除版の有効化前に M 完走、(8) 起動契約 (計算ノード投入経路・失敗回収) | closure A 8.4 走/日 ≈ 35〜44 分/日、closure B 13.7 走/日 ≈ 57〜72 分/日。同期なら利得が消え、非同期なら有効化順序が要る | §1 の M 固有列 (特に実列挙経路と実 ccbench 比較) を各受入走で観測する機会 | α 247.2 / β 251〜254、感度 228〜265 秒。300 秒を切るとは断定しない |
| (d) (b) + (c) | 両方 | 両方 | (c) と同じ | 負荷 5,285×3、最長 node 150 秒 (M′ なら 170 秒) |

**親の推奨: (a) を維持し、(b) の実測結果を待ってから (c) を再度諮る。** (c) の条件 (1)〜(8) は本 wave の scope 外 (追加 gate・検査・台帳)
であり、実装するなら別 wave で D2002 / D2003 に従う。規律 2 に照らし、「述語が重複しているから移してよい」は §1 で示せた行にしか言えず、
示せない行は M 固有として数えた。

## 6. 本 wave が主張しないこと

- 「別系列化すれば受入が 5 分を切る」— 1 session のモデル値 (228〜265 秒) であり実走ではない。
- 「利用時拒否は実効的」— 判定器単体の 11/11 であり、production 配線・迂回路・真正性は未成立。
- 「M は単体検査で代替できる」— 述語単位の重複しか無い。
- 「M は実 repo に依存しない」— timed lock を持たないだけで、output 複製と M11 の実 ccbench 比較は実 repo に依存する。

## 7. 工数

codex 子 3 本 (plan 1、consult 2、`gpt-6-astra` / `medium`、いずれも rc=0・受理検査 OK)。親 probe 6 種 (allocate 再計算 v1/v2、worker 占有、
lock mode、判定器負例、束縛失効回数、production verify 実走 135.5 秒)。計算ノードは受入 1 走 (段 9) 以外に使っていない。
