**修正後 GO。must-fix 1 件、should 4 件、nit 2 件。** 対差 123.9 秒・27.3 % と次の一手の採否は支持されますが、コピー区間の混同を直す必要があります。

以下、`J` は一次資料ディレクトリ `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag`、README は今回の insight、fragment は指定の worklog を指します。

## 所見

### R1 — must-fix：copytree の比較対象が途中で変わっている

- **場所:** README 結論 1・3・4 の比較表。
- **一次資料の値:** `J/analysis/r1.json` の `keys[].builds[].seconds.copy_breakdown["copy.copytree"]` は active_v2 builder で **95.1993 秒**。一方、`J/job-out-r1/A/spans-*.jsonl` の `name="copy.copytree"`、`worker="gw14"` は **90.0661 秒**。前者は別のコピーも含む合計。
  R2'' の生 span で可視 output の copytree 単体を同じ定義で取ると、共有 7 key は **A2 111.4473〜111.4970 秒 → X 2.6739〜2.7427 秒**、対応 key ごとの差は **108.7150〜108.7923 秒**。
- **何が誤るか:** R1 の「実 copytree 90.1」と表の「copytree 117.1 → 8.5」が異なる区間なのに、同じ量として読める。
- **最小の修正:** 表を「builder 内 copytree 合計」と明記し、可視 output 単体の行を別に置く。`copy 138.0 → 11.1` も builder 全体のコピー成分合計と明記する。W_0 の差は変更不要。

### R2 — should：A 系全走へ広げた超過率が誤っている

- **場所:** README 結論 8。
- **一次資料の値:** `J/analysis/r1.json:shard.W=429.433`、`r2-a2.json:shard.W=453.222`、`r2c-pair.json:metrics_s.W_0.A2=454.623`。T-2825 README §3 の B は **310.663〜344.931 秒**。
- **何が誤るか:** 「A 系 429.4〜454.6 が 25〜38 % 超」は R1 の比較率を全走に流用している。全組合せでは **24.5〜46.3 %**、B 上端だけとの比較なら **24.5〜31.8 %**。
- **最小の修正:** 比較対象を固定して率を訂正するか、率を削除して実測範囲だけを残す。

### R3 — should：走・key の取り違えと範囲の不一致

- **場所:** README 結論 2・4・6、fragment「次の一手差分」T-2273。
- **一次資料の値:**
  - `J/analysis/r2-a2.json:critical_worker_decomposition.gw2.totals_s.flock_wait` = **230.6700 秒**。
  - `r2c-pair.json:critical_worker_decomposition.A2.gw2.totals_s.flock_wait` = **230.9168 秒**。
  - 同 `builders[]` の active_v2 key `[none,false,true,false,true]`、`seconds.issue.X` = **79.4107 秒**、`seconds.git.X` = **13.8623 秒**。
  - 同共有発行 key の `seconds.issue.A2` は **79.2153〜79.3582 秒**。
  - `r1.json:keys[].builds[].seconds.issue` の共有発行 key は **79.3927〜80.0541 秒**。
- **何が誤るか:** R2'' の待ちを 230.7、X の依存 builder を発行 79.3・git 13.8 とする記載、および A2 発行範囲 79.1〜79.4、fragment の発行範囲 79.2〜79.6 は対象に一致しない。
- **最小の修正:** R2 と R2'' を分け、後者の待ちは **230.9**、X の依存 builder は発行 **79.4**・git **13.9** とする。範囲は「全発行 key」か「依存 builder」かを固定して再集計する。

### R4 — should：同時コピーと介入の対象に非共有 builder が 1 本ある

- **場所:** README 結論 2・3・5、fragment 題名・T-2273。
- **一次資料の値:** `J/analysis/r1.json:nonshared_builds` に **gw20** の成功 build があり、JUnit 基準 **t≈130.288 秒**開始。`r2c-pair.json:builders` は共有 7 件＋非共有 1 件、`visible_copies.A2/X` は各 **8 件**。X の gw20 も生 span の `extra.substituted=true`。
- **何が誤るか:** 「共有 7 key」は正しいが、Lustre を読む全本数と介入範囲まで 7 本だったように読める。
- **最小の修正:** 「共有 7 本に加え、検査用の非共有 builder 1 本も同時に動き、対照の差し替え対象だった」と一文追加する。

### R5 — should：29,885 は可視集合の件数で、実コピー件数ではない

