## 対応表

| 所見 ID | 判定 | 根拠 file:line |
|---|---|---|
| R1-1 | closed | option 値を除外する `_positional_tokens()` と `has_target` 配線に変更済み。`tools/run_tests.py:337-353,758-763`、`orchestrator/tests/test_run_tests_preflight.py:576-600` |
| R1-2 | closed | 個別 file/node は acceptance から除外され、既定 target との完全一致だけを許す。`tools/run_tests.py:398-406`、`orchestrator/tests/test_run_tests_preflight.py:146-166` |
| R1-3 | regressed | selector/no-execution の具体例は閉じたが、`PYTEST_ADDOPTS=' '` を非 acceptance、suite identity を full とする新しい分裂を導入。`tools/run_tests.py:296-301,376-406,602-619`、`orchestrator/tests/test_run_tests_preflight.py:169-172`、`orchestrator/tests/test_run_tests_task_run.py:82-84` |
| R1-4 | partial | symlink marker は拒否するが、通常 directory に regular `CMakeLists.txt` と任意の非 symlink `.git` を置くだけで通る。`tools/run_tests.py:489-498`、`tools/check_wave_startup.py:134-150`、`orchestrator/tests/test_check_wave_startup.py:36-55` |
| R1-5 | closed | handoff directory symlink と regular file でない `README.md` を拒否する。`tools/check_wave_startup.py:160-191`、`orchestrator/tests/test_check_wave_startup.py:157-178` |
| R1-6 | closed | final では git 実行不能・非0・decode失敗を rc=13 にする。PATH/HOME 偽装部分は親裁定の脅威モデル外。`tools/run_tests.py:418-451`、`orchestrator/tests/test_run_tests_preflight.py:276-295` |
| R1-7 | closed | 採用範囲の `GIT_CONFIG_NOSYSTEM` 保持と `GIT_TERMINAL_PROMPT=0` は実装済み。PATH/HOME 部分は親裁定 refuted。`tools/run_tests.py:100-102,409-415`、`tools/check_wave_startup.py:22,32-40`、`fix-a-prompt.txt:37-39` |
| R1-8 | closed | `O_NOFOLLOW`、同一 fd の `fstat`・bounded read により指摘された path 交換と growth を閉じた。`tools/check_codex_output.py:67-106`、`orchestrator/tests/test_check_codex_output.py:101-149` |
| R1-9 | closed | 4種類の GIT poison を実際に注入して除去を確認する。`orchestrator/tests/test_run_tests_preflight.py:186-213`、`orchestrator/tests/test_check_wave_startup.py:223-250` |
| R1-10 | closed | テスト側を literal 10 MiB + 1 に固定済み。`orchestrator/tests/test_check_codex_output.py:93-98` |
| R1-11 | closed | node 無し plain relative target の実入口テストを追加済み。`orchestrator/tests/test_run_tests_preflight.py:551-573` |
| R1-12 | partial | traceback は防いだが、fresh の `symbolic-ref` decode失敗を「detached HEAD」と誤診する。decodeテストは resume のみ。`tools/check_wave_startup.py:43-67,93-99`、`orchestrator/tests/test_check_wave_startup.py:268-280` |
| R1-13 | partial | mock 分岐は増えたが、現 handoff の全走・実地 auto-init 主張は fix 前実装の測定のまま。現コードの実地成功証拠ではない。`orchestrator/tests/test_run_tests_preflight.py:363-414`、`/home/SFC/tanab/.claude/jobs/51e482b2/tmp/handoff-dev-wave-t153-t158.md:54-56` |
| R2-1 | regressed | network 発火は抑えたが、isolated clone には modules cache が無いため既定 fixed check が確実に rc=14 になる。`tools/dev_waves/cli.py:187-193`、`tools/dev_waves/checker.py:623-645`、`tools/run_tests.py:556-562` |
| R2-2 | partial | cache 存在だけを見て、gitlink SHA・URL・cache内容を検証せず、`--no-fetch` なしの update を実行する。`tools/run_tests.py:556-579`、`tools/dev_waves/git_state.py:498-528`、`.gitmodules:1-4` |
| R2-3 | closed | 個別 file/node は targeted になった。`tools/run_tests.py:398-406`、`orchestrator/tests/test_run_tests_preflight.py:146-166` |
| R2-4 | regressed | selector/no-execution は閉じたが、空白だけの `PYTEST_ADDOPTS` で acceptance と full identity が分裂する。`tools/run_tests.py:296-301,376-406`、`orchestrator/tests/test_run_tests_task_run.py:82-84` |
| R2-5 | closed | 親裁定 refuted。既存 open red が0件で legacy re-key の実害なしと裁定済み。`/home/SFC/tanab/.claude/jobs/51e482b2/tmp/handoff-dev-wave-t153-t158.md:64-65` |
| R2-6 | partial | external file 検査 primitive は追加したが、O20 consumer は `--forbid-worktree-handoff` しか渡さず、外部 handoff 欠落を検査しない。`tools/check_wave_startup.py:224-245,267-287`、`docs/dev-wave/operations.md:112-117` |
| R2-7 | partial | `.gitmodules`・gitlink を持たない通常 directoryでも、偽 `.git` fileを足せば合格する fixture 自体が残る。`tools/check_wave_startup.py:134-150`、`orchestrator/tests/test_check_wave_startup.py:36-55` |
| R2-8 | partial | worker別 schema/default 部分は親裁定 refuted/scope外。対象 file と heading はO01に入ったが、100644の checkerを `python3`なしで記載しており逐語実行不能。`docs/dev-wave/operations.md:8-11`、`integration-v2.patch:1201-1207`、`plan-v2.md:73-76` |
| R2-9 | partial | pytest rc 0–5との数値衝突は解消したが、dev_waves は rc13/14を含む全非0を同じ `CHECK_FAILED/nonzero` に畳み、stderrも捨てる。`tools/run_tests.py:98-99,486,515`、`tools/dev_waves/checker.py:326-343` |
| R2-10 | closed | 親裁定 refuted。argv絶対化への期待変更は採用済み設計として扱う。`orchestrator/tests/test_run_tests_task_run.py:50-63,99-128` |
| R2-11 | closed | 親裁定 scope外。qsub非検査は help に明示されている。`tools/check_wave_startup.py:248-253`、`orchestrator/tests/test_check_wave_startup.py:283-287` |
| R2-12 | partial | FIFOだけをskipした。Windowsで権限依存の symlink fixture は無条件実行され、実装自体も `O_NOFOLLOW` 不在なら正常 file を全拒否する。`orchestrator/tests/test_check_codex_output.py:68-90`、`tools/check_codex_output.py:67-76` |
| R2-13 | closed | 親裁定 scope外。docs予算と置換方法は親の完了検査対象。`docs/dev-wave/operations.md:60-63,110-117` |

