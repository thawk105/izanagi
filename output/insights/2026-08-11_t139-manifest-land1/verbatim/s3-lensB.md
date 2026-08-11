結論は **NO-GO**。read-only の静的監査のみで、pytest・PBS投入・受入全走は実行していない。hash、import、算術だけ確認した。

## R4 の再利用境界と pilot 1 本の最小集合

| 層 | 再利用できる資産 | 新規に必要な部分 |
|---|---|---|
| submit / durable intent | `submission.py:143–173`、`qsub_binding.py:44–93` | T-139 manifest・a13・intent と qsub の束縛 |
| PBS / driver | `t139_positive_control_probe.pbs:53–93,316–338`、`r4_env_probe.py:1245–1415` | 36 run、a09、a03 phase、失敗分類、pilot receipt |
| collector / writer | `collector.py:246–268,524–608,1439–1883`、`atomic_publish.py:24–123`、`artifacts.py:384–536` | T-139 schema、a04、a13全履歴、binding-required sink |
| iteration verifier | `t126_driver.py:186–318,480–679`、`r4_env_probe.py:595–700,1418–1475` | 3 arm×trace 0/1 の6 build、correctness 2×3、a05再hash |
| certified consumer | 現行 T126 は `evidence-only/no-promotion` (`t126_driver.py:1227–1246`) | U8/U9 の J・certified選択・材料report・試行台帳 |

pilot 1 本を受領証検証まで通す最小集合は、U0–U6相当（manifest、resolver、schema/semantic verifier、a13予約、intent/PBS、verification allocation、pilot driver、collector/writer）である。ただしこれは certified 選択を変えない。a10 は適格 pilot 8 本を要求するため、U8/U9が必要になる。

時間算術は次のとおり。

- 性能割当て: `36×15=540`、待機 `24×30+11×60=1380`、非余裕小計 `2400`、`2400+900+300=3600`。
- 検証割当て: `180+1440+360+360+180+120=2640`、従って `2640+660+300=3600`。
- 追補本文の `(B) 2340` は誤記（`addendum-a-reissue.md:105–119,132–134`）。
- 全走は予備なし9割当て、最大11割当てで、aggregate は9時間／11時間。1 session の上限時間が定義されていないため、「必ず収まらない」という結論は証明不足。ただし現状の計画は GO を証明できない。

## 所見

[blocker] **RI-B1: reissue が旧受理条件を暗黙参照している。**  
根拠: `s2-plan.md:36–57`。  
失敗シナリオ: 旧 blob を逐語有効と解釈する consumer と、新 blobだけを読む consumerで `planned_execution`・qsub失敗行・intent の受理集合が分かれる。  
影響: 同一 manifest でも受領証の accepted 集合と参照 blob が一意に定まらない。

[blocker] **RI-B2: nested exact closure に未定義 key と内部矛盾が残る。**  
根拠: `s2-plan.md:59–72`、`a01:105–119`、`a05:309–329`。  
失敗シナリオ: `cluster_slot`、actual run、correctness scope、3 arm×3点の binary rehash、a10の fixed input が schemaに表現できない。  
影響: 正しい receipt が拒否されるか、不完全な receiptが通り、schemaの受理集合が固定できない。

[blocker] **RI-B3: marker 不在だけで pre-performance と分類しており a04 に反する。**  
根拠: `s2-plan.md:74–86`、`addendum-a-reissue.md:259–306`。  
失敗シナリオ: markerを削除した後に性能 rawだけ残した attempt が、予備置換可能な pre-performance failure になる。  
影響: reserve 使用可否、attempt 状態、試行台帳の post-performance 件数が変わる。

[blocker] **RI-B4: a13 が current tip 重複しか検査しない。**  
根拠: `s2-plan.md:88–92`、`addendum-a-reissue.md:919–929`。  
失敗シナリオ: 過去の予約行を削除して同じ `(family_root, ordinal)` を再登録する。current tipには重複がないため通る。  
影響: `k`、`alpha`、reservation commit/digest の参照が履歴依存で変わる。

[blocker] **core の合成 digest は approval-ready ではない。**  
根拠: `preregistration.md:331–334` の行は実測で450行中333行目に残り、sha256は `a7852ad9…`。`addendum-a-reissue.md:825–838` は較正を与えないと明記する一方、`erratum.py:397–447` の draft erratum は承認集合外 (`erratum.py:34–39`)。  
失敗シナリオ: `dfb821…` を固定しても、§7はstress check、§14はcalibration specificationを要求する。  
影響: approved core blob、erratum digest、composed digest、land1のdecision参照が成立しない。

