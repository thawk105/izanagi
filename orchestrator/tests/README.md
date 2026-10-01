# orchestrator/tests — テスト方針

## 一時ディレクトリ (conftest.py)

campaign 系は書き込みごとに flush+fsync するため、一時 dir がジャーナリング FS
にあるとスイートが I/O バリア律速になりうる (実測は worklog 2026-07-17)。
かつて `conftest.py` はこれを避けるため TMPDIR を tmpfs (`/dev/shm`) へ向けていたが、
**tmpfs はメモリであり、メモリ枠を持つ計算機ではその枠を直接食う**。この誘導は撤去した。
**conftest は TMPDIR を設定しない。** 経緯と実測は worklog の該当エントリを参照。

置き場を選ぶときは**環境ごとに実測して決める** — 「局所ディスクなら速い」は成り立たない。
本 wave の実測 (300 回の write+fsync、payload 4 KiB、単一プロセス。
計算ノードは bnode021 で loadavg 0.29 = 単独、ログインノードは pegasus02 で loadavg 17 の共有下):

| 置き場 | Pegasus 計算ノード | Pegasus ログインノード |
|---|---|---|
| `/dev/shm` (tmpfs) | 0.001s | 0.002s |
| `/tmp` | **0.026s** (xfs — fstype は bnode041/043 で `stat -f` 実測) | **8.7〜9.4s** (局所 RAID) |
| `/scr` | 0.021s (xfs) | 存在しない |
| `/home` (Lustre) | 0.42〜0.49s | 0.435〜0.447s |

ログインノードでは `/tmp` が最も遅く `/home` が 20 倍速い。計算ノードでは `/tmp` も
`/scr` も十分速い。TMPDIR を明示するなら**その機械で測った値**に基づいて選ぶ。

tmpfs (`/dev/shm`、`/run/user/*`、tmpfs な `/tmp`) は選んではいけない。

- **TMPDIR を明示的に tmpfs へ向けた場合**は回帰ガードが
  `/proc/self/mountinfo` の fstype を見て**赤にする**
- **TMPDIR 未設定で環境既定が tmpfs の場合** (systemd 既定の `/tmp` 等) は
  ガードは赤にせず **skip し、理由にパスと fstype を出す**。その環境では
  ディスク上の TMPDIR を明示すること
- ガードの射程は実行時の `TMPDIR` と `tempfile.gettempdir()`、および conftest の source 上の
  結線 (`os.environ["TMPDIR"]` 系の代入と `tempfile.tempdir = <tmpfs>` 代入) である。
  **pytest の `--basetemp` は射程外** (`tools/run_tests.py` は絶対パス化して pytest へ渡すだけで、
  ガードはその値を見ない)
- 素の `python3 test_*.py` 実行は conftest を経由しない (元から TMPDIR に従う)
- fsync を呼ぶコード経路は変えていない (検査は弱めない)。実測でも
  `test_campaign.py` の fsync 回数は置き場によらず 620 回で一致する

### 並列実行 — 推奨の起動方法

```
python3 tools/run_tests.py            # スイート全体。xdist 無ければ --user へ自動導入し自動並列度で
python3 tools/run_tests.py <pytest引数>  # 対象・-n の上書きはそのまま渡る
IZANAGI_TEST_NPROC=max python3 tools/run_tests.py  # 上限を外し全 affinity コア
```

pytest-xdist は**必須依存にしない** — 自動導入に失敗する環境 (オフライン等) では
ランナーが直列にフォールバックし、`python3 -m pytest orchestrator/tests` 直叩きも
従来どおり使える。並列度は `min(使えるコア数, 上限32)` で環境に自動追従する
(手調整を無くすため。2026-07-19)。「使えるコア数」は cgroup / CPU affinity を尊重する
ので、**PBS ジョブ内では割り当て分だけ、素のマシンではコア数どおり**になり、共有ノードの
login shell でも上限 32 で頭打ちになる (全コアを掴まない行儀を自動で満たす)。上限の根拠は
実測 (worklog 2026-07-19: 約1946 テストで -n 8/16/32/96 = 18.7/14.6/10.5/13.0s。32 以降は
worker 起動コストが利得を食い 96 は 32 より遅い)。明示上書きは `-n <数>` (最優先) と
環境変数 `IZANAGI_TEST_NPROC`。

