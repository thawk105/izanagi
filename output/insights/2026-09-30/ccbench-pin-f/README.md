# [T-2854] CCBench の pin を C `68106660` から F `25898d00` へ進めた — 前提の実測・patch の棚卸し・追随・生成器対照の本走との隔離

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 依頼: 第 5 陣 md_15 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_15.txt`、共通指示 common-5.txt)。[T-2854] のうち pin 前進の部分。TPC-C を campaign で評価する配線は範囲外で item に残す。
- 承認の根拠: D2277 項 1 (CCBench の CI が緑の tip に限り pin 前進を承認)、D2293 (C → F の D297 規則 v2 は GCC 11.4 / 12.3 とも pass)、D2322 項 6 (F への pin 前進は AI)。手順の先例: D2150 / D2184、直近の同型 wave [T-2858] (`output/insights/2026-09-23/t2858-mocc-xp-pin-advance/README.md`)。
- wave: branch `worktree-dev-wave-ccbench-pin-f` (起点 local main `908741c6f`、開始 gate rc=0)。段 2・3 を省いた軽量版 (前例と同型で設計の択一が無い)。
- job dir (生ログ・棚卸しの JSON・prompt・子の報告): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-f/`。

## 1. 前提の実測 — F を GitHub から取得でき、CI は緑

2026-09-30 22:13 JST、GitHub `thawk105/ccbench` だけを取得元とする HTTPS の single-branch fresh clone (`--branch izanagi-tpcc-v3-silo-mocc-fmt`) で次を得た (job dir `ghfetch.log`。22:06 の `git ls-remote` も同じ tip、`ls-remote.log`)。

| 項目 | 値 |
|---|---|
| HEAD | `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` |
| tree | `c96b282d12bcbedb6d7513d6c9409f2d02337856` (主 checkout の submodule にある F の tree と一致) |
| 親 | `40a7f4acb174ca43cb590f40d13847216a1564bc` |
| C との関係 | C `68106660…` は F の祖先。C..F は 4 commit |
| C..F の差分 | `cc/mocc/transaction.cc` +83/−34、`cc/silo/transaction.cc` +75/−22、`include/tpcc.hh` +12/−0、`include/trace.hh` +48/−2 (計 4 file、+218/−58、`git diff --numstat`)。CMake・build 設定には触れない |
| check-runs (GitHub API、head_sha = F) | `build` completed / success (2026-09-29T13:42:03Z)、`format-check` completed / success (13:39:47Z)、total 2 |

C..F の 4 commit: TPC-C の trace v3 helper と trace 専用の commit 計数 (`6aa7a58f`)、MOCC・Silo で TPC-C 文脈の trace v3 frame を出す (`53f6b097`・`40a7f4ac`)、clang-format 14 の整形 (`25898d00`)。

## 2. patches/ の厳密適用 — F で新たに外れるのは 4 本

driver と同じ `git apply` (fuzz なし) で、`patches/*.patch` 98 本を GitHub clone から作った C と F の detached checkout にそれぞれ当てた (`--check`、job dir `patch_census.py` → `patch-census.json`)。

| C | F | 本数 |
|---|---|---:|
| 当たる | 当たる | 54 |
| 当たる | **当たらない** | **4** |
| 当たらない | 当たらない | 40 |
| 当たらない | 当たる | 0 |

F で新たに外れる 4 本:

| patch | 外れる箇所 | 現行 pin で当てる consumer |
|---|---|---|
| `broken-mocc-early-unlock.patch` | `cc/mocc/transaction.cc:1257` | なし。`s3_mocc_lock_coverage.py` (`PIN` = e9e477ca)・`test_mocc_proof_surface.py`・`test_mocc_mutation_proof.py`・`test_mocc_xp_pin_candidate.py` はいずれも e9e477ca か C に独立束縛 |
| `broken-mocc-hot-update-unlock.patch` | `cc/mocc/transaction.cc:1257` | なし。`s3_mocc_mutation_proof.py` (`PIN` = e9e477ca) と上の test |
| `broken-silo-corrupt-write-payload.patch` | `cc/silo/transaction.cc:655` | なし。`condition_meaning_gate.py` の define ↔ patch の静的登録と、[T-2847] の一回限りの変異走 (当時の pin e9e477ca) だけ |
| `broken-silo-published-version-mismatch.patch` | `cc/silo/transaction.cc:657` | 同上 |

