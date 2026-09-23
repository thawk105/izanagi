単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/codex/s5-fix1-prompt.md と s5-fix1-out.md — 前巡の依頼と報告。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/job-out-r2b/incomplete.json と env-before.json — 前巡版の計算ノード実走 (request 19108.nqsv) の記録。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py — 修正対象 (`staged_replica`、`/scr` の扱い)。読めなければ即停止。

## 役割と所有

[T-2273] 診断 wave の fix 子 2 巡目 (workspace-write)。作業 worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe` (branch `author-t2273-probe-fix2`、前巡 commit の上)。所有 path は `tools/t2273_replica_runner.py` だけ (plugin / analyze は変えない)。docs・テスト・既存 tools は編集しない。`git add` / `git commit` をしない。

## 実走で分かった事実

- 計算ノードでは `/scr` は `/dev/md0` の xfs (mount option `noquota`、node-local) だが、**`/scr/<user>` は存在しない** (`statvfs/stat: FileNotFoundError`)。前巡版は `/scr/<user>` が無いと X を止めるので、このままでは X が走らない。
- `quota -s` の出力: `/dev/nvme0n1p4` (= `/`、TMPDIR の /tmp) は limit 100G、`/dev/nvme0n1p5` は limit 8192M。
- なお前巡の実走が smoke 後の clean 検査で止まったのは、親が走行中に wave 木へ file を書いたため (親の手順ミス、probe の欠陥ではない)。この検査はそのまま残す。

## 直すこと (最小限)

1. `/scr` が存在し、node-local (`/proc/mounts` で source が `/dev/` の block device、fs が Lustre/NFS でない) かつ書込み可能なら、`/scr/<user>` を `mkdir(mode=0o700, exist_ok=True)` で作ってよい (既存なら所有者が自分で dir であることを確かめる)。その下に `mkdtemp` で staging を作る。作った `/scr/<user>` 自体は job 終了時に空なら消す (既存だったものは消さない)。作ったかどうかを `staging.json` に記録。
2. `/scr` 自体が無い・書けない・node-local と確認できない場合は、従来どおり X を止め `incomplete.json` (/tmp へ fallback しない)。
3. 他の挙動 (TMPDIR 継承、残骸掃除の規則、quota 記録、clean 検査、pair の順序) は変えない。

## 検査・報告

- 前巡までの合成正例・負例を再走し、期待値を変えずに緑を確認する (反転・緩和・skip・削除の禁止)。
- 追加: 一時 dir を `/scr` 役に注入して「`<user>` dir が無ければ作る」「既存なら残す」「書けなければ止める」の正例・負例 (production の分岐を stub で素通りさせない)。
- 緑には実走 command と範囲を併記。計算ノード本走は「実装済み・未実走」。報告に変更点・`git status --porcelain`、最後に `## 総括` (5 行以内)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
