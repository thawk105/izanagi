## 総括

静的レビューでは、本走に必要な部品に加えて、score の実行不能と系列終了 event の欠落を確認した。report の新テストは台帳形式と一致せず、生死確認 3 系列の job Elapse と見積りの取り直しも、この差分にはない。新テストは 19 関数あるが、実行していないため所要時間と 60 秒以内という裁定への適合は判断できない。

## 所見

1. **must-fix — score が実行できない。** `tools/pegasus/silo_policy_contrast_launch.py:153-154` は `endpoint-fixed` に `endpoint` を入れるが、`orchestrator/campaign/p3_s4_loop_policy.py:807-813` は event 直下の `logical_slot` を読む。**成果物への影響:** endpoint の score が止まり、certified 選択を report の比較値へつなげられない。**推奨: 縮小** — 保存形と読取りを一つの契約に揃える。

2. **must-fix — 通常の系列終了が記録されない。** `orchestrator/campaign/silo_policy_contrast.py:184-189` は score 完了後に `None` を返すだけで、`series-end` を書く経路は親の役割失敗時（`tools/pegasus/silo_policy_contrast_parent.py:65-67`）しかない。report は終了理由が無い系列を欠測にする（`orchestrator/campaign/silo_policy_contrast_report.py:110-111`）。**成果物への影響:** 完走系列と参照系列を report が欠測扱いする。**推奨: 縮小** — score・参照の完了時と retry 枯渇時の終了記録を系列制御へ集める。

3. **must-fix — 429 後の成功を outage と返し得る。** `tools/pegasus/silo_policy_contrast_parent.py:51-60` は成功時に、その機会の *過去* の `opportunity-end` も完了判定へ使う。429 の `outage` event だけが残ったまま正常終了すると、その `outage` を返す。**成果物への影響:** A の消費と候補の有無が親の戻り値・台帳で食い違う。**推奨: 縮小** — 今回の起動で増えた event だけを判定する。

4. **must-fix — report テストが台帳 reader の形式を満たさない。** `orchestrator/tests/test_silo_policy_contrast_report.py:17-18` の fixture は event file に `event_seq` を書かないが、`orchestrator/campaign/silo_policy_contrast.py:50-54` は必須としている。**成果物への影響:** 新 report テスト 2 本は統計判定まで到達できない。**推奨: 再利用** — fixture を `ContrastLedger.append` で作る。

5. **should-fix — 同じ状態判定を複数箇所で持つ。** A・B は `orchestrator/campaign/silo_policy_contrast.py:103-106` と `orchestrator/campaign/silo_policy_contrast_report.py:117-118` で別計算し、未終端 slot も前者 `:101-102,147-149` と `orchestrator/campaign/p3_s4_loop_policy.py:778-781` で再判定する。**成果物への影響:** 台帳・job・report の使用予算や停止理由がずれる余地がある。**推奨: 再利用** — `series_state` の判定を使う。

6. **should-fix — 原提案番号 a の導出が分散する。** launcher は `series_state()['A'] + 1`（`tools/pegasus/silo_policy_contrast_launch.py:69`）、driver の却下記録は独自の event 集計（`orchestrator/campaign/p3_s4_loop_policy.py:1003-1007`）を使う。**成果物への影響:** 同じ却下の履歴行と台帳 event に異なる a が付く可能性がある。**推奨: 再利用** — 系列制御に a の導出を一箇所だけ置く。

7. **should-fix — 既存の台帳・IR 射影を重複実装している。** create-only の `_publish` と event 読込み・追記（`orchestrator/campaign/silo_policy_contrast.py:22-85`）は `t2849_comparison_harness.py:49-89` の形を再実装している。`silo_policy_contrast_generators.py:20-25` の `tagged` も `p3_s4_loop_policy.py:82-88` の `_tagged_ir` と同形。**成果物への影響:** 削減しても台帳・候補の内容は変わらず、形式変更時の修正箇所が減る。**推奨: 再利用**。

8. **should-fix — 研究成果物はまだ揃っていない。** 差分の 19 file は実装とテストで、生死確認 3 系列の job Elapse、§11.3 の再見積り、§12 の発効束は含まれない（`docs/silo-policy-generator-contrast-preregistration.md:380,433-452`）。report も要求された A 使用数・拒否の検査段別内訳を集計していない（`orchestrator/campaign/silo_policy_contrast_report.py:117-131,203-220`）。**成果物への影響:** 発効と n の裁定に必要な実値を提示できない。**推奨: 縮小** — 追加の一般的な gate より、指定された実測と報告項目を優先する。

9. **nit — テスト量の上限は静的には確認できない。** 新規は 19 テスト関数とパラメータ展開（例: `orchestrator/tests/test_p3_s4_loop_job_contract.py:1508`）だが、所要の記録は差分にない。**成果物への影響:** 全体 5 分・新規 60 秒以内を圧迫するか未判定。**推奨: 縮小** — まず所要を測り、重なる境界のケースだけ整理する。