Silo の 2 本は先行資料 (`output/insights/2026-09-29/silo-intra-txn-fix/README.md` の表「D: F でも当たらない」) と一致する (F の writePhase の整形と trace v3 で文脈が変わった)。MOCC の 2 本は今回の棚卸しで新たに判明した。4 本とも壊し (positive control) で、現行 pin に自動で当てる driver が無いので、作り直しはこの wave では行わず [T-2854] の残りとして item に残す (作り直すなら、F の上で壊れ方が発火することを実走で示すまでが 1 単位)。

単独では両方で当たらない 40 本は、他の patch の上に重ねる前提のもの (骨格 → 計装・probe → 壊し) と旧 pin (e9e477ca) を前像とするものである。このうち C..F の変更 4 file に触れる 17 本を driver の重ね順で当て直した (job dir `patch_layered.py` → `patch-layered.json`)。結果は C と F で全件同じだった:

- Silo の関数方策の骨格 `silo-function-policy-variant.patch` の上: probe (`instr-silo-function-policy-probe.patch`) と壊し 11 本 (`broken-silo-policy-*`) は、probe を挟む順 (driver `silo_policy_coverage.py` の既定) で 11 本とも C・F で当たる。probe を挟まない順では 7 本が C・F とも外れる (probe の行を文脈に持つため)。
- trigger-gating の骨格 → 計装 → `broken-silo-trigger-misattr.patch`、`silo-backoff-fixed.patch` → `silo-backoff-requested-us.patch`: C・F とも当たる。
- MOCC の温度述語の骨格 → `instr-mocc-lock-coverage-temperature.patch`、`instr-mocc-lock-coverage*.patch`: C・F とも外れる (前像 e9e477ca。C は同じ計装を既に含む — `patches/README.md` の記述どおり)。

生成器対照の本走 (md_11) が使う `silo-function-policy-variant.patch` は C・F とも当たる。

## 3. 生成器対照の本走 (md_11) との隔離

