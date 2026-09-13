## 総括

**real：十進文字列の受理案は、float 変換後にゼロになる正の値まで受理集合を広げる。正値検査を残す局所修正が必要。**
**real：sized の実行障害は計測停止・依存 staging の 2 箇所だけではない。source binding と成果物 consumer にも pilot 専用分岐がある。**
30 対・3 組・対ブロック6本のスケジュール自体には、60 対固定による障害を見つけなかった。
提示 JSON の key／値に追加の不一致は見つからない。ただし、十進文字列対応・実ファイル配置・README pin 確定が前提である。
`final_estimate_eligible=true` と非認証 lane は両立する。正式性・昇格許可にはならない。
以下は静的読解と JSON／hash の照合結果。pytest、replay、`load_policy`、計測は実行していない。

## 所見

以下、`driver` は `orchestrator/campaign/paper_story_a1_paired.py`、`plan` は親指定の `codex-artifacts/a1-sizing-certificate/s2-plan.md` を指す。

### 1. real — 十進文字列対応で float の正値条件が落ちる

根拠：`plan:45–53`、`driver:1251–1260`、`driver:1477–1485`、`driver:4713–4721`。

提案は `_positive_decimal(value)` の正値性と、`float(value)` の有限性だけを確認する。`"1e-999"` は前者を満たすが、後者は有限な `0.0` になる。既存の `float(...) <= 0` に相当する拒否が消える。

数値変換だけを確認し、`Decimal("1e-999") > 0` と `float(Decimal("1e-999")) == 0.0` を確認した。validator の実走ではない。

**成果物影響：policy と証明書の該当値を一致させ、binding も更新した入力では、ゼロの k／sigma を出力する受理経路が新たにでき、k なら区間半幅がゼロになる。今回の候補値には該当しない。**

局所修正は、変換後にも `_finite_number(converted)` **かつ `converted > 0`** を要求すること。既存テスト案にこの負例を加える。

### 2. real — 本走の実行障害と source binding の不足は、段 2 の指摘より広い

根拠：

| 箇所 | sized での挙動 |
|---|---|
| `driver:7077–7079` | source contract の study／attempt 一致を無条件要求。sized は拒否 |
| `orchestrator/campaign/paper_story_a1_source.v1.json:3–4` | contract は pilot study、`attempt-0004` |
| `tools/pegasus/paper_story_a1_paired.sh:1362–1372` | sized では依存 source staging と `--third-party-source-root` 付与を省略 |
| `driver:7080–7093` | 上記停止だけ外しても、hydrate origin・staged root・依存準備を引き続き要求 |
| `driver:2194–2195` | source amendment の4ファイルを binding に加えるのは pilot のみ |
| 同 script `:74–81`、`:450–456`、`:984–991` | 非認証／terminal の source binding への追加も pilot のみ |
| `driver:4811`、`:5170–5181` | amendment binding がある場合だけ contract 照合と amended source admission 検査を行う |
| `driver:4954`、`:4973–4987` | amended source と通常 source で configure argv の受理形が違う |

`driver:2587–2590` と `:3360–3366` にも、pilot 専用の contract／hydrate 入力検査がある。sized を直接拒否する分岐ではないが、同じ実行準備を sized には要求していない。

**成果物影響：現案では sized 計測は完走不能。停止条件だけを外しても、source 参照集合と build 証拠の受理形が pilot と異なり、同じ amended build の成果物を受理できるとはいえない。**

本 wave を証明書・policy 凍結に限定する判断は可能。ただし、親へ返す実行面の項目を「2 箇所の限定解除」ではなく、上表の既存経路を揃える課題として記載する必要がある。

### 3. refuted — 30 対にするとスケジュール・受領証が60対固定で落ちる

根拠：

- `driver:1137–1149`：`pair_indices` は開始0・終端=`reps`。
- `driver:1762`：組数は `reps // 10`。
- `driver:1798–1821`：各組に逆順の対ブロックを1本ずつ生成。
- `driver:1908–1911`：receipt は生成済み plan のブロック数と `2 * reps` を要求。
- `driver:2011–2015`：各 arm の点数は `_expected_reps(...)`。
- `orchestrator/campaign/pipeline.py:2760–2765`：20以上の10の倍数を許し、組数を `perf.reps // 10` で導出。
- 同 `:2903–2913`：pair index も group とブロック位置から導出。
- `driver:5201–5209`、`:4643–4647`、`:4664–4672`：arm 長、対差、分散の分母も `reps` に追随。

30対なら **3組、対ブロック6本、armブロック12本、各先行3本、観測行60行**。3 bit の0／1が同数になる必要はなく、各組が両先行を1本ずつ含むことで釣り合う。

### 4. refuted — 提示 JSON に、提案修正後も拒否される余分な key がある

JSON を抽出して pilot policy と構造比較した。差分は `plan:402–419` に列挙された項目と一致した。

