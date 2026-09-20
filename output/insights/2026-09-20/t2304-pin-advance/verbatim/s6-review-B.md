## 所見

1. **3 点同一性と履歴：refuted / nit。不整合はない。**

   `external/ccbench` の HEAD tree entry、`s8b_approved.py:67`、`pin.py:31` は整合する。

   ```text
   gitlink = e9e477ca1b55348ab4530de0b1cf663ce4555290
   CCBENCH_FULL_SHA = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
   CURRENT_PIN = "e9e477c"
   ```

   指定 diff では `s8b_approved.py` の他の定数・凍結 SHA・import 束縛は変更されていない。AST 比較でも当該定数と docstring 以外は一致した。

   `pin.py:6` の履歴も、候補の実 Git 履歴と一致する。

   ```text
   ef9328a3 2026-08-21 feat(mocc): add correctness trace v2 hook
   058d0c4e 2026-08-23 fix(mocc/trace): move the trace include comment ...
   ae6880f7 2026-08-28 feat(mocc): add T-1943 payload lineage witness
   e9e477ca 2026-08-28 fix(mocc): preserve TRACE=0 include identity
   ```

   9 月 20 日は pin 前進日であり、候補 commit の作成日とは混同していない。D2150 項 1 の承認対象とも一致する。成果物への不正な変更は認めない。

2. **波及：real / must-fix。`CURRENT_PIN` が admission policy 全体を変え、独立 full OID の系列も影響を受ける。**

   **根本箇所は `orchestrator/campaign/build_admission.py:499`。** author 報告の「波及」は STOCK_BASELINE 判定だけを挙げ、policy 自体の変更を落としている。

   ```python
   def _new_policy() -> BuildAdmissionPolicy:
       preimage: dict[str, object] = {
           "schema": POLICY_SCHEMA,
           "repo_stock_pin": CURRENT_PIN,
   ```

   このため、新値への変更は **全 class の policy SHA を変更する**。旧 full OID、review receipt、generator receipt を保持しても回避できない。

   - **K2 次巡**：`p3_s4_loop.py:112` の独立 full OID は保持されるが、`:3037` で現行 policy を campaign config に入れる。`ident.py:84` はその policy を identity に含め、`:139` は旧 lock との不一致を拒否する。
   - **A-1 sized**：`paper_story_a1_paired.py:1076` は v3 の canonical full OID を保持する一方、`:7061`、`:7071`、`:7350` で現行 policy を束縛する。旧系列と同じ campaign identity にはならない。
   - **凍結 v2 g1 chain**：`s8b_ratified_freeze.py:3261` の launch 検証は現行 policy を要求する。履歴 reverify の `None` 分岐とは異なる。
   - **B-4 床値の旧 binary 再利用・resume**：`s8b_floor_campaign.py:8149` と oracle の `s8b_oracle_driver.py:1003` は、旧 protocol の pin に加えて現行 policy を要求する。

   決定的な拒否箇所は `s8b_binary_admission.py:368`。

   ```python
   if expected_policy is not None:
       ...
       if admission["policy_sha256"] != expected_policy.sha256:
           raise BinaryAdmissionError("receipt admission policy が現行 policy と不一致")
   ```

   **放置時の影響：旧 pin 系列の campaign ID が変わり、旧 lock の継続や凍結 binary の live 消費が policy 不一致で拒否される。** 既に起動して旧コードを保持するプロセスまで即時停止するという意味ではなく、新コードでの再起動・継続・live 検証が問題になる。

   land 前に、この policy 世代の扱いを解決する必要がある。旧成果物の SHA を張り替える、現行照合を一律に外す、履歴検証用 `None` を live 経路へ流す修正は適切でない。「独立 full OID なので影響なし」という D2150 の前提に対する新事実として親へ返すべきである。

   **付随する報告漏れ：real / nit。** `backoff_requested_us.py:627`、`autonomous_trial_completeness.py:893` の旧 identity 拒否と、`tools/pegasus/probes/t2187_adaptive_const_probe.py:888` の成立不能も未記載。

   ```python
   if CURRENT_PIN != PIN_FULL[: len(CURRENT_PIN)] or head != PIN_FULL:
   ```

   T-2187 の `PIN_FULL` は旧 full OID のままなので、新コードではどちらの checkout でもこの条件を通らない。ただし指定された稼働中系列への接続は確認できず、独立の must-fix には数えない。

