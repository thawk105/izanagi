---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t553-git-budget
seq: 3
---

## 新規

### {{F:mutation-spec-timeout-below-dispatch-floor}}. 変異 spec の timeout を local 実測から決め、dispatch 経路の下限を割った [テスト代表性] [手順漏れ]

- 事象: 変異 matrix が `mutation harness aborted: mutation record M03.artifact dispatch path
  field が文字列でない` で中断した。`--resume` を 3 回繰り返しても同じ変異で止まり進捗ゼロ。
  中断した dispatch dir には `receipt.json` も job 出力も無く、job が完走する前に打ち切られていた。
- 根本原因: 親が実装子へ渡した所要見積りが**ログインノード local の 3.87 秒**で、
  spec がそこから `timeout_seconds: 30` / `hang_timeout_seconds: 15` を決めた。
  しかし runner は `--runner-mode dispatch` であり、**scheduler への投入・queue・ノード起動・
  回収の往復だけで 21.8〜26.9 秒**かかる。台帳実測は baseline 21.761 秒、M01 26.855 秒、
  M02 26.923 秒。`hang_timeout_seconds = 15` は往復すら終わらない値で、
  `hang_risk: true` の 4 件が全部 artifact 不完全で落ちた。non-hang の 30 秒も
  実測 26.9 秒に対して余裕 3 秒しかなかった。
- 分離できた範囲: 順序依存ではない (resume で先頭に来ても同じ変異で落ちる)。
  変異内容とも無関係で、`hang_risk` の真偽だけが分岐条件だった。
- 恒久対応: `estimated_run_seconds` / `timeout_seconds` / `hang_timeout_seconds` を
  dispatch 実測 (26.923 秒) から決め直し `27 / 90 / 60` とした。倍数で余裕を取る
  (queue 待ちは他ジョブ次第で伸びるため、秒数の加算では足りない)。
  再走で **12/12 KILLED、SURVIVED 0、baseline PASSED** を得た。
  規律として `docs/dev-wave/mutation.md` の `DW-M05` が親へ課す「起動前に総所要を見積る」義務は、
  **runner mode ごとの下限を含めて見積る**ことを意味する。
- 再発検知: 変異 spec の timeout が runner mode の実測下限を下回っていないかを、
  親が spec 起草子へ渡す見積り値の出所 (local か dispatch か) で確認する。

### {{F:lease-state-matched-literally}}. 受入 lease の状態判定を逐語一致で書き、取得済みのまま lease を握り続けた [手順漏れ]

- 事象: 受入 lease の待ち手スクリプトが `state=acquired` という文字列一致で判定していたが、
  `tools/wave_land_window.py claim` の出力は JSON (`"state": "acquired"`) だった。
  そのため **lease を取得した後も break せず claim を回し続け、受入全走を投入しないまま
  約 3 分間 lease を保持**した。その間ほかの wave の受入投入は止まる (head-of-line blocking)。
- 根本原因: 出力形式を確かめずに、runbook §7.3 の説明文にある `state=acquired` という
  表記をそのまま shell の pattern にした。**説明文の表記と実際の出力形式は別物である。**
- 分離できた範囲: lease 自体は正常に動作しており (`holder_self: true` を返していた)、
  欠陥は親の投入ラッパだけにあった。実害は他 wave の待ち時間のみで、受入結果には影響しない。
- 恒久対応: 判定を JSON parse へ変え、`state` と `holder_self` の両方を見る形にした。
  規律としては、**待ち手を書く前に対象コマンドの出力を 1 回実際に見る**ことに尽きる。
  runbook §7.3 は「`state=acquired` のときだけ投入する」と意味を述べており、
  逐語の pattern を与えているわけではない。
- 再発検知: 待ち手が「取得できたのに投入していない」状態は、lease の `age_seconds` が
  伸び続けるのに受入ログが生成されないことで検出できる。
