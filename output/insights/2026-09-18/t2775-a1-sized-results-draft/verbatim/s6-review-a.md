## must-fix

以下、「稿」は `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` を指す。測定値の転記・再計算は一致したが、証拠の所在・範囲に次の誤記がある。

**M1 — 「anomaly 数は result.json には無い」は誤り。**

- 根拠: 稿253行。公開 leaf の `result.json` は、`workloads[0..2].wal_evidence.records[2].payload.anomalies` と同 `records[5].payload.anomalies` に、計6件の `0` を持つ。各 WAL の3行目・6行目とも一致した。`arms.<name>.correctness_evidence` に無いことと、result 全体に無いことを混同している。
- 放置時の影響: 正しさの数値を確認できる参照先を誤って限定する。
- 是正案（253行の括弧内を置換）:
  > anomaly 数は `arms.<name>.correctness_evidence` には無いが、result.json 内の `workloads[].wal_evidence.records[].payload.anomalies` に WAL の記録値として収録されている。

**M2 — 投入から materialize までの所要の出所が違う。**

- 根拠: 稿322行は「job の accounting と WAL の ts から書いた事実」とする。しかし、その両資料には submit 開始・materialize 完了の時刻が無い。稿266・273・431行自身が、記録 insight §3 の mtime 由来と明記している。掲載時刻の差は `06:45:38 − 06:30:16 = 922秒 = 15分22秒`。
- 放置時の影響: 下流が accounting／WAL から全工程の所要を再導出できる、と誤認する。
- 是正案（L-A1S-20を置換）:
  > **投入から materialize 完了までの約15分は、再投入の予算や計画値ではない。** 記録 insight §3 が記録した job dir file の mtime（06:30:16〜06:45:38）の差であり、本稿はこの時刻を再計測していない。別の attempt の所要へ一般化しない。

  冒頭13行・413行の「記録 insight を数値の出所にしていない」も、次のように範囲を限定する必要がある。
  > 測定値・統計値の出所に記録 insight の本文は使わない。投入・complete・materialize の時刻は、§5.5 に明記した mtime 記録による。

**M3 — 「本 attempt では衝突は起きていない」は記録から確認できない。**

- 根拠: 稿315行。`.complete.json.publish` と `result.json.materialization_evidence.publish` は、存在確認後から rename までに非協力的 writer が作った空ディレクトリを置換しうる、と明記する。記録されているのは `EINVAL` と選択した公開方式・保証・限界であり、この区間の衝突不在を観測した field は無い。
- 放置時の影響: 成果物自身が留保した公開時の証拠範囲を、衝突不在の実証へ強める。
- 是正案:
  > 公開完了は記録されているが、存在確認後から rename までの非協力的 writer との衝突不在は、この記録からは確認できない。

**M4 — 限定の出所に stale 注記を採用している。**

- 根拠: 稿304行、L-A1S-2の出所が「D2044 項8、stale 注記3件目」。D2044 項8が定めるのは投入認可の据え置きとユーザー手番であり、headline 値の使用制限そのものではない。stale 注記を出所にしないという本依頼・稿冒頭の宣言とも一致しない。
- 放置時の影響: 執筆上の利用制限を、投入認可の裁定が直接命じた制限として引用することになる。
- 是正案（出所欄）:
  > 本稿の利用範囲（§0.3）、policy `authority`、事前登録 §1.1／§7.2。投入・再投入の認可主体については D2044 項8／D2120 項3。

## should

**S1 — F36対応と系列規則の例外関係を明示する。**

- 根拠: 稿289〜292行と段4裁定§6の自己参照回避は正しい。一方、`docs/paper-story/README.md` 255〜256行には「数値は図の provenance JSON から転記し、転記元の SHA-256 を文書に書く」が残る。稿は result.json から転記するため、この文言への適合とは言えない。README243行も自己参照回避だけを説明している。
- 放置時の影響: 将来の執筆者が系列規則に合わせて provenance hash を稿へ追記し、循環を再導入しうる。
- 是正案（稿§2.6とREADME対象行に追記）:
  > 本稿は F36 回避のため、系列規則の provenance 転記方式に対する個別の扱いとして、数値を公開 leaf の result.json から転記し、その SHA-256 を §5.1 に記す。図の provenance の SHA-256 は figures/README.md に置く。

**S2 — C1旧3値の直接の参照先を追加する。**

- 根拠: 稿47行の `+38.3% / +11.3% / −6.6%` は、指定された D1993・L23には載っていない。ただし `docs/decisions.md:341`、D19の「帰結」に同じ3値が存在するため、数値そのものを誤りとは判定しない。§5.4・§5.5にはこの出所が無い。
- 放置時の影響: 読者が提示された引用先から旧3値を確認できず、記録 insight 由来との区別がつかない。
- 是正案:
  > C1の旧環境3値の照合先は D19「帰結」（docs/decisions.md）である。本 attempt の測定値ではない。

## nit

**N1 — intent の2種類の hash を区別すると明確になる。**

- 根拠: 稿124〜125行の `7eb40486…` は `intent_sha256` field、393〜394行の `0c3aadae…` は file bytes の hash。両方とも正しい。前者は `intent_sha256` を除外し、実装の canonical JSON 形式で再計算して一致した。
- 放置時の影響: 値・判定・参照は変わらないが、同一 file に異なる hash が付いたように読める。
- 是正案:
  > submission が持つ intent の canonical digest（`intent_sha256`）は `7eb40486…`。intent file 全体の bytes SHA-256 は §5.2 の `0c3aadae…`。

