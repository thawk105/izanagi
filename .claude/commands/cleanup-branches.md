---
description: 古い・取込済みの branch と worktree を退避してから掃除する (submodule 罠対応、push 系はユーザー引き渡し)
argument-hint: [任意: 対象限定 (branch/worktree 名)。省略時は全量棚卸し]
---

## 0. 最優先 mutation boundary

この command の受領から final response 完了までを cleanup 実行とする。成功・削除 0 件・罠発見・
検査赤・途中停止を含め、**本節は `CLAUDE.md` の一般クラス 2 規律より優先する**。クラス 2 は
repo 内容や履歴の変更権限を与えない。対象限定の引数: $ARGUMENTS

状態変更の allowlist は、(1) §2 の削除対象 branch の `git branch -d`/`-D`、(2) §2 の撤去対象 worktree の
§3 の unlock・detach・branch 解放・ゴミ置き場への mv と実体削除・条件付き prune、(3) §2 の退避と
計画表・script・log の repo 外退避 dir への書込、(4) land 調整役 session への連絡だけである。
Codex はさらに real prune を許さない。§1〜§4 の読み取り検査と final での報告は
state mutation ではなく許可する。overlay は許可集合を狭めるだけで、本 command は再許可しない。

**未列挙の state mutation は目的・修復・一般クラス 2 規律を理由にしても禁止する。** とくに
branch/worktree の新規作成、surviving worktree の tracked/untracked file・index・設定の作成/編集、
handoff/worklog/spool/insight/failure/decision の作成、`git add/commit/amend/merge/rebase/cherry-pick/reset`、
同一実行内の自己改善、local main/commit graph/remote の変更、push を禁止する。repo file を変更しない
cleanup では project tests・build・provenance 監査も行わない。未確定事項・新しい罠・prompt 不備は
final で裁定候補として返し、実装・記録は明示起動された別 dev-wave だけが行う。

## 1. 棚卸し (削除の前に全量を見る)

- §2 の安い条件が先、高い判定は通過対象のみ。
- `git worktree list --porcelain` / `git branch -a` を列挙。全 local branch の
  `git rev-list --count --left-right <b>...main` (左=ahead 右=behind) と tip 時刻、
  ahead>0 のみ `git cherry main <b>` を各 1 command に集約。未着地は §5 の報告へ
- 除外対象含む全 worktree の `GIT_OPTIONAL_LOCKS=0 git status --short` を §4 用に保存。
  独立な読み取り並列可。読み取り・占有検査の起動親/wrapper (検査時も生存する親含む) の argv に対象 path 禁止。
  対象入り argv の全読み取り終了後、§2 の安い条件通過対象のみ §3 の占有検査へ。