### 実 repo の T-080 receipt 解決は process 内で 1 回に畳む ([T-057])

`t080_freeze_migration.verify_receipt(root=<実 repo>)` は 1 回 **22.4 秒**かかる
(git subprocess 1845 本。`cat-file blob` 1607 本は異なる oid が 52 個しかない重複で、
コストは repo の commit 数に比例して伸びる)。oracle driver 系テストは `root=ROOT` を渡して
これを 50〜75 回払っており、全走時間の 9 割を占めていた。

`real_repo_receipt_memo.py` (テストではなく支援モジュール) が実解決値を process 内で共有する。
使うときの規律は同モジュールの docstring が正本。要点は 3 つ:

- **canned 値を作らない。** 初回 miss は必ず本番 `verify_receipt` へ委譲し、戻り object を
  そのまま返す (テストが観測する値は導入前と同一 = 受理集合を変えない)。
- **解決の回数・世代差 (epoch drift)・tamper 自体を検査する node では使わない。** 該当は
  `_run(..., memo_receipt=False)` で明示的に opt-out する。
- **patch 先はテストが import する module object** (`campaign.s8b_oracle_driver`)。
  `orchestrator.campaign.s8b_oracle_driver` は同一ファイルでも別 object で、そちらを patch すると
  memo が発火しない静かな空振りになる。`test_s8b_binding_driftguards.py` の positive control が
  この空振り・canned 値・guard 欠落を殺す。

## 受入全走の作法 — 範囲・並列度・checkout 依存 (F41)

受入全走は**範囲と並列度の両方を明示して**回す。`python3 tools/run_tests.py` が両方を
既定で満たす正しい形 (範囲 `orchestrator/tests`、並列度 = 環境自動追従)。素の pytest を
使うなら `python3 -m pytest -q -n 32 orchestrator/tests` のように両方を書く — repo の
`pytest.ini` は `addopts` を**持たない**ので、素の `python3 -m pytest -q` は今も**直列走**である。

範囲については、`pytest.ini` の `testpaths` が引数なし起動を `orchestrator/tests` へ閉じ、
`norecursedirs` が `output` / `external` / dot ディレクトリを収集から外すため、
**ignored な生成物が溜まった checkout でも他所のテストを拾わなくなった**
(failures F41: 対策前は cygnus main checkout で 1253 errors)。ただし `testpaths` が効くのは
**位置引数を 1 つも渡さないとき**だけなので、範囲を明示する作法自体は変えない。
`addopts` を ini へ書いてはならない — `run_tests.py` の受入判定は環境変数 `PYTEST_ADDOPTS`
しか見ず ini を構造的に読まないため、「全走のつもりで実は選択走」が preflight を通る
(`orchestrator/tests/test_pytest_collection_config.py` が機械的に固定している)。

- **wall も赤の有無も checkout に依存する。** git worktree には ignored なファイルが
  存在せず、main checkout には蓄積する。同じコマンドでも収集集合・skip 集合・実行時間が
  変わる (F41 の根本原因)
- **前の記録と比べるときは同じ checkout で測り直す。** 別 checkout の値との差は修正効果と
  交絡して帰属できない。記録には測った checkout を必ず併記する (dev-wave 側の義務は
  `docs/dev-wave/operations.md` DW-O18、実行環境の確定義務は同 `core.md` DW-S01)
- 依存物 (submodule・g++-13) の在庫も checkout と環境で変わる —
  skip で失われた検出力は rc と一緒に記録する (「依存物不在時の skip」参照)。新しい worktree
  では CCBench submodule の実体化が必要で、未実体化だと real-repo 系が skip でなく赤になる
  (2026-07-28 実測: 42 failed)。`--reference` clone は `objects/info/alternates` を freeze 検証が
  拒否する (proof chain の自己完結要件) — repack で自己完結化するか dissociate で clone する

## 二重 runner

中核の machine 非依存テストは pytest でも素の `python3 orchestrator/tests/test_*.py`
でも走る (pytest 非依存の `_run()` を各ファイル末尾に持ち、末尾 `if __name__ ==
"__main__": sys.exit(_run())` で駆動する)。pytest が無い環境でも検証を止めないための
意図的な設計。`_run()` は AssertionError (FAIL)・その他例外 (ERROR)・`skiputil.Skip`
(SKIP) を分けて数える。`tmp_path` 等の pytest fixture を要するテストには、`_run()` が
`inspect.signature` で検出して tempfile ベースの一時 dir を注入する。