| 対象 | 実装との照合 |
|---|---|
| top-level | 16 keys：`authority`, `campaign_schema`, `ccbench_acceptance`, `execution`, `final_estimate_eligible`, `invalid_rules`, `pairing`, `preregistration`, `quality`, `rerun`, `scale`, `schema_version`, `sizing`, `sizing_inputs`, `study_id`, `workloads`。禁止される `arms`／`arm_order` はない（`driver:1395`） |
| workload | 各9 keys：`arms`, `df`, `k`, `name`, `pair_indices`, `planned_sigma_tps`, `reps`, `schedule_root_seed`, `ycsb_rratio`。腕・flags は期待値と一致（`:1437–1458`）。**sized には workload の exact key 集合検査はない**（`:1471–1485`） |
| `pair_indices` | `start_inclusive`／`stop_exclusive` の2 keys、値0／30で一致（`:1137–1149`） |
| `pairing` | `arm_block_reps`, `contrast`, `design`, `estimand`, `group_pairs`, `physical_orders`, `schedule_receipt_schema`, `seed` の8 keys。値も一致（`:1488–1538`） |
| `quality` | 6 fields と文字列が一致。ただし semantic validator は key 集合を exact 固定せず `.get` で検査（`:1554–1570`） |
| `rerun` | 3 keys、4理由の順序を含め dict 全体が一致（`:1573–1579`） |
| `scale` | `expected_verify_configs`, `extime_s`, `records`, `threads`, `ycsb_max_ope`, `ycsb_rmw`, `ycsb_zipf_skew` の7 keys。pilot と同値。v3 semantic validator に独立の scale 検査はない |
| `invalid_rules` | 16文字列の内容・順序が一致（`:1571`） |
| `ccbench_acceptance` | 6 keys、boundary の5項目・順序・pin・bool が一致（`:1629–1638`） |
| `sizing` | 分数、条件名、候補格子、pilot の60／12／6を保持し一致（`:1581–1626`） |
| `sizing_inputs` | 2 bindings、各 `path`／`sha256` の exact 集合と一致（`:1665–1679`） |

`validate_policy` の top-level exact 検査は、**新しい tracked sized JSON 自身**との比較であり、pilot の key 集合との比較ではない（`driver:1698–1707`）。`authority`・`scale` などもここで canonical の値に束縛される。

現在のコードにそのまま渡せば、文字列 `k`／sigma は `driver:1480–1483` で拒否される。README placeholder、未配置ファイル、未確定 pin も解決が必要であり、「全文が現在すでに load できる」という意味ではない。

候補証明書については canonical bytes と指定 hash が一致し、3 workload の n／df／k／sigma、D1452 の5登録値も案と一致した。

### 5. refuted — 文字列化により、統計 consumer 以外の算術が壊れる

policy の2 fieldsを直接読む箇所は以下で尽きる。

| 箇所 | 用途・判定 |
|---|---|
| `driver:1181–1197` | v2 validator。今回の変更対象外 |
| `driver:1370–1387` | 証明書との Decimal 比較。文字列対応済み |
| `driver:1480–1483` | v3 sized validator。提案の変更対象 |
| `driver:4713–4721` | k の算術、sigma の比較、数値としての結果出力。float 変換済み |

汎用比較の `driver:1704–1707` は文字列同士の比較になる。schedule receipt は seed・配置・TPS を扱い、両 fields を使用しない（`:1835–1854`、`pipeline.py:2972–2987`）。

生成・検証ツールの同名 field は証明書側の値であり、sized policy を読む経路ではない。

したがって、段 2 の「計算側は変更不要」という結論は支持できる。ただし所見1の変換後正値検査は必要。

### 6. refuted — sized は非認証 lane に入らない／`final_estimate_eligible=true` と衝突する

根拠：`ident.py:48–80`、`wal.py:120–162`。

両層とも sized の identity を含み、独立に `formal is False`、`promotion_prohibited is True`、mode、trial 一致を要求する。`_is_a1_balanced5_non_certifying_config` は sized にも当たる。

結果として：

- 非認証 WAL append／replay を使う（`loop.py:539–547`、`:571–574`）。
- 中断は balanced5 の terminal invalid 回復へ進む（`ident.py:493–499`、`:524–530`、`wal.py:2494–2500`）。
- registry projection は `certifying=False`（`trial_registry.py:3998–4005`）。
- `final_estimate_eligible=true` は統計の pilot 専用早期 return を外す（`driver:4707–4721`）。

親 brief の `authority.formal=true` 案は、policy の bool だけで正式 lane を選べる実装ではない。campaign marker は `driver:2234–2241`、`:2282–2288` で別に固定される。段 2 の非正式案を支持する。

### 7. real〔nit〕／refuted — D1452 の挿入は拒否理由の優先順位を変えるが、既存の不正入力を受理しない

