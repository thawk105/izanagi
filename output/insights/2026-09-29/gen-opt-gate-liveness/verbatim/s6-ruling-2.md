# 段 6 裁定 2 (焦点再レビュー s6-focus1.md への裁定、2026-09-29 15:3x JST)

焦点再レビュー判定: NO-GO。F1・F2・F4・F6・F8・F9 closed、F5 refuted-confirmed、F3・F7 partial、新所見 N1。

| 所見 | 裁定 | 扱い |
|---|---|---|
| N1 must-fix | real・採用 | 起動器 `launch_gate_liveness.py` の判定器の終了値の扱いを直す。判定器 (`orchestrator/verifier/cli.py` の main の終わり) は certified=0、non-serializable を含む=1、indeterminate を含む=3 を返す。stdout の JSON が読めて `results[0].verdict` がある場合、rc 0・1・3 は「判定結果」として記録し走行を続け、`prereg` を評価する (B1 の verdict は記録だけ、stock は診断、fix は serializable かつ certified を期待 → 外れれば prereg 不一致で終了値 4)。JSON が読めない・rc がそれ以外 (起動失敗、timeout など) だけを実行失敗 (終了値 1) にする。`/usr/bin/time -v` は子の rc をそのまま返すことを前提にしてよい。 |
| F3 partial | N1 で閉じる | 同上。 |
| F7 partial | 親の分担 | 見積りは親が一次資料に書く。stock job の実測 (bnode009、trace build configure 1.7 秒 + build 4.3 秒、job 全体約 2 分) を使う。レビューの訂正 (依存物準備の build は `ycsb_silo.exe` だけ) を採る。 |

stock job (s1-stock、35409.nqsv) は fix 1 後の起動器で完走済み (rc=0、判定器は両 workload で rc=0) なので、N1 の修正は stock の結果に影響しない。stock の結果は再走しない。
