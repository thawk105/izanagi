# [T-2304] ccbench pin を 511c9538 から e9e477ca へ前進した — 実装・再実測・波及の記録

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 裁定: D2150 項 1 (2026-09-18、ユーザー承認)。材料 = `output/insights/2026-09-17/t2756-pin-evidence/README.md`。
- wave: `dev-wave-t2304-pin-advance` (branch `worktree-dev-wave-t2304-pin-advance`、base main `947fd160a`)。段 2/3 省略の軽量版、段 6 敵対レビュー 2 本 + 相談 2 本。
- job dir (生ログ・patch・probe の実体): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/`。逐語は `verbatim/`。

## 0. 結論 (先に書く)

1. **前提 (D2150 項 1 (ii)) は成立した。** 2026-09-20 13:17 JST、GitHub `thawk105/ccbench` だけを取得元とする single-branch fresh clone (`--branch izanagi-mocc-pin-e9e477ca`) で HEAD = `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`511c9538…` はその祖先 (間 4 commit: ef9328a3 / 058d0c4e / ae6880f7 / e9e477ca)、差分は `cc/mocc/transaction.cc` の 141 行追加のみ。
2. **① 3 点を同一 commit で更新した** (`827682b60`): gitlink `external/ccbench`、`s8b_approved.CCBENCH_FULL_SHA`、`pin.CURRENT_PIN` (7 桁 `e9e477c`)。`PREVIOUS_PIN` / `KICKOFF_PIN*` と alias 参照 (`PIN = pin.CURRENT_PIN` 等) は据え置き (先例 fb5e74a17)。
3. **④ 生成物形の再実測は同形だった** (§2)。計算ノード bnode019 (CMake 3.25.0、g++ 11.4.0、configure TRACE=0/1 + `ycsb_mocc.exe` build) と login pegasus02 (CMake 3.25.0 と 3.22.1、configure のみ) で、production の `_assert_fetchcontent_fully_disconnected_effective` と `_masstree_source_root_from_cmake_cache` が実 build dir に対して OK。
4. **⑦ test の追随は 2 層あった。** (a) 現行 pin の literal 7 行 (author) と、(b) **admission policy の epoch 移動**に伴う golden の追随 (fix、§3)。後者は `build_admission` の policy preimage が `repo_stock_pin = CURRENT_PIN` を含むため policy sha が `949ddcc2…` → `db6bc9ea…` へ動いたことによる (前回 pin 前進 T-816 と同型)。旧 pin を control・凍結成果物・比較 policy の base・歴史 fixture とする 43 行は据え置き。
5. **新事実 2 点を D2150 項 1 の射程限定として決定台帳へ追記した** (§4、spool fragment)。「主経路は影響を受けない」は固定 checkout での継続と旧証拠の保持についてだけ成立し、新 main での live 消費 (旧 policy の binary / lock、`resolve_current_floor_protocol`) には成立しない。承認対象・実装範囲・②③⑤の時期は変えない。
6. **land の順序**: 並行 wave [T-2724] (凍結 v2 g1 の A/X) の land 完了 tip が local main に含まれることを確認してから、その main を取り込んだ tip の受入を経て land する (§4、相談 D / X の一致)。
7. clang 14 は D2150 項 1 (iii) のとおり未確認のまま限界として記録 (本 wave で再検査していない)。

## 1. 変更の実体

| 区分 | 変更 | commit |
|---|---|---|
| gitlink | `external/ccbench` 511c9538e4e8efa54b45cda62e72389ed3b706ec → e9e477ca1b55348ab4530de0b1cf663ce4555290 | `827682b60` |
| 定数 | `orchestrator/campaign/s8b_approved.py` `CCBENCH_FULL_SHA`、`orchestrator/campaign/pin.py` `CURRENT_PIN` (docstring に前進履歴 1 段) | `827682b60` |
| test (現行 pin literal、群 A 7 行) | `test_p3_build_authority_cli.py` `_EXPECTED_REPO_STOCK_PIN`、`test_p3_s4_loop_sort.py:781`、`test_p3_s4_loop_trigger_gating.py:2170`、`test_s6_sort_sweep.py:390`、`test_s8a_trigger_sweep.py:108,485`、`test_t126_qualification_driver.py:785` | `827682b60` |
| docs | `docs/phase3.md` 見送り台帳 [T-167] 行の pin literal 除去 + 前進の追記 (check_docs の literal 再掲検査が新値で発火するため)、`docs/phase3-8b-restart-runbook.md` P1 の期待 gitlink | `827682b60` |
| test (policy epoch、実 checkout 照合、builder golden、fixture 整合) | §3 の 10 file | `ad966d12f` |
| production (probe) | `tools/pegasus/probes/t2187_adaptive_const_probe.py` `PIN_FULL` (同 probe は `CURRENT_PIN == PIN_FULL[:7]` を自ら要求するので据え置くと起動不能) | `ad966d12f` |
| docstring | `orchestrator/campaign/buildcache.py` `_masstree_source_root_from_cmake_cache` (新 pin の再実測範囲) | `ad966d12f` + 後続 fix |

