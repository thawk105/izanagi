---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: worktree-crispy-leaping-sparkle
seq: 1
title: '[T-1361] 焦点走を consumer test まで広げる義務を新規L2節DW-O26へ収容した (コード+テスト+docs+記録、branch worktree-crispy-leaping-sparkle、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 予算精査 (git 派生不可): `.claude/commands/dev-wave.md` の余白は実測 8 bytes (9492/9500)。
  代替収容先 `DW-O18` (995/1000)・`DW-C01` (991/1000) もいずれも満杯と実測し、前例 commit
  `ebf6b133` (2026-08-18) が使った range 表記圧縮は既に適用済みで再現不可と判明した。
  段2 codex plan が別途 3 箇所 (-15 bytes) を発見し、収容可否が「Yes」に転じた。
  詳細は {{D:operations-section-registry-union}}。
- 段5 実装子 1 回目は内容が正確ながら `## 総括` トレーラー欠落 (親の prompt 不備) で
  not_accepted。中断子の部分成果物 (diff) を保全し、2 回目 (監査確定 prompt) で accepted。
- 段6 敵対レビュー2本のうち1本が、親が実測で見つけた2件に加え3件目の real
  (`test_dev_wave_operation_order_rejects_titleless_reorder_and_missing_target` に同型の
  改行欠落バグが潜在、弱い assertion で今は隠れている) を発見した。
- 段5/段6 の codex 子は全試行が Pegasus dispatch 不調 (`qstat -Q` preflight rc=1 等) で
  pytest 実走不能だった。親が `tools/run_tests.py` で実測し、472 passed, 3 skipped, 0 failed
  を確認した (子の「実装済み・未実走」申告は正確だった)。
- launcher の dirty-tree preflight (`docs/dev-wave/{operations,workers}.md` が HEAD と
  1 byte でも異なると codex dispatch 全体が rc=2) に実地で抵触した ([T-1362] handoff 記載の
  既知の罠)。`operations.md` を一時的に HEAD へ退避 → レビュー/fix 投入 → 復元、で回避した。
- 変異は `tools/mutation_harness.py` (dispatch) でなく手動 (DW-O19 手順) で本走した — codex
  子の pytest 実走不能と同じ infrastructure 不調を harness dispatch も踏む蓋然性が高いため。
  baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0。うち3件は本 file 特有の shared
  fixture (`_build_min_repo()` が production 定数を直接参照) 経由の cascade (273〜274件) を
  伴う冗長gate (DW-M03) で、単独理由の証拠は直接等価 assert 1件へ帰属させた。詳細は
  `output/insights/2026-08-19_t1361-focus-consumer/mutation-ledger.md`。
- 副次的に、`docs/handoff/2026-08-19-t1362-reasoning-pin.md` が「段9停止・ユーザー裁定待ち」の
  まま残存しているが T-1362 は commit `0333abe6` で main へ既に着地済みと確認した。land の
  handoff 保護ガードにより本 wave からは削除できず、別途ユーザーへ報告する。

## 次の一手差分

### 完了

- [T-1361] [T-1361] を完了として閉じる。`docs/dev-wave/operations.md` へ新規節 `DW-O26` を
  追加し、`.claude/commands/dev-wave.md` 条件18から到達可能にした。`tools/check_docs.py` が
  登録・exact pin・条件契約を機械強制する。敵対レビュー2本・fix・変異 matrix を完了し、
  この commit を対象に受入全走を投入する。
  remaining: none
  base: 6378293b8dc2eb8657e46b394c9f92f0f716c553aec6afd2972f88b230c55406
