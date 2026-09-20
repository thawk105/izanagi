# B-10 待ち方 grid の結果節 — 登録した `constant` 対 `symmetric-modulo` の 1 contrast は 3 族とも Holm で `different`、36 cell の 95% 区間は等価域 ±3.0% の内側 32・境界を跨ぐ 4・外側 0 (2026-09-20)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である (D1631)。

**本稿は同系列の既存の稿を改めるものではない。** 同系列は append-only であり、A-2 / A-6 / B-7 / [T-1998] の稿も、
B-10 静的右 tail の 2 稿 (`2026-09-16-b10-static-tail-not-observed.md`、`2026-09-19-b10-static-tail-cohort2.md`) も
1 byte も変えずに残る。右 tail の 2 稿は別の事前登録 (`docs/b10-backoff-static-tail-preregistration.md`)・別の格子・
別の driver による別の cohort の事実であり、本稿が書く待ち方 grid の判定とは**合成しない** (D2157 の精神を待ち方 grid
との間にも当てる)。

**本稿の言い方は事前登録が固定している。** `docs/b10-backoff-shape-preregistration.md` の発効版 (§1.1) §3 は、
書ける主張を「登録した 2 つの特定の実装の間で、待ち方の違いが throughput を動かすかを事前登録した手続きで検定した」
「有意な族については方向・効果量・信頼区間を**この contrast に限って**限定付きで述べる」までに固定し、
§8 は「`binary` を測った」「3 水準を比較した」「A-2 の逆転や過抑制域の機序を説明した」「待ち方と待ち量の直交切り分けを
一般に閉じた」と書くことを禁じる。本稿はこの固定に従う。

**判定は 2026-09-05 に出て、2026-09-07 に記録され、同日ユーザー裁定 D1678 で「現行 report で閉じる」とされた。**
本稿の file 名の日付 (2026-09-20) は起草日であり、実走日でも記録日でもない (§1.5)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

results 系列は「1 file = 完走した 1 つの protocol または campaign 群の結果」を単位とする (D1631)。
本稿の単位は、**事前登録 `docs/b10-backoff-shape-preregistration.md` の発効版 (commit `77b33e37d`、§1.1) に対して
report phase (request `978195.nqsv`、2026-09-05 JST) が出した 1 つの判定** — write-heavy / balanced / read-heavy の
3 campaign × 45 cell = 135 cell を exact に集約し、3 族 Holm と 36 cell の効果量・区間を出したもの — である。
3 campaign は別 job・別日・別 driver 版で走った (§1.3・§1.4。balanced と read-heavy の host は異なり、write-heavy の host は未記録)。集約が 1 つの判定を成すのは、driver の限定受理
(§1.4) が 3 campaign を同じ事前登録束縛の下で受理したからである。

### 0.2 本稿が判定しないこと (最初に置く)

**事前登録 §9 が「本書が閉じない B-10 の残り」として列挙した 9 項目は、いずれも本稿が閉じない。** 発効版 §9 は
「これらは未取得のまま残る。本書の結果をもってこれらが閉じたと書いてはならない」と定める。9 項目は次のとおり
(発効版 blob の逐語を要約したもの。順序は §9 のまま):

1. 過抑制域の機序
2. ピーク位置の再現
3. balanced workload の profile
4. 実走での要求待ち量そのものの分布 (分位点・自己相関・スレッド間同時値率) の診断
5. `binary` を含む 3 水準の ladder と、ばらつきの用量反応
6. 待ち方と待ち量の一般的な直交切り分け (本書が閉じるのは 1 contrast の範囲だけ)
7. 本走中の実要求待ち量・実待機時間が形の間で一致しているかの確認 (合成ループの残差しか測っていない)
8. 乱数計算そのものと撹拌器のオーバーヘッドを、待ち方の効果から分離すること
9. 結果を見ていない設計による独立な追試 (本書の grid は probe-informed amendment である)

**このうち D1678 (2026-09-07、ユーザー裁定) が「起票せず見送る。再訪条件 = 査読で当該項目の提示を要求されたとき」と
裁定したのは 5 項目 — 過抑制域の機序、ピーク位置、`binary` を含む ladder、用量反応、独立追試 — である。** D1678 の
5 項目は上の項目 1・2・5 (ladder と用量反応を分けて 2 つに数える)・9 に当たる。項目 3・4・6・7・8 は D1678 の見送り列挙に
入っておらず、本稿はそれらに新しい地位を与えない — §9 のとおり「未取得のまま残る」とだけ書く。**本稿は D1678 を改めない。**

**制約 3 つ (いずれも 2026-08-27 のユーザー裁定) を本稿の限定として先に置く。**

- **D1092:** 診断計装下の試行は正しさ検査を通すか、診断由来の機序判断を成果物から外す。本 report は機序判断を
  含まず、本稿も機序を書かない (§3 の限定 3)。
- **D1094:** 性能低下の判定に使う下限値は現環境・workload 別に結果を見る前に測り直し、版を付けて束縛する。本 report は
  下限値による退行判定を行っておらず、載っている「参考幅」は外部 floor 由来で検出力の保証ではない (§2.5、§3 の限定 5)。
- **D1097:** 実走行での待ち量の分布を測る診断ビルドは作らず、主張を**指示値の平均**に限定する。本稿の μ は指示値
  (構成上の平均) であり、実待機時間の分布についての主張は置かない (§3 の限定 3)。

その他、本稿が書かないもの:

- **機序。** なぜ `symmetric-modulo` が高い側に出るのかは対象外である (D1097、D1678。事前登録 §3「差の機序が脱同期だけである」
  とは書けない — 総待ち量 = 呼び出し回数 × μ も同時に動く)。
- **`binary`、3 水準の ladder、ばらつきの用量反応** (事前登録 §3・§8・§9)。
- **性能の認証。** report の `official_certification` は `false` である。**ここにある性能値を根拠に variant を採用してはならない**
  (絶対規律 2)。
- **静的右 tail の 2 cohort との合成・比較。** 右 tail の稿は別の事前登録・別の格子 (1000〜9999 マイクロ秒) の事実である。
- **A-2 / A-6 / B-7 / [T-1998] の certification や退行判定との合成。** 別 protocol・別 attempt である (絶対規律 7)。
- **研究として成功か失敗か、新規性があるかの宣告** (D12)。`different` は事前登録の判定手続きが出した分類名であり、
  成否のラベルではない。
- **B-10 という論文項目の閉鎖。** 閉じたのは待ち方 grid の判定 (D1678) であって、B-10 の項目そのものではない
  (版 2026-09-20 §8 の書き方に従う)。
- **当時の実行全体を独立に監査したという主張、および report の再導出** (§3 の限定 12)。
- **この結果が他の workload・他の機体・他の CCBench pin・他の protocol へ転移するという主張。**
- **論文図。** 待ち方 grid の判定を描いた図は存在しない (§3 の限定 11)。

### 0.3 書くもの

事前登録が固定した格子・動作点・反復数・block・判定手続きの下で得られた、性能 cell と検証 slot の完全性、3 族 Holm の
出力、族統計量の入力である 54 個の対差、36 cell の効果量と 95% paired-block 区間と等価域との関係、退行込みの全 workload
報告、外部 floor 由来の参考幅、全 135 cell の中央値 throughput・ばらつき・abort 率・backoff 呼び出し回数・名目総待ち量・
正しさの認証状態 (事前登録 §8 の必須項目)、3 campaign と report phase の実行 identity、正しさの記録、物理残差の 3 区分、
この結果が言わないことの一覧、転記元の SHA-256。

---

## 1. 条件 — 事前登録が固定したものと、成果物が記録したもの

### 1.1 事前登録への束縛

report 成果物 (`b10_backoff_shape_provenance.json` の `preregistration` と report 冒頭) と 135 record の
`preregistration_binding` は、次の束縛を記録している。事前登録 commit・blob・spec・patch・formula の 5 つは
**3 campaign と report で同値**である (実測: 135 record で異なり数 1)。

| 事項 | 値 |
|---|---|
| 事前登録 commit (発効版) | `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` (2026-08-29) |
| 事前登録文書の git blob | `ea910de32df83c1bb320cbe62344dc5fb3b94684` (35,820 bytes、内容の SHA-256 `f43997a7d2350a9bdcd53e34dbf9b4b0648c9c659dd6111d0adcd08d29d6bdb2`) |
| spec (§5 の機械可読 spec) の SHA-256 | `9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2` (`schema_version` `izanagi-b10-backoff-shape-preregistration/v4`) |
| patch の SHA-256 | `36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832` |
| 式 (hole line) の SHA-256 | `5b3d8deefed35d05597891592d7af442c96b2fa094cdebc8376b2e9bc9cd7662` |
| 解析コード (report を出した driver) | commit `2a338449bb2798b729c5bc2f9bfe76463a7fe347` / SHA-256 `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9` |
| report の束縛 (`binding_sha256`) | `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483` (read-heavy campaign の束縛と同値。write-heavy / balanced の束縛は別値、§1.4) |
| 較正 record | `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` (SHA-256 `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`、`records` 1,000,000、`threads` 48、`clocks_per_us` 2100、`lower_bound_selected` true、`saturated` false、`cache_floor_warning` false) |
| CCBench pin | `511c953` |
| `official_certification` | `false` (driver の固定値) |

