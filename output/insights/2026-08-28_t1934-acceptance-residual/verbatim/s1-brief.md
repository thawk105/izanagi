# T-1934 段1 brief

- scope: 既存 acceptance K=2/K=3 の receipt、JUnit、shard report、runner log だけから `pytest wall - 最遅 worker duration 和` を collection、worker 起動、prewarm、finalization に分ける。
- scope: 最大成分が現行 main で再現可能かつ局所修理が一意な場合だけ、その1成分へ最小修理を1件当て paired 再測定する。
- scope 外: T-1933 の重い単体短縮、別成分の同時修理、恒久 timing 計装、新監視基盤、skip/deselect/timeout 緩和、受理集合変更。
- 確定裁定: 規律2を緩めない。rulings inbox は未裁定索引で authority ではなく、T-1934 に裁定待ちはない。
- 既存被覆: D713 は queue/job/pytest/外側 wall を分離し、D724/D1103 は shard 経路、D518/D636 は controller-only prewarm を確定済み。純増は残差4成分の現物分解と最大成分だけの条件付き修理である。
- 既存 K=3 現物: shard wall 160.920/123.215/146.192秒、最遅 worker 101.697/74.175/96.635秒、残差 59.223/49.040/49.557秒。
- 既存 K=3 現物: prewarm consumer は shard-0 のみ receipt 36件 + oracle 28件、shard-1/2 は双方0件。prewarm無し2 shardにも約49秒の残差がある。
- 既存 timestamp: scheduler start→JUnit session timestamp は4.129/5.372/7.353秒。JUnit終了推定→scheduler end は秒粒度で0〜0.455秒。login独立collectionはsession作成後約9秒で完了しqueue待ちと併走した。
- 既存対照: 同系runnerの全collection・48 worker・0 test走は12.86秒。ただし旧tip/別走の値で、現行4成分の一意分解には使わない。
- (P1) `worker duration 和` は busy-timeであり、残差は4成分以外のscheduler idleも含む。既存artifactだけでは collection と worker起動、idleを一意に分離できない、という親の provisional 裁定であり攻撃対象。
- (P2) finalizationは1秒未満、prewarm差分は最大でも約10秒の観測なので、約49秒の共通残差が最大候補。ただし collection対worker起動対idleは非識別、という親の provisional 裁定であり攻撃対象。
- 不変条件: report/JUnit/receiptの完全性、selected==finished、shard和==独立collection、scheduler=loadgroup、pytest rc、恒久除外、freeze/oracle gateを一切弱めない。
- 成果物影響: 誤って最大成分を断定すると受入高速化を再現できず、land待ちと検査資源を増やす。受理集合・certified選択・研究report/proof bytes自体は本診断で変えない。
- 成果物: 4成分の値または上下界・非識別理由・最大成分判定、実装可否裁定、必要なら1修理のpaired全受入、scope外handoff、worklog fragment。
- 実測環境: Pegasus LOGINから `tools/run_tests.py`/acceptance lease経路を使い、性能測定はcomputeへdispatchする。queue待ちは目標外だがreceiptに分離記録する。
- 分割: 段2 plan 1本、段3は計時識別レンズとcorrectness/局所修理レンズの2本。段4で実装なしなら5/6を飛ばす。
- 変更面候補アンカー: `tools/run_tests.py` の shard dispatch/pytest child境界、`tools/acceptance_shards.py` の plugin hooks/report/merge、`orchestrator/tests/conftest.py` の2 prewarm hook。現時点で編集所有は未確定。
