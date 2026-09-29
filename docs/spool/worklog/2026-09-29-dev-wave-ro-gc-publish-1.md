---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-ro-gc-publish
seq: 1
title: [T-2911] VHash md_22: Cicada の read-only commit でも GC の公開を進める variant を小モデル・判定器・同時刻計測で確かめた (branch worktree-dev-wave-ro-gc-publish)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_22.txt` (一次資料 `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md`、設計判断 {{D:cicada-ro-commit-mainte-variant}}、失敗の再発 F100・F110・F139)。
- 結論 (一次資料 §0): 長い read-only tx を 1 本続けると stock Cicada の公開は 36/36 走で 0 回、ro commit の後始末で `mainte()` を呼ぶ variant で 289〜299 回 / 3 秒に戻る。throughput (計器なし) の variant/stock は長い ro で 1.56〜16.83、長い ro なしで 0.964〜1.073。小モデル 5 構成 × 6 腕で安全腕の違反 0 (適法な切断あり)、slot を tx の途中で動かす正例 2 本は違反。trace build 24 走で巡回 0 (上限 indeterminate)。長い ro の rts が境界を押さえる分 (約 13 ms) は固定 snapshot のまま残る。
- 重複起動: 同じ md_22 を 21:43 JST に先に始めた別 session (a97797) が、worktree・commit 0 のまま譲って停止した (譲り返し不要の連絡を受信)。
- ユーザーの手当て: 段 5 の dry-run で子 worktree へ `cd` し、session の全 Bash が隔離 guard に拒否された。復帰の `EnterWorktree(path)` は login の高負荷で 11 回時間切れ、ユーザーの `! cd` も拒否。ユーザーの許可 (「どうぞ抜けていいですよ」) で `ExitWorktree(keep)` して続けた (F100 の再発)。
- land の調整: 並行 land 調整役への `LAND-READY` 申告と、撤去の `CLEANUP-READY` 申告の手順を別 session から受けた。
- 棄却・限定した所見: 段 6 レビュー B の「陰性対照が前進あり = 反証」は refuted (段 4 の「発火」は GC 安全違反を指し、前進は対象外)。B の「smoke に時間見積りを入れる」は driver の要件にせず親が raw から計算。レビュー A の「rc=3 を受理している」は受理自体は先例どおり正しく、記録名 (`verdict_label`) だけ直した。焦点再レビュー 1 の partial 4 件は一次資料で範囲を限る (探索した 5 構成、slot 引上げの正例は途中の flag を要する条件付き、非 ro の write は実行時に数えていない、非同居は計測後に照合) として閉じた。
- 親の誤記: 長い ro なしの throughput 比の範囲を途中報告で 0.985〜1.073 と書き、焦点再レビュー 2 が 36 対の再計算で 0.964〜1.073 と指摘した。一次資料は訂正済み。
- main の取り込み (2026-09-30): VHash hot block wave と登録簿 7 file が衝突し、衝突の外でも両 wave が件数 pin を同じ新値へ書き換えていて git が 1 回分の加算しか残さなかった ({{F:same-value-pin-automerge}})。Codex author の fix 子が合成の最終形を書き (75 macro に合わせて pin を再導出)、merge commit afd33c945 で焦点走 8 (47 file) 緑、変異 B (MB3) の取り直しも KILLED。子を merge 途中の作業木へ投入して起動時に停止した (F815 の再発)。
- 子の工数: Codex plan 1・相談 2・author 2・review 2・fix 11 (単位 A 1、単位 B 10、うち 1 本は起動時停止の後に再投入)・焦点再レビュー 2・merge 合成監査 1。fix の 8 巡はレビュー所見ではなく、親の実機 (焦点走・smoke・verify・作図) で見つけた不具合への対応、1 巡は main 取り込みの合成。
- 計算ノード: 合計 6,610 s (約 1.84 node 時間)。内訳は一次資料 §12。受入全走は local main を取り込んだ tip で行う。

## 次の一手差分

### 完了

- [T-2911] Cicada の read-only commit で `mainte()` を呼ぶ variant (`patches/cicada-ro-gcflag-variant.patch`) を、小モデル (`tools/vhash_forwarding_model/ro_gc_publish.py`、5 構成 × 6 腕の全探索)・判定器 (trace build 24 走で巡回 0、上限 indeterminate)・同時刻計測 (公開回数・境界年齢・throughput、12 条件 × 6 対) で確かめ、(a) 公開の停止・遅れと (b) 長い ro の rts が境界を押さえる分を分けて一次資料に記録した ({{D:cicada-ro-commit-mainte-variant}})。
  remaining: none
  base: dd33da83dbc761475bad81b469c25f0390a0b9e15d5d809c3dcdc5ae75908503

### 新規

- {{T:vhash-baseline-ro-gcflag}} **P2・新規**: VHash の GC 側の比較相手 Cicada に ro-gcflag 修正 (`patches/cicada-ro-gcflag-variant.patch`) を入れるかを paper-story の次の版で決め、入れる場合は 3 秒より長い走行 (例 30 秒) で stock・variant の throughput 比と版の蓄積の走行時間依存を測る。stock Cicada の「read-only だけを続ける worker 1 本で GC の公開が止まる」欠陥を CCBench 上流へ提案するかは人間の判断 (D16/D18)。根拠: `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md` §0・§11・§13。
