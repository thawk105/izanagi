# cleanup 引き渡し script の退避 tar が空のまま worktree 4 本を撤去し、K2 loop の campaign 原本が消失した (2026-09-20 19:25 JST)

authority: none / default_effect: no-state-change (事故の凍結記録。可変状態の正本は worklog 末尾と現行 phase doc)。

一次資料 (wave `dev-wave-cleanup-backup-loss-record`、基準 HEAD = local main `2bf985125`、2026-09-20 19:4x〜 JST、台帳 ID は fold が採番)。
事故を起こした script と退避 dir は repo 外 `/work/1/SFC/tanab/cleanup-20260920/` (`handoff.sh`、`backup/20260920-192523/`)、
同日の `/cleanup-branches` 棚卸し記録は同 dir の `inventory/`。job dir (repo 外) は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/`。

## 1. 何が起きたか

1. 2026-09-20 16:26 JST の `/cleanup-branches` 実行 (worktree 7 撤去・branch 180 削除、巻き添え 0) の final で、
   「unlocked・main 取込済み・非占有だが未追跡 `output/` を抱えて dirty」の worktree 4 本を裁定候補 1 として報告した。
2. ユーザー「私は何のコマンドを打てば良い？スクリプト作ってくれたら助かる」を受け、Claude (本 wave と同じ session) が repo 外に
   引き渡し script `handoff.sh` を書いた。`retire` は「占有検査 rc0 → 退避 (tracked diff + 未追跡 tar) → detach → branch -d →
   `tools/cleanup_remove_dirs.py` → prune」の順で、退避を「撤去を取り返しのつく操作にする」ために置いた。
3. 19:25:23 JST、ユーザーが `bash handoff.sh retire candidates-1-dirty.txt` を実行し、4 本とも `y`。4 本の dir 撤去・
   branch `worktree-dev-wave-t2698-official-floor-resubmit` の `-d`・prune まで完了した。
4. 検算で `backup/20260920-192523/*/untracked.tgz` が **4 本とも 0 entry** と判明した。tracked の差分は元々 0 だったので、
   失ったのは未追跡 file だけである (status の行数: t2698 = 3 dir、submit-tree 3 本 = 各 2 dir。file 数は撤去前の実測で 48 / 8 / 7 / 8)。

## 2. 原因 (再現済み)

退避行は次の形だった:

```
git -C "$w" ls-files -o --exclude-standard -z | tar --null -T - -czf "$d/untracked.tgz" -C "$w" 2>/dev/null || :
```

GNU tar は引数を順に処理するため、`-T -` から読む file 名は**その時点の cwd** (script が直前に `cd` した repo root) 基準で
解決される。`-C "$w"` は list を読み終えた後にしか効かない。撤去対象の未追跡 path は repo root には存在しないので全件
`stat 不能` になり、そのエラーを `2>/dev/null || :` が握り潰した。**退避 step は何もしていないのに成功として次の撤去へ進んだ**
(恒真ゲート)。生きている worktree で同じ 2 形を並べて再現した: `-T -` の後ろに `-C` = 0 entry (stat 不能 72 件)、
`-C` を `-T` の前 = 2409 entry (list の 72 path 全部を含む)。

見落としの 2 段目: 候補 list を作るとき、submit-tree の `?? output/exploration/` を「単なる dirty」と分類し、該当 wave の insight の
「証拠の所在」節 (「campaign WAL … は repo へ複製していない。原本は submit-tree の下」) を引かなかった。round 3 の HANDOFF には
「submit-tree は残置」と意図的に書かれていた。

## 3. 失ったもの / 残っているもの

Lustre (`/work`) に snapshot は無く、`rm -rf` 後の復元手段は無い。他の tree・job dir・insight を全走査した結果:

| 撤去した worktree | 消えた未追跡 file | 他の写し | 判定 |
|---|---|---|---|
| `.claude/worktrees/dev-wave-t2698-official-floor-resubmit` | `output/claims/`、`output/env/pegasus/floor/attempts/submissions/eb2759286496ac320307d0b3c3064e18/`、`output/s8b-build-cache/` (48 file) | wave 自身の退避 bundle `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/` (109 file、`MANIFEST.json` に bytes と sha256。submission dir・claim・run dir・binary 12 本を含む) | **実害なし** (build cache は再生成可、bundle 外の claim file は lease 記録) |
| `dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree` (HEAD a99425b66) | campaign `p3-s4-loop-s4-autonomous-409e13f8`: `runs/wal.jsonl` (5 record、sha256 `eb8927b7…`)、`runs/agent_outputs.jsonl` (3 行、`66d3e737…`)、`loop_state.json` (`917ba3d3…`)、`s4_loop_digest.txt` (`f993251d…`)、`campaign.lock` (`f1ab4966…`)、`knowledge_manifest_receipt.json` (`c42dc712…`)、`output/env/pegasus/claims/` | 受領証だけは round 2 と同 bytes (`c42dc712…`) が t2746 job dir の `scratch-campaign/` に残る。`layer3_report.json` は job dir root と insight に複製済み | **WAL・AO・loop_state・digest・campaign.lock の原本 bytes 消失**。派生物 (`output/insights/2026-09-19/k2-loop-round3/materials/` 12 file、`layer3_report.json`、job 出力) と各原本の sha256 は insight に残る |
| `dev-wave-jobs/dev-wave-t2746-k2-loop-round2/submit-tree` (HEAD d2ebef7a4) | 同 campaign の round 2 本走: WAL (`03ac8508…`)、AO (4 行、`804c62c7…`)、`loop_state.json` (`03ebaf94…`)、`s4_loop_digest.txt` (`a0a4c204…`)、`campaign.lock`、受領証、claims | job dir の `scratch-campaign/` (2026-09-18 08:00 の dogfood 用写し) の WAL・`loop_state.json`・`s4_loop_digest.txt`・受領証が insight 記載の sha256 と **byte 一致**。AO は別走 (`1866ebc8…` ≠ `804c62c7…`)、`campaign.lock` は insight に sha 記載なく照合不能 | **AO の原本消失、campaign.lock は照合不能**。WAL / loop_state / digest / 受領証は写しで残る |
| `dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/submit-tree` (HEAD d97c423bd) | 同 campaign の roundtrip 走: WAL、`loop_state.json`、`s4_loop_digest.txt`、受領証、claims | 無し。insight (`2026-09-16/t2588-k2-loop-roundtrip`) は自走 WAL の sha256 を記録しておらず、`bench_done` の値 (`throughput_tps=487088.5` 等) と job 出力 (`evidence/attempt-0001/`) だけが残る | **原本消失、sha256 も無い** (知識源 WAL は git 管理の commit `2fa13a262` にあり無傷) |

影響の範囲: 3 巡の K2 loop の**結論 (論文ストーリー 2026-09-20 §8 B-6、fig12)** は insight の派生物と評価値で書かれており変わらない。
変わるのは「原本 bytes を後から再検算できる」という provenance の強さで、round 3 / roundtrip は sha256 (round 3) または値 (roundtrip)
までしか遡れなくなった。次巡 (round 4) が round 3 の `loop_state.json` から再開する設計なら、checkpoint を派生物から再構成するか
別走にするかの裁定が要る (worklog の次の一手に新規 T「K2 loop 原本消失の下流影響」として起票)。

## 4. 修正 (同日、repo 外 script)

`handoff.sh` の退避を fail-closed に直した: `tar -C "$w" --null -T - -czf …` の順にし、エラーを握り潰さず、`ls-files -o` の
list を `untracked-list.txt` に残し、**tar の非 dir entry 数が list 数を下回れば撤去せず rc=6 で止める**。生きている worktree
(`dev-wave-t1851-c3c-official-floor`、未追跡 72 file) で list の全 path が tar に在ることを実測した。候補 2・3 の worktree は
この修正の前に 1 本も撤去していない。

command 側 (`/cleanup-branches` §2・§3) への反映は本 wave の scope 外で、worklog の次の一手の新規 T「cleanup-branches の原本判定と退避検算」に送る。

## 5. 教訓 (failures 台帳のエントリと同内容)

- 退避は「rm の前に退避物を検算する」までが退避である。tar の rc を握り潰した時点で退避 step は恒真ゲートになる。
- 「未追跡 = 捨ててよい」ではない。submit-tree / wave worktree の `output/exploration/`・`output/env/` は campaign 原本の置き場で、
  insight の「証拠の所在」節が repo 外原本の所在を明記している。候補にする前にそこを引く。
- 対話 script で `while read` の stdin を `read -p` が共有すると、問いが list 行を食う (同 script の別バグ、同日修正)。
