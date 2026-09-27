## 変更 file と要点 (file:line)

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/campaign/p3_s4_loop_policy.py:122): 環境と用途ごとの campaign identity、計測契約、stock・pair・replay の経路、候補評価例外時の履歴行を実装した。
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_p3_s4_loop_policy.py:421): identity、stock、WAL、replay、pair、例外、環境不一致の検査を追加した。既存テストの期待値は変更していない。

## interface の実装 (interface.md §1 との対応)

指定された CLI action、用途別 campaign、site と環境の照合、fetchcontent 受領証の 5 値、stock JSON、pair の同一 authorization session、replay の共有 gate を配線した。`dependency_prefix` は [main の取得箇所](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/campaign/p3_s4_loop_policy.py:602)で `CMAKE_PREFIX_PATH` から取得する。

## test の実走 (コマンド・nodeid の範囲・passed / failed 件数、または未実走)

**実装済み・未実走。** `python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_policy.py -q` は `qstat -Q` の事前確認で rc=16 となり、pytest 子プロセスは起動しなかった。したがって passed / failed 件数はない。両ファイルの `py_compile` と `git diff --check` は成功したが、テストの緑判定には数えない。

## 変異 M-F1〜M-F6 の fixture と単一理由性の見立て

M-F1 は stock flag の完全一致と実 `source_digest` 判定、M-F2・M-F3 は別 attempt を混ぜた WAL の 12% 期待値、M-F4・M-F5 は replay の履歴非生成と実 auditor gate、M-F6 は 4 種の campaign id の比較を対応させた。**単一理由性は未実走のため未確定**。実 source 判定テストは `g++-13` または CCBench submodule が使えない環境では skip する。

## 所有外への波及と、変えなかった既存の受理・拒否挙動

静的に確認した consumer は job body、`test_p3_exploration_namespace.py` の driver 契約、`test_campaign.py` の caller inventory、`test_ccbench_spawn_sites.py`、coder entrypoint と build sink の検査である。`run_campaign` の静的呼出し数は従来どおり 1 箇所。これら所有外テストは未実走で、計測前の site 照合が既存 driver 契約テストに波及する可能性が残る。

既定 `linux-baremetal` の identity 形、preview の coder-only 入力、record-reject の不合格限定、emit の baseline 必須、run-iteration の build opt-in、既存 no-build の受理・拒否条件は変更していない。

## 総括

単位 A の所有 2 ファイルに実装とテストを追加した。計算ノードへの dispatch が失敗したため、実走による合否確認と変異の確定は親側で必要。commit と docs 編集は行っていない。