本稿の起草時、commit `77b33e37d`・`2a338449b` はいずれも HEAD の祖先である (実測)。作業ツリーの
`docs/b10-backoff-shape-preregistration.md` は v5 (39,278 bytes、SHA-256 `7918bc12e60b48de56e0e0c3526f1b166e4e1bab9258bf1bf87bda567bfe847b`)
であり、発効版の bytes ではない。v5 は 2026-09-07 の改訂で `schema_version` を `/v5` にし `patch_sha256` /
`formula_sha256` を付け替えたもので、同 §0 は「v4 の下で完了した 135 cell は v4 のまま残る。v5 へ resume・追記・再ラベル
してはならない」と定める。**本稿が束縛するのは v4 の発効版 blob `ea910de32…` であり、v5 ではない。** 現行 §10 の
erratum (2026-09-04 付、適用は 2026-09-07) は §7 の理由の記述の訂正であって、spec・grid・解析 field・判定手続き・過去の
成果物の束縛を変えない (同 §10。D1627)。

### 1.2 格子・動作点・反復・block

いずれも provenance JSON の `preregistration.spec` に記録された発効版 spec の値である。

- 形 (shape): `constant` (code 0、support = μ) と `symmetric-modulo` (code 1、support = μ/2 から 3μ/2 の閉区間)。
  符号化は `BACKOFF_FIXED = shape_code × 1000 + μ`。**登録した形はこの 2 つだけで、`binary` は登録していない。**
- μ (指示待ち量の構成上の平均、マイクロ秒): 2 / 5 / 10 / 25 / 50 / 100 の 6 点。
- 参照点 3 つ: `none` (`BACK_OFF=0`)、`adaptive` (`BACK_OFF=1`、`BACKOFF_FIXED=-1` = CCBench 内蔵の適応 backoff)、
  `zero-loop` (`BACK_OFF=1`、`BACKOFF_FIXED=0`)。参照点は報告するが、判定の族には入らない。
- 1 block = 参照 3 + 登録 cell 12 (2 形 × 6 μ) = 15 点。block は 3 つ (`block-1`〜`block-3`) で、block ごとの実行順は
  spec の `blocks.run_order` に固定されている (§2.6 の表は記録された `schedule_index` の順に並ぶ)。
- 動作点: `threads` 48、`records` 1,000,000 (較正 record)、`extime_s` 3。YCSB は `ycsb_max_ope` 10、`ycsb_rmw` 0、
  `ycsb_zipf_skew` 0.9、read ratio は write-heavy 5 / balanced 50 / read-heavy 95。
- 反復: 性能 5 rep/cell、正しさ 5 rep/cell (`correctness_mode` `legacy+performance`、§1.6)。screening なし。
- 判定 (spec `analysis`): 各 workload で block 内の対 (同 block・同 μ の `symmetric-modulo` 対 `constant`) の相対効果
  (中央値 throughput の比 − 1) を 18 個 (3 block × 6 μ) 作る。族は 3 つ (workload × `symmetric-modulo`)。統計量は
  対相対効果の和の絶対値、両側 exact 符号反転 permutation (全 2^18 列挙)、Holm を 3 族に当て、
  `testable` かつ Holm p ≤ α (0.05) なら `different`、そうでなければ `not-detected`。1 対でも使えない
  (欠測・性能 error・正しさ未認証・不安定・曝露不足) 族は `indeterminate` (p = 1)。cell ごとの効果量は 3 block の
  相対効果の平均、95% 区間は student-t (自由度 2、臨界値 4.302652729911275) の paired-block 区間、等価域は ±3.0%。
- 曝露: 性能 rep の abort 回数の和 (= backoff 呼び出し回数) が 10,000 未満の cell は `indeterminate`。

### 1.3 3 campaign と report phase の実行 identity

3 つの workload campaign と report phase の投入受領証・job 結果 (repo 外、§4.2) と、report の `records[]`・
`performance_cell_completeness.source_campaigns[]` から。

| workload | campaign id | request | 投入 (JST) | 完了 (JST) | 実行 host | driver (source commit) | 解析コード SHA-256 | `binding_sha256` |
|---|---|---|---|---|---|---|---|---|
| write-heavy | `b10-backoff-shape-silo-write-heavy-formal-e3de15eb` | `965564.nqsv` | 2026-09-01 21:02:12 | 2026-09-02 01:05:47 | **未記録** (`not-recorded-legacy-v2`) | `0a07481b8d3ff180b9817500b8ef44848ebe874e` | `34072fb2a5a5aed0e19ff1e653bb31bb71c3c434f32b3055c4b0b7a9e422c4ed` | `f0f9b2a1941707b29120a93af90cec70cfeabbf2309481f29cb19e8d71924e76` |
| balanced | `b10-backoff-shape-silo-balanced-formal-143a3f74` | `974207.nqsv` | 2026-09-03 20:29:45 | 2026-09-04 00:09:45 | `bnode015` | `c7ed565892cd4aba52d7fa47a7d1da17b117c005` | `f6246360c784813a581d7e104f116c07838106022fb9245f5de50b338e9ea0ec` | `588aaa9cd5eb844eeef48251777bb1d682d3b4993bae0e1b9bac94d893d7ae8f` |
| read-heavy | `b10-backoff-shape-silo-read-heavy-formal-acf840c8` | `977647.nqsv` | 2026-09-05 01:06:33 | 2026-09-05 11:56:55 | `bnode088` | `2a338449bb2798b729c5bc2f9bfe76463a7fe347` | `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9` | `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483` |
| (report) | — | `978195.nqsv` | 2026-09-05 13:14:11 | 2026-09-05 13:20:54 | 未記録 (集約のみ、測定なし) | `2a338449bb2798b729c5bc2f9bfe76463a7fe347` | `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9` | `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483` |

投入・完了時刻は受領証の `submitted_epoch` と job 結果の `completed_epoch` を JST へ直したもの。3 workload job の phase は
いずれも `verify-perf` (正しさ検証と性能測定を同一 job・同一 checkout で行う相。D1480 条件 1)、queue `gen_S`、1 node、
`driver_rc` 0、`driver.stderr` 0 bytes。write-heavy の壁時計枠は 43,200 秒、balanced 43,200 秒、read-heavy と report は
86,400 秒 (D1605)。受領証の job script SHA-256 は driver 版ごとに違う (write-heavy `c2c92b6c0a4d5487ec25895cdf42ca1243fe38094e470e81a2f3d3a401deebcc`、
balanced `bc80b66684bfe2dd498b4587846964f7497337b5921bdda97b81d169634ae892`、read-heavy と report `6f633ad08579d020190bf76263c006774a2d548a48ccd3f99106f090df628f6b`)。3 campaign の各 15 変種は `build_attempt_id` と `performance_binary_sha256` が変種ごとに相異なる
(workload あたり 15 個ずつ、実測)。

**write-heavy の実行 host は成果物に無い。** 当時の driver 版は host を記録しておらず、report を出した driver は
限定受理 (§1.4) で `execution_host` の不在を要求した上で `not-recorded-legacy-v2` を射影する。3 workload は別 job・
別日であり、balanced (`bnode015`) と read-heavy (`bnode088`) の host は異なるが、write-heavy が別 node だったかは一次資料から
確定できない。**workload 間で絶対 throughput を比べない** (§3 の限定 6)。

### 1.4 driver 版の差と限定受理

3 campaign は driver の版が違う (§1.3 の `source commit` 列)。driver 自身の bytes が `analysis_code_sha256` として
束縛へ入り campaign 同一性まで流れるため、後の版の driver は先に完走した campaign を通常経路では受理できない。
report を出した driver (`2a338449b`) は次の裁定に従い、**系列限りの有限な内容 digest 集合へ exact に閉じた限定受理**で
旧 2 系列を集約に入れた。

- **write-heavy** (`e3de15eb`、45 record): D1588 (2026-09-03)。実装内に凍結した 45 個の内容 digest 集合と一致しない
  record は 1 件も通さず、`execution_host` の不在を要求して射影する。**取り直していない** (D1509 決定 3)。D1588 の記録に
  よれば、もう 1 本の write-heavy campaign は 45 件すべてが性能 binary の SHA 不一致で測定不能に終わっており、「採用する
  campaign に選択の余地は無い」。本稿はその失敗系列を独立に監査していない (D1588 の記録への帰属)。
- **balanced** (`143a3f74`、45 record): D1636 項 4 (2026-09-05)、D1597 の形。campaign ID・旧 analysis commit・旧
  analysis SHA・旧 `binding_sha256`・45 件の内容 digest の exact 集合・45 cell exact 一致を balanced 専用の validator で
  要求し、write-heavy の validator とは共通化しない。**取り直していない。**
- **read-heavy** (`acf840c8`、45 record): report と同じ driver 版で走ったので、report 時点では通常経路で受理された。

D1597 (2026-09-04、ユーザー裁定) は「歴史的な束縛と同じ形の記録を一般に受理する規則は作らない。driver を編集する
たびに同じ形の限定受理を新しく書く」と定めている。本稿の起草時、45 record の内容 digest (`record_sha256`) を sorted
して改行で連結し末尾にも改行を付けた ascii の SHA-256 は write-heavy `6cb14801e858cedd955d983267436585d75c713be48d79b50b0076fd99845b71`、
balanced `8e5f0b48ba9e635e3d0e4e6c9c312c7436008dbe1a34f91a5763300920c37bad`、read-heavy
`27195442abce632ffae7a7241abd3cd8e765fe63fb590a62a37d4166049400c8` である (実計算。read-heavy の値は
`output/insights/2026-09-07/t1905-b10-readheavy-admit/README.md` が記録する meta digest と一致する)。

