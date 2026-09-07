---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2353-terminal-stage
seq: 3
---

## 新規

### {{F:generator-output-pin-closure}}. 生成器の出力を固定する pin を、対象 file 自身の path 検索と hex literal 検索が取り逃した [閉包漏れ] [near miss]

- 事象: 親が段 1 で pin 閉包を引き、対象 3 file への path 参照と 64 桁 hex literal を検索して
  「bytes を pin する凍結 manifest・golden は不在」と brief に書いた。実際には fixture 生成器の
  **出力**を固定する凍結 snapshot (`orchestrator/tests/reflux_origin_fixture_baseline.json`) と
  golden literal 4 個 (`orchestrator/tests/test_reflux_result_evidence.py`) が実在し、
  合計 7 個の値が変更で stale になる状態だった。段 2 のプランと段 3 の 2 レンズが独立に検出した。
- 根本原因: 検索の起点を「変更する file」に置き、「その file の関数が返す値を hash して pin している
  箇所」へ辿らなかった。この種の pin は対象 file の path でも、変更前後どちらの hash 値でも引けない。
  生成物に path が無い (in-memory で作られる) 場合は、DW-O09 が言う成果物 path 検索がそもそも
  空振りする。
- 恒久対応: 依存グラフを起点にした引き直しを memory `closure-and-search-discipline` へ追記した。
  引き方は、変更する生成関数の全 caller を辿り、その戻り値に hash / 長さ / canonical bytes を
  適用している箇所を列挙する。値でも path でも引けないため、caller 追跡だけが見つける。
- 再発検知: 本 wave では段 2 と段 3 の 2 レンズが 3 者独立に検出した。閉包の再検査を段 3 のレンズへ
  明示的に入れる (「まだ他にあるはずだと疑え」と 4 通りの独立な引き方を指定する) 形が発火した。
