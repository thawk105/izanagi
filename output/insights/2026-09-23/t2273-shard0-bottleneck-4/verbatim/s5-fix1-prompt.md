単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/s4-ruling.md — 段 4 裁定。「追補 1」の「R2 の事前登録」が仕様の正本 (変えない)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/codex/s5-author-r2-out.md — 前巡の実装報告。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/job-out-r2/ — R2 の実走出力 (request 19029.nqsv)。`incomplete.json`、`staging.json`、`X/pytest.log` の末尾、`A2/env-after.json`、`X/env-before.json`、`env-before.json`。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py (と必要なら plugin / analyze) — 修正対象。読めなければ即停止。

## 役割と所有

[T-2273] 診断 wave の fix 子 (Codex role=author 相当、workspace-write)。作業 worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe` (branch `author-t2273-probe-fix1`、前巡 commit の上)。所有 path は `tools/t2273_replica_runner.py` / `tools/t2273_replica_plugin.py` / `tools/t2273_replica_analyze.py` だけ。他は 1 byte も変えない。docs・テスト・conftest・既存 tools は編集しない。`git add` / `git commit` をしない。

## 起きたこと (実走の事実)

R2 の pair 走で smoke → A2 (rc 0) → staging (成功、45.6 秒、29,885 file) → X の順に進んだが、X は pytest の一時 dir 作成が `OSError: [Errno 122] Disk quota exceeded` で多数失敗し (failed 21 / errors 25)、report.json が無く rc 16 になった。計算ノードの `/tmp` は `/` (nvme xfs、mount option `usrquota`) で**ユーザー quota** がある。staged repo (`/tmp/t2273-output-*/repo`、clone した object 約 620 MB + output 29,885 file) と、smoke・A2 が残した /tmp の一時物 (`pytest-of-<user>/pytest-*`、`izanagi-t080-e2e-*`、`izanagi-task-run-*` 等) が重なって quota を超えたと読める。**X の測定値は無効**。

## 直すこと (最小限)

1. **staged repo の置き場を /tmp の外の node-local へ移す:** `/scr/<user>/` (T-2817 runner が使っていた node scratch) が存在し書込み可能ならその配下に `mkdtemp` で作る。無ければ X を実施せず `incomplete.json` に理由を書いて止める (/tmp へ fallback しない)。置き場の path・mount point・filesystem 種別・`os.statvfs` を `staging.json` に記録。**テストの TMPDIR は従来どおり継承値 (/tmp) のまま**にする (実受入と同じ条件、裁定 C7)。staged repo は job 終了時に削除する (失敗時も)。
2. **各走 (A2・X) の直前に、前の走が /tmp に残した自分の一時物を消す:** 対象は TMPDIR 直下の自 user 所有の `pytest-of-<user>` 配下の `pytest-*`、`izanagi-t080-e2e-*`、`izanagi-task-run-*`、および前走の session 残骸で、**この job が作ったものに限る** (job 開始時点の一覧を `env-before.json` に記録し、開始時から在ったものは消さない)。A2 の前 (smoke の残り) と X の前 (A2 の残り) の両方で同じ規則を適用し、消した件数・bytes を各走の `env-before.json` に記録する。
3. **quota と空きの記録:** 各走の前後と staging の前後に、`quota -s` (無ければ `quota -v`、どちらも無ければ欠測と記録) の出力と、TMPDIR と staged 置き場の `os.statvfs` を記録する。
4. 既存の run mode・pair の他の挙動・plugin の差し替え条件・analyzer の判定は変えない。analyzer は `staging.json` の新しい欄を表示するだけでよい。

## 検査・報告 (DW-S05-C を継承)

- 既存の合成正例・負例を再走し緑を確認する。**既存の期待値を変えない** (反転・緩和・skip・削除の禁止。赤なら実装側が誤り)。
- 追加: 一時 dir で「job 開始時から在った一時物は消さない・job が作ったものだけ消す」の正例と負例、「/scr 不在なら X を止める」の負例を login で走らせる (/scr の有無は引数や注入で切り替えてよいが、production の分岐を stub で素通りさせない)。
- 緑には実走 command と範囲を併記。計算ノード本走は「実装済み・未実走」。
- 報告に変更点・実走結果・`git status --porcelain`。最後に `## 総括` 節 (5 行以内)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
