# 段 6 終結 (2026-09-23 21:37 JST)

- review (codex/s6-review.md): NO-GO、must 1・should 3・nit 1、全採用 → fix1 (子木 commit cef14d31)
- 焦点再レビュー (codex/s6-focus1.md): 前巡 1・2・3・5 closed、4 partial、新 must-fix 2 (空でない out-dir の上書き、JSON 保存失敗で rc=0) → fix2 (子木 commit 8dcd287b)
- fix2 の closure は親が実機で確認 (DW-O16、3 巡上限内。差分 20 行):
  - 空でない out-dir (result.json に "keep"): stderr "--out-dir must be empty"、rc=2、既存 file は不変
  - 空の out-dir・login node (pegasus02): "refusing login node"、rc=2、meta.json (launcher_rc=2, phase=preflight) と result.json を記録
  - JSON 保存失敗の注入は fix2 子の自己検査 (codex/s6-fix2.md) に依拠、親は差分を読んで rc 更新経路を確認
- 親の login 実走 (fix 前 v1): fixture g4_rw_no_cycle で verify_once = S certified integrity 全 0、r8_silo_broken_norw で N (rc=1)、C 行 7 field 抽出・classify とも期待どおり
- 投入版: launch_sort_nonswo.py (子木 8dcd287b の t2847_launch/launch_sort_nonswo.py と同 bytes)。分類規則・workload・timeout・build argv は prereg から不変 (焦点再レビューの固定条件照合)。
- GO。
