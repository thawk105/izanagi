---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2457-a6-fanout-live
seq: 3
---

## 新規

### {{F:probe-summary-file-cannot-discriminate-per-rank}}. 生死確認 probe が rank ごとの出力を 1 本の要約 file へ書き、弁別できない主張を「実測」として insight と裁定へ通した [捏造/幻覚] [テスト代表性]

- 事象: multi-node の生死確認 probe が「job script は job 0 (head) でだけ走った」と記録し、
  その insight を根拠に輸送設計の裁定が書かれた。実機で `-b 5` の認証を走らせたところ
  **job script は 5 rank すべてで走り**、rank 1〜4 が同じ compute 結果 file を作ろうとして
  5 秒で全体が落ちた。結果 file を実際に書いたのは head ではなく rank 4 だった。
- 根本原因: probe は全 rank が**同じ 1 本の要約 file へ書く**設計で、残るのは最後に書いた
  rank の内容だけだった。「1 rank 分の内容しか無い」から「1 rank しか走らなかった」を導いた
  のは**推論であって観測ではない**。probe の出力形式が、確かめたい主張 (何個の rank が走ったか)
  を弁別できていなかった。裁定文と insight はこれを実測として書き、下流はその強さで読んだ。
- 恒久対応: memory `liveness-probe-must-separate-observation-per-subject` —
  **並行する主体 (rank・ノード・process) を数える確認は主体ごとに別 path へ書き**、1 本の
  要約への上書きから主体数を導かない。memory `mutation-discipline` の「観測 root」条項と
  同じ向きであり、書き先を 1 本にした時点で主体数の主張は立たない。加えて `DW-S01` の既存義務
  「brief 前に承認済み裁定と引数の前提を実測し、覆す新事実は brief に出して段 4 で再裁定する」の
  対象に、**先行 wave の生死確認が「実測」と書いた項目も含める** — 一次資料の probe 出力まで
  辿り、その出力形式が主張を弁別できるかを見る。`docs/dev-wave/core.md` の `DW-G01` へ入れる
  ことも試したが、L1 の byte 予算 (10,625) を 210 bytes 超えて `check_docs.py` が赤になるため
  入れていない。安全義務を削って詰めることはしない。
- 再発検知: 生死確認の結論を insight へ書くとき、主張ごとに「どの file のどの行がその主張を
  他の可能性から弁別するか」を 1 行で添える。添えられない主張は「推論」と明記する。本件は
  実機実走が 1 回で暴いたので、**機構の本走を先送りにしないこと自体が検出器**である。
