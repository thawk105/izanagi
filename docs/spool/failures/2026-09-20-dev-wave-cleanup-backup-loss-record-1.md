---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-cleanup-backup-loss-record
seq: 1
---

## 新規

### {{F:cleanup-backup-tar-empty}}. cleanup 引き渡し script の退避 tar が空のまま worktree 4 本を撤去し、K2 loop の campaign 原本を失った [恒真ゲート] [手順漏れ] [証拠破損]

- 事象: 2026-09-20 19:25 JST、`/cleanup-branches` の裁定候補 1 (unlocked・main 取込済み・非占有だが未追跡 `output/` を抱えた
  worktree 4 本) を、Claude が repo 外に書いた引き渡し script `/work/1/SFC/tanab/cleanup-20260920/handoff.sh retire` で
  ユーザーが撤去した。退避 step (`git diff HEAD` + 未追跡 file の tar) を撤去の前に置いていたが、`backup/20260920-192523/*/untracked.tgz`
  は 4 本とも 0 entry だった。tracked の差分は 0 だったので失ったのは未追跡 file だけで、K2 loop の campaign 原本
  (`submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/` の WAL・`agent_outputs.jsonl`・`loop_state.json`・
  `s4_loop_digest.txt`・`campaign.lock`・受領証) が round 3 は全部、round 2 は AO と `campaign.lock`、roundtrip (t2588) は全部
  (sha256 の記録も無し) 消失した。t2698 は wave 自身の `run-backup/` bundle が在り実害なし。Lustre に snapshot は無く復元不能。
  損失表と写しの照合は `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`
- 根本原因: (1) `tar --null -T - -czf out -C "$w"` の順で書いたため、`-T -` の file 名が script の cwd (repo root) 基準で解決されて
  全件 stat 不能になり、`2>/dev/null || :` がそれを握り潰した — 退避 step が何もせず「成功」する恒真ゲート。(2) 候補判定で
  submit-tree の `?? output/exploration/` を「単なる dirty」と見なし、各 wave の insight「証拠の所在」節 (「campaign WAL は repo へ
  複製していない、原本は submit-tree の下」) と round 3 HANDOFF の「submit-tree は残置」を引かなかった。(3) script を実データで
  通す前にユーザーへ渡した (読み取り subcommand だけ実走し、退避 step は撤去を伴うため試さなかった)
- 恒久対応: `handoff.sh` を同日 fail-closed に修正 (`tar -C "$w" --null -T -`、エラー非抑止、`ls-files -o` の list と tar の非 dir entry 数を
  照合し不足なら撤去せず rc=6。生きている worktree で 72/72 を実測)。memory `cleanup-discipline` に「退避 tar の -C 順・entry 検算・
  `?? output/exploration/` は原本」を追記。`/cleanup-branches` §2・§3 への反映 (未追跡 `output/` の原本判定に insight「証拠の所在」を
  引く、退避の検算を撤去の前提にする) は {{T:cleanup-submit-tree-originals}} で別 wave が行う
- 再発検知: 退避 dir の `untracked-list.txt` と `untracked.tgz` の entry 数照合 (修正後の script が rm 前に自動で行う)。
  worktree 撤去を含む cleanup では、撤去後に `backup/*/untracked.tgz` の entry 数 > 0 を報告に載せる
