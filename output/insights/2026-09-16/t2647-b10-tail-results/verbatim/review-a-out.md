## 数値の検算

**照合できた数値に不一致はありません。** 原成果物 JSON / DAT から次を検算しました。

- 18 区間 × 6 推定値＝108 値：小数第4位まで一致。全区間で `L = 1 − 2^qU` も一致。
- 24 cell の throughput・abort率の平均48値、変動係数48値：指定桁への丸めを含め一致。
- 生標本の throughput 120値、aborts / commits 120組：全件一致。DAT の abort率再計算値と JSON の rep・`tps` 配列も一致。
- 集団 verdict、3 workload の状態、18区間の分類、非単調性のフラグ：一致。
- 格子・raw値・genome・動作点・測定順・seed・時間枠・3 jobのID・JST開始時刻・所要秒：一致。
- 正しさ記録は40件 × 3＝120件。全件 `certified: true`、`anomalies: 0`、`verdict: serializable`。性能binary digestの相異数は各workloadで8。
- throughput比 `0.444 / 0.481 / 0.400`、変動係数の範囲も一致。

数値の負号は U+2212（−）。表の桁区切り・百分率の丸めにも誤りはありません。

ただし、balanced / read-heavy のホスト、両jobの `freeze_trees_sha256`・worktree状態は、対応する原ファイルが射影に含まれないため独立検算していません。現在のHEADへの祖先性と旧版との差分も、今回の読取り範囲では未検証です。

## field 名と JSON path

**不存在fieldを根拠にした所見はありません。** `correctness_flags`、`source_measurement`、`confirmed_nonmonotonicity`、`upward_wiggle` などは実在します。

本文の短縮表記をrootから記すと、以下です。§4.2の出所表はこの階層と整合します。

- `campaigns[].completion.scheduler.job_start_epoch`
- `campaigns[].points[].correctness[].payload.certified`
- `campaigns[].points[].tps`
- `campaigns[].points[].reps[].throughput_tps`

## SHA-256 の再計算

**指定7ファイルすべて、raw bytesから再計算した完全長SHA-256が稿と一致しました。**

repo外3件、事前登録文書、insight 3件が対象です。`-complete.json` の `artifacts` にあるJSON / DATのdigestも一致します。

さらに事前登録のJSONコードブロック本文を末尾改行込みでハッシュし、specの値
`08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef`
との一致を確認しました。commit ID・identity各digest・WAL / lock digest・job script digestの転記にも不一致はありません。

## 引用の逐語性

**1件あります。重大度: nit**

[稿の§2.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md:218) は、事前登録§4.4を次の形で引用しています。

> 真に平坦な区間が `U ≤ 0.05` に届くかどうかの目安

[原文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/b10-backoff-static-tail-preregistration.md:315) は `U_i <= 0.05` です。添字の省略と比較記号の置換があり、逐語引用ではありません。引用内を原文表記へ戻せば解消します。

**放置時の影響:** 数値・受理集合は変わりませんが、下流の執筆に非逐語の直接引用が継承されます。

§4.5の固定表現、§3のthroughput併記要求、反証可能な主張の引用は、Markdown装飾と折返し改行を除けば一致しています。

## 出所の帰属

**確認範囲で逆転・混同はありません。**

- `bnode017` は指定された `qstat-f.stdout` の `Execution Hosts(JSVNO)` に存在。
- `freeze_trees_sha256` は指定されたjob rootの `completion.json` に存在。
- 再導出のbyte一致はinsight 11 §4、探索走argvの未保存は同§3.4、21行追補とspec不変は同§3.1に記載。
- 図のcohortと作成しなかった理由はinsight 13 §4と整合。

3 jobすべてへの一般化や、列挙された全成果物にsource commitが無いという不在主張は、今回の射影だけでは独立確認できません。不一致の発見とは区別します。

## 入口 README の 1 行

**本文との不一致はありません。**

実際に数えると、限定は連番1〜14の14件、生標本表は24行、原成果物は性能120 rep・正しさ120記録です。稿名・日付・group・run kind・commit略記・verdict・18区間の分類・局所平坦区間0・未認証の記述も整合しています。

## 総括

**must-fix 0件、should-fix 0件、nit 1件。** 修正対象は `U_flat` 説明中の非逐語引用です。照合した数値・7ファイルのSHA-256・入口の件数に不一致はありません。

指定13ファイルはすべて読取り可能でした。射影外の資料は読まず、書込み・測定・テスト実行は行っていません。