3. **④ 実測：形の再実測としては refuted / nit。引数完全一致・2 版再確認という主張は不可。**

   `shape-probe/t2304_shape_probe_job.sh:54` の configure は Release、sanitizer OFF、compiler、prefix、base-only、disconnected、TRACE を指定している。`buildcache.py:1947` の `_v2_commands` と共通する regime である。

   ```text
   -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF
   -DCMAKE_C_COMPILER=/usr/bin/gcc -DCMAKE_CXX_COMPILER=/usr/bin/g++
   -DCMAKE_PREFIX_PATH="$PREFIX" -DFETCHCONTENT_BASE_DIR="$BASE"
   -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCCBENCH_TRACE="$trace"
   ```

   ただし、本番は genome の defines、条件付き binary-path defines 等も加えるため、**全 production invocation と同一 argv ではない**。probe は `-G` を明示していないが、生成された cache は 3 件とも `Unix Makefiles`。本番 `_v2_commands` も generator を明示していない。

   Python probe の `:40` は本番と同じ次の関数を、実 configure 済み build dir に対して呼ぶ。本番呼出箇所は `buildcache.py:2860`、`:2869`。

   ```python
   buildcache._assert_fetchcontent_fully_disconnected_effective
   buildcache._masstree_source_root_from_cmake_cache
   ```

   compute build0/build1、login build0 の各 JSON `:15` 以降はすべて T-1997 と同形で、両 check が成功している。

   ```text
   FETCHCONTENT_BASE_DIR:PATH=<base>
   FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=
   CMAKE_GENERATOR:INTERNAL=Unix Makefiles
   set(CMAKE_MULTIPLE_OUTPUT_PAIRS
     "<base>/masstree-src/config.h" "<base>/masstree-src/libkohler_masstree_json.a"
     )
   ```

   `cp -a` は export-ignore される `cc/oze` も保持し、`.git` 除去はこの CMake 生成物形を変える要因には見えない。したがって**今回の形状検査について source root の代替として妥当**。一方、HEAD 照合だけではコピー時の tracked clean を証明しないため、完全な source provenance・本番 build 全体の等価性まで主張しないこと。

   **CMake 版の差は real / nit。** shell `:26` は両ノードで intelpython の CMake を優先し、`login.out:20` も明確に次を記録する。

   ```text
   cmake version 3.25.0
   ```

   新 pin の 3.22.1 は未確認。旧 pin の 2 版実測を保持し、新 pin は 3.25.0 のみと限定して記載すれば、今回の形状再実測として再走必須とはしない。brief の「login = 3.22.1」を完了したとは記録できない。

4. **buildcache docstring の未更新：real / nit。段 6 fix で実測範囲を追記する。**

   `buildcache.py:1058` は現在も旧 pin の事実だけを記す。

   ```text
   この cache / DependInfo の形は CMake 3.22.1 と 3.25.0、CCBench pin
   ``511c9538e4e8efa54b45cda62e72389ed3b706ec``、Unix Makefiles 生成器で
   同一と実測された。
   ```

   旧記述自体は誤りではない。放置しても受理集合は変わらないが、新 pin 再実測の範囲と限界がコードから追えない。下記文案で追記する。

5. **land 経路：refuted / nit。設計どおりだが、初回失敗を未 land と扱わないこと。**

   `tools/dev_wave_land.py:5464` は gitlink 変更時に postcondition failure を追加する。

   ```python
   if gitlinks_changed:
       failures.append(
           "tested range changes gitlinks; D16 post-land submodule synchronization "
           "remains required"
       )
   ```

   `orchestrator/tests/test_dev_wave_land.py:2954` は、main が tip に進んだ後も失敗し、submodule 同期後に `already-landed` となる経路を固定している。

   必要な対処は次のとおり。

   - 初回 `landed-postcondition-failed` 後に main HEAD を確認し、merge のやり直しや rollback と解釈しない。
   - main の submodule object DB に候補 commit が存在することは `cat-file -t` でも確認できた。対象 gitlink への checkout に候補取得の fetch は不要。`--remote` を使わず同期し、同じ land 要求を再実行する。
   - 他 wave が新しい superproject tip を取り込んでも submodule が旧 HEAD のままなら、`dev_wave_land.py:1895` の clean gate を落とす。各 worktree の gitlink に合わせて同期する。旧 pin の測定用 checkout を一律に新 pin へ変更しない。
   - `.gitmodules:4` の `branch = izanagi-trace` は通常の gitlink checkout を妨げない。`--remote` では別 branch を追うため不使用を維持する。今回 branch 設定の変更は不要。

   放置時の影響は land 完了状態の誤報告、または後続 wave の clean gate 停止であり、実装上の追加欠陥は認めない。

