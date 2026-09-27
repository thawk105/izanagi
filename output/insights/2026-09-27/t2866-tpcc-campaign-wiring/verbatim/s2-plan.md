## 総括

- **最重要の修正点:** 現 pin の TPC-C trace は v2 であり、pipeline は検証を bench より先に行う。したがって現 pin の `pipeline.evaluate` 1 件で「build → bench → verify」は達成できない。期待結果は **trace/perf の build 完了 → v2 reject の WAL 記録、bench 未実行**である。bench 配線は v3 の合成試験と将来の実 binary で確認する。根拠: `pipeline.py:2110-2111, 2208-2214, 2820-2842, 3135-3190`、[D2238](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/verbatim/D2238.md)。
- workload は `evaluate` の既定値付き引数として受け、buildcache と測定関数へ渡す。`PerfConfig` は変えない。`ident.py:196-229` の campaign identity は `search_config` を含むため、TPC-C の production campaign では `search_config.workload="tpcc"` を使い、既存 YCSB の preimage は維持する。
- buildcache は target、binary path、compiler input target を同じ `f"{workload}_{protocol}.exe"` から作る。YCSB の cache key、v2 preimage、manifest bytes は条件付き追加で保つ。
- 実行器は s1 の 57:43 cell だけを検証へ通す。v2 は indeterminate、anomaly または非直列化は disqualified を優先する。s2 と s1 の他の構成は「認定経路なし」のままとする。
- 指定資料とコードを静的に確認した。read-only のためテストと計算ノード実測は行っていない。

## brief (P1)〜(P5) への所見

| 裁定 | 所見 | 根拠・修正 |
|---|---|---|
| P1 | **修正** | `evaluate` は通常 verify-first。v2 reject 時に `_bench_prepared` へ到達しない (`pipeline.py:2208-2214, 3135-3190`)。生死確認は build と WAL reject、bench は v3 fixture 経由の試験に分ける。規律 2 は維持する。 |
| P2 | **採用、補足** | `PerfConfig` は `pipeline.py:188-194` の値で、campaign preimage は `ident.py:196-229` の `CampaignConfig.search_config` に由来する。`pipeline.py` 内に `asdict(perf)` は無い。field 追加を避け、TPC-C campaign の search config に workload を記録する。直呼び `evaluate` は独立 layout を使う。 |
| P3 | **採用** | `verification_status` は anomaly／`serializable is False` を先に disqualified とする (`t2851_transfer_runner.py:466-470`)。v2 の場合は `certified=False` として渡し、reason を既存 `trace-witness-unsupported-workload` にする。 |
| P4 | **採用、試験の条件を明確化** | `Integrity.existence_violation_details` は v2 で `None`、v3 DSG で `[]` から始まる (`verifier/model.py:499`, `verifier/dsg.py:329-349, 385-392`)。`test_campaign.py:7620-7680` の合成 v3 frame を実 verifier に通す正例・負例を実行器試験へ移せる。現 pin の実 v3 到達は主張しない。 |
| P5 | **採用** | production job は gflags と glog を `$TMPDIR` に build/install し、`CMAKE_PREFIX_PATH` を設定する (`tools/pegasus/p3_s4_loop_pegasus.sh:617-673`; 同様に `floor_campaign.sh:999-1145`)。v2 build へは `dependency_prefix` を明示する例が `p3_s4_loop_pegasus.sh:741-753` にある。 |

## プラン

### A — buildcache と試験

`orchestrator/campaign/buildcache.py`:

- `cache_key(..., *, admission, workload: str = "ycsb")` (`:625-645`)、`build(..., *, ..., workload="ycsb")` (`:3414-3459`)、`build_v2(..., workload="ycsb")` (`:3222-3278`)、`_build_v2_impl(..., workload="ycsb")` (`:2386-2420`)、`_v2_commands(..., workload="ycsb")` (`:1949-1962`)、`_v2_identity(..., workload="ycsb")` (`:1303-1398`) に通す。入口で exact `str` の `ycsb|tpcc` を検証する。
- legacy key は `raw` の末尾へ **TPC-C の場合だけ** `|workload=tpcc` を加える (`:640-645`)。これで YCSB の hash と bdir 名は同じ bytes、TPC-C は別 namespace。
- v2 preimage は `workload=="tpcc"` のときだけ `"workload": "tpcc"` を追加 (`:1323-1335`)。YCSB の key 集合と digest を維持する。
- target を一度作り、`_v2_commands` (`:1962`)、binary relpath (`:2708-2711`)、hit 時 compiler target (`:2736-2740`)、fresh 時収集・検証 (`:2928-2931, 2952-2955`)、legacy `build` (`:3453-3469`) に使う。`_v2_result` 相当の再現コマンド生成 (`:2119-2147`) とその呼び出しにも workload を通す。`ccbench_add_protocol` は `${wl}_${name}.exe` を `add_executable` し (`external/ccbench/cmake/ProtocolHelpers.cmake:19-35`)、silo/mocc は `WORKLOADS ycsb tpcc ...` (`cc/silo/CMakeLists.txt:1-3`, `cc/mocc/CMakeLists.txt:1-3`)。出力は `cc/<protocol>/tpcc_<protocol>.exe`。
- v2 cache hit は caller から渡された `binary_relpath` と `compiler_target` で `_validate_v2_entry` が再照合する (`:1626-1640, 1738-1755, 2720-2746`)。fresh の compiler manifest も同じ target で収集・検証する (`:2928-2965`)。target の二重定義を残さない。
- 下流の `build_admission.py:262-298` は独自 admission preimage を正準化するが、buildcache preimage の固定 key 集合ではない。`campaign_lock.py:913-918` は campaign identity の JSON 正準性を検査する別の preimage。`s8b_binary_admission.py:142-150` は genome binding を扱う。今回の target 名追加に伴う固定 key 照合は静的探索では見つからなかった。ただし v2 hit と受領証を通す試験で確証する。

