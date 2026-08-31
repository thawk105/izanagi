## 親の実測の再測結果

1. **実測1: 支持。ただし成立範囲と行番号を訂正。**

   - 列挙は `s8b_holdout_freeze.py:1821` の `tuple(os.listdir(namespace_fd))`。brief の `:1792` は誤り。
   - run directory が消えていれば不可視であるだけでなく、directory が残っていても `result.json` が消えていれば `:1842-1847` で読み飛ばされる。
   - 列挙後に追加された earlier run も、その呼出しでは不可視。反対に検査前に再配置すれば再び可視になる。
   - 選択 helper の production 呼出しは candidate 側 `:2053` と current launch 側 `s8b_ratified_freeze.py:3305` の2件だけ。別名束縛・動的参照を含む別 production 入口は見つからない。
   - 復元・履歴再構成が0件なのは、この floor selection authority の範囲。Git一般の復元や任意の再配置まで存在しない、という一般化は過大。

2. **実測2: 支持。ただし「g2は黙って非検査」は静的 loader に限定すべき。**

   - 投影 equality は `s8b_ratified_freeze.py:1056-1085` の `generation_number == 1` 枝だけ。
   - 静的 loader は合成 g2 を受理できることが `test_s8b_ratified_verify.py:1266-1273` にも固定されており、g2 の floor/source 投影は検査しない。
   - 一方、current と historical の full validation は共通 core `:3073` を通り、`:3107-3110` で g2 を artifact I/O 前に拒否する。したがって全経路について「黙って非検査」と書くのは誤り。

3. **実測3: 元の主張を反証、brief末尾の訂正を支持。**

   - `:3305` の呼出しに局所 generation 条件がない、という構文上の観測だけは正しい。
   - 到達性では `:3107-3110` が必ず先行するため、公開 current launch で g2 に g1 選択規則が伝播する経路はない。
   - `launch_validate` と `reverify_published_freeze` はともに同じ gate を通る。ただし選択 identity は `result_type is LaunchValidatedFreeze` の current 分岐 `:3303` だけで、historical reverify には課さない。
   - helper `_assert_floor_selection_identity` 自身は generation-neutral。任意 Python による直接呼出しは公開保証外である。

4. **実測4: 交差ゼロは支持、t2027の件数は訂正。**

   - 全 local worktree の未commit差分、全branchおよびdetached worktreeの `main...HEAD` を、予定 fragment・両実装ファイルに限定して再走査し、交差は0件。
   - ただし t2027 branch の差分は4ファイルではなく8ファイル。production 4件に加え対応test 4件がある。
   - 8件は `buildcache.py`、`s8b_binary_admission.py`、`s8b_compiler_input.py`、`s8b_floor_campaign.py` と各対応test。今回の予定fragment・両freeze実装とは交差しない。

## 所見

### 1. docs-onlyの結論は正しいが、P1-1の理由は誤っている

- **対象:** (P1-1)
- **何が誤りか:** 「コード変更は成果物の値を変えない」という一般化。`s8b_holdout_freeze.py:2062-2064,2077` は同ファイルのblob hashをfuture candidateの `generator.sha256` に入れるため、このファイルの変更は成果物値を変えうる。
- **放置時の影響:** 不要な実装変更を入れるとfuture candidateの値と参照が変わり、「受理集合・値・参照すべて不変」というwave説明が偽になる。
- **親が採るべき対応:** docs-onlyを維持する。理由は「既存到達可能挙動がD1325と一致し、実装変更が不要」に置き換える。

### 2. このwaveが実際に閉じるのはworklogの誤った実装待ち状態

- **対象:** docs-onlyの実効性、`docs/worklog.md:1684-1686`
- **何が誤りか:** D1325自体は既にdecisionsとworklogへ着地済みだが、T-2067は現在も「裁定済み → 実装待ち」と記録されている。2択は既存挙動を採用する終端裁定なので、この2件に実装待ちは存在しない。
- **放置時の影響:** 最新carry `:2913` がこの本文を運び続け、次の着手者が不要な実装検討を反復する。D1313が却下した「残余を正確に記録しない」型そのものになる。
- **親が採るべき対応:** fragmentで「設計択一2件は完了、残る3件」を明記し、T-2067は `更新` の一部完了とする。D1325という新しい決定を作ったとは主張しない。

