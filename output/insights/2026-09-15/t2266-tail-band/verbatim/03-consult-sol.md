## (P1') の判定

**追補が認めた反証型 (d) では倒せた。研究上の必要性を示す (a)〜(c) では倒せない。**

[worklog 逐語:1](/home/SFC/tanab/.claude/jobs/a6836a0d/tmp/wave/t2266-tail-band/ref-worklog-1416-t2266.md:1) は、1000 µs 取得済みとした**後で**901〜998 µs を残件にしている。[brief:8](/home/SFC/tanab/.claude/jobs/a6836a0d/tmp/wave/t2266-tail-band/01-brief.md:8) も帯の標本取得を要求する。「1000 の取得で帳尻は消えた」は、この明示的な依頼を取り消す根拠にならない。

**調査した範囲に、901〜998 µs の測定値を必須入力とする既存 consumer・主張・図表・事前登録は無い。** 検索と読解の範囲は次のとおり。

- `docs/paper-story/`、`docs/paper-story-backoff/`、`docs/decisions.md`、`docs/` 内の事前登録文書、`output/insights/` の Markdown を帯の数値表記で検索し、該当する tail 記述を確認した。
- `paper-story/2026-09-05.md:158,891,1658,1904,1956` と `2026-09-14.md:993,1906,1950,2115` は**未取得・未測という限界の記載**であり、内部点を必要とする判定式ではない。
- `paper-story-backoff/` の3文書には帯の数値表記が無い。`2026-09-10.md:144` は900超の定数外挿を限界とし、`:153` は移行・追加測定を後回しにしている。高域への関心はあるが、901〜998の実測を必須にしていない。
- `tools/t2216_backoff_walk_model.py:53,304,372` の較正は既存6点と v1 に固定され、帯を要求しない。図生成器も `tools/plotting/plot_t2266_tail_mechanism.py:38,239` で同じ6点に固定される。
- D1724の会計近似は、固定した `(u,r)` と新しい実測αから条件付きの再構成を検証することはできる。しかし現行図は6点から再当てはめする（同生成器`:279`）。**901〜998だけに特有の予測・破綻機序・事前の誤差基準は無い。** D1724自身も「実測αを条件に与えた再構成であって予測ではない」と限定する。

これは静的検索・読解の結論であり、帯の性能や滑らかさの実測ではない。

## 所見

以下の相対パスはすべて指定 worktree 内。

### 1. O-C は依頼された測定を代替しない

**real / must-fix**  
**file:line:** `ref-worklog-1416-t2266.md:1,11`、`01-brief.md:8`、`02-plan.md:3`

帯と指定driverを現行契約のまま同時に満たせないことは、別実験への置換を許可するものではない。planの「T-2266完了とは扱わない」は正確だが、それだけで依頼不履行は解消しない。

**放置時の影響:** 成果物は1250〜9999 µsの判定へ変わり、依頼された901〜998 µsの標本はゼロのままになる。

### 2. 「符号化事故の帳尻だから消えた」は史料と整合しない

**real / must-fix**  
**file:line:** `01b-brief-addendum.md:37`、`ref-worklog-1416-t2266.md:11`、`output/insights/2026-09-10/t2266-formal-1000us/README.md:157`

1000取得後の一次資料も帯を未測・残件としている。F718が起源という推測と、その残件を閉じてよいという判断は別である。また同じ符号化枝を通ることは内部の性能が滑らかである証明ではない。

**放置時の影響:** 未測という測定事実が、根拠のない「解消済み」という台帳上の結論へ変わる。

### 3. 追補の数値転記は概ね正しいが、差分1セルと参照行が誤り

**real / nit**  
**file:line:** `01b-brief-addendum.md:15,24`、`output/insights/2026-09-04/t2266-backoff-static-tail/README.md:56`、`output/insights/2026-09-10/t2266-formal-1000us/README.md:90`

12個のthroughput値は一致した。再計算すると700→800のbalancedは **−5.64%** で、−5.63%ではない。他の8差分は表と一致する。700/800/900の正しい参照行は56/58/59、1000の値は90〜92行である。

**放置時の影響:** 集計表の1セルと参照先が誤ったまま残る。帯の測定要否を決めるほどの差ではない。

### 4. 追補によって O-C が必ず blob 不一致で止まる、は成立しない

**refuted / must-fix〔旧commitを指定する場合〕**  
**file:line:** `orchestrator/campaign/b10_backoff_static_tail_formal.py:232`、`docs/b10-backoff-static-tail-preregistration.md:1081`

照合は「指定commitがHEADの祖先」「現在の文書全文がそのcommitの文書と一致」である。読み取り比較で次を確認した。

