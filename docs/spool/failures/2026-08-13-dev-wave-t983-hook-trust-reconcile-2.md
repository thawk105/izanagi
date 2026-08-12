---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t983-hook-trust-reconcile
seq: 2
---

## 再発

### F35

- **再発: 2026-08-13** — `/rulings` が **既に実装され land 済みの作業を「新規・未実装」として起票**し、
  ユーザーがその起票資料で実装 wave を投入した。起票資料
  `rulings-inbox/2026-08-12-codex-hook-trust-wave.md` は 2026-08-12 12:56 執筆、実装 commit は
  同日 14:52 (branch `worktree-dev-wave-t-codex-hook-trust`、archive worklog エントリ (476))。
  起票が先で実装が後という順序のため、起票時点では誤りではない。**誤りは起票の後に生じ、
  投入までの約 12 時間、誰も main を再照合しなかった**ことにある。結果として起票資料と
  `[T-983]` の本文は「checker は構造的に rc=0 になれない」という**既に反証された機序**を
  投入時まで主張し続けた (実測 rc=0、2026-08-13 01:00 JST、main tip `adf7997f`)。
  検出は dev-wave 段 1 の前提実測 (`DW-S01`) で、実装子を 1 本も起動する前に止まった。
  本件は F35 の既知の構造的穴 —「恒久対応 1 は `DW-S01` にしか入っておらず `/rulings` の
  収集手順は射程外」— の 2 度目の顕在化であり、**起票から投入までの時間差**という新しい面を足す。
  `DW-S01` は投入後の防壁として今回も機能したが、投入前 (起票資料の鮮度) には効かない。
