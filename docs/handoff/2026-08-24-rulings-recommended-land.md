# 2026-08-24 rulings 推奨案 5 件の記録・main land
- 目的: ユーザー裁定「推奨通り」を5件へ反映し、spool foldを経てlocal mainへlandする
- 状態: 作業中
- 最終更新: 2026-08-24 01:12 JST
- 基準コミット: 402a5752b9cf59a769f5b5af17e56b67a68190f1 (worktree: worktree-rulings-20260824-recommended)

## 完了した中間成果

- `rulings` Skillと共通dispatcherに従い、裁定待ちを再収集した。
- ユーザー裁定は、床値救出3件とknown-violation 2件について直前提示の推奨案を採用するもの。
- 元項目は `worktree-dev-wave-t1484-floor-restart-registry` と
  `worktree-dev-wave-known-violation-review-20260823` の未land fragmentにある。
- 他waveのplaceholder slugは参照できないため、両waveがfoldされ実T番号を得るまで記録を待つ。

## 未完の作業と次の一手

1. 両元waveのlocal main landを確認する。
2. 確定T番号と本文digestを取得し、5件を裁定済みへ更新するworklog fragmentと設計判断fragmentを書く。
3. `check_docs.py`、`check_codex_agents.py`、spool dry-run、関連検査、provenanceを通す。
4. 受入・landを行いlocal mainへfoldする。pushは行わない。

## 落とし穴・気づき

- T-1597はD730が既に処遇を決めているため今回の5件に含めない。
- 元waveのworktreeを直接編集しない。生きたセッションとユーザー変更を保護する。
- mainの未追跡 `.codex/worktrees/` は既存のCodex作業木であり触れない。
