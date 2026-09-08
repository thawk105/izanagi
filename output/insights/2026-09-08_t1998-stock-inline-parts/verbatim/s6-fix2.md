## 所見ごとの対応表

| 所見 | 状態 | 主な修正箇所 |
|---|---|---|
| F1 | closed | [t1998_stock_inline_pair.py:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:361)、[test:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:518) |
| F2 | closed | [t1998_stock_inline_pair.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:389)、[test:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:576) |
| F3 | closed | [t1998_stock_inline_pair.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:419)、[test:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:657) |
| F4 | closed | [t1998_stock_inline_pair.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:498)、[test:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:609) |
| F5 | closed | [t1998_stock_inline_pair.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:960)、[test:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:618) |
| F6 | closed | [t1998_stock_inline_pair.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:106)、[test:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:536) |
| F7 | closed | [t1998_stock_inline_pair.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:40)、[test:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:682) |
| F8 | closed | [test_t1998_launcher_contract.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_launcher_contract.py:104) |
| F9 | closed | [t1998_stock_inline_pair.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:542) |

## 直した内容

- typed CMake define を正規化し、診断 knob と `CCBENCH_TRACE` を判定。
- configure/build directory と、exact `numactl --interleave=all` 後の実行対象を結合。
- toolchain manifest の canonical SHA-256 を各 arm で再計算。正例 fixture も自己整合化。
- `verify_done` を env tag 比較へ追加。
- 全 record の anomaly/verdict と、全 verify/bench の attempt 帰属を検査。
- 全 build genome に対して `BACKOFF_NOINLINE` key の存在自体を拒否。
- global admission failure の arm を `unknown` に変更。
- submit receipt 3 event の schema literal を exact pin。
- 恒偽だった `expected_genome` 診断分岐を削除し、F6 の全 genome 検査へ統合。
- 指定された冗長 gate 全箇所へ、単独では発火しない旨の comment を追加。

## 実走した検査

- `PYTHONPATH=. python3 orchestrator/tests/test_t1998_stock_inline_pair.py`
  - 29 passed
  - 0 failed
- `PYTHONPATH=. python3 orchestrator/tests/test_t1998_launcher_contract.py`
  - 7 passed
  - 0 failed
- `git diff --check`
  - 問題なし

## 受理集合の変化

- typed を含む実効 `BACKOFF_NOINLINE=1` configure を新たに拒否。
- `perf_build_cmd` 欠損、configure/build directory 不一致を新たに拒否。
- `/bin/true`、`/bin/echo` を実行し binary path を decoy 引数にした command を新たに拒否。
- toolchain manifest と record digest が不整合な root を新たに拒否。
- `verify_done.env_tag` が他 stage と異なる root を新たに拒否。
- attempt 非帰属の verify/bench、anomaly record、非 serializable verdict を新たに拒否。
- off-pair を含む全 genome の `BACKOFF_NOINLINE` key を値にかかわらず新たに拒否。
- schema literal が変更された submitter source を launcher 契約検査が新たに拒否。
- F7 は拒否集合を変えず、帰属を誤った `baseline` から `unknown` へ修正。

## 残した赤とその理由

なし。指定された両 harness は failed 0 です。nit と scope 外項目は実装していません。

## 総括

F1〜F9 はすべて closed です。変更は所有指定された 3 path のみで、`git add`、commit、build、benchmark、測定、qsub は実行していません。