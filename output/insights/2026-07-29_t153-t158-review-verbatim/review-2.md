## 所見

1. [must-fix] dev_waves の隔離 checkout で fixed check が外部通信必須へ退行する。根拠: `tools/dev_waves/cli.py:187-194`、`tools/dev_waves/checker.py:315-343,606-636`、`tools/dev_waves/git_state.py:531-560`、`tools/run_tests.py:459-502`、`.gitmodules:1-4`。
   - 攻撃入力・状態: submodule を持たない isolated clone で既定 `tools/run_tests.py orchestrator/tests` を実行する。acceptance 判定後、HTTPS URL への `git submodule update` が timeout なしで走り、egress 禁止なら rc=4、blackhole なら外側 timeout 後も孫 git が残り得る。
   - 成果物影響: fixed check は従来の診断可能な pytest 赤より手前で `CHECK_FAILED` に潰れ、正当な wave の受理と supervisor の安定性を壊す。

2. [must-fix] auto-init が dev_waves の trust-root 外にある `.gitmodules` と gitlink を実行材料へ昇格させる。根拠: `tools/dev_waves/git_state.py:498-528`、`tools/dev_waves/checker.py:561-578`、`tools/run_tests.py:475-489`。
   - 攻撃入力・状態: wave commit が `tools/`・`orchestrator/tests/` を変えず、`.gitmodules` URL と `external/ccbench` gitlink だけを攻撃者管理 repository/commit へ変更する。trust-root 比較は通り、active check がその submodule を取得する。
   - 成果物影響: verifier が未監査の外部 source/CMake 材料で fixed suite を動かし、その結果を採用判定へ混入する。

3. [must-fix] `_is_acceptance_run()` は単一 node まで acceptance とし、既存の正当な targeted green を赤にする。根拠: `tools/run_tests.py:359-384,459-502`、`orchestrator/tests/test_run_tests_preflight.py:118-130`、`tools/run_tests.py:522-539`。
   - 攻撃入力・状態: submodule 未初期化・offline checkout で、submodule 非依存の `orchestrator/tests/test_run_tests_nproc.py::test_available_cpus_positive_and_affinity_bounded` だけを指定する。テストが明示的に acceptance と固定しているため init 失敗 rc=4 となる一方、台帳 identity は positional argv のため `targeted` になる。
   - 成果物影響: 局所検証が pytest 到達前に停止し、同じ run が gate 上は acceptance、台帳上は targeted という二義的記録になる。

4. [must-fix] preflight が `PYTEST_ADDOPTS` を見ず、no-execution/selector 契約を破る。根拠: `tools/run_tests.py:295-300,355-384,644-651`、`orchestrator/tests/test_run_tests_preflight.py:23-30`。
   - 攻撃入力・状態: `PYTEST_ADDOPTS=--collect-only python3 tools/run_tests.py` または `PYTEST_ADDOPTS='-k one'` を submodule 未初期化環境で実行する。pytest は no-execution/targeted だが、preflight は空 argv を acceptance として init・削除 gate を発火する。
   - 成果物影響: collection-only が不要な checkout 変更・egress・rc=4 に化け、収集成果物を作れない。

5. [must-fix] targeted suite ID の legacy 互換がなく、既存台帳の red→green 対応が切れる。根拠: `tools/run_tests.py:168-224,505-539,644-645`、`tools/task_runs/aggregate.py:149-203`、`orchestrator/tests/test_run_tests_preflight.py:109-115`。
   - 攻撃入力・状態: `/tmp/caller` から `test.py -k x` を記録付きで実行する。同じ意味の argv が旧実装では `pytest-targeted-648b6c47e787`、新実装では絶対化により `pytest-targeted-e86b066053f6` となる。新テストは正規化後同士しか比較しない。
   - 成果物影響: 旧 red と新 green が別 suite として残り、report の `open_red` が過大、`red_to_green_cycles` が過小になる。なお full-suite 定数 `pytest-orchestrator-full` 自体は不変。

6. [must-fix] `--expect-external-handoff` は外部 handoff の実在を一切検査しない。根拠: `tools/check_wave_startup.py:124-156,179-183`、`docs/dev-wave/operations.md:109-113`、`dev-wave-bg-worktree-startup-checks.md:21-23`。
   - 攻撃入力・状態: job tmp に handoff が存在せず、worktree の `docs/handoff/` も空または不在の状態で `--expect-external-handoff` を指定する。実装は「worktree 内に残置がない」だけで rc=0 を返す。
   - 成果物影響: handoff を作り忘れた sessionを正常開始と誤認し、中断・再開時の生存情報を失う。