根拠：`plan:64–93`、`driver:1295–1387`。

- **refuted：hash、canonical bytes、pilot input binding の既存拒否を飛ばす。** これらは挿入位置より前で、不変。
- **real〔nit〕：複合破損時の拒否理由は変わる。** 例えば登録値欠落と workload 欠落が併存すると、従来の `certificate workload set differs` より新しい registered-policy エラーが先に発生する。
- **refuted：その結果、元々拒否された証明書が通る。** 新チェック通過後には、既存 workload／n／df／k／sigma 検査がすべて残る。

この理由順序だけによる成果物の値・受理集合・参照の変化はないため nit とする。既存理由の優先順位まで維持するなら、新照合を既存 workload 検査の後へ置けば足りる。

### 8. refuted — 段 2 が変更不要とした既存テストに、追加の必然的な赤がある

静的に確認した固定面：

| テスト位置 | 固定する対象 | 今回の影響 |
|---|---|---|
| `test_paper_story_a1_paired.py:856–900`、`:941–950` | v2 policy・hash | 変更なし |
| `:903–938` | legacy literal goldens、headline dir の exact file 集合 | 新規 sized dir は対象外 |
| `:955–966` | pilot JSON の duplicate-key 拒否 | 変更なし |
| `:969–1000`、`:1096–1131` | pilot の60対・6組・seed | pilot を保持すれば変更なし |
| `:1248–1320` | pilot observation の exact keys、collector 呼出し | 変更なし |
| `:1352–1397` | pilot sizing／CCBench／preregistration literals | 変更なし |
| `:1431–1448` | historical bytes、v2 README binding | 変更なし |
| `:2014–2052` | 統計・arm validator の AST 制約 | 提案変更箇所は対象外 |
| `:3333–3366` | sidecar source file 集合 | 今回 source 集合を変えない案なら影響なし |

`test_v3_loader_accepts_future_sized_policy_shape`（`:1012–1093`）は、段 2 の予測どおり未修正なら赤になる。certificate fixture に `policy` がなく、実 pin 導入後の tmp repo に README もない。提案された fixture／pin の修正は必要である。

## 60/12/6 に固定されている箇所の一覧 (攻撃点 1 への回答)

| file:line | 固定内容 | 本 wave で直す要否 |
|---|---|---|
| `driver:1472–1476` | pilot workload の60対 | 不要。pilot 分岐限定 |
| `driver:1596–1611` | pilot sigma 式の60／12、pilot 設計60／12／各先行6 | **変更しない**。本走の rep 数ではなく sizing 入力 |
| `paper_story_a1_paired.v3-pilot.json:131–148` | pilot sizing の60／12／6 | 変更しない |
| 同 `:218–225`、`:257–264`、`:296–303` | 各 workload の df=59、stop=60、reps=60 | 変更しない。新 sized JSON 側を30にする |
| pilot preregistration `README.md:46–50`、`:87–88`、`:110–118` | pilot 配置・入力統計の60／12／6 | 変更しない。新 README の本走配置を30／6／3とする |
| `tools/size_paper_story_a1_balanced.py:64–67`、`:460–490`、`:509` | pilot 点数、ブロック数、各先行6、6組 | 変更不要・変更提案なし |
| `tools/verify_paper_story_a1_balanced_sizing.py:64–65`、`:358–374`、`:392–434` | 同じ入力条件を独立に検査。120行、index上限59／5／11も固定 | 変更不要・変更提案なし |
| `trial_registry.py:762`、`:5802`、`:5855` | 6 trials／reports | A-1 の対数ではない。A-1 専用 projection は `:3947–4007` の3 workload／3 campaign。変更不要 |
| 上記所見8の pilot テスト | 60対／6組／12ブロック | pilot 回帰用として保持 |

driver の schedule／receipt／成果物統計 consumer、pipeline、loop、wal、ident、job script に、**sized を60対・対ブロック12本・各先行6本に固定する検査は見つからなかった**。script の60秒や registry の別用途の6件は対数制約ではない。

`driver:2091–2133` の sizing-pilot 出力は pilot 専用だが、materializer 側も `driver:8514–8521` で pilot に限定して呼ぶため、sized の成果物生成をこの入口で拒否する経路ではない。

## 親裁定へ返す項目

1. **本 wave 内の局所修正**：十進文字列受理で、float 変換後の正値検査を保持する。underflow の負例を追加する。
2. **本 wave の完了表現**：「証明書・policy の凍結／loader 受入」まで。本走実行可能とは書かない。
3. **後続の実行面**：source contract、hydrate 入力、staging、source binding の各生成箇所、amended build consumer を一式で扱う。7079行の拒否だけを外す案は不十分。
4. **正式測定の認可**：`final_estimate_eligible=true` を投入認可・正式昇格と解釈しない。[T-1505] の人間手番を維持する。