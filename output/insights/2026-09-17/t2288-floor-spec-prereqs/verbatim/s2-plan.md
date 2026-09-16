## 前提の検査

**P1 の採用値と P2 の 3 セル案は採用可能。ただし P3 は修正が必要で、「残前提は A-5 のみ」は範囲を限定して記録する。** 以下は親の裁定・編集用の起草であり、この段ではファイルを変更していない。

以下、`事前登録` は `docs/phase3-b4-reflux-ablation-preregistration.md`、`registered/` は `output/env/pegasus/calibration/registered/` を指す。

独立確認した結果は次のとおり。

| 確認対象 | 結果 |
|---|---|
| registered 較正 | 8 件すべて tracked、SHA-256 は親の一覧と一致 |
| admission | 実際に `load_verified_calibration(env_tag="pegasus", clocks_per_us=2100, attestation_mode="required", …)` を呼び、8/8 ADMITTED |
| silo の内訳 | rr5 × 1、rr50 × 2、rr95 × 1。rr50 の 2 件は genome 不在で、対応 job の binary は silo |
| g1 の method | `proc-cpuinfo` |
| 他 7 件の method | `proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1` |
| silo 4 job の argv | 4 件とも `--extime` 上書きなし |
| 実施していないもの | pytest、spec loader、driver、issuer、build、較正・床値の測定 |

重要な境界は以下。

- `calibration_verify.py:130` が現行 policy と比較するのは **tolerance**。method 一致検査ではない。
- `floor_pair_driver.py:1155` 以降の binder は admission、accepted、records、env、threads、clocks、workload を確認するが、較正 protocol や `extime/reps/ycsb_max_ope` の意味的一致は検査しない。
- §5 の表 (`事前登録:154`) に contention の具体列はない。3 セルは既存列の転記ではなく、今回承認する具体化である。
- binary 調達は済んでいるが、消費 checkout からの配置は別件 T-2697 に残る (`docs/archive/worklog-phase3-0916-1544.md:425`, `:719`)。

## A-3 の起草

記録先は新規 `docs/spool/decisions/2026-09-17-dev-wave-t2288-floor-spec-prereqs-1.md`。共通 frontmatter は以下とする。

```yaml
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2288-floor-spec-prereqs
seq: 1
---
```

D 見出し案: `{{D:floor-perf-config}}. B-4 床値の測定設定を較正構成と明示承認で確定する`

**決定:** D1641 決定 3 の委任と D1696 の人手確認責任に基づき、workload 別 3 spec の各測定を `extime=3`、`reps=5`、`ycsb_max_ope=10` とする。`records/threads/workload` は採用較正から取る。ここで承認するのは凍結 spec に書く設定であり、§5 の設定 artifact 欄を埋めたとは扱わない。

**理由:**

| 項目 | 根拠と承認の位置づけ |
|---|---|
| `extime=3` | `orchestrator/calibrator/cli.py:150` の既定値。下記 4 job の argv に上書きがない。`runner.py:1119` の bench flags は渡された extime を使う。較正取得構成から復元する値であり、較正 JSON の直接出力ではない。 |
| `ycsb_max_ope=10` | `runner.py:1119` の固定 flags に含まれず、当該 argv の workload 3 key にもない。`external/ccbench/include/ycsb.hh:22` の既定 10 による構成を採る。runner 一般がこの flag を渡せないという意味ではない。 |
| `reps=5` | **calibrator 出力からは導けないため、今回の D で明示承認する。** `pipeline.py:189` の既定、`事前登録:1227` の「1 測定 = 5 反復 × 3 秒」という名目構成と整合させる。`floor_pair_driver.py:61` の `median/v1` に対して奇数反復を採る。 |

取得構成の証拠は次の各 `calibrate-argv.json` と親の `probe-calibrate-argv.txt`。

```text
output/env/pegasus/calibration/job-staging/0:867876.nqsv/calibrate-argv.json
output/env/pegasus/calibration/job-staging/0:892707.nqsv/calibrate-argv.json
output/env/pegasus/calibration/job-staging/0:995805.nqsv/calibrate-argv.json
output/env/pegasus/calibration/job-staging/0:478.nqsv/calibrate-argv.json
```

sweep 3 / noise 10 は `cli.py:151` の別用途の反復設定である。とくに sweep は各 records 点で `measure_fn(..., reps=reps)` を呼ぶ (`sweep.py:101`)。したがって「どちらも 1 測定の反復数ではない」とは書かず、**床値 driver の各候補・参照測定に採る反復数を一意に指定しない**と書く。

