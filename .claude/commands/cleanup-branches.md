---
description: マージ済みブランチと worktree を安全手順で掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 削除対象の限定 (ブランチ名/worktree 名)。省略時は全量棚卸しして安全なものだけ削除]
---

## 0. 最優先 mutation boundary

この command の受領から final response 完了までを cleanup 実行とする。成功・削除 0 件・罠発見・
検査赤・途中停止を含め、**本節は `CLAUDE.md` の一般クラス 2 規律より優先する**。クラス 2 は
repo 内容や履歴の変更権限を与えない。対象限定の引数: $ARGUMENTS

状態変更の allowlist は、(1) §2 を満たす既存 local branch の `git branch -d`、(2) §2 を満たし
所有確認済みの既存 worktree について §3 が定める detach・branch 解放・directory と対応 metadata の
撤去だけである。Codex はさらに real prune を許さない。§1〜§4 の読み取り検査と final での報告は
state mutation ではなく許可する。overlay は許可集合を狭めるだけで、本 command は再許可しない。

**未列挙の state mutation は目的・修復・一般クラス 2 規律を理由にしても禁止する。** とくに
branch/worktree の新規作成、surviving worktree の tracked/untracked file・index・設定の作成/編集、
handoff/worklog/spool/insight/failure/decision の作成、`git add/commit/amend/merge/rebase/cherry-pick/reset`、
同一実行内の自己改善、local main/commit graph/remote の変更、push を禁止する。repo file を変更しない
cleanup では project tests・build・provenance 監査も行わない。未確定事項・新しい罠・prompt 不備は
final で裁定候補として返し、実装・記録・commit は後から明示起動された別 dev-wave だけが行う。

削除は不可逆に近いので、以下の条件を満たすものだけ消し、迷ったら残して報告する。

## 1. 棚卸し (削除の前に全量を見る)

- §2 の安い条件が先、高い判定は通過対象のみ。
- `git worktree list` / `git branch -a` を列挙。全 local branch の
  `git rev-list --count --left-right <b>...main` (左=ahead 右=behind) と
  ahead>0 のみ `git cherry main <b>` を各 1 command に集約。
  rebase/cherry-pick 後も ahead>0。`+` 行は実在でなく内容判定
  (spool 不在は fold で正常)。未着地は §5 へ
- 除外対象含む全 worktree の `GIT_OPTIONAL_LOCKS=0 git status --short` を §4 用に保存。
  独立な読み取り並列可。読み取り・占有検査の起動親/wrapper (検査時も生存する親含む) の argv に対象 path 禁止。
  対象入り argv の全読み取り終了後、§2 の安い条件通過対象のみ §3 の占有検査へ。
- `python3 tools/audit_dangling_commits.py --offrepo-root <runbook §7.2 の dir>` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check --branch <b>...
  --retire-worktree <absolute-path>...` に渡す。rc0完全/2不完全/3通知/64usage・JSON は §5 へ

## 2. 安全条件 (満たさないものは削除せず報告に回す)

- 安い条件: local main / primary worktree、foreign・locked・所有不明は inventory/report のみ。
  worktree: HEAD 直近 (目安 1h) は保持、main 取込済み必須。
  branch: **ahead=0 (main 取込済み)** のみ `git branch -d` (`-D` 禁止)。
  -d 拒否は取込漏れの兆候、停止・報告
- 高い条件: 削除直前に §1 の status 空を再確認。§3 の占有・判定不能は保持。
  迷えばユーザー確認。対象内で作業中は先に main checkout へ退出

## 3. worktree の削除手順 (F26)

削除の直前に対象ごと `python3 tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、
rc1=占有/rc2=判定不能は停止。submodule は `git worktree remove` 禁止、F26 の手順にする:

1. `git -C <worktree> checkout --detach`
2. `git branch -d <branch>` (取り込み済み確認の上)
3. 全対象の 1・2・占有検査の後、dir 撤去は
   `python3 tools/cleanup_remove_dirs.py -- <絶対path>...` を前景 1 回 (setsid・nohup・& 禁止)。
   rc0 (全件 removed) 以外は停止。detach・branch 削除・prune は直列。rc0 後
   `git worktree prune --dry-run --verbose` の全候補＝今回所有確認済み対象なら
   `git worktree prune`。余分・不明候補時は real prune せず引渡し

**`git submodule deinit` は使わない**。誤実行時は追加修復せず停止し、必要な
`git submodule update --init external/ccbench` を final で引き渡す。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らない。main が当該 commit を含むことを
`git log` で確認し、`action: keep` で抜けて本節の手順で畳む。
cwd 固定の背景セッション (ExitWorktree が no-op・cd 非持続) や occupied/locked worktree は、
detach・unlock・branch/directory 削除・prune を行わず、そのまま引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおり
- `git submodule status` — main checkout の external/ccbench が `-` prefix なし (初期化済み) で
  pin に一致すること
- cleanup 前の status を保存し、surviving worktree・index・repo file に新しい差分が無い

## 5. ユーザー引き渡し (AI は push しない)

リモート branch の削除 (`git push origin --delete <b>`) と main の push は行わず、対象をユーザーへ列挙。
削除しなかった branch は理由 (ahead>0/dirty 等)・閉包・判定・救出期限、worktree は理由を報告する。

## 6. 自己改善候補の終端

記載と実挙動の食い違い・新しい罠・手順不足は `docs/skill-self-improvement.md` の routing 候補として
final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。
