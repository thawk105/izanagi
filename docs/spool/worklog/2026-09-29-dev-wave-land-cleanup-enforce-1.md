---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-land-cleanup-enforce
seq: 1
title: dev-wave の land 後に worktree・branch が残る原因を 9/29 の約 35 wave で実測し、子木を退避してから撤去する経路・撤去中の main 前進の許容・branch の compare-and-delete・land 済み wave 木の終了時 hook を入れた (コード + test + docs + insight、branch worktree-dev-wave-land-cleanup-enforce)
---

## 本文

- 依頼: ユーザー「dev-waveをした後に、local mainにland成功しつつワークツリーやブランチを掃除せずに終了するやつが多いせいで、ワークツリーやブランチのごみが溜まりやすい。改善してくれ」。背景 job。一次資料 `output/insights/2026-09-29/dev-wave-land-cleanup-enforce/README.md`、判断は {{D:child-archived-removal}}、再発は F1036。
- 根拠にしたユーザー裁定 (memory、repo 未記録): 2026-09-29 md_14「自分で出したゴミは自分で掃除しろ」(自分の子 branch は bundle 退避して `-D`、撤去 tool が拒否しても残置報告で止めない) と同日「価値の小さい残骸は退避してから消す」。D2163 の却下案「非祖先は退避して撤去」をこの裁定に基づき条件つきで採った。
- 段構成: 撤去の受理集合を広げるので軽量版にせず、段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本 + 焦点再レビュー 1 本。段 3 の過剰レンズで plan の完全退避目録と途中再開 journal を削り、正しさレンズの must-fix 4 件 (per-worktree ref、land 前呼出し、`-D` の競合、証拠 dir の保管) を条件と手順へ取り込んだ。段 6 のレビュー A2 は NO-GO (wave 条件を削除直前に見直さない、stdin 無制限) → fix 1。
- 実装 commit: cb55395a0 (author 1)、0ad743c0b (author 2: Stop hook)、329456b6b (fix 1)、308091ea3 (fix 2: test のみ)。子木は作らず wave 木 1 本で Codex を直列に走らせた (F873)。
- 棄却・訂正: Stop hook を `hooks/` に置く当初案は guard_write の「hook 実行面」自己保護で Codex の書き込みが拒否された。D427 の別 worktree 経路は作業ツリーを増やし着地形 (F266) も難しいので、書込みを防護しない注意喚起として `tools/` に置いた (段 4 補遺、段 6 で攻撃させ異議なし)。B2 の「DW-O28 の `-D` 表記が実装と食い違う」は、DW-O28 が 996/997 bytes で追記不能かつ意味は同じ強制削除として不採用。焦点再レビューの「M14 は単一理由で落ちる」は変異の実測で覆った。
- 変異: probe (329456b6b) で M2・M14 が SURVIVED (test の穴) → fix 2 で test を足し、final (308091ea3) は 16/16 が事前登録と一致 (KILLED 15、等価変異 P0 SURVIVED、MISMATCH 0、直列 dispatch 68 分)。束ね経路は nodeid・`-k` を許さず、撤去 test が計算ノードで `lexical cwd is unavailable` の baseline 赤になって使えなかった。
- 焦点走: fix 2 後に 782 passed / 1 skipped (login)。受入全走はこの記録 commit の tip で行い、受領証は job dir (`/work/1/SFC/tanab/tmp/dev-wave-land-cleanup-enforce-2026-09-29/`) に残す (受入後にこの fragment を書き足さない)。
- 異常と救出: 変異の直列 probe 投入後に束ね経路の存在を記憶で知ったが、途中停止は孤児 job の hold を立てうる (runbook §7.6) ので止めずに完走させた。並行の login 自走は run_tests の Lustre 上の `git status` で 1 走 260 秒まで伸び、probe が先に完走したので計算ノード投入が無いことを確かめて停止し、注入中の変異を `git checkout --` で戻して blob を HEAD と照合した。wave 木に起動器の残差 commit 時の空の `index.lock` が残り、占有 0 を確かめて除いた。段 6 のレビュー 1 回目は review 段に `--reasoning` を渡して 2 本とも rc=2 で即死した (dry-run の省略)。
- 並走: 「cleanup branches」session (既存残骸の一括掃除) と land 調整役に、こちらは他の木を触らず自分の wave 木・branch・job dir だけを段 9 で撤去すると伝えた。
- 止まらない経路 (後送、insight §3): 調整役の撤去許可が来ないと止まる運用、ExitWorktree で main に戻ってから終わる session、amend による wave 本体の reflog rc=20、途中停止 (rc=30) からの再開。

## 次の一手差分
