単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語 (特に最終行「計算ノードは使わない。」): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 本 wave の到達点: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/output/insights/2026-09-30/codex-astra-ultra/README.md

参照してよい repo (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/ (`docs/dev-wave/core.md` の DW-S04・DW-STOP、
`tools/acceptance_shards.py`、`docs/decisions.md` で「計算ノード」「node 時間」「受入」を grep)。

## 前置き

読み取り専用 sandbox、静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。
**sub-agent を spawn しない (spawn_agent 等の collaboration tool を使わない)。この起動器は委任した attempt を拒否する。**

# 依頼 — 攻撃レンズ: 「受入全走 (計算ノード 3 shard) を走らせて land する」案 (A) を通してはいけない理由を探せ

事実: 受入全走は `tools/run_tests.py` の明示 shard 3 が `tools.pegasus.dispatch_compute` 経由で計算ノードへ投げる。依頼の最終行は「計算ノードは使わない。」。
land には受入全走が必須 (DW-S04)。

案 (A) を攻撃せよ: 依頼文の最終行が受入まで含むと読むべき根拠、ユーザーの直接指示を AI が狭く解釈して計算資源を使うことの危険、
land しないこと (案 B) の実害が小さい根拠 (切り替えは docs が local main に着地するまで他 wave に効かないが、研究・成果物の値は変わらない等)、
逆に (B) を採ると何が壊れるか。**攻撃が成立しなかった項目は正直にそう書け。全項目を無理に成立させるな。**

# 出力形式

markdown。「## 攻撃 (成立/不成立を明記)」「## (B) の実害」「## 総括」。
