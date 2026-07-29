1. [must-fix] `brief「不変条件」` と P1／cwd 方針が自己矛盾している。未初期化 worktree を自動 init して実行可能にする P1 と、呼出元 cwd 由来の失敗を直す `tools/run_tests.py:377,379,441` は、いずれも受理集合を拡大し得るため「縮小方向のみ」ではない。  
   具体入力・状態: submodule 未初期化の fresh worktree、または repo 外 cwd からの相対 target。  
   成果物影響: 拡大変異を「禁止」と誤登録すると、正しい修復まで回帰扱いする一方、意図しない拡大との区別も失う。

2. [must-fix] P1 の自動 init の発火範囲が未裁定で、targeted／非実行形を過剰拒否する。`tools/run_tests.py:406-442` は現在 `--version`、`--help`、単一テストも同じ入口を通るが、xdist は導入失敗時に直列へ退避するのに対し、P1 は init 失敗時 fail-closed であり「同型」ではない。  
   具体入力・状態: `.git` のない source archive、read-only checkout、オフライン環境で `python3 tools/run_tests.py --version` または `/tmp/test_unit.py` を指定。  
   成果物影響: CCBench を消費しない正当な targeted 実行まで拒否され、runner の既存用途が不当に縮む。

3. [must-fix] P1 は「どの submodule 状態を異常とするか」が曖昧である。`.gitmodules:1-4` の top-level は初期化済みでも、現状態では `external/ccbench/.gitmodules:1-3` の nested `third_party/shirakami` が未初期化である。再帰 status を見ると無関係な nested を要求し、先頭 `-` だけを見ると `+`（gitlink と別 commit）や `U` を通す。  
   具体入力・状態: top-level CCBench は正しい pin、nested Shirakami だけ `-`、または CCBench status が `+<sha>`。  
   成果物影響: baseline を不要な network 依存で拒否するか、逆に誤った CCBench 実体を freeze 検査まで通して受入記録を汚す。

4. [must-fix] P2 に `_is_full_suite()` を流用すると実際の全走を回避できる。`tools/run_tests.py:226-264` は位置引数や非空 `PYTEST_ADDOPTS` を targeted とするため、`tools/dev_waves/cli.py:187-194` が実際に使う `run_tests.py orchestrator/tests` では gate が発火しない。逆に `-o python_files=test_run_tests_nproc.py` は一部収集なのに full と分類される。  
   具体入力・状態: `python3 tools/run_tests.py orchestrator/tests`、`PYTEST_ADDOPTS=-q python3 tools/run_tests.py`、または `-o python_files=test_run_tests_nproc.py`。  
   成果物影響: supervisor の受入全走で未 stage 削除を見逃す一方、一部収集を task-run 台帳へ full-suite と誤記録する。

5. [must-fix] `IZANAGI_ALLOW_UNSTAGED_DELETIONS=1` は `DW-O11` の義務を無監査で無効化する。`tools/run_tests.py:337-341` の task-run event には bypass 使用事実も理由も入らず、stderr 警告だけでは後から通常受入と区別できない。  
   具体入力・状態: tracked freeze 入力を削除したまま、同 env を付けて canonical 全走を実行。  
   成果物影響: O11 を守った受入と bypass 受入が同じ台帳形になり、worklog の受入記録を偽装可能にする。

6. [must-fix] P1〜P3 に Git 環境の消毒がない。単純な `git -C` や `cwd=repo` だけでは `GIT_DIR`／`GIT_WORK_TREE` が優先される。既存の `tools/dev_waves/git_state.py:116-157` はこれを除去し、`orchestrator/tests/test_dev_waves_git_state.py:68-81` で固定済みなので再実装すべきでない。  
   具体入力・状態: 実 worktree は削除・未初期化、環境に `GIT_DIR=/tmp/clean/.git GIT_WORK_TREE=/tmp/clean` を設定。  
   成果物影響: gate が別 repo の clean 状態を観測して対象 worktree を誤受理するか、別 repo を自動 init する。

7. [must-fix] `_is_target()` は argv 文法を理解しないため、相対 target 絶対化の基礎にできない。`tools/run_tests.py:158-162` は `::` を含む任意 token と実在する option 値を target 扱いする。  
   具体入力・状態: `-k 'foo::bar'`、`--deselect=test_x.py::node`、`--rootdir .`。後二者は option／値なのに target と誤認され、素朴な絶対化なら token 自体も破壊される。  
   成果物影響: default target が脱落または selector が書き換わり、記録された suite と実収集集合が一致しなくなる。