### 3. load-only consumerの母集合がplanでは過小

- **対象:** plan Q2、残る3件のうちload-only consumer
- **何が誤りか:** `s8c_result_judge.py` だけではない。
  - `s8b_oracle_manifest.py:1205` はstatic loaderだけで、`:674-688,807-809` のfloor/budgetを候補manifestへ射影する。
  - `s8c_result_judge.py:2108,2188` はstatic loaderからfloor artifact参照を消費する。
  - `p3_autonomous_workload_trial.py:4640` はC06予算用にstatic loaderを使う。現在は `_load_s8c_schedule_authority():1799-1804` が常時拒否するため未到達だが、site自体は存在する。
- **放置時の影響:** 残余をs8c judge 1件と読ませると、oracle manifestや将来到達するC06経路で同じ規則準拠検討が再発する。受理集合は今回変わらないが、残余の参照集合が過小になる。
- **親が採るべき対応:** worklogでは「load-only consumer群」と書き、少なくとも上記3群を母集合として扱う。

### 4. 削除経路は通常のcampaign操作にはないが、現実のfilesystem操作として存在する

- **対象:** E3、「削除された earlier run」
- **何が誤りか:** 「production cleanupがない」ことと「削除経路がない」ことは別。
- **証拠:**
  - fresh runは `s8b_floor_campaign.py:7798-7816` が通常directoryとしてcreate-only作成し、resumeは `--resume` で継続する。completed official runを消すproduction APIは検索範囲内にない。
  - `output/env/.../s8b-floor-official/` はguardの防護treeに含まれない。防護対象は主に `output/campaigns`、`output/exploration/campaigns`、`external/ccbench` である。
  - よってworkspace書込主体は `rm -rf -- output/env/.../s8b-floor-official/<run>` で消せる。未追跡runなら限定した `git clean -fd -- <namespace>` でも消える。
  - 現worktreeにはofficial run directory自体が0件で、実際に削除が発生した履歴証拠はない。
- **放置時の影響:** earlier Aを消した後にBをcandidateへ渡せば、現在集合だけを見る受理集合ではBが選ばれうる。
- **親が採るべき対応:** 「戻さない」はこの実在する残余を受容する裁定であり、攻撃を閉じたとは書かない。新機構の提案は不要。

### 5. active g1が実在するとの読みを防ぐ必要がある

- **対象:** planの「g1のみの成立点」説明
- **何が誤りか:** コード上のg1 fenceと、発効中のg1 artifactの存在が区別されていない。
- **証拠:** `output/s8b-freeze/` にv2 generation、approval、active pointerは0件。official runも0件。`BUDGET_APPROVAL_SHA256` は `s8b_holdout_freeze.py:52` で `None`。
- **放置時の影響:** docsだけのwaveがruntimeのg1選択を有効化した、または再凍結を可能にしたと誤読される。実際の成果物値・受理集合は何も変わらない。
- **親が採るべき対応:** 「コード上の既存境界を確認しただけで、active g1・official floor・予算承認を生成しない」と明記する。

### 6. planの「静的検査だけ」はwave完了条件としては不足

- **対象:** plan末尾の検証手順
- **何が誤りか:** briefは最終的な受入全走を明記しているのに、planは変更後の検査を `check_docs.py` とspool dry-runだけとしている。
- **放置時の影響:** 文書内容は正しくても、親がplanを逐語採用するとwaveの受入証拠が不足する。
- **親が採るべき対応:** 本consult段では静的検査のみでよいが、段7ではbriefのacceptance全走を維持する。pytest未実走を緑と報告しない。

### 7. 既裁定の順序・前提・予算留保