- **場所:** README 結論 5、fragment 題名の「29,885 file ずつ」。
- **一次資料の値:** `J/job-out-r2c/staging.json:visible_path_count=29885`。`test_s8b_oracle_driver.py:_copy_git_visible_output` は `retained_output = visible_output - excluded_artifacts` とし、receipt・draft・floor artifact 等を除外してコピーする。
- **何が誤るか:** 可視集合の検査件数を、そのまま各 builder の実コピー件数としている。
- **最小の修正:** 「可視集合 29,885 path を列挙し、所定の除外後に複製」に置換する。

### R6 — nit：完走した test 件数

- **場所:** fragment 本文「約 4,100 test」。
- **一次資料の値:** `J/job-out-{r1/A,r2/A2,r2c/A2,r2c/X}/pytest.log` は全て **4216 passed, 53 skipped**。`r2c-pair.json:outcomes.A2/X` は各 **4269 件**。
- **何が誤るか:** 現在の走の件数を過少に記載している。
- **最小の修正:** 「4,269 件（4,216 passed、53 skipped）」とする。

### R7 — nit：mdc close の集計範囲が不明

- **場所:** README 結論 3。
- **一次資料の値:** `J/analysis/r1.json:builder_resources[].sample_mean.lustre_ops_s` の **7,362.2003 回/秒**は特定の `lustre-MDT0000-mdc-ff2286b3c3d71800/md_stats:close`。記録された全 mdc の close 合計は **7,377.9003 回/秒**。
- **何が誤るか:** 単一 counter の値が node 全体の合計に見える。
- **最小の修正:** 対象 counter を明記するか、全 counter 合計にする。

## 照合済み一覧

- **job:** R1＝18929／bnode030／514 秒、R2＝19029／bnode025／954 秒、R2'＝19108／bnode005／84 秒、R2''＝19131／bnode081／1,046 秒。環境記録と NQSV footer に一致。合計 **2,598 秒＝0.7217 node 時間**。
- **R1:** W_0 **429.433**、O_max **289.0451／gw2**、L **272.093／gw40**。rank 96 の **261.678＝206.5147＋14.5429＋0.6632＋39.9572**、後続 **22.688＋4.676**。gw40 の分解も一致。
- **R1 builder:** 依存先 gw14、構築 **206.5271**、copy 合計 **113.3571**、git **13.4871**、発行 **79.6080**。共有 7 key の開始は **t=130.276〜130.287**、非発行 key **126.8619 秒**。
- **CPU 判定:** output copytree の self CPU/壁 **約0.108**、node CPU **0.2419**、iowait **0.00225**、run queue **13.033**。依存 builder の発行比 **1.00093**、git 比 **0.98645**。事前登録の「待ち支配／CPU 支配」に一致。
- **R2'' 対差:** W_0 **454.623→330.677、差123.946、27.2635 %**。O_max 差 **123.5781**、L 差 **121.405**。両腕とも O_max＝gw2、L＝gw40。pre/post、構築時間範囲、copy 合計短縮も一致。
- **staging・有効性:** **43.9403 秒**、差引き **80.0057 秒**。outcome 集合一致、可視集合件数・digest は A2/X/staging で一致、両走 rc 0、clean・others 0。全有効性 check が真。採否基準を満たす。
- **失敗分類:** R2 X の rc 16、failed **21**／errors **25**、quota エラーを確認。R2' は smoke 後 `git_status_line_count=1` で停止。下書きの作成者が親だったという帰属は裁定の記録に依拠する。
- **既存値・呼出し元:** T-2825 の W_0・pre・旧 A 所要範囲、T-2786 の collection 中 copy **30〜35 秒**、T-2817 の copy **100.4／64.2／33.0 秒**は指定 README に一致。`_copy_git_visible_output` の呼出し元は実 ROOT の 1 箇所と fixture root の 2 箇所。

開始 gate の実行履歴、author の 4 巡・branch 終端、ff-only とコード差分ゼロは、今回の射影内の計測資料だけでは独立確認できていません。全記載の照合完了とは扱いません。

過剰・削除レンズでは、1 対であること、後走 warm、原因未同定、X の絶対値を 5 分未満の根拠にしないことは明示されています。禁止された先行実装を勧める記述は見つかりませんでした。

## 総括

**修正後 GO — must-fix 1 件。** 可視 output 単体と builder 全体のコピー区間を区別すれば、主要な採否判断は維持できます。