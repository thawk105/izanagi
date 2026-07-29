## 所見

1. [must-fix] `cwd=_REPO` の追加だけでは相対 target を吸収できない。根拠: `tools/run_tests.py:158-161,433-441`。既知の `CheckSpec` は `tools/dev_waves/checker.py:315-330` が既に checkout を cwd にするため維持でき、`checker.py:69-72` / `git_state.py:519-523` の文字列集合も変更不要である。
   攻撃入力・状態: repo 外で `python /repo/tools/run_tests.py orchestrator/tests` を実行すると、現 cwd 基準の `_is_target()` は偽になり、絶対 default target と、cwd 変更後に有効になる相対 target の両方が pytest argv に入る。
   成果物影響: 重複収集または target 解決失敗で受入 rc と worklog の判定が汚れる。

2. [must-fix] P2 の「full-suite」と既存 `_is_full_suite()` の意味が一致しない。根拠: brief P2、`tools/run_tests.py:226-264,284-301`、`tools/dev_waves/cli.py:187-194`。
   攻撃入力・状態: tracked file を未 stage 削除した状態で `python3 tools/run_tests.py orchestrator/tests` を実行すると、位置引数があるため現 helper は targeted と判定する。逆に helper を変更すると、`orchestrator/tests/test_run_tests_task_run.py:69-77` が固定する task-run identity を変える。
   成果物影響: 意味上の全走なのに削除 preflight が発火しないか、既存台帳の suite identity が無断で変わる。専用の acceptance-full-suite 述語が必要。

3. [must-fix] P1 の xdist 類推は成立しない。根拠: brief P1、`tools/run_tests.py:144-155,409-420`、`orchestrator/tests/README.md:24-26,149-155`。
   攻撃入力・状態: fresh・offline checkout で submodule 非依存の単一テストを指定すると、xdist は導入失敗時に直列へ縮退する一方、P1 は不要な submodule init 失敗だけで pytest 前に非ゼロ終了する。
   成果物影響: 従来実行可能だった targeted 検査まで拒否され、差分の局所検証と受入判断を不必要に停止する。

4. [must-fix] dev-waves の隔離 checkout と P1 はネットワーク依存で衝突する。根拠: `tools/dev_waves/cli.py:192`、`tools/dev_waves/checker.py:303-330,606-636`、`tools/dev_waves/git_state.py:531-560`、`.gitmodules:1-4`。
   攻撃入力・状態: active check 用 clone は submodule を初期化せず、URL は HTTPS のまま。egress 不可環境では `run_tests.py` の自動 init が失敗し、egress 可でも固定検査が外部通信と checkout 変異へ依存する。
   成果物影響: 正当な wave commit が fixed-check failure として拒否される。安全に閉じるには isolated checkout 側の local-only materialization まで consumer scope に含める必要がある。

5. [must-fix] 「submodule 初期化」の対象深度が未定義である。根拠: brief P1/P3、`.gitmodules:1-4`、`external/ccbench/.gitmodules:1-3`、`orchestrator/tests/README.md:149-155`。
   攻撃入力・状態: top-level `external/ccbench` は実体化済みでも、nested `third_party/shirakami` は未初期化になり得る。`git submodule status --recursive` の全 `-` を拒否すれば現行の正当な状態も失敗し、再帰 init なら無関係な外部取得を増やす。
   成果物影響: startup gate が恒常的に偽失敗するか、受入に不要な依存物まで可用性条件になる。

6. [must-fix] P3 の `HEAD=local main` exact equality は再開 wave を拒否する。根拠: brief P3、`docs/dev-wave/operations.md:109-117`、`docs/dev-wave/core.md:101-107`。
   攻撃入力・状態: wave branch に正常な commit があり tree は clean、または並行セッションで main が進んだ状態で再開する。HEAD と main は異なるのが正常で、`--ff-only main` でも wave が main より先なら equality には戻らない。
   成果物影響: 正当な再開・競合解消・最終 main 取り込みが startup gate に阻まれる。fresh-start exact mode と resume/clean-tree modeを分離すべき。

7. [must-fix] P3 は auto-memory の3点を過不足なく機械化していない。根拠: brief P3、`dev-wave-bg-worktree-startup-checks.md:11-27,33-34`、`docs/dev-wave/operations.md:111-117`。
   攻撃入力・状態: 空の `docs/handoff/` を検査した直後に親が同ディレクトリへ handoff を作れば通過後にF50を再現できる。また第3点の qsub 後 receipt・qstat・会計痕跡検査は完全に欠落し、代わりに作業途中では不適切な clean-tree 検査を追加している。
   成果物影響: F49/F50 型を「機械化済み」と誤認し、handoff 消失または無効 job の結果を受入材料へ混ぜる。

