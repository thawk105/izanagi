## 所見

以下では C=`tools/plotting/plot_a2_certification.py`、P=`orchestrator/campaign/paper_story_a2_certification.py`、T=`orchestrator/tests/test_plot_a2_certification.py`、A=対象 `certification.json` とする。

[B-1]

- 主張: historical 世代の key 集合を現行集合との差分として定義する案は、次の configure key 追加を旧世代へ自動伝播させるため、同じ再発を起こす。
- 根拠: `s2/plan.md:61-67` は `POLICY_GENERATION_PRE_FETCHCONTENT_PATHS: (_TRACE0_CONFIGURE_ARGV_KEYS - {"fetchcontent_path_argument_prefixes"})` とする。現行集合は P:129-134 の 7 key、A:1 の埋め込み policy は decoded `trace0_cmake_argv.configure` に 6 keyしか持たない。
- 具体的な破れ方: 将来 `_TRACE0_CONFIGURE_ARGV_KEYS` に `new_required_key` を足すと、旧世代集合も「現行集合 minus FetchContent」なので `new_required_key` を要求する。t2364 は P:450-453 の exact-key 検査で再び読めなくなる。
- 深刻度: blocker
- 提案する最小の直し方: historical 世代は現行集合から計算せず、6 keyを独立した `frozenset` literalとして凍結する。current 側も immutable にし、historical 定義から current 定数を参照しない。

[B-2]

- 主張: 世代差を configure の2箇所だけに限定するため、plan は完全な歴史文法を凍結せず「1件限定 adapter を loader 内へ移した」段階に留まる。
- 根拠: `s2/plan.md:70` は「値は generation ごとの exact key set だけ」、同:117 は「P:367-602 の残りの検査、`_protocol_preimage` は変更しない」とする。実際には schema と top-level shape が P:376-383、各値制約が P:384-593、protocol preimage が P:318-329、consumer の schema assertion が C:291 に共有されている。既存記録も `docs/failures.md:23026-23027` で「この対応は 1 件限定の adapter であり、構造そのものは残る」と明記している。
- 具体的な破れ方: 次に `_TOP_LEVEL_KEYS` へ必須 fieldを加える、`POLICY_SCHEMA` を v3 にする、既存値制約を締める、または `_protocol_preimage` を変えると、exact pairから historical generationを選べても、configure 分岐へ到達する前か protocol identity照合でt2364が拒否される。
- 深刻度: blocker
- 提案する最小の直し方: generationごとに schema、全 exact-key集合、protocol-preimage規則、値 validatorを束ねた不変な grammar contractを渡す。共有関数を使う場合も、各 predicateを contractから取得させ、historical 世代が将来の current 定数や predicateを参照しない構造にする。

[B-3]

- 主張: planned t2364正例は当該1件の再発を検出できるが、今後追加される canonical current-full成果物の登録漏れを検出する閉包テストがない。
- 根拠: `s2/plan.md:197-204` は t2364専用正例だけを追加する。C:47-55 の `CANONICAL_SHA256` は複数成果物を列挙する一方、現在の T:1200-1215 は hash literalの一致しか検査せず、各 current-full policyを loaderへ通さない。
- 具体的な破れ方: 次の成果物を `CANONICAL_SHA256` に追加しても artifact固有の loader testを追加し忘れれば、さらに次の文法変更でその成果物だけ読めなくなっても全走は緑のままになり、図の再生成時まで気づかない。
- 深刻度: must-fix
- 提案する最小の直し方: Tへ、`CANONICAL_SHA256` の全 certificationを走査し、current-full schemaなら埋め込みpolicyをdecodeして `_load_current_policy` まで通す静的閉包テストを1本追加する。外部12-file rootは不要である。

[B-4]

- 主張: 「受理集合を1件も増やさない」という brief と、任意 callerが historical 文法を指定できる公開 `load_policy` 案は、受理面の定義が一致していない。
- 根拠: `s1-brief.md:38` は「受理集合を 1 件も増やさない」とするが、`s2/plan.md:77-80` は公開 `load_policy(..., generation=...)` を追加し、同:98-115 は historical世代なら6-key policy全般を検査可能にする。exact hash pairはconsumer側の同:164-172にしかない。
- 具体的な破れ方: callerが任意に作った文法上正しい6-key policyを `load_policy(path, generation=POLICY_GENERATION_PRE_FETCHCONTENT_PATHS)` へ渡せば、t2364のhash pairでなくても受理される。figure consumerの成果物受理集合は閉じていても、公開loaderの受理言語は広がる。
- 深刻度: must-fix
- 提案する最小の直し方: 不変条件を「`load_measurements` の成果物受理集合」に限定すると明記するか、公開 `load_policy` の署名を維持し、historical dispatchはconsumer専用のprivate entry pointへ分離する。