**偽緑ガード:** `__main__` ブロックを持たないテストファイルは `python3 file.py` で
0 件実行・exit 0 の**偽緑**になる (test_s1_known_axes_freeze の独立レビュー所見 B、
audit 2026-06-30 §3 と同型)。これを避けるため、全 `test_*.py` は「自走 harness
(`_run()` か、テストを実際に走らせる `__main__`) を持つ」か「下記 pytest 専用
allowlist に載っている」かのいずれかでなければならない。この二分は
`test_plain_runner_coverage.py` のメタテストが機械強制する — 新規ファイルは harness を
足すか allowlist に明示追加するかを迫られ、無自覚な偽緑の再発を検出できる。

### pytest 専用ファイル (allowlist)

以下は pytest fixture / parametrize に依存する、または `__main__` を持たない意図的な
pytest 専用テストで、`python3 file.py` 直接実行は no-op (偽緑ではなく設計上の非対象)。
自走 harness を後から足したらこの一覧から外すこと (メタテストが陳腐化を検出する)。
本 wave の `test_reflux_*.py` 9 本は pytest fixture (`tmp_path` / `monkeypatch` / autouse) または parametrize に依存するため pytest 専用とする。

<!-- PYTEST_ONLY_ALLOWLIST_START -->
- test_auditor_gate.py
- test_backoff_consumers.py
- test_bench_first_real_wal.py
- test_branch_rescue_ledger.py
- test_check_trace0_header_rule.py
- test_check_worktree_occupancy.py
- test_codex_role_runtime.py
- test_dev_wave_wait.py
- test_env_contract.py
- test_layer3_report.py
- test_mocc_g2_discriminator.py
- test_mocc_trace_job_contract.py
- test_p3_b4_producer_auth_experiment.py
- test_p3_s4_loop_policy.py
- test_pegasus_calibration_workload.py
- test_profiler_directive.py
- test_reflux_formal_consumer.py
- test_reflux_origin_artifacts.py
- test_reflux_origin_binding.py
- test_reflux_origin_client.py
- test_reflux_origin_fixture_builder.py
- test_reflux_origin_topology.py
- test_reflux_originless_compatibility.py
- test_reflux_result_evidence.py
- test_reflux_source_closure.py
- test_ruleops.py
- test_s1_direct_comparison.py
- test_s1_measurement_freeze.py
- test_s1_report.py
- test_s1_verify_extime_calibration.py
- test_s6_proposal_rounds.py
- test_s6_sort_sweep.py
- test_s8a_trigger_sweep.py
- test_s8b_budget.py
- test_s8b_budget_approval_preflight.py
- test_s8b_descriptor.py
- test_s8b_floor_stats.py
- test_s8b_gate_core_exact_launch_validated.py
- test_s8b_holdout_freeze.py
- test_s8b_materialization.py
- test_s8b_oracle_driver.py
- test_s8b_oracle_judge.py
- test_s8b_oracle_manifest.py
- test_s8b_oracle_n_pilot.py
- test_s8b_oracle_report.py
- test_s8b_prediction_runner.py
- test_s8b_ratified_freeze.py
- test_s8b_ratified_verify.py
- test_s8b_selector_freeze.py
- test_s8b_selector_input.py
- test_s8b_selector_output.py
- test_s8b_verdict.py
- test_s8c_acceptance_receipt.py
- test_s8c_preregistration_invariant.py
- test_s8c_preregistration_predicates.py
- test_scoped_acceptance.py
- test_scoped_acceptance_land.py
- test_screening_driver.py
- test_screening_opt_in.py
- test_t419_probe_causality.py
- test_verifier_gate_witness.py
- test_vhash_forwarding_prototype.py
- test_vhash_cicada_hot_block.py
- test_vhash_ro_gc_publish.py
- test_wave_land_window.py
<!-- PYTEST_ONLY_ALLOWLIST_END -->

