## 所見 (重い順)

1. [blocker] D1192 の「同一の是正 3 択」は実測されておらず、むしろ両クラスで挙動が異なる

対象: brief `brief.md:37-44`

破れ:

- 「同一 cache entry」は同じ completion / manifest なので同意する。
- 「同一 descriptor」も同じ manifest envelope なので同意する。
- 「同一拒否述語」は、job 終了後に切り出した v1 入力を `_external_entry()` に通す純関数的な意味では同じである。しかし production lifetime では同じ赤ではない。クラス 1 は staging が `buildcache.py:2765` で削除された後の receipt 発行で落ちる一方、クラス 2 の `/scr/0_<jobid>` は `s8b_floor_campaign.py:4159-4162,4289-4302,4374-4393` の receipt 発行時にはまだ生きている。
- 「同一の是正 3 択」は `probe-d1192-conditions.out` に測定結果がなく、brief の推論だけで埋められている。

特に代替案の効き方が違う。

- base 絶対 path の identity 化はクラス 2では既に行われているが、クラス 1の staging root は identity 決定後に作られるため同じ形では適用できない。
- missing entry の cache miss 降格は、クラス 1では fresh build 自身が staging を消すので receipt の赤を直さない。クラス 2にはそもそも自然な cross-job hit がない。
- `insight-t1942-floor-gate.md:150-153` 自身も、absolute-base identity は cold build の赤を直さないと結論している。これは brief `:44` の「どちらにも同じ形で適用できる」と両立しない。

影響:

D1322 が要求した事前条件を 4/4 で満たしたとは記録できない。未充足のまま v3 root tag を追加すると、manifest SHA、binary admission receipt、portable built record の参照値と受理形が変わる一方、その統合根拠が成立しない。

是正案:

親実測では、両クラスについて各 3 案を production lifetime で照合する必要がある。最低限、fresh build から receipt までと、旧 root 消滅後の hit 相当を分け、entry 選択、live validator、receipt の各結果を記録すること。結果が上記どおり異なるなら、M1 を「未充足」に直して再裁定へ返す。

scope 内。D1322 が明示した先行照合そのものであり、新しい一般 gate の提案ではない。

2. [blocker] plan の形 Bは、identity を変更しても production では発火せず、追加 gate だけを持ち込む

対象: plan `s2-plan.md:72-135,302-309`

根拠:

`_v2_identity()` の全 field は `buildcache.py:1305-1366` にある。形 B適用後の cross-job 同一性は次のとおり。

| preimage field | job 間で同値になりうるか |
|---|---|
| `genome_canonical` | 同じ cell なら同値 |
| `ccbench_commit` | 同じ pin なら同値 |
| `trace` | 同じ build 種なら同値 |
| `src_token` | 内容由来で同値になりうる。brief M4 の実測とも一致 |
| `cc` | 同じ toolchain なら同値 |
| `cxx` | 同じ toolchain なら同値 |
| `toolchain_manifest_sha256` | 同じ実体なら同値 |
| `site` | 同じ site class なら同値 |
| `dependency_prefix` | 現行は不同。形 B後も `tree_sha256` が同値になるか未測定。install tree 内の絶対 prefix bytesや symlink targetまで同値である証拠がない |
| `admission` | 不同。これだけで hit は不可能 |
| `source_snapshot_sha256` | 同一 materialization なら同値 |
| `compiler_input_manifest_schema` | 同じ schema なら同値 |
| `compiler_input_policy` | 同じ descriptor path なら同値 |
| `fetchcontent_dependency_receipt` | 同じ dependencyなら同値になりうる |
| `fetchcontent_archive_sha256` | 同じ archiveなら同値 |
| `fetchcontent_transport_mode` | 同じ configurationなら同値 |
| `fetchcontent_population_policy` | 同じ post-oracle modeなら同値 |
| `fetchcontent_dependency_manifest_sha256` | 同じ dependency manifestなら同値 |

決定的なのは `admission` である。

- `buildcache.py:2251` が admission 全文を identity に入れる。
- `build_admission.py:362-363` は receipt 全文を返す。
- receipt は `build_admission.py:662-674` で `source` を含む。
- `source_digest.py:164-175` の `source` は絶対 `source_root` を含む。
- floor は `s1_direct_comparison.py:625-627` から `patchharness.checkout()` を使い、同関数は `patchharness.py:362-372` で毎回ランダムな使い捨て worktree を作る。

したがって同じ cell でも別投入では `admission.source.source_root` とその `receipt_sha256` が変わる。形 Bは `dependency_prefix` を変えても別 job の entry を選ばない。plan 自身も `:135,192-194,306` でこれを認めており、「採るべき分岐は形 B」だけが結論と矛盾している。

DW-G05 の影響は次のとおり。

- v3 schema / root tag / validator: manifest、manifest SHA、admission receiptとその参照が変わる。root-neutral な durable proofを作る効果は説明できる。
- runtime root の BuildResult 伝搬と receipt 配線: 無ければ v3 receiptが拒否され、built record、certified 選択、後続 report / ledger が作れない。must-fix と言える。
- dependency identity の相対化、tree digest、前後再検査: production hitを増やさず、cache entry digestとdirectory参照を変え、新しい拒否条件を増やすだけである。D1322 の must-fix とは言えない。

是正案:

本 waveでは形 A相当の manifest v3化と receipt-time runtime bindingだけを実装し、「移動した base への cross-job 再束縛が発火する」とは主張しないこと。形 Aでも receipt validator自体は動くが、originとcurrentが同じ job rootなので、changed-base保証としては「謳うだけで発火しない保証」に当たる。

admission の root-neutral projectionは別裁定が必要であり、本 planへ加えるのは scope 外。

3. [blocker] [T-2043] の現在の判定手続きでは「第 2 クラスが閉じた」証拠にならない