## 一致 — 数値

指定式を別途実行し、親のスクリプトの転記照合だけに依存せず確認した。

| workload | mean | sample sd | h | B |
|---|---:|---:|---:|---:|
| write-heavy | 1591948.5 | 46253.31396347129 | 23911.502943472762 | 68795.219 |
| balanced | 448830.1666666667 | 54842.032905228465 | 28351.599461068836 | 115876.89600000001 |
| read-heavy | -576749.7666666667 | 63763.46597396226 | 32963.69867738655 | 310204.40199999994 |

- **180標本・90対差:** 稿§2.2、result の `pairs`、`arms.raw_tps`、WAL `bench_done.tps` が一致。全対で `variant − baseline` が一致。
- **区間6端点・baseline平均3値:** §2.1の全桁と一致。`n=30`、`df=29`、`k=2.8315526875186725`、planned sigma 3値も policy と一致。
- **分類:** 3件とも `abs(mean) − h > B`。`resolved-above-floor`、符号 `+/+/−`、`variance_plan_breach=false` ×3と一致。
- **派生比:** `0.6942118317844151 / 0.11620008357835197 / −0.05577771588167212`。稿の `+0.694 / +0.116 / −0.056` と一致。
- **sd／計画sigma:** `0.6965498403340564 / 0.9672753664253991 / 0.8539541424279983`。稿の `0.697 / 0.967 / 0.854` と一致。
- **6 arm の mean・min・max・median・CV:** 掲載精度で一致。CVの独立再計算には最終桁の浮動小数点差があるが、稿の逐語値は WAL と一致。
- **elapsed／CPU:** monotonic差と Bash `times` 原文の差から再計算。`553.96 / 755.30 / 323.80秒`、`9121.249 / 9121.098 / 9118.327秒` と一致。
- **時刻:** receipt epochのJST換算、WALの30 recordの時刻、build／verify／benchの記述範囲と一致。submit／complete／materialize は記録 insight・MANIFESTのmtime記録と一致し、§5.5にはその由来が明記されている。

## 一致 — hash・識別子・記録

- **SHA-256:** 公開leaf4 file、policy、事前登録、campaign.lock3本、WAL3本、schedule receipt3本、raw2 file、受領証3種、intent、job scriptの**22 fileのhash**を現物から確認。稿中の対応値と一致。intentのcanonical digestも別途一致。
- **bytes:** leafの `269649 / 19343 / 1392`、durable9 file、rawの `263360 / 18112` が一致。
- **campaign ID3件:** `identity_preimage` のSHA-256先頭8桁を再計算し、`ec74e1c8 / fdd1cb88 / 9912d892` と一致。
- **識別子:** study、schema、request `4939/4940/4941.nqsv`、host `bnode107/108/109`、source commit、CCBench pin、variant ID4種、genome、arm名・roleが各記録間で一致。source bindingの9 fileも現物hashと一致。
- **WAL:** 各10行、計30 record。5 stageが各2件、`env_tag=pegasus`、行異常なし。verify frame6件のbyte rangeとSHA-256も一致。
- **6 armの状態:** reps 30、rounds 1、attempt 1、unstable false、rep_notes空、valid true、errors空。`high_variance=false` は稿の指定どおり WAL `commit` に存在。
- **正しさ:** commits／aborts全12値、anomalies 0 ×6、certified true、serializable、legacy、proof_surfacesの4値、commit witnessが一致。
- **insightの逆転:** 稿の指摘が正しい。balancedは `466561 / 483318`、read-heavyは `516607 / 515988`。WALとjob stdoutが一致し、insight §4の表だけが逆。
- **測定条件:** records・threads・rratio・extime・clock・Zipf・rmw・max_ope、`use_perf=false`、`counter_status=not_required`、throughput以外のleading indicatorがnullであることを確認。
- **物理順:** 3 workload各12 block、各5標本。seedからのbit再計算は `100 / 110 / 101`。各10対群の順序は指定された2形と一致。
- **raw／leaf差:** resultは `materialization_evidence` とlimitations第5項、receiptは `materialization` の追加だけ。statisticsとarmsは構造的に同一。
- **scheduler:** 3本とも `request-disappeared-after-visibility`、state／exit_status未観測。成功との区別も稿どおり。

## 一致 — 限定・README・F36

- 限定は20件。非認証lane、headline不採用、横断結論禁止、C1再現判定禁止、単一attemptから安定性への一般化禁止、A-1充足・formal化・再認可を判定しない旨は揃っている。
- `improvement / regression` は事前登録の分類語の引用であり、本attemptへの方向判定としては書かれていない。
- v3 policyに `classification_rules` は無い。実装の述語・定数 `0.03`、policyの `3/100`、事前登録の分類述語の同値性は記述どおり。
- README243行は**4列**。限定20、生標本180、3 job、source、図9、分類・符号・laneの記述は稿と一致。134行は既存の「変わらないこと」を弱めていない。
- 稿に図のprovenance hash・PNG/PDF bytes hashは無い。`caption_source`との自己参照を避ける理由は正しい。系列規則との関係だけがS1の残件。

## 総括

**NO-GO。must-fix 4件。**

主要な測定値・統計・hashは一致した。修正が必要なのは、anomaliesの収録先、工程所要の出所、衝突不在の断定、stale注記の出所利用である。

読み取り再計算・静的照合のみ実施。file変更・pytest実行はしていない。