---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2195-policy-binding
seq: 3
---

## 新規

### {{F:fifo-negative-leaks-blocked-grandchild}}. 書き手なし FIFO の負例が block した孫 process を残し、計算ノードの job が walltime まで終われなかった [観測の穴] [後始末漏れ]

- 事象: 変異走行で gate の policy open から `O_NONBLOCK` を外したところ、pytest は 14.28 秒で
  `1 failed, 144 passed` を出した (負例は期待どおり赤) のに、計算ノードの batch job は walltime
  3609 秒まで終われず orphan hold と変異残留を作った (request 979716)。
- 根本原因: `subprocess.run` の timeout は直接の子 (`bash`) しか kill しない。FIFO の open で block した
  孫 (heredoc の `python3`) が job の stdout / stderr を掴んだまま残るため、pytest が終わっても
  job が終われない。負例に timeout を付けることは「test が赤になること」しか保証せず、
  「走行が終わること」を保証しない。
- 恒久対応: {{D:mocc-policy-binding-five-party-sha}} の実装で、policy や pinned receipt に FIFO を置きうる
  3 つの wrapper の子起動を `start_new_session=True` + timeout 後の `os.killpg` による回収へ替えた
  (`orchestrator/tests/test_mocc_trace_job_contract.py` の `_run_in_process_group`)。
- 再発検知: 同じ変異 (gate policy open の `O_NONBLOCK` 削除) を変異 spec へ登録済み。回収経路が壊れれば
  この変異が再び walltime まで走り、期待 node と一致しない形で露見する。台帳は
  `output/insights/2026-09-07_t2195-policy-binding/mutation-ledger-final.json`。