据え置いたもの (規律 7、D2150 ②③⑤⑥⑧⑨): 較正 record、凍結 floor protocol (`output/s8b-freeze/**`)、A-1 v3 登録の `canonical_pin`、mocc 比較 policy (`tools/pegasus/mocc_trace_v1_policy.json` base=511c / new=e9e4)、`p3_s4_loop.py:PIN` (D1936 の独立 full OID、CURRENT_PIN と照合しない)、backoff 解析 3 本の `CCBENCH_PIN` (事前登録済み系列の束縛)、`.gitmodules` の `branch = izanagi-trace` (`--remote` 不使用)、群 B の test 43 行。

## 2. ④ 生成物形の再実測 (buildcache が要求する CMakeCache / DependInfo)

| 実行 | 場所 / 版 | configure | check 2 関数 | build |
|---|---|---|---|---|
| compute build0 (TRACE=0) | bnode019、request 12613 (generic task)、CMake 3.25.0 (`/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/cmake`)、g++ 11.4.0 | rc=0 | `DISCONNECTED_OK` / `MASSTREE_ROOT_OK` | `ycsb_mocc.exe` rc=0 (698680 bytes) |
| compute build1 (TRACE=1) | 同上 | rc=0 | OK / OK | `ycsb_mocc.exe` rc=0 (709928 bytes) |
| login (3.25.0) | pegasus02、同 intelpython cmake | rc=0 | OK / OK | (configure のみ) |
| login (3.22.1) | pegasus02、`/usr/bin/cmake` | rc=0 | OK / OK | (configure のみ) |

4 件とも cache 3 行は `CMAKE_GENERATOR:INTERNAL=Unix Makefiles` / `FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=` (空値、出現 1 行) / `FETCHCONTENT_BASE_DIR:PATH=<base>`、DependInfo の `CMAKE_MULTIPLE_OUTPUT_PAIRS` は `<base>/masstree-src/{config.h,libkohler_masstree_json.a}` の 1 組で、T-1997 (旧 pin) の記録と同形。計算ノードの所要は configure 2 回 + build 2 回で 26 秒 (13:58:57〜13:59:23)。configure 引数は production の `_v2_commands` と同じ regime (Release、sanitizer OFF、`/usr/bin/gcc` `/usr/bin/g++`、`CMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps`、base-only FetchContent、`FETCHCONTENT_FULLY_DISCONNECTED=ON`) だが genome defines・binary-path defines は含まない (形の再実測であり、全 production invocation との argv 同一性や source provenance の完全性は主張しない — レビュー B 所見 3)。source snapshot は実 checkout の `cp -a` (`git archive` は `cc/oze` を export-ignore で落とすため不使用)。probe 2 本は Codex author 作、親が実走 (`verbatim/t2304_*.md`、出力 `verbatim/shape-probe-*`)。

## 3. ⑦ test 追随 — policy epoch の移動

焦点走 set1 (計算ノード request 12617、61 file): 6541 passed / **104 failed / 75 errors**。理由別集計は `verbatim/focus-set1-classified.txt`。原因は 1 つ: `build_admission._new_policy()` の preimage `{schema, repo_stock_pin=CURRENT_PIN, coder_authority, generator_registry, review_registry}` の sha256 が `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44` → `db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a` へ移り、現行 policy に束縛された golden がずれた。fix (`ad966d12f`) の方針 = 旧 epoch (T-816) を歴史 golden として残し、T-2304 epoch を production 関数の直接評価で再計算した literal で追加し、現行 ≠ 旧 の負例を保つ (先例 a80daf834 / fb5e74a17)。

