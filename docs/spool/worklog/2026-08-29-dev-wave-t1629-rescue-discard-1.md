---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1629-rescue-discard
seq: 1
title: 救出候補 T-1629 批准機構の 7 file を全件破棄と裁定し、worktree 3 本を畳んだ (docs、branch worktree-dev-wave-t1629-rescue-discard、実装面差分ゼロ)
---

## 本文

- ユーザーの救出依頼は「main へ一度も着地していない 7 file」という前提で来たが、**前提は誤り
  だった**。jsonl 1 件を除く 6 file は 2026-08-27 に `5107ced3c` (feat) で main へ着地し、
  `abd3390af` と `647acd2d7` で修正され、その後 `c986c1459`「merge: main を取り込み、
  批准機構の撤去を 27 path 世界へ広げる」で main から削除されていた。3 commit とも main の祖先である。
- 前提が誤って見えた原因は `git log --oneline --diff-filter=D --all -- <paths>` が 0 件を返した
  ことにある。path 限定 `git log` は既定で merge commit の差分を出さないため、merge 内でだけ
  起きた削除は完全に不可視になる。F560 と同一の型なので再発として記録した。
- 機構そのものは D1139「enforcement source closure の批准突き合わせを廃止する」(ユーザー裁定) が
  廃止済みである。同裁定は D905 を明示的に上書きし「命じられた実行主体は今後も作らない」と書き、
  **却下した選択肢に「批准行の発行を署名 broker で機械化する (D905 が命じ、別 wave が実装済み)」を
  名指しで挙げている**。今回の救出候補 3 本はその実装そのものである。よって全件破棄と裁定した
  ({{D:ratification-rescue-discard}})。
- file 1 件ごとの処遇と理由は {{D:ratification-rescue-discard}} の表に置いた。7 file すべて破棄で、
  内訳は ed25519 検証 2 件、受領証 2 件と空 jsonl 1 件、broker 2 件である。
- worktree 内の untracked copy はいずれも着地版より前の段 5 author 草稿だった。行数は
  ed25519_verify 138 (着地版 144)、受領証 474 (同 1035)、broker 250 (同 1039)。
  `enforcement-source-ratification-receipts.v2.jsonl` は 0 byte の空 file で、7 件のうち唯一
  一度も着地していないが、内容がないため救出対象にならない。
- 撤去前の損失確認は 3 経路で行った。(a) `check_branch_rescue.py` の削除損失閉包が
  commit 0 件・complete=true。(b) 3 worktree の HEAD `9463bcbcb` が main の祖先。
  (c) untracked 7 file が `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/` の同名 path と
  sha256 一致で既に repo 外へ退避されている。よって撤去による損失はゼロである。
- `check_branch_rescue.py` の rc は 2 (不完全) だった。原因は retention phase の `verify-pack`
  timeout 2 件と、実行中に他 wave が root inventory を動かした churn 1 件で、いずれも
  object retention の可視化が不完全という意味である。損失検出そのものは complete=true であり、
  かつ損失 commit が 0 件なので retention の可視化は成立しても使い道がない。`--timeout-seconds`
  の上限は 900、`--assessment-timeout-seconds` の上限は 60 で、上げても timeout は解消しなかった。
- 変異 harness は 2 本稼働していたが、`--repo` はいずれも自分の worktree
  (t2033-axis1-retake、t2061-wal-admission) で、主 checkout は観測対象外だった。
  harness の clean-tree 走査は `--repo` 配下限定である。撤去禁止条件には当たらない。
- 撤去手順は F26 に従った。3 worktree とも `external/ccbench` を持つため
  `git worktree remove` を使わず、unlock → `rm -rf` → prune とした。`git worktree prune
  --dry-run --verbose` の候補は 3 対象と完全一致し、他セッションの跡は混ざらなかった。
- 撤去直前の `check_worktree_occupancy.py` は 3 本とも rc=0 unoccupied で、scanned は
  2248-2251 だった。事後検査では t1629 の残骸ゼロ、`git submodule status` は pin 一致で
  `-` prefix なし、主 checkout の `git status --short` は撤去前と無変化だった。
- `/cleanup-branches` の手順に 2 件の食い違いを見つけたので、段 8 の routing 候補として
  最終報告に挙げた。§2 / §3 の「locked worktree は引き渡しのみ」が、理由文なし lock を全件に
  付ける codex worktree の現状では全撤去を止める点と、§0 の全面 mutation 禁止 overlay が
  §2〜§3 だけを引用した他 command の記録義務と衝突する点である。
- 本 wave は実装面の差分ゼロにつき変異 matrix を免除した (D95 決定 2)。受入全走は免除しない。

## 次の一手差分

### 新規

- {{T:ratification-ledger-leftover}} **P3・新規**: D1139 が批准突き合わせを廃止した後も
  `hooks/enforcement-source-closure-ratifications.v1.jsonl` (1 行) が main に残っている。
  production の consumer は実測ゼロ (`output/` と `docs/archive/` の記録以外に参照なし)。
  廃止済み機構の死んだ台帳を残すか撤去するかを裁定し、撤去するなら `hooks/` の防護 path を
  通す手順とあわせて決める。