report より後の裁定 (D1771 / D1834、2026-09-08) は read-heavy 系列を含む限定受理の束縛先を lock 記録値・系列ごとの
lock 全体 digest へ改めたが、これは本 report の bytes と判定を変えない。**現行コードとの差は、記録された判定を無効に
する理由にならない** (絶対規律 7)。

### 1.5 report phase の投入と成果物

- 投入元: driver bytes を固定した checkout (detached `2a338449b`) から `tools/pegasus/submit_b10_backoff_shape.sh` の
  `--phase report` を 1 回だけ投入 (nonce `23409962b76be959bb523a0cd5a31bc1`、job script SHA-256
  `6f633ad08579d020190bf76263c006774a2d548a48ccd3f99106f090df628f6b`、受領証 schema `pegasus-b10-submit-receipt/v2`)。
- 実走: `978195.nqsv`、2026-09-05 13:14:11 投入、13:20:54 完了、`driver_rc` 0、`driver.stdout` 391 bytes (成果物 2 件の
  path のみ)、`driver.stderr` 0 bytes。report phase は測定を行わず、3 campaign の record と WAL を読んで集約するだけである。
- 成果物 (repo 内、bytes は固定 checkout の出力と一致することを記録 wave が確認、`output/insights/2026-09-05/t1905-b10-report/README.md` §1):
  `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json`
  (`schema_version` `b10-backoff-shape-provenance/v2`) と同 dir の `b10_backoff_shape_report_978195.nqsv-23409962b76b.md`。
  SHA-256 は §4.1。
- 記録: worklog entry 1288 (2026-09-07、`docs/archive/worklog-phase3-0907-1288.md`)、insight
  `output/insights/2026-09-05/t1905-b10-report/README.md`。判定は driver の `judge()` の出力をそのまま写し解釈を足していない
  (同 insight 冒頭)。同日 D1678 で「現行 report で閉じる」。

### 1.6 正しさの記録

正しさは trace 有効ビルドの別走行から来る (絶対規律 1、事前登録 §7)。3 campaign の WAL (`runs/wal.jsonl`、各 135 行) は
15 変種それぞれに `build_start` 1・`build_done` 1・`verify_done` 6・`commit` 1 を持ち、**`verify_done` は 1 campaign
あたり 90 件、3 campaign 合計 270 件すべてが `certified` = `true`、`verdict` = `serializable`、`anomalies` = 0** である
(実測)。`commit` 行の `verify_configs` は `["legacy", "performance"]`、`verifier_evidence` は変種ごとに 6 件を束ねる。

`verify_done` 90 件の内訳は `workload.tag` = `legacy` 15 件 (変種ごと 1 回) + `performance` 75 件 (変種ごと 5 回)。
report の `verification_slot_completeness` はこれを (workload, variant, verify_tag, repetition) の論理 slot 270 に射影し、
`expected` 270 / `completed` 270 / `incomplete` 0、`wal_truncated_tail` false、`wal_read_error` null、`unknown_verify_tags`
なし、`registered_tag_overruns` なしと記録する。**既知の限界** (同 field の `known_limitation` の逐語): duplicate WAL frames
and distinct repetitions cannot be distinguished because verify_done has no repetition identity。

**2 種類の検査条件は同じではない。** driver (固定 checkout の `orchestrator/campaign/pipeline.py`) の定義では、`legacy`
は 4 スレッド・200 tuple・read ratio 50・rmw 有効・max ope 5・1 秒の小規模高競合条件を 1 回、`performance` は性能測定と
同じ条件 (48 スレッド・1,000,000 records・workload 別の read ratio・3 秒) を 5 回である。したがって「性能を測った条件その
ものの trace 有効ビルドが、各変種 5 回すべて `serializable`・anomaly 0 だった」と書ける (§3 の限定 8)。

**性能測定に使った binary は認証した attempt の binary である。** 135 record は `build_attempt_id` と
`performance_binary_sha256` を持ち、report は WAL の certified attempt との一致を要求する (D1480 条件 1、
事前登録 §7 「一致しないセルは bench へ送らず判定不能とする」)。判定不能 cell は 0 である。record の
`build_attempt_id` (workload あたり 15 個) はいずれも同 campaign の WAL に現れる (実測)。

**これは性能の認証ではない。** `official_certification` は `false` であり、report 冒頭は「Formal driver 経路について、
登録前に性能を見ていないという限定主張だけを行う」と書く。

### 1.7 物理残差の 3 区分

事前登録 §8 の要求に従い区別して書く。本稿は物理残差を測り直していない。

- **開示した 18 cell の probe:** 発効版 §4.1 (request `953543.nqsv`、host `bnode142`、2026-08-27 UTC 16:26、
  probe 100,000 呼び出し/cell、`clocks_per_us` 2100、結果 SHA-256 `6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3`、
  probe 時点の placeholder 事前登録 commit `1549bd927`)。
- **登録した 12 cell とその値:** provenance JSON の `physical_residual_values` (spec §5 と同値)。上限は絶対偏差 1.0% 未満
  (exclusive)、測定量は `realized-backoff-loop-cycles`。

| shape | μ (µs) | 指示平均 (cycles) | 実現平均 (cycles) | 偏差 (%) |
|---|---:|---:|---:|---:|
| constant | 2 | 4200.0 | 4223.59116 | +0.5617 |
| symmetric-modulo | 2 | 4200.0 | 4218.32476 | +0.4363 |
| constant | 5 | 10500.0 | 10538.38268 | +0.3655 |
| symmetric-modulo | 5 | 10500.0 | 10544.10586 | +0.4201 |
| constant | 10 | 21000.0 | 21035.41464 | +0.1686 |
| symmetric-modulo | 10 | 21000.0 | 21047.27694 | +0.2251 |
| constant | 25 | 52500.0 | 52530.59194 | +0.0583 |
| symmetric-modulo | 25 | 52500.0 | 52275.76334 | −0.4271 |
| constant | 50 | 105000.0 | 105021.8346 | +0.0208 |
| symmetric-modulo | 50 | 105000.0 | 104692.05524 | −0.2933 |
| constant | 100 | 210000.0 | 210029.9768 | +0.0143 |
| symmetric-modulo | 100 | 210000.0 | 210487.20626 | +0.2320 |

  偏差は小数第 4 位に丸めた (生値は JSON の `deviation_pct`)。最大絶対偏差は 0.5616942857142844% (`constant` / μ 2) で
  上限 1.0% の内側である。
- **v4 の束縛:** §1.1 の commit・blob・spec・patch・formula。

**これは合成ループの残差であって、本走中の実待機時間ではない** (事前登録 §9 の項目 7、D1097)。

---

## 2. 結果

### 2.1 完全性と曝露

| 事項 | 値 |
|---|---|
| 性能 cell | expected 135 / observed 135 (論理 key = workload, block_id, point)。3 campaign とも 45 |
| 検証 slot | expected 270 / completed 270 / incomplete 0 (§1.6) |
| `correctness_certified` | 135 cell すべて `true`、`missing` は 135 cell すべて `false` |
| `unstable` | 135 cell すべて `false` (`cv` の最大は 0.0336、balanced `block-1` `adaptive`。登録 cell の最大は 0.0279、balanced `block-3` `symmetric-modulo-mu5`) |
| 曝露 (backoff 呼び出し ≥ 10,000 回/cell) | 登録 cell 108 + `adaptive` 9 + `zero-loop` 9 = 126 cell が `met`。`none` 9 cell は呼び出し 0 回で `indeterminate` だが、判定の族には入らない参照点である |
| 判定不能 cell / 族 | 0 / 0 (3 族とも `status` `testable`、`reasons` 空) |
| `official_certification` | `false` (135 record と report で同値) |

`performance_cell_completeness` は「exact 135 cell の gate は 3 workload job の終了を証明しない。終了は 3 job の終了後に
投入する順序で保証し、機械的な終了 gate は無い」と記録する (`proves_all_workload_jobs_terminated` false)。

### 2.2 3 族 Holm

判定 (`judgement`、`schema_version` `b10-backoff-shape-judgement/v1`、α 0.05、spec SHA `9c594114…`):

| 族 (workload / shape) | `status` | `outcome` | 対の数 | raw p | Holm p |
|---|---|---|---:|---:|---:|
| write-heavy / symmetric-modulo | `testable` | **`different`** | 18 | 0.02556610107421875 (= 6702 / 2^18) | 0.02556610107421875 |
| balanced / symmetric-modulo | `testable` | **`different`** | 18 | 0.00026702880859375 (= 70 / 2^18) | 0.0005340576171875 |
| read-heavy / symmetric-modulo | `testable` | **`different`** | 18 | 7.62939453125e-06 (= 2 / 2^18) | 2.288818359375e-05 |

raw p は全 2^18 = 262,144 通りの符号反転を列挙した exact 値であり、分母 2^18 の分数で書ける (括弧内。本稿の再計算)。
read-heavy の 2 / 2^18 は 18 対すべてが同符号のときの両側 p の下限である。Holm は昇順 (read-heavy × 3、balanced × 2、
write-heavy × 1) で、3 族とも Holm p ≤ 0.05。report .md は raw p を `0.025566101` / `0.00026702881` / `7.6293945e-06`
と丸めて印字する。

