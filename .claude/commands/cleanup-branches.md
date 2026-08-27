---
description: マージ済みブランチと worktree を安全手順で掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 削除対象の限定 (ブランチ名/worktree 名)。省略時は全量棚卸しして安全なものだけ削除]
---

ブランチ・worktree の掃除 (クラス 2)。削除は不可逆に近いので、安全条件を満たすものだけ消し、
迷ったら残して報告する。対象限定の引数: $ARGUMENTS

## 1. 棚卸し (削除の前に全量を見る)

- `git worktree list` と `git branch -a` を列挙し、各ローカル branch の `git rev-list --count
  main..<b>` (ahead) / `<b>..main` (behind) を出す
- 各 worktree の `git status --short` (未コミット差分の有無)
- ahead>0 のブランチは `git cherry main <b>` を出す。ahead だけでは判定できない
  (rebase / cherry-pick は ahead>0 のまま残る)。`+` 行は実在でなく内容で判定する
  (spool の不在は fold で正常)。未着地なら §5 で報告
- `python3 tools/audit_dangling_commits.py --offrepo-root <runbook §7.2 の dir>` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check --branch <b>...
  --retire-worktree <absolute-path>...` に渡す。rc0完全/2不完全/3通知/64usage・JSON は §5 へ

## 2. 安全条件 (満たさないものは削除せず報告に回す)

- ブランチ: **ahead=0 (main に取り込み済み) のみ削除**。`git branch -d` を使う (`-D` は使わない —
  -d が拒否したら取り込み漏れの兆候なので止めて報告)
- worktree: クリーン (未コミット差分なし) かつ HEAD が main に取り込み済みのみ。
  占有は §3 で実測し、占有・判定不能・HEAD 直近 (目安 1h) は残す。迷ったらユーザー確認へ
- 自分がその worktree 内で作業中なら、先に main checkout 側へ抜けてから操作する

## 3. worktree の削除手順 (F26)

削除の直前に対象ごと `python3 tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、
rc1=占有/rc2=判定不能は停止。submodule は `git worktree remove` 禁止、F26 の手順にする:

1. `git -C <worktree> checkout --detach` (branch を解放)
2. `git branch -d <branch>` (取り込み済み確認の上)
3. ディレクトリを削除して `git worktree prune`

**`git submodule deinit` は使わない**。誤実行時は
`git submodule update --init external/ccbench` で復元。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らない。main が当該 commit を含むことを
`git log` で確認し、`action: keep` で抜けて本節の手順で畳む。
cwd 固定の背景セッション (ExitWorktree が no-op・cd 非持続) では、自分が居る
worktree の削除と prune をせず、detach → branch -d → unlock まで実施し
残りを引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおり
- `git submodule status` — main checkout の external/ccbench が `-` prefix なし (初期化済み) で
  pin に一致すること
- `git status` がクリーン

## 5. ユーザー引き渡し (AI は push しない)

リモート branch の削除 (`git push origin --delete <b>`) と main の push は行わず、対象をユーザーへ列挙。
削除しなかった branch は理由 (ahead>0/dirty 等)・閉包・判定・救出期限、worktree は理由を報告する。

## 6. スキル自己改善 (発火条件つき)

今回の実行でスキル記載と実挙動の食い違い・新しい罠・手順不足を実測した場合だけ発火する。
発火したら `docs/skill-self-improvement.md` を読み、`cleanup-branches` の routing と commit 契約に従う。
発火しなければ本文を変更しない。