| 指定commit | 現在の全文bytesと一致 |
|---|---|
| 初版 `9e97d27b8` | 不一致 |
| 追補版 `cad6f46d8` | 一致 |
| 基点 `0600887d9` | 一致。HEADの祖先性も成立 |

したがって初版指定なら止まるが、基点指定なら**この照合では止まらない**。shape側と同じ全文照合上の注意はあるものの、初版commitへの固定はtail driverには無い。これは投入経路全体の成功確認ではない。

**放置時の影響:** 初版commitを選ぶと測定前停止となる。基点指定なら、この理由による値・受理集合の変更は無い。

### 5. O-C が正しさゲートを緩める経路は確認できない

**refuted / must-fix〔緩和があれば〕**  
**file:line:** `orchestrator/campaign/b10_backoff_static_tail_formal.py:342,393,611`、`docs/b10-backoff-static-tail-preregistration.md:841`

正しさの権威は `payload.certified is True`。加えて現行specの anomaly上限は0で、記録数・modeも検査する。`verdict`文字列やreportの認証表記へのfallbackは無い。性能前の拒否は `orchestrator/campaign/pipeline.py:655` にもある。

異常を含むcampaignはloaderで拒否され、report経路では `load_failure` とraw WALを保存する（formal driver`:452`）。失敗が1件でもあれば集団verdictは `invalid`（`:634`）。残った正常点だけで集団を有効化しない。

**放置時の影響:** 現行コードでは受理集合の拡大を確認できない。異常集団の数値は記述用に残り、登録主張には使えない。

### 6. §7の失敗は「完走後の判定」だけではない

**real / must-fix〔報告手順〕**  
**file:line:** `docs/b10-backoff-static-tail-preregistration.md:995`、formal driver`:526,543,620,668,793`

現実に発火可能なのは、正しさ不合格・欠測、整数カウンタ欠落、ビルド不完全、CV≥2%、支持された非単調性、時間切れ、identity・出所・mode不一致などである。

- 読込・解析まで到達した失敗は、理由付きで集団 `invalid`。
- 内部締切は失敗reportを生成する。
- **事前登録照合はreport生成より前**なので、blob不一致では集団reportが自動生成されない。
- schedulerによる強制終了では、内部締切のreport生成も保証できない。

**放置時の影響:** 「reportが無い失敗」を回収対象から落とすと、失敗したjobと取得済み観測が成果物から欠落する。新規gateは不要で、既存ログ・receipt・WALの回収を明記すればよい。

### 7. formal report が v1 consumerへ通る経路は確認できない

**refuted / must-fix〔混入があれば〕**  
**file:line:** formal driver`:636,650`、`tools/t2216_backoff_walk_model.py:53,304`、図生成器`:38,239`

formalは専用schema・stemでcreate-only出力する。既存consumerはv1と6点を要求するため、formal reportを渡しても受理しない。編集ゼロのO-Cが既存3系列の受理集合を変更する根拠は無い。

**放置時の影響:** 現行の分離を維持すれば既存成果物は不変。新reportを旧解析へ反映済みとは報告できない。

### 8. O-A の親アンカー表は最小実装面を欠いている

**real / must-fix**  
**file:line:** `01-brief.md` §8、`tools/pegasus/b10_backoff_grid.sh:187,612,658`、`backoff_extended_sweep.py:633,1331,1438`

新RUN_KINDにはsubmit入口だけでなく、job側の受理・argv転送・完了確認も必要。最小案は、例えば950 µsの1点を3 workloadで測る専用系列を作り、専用identity・schema・stem・rep記録・reportをT2418の先例に沿って追加すること。binary相異検査の完全性も新系列に接続する。既存格子とformal driverは変更しない。

**放置時の影響:** submit側だけ追加するとjob側で拒否されるか、指定RUN_KINDが転送されず、意図した帯の成果物を得られない。

## 採るべき O

**O-A。** 研究上901〜998だけを細分すべき既存根拠は見つからなかったが、依頼は帯の標本取得を明示している。D1848の専用系列による分離を使い、最小点数で測るのが依頼に対応する。950 µsを測ったなら「帯内950 µsの標本取得」とだけ報告し、帯全域の被覆や機序確定へ広げない。帯を測らない場合の誠実な返答は「1000の回収済みを確認したが、帯は未測。指定driverでは測れず、今回の依頼は未完了」であり、O-C完了による置換ではない。

## 総括

(P1') は依頼の明示という反証型(d)で倒せた。帯専用の研究上の必須consumerは見つからない。  
O-Cの正しさ・既存consumer分離に、現に破れた防壁は確認できない。  
追補後bytesは基点commitと一致し、初版commit指定の場合だけblob照合で止まる。  
依頼への対応はO-A。O-Cを帯測定やT-2266完了の代わりにはできない。  
ファイル変更・投入・テスト実走は行っていない。