**方向。** 族統計量の入力である対相対効果 (`symmetric-modulo` の中央値 throughput ÷ `constant` の中央値 throughput − 1)
の 18 個の和は 3 族とも正 (write-heavy +0.11203、balanced +0.13168、read-heavy +0.08773。本稿の再計算)。
**方向は 3 族とも `symmetric-modulo` が高い側である。** これは事前登録 §3 が「有意な族については方向・効果量・信頼区間を
この contrast に限って限定付きで述べる」と認めた範囲の記述である。

### 2.3 対差 (族統計量の入力、18 × 3)

provenance JSON の `judgement.families[].differences` (記録順) を、block と μ に対応づけて % で示す。対応づけは本稿の
起草時に 135 record の `median_tps` から同じ式で再計算して確かめた (54 個すべて一致。順序は block-1 の μ 2 → 100、
block-2、block-3 の順)。値は小数第 2 位に丸めた。

| workload | block | μ 2 | μ 5 | μ 10 | μ 25 | μ 50 | μ 100 |
|---|---|---:|---:|---:|---:|---:|---:|
| write-heavy | block-1 | −1.13% | −1.49% | +0.20% | +2.21% | +1.63% | +1.25% |
| write-heavy | block-2 | +1.75% | −0.68% | −0.13% | +0.66% | +1.09% | +1.07% |
| write-heavy | block-3 | +1.62% | −0.75% | +1.09% | +0.97% | +0.73% | +1.11% |
| balanced | block-1 | +0.83% | +0.10% | +0.88% | +2.66% | +0.84% | +1.05% |
| balanced | block-2 | −0.71% | +0.45% | +1.26% | +0.76% | +0.46% | +0.92% |
| balanced | block-3 | +1.30% | −0.19% | +0.70% | +0.70% | +0.84% | +0.32% |
| read-heavy | block-1 | +0.91% | +0.94% | +0.28% | +0.47% | +0.31% | +0.30% |
| read-heavy | block-2 | +0.44% | +0.48% | +0.06% | +0.79% | +0.33% | +0.56% |
| read-heavy | block-3 | +0.58% | +0.22% | +0.27% | +0.86% | +0.53% | +0.43% |

**退行込みの報告 (対の水準)。** 負の対差は write-heavy 5 / 18 (μ 2 の block-1、μ 5 の 3 block、μ 10 の block-2)、
balanced 2 / 18 (μ 2 の block-2、μ 5 の block-3)、read-heavy 0 / 18。最小は write-heavy block-1 μ 5 の −1.49%、
最大は balanced block-1 μ 25 の +2.66%。

### 2.4 cell ごとの効果量と 95% paired-block 区間

`judgement.cell_effects` の 36 cell (`symmetric-modulo` 18 + `constant` 18)。`constant` の 18 cell は自分自身との対なので
効果 0、区間 [0, 0]、`inside-equivalence-range` である (report にそのまま並ぶ)。以下は `symmetric-modulo` 18 cell を % に
直し小数第 2 位に丸めたもの (効果 [下限, 上限] 等価域との関係)。生値は続く表。

| workload | μ 2 | μ 5 | μ 10 | μ 25 | μ 50 | μ 100 |
|---|---|---|---|---|---|---|
| write-heavy | +0.74 [−3.29, +4.78] 境界を跨ぐ | −0.97 [−2.10, +0.15] 内側 | +0.39 [−1.18, +1.96] 内側 | +1.28 [−0.75, +3.31] 境界を跨ぐ | +1.15 [+0.02, +2.28] 内側 | +1.14 [+0.91, +1.38] 内側 |
| balanced | +0.47 [−2.14, +3.08] 境界を跨ぐ | +0.12 [−0.67, +0.92] 内側 | +0.95 [+0.23, +1.66] 内側 | +1.37 [−1.41, +4.15] 境界を跨ぐ | +0.71 [+0.18, +1.25] 内側 | +0.76 [−0.20, +1.73] 内側 |
| read-heavy | +0.65 [+0.04, +1.25] 内側 | +0.55 [−0.36, +1.46] 内側 | +0.20 [−0.10, +0.50] 内側 | +0.71 [+0.20, +1.21] 内側 | +0.39 [+0.10, +0.69] 内側 | +0.43 [+0.11, +0.75] 内側 |

生値 (`effect` / `ci95_low` / `ci95_high`、小数のまま):

| workload | μ | `effect` | `ci95_low` | `ci95_high` | `equivalence_relation` | `status` |
|---|---:|---:|---:|---:|---|---|
| write-heavy | 2 | 0.007442284930762007 | -0.03287351722250576 | 0.04775808708402978 | `overlaps-equivalence-boundary` | `estimable` |
| write-heavy | 5 | -0.009738229292106326 | -0.020976416345050222 | 0.0014999577608375714 | `inside-equivalence-range` | `estimable` |
| write-heavy | 10 | 0.0038867971967747237 | -0.011826149118458707 | 0.019599743512008154 | `inside-equivalence-range` | `estimable` |
| write-heavy | 25 | 0.012787354532664738 | -0.007540514927378788 | 0.03311522399270826 | `overlaps-equivalence-boundary` | `estimable` |
| write-heavy | 50 | 0.011523456644465968 | 0.00021801346639591275 | 0.022828899822536025 | `inside-equivalence-range` | `estimable` |
| write-heavy | 100 | 0.011440148218973952 | 0.009098420777480324 | 0.01378187566046758 | `inside-equivalence-range` | `estimable` |
| balanced | 2 | 0.004714900870075052 | -0.021400312022563796 | 0.030830113762713898 | `overlaps-equivalence-boundary` | `estimable` |
| balanced | 5 | 0.0012253172031591413 | -0.006720210172551036 | 0.009170844578869318 | `inside-equivalence-range` | `estimable` |
| balanced | 10 | 0.009462806928990078 | 0.0023389201356250056 | 0.01658669372235515 | `inside-equivalence-range` | `estimable` |
| balanced | 25 | 0.01371228762961548 | -0.0140820535791324 | 0.04150662883836336 | `overlaps-equivalence-boundary` | `estimable` |
| balanced | 50 | 0.007128362900253575 | 0.0017596778667229498 | 0.0124970479337842 | `inside-equivalence-range` | `estimable` |
| balanced | 100 | 0.00764931941820753 | -0.0019781040029110434 | 0.017276742839326103 | `inside-equivalence-range` | `estimable` |
| read-heavy | 2 | 0.006461511483549638 | 0.00042504164345056033 | 0.012497981323648717 | `inside-equivalence-range` | `estimable` |
| read-heavy | 5 | 0.005481995949940736 | -0.003587960840649656 | 0.01455195274053113 | `inside-equivalence-range` | `estimable` |
| read-heavy | 10 | 0.0020219568439350244 | -0.0010020143689218313 | 0.00504592805679188 | `inside-equivalence-range` | `estimable` |
| read-heavy | 25 | 0.0070534494843090085 | 0.0019942094492431534 | 0.012112689519374864 | `inside-equivalence-range` | `estimable` |
| read-heavy | 50 | 0.003915419971911138 | 0.0009546519275700489 | 0.006876188016252227 | `inside-equivalence-range` | `estimable` |
| read-heavy | 100 | 0.004308112939568787 | 0.001121780056311224 | 0.007494445822826349 | `inside-equivalence-range` | `estimable` |

**集計。** 36 cell の `status` はすべて `estimable`。等価域 ±3.0% との関係は、**内側 32、境界を跨ぐ 4** (write-heavy μ 2・
μ 25、balanced μ 2・μ 25)、**外側 0**。判定不能 0。本稿の起草時に 135 record の `median_tps` から効果 (3 block の相対効果の
平均) と区間 (平均 ± 4.302652729911275 × 標本標準偏差 / √3) を再計算し、18 cell すべてで `effect`・両端が一致 (差 < 1e-9)、
等価域との関係も 36 cell すべてで一致した (転記の検算。§3 の限定 12)。

**退行込みの報告 (cell の水準)。** 点推定が負なのは write-heavy μ 5 の 1 cell (−0.97%、区間 [−2.10%, +0.15%] は 0 を含む)
だけで、残り 17 cell は正。区間の下限が正 (0 を含まない) なのは write-heavy μ 50・μ 100、balanced μ 10・μ 50、read-heavy
μ 2・μ 25・μ 50・μ 100 の 8 cell、区間が 0 を含むのは 10 cell である。**どの workload でも、区間全体が等価域の外へ出た cell は
無い。** 境界を跨ぐ 4 cell は区間の一部が等価域の外にある (例: write-heavy μ 2 の区間は [−3.29%, +4.78%])。点推定は 36 cell
すべてが等価域の内側である。
事前登録 §8 が求める「対象 workload で勝っても他 workload で退行があれば退行込みで全件報告する」に対しては、
上の 18 cell と §2.3 の 54 対がその全件である。

### 2.5 外部 floor 由来の参考幅 (検出力の保証ではない)

report と spec の `external_floor_reference_widths` (`power_guarantee` false、用語は `external-floor-derived-reference-width`):

| workload | between-run CV (%) | 参考幅 (%) | 出所環境 |
|---|---:|---:|---|
| write-heavy | 0.67 | 1.9 | linux-baremetal |
| balanced | 1.07 | 3.0 | linux-baremetal |
| read-heavy | 0.22 | 0.62 | pegasus |

