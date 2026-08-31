---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t425-premise-refuted
seq: 2
---

## 再発

### F597

- **再発: 2026-09-01** — 既存例は親の「既に閉じている」を段 3 が反証した型だったのに対し、本件は
  **段 3 を省いたため、親の誤った readiness 判断がそのままユーザー報告として出た**点が新しい。
  親は T-425 の着手前実測で「A4 の現物は揃っている」「凍結側を g2 まで進める必要がある」と結論し、
  軽量版として相談子を立てずに報告した。ユーザーの指示で後から Codex 相談 2 レンズを回したところ、
  両方が独立に反証した。A4 は readiness index が `unmet` と書いており、親は「発行前だから正常」を
  「揃っている」へ読み替えていた。凍結世代は環境世代と別番号で、正式 launch は
  `orchestrator/campaign/s8b_ratified_freeze.py` の `certificate-generation-scope` が
  `generation_number == 1` 専用に限定するため、g2 まで進めるとかえって拒否される。
  停止裁定は「実装しない」という裁定であって作業なしではなく、対象が activation の正しさ関門である
  以上 `DW-C00` の「正しさ防壁に触る段では独立の敵対検証子を省かない」に該当する。**停止で終える
  wave を軽量版の根拠にしてはならない。** 実害は誤った報告 1 通で止まり、実装・land には至っていない。
