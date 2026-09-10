## 射程

- **[refuted / nit] 射程逸脱はない。** tracked production 差分は [screening_driver.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:170) の `_run_condition_gate_for_genome`、[同:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:243) の `_require_condition_gate_before_evaluation`、[同:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:506) の `evaluate_candidate` と、それらに必要な import だけである。裁定 6、プラン v2 の射程に一致する。

- **[refuted / nit] `s6_sort_sweep` と `s8a_trigger_sweep` の供給挙動は変わっていない。** 両 caller は manifest を渡していない [s6_sort_sweep.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/s6_sort_sweep.py:421)、[s8a_trigger_sweep.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/s8a_trigger_sweep.py:523)。新しい供給 guard は manifest 非 `None` の場合だけ発火する [screening_driver.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:189)。`None` 経路では一時 directory、prepare、FetchContent 引数のいずれも発生しない。

- **[refuted / nit] D1733 の禁止面への変更はない。** `backoff_repro`、`s1_direct_comparison`、pin、freeze は status と diff の対象外であり、D1733 の禁止 [verbatim-d1733.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/verbatim-d1733.md:3) およびプラン v2 [s4-adjudication.md:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/s4-adjudication.md:155) に適合する。

## 変異の再照準 (probe 用一覧)

以下の node 記号はすべて `orchestrator/tests/test_screening_driver.py::` を接頭辞とする。

- A = [test_screening_condition_gate_accepts_real_runtime_genome_value:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:182)
- R = [test_screening_condition_gate_rejects_real_ignored_runtime_define:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:206)
- E = [test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:227)
- L = [test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:288)
- N = [test_screening_condition_gate_fails_without_prepared_base_side_effect:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:332)
- U = [test_screening_condition_gate_without_manifest_preserves_unsupplied_path:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:352)
- Q = [test_screening_condition_gate_no_requests_does_not_prepare_with_manifest:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:389)
- S = [test_screening_condition_gate_prepare_is_nested_inside_stock_checkout:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:410)
- O = [test_screening_condition_gate_is_before_real_evaluate_build_sink:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:542)
- V = [test_evaluate_candidate_forwards_v2_contract_and_toolchain_binding:971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:971)
- C = [test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build:1016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:1016)
- F = [test_evaluate_candidate_prepare_failure_escapes_without_wal_abort:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:1091)

R の fixture 修正後を前提とした probe 一覧は次のとおり。各変異は記載した 1 原因へ帰属し、no-op ではない。

