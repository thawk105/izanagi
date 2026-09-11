---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2397-a1-attempt4
seq: 1
title: [T-2397] A-1の二停止原因を閉じ、attempt-0004を全3 workload validで完走した
---

## 本文

- D1936項3の実装を開始したが、実buildも未patch sourceを使い、修正すると凍結tracked-cleanと
  衝突することをplan/敵対相談で確認した。提示した整合案への続行指示を受け、旧登録bytesを
  保存したsource追補で実装した。決定は {{D:a1-fixed-patch-source}}。
- 既存materializer/独立期待tree/依存stagingを再利用。関門・実build・consumerを同じsourceへ
  揃え、任意追加差分、HEAD/root違い、verifier anomalyの拒否とT-2514の全detail保存を維持した。
- 独立review-aはmust-fix0。review-bのescape所見は親/別CodexのASTで反証し変更しなかった。
  実測で見つかったstudy再選択、追加Git spawn、既存sink行番号のずれはCodex fixで局所修復した。
- 親の関連走はA-1 203passed、job 171passed、campaign 414passed/3skipped。
  制約4fileと実機source probeは111passed/1skipped、request991844/bnode001、213.72秒。
  全6armの供給/意味12recordがgreen、admission3件true、trace/perf build計12件と既存verifyが通過。
- 変異の最終単体群はrequest991859、baselineと6件の全期待nodeが一致、wrapper rc0。
  実機群はrequest991865、baseline通過、prefix脱落と未patch root差戻しをそれぞれ拒否し、
  M1/M2とも期待node一致、wrapper rc0。意味的な挙動6件と構造/診断2件を区別する。
- 初期の検査赤はF763/F764/F785の再発も含んだ。既存の検査・環境契約を弱めず、
  commit固定、専用TMPDIR、独立cloneで再検証した。終了済みjobの2形式holdは
  終端・request hash・clean/HEADを確認して解除し、手動qdelやF47解除は行わなかった。
- 既存submitでattempt-0004だけを投入。source a9d20d701、request991875/991876/991877、
  nodes bnode023/bnode026/bnode027。全jobのready/bench-startを確認し、全driver_rc0で終了した。
  complete/materializeもrc0、complete/all_workloads_terminal=true、
  write-heavy/balanced/read-heavyが全てvalid=true/errors=[]。各60対のpilotを保存した。
- 成果物 = output/insights/2026-09-01_paper-story-a1-balanced5-pilot/。
  sizing-pilot.jsonを生成。性能優劣の結論・正式結果への昇格・追加試行はしていない。
  実装/相談/検査/生証拠の所在 = output/insights/2026-09-11/t2397-a1-attempt4/README.md。
- 最終受入は記録commit固定後に既存acceptance経路で実行し、耐久receiptを共通landが検証する。
  初回はmain取込のphase文書競合で子テスト前に停止。両checkpointを残し、自動結合testの
  2親統合を別Codex authorが作成してbyte一致を確認した後、同waveで受入を再開する。
  改善候補は、並行waveの変異開始時に既存F785の独立clone手順へ導く参照の明確化を1件記録した。
  改善実装・次wave起動・pushは行わない。

## 次の一手差分

### 完了

- [T-2397] 登録済みA-1 pilot attempt-0004を全3 workload validで完走し、sizing入力を生成した。
  remaining: none
  base: 879cfd0ee8afc71da65cbbd34ef78330e1648964500c6ffbf08b7401cd10cbaa
- [T-2512] 既存の依存供給をA-1条件関門と実buildへ接続し、実機と変異で検査した。
  remaining: none
  base: 5b59979b64f9bf5b2815df38e3853bbfa819fc189e863f50d00d327de71f5568
- [T-2513] 指定patchだけを適用した実sourceを関門/build/consumerへ揃え、実機と変異で検査した。
  remaining: none
  base: ae6cb4144132912c798277ec2220b11ba0775541f1dfdb2a3e35465bced4b9fd