[blocker] **Draft 2020-12 schemaを現在の検査実体で再現できない。**  
根拠: 実環境は `jsonschema 3.2.0` で `Draft202012Validator` 不在。既存経路は `artifacts.py:630–653` と `collector.py:287–300` の Draft7。  
失敗シナリオ: `unevaluatedProperties` 等を含むschemaをDraft7で読むと、実装ごとに未知keyの受理が変わる。  
影響: land1 schema blobの承認結果とland2 receipt受理集合がvalidator依存になる。

[blocker] **a09の論理導出は決定論的だが、schedule tableのcanonical bytesが未定義。**  
根拠: `addendum-a-reissue.md:552–605`。seed hash、ASCII preimage、digest比較、tie-breakは再導出できたが、`schedule_sha256` の対象となる表の改行・区切り・JSON/TSV形式・key順がない。  
失敗シナリオ: 同じ18個の順列をJSONとTSVで出力すると、論理scheduleは一致するがsha256が異なる。  
影響: receiptの `schedule_sha256` をvalidatorが独立再計算できず、schedule受理集合が閉じない。

[blocker] **変異の単一理由帰属が未証明。**  
根拠: `s2-plan.md:670–713`。`blobref.py:89–135`、`erratum.py:477–508`、既存T126のdurable binding検査が前後に存在する。  
失敗シナリオ: M1/M2/M4をresolverだけ変えても、固定blob digest・composed digest・writer再検査が先に拒否し、期待node以外が落とす。M14/M15/M21/M25もintent、collector、writer、reportの重複gateがある。  
影響: mutationの「当該nodeだけが落ちる」という受理集合差分を主張できない。M26も、実際の承認経路は caller-selectable な `require_exact_fields` ではなく固定集合の `require_approved_addendum_a_fields` (`addendum_envelope.py:152–186`) であり、wave前実コードと同型ではない。

[must-fix] **a01本文の検証割当て小計を訂正する必要がある。**  
根拠: 算術 `180+1440+360+360+180+120=2640`、本文 `addendum-a-reissue.md:115` は2640、同132–134だけ2340。  
失敗シナリオ: plannerが2340を内部deadline計算へ使い、実際のphase余裕を300秒過大評価する。  
影響: 検証割当てのbudget表、receiptのphase cap参照、受入記録が不一致になる。

[must-fix] **a03の10秒窓はhard capと算術矛盾しないが、実装境界の表現が危険。**  
根拠: `a03` は `[150,160)`、判定 `[160,165)`、marker `[165,170)`、TERMは170 (`addendum-a-reissue.md:171–182`)。  
失敗シナリオ:一般的な「cap末尾10秒」を実装して `[170,180)` を読むと、判定・markerの時間がなくなる。  
影響: raw windowのrun対応、a04のpre/post分類、36窓の完全性が変わる。

[must-fix] **単独性確認とa03静穏窓は両立するが、既存probeは単独性gateではない。**  
根拠: Exclusive submitはOFF (`pegasus-runbook.md:45–48`)、r4のforeign process情報は `diagnostics_only` (`t139_r4_env_probe.py:874–933`)、同probe自身もscheduler-backed ledgerを持たない (`:1810–1815`)。  
失敗シナリオ: pgrep後に同一nodeへ別jobが開始する、または8本を並列投入して同一nodeを共有する。  
影響: a03のbusy値と実測runの外乱が分離できず、単独性を通過したように見えるattemptが変わる。R2の非保証範囲なので blockerにはしないが、保証主張は禁止する必要がある。

[must-fix] **a05は既存build手順をそのまま再利用できない。**  
根拠: positive probeは全buildで `CCBENCH_TRACE=0`、compilerは `command -v` (`t139_positive_control_probe.sh:392–452`)。r4のcompile validatorはmode macroを拒否 (`t139_r4_env_probe.py:609–623`)。a05は3 armを各3点再hashする (`addendum-a-reissue.md:309–329`)。  
失敗シナリオ: verification allocationで生成したmode1/modeX binaryと、probeが記録したstock/trace0 binaryを同一identityとして扱う。  
影響: certified receiptのbinary identity、correctness/performance分離、実行対象の受理集合が誤る。

[must-fix] **pilot 1本のE2Eはgateの効力を証明しない。**  
根拠: `a10` は `n_p=8` (`addendum-a-reissue.md:630–637`)、U8/U9は最小集合から除外 (`s2-plan.md:510–518`)、現行T126は `evidence-only/no-promotion`。  
失敗シナリオ: receiptはacceptedになるが、J・certified選択・材料report・試行台帳の値は一つも更新されない。  
影響: receipt受理集合だけ変わり、certified選択・report参照・公開値は不変。pilot 1本を「成果物を変えるgate」と報告してはならない。

