# 依頼の逐語 (2026-09-21 08:2x JST、ユーザーの直接メッセージ = `/dev-wave` の引数)

[T-2824] (D2194 項 5、控え /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md 項 5、一次資料
  output/insights/2026-09-20/t2810-g1-launch-validation/README.md §5・§8) 未発効候補 output/s8b-freeze-candidates/holdout_freeze.v2.g1.json
  だけを削除する commit を作る。着手直前の local main から fresh worktree。scan 除外は不変、B-10 freeze-tree pin の対象外、G/A/X・floor_source
  の bytes 不変、V2_CANDIDATE_REL (orchestrator/campaign/s8b_holdout_freeze.py) の定数と create-only 拒否は消さない。削除後に loader の
  load、historical reverify_published_freeze、live launch_validate、docs/phase3-8b-restart-runbook.md §2 P3 (g1 / v1 path) を再実測し、held
  真値 _ACTIVATED_G1_REFUSALS を現在値に更新する (test 追随は Codex author)。帰結 (再生成で hit が復活しうる、候補 bytes と来歴は X2 の履歴
  blob と世代文書で保持) を insight に記録する。live の policy 拒否 ([T-2812] 系) は本 wave で解消しない・触らない。規律 2
  を緩めない。本題だけ。gate・台帳の追加は scope 外。

(会話中のユーザー発話は他に「どう？」(進捗確認) の 1 件だけ。)
