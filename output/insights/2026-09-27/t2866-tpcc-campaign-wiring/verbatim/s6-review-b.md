## 総括

**NO-GO。** 対象 commit の主要な配線は plan v2 に沿っており、現時点で削除すべき本番コードは見当たりません。
ただし、使い捨て driver が必須の `pipeline.evaluate` 実測を省略しています。現 pin の TPC-C trace が既存 reason で拒否され、その判定が WAL に残るという完了条件を満たせません。
driver に評価 1 件を追加し、実行結果を確認してから受理するのが最小修正です。レビューは静的検査のみで、テスト実測は行っていません。

## 所見

- **RB1・不足** — `smoke_driver_d.py:208-211` は evaluate を呼ばず、`omitted` と記録します。放置すると **WAL に TPC-C の拒否判定が存在せず**、campaign 評価の実機到達を成果物から確認できません。独立 layout で錨 `s1-H-base` の R1 を `pipeline.evaluate(..., workload="tpcc", correctness=錨 flags)` に 1 件投入し、v2 の既存 reason による reject と bench 未起動を記録してください。
- **RB2・不足** — `smoke_driver_d.py:201-212` は job・verify・bench の結果を保存しただけで正常終了します。放置すると、失敗した job や期待外の検証結果でも完了記録が成立します。`completed_blocks`、verify の `indeterminate` と reason、bench の rc・tps、RB1 の WAL 判定を確認し、不一致なら非ゼロ終了にしてください。
- **RB3・縮小** — `orchestrator/tests/test_buildcache_v2.py:124-151` の不正 workload 試験は、同じ拒否を内部 API を含む五つの入口で繰り返します。受理集合は変わりません。公開入口の `build`・`build_v2` と identity 衝突の試験に絞れます。既存の拒否期待値は緩めないでください。
- **RB4・維持** — `orchestrator/campaign/pipeline.py:1566-1567,2918-2922` の TPC-C 限定 workload 記録は bench・commit の参照を明確にし、YCSB payload を保ちます。削除するとレポートと台帳から TPC-C の測定点を識別しにくくなるため維持が妥当です。