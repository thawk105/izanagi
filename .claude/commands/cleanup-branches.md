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

## 2. 安全条件 (満たさないものは削除せず報告に回す)

- ブランチ: **ahead=0 (main に取り込み済み) のみ削除**。`git branch -d` を使う (`-D` は使わない —
  -d が拒否したら取り込み漏れの兆候なので止まって報告)
- worktree: クリーン (未コミット差分なし) かつ HEAD が main に取り込み済みのもののみ。
  他セッションが使用中の可能性がある worktree (自分が作っていない・最近更新されている) は
  ユーザーに確認してから
- 自分がその worktree の中で作業している場合は、先に main checkout 側へ抜けてから操作する

## 3. worktree の削除手順 (F26 の罠 2 件に対応)

submodule (external/ccbench) の gitlink を含む worktree は `git worktree remove` が**無条件拒否**
する (`--force` でも不可)。git 文書化済みの回避手順を使う:

1. `git -C <worktree> checkout --detach` (ブランチを解放)
2. `git branch -d <branch>` (取り込み済み確認の上で)
3. ディレクトリを削除して `git worktree prune`

**`git submodule deinit` は使わない** — submodule 登録 (`submodule.*` config) は worktree 間で
共有されており、main checkout の submodule まで未初期化になる (F26)。誤って実行した場合は
`git submodule update --init external/ccbench` で復元する (ローカル .git/modules から即時)。

セッション自身が EnterWorktree で作った worktree を畳む場合の注意: ExitWorktree の remove は、
コミットが main へ ff 済みでも「未取り込みで失われる」と誤警告することがある (2026-07-20 実測)。
`discard_changes: true` で押し切らず、main が当該コミットを含むことを `git log` で確認のうえ
`action: keep` で抜け、本節の手動手順 (detach → branch -d → 削除 → prune) で畳む。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおりか
- `git submodule status` — main checkout の external/ccbench が `-` prefix なし (初期化済み) で
  pin されたコミットに一致すること
- `git status` がクリーンであること

## 5. ユーザー引き渡し (AI は push しない)

リモートブランチの削除 (`git push origin --delete <b>`) と main の push は行わず、対象を列挙して
ユーザーに提示する。削除しなかったブランチ・worktree はその理由 (ahead>0、dirty 等) と併せて報告する。
記録はセッションの通常規律 (worklog) に従う。

## 6. スキル自己改善 (発火条件つき、/dev-wave 段 8 と同型)

今回の実行で**スキル記載と実挙動の食い違い・新しい罠・手順の不足を実測した場合のみ**発火する
(毎回の文面いじりはしない)。発火したら同セッション内で:

- 本スキルの該当節を実測に合わせて更新する
- 台帳との整合を同時に取る — 新しい罠は failures.md へ F 追記、既存 F26 の型の再発なら
  同エントリへ「再発: 日付」追記 (台帳の運用規則どおり)
- スキル編集 + 台帳追記を 1 コミットにまとめ、worklog に 1 行残す
