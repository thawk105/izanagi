---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2429-verify-fanout
seq: 2
---

## 新規

### {{F:codex-child-dies-at-model-call-cap}}. 段 5 実装子が model 呼び出し上限で報告を書かずに打ち切られた [手順漏れ] [コンテキスト浪費]

- 事象: [T-2429] の段 5 実装子 (単位 A) が既定の model 呼び出し上限 100 回に当たって打ち切られ、
  受領証は `f45_missing_output`、成果物は 0 byte になった。46 分の作業のうち worktree の未 commit
  差分 (pipeline 834 行、commit_receipt 183 行、新規 module と新規テスト) は残っていたが、
  何を実装し何が未了かの申告は失われた。親は差分を監査対象として引き継ぐ継続子を投げ直した。
- 根本原因: `tools/dev_wave_codex.py` の `--max-model-calls` は既定 100 で、`DW-O01` は
  「`--max-*` は非権威で増量可」とだけ書く。上限に当たったときに**報告が 0 byte になる**ことと、
  そのとき worktree の差分は残るので継続子に監査させれば作業を捨てずに済むことは、どの手順書にも
  書かれていなかった。親は重い単位の見積りを取らずに既定のまま投げた。
- 恒久対応: memory `codex-child-dies-silently-at-model-call-cap` — 重い実装単位では
  `--max-model-calls` を上げ、prompt に「予算の 8 割で報告を書く」を明示し、打ち切られたら
  worktree の差分を残したまま継続子へ監査させて引き継ぐ。`DW-O01` は既に「重い巡は call/token を
  見積もる。中断子は未完了と記し次の子に監査させる」を持っており、欠けていたのは「打ち切ると
  出力が 0 byte になる」の 1 点だけである。同節への追記は L1.5 層の byte 予算 (9,696) に 58 bytes
  分の余地が無く入らなかったため memory に持つ (同じ理由で入らなかった 2 例目)。
- 再発検知: 受領証 (`receipt.json`) の `failure_class=f45_missing_output` と
  `limit_trigger=max_model_calls` の組。`check_codex_output.py` は 0 byte を rc 非 0 で弾くので、
  親は必ずこの組を見て継続子か再投入かを決める。

## 再発

### F1

- **再発: 2026-09-08** — [T-2429] の起票文と D1763、および 2026-09-08 の A-6 insight が
  「ノードを跨いで建て直すと bytes が変わることは 2026-09-02 に実測済み」と書いていたが、
  一次資料 (2026-08-31 の B-10 正式走 insight) の実測は「**別 job** で建て直すと job 固有の path が
  `.rodata` の `__FILE__` と RUNPATH へ混入して bytes が変わる」であり、2 台の計算ノードで
  建て直して sha256 を突き合わせた記録は存在しない。「別ノード」への一般化は同資料末尾の推論を
  後続文書が確定事実として引き写したものだった。検出は本 wave の段 1 で親が一次資料を
  独立コンテキストで検索したことによる。含意そのものは成り立つが、言い切りが一次資料より強い。