[suspicion] **7,600 production / 7,820 testの精密な行数は独立再計算できない。**  
根拠: U4自身が既存 `submission.py:143–173`、`qsub_binding.py:44–93`を参照し、U5は既存 `t126_driver.py:186–318,480–679,866–1256`、U6は既存collector/atomic publishを参照している。  
失敗シナリオ:既存のprocess-group、atomic publish、qsub binding、13窓driverを全量新規実装として積算する。  
影響: `production 7,600`をnet-new行数とするなら過大見積りで **refuted**。gross変更面の数字なら、算定規則がないため1 wave判定の根拠にならない。

[must-fix] **「1 sessionには収まらない」は資源算術だけでは導けない。**  
根拠: 9/11割当て×3600秒はaggregate上限であり、PBSは並列実行可能。session wallclock上限、queue待ち、同一node共有禁止の投入順が固定されていない。受入全走516秒は8.6分。  
失敗シナリオ:8本を異なるnodeで並列実行すればcritical pathは検証1本＋最長pilot約1時間になり得る。逆に直列なら9–11時間を要する。  
影響: 現プランの「必ずNO-GO」はrefuted。ただし上限不定なのでGOも出せず、実行計画は未確定。分割は決定しない。

[must-fix] **land 1手順は引数自体は正しいが、並行land後の再検査が不十分。**  
根拠: `dev_wave_land.py:2429–2454` の引数、`:1078–1110` の audited closure、`:619–636` の history modifier、`:815–889` の未追跡/submodule dirt、`:2380–2411` のff-only/foldは実在する。  
一方、プランは `BASE_MAIN` を `s2-plan.md:308` で固定したまま、最新main取り込み後も `:400–423` のdiffに使う。  
失敗シナリオ:他waveがlandした後にmainをmergeすると、古いBASE_MAINとの差分へ他waveの実装pathが混ざり、allowlist検査が停止する。mergeしなければland toolがstale-mainで停止する。  
影響:安全側に停止するが、land 1→land 2の再base、`TESTED_MAIN`再計算、audited列・spool base digest・受入/provenance再実行の手順がないため、そのままでは通らない。

[must-fix] **a13循環は必要条件としては refuted。**  
根拠: `s2-plan.md:598–620`、`a13:919–929`。  
(i) reservation JSONLをland1のdocs/data foldへ同梱できるなら、`reservation land → land2 branchでpilot → receipt commit → land2を一度fold` が成立し、R1の同一landとR3(a)を両立する。  
(ii) reservationをland2後に入れる案は、pilot前のcanonical main要件または同一land要件に反する。  
(iii) remote ref/CASはR3(b)であり、固定前提に反する。  
影響: 現プランのallowlist (`s2-plan.md:387–395`) はreservation pathを含まないため、(i)を採るなら現手順は不足する。 (i)をR1が許さない解釈なら循環はrealで、代替(ii)/(iii)には新裁定が必要。

[must-fix] **親briefのP4は誤りではないが、scope外のrealな層を隠してはいけない。**  
根拠: `package.md:106–122` はb03をauthority noneの別studyとして扱い、`s1-brief.md:64–65` のscope外と整合する。  
失敗シナリオ: primary a13だけを実装して、個別公表系列のordinal・public report参照をcertified材料と同一視する。  
影響: 現primaryのJは変わらなくても、将来の公表台帳・材料report・参照digestが変わる。厳密なscope外real層は、b03公表台帳と、canonical boundary外の独立clone／非協調writerの2層。U8/U9はpilot-one最小集合外だが、R4全体scope内である。

[must-fix] **P6の「pilot 8 slot」は不正確。**  
根拠: `a09:562–571` はslot 1–13を定義し、pilotはそのうち適格8本、replacementは同じslotを再利用する。  
失敗シナリオ: slot数を8と実装してslot 9–13の導出を省くか、replacementへ新slotを発行する。  
影響: schedule、prefix balance、replacementの受理集合が変わる。seed/key grammar自体の決定論性は確認済み。

## 総括

1. GO/NO-GO: **NO-GO**（現草案のままland 1/land 2・pilot開始不可）。
2. blocker件数: **8件**。
3. 1 wave可否: aggregateは9–11時間だがsession上限・並列規則が未定義で、「不可能」は未証明。ただし現状GOも証明できない。
4. scope外だがrealな層: **2件**（b03公表台帳、canonical boundary外の独立clone／非協調writer）。