## 新規所見

- [must-fix] `tools/run_tests.py:296-301,376-406,435-439,602-619` — `PYTEST_ADDOPTS=' '`、未stage削除ありで既定実行すると、pytestと台帳は full なのに deletion gate は非 acceptance として不発。成果物影響: final全走を未検査のまま full green と記録できる。

- [must-fix] `tools/run_tests.py:366-406,602-619` — collectionを狭める valueless plugin option `--smoke-only` が導入済みの状態で同optionを渡すと、unknown long optionは acceptance、suite identityは targeted。成果物影響: targeted greenへ acceptance用副作用・証明を誤適用する。

- [must-fix] `tools/dev_waves/git_state.py:531-560`、`tools/dev_waves/checker.py:623-645`、`tools/run_tests.py:556-562` — completed waveのisolated cloneには `.git/modules/external/ccbench` が複製されない。成果物影響: orchestrator fixed checkがpytest前に必ずrc=14となり、正常waveを受理できない。

- [must-fix] `docs/dev-wave/operations.md:11,116-117`、`integration-v2.patch:1201-1207,1359-1365` — 100644の新規checkerを文書が `python3` なしで直接呼ぶ。成果物影響: 手順を逐語実行すると permission deniedとなり、成果物検収とstartup gateが発火しない。

- [must-fix] `tools/check_wave_startup.py:224-245,267-287` — valid external handoffと `docs/handoff/active.md` が同時にある状態で `--external-handoff PATH` だけを指定するとrc=0。逆にO20はforbidだけで外部欠落を通す。成果物影響: 相反する二つのhandoff、またはhandoff無しを正常開始として採用する。

- [nit] `tools/check_wave_startup.py:43-67,93-99` — fresh modeの`symbolic-ref`だけが非UTF-8を返すと、UTF-8失敗ではなくdetached HEADと報告する。成果物影響: rcは赤のままだが是正操作を誤誘導する。

- [must-fix] `tools/check_codex_output.py:100-110` — regular fileを `b"\xff"*500 + "\n## 総括\n"` とすると、`errors="replace"` によりrc=0。成果物影響: 壊れた非UTF-8成果物が機械検収を通過する。

## 総括

NO-GO — closed 14 / partial 9 / regressed 3 / 新規所見 7（must-fix 6、nit 1）。静的検査のみで、pytestは未実走。