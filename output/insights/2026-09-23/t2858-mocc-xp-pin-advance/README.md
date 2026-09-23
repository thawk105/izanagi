# [T-2858] ccbench pin を e9e477ca から C = 68106660 (mocc の X/P 計装) へ前進した — 実装・再実測・波及の記録

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 裁定: D2227 項 1 (2026-09-23、ユーザー裁定 択 (a))。範囲は D2150 項 1 と同じ ①④⑦。提示資料 = `output/insights/2026-09-23/t2858-mocc-xp-pin-revalidation/README.md`、材料 = `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md`。
- wave: branch `worktree-t2858-mocc-xp-pin` (base main `65fd1422f`)。段 2/3 省略の軽量版 (前例 T-2304 と同型)、段 6 敵対レビュー 2 本 + 焦点再レビュー 1 本。
- job dir (生ログ・patch・probe・変異の実体): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2858-mocc-xp-pin/`。

## 0. 結論

1. **前提は成立した。** 2026-09-23 20:01 JST、GitHub `thawk105/ccbench` だけを取得元とする single-branch fresh clone (`--branch izanagi-mocc-xp-instrumentation`) で HEAD = `68106660686232781bca3be792a750d3e19d7a8a`、親 = `e9e477ca…` ちょうど 1 本、tree `6dc0883c…`、`cc/mocc/transaction.cc` blob `e393efbf…`、差分は同 file の +64 行だけ (job dir `ghfetch.log`)。
2. **① 3 点を同一 commit で更新した** (`688e79092`): gitlink `external/ccbench`、`s8b_approved.CCBENCH_FULL_SHA`、`pin.CURRENT_PIN` (7 桁 `6810666`)。alias 参照 (`PIN = pin.CURRENT_PIN`) は自動追随。
3. **④ 生成物形は同形だった** (§2)。
4. **⑦ test の追随は 3 層だった** (§3): 現行 pin の独立 literal、admission policy epoch の golden、そして **C で mocc が X/P 証拠を得たことによる事実の反転** (verifier の現行 pin 正負対)。
5. 温度述語の軸 `axis_mocc_temperature.py` は無変更 (資料 §3.2 項 4 の判断。`PIN` は wrong-oid 負例にしか使われない)。決定は decisions fragment (`docs/spool/decisions/2026-09-23-t2858-mocc-xp-pin-1.md`)。
6. clang 14 は D2150 項 1 (iii) / D2227 項 1 のとおり未確認のまま限界として記録 (再検査していない)。較正 record・凍結成果物・旧 proof は旧 pin のまま (規律 7)。TPC-C の commit は含まない。

## 1. 変更の実体

| 区分 | 変更 | commit |
|---|---|---|
| gitlink | `external/ccbench` e9e477ca1b55348ab4530de0b1cf663ce4555290 → 68106660686232781bca3be792a750d3e19d7a8a | `688e79092` |
| 定数 | `orchestrator/campaign/s8b_approved.py` `CCBENCH_FULL_SHA`、`orchestrator/campaign/pin.py` `CURRENT_PIN` (comment に前進履歴 1 段) | `688e79092` |
| test (現行 pin literal・実 checkout 照合) | `test_p3_build_authority_cli.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_t126_qualification_driver.py`、`test_dynamic_backoff_transitions.py`、`test_t2187_adaptive_const_probe.py` | `688e79092` / `36beaed58` |
| production (probe) | `tools/pegasus/probes/t2187_adaptive_const_probe.py` `PIN_FULL` (probe 自身が `CURRENT_PIN == PIN_FULL[:7]` を要求) | `688e79092` |
| test (policy epoch golden) | `test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_b4_closed_critic.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s8a_trigger_sweep.py`、`test_s8b_protocol_builder.py`、`test_s8b_materialization.py` | `688e79092` / `36beaed58` |
| test (事実の反転) | `test_verifier.py` の現行 pin 正負対 | `36beaed58` |
| docstring | `orchestrator/campaign/buildcache.py` `_masstree_source_root_from_cmake_cache` (④ の再実測) | `5dfc2df0d` |
| docs | `docs/phase3.md` 見送り台帳 [T-167] 行に承認と前進を追記 (C の literal は記号参照へ)、`docs/phase3-8b-restart-runbook.md` P1 の期待 gitlink、`patches/README.md` の候補 patch 節の採用注記と旧計装節の「現 pin」誤記訂正 | `688e79092` |

規模 (`git diff --numstat 65fd1422f 5dfc2df0d`): production (`orchestrator/campaign`・`tools`) +15 / −10 行 (定数・comment・probe 1 行・docstring)、test +209 / −58 行。Codex 子 = author 1、fix 2、review 2 + 焦点再レビュー 2 回 (1 回目は形式不受理)。

据え置いたもの (規律 7、D2150 ②③⑤⑥⑧⑨): 温度述語の `PROOF_PIN`・template・proof、`s3_mocc_lock_coverage.py` の `PIN`、`s3_mocc_template_proof.py` の proof OID、mocc 比較 policy (`tools/pegasus/mocc_trace_v1_policy.json`)、mocc 系 test の旧 pin 束縛 (`test_mocc_proof_surface.py` の `_E9`、`test_mocc_mutation_proof.py` の `_PIN`、`test_mocc_trace_job_contract.py` の `NEW_OID`、`test_mocc_xp_pin_candidate.py` の `BASE`)、図 15 の出所、`test_p3_s4_loop.py` の捕捉時 preimage、較正 record、凍結 floor protocol、T-2304 以前の歴史 golden。

## 2. ④ 生成物形の再実測

計算ノード bnode009 (request 21112、generic task、Elapse 35 秒)、CMake 3.25.0、g++ 11.4.0。source は wave 木の submodule (HEAD = C) の `cp -a` snapshot (`git archive` は `cc/oze` を落とすので不使用)。前例の Codex 作 Python probe (`t2304_masstree_shape_probe.py`、引数駆動) をそのまま使い、job shell だけ Codex author が T-2858 版を書いた (前例との差は path・期待 HEAD・変数名だけ)。

| 構成 | configure | 2 検査 (`_assert_fetchcontent_fully_disconnected_effective` / masstree root) | `ycsb_mocc.exe` build |
|---|---|---|---|
| TRACE=0 | rc=0 | OK / OK | rc=0 (698,680 bytes) |
| TRACE=1 | rc=0 | OK / OK | rc=0 (711,464 bytes) |

cache 3 行 (`CMAKE_GENERATOR:INTERNAL=Unix Makefiles`、空値の `FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=`、`FETCHCONTENT_BASE_DIR`) と DependInfo の `CMAKE_MULTIPLE_OUTPUT_PAIRS` (`<base>/masstree-src/{config.h,libkohler_masstree_json.a}`) は前例 T-2304 と同形。参考: 前例の e9e477ca の実測は TRACE=0 698,680 bytes / TRACE=1 709,928 bytes で、TRACE=0 の大きさは同じ、TRACE=1 だけが増えた (計装が TRACE 枝にだけ入ったことと整合。bytes 同一性・`.text` 一致は主張しない。TRACE=0 の同一性の正本は D297 で、C は GCC 2 版で pass、clang は未完了)。CMake 3.22.1 は今回測っていない。

## 3. ⑦ test 追随

焦点走 set1 (実装 commit `688e79092`、75 file = 前例の 61 file + 前例の受入で後から赤が出た 7 file + T-2304 以後の pin 参照 test + DW-O26 の inventory 4 群、request 21111、Elapse 229 秒): **10 failed / 8934 passed / 33 skipped**。前例の初回 (104 failed / 75 errors) より少ないのは、前例の fix が触った file 群を最初から実装子の所有に入れ、policy epoch の golden を 1 巡目でまとめて追随させたため。

赤 10 件の 3 群と処置 (fix1 `36beaed58`):

| 群 | 件数 | 原因 | 処置 |
|---|---:|---|---|
| s8a の effective reasons 読み込み | 8 | 合成 fixture の `_CHARACTERIZATION_PIN` が旧 pin のままで、production の「artifact の ccbench_commit == 現行 PIN」で先に弾かれ、各 test が狙う拒否理由に届かない。この literal は T-816・T-2304 でも現行 pin へ追随してきた合成 fixture 用の値 (実装子は「特定の記録に束縛」と誤分類) | 現行 pin へ追随 |
| floor manifest golden | 1 | build record の admission receipt を含み policy epoch で動く (前例 05c04a4cc と同型)。実装子の sandbox からは値を取れなかった | 焦点走の sealed 実走値 `08158021…` を現行 golden に、T-2304 epoch 値を歴史 golden に保持し「現行 ≠ 旧」を追加 |
| verifier の現行 pin 正負対 | 1 | **C は mocc に X/P 計装を足す commit なので、現行 pin の実 compiled source で mocc の X / P が evidence-present になった**。同じ trace を mocc として検証すると clean・serializable・certified | mocc の期待を新 pin の事実へ。拒否側の被験は X/P 計装を持たない tictoc へ移し、exact record・not clean・indeterminate・not certified を保つ。nodeid は real-repo 系の登録簿に載るので改名しない |

注意: tictoc は現行 verifier の対象 protocol 外なので proof surface は `unavailable` (「対応 protocol の実 source に計装が無い → evidence-absent」ではない)。後者の経路は、対応 protocol の silo・mocc がどちらも C で計装を持つので現行 checkout では到達不能になった。この経路は旧 pin (e9e477ca) を明示 checkout する `test_mocc_proof_surface.py` の verifier test が被覆し続ける (段 6 レビュー A・焦点再レビューで確認)。

再走: set2 (fix1 の 3 file、Elapse 12 秒) = **211 passed**、set3 (変異 runner 8 file、変異単価の測定を兼ねる、Elapse 35 秒) = **419 passed / 2 skipped**。

## 4. 段 6 レビュー

- レビュー A (追随 / 据え置きの分類・弱体化の偽装・過剰削除レンズ): 所見なし、GO。`_CHARACTERIZATION_PIN` の追随、mocc 系の旧 pin 束縛の据え置き、verifier の evidence-absent 経路の旧 pin での被覆を確認。
- レビュー B (3 点同一性・live consumer・land / D16・④): should-fix 1 = buildcache docstring に C の再実測を記録 → fix2 `5dfc2df0d`。3 点一致、C の object が主 checkout の submodule 格納域にあること、旧計装 patch の C への二重適用が無いこと、温度述語の `PIN` の判断を確認。policy epoch による旧 binary / lock の live 消費不能と floor protocol 解決の fail-closed は T-2304 §4 と同型で、今回固有の追加破損は無い。
- 焦点再レビュー: 1 回目は内容 GO だが `## 総括` を見出しでなく太字で書き起動器の形式検査で不受理 (rc=70)。見出し必須を明記して再投入し受理: 前段所見 2 件とも closed、新規所見なし、GO。

