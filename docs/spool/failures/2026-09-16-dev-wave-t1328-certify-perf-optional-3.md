---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t1328-certify-perf-optional
seq: 3
---

## 新規

### {{F:inherited-sigterm-disposition-voids-signal-fixture}}. 継承された signal 無視設定が signal 依存の fixture を無効化し、テストは緑のまま意図した経路を 1 度も検査しなかった [テスト代表性] [恒真ゲート]

- 事象: 新規テストの `probe_error` 対照 2 件が、login node では緑だが Pegasus 計算ノードへ
  dispatch すると `assert 0 == 2` で赤になった。赤の内容は「production 断片が `exit 2` へ
  入らなかった」であり、receipt は `status=available / reason=available / rc=0` だった。
  **login node の緑は「経路を検査して通った」ではなく「意図した経路に一度も入らなかった」**
  を意味していた。
- 根本原因: fixture の偽計測コマンドが `os.kill(os.getpid(), signal.SIGTERM)` で自分を殺し、
  判定器の `rc < 0` → `probe-signal` → `probe_error` を作ることに依存していた。
  **SIGTERM の無視設定 (SIG_IGN) は exec を越えて継承される。** その設定を持つ実行環境では
  kill が何も起こさず、fixture は次の行へ進んで正常な出力を書き rc=0 で終わる。
  結果として `probe_error` ではなく `available` が観測され、停止を期待する assertion が外れる。
- 恒久対応: 自己終了を SIGKILL へ替えた。SIGKILL は無視・捕捉・ブロックのいずれもできないため、
  親 process の signal 処理設定に依存しない。期待値 (断片が rc=2 で止まること) は緩めていない。
  一般則は {{D:perf-probe-decides-not-candidate-exhaustion}} ではなく本項に置く —
  **テスト fixture が process の終了手段に依存するとき、その手段が継承される設定で無効化されないか
  を確かめる。** 無視できる signal を fixture の主機構にしない。
- 再発検知: 修正前後の対照を login node で取った。親 Python に `SIGTERM=SIG_IGN` を設定すると
  修正前は同じ本文で 2 件赤・receipt `available`、修正後は同じ条件で 2 件緑になる。
  構造的には、変異 harness の baseline を計算ノードへ dispatch して走らせることが検出者である
  (login node の実行だけでは検出できない)。DW-O16 の「PATH 構築・interpreter 解決・
  外部 command 選定など実行環境に依存する実装は、レビュー通過だけで closed とせず実機で
  動かすまで確かめる」が、**signal 処理設定にも及ぶ**ことを本件が示した。

### {{F:scanner-green-is-not-all-gates-green}}. 指定の走査器が緑でも別 gate の候補集合には当たる [恒真ゲート] [手順漏れ]

- 事象: 段 7 で `docs/dev-wave/core.md` DW-S07 が指定する三軸語走査器
  (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) を実行し rc=0 (検出なし) を得て
  記録を commit した。**受入全走がその commit を原因とする 45 件の赤を返した** —
  `test_s8b_oracle_driver.py` 40 件と `test_s8b_floor_campaign.py` 5 件が
  `FreezeError: holdout hit 2 件` で落ちた。
- 根本原因: 収容した変異 harness の生出力 2 本が pytest の収集一覧を丸ごと抱えており、
  その中の test 関数名が `s8b_holdout_freeze._assert_search_pass` の conjunction に当たった。
  **同じ module の `search` サブコマンドと、t080 e2e が走らせる `_assert_search_pass` は
  候補集合が同じではない。** 前者の緑は後者の緑を含意しない。
- 恒久対応: 機械が生成した大きな出力を insight へ入れるときは、生出力をそのまま収容せず、
  **必要な field だけを抜いた派生形にして、生出力は repo 外に残し sha256 と byte 数で引用する。**
  派生形に検出語が残っていないことを機械で確認する。本件では 418,586 bytes と 466,299 bytes の
  生出力を 26,009 bytes の派生台帳へ替え、baseline・各変異の期待/観測 node・各種 hash は保持した。
- 再発検知: 受入全走が検出者である。**走査器 1 本の緑を全 gate の緑と読まない。**
  記録に「走査器 rc=0」と書くときは、その走査器の候補集合が何であるかを併記する。
