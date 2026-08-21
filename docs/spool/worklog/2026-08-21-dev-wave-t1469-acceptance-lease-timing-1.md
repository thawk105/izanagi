---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1469-acceptance-lease-timing
seq: 1
title: [T-1469] 受入lease claim待ちのstaleness事後定量化を実施した (docsのみ、branch worktree-dev-wave-t1469-acceptance-lease-timing)
---

## 本文

- command引数の「開始直後にCodex roster・snapshot・worktree/lease・handoff・canonical worklog
  を照合」を実行し、重複稼働なし・owner不明なしを確認してから着手した (ListAgentsの8 peer
  session、`docs/handoff/`の残1件はT-1473で無関係、`git worktree list`にT-1469関連なし)。
- DW-C00の軽量既定 (設計択一が割れない・正しさ防壁に触れない・受理集合が変わらない) に
  該当すると判断し、段2 (codexプラン起草)・段3 (敵対相談) を省略した (P1、攻撃対象)。
  実装面ゼロのためD95によりCodex子も不要と判断した。
- 母集団選定でclean/多試行の線引きが必要だった: `acceptance-run.pid`を持つ11 wave dirのうち、
  `acceptance-child-N.log`が複数本 (再試行あり) の4件は、単一のpid mtimeがどの試行に対応するか
  一次資料だけから一意に確定できないと実際に確認し (`dev-wave-t1444-pegasus-env-tag`でpid mtimeが
  attempt-7の受理より後・attempt-8開始より前に位置する等)、機械的な一貫性のため4件とも除外した
  (P1、insight 1.2節に詳細)。
- 当初`git log`のcommitter dateで「main advanceの検出」を試みたが、commit日時が
  「wave branch上でのcommit作成時刻」であり「main反映(land)時刻」と一致しない場合があると
  気づき、`git reflog show main`(mainブランチ自身へのref更新だけを記録する、より正確な一次資料)
  に切り替えた。この訂正の経緯はinsight本文に残していないため、本項目としてここに記録する。
- staleの判定規則 (待ち区間内に他waveのland 1件以上で stale) は {{D:lease-preclaim-staleness-evidence}}
  の理由欄に整合させた。この規則の是非自体は敵対検証していない (P2、insightの規律で
  「反実仮想の定量化である」ことは明記した)。
- 詳細な数値・分布・限界は `output/insights/2026-08-21_t1469-acceptance-lease-timing/README.md`
  に記録した (git管理下、本entryでの逐語再掲はしない)。

## 次の一手差分

### 完了

- [T-1469] claim前merge・受入テストのstaleness事後定量化を完了し、insightへ記録した。
  D631の再訪条件は不成立 ({{D:lease-preclaim-staleness-evidence}})。
  remaining: none
  base: 816650116ad6e1fd9e0f02f32bd7d6236107416e1ab75edd170601ac9b481718