- **対象:** E5
- **確認結果:**
  - D811はpilot値を発効させずofficial値を先に採る。
  - D1161とD1334は承認JSON・pinをユーザー手番に残し、予算数値をofficial実行後まで保留する。
  - D1032、D1193、D1279、D1336はattempt registryと予算権限の設計・着地順を留保している。今回のfreeze budget approvalと混同して決めてはならない。
  - D1284はfloor protocolの世代移行を上位の段0権限束所有に残す。独立したg2設計は不可。
  - D1294は共有批准凍結の将来発効をrulings照合で拾い、新しい検知機構を作らない。
  - D1335によりworklog同期が必須。ただし現状は既に「実装待ち」まで同期済みであり、本waveの価値はその状態を「2件終端・3件残存」へ訂正する点にある。
- **抵触:** docs-onlyと直接抵触する裁定はない。予算確定、g2設計、上限解除を含めると抵触する。

## 閉包の数え上げ

母集合は「floor選択identity、floor/source投影、g1候補のserialization、RatifiedFreezeからfloor/budgetを消費するproduction site」とした。

検索軸は、識別子検索に加え、literal `1`、path形式、budget scope、公開API名、helper呼出し、loaderの別名import、floor/budgetの実消費を使用した。

**core 5箇所**

1. generation-neutralな規則本体: `s8b_holdout_freeze.py:1928-1963`
2. g1 candidate側呼出し: `:2053-2056`
3. g1限定投影: `s8b_ratified_freeze.py:1054-1085`
4. full validationのgeneration gate: `:3107-3110`
5. currentだけの選択呼出し: `:3303-3309`

**g1の命名・serialization面 8箇所**

1. candidate path: `s8b_holdout_freeze.py:49`
2. budget approval path: `:50`
3. budget scope: `:51`
4. refreeze note: `:62`
5. builder API: `:2014-2017`
6. literal `generation_number: 1` と診断: `:2084,2097-2098`
7. create-only generator API: `:2187-2198`
8. CLI surface: `:2212-2217`

**名乗り損ねているload-only consumer 3群**

1. oracle manifest: `s8b_oracle_manifest.py:674-688,842-860,1205`
2. s8c floor verifier/publish: `s8c_result_judge.py:2033-2060,2108,2188`
3. s8c C06 budget: `p3_autonomous_workload_trial.py:1807-1878,4640`

**除外**

- `_GEN_RE:88`、`_gen_path:1124`、generation chain `:1252-1265`、static loader `:1399-1418` は汎用gN machineryであり、D1325の選択・投影g1保証そのものではない。ただしload-only consumerを成立させる基盤として確認済み。
- oracle driverは `load → launch_validate`、report・oracle judge・verdictは `load → reverify` を通るためload-only群から除外。ただしhistorical reverifyはD1312どおり選択identityを課さない。
- tests・fixtureはproduction母集合から除外。対応する主な固定点は candidate生成 `test_s8b_holdout_freeze.py:1798`、selection `:2160,2194,2364`、投影 `test_s8b_ratified_freeze.py:1477`、g2 static load/full拒否 `test_s8b_ratified_verify.py:1266,1402`、historical選択除外 `:890`、budget scope `test_s8b_budget_approval_preflight.py:31`。
- s8c内部のG1/G2、環境契約世代、condition-freezeのg1は別の世代体系なので除外。
- archive、insight、過去planはruntime siteでないため除外。

## 残る不確実性

- 静的検査のみで、pytest・acceptanceは実走していない。
- repo外backup、人手による復元、任意Pythonによる再配置の有無は証明できない。
- 現在official runが0件なので、削除経路は能力の実在確認であり、過去に実行された証拠ではない。
- worktree・branch交差ゼロは今回の再測時点の状態であり、並行land後は再取得が必要。
- arbitrary Pythonによるprivate helperや公開型constructorの直接利用は、コード自身が明示する保証境界外。

## 総括

最も重い所見は、コードではなくworklogの「実装待ち」が残っているため、docs-onlyにも実効的な閉包価値があること。  
元の実測3は反証され、到達可能なg2への選択規則伝播はない。  
削除経路は通常campaign APIにはないが、generic filesystem cleanupとして現実に存在し、D1325はそれを閉じずに受容する裁定である。  
親は段4で「docs-only採用」と「T-2067を2件終端・3件残存へ更新」を採るべき。  
同時にload-only consumerを3群で記録し、active g1や上限解除を一切主張しないこと。  
最終完了時はplanの静的検査だけで止めず、briefのacceptance全走を維持する。