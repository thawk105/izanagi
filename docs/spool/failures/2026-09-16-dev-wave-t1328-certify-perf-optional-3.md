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
