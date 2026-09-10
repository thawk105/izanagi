## 総括

- generation/search の生成 variant を selector 語彙の「予測構成」へ写す規則は未凍結で、現行 plan のままでは B-2 判定入力を定義できない。
- §5 validator は発効連言へ未接続、result judge は production caller 不在であり、「機械検証 consumer は実在する」は過大評価である。
- 新規 living prereg を中心成果物にするのは時期尚早で、先に generation 出力裁定と 8b/8c 再凍結を行うべきである。

1. [severity: must-fix] [real] generation/search の出力を `on_off_prediction_difference` / `swapped_follow_through` へ写す規範は repo に凍結されていない。
   [根拠 `docs/phase3-8b-descriptor-design.md:220-234`, `orchestrator/campaign/s8c_result_judge.py:266-309`, `orchestrator/campaign/s8c_result_judge.py:538-725`, `orchestrator/campaign/p3_autonomous_workload_trial.py:4063-4129`]
   [成果物影響] G=2 のどの proposal/variant を各 arm の `configuration_id` とするかで三条件、`selection_evaluation`、最終 conclusion が変わる。
   [提案] proposal sequence 全体、最終 generation、または別 selector のどれを outcome とするかをユーザー裁定し、variant identity と swapped 一致規則を 8b §8 再凍結と 8c 改訂で正本化する。

2. [severity: must-fix] [refuted] 「B-2 の因子・セル・反復・判定規則は既に凍結済み」は generation/search については成立しない。
   [根拠 `docs/phase3-8c-preregistration.md:57-70`, `docs/phase3-8c-preregistration.md:124-143`, `docs/phase3-8c-preregistration.md:185-197`, `docs/phase3-8b-descriptor-design.md:464-484`]
   [成果物影響] 6 reporting cell と G=2 は固定済みでも統計反復 `n` と judged variant が未定なので、paired contrast と `official_status` は生成できない。
   [提案] 「holdout・3 arm・6 reporting unit・G=2 は凍結済み、統計反復と generation outcome mapping は未凍結」と brief を限定する。

3. [severity: must-fix] [refuted] brief の「判定パラメータを機械検証する consumer は既に実在する」は、発効・正式受入を担う consumer という意味では誤りである。
   [根拠 `orchestrator/campaign/s8c_preregistration.py:818-832`, `orchestrator/campaign/s8c_preregistration.py:1042-1051`, `orchestrator/campaign/s8c_preregistration.py:1925-1956`, `orchestrator/campaign/s8c_result_judge.py:217-239`, `orchestrator/campaign/s8c_result_judge.py:1012-1020`, `docs/decisions.md:25943-25950`]
   [成果物影響] parser の violations は発効連言へ入らず、judge も production から呼ばれないため、doc-only wave 後も certified 選択と公式三表は 0 件のままである。
   [提案] `section5_value_violations` を発効判定へ結線し、発効版 §5 から `_ContrastParams` を構築する束縛と supervisor→judge→三表の production caller を別 wave で実装する。

4. [severity: must-fix] [real] plan は generation 出力裁定を要求しながら、同じ wave で 8b/8c を変更しないとしており、正本化の順序が自己矛盾している。
   [根拠 `dev-wave-jobs/dev-wave-b2-descriptor-prereg/plan.md:44-48`, `dev-wave-jobs/dev-wave-b2-descriptor-prereg/plan.md:118-127`, `docs/phase3-8b-descriptor-design.md:255-267`, `docs/phase3-8c-preregistration.md:285-301`]
   [成果物影響] pilot 文書だけが裁定済み mapping を持つと、8b/8c と pilot で判定入力の参照先が分岐し、受理集合の権威が一意でなくなる。
   [提案] wave を「裁定＋8b/8c 再凍結」と「pilot prereg」の二段に分け、前段が land するまで後段を作らない。

5. [severity: should-fix] [refuted] P2 を今作らなければ §5 が「永久に空欄」となる、という成果物影響は裏付けられない。
   [根拠 `dev-wave-jobs/dev-wave-b2-descriptor-prereg/brief.md:74-80`, `docs/phase3-8b-descriptor-design.md:481-484`, `docs/phase3-8c-preregistration.md:179-183`, `orchestrator/campaign/p3_autonomous_workload_trial.py:922-935`, `orchestrator/campaign/s8c_preregistration_evidence.py:3075-3075`]
   [成果物影響] 現時点では draft の有無にかかわらず formal launch と `official_status` は拒否され、P2 自体は受理集合を変えない。
   [提案] 当面の成果物を `output/insights/` の generation-output ruling package と依存タスク表に替え、mapping・schedule schema・manifest authority の確定後に前向き pilot prereg を作る。

