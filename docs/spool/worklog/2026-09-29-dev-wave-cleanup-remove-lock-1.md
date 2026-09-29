---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-cleanup-remove-lock
seq: 1
title: worktree 撤去の同時実行制限 — tools/dev_wave_cleanup.py の撤去 (wave 撤去・remove-child) を共有 repo 全体で同時 1 本にし、使用中は待たず rc=75 で即戻す。DW-O28 に 1 文 (コード + docs + insight、計算ノード job なし、branch worktree-dev-wave-cleanup-remove-lock)
---

## 本文

- 依頼: 並行 wave 指示 md_1 (`/work/1/SFC/tanab/tmp/git-maint-2026-09-29/md_1.txt`、共通 `common.txt`)。2026-09-29 に remove-child 16 本の同時起動が Lustre の I/O 待ちで 20 分以上止まった件への手入れ。結果・経緯・変異台帳・レビュー裁定の正本は一次資料 `output/insights/2026-09-29/worktree-removal-lock/README.md`。
- 「次の一手」に「worktree 撤去の同時実行制限」を含む item は無かった。この wave で完了し残件が無いので、新規 item は立てず本エントリで記録した (新規と完了を同じ fragment で扱う形は spool 規則に無い)。
- 実際に行った手順: 段 1 brief → 段 2・3 は軽量版で省略 → 段 4 裁定 (lock を common dir 配下の file に置く案) と変異 6 本の事前登録 → 親が DW-O28 を先に docs commit → 段 5 author 1 本 → 親の login 自走で既存 test `test_remove_child_rejects_wave_root_and_primary[primary]` が赤 (拒否経路でも primary の `.git` に lock file が増える、実装起因) → 裁定を改め fix-1 (common dir の directory fd を flock、file を作らない) → 統合 commit → 段 6 read-only review 1 本 (NO-GO、must-fix 3 件は refuted 2・nit 1 と裁定) → login 自走の変異で M3 (`RC_BUSY` を 20 へ) が生存 → fix-2 (テストを字面の 75 と比較) → 変異 5 本を最終 commit で再走し全て期待 node どおり KILLED、M6 (DW-O28 literal) は実 repo check_docs の手動 probe で KILLED。
- 棄却した review 所見: R1「lock 前に check-ref-format」は branch 名の usage 検査で親が許可した順序。R2「不正な --main-worktree が競合中は rc=20 でなく rc=75」は busy 判定を検証より先に置いた設計どおりで、再試行時は従来の rc=20 (意味は不変)。R3「DW-O28 の『段 9 に』『付ける』の短縮」は nit (land は段 9 にしか起きない、予算 997/1000)。
- 検査: 撤去テスト file の login 自走 205 passed、実 repo `python3 tools/check_docs.py` 違反なし、全史 provenance 13,358 件新規違反なし。`orchestrator/tests/test_check_docs.py` は growth hold で自走不可のため、DW-O28 の docs・literal・合成 fixture の byte 一致 (997) を直接照合した。変異は common.txt (計算ノード job は受入全走だけ) に従い dispatch final を回さず login 自走で判定した。
- セッション異常: `EnterWorktree` の name 形が Lustre の `Interrupted system call` で失敗し branch だけ残ったので、手で `git worktree add` して path 形で入った (既知型)。worktree 1 本の作成に約 20 分。開始 gate は作成中に main が 8 commit 進んだため ff-only で揃えてから rc=0。
- エージェント工数: Codex (gpt-6-sol、medium) author 1 (28 call・275 秒)・fix 2・review 1。計算ノード job なし。受入全走は記録 commit 後に投入する。

## 次の一手差分
