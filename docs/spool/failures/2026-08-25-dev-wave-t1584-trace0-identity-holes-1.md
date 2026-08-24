---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1584-trace0-identity-holes
seq: 1
---

## 新規

### {{F:normalization-drops-old-rejection}}. 正規化を足すと旧解析が拾っていた入力が受理側へ移る [恒真ゲート] [受理集合]

- 事象: TRACE=0 前処理同一性検査の穴を塞ぐ過程で、同型の退行が 3 回続けて起きた。
  (1) CMake bracket-aware lexer を足したら、bracket argument 内の見かけの供給 call を拾って
  いた旧走査が消え `set(DOC [[target_compile_definitions(t PRIVATE MQLOCK)]])` が通った。
  (2) raw/logical include の位置・綴り対応 gate を足したら `len(raw) != len(logical)` の
  件数拒否が消え、両側の block comment 内へ decoy の `#include` を 1 本置いた pair が通った。
  (3) 先頭 UTF-8 BOM の除去を足したら BOM 有無の差による include 行列の不一致拒否が消え、
  old だけ BOM 付きの pair が通った。3 例とも実装子は「受理集合は狭まる方向にだけ動かした」と
  自己申告し、テストも緑のままで、静的な敵対レビューだけが検出した。
- 根本原因: 解析の正確さと受理集合の単調性は独立である。粗い解析は本来通すべき入力も拒否して
  いる (過剰拒否) ことがあり、それを正すと受理集合は必ず広がる。「より正確にした」ことは
  受理集合を広げてよい理由にならない。旧拒否だけが発火する負例が無かったため機械検査も素通しした。
- 恒久対応: {{D:normalization-must-union-old-view}} が「正規化を足すときは旧 view を置き換えず
  必ず和集合にし、旧拒否だけが発火する単調性テストを同時に置く」ことを定める。実体は
  `orchestrator/campaign/source_digest.py` の `_c_supply_views` / bracket monotonicity view と
  `tools/check_trace0_preprocess_identity.py` の include 認識面の和集合。
- 再発検知: `orchestrator/tests/test_check_trace0_preprocess_identity.py` の単調性テスト
  (`test_bracket_payload_legacy_rejection_is_preserved`、両側 decoy-only、old/new 非対称 BOM) と、
  和集合の旧 view 側だけを殺す変異 (M6 / M11c / M4d) を変異事前登録に含めること。

### {{F:static-single-reason-judgment-masks-mutation}}. 変異の単一理由性を静的判定で済ませると mask を見逃す [変異] [恒真ゲート]

- 事象: 変異事前登録で、親と実装子がともに「M6b (`set_property` 供給認識の除去) は同じ入力を
  拒否する層が前後に無く単一理由」と静的に判定した。DW-M07 に従い全件 SURVIVED 期待の probe 巡を
  回したところ **M6b は SURVIVED** だった。親自身が monotonicity view のループへ `set_property` を
  含めていたため、主分岐を消しても旧 view 側が同じ helper を呼んで拒否していた。
  同じ probe で M11b (line-spliced include の専用拒否) も冗長 gate として SURVIVED した。
- 根本原因: 和集合・多層防壁を持つ実装では、ある分岐を消しても別層が同じ入力を拒否するため、
  コードを読んだだけでは実効 gate を特定できない。とくに**自分が直前に足した層**は
  「前後に無い」の検査対象から抜け落ちやすい。
- 恒久対応: DW-M01 の「同じ入力を拒否する層が前後に無いことをコードで確認する」は静的確認では
  足りない。DW-M07 の probe 巡 (全件 SURVIVED 期待で観測 node を集める) を、期待 node が
  埋まっている場合でも和集合・多層防壁を持つ実装では回す。SURVIVED した M は実効 gate へ
  再照準するか、DW-M03 に従い冗長 gate と明記して単独変異の証拠から外す。
- 再発検知: 本 wave の probe 巡 receipt (`mutation-ledger-probe.json` の SURVIVED 2 件) と、
  再照準後の probe 第 2 巡で SURVIVED 0 件になったこと。