| file | 変更 | 赤 |
|---|---|---:|
| `test_dynamic_backoff_transitions.py` | `PIN_FULL` → 新 (setup で実 checkout の HEAD と比較し、その include/ を複製する) | 75 errors |
| `test_t2187_adaptive_const_probe.py` | `PIN_FULL` → 新 (実 HEAD 照合)。t2417 policy performance の producer fixture だけは旧系列の pin を注入 (analysis 側 `backoff_policy_performance_analysis.CCBENCH_PIN` は事前登録済み系列の束縛で不変) | 28 |
| `test_autonomous_trial_completeness.py` | `_CURRENT_POLICY_BOUND_CAMPAIGN_IDS` / `_CURRENT_WORKLOAD_CAMPAIGN_EPOCHS` を 1 段進め、旧 current は `_T816_*` として保持 (+ inline golden 1 行は後続 fix) | 57 |
| `test_campaign.py` | representative / backoff / S6 の campaign ID と cache key golden に `_T2304_*` を追加 | 4 |
| `test_s8a_trigger_sweep.py` | `_ADMISSION_POLICY_SHA256` → 新 (旧は `_T816_*`)、`_T2304_S8A_CAMPAIGN_IDS` 追加 | 6 |
| `test_s8b_protocol_builder.py` | builder の独立 golden bytes / sha を再計算 (旧は `_T816_*` として保持)、approved 定数の期待 sha | 3 |
| `test_s8b_floor_campaign.py` | public preflight fixture: clone の gitlink を選択対象 protocol の pin に合わせる (versioned = 511c9538、legacy = d706650)。新 gitlink では現行 env 契約の候補 2 件・head exact 0 件で `resolve_current_floor_protocol` が fail-closed になる (production の設計どおり、§4) | 3 |
| `test_p3_s4_loop_trigger_gating.py` / `test_p3_s4_loop_sort.py` | campaign ID golden に T-2304 epoch を追加 | 3 |

焦点走 set2 (fix 後、同 61 file、request 12617 の次): **1 failed / 6719 passed / 31 skipped**。残 1 = `test_campaign_identity_is_pinned_without_producer_helper_oracle` の inline golden (dict を oracle にしない独立 pin) の取り残し → 後続 fix で T-2304 値へ。期待値の反転・緩和・skip・削除は無い (レビュー A / B の検算)。

焦点走 set3 (fix2 / fix3 後): **6720 passed / 31 skipped / 0 failed**。ただし受入全走 pre-1 (3 shard、25,967 test) で焦点走の file 集合に無かった **赤 24 件**が出た (fix4〜6、commit `05c04a4cc` / `a2e3c73cb`): (a) policy epoch golden の残り 11 (`test_p3_s4_loop` 4、`test_p3_autonomous_workload_trial` 3、`test_p3_b4_closed_critic` 3、`test_s8b_materialization` の manifest golden 1 = build record の admission receipt を含むため。sealed 実走の実測値 `f7f7a421…` を採用)、(b) `test_between_run_floor` 2 = **候補 e9e477ca は mocc に correctness trace v2 hook を足す commit なので、「mocc に hook 証拠が無い」を前提にした source-facts test と負例が反転**した (source-facts は新 pin の事実 silo / mocc = True・tictoc = False へ、負例は hook の無い tictoc を被験にして意味を保つ)、(c) `test_b10_backoff_shape_sweep` 11 = **記録済み B-10 formal 系列 (LEGACY campaign ID、pin 511c953) の report collector が歴史 lock の identity を動く現行 `PIN` で照合**していた → 材料 ⑨ (旧測定・比較 policy の保持) に従い `LEGACY_REPORT_CCBENCH_PIN = "511c953"` に束縛 (production `b10_backoff_shape_sweep.py:3193`。受理集合は「現行 pin 一致」→「記録 pin 一致」への縮小。新規走行の `PIN` 参照は不変)。b10 module の +4 行で `test_ccbench_spawn_sites` の行番号 pin 2 箇所 (3644 → 3648、4470 → 4474) も追随。fix 後の焦点走 set4 (12 file) = 1473 passed、main 取り込み後の set5 / set6 も緑。

## 4. 新事実と親の裁定 (D2150 項 1 の射程限定、spool decisions fragment)