7. [must-fix] submodule marker は「submodule 初期化」の証明になっていない。根拠: `tools/check_wave_startup.py:116-121`、`tools/run_tests.py:462-465`、`orchestrator/tests/test_check_wave_startup.py:36-64`、`orchestrator/tests/test_run_tests_preflight.py:232-239`。
   - 攻撃入力・状態: `.gitmodules` も gitlink もない通常 directory に `external/ccbench/CMakeLists.txt` だけを commitする。startup の正例 fixtureそのものがこの形であり、run_tests は同名 directoryでも `.exists()` により通す。
   - 成果物影響: startup は `OK`、run_tests は init 済みと誤認した後、real-repo suite が偽赤または別 source で実行される。

8. [must-fix] `check_codex_output.py` の既定値を DW-O01 全呼出しへ配線する契約が成立していない。根拠: `tools/check_codex_output.py:13-15,88-108`、`docs/dev-wave/workers.md:5-17,32-49`、`plan-v2.md:63-68,73-80`。
   - 攻撃入力・状態: DW-S02 に適合する400-byteの正しい plan、または1KBの正しい author 報告だが `## 総括` を要求されていない成果物を採用する。既定 checker は拒否し、計画中の O01 コマンド表記は必須 positional file も示していないため、逐語実行なら argparse rc=2になる。
   - 成果物影響: 正常な子成果物を破損扱いして再投を反復する。各 worker prompt の schema固定、対象 file の明記、親の意味検収維持が必要。

9. [must-fix] rc=3/4 は pytest の既存 exit-code namespace と衝突する。根拠: `tools/run_tests.py:456,502,644-687`、`tools/dev_waves/checker.py:326-343`、`output/task-runs/README.md:95-96`。
   - 攻撃入力・状態: 未 stage 削除と pytest internal error がともに rc=3、submodule 不在と pytest usage error がともに rc=4になる。dev_waves は stdout/stderr を捨て、いずれも同じ fixed-check nonzero に畳む。
   - 成果物影響: caller・台帳・supervisor が原因別の是正を選べず、D75型の同一識別子二義化が固定される。

10. [nit] 既存 task-run test は「call-shape追随」以上に意味を書き換えている。根拠: `orchestrator/tests/test_run_tests_task_run.py:50-63,99-128`、`plan-v2.md:44-47`。
   - 攻撃入力・状態: `test_opt_in_keeps_pytest_argv...` は相対 target を保持する旧主張から絶対化を期待する test へ変わり、preflight も monkeypatch で除外する。legacy suite ID互換の assertion はない。
   - 成果物影響: 回帰テスト名・裁定記録と実際の保証が食い違い、台帳互換破壊を緑で追認する。

11. [nit] qsub の scope 外表記は実在するが、固定テストがその契約を守っていない。根拠: `tools/check_wave_startup.py:160-165`、`orchestrator/tests/test_check_wave_startup.py:179-183`、`plan-v2.md:61-62,75-77`。
   - 攻撃入力・状態: help を「qsub も検査する」に変更しても、テストは `"qsub"` の存在しか見ないため緑のまま。予定の O20 文も「立ち上げ検査」とだけ書けば第3点まで済んだように読める。
   - 成果物影響: F49 の receipt/qstat/会計検査を実施済みと誤記し、無効 job の出力を採用し得る。

12. [nit] 新規 test は native Windows 非可搬である。根拠: `orchestrator/tests/test_check_codex_output.py:68-78`。
   - 攻撃入力・状態: Windows で `fifo` parameterを実行すると `os.mkfifo` が使えず失敗し、symlinkも権限依存になる。現行の本 repo 実行環境は Linux/Python 3.10/Git 2.34なので直近環境では発火しない。
   - 成果物影響: 将来のWindows開発層では実装回帰でなくfixture由来の赤を受入結果へ混ぜる。

13. [nit] docs予算は成立可能だが、「追記」では超過する。根拠: `tools/check_docs.py:153-162`、`docs/dev-wave/operations.md:61-62,116-117`、`plan-v2.md:73-79`。
   - 攻撃入力・状態: 現在23,845 bytes。O11を166→76 bytesへ縮約し、O01 109 bytesとO20 148 bytesを単純追加すると24,012 bytes。一方、O20既存165 bytesを置換すれば23,847 bytesで収まるが、現行の`--ff-only`是正義務を落とせない。
   - 成果物影響: 置換位置を誤ると `check_docs` 赤、予算優先で既存是正義務を削るとDW-O20契約が弱化する。

## 総括

**NO-GO — [must-fix] 9件、[nit] 4件、計13件。**

self-runnable footer、README allowlist不変、conftest不変、loadgroup/real-repo groupとの重複なしは静的に確認した。テスト実走は制約どおり行っていない。