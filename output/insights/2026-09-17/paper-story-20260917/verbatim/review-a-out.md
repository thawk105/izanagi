## 所見

1. **real / must-fix — K2 の「新しい値」は既評価値の再提案である。**
   **該当節:** §0 前進9、§2(c)「段4の自律ループ」、§7「前版から引き継ぐ項目」。
   **一次資料:** `output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md`「role の出力」、同 `materials/proposal-1.json`・`proposal-2.json`・`evidence/job.stdout`。
   評価した proposal-1 は `value=20`。一次資料は、fixture 既定値かつ T-2581 で評価済みの値であり、**未評価値生成の成功には数えない**と明記している。本文の「K2 の1巡が評価した新しい値」はこれと食い違う。`value=25` は次提案として保存しただけである。
   **対案:**
   > 新たに生成した提案は既評価値 `20` の再提案だった。その評価結果を次提案 `25` へ戻す往復が成立した。`25` は未評価であり、未評価値の評価や改善の実証には数えない。
   **放置時の影響:** 実測還流の成立が、新しい探索点を生成・評価した証拠へ拡張される。

2. **real / must-fix — バックアップ作成と D2077 の namespace 退避完了を同一視している。**
   **該当節:** §8 A-4「未発効である」、関連する §5 の D2077 説明。
   **一次資料:** D2077 決定2、D2078、`output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` §9、worklog entry 1577、repo 外 `run-backup/MANIFEST.json`。
   108 file の保全は確認できる。しかし一次記録は「wave worktree 側の原本は撤去まで残す」とし、entry 1577 も成果物を残した測定木とは別の clean な木から land すると記録している。D2077 が要求するのは **env の official namespace 全体の退避と、元の run・空 namespace の除去**である。バックアップの存在だけでは、この工程の完了を示さない。
   **対案:**
   > 108 file の repo 外バックアップは作成済みである。これは D2077・D2078 に従う namespace 全体の退避完了とは区別する。取得記録は測定木への原本保持を明記しており、本版では当該工程を完了扱いしない。再配置・commit・candidate 生成も未完である。
   **放置時の影響:** 成果物の保全という観測が、candidate 生成へ向かう規定工程の完了証拠へ昇格する。