事前登録 §6 のとおり、これは本実験が実装した検定の検出力ではない。write-heavy と balanced の値は別環境
(linux-baremetal) 由来で、Pegasus の値ではない。report は「非有意は登録した設計が差を検出しなかったことだけを意味し、
検出力の保証の主張ではない」と書く。本稿は 3 族とも `different` なのでこの但し書きの適用場面は無いが、**「検出力の範囲内で
検出した」とも書かない** (§3 の限定 9)。この表を退行判定の下限値として使っていない (D1094、§3 の限定 5)。

### 2.6 全 135 cell (事前登録 §8 の必須項目)

provenance JSON の `records[]` から、workload → block → `schedule_index` の順に転記した。列: 実行 host、block、point、
shape、μ (µs)、中央値 throughput (毎秒トランザクション数、5 rep の中央値)、CV (5 rep の変動係数)、abort 率、abort 回数
(5 rep の和)、backoff 呼び出し回数 (= abort 回数。`none` は 0)、毎秒呼び出し回数、名目総待ち量 (µs、= 呼び出し回数 × μ。
`none` と `adaptive` は無し (JSON では `null`)、`zero-loop` は μ = 0 なので 0)、正しさ認証、`unstable`、曝露。CV と abort 率は小数第 4 位、毎秒呼び出し回数は小数第 2 位に丸めた。
各 cell の 5 rep の throughput・abort 回数・commit 回数・壁時計は `records[].throughputs` / `rep_abort_counts` /
`rep_commit_counts` / `rep_walltime_s` にあり (675 個ずつ、実測)、本稿には転記しない。