- **M1 [real / nit]** [screening_driver.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:594)。old anchor: `expected_toolchain_manifest=expected_toolchain_manifest,`。`evaluate_candidate` からの転送を削除する。期待赤: **O, C, F**。
- **M2 [real / nit]** [screening_driver.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:261)。old anchor: `source_root, genome, stock_root=stock_root, cxx=cxx, cmake=cmake,` に続く `expected_toolchain_manifest=expected_toolchain_manifest,`。stock 分岐だけ `None` にする。期待赤: **S**。
- **M3 [real / nit]** [screening_driver.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:189)。old anchor: `if expected_toolchain_manifest is not None:`。`is None` に反転する。期待赤: **A, R, E, L, U, S, C, F**。
- **M4 [real / nit]** [screening_driver.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:183)。old anchor は `requests = _condition_requests_for_genome(genome)`、`if not requests:`、`return None`。空判定を prepare の後へ移す。期待赤: **Q, V**。V の BuildCacheError も「request 無しなのに prepare した」という同じ原因である。
- **M5a [real / nit]** [screening_driver.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:195)。old anchor: `buildcache.prepare_masstree_fetchcontent(`。call を削除する。期待赤: **R, E, L, S, C, F**。
- **M5b [real / nit]** 同じ old anchor。call を同じ引数で 2 回実行する。期待赤: **R, E, L, S, C**。L は 2 回目の fixture header directory 作成で落ち得るが、原因は prepare 重複だけである。
- **M6a [real / nit]** [screening_driver.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:196)。old anchor: `ccbench_dir=source_root,`。`ccbench_dir=stock_root,` へ変更する。期待赤: **E, C**。
- **M7a [real / nit]** [screening_driver.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:199)。old anchor: `configure_timeout_s=900,`。`90` へ変更する。期待赤: **E**。
- **M7b [real / nit]** [screening_driver.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:200)。old anchor: `target_timeout_s=900,`。`90` へ変更する。期待赤: **E**。
- **M8 [real / nit]** [screening_driver.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:201)。old anchor: `site=None,`。`site="OTHER",` へ変更する。期待赤: **E**。current site の再観測を固定値へ変えるため、引数省略と異なり semantic no-op ではない。
- **M9 [real / nit]** [screening_driver.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:205)。old anchor: `f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base_dir}",`。値を `source_root` に差し替える。期待赤: **E, L, S, C**。
- **M10 [real / nit]** [screening_driver.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:207)。old anchor: `captured = condition_meaning_gate.capture_define_inputs(`。その直前で `stack.close()` し、関門前に base を消す。期待赤: **E, L, S**。
- **M11 [real / nit]** [screening_driver.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:195)。old anchor: `buildcache.prepare_masstree_fetchcontent(`。`MasstreeFetchContentError` を捕捉して現行 configure で続ける。期待赤: **F**。
- **M12 [real / nit]** [screening_driver.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:227)。old anchor: `if not admission.admitted:`。manifest 非 `None` では reject を無視する。期待赤: **R, N**。
- **M13 [real / must-fix]** [screening_driver.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:210)。old anchor: `configure_args=configure_args,`。`configure_args=_condition_gate_base_configure_args(genome),` として prepared base を capture へ渡さない。期待赤の完全集合は **E, L, S, C** であり、L だけではない。裁定 8 の「その正例だけを殺す」[s4-adjudication.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/s4-adjudication.md:116) は現テスト配置では成立しない。既存期待値を変えず、4 node の完全集合で登録するか、逐語どおりの単独 kill が必須なら再裁定が必要である。

- **[real / must-fix] M6b は probe から外すべきである。** lexical な非 canonical 表記が同じ root に解決される変異は、prepare 側が absolute existing directory だけを検査し [buildcache.py:2020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/buildcache.py:2020)、CMake source を `realpath` 化する [同:2045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/buildcache.py:2045) ため semantic no-op になる。別 directory へ向ければ M6a と同種の wrong-root 変異になり、M6b 固有ではない。

## 焦点走の対象集合

- **[real / should-fix] 親の暫定集合には actual production caller suite が 2 本不足する。** `s6_sort_sweep` と `s8a_trigger_sweep` は manifest 無しの実 caller [s6_sort_sweep.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/s6_sort_sweep.py:421)、[s8a_trigger_sweep.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/s8a_trigger_sweep.py:523) なので、`test_s6_sort_sweep.py` と `test_s8a_trigger_sweep.py` を追加する。これは新しい gate の要求ではなく、明示された非発火経路の既存 consumer 回帰である。

- **[real / nit] `test_backoff_extended_sweep.py` は strict な changed-function consumer ではなく、D1666 同型経路の保守的な余剰である。** 削る必要はない。

親が走らせる最終集合は暫定 10 本に次を加えた 12 本とする。

- `test_screening_driver.py`
- `test_condition_meaning_gate.py`
- `test_backoff_sweep.py`
- `test_backoff_extended_sweep.py`
- `test_official_perf_closure.py`
- `test_ccbench_spawn_sites.py`
- `test_campaign.py`
- `test_p2_2_site_aware.py`
- `test_t1416_backoff_compiler_binding.py`
- `test_screening_opt_in.py`
- `test_s6_sort_sweep.py`
- `test_s8a_trigger_sweep.py`

`backoff_repro`、`s1_direct_comparison` の suite は production diff も共有 caller もなく、D1733 禁止面なので追加不要である。

## 新規 fixture の登録

