## 変更した file と関数

- [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:170)
  - `_run_condition_gate_for_genome`
  - `_require_condition_gate_before_evaluation`
  - `evaluate_candidate`
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:182)
- 新規 fixture:
  - [CMakeLists.txt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/prepared-base-required/CMakeLists.txt:1)
  - [transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/prepared-base-required/cc/silo/transaction.cc:1)
  - `cmake/Options.cmake`
  - `include/backoff.hh`

docs、commit、push、branch 操作は行っていない。

## 供給の配線

`evaluate_candidate` から manifest を `_require_condition_gate_before_evaluation` へ渡し、stock・非 stock の両分岐から `_run_condition_gate_for_genome` へ転送した。

request 空判定と build-route 検査の後、manifest が非 `None` の場合だけ一時 base を canonical 化して、次の exact keyword で prepare する。

- `ccbench_dir=source_root`
- `fetchcontent_base_dir=<canonical base>`
- 同一の `expected_toolchain_manifest`
- `configure_timeout_s=900`
- `target_timeout_s=900`
- `site=None`

`dependency_prefix` と 3 種の source directory は渡していない。configure 引数末尾へ同じ base の `-DFETCHCONTENT_BASE_DIR=...` を 1 本だけ追加する。

一時 base は supply 腕、meaning 腕、family admission の完了後に閉じる。stock 経路では stock checkout の内側で生成・破棄される。prepare 例外は捕捉しない。

docstring には、manifest 非 `None` が供給権限ではなく現行 call graph 上の backoff screening 経路の代理であることと、`site=None` により関門ごとに `current_site()` を再観測することを明記した。

## load-bearing 正例の作り方

新規 fixture の owner TU が `<izanagi_prepared_dependency.hh>` を includeする。この header は fixture 内には存在せず、一時 FetchContent base 内にだけ生成される。

正例の prepare 代役は次の実体を副作用で作る。

`<base>/izanagi-screening-dependency-src/include/izanagi_prepared_dependency.hh`

実 supply evaluator と CMake configure/preprocess は stub 化せず、requested/control の両 configure argvと dependency closure が同じ header を参照することを検査する。

同じ fixture に対して prepare 代役を no-op にする負例も追加した。期待結果は `preprocess-failed` を含む family reject である。

fixture directory の個数や名前を固定する exact 在庫検査は静的検索で見つからなかったため、登録変更はしていない。

## 変更前後の受理・拒否挙動

変更前:

- screening 関門は準備済み base を受け取らず、dependency population が必要な呼び出しは判定前の preprocess で赤になり得た。
- request なし、manifest なし、build-route 不整合、stock 比較、meaning 腕、family admission の既存挙動が存在した。

変更後:

- manifest 非 `None` の経路では、準備済み base 未供給だけを理由に前段で赤だった呼び出しが、既存の判定へ進める。これは制御された受理集合の拡張である。
- manifest `None` は一時 base、prepare、FetchContent 引数を発生させない。
- request なしと build-route 不整合は prepare より前に終了する。
- 判定式、既定値、stock 比較、meaning 腕、admission 条件は変更していない。
- 実効性を無視する既存 fixture は、base 供給後も `preprocess-bytes-identical` で拒否される。
- 共有 base の影響範囲は masstree、mimalloc、googletest の FetchContent population 全体である。

## 実走した検査 (nodeid と rc)

pytest nodeid の実走は 0 件。両コマンドとも `tools/run_tests.py` を使用したが、Pegasus dispatch の `qstat -Q` preflight が失敗し、`rc=16`、`child_started=false` だった。緑は申告しない。

実走できた静的検査:

- `git diff --check`: `rc=0`
- 変更した Python 2 ファイルの AST parse: `rc=0`

## 未実走のもの

`rc=16` で child が起動しなかった焦点 nodeid:

- `test_screening_condition_gate_accepts_real_runtime_genome_value`
- `test_screening_condition_gate_rejects_real_ignored_runtime_define`
- `test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments`
- `test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm`
- `test_screening_condition_gate_fails_without_prepared_base_side_effect`
- `test_screening_condition_gate_without_manifest_preserves_unsupplied_path`
- `test_screening_condition_gate_no_requests_does_not_prepare_with_manifest`
- `test_screening_condition_gate_prepare_is_nested_inside_stock_checkout`
- `test_screening_condition_gate_is_before_real_evaluate_build_sink`
- `test_evaluate_candidate_forwards_v2_contract_and_toolchain_binding`
- `test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build`
- `test_evaluate_candidate_prepare_failure_escapes_without_wal_abort`

D1666 回帰・制約 meta-test も `rc=16` で未実走:

- backoff prepare/gate 回帰 2 nodeid
- official perf closure 2 nodeid
- process/build-sink closure 2 nodeid
- certified-writer caller inventory 1 nodeid

変更後に強化した route-mismatch nodeid、`test_screening_driver.py` 全体、repo-wide test、実 CCBench screening は未実走。

## 波及可能性の静的列挙

- production caller は 4 箇所。
  - `backoff_sweep.py` の baseline・候補 2 箇所は manifest を渡すため供給が発火する。
  - `s6_sort_sweep.py` と `s8a_trigger_sweep.py` は manifest を渡さず、非発火のまま。
- `backoff_repro.py` と `s1_direct_comparison.py` には供給を追加していない。
- 既存の共有 fixture `supplied`、`effectuation-ignored`、`f707-missing-supply` は複数の condition gate、backoff、s1 系 test から参照されるが、内容は変更していない。
- 新規 `prepared-base-required` fixture の consumer は今回追加した正例・負例だけ。
- 静的 closure の波及候補は `test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、`test_campaign.py`。
- `buildcache.py`、`condition_meaning_gate.py`、pin、freeze は無変更。

## 総括

段 4 裁定どおり、driver 段と同型の準備済み FetchContent base 供給を screening 関門へ配線した。load-bearing な合成 fixture と正負例、exact argv、寿命、stock 入れ子、root 一致、manifest 転送、例外境界の検査も実装済み。

ただし Pegasus dispatch infrastructure failure のため、状態は「実装済み・未実走」であり、closed とは申告しない。