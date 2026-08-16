## 総括

**NO-GO。must-fix 1 件、should-fix 1 件です。** 凍結記録 g3 自体、g1/g2 の不変性、pin 閉包、D439 の land 手続には破綻を見つけませんでした。一方、運用文書が D410/D438 より前の generation 上限を現行仕様として残しています。pytest は実行していません。`tools/check_docs.py` は rc=0「違反なし」でした。

[severity: must-fix]  
[攻撃シナリオ] 改訂後 runbook を読んだ実走者が「2 世代は禁止、承認上限は 1」と信じ、正式系列を `G=1` で準備するか、正しい `G=2` を不可能として停止する。実装は既に上限 2 で、事前登録は exact `G=2` を要求するため、運用正本と実装・凍結契約が正反対になる。  
[根拠] `docs/phase3-s8c-autonomous-trial-runbook.md:120-149,227-246` は上限 1 と第二層射影未実装を現行形として記す。一方 `orchestrator/campaign/p3_autonomous_workload_trial.py:122,389-398,2436-2442` は上限 2 と射影消費を実装し、`docs/phase3-8c-preregistration.md:67-70,91-108` は exact `G=2` と閉じた第二層射影を規範化している。  
[成果物影響] runbook に従うと試行台帳の `generation_budget_per_workload` が 1 になり、その系列は正式 8c 証拠として受理不能になる。certified 選択は空のまま、材料レポートも正式 6 cell 系列を参照できない。  
[提案] runbook の該当 2 ブロックを D410/D438 後の状態へ更新する。探索例の `--max-generations 1` を残すなら「探索例として意図的」と限定し、正式系列は exact `G=2`、上限機構だけでは下限を強制しないことを明記する。

[severity: should-fix]  
[攻撃シナリオ] 後続 T-1187 の consumer 実装者が設計正本・phase doc の古い D114 記述を採用し、上限 1 の consumer や受入仕様を再導入する。  
[根拠] `docs/phase3-8c-wiring-design.md:15-24` は「固定する前提」として上限 1 を掲げ、`docs/phase3.md:470-493` も上限 1 維持を現在形で残す。D410 は上限 1 を 2 へ上げる (`docs/decisions.md:17149-17166`)。なお `docs/phase3-8c-wiring-design.md:402-405` の `TrialBinding.prereg_commit` は、現行実装を説明しており据え置き裁定は妥当である。  
[成果物影響] 将来 consumer が旧上限で作られると、exact `G=2` の trial が入口または受入で拒否され、試行台帳の受理集合と材料レポート参照が凍結契約より狭くなる。  
[提案] **scope 外・裁定パッケージ候補。** 歴史記述を遡及改変せず、両文書へ D410/D438 による supersession と現行値 2 の短い注記を追加する。

確認結果:

1. pin 閉包: live literal pin は `test_s8c_preregistration_core.py:1123-1137` の現行契約 hash と g1 歴史 pin のみ。identifier/key 検索でも追加 trust root は見つからなかった。
2. g1/g2: worktree と HEAD blob の SHA-256 はそれぞれ `a8fe5246...419`、`d3c6a3de...225` で一致。改変なし。
3. g3: generation=3、D438、全保護 hash が最終 worktree bytes の再計算と一致。`supersedes_sha256` は g2 raw bytes の SHA-256 と一致。
4. commit 境界: 現在は全差分が未 commit で、brief は凍結範囲・g3・境界テストを同一 commit とする。最終 commit 前の再確認は必要。
5. 凍結範囲: §5 欄名 hash は全世代で同値。値セルの状態も不変。§0 禁止の三軸 canonical 綴りは検出されなかった。
6. `prereg_commit`: code/test の多数の現行 consumer は T-1187 scope 外として意図的に残る。互換 alias の追加ではなく、旧単一 schema の現状である。
7. docs checker: rc=0。不存在 D、path、行番号、pin literal の違反なし。
8. doc/契約: prereg doc と契約は未配線、上限と exact `G=2` の責務分離を正直に記す。runbook のみ上記 must-fix。
9. nodeid: 親予測外の既存赤 nodeid は静的検索で見つからなかった。path 件数固定は `test_contract_path_inventory_has_expected_count` のみ、`REASON_CODES` は enum から動的導出、schema key 集合は変更なし。
10. land: D438 は g3 導入前の HEAD に実在。裁定照合は世代導入 commit の `docs/decisions.md` blobを見る (`s8c_preregistration.py:1352-1374`)。後続 fold は同一 freeze state の子孫なので g3 検証を壊さない。