## 5. 変異 matrix (段 4 事前登録 + 段 6 erratum)

harness = `tools/mutation_worktree.py` (独立 clone `mutation-source`、main = 実装面の最終 commit `5dfc2df0d`、`--runner-mode dispatch`、runner file = `test_s8b_approved` / `test_p3_s4_loop_sort` / `test_p3_s4_loop_trigger_gating` / `test_s6_sort_sweep` / `test_s8a_trigger_sweep` / `test_p3_build_authority_cli` / `test_t126_qualification_driver` / `test_s8b_protocol_builder` の 8 本)。単価は投入前に同じ 8 file の 1 dispatch (set3、35 秒) で実測した。DW-M08 に従い、初回を probe (全件 SURVIVED 期待と明記した観測走) にして観測 node を集め、完全集合で final を再登録した。

- **probe (spec sha256 `928982a5…`):** 基準走 PASSED。mut1 = 13 node、mut2 = 63 node、mut3 = 46 node (全件 MISMATCH = 観測、kill とは読まない)。
- **erratum:** 段 4 で等価変異 (SURVIVED) として登録した mut3 (pin.py のコメント言い換え) は等価ではなかった。pin.py は contract-loader binding の enforcement 閉包 (作業木 bytes == HEAD blob を要求) に入っており、harness が commit せずに書き換えると内容に関係なく `contract-loader-drift` で 46 node が fail-closed する (正しい挙動。前例 T-2304 の後に入った層)。
- **分解:** mut3 の 46 ⊂ mut2 の 63、mut1 と mut3 の交わり 0 (s8b_approved.py は閉包外)。mut2 だけが殺す 17 node (s8b_approved の gitlink / prefix 照合 2、s8a の effective reasons 読み込み 8 と default-off campaign ID 1、sort / trigger の default cfg・campaign identity・契約 digest 5、t126 の stock source 1) が pin 値の単一理由の証拠で、46 node は drift 層 (冗長 gate) として pin 値の証拠から外す (DW-M03)。
- **final (spec sha256 `cfd52949…`、結果を見た後・final の前に再登録、段 4 裁定文書に追記):**

