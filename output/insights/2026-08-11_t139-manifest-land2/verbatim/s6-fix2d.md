## 総括

指定された 3 所見を修正しました。変更は次の 2 file のみで、docs／output／承認文書は未変更、commit／git add も実行していません。

- [erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2d/orchestrator/preregistration/erratum.py:172)
  - caller digest を exact `str` へ正規化。
  - digest を `bytes` 同士で比較し、`str` subclass の `__ne__` 迂回を封鎖。
  - parsed document ごとに `APPROVED_ERRATA` membership を検査し、registered draft を `UnapprovedErratumError` で拒否。
- [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2d/orchestrator/tests/test_t139_preregistration_binding.py:306)
  - `str` subclass digest 攻撃の負例を追加。
  - coherent draft registry の合成拒否を追加。
  - 承認 `old_sha256` を維持したまま `old_text` bytes だけ変える負例を、固定 Git blob seed で復活。

### 実走結果

`tools/run_tests.py` は両走とも `qstat -Q preflight rc=1` により `rc=16`。契約に従い素の pytest へ切り替えました。

焦点 nodeid、4 passed:

- `test_composed_digest_rejects_str_subclass_comparison_bypass`
- `test_compose_core_rejects_registered_draft_erratum`
- `test_s7_erratum_rejects_old_text_bytes_mismatch`
- `test_two_errata_locators_are_disjoint_and_compose_to_expected_digest`

範囲走:

- `orchestrator/tests/test_t139_preregistration_binding.py`
- `orchestrator/tests/test_plain_runner_coverage.py`
- 結果: `57 passed in 2.74s`

追加検査:

- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0
- `git diff --check`: rc=0

残るテスト赤は、実走範囲では 0 件です。

### 変異 gate

検査を消すと赤くなる nodeid:

- digest の exact-str／bytes 比較を旧比較へ戻す:
  `orchestrator/tests/test_t139_preregistration_binding.py::test_composed_digest_rejects_str_subclass_comparison_bypass`
- approval membership 検査を削除:
  `orchestrator/tests/test_t139_preregistration_binding.py::test_compose_core_rejects_registered_draft_erratum`
- `old_bytes != target_line` 検査を削除:
  `orchestrator/tests/test_t139_preregistration_binding.py::test_s7_erratum_rejects_old_text_bytes_mismatch`

### 波及可能性

- repo 内の `compose_core` caller は現状この test file のみ。将来の resolver／admission consumer は、registered draft 合成時に新しい `UnapprovedErratumError` を受けます。
- `orchestrator.preregistration.__init__` の export 集合は変更していません。
- `CORE_REF`、`ERRATUM_REF`、`S7_ERRATUM_REF`、合成 digest fixture は変更なし。
- 現行の承認済み S15＋S7 合成正例は引き続き通過します。
- `blobref.py`、`approval_payload.py`、共有 consumer test、承認文書 bytes は未変更です。