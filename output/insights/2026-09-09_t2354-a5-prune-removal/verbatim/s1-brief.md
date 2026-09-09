# 段 1 brief — [T-2354] A-5 job body の共有 gitdir prune 撤去

## 研究前進

土台の修理である。止めている研究の実測は **同一 checkout から複数 job を出す Pegasus 測定**
(A-5 の 2 workload、B-10 の 3 job、T-1998 launcher が再利用する同じ job body)。
実測で失われた値: 2026-09-07 に A-5 balanced が 8 genome を commit した後、T-2266 が 8 点中
6 / 6 / 4 点を commit した後に、いずれも `fatal: not a git repository` で落ちた (F251 再発)。
最小差分は job 本体の終了処理から共有 submodule gitdir への
`git worktree prune --expire now` を外すこと。完了判定は (a) A-5 job body に共有 gitdir への
prune が 1 箇所も無い、(b) 契約テストが新しい受理形 (prune 不在) を固定する、
(c) 兄弟 job の「別ノードにあり手元には存在しない」worktree 登録が A-5 の終了処理を跨いで
生き残ることを、実 git fixture の実走で示す。

## 確定済みユーザー裁定 (D1700、2026-09-07 /rulings 第 12 回)

- job 本体の共有 gitdir への `worktree prune --expire now` をやめ、**自 path への
  `worktree remove --force` だけに限る** (B-10 job body が既に採っている形)。
- remove が失敗したときは他 job の登録を prune せず、**残置を明示**して後続の安全な掃除へ回す。
- **投入器を workload ごとの checkout に分ける案は却下済み**。依頼文はこの二択を再掲しているが、
  裁定は実装方向まで確定しているので二択へ戻さない (DW-S04)。

## scope

- in: `tools/pegasus/a5_second_boot_backoff_sweep.sh` の `remove_worktrees()` から prune を外し、
  remove 失敗時の残置を receipt に明示する。`orchestrator/tests/test_a5_second_boot_job_contract.py`
  の受理形を更新し、prune 不在と自 path remove の挙動を検査する。
- out: 投入器 (`submit_a5_second_boot_backoff_sweep.sh`) の分割、B-10 job body の変更、
  登録簿 schema の変更、汎用の worktree 掃除機構、仮想リスク向けの gate / 台帳 / 一般化、
  Pegasus への実測投入 (本 wave は計測を行わない)。

## 不変条件

- 規律 2 を緩めない。既存テストの期待値を「通すため」に反転・緩和・skip・削除しない。
  受理形の変更は本件が意図する 1 点 (prune 正例 → prune 不在) に限る。
- 掃除の失敗を成功と report しない。remove 失敗時の rc 伝播 (`cleanup_worktrees` → job rc)
  と `write_failure_receipt` の発火条件を現行のまま保つ。
- 内側 timeout 予算の総和 + 終了余裕 < 外側 walltime の関係を壊さない
  (`WORKTREE_CLEANUP_CAP_S` を含む budget assert は job body 冒頭にある)。
- 新しい Pegasus 実行体を作らない (F660)。登録簿 entry の path・class を変えない。

## 変更面 (実アンカー)

| path | 行 | 現状 | 変更 |
|---|---|---|---|
| `tools/pegasus/a5_second_boot_backoff_sweep.sh` | 123-170 | `remove_worktrees()`: ccbench remove → repo remove → **共有 gitdir prune** → `printf '%s\nprune_rc=%s\n'` | prune ブロック撤去、receipt 書式改訂 |
| `orchestrator/tests/test_a5_second_boot_job_contract.py` | 297 | `assert 'git -C "$CCBENCH_BASE" worktree prune --expire now' in normalized_job` | 不在 assert へ反転 |
| `orchestrator/tests/test_a5_second_boot_job_contract.py` | 298 | `assert "printf '%s\\nprune_rc=%s\\n'" in job` | 新 receipt 書式へ |
| (新規 test) | — | A-5 の cleanup を実 git fixture で実走する検査は無い | B-10 の `test_b10_job_exit_trap_removes_worktree_on_normal_and_abnormal_exit` と同型を 1 本足す |

## pin 閉包 (DW-O09 / O10)

- job script の sha256 `0ef4d41ee1dd…` の hit は `output/insights/` の過去 submit 記録と
  reservation のみ = 歴史記録。live な golden・FROZEN_MANIFEST・generator hash pin は無い。
- producer が書く受入対象 file: `env/ccbench-worktree-remove.{stdout,stderr}`,
  `env/repo-worktree-remove.{stdout,stderr}`, `env/ccbench-worktree-prune.{stdout,stderr}` (撤去対象),
  `env/worktree-remove.rc`。repo 内 consumer は上記 2 テストだけ
  (`test_backoff_extended_sweep.py:1785` は B-10 の同名 file で無関係)。
- `tools/pegasus/admission_registry.json` は path を key にし sha256 を pin しない → entry 変更不要。
  F660 は新規実行体の話であり、本 wave は既存登録済み実行体の本文編集なので発火しない。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1)** `env/worktree-remove.rc` は B-10 と同じ 1 行 (`<cleanup_rc>`) へ揃えるのではなく、
  remove 失敗時に残置 path を機械可読に明示する行を残す。D1700 の「残置を明示」を満たす最小形は
  stderr だけで足りるのか、receipt に専用 field が要るのかを攻撃せよ。
- **(P1)** repo 側 worktree (`$REPO_BASE`/`$JOB_REPO`) の remove は現状どおり残す。
  prune 撤去の対象は ccbench 側の共有 gitdir だけである、という読みが正しいかを攻撃せよ。
- **(P1)** 契約テストへ実 git fixture の実走検査を 1 本足すのは、本件の直接の正例・負例であって
  「仮想リスク向けの検査追加」ではない、という線引きを攻撃せよ。

## 成果物の形

コード 1 file + テスト 1 file の変更、insight (逐語 + 変異台帳)、worklog / decisions fragment。
Pegasus 実測なし。

## 分割方針

編集面は 2 file・素集合でないため実装は Codex `role=author` 1 単位。段 2 plan 1 本、
段 3 敵対相談 2 本 (レンズ別)、段 6 敵対レビュー 2 本 + 変異 matrix + 受入全走。
受理集合が変わる wave なので軽量版にせず段 2・3・6 review を省かない (DW-C00)。

## DW-G05 成果物影響

放置すると、同じ checkout の gitdir を共有する複数 job のうち後に終わる側が、計測値を commit
した後・finalizer 前に必ず落ちる。certified 選択の材料となる測定 (A-5 の 8 genome、B-10 の
格子点) が試行台帳から欠落し、再投入の計算資源を二重に使う。

## 受入・実測環境

受入全走は wave worktree の login node 上で `tools/dev_wave_wait.py acceptance`。
変異本走は `--runner-mode dispatch`。Pegasus への計測 job 投入は行わない。
