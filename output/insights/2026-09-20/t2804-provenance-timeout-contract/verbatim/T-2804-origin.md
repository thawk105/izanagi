- [T-2804] **P2・新規**: land の `_run_provenance_checker` は `timeout=480` を持ち、dispatcher の既定 queue 待ち
  上限は 900 秒。全史監査が dispatch へ倒れると監査本体が正常でも queue 待ちだけで land が先に打ち切る。D2148 項 8 (外側 timeout は全区間) の
  実装と併せて両立の契約を決める。timeout の延長は裁定なしに行わない。
