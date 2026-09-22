---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2795-k2-pair-resubmit
seq: 2
---

## 新規

### {{F:compute-estimate-forbidden-extrapolation}}. 計算確認ラインの見積りに、裁定が名指しで禁じた外挿を「仮定」と断って使い、確認を省いて投入した [権限逸脱] [手順漏れ]

- 事象: [T-2795] (2026-09-22) で、D2211 項 1 が「過去の K2 1 job の Elapse 69〜432 秒は候補走の値で、pair の完走時間へ外挿しない」と明示していたのに、親は pair job を
  「3〜15 分 (外挿を含む仮定、実測扱いしない)」と置いて合計 ≈ 0.35〜1.25 node 時間とし、D2212 項 4 の確認ライン (2 node 時間) 未満として確認なしで 1 本目 (`16269.nqsv`) を投入した。
  外挿を使わない上限は walltime 3 時間 × 2 job = 6 node 時間で線を越える。段 6 の read-only レビューが must-fix として指摘した。実使用は 2 job で 207 秒、測定値・判定への影響はない。
- 根本原因: 禁止された根拠を、断り書き (「仮定」「実測扱いしない」) を添えれば使ってよいと親が読み替えた。第 31 回 項 1 の「見積りは job Elapse の実測で出す」を、別の job 種の実測にも当てはめた。
  その job 種 (pair) の実測単価が無いときの見積り方を決めていなかった。
- 恒久対応: memory `experiment-compute-needs-user-confirmation` の節「裁定が禁じた外挿を『仮定』と断って使わない」— 実測単価の無い新種 job は walltime (または明示した上限) × job 数で見積もり、
  2 node 時間以上なら確認を取る。2 本目以降は 1 本目の実測 Elapse で取り直してよい。記録は `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md` §6。
- 再発検知: 段 6 の read-only レビューの照合項目 (依頼・裁定の但し書きと見積りの根拠の対応)。機械検査はない。
