---
description: マージ済みブランチと worktree を安全手順で掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 削除対象の限定 (ブランチ名/worktree 名)。省略時は全量棚卸しして安全なものだけ削除]
---

ブランチ・worktree の掃除を行う (クラス 2)。削除は不可逆に近いため、安全条件を満たすものだけを
消し、迷ったら残して報告する。対象限定の引数: $ARGUMENTS

## 1. 棚卸し (削除の前に全量を見る)

- `git worktree list` と `git branch -a` を列挙し、各ローカルブランチの `git rev-list --count
  main..<b>` (ahead) / `<b>..main` (behind) を出す
- 各 worktree の `git status --short` を確認する (未コミット差分の有無)
- ahead>0 のブランチは `git cherry main <b>` を出す。ahead だけでは取り残しを判定できない
  (rebase / cherry-pick 経由は ahead>0 のまま残る)。`+` 行が真の取り残しで、ファイルが main に
  無ければ取り込み漏れとして §5 で報告する
- `python3 tools/audit_dangling_commits.py --offrepo-root <runbook §7.2 の dir>`
  rc0削除/1§5報告・救出判断/2実行不能・削除停止。抑止行も rc0 で §5 へ

## 2. 安全条件 (満たさないものは削除せず報告に回す)

- ブランチ: **ahead=0 (main に取り込み済み) のみ削除**。`git branch -d` を使う (`-D` は使わない —
  -d が拒否したら取り込み漏れの兆候なので止まって報告)
- worktree: クリーン (未コミット差分なし) かつ HEAD が main に取り込み済みのもののみ。
  他セッション使用中の可能性 (自分が作っていない・最近更新) は推測せず `/proc/*/cwd` の
  readlink 走査で実測し、滞在プロセスあり・HEAD 直近 (目安 1h) は残す。迷ったらユーザー確認へ
- 自分がその worktree の中で作業している場合は、先に main checkout 側へ抜けてから操作する

## 3. worktree の削除手順 (F26)

submodule の gitlink を含む worktree は `git worktree remove` を使わず、F26 の安全手順を使う:

1. `git -C <worktree> checkout --detach` (ブランチを解放)
2. `git branch -d <branch>` (取り込み済み確認の上で)
3. ディレクトリを削除して `git worktree prune`

**`git submodule deinit` は使わない**。誤って実行した場合は
`git submodule update --init external/ccbench` で復元する。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らない。main が当該 commit を含むことを
`git log` で確認し、`action: keep` で抜け、本節の手動手順で畳む。
cwd 固定の背景セッション (ExitWorktree が no-op・cd 非持続) では、自分が居る
worktree の削除と prune を行わず、detach → branch -d → unlock まで実施して
残りを引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおりか
- `git submodule status` — main checkout の external/ccbench が `-` prefix なし (初期化済み) で
  pin されたコミットに一致すること
- `git status` がクリーンであること

## 5. ユーザー引き渡し (AI は push しない)

リモートブランチの削除 (`git push origin --delete <b>`) と main の push は行わず、対象を列挙して
ユーザーに提示する。削除しなかったブランチ・worktree はその理由 (ahead>0、dirty 等) と併せて報告する。

## 6. スキル自己改善 (発火条件つき)

今回の実行でスキル記載と実挙動の食い違い・新しい罠・手順不足を実測した場合だけ発火する。
発火したら `docs/skill-self-improvement.md` を読み、`cleanup-branches` の routing と commit 契約に従う。
発火しなければ本文を変更しない。
