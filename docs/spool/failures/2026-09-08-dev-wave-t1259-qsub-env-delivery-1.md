---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1259-qsub-env-delivery
seq: 1
---

## 新規

### {{F:synthetic-fixture-hides-column-layout}}. 合成 fixture で書いた外部 command の列解析検査が、実機の列並びを 1 度も通さず緑だった [恒真ゲート] [未実測]

- 事象: 投入 script が `qstat` 本文から状態列を取る処理で、状態列 (STT) でなく Pri 列を
  読んでいた。実測した本文の field 番号は `0=RequestID 1=ReqName 2=UserName 3=Queue 4=Pri 5=STT`
  であり、実装は index 4 を状態として読んでいた。receipt には `observed_state: "0"` が残った。
- 根本原因: 既存 test の fixture が合成で、STT を index 4 に置いていた。実装と fixture が
  同じ誤った列配置を共有していたため、**実装が誤っていても緑になった**。実機の出力を
  1 度も通していない検査だった。敵対レビュー 2 本と焦点再レビュー 1 本も見つけていない。
- 恒久対応: `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の
  `test_request_receipt_accepts_measured_qstat_layout` が、実機から採った header 2 行 +
  データ行 1 行を逐語 fixture として持ち、`observed_state == "STG"` と owner 一致と受理成功を
  固定する。旧実装はこの fixture で `observed_state == "0"` になり赤になる。
- 再発検知: 外部 command の列・書式を解析する実装を足すときは、合成 fixture だけでなく
  実機出力の逐語 fixture を同じ検査に入れる。

### {{F:review-blind-to-uncovered-predicate}}. 「負例を足した」という報告が、実際にはその述語を通らない負例だった [恒真ゲート]

- 事象: 事前登録した 10 変異の probe 走で 5 件が生き残った。うち 3 件は
  未承認 driver argv への承認 flag 混入、argv 完全一致の緩和、承認値と nonce の一致検査の
  骨抜きであり、**いずれも規律 2 の中心にある**。直前の fix は「負例を追加した」と報告していたが、
  その負例は前段の検査が先に拒否する入力を使っており、対象の述語を通っていなかった。
- 根本原因: 負例の設計時に「どの検査が最初に拒否するか」を確かめていなかった。
  静的レビューは述語の存在を見るだけで、その述語に到達する入力があるかを見ない。
- 恒久対応: 変異事前登録の単一理由性確認 (`DW-M01`) を、負例側にも適用する。
  fix の報告に「足した負例 / その入力が最初に当たる検査 / 過剰決定なら根拠」を書かせる。
  実効は変異走で確かめる — {{D:mutation-over-static-review-for-negative-examples}}。
- 再発検知: 変異 matrix の SURVIVED を「等価変異」と判定する前に、その位置へ到達する
  負例が実在するかを確かめる。
