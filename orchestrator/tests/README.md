# orchestrator/tests — テスト方針

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

<!-- PYTEST_ONLY_ALLOWLIST_START -->
- test_auditor_gate.py
- test_backoff_consumers.py
- test_bench_first_real_wal.py
- test_codex_role_runtime.py
- test_layer3_report.py
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
- test_s8b_oracle_driver.py
- test_s8b_oracle_judge.py
- test_s8b_oracle_manifest.py
- test_s8b_oracle_report.py
- test_s8b_prediction_runner.py
- test_s8b_selector_freeze.py
- test_s8b_selector_input.py
- test_s8b_selector_output.py
- test_s8b_verdict.py
- test_screening_driver.py
- test_screening_opt_in.py
<!-- PYTEST_ONLY_ALLOWLIST_END -->

## 依存物不在時の skip (可視化)

gnuplot / 実 Silo サンプル / submodule / C++ toolchain (g++-13) が無い環境では、
該当テストは `skiputil.skip()` で **skip として数える**。print + return の疑似
スキップは PASS に数えられ、「fresh clone で load-bearing テストが空虚に緑」という
カバレッジ蒸発を隠すため使わない (audit 2026-06-30 §3)。skip は依存物の**具体的な
不在検知**に限定し (実ファイルの存在・`shutil.which("g++-13")`)、依存物が揃った
環境では従来どおり実検査が走る (検査は弱めない)。

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

テストの後半だけが依存物を要する場合 (前半で実検証が完了している場合) は
skip でなく return で打ち切る (その旨コメントを付ける)。

## fixtures

判定既知の手製極小トレースは `fixtures/README.md` 参照。
