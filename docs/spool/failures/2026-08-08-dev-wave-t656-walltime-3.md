---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t656-walltime
seq: 3
---

## 再発

### F57

- **再発: 2026-08-08 ([T-656] 受入全走)。** 48 worker の全走 (request `896109`、7414 件) で
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が 1 件落ちた (7393 passed / 1 failed / 20 skipped)。assert 不一致ではなく
  `git -c core.useReplaceRefs=false cat-file --batch-check` の 15 秒 timeout (`returncode -9`) で、
  台帳既載の 2026-08-06 ([T-522]) / 2026-08-08 ([T-639]) と**同一 node・同一 producer**である。
  同 file の単独再走は 8 passed / 39.51 秒 (rc=0) で再現しない。本 wave の差分は
  `dispatch_compute` の既定 walltime 定数とその検査だけで当該コードへ到達せず、
  `DW-O18` により帰属しない。
  **新しい情報は、この全走が 40 分枠へ引き上げた最初の走行だったこと**である。走行そのものは
  Elapse 1213 秒で完走しており、枠不足 (F167 型) とは別型であることが同じ走行の中で分離できた。
  親は codex 子を 1 本も起動していない。恒久対応は F57 既載の失敗 artifact 保存による原因分離
  ([T-190]) のままで、本 wave では変えない。

### F155

- **再発: 2026-08-08 ([T-656] 記録後の再走)。** 段 7 の docs commit 後に
  `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py orchestrator/tests/test_spool_fold.py -q -rf`
  を追加 flag なしで投げ、`bounded scope の memory.max / memory.oom.group を走行中に attest できない`
  で rc=16 になった。`--force-dispatch` を足した再走は計算ノードで 438 passed / rc=0。
  本 F の (b) と 2026-08-07 ([T-618]) の再発が**既に射程として明記していた**
  「login ノードから投げる短時間の targeted 走行」そのものであり、新しい条件ではない。
  実装差分は 1 byte も汚れていない。**新しい情報は、この型が変異本走・単発 targeted 走行だけでなく
  段 7 の記録後再走 (F34 の閉じ工程) でも出ること**で、発火点は wave の終盤にもある。
  恒久対応は本 F 既載の既定 recipe のままで、追加の機構は作らない。
