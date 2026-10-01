単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語 (特に最終行「計算ノードは使わない。」): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 本 wave の到達点: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/output/insights/2026-09-30/codex-astra-ultra/README.md
- 段 6 の裁定 (変異・焦点走の扱い): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-fix1-ruling.md

参照してよい repo (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/ (`docs/dev-wave/core.md` の DW-S04・DW-STOP、
`docs/dev-wave/operations.md` の DW-O23・DW-O27、`tools/acceptance_shards.py` の run_parallel、`tools/run_tests.py` の login admission)。

## 前置き

読み取り専用 sandbox、静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。
**sub-agent を spawn しない (spawn_agent 等の collaboration tool を使わない)。この起動器は委任した attempt を拒否する。**

# 依頼 — 決定レンズ: 親はどうすべきか決めよ

事実: 本 wave は実装・レビュー・fix・記録まで済み、wave branch に commit 済み。local main へ land するには受入全走が必須 (DW-S04: 縮小受入を land が
再検証した wave 以外は免除しない) で、受入は `tools/dev_wave_wait.py acceptance` → `tools/run_tests.py` の明示 shard 3 が
`tools.pegasus.dispatch_compute` 経由で**計算ノードへ投げる**。login に留める sanctioned な経路は無い (run_tests は余裕不足なら dispatch)。
変異 matrix も login では走らない。依頼の最終行は「計算ノードは使わない。」。

決めること: (A) 受入全走 (計算ノード 3 shard) を走らせて land する、(B) 計算ノードを使わず land しない (branch を commit 済みで残し、受入と変異は
ユーザー裁定待ちの項に置く)、(C) 他の案。依頼文の読み (最終行はどの行為を指すか: 生死確認・probe だけか、wave の受入・変異まで含むか)、
dev-wave の land 規律、この機体の他の依頼で受入が日常的に計算ノードを使っている事実、切り替えが着地しないことの影響 (他 wave はずっと sol・medium のまま)
を比べ、推奨を 1 つ選び、その理由と「やらない理由の最も強い形」を書け。

# 出力形式

markdown。「## 依頼文の読み」「## 各案の帰結」「## 推奨」「## やらない理由の最も強い形」「## 総括」。
