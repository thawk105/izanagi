## 判定と照合範囲

**NO-GO。数値の訂正と完走記録は整合していますが、所見1・2の旧断定が残り、所見3の時系列訂正にも証拠以上の断定があります。**

以下の略号を使います。

- `R`：`output/insights/2026-09-19/t2288-floor-pair-w1/README.md`
- `W`：`docs/spool/worklog/2026-09-19-dev-wave-t2288-floor-pair-w1-1.md`
- `F`：`docs/spool/failures/2026-09-19-dev-wave-t2288-floor-pair-w1-2.md`
- `J`：`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1`
- `E/<nonce>`：指定の floor-pair evidence directory
- `C`：`tools/pegasus/floor_pair_campaign.sh`

静的照合のみ実施しました。ファイル書き込み、pytest、ジョブ投入、性能再測定は実施していません。

## 派生値の再計算

| 対象 | 再計算・照合結果 |
|---|---|
| 6 / 1 / 1 | 正しい。`C:106`のpayloadへ写るFP変数は6個。3 jobすべてsubmit receiptと一致。evidence directoryは出力先で確認。walltime変数は非空・形式・正値検査の通過までで、受信値の逐語記録なし。 |
| 投入から開始まで8秒 | 初期qstatのEntered Queue→Startedは、rr95＝21:32:11→19、rr50＝21:32:20→28、rr5＝21:32:22→30。全件8秒。launcher起動時刻を起点にした時間とは区別が必要。 |
| rr50 Elapse＝4145S | `E/8b8…/scheduler.stderr:13`と一致。job-resultのepoch差4141秒とは異なる量。 |
| 表18 / 42 cell | データ行6×3列＝18、14×3列＝42。合計60。 |
| JSONL 378行 | 各126行＝header 1＋session 124＋terminal 1。3本で378。 |
| 372 session・744測定 | JSONL全件を数え直して一致。全sessionがcomplete。 |
| 1,116 probe・3,720 rep rc | sessionごとにprobe 3個、測定ごとにrep rc 5個。全probe clear、全rep rc 0。 |
| 証拠30本 / submit関連24本 | 実投入directory各10本×3＝30。submitの6回×meta・rc・stdout・stderr＝24。前レビューからの転記も一致。 |
| 11 call、246秒 | 指定receiptの`attempts[0].model_calls=11`、`wall_clock_s=245.66000306`。秒単位に丸めて246で正しい。 |
| mtime 21:28:45 / 21:30:42 / 21:31:05 | `stat -c '%y'`でdetach.sh／place.log／submit-rr95-w1-dry.metaがそれぞれ一致。 |
| dry-run終了と実投入開始 | rr5 dry-run meta終了＝21:31:27、rr95実投入meta開始＝21:32:09。42秒の間隔は確認できる。 |

ただし、最後の時刻・mtimeは**briefや裁定本文を書いた時刻を記録していません**。`HANDOFF:15,30`、`R:151`、`W:36`、`F:16`の「briefは12:27:09Zより前」「裁定は21:31:27〜21:32:09の間」「順序は保たれていた」は、指定資料から独立には確定できません。親の操作説明として明示するか、当該書き込みを示す履歴が必要です。

さらに、`F:14–15`の出典付き時刻に新たな不一致があります。rr95の`submit-receipt.json:1`は`prepared_epoch=1789821131`、すなわち**21:32:11 JST**です。21:32:09は`submit-rr95-w1.meta:1`のlauncher開始時刻です。

## 既存セルの回帰確認

「完走の記録」表から、次の**18 cell（6行×3 workload）**を一次資料と再照合しました。

| Rの行 | rr95 | rr50 | rr5 |
|---|---|---|---|
| 107：job_rc / gate / reason / driver_rc | 0 / driver / completed / 0 | 同左 | 同左 |
| 108：hostname / pbs_jobid | bnode022 / 0:10711.nqsv | bnode080 / 0:10712.nqsv | bnode081 / 0:10713.nqsv |
| 110：epoch差 | 4178秒 | 4141秒 | 4602秒 |
| 111：Elapse / Remaining | 4182 / 82218S | 4145 / 82255S | 4607 / 81793S |
| 114：行数 / hash先頭 / mode | 126 / fa06e2130b0d15cd / 0600 | 126 / 8bdd909394fa2bce / 0600 | 126 / 12fbe874c2899de9 / 0600 |
| 115：terminal計数 | complete、124/124、248/248、62/62、drop 0 | 同左 | 同左 |

