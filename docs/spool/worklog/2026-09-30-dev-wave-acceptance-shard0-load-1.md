---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-acceptance-shard0-load
seq: 1
title: 受入 shard-0 の最忙 worker の短縮 (md_6) — T-080 共有 base の先行構築を実装し同時刻対照 2 対を取ったが割れ、事前登録どおり実装は land せず記録だけ land する (docs + insight、実装は branch worktree-dev-wave-acceptance-shard0-load に保存)
---

## 本文

- 一次資料: `output/insights/2026-09-30/acceptance-shard0-load/README.md`。判断は {{D:t080-base-prewarm-not-landed}}、対照で見つけた実装の欠陥は {{F:prewarm-copied-consumer-timeout}}。
- ユーザー裁定 (2026-09-30、本 wave 中): 計算が 2 node 時間を超える見込みを 2 回確認した。1 回目 (約 2.4) は「推奨通り、測定はジョブを分割して高速に」、正式受入を対照に兼ねられないと分かって約 2.7 で再確認したら「賢く、並列で高速に main land まで」、実装の欠陥で対照を取り直す約 4.8 は「撮り直しはいい、ジョブは可能な限り分割して高速に」。実使用は計算ノードの job Elapse 合計 5.16 node 時間 (land 用の縮小受入は別)。
- 段 3 相談 1 本・段 6 敵対レビュー 2 本・焦点再レビュー 1 本。段 6 は両レビューとも NO-GO で fix 1 巡、その後対照の実走で出た欠陥に fix 2 巡目 (F4)、新設 test の helper の競合に F5。変異 6 本は最終 tip で全 KILLED (期待 node と完全一致)。
- 棄却: 段 6 review A 所見 6 (写しの撤去後に consumer が実 repo 複製へ進む順序) は、finish が全 worker の終了後にしか走らないので refuted。
- 異常: 変異元 clone の作成で完全 SHA を打ち間違えて 1 回中止した (途中の clone は job dir に残置)。Bash guard が dir 名 `source` を shell の `source` と読んで削除を拒否したので別名 (`mutsrc`) で作り直した。計測 runner の子木で F1078 が 3 回再発した (成果物は repo 外なので影響なし)。受入 1 走の非帰属赤 2 件 (`test_b5_contrast_launch.py` の時間依存の待ちループ、`test_plot_b7_fixed5_regression.py` の文字枠の重なり) は本 wave の差分が到達しないことを確かめ、どちらも無効にした対照の中だけで起きた。
- 実装を land しないので、記録は main から切った別の木 (branch `record-dev-wave-acceptance-shard0-load`) で作った (同じ木で branch を切り替えると撤去 tool が拒否するため)。

## 次の一手差分
