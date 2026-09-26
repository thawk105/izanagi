## 対応表

| 1 巡目の項目 | 2 巡目の判定 |
|---|---|
| A-M1・B-M1／短縮 pin | **closed（静的）**。[pipeline.py:2738](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2738) は実 HEAD の前方一致を使い、[同:2716](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2716) は宣言値、[同:2725](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2725) は完全 HEAD を記録する。 |
| A-S2・A-S3・B-S2、焦点走の赤 10 件 | 差分による regression は見当たらない。proof source fixture、patch 復元、起動箇所、env 未設定時の分岐は変更されていない。 |
| B-N3 | 従来どおり未対応の nit。 |

短縮 SHA・完全 SHA・別 commit の短縮形は、保全と build 側でそれぞれ一致・一致・不一致となる。空宣言だけは `buildcache._verify_ccbench_commit` 単体では照合を省くが、通常の evidence 生成では [SourceEvidence が拒否する](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/source_digest.py:217)。保全側も拒否する。

## 新規所見

なし。`failed` inventory では取得済みの実 HEAD が `ccbench_pin`、宣言値が `ccbench_pin_declared` に残り、取得前の失敗では前者が `null` となる。いずれも `status="failed"` で完成した R1 入力にはならない。[pipeline.py:2715](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2715)、[同:2745](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2745)

[M12 用テストの単一 assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:163) は `complete` と両 pin 値を同時に検査するため、完全一致への変異で赤になる。テストは evidence の pin を差し替えるが、評価 fixture は source 解決と build を模擬しており、その差し替えが保全前に別の pin 照合で拒否される経路はない。build 実経路そのものの実走証明ではない。

## 総括

**GO（静的レビュー）。must-fix なし。** build・pytest・変異 probe はこのレビューでは実行していない。