- **A. policy epoch**: 現行 policy を要求する live 経路 (`s8b_binary_admission` の receipt 照合、`s8b_ratified_freeze` の `LaunchValidatedFreeze`、`s8b_floor_campaign` の旧 binary 再利用・resume、`ident` の旧 lock 拒否、`p3_s4_loop` / `paper_story_a1_paired` の policy 束縛) は、旧 policy で admission された binary / lock を新 main から消費できない。独立 full OID は source pin を固定するだけで policy 束縛を免れない。加えて `p3_s4_loop.py:3035` の `assert_pinned_clean(fixed_sub, PIN=511c9538)` は新 main の submodule で fail-closed (D2150 が ③ として承知の帰結)。
- **B. floor protocol 解決**: `resolve_current_floor_protocol()` は新 gitlink の checkout で fail-closed (候補 2 件 = anchor d706650 / versioned 511c9538、head exact 0 件)。新 pin の successor protocol は AI reseal (材料 ⑤)。
- **止まる作業 (相談 D / X の点検)**: 稼働中 attempt (K2 round 3、A-1 sized 再走、B-4 床値の窓 job) は固定 commit の submit-tree で走り新 main を読まないので止まらない。B-4 floor-pair の receipt 検証は `expected_policy=None` の経路で current resolver を呼ばない。g1 の official launch (W-4) は T-2724 自身が記録した lineage 矛盾で本日中に起きる状態ではない。**新 main から旧系列を再開・再投入する場合**は、系列ごとに ② (新登録・新 identity) ③ (driver の pin) ⑤ (successor protocol) と source / admission の整合が要る。旧 binary の再 admission だけでは旧 lock の継続も source pin の不一致も解消しない。
- **裁定 = O2 (訂正版)**: wave は tested tip まで完成させ、[T-2724] の land 完了 tip が local main に含まれる (`git merge-base --is-ancestor`) ことを確認してから、その main を取り込んだ tip の受入を経て land する。待機は policy 問題の解決ではなく「旧 pin + A/X を含む pin 前進前の commit を歴史再開の起点として先に確定する」ための順序。O3 (停止・再裁定) はユーザーの恒久指示 (相談して親が決める) の下で採らず、O1 (即 land) は T-2724 の残工程に新しい拒否原因を持ち込む。決定台帳への追記は `docs/spool/decisions/2026-09-20-dev-wave-t2304-pin-advance-1.md` (D2150 の逐語は書き換えない)。

## 5. 変異 matrix (MUT-1〜3、DW-M01 事前登録)

harness = `tools/mutation_worktree.py` (独立 clone `mutation-source`、main = 実装 tip `225eba8184666b0230d44d37d6631a580055b358`、`--runner-mode dispatch`、runner file = `test_s8b_approved` / `test_p3_s4_loop_sort` / `test_p3_s4_loop_trigger_gating` / `test_s6_sort_sweep` / `test_s8a_trigger_sweep` / `test_p3_build_authority_cli` / `test_t126_qualification_driver` / `test_s8b_protocol_builder` の 8 本)。事前登録 (段 4) では killer node を部分列挙していたので、DW-M08 に従い**初回を probe (全件 SURVIVED 期待) と明記して観測 node を集め、完全集合で final spec を再登録**した (probe2 の結果 `verbatim/mutation-probe2-summary.json`: MUT-1 / MUT-2 は MISMATCH = 観測 node 非空、これは kill と読まない)。最初の probe 投入は spec の `timeout_seconds=2700` が dispatch 待機契約 (queue 3600 + grace 600) より短く起動前に中止 (`timeout_seconds=5400` / `hang_timeout_seconds=3000` で再投入)。

| id | category | 置換 | 期待 | 結果 | node |
|---|---|---|---|---|---|
| mut1-ccbench-full-sha-reverted | negative | `s8b_approved.CCBENCH_FULL_SHA` 新 40 桁 → 旧 `511c9538…` | KILLED | **KILLED** | 13 (`test_s8b_approved` 2 + `test_s8b_protocol_builder` 11: gitlink ≠ 承認定数、builder の C4-4 照合と golden) |
| mut2-current-pin-reverted | negative | `pin.CURRENT_PIN` `e9e477c` → `511c953` | KILLED | **KILLED** | 21 (`test_s8b_approved` 2、独立 literal の群 A 6、policy epoch 束縛の s8a / trigger / sort / authority CLI / t126 13) |
| mut3-equivalent-pin-comment | positive (等価) | `pin.py` の comment 1 行の言い換え | SURVIVED | **SURVIVED** | 0 |