| workload | 実行 host | block | point | shape | μ (µs) | 中央値 throughput | CV | abort 率 | abort 回数 | backoff 呼び出し回数 | 毎秒呼び出し | 名目総待ち量 (µs) | 正しさ認証 | `unstable` | 曝露 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| write-heavy | not-recorded-legacy-v2 | block-1 | none | — | — | 2422011 | 0.0322 | 0.7849 | 134719086 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-1 | adaptive | — | — | 1354088 | 0.0179 | 0.1221 | 2830938 | 2830938 | 188729.20 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | zero-loop | constant | 0 | 2439674 | 0.0083 | 0.7818 | 130595054 | 130595054 | 8706336.93 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu2 | constant | 2 | 3454217 | 0.0074 | 0.6364 | 90469377 | 90469377 | 6031291.80 | 180938754 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3415244 | 0.0092 | 0.6350 | 89221334 | 89221334 | 5948088.93 | 178442668 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3923154 | 0.0056 | 0.5006 | 58974695 | 58974695 | 3931646.33 | 294873475 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu5 | constant | 5 | 3982673 | 0.0200 | 0.4990 | 58789077 | 58789077 | 3919271.80 | 293945385 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu10 | constant | 10 | 3924247 | 0.0044 | 0.3873 | 37256513 | 37256513 | 2483767.53 | 372565130 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3932174 | 0.0034 | 0.3862 | 37156234 | 37156234 | 2477082.27 | 371562340 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3505891 | 0.0068 | 0.2586 | 18271151 | 18271151 | 1218076.73 | 456778775 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu25 | constant | 25 | 3430191 | 0.0046 | 0.2631 | 18381750 | 18381750 | 1225450.00 | 459543750 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu50 | constant | 50 | 2904761 | 0.0041 | 0.1915 | 10318030 | 10318030 | 687868.67 | 515901500 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2952224 | 0.0036 | 0.1882 | 10250505 | 10250505 | 683367.00 | 512525250 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2375988 | 0.0029 | 0.1357 | 5599704 | 5599704 | 373313.60 | 559970400 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu100 | constant | 100 | 2346648 | 0.0044 | 0.1376 | 5623103 | 5623103 | 374873.53 | 562310300 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | adaptive | — | — | 1356456 | 0.0098 | 0.1247 | 2918754 | 2918754 | 194583.60 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | zero-loop | constant | 0 | 2428482 | 0.0166 | 0.7834 | 130553071 | 130553071 | 8703538.07 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | none | — | — | 2386915 | 0.0097 | 0.7906 | 135235525 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3434411 | 0.0152 | 0.6353 | 89880322 | 89880322 | 5992021.47 | 179760644 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu2 | constant | 2 | 3375498 | 0.0144 | 0.6388 | 90148296 | 90148296 | 6009886.40 | 180296592 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu5 | constant | 5 | 3951087 | 0.0044 | 0.5000 | 59341088 | 59341088 | 3956072.53 | 296705440 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3924361 | 0.0075 | 0.5001 | 58827499 | 58827499 | 3921833.27 | 294137495 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3950786 | 0.0038 | 0.3852 | 37084422 | 37084422 | 2472294.80 | 370844220 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu10 | constant | 10 | 3955909 | 0.0028 | 0.3849 | 37129418 | 37129418 | 2475294.53 | 371294180 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu25 | constant | 25 | 3444681 | 0.0024 | 0.2622 | 18345577 | 18345577 | 1223038.47 | 458639425 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3467458 | 0.0056 | 0.2601 | 18319305 | 18319305 | 1221287.00 | 457982625 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2948141 | 0.0043 | 0.1883 | 10246320 | 10246320 | 683088.00 | 512316000 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu50 | constant | 50 | 2916249 | 0.0031 | 0.1907 | 10302119 | 10302119 | 686807.93 | 515105950 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu100 | constant | 100 | 2353744 | 0.0019 | 0.1373 | 5620589 | 5620589 | 374705.93 | 562058900 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2378941 | 0.0014 | 0.1356 | 5600801 | 5600801 | 373386.73 | 560080100 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | zero-loop | constant | 0 | 2355992 | 0.0262 | 0.7872 | 132217987 | 132217987 | 8814532.47 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | none | — | — | 2380088 | 0.0122 | 0.7896 | 133974270 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-3 | adaptive | — | — | 1375023 | 0.0119 | 0.1255 | 2967792 | 2967792 | 197852.80 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu2 | constant | 2 | 3373450 | 0.0078 | 0.6407 | 90258398 | 90258398 | 6017226.53 | 180516796 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3427953 | 0.0079 | 0.6361 | 89686236 | 89686236 | 5979082.40 | 179372472 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3918943 | 0.0099 | 0.5007 | 58883537 | 58883537 | 3925569.13 | 294417685 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu5 | constant | 5 | 3948581 | 0.0049 | 0.4999 | 59291149 | 59291149 | 3952743.27 | 296455745 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu10 | constant | 10 | 3916268 | 0.0082 | 0.3868 | 37203056 | 37203056 | 2480203.73 | 372030560 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3959094 | 0.0067 | 0.3849 | 37048838 | 37048838 | 2469922.53 | 370488380 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3484569 | 0.0040 | 0.2595 | 18303393 | 18303393 | 1220226.20 | 457584825 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu25 | constant | 25 | 3451158 | 0.0049 | 0.2619 | 18360901 | 18360901 | 1224060.07 | 459022525 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu50 | constant | 50 | 2919663 | 0.0033 | 0.1905 | 10301616 | 10301616 | 686774.40 | 515080800 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2940961 | 0.0047 | 0.1883 | 10246544 | 10246544 | 683102.93 | 512327200 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2381736 | 0.0010 | 0.1355 | 5598223 | 5598223 | 373214.87 | 559822300 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu100 | constant | 100 | 2355560 | 0.0035 | 0.1373 | 5624052 | 5624052 | 374936.80 | 562405200 | yes | no | met |
| balanced | bnode015 | block-1 | none | — | — | 3652963 | 0.0231 | 0.6874 | 121545410 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-1 | adaptive | — | — | 1253516 | 0.0336 | 0.2115 | 5012955 | 5012955 | 334197.00 | — | yes | no | met |
| balanced | bnode015 | block-1 | zero-loop | constant | 0 | 3676625 | 0.0097 | 0.6833 | 118701222 | 118701222 | 7913414.80 | 0 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu2 | constant | 2 | 4187219 | 0.0106 | 0.5634 | 81244885 | 81244885 | 5416325.67 | 162489770 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4221855 | 0.0047 | 0.5633 | 81484350 | 81484350 | 5432290.00 | 162968700 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4172133 | 0.0064 | 0.4672 | 54809545 | 54809545 | 3653969.67 | 274047725 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu5 | constant | 5 | 4167860 | 0.0058 | 0.4687 | 55072049 | 55072049 | 3671469.93 | 275360245 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu10 | constant | 10 | 3813996 | 0.0040 | 0.3893 | 36475711 | 36475711 | 2431714.07 | 364757110 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3847706 | 0.0020 | 0.3863 | 36369003 | 36369003 | 2424600.20 | 363690030 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3084737 | 0.0041 | 0.2891 | 18817078 | 18817078 | 1254471.87 | 470426950 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu25 | constant | 25 | 3004729 | 0.0238 | 0.2923 | 18538341 | 18538341 | 1235889.40 | 463458525 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu50 | constant | 50 | 2428183 | 0.0024 | 0.2272 | 10705046 | 10705046 | 713669.73 | 535252300 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2448502 | 0.0023 | 0.2250 | 10669776 | 10669776 | 711318.40 | 533488800 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1879789 | 0.0026 | 0.1714 | 5834649 | 5834649 | 388976.60 | 583464900 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu100 | constant | 100 | 1860266 | 0.0032 | 0.1732 | 5844335 | 5844335 | 389622.33 | 584433500 | yes | no | met |
| balanced | bnode015 | block-2 | adaptive | — | — | 1232300 | 0.0255 | 0.2117 | 5025250 | 5025250 | 335016.67 | — | yes | no | met |
| balanced | bnode015 | block-2 | zero-loop | constant | 0 | 3656568 | 0.0121 | 0.6843 | 118760199 | 118760199 | 7917346.60 | 0 | yes | no | met |
| balanced | bnode015 | block-2 | none | — | — | 3586501 | 0.0095 | 0.6900 | 120199576 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4198348 | 0.0081 | 0.5620 | 81082198 | 81082198 | 5405479.87 | 162164396 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu2 | constant | 2 | 4228433 | 0.0075 | 0.5622 | 81410765 | 81410765 | 5427384.33 | 162821530 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu5 | constant | 5 | 4180192 | 0.0030 | 0.4673 | 55026253 | 55026253 | 3668416.87 | 275131265 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4199083 | 0.0070 | 0.4653 | 54900500 | 54900500 | 3660033.33 | 274502500 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3862252 | 0.0038 | 0.3864 | 36401759 | 36401759 | 2426783.93 | 364017590 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu10 | constant | 10 | 3814226 | 0.0038 | 0.3901 | 36545715 | 36545715 | 2436381.00 | 365457150 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu25 | constant | 25 | 3056567 | 0.0033 | 0.2919 | 18860673 | 18860673 | 1257378.20 | 471516825 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3079650 | 0.0039 | 0.2895 | 18813525 | 18813525 | 1254235.00 | 470338125 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2441075 | 0.0033 | 0.2256 | 10668446 | 10668446 | 711229.73 | 533422300 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu50 | constant | 50 | 2429818 | 0.0016 | 0.2270 | 10700591 | 10700591 | 713372.73 | 535029550 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu100 | constant | 100 | 1862902 | 0.0051 | 0.1730 | 5837823 | 5837823 | 389188.20 | 583782300 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1880074 | 0.0017 | 0.1712 | 5828019 | 5828019 | 388534.60 | 582801900 | yes | no | met |
| balanced | bnode015 | block-3 | zero-loop | constant | 0 | 3618263 | 0.0050 | 0.6834 | 116995409 | 116995409 | 7799693.93 | 0 | yes | no | met |
| balanced | bnode015 | block-3 | none | — | — | 3572391 | 0.0107 | 0.6911 | 120029097 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-3 | adaptive | — | — | 1229420 | 0.0286 | 0.2089 | 4918601 | 4918601 | 327906.73 | — | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu2 | constant | 2 | 4180079 | 0.0055 | 0.5638 | 81150807 | 81150807 | 5410053.80 | 162301614 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4234369 | 0.0071 | 0.5613 | 80992548 | 80992548 | 5399503.20 | 161985096 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4192970 | 0.0279 | 0.4676 | 54594151 | 54594151 | 3639610.07 | 272970755 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu5 | constant | 5 | 4200819 | 0.0102 | 0.4672 | 54975846 | 54975846 | 3665056.40 | 274879230 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu10 | constant | 10 | 3809797 | 0.0058 | 0.3890 | 36512992 | 36512992 | 2434199.47 | 365129920 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3836308 | 0.0018 | 0.3871 | 36378287 | 36378287 | 2425219.13 | 363782870 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3083873 | 0.0019 | 0.2891 | 18807661 | 18807661 | 1253844.07 | 470191525 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu25 | constant | 25 | 3062565 | 0.0047 | 0.2916 | 18856718 | 18856718 | 1257114.53 | 471417950 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu50 | constant | 50 | 2424905 | 0.0023 | 0.2275 | 10702404 | 10702404 | 713493.60 | 535120200 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2445236 | 0.0030 | 0.2253 | 10661626 | 10661626 | 710775.07 | 533081300 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1869508 | 0.0054 | 0.1718 | 5831209 | 5831209 | 388747.27 | 583120900 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu100 | constant | 100 | 1863479 | 0.0016 | 0.1729 | 5843456 | 5843456 | 389563.73 | 584345600 | yes | no | met |
| read-heavy | bnode088 | block-1 | none | — | — | 10311699 | 0.0095 | 0.1549 | 28470693 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-1 | adaptive | — | — | 2323131 | 0.0085 | 0.0402 | 1460201 | 1460201 | 97346.73 | — | yes | no | met |
| read-heavy | bnode088 | block-1 | zero-loop | constant | 0 | 10198102 | 0.0047 | 0.1539 | 27795829 | 27795829 | 1853055.27 | 0 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu2 | constant | 2 | 9630186 | 0.0028 | 0.1447 | 24423602 | 24423602 | 1628240.13 | 48847204 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9718203 | 0.0031 | 0.1446 | 24639061 | 24639061 | 1642604.07 | 49278122 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9102850 | 0.0027 | 0.1339 | 21087198 | 21087198 | 1405813.20 | 105435990 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu5 | constant | 5 | 9017765 | 0.0012 | 0.1349 | 21081311 | 21081311 | 1405420.73 | 105406555 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu10 | constant | 10 | 8232900 | 0.0048 | 0.1227 | 17250734 | 17250734 | 1150048.93 | 172507340 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8255918 | 0.0033 | 0.1216 | 17122746 | 17122746 | 1141516.40 | 171227460 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6899590 | 0.0017 | 0.0994 | 11430533 | 11430533 | 762035.53 | 285763325 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu25 | constant | 25 | 6867054 | 0.0023 | 0.1002 | 11469100 | 11469100 | 764606.67 | 286727500 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu50 | constant | 50 | 5651380 | 0.0014 | 0.0815 | 7520706 | 7520706 | 501380.40 | 376035300 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5669177 | 0.0019 | 0.0810 | 7486903 | 7486903 | 499126.87 | 374345150 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4473432 | 0.0022 | 0.0633 | 4535535 | 4535535 | 302369.00 | 453553500 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu100 | constant | 100 | 4459835 | 0.0019 | 0.0638 | 4554715 | 4554715 | 303647.67 | 455471500 | yes | no | met |
| read-heavy | bnode088 | block-2 | adaptive | — | — | 2327468 | 0.0064 | 0.0400 | 1451693 | 1451693 | 96779.53 | — | yes | no | met |
| read-heavy | bnode088 | block-2 | zero-loop | constant | 0 | 10132409 | 0.0041 | 0.1539 | 27600091 | 27600091 | 1840006.07 | 0 | yes | no | met |
| read-heavy | bnode088 | block-2 | none | — | — | 10179288 | 0.0033 | 0.1549 | 27960631 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9674282 | 0.0031 | 0.1444 | 24483970 | 24483970 | 1632264.67 | 48967940 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu2 | constant | 2 | 9631925 | 0.0023 | 0.1447 | 24440757 | 24440757 | 1629383.80 | 48881514 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu5 | constant | 5 | 9005092 | 0.0022 | 0.1350 | 21075893 | 21075893 | 1405059.53 | 105379465 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9048083 | 0.0032 | 0.1339 | 20991815 | 20991815 | 1399454.33 | 104959075 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8220868 | 0.0073 | 0.1218 | 17070086 | 17070086 | 1138005.73 | 170700860 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu10 | constant | 10 | 8215784 | 0.0050 | 0.1226 | 17206917 | 17206917 | 1147127.80 | 172069170 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu25 | constant | 25 | 6844838 | 0.0017 | 0.1004 | 11452259 | 11452259 | 763483.93 | 286306475 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6898605 | 0.0026 | 0.0995 | 11446665 | 11446665 | 763111.00 | 286166625 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5670159 | 0.0018 | 0.0809 | 7484550 | 7484550 | 498970.00 | 374227500 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu50 | constant | 50 | 5651461 | 0.0024 | 0.0814 | 7508840 | 7508840 | 500589.33 | 375442000 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu100 | constant | 100 | 4452598 | 0.0029 | 0.0639 | 4557727 | 4557727 | 303848.47 | 455772700 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4477590 | 0.0011 | 0.0633 | 4537706 | 4537706 | 302513.73 | 453770600 | yes | no | met |
| read-heavy | bnode088 | block-3 | zero-loop | constant | 0 | 10133586 | 0.0057 | 0.1539 | 27573535 | 27573535 | 1838235.67 | 0 | yes | no | met |
| read-heavy | bnode088 | block-3 | none | — | — | 10158776 | 0.0034 | 0.1547 | 27898034 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-3 | adaptive | — | — | 2326305 | 0.0075 | 0.0405 | 1479465 | 1479465 | 98631.00 | — | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu2 | constant | 2 | 9618673 | 0.0018 | 0.1450 | 24479065 | 24479065 | 1631937.67 | 48958130 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9674916 | 0.0026 | 0.1445 | 24524138 | 24524138 | 1634942.53 | 49048276 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9040824 | 0.0029 | 0.1341 | 20995570 | 20995570 | 1399704.67 | 104977850 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu5 | constant | 5 | 9020648 | 0.0030 | 0.1348 | 21103528 | 21103528 | 1406901.87 | 105517640 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu10 | constant | 10 | 8204568 | 0.0060 | 0.1227 | 17193604 | 17193604 | 1146240.27 | 171936040 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8226320 | 0.0050 | 0.1216 | 17091221 | 17091221 | 1139414.73 | 170912210 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6910847 | 0.0014 | 0.0995 | 11452746 | 11452746 | 763516.40 | 286318650 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu25 | constant | 25 | 6852143 | 0.0028 | 0.1002 | 11451239 | 11451239 | 763415.93 | 286280975 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu50 | constant | 50 | 5642522 | 0.0030 | 0.0815 | 7509987 | 7509987 | 500665.80 | 375499350 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5672363 | 0.0009 | 0.0809 | 7488458 | 7488458 | 499230.53 | 374422900 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4477951 | 0.0009 | 0.0633 | 4540249 | 4540249 | 302683.27 | 454024900 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu100 | constant | 100 | 4458944 | 0.0008 | 0.0638 | 4557110 | 4557110 | 303807.33 | 455711000 | yes | no | met |

