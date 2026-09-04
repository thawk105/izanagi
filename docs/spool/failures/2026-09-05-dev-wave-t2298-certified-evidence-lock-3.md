---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-05
wave: dev-wave-t2298-certified-evidence-lock
seq: 3
---

## 新規

### {{F:measure-dispatch-during-author-edit}}. 実装子が編集中の worktree を cwd にして測定 job を dispatch し、測定値と赤 1 件が HEAD のものでなくなった [計測汚染] [手順漏れ]

- 事象: 段 5 の Codex 実装子が `orchestrator/tests/test_p3_b4_raw_record_producer.py` を編集している最中 (mtime 22:45:13) に、
  親が同じ worktree から測定 job M-C (`tools/pegasus/dispatch_compute.py --task generic`、shard-0 の 111 file を 48 worker で
  走らせて timeline を取る) を投入した。job は編集途中の file を読み、`test_m18_symlinked_evidence_is_rejected_with_regular_control`
  が赤になり、同 file の所要も HEAD の値ではなくなった。timing の構造的結論 (wall = collection 56 + test 190 + 5、隠れ待ち 0)
  には影響しなかったが、赤の帰属を一度は疑う手間が生じた。同じ日に、親が焦点走の local 試行中に `git add` を行い、
  `git status` の digest が変わって自動 fallback が止まり rc=16 を 1 回作った (near miss、同型)。
- 根本原因: `DW-M05` は「変異中は親の編集と worktree へ書きうる子の起動を止める」と定めるが、逆向き (子が編集中に親が
  同じ worktree を実行対象にする) と、index の変更が実行中の tree 指紋を変える点は書かれていない。親は実装子の起動と
  測定 job の投入を独立な並列作業と見なした。
- 恒久対応: `DW-S05-A` 近傍へ「実装子が走る worktree を cwd にする dispatch・run_tests を親は起動しない。run_tests の
  走行中は index を含め木を触らない」を足す (段 8 で裁定。予算に収まらなければ memory `no-dispatch-from-worktree-while-child-edits`)。
- 再発検知: 測定 job の meta に対象 file の mtime と `git status --porcelain` を記録し、job 開始時刻より新しい mtime を
  汚染として報告する (本 wave の `measure/run_c.py` は HEAD だけを記録しており、これが取り逃した)。

## 再発

### F832

- **再発: 2026-09-04** — 翌日の wave (entry 1241、D1593 / D1594) が同じ台帳から「鎖 1 = real-repo group 303.7 秒の 1 worker
  直列」「鎖 2 = certified_evidence 258.1 秒」を数え、下限モデル 381.9 秒が実測 388.3 秒と 1.6% で一致したことを裏付けにした。
  現物では `conftest.py` の `_strip_real_repo_loadgroup_suffix` (commit 5ac638955、2026-08-26) が同 hook の yield 後に
  process-memo 4 node 以外の group suffix を剥がしており、鎖 1 は起草時点のコードに存在しなかった (21:16 走の report.json で
  real-repo は 38 worker に分散)。鎖 2 も台帳値で、当日 junit の 17 consumer 合計は 84.9 秒だった。D1618 (T-2297) はこの
  前提の上で承認されている。検出は本 wave の段 1 実測 (report.json の `group_to_workers` と hook の後段を読んだ)。
  hook の前段 (marker 付与) だけを読んで後段 (strip) を読まなかった点も同根。