[B-5]

- 主張: plan自身の file:line anchorは全件実在するが、親briefの3 anchorは実範囲からずれている。
- 根拠: `s1-brief.md:50` の「C:194-250」「同 256-290」「`_expected_hashes:124-142`」に対し、実際は `_historical_policy_view` が C:194-252、`_load_current_policy` が C:255-307、`_expected_hashes` が C:125-144である。planが参照する P:49、129-134、367-602、2153-2219、4929-4932、C:47-70、125-160、176-307、603-625、857、908-916、T:187-396、501-895、producer test:1813-1826、1954-1998、job-contract test:596-610 はすべて現物と一致した。
- 具体的な破れ方: briefだけを辿るreviewerは、historical `Policy.cells` の返却行 C:251-252、current policyのidentity/cell/source-bound検査 C:291-307、expected-hash shape検査 C:143-144を読み落とす。
- 深刻度: nit
- 提案する最小の直し方: briefの3 anchorを C:194-252、C:255-307、C:125-144へ直す。

[B-6]

- 主張: test名の置換で既存docs pinが陳腐化する。
- 根拠: `docs/failures.md:23024-23025` は「`test_historical_rejects_changed_certification_bytes` を赤にする」と記録するが、`s2/plan.md:209-214` は T:543-553 を `test_historical_generation_requires_certification_hash_component` へ置換する。
- 具体的な破れ方: failure記録から現行testへ到達できなくなり、当該変異の再発検知先が見つからない。repo内のwhole-file SHA-256検索では変更予定のC/P/T source hashに別pinはなく、shipped A-2/A-6 policy hash pinはproducer test:1817-1822、1995-1998に限られ、policy fileを編集しない限り波及しない。
- 深刻度: nit
- 提案する最小の直し方: T:543 の既存test名を維持してbodyだけ強化する。改名するなら対応するfailure文書も同じ変更単位で更新する。

[B-7]

- 主張: briefが必須とした「過去測定を現行正しさへ昇格させない」という明記先が、planの具体的な編集項目から抜けている。
- 根拠: `s1-brief.md:33-34` は「この一文を成果物 (insight README と decisions) に明記する」と要求するが、`s2/plan.md:193` は不変保証として概念を述べるだけで、対象READMEやdecision fragmentへの編集手順を持たない。
- 具体的な破れ方: codeとtestが完成しても、`output/insights/2026-09-08_t2421-a2-policy-version/README.md` とdecision記録の一方または両方に要求文がなく、明示要求を満たさないまま完了扱いになり得る。
- 深刻度: must-fix
- 提案する最小の直し方: planへ両ファイルへの逐語追記を明示し、docs検査前に両方を検索する完了チェックを置く。

## 次に文法が締まったときの追跡

1. producer文法の担当者がP:129-134へ新しいconfigure keyを追加する。この時点でplanned historical定義がcurrent集合との差分なら、その新keyが旧世代にも混入する。

2. C:164-172相当のplanned分岐は、t2364のexact `(cert sha, policy sha)` から `pre-fetchcontent-path-arguments` を正しく選ぶ。

3. producerの `load_policy(..., generation=...)` はplanned P:85-93で世代を解決するが、P:450-453相当のexact-key検査で、新keyを持たないA:1のpolicyを拒否する。つまり選択成功後に同じ再発が起きる。

4. 今回予定される `test_t2364_frozen_policy_loads_through_registered_generation` が実装されていればt2364については赤になり、追加漏れに気づく。ただし他のcanonical current-full成果物には同型testが自動適用されない。

5. 修復には、少なくともP:49付近へ「変更前current」を表す新generation ID、P:134直後へ変更前文法の独立literal、C:57-70へその期間の各成果物のexact hash pair、T:516以降へ正例とhash-component負例を追加する必要がある。

6. 新しい締め付けがtop-level key、schema、値制約、protocol preimageの変更なら、さらにP:376-602の該当検査とC:291のschema assertionも世代別にする必要がある。現在のplanにはその追加箇所を導くgrammar contractがない。

7. 最小の再発検知閉包は、TでC:47-55の全canonical current-full成果物を列挙して埋め込みpolicyをparseすること。このtestを入れ忘れた場合、artifact固有testのない成果物は実際の図再生成まで破損を検知できない。

## 親 brief の検算

1. 事実1: 支持。C:255-268だけがproduction consumerとして `policy_bytes_base64` をdecodeし、呼出しはC:586-587のcurrent-full分岐だけである。repo検索で他の非test consumerはなく、P:2772、2851、4743等はproducer側の書出しである。

