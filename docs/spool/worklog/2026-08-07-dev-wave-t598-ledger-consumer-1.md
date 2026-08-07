---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t598-ledger-consumer
seq: 1
title: [T-598] claude 消費台帳の結線先を裁定した — 4 候補すべてを現状では不採用とし、結線しても削減施策の起票条件は解除されないと実測で示した (docs のみ、実装差分なし、branch worktree-dev-wave-t598-ledger-consumer)
---

## 本文

- 段 2 のプラン起草と段 3 の敵対 2 本 (いずれも codex `gpt-5.6-sol`、`reasoning=max`、read-only)
  が独立に **NO-GO** を返し、親の段 1 推奨を 2 箇所で反証した。設計判断は {{D:claude-ledger-consumer-wiring}}。
- **親の中心的な前提が誤りだった。** 親は「`output/task-runs/` の token 4 区分の欄が producer 不在で
  空いており、claude 台帳を差せば埋まる」と brief に書いた。段 2 が実コードで訂正 —
  `tokens` は `agent_run` event 専用 field であり、task 単位の欄は存在しない。最終 report の
  `0/0` は「token 欄が空」ではなく「agent event 自体が無い」の意味だった。
  **推奨の動機付けが崩れた上で残った推奨を、段 3 が改めて棄却した。**
- **親の実測の一般化も反証された。** 親は本 session 1 例から「worktree ごとに claude の project が
  分かれるので wave 単位に帰属できる」と一般化した。レンズ A が transcript 305 file の `cwd` を
  実際に集計し、145 file が worktree 以外の project 配下に worktree の作業記録を持ち、
  37 file が 1 file 内で作業場所を混在させ、3 file が worktree 間を移動していた。
  **本 wave 自身の transcript も、worktree に入る前後の記録を同一 file に持っていた。**
  帰属 key として使えるという主張は限定付きに格下げした。
- **本 wave の最重要の発見は、依頼文の前提そのものへの反証である。** [T-598] は
  「結線先が決まるまで削減施策は起票しない — before/after を測れないため」と書かれていた。
  レンズ A は、結線を決めても但し書きは解除されないことを示した。前後比較の成立には
  (1) 施策より前に前向き baseline を貯め終えること、(2) run ごとの介入 exposure と
  比較可能な層別を固定すること、(3) 効果量と分散から n を事前に決めること、
  (4) 欠測が施策の効きと相関しないこと、が要る。**遡及は不能**なので (1) は時間依存である。
- 段 3 レンズ B は、段 2 の推奨案の実装規模を再見積りし、production 差分だけで 645〜816 行
  (段 2 の自己申告 350〜500 行は過少) と判定した。D205 のプロトタイプ基準に照らして過大と裁定した。
- **実装子は起動していない。** 実装差分が無いため、変異 matrix と受入全走は本エントリの対象外である。
  docs の変更は `docs/README.md` の tools 地図へ 1 行 (この台帳が地図に載っておらず、
  発見可能性がゼロだった) のみ。
- 逐語 (段 2 プラン、段 3 の 2 レンズ、段 4 裁定) は `output/insights/2026-08-07_t598-ledger-consumer/`。

## 次の一手差分

### 更新

- [T-598] **P2・ユーザー裁定待ち (2026-08-07 wave で結線先を裁定済み)**:
  4 候補のうち (a) cron 定期観測・(c) claude 側 A/B・(d) task-run 台帳 v2 への結線は
  **いずれも不採用**とした ({{D:claude-ledger-consumer-wiring}})。第一候補は
  **(b) wave 単位の前向き収集** — canonical CLI の JSON 出力を wave ごとに 1 件 typed artifact として
  保存する形。**発効には dev-wave 側の契約行が要り、予算残 13 bytes では land できないため
  [T-597] に従属する。** 残るユーザー裁定は 4 件 —
  (U-1) 前向き baseline を今から貯め始めるか (貯めないと最初の施策は永久に before を持てない)、
  (U-2) 記録先を tracked にするか repo 外にするか (tracked は作業時間窓・走査件数・識別子が
  git 履歴へ撤回不能に残る)、(U-3) task-run 台帳の次世代を開くか、
  (U-4) 「削減施策の起票条件」を本文の但し書きから 4 条件へ置き換えてよいか。
  base: 386a19caf9c2becb7bcbcc930108ac7b35f7bcbb14e665f06b06e825e7d26df2
