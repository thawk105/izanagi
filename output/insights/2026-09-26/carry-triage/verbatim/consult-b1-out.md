T-841 | 反対: keep にすべき | 本文は「検査を通っていない実行ファイルが certified 経路へ入る」と指摘する。現行コード自身も host-effect gate の結果が cache / WAL / COMMIT に束縛されない限界を **T-841 の残件**と明記しており (`orchestrator/campaign/coder_effect_gate.py:20-26`)、現行の段 4 driver はその gate を使う (`p3_s4_loop.py:801-805`)。実害未測定だけでは、規律 2 の現行経路にある穴を drop できない。

T-1072 | 反対: keep にすべき | 本文の「材料の逐語経路は指示めいた文字列の運び屋」という懸念は、判定理由が挙げる文字集合検査だけでは閉じていない。その検査は diff-quarantine の文字列用 (`orchestrator/critic/digest.py:233-251`) だが、trace 由来の `key` と integrity `notes` は同じ renderer で逐語表示され (`digest.py:1290-1306,1427-1432`)、現行段 4 の critic digest に入る (`p3_s4_loop.py:1206-1215,3247-3259`)。規律 6 の表示経路として残す疑義が強い。

T-2218 | 反対: keep にすべき | D1531 は、呼び手が spec の path と期待 hash の両方を選ぶ現行照合は受理集合を狭めず、承認済み spec からの再導出が必要だと裁定している。現行 B-4 driver はなお両値を CLI で受け取り (`orchestrator/campaign/floor_pair_driver.py:3113-3126`)、その組を照合する (`同:1197-1235`)。稼働中の B-4 測定手順の前提なので、「実害の実測が無い追加」という理由は不十分。

T-469 | 反対: drop にすべき | 本文の消費台帳案は D893 の将来設計であり、現在の certified 選択に到達する経路を示していない。D1241 は測定前固定を証明できない floor-backed 主張を non-certifying に制限しており、現行 checkout に certified-selection consumer が無いこともコードが明記する (`orchestrator/campaign/layer3_report.py:1004-1008`)。規律 2 の現行穴として keep する根拠は弱い。

T-470 | 反対: drop にすべき | D860 の受領証 bytes 消費義務は、certified 選択を接続する際には有効である。しかし現行 checkout にはその consumer 自体が無い (`orchestrator/campaign/layer3_report.py:1004-1008`) ため、判定理由の「現行経路」は誤り。接続時に再起票する扱いが P2 に整合する。

T-842 | 反対: drop にすべき | 恒偽の `forbidden_identifiers` は現存する (`orchestrator/campaign/p3_autonomous_workload_trial.py:1969-1976`、`autonomous_trial_completeness.py:2477-2481`)。ただし本文の削除対象は 8c autonomous trial の preview と completeness であり、段 4 の `coder_effect_gate` が使われること (`p3_s4_loop.py:801-805`) だけでは、この恒偽 field が現行 driver の certified 判定へ届く証拠にならない。D890 の整理として旧系列再開時に再起票するのが妥当。

## 総括

第 1 部 **344 項**を走査し、**6 件**に反対・疑義がある。最も重いのは **T-841**（現行 gate 結果の非束縛）、**T-1072**（trace 文字列の critic への逐語表示）、**T-2218**（現行 B-4 spec 束縛と D1531 の不一致）。

brief の **P1** は実害判定の原則として妥当だが、規律 2・6 の現行経路にある穴を「実害未測定」だけで落とす根拠にはならない。**P2** は将来の consumer にだけ必要な追加には妥当で、T-469・T-470 に当てはまる。静的照合のみで、テストは実行していない。