**18 cellすべて一致し、抜き取り範囲の数値回帰はありません。** JSONLのSHA-256も再計算し、driver.stdoutの値と全件一致しました。

## 訂正文とfragmentの評価

`R:18–22,69–86,122–130,170–172`と`W:21–25`は、変数の確認範囲とsignalの観測限界を適切に分けています。証拠より弱すぎる訂正ではありません。しかし次が残っています。

- `R:99`：見出しに「signal なし」。
- `HANDOFF:57`：「signal なし」「8変数の配送を値で確認」。

いずれも旧断定の残存です。前レビュー所見1・2の修正完了とは扱えません。

`R:185–190`の申し送り4・5は妥当です。dry-run各directoryには記載どおり2ファイルだけが存在し、watcherの検索は`run-watch.sh:27`で`c1`固定です。

段6節の所見11〜15は、`R:159`と`W:32`で5件ともrefutedとして正しく要約されています。再分類・逆転はありません。

failures fragmentは、frontmatter、`## 再発`、`### F1`、再発item 1件、継続行、placeholderなしという構造を満たします。日付内の`(near miss)`も既存F1の型と整合します。**文法上の問題と、本文の時刻・証明範囲の問題は別です。**

## 総括

**判定：NO-GO。closed 6件、partial 4件、regressed 0件。**

| 前所見 | 判定 | 根拠 file:line・残件 |
|---|---|---|
| 1 | partial | `R:122–127`、`W:21–23`は`C:106`と一致。ただし`HANDOFF:57`に「8変数を値で確認」が残る。 |
| 2 | partial | `R:129–130`、`W:24`は`C:176–189`に即した限定。`R:99`と`HANDOFF:57`の「signalなし」が未修正。 |
| 3 | partial | `HANDOFF:4,15,30`で推定時刻だったことは明示。`R:151`、`W:36–37`、`F:16–17`の「順序を追認」は指定証拠だけでは成立しない。 |
| 4 | partial | `HANDOFF:24`でdocs-onlyにも適用されることと前レビューのgrepを明示。ただし「新規2本のみ」は新規Fを含む現在の範囲と不一致。`R:152`も同じ。 |
| 5 | closed | `HANDOFF:59`の4145Sは`E/8b8…/scheduler.stderr:13`と一致。 |
| 6 | closed | `R:189–190`でc1→c2を明記。`J/run-watch.sh:27`と整合。 |
| 7 | closed | `R:63–65`、`W:19–20`で8秒と内訳未分離を明示。初期qstat全3本のEntered Queue／Startedと一致。 |
| 8 | closed | `R:79`の`observations/qstat-f-<id>-initial.txt`は実在する指定3本と整合。 |
| 9 | closed | `R:185–186`の2ファイル構成はdry-run全3directoryと一致。 |
| 10 | closed | `HANDOFF:22`でrepo内実装とrepo外運用launcherを区別。`R:187–188`の6本とも整合。 |

新規所見は以下です。旧断定の残存と時系列証明の不足は、上表の所見1〜3に含め、重複採番しません。

| 番号 | 分類 | 重要度 | 根拠・必要な訂正 |
|---|---|---|---|
| 16 | real | should | `F:14–15`の`prepared_epoch = 21:32:09`は誤り。`E/3fb5…/submit-receipt.json:1`は21:32:11。21:32:09を使うなら出典を`J/submit-rr95-w1.meta:1`へ訂正する。 |
| 17 | real | nit | `R:152`、`HANDOFF:24`の「新規2本のみ」はF追加後の現況と不一致。当初の対象2本という履歴説明と、現在の対象3本を区別する。 |

**読めなかった必読資料：なし。** 指定資料では確定できなかったのは、brief・裁定本文の実際の記載時刻と、その事前性です。