| id | category | 置換 | 期待 | 結果 | node |
|---|---|---|---|---|---:|
| mut1-ccbench-full-sha-reverted | negative | `s8b_approved.CCBENCH_FULL_SHA` C → e9e477ca | KILLED | **KILLED** | 13 (前例と同じ集合: `test_s8b_approved` 2 + `test_s8b_protocol_builder` 11) |
| mut2-current-pin-reverted | negative | `pin.CURRENT_PIN` `6810666` → `e9e477c` | KILLED | **KILLED** | 63 (値の層 17 + drift 層 46) |
| mut3-pin-comment-contract-loader-drift | negative (drift 層) | pin.py の comment 1 行の言い換え | KILLED | **KILLED** | 46 |
| mut4-equivalent-approved-comment | positive (等価) | s8b_approved.py の comment 1 行の言い換え | SURVIVED | **SURVIVED** | 0 |

final: 基準走 PASSED、`summary = {KILLED: 3, SURVIVED: 1, MISMATCH: 0, matching: 4/4}`、rc=0 (原本 `mutation-final-results.json`、spec・probe 結果・dispatch 受領証の写しは job dir)。計算: probe 4 job 計 112 秒、final 5 job 計 151 秒。

受入全走と land は本書を含む記録 commit の後に走るので、本書には結果を書かない (worklog と job dir の `acceptance-*` / `land-*` が正本)。

## 6. 限界・据え置き

- clang 14 の TRACE=0 前処理同一性は未確認 (D2150 項 1 (iii)、D2227 項 1)。
- CMake 3.22.1 での再実測はしていない (C は CMake に触れない)。
- ②③⑤⑥⑧ (登録・identity・driver 移送・successor floor protocol・較正・性能事前登録) は各新系列の着手時。新 main から旧系列を再開するときの前提は T-2304 insight §4 と同じ。MOCC の floor 系列は C の gitlink と一致する successor protocol が無い間 fail-closed (資料 §3.2 項 6)。
- I 面 ([T-2295])、hot 経路の C 上での再立証、同サイズのポインタ置換の動的立証、mocc の探索面入り、温度述語 hole の採用、TicToc の候補化は含まない。