**この表は記述的な集計である。** 参照点 `adaptive` (CCBench 内蔵の適応 backoff) の中央値 throughput が 9 block すべてで同 block の
登録 12 cell の最小値より低いこと、abort 率が 18 系列 (3 workload × 2 形 × 3 block) すべてで μ に対し狭義に単調減少すること、
中央値 throughput は read-heavy の 6 系列すべてで μ 2 から狭義に単調減少する一方、write-heavy の 6 系列はすべて非単調で μ 5 または
μ 10 が最大、balanced は 6 系列中 4 系列 (`constant` の block-1・block-2、`symmetric-modulo` の block-1・block-3) が狭義に単調減少で
残り 2 系列 (`constant` の block-3、`symmetric-modulo` の block-2) は μ 5 が最大であること (本稿の起草時に表の値から確認) は、表の値の記述であって機序でも採用根拠でもない。参照点は
判定の族に入らない (§1.2)。

### 2.7 事前登録 §3 の「書ける主張」の範囲での要約

48 スレッドの Silo / YCSB 3 workload、μ = 2〜100 µs の登録 grid で、指示待ち量の構成上の平均を μ に揃え合成ループの
物理残差を 1.0% 未満に押さえた条件のもと、**`constant` と `symmetric-modulo` という 2 つの特定の実装の間の throughput の
差は、事前登録した手続きで 3 族とも検出された** (`different`)。方向は 3 族とも `symmetric-modulo` が高い側。効果量の 95% 区間は
32 cell で ±3.0% の等価域の内側、4 cell で境界を跨ぎ、区間全体が外側に出た cell は無い。**これはこの 1 contrast についての主張であり、待ち方の
効果一般・ばらつきの用量反応・`binary` を含む ladder・直交切り分けの一般化については何も言わない** (事前登録 §3
「書けない主張」、§9)。

---

## 3. 限定 (この結果が言わないこと)

1. **判定が及ぶのは 1 contrast だけである。** 登録した `constant` 対 `symmetric-modulo`、μ = 2〜100 µs、48 スレッドの
   Silo / YCSB 3 workload。待ち方の効果一般や「待ち方と待ち量の直交切り分けを一般に閉じた」とは書かない (事前登録 §3・§8)。
2. **事前登録 §9 の 9 項目はいずれも本稿が閉じない** (§0.2)。うち 5 項目は D1678 が見送りと裁定し再訪条件 (査読で提示を
   要求されたとき) を持つ。残り 5 bullet (項目 3・4・6・7・8) は D1678 の列挙に無く、本稿はそれらに地位を与えない。
3. **機序を言わない。** `symmetric-modulo` が高い側に出る理由は本稿の対象外である (D1678)。事前登録 §3 のとおり
   「差の機序が脱同期だけである」とは書けない — 総待ち量 = 呼び出し回数 × μ も同時に動く (§2.6 の名目総待ち量列は cell
   ごとに違う)。**主張は指示値の平均に限定する** (D1097): μ は構成上の平均であり、実走行での待ち量の分布は測っていない
   (事前登録 §9 の項目 4・7)。D1092 に関しては、本 report に診断計装由来の値は無く (abort 回数・呼び出し回数は CCBench の
   計数、名目総待ち量は計算値)、本稿は機序判断を置かない。
4. **`binary` を測っていない。** 3 水準の ladder・ばらつきの用量反応について何も言わず、「`binary` の除外が事前登録された
   判断だった」とも書かない (事前登録 §8)。測ったのは 2 点である。
5. **判定下限 (床値) による退行判定を行っていない** (D1094)。§2.5 の参考幅は外部 floor 由来で、write-heavy / balanced は
   別環境の値である。本稿は D1639 で後に測られた Pegasus の between-run CV (rr5 / rr50 / rr95) を流用せず、それと本結果を
   比べない。
6. **3 workload の実行は別 job・別日・別 driver 版である** (§1.3)。balanced と read-heavy の host は異なる。write-heavy の実行
   host は成果物に無く、別 node だったとは書かない。判定は workload 内の block 対だけで組まれており、workload 間の絶対
   throughput は比べない。
7. **旧 2 系列は限定受理で集約に入った** (§1.4)。write-heavy (D1588) と balanced (D1636) は、report を出した driver の
   通常経路では受理されない束縛を持つ record を、系列限りの digest 集合へ exact に閉じて受理したものである。取り直して
   いない。報告後の裁定 (D1771 / D1834) による受理経路の改訂は本 report の bytes を変えない (絶対規律 7)。
8. **正しさの認証は trace 有効ビルドの別走行についてである** (§1.6)。`performance` 条件の 5 回は性能測定と同じ flag だが
   別 run であり、性能測定の run そのものを検査したのではない。`legacy` 条件の 1 回は小規模高競合条件である。性能 binary
   と認証 attempt の binary の SHA-256 一致は driver が要求し、判定不能 cell は 0 だった。**性能を認証していない。**
   `official_certification` は `false` で、**この性能値を根拠に variant を採用してはならない** (絶対規律 2)。
9. **検出力を主張しない。** 参考幅は検出力の保証ではない (事前登録 §6)。「検出力の範囲内で検出した」とは書かない。
10. **静的右 tail の 2 cohort と合成・比較しない。** `2026-09-16-b10-static-tail-not-observed.md` と
    `2026-09-19-b10-static-tail-cohort2.md` は別の事前登録・別の格子 (1000〜9999 µs)・別の driver・別の判定述語の事実で
    ある。A-2 / A-6 / B-7 / [T-1998] の certification・退行判定とも合成しない (絶対規律 7)。
11. **論文図は無い。** 待ち方 grid の判定を描いた凍結図は `docs/paper-story/figures/` に無い。fig8 / fig8b は右 tail の
    cohort、fig2b / fig2c は別系列の backoff sweep である。**それらを本判定の図として引かない。**
12. **当時の実行全体を独立に監査したとは言わず、report を再導出してもいない。** 本稿の起草時に行ったのは、report .md と
    provenance JSON・3 campaign の record と WAL・4 件の投入受領証と job 結果を現物で読み SHA-256 を実計算したこと
    (§4)、および 135 record の `median_tps` から対差 54 個・18 cell の効果と区間・36 cell の等価域との関係を同じ式で
    再計算して一致を確かめたこと (§2.3・§2.4) までである。これは転記の検算であって、当時のビルド・verify・失敗 attempt
    の履歴の独立監査ではない。record・WAL・受領証は repo 外にあり (§4.2)、tracked file ではない。
13. **`different` は protocol の出力であって、研究の成功・失敗の宣告ではない** (D12)。本稿はこの結果を B-10 という論文
    項目の閉鎖として扱わない。閉じたのは待ち方 grid の判定であり (D1678)、その再訪条件は「査読で要求されたとき」である。
14. **転移を言わない。** 測ったのは silo protocol、Pegasus 計算ノード 48 スレッド、YCSB 3 workload、CCBench pin
    `511c953`、この較正・事前登録の下だけである。他の workload・機体・pin・protocol へ転移するとは言わない。
15. **物理残差の 3 区分を混同しない** (§1.7)。開示した 18 cell の probe、登録した 12 cell とその値、v4 の束縛は別のもので
    あり、本稿は測り直していない。probe は 2026-08-27 の別 job (host `bnode142`。balanced / read-heavy の host とは異なり、write-heavy の host は未記録) の
    測定である。
16. **統計の意味を広げない。** 検定は対相対効果の和の絶対値を統計量とする両側 exact 符号反転 permutation (全 2^18 列挙)
    と 3 族 Holm、区間は 3 block の相対効果の平均に対する student-t (自由度 2) の paired-block 区間である。1 族 18 対は
    3 block × 6 μ であり、物理残差の 12 cell とは別のものである (事前登録 §6)。等価域との関係は区間の位置の分類名で
    あって等価性検定の結果ではない。中央値 throughput は各 cell 5 rep の中央値である。
17. **日付を混同しない。** 3 workload job は 2026-09-01〜09-05、report は 2026-09-05、記録と D1678 は 2026-09-07、本稿の
    起草は 2026-09-20 である。事前登録の発効版は 2026-08-29、erratum §10 の適用は 2026-09-07 (判定後) である。
18. **`records` の `settled` field は 3 件だけ `true`** (各 workload の `block-1` `none`)、残り 132 件は `null` である。
    本稿はこの field の意味を解釈しない (report .md はこの field を印字しない)。
19. **参照点 `adaptive` の値から CCBench 内蔵の適応 backoff の優劣を言わない。** 参照点は判定の族に入らず (§1.2)、
    本稿の対比は登録した 2 形の間だけである。

---

## 4. 一次資料

### 4.1 repo 内の一次資料 (tracked)

SHA-256 は本稿の起草時に作業ツリーの現物から実計算した。本稿自身の SHA-256 は書かない (F36)。

