**現時点の着地判定はNO-GOです。** A-S1のREADME側例外は解消し、F-MF1も局所修正されています。ただし、F-MF1の実走完了と、稿が参照するwave insightの着地が未確認です。数値・図・caption・hashの不整合は見つかりませんでした。

参照略号：

- [D：結果稿](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md)
- [G：生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/tools/plotting/plot_a1_sized_paired.py)
- [T：対応test](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/orchestrator/tests/test_plot_a1_sized_paired.py)
- [R：paper-story README](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/docs/paper-story/README.md)
- [F：figures README](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/docs/paper-story/figures/README.md)

**対応表：closed 11／partial 1／regressed 0。** closedは所見への修正・現物整合を確認した意味で、今回のpytest成功を意味しません。

| 所見 | 判定 | 現物の根拠 | 値・受理集合・参照への実害と解消状況 |
|---|---|---|---|
| A-M1 | closed | D §2.4。公開leafのWAL収録30 record中、verify_done 6件ともanomalies=0 | anomaly情報の所在を誤案内する記述を訂正済み |
| A-M2 | closed | D冒頭・L-A1S-20・§5.5。mtime記録から922秒を再計算 | 所要時間をaccounting由来や再投入予算へ一般化する誤りを除去 |
| A-M3 | closed | D L-A1S-13が「衝突不在は…確認できない」と明記 | publishの保証範囲の過大主張を除去 |
| A-M4 | closed | D L-A1S-2はpolicy・事前登録・裁定を参照 | stale注記を認可・利用範囲の根拠にする参照を訂正 |
| A-S1 | closed | R:257–259にresult.jsonから数値・hashを得る個別扱いを明記。D §2.6と一致 | 系列規則に従って稿へ図provenance hashを追記し、循環を作る誘導を解消 |
| A-S2 | closed | D §0.3とclaim-evidence `2026-08-26.md` C1行の旧3値が一致 | 旧値を本attemptの測定値と取り違える参照を訂正 |
| A-N1 | closed | intent canonical digestとfile bytes hashを独立再計算し、Dと一致 | 異なるhashの用途を混同する記述を解消 |
| B-MF1 | closed | G:397はgenerator pathだけ照合。生成時hash記録とT:370の変更正例を維持 | 現行generator hash相違だけによる過剰拒否を除去 |
| B-MF2 | closed | T:381のPNG/PDF path完全一致をT:477から使用。別directory負例あり | 同名の別画像による着地bundleの代用を拒否する構造 |
| B-S1 | closed | T:480–486がREADMEの3 hash行を検査。最終bytesと独立照合済み | READMEが別の成果物を指す参照ずれを検出可能 |
| B-S2 | closed | T:463–466で区間両端を照合。全6端点を再計算 | 稿の区間だけが誤っても通る検査漏れを解消 |
| F-MF1 | **partial** | T:475の存在assertへ無条件到達。全欠落負例と部分欠落全6集合を追加 | 全欠落でclosure全体をskipする経路は除去済み。ただし新しい負例・M13の実走終端未確認 |

**公開leafからの独立再計算結果**です。生成器を呼ばず、raw_tpsから算出しました。単位はtps、表示は小数第3位までです。

| workload | 対差平均 | h | B | 平均±h |
|---|---:|---:|---:|---|
| write-heavy | 1,591,948.500 | 23,911.503 | 68,795.219 | [1,568,036.997, 1,615,860.003] |
| balanced | 448,830.167 | 28,351.599 | 115,876.896 | [420,478.567, 477,181.766] |
| read-heavy | −576,749.767 | 32,963.699 | 310,204.402 | [−609,713.465, −543,786.068] |

3件とも`abs(mean) − h > B`、標本sdは計画sigma未満です。分類`resolved-above-floor`、符号+/+/−、`variance_plan_breach=false`と一致しました。

さらに、稿の180標本・90対差、6 armの平均・最小最大・中央値・cv、verify_doneのcommits／aborts／anomaliesを照合しました。provenanceのcells・描画系列、captionの丸め値、稿の表にも不一致はありません。最終PNGを目視し、PDFのラベル抽出も確認しました。

最終bytesのSHA-256は、READMEおよびprovenanceの該当欄と一致しています。

| 成果物 | SHA-256 |
|---|---|
| PNG | `7bbf0b16c856e9534577b100dc783f9b97b337adb9c9675772eeb4cf7956ce95` |
| PDF | `a2db2577f1db830c8fd252dccde496e004738e779fcb8fbf5f8ddb8965a7ade7` |
| provenance | `6e386d42457b154c9c58910bc1905df0947e7988f980237381cb6116e5ebf5ac` |
| caption_sourceの稿 | `67e8c53cbfe27a33fa51d55744364050cadbd1e83e605c0f9c06477f882d8e2e` |

全存在の現物は揃い、path・hash・caption・数値の整合を確認しました。全欠落・部分欠落は存在assertで拒否される構造ですが、負例の実走成功とは扱っていません。

生成器は旧impl tip `1c991c0cc`から不変です。回収fixはskip除去と欠落回帰検査に限定され、入力predicate・verifierの変更、汎用framework・追加gate・台帳の新設はありません。規律2のcertified検査と`formal=false / promotion_prohibited=true`を維持しています。開始mainとの差分でも、既存の図・結果稿・公開leaf・policyの変更はなく、figures READMEの既存行削除もありませんでした。

**残件は次の2点です。**

1. **R-M1：着地前must-fix―稿の参照先が未存在。** D §5.3が挙げる`output/insights/2026-09-18/t2775-a1-sized-results-draft/README.md`は現在のworktreeにありません。
   **実害：** 読者が稿から検算・レビュー記録へ辿れません。予定済み記録の着地で解消でき、追加frameworkは不要です。
2. **親担当の実走終端。** 読み取った`focus-tests-1.log`はrequest `6379.nqsv`の`QUE`まででした。全存在正例、欠落負例、M13、新旧挙動差、継承M0〜M12について、実走完了をこのレビューでは確認していません。

## 総括

**修正内容の静的レビューは良好ですが、現時点のlandはNO-GOです。** 既存11件は解消、F-MF1は実装済み・実走未確認です。参照先の記録を着地させ、親担当の検証終端を確認する必要があります。

今回は読み取り・独立再計算・画像確認のみです。ファイル変更、pytest、変異実走、子の起動は行っていません。
