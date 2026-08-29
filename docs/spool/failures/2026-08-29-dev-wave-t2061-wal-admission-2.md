---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2061-wal-admission
seq: 2
---

## 新規

### {{F:mutation-harness-queue-wait-fixed}}. 変異 harness の待ち上限だけ上書きが届かず、混雑時に走らせられない [手順漏れ]

- 事象: [T-2061] wave で変異走行が 4 回連続で起動できなかった。いずれも下位の
  `DispatchError: queue-wait-timeout` で、子は 1 度も起動していない。実測の待ち時間は 902 秒で、
  既定上限 900 秒 (`tools/pegasus/dispatch_compute.py` の `DEFAULT_QUEUE_WAIT_TIMEOUT_S`) を
  わずかに超えていた。当時の gen_S は 61 待ち / 75 実行 / 49 保留。
- 根本原因: `tools/run_tests.py` は `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` で待ち上限を
  上書きできるが、**変異 harness は dispatch 時に `run_tests.py` を介さず
  `tools/pegasus/dispatch_compute.py` を直接呼ぶ** (`tools/mutation_harness.py` の
  collection / 本走の command 構築)。そのため上書きが届かず、上限は 900 秒に固定される。
  `dispatch_compute.py` 側に同等の環境変数は無く、harness は `--queue-wait-timeout` を渡さない。
- 逃げ場が無いこと: ローカル走行は harness が `receipt_path` / `job_stdout_path` の null を
  要求する一方、`run_tests.py` は headroom を見て自動 dispatch する。強制ローカルの手段が無いため、
  混雑時は dispatch の成功を待つ以外に選択肢が無い。
- 恒久対応: 未実装。当面の回避は「失敗ごとに間隔を空けて自動で投げ直す」ことで、本 wave では
  その形で通した (混雑が引いた回に baseline PASSED、15/15 KILLED)。
  機械的な恒久対応は待ち上限の伝播経路を作ることだが、`dispatch_compute.py` の受理集合に
  触れるため別裁定とする。
- 再発検知: 変異走行が `rc=2` で止まり、`output/pegasus-dispatch/*/receipt.json` の
  `outcome.reason` が `DispatchError: queue-wait-timeout` で `state_history` の末尾が
  900 秒付近の `QUE` なら本件である。子が起動していないので**本 wave の赤ではない**。

### {{F:tmp-git-poisons-output-root-gate}}. `/tmp/.git` の点滅生成で全 tmp_path が repository 内と判定される [計測汚染]

- 事象: [T-2061] wave の焦点走で 18 件が
  `ValueError: official output_root は repository 外でなければならない`
  (`orchestrator/campaign/layout.py`) で落ちた。実装とは無関係だった。
- 根本原因: `/tmp` 直下に空の `.git` directory が存在すると `_has_git_ancestor()` が真になり、
  pytest の `tmp_path` (既定で `/tmp` 配下) がすべて repository 内と判定される。
  他 session のテストが一時的に作っては消しており、`rmdir` しても再生成される。
- 二次の罠: 回避のため `TMPDIR` を移すとき、`/work/1/SFC/tanab/dev-wave-jobs/` の下にも `.git` が
  あるため同じ罠に落ちる。本 wave は最初にここを選んで 229 件の偽赤を出した。
  `.git` の祖先が無い場所を選ぶ必要がある。
- 恒久対応: 未実装。当面の回避は `.git` 祖先の無い専用 `TMPDIR` を wave ごとに用意すること。
- 再発検知: `layout.py` の `official output_root は repository 外でなければならない` が
  複数 test file で同時多発したら、失敗した `raw = ...` の path から祖先を辿って `.git` を探す。

### {{F:enforcement-closure-member-needs-commit}}. 閉包 member を未 commit のまま検査すると全域が drift で赤になる [手順漏れ]

- 事象: [T-2061] wave で `orchestrator/campaign/artifact_admission.py` を編集した直後の焦点走が
  11 件赤になった。本文は
  `contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/artifact_admission.py`。
- 根本原因: 同 file は `orchestrator/campaign/campaign_lock.py` の
  `CONTRACT_LOADER_RELATIVE_PATHS` (exact 24 path の enforcement source closure) の member であり、
  `contract_loader_binding` は disk bytes と HEAD blob の一致を要求する。編集して未 commit の間は
  必ず drift になる。commit 後に同じ 3 file を再走して 74 passed で解消を確認した。
- 恒久対応: 未実装。作法としては「閉包 member を編集する wave は、検査を走らせる前に commit する」。
- 再発検知: `contract-loader-drift` の本文が名指しする path が
  `CONTRACT_LOADER_RELATIVE_PATHS` に載っており、かつ `git status` でその path が未 commit なら本件。
  **実装の回帰ではない。**
