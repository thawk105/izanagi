---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1683-rr5-cost-calibration
seq: 3
---

## {{D:measurement-instrument-must-match-target-env}}. コストを測る器具は、測る対象と同じ pin・同じ env contract で走らせる

**決定:** ある走行のコストを見積もるための計測は、その走行が実際に使う ccbench pin と
env contract を使って行う。既存の calibration 成果物を、pin か env tag のどちらかが
違うまま見積りの根拠にしない。器具側が別の pin を固定しているなら、その器具は使わず、
対象と同じ条件で走る計測経路を用意する。

**理由:**
- pin が違えば測る対象の実装が違う。本 wave の起票根拠だった参照値は
  `s2_verify_calibration.py` が産んだもので、同 driver は歴史再現用に
  ccbench pin を `dff0f1e` へ固定している。A-2 の現行 pin は `511c953` である。
- env contract が違えば実行条件が違う。`linux-baremetal` は
  `clocks_per_us=1800` で numactl を前置するが、`pegasus` は `2100` で numactl を前置しない。
  同じ workload flag を書いても、走る条件は同じにならない。
- 本 wave の実測では、条件を揃えた結果として**最も重い cell の同定が入れ替わった**。
  参照値から比で外挿していれば write-heavy (rr5) が律速だと結論していたが、
  実際に最も重いのは balanced (rr50) の backoff 無し cell だった。
  比の転移は絶対値を外すだけでなく、順序も外す。

**却下した選択肢:**
- 既存の参照値へ workload 比を掛けて外挿する — 上記のとおり順序ごと外す。
  ユーザー裁定でも明示的に禁じられた。
- 器具側の pin 固定を現行 pin へ書き換える — 同 driver は歴史再現の役割を負っており、
  pin を動かすと過去の成果物との対応が切れる。別経路を用意するほうが安い。
- env contract の値を計測側へ literal で写す — 写した時点で contract の変更に追随しなくなる。
  `env_contract.lookup()` から引く。

## {{D:cheap-probe-before-long-reservation}}. 長い予約枠を取る計測は、同じ枠の中で最初に安く落ちるように組む

**決定:** 数時間規模の walltime を予約して行う計測は、失敗が予約枠の先頭で
安く露見する順に検査を並べる。具体的には、計算ノードでしか判明しない前提
(toolchain の実在、受理判定、単独性、空き容量) を、重い build と本計測より前に置く。

**理由:**
- 本 wave の実走 4 回のうち 2 回は probe の欠陥で落ちたが、どちらも 22〜23 秒で
  終わったため 6 時間の枠をほとんど消費しなかった。落ちた位置が
  build 完了後や計測途中であれば、1 回の失敗で数十分から数時間を捨てていた。
- 計算ノードでしか判明しない前提は、login node の検査や子の sandbox では
  原理的に確かめられない。「実走して初めて分かる」ことは避けられないので、
  **分かるのを早くする**ほうを設計する。

**却下した選択肢:**
- 短い walltime で試走してから本番を投げる — 投入と queue 待ちが 2 回になり、
  かつ試走用の別 job body を保守することになる。同じ job body の先頭で落とすほうが安い。
- 検査を省いて本計測へ直行する — 失敗が遅い位置へ移るだけで、期待コストは上がる。
