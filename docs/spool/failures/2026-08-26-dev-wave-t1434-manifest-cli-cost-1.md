---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1434-manifest-cli-cost
seq: 1
---

## 新規

### {{F:codex-child-deletes-parent-untracked-output}}. workspace-write の子が親の未追跡成果物を一時コピーと誤認して消した [権限逸脱] [手順漏れ]

- 事象: 段 6 の fix 子が作業終了時に「insights の一時コピー」として
  `output/insights/<wave>/` 配下を除去した。実体は親が書いた段 1 brief・段 4 裁定・段 6 裁定で、
  未追跡だったため git から復元できなかった。job dir の控えから手で戻した。
- 根本原因: 子 prompt が「`output/` を編集するな」と書いていたが、
  **子が自分で作った一時物を片付ける動作と、親の成果物を消す動作を区別する記述が無かった。**
  加えて親が、workspace-write の子を起動する前に自分の成果物を commit していなかった。
- 恒久対応: 親側の手順を `docs/dev-wave/operations.md` の `DW-O02` へ寄せる
  ({{D:commit-parent-artifacts-before-workspace-write}})。
  子 prompt には「`output/insights/` 配下は親の成果物である。一時コピーではない。消すな」を
  明示的に書く。
- 再発検知: 変異 harness と受入 preflight が未追跡 file を拒否するため、
  親が commit を怠ったまま次段へ進むと機械的に止まる (`mutation harness aborted:
  tracked/index dirt または untracked file があるため停止`)。

### {{F:mutation-registration-counted-one-link-for-a-whole-chain}}. 連鎖する検査を 1 変異で代表させ、他リンクの穴を取り逃しかけた [恒真ゲート]

- 事象: task manifest の digest 連鎖 8 箇所に対して変異を 1 件だけ登録していた。
  段 6 の敵対レビューが「freeze の 1 リンクしか殺せない」と指摘し、
  親が consumer ごとに 8 分割して登録し直したところ、
  **`append-verdicts` と `reveal-mapping` の packet state 検査を外す変異が 588 件緑のまま生存した。**
  分割しなければ「KILLED 1/1」で通っていた。
- 根本原因: 同じ helper を呼ぶ検査群を「1 つの機構」と数え、
  **呼び出し側ごとに独立した防壁であることを勘定に入れていなかった。**
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` に従い、
  連鎖する検査は consumer ごとに登録する ({{D:mutation-registration-per-consumer}})。
- 再発検知: 変異 matrix の SURVIVED が 0 でなければ land できない。
  分割前は SURVIVED が出ず、分割後に 2 件出た。分割自体が検出器である。
