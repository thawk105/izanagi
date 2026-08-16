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
- 依存物 (submodule・g++-13・実 Silo サンプル) の在庫も checkout と環境で変わる —
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
- test_check_worktree_occupancy.py
- test_codex_role_runtime.py
- test_dev_wave_wait.py
- test_env_contract.py
- test_layer3_report.py
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
- test_s8b_descriptor.py
- test_s8b_floor_campaign.py
- test_s8b_floor_stats.py
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
- test_s8c_preregistration_core.py
- test_s8c_preregistration_invariant.py
- test_s8c_preregistration_predicates.py
- test_screening_driver.py
- test_screening_opt_in.py
- test_t419_probe_causality.py
- test_wave_land_window.py
<!-- PYTEST_ONLY_ALLOWLIST_END -->

## 依存物不在時の skip (可視化)

gnuplot / 実 Silo サンプル / submodule / C++ toolchain (g++-13) が無い環境では、
該当テストは `skiputil.skip()` で **skip として数える**。print + return の疑似
スキップは PASS に数えられ、「fresh clone で load-bearing テストが空虚に緑」という
カバレッジ蒸発を隠すため使わない (audit 2026-06-30 §3)。skip は依存物の**具体的な
不在検知**に限定し (実ファイルの存在・`shutil.which("g++-13")`)、依存物が揃った
環境では従来どおり実検査が走る (検査は弱めない)。

**この分類は外部依存物の不在だけを数える。** 前提が repo 内に揃っているのに走らない skip は
別分類であり、下の「条件付き未実走」へ数える。census を作るときに混ぜてはならない。

- **実 Silo サンプル** (`output/runs/silo-sample`, 184k txn / 66MB):
  `test_verifier.test_real_silo_serializable` (規律2 の緑の地面) が使う。
  `.gitignore` の `output/runs/` 包括無視で git 追跡外のため fresh clone には無い。
  再生成: trace-enabled build (`build-trace`, `-DCCBENCH_TRACE=1`) で `ycsb_silo` を
  回し trace を `output/runs/silo-sample/` に置く (patches/README.md の trace 手順、
  worklog 2026-06-18 参照)。
- **submodule**: `git submodule update --init external/ccbench` 後に
  source_digest / EVOLVE-BLOCK / S-1 freeze 生成系テストが有効化される。submodule 実ファイル
  (`cmake/Options.cmake` / `include/backoff.hh` / `cc/silo/CMakeLists.txt`) を直接読む
  テストは当該ファイルの不在を検知して skip する — source_digest 系は
  `_require_ccbench_file()`、`build_document()`/`generate()` を叩く
  `test_s1_known_axes_freeze` は `_require_submodule_sources()`、`.git` 由来の HEAD が
  要るものは `_ccbench_head_or_skip()`。
- **C++ toolchain (g++-13)**: source_digest の preprocess は `g++-13` を直接叩く
  (D23)。preprocess を駆動する source_digest / diff-of-diffs 系テストは、
  `g++-13` が PATH に無い環境では `_require_g13()` で skip する
  (`_fake_ccbench_repo()` で submodule 非依存に走るものも、preprocess 段で g++-13 が要る)。
- **gnuplot**: `test_reports.test_make_plot_generates_valid_png` のみ。
- **pinned Codex runtime** (pinned codex + 同梱 bwrap + trusted busybox):
  `test_codex_role_runtime` の runtime 系。codex の auto-update でピンがずれると
  不在扱いになるため、既定は理由付き skip。codex_roles を変更する作業と D56 再開
  儀式では `IZANAGI_REQUIRE_CODEX_RUNTIME=1` で在庫番人を hard-fail に戻す (D60)。

テストの後半だけが依存物を要する場合 (前半で実検証が完了している場合) は
skip でなく return で打ち切る (その旨コメントを付ける)。

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
本番経路が実際に使っている機構である。4 node は `conftest.py` の `REAL_REPO_SERIAL_NODES` へ
登録済みで xdist の `real-repo` group で直列化されるため、並列との衝突も無い。

**それでも受入 suite では窓を開けない (ユーザー裁定)。** 開けても実効回収は 4 node 中 2 node に
留まる — `test_source_digest_fixed_variant_distinct` は `_require_g13()` 相当のガードを持たない
まま `source_digest.src_token` を呼ぶため、pinned compiler が無い環境では skip でなく未捕捉
RuntimeError = 赤になる。回収 2 node と引き換えに、受入全走という共有の関門へ実 submodule を
変異させる箇所が 4 増える。費用対効果が pinned compiler の在庫に依存するので、在庫が入るまでは
開けない。隔離 checkout でこの境界を測る経路は別タスクとして起票してある。

**塞がないままの成果物影響。** source digest の alias 防止・未定義 macro の fail-closed・
hook 編集面の実 template 結線は、標準の受入全走では**恒久的に未検査**である。誤った variant
identity や certified 選択を許しうる面なので、census を読むときに「外部依存だから仕方ない」と
数えてはならない。

## fixtures

判定既知の手製極小トレースは `fixtures/README.md` 参照。
