---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: t222-scheduler-group
seq: 1
title: '[T-222] dispatch_compute.py の accounting evidence へ scheduler group (Group Name) 束縛を追加した (コード + テスト + docs + 記録、branch worktree-t222-scheduler-group、変異 matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=non-attributable-only)'
---

## 本文

- [T-193] 閉鎖時にユーザーが独立残務として切り出した「accounting footer の `Group Name` を
  policy account へ exact 束縛する」を main の `_accounting_present` へ適用した。未 land の
  `codex/dev-wave-improve` branch (削除済み) の先行設計・段6敵対レビュー・変異検証を参考資料として
  引いたが、対象コードの形が違うため鵜呑みにせず main の実形へ再導出した。
- 段3 敵対相談2レンズが実データ (`output/insights/2026-07-30_pegasus-compute-node-dispatch/probe-874129-accounting.txt`)
  で fixture の field 順序を裏取りし、`silo_ladder_rung1.py` / `floor_liveness.py` /
  `collect_receipt.py` / `t503_restore_durability_probe.py` に同型 (Group Name 未検証) の
  独立経路4件を発見した (real、scope外)。DW-G03 の独立2例閾値は満たすが、起票時の scope
  (`dispatch_compute.py` 単体) と矛盾するため本 wave では実装せず、次の一手へ新規候補として残す。
- 段6敵対レビュー2本は blocker ゼロ、real (非blocker) 2件 (挿入位置の字義解釈・tail境界テストの
  恒真性) はいずれも成果物影響を1行で書けず nit/backlog とし、fix サイクルは起動しなかった。
- **変異 M3 (`_accounting_present` の期待値を誤った定数へ差し替える変異) と M4 (比較演算子反転)
  は、file 全体 (188 test) で実走すると `_Scheduler(accounting=True)` に依存する無関係なテストへ
  広く波及し、pytest-xdist の worker 集約・終了処理が host 混雑下で 90〜300秒無応答になる現象を
  4回再現した** (`git checkout --` で復元済み、実装差分とは無関係)。詳細と回避策 (対象2テスト
  関数への nodeid 絞り込み) は {{F:pytest-xdist-teardown-hang-under-mass-failure}}。
  絞り込み後は2秒未満で完走し、M3 の事前予測 (正例テストのみ) は実測と一致したが、M4 は
  「正例テストが真っ先にKILLED」という記述に対し実測は負例4件も同時にKILLEDすることを明らかにした
  (F323型、記録は実測へ補正済み)。
- 受入投入は `owned-path-overlap` (main 側 [T-1115] が同じ `dispatch_compute.py` を独立変更) で
  1回 rc=70 停止した。`docs/failures.md` F225 の恒久対応 (Codex子が main 側の変更を先取り統合
  してから親が手動 merge commit を作る) に従って解消し、2回目の投入で受理された
  (`tested_main=b8b51892d55cbcf37487a4638ebe9d6fd589317a`,
  `tested_tip=2a652ecd6260267496aa4cd0b595ca796debcadb`)。
  赤 1件 (`test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`)
  は checker が non-attributable と判定 (同時期の他 wave entry (723) も同じ赤を同じ理由で観測)。
- 詳細な段1-6 の記録は `output/insights/2026-08-19_t222-scheduler-group/` を参照。

## 次の一手差分

### 完了

- [T-222] `tools/pegasus/dispatch_compute.py` の `_accounting_present` へ scheduler group
  (Group Name) の policy account exact 束縛を実装し、受入全走まで完了した
  (verdict=non-attributable-only)。
  remaining: none
  base: efbe511ef51b7bb5a2515e160b395396d741d185201e66b8614cf2771ebe6c7c

### 新規

- {{T:pegasus-accounting-group-name-family}} **P3・新規**: `silo_ladder_rung1.py` /
  `floor_liveness.py` / `collect_receipt.py` / `t503_restore_durability_probe.py` の4箇所が
  `dispatch_compute.py` の `_accounting_present` とは独立に accounting evidence を検証しており、
  いずれも Group Name (scheduler group) を検証していない ([T-222] 段3 lens B の所見)。
  DW-G03 (独立2例) の閾値を満たす族一般化候補。対応 (横断的に同じ束縛を足すか、明示的に
  scope 外と裁定するか) はユーザー裁定待ち。