- **[refuted / nit] `prepared-base-required` を登録すべき exact fixture 在庫検査、登録簿、在庫 test は無い。** `find orchestrator/tests/fixtures/condition_meaning_gate -maxdepth 1 -mindepth 1` で現在の 4 directory を列挙し、`rg "condition_meaning_gate"` と `rg "(iterdir|glob|rglob|listdir|os.walk|scandir|inventory|manifest|registry)"` を `orchestrator/tests` と `tools` に対して照合した。

  見つかった参照は、個別名を直接束縛する定数 [test_condition_meaning_gate.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_condition_meaning_gate.py:26)、[test_screening_driver.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:44)、共有 `supplied` fixture だけを指す helper [condition_gate_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/condition_gate_test_support.py:10) である。macro registry test [test_condition_meaning_gate.py:971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_condition_meaning_gate.py:971) も directory 在庫を数えていない。登録変更は不要である。

## 親の診断の検証

- **[real / must-fix] 親の診断を裏取りする。** `effectuation-ignored/CMakeLists.txt` は [1-7 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/effectuation-ignored/CMakeLists.txt:1) に `FETCHCONTENT_BASE_DIR` の参照がない。一方、関門の process wrapper は return code だけでなく、成功時の stderr が 1 byte でもあれば `failure_reason` で落とす [condition_meaning_gate.py:1574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/condition_meaning_gate.py:1574)。CMake configure ではその reason が `configure-failed` である [同:1673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/condition_meaning_gate.py:1673)。

  D1666 後の `supplied` fixture は同じ問題を避ける参照を持つ [supplied/CMakeLists.txt:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/supplied/CMakeLists.txt:3)。親の観測した `configure-failed` [s6-parent-measurement.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/s6-parent-measurement.md:14) と完全に整合する。

  修正対象は既存期待値ではなく fixture であり、`effectuation-ignored/CMakeLists.txt` に同じ無害な参照を加えるべきである。base 無しの既存 consumer は [test_condition_meaning_gate.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_condition_meaning_gate.py:600) と [test_backoff_sweep.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_backoff_sweep.py:210) であり、CLI 変数を渡さないため無害な参照の追加で判定は変わらない。

## 恒真性

ここでいう「実装削除」は、API 引数だけを残して実体の供給 block [screening_driver.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:189) から [同:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:206) を削除する M5a 相当とする。

- **[real / nit] 実装を削除しても緑のままになる追加 test は 3 本ある。**
  - N: `test_screening_condition_gate_fails_without_prepared_base_side_effect`
  - U: `test_screening_condition_gate_without_manifest_preserves_unsupplied_path`
  - Q: `test_screening_condition_gate_no_requests_does_not_prepare_with_manifest`

  N は負例、U と Q は非発火不変条件なので、これ自体は欠陥ではない。ただし実装が存在する証拠には数えられない。

- **[refuted / nit] load-bearing 正例の恒真性は反証できる。** L は prepare 代役が一時 base にだけ header を生成し [test_screening_driver.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:293)、fixture の owner TU がその header を必須 include する [transaction.cc:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/prepared-base-required/cc/silo/transaction.cc:3)。M5a または M13 では赤になるため、L は機構の実効性を示す証拠として数えてよい。

- **[real / nit] 実装証拠として数えてよい test は E、L、S、C、F である。** それぞれ prepare の実在と exact 引数、base の実効供給、stock/base 寿命、canonical root 配線、例外境界を固定する。R は既存の赤判定維持を示す回帰証拠であり、供給機構の正例ではない。

## 総括

- **[real / must-fix] 現状は承認不可。** baseline の唯一の赤は親の診断どおり fixture の未使用 CMake 変数警告であり、`effectuation-ignored/CMakeLists.txt` 側の修正が必要である。
- **[real / must-fix] 変異登録は M6b を除外し、M13 の期待集合を E・L・S・C に直す必要がある。** M13 を「L だけ」とする裁定逐語を維持するなら再裁定が要る。
- **[refuted / nit] production 実装自体の射程逸脱、禁止経路への供給、pin・freeze 変更は見つからない。**
- **[real / should-fix] 焦点走には `test_s6_sort_sweep.py` と `test_s8a_trigger_sweep.py` を追加する。**

本レビューでは pytest を実行しておらず、静的検査と親の実測結果だけに基づく。