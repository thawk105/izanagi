---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-t-397-sort-witness
seq: 3
---

## 新規

### {{F:mutation-parse-observation-gap}}. 実経路テストが構造化 witness の一部 branch の内容を検査せず、変異が SURVIVED した [テスト代表性]

- 事象: [T-397]/[T-410] の変異matrix (B-057) で、`orchestrator/verifier/parse.py` の
  `_sort_permutation_observation` の `"rcdptr-set-changed"` 分岐 (`rcdptr_multiset_preserved`
  を `False`→`True` に反転する変異) が SURVIVED した。
- 根本原因: `test_permutation_violation_details_follow_parse_verify_report_path`
  (`orchestrator/tests/test_verifier.py`) は、複数 branch (size-changed/rcdptr-set-changed/
  未知 token) を1回の trace で網羅する設計だったが、`details["sample"][0]["observation"]`
  (size-changed 側) の完全一致は検査する一方、`details["sample"][2]` (rcdptr-set-changed 側)
  は `source_thread_hint`/`source_thread_hint_basis` だけを検査し `observation` 本体を
  検査していなかった。複数 branch を1テストに詰めると、どの branch の完全一致検査を書いたか
  見落としやすい。
- 恒久対応: `sample[2]["observation"]` の完全一致 assert を追加 (commit `e946168c`)。
  一般則としては、複数 branch を1 fixture で網羅するテストでは、各 branch の代表 sample に
  ついて「完全一致 assert を書いた branch」のチェックリストを明示する (本 wave では
  変異matrixが機械的にこの欠落を検出した — 規律3 の実例)。
- 再発検知: 変異matrix (B-057) の各 branch を独立した mutation として登録し、KILLED を
  確認する運用そのもの。

### {{F:mutation-contract-loader-contamination}}. 変異harnessの一時書換えが CONTRACT_LOADER_RELATIVE_PATHS の autouse fixture を汚染し、変異matrixの node 抽出が失敗した [計測汚染]

- 事象: [T-397]/[T-410] の変異matrix probe で、`orchestrator/verifier/parse.py` を対象にした
  変異を `orchestrator/tests/test_critic.py` を含む runner で走らせたところ、
  `mutation harness aborted: rc=1だがcanonical stdoutからfailed nodeを確実に抽出できないため
  停止` で harness が中断した。
- 根本原因: `tools/mutation_worktree.py`/`tools/mutation_harness.py` は spec の変異を
  対象 file へ一時的に書き込む (元 commit へは戻すが、走行中は disk が HEAD と異なる)。
  `orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS`
  (`orchestrator/verifier/{core,dsg,model,parse,__init__,report}.py` 等23 file) に該当する
  file を変異すると、`orchestrator/tests/conftest.py` の `ratified_enforcement_source`
  (test_critic.py で autouse) が disk≠HEAD blob を検出し、対象外の全テストまで
  contract-loader-drift の setup error になる。この大量の同型 error が、正規の FAILED 行の
  抽出を曖昧にした。
- 恒久対応: 変異matrix の runner に渡す test file 集合を、変異対象が
  `CONTRACT_LOADER_RELATIVE_PATHS` に該当するかどうかで分割する
  (該当する変異は `test_critic.py` 等 `ratified_enforcement_source` 依存テストを runner から
  除外する)。`orchestrator/critic/digest.py`・`orchestrator/campaign/s5_permutation_coverage.py`・
  `orchestrator/campaign/silo_ladder_rung1.py` はこのリストに含まれないため、これらを対象と
  する変異では分割不要。
- 再発検知: 今回と同型の `mutation harness aborted: ... failed node を確実に抽出できない`
  エラー文字列。変異対象 file が `CONTRACT_LOADER_RELATIVE_PATHS` に含まれるかを段6条件成立時
  (`DW-M01` 事前登録時) に照合する運用を候補として段8へ送る。