3. **real / must-fix — 本文レビューの完了宣言に対応する記録が §10 に無い。**
   **該当節:** 冒頭のレビュー実施宣言、§10「敵対レビューの所見と裁定」。
   **一次資料:** レビュー対象 `2026-09-17.md` の §10 全体、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/ruling-s4.md`「plan v2」。
   現稿は「本文に対して敵対レビュー2レンズを通した」「所見の裁定は§10に置いた」と書くが、§10 は段2・段3・段4直前の起点更新で終わっている。段6の所見・裁定は未収録である。
   **対案:** レビュー中は次へ訂正し、凍結前に実際の所見と採否を追記する。
   > 骨格に対する敵対相談は完了した。本文レビューは実施中であり、その所見と裁定は凍結前に本節へ記録する。
   **放置時の影響:** 本文の検証履歴を、参照先で追跡できないまま完了済みと主張することになる。

4. **real / nit — 「refuted は1件」は母集合が曖昧である。**
   **該当節:** §10「段3 — 骨格に対する敵対相談」。
   **一次資料:** `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/codex/consult-a-out.md`。
   同資料には、引き写し所見4の「旧版58項」に加え、正しさ所見3の「T-2630 を理由とする A-2/A-6 の認証取消し等」も `refuted` と明記されている。
   **対案:**
   > 段4の裁定一覧で refuted として個別計上したのは「前版§7の58項」の1件である。レンズA原文では、認証取消し等への拡張案も refuted とされている。
   **放置時の影響:** 科学的結論は変わらないが、相談原文と裁定一覧の件数が一致しなくなる。

## 照合して一致を確認した範囲

- **official 床値:** repo 外の原本 `run-backup/run_dir/result.json` と repo 内射影を照合。rr20 **35,817.945**／rr80 **46,065.78**、`scale_ref` **1,193,931.5／1,535,526.0**、配線下限 **0.03**、記載された `u_noise` 範囲が一致。12 cell 全件 valid・各 `n_valid=8`、CV **0.002262…〜0.012362…**。registry は **481行＝1＋96×5**、terminal 96件すべて `observed`。snapshot の ledger **72→84**、attempt-ledger **516→612**、request **1818.nqsv**、Elapse **4769秒**も一致。バックアップ manifest は108件。
- **初投入日・祖先性:** C3b §2 の **2026-09-09 22:09 JST／988501.nqsv**を確認。`git merge-base --is-ancestor ce2769c32 af3762d62` は **rc=0**。entry 1450 の D2 一括統合記録も確認。
- **右 tail:** 権威 JSON・DAT・complete の SHA-256 は記載と一致。3 workload 各6区間、計 **18区間すべて `declining`**、集団 verdict、空の failures、`performance_certified=false` が一致。格子8点・24 cell・120性能標本を確認。DAT の整数カウンタから throughput と abort 率の平均を再計算し、統制稿の24行の表と一致。1250→9999 µs の throughput は3 workload とも半分以下。
- **右 tail correctness:** **120記録すべて certified・anomaly 0・serializable**。全 campaign の legacy 条件は **4 threads・200 tuples・rr50・rmw・1秒・max ope 5**。本文は性能条件の認証へ昇格させていない。
- **較正:** 現物 **8 record**。旧 rr50 2件、silo rr95・rr5各1件、非 silo 4件。rr5 は **2,000,000 records／LLC miss 1.566765…%／CV 0.970683…%**。非 silo の LLC miss／CV は、mocc rr50 **14.8213／1.4348%**、rr95 **17.0084／1.7204%**、tictoc rr50 **7.9688／2.2160%**、rr95 **9.5573／0.8336%**で本文の丸めと一致。
- **T-2630:** 8変異の台帳は期待署名一致8・MISMATCH 0。到達5変異の名前、M4のcompile失敗、M4bのsource水準の限定、M6のTRACE側の境界を一次記録と照合。F1016・entry 1580・[T-2731] は実在し内容も対応。A-2/A-6の取得済み判定を取り消す根拠にはしていない。
- **K2・B-4・8c:** K2のjob **1216.nqsv**、**719,324.5 tps／CV 1.70%**、proposal-2 **25・未評価**を確認。B-4のrecordは指定pathに存在しexact 12 key。repo外binaryは **701,760 bytes**、SHA-256もrecordと一致。配置規則はD2069と一致。8c §5は **9欄中8欄未記入**、記入済みは `no_hypothesis_test`。コードの充足可能集合は `{"C10"}`。
- **A-2／A-6／T-1998:** 権威成果物の6 cellのmedian・効果量・status・`bound`・correctness反復数が本文と一致。T-1998原本の両腕5標本・median・ratio・improvement・再計算CVも一致。producerの `complete` とconsumerの `accepted` は区別されている。
- **裁定参照:** D2016／D2026／D2027／D2049／D2050／D2053／D2069／D2072／D2077／D2083、およびD2044項3・8・9・11・12・13・14・25・36を照合。所見2を除き、確認した要約の射程は対応する。
- **件数・README・凍結物:** §0は14点、§2(g)は11点、§2(e)の列挙は5件、§7は58＋9項、§9は7種。results現物・README表とも7稿。§2(e)の「5度」は本文が列挙する2件＋一括裁定3件として整合するが、全履歴での網羅性までは再監査していない。READMEの訂正3件・stale 0件は新版と対応。恒久erratum節とresults節はHEAD比で不変。行番号形式の参照は検出なし。
- **変更範囲:** `git status` はREADME更新と新版新規の2 fileのみ。tracked差分はREADMEだけ、staged差分なし。旧版・results・figures・claim-evidence・paper-story-backoffに差分なし。

## GO / NO-GO

**NO-GO。現稿のままの凍結は不可。**

must-fix は所見 **1〜3**：

- K2の既評価値20を「新しい値」とする記述。
- バックアップ作成をD2077の退避工程完了とする記述。
- §10の本文レビュー記録の欠落と完了宣言。

## 総括

主要な数値群と判定は、照合した一次資料に一致した。
B-7非充足、床値案未発効、legacy correctnessの限定、3走行非poolは維持されている。
必要な修正は、到達範囲と検証履歴の記述である。
凍結物の変更、追加測定、新しい検査機構は必要ない。
全旧来項目の全数値・全参照を網羅監査したという保証ではない。
書き込み・commit・push・pytest・build・測定は行っていない。