- self-run: `test_vhash_ceiling_vs_sota.py` — ceiling driver の変異 M1〜M18、rc 3 の受理、壊し正例、30 秒判定、build shard と予算 gate の入力対照
- self-run: `test_plot_vhash_ceiling_vs_sota.py` — 実寸 matplotlib Figure、予備と 30 秒比較の小標本 CI
- self-run: `test_vhash_c2_motivation.py` — C2 driver の変異 M1〜M9、macro・flag・腕順・成立判定・選択・集計・parse

- self-run: `test_s8c_acceptance_receipt_v2.py` — receipt v2 の正例・負の対照
- self-run: `test_s8c_gate_report.py` — 8c 事前登録関門の状態・根拠を構造化報告

## 依存物不在時の skip (可視化)

gnuplot / submodule / C++ toolchain 候補が無い環境では、
該当テストは `skiputil.skip()` で **skip として数える**。print + return の疑似
スキップは PASS に数えられ、「fresh clone で load-bearing テストが空虚に緑」という
カバレッジ蒸発を隠すため使わない (audit 2026-06-30 §3)。skip は依存物の**具体的な
不在検知**に限定し (実ファイルの存在・全 C++ compiler 候補の不在)、依存物が揃った
環境では従来どおり実検査が走る (検査は弱めない)。

**この分類は外部依存物の不在だけを数える。** 前提が repo 内に揃っているのに走らない skip は
別分類であり、下の「条件付き未実走」へ数える。census を作るときに混ぜてはならない。

**実 Silo トレースはこの分類から外れた。** 規律2 の実データ地面は、追跡下の
`orchestrator/tests/fixtures/` にある実 emitter 由来の **3 fixture** —
`g5_silo_real_prefix` (4 thread の stock)、`g6_silo_serial_1thread` (1 thread の stock)、
`r8_silo_broken_norw` (read-set 再検証を抜いた build) — が担う。
`test_verifier` の `test_real_silo_serializable` /
`test_silo_serial_1thread_fixture_contract` / `test_broken_silo_norw_fixture_contract` /
`test_broken_silo_norw_structured_report_is_exact` / `test_new_real_fixture_bytes_are_exact` は
**どの checkout でも必ず実走する** (skip も任意入力分岐も持たない)。
この無条件実走は `test_skip_classification.py` の AST 契約が g5 / g6 / r8 の 3 node について
機械で固定している。追跡外の大規模サンプル `output/runs/silo-sample` は、
置いた機体でだけ同じ node の中で追加検証される任意入力であり、不在でも skip しない
(必須検査は既に完了しているため)。fixture の由来・再生成手順・判定既知の根拠と、
**独立に決まる述語と verifier 由来の golden の区別**は `fixtures/README.md` が正本。

- **submodule**: `git submodule update --init external/ccbench` 後に
  source_digest / EVOLVE-BLOCK / S-1 freeze 生成系テストが有効化される。submodule 実ファイル
  (`cmake/Options.cmake` / `include/backoff.hh` / `cc/silo/CMakeLists.txt`) を直接読む
  テストは当該ファイルの不在を検知して skip する — source_digest 系は
  `_require_ccbench_file()`、`build_document()`/`generate()` を叩く
  `test_s1_known_axes_freeze` は `_require_submodule_sources()`、`.git` 由来の HEAD が
  要るものは `_ccbench_head_or_skip()`。
- **C++ toolchain 候補 (`g++-13`, `g++-12`, `g++` の順)**: source_digest / diff-of-diffs
  系の受入テストは、各 node で `_any_cxx()` が最初に実在する 1 本を選び、同じ compiler を
  current/HEAD・positive/negative・cache consumer へ明示して実走する。全候補不在時だけ依存物
  skip にする。digest の値や関係を compiler 版横断で保証する機構ではなく、同一の選択済み
  compiler 内で現行 source の等値・非等値・受理・拒否関係を検査する契約である。
  **pinned toolchain は compiler の不在を解消しない** (2026-08-23 実測)。
  `orchestrator/qualification/submission.py` の `prepare_toolchain()` は
  `shutil.which("g++-13")` で PATH 上の実体を解決して realpath と sha256 を記録するだけで、
  compiler を導入する経路を持たない。T-1461 の staged FetchContent も masstree / mimalloc /
  googletest の**ソース**転送であって compiler は対象外である。qualification の exact
  gcc-13/g++-13 toolchain manifest と series identity は今回変更していない。本番 campaign の
  `buildcache.compilers_for_current_site()` が Pegasus compute で素の `g++` を返す契約とも別で、
  `_any_cxx()` が production と同じ要求名を選ぶ保証は主張しない。受入テストを available compiler
  fallback へ寄せる択 (a) は 2026-08-23 にユーザー裁定済み ([T-1526])。
