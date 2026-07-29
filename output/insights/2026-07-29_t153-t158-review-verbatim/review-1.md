1. [must-fix] Author A-1/A-7 の A7 が未解消である。`_is_target()` は argv 文法を見ず、option 値も target と誤認する (`tools/run_tests.py:227-230,678-683`)。  
   攻撃入力・状態: repo root で `python3 tools/run_tests.py --rootdir .`。絶対化された既存 directory 値を target と判定して `_DEFAULT_TARGET` を追加しない一方、suite identity は full のままになる。`--deselect=x.py::node` でも同様。  
   成果物影響: 実際には既定 target 無しの収集を「orchestrator full」と記録し、受入集合と task-run 記録が分裂する。

2. [must-fix] Author A-3/A-6 の acceptance 定義が単一 targeted test まで含み、既存の正当な緑を赤にする (`tools/run_tests.py:359-384,459-502`; `orchestrator/tests/test_run_tests_preflight.py:123-125`)。  
   攻撃入力・状態: marker 欠落・offline の worktree で、CCBench 非依存の `orchestrator/tests/test_check_codex_output.py::test_normal_output_is_accepted` だけを指定する。default target 配下なので acceptance 扱いとなり、不要な submodule init が失敗して rc=4 になる。  
   成果物影響: 局所検証可能だった targeted run を偽赤にし、修正可否と受入判定を停止する。

3. [must-fix] Author A-3/A-6 は実効 pytest argv を見ていない。`PYTEST_ADDOPTS` と compact short option が acceptance/no-execution 判定から脱落する (`tools/run_tests.py:355-384,459-466,527-539`)。  
   攻撃入力・状態: `PYTEST_ADDOPTS=--collect-only python3 tools/run_tests.py`、または `PYTEST_ADDOPTS='-k selected'`。実際は非実行形・targeted なのに削除 gate と auto-init が acceptance として発火する。`-qkselected` も `_SELECT_FLAGS` を回避する。  
   成果物影響: targeted と記録される実行へ acceptance gate の副作用・拒否を課し、suite identity と gate 判定を矛盾させる。

4. [must-fix] submodule marker は実体を保証しない。A 側の `.exists()` は directory/symlink、B 側の `.is_file()` は外部 file への symlink を受理する (`tools/run_tests.py:463-465,488-489`; `tools/check_wave_startup.py:116-121`)。  
   攻撃入力・状態: 未初期化状態で `external/ccbench/CMakeLists.txt -> /etc/passwd` を作り、run_tests または startup の resume mode を実行する。  
   成果物影響: submodule 不在でも gate が緑となり、依存テストの skip・偽赤を正式な受入結果へ混入させる。

5. [must-fix] Author B-1 の handoff 検査は symlink と path type で回避できる (`tools/check_wave_startup.py:124-136,148-156`)。  
   攻撃入力・状態: resume mode で `docs/handoff` を空の外部 directory への symlink にする、または `docs/handoff/README.md/active.md` のように directory 名を `README.md` にする。どちらも `--expect-external-handoff` を通る。  
   成果物影響: worktree-local handoff の残置・退避を見逃し、F50 再発を startup 合格として記録する。

6. [must-fix] bypass 値の exact `"1"` と exact `final` 拒否自体は正しいが、final より前の git fail-open で同じ gate を回避できる (`tools/run_tests.py:400-428,444-456`)。  
   攻撃入力・状態: marker 初期化済み・未stage削除ありで、`PATH=/nonexistent IZANAGI_TEST_TRIGGER=final /usr/bin/python3 tools/run_tests.py`。git 不在を警告して rc=0 で続行し、final 拒否分岐へ到達しない。偽 git が rc=0・空出力を返す場合は警告すらない。  
   成果物影響: 「final では bypass 不可」という受入証明を偽緑にする。通常 no-git は fail-open、final は未検査として非認証に分ける必要がある。

7. [must-fix] GIT_* 消毒は prefix としては完全だが、Git の trust environment として不完全かつ過剰である (`tools/run_tests.py:387-405,475-484`; `tools/check_wave_startup.py:29-45`; `tools/dev_waves/checker.py:303-312`)。  
   攻撃入力・状態: `PATH` の偽 git、`HOME`/system gitconfig の `core.worktree`・`core.fsmonitor`・URL rewrite を使う。さらに isolated checker が設定した `GIT_CONFIG_NOSYSTEM=1`、`GIT_TERMINAL_PROMPT=0` まで run_tests が除去する。  
   成果物影響: 別 worktree の状態を観測する偽緑、passive checker からの外部 command 実行、auto-init の取得先・network 挙動の変質を許す。

