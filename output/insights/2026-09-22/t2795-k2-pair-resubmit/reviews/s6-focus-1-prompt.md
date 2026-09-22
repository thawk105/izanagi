単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- 前巡のレビュー: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/reviews/s6-review.md (NO-GO、M1 / S1) と
  同 dir の `s6-adjudication.md` (親の裁定)、`s6-review-prompt.md` (前巡の依頼)。
- fix commit: repo root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit の HEAD (`6dc046add`)。差分は `git show 6dc046add` と `git diff 88071a245 6dc046add` で読む。
- 対象 file: 同 worktree の `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md` (§3・§6・§9)、`reviews/s1-brief.md` (当時のまま保存されているはず)、
  `docs/spool/worklog/2026-09-22-dev-wave-t2795-k2-pair-resubmit-1.md`、`docs/spool/failures/2026-09-22-dev-wave-t2795-k2-pair-resubmit-2.md`、
  書式正本 `docs/spool/README.md` と `docs/spool/failures/README.md`、`docs/failures.md` 冒頭の型タグ一覧 (15〜25 行付近)。
- 裁定: 同 worktree の `docs/decisions.md` の D2211 (70677 行〜、項 1)、D2212 (70885 行〜、項 4)、控え /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-22-rulings-full31-verdicts.md 項 1。
- 一次資料 (読取専用、repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/ の `review.md` (s6-review.md の正規化前の原文)、`evidence/attempt-{pair,r4}-0001/job.stderr`
  (Elapse)、`qsub-submit-pair.sh`、同 worktree の `tools/pegasus/p3_s4_loop_pegasus.sh` 先頭の `#PBS -l elapstim_req`。
- 記憶 (読取専用、恒久対応のポインタ先): /home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/experiment-compute-needs-user-confirmation.md の末尾の節。

## 依頼 — fix 後の焦点再レビュー (docs-only)

前巡の所見 M1 (投入前の見積りが D2211 項 1 の禁じた外挿で、記録が遵守を過大に書いた) と S1 (候補間差の不確かさの言い過ぎ) への fix を検査せよ。

1. **所見ごとの対応表** (closed / partial / regressed、根拠の file:line) を必ず出せ。表なしで閉じたと判定しない。
2. **fix で親が書いた派生値を原データから再計算せよ:** 「walltime 3 時間 × 1 node × 2 job = 6 node 時間」(job body の `elapstim_req` と qsub で walltime を上書きしていないことを `qsub-submit-pair.sh` で確認)、
   「2 job で 207 秒 (≈ 0.06 node 時間)」(両 job.stderr の Elapse)、「行末空白 15 行」「5,806 B → 5,776 B」「sha256 241309447… → 8576ad1e…」「diff -w -B 一致」(`review.md` と `s6-review.md`)。
3. **開示の正確さ:** README §6 と worklog fragment の記述が D2211 項 1 の文言と整合し、過小にも過大にもなっていないか (「本来は 1 本目の前に確認を取るべきだった」の根拠、4 巡目前の取り直しとの区別、
   測定値・判定への影響なしの主張)。brief (`reviews/s1-brief.md`) を書き換えていないか (`git diff 88071a245 6dc046add -- <brief>` が空か)。
4. **failures fragment の形式:** `## 新規` の `### {{F:slug}}. 題 [型タグ]`、型タグが台帳の語彙 ([権限逸脱] [手順漏れ] 等) から選ばれているか、恒久対応が実体 (memory の節) を指し、その節が実在するか、
   placeholder の綴りが worklog fragment と一致するか。
5. **回帰:** fix が他の記述 (§0 の主張、§1〜§5 の数値、round 3 README の追記、phase3.md の行) と矛盾を生んでいないか。

各所見は real / refuted、file:line、成果物影響 1 行 (DW-G05) を付け、must-fix / should / nit に分けよ。実装や新 gate の提案はしない。
書込可能な tmp は無いので静的検査と読取専用コマンドでよい。書込みは禁止 (Bash 経由のリダイレクト・sed -i・tee も禁止)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 出力形式

markdown。`## 対応表`、`## must-fix`、`## should`、`## nit`、`## 総括` (GO / NO-GO と理由 3 行以内)。