- `python3 tools/audit_dangling_commits.py --offrepo-scan off` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check --branch <b>...
  --retire-worktree <absolute-path>...` に渡す。rc0完全/2不完全/3通知/64usage・JSON は退避 dir と §5 へ。
  rc2 は削除を止めない。worktree 200 本超は `git worktree list` が 8 秒上限を超え必ず rc2 なので、
  §3 の撤去後・branch 削除前に branch 候補だけで再走し、再び rc2 なら JSON を残して進む

## 2. 残す対象と退避 (残す対象以外は退避して消す)

- 残す: main / primary checkout、§3 の占有、HEAD・tip が直近 (目安: 稼働 wave の開始以降か 6h 以内) に
  動いた木・branch、稼働 session (ListAgents・投げ文) の主題の木・branch (棚卸し後に同系列の新 wave が
  起動すればその系列も)、現行 docs (phase doc・worklog 末尾の次の一手・decisions) が残すと名指しした branch
  (grep は main の tracked docs だけ、`main-worklog-*.md` 等の写しは数えない)、land 中の wave の branch、棚卸し後の新規
- 原本の置き場 (insight「証拠の所在」等が計測原本の所在と名指しする木、`dev-wave-jobs/` の投入木を含む) と
  未追跡 `output/` (`exploration/`・`env/`) の原本は、tar の写しが一致しても残して報告。登録だけ外す案も
  Git の再現手順と submodule を壊すので不可。写しへの移管は insight 更新を伴うので別 dev-wave (F1034)
- 他は施錠・ahead>0・未着地・dirty・rescue 判定不能でも消す。損失ゼロは要件でない (研究価値のない probe・
  お試しは失われてよい)。範囲は AI が Codex 2 役 (決定役・攻撃役の read-only consult) に掛けて決め、
  ユーザーへ確認・実行を回さない
- 消す前に repo 外 `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-<日付>/` へ退避: 削除 branch は 1 本の
  bundle (`^main`、`create`+`verify`+`list-heads` 一致)、main に無い detached HEAD と submodule HEAD
  (main 側 module repo に無いもの) は木ごとの bundle、追跡差分は `diff HEAD --binary`、未追跡は
  `ls-files -o --exclude-standard` と `output/` 下の ignored を tar (§3 の件数照合)
- ahead=0 は `git branch -d`、-d 拒否と ahead>0 は退避後に `-D`。名前と期待 tip の表で一括削除
- 高い条件: 削除直前に tip・HEAD が棚卸し時と同じで占有が無いことを再確認し、外れたら残す。
  対象内で作業中は先に main checkout へ退出

## 3. worktree の削除手順 (F26)

削除の直前に対象ごと `python3 tools/check_worktree_occupancy.py <worktree>`。rc0 のみ進み、
rc1=占有/rc2=判定不能は停止。submodule は `git worktree remove` 禁止、F26 の手順にする:

1. 施錠木は §2 の退避後に `git worktree unlock`。land 調整役 session がいれば
   CLEANUP-READY → OK を待つ → 撤去後に CLEANUP-DONE
2. `git -C <worktree> checkout --detach`、`git branch -d <branch>` (§2 の条件で `-D`)
3. 木を同じ file system のゴミ置き場 `/work/1/SFC/tanab/tmp/cleanup-trash-<日付>/` へ `mv` (rename で数秒/本)
4. 全 mv 後の `git worktree prune --dry-run --verbose` の全候補＝今回 mv した対象なら `git worktree prune` を 1 回。
   land 調整役がいれば PRUNE OK を待つ。他 wave の撤去途中の登録が混ざれば、持ち主が同意した分を足した
   集合と完全一致した時だけ打ち、それ以外は real prune せず引渡し
5. prune 後、ゴミ置き場の実体を `python3 tools/cleanup_remove_dirs.py -- <2 path>` で 2 本ずつ背景で消す
   (渡した全 path を同時に rm する。Lustre では多並列にしない、1 本 75〜250 秒)。rc0 以外は残して報告

撤去・削除 script は対象を本文に名指しする (計画 file から読む script は auto mode の判定が拒否する)。
拒否されてもユーザーへ実行を回さない。名指しの形へ直して再申請し、なお拒否なら迂回せず final で報告する。
退避の tar は `-C <worktree>` を `-T` の前に置き、`ls-files -o` の list 数を tar の非 dir entry 数が
下回れば撤去しない (F1034)。

**`git submodule deinit` は使わない**。誤実行時は追加修復せず停止し、必要な
`git submodule update --init external/ccbench` を final で引き渡す。正本は `docs/failures.md` F26。

ExitWorktree の remove を `discard_changes: true` で押し切らず、main が当該 commit を含むと
確認して `action: keep` で抜け、本節で畳む。
cwd 固定の背景セッションや occupied worktree は、
detach・unlock・branch/directory 削除・prune を行わず、そのまま引き渡す (F51)。

## 4. 事後検査

- `git worktree list` / `git branch` が期待どおり
- `git submodule status` — main checkout の external/ccbench が初期化済み (`-` なし) で pin 一致
- §1 の status と比べ、surviving worktree・index・repo file に新しい差分が無い

## 5. ユーザー引き渡し (AI は push しない)

remote branch 削除・main の push はせず対象を列挙。残した木・branch は理由 (占有・直近・主題・名指し・原本)、
消したものは bundle・tar の path・sha256・verify 結果と rescue JSON の path を示し、損失 commit の
台帳転記と原本の移管候補を別 dev-wave へ引き渡す。
push が毎回別 object の `loose object <sha> ... is corrupt` で落ち、名指し object が正常なら Lustre 読込失敗の疑い。
修復・fsck 前に primary の main checkout で送る範囲だけ pack 化してから再 push:
`printf 'main\n^origin/main\n' | git pack-objects --revs -q .git/objects/pack/pack`。
元の object は消さない (D1115 と非衝突)。全体 repack は 10 分超で不要。

## 6. 自己改善候補の終端

記載と実挙動の食い違い・新しい罠・手順不足は `docs/skill-self-improvement.md` の routing 候補として
final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。