試験案: `test_buildcache.py::test_tpcc_key_and_target_keep_ycsb_golden`、`test_buildcache_v2.py::test_tpcc_v2_identity_and_target_are_distinct`、`::test_tpcc_compiler_manifest_fresh_and_hit`、`::test_invalid_workload_rejected`。正例は silo/mocc の両 target、負例は異なる workload の cache hit を拒むこと。既存 YCSB golden bytes も照合する。

### B — pipeline、calibrator、critic と試験

- `pipeline.evaluate(..., *, workload: str = "ycsb")` (`pipeline.py:3054-3097`) から `_prepare_evaluation_core(..., workload="ycsb")` (`:1638-1674`) へ渡し、`_build_one` の legacy/v2 両呼び出しへ同じ値を渡す (`:2075-2104`)。TPC-C を既存 campaign layout に混ぜないため、production caller は `CampaignConfig.search_config` に workload を入れる (`ident.py:196-229`)。YCSB の search config は変更しない。
- TPC-C の correctness は caller が `CorrectnessWorkload(flags=...)` を渡す。`pipeline.py:155-161` の既定 legacy と `:1809-1812` の自動生成は YCSB flags なので、TPC-C の暗黙既定に使わない。錨 s1-H は `tpcc_num_wh=1`, `thread_num=48`, payment `43`, 他三種 `0`, `tpcc_interactive_ms=0`, `extime=3` (`t2851_transfer_runner.py:77-86`; 事前登録 `:86-110`)。四つの比率 flag は文字列 `"43","0","0","0"` を渡す。`_run_trace` は文字列 exact match で 57:43 のみ受理する (`pipeline.py:452-469`)。s2 や欠落、`"043"` は既存 reason で拒否する。
- `calibrator/runner.py` の `capture_measure_point` (`:825-867`) と `measure_point` (`:1085-1126`) に既定 `workload_name="ycsb"` を足し、`-ycsb_tuple_num` は YCSB の場合だけ同じ位置に入れる。TPC-C では `records` を倉庫数とみなし `-tpcc_num_wh=<records>` を同じ位置に入れる。`PerfConfig.workload` には `tpcc_num_wh` を重複して入れず、比率・think time だけを入れる。`pipeline._run_bench` の二つの `measure_point` 呼び出し (`:1442-1455`) に workload を渡す。`benchparse.py:24-57` は `throughput[tps]` または commit 数／時間を読む一般形で、TPC-C 専用変更は不要と見込む。
- `performance_correctness_workload(perf)` は YCSB の exact 4 key を要求する (`pipeline.py:197-227`)。TPC-C の直呼びでは使わず、caller 指定の correctness を使う。探索 loop は `loop.py:313-324` の verify mode 選択が YCSB 構成を生成するため、この wave の 1 genome 生死確認入口には使わない。`screening` は `pipeline.py:1803-1808, 2680-2715` の別経路なので driver では指定しない。leading indicators は `benchparse.py:65-99` の共通 stdout 項目を読む (`pipeline.py:1538-1549`) が、実 TPC-C stdout の確認は必要。
- critic は `digest.py:1336-1337` の説明のみ「証明済みの commit witness／v3 契約を満たさない workload または TPC-C trace」に直す。reason 文字列と登録集合は変えない。`test_critic.py:976-1000` は reason の保存を検査するので、説明文の表示を検査する一件を加える。

試験案: `test_campaign.py::test_tpcc_evaluate_v2_writes_abort_without_bench`、`::test_tpcc_evaluate_v3_reaches_bench`、`::test_tpcc_default_ycsb_flags_never_launch`、`::test_tpcc_stage1_run_trace_allowlist` (`:7586` の既存)、`test_calibrator.py` の YCSB argv bytes と TPC-C argv、`test_critic.py::test_tpcc_unsupported_workload_hint`。TPC-C の「bench まで」を現 pin の実測で期待しない。

### C — 転移実行器と試験

