---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-helper-forwarding
seq: 3
---

## 新規

### {{F:worktree-add-reset-index-leaves-branch}}. 高負荷の Lustre で `git worktree add -b` が checkout の後に失敗し、dir と管理情報は消えて branch だけが残った [セッション死・救出]

- 事象: 2026-09-29 14:10〜14:29 JST、背景 job の wave 開始で `EnterWorktree(name)` が既知の「Could not read the repository git config」で失敗したため、手動で `git worktree add -b worktree-dev-wave-vhash-helper-forwarding <path> main` を走らせた。35,128 file の checkout が 100% まで進んだ後に `fatal: Could not reset index file to revision 'HEAD'` rc=128 で終わり、worktree の dir と `.git/worktrees/` の管理情報は消えたが、branch (main と同じ commit) だけが残った。展開中に「システムコール割り込み」の警告があり、同時刻に 16 本の worktree 撤去で Lustre が詰まっていた (land 調整役の通知)。
- 根本原因: ファイルシステムの一時的な失敗 (割り込まれた system call) で index の書き込みが失敗し、`git worktree add` は作りかけの worktree を片付けるが `-b` で作った branch は消さない。同じ引数での再実行は「branch が既にある」で失敗する。
- 恒久対応: 回復手順を memory `worktree-discipline` に足した — 残った branch が main と同じ commit であることを `git rev-parse` で確かめ、`-b` を付けずに既存 branch を指定して `git worktree add <path> <branch>` を 1 回だけ再実行する (今回はこれで 14:58 に完成)。add には timeout を掛けない (既存の規律)。
- 再発検知: `git worktree add` の rc と、`git worktree list` に path が無いのに `git branch --list <branch>` が残る状態。

## 再発

### F1

- **再発: 2026-09-29 (near miss、3 件)** — md_16 の wave の親が、子 worktree で fix branch を切るときに短縮 SHA を**手で伸ばして書き**、`git checkout -b vhash-hlp-fix1 e5a825d57601547` と `git checkout -b vhash-hlp-fix3 ade14b4d1c` が「not a commit」で拒否された (もう 1 件は同じ形で rev-parse の出力に切り替えて回避)。git が拒否したので誤った commit から branch を切る実害はなかった。型は「一次資料 (rev-parse の出力) から転写せず手で書き直す」で、2026-09-20・21 の再発と同じ。恒久対応は変更なし (memory `worktree-discipline` の「sha は rev-parse の 40 hex をそのまま使う」) — branch を切るときは `HEAD` や `$(git rev-parse <短縮>)` の出力を使い、SHA を手で書かない。

### F936

- **再発: 2026-09-29 (near miss)** — md_16 の wave で、焦点走 (`tools/run_tests.py --force-dispatch`) の job が待ち行列にいる間に、親が wave の worktree の `output/insights/` へ一次資料の下書きを書いた。job の起動前に気づき、下書きを job dir (`insight-stage/`) へ移して worktree を clean に戻したので、job は緑で走った。実害なし。恒久対応は既存どおり (memory `dirty-tree-during-pending-job`: 投入中の job がある worktree では書かない。一次資料の下書きは計測と受入が全部終わるまで job dir で作る)。
