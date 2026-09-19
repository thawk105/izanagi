## 検算表

値の対は、特記しない限り fixed-5 / fixed-10 の順。丸めは原データの集計後に行った。

| 項目 | 文書の値 | 一次資料からの再計算値 | 判定 |
|---|---|---|---|
| 1. 校正表18行 | README §5.1の全cell、results §3.1 | commit・各wall・rc・verdict・certified・anomaly・GiB換算・eligible・stop・outcome・nodeを再生成。全cell一致。実走16件ではcommit witnessとC行数も一致 | 一致 |
| 1. 校正集合 | 両候補とも `{3,6}` / `{3,6}` / `{3}` | workload順に同値。`chosen_max_eligible`＝6 / 6 / 3、`indeterminate_count`＝1 / 1 / 0。各`F_s`もsetup＋hydrate＋buildと一致 | 一致 |
| 2. 共通部分・extime | `{3}`、3 s | 両候補とも `{3}`、3 s、段下げなし | 一致 |
| 2. 本走見込み | 6346.534 / 5998.965 s、F̂＝31.140 s | 6346.533662369 / 5998.964904023 s、F̂＝31.140494913 s | 一致 |
| 2. 見込み内訳 | `summary-A`のT / A / F | fixed-5＝5856.162 / 303.529 / 186.843 s、fixed-10＝5522.493 / 289.629 / 186.843 s | 一致 |
| 3. 校正Elapse | 6462 / 6339 S | fixed-5＝1445＋955＋4062＝6462、fixed-10＝1351＋925＋4063＝6339。request 10868〜10873の対応も一致 | 一致 |
| 3. 校正runner wall | 6447.5 / 6324.9 s | 6447.466368417 / 6324.866527141 s。`summary-A`の6447.466 / 6324.867とも一致 | 一致 |
| 4. 本走job表12行 | request・node・開始終了時刻・Elapse・wall・固定費 | 全12行をlogとjob.jsonから再生成し一致 | 一致 |
| 4. 本走消費 | Elapse 6316 / 6134 S、runner 6288.1 / 6105.7 s | Elapse同値、runner 6288.106104058 / 6105.657509023 s。各候補14400 S以下 | 一致 |
| 5. workload別集計6行 | commit範囲、verifier最小・最大・中央値、maxrss範囲、時間和 | 48記録から再生成し全6行一致。Σ処理時間＝965.1 / 1366.3 / 3458.6 / 974.5 / 1335.5 / 3306.7 s、Σ保全＝41.5 / 65.8 / 198.5 / 42.4 / 65.0 / 189.2 s | 一致 |
| 5. 本走全件の条件 | 48枠すべてattempt 1、rc 0、serializable、certified、anomaly 0、保全・identity一致 | 重複なし48枠。全条件48/48一致。指定integrity項目も全件正常 | 一致 |
| 6. 最終判定 | 各候補pass、判定集合30、anomaly 0、未完走2、未実走1 | 本走24＋校正完走6＝30。operational indeterminate 2、CLI indeterminate 0、not_run 1。最終summaryと一致 | 一致 |
| 6. ruling束縛 | 校正18、本走48、許可sha 2種 | 候補ごと校正9件が`2f9d8eb1…`、本走24件が`1ddd2386…`。v1は両候補`undetermined`、理由は`ruling sha mismatch`のみ | 一致 |
| 7. runner・裁定・summary hash | v1 1301行／`91bbf85d…`、v2 1384行／`c960093d…`等 | 行数・記載された全桁sha一致。summary A/B/B-fix1＝`0ed068a6…` / `723d8112…` / `f7248a7f…` | 一致 |
| 7. identity・環境 | `678b7203…` / `16c29935…`、HEAD・patch・module 9件・toolchain | 全記録のbuild前後identity一致。fixed-5はT-1998 §5と一致。A-2旧token 2種もcertification.jsonと一致。18 jobの環境束縛は同一、binary shaは18種類。Pythonは3.10.12 | 一致 |
| 8. 保全 | 3072 files、213,338,672,445 → 48,928,578,277 bytes、4.36倍 | 64 manifest×48 files＝3072。同bytes、比4.360205834 | 一致 |
| 9. 段A時刻 | 22:46〜00:02 JST | Created＝9/19 22:46:34、最初のStarted＝22:49:38、最後のEnded＝9/20 **00:01:24**。summary生成＝00:02:02 | **終了と集計の時刻が混在** |
| 9. 段B時刻 | 00:04〜00:43 JST | Created＝00:04:14、最初のStarted＝00:04:23、最後のEnded＝00:43:04 | 一致 |
| 9. 裁定・確定時刻 | resultsの裁定22:20、extime確定00:05 | 裁定原文は**22:2x**。追補見出しは00:05だが、summary生成00:02:02、段B投入00:04:14 | **精度・時系列に問題** |
| 10. CPU時間 | README §5.3：6 s走822 / 824 s | `ru_utime`＝**816.686709 / 824.115233 s** | **不一致** |
| 10. 実走件数 | 「校正18走」「全66走」 | 校正18記録＝**実走16＋not_run 2**。本走48を合わせ実走64、記録66 | **実走と記録の区別が必要** |

