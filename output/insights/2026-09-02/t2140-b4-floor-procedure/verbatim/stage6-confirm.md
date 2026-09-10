## 対応表

- 所見 5: closed — §11.1 と §11.2 は「既決・案」「事実・案」の混在へ修正され、包括分類の矛盾は解消した。[事前登録:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:858)、[事前登録:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:920)
- 所見 6: closed — D1383 の既決範囲を正確に引用し、AI を各役割から排除する追加条件は明示的に *案* とした。[事前登録:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:862)、[事前登録:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:864)、[D1383:44017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:44017)

## 札の照合

- *既決 (D1383)*: 一致 — AI が案と測定計画を用意し、発効主体・証拠はユーザーが決め、AI は値を既成事実化しない、という裁定本文どおり。[事前登録:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:862)、[D1383:44017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:44017)
- *既決 (D1060)*: 一致 — 既存 floor・既存 calibration の流用を採らず、新しい計測を必要とする決定に対応する。[事前登録:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:875)、[D1060:36501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:36501)
- *既決 (D1377)*: 一致 — caller 由来の floor 値および自由記述の出所を権威として受け取らない決定に対応する。[事前登録:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:877)、[D1377:43885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:43885)
- D1266 の既決記載: 一致 — 記入者・レビュー者をともに `thawk105` とする裁定が実在する。[事前登録:905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:905)、[D1266:41167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/decisions.md:41167)
- §11.0 の *事実* は一致 — floor 不在は `floor_domain_error` となり、`analysis_invalid` を経て `protocol_violation` へ写る。材料レポートも `floor=None` を固定している。[分析契約:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_contract.py:323)、[分析契約:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_contract.py:777)、[材料レポート:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_material_report.py:224)
- §11.2 の *事実* も一致 — 既存 driver の CV、動作点、事前確認だけの競合検査、出力命名、create-only、未校正の B-4 既定設定を現物と照合した。[between-run driver:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:202)、[between-run driver:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:263)、[B-4 既定設定:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_s4_loop.py:969)
- 標本数と費用も再計算して一致 — n=59、n=299、8 標本時の約33.7%・約7.7%、236セッション、3,540秒、追加1,770秒はいずれも正しい。[事前登録:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:953)

## 新しい所見

なし

## 総括

- 所見 5・6 はともに closed。このまま記録してよい。
- D1383 の引用は現物を超えておらず、役割の一律排除は未裁定の *案* として分離されている。
- 差分は 182 行追加・削除 0 行で、§5.1.1 の抽出範囲外にだけ追加されている。
- §5.1.1 は HEAD と byte 単位で一致し、双方 21,833 bytes、SHA-256 は pin と同じ `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`。[抽出規則:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)、[pin:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)
- §5 の値表も HEAD と byte 単位で一致し、floor は `未記入` のままである。[事前登録:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:162)
- pytest は実走しておらず、静的読解、diff、hash、byte 比較だけで判定した。