8. [must-fix] cwd 強制は相対 target だけ直しても pytest の引数透過を保存しない。`orchestrator/tests/README.md:18-25` は pytest 引数がそのまま渡ると約束するが、path-valued option と plugin 独自 option は child cwd に対して解釈される。  
   具体入力・状態: `/tmp/project` から `/repo/tools/run_tests.py tests/test_x.py --rootdir . --confcutdir . --basetemp tmp --junitxml report.xml`。target だけ絶対化すると rootdir、conftest 境界、tmp、report の場所は repo root 側へ移る。  
   成果物影響: 同じ argv で異なる conftest／test 集合を実行し、既存の正当な targeted 利用を誤拒否または誤記録する。

9. [must-fix] cwd 変換と suite identity の正本が未定義である。`tools/run_tests.py:267-301` は絶対 repo 内 path だけを相対化するため、実行用 cmd だけ絶対化すると、同一 `/tmp/project/tests/test_x.py` が相対指定と絶対指定で別 suite ID になる。全 `subprocess.call` 三経路への cwd 適用も必要である。  
   具体入力・状態: `IZANAGI_TASK_RUN_ID` 付きで、`tests/test_x.py` と `/tmp/project/tests/test_x.py` を同じ caller cwd から実行。sidecar 成功時は `:379`、失敗時は `:377`、opt-out は `:441` を通る。  
   成果物影響: 同じ収集集合が異なる task-run suite に分裂するか、一部経路だけ caller cwd のまま記録される。

10. [must-fix] brief の「既存被覆なし」「純増分のみ scope」は静的に反証できる。`test_run_tests_task_run.py:50-61` は subprocess kwargs が `{}` であることを明示 pin し、同 `:128-138` と `test_run_tests_nproc.py:161-175` の fake は cwd kwarg を受けない。brief の author A 所有にはこの二既存ファイルが含まれない。  
    具体入力・状態: 三つの `subprocess.call` に `cwd=_REPO` を追加する。  
    成果物影響: 必要な既存テスト追随が所有外となり、想定内の call-shape 変更を回帰または新規テストだけの検出力と誤集計する。

11. [must-fix] P3 の HEAD 判定は branch／Git operation state と実行時点を区別していない。SHA 等値だけなら detached HEAD や rebase の clean 窓を通し、branch を `main` に限定すると正しい wave branch を拒否する。`DW-O20` は branch 名不一致を記録付きで許す場合もある（`operations.md:109-117`）。  
    具体入力・状態: main と同じ SHA の detached HEAD、`rebase-merge` が残る clean 状態、または実装 commit 後に startup checker を再実行。  
    成果物影響: land 不能な wave を開始するか、正当に前進した wave を stale と誤判定する。

12. [must-fix] P3 の handoff 検査は開始順と衝突する。`.claude/commands/dev-wave.md:13-15` と `docs/handoff/README.md:15-17` はクラス 3 開始時に handoff を作るが、P3 は `docs/handoff/` の残置ゼロを要求する。O20 の外部 handoff は条件付き例外にすぎない。  
    具体入力・状態: 正規開始手順で自セッションの `docs/handoff/<wave>.md` を作成後、startup checker を実行。  
    成果物影響: 正規手順を自己拒否するか、通過のために唯一の中断復旧記録を削除させて handoff 消失を再発させる。

13. [must-fix] P3 は既存機械層との統合範囲がない。`tools/dev_waves/git_state.py:38-56,304-335` は stable snapshot・dirty submodule・環境消毒を実装済みで、`tools/dev_waves/daemon.py:819-850` も preflight を持つ。一方、`tools/dev_waves/cli.py:187-194` の固定 check 群は新 script を呼ばない。  
    具体入力・状態: 手動 `/dev-wave` と `tools/dev_waves.py client submit` の二入口をそれぞれ使用。  
    成果物影響: 一方だけ新 gate が効く、または重複実装が将来ドリフトし、「O20 を機械化済み」という記録が実際の全入口に成立しない。

14. [must-fix] P3 の「rc 集約」と submodule 自動 init は passive-before-active を破る。既存 verifier は `tools/dev_waves/checker.py:588-638` で passive failure 後に active checks を開始しない。  
    具体入力・状態: HEAD mismatch または dirty tree と、未初期化 submodule が同時に存在。  
    成果物影響: 既に開始不能と判明した worktreeを checker 自身が変更し、失敗時点の Git 状態と是正責任を曖昧にする。