- **gnuplot**: `test_reports.test_make_plot_generates_valid_png` のみ。
- **pinned Codex runtime** (pinned codex + 同梱 bwrap + trusted busybox):
  `test_codex_role_runtime` の runtime 系。codex の auto-update でピンがずれると
  不在扱いになるため、既定は理由付き skip。codex_roles を変更する作業と D56 再開
  儀式では `IZANAGI_REQUIRE_CODEX_RUNTIME=1` で在庫番人を hard-fail に戻す (D60)。

テストの後半だけが依存物を要する場合 (前半で実検証が完了している場合) は
skip でなく return で打ち切る (その旨コメントを付ける)。

## real-repo 排他と loadgroup

`REAL_REPO_ACCESS_BY_NODE` の resource node は shard では `real-repo` group に閉じるが、
実行時は process memo 4 node だけが `@real-repo` を保持し、それ以外は suffix を外して
node ごとの work unit にする。親 repo と CCBench は別の reader/writer lock を取り、各 lock は
移行中の worktree-root key を先に取得してから Git common-dir を解決し、新 key を同じ mode で
取得する。process 内は key ごとに 1 fd と参照 count を共有し、SH 中の同一 thread の EX は同じ
fd を昇格、終了時に SH へ降格する。これにより sibling worktree と旧 session のどちらとも
同一 host/filesystem 上で排他しつつ、長寿命 fixture の入れ子による自己競合を避ける。
writer の飢餓 (F976) は各 key と同名の `.gate` flock で抑える。writer は fresh の EX 取得と
SH→EX の昇格 (gate を開いてから自分の SH を解放する) で gate を EX 保持したまま main を待ち、main
取得直後に gate を閉じる。process が実 repo lock を 1 つも持たない fresh reader は、main を取る前に
必要な全 key の gate を SH で試して即解放し、writer が gate を保持する間は何も持たずに待つ (この
検査のためだけに common-dir を main 取得前にも解決する。本体の key は従来どおり legacy 取得後に
解決する)。既に lock を持つ process (入れ子・2 つ目の資源) の reader と EX→SH の降格は gate を
見ない (main を握ったまま gate で待つ hold-and-wait を作らないため)。gate は NB polling で待機順を
持たないので、保証するのは「writer が gate を保持する間、その gate の事前検査を行う fresh reader を
待たせる」ことであり、検査済み reader の main 取得は妨げず、待機開始からの厳密な優先でもない。
deadline 245 秒は gate と main で共有する。

長寿命 fixture は node protocol へ登録しない。`s8c-preregistration-candidate`、
`s8c-predicate-snapshot`、`campaign-repository-scan` を別 loadgroup のまま保持し、fixture 自身が
setup と `yield` の全寿命を対応 lock で覆う。異なる group の resource 衝突は
`tools/acceptance_shards.py` の独立した衝突辺で同じ shard component へ union するため、
別 host の shard 間で `/tmp` flock に依存せず、同一 shard 内では別 worker の並列性を保つ。
controller prewarm 2 系統も実 resolver 呼出しだけを parent SH 内で行う。
suite 全体を subprocess collect する 3 node は inner collection が node protocol を通らないため、
外側 node 自身を parent SH reader として登録する。

## 条件付き未実走 (repo 内で満たせるが開けていない)

**依存物不在とは別分類。** 前提が repo 内に揃っているのに、受入 suite ではその窓を開けない
ために走らない skip をここへ数える。`skiputil.skip()` ではなく
`skiputil.skip_conditional_unrun()` を使い、理由文の先頭へ分類語を出す。分類の結線は
`test_skip_classification.py` が機械で固定する。

現在この分類に属するのは template patch (`patches/silo-backoff-fixed.patch`) 未適用の
次の 4 node だけである。

- `orchestrator/tests/test_campaign.py::test_source_digest_parse_options_defaults`
- `orchestrator/tests/test_campaign.py::test_source_digest_fixed_variant_distinct`
- `orchestrator/tests/test_campaign.py::test_source_digest_failsclosed_on_missing_define`
- `orchestrator/tests/test_hooks.py::test_real_submodule_payload_edit`