## 所見

1. **must-fix：CPU時間の転記誤りと定義の曖昧さ。**
   [README §5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/output/insights/2026-09-20/verify-phase-adopted-backoff/README.md:116)のfixed-5・6 s走「822 s」は誤り。ユーザーCPU時間なら約817 sである。また「520 / 522 s」「824 s」は`ru_utime`相当で、総CPU時間ではない。総CPU時間（user＋system）は、10 s走546.951108 / 549.039274 s、6 s走884.363693 / 892.184007 s。使用する定義を明記して統一すること。

2. **must-fix：時刻を一次資料の精度とイベントに合わせること。**
   [results §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md:81)の「22:20」は、原文「22:2x」からは確定できない。§3.1の「00:05確定」も、00:04:14の段B投入より後になる。計算結果は00:02:02のsummaryに存在するため、追補の記載時刻とextime決定時刻を区別する必要がある。段Aの「00:02」もjob終了ではなく集計時刻として説明すること。

3. **must-fix：18／66を「実走数」として扱わないこと。**
   README §4.3・§9、results §0.1、paper-story READMEの2026-09-20行にある「18走」「66走」は、`not_run`を含む記録件数である。「校正18枠・16実走・2未実走」「全66記録・64実走」とすると、保全64走との関係も明確になる。判定集合30件／候補の計算自体は正しい。

4. **should：校正＋本走の合計消費を追記すること。**
   段4裁定§3.1は両者の和も報告すると定めるが、対象稿には明示されていない。dispatch Elapse合計はfixed-5 **12,778 S**、fixed-10 **12,473 S**。本走だけの予算判定は正しく、変更不要。

5. **should：未照合事項を「全件確認済み」に含めないこと。**
   selftest件数42／49はコードの呼出しと反復から整合するが、指定一次資料だけでは過去のPASS実行結果までは検証できない。旧校正433.3／974.7 s、起点の`a99425b66`、背景job識別子等も、今回指定された直接記録では独立確認できない。これらは主要測定値の一致とは別に、出所確認が残る。

主要な件数・sha・extime・消費について、文書同士で異なる値を記す箇所は認めなかった。ただし、上記の時刻・実走件数の問題は複数文書に共通している。

## GO / NO-GO

**NO-GO。** CPU時間に数値の不一致がある。時刻と実走件数の表現も修正が必要。

## 総括

校正表・本走表・集計・予算・保全量・主要hashは独立再計算と一致した。
両候補のpass、判定集合30件／候補、anomaly 0という結果は原記録に整合する。
CPU時間の誤記、時刻の精度と時系列、記録件数と実走件数の混同を修正して再レビューすること。
ファイル変更・測定・テスト実行は行っていない。