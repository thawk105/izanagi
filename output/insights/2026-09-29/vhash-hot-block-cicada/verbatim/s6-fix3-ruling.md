# 段 6 fix 裁定 3 — 本走 trace job 0 の停止 (壊し版の integrity 違反で例外)

2026-09-30 01:55 JST / 親。tip d109d4078、計測木 vhb-m0、trace0b = 36734.nqsv (bnode005、Elapse 224 s、rc 1)。

## 事実 (raw-trace-0.json と完全 stderr: vhb-m0/output/pegasus-dispatch/ae871cd245a1d525f295473e7c4d12ad/)
- 5 腕 (K0/1/2/4/8) × T1・T2 の trace 10 走: すべて verdict indeterminate、巡回 0、integrity clean。
- broken-B1 T1: non-serializable、巡回 10、事象 reached/changed/committed = 100,537/100,537/100,537、帰属 witness 10。
- broken-B2 T1: non-serializable、巡回 3、事象 1,447/1,443/71、帰属 witness 3。**事前予測 (committed 0、検出 0) は外れた。**機序は未特定。
- 次の壊し走 (順序から broken-B1 T2 とみられる) で driver が `trace integrity failed: commits=446733 rows={C 446733, R 2941511, W 1041897, E 446733} integrity={clean False, orphan_reads 50, ...} notes ['988 cy…` の RuntimeError を出して job ごと停止し、B1 T2・B2 T2 の記録が無い。

## 裁定
- real・本 wave 帰属 (driver が壊し版の走にも integrity clean を要求して例外にしていた)。先例 md_17 は orphan read を壊しの検出として記録している。md_3 の段 6 裁定は「壊し run 自身の integrity 数値 0」を分類「期待した経路で検出」の条件に加えたが、例外で走を捨てるのではなく分類に使った。
- 直し (F5、driver と test だけ): 壊し版 (broken) の trace 走は、integrity が clean でなくても判定器の結果 (verdict・rc・total_cycles・integrity の全 field) と事象・帰属を記録して job を続ける。stock / K の trace 走は従来どおり clean を要求 (変えない)。aggregate の壊し判定は、裁定 §3 の 3 条件 (committed ≥ 1・non-serializable・帰属 witness ≥ 1) に加えて、integrity の状態を別の欄で出し、分類を「巡回で検出・帰属あり (integrity clean)」「巡回で検出・帰属あり (integrity 違反あり: 種類と件数)」「integrity 違反のみ」「未検出」に分ける。
- 取り直し: F5 の統合後、同じ out/main (同じ binary) で trace job 0 を再走する (1 job、約 4 分)。旧 raw-trace-0.json は raw-trace-0.first.json として保存し、一次資料に初回の記録として残す。
- 変異: M11 = 壊し版の integrity 違反で例外に戻す → 新 test が赤 (単一理由を確認して登録)。
- B2 の予測外れは一次資料に「予測・観測・未特定の機序」として書く。予測を後から書き換えない。