**外部依存物の不在ではない。** patch は repo 内にあり、現行 pin に対して `git apply --check` が
rc=0 で当たる。適用は `orchestrator/campaign/patchharness.py` の `applied()`
(pinned-clean assert + tree lock + apply + finally revert + clean assert) が行い、campaign
本番経路が実際に使っている機構である。4 node は `conftest.py` の
`REAL_REPO_ACCESS_BY_NODE` へ reader として登録され、`real-repo` marker で shard 閉包を保ち、
実行時は親 working tree / 共有 ccbench 別の protocol-level RW lock で writer と排他する。

**それでも受入 suite では窓を開けない (ユーザー裁定、[T-790])。** 開けても実効回収は
4 node 中 2 node に留まる。回収 2 node と引き換えに、受入全走という共有の関門へ実 submodule の
作業ツリーを変異させる箇所が増える。隔離 checkout でこの境界を測る経路は別タスクとして
起票してある。

**2026-08-23 の修正前実測。** 隔離 worktree で template patch を campaign 本番経路
`patchharness.applied()` により実適用し、4 node を実走した。`parse_options_defaults` と
`test_real_submodule_payload_edit` は PASSED、`failsclosed_on_missing_define` は
`_require_g13()` で skip、`fixed_variant_distinct` はガードを持たないまま
`source_digest.src_token` を呼んで未捕捉 RuntimeError = 赤になった。上の「実効回収 2 node」は
この形で再現する。**このガード欠落は同日に修理済み**で、当時は赤でなく exact g++-13 の
依存物不在 skip に落ちる形になった。2026-08-24 の [T-1526] 実装後は、窓が閉じている間は同じ
conditional skipを維持し、窓が開けば available compiler で実走する。順序と selected-cxx 結線は
`test_skip_classification.py::test_conditional_preprocess_nodes_classify_before_compiler_selection` と
`test_selected_cxx_is_bound_to_every_target_consumer` が固定する。

**費用の数値は次のとおり。** 現在この suite は実 submodule の**作業ツリー**を変異させる node を
持たない — `patchharness.applied()` の呼出しはすべて `_fake_ccbench_repo()` の tmpdir 偽 repo が
対象である (`patchharness.checkout()` は実 submodule に対しても使うが、使い捨て worktree を
作るだけで共有作業ツリーは変異させない)。窓を何個開けるかは実装形 (4 node を 1 window で包むか
node ごとに開くか) で変わるので、確定値をここへ書かない。時間費用は小さい — 単発直列配置での
window 開閉込みの差分は約 0.5 秒、隔離 checkout 側は `git worktree add --detach` の
0.07 秒/サイクルである。ただしどちらも xdist 受入全走の予測ではない。
`REAL_REPO_ACCESS_BY_NODE` へ登録済みであることは「追加ペナルティ 0」を意味しない。

**律速は pinned compiler の在庫ではない (2026-08-23 実測)。** pinned でない g++-12 を渡すと、
`fixed_variant_distinct` が主張する 5 つの関係 (`-1` は stock へ正規化 / 値違いは別 id =
alias 防止 / variant_id が分かれる) も、`failsclosed_on_missing_define` の供給漏れ停止も
そのまま成立した。これは D34 (digest の**値**は環境依存で pin しない) と整合する — これらの
テストは関係しか主張していない。したがって「在庫が入るまで開けない」は制約の言い換えとしては
正しくない。ただし版非依存は保証ではなく現行 source での実測一致であり、合成枝が
`#if __GNUC__` のような builtin 条件を使えば関係まで版依存になりうる。
この版非依存 caveat は維持したまま、受入テストは available compiler fallbackへ寄せる択 (a) で
裁定・実装済みである。qualification の exact compiler契約や compiler portability一般化は別scope。

**塞がないままの成果物影響。** source digest の alias 防止・未定義 macro の fail-closed・
hook 編集面の実 template 結線は、標準の受入全走では**恒久的に未検査**である。誤った variant
identity や certified 選択を許しうる面なので、census を読むときに「外部依存だから仕方ない」と
数えてはならない。

## fixtures

判定既知の手製極小トレースと、実 emitter 由来の実データ fixture は `fixtures/README.md` 参照。