15. [must-fix] P4 の「500 bytes + 総括見出し」は F43 型の本文喪失を検出しない。194-byte の破損原文へ空白を追加し、fenced code 内に `## 総括` を置けば条件を満たせる。また `[must-fix]` が本文にあるのに総括を `GO / 0件` とする不整合も検査しない。  
    具体入力・状態: `review-b1-broken-artifact.md` に 400 bytes の padding と ```` ```markdown\n## 総括\n``` ```` を追記。  
    成果物影響: 推敲断片を完成成果物として採用し、実在したレビュー所見を再び受入判定から失う。

16. [must-fix] P4 は正当な成果物も拒否する。current worker 契約 `docs/dev-wave/workers.md:10-16,45-49` は exact `## 総括` を要求せず、実在する `reviewA.md:1,72` は `## 判定`、`reviewB.md:1,35` は `# 判定: REJECT` を使う。所見ゼロの正当な総括は 500 bytes 未満にもできる。  
    具体入力・状態: `## 総括\n\nGO。must-fix 0件、nit 0件。` の短い完了出力、または上記既存 review 形式。  
    成果物影響: 完成済みレビューを破損扱いして不要な再投・重複所見・課金を生み、受理集合を prompt 非依存に誤縮小する。

17. [must-fix] P4 は呼出しと成果物の binding が scope 外で、standalone checker のままでは gate ではない。`docs/dev-wave/operations.md:6-10` は今も `.done` と exit code だけで完了判定し、exact `-o` path を新 checker へ渡す処理がない。さらに `--min-bytes 0` を許せば公開 bypass になる。  
    具体入力・状態: current `-o` が194-byte断片でも、checker には前 wave の正常ファイルを渡す、または `--min-bytes 0` を指定。  
    成果物影響: script 自体のテストだけ成立して実運用は無防備なままとなり、F43 prose を縮約すると唯一の差し戻し義務まで失う。

18. [must-fix] brief の実測一般化が強すぎる。42件は `worklog archive:29-31` と `docs/worklog.md:844-846` の二 fresh-worktree 条件に限られ、targeted／no-Git／nested 不在への一般化根拠ではない。「3165 passed」は tracked worklog に対応記録・HEAD・task-run ID・node digest がなく、F41 が要求する checkout／依存在庫の束縛も不足する。  
    具体入力・状態: main の並行前進、別 checkout、nested submodule 状態または plugin 環境が異なる全走。  
    成果物影響: node 数や拒否理由の変化を新 gate の回帰／改善へ誤帰属し、baseline 比較と wave GO 判定を誤る。

19. [must-fix] 変異の単一帰属が現 plan では成立しない。P1 を外した変異は pytest 本体の42件失敗に mask され、P3/P4 は consumer がないため script の operational wiring を削除する変異自体を作れない。cwd も三つの call branch を別々に殺す必要がある。  
    具体入力・状態: P1 detection 除去、P2 main wiring 除去、P3/P4 の呼出し除去、`:377`／`:379`／`:441` の cwd を一つずつ除去。  
    成果物影響: helper 直呼びテストだけで「変異 KILLED」と記録し、実入口では gate が一度も発火しない実装したふりを許す。

20. [nit] P4 の byte／file 契約も未定義である。`--min-bytes` は文字数でなく raw byte 数で測り、symlink・FIFO・巨大 file を拒否する必要がある。既存の安全な読み方は `tools/dev_waves/receipt.py:182-218` にある。  
    具体入力・状態: 200文字の日本語（UTF-8では約600 bytes）、FIFO、または別成果物への symlink。  
    成果物影響: 正しいサイズ境界を誤判定するか、検収 process が停止して成果物採否を記録できない。

21. [nit] fail-fast の順序が未指定である。現行 `tools/run_tests.py:409-420` は `_ensure_xdist()` を最初に呼ぶため、P2 が後段なら拒否が確定する前に pip install を試みる。  
    具体入力・状態: xdist 未導入かつ未 stage 削除がある canonical 全走。  
    成果物影響: 受入結果は変えなくても、失敗した検収がユーザー環境・networkへ不要な副作用を残し、「fail-fast」の運用記録を不正確にする。

## 総括

**NO-GO — must-fix 19件 / nit 2件、計21件。**