D1640 の 5 反復 (`docs/decisions.md:50294`) と qualification shape (`pipeline.py:1697`) は別用途の先例であり、B-4 の承認根拠そのものにはしない。`p3_s4_loop.py:1565` の配線規模設定も流用しない。

**却下した選択肢:**

- sweep の 3 または noise の 10 を自動転記する。用途が異なり、B-4 の反復数を導けない。
- `reps=5` を「較正済みの出力値」と記す。artifact にその field はない。
- CV や throughput を比較して reps を調整する。結果依存の設計変更になる。
- 完全な設定 producer を新設する。D1536 に従い、今回は既存取得構成と認可済み人手承認で用意する。

なお、現行 source と argv による復元を、過去の実行 source bytes まで完全に検証したこととは区別する。

## A-4 の起草

同じ decisions fragment に置く。

D 見出し案: `{{D:floor-contention-cells}}. B-4 床値の対象を workload 別の 3 セルに具体化する`

**決定:** D1641 決定 3 と D1936 項 7 に基づき、対象 driver `base (silo-backoff-magnitude)` に対して、次の 3 セルを閉じた集合として承認する。workload ごとに 1 spec・1 cell とし、文字列 `"0"` を `"false"` へ置換しない。

| workload | records | threads | workload 3 key の逐語 | extime | reps | ycsb_max_ope |
|---|---:|---:|---|---:|---:|---:|
| read-heavy / rr95 | 1000000 | 48 | `{"ycsb_rmw":"0","ycsb_rratio":"95","ycsb_zipf_skew":"0.9"}` | 3 | 5 | 10 |
| balanced / rr50 | 1000000 | 48 | `{"ycsb_rmw":"0","ycsb_rratio":"50","ycsb_zipf_skew":"0.9"}` | 3 | 5 | 10 |
| write-heavy / rr5 | 2000000 | 48 | `{"ycsb_rmw":"0","ycsb_rratio":"5","ycsb_zipf_skew":"0.9"}` | 3 | 5 | 10 |

束縛する較正は次のとおり。

```text
rr95:
path = output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json
sha256 = 5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc

rr50:
path = output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json
sha256 = 94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9

rr5:
path = output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json
sha256 = 2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067
```

**理由:** §5 表 (`事前登録:154`) は対象 driver を指定するが、contention セルを列挙していない。§5.1 の floor 追補 (`:281`) も 3 spec の集約規則であり、具体的 skew/thread 列ではない。

そこで今回の導出規則を、**対象 silo・Pegasus・3 workload について、固定した registered 集合に共通して存在する `threads/skew/rmw` の較正条件を採り、records は C 群で選んだ較正の `saturation.records` をそのまま採る**と明記する。利用可能性から実験対象が自動決定したとは書かず、この範囲への限定を D で承認する。

根拠は D15、D1854、および `floor_pair_driver.py:1181` の exact 一致要求。rr95 の records は当該 JSON `:1617`、rr5 は `:1618`、workload はそれぞれ `:1691`、`:1692` にある。rr50 は上記 artifact と SHA で束縛する。

**却下した選択肢:**

- §5 に具体列が既記載だったとする。
- rr50 の較正を rr95/rr5 に流用する。
- 未較正の skew/thread セルを追加する。
- 観測した floor の大小でセルを間引く。
- この集合を、他の contention 条件を覆う床値と解釈する。

## C 群の起草

同じ decisions fragment に置く。

D 見出し案: `{{D:floor-calibration-selection}}. B-4 床値の較正を取得由来と最早順で人手選択する`

**決定:** 以下は D2044 項 11 に対する新しい人手選択規則である。D1696 に従い、loader、binder、gate、schema は変更しない。候補集合は起点 commit `20a92f6a6` の registered tracked record に固定し、結果に応じて探索範囲を広げない。