## 波及の全数表

同一動作の consumer はまとめた。行番号は repo 内、probe は `tools/pegasus/probes/` 配下。

| consumer | 新値での挙動 | 設計どおりか |
|---|---|---|
| `build_admission.py:499,510` | policy preimage・SHA が全 class で変更 | **既存系列への無影響という前提と不整合。must-fix** |
| `build_admission.py:674,728,758` | 新 short pin の clean stock を受理。旧 stock receipt は現行検証で拒否 | stock 集合の移動自体は意図内 |
| `ident.py:84,139`、`wal.py:2800` | policy を含む campaign identity が移動。旧 lock の live 継続を拒否 | 上記 must-fix の波及 |
| `p3_s4_loop.py:112,3037` | source は旧 full OID、policy は新値。K2 identity が変わる | **full OID だけでは保護されない** |
| `paper_story_a1_paired.py:1076,7071,7350` | v2 は pin 自体も移動。v3 sized は旧 full OID でも policy が移動 | **v3 無影響とはいえない** |
| `s8b_floor_campaign.py:4836,5825,5884,6495,8149` | 現行 policy を要求する binary 消費・resume が旧 receipt を拒否 | 上記 must-fix の波及 |
| `s8b_binary_admission.py:368` | HUMAN_REVIEWED でも policy SHA 不一致を拒否 | 述語は正常。pin 前進との整合が未解決 |
| `s8b_ratified_freeze.py:3261` | g1 の launch 検証は旧 policy を拒否。履歴 reverify は別経路 | **live chain に影響** |
| `s8b_holdout_freeze.py:1522` | result binaries に現行 policy を要求 | 上記 must-fix の波及 |
| `s8b_oracle_driver.py:1003` | run contract の旧 pin を保持しても旧 policy の binary を拒否 | 上記 must-fix の波及 |
| `s8b_floor_campaign.py:1033,1057` | 現行 env 契約候補が 1 件なら旧 pin protocol を返す。複数なら新 gitlink exact を優先 | 意図どおり。旧 protocol 一律拒否ではない |
| `s8b_floor_campaign.py:1130,1296,1312` | reseal の target pair、builder の C4-4 と出力 pin が新 gitlink へ移動 | 意図どおり。新 protocol の発行は別作業 |
| `paper_story_a2_certification.py:3694` | 新 canonical short pin を要求 | 意図どおり |
| `paper_story_a2_certification.sh:304–327`、`submit_paper_story_a2_certification.sh:212–230` | 7 桁形式に加え repository pin・実 HEAD の照合先が移動 | 意図どおり。regex 適合だけでは説明不足 |
| `s1_measurement_freeze.py:266,437` | 新規 document の既定 pin が移動。hold 解除時は旧 recorded pin を拒否 | 意図どおり。hold 中は marker 経路 |
| `backoff_requested_us.py:516,627` | 旧 reference の policy と pin を拒否。新規走行・記録は新 pin | 報告漏れ。旧記録の live 再利用に影響 |
| `autonomous_trial_completeness.py:893` | 旧 pin の producer identity を拒否 | 報告漏れ |
| `backoff_profile.py:76`、`backoff_sweep.py:55`、`between_run_floor.py:55`、`pegasus_floor_scoping.py:39` | alias が新 pin へ追随し、checkout・新規 campaign/build identity が移動 | 新規現行系列として意図内 |
| `backoff_extended_sweep.py:187,337,582`、`backoff_overthrottle.py:419`、`backoff_requested_us.py:1068` | source 解決・patch 適用・build・出力 identity が移動 | 新規現行系列として意図内 |
| `b10_backoff_static_tail_formal.py:306,751`、`b10_backoff_shape_sweep.py:88` | 新規 campaign/source が新 pin へ移動 | 同上。旧比較 policy は別途保持 |
| `s3_lock_coverage.py:53`、`s5_permutation_coverage.py:50`、`s6_sort_sweep.py:87` | pinned-clean、patch、build 対象が移動 | 意図内 |
| `axis_trigger_gating.py:59`、`axis_mocc_temperature.py:21` | 軸 source の pin が移動 | 意図内 |
| `p3_s4_loop_sort.py:103`、`p3_s4_loop_trigger_gating.py:72` | 直接／import alias により新規 identity が移動 | 意図内 |
| `s8a_trigger_coverage.py:60`、`s8a_trigger_sweep.py:104` | trigger 軸 alias を介して移動 | 意図内 |
| `s1_verify_extime_calibration.py:57` | 較正検証走行の source pin が移動 | 旧較正 record の取得事実は変更しない |
| `t1683_rr5_cost_probe.py:94,237` | 新 pin の HEAD・clean source を要求 | 現行 pin probe として追随 |
| `t2187_adaptive_const_probe.py:72,888,2718` | 旧 full OID と新 CURRENT_PIN が両立せず起動拒否。recorded source 照合も移動 | 歴史 probe の据置きとして明記が必要 |
| `tools/check_docs.py:1376,6754` | literal 再掲検査の対象が `e9e477c` へ移動 | LIVING_DOCS 34 件で該当 0 行。`docs/phase3.md` も解消済み |
| `env_contract.py`、`calibration_verify.py`、登録済み較正 record | path/hash 等の束縛を保持。現行 pin との等値照合による一律拒否はない | D2150 項 1(iv)どおり |
| A-1 v3 登録、`paper_story_a1_paired.py:205,2400`、job shell `:366` | 新 pin checkout は旧 canonical source 契約で拒否 | 意図どおり。ただし policy 波及は別問題 |
| `mocc_trace_v1_policy.json:20–21` | base=旧、new=候補の比較端点を保持 | 意図どおり。base を新 pin に置換してはいけない |

