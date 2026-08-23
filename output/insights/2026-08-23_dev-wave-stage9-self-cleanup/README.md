# dev-wave 段 9 の自己 worktree/branch 撤去経路 — 材料と逐語

branch: `worktree-dev-wave-stage9-self-cleanup`
base: `59ef288c` / local main 取り込み: `4261ec2d` (merge `116dc4d2`)

ユーザーの起票は「dev-wave を終えた後、main land まで成功したら自分のワークツリー・
ブランチを掃除するよう dev-wave を改善して」。

## 逐語 (`verbatim/`)

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief と、段 2 起動後に判明した既裁定との衝突の訂正 |
| `s2-plan.md` | 段 2 の実装プラン (read-only codex) |
| `s3-consult-sol.md` | 段 3 敵対相談・破壊安全性レンズ 12 所見 |
| `s3-consult-luna.md` | 段 3 敵対相談・正本整合レンズ 9 所見 |
| `s4-ruling.md` | 段 4 裁定と、実測による訂正 A1〜A6、段 6 裁定、comm allowlist の撤回、変異再照準 |
| `s6-review-sol.md` | 段 6 敵対レビュー・破壊安全性レンズ 11 所見 (NO-GO 判定) |
| `s6-review-luna.md` | 段 6 敵対レビュー・正本整合レンズ 4 所見 |
| `mutation-preregistered-nodes.json` | 変異走行前に凍結した期待 node (sha256 `01c1b9eaeef1577bf99ce29f861dcd9b828d64227d6f78c62913948fcc81a877`) |

## 主要な実測値

| 対象 | 値 |
|---|---|
| 着手時の滞留 | worktree 31 本 / branch 114 本 |
| dev-wave docs・command 内の撤去義務 | 0 件 (「撤去」「掃除」「畳む」「cleanup」で grep) |
| 入口 byte | 9,497 / 9,500 → 9,584 / 9,584 (条件 27 の 1 行 = 87 byte) |
| dev-wave docs L1 層 | 10,624 / 10,625 (変化なし) |
| dev-wave docs L1.5 層 | 9,565 / 9,566 (変化なし) |
| `DW-O28` | 983 / 1,000 byte |
| 占有検査の `unreachable.cwd_permission` | 2,020〜2,213 (他ユーザーの process 数) |
| 占有検査の `same_uid_cwd_unreachable` | 3 件 (`(sd-pam)` / `sshd` / `ssh-agent`)、dispatch 中は `nqs_shpd` が加わる |
| zombie による恒久 indeterminate | pid 1035937 (`State: Z`) で 2 回連続再現 |
| 焦点走 (3 file) | 628 passed / 3 skipped / rc=0 (2 回連続) |
| 変異 matrix | baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0 |
| codex 子 | 11 本 (plan 1 / consult 2 / author 1 / fix 6 / review 2)、全て `gpt-5.6-sol` / `xhigh` |
| launcher の `not_accepted` | 11 本中 3 本 (いずれも evidence の実体は健全) |

## この wave でだけ分かったこと

1. **worktree が 31 本溜まっていたのは怠慢ではない。** 占有検査がホスト上の zombie 1 本で
   恒久的に `indeterminate` を返し、`/cleanup-branches` §3 の「rc0 のみ進む」を誰も
   満たせなかった。掃除の自動化より先に、掃除の関門が通れることを確かめる必要があった。
2. **gate の述語は field の実在ではなく到達可能な値域で決まる。** 同じ wave で 2 度、
   実環境で満たせない述語を採用して撤回した。2 度目は「本プロジェクト自身が
   計算ノードへ dispatch している最中にだけ破れる」形だった。
3. **2 層防壁は下層が上層の破れを吸収する。** preflight の ancestry 検査を消しても
   テストは 1 件も落ちなかった。2 層目は `rm -rf` の後にしかないので、実害
   (worktree を消してから拒否する) は防げない。敵対レビュー 2 本では出ず、変異でだけ出た。
4. **この機体では変異 harness の KILLED 判定が使えない。** `--runner-mode local` の
   collection は dispatch 経由になり、`dispatch_compute.py` の成功時中継 4 KiB 上限で
   全 node 一覧が届かない。`--runner-mode dispatch` は baseline が `PARSE_ERROR` になる。
   期待 node を走行前に凍結し、probe 形式の観測と完全一致を親が照合する形で代替した。
