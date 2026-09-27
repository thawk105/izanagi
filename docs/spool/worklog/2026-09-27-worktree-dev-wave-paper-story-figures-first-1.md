---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-paper-story-figures-first
seq: 1
title: 論文ストーリーの版を図とグラフ中心で書く規則を README に入れた (ユーザー指示、次の版から適用、docs のみ、branch worktree-dev-wave-paper-story-figures-first)
---

## 本文

- ユーザー指示 (2026-09-27): 論文ストーリーを書くときは図やグラフを多く使う。文章量が多く全部を精読するのは難しく、
  図のほうが見てわかりやすいため。規則と理由は {{D:paper-story-figures-first}}、正本は `docs/paper-story/README.md` の
  「版を書くときの図の使い方」節。
- 実測: 本文に埋め込まれた図は 2026-07-10 版 3 枚、2026-08-23 版〜2026-09-26 版は毎版 2 枚 (P2-5 と P2-4 の図)。
  2026-09-26 版は旧 `fig1_` を埋め込んでおり、後継図 `fig1b_` (`figures/README.md` に登録済み) に触れていない (版は凍結物なので直さない。次の版は後継図を使う)。
- dev-wave 軽量版 (docs のみ、子なし)。開始 gate rc=0、`python3 tools/check_docs.py` rc=0。凍結済みの版・図は 1 byte も変えていない。

## 次の一手差分
