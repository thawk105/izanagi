## 所見

無し。

## 単一帰属の判定

- report: 成立。`test_s8b_oracle_report.py:1662-1669` の earlier result は `b"{}"`。強制行 `s8b_oracle_report.py:2548` を消すと、`reverify_published_freeze` は `ReverifiedFreeze` を指定するため `s8b_ratified_freeze.py:3322-3340` の選択分岐へ入らず、全走査にも新規 conjunction hit は生じない。その後は manifest 検証、report 生成、出力作成まで到達して rc=0 となる。

- judge: 成立。`test_s8b_oracle_judge.py:743-759` も earlier result は `b"{}"`。強制行 `s8b_oracle_judge.py:750` の削除後は同じく historical reverify が選択規則を再検査せず、実 manifest、observations、judge 経路を通って出力されるため rc=0 となる。

- verdict: 成立。`test_s8b_verdict.py:1007-1024` の earlier result は `b"{}"`。強制行 `s8b_verdict.py:829` の削除後は実 reverify を通り、`test_s8b_verdict.py:1046-1055` の後段 seam が成功値を返し、`s8b_verdict.py:867` の出力作成まで到達して rc=0 となる。

## 総括

3 CLI の強制位置、負例の単一帰属、正例による実強制呼出しを静的に確認した。  
D1504 対象の既存2テストは記録 stub と引数照合になっており、単純 no-op ではない。  
追加 assert に既知案件以外の恒真、恒偽、意図非検査は見つからなかった。  
pin は literal のままで、raw hash、report hash、judge hash の全てが実 bytes と一致する。  
pytest は実行しておらず、親提示の実測結果を前提とした。