- `verify_candidate` (`t2851_transfer_runner.py:474-536`) の早期 return (`:507-510`) を `cell.workload=="tpcc" and (cell.stage!="s1" or 57:43 でない)` に限定する。s1 は `_binary` → `pipeline._run_trace` → `_trace_witness_ok` (`:539-544`) → `verify_trace_dir(..., ccbench_root=...)` (`:515-532`) を既存 YCSB と共有する。
- TPC-C のみ `cell.flags` の値を `str(v)` に変換して渡す。YCSB は現在の引数をそのまま渡し、argv を維持する。これは `_run_trace` の文字列条件 (`pipeline.py:458-466`) に必要。
- verifier 後、TPC-C で `vr.integrity.existence_violation_details is None` なら `verification_status(..., certified=False)` を使い indeterminate、reason は `trace-witness-unsupported-workload` とする。anomaly／`serializable is False` の判定を先に適用して disqualified を優先する (`runner.py:466-470`)。v3 `list` のときだけ通常の `vr.certified` を使う。TPC-C の verifier 出力は `core.result_to_dict_v3` (`verifier/core.py:194-204`) で詳細を残し、YCSB の既存 `result_to_dict` は維持する。
- `test_verify_tpcc_anchor_is_indeterminate` (`test_t2851_transfer_runner.py:332-359`) は「s1-H に経路なし」という期待をやめ、s2 または s1 非 57:43 の経路なし試験へ移す。s1-H には `_run_trace` flags、witness 失敗、実 verifier に通す合成 v3 正例、v2 indeterminate、v3 anomaly disqualified、再検証回数の試験を置く。合成 frame は `test_campaign.py:7620-7680` を再利用可能。

単位間の契約は `workload: Literal["ycsb","tpcc"]` 相当の値を **B → A** へ渡すこと、B の TPC-C correctness と C の cell flags がともに `_run_trace` の四 flag を文字列 exact match にすること。

## 生死確認 driver

repo 外の使い捨て driver は、計算ノードの単一 job で次の順に動かす。

1. `p3_s4_loop_pegasus.sh:617-673` と同じ pinned gflags/glog source から `$TMPDIR` に build/install し、`CMAKE_PREFIX_PATH` を設定する。v2 呼び出しでは `dependency_prefix=";<...>"` 形式の二 prefix を渡す (`:741-753`; buildcache の正規化は `buildcache.py:2626-2636`)。依存の source path と pin は job policy から取り、driver に仮定を埋め込まない。
2. 前 wave と同じ R0/R1 genome を読み、`buildcache.build` または必要な v2 context を揃えた `build_v2` で silo の perf/trace を各一つ buildする (`buildcache.py:3414`, `:3222`)。trace は `TRACE=1`、perf は `TRACE=0`。
3. binary path・sha256・source root を渡して `freeze_candidates` (`t2851_transfer_runner.py` の freeze API) を作る。錨 `s1-H-base` の `run_job` 1 本 (`:357`) と `verify_candidate(R1)` 1 本 (`:474`) を実行する。留保 cell は生成・実行対象から外す。
4. 独立した一時 campaign layout (`layout.py:191-253`) と、TPC-C を含む `search_config` の lock (`ident.py:196-229`, `wal.py:2905-2932`) を用意する。Pegasus の `AuthorizedContract` (`env_contract.py:846`) と `BuildRunContext` (`build_admission.py:537`) を通常入口と同じように取得して `pipeline.evaluate(..., workload="tpcc", correctness=錨 flags, screening=None)` (`pipeline.py:3054`) を 1 genome 実行する。現 pin なら WAL の v2 reject と **bench 未起動**を記録する。
5. `_probe("tpcc")` (`runner.py:342-354`) は driver のファイル名・argv に `tpcc_.*\.exe` を含めず、binary 不在時 True、起動中 False、終了後 True を確認する。`pgrep` の rc/stdout と driver PID の argv を保存する。

所要は依存準備約 5〜15 分、4 build と 1 job・verify・evaluate を合わせて **おおむね 30〜60 分の 1 node job**を仮見積りとする。build の実時間と trace サイズは未実測で、2 node 時間に達しそうなら投入前に見積りを更新する。

## リスクと未確定

- **TPC-C bench stdout:** `benchparse.py:24-99` の共通項目が実 binary で出るかを、計算ノードの 1 perf run で確かめる。出なければ parser の局所修正が要る。
- **`_probe` の自己一致:** `pgrep -af` は `runner.py:348-351` に固定されている。実機で driver argv を確認するまで合格とは言わない。
- **v2 identity 下流:** build admission、campaign lock、s8b の静的探索では buildcache preimage の固定 key 集合を見つけなかった。A の v2 fresh/hit、manifest、受領証試験で最終確認する。`calibrator/cli.py:416` の `ycsb_<protocol>.exe` 固定は calibration receipt 経路であり、今回の `evaluate` 直呼びには入れない。
- **meta-test:** spawn site の AST inventory (`test_ccbench_spawn_sites.py:2872, 4153`)、materializer registry (`test_s8b_floor_campaign.py:8014-8164`)、acceptance duration ledger (`test_acceptance_schedule_order.py:832-845`)、define sink の閉包試験 (`test_ccbench_spawn_sites.py:2917-2941`) を影響確認対象にする。既存 launch site 内の引数変更だけなら台帳の追加は不要と見込むが、author の最終差分に新規 launch site が出た場合は対応させる。