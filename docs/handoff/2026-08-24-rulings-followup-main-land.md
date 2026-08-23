# rulings 推奨8件の記録と main land
- 目的: 2026-08-24 の `$rulings all 説明付き` へのユーザー裁定「推奨通りで」を記録し local main へ land する
- 状態: 作業中
- 最終更新: 2026-08-24
- 基準コミット: 618c9236c843ef9689a10679cc50e0fc95339c49 (worktree-rulings-20260824-followup)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- AGENTS.md / CLAUDE.md / rulings skill / dispatcher、class 2 起動資料、全残 handoff、spool・hook・provenance 契約を確認した。
- 裁定対象10 IDの現本文 digestを `tools/spool_fold.py --base-digest` で取得した。
- 裁定は新規 decision 6件、D730 の既裁定適用による予算項3件の終端、push の人間手番として記録する。
- fold dry-run は `status=planned`。新規 decision は D749〜D754 に採番予定で、base digest 不一致はない。
- `check_codex_agents.py` 成功、`check_docs.py` 違反なし (既存 handoff 警告2件のみ)、
  `tools/run_tests.py orchestrator/tests/test_spool_fold.py -q` は 166 passed。

## 未完の作業と次の一手 (具体的に)

1. fragment と handoff を commit する。
2. commit 後 provenance 履歴監査、canonical acceptance、local main land を行う。
3. push は行わず、ユーザー手番として返す。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- T-1515 は T-1570 に従属するため同じ裁定で更新する。
- T-1583 / T-1591 / T-1617 と未採番 cleanup 手順候補は D730 を適用する。別々の実害を「同型3例」と数えない。
- main checkout の未追跡 `.codex/worktrees/` は既存状態であり、本 wave は触らない。
- fold は main に既存の `docs/spool/worklog/2026-08-24-cleanup-branches-codex-20260824-1.md` も
  同じ transaction で吸収する計画を表示した。既存 fragment は変更せず、標準 fold の対象として扱う。
