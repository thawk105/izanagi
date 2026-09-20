---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-cleanup-backup-loss-record
seq: 1
title: /cleanup-branches (worktree 7 撤去・branch 180 削除) の後、引き渡し script の退避 tar が空のまま worktree 4 本を撤去し K2 loop の campaign 原本を失った事故を記録した (docs のみ、branch worktree-dev-wave-cleanup-backup-loss-record)
---

## 本文

- 同日 16:26 JST の `/cleanup-branches` (Claude、背景 job): worktree 85 本・local branch 323 本を棚卸しし、ahead=0 の branch 180 本を
  `-d`、unlocked・main 取込済み・clean・非占有の worktree 7 本を撤去 (巻き添え 0、dangling 監査 0 件、救出検査 rc=2 は
  fig11-a6 wave の自己撤去と verify-pack timeout 由来で損失 3 commit は全部 reflog 専用の amend 前版・内容着地済み)。
  未削除は ahead>0 の 132 本と、locked 31・dirty 4・Codex 子木 30 の worktree。棚卸し記録は repo 外
  `/work/1/SFC/tanab/cleanup-20260920/inventory/`。
- ユーザー手番 (remote): `origin/main-check`・`origin/_localmain_check` は GitHub 側に既に無く `git remote prune origin` で消す形が正しかった
  (script は push --delete を試みて `remote ref does not exist`)。残骸 remote-tracking ref 5 本をユーザーが `update-ref -d`。
  うち `refs/remotes/localmain` (d46c40658、main 未取込 7 commit) は t2075 wave の古い写しで、code 修正は main に同一 patch、insight 3 file は
  移設先 `output/insights/2026-09-01/t2075-layer3-bypass-hard-failure/` と byte 同一、fragment は fold 済み — 損失なし。main は
  ユーザーが push 済み (origin/main = main)。
- ユーザー「私は何のコマンドを打てば良い？スクリプト作ってくれたら助かる」→ Claude が repo 外に `handoff.sh` (remote 掃除・push・
  退避付き撤去、1 件ずつ y/N) と候補 list 3 本を用意。**19:25 JST、候補 1 (dirty 4 本) の撤去で退避 tar が 0 entry のまま撤去**
  → {{F:cleanup-backup-tar-empty}}。失ったのは K2 loop round 3 の campaign 原本全部、round 2 の AO と campaign.lock、roundtrip (t2588) の
  原本全部。round 2 の WAL・loop_state・digest・受領証は t2746 job dir の `scratch-campaign/` 写しが sha256 一致で残り、t2698 は wave 自身の
  `run-backup/` bundle で無傷。損失表・照合・原因の再現は `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`。
- ユーザー裁定「記録していいよ」(19:3x JST) で本 wave (docs のみ、実装差分ゼロ、Codex 段なし) を起動。script は同日 fail-closed に修正済み
  (rm 前に list と tar の entry 数を照合)。候補 2 (Codex 子木 9 本)・候補 3 (古い locked 9 本) は未撤去のまま、続行はユーザー判断。
- 同じ script の別バグ 2 件 (list の相対 path が `cd` 後に解決できず「撤去 0 件」、`while read` の stdin を `[y/N]` の `read` が食い
  1 本おきに skip) も同日修正。いずれも撤去には至っていない。
- 4 insight README (round3 / t2746 / t2588 / t2698) に erratum 節を追記し、「原本は submit-tree に残る」を現況 (消失 / 写し / bundle) に改めた。

## 次の一手差分

### 新規

- {{T:cleanup-submit-tree-originals}} **P2・新規**: `/cleanup-branches` §2・§3 に (a) submit-tree / wave worktree の未追跡 `output/`
  (`exploration/`・`env/`) を候補にする前に該当 wave の insight「証拠の所在」節で repo 外原本かを確かめる、(b) 退避 tar の
  `-C` 順と entry 数の検算を撤去の前提にする、を書く (command 改訂は同 command §0/§6 により別 wave。{{F:cleanup-backup-tar-empty}})。
- {{T:k2-loop-originals-lost-downstream}} **P2・新規**: K2 loop round 2 / 3 / roundtrip の campaign 原本消失 ({{F:cleanup-backup-tar-empty}}) が
  次巡 (round 3 の `loop_state.json` からの再開) と論文ストーリー §8 B-6 / fig12 の provenance 記述に及ぼす影響を評価し、checkpoint を
  派生物 (`materials/`、`layer3_report.json`) から再構成するか別走にするかをユーザー裁定に載せる。
