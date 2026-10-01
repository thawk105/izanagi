# 使い捨て script の逐語 (repo 外の job dir で実行、repo へは md として保存)

実装面の資材 (shell) を repo に置かないため、本文を md に写す。`HOOK` は実行時点の wave 木の hook を指した
(段 1 は変更前 5f9e8c549 の bytes、段 6 は fix 後 70af9ee82 の bytes。結果は `raw/repro-before.log` と `raw/repro-after-fix1.log`)。

## repro.sh — F1081 の誤検出の実物再現

```bash
#!/bin/bash
# F1081 の誤検出を実物の hook script で再現する (使い捨て repo、repo 外)
set -u
HOOK=/work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly/tools/dev_wave_cleanup_stop_hook.py
R=/home/SFC/tanab/.claude/jobs/d2fe5f67/tmp/repro
rm -rf "$R"; mkdir -p "$R/main"
cd "$R/main" || exit 2
git init -q -b main . && git config user.name t && git config user.email t@example.invalid
echo a > a && git add a && git commit -qm base
BASE=$(git rev-parse HEAD)
echo b > b && git add b && git commit -qm main-advanced
# EnterWorktree 相当: local main より遅れた起点 (origin/main 相当) から wave branch を切る
git worktree add -q -b wave "$R/wave" "$BASE"
hook() { printf '{"cwd":"%s"}' "$1" | python3 "$HOOK"; echo "  rc=$?"; }
echo "--- (1) 作成直後 (commit 0, ff 前)"; hook "$R/wave"
git -C "$R/wave" merge -q --ff-only main
echo "--- (2) DW-O20 の ff-only 直後 (自分の commit 0, 未 land)"; git -C "$R/wave" reflog show --format='   %h %gs' refs/heads/wave; hook "$R/wave"
echo w > "$R/wave/w" && git -C "$R/wave" add w && git -C "$R/wave" commit -qm wave-work
echo "--- (3) 自分の commit 1, 未 land"; hook "$R/wave"
git merge -q --ff-only wave
echo "--- (4) main へ ff-only land 済み"; git -C "$R/wave" reflog show --format='   %h %gs' refs/heads/wave; hook "$R/wave"
```

## probe_time.sh — reflog の時刻と tag `main` からの ff の subject (結果は `raw/probe-reflog-time.log`)

```bash
#!/bin/bash
# reflog 時刻が GIT_COMMITTER_DATE に従うか、tag main からの ff の subject を確かめる (使い捨て repo)
R=/home/SFC/tanab/.claude/jobs/d2fe5f67/tmp/probe-time
rm -rf "$R"; mkdir -p "$R/main"; cd "$R/main" || exit 2
git init -q -b main . && git config user.name t && git config user.email t@example.invalid
echo a > a && git add a && GIT_COMMITTER_DATE="1700000000 +0000" git commit -qm base
GIT_COMMITTER_DATE="1700000100 +0000" git worktree add -q -b wave "$R/wave"
git checkout -q -b side && echo s > s && git add s && GIT_COMMITTER_DATE="1700000200 +0000" git commit -qm side && git checkout -q main
git tag main side
GIT_COMMITTER_DATE="1700000300 +0000" git -C "$R/wave" merge -q --ff-only main 2>&1 | head -2
GIT_COMMITTER_DATE="1700000400 +0000" git merge -q --ff-only wave 2>&1 | head -2
echo "--- wave reflog"; git -C "$R/wave" reflog show --date=unix --format='%H %gd %gs' refs/heads/wave
echo "--- main reflog"; git reflog show --date=unix --format='%H %gd %gs' refs/heads/main
git --version
```

## observe_reflogs.sh — 実 repo の local branch の reflog 観察 (読み取りのみ、結果は `raw/branch-reflogs-1200jst.txt`)

```bash
#!/bin/bash
# read-only: 各 local branch の reflog 文言と main 祖先性を観察する
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/cleanup-stop-hook-ffonly || exit 2
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
  [ "$b" = main ] && continue
  anc=no
  git merge-base --is-ancestor "refs/heads/$b" refs/heads/main && anc=yes
  n=$(git reflog show --format='%H' "refs/heads/$b" 2>/dev/null | wc -l)
  echo "== $b ancestor_of_main=$anc entries=$n"
  git reflog show --format='   %h %gs' "refs/heads/$b" 2>/dev/null | head -10
done
```

10:2x JST の初回は各行を `cut -c1-110` で切っていたため多バイト文字の途中で切れた不正な UTF-8 を含み、repo へは入れなかった。
その集計 (25 branch、各 branch 最新 10 項まで) は `commit` 57・`branch` 25・`commit (merge)` 15・`merge main` 3・
`merge db8d7f1ec` (非 ff merge) 1。12:00 JST の取り直し (20 branch、間に他 wave の撤去が進んだ) は
`commit` 51・`branch` 18・`commit (merge)` 14・`commit (amend)` 1・`merge main` 2。
