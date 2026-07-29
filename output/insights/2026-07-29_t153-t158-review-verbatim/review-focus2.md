## 対応表

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| New-1 | closed | 空白だけの `PYTEST_ADDOPTS` は `.strip()` 後に空となり acceptance を維持し、削除 gate が発火する。`tools/run_tests.py:366-371,450-501`、`orchestrator/tests/test_run_tests_preflight.py:191-197` |
| New-2 | regressed | `--smoke-only` 等の未知 option は default-deny になり、引数なし・`-n 8`・`-q`・`--dist loadgroup` も受入を維持した。一方、既知の非選択フラグを受理する分岐がなく、新たな full/acceptance 分裂を導入した。`tools/run_tests.py:61-66,366-421`、`orchestrator/tests/test_run_tests_preflight.py:136-182` |
| New-3 | scope 外 | isolated checkout と modules cache 欠落の問題は親裁定どおり対象外。`tools/dev_waves/git_state.py:531-560`、`tools/dev_waves/checker.py:623-645`、`tools/run_tests.py:571-577` |
| New-4 | closed | O01/O20 は checker を直接起動し、両 checker と runner は Git mode `100755`。`docs/dev-wave/operations.md:11,116-117`、`integration-v3.patch:1321,1483,1789-1790` |
| New-5 | closed | `--external-handoff` は外部 file 検査に加えて worktree handoff 残置検査を必ず含意する。O20 consumer も同 option を指定する。`tools/check_wave_startup.py:226-246`、`orchestrator/tests/test_check_wave_startup.py:181-196`、`docs/dev-wave/operations.md:116-117` |
| New-6 | closed | `symbolic-ref` の rc=1 だけを detached とし、decode 失敗由来の rc=127 は git 読み取り失敗になる。`tools/check_wave_startup.py:43-67,93-101`、`orchestrator/tests/test_check_wave_startup.py:293-310` |
| New-7 | closed | 成果物は strict UTF-8 decode され、`UnicodeDecodeError` は rc=1 の理由になる。`tools/check_codex_output.py:100-115`、`orchestrator/tests/test_check_codex_output.py:68-75` |
| R2-2（`--no-fetch` 残余） | closed | cache-only auto-init の実 argv に `--no-fetch` があり、call-shape test も完全一致で固定する。`tools/run_tests.py:579-598`、`orchestrator/tests/test_run_tests_preflight.py:388-425` |
| R1-4 / R2-7 fake-dir | scope 外 | 親裁定どおり対象外。marker と非 symlink `.git` の存在だけを見る実装は残る。`tools/run_tests.py:504-515`、`tools/check_wave_startup.py:136-159` |
| R2-9 | scope 外 | dev_waves が非0を `CHECK_FAILED/nonzero` に畳む残余は対象外。`tools/dev_waves/checker.py:326-343` |
| R2-12 残余 | scope 外 | `O_NOFOLLOW` 非対応環境と symlink fixture の可搬性は対象外。`tools/check_codex_output.py:67-76`、`orchestrator/tests/test_check_codex_output.py:78-102` |
| R1-13 実地再測 | scope 外 | 現在の証拠は mock call-shape まで。commit 後の実地再測は親が実施する。`orchestrator/tests/test_run_tests_preflight.py:388-425`、`review-focus.md:17` |

## 新規 regression

- [must-fix] `tools/run_tests.py:61-66,275-334,366-421,450-454,533-547,618-635`、`orchestrator/tests/test_run_tests_preflight.py:157-182` — 具体入力: tracked test を未stage削除した状態で `IZANAGI_TEST_TRIGGER=final IZANAGI_TASK_RUN_ID=20260729-e2-01234567 tools/run_tests.py --disable-warnings`。`--disable-warnings` は既知の非選択フラグで実際には既定 target 全体を走らせ、台帳も `full` とする一方、default-deny が targeted 扱いして削除 gate と submodule auto-init を飛ばす。成果物影響: 削除された test を収集しない green を未検査の `full` 受入証拠として記録でき、`docs/dev-wave/operations.md:60-63` の O11 とも食い違う。

## 総括

NO-GO — closed 6 / partial 0 / regressed 1 / 新規 1（must-fix 1、nit 0）/ scope 外 5。静的検査のみで pytest は未実走。