8. [must-fix] 新ツール2本には呼び手がなく、現 scope のままでは死文である。根拠: brief scope・成果物分割、`docs/dev-wave/operations.md:6-10,109-117`、`.claude/commands/dev-wave.md:84-102`、`.claude/settings.json:8-47`。
   攻撃入力・状態: author B がスクリプトと単体テストだけを追加し、親が既存 prose を縮約する。hooks・settings・qsub/job script・dev-waves `CheckSpec` のいずれも両ツールを起動しないため、通常の `/dev-wave` は従来どおり `.done` と exit codeだけを見る。
   成果物影響: 194-byte 破損成果物や startup 漏れを新 gate が一度も観測せず、実装したふりになる。`DW-O01` に成果物採用前の output 検査、`DW-O20` と条件20に brief 前の startup 検査を明記すべき。

9. [must-fix] P4 の単一 regex 契約は既存 worker 出力と非互換かつ回避可能である。根拠: brief P4、`docs/dev-wave/workers.md:5-17,32-43,45-49`、`docs/failures.md:790-804`。
   攻撃入力・状態: 正常な author 報告が500 bytes超でも `## 総括` を持たなければ拒否される。一方、501 bytesの推敲断片に fenced example の `## 総括` を含める、または下限未検証の `--min-bytes 0` を渡せば形だけ通せる。
   成果物影響: 正当な実装報告を偽失敗にするか、レビュー所見が失われた断片を成果物として採用する。適用する段・prompt schema・anchored heading・下限を固定する必要がある。

10. [must-fix] 所有分割は現状では素集合でない。根拠: brief「成果物・分割」、`orchestrator/tests/test_run_tests_task_run.py:50-61`、`orchestrator/tests/test_run_tests_nproc.py:161-175`、`orchestrator/tests/test_plain_runner_coverage.py:60-86`、`orchestrator/tests/conftest.py:47-104`。
    攻撃入力・状態: `subprocess.call(..., cwd=...)` は既存の exact call-shape と一引数 fake を壊すが、両既存テストは author A の所有外。さらに3新規 test が pytest-onlyなら両 author が同じ `orchestrator/tests/README.md` allowlist を編集する。実 repo を使えば `conftest.py` と独立 golden も共有編集になる。
    成果物影響: 並行 patch が衝突するか、既存契約を更新できず統合不能になる。F42 nodeid は `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`、直列化関連は `orchestrator/tests/test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised` と `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`。

11. [must-fix] O11/O18/O20/F43 prose は今回の機械層で完全代替されない。根拠: `docs/dev-wave/operations.md:59-62,94-99,109-117`、`tools/check_docs.py:7-10`、`docs/skill-self-improvement.md:48-50,83-84`。
    攻撃入力・状態: P2 は削除を検出しても stage しない、cwd 強制は direct pytest や他 nested subprocess を覆わない、P3 は外部 handoff の置き場を保証しない、P4 は内容検収・再投を保証しない。この状態で「機械化済み」として各義務を削る。
    成果物影響: lint が構造上受理しても安全義務が弱化し、受入 rc・レビュー所見・worklog が再び偽の根拠になる。事故説明だけを縮め、規範動作は残すべき。

12. [must-fix] `IZANAGI_ALLOW_UNSTAGED_DELETIONS` は literal 衝突こそないが、D75 上の意味境界と監査性が不足する。根拠: brief P2、`docs/dev-wave/operations.md:69-72`、`tools/run_tests.py:315-341,346-365`、`orchestrator/tests/conftest.py:116-129`。
    攻撃入力・状態: 長寿命 shell で一度 export すると、その後の全 full-suite が無言で同じ bypass 状態を継承し得る。task-run record に bypass 使用 field はなく、警告以外は通常実行と識別不能である。
    成果物影響: deletion gate を適用したという受入記録を後から証明できない。`IZANAGI_TEST_*` 名前空間、値の exact `1`、final での禁止または記録を裁定すべき。

13. [nit] 文書配線の機械予算は極端に狭い。根拠: `tools/check_docs.py:148-162,234-287,1462-1483`。
    攻撃入力・状態: 現在 `docs/dev-wave/**` は23,845/24,000 bytes、`docs/skill-self-improvement.md` は5,997/6,000 bytes。wave-start dispatchへO20を追加すると exact dispatch contract のコード変更も必要になり、長文を command 一行へ足すと140 chars制限にも近づく。
    成果物影響: 安全配線そのものが予算・dispatch検査に阻まれる。新節を作らず既存 `DW-O01` / `DW-O20` 本文へ統合し、総量純減を実測すべき。

## 総括

**NO-GO — [must-fix] 12件、[nit] 1件、計13件。**