D2305 項 1 は本走の pin を C に固定し、途中で変えないとする。本走の submit checkout 16 本 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/trees/c01`〜`c16`) の git 管理 file を 2 回読んだ (着手時と、実装・焦点走の後の 2026-09-30 23:34:27 JST。job dir `trees_head.py`、2 回目の出力 `trees-head-2.txt`。16 行とも同じ 3 値):

- 16 本とも HEAD = `1da88472bc54d7d59c1c8b0430dd67bfb5776618` (detached)、submodule の HEAD = C `68106660686232781bca3be792a750d3e19d7a8a`、worktree lock あり。
- submodule の格納域は worktree ごとに別 (`.git/worktrees/cNN/modules/external/ccbench`)。本 wave が動かすのは main の gitlink と主 checkout の submodule だけで、これらには届かない。

ただし、本走の Silo 方策 driver は `axis_silo_function_policy.PIN = pin.CURRENT_PIN` を読むので、**新しい main から submit checkout を作り直すと pin は F になる**。本走が固定 checkout のまま完走する限り影響は無い。land 後に本走の wave へこの点を知らせる。

## 4. 変更の実体

| 区分 | 変更 | commit |
|---|---|---|
| gitlink | `external/ccbench` C → F | `90f70add1` |
| 定数 | `orchestrator/campaign/s8b_approved.py` `CCBENCH_FULL_SHA`、`orchestrator/campaign/pin.py` `CURRENT_PIN` (comment に前進履歴 1 段) | `90f70add1` |
| production (probe・docstring) | `tools/pegasus/probes/t2187_adaptive_const_probe.py` `PIN_FULL`、`orchestrator/campaign/buildcache.py` docstring (F は CMake・build 設定に触れないので生成物形を再実測していない旨。C の実測は履歴として残す) | `90f70add1` |
| test (現行 pin の独立 literal・実 checkout 照合) | `test_dynamic_backoff_transitions`・`test_p3_build_authority_cli`・`test_p3_s4_loop_sort`・`test_p3_s4_loop_trigger_gating`・`test_s6_sort_sweep`・`test_s8a_trigger_sweep`・`test_t126_qualification_driver`・`test_t2187_adaptive_const_probe` | `90f70add1` |
| test (policy epoch の golden。C epoch = T-2858 の値は歴史 golden に保持) | `test_autonomous_trial_completeness`・`test_campaign`・`test_p3_autonomous_workload_trial`・`test_p3_b4_closed_critic`・`test_p3_s4_loop`・`test_p3_s4_loop_sort`・`test_p3_s4_loop_trigger_gating`・`test_s8a_trigger_sweep`・`test_s8b_protocol_builder`・`test_buildcache_v2`・`test_s8b_materialization` | `90f70add1` / `c2e25f9ae` |
| docs | `docs/phase3-8b-restart-runbook.md` の preflight P1 の期待 gitlink (段 6 レビュー A の should-fix) | `d935925ef` |

規模 (`git diff --numstat 908741c6f d935925ef -- orchestrator tools`): 計 +182 / −60 行、うち production (`orchestrator/campaign`・`tools`) +17 / −11 行 (定数・comment・probe 1 行・docstring)。test は 16 file。Codex 子 = author 1、fix 1、review 2。

据え置いたもの (C に独立束縛、規律 7): `p3_s4_loop.campaign_pin_for_protocol("mocc")` と MOCC の較正の注記、`vhash_cicada_hot_block.PIN`・`vhash_cicada_vlife.PIN`、`test_mocc_xp_pin_candidate.C`、`test_p3_s4_loop_job_contract`・`test_t2849_job_contract`・`test_t2849_loop_entry` の fake `ccbench_head`。e9e477ca / 511c9538 に束縛の MOCC 系・silo 系、較正 record・凍結成果物・旧 proof、`patches/README.md` の各 patch の前像の記述 (当時の事実)、生成器対照の事前登録 (`docs/silo-policy-generator-contrast-preregistration.md` の PIN 行、登録値) も変えていない。

## 5. 焦点走 (計算ノード)

| 走 | 対象 | request | Elapse | 結果 |
|---|---|---|---:|---|
| set1 | 実装 commit `90f70add1`、163 file (前例 [T-2858] の 75 file + pin 消費者を参照する test の grep 追加 88 file) | 39785 | 854 s | 10 failed / 15,705 passed / 56 skipped |
| set2 | fix1 commit `c2e25f9ae`、修正 5 file + sealed runner + 変異 runner 候補 8 file の 13 file | 39992 | 43 s | 1,716 passed / 2 skipped |

set1 の赤 10 件は 2 群だった (処置は fix1 `c2e25f9ae`):

| 群 | 件数 | 原因 | 処置 |
|---|---:|---|---|
| policy epoch の golden の追随漏れ | 8 | `test_p3_s4_loop` の cfg hash と campaign ID 4 件 (`4c200821` → `2f78711e`、`7b19f909` → `cc4650d0`)、`test_s8b_protocol_builder` の承認 protocol sha 2 件 (`6b0c326d…` → `5004ceef…`、長さ 774 bytes は不変)、`test_buildcache_v2` の YCSB cache key 1 件 (`silo_c2d907920f_t0` → `silo_b2c514cb5a_t0`)、`test_s8b_materialization` の floor manifest sha 1 件 (→ `df973e45…`、実装子が採取できなかった値) | 計算ノードで production が返した値へ追随し、C epoch の値を歴史 golden として保持 |
| 実装子の改名ミス | 2 | `test_p3_autonomous_workload_trial` の `_T816_C01_*` を改名し `_C01_*` を二重定義した (`NameError`) | 名前と値を変更前へ戻した。C01 の campaign ID も F で変わる (production の直接評価) ので、C epoch の値を `_T2858_C01_*` に保持 |

正しさの判定 (verifier・anomaly・certified) が変わった赤は無い。F で厳密適用が外れる 4 本の patch を現行 gitlink に当てる test も赤にならなかった。set1 の 1 job 854 秒は common-5 §4 の目安 (1 本 5 分程度) を超えた。同じ worktree からの dispatch は直列が契約 (DW-C00) で、file を割っても合計は減らないため 1 本で流した。

## 6. 段 6 レビュー

- レビュー A (追随 / 据え置きの分類・弱体化の偽装・過剰と削除): should-fix 1 件 = `docs/phase3-8b-restart-runbook.md` の preflight P1 が現行 gitlink を C と期待したままで、F の木で再開手順が必ず止まる → 親が P1 を F へ直した (`d935925ef`、docs の 1 行。C 以前の履歴と凍結 floor protocol の旧 pin の説明は保持)。4 本の patch を現行 gitlink へ自動で当てる経路は見つからなかった。
- レビュー B (3 点同一性・live consumer・生成器対照の本走との隔離・land): 所見なし、GO。本走の launcher は台帳の checkout を job に渡し、job 側が HEAD と submodule の pin を照合する。trace v3 は TPC-C 文脈でだけ選ばれ、YCSB の v2 出力と現行 parser の前提は変わらない。F の object は主 checkout の submodule 格納域にある。policy epoch の移動による旧 binary / lock の live 消費不能と floor protocol 解決の fail-closed は D2184 と同型で、F 固有の追加は無い。
- 焦点再レビューは行っていない。fix1 はレビュー前に入っており 2 本とも fix1 後の木を読んだ。レビュー後の修正は docs の 1 行だけである。

## 7. 変異 matrix (段 4 事前登録 + probe 後の再登録)

harness = `tools/mutation_worktree.py` (独立 clone `mutation-source`、main = 実装面の最終 commit `c2e25f9ae`、`--runner-mode dispatch`、runner file = `test_s8b_approved` / `test_p3_s4_loop_sort` / `test_p3_s4_loop_trigger_gating` / `test_s6_sort_sweep` / `test_s8a_trigger_sweep` / `test_p3_build_authority_cli` / `test_t126_qualification_driver` / `test_s8b_protocol_builder` の 8 本)。単価は焦点走 set2 (この 8 本を含む 13 file、43 秒) で見た。DW-M08 に従い、初回を probe (全件 SURVIVED 期待と明記した観測走) にして観測 node を集め、完全集合で final を再登録した (段 4 裁定文書に追記)。

- **probe (spec sha256 `e04ab2ac…`):** 基準走 PASSED。mut1 = 13 node、mut2 = 63 node、mut3 = 46 node (MISMATCH = 観測、kill とは読まない)、mut4 = 0 node。
- **分解:** mut3 の 46 ⊂ mut2 の 63、mut1 と mut3 の交わり 0、mut1 と mut2 の交わり 2。前例 [T-2858] と同じ構造で、mut2 だけが殺す 17 node を pin 値の単一理由の証拠、mut3 の 46 node を contract-loader drift 層 (pin.py の作業木 bytes と HEAD blob の一致を要求する冗長 gate) とする (DW-M03)。
- **final (spec sha256 `52fbb5fd…`):**

| id | category | 置換 | 期待 | 結果 | node |
|---|---|---|---|---|---:|
| mut1-ccbench-full-sha-reverted | negative | `s8b_approved.CCBENCH_FULL_SHA` F → C | KILLED | **KILLED** | 13 |
| mut2-current-pin-reverted | negative | `pin.CURRENT_PIN` `25898d0` → `6810666` | KILLED | **KILLED** | 63 (値の層 17 + drift 層 46) |
| mut3-pin-comment-contract-loader-drift | negative (drift 層) | pin.py の comment 1 行の言い換え | KILLED | **KILLED** | 46 |
| mut4-equivalent-approved-comment | positive (等価) | s8b_approved.py の comment 1 行の言い換え | SURVIVED | **SURVIVED** | 0 |

final: 基準走 PASSED、`summary = {KILLED: 3, SURVIVED: 1, MISMATCH: 0, matching: 4/4}`、rc=0 (原本 job dir `mutation-final-results.json`、spec・probe 結果の写しも job dir)。harness が記録した所要 (dispatch のキュー待ちを含みうる): probe 5 走 計 752 秒、final 5 走 計 1,525 秒。

受入全走と land は本書を含む記録 commit の後に走るので、本書には結果を書かない (worklog と job dir の `acceptance-*` / `land-*` が正本)。

## 8. 限界・据え置き

- F の上での TPC-C の実走 (v3 trace の出力と認定) はしていない。v3 emitter の実 trace は単位 11 で C2' の上で確かめたもので、F は C2' に整形と `#line` を足した commit である (D2293)。
- F で厳密適用が外れる壊し patch 4 本の作り直しは [T-2854] の残り。
- ④ (buildcache の生成物形) は再実測していない (C..F は CMake・build 設定に触れない)。clang 14 の TRACE=0 前処理同一性は前例と同じく未確認。
- 新 main から旧系列 (C の policy epoch の binary・lock・floor protocol) を再開するときの前提は D2184 と同じで、固定 checkout から走る。
- 生成器対照の本走の隔離は、submit checkout の実物と launcher の照合経路で確かめた。本走が新しい main から checkout を作り直すと pin が F になる点は、本走の wave へ知らせる。