final: baseline PASSED、`summary = {KILLED: 2, SURVIVED: 1, MISMATCH: 0, matching: 3/3}`、rc=0 (`verbatim/mutation-spec-final.json` sha256 `f4ff7aaa…`、`verbatim/mutation-final-summary.json`、原本 `mutation-final-results.json` は job dir、sha256 は summary に記載)。単一理由: MUT-1 は承認定数の退行 (gitlink 実測との不一致に全 node が帰着)、MUT-2 は現行 pin 値の退行 (7 桁 literal と policy epoch の両方が同じ 1 変異に帰着)。過剰拒否の正例 = `test_build_admission.py` の STOCK_BASELINE 正例は焦点走 set3 で緑 (記号参照)。

## 6. 受入全走・land

- 受入 = `tools/dev_wave_wait.py acceptance` (post-claim merge で local main を固定 SHA で取り込み、3 shard の全走)。門番 = 他 session の受入 leader ≤ 1 かつ load1 < 60 (`gate-acceptance-loop.sh`)。結果 (receipt・shard log・tested main / tip) は job dir `acceptance-*.{done,log}` / `acceptance-receipt-*.json` に残す (本 commit の後に走るので本節には結果を書かない。緑でなければ land しない)。
- land = `tools/dev_wave_land.py` (§4 の順序: [T-2724] の land 完了 tip `9ac17b806` が main に含まれてから。実際には受入 3 回 (pre-1 = 赤 24、final-1 / final2-1 = post-claim merge が両親と異なる実装面で merge-message-provenance 拒否、final3-1 = child-green) と main 前方 merge 3 回 (`a670b3104` / `1d4d06a27` / `482f19b88`。最後は Codex merge author が 2 file を 3 版から書き、main 側 [T-2795] の新 golden `_DEFAULT_PREIMAGE_BEFORE_PAIR` の `repo_stock_pin` を新 epoch へ追随) を経た)。
- **land の実測 (18:19〜18:23):** attempt 2 で main が `fec4a8187` → `482f19b88` (tested tip) へ ff し、設計どおり `landed-postcondition-failed` (D16 post-land submodule synchronization remains required)。main checkout で `git submodule update --recursive external/ccbench` (fetch なし、候補 object は `.git/modules/external/ccbench` に既在) → submodule HEAD = e9e477ca。**同一要求の再実行 (attempt 4) は rc=27 `unresolved mutating turn`** — turn registry の ticket (seq 142) が `mutating` のまま残り、観測器が「ff 済み・fold 未開始 (expected_fold = planned)・fold state 無し」の形を解決できない (D16 の既存 test は fragment 無し = noop fold の場合だけ)。この dead mutating record は後続の全 wave の land も塞ぐ (`_turn_select` の recovery 集合)。18:3x に peer 6 session へ advisory を送り、`tools/dev_wave_land.py` の回復経路を Codex author で直した (`_observe_dead_land_turn` に landed-fold-pending の分岐、`_finish_land_turn` で同形を `mutating` に残さない、test 3 本)。台帳 = failures fragment (F 採番は fold 時)。修正後の受入と land は本 wave の tip (修正 commit 込み) で取り直し、その land が旧 ticket を `waiting` へ解決して fragment 3 本 (worklog / decisions / failures) を fold する。
- 他 wave の worktree の submodule は各自の gitlink に従い、旧 pin の測定用 checkout を一律に新 pin へ変えない。

## 7. 限界・据え置き

- clang 14 の TRACE=0 前処理同一性検査は未確認 (D2150 項 1 (iii))。
- 新 pin の生成物形は CMake 3.22.1 (configure) / 3.25.0 (configure + build) で確認。他の generator・他の compiler は未確認。
- ③ の driver 移行 (K2 の `p3_s4_loop.py`、A-1 の v3 契約) と ⑤ の successor protocol、② の新登録は本 wave に含まない。新 main から各系列を再開するときの前提は §4。
- t2187 probe の `PIN_FULL` 更新は「同 probe が CURRENT_PIN と一致することを自ら要求する」ための追随であり、既に記録された t2187 / t2417 の測定 (旧 pin の `ccbench_head` を artifact に持つ) を書き換えない。

## 8. 工数

codex 子 8 本 (author 1、review 2、consult 2、fix 3 (うち 1 は docstring 1 行、1 は inline golden 1 行))。計算ノード job: generic 1 (④、26 秒)、焦点走 3 (各 2.5〜3 分、request 12617 ほか)、変異 probe2 + final (各 4 run、約 15 分)、受入 (job dir の receipt)。login 実行: configure probe 2 回 (3.25.0 / 3.22.1、各 30 秒)。
