# 回収監査の裁定

- review A/Bはdone=0、check_codex_output=0。新規の実装must-fixは双方0。
- REC-1はreal、採用。旧failures fragmentはfix前NO-GOを解消根拠にしており、fix-4/5と最終焦点走、新独立監査へ参照を訂正する。
- BのRR-4「2 errors脱落」はrefuted。一次focus-chain-3.logのpytest終端は `2 failed, 1088 passed, 7 skipped in 388.35s`、failure digestは`failures=2 failed=2 errors=0`。summary.txtの`2 errors`が誤り。INTERNALERROR/crashitemの存在を別記して、旧summaryにerratumを付ける。旧生logは不変。
- RR-1は両監査で静的closed。base構築が親rootを読む既存残余を、copy後の読取り閉鎖と混同しない。
- 受入300秒・base/copy所要の目標証明は本回収の追加scopeにしない。新実測がない数値を記録しない。
- 旧変異はe2b3cc483で12 KILLED/1 SURVIVED、双方baseline247 passed。spec SHAとexpected/failed集合を照合済み。統合tipでproduction3fileと対象4test fileはbyte同一。現tipの新実走とは区別する。
- 実装修正はsink2リテラルだけを隔離authorへ依頼済み。共有fileの現main追加を保持する。新gate/台帳/一般化は追加しない。
- failuresの「245秒の半分を超えたらshared-baseへ」は測定根拠のない一般規則なので採用せず、本事象の検査ポインタへ限定する。