## docstring 文案

`buildcache.py:1058` 以降を、例えば次の 4 行とする。

```text
旧 pin ``511c9538e4e8efa54b45cda62e72389ed3b706ec`` では CMake 3.22.1 / 3.25.0 で同形を実測済み。
新 pin ``e9e477ca1b55348ab4530de0b1cf663ce4555290`` でも CMake 3.25.0 の計算ノード・login で同形を確認した (T-2304、新 pin の 3.22.1 は未確認)。
いずれも Unix Makefiles・base-only で、空値の FETCHCONTENT_SOURCE_DIR_MASSTREE が 1 行あり、DependInfo の pairs は <base>/masstree-src/{config.h,libkohler_masstree_json.a}。
CCBench pin 更新時は生成物の形を再実測すること。
```

## 攻撃したが破れなかった点

- gitlink・full SHA・7 桁 prefix の整合、凍結定数の保持、4 commit の履歴は成立している。
- floor resolver の一意候補 fallback は存在し、旧 protocol を新 gitlink 不一致だけで拒否しない。
- probe は実 CMake 生成物に対して本番の 2 関数を呼んでおり、模擬 cache の成功ではない。
- 3 件の cache と DependInfo は T-1997 と同形。旧 pin からの差分も `cc/mocc/transaction.cc` の 141 行追加だけで、CMake は不変。
- LIVING_DOCS の新 pin literal 再掲は 0 件。
- D16 の同期後再実行経路はコードと専用 test に存在する。ただし本レビューでは pytest は実行していない。

## 総括

**must-fix 1 件。NO-GO。**

`CURRENT_PIN` の変更が admission policy 全体を変えるため、独立 full OID や旧凍結の保持だけでは K2・A-1 sized・g1 live chain・床値 resume を保護できない。land 前にこの波及を解決する必要がある。実測については、新 pin の確認範囲を CMake 3.25.0 に限定して記録すればよい。