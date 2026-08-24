---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1636-dangling-argv-batch
seq: 2
---

## 再発

### F24

- **再発: 2026-08-25** — `tools/dev_wave_wait.py producer` を背景 job で張った段 6 fix の待ち手が、producer 生存中に **exit 0 かつ出力ゼロ**で偽完了した。`.done` は不在、launcher pid は経過 1 分 24 秒で生存しており、実際の完了は約 8 分後だった。既存の恒久対応 (待ち手の rc を信じず `.done` の exit code と producer 生死で判定する) がそのまま効き、`git diff` が未変化であることと `ps -p` の生存で誤完了を弾いて待ち手を張り直した。本 wave の追加事実は無く、2026-08-17 / 2026-08-23 と同型の 3 度目である。

### F136

- **再発: 2026-08-25 (同日 4 例目)** — **docs-only ではない実装 wave でも同じ形が出た**点が新しい。同日 2・3 例目はいずれも差分が `docs/spool/` だけの wave だったため「docs-only wave が受入 shard 経路を通ると再現する」と記述したが、本 wave の差分は `tools/audit_dangling_commits.py` と `orchestrator/tests/test_audit_dangling_commits.py` の実装面 2 file である。それでも `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系が 11 件赤になり (11 failed / 15,431 passed / 60 skipped)、junit の差分は 11 件とも `first extra item: ('dir', 'task-runs/reports')` で 2・3 例目と逐語一致した。受入 shard は同じ作業木から request `945262` と `945263` を重ねて投入している (shard-1 の junit が 06:21:48、shard-0 が 06:23:55 に確定)。帰属は台帳が定める 3 点で否定した — (1) wave の実装面差分は `launch_cert` / `certificate` を 1 箇所も参照しない (`git diff 16086f12..HEAD -- tools/ orchestrator/` の grep が 0 件)、(2) 同 file の焦点走は **451 passed / 2 skipped** で緑 (2・3 例目と内訳まで一致)、(3) junit 差分が実装ではなく `output/task-runs/` の dir 増加を指す。**差分の性質 (docs-only か実装か) は条件でなく、受入 shard 経路を通ること自体が条件である**ことが確定した。恒久対応は本 wave の scope 外で、受入基盤の所有 wave の判断に委ねる点は既存の再発と同じ。

## supersede 追記

- F526 **supersede: 2026-08-25** — 恒久対応の「分割実行への是正は本 wave の編集面の外」は解消した。`_landed_reference_matches()` は {{D:git-grep-batch-dual-limit}} の二重上限で分割実行し、再発検知は変異 15 件 (全件 KILLED) と `SC_ARG_MAX` 由来の母集合で pin した。argv 上限の手前で `SIGKILL` される領域があることも同時に判明したため、上限は byte だけでなく本数にも掛けている。実探索根に対する本番相当の実走は 2:16:05 で完走し rc=1 (所見あり) を返した。