6. [severity: should-fix] [real] 新文書案は既存正本と大幅に重なるが、pair-planning 固有の estimand と導出関数だけは既存文書に無い。
   [根拠 `docs/phase3-8c-preregistration.md:25-70`, `docs/phase3-8c-preregistration.md:145-197`, `docs/phase3-main-experiment.md:64-68`, `docs/phase3-main-experiment.md:346-370`, `docs/phase3-b4-reflux-ablation-preregistration.md:150-225`, `output/insights/2026-08-21_t1472-h1h2-readiness-audit/README.md:273-289`]
   [成果物影響] arm・gate・全件報告・現在地を再定義すると参照分岐が生じる一方、固有の parameter 導出規則が無いままでは §5 の値を前向きに決められない。
   [提案] 後日作る文書は既存正本を参照し、固有部分を「generation outcome 単位、pilot cell、完全 block、候補 n、`delta_min`/`sd_max` 導出純関数、独立データ境界」に限定する。

7. [severity: should-fix] [real] 既存 T-1142 n-pilot は重複実験ではないが、既知結果として新 pilot の HARKing 境界へ必ず登録すべきである。
   [根拠 `output/insights/2026-08-16_t1142-n-pilot-prereg/preregistration.md:1-8`, `output/insights/2026-08-16_t1142-n-pilot-prereg/preregistration.md:66-81`, `output/insights/2026-08-16_t1142-n-pilot-prereg/preregistration.md:183-190`, `output/insights/2026-08-16_t1142-n-pilot-prereg/measured_distributions.md:75-90`]
   [成果物影響] R=11 の既知分布から境界や n を選び、それを前向き登録と呼ぶと §5 パラメータと公式判定の事前性が失われる。
   [提案] plan のとおり既知結果台帳へ載せ、前向き導出から除外するか、exploratory prior と明記して事前登録済みとは呼ばない。

8. [severity: nit] [refuted] brief の「§5 の 7 欄が未凍結」は単純な件数誤りであり、plan の訂正が正しい。
   [根拠 `dev-wave-jobs/dev-wave-b2-descriptor-prereg/measured-activation-report.txt:3-11`, `docs/phase3-8c-preregistration.md:185-197`, `dev-wave-jobs/dev-wave-b2-descriptor-prereg/plan.md:5-7`]
   [成果物影響] 現在の受理集合は変わらないが、解除対象の台帳件数を誤る。
   [提案] 「9 欄中 8 UNFILLED、検定 4 点だけ FILLED」へ統一する。

9. [severity: nit] [real] P4 の編集ファイル見積りは概ね正しく、追加 fixture 編集は不要だが、間接的に複数の living-doc lint とテストが動く。
   [根拠 `tools/check_docs.py:128-169`, `tools/check_docs.py:6637-6703`, `orchestrator/tests/test_check_docs.py:708-710`, `orchestrator/tests/test_check_docs.py:1230-1232`, `orchestrator/tests/test_check_docs.py:10076-10111`, `orchestrator/tests/test_check_docs.py:11945-11953`]
   [成果物影響] 新文書は不在検査、腐敗行番号、限定的な現況再掲、pin literal、D参照、実在 path 検査へ入り、失敗すれば文書受入が赤になるが certified 表の値は変わらない。
   [提案] `LIVING_DOCS` と `docs/README.md` の2編集でよい。`test_check_docs.py` は `_ENUMERATED_DOCS` から自動追随するため変更せず、checker と同テストを焦点走対象にする。任意の可変状態一般は検出しないため snapshot は commit 固定表現に限る。

10. [severity: nit] [real] 親の実測項目 1 と 5 は現物と整合し、項目 6 の編集面競合も静的再照合では確認されなかった。
   [根拠 `orchestrator/campaign/contract_loader_binding.py:349-362`, `orchestrator/campaign/enforcement_source_ratification.py:619-626`, `output/insights/2026-08-26_t1759-t1742-ratification-history/README.md:26-33`, `docs/failures.md:10710-10725`, `dev-wave-jobs/dev-wave-b2-descriptor-prereg/brief.md:40-44`]
   [成果物影響] 批准閂は閉じたまま、F369 は既知の診断経路問題、予定3 pathの並行編集競合は無く、正式結果・台帳値はいずれも不変である。
   [提案] この3点は brief に残してよい。ただし批准呼出しと pytest は本 consult では再実走しておらず、静的検査・既存実測記録との照合として記述する。