| 条件 | 根拠 | 値依存でないことの意味 |
|---|---|---|
| c1: 固定 checkout の registered tracked record | binder の tracked bytes 束縛 `floor_pair_driver.py:1131`。registered 限定自体は今回の人手規則 | 保存場所と取得集合で決め、throughput/CV で探索対象を変えない |
| c2: required admission 成功かつ accepted | `calibration_verify.py:116`、`floor_pair_driver.py:1170` | 既存品質条件を維持する。accepted 同士を品質値の大小で順位付けしない |
| c3: 対象 protocol と一致 | 対象 driver は `事前登録:158`。genome 解釈は `layer3_report.py:477` | protocol の出所で分類し、性能値で分類しない |
| c4: env/clocks/threads/workload の一致 | D15、D1854、`floor_pair_driver.py:1181` | 測定条件による一致。records は選択後に採用較正から転記し、望む records で候補を先に選ばない |
| c5: 取得 method が今回固定する method と一致し、既知の自己不整合 identity でない | method の実定義は `env_attestation.py:35`。除外 identity は D1537、`layer3_report.py:79` | 現行取得方式と既裁定の identity を用いる。CV、miss rate、floor の大小を新たな除外条件にしない |

c3 の genome 不在例外は、今回確認した歴史的 2 record の**完全 SHA**に限定する。

```text
753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49
94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9
```

この 2 件だけ、対応する取得 receipt と job-staging argv の silo binary を根拠にする。将来の genome 不在 record へ `--binary` fallback を一般化しない。D1538 の限定を人手規則でも保つ。

c5 の固定 method は次の文字列とする。

```text
proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1
```

これは **既存 verifier の method gate ではない**。また D1537 は層 3 の既裁定であり、その identity を B-4 の人手採用にも使うことを今回明示する。

**採用順序:** 適格 record を `acquisition_receipt.qsub.submit_epoch` の昇順で選ぶ。同 epoch は、取得前に確定する qsub の `(project, queue, request_id)` の逐語辞書順で決める。同一取得 identity に異なる内容がある場合、または順序根拠が欠ける場合は、恣意的に読み飛ばさず人手確認へ戻す。SHA は内容束縛と重複確認に使い、順位には使わない。

D1311 は「最早の適格」の設計上の先例であり、較正に直接適用済みの裁定とは書かない。

適用結果:

| record | c1/c2 | c3/c4 | c5 | 結果 |
|---|---|---|---|---|
| rr50 g1 `753f535a` | 通過 | 歴史的 silo、条件一致 | method 不一致かつ既知除外 identity | 不採用 |
| rr50 g2 `94a4b79f` | 通過 | 歴史的 silo、条件一致 | 通過 | 採用 |
| rr95 `5c836a22` | 通過 | genome=silo、条件一致 | 通過 | 採用 |
| rr5 `2b7ba072` | 通過 | genome=silo、条件一致 | 通過 | 採用 |
| mocc/tictoc 4 件 | 通過 | c3 不一致 | 採否に不要 | 不採用 |

**却下した選択肢:** 最新採用、最小 CV 採用、望む records による選択、genome 不在の無限定 fallback、内容 SHA による同時刻順位付け。

**時系列の留保:** 親資料には既に較正の数値結果が含まれ、本段も閲覧した。「較正結果を一切見る前に規則を定めた」とは記録できない。将来の B-4 床値結果の前に固定する規則として起草し、D2044 の「結果を見る前に」と既知較正への適用の関係は、親の段 4 で明示的に判定する。値非依存な式であることだけで、過去の閲覧時系列を解消したとは扱わない。

## T-2465 の追記案

`事前登録:1155` の「ユーザー裁定へ返してある。」直後に、次の 1 文を追加する。

> **追記 (2026-09-17、[T-2465])。** この食い違いは D1887 と D1936 末尾により決着しており、担当者の指名と採用証拠の受理は D1641 決定 1・2、対象集合と統計関数は同決定 3 の既裁定を §11.3 へ追記反映するものとする。

`事前登録:1297` の直後、次の bullet の前に、2 space インデントで以下を追加する。

> **追記 (2026-09-17、[T-2465]、D1887・D1936)。** 上記の「残り」のうち、担当者の指名、対象集合、統計関数、採用証拠の受理は、現在もユーザー手番として未決なのではない。D1641 決定 1 により、測定実行者・証拠確認者・§5 記入担当者はいずれも `thawk105` 名義で、操作は AI 委任とし兼務を許す。証拠確認者は独立検査者ではなく、凍結どおりの測定を確認する責任者である。同決定 2 により、成果物の採用裁定は測定後に委任下の AI が行い、D として記録する。対象集合と統計関数は同決定 3 に記載済みであり、D1936 末尾が追加授権ではなく追記反映と確定した。対象は凍結セル集合 × 2 時間窓の全部、統計は標本最大値を用いる分布自由の片側許容限界であり、workload 別 3 spec の結果を保守側の最大として集約する (D1936 項 7、§5.1 の追補)。標本数は D1695 の 1 campaign・1 セルあたり n = 62 を用い、59 を予定標本数として復活させない。専用 driver の変更単位も未決ではなく、D1641 決定 4 の別実装 wave という決定を、D1453・D1694 に従い既存 driver の適合として読む。以上は既裁定の反映であり、具体的な凍結入力の充足、§5.1 の解除条件、§6 の前提条件、測定後の採用裁定を代替せず、測定開始・§5 記入・本書の発効を新たに許可しない。