| 資料 | path | SHA-256 |
|---|---|---|
| report 成果物 (provenance JSON、判定・135 record・束縛を含む) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` | `a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca` |
| report 成果物 (人間可読の report) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_report_978195.nqsv-23409962b76b.md` | `e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768` |
| 事前登録 (発効版 v4、report が束縛した版) | commit `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` の `docs/b10-backoff-shape-preregistration.md` (git blob `ea910de32df83c1bb320cbe62344dc5fb3b94684`) | `f43997a7d2350a9bdcd53e34dbf9b4b0648c9c659dd6111d0adcd08d29d6bdb2` (blob 内容、35,820 bytes) |
| 事前登録 (作業ツリーの現行 v5、束縛の対象ではない) | `docs/b10-backoff-shape-preregistration.md` | `7918bc12e60b48de56e0e0c3526f1b166e4e1bab9258bf1bf87bda567bfe847b` (39,278 bytes) |
| report phase の記録 (判定の逐語、erratum の適用) | `output/insights/2026-09-05/t1905-b10-report/README.md` | `18ec79f65c9ed687699f8b53bc97e8f863b346df0476d27a7afe787b32748b65` |
| write-heavy 系列の投入記録 | `output/insights/2026-08-31_t1905-b10-formal-run/README.md` | `97ee119ef259a3b00eefc815a940b80944a621ab4ee1a329a5e4282be3b67eba` |
| balanced 45 cell の限定受理と試し打ち | `output/insights/2026-09-05/t1905-b10-trial-cell/README.md` | `d777fbae56c98500dbbaa40c1162d5e15ba97ba80a14de17672490ba7ad3dcb7` |
| read-heavy 45 cell の限定受理 (報告後、D1597 の形) | `output/insights/2026-09-07/t1905-b10-readheavy-admit/README.md` | `73780ea912bcaddc8f031edb5c89130bc1c7cc592e60a576bab42c1bfe25f672` |
| 記録 (worklog entry 1288) | `docs/archive/worklog-phase3-0907-1288.md` | (凍結 archive。SHA-256 は書かない) |
| 裁定 | `docs/decisions.md` の D1092 / D1094 / D1097 / D1480 / D1509 / D1588 / D1597 / D1605 / D1627 / D1631 / D1636 / D1678 / D1771 / D1834 / D2157 | (追記型台帳。SHA-256 は書かない) |

解析コード SHA-256 `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9` は、commit `2a338449b` の
`orchestrator/campaign/b10_backoff_shape_sweep.py` の blob 内容の SHA-256 と一致する (実測)。

### 4.2 権威 bytes (repo 外)

**これらは repo の tracked file ではない。本稿は下の file を現物で読み、SHA-256 を起草時に実計算した。**
root は `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/` である。

投入受領証と job 結果 (`submissions/<nonce>/submit-receipt.json`、`submissions/<nonce>/job-attempts/<request>/job-result.json`):

| 対象 | nonce | request | 受領証 SHA-256 | job 結果 SHA-256 |
|---|---|---|---|---|
| write-heavy | `4911e3361f48adc0c0ca1fb015660464` | `965564.nqsv` | `002f7eb55ff1658422cfe77b6000100dc112e14ceb0037be22b4ded54671fb5d` | `b747bb47fed94f07bf23f80bedd1e67cca3e6208ca186d0a7aed12830460333d` |
| balanced | `c42191d4f1e6ecdbd5b7eb7f3100df50` | `974207.nqsv` | `54748afd205895605a6005c1956e96a36c66ad1057a7bcd79d44cbc6782da75b` | `eaf8ade5d30f3770b6725882be1a66c17bff5cd1fb336026e746afc1cfd1efbe` |
| read-heavy | `4537eb096a8ded8119e0bc92944f3171` | `977647.nqsv` | `f055cf2dbc957b3cb9d21d5682b916cc691d2ecf8eb9229cb8ef9815a60e6ed0` | `11e1a4792c540f75b34996fd85d205f0ff5f5308c68bf0d3e0535d35aac91a1f` |
| report | `23409962b76be959bb523a0cd5a31bc1` | `978195.nqsv` | `93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4` | `d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b` |

report の受領証 SHA-256 は provenance JSON の `submission.receipt_sha256` と一致し、3 workload の受領証 SHA-256 は各
45 record の `submission_receipt_sha256` と一致する (実測)。

campaign ごとの durable authority (`official-output/campaigns/<campaign id>/` 配下):

| workload | `campaign.lock` SHA-256 | `runs/wal.jsonl` SHA-256 | block record (`runs/b10-backoff-shape-blocks/`、45 file) の内容 digest の meta digest |
|---|---|---|---|
| write-heavy | `0a32c22b8afedd6b5542d0ec1da6cba713e55d77fd83cc878d173e568ee91674` | `e2c457291128fc53b990757dd54ae4fe61a5881fc9b66c03995ddbf0c87afc16` | `6cb14801e858cedd955d983267436585d75c713be48d79b50b0076fd99845b71` |
| balanced | `087e46dfc825b4db6b1fba585e339f989ea94b8e68c14bbb9cb7088fa7ad86b9` | `ed78d48073047acd1543df886c11486260c4c8d08e780a07535553b2d33bec1d` | `8e5f0b48ba9e635e3d0e4e6c9c312c7436008dbe1a34f91a5763300920c37bad` |
| read-heavy | `5abdfe110ac418b9d98a541ce7bfc3b4aa8975a97fbd6e82b5570f76330180b7` | `00e4f9408c5b4167a98dbdbcd3837da694e94133c609f58b315d5356f3e259fe` | `27195442abce632ffae7a7241abd3cd8e765fe63fb590a62a37d4166049400c8` |

meta digest は各 record 封筒 (`schema_version` `b10-backoff-shape-block-envelope/v1`) の `record_sha256` 45 個を sorted
して改行で連結し末尾にも改行を付けた ascii の SHA-256 である (§1.4)。3 campaign とも、`campaign.lock` の SHA-256 は同
campaign の WAL の `commit` 15 行すべての `commit_verification_receipt.lock_identity_sha256` と一致する (実測)。

### 4.3 値の出所

| 掲載値 | 出所 |
|---|---|
| 事前登録の束縛 (commit・blob・spec・patch・formula・binding・解析コード)、`official_certification`、較正、pin | provenance JSON の top-level と `preregistration` |
| 格子・参照点・動作点・反復・block 実行順・判定手続き・等価域・曝露規則 | 同 `preregistration.spec` (`grid` / `blocks` / `execution` / `workloads` / `analysis`) |
| 3 campaign の campaign id、driver 版 (`analysis_commit`)、解析コード SHA-256、`binding_sha256` | 同 `performance_cell_completeness.source_campaigns[]` と `records[]` |
| 3 workload と report の request、投入・完了時刻、phase、queue、壁時計枠、job script SHA-256、`driver_rc` | repo 外の受領証と job 結果 (§4.2) |
| 実行 host | `records[].execution_host` (report .md の `host` 列と同値) |
| 性能 cell と検証 slot の完全性、tag 別件数、WAL の truncated / error | 同 `performance_cell_completeness` と `verification_slot_completeness` |
| `verify_done` の `certified` / `verdict` / `anomalies` / `workload.tag` の件数 | repo 外の 3 campaign の `runs/wal.jsonl` (§4.2) |
| `legacy` / `performance` の検査条件 | commit `2a338449b` の `orchestrator/campaign/pipeline.py` (`CorrectnessWorkload` の既定 flag と `performance_correctness_workload`) |
| 3 族の `status` / `outcome` / raw p / Holm p / 対差 | 同 `judgement.families[]` |
| 36 cell の `effect` / 区間 / `equivalence_relation` / `status` | 同 `judgement.cell_effects[]` |
| 参考幅 | 同 `external_floor_reference_widths` |
| 全 135 cell の中央値・CV・abort 率・abort 回数・呼び出し回数・毎秒呼び出し・名目総待ち量・認証・`unstable` | 同 `records[]` (report .md の表と同値) |
| 曝露 `met` / `indeterminate` | report .md の `exposure` 列 (本稿でも `backoff_call_count` ≥ 10,000 で再判定して一致) |
| 物理残差 12 cell | 同 `preregistration.physical_residual_values`、probe の identity は `spec.physical_residual.provenance` |
| 対差の順序、効果と区間、等価域との関係の検算、族統計量の符号 | `records[].median_tps` からの本稿起草時の再計算 (§2.3・§2.4) |
| 限定受理の形と meta digest | D1588 / D1597 / D1636、`output/insights/2026-09-07/t1905-b10-readheavy-admit/README.md`、record 封筒からの実計算 |

### 4.4 同じ結果についての既存の稿

**results 系列に本 report の稿は他に無い。** 本稿が最初である。同系列の B-10 の既存 2 稿は静的右 tail の cohort についての
ものであり、本稿とは別の結果である。

版の側では、`docs/paper-story/2026-09-20.md` の「最新スナップショット以後に確定したこと」と §8 の B-10 の項が、この判定の
要約 (3 族 Holm の p、方向、効果量の集計、完全性、`official_certification` `false`) を insight と D1678 を出所として持つ。
本稿の値はそれらと一致するが、**本稿の出所は版ではなく §4.1・§4.2 の一次資料である。本稿は版を改めない。** 版へ取り込む
かどうかは、次の版の契約が決める。
