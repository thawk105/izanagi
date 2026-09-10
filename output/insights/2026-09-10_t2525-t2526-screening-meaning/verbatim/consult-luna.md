## 総括

planは版更新・旧bytes保持・caller追従の主要箇所を押さえている。must-fix候補は計画の縮小2件。静的検査のみ実施し、書込み・pytest・性能測定は行っていない。

1. **real候補 / must-fix：宣言case整合検証の新設は今回不要。**
   所在：[plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/artifacts/dev-wave-t2525-t2526/plan.md:38)、`backoff_sweep.py:118,425`、`condition_meaning_gate.py:3400,4098`。
   共通gateが不一致caseを未確立として受理するという説明は正しい。ただし今回のcallerは、既存の要求key完全一致検証とraw別の宣言生成を通る。正しく生成した宣言と観測の不一致は既存gateで拒否でき、転送ミスはmeaningがgreenになる検査で検出できる。新しい局所拒否の必要性は示されていない。
   **影響：明示した不一致宣言を未確立から拒否へ変え、今回必要な配線を越えて受理集合を狭める。**
   最小修正：`:38`の局所検証と`:95`の専用検査・変異を削除し、既存helperによる宣言生成、転送、実gateの正負検査に限定する。

2. **real候補 / must-fix：create-only変異の検出帰属が成立しない。**
   所在：[plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/artifacts/dev-wave-t2525-t2526/plan.md:99)、`backoff_extended_sweep.py:1268,378,395`、`test_backoff_extended_sweep.py:785`。
   materializerの存在検査を除去しても、両ファイルが既存なら下流writerの`O_EXCL`で拒否され、bytesも保持される。提案した再生成検査では、この変異をkillできるとは限らない。writer自体の保持検査は既存。
   **影響：既存bytes保持の観測は正しくても、存在検査除去の検出力を過大評価する。**
   最小修正：この新設検査・変異を必須集合から外す。今回の差分ではv2 discoveryと実materializerの出力先・metadata整合を検証する。

3. **refuted候補：basename据置きによる旧report上書き。**
   所在：`backoff_extended_sweep.py:675,1027,1264`、`replay.py:143`。
   discoveryはslug付きprefixで選び、reportは選択campaign配下へ書く。v2 slugならv1と分離する。
   **影響：計画どおりなら旧campaign/reportへの書込み参照は生じない。**
   最小修正：なし。v1 fallbackを設けない計画を維持する。

4. **refuted候補：shell・report consumerの版更新漏れ。**
   所在：`tools/pegasus/b10_backoff_grid.sh:645`、`tools/pegasus/submit_b10_backoff_grid.sh:37`、`backoff_extended_sweep.py:1526`。
   該当経路は維持予定のrun-kindとbasenameを使う。`orchestrator`・`tools`内のv1固定参照検索でも、producerと計画記載のテスト以外に追加編集対象は見つからなかった。
   **影響：今回の版変更に伴うcaller/consumerの取り残しは確認されない。**
   最小修正：なし。

5. **refuted候補：凍結hash不一致を今回の回帰として修復する必要。**
   所在：`s1_known_axes_freeze.py:872,889`、`output/s1-freeze/known_axes_freeze.json:152`。
   generatorだけでなく、記録された`backoff_sweep.py`のhashも現在既に不一致だった。親planのgenerator不一致は再確認できたが、それだけから全consumerの状態は一般化できない。
   **影響：既存の参照不一致はあるが、今回の凍結bytes変更・manifest再発行を正当化しない。**
   最小修正：再発行せず、関連回帰で失敗した場合に今回差分との帰属を分ける。