「n=62 なら全 stratum に 59 件残る」とは追記しない (`事前登録:1216`)。

なお指定アンカーは、現物では **第 2 bullet に属する追記末尾**である。「第 1 bullet」という番号ではなく、`:1297` の逐語アンカーで編集する。

## worklog fragment 案

新規 `docs/spool/worklog/2026-09-17-dev-wave-t2288-floor-spec-prereqs-2.md` とする。`ledger: worklog`、`seq: 2`、title は「B-4 床値 spec の設定・セル集合・較正選択を記録し、事前登録の既裁定反映を訂正する」。

親は `docs/spool/worklog/README.md:5` の H2 2 節と、同 README の action 見出し文法に組み立てる。以下はその payload 案。

**本文案:**

> A-3 の設定承認を {{D:floor-perf-config}}、A-4 の具体セル集合を {{D:floor-contention-cells}}、C 群の人手選択規則を {{D:floor-calibration-selection}} に記録した。較正結果の既知性、method 条件の新規性、registered 限定の射程を開示した。事前登録の訂正は D1887・D1936 による既裁定反映であり、新規授権ではない。受入結果と親裁定の採否は実施後の事実を記す。

**T-2288 の `更新` 本文案:**

> - [T-2288] **P1・本 wave 対象の残前提は A-5 のみ**: A-3 の `extime=3/reps=5/ycsb_max_ope=10`、A-4 の silo・t48・skew 0.9・rmw 0 における rr95/rr50/rr5 の 3 セル、および C 群の適格条件・最早順を記録した ({{D:floor-perf-config}}、{{D:floor-contention-cells}}、{{D:floor-calibration-selection}})。rr5 の accepted 較正は取得済みで、B 群も充足している。残る A-5 は窓日時・campaign 識別子・seed・出力名・実行設定の確定である。ただし消費 checkout から binary を解決する配置は別件 [T-2697] に残り、本更新で凍結可能性を保証しない。workload 別 3 spec の作成・検証・commit、床値実測、集約、採用裁定、§5 floor 欄記入は未実施。

末尾に親取得の完全な `base:` を付ける。`f0a10547…` の省略形を実 fragment に書かない。

**T-2465 の `完了` 本文案:**

> - [T-2465] D1641 決定 1〜3、D1695、D1887、D1936 を §11.3 の追記訂正へ反映し、§11.1 の裁定待ち記述にも決着を追記した。driver の変更単位は D1641 決定 4 と D1453・D1694 に従って記録した。既存文と §5 の値セルを保持し、受入検査を完了した。

末尾に `remaining: none` と親取得の完全な `base:` を置く。受入完了前にこの完了文を確定しない。

## A-5 裁定パッケージ案

**値は起草しない。** 親が返すパッケージには、次の未確定 field と既決の制約を載せる。

| 必要事項 | 決める内容・確認事項 |
|---|---|
| 2 窓の `not_before/not_after` | UTC の非空半開区間、重複なし。24 時間以上の分離を人手で確認 |
| 各窓の `campaign_id` | spec 内で重複しない識別子、3 spec 間の対応 |
| `seed_hex` | 64 桁 lowercase hex。結果を見る前に固定 |
| `artifact_relpath` × 2 | 各窓の create-only 出力先 |
| `summary_relpath` | spec の create-only summary 出力先 |
| 実行設定 | site/env/clocks、配置済み binary、実行 command、予定標本と pair の対応 |

出力名 3 個は **1 spec あたり**であり、3 spec の concrete path と集約出力との関係も確認する。今回値は付けない。

構文根拠は `floor_pair_driver.py:869`、`:929`、`:1033`。標本数と分離は D1695・D1974 による人手責任である。

決定主体については §11.1 の逐語を併記する。

- `事前登録:1122`: 「AI が起草した候補値を無裁定の既定値として凍結へ入れない」
- `:1133`: 「標本数・campaign 数・時間窓の分離 | ユーザー」
- `:1136`: 「成果物の書式と命名 | ユーザー」
- `:1152`: 「上表の決定主体欄のうち承認・採用の主体は、この委任に従って読む」