対象: brief `brief.md:134-136`、plan `s2-plan.md:186-194,302-309`

破れ:

plan の synthetic hit testは source/admissionを固定して初めて hitを作る。一方 `test_v3_distinct_source_roots_still_select_distinct_admission_identity` は、production条件では hitしないことを固定する試験である。両者を通しても、実 floor の別 job再束縛は一度も発火しない。

床値 jobを再投入して receipt発行まで通った場合に証明できるのは次だけである。

- 7件が `dependency-prefix` の根相対 entryとして記録された。
- 同じ jobで生きている current rootsに対する receipt-time検証が通った。
- class 2由来の赤がその投入では出なかった。

それだけでは、作成 job消滅後に別 jobのrootへ再束縛できることは証明しない。

影響:

「閉じた」と記録すると、実際には未発火の保証を根拠に T-2043、床値投入、certified reportの参照状態を進めることになる。

是正案:

判定を二つに分ける。

- 「現行 fresh floor経路の赤なし」: 実投入が receipt発行を通り、7件が根相対で、receiptやproofに旧 job絶対 pathが無いこと。
- 「cross-job再束縛の閉包」: job Aのentryを、Aのroots消滅後にjob Bが実際に選択し、Bのrootsでcache-hit validationとreceipt発行を通すこと。

後者は現行 admission identityでは成立不能なので、T-2043 は「cross-job再束縛は未発火、閉包とは判定しない」とするのが健全である。

scope 内。追加の admission設計は scope 外。

4. [major] production の build-to-receipt 配線を検出する testが無いまま planが閉じている

対象: plan `s2-plan.md:204-208,293-300`

根拠:

plan自身が `s8b_floor_campaign.py` の新 keyword伝搬を消す変異を killできないと認めている。この伝搬は単なる補助情報ではない。`s8b_binary_admission.py:231-238` のlive validatorへ current rootが届かなければ、v3 dependency entryはreceipt発行で拒否される。

影響:

配線欠落時は `s8b_floor_campaign.py:4427-4445` の built recordが作られず、certified集合、report、ledgerの全後続値が欠落する。明確なDW-G05 must-fixである。

是正案:

所有解除を待って直接 bridge testを追加するか、所有競合しない新しいtest moduleで `build_cells()` からissuerまでをspyすること。どちらもできないなら、テスト閉包未成立を残したまま完了扱いにしない。

scope 内。これは仮想リスク用gateではなく、新設するproduction配線の直接試験である。

5. [minor] brief の caller 数は誤りだが、M3 の結論自体は projected production closureでは支持される

対象: brief `brief.md:60-68`

破れ:

直接 callerは3箇所ではなく4箇所である。漏れは `s8b_compiler_input.py:1090-1096` のcollector自己検証。plan `:5-24` の4箇所列挙が正しい。

参照閉包の確認結果:

- collector自己検証: `s8b_compiler_input.py:1090-1096`
- cache hit: `buildcache.py:1694-1705`、入口は `buildcache.py:2467-2492`
- fresh build: `buildcache.py:2637-2646`
- receipt発行: `s8b_binary_admission.py:231-238`、production callerは `s8b_floor_campaign.py:4374-4393`
- oracleの間接経路は `s8b_oracle_driver.py:1196-1235` が `pipeline.buildcache.build_v2` を包み、`pipeline.py:1076-1086` が呼ぶが、live検証はbuild呼出し中である。
- `validate_portable_binary_record()` は `s8b_binary_admission.py:366-380` で構造正規化とdigest再計算だけを行い、live pathを再解決しない。
- projected campaign内に再exportや動的な別validator callerは見つからなかった。

他 configurationやprefix供給方法についても、explicit/ambient prefixはいずれも `buildcache.py:2379-2387` でidentityへ入る。仮に形 Bでそこを相対化しても admissionのランダムsource rootが残るため、結論は変わらない。

影響:

caller数の記録訂正以外に、certified集合、report、ledger、受理集合への影響はない。DW-G05上はnitであり、M3を覆すmust-fixではない。

是正案:

briefを「直接4箇所。うち1箇所はcollector自己検証」と訂正する。M3の根拠は単一completionからの一般化ではなく、このcall graphとadmission identityの構造証明へ置き換える。

scope 内。

## 同意した箇所 (短く)

- 現行 `dependency_prefix` がjobid入り絶対 pathのままpreimageへ入る点は正しい (`buildcache.py:1314,2379-2387,2431-2454`)。
- entry directory名がcanonical preimageのSHA-256である点も正しい (`buildcache.py:1371,2452-2454`)。
- jobidだけを変えれば別digestになるというprobeの結論は正しい。
- 同じcompletion / manifestなので「同一cache entry」「同一descriptor」は満たす。
- `dependency_prefix`だけをidentityから外しても、absolute `admission.source_root` がcross-job hitを阻むというM4とplanの指摘には同意する。
- v2の受理集合を変えずv3へ分ける方針はD1338と整合する。

## 総括

M3は、caller数の誤記を除けば現行production closureについて正しい。ただし根拠はjob 952631の1例ではなく、random worktreeを含むadmission identityと閉じたcall graphである。

一方、M1の「同一の是正3択」は実測されておらず、実際のlifetimeでは両クラスの赤と代替案の効き方が異なるため、D1322の先行条件を4/4で満たしたとは言えない。planの形 Bもadmission identityに阻まれて発火せず、identity/tree gateの追加は本題の成果物へ正の効果を持たない。

したがって現planのままでは実装段へ進めない。scope内で残せるのは、v3 root tag、runtime root伝搬、receipt検証という形 A相当の実装と、「cross-job再束縛は未発火でT-2043は閉じていない」という明示的な判定である。静的検査のみで、pytestは実行していない。