---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t1851-leftover-audit
seq: 1
title: T-1851 の取り残し worktree dev-wave-t1851-c3c-official-floor の tracked 外 file 3,485 件を T-1851 / T-2698 の正典と照合し、正典に無い研究記録 216 件 (claims 3・submissions の小 file 57・無視対象の job-staging 156) を repo 外の job dir へ sha256 付きで保全した — lock・worktree・branch は不変 (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-t1851-leftover-audit)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、台帳 ID 未起票): 取り残し worktree の未追跡 `output/claims/` と floor submissions 3 件を [T-1851] / [T-2698] の正典と照合し、正典に無い研究記録だけを repo 外へ sha256 付きで保全、照合結果を insight 1 本に記録する。lock 解除・worktree と branch の削除・自動撤去の拡大・gate / 検査 / 台帳の追加はしない。記録 = `output/insights/2026-09-22/t1851-leftover-worktree-audit/README.md`、保全先 = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-leftover-audit/preserved/`。
- 依頼の前提を 1 点広げた (段 1 の親裁定 P1): 対象 worktree の tracked 外 file の約 3 割は `.gitignore` の無視対象で `git status` に出ず、同じ 3 走行の job-staging 3 dir (受領証・失敗記録・環境記録) が依頼文にも T-2724 §4 の dirty 内訳にも入っていなかった。撤去時に黙って失われる位置なので照合・保全に含めた。
- 軽量版 (DW-C00): 設計択一・正しさ防壁・受理集合に触れない docs のみ。段 2・3 と実装子は省き、一次資料からの再抽出を含むので段 6 の独立 read-only レビュー 1 本を残した。実装面の差分はゼロで変異 matrix は免除。
- 対象 worktree へは git を向けなかった (隔離 session の Bash guard が `git -C` と変数入りの find・heredoc を拒否する)。列挙・hash・保全は job dir `scripts/` の Python で行い、script は repo に入れていない。
- insight の初稿に「T-2814 の原本判定は掃除手順に入っていない」と書いたが、T-2814 は 2026-09-21 (1775) に着地済みで誤りだった。記録前に訂正し、`/cleanup-branches` §2 が引く「証拠の所在」節を insight に設けた。
- submodule 初期化の 1 回目は `runtime-io-failure` (`update-no-fetch`) で落ち、同じ command の再実行で通った。
- 工数: codex 子 1 本 (段 6 review)。計算ノードは受入 1 回だけ (2026-09-21 の確認ライン 2 node 時間を下回る)。

## 次の一手差分