担当者、測定認可、設定承認、成果物採用を再裁定しない。未確定の具体値、特に表に個別記載のない seed を既定値として補わない。AI は必要 field、構文、制約、確認手順を整理できるが、本段では日時・識別子・seed・出力名の候補そのものを書かない。

D1812 (b) の B-4 開始時刻の扱いを、floor spec の必須窓日時を省略できる根拠にはしない。

## 受入と検査の順序

1. 親裁定を先に記録し、3 D の fragment、事前登録 2 箇所、worklog、insight を編集する。§5 値セルと実装面の差分ゼロを確認する。
2. `python3 tools/check_docs.py`。
3. `python3 tools/spool_fold.py --dry-run --show-diff`。base digest、placeholder、採番後本文を確認する。実 fold はしない。
4. login node から `tools/run_tests.py` を通して、以下の 4 node を焦点走する。実行場所は runner の判断に従う。

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_admission_record.py::test_section5_source_cell_examples_and_expectation_bindings \
  orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_resolver_exact_sentinel_is_the_only_absence \
  orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_resolver_returns_exact_fraction_from_valid_pin \
  orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_aggregate_public_issue_load_and_preregistration_pin
```

これらは実在する §5 consumer の検査だが、fixture を用いる。**4 本の成功だけで編集した実文書の無影響を証明したとは言わない。** 実文書の §5 表の byte 不変確認と、`test_p3_b4_analysis_prereg_consumer.py::test_current_document_contract_literals_match_implementation` による凍結分析節の確認を併用する。

5. 親の受入全走を行い、実結果を insight/worklog に記録する。必要な `check_codex_agents.py`、commit 後の provenance 監査も親側で行う。未実施検査を緑と記録しない。

## 親 brief への反証

| 対象 | 訂正 |
|---|---|
| P1「reps は分散だけを決める」 | 過剰一般化。反復数は実行量、時間的標本化、中央値の標本分布にも影響する。`runner.py:1155` の反復実行を根拠に、bench の 1 回あたり flags を変えない量、と限定する。 |
| P1「sweep 3 / noise 10 はどちらも 1 測定の反復数ではない」 | sweep は `sweep.py:101` で 1 点の測定に reps を渡す。B-4 の測定単位を一意に定めない、と訂正する。 |
| P2「§5 に列挙するセル」 | §5 に具体列はない (`事前登録:154`)。今回の承認による具体化として記録する。 |
| P3「現行 policy と method 一致」 | `effective_clock_policy.py:6` は tolerance のみ。method 定義は `env_attestation.py:38`。人手選択条件の新設として明記する。 |
| P3 の genome 不在 fallback | D1538 の歴史的内容 hash 限定を伴わせる。`layer3_report.py:493` の fallback だけを一般化の根拠にしない。 |
| P3 の同 epoch SHA 昇順 | SHA は測定値を含む内容から決まるため、厳密な値非依存順位とは言えない。取得前 identity による順序へ置換する。 |
| P3 の「結果を見る前」 | 較正の数値は既知。値非依存規則と閲覧時系列を区別し、段 4 で適用範囲を裁定する。 |
| P4 の第 1 bullet | 指定逐語は現物の第 2 bullet に属する (`事前登録:1292`)。追記位置は `:1297` 直後。 |
| P5 | 妥当。3 D は spool、本文は既採番 D のみ、§11.2 へ設定値を再掲しない。 |
| 「残前提 A-5 のみ」 | 本 wave の前提整理に限る。T-2697 の配置依存は残す (`worklog-phase3-0916-1544.md:431`)。 |
| 新事実「導出は argv 等から行うしかない」 | extime/max_ope の構成復元には当たるが、reps=5 はそこから導けない。明示承認を別に置く。 |

8 件 ADMITTED、g1 method、4 job の extime 上書きなし、g1/g2 の pin 対応 (`env_contract.py:252`) は再現できた。protocol を較正 binder が照合しないという指摘も正しい。ただし、それだけで spec 全体の受理を実測したことにはならない。

## 総括

A-3/A-4 と T-2465 は上記案で起草できる。C 群は method 条件、歴史的例外、同時刻順序、既知結果との時系列を明記して親裁定へ渡す。

「A-5 のみ」は本 wave の残前提に限定し、T-2697 と spec 凍結・床値実測・§5 記入を残す。書き込み・pytest は未実施、較正 admission は 8/8 を独立再現した。