8. [must-fix] Author B-2 の regular-file/symlink 拒否と10MB上限は TOCTOU で破れる (`tools/check_codex_output.py:55-83`)。  
   攻撃入力・状態: `lstat()` 後、`read_bytes()` 前に対象を正常 file への symlinkへ rename 交換する。または lstat 後に file を10MB超へ伸長する。実読込後の file type と上限を再検査しない。  
   成果物影響: 別成果物を検査して破損 target を採用する偽緑、または上限なし読込による検収停止を起こす。

9. [must-fix] GIT_* 消毒テストが F27 型の「検査した形」になっている (`orchestrator/tests/test_check_wave_startup.py:138-155`; `orchestrator/tests/test_run_tests_preflight.py:151-169`)。  
   攻撃入力・状態: startup test は poison GIT_* を一つも注入しないため、ambient GIT_* が無い環境では `_git_env=os.environ.copy()` 変異が緑になる。run_tests 側も三名称だけ消す変異なら、未注入の `GIT_OBJECT_DIRECTORY` 等を残して緑になる。  
   成果物影響: repository redirect を許す実装へ退行しても「消毒テスト済み」と誤認し、startup・削除 gate の偽緑を受理する。

10. [must-fix] 10MB test が実装定数を fixture に差し込む F27 である (`orchestrator/tests/test_check_codex_output.py:82-86`)。  
    攻撃入力・状態: `_MAX_READ_BYTES` を20MBへ変異すると、test も20MB+1の fileを作るので緑のまま。15MB成果物は実運用で受理される。  
    成果物影響: 読込上限の契約退行を検出できず、過大成果物を正常として採用する。

11. [must-fix] V5 の kill test は `::node` 付き target しか検査せず、plain position target の絶対化除去を殺せない (`orchestrator/tests/test_run_tests_preflight.py:54-79,109-115,346-367`)。  
    攻撃入力・状態: 「`node_separator` がある時だけ絶対化する」変異を入れる。既存 test は全て緑だが、repo 外 cwd の `python /repo/tools/run_tests.py test_sample.py` は child cwd 変更後に別 path を指す。  
    成果物影響: V5 を KILLED と記録しながら、代表的な相対 targeted 利用を偽赤にする。

12. [nit] git 出力の encoding failure は仕様化された rc・集約へ変換されない (`tools/run_tests.py:400-407,475-487`; `tools/check_wave_startup.py:38-49`)。  
    攻撃入力・状態: `core.quotePath=false` と非UTF-8 filename、または非UTF-8 bytes を出す git wrapper。`text=True` の `UnicodeDecodeError` は `OSError` ではないため traceback になる。  
    成果物影響: 削除なら rc=3、submoduleなら rc=4、startupなら是正付き集約となるべき異常を、理由不明の rc=1 として誤記録する。

13. [must-fix] 親の「3235 passed」「auto-init 実地確認」は提示証拠より射程が広い (`/home/SFC/tanab/.claude/jobs/51e482b2/tmp/handoff-dev-wave-t153-t158.md:11,30-52`; `orchestrator/tests/test_run_tests_preflight.py:267-293`; `tools/run_tests.py:463-465`)。  
    攻撃入力・状態: handoff の init は実装前の手動 `submodule update --init` であり、auto-init test は subprocess を mock して marker を直接作る。初期化済み worktreeの通常全走は marker short-circuit のため auto-init 分岐を通らない。  
    成果物影響: 一 checkout の全走緑を、missing-marker・offline・no-git・sanitized-env の auto-init 成功証明へ一般化して wave GO を誤る。

事前登録変異については、exact な全除去としての V1〜V9/P1〜P4 は対応 test で赤になる。対応は V1/V2=`test_run_tests_preflight.py:320-343`、V3/V4=`test_run_tests_task_run.py:50-170` と `test_run_tests_nproc.py:162-183`、V5=`test_run_tests_preflight.py:346-367`、V6/V7/P4=`test_check_wave_startup.py:62-116`、V8/V9/P3=`test_check_codex_output.py:26-56`、P1/P2=`test_run_tests_preflight.py:205-256`。exact 変異間の F28 mask は見当たらない。ただし V5 の部分変異は所見11のとおり生存し、未登録の消毒・read-limit 変異も所見9・10で生存する。

## 総括

NO-GO — [must-fix] 12件 / [nit] 1件、計13件。