2. 事実2: 支持。ただしconsumer parseに限定する。P:129-134は7 key、A:1のdecoded policyは6 key、shipped policy:52-78との差は `fetchcontent_path_argument_prefixes` だけだった。`source_commit` 31ec382a... のhistorical `load_policy` と現行P:367-602の差もkey集合とP:472-487の値検査だけである。一方、実行時argv文法はP:2193-2217も変更されており、historical `Policy` の再実行には使えないが、figure consumerはその関数を呼ばないため今回のfigure-data構築は壊さない。

3. 事実3: 支持。overrideなしではC:128-136がresolved pathをC:47-55のrepo-owned pin表へ照合し、未登録なら「`path is not in repository-owned pin table`」で拒否する。C:139-144もhash pairのshapeを閉じる。

4. 事実4: 支持。C:57-70の唯一のentryは2 hashをtuple keyに持ち、C:275-287はその完全一致でのみhistorical分岐する。

5. 事実5: 支持。P:110-115は13 top-level key、P:318-329のprotocol preimageは9 keyである。除外は `historical_reference`、`durable_measurement_base`、`tracked_destination`、`scheduler` の4つである。

6. 事実6: 支持。C:857は生成時のgenerator hashを記録するが、C:908-916のlive closureはtracked inputsとoutputsだけを検査する。既存fig6 provenance:4-6にもgenerator hashはあるがlive pinではない。現在のC/P/T source全体hashを `orchestrator/tests/`、`tools/`、`docs/` で検索しても別pinはなかった。

7. 事実7: 支持。C:162-174がlegacy/current-fullを分け、C:585-597でpolicy loaderを使うのはcurrent-fullだけである。legacyは固定 `LEGACY_WORKLOADS` と `LEGACY_CELLS` を使う。

8. (P1-a): 支持。C:194-252はschema、configure key集合、protocol hashの3 assertion後に`Policy`と`CellSpec`を再構成し、入力bytesはC:275-287のexact pairに固定されるため、現状のartifact受理集合は広がらない。ただし「正しさではない」という表現は選択集合についてだけ有効で、adapter実装の将来ドリフトまで免責するものではない。

9. (P1-b): 支持。A:1の埋め込みpolicy、shipped policy:1-136、historical/currentの`load_policy`全体を突き合わせた範囲では、parse文法差はconfigure key 1個とその値検査だけである。実行時argv validatorの差は別に存在するが、今回のconsumer経路では未使用である。

10. (P1-c): 支持。A:1のcertification bytesには `"source_commit":"31ec382a..."` が含まれ、C:151-156でcertification全bytesのSHA-256を検査するため、source commitは既にcert hashへ束縛されている。第三key化は独立した閉包強化にならない。2026-08-24 certificationにも `source_commit` は実在した。

## 読解で予測する赤

これは静的読解であり、pytest実測ではない。

planを記載どおり完全に実装し、T:340-649も同時更新する前提では、全ファイル走で赤になる既存nodeidは予測しない。`load_policy()` の既定はcurrentのままで、A-2 bytes/protocol pin test、A-6 pin test、current FetchContent負例はいずれも維持される。job-contract test:604-610のwrapperはpathだけを受けるが、その経路は既定世代しか呼ばない。

ただし次の旧nodeidを直接指定する外部呼出しはcollection errorになる。

- `orchestrator/tests/test_plot_a2_certification.py::test_historical_exact_hash_pair_uses_the_historical_policy_view` — planが改名するため。
- `orchestrator/tests/test_plot_a2_certification.py::test_historical_rejects_changed_certification_bytes` — planが置換・改名するため。repo内runner pinは見つからなかったが、`docs/failures.md:23025` はこの名前を参照している。

## 裁定パッケージ候補

- 将来producerが `policy_generation` を成果物へ書く案。D1754のhash pairを主keyのまま残し、generationは自己記述性と二次assertionにだけ使える。既存artifact schemaとbytesを動かすため今回scope外だが、手動登録漏れを減らす実効性がある。
- historical `Policy` をproducer再実行にも利用する案。P:2153-2219のcurrent argv validatorはFetchContent 4 pathを要求するため、parse世代化だけでは再実行できない。figure-data読取とは別契約としてversioned execution validatorが必要である。
- loader source/provenanceのlive pin。現在のfig6 provenance:4-6は生成時記録だけであり、「どのversioned validatorで再解釈したか」を将来証明するなら別のpin設計が要る。

## 総括

最重点は、historical key集合がcurrent集合との差分で定義され、次のkey追加で直ちに再汚染される[B-1]である。  
さらにconfigure以外のvalidatorが全世代共有なので、planは再発構造を一般には除去していない[B-2]。  
t2364固有testは有効だが、全canonical artifactを自動走査する閉包testが必要である。  
段4では「今回1件を直す」にscopeを狭めるか、「完全な世代別grammar contract」を作るかを必ず裁定すべきである。