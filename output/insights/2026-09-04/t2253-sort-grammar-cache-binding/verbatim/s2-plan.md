## プラン

- `orchestrator/campaign/p3_s4_loop_sort.py:285-305, 331-349, 370-375, 397-401`
  - `default_cfg()` の `search_config["sort_swo_oracle"] = ORACLE_CONTRACT_ID` は変更しない。したがって campaign identity は不変。
  - `p3_s4_loop.py:1277-1287` の `_require_backoff_grammar_version()` を局所的に写し、次を新設する。
    ```python
    def _require_sort_oracle_contract(cfg: CampaignConfig) -> str
    ```
    `cfg.search_config["sort_swo_oracle"]` が exact `str` で、実行中の `sort_swo_oracle.ORACLE_CONTRACT_ID` と完全一致するときだけ返す。
  - `run_one_iteration()` で、`p3_s4_loop.py:1451` と同じ位置関係になるよう、identity binding 前に上記 producer を一度だけ呼ぶ。
  - 唯一の既存呼出し `p3_s4_loop_sort.py:397-401` に
    `sort_oracle_contract_id=sort_oracle_contract_id` を追加する。呼出し自体は増やさず、`test_campaign.py:5355` の個数 pin を守る。写し元は `p3_s4_loop.py:1529-1537`。

- `orchestrator/campaign/loop.py:26-28, 239-260, 334-350, 477-485, 558-591`
  - 実行中契約との照合用に `sort_swo_oracle` を import する。
  - `run_campaign()` の keyword-only 部へ次を追加する。写し元は `loop.py:256`。
    ```python
    sort_oracle_contract_id: Optional[str] = None
    ```
  - `loop.py:336-349` の backoff gate は一行も緩めず、その隣に sort 専用 gate を置く。config 宣言、明示引数、実行中 module の `ORACLE_CONTRACT_ID` の三者が exact `str` かつ完全一致することを要求し、`_authorize_measurement()` の `loop.py:377-382` と layout/WAL 作成の `loop.py:394-409` より前に失敗させる。
  - `backoff_grammar_version` と `sort_oracle_contract_id` が両方非 `None` なら、この入口で `ValueError` とする。
  - `source_options` の `loop.py:477-485` と `evaluate_options` の `loop.py:558-591` に、sort 引数が非 `None` の場合だけ同名 key を追加する。既定時は dict の内容と downstream 呼出し形を増やさない。写し元はそれぞれ `loop.py:478-480`、`loop.py:558-561`。

- `orchestrator/campaign/pipeline.py:883-912, 1090-1101, 1232-1278, 1799-1827, 1855-1871`
  - `_prepare_evaluation_core()` と `evaluate()` の keyword-only 部へ、いずれも次を追加する。写し元は `pipeline.py:902` と `pipeline.py:1818`。
    ```python
    sort_oracle_contract_id: Optional[str] = None
    ```
  - `evaluate()` から `_prepare_evaluation_core()` へ素通しする。写し元は `pipeline.py:1870`。
  - pre-build の `source_digest.resolve_evidence()` 用 `source_options` に、非 `None` 時だけ追加する。写し元は `pipeline.py:1090-1100`。
  - v2 用 `common` と legacy 用 `build_options` に、非 `None` 時だけ追加し、それぞれ `buildcache.build_v2()` と `buildcache.build()` へ渡す。写し元は `pipeline.py:1252-1253` と `pipeline.py:1262-1272`。
  - verify、oracle、diff 検疫、auditor、bench の分岐には触れない。

- `orchestrator/campaign/source_digest.py:2177-2216, 2294-2323, 2342-2360`
  - `_bind_backoff_grammar_version()` の直後に sort 専用 binder を新設する。
    ```python
    def _bind_sort_oracle_contract_id(
        raw_digest: str,
        sort_oracle_contract_id: Optional[str],
    ) -> str
    ```
    `None` なら `raw_digest` をそのまま返し、非 `None` なら exact 非空、NUL を含まない ASCII `str` を要求して、次の exact preimage の SHA-256 を返す。
    ```text
    sort-src-token/v1\0contract=<ORACLE_CONTRACT_ID>\0source=<raw_digest>
    ```
    写し元は `source_digest.py:2177-2195` の `backoff-src-token/v1` binder。
  - `_resolved_src_token()` の既存三引数呼出しを保ちつつ、keyword-only の
    `sort_oracle_contract_id: Optional[str] = None` を追加する。両束縛が非 `None` なら `ValueError`、stock 判定なら従来どおり `STOCK`、sort 指定なら sort binder、それ以外は既存 backoff binderへ進める。
  - `src_token()`、`resolve_evidence()`、`resolve()` に同じ keyword-only・既定 `None` の引数を追加して `_resolved_src_token()` まで渡す。対応する backoff seam は `source_digest.py:2206-2216`, `2294-2323`, `2342-2360`。
  - `SourceEvidence` の schemaや fieldは増やさない。変わるのは指定された非 stock 経路の既存 `src_token` と、それから導出される `verification_variant` (`source_digest.py:2330-2338`) だけ。

- `orchestrator/campaign/buildcache.py:2245-2255, 2594-2598, 2836-2840, 2935-2958, 2980-3009, 3098-3104, 3176-3180, 3241-3245, 3308-3328`
  - `_build_v2_impl()`、`build_v2()`、`build()`、`_recheck_source_evidence()` の keyword-only 部へ
    `sort_oracle_contract_id: Optional[str] = None` を追加する。写し元は各署名の `backoff_grammar_version`。
  - `build_v2()` の `common` には非 `None` 時だけ追加する。写し元は `buildcache.py:3008-3009`。
  - v2 の cache-hit と fresh-build 出口 `buildcache.py:2594-2598, 2836-2840`、legacy の同出口 `buildcache.py:3176-3180, 3241-3245` から `_recheck_source_evidence()` へ渡す。
  - `_recheck_source_evidence()` は `source_options` に非 `None` 時だけ追加し、`resolve_evidence()` で同一契約を使った `SourceEvidence` を再計算する。写し元は `buildcache.py:3320-3328`。
  - `cache_key()` (`buildcache.py:624-642`) と `_v2_identity()` (`buildcache.py:1295-1324`) の署名や preimage は変更しない。前者の `|src=<src_token>`、後者の既存 `src_token` fieldへ、束縛済み tokenが入ることで両 cache identityを分離する。

- 変更しない面
  - `orchestrator/campaign/p3_s4_loop.py`: backoff producer、gate、binder経路を変更しない。
  - `orchestrator/campaign/sort_swo_oracle.py`: 契約生成を変更しない。
  - `orchestrator/campaign/wal.py`, `s1_direct_comparison.py`, `s6_sort_sweep.py`: P4からP6の裁定どおり変更しない。
  - `diffq_variant_id()`、`record_diff_reject()`、受理集合に関わる検査は変更しない。

## テスト計画

追加先は `orchestrator/tests/test_p3_s4_loop_sort.py:767-775` の default config 節直後を基本とし、`test_p3_s4_loop.py:3394-3842` の D1411 群を sort 名と contract 型へ写す。実走はしていない。

- `test_sort_oracle_contract_has_one_config_producer_and_exact_gate`
  - `default_cfg()`、`_require_sort_oracle_contract()`、実行中 `ORACLE_CONTRACT_ID` の一致を確認し、key 欠落、非 `str`、空文字、別 contractを受理すると赤になる。

- `test_sort_driver_forwards_campaign_declared_contract_to_single_run_campaign_call`
  - `run_one_iteration()` の既存一回の `run_campaign()` 呼出しを spy し、producer の戻り値が `sort_oracle_contract_id` として渡らない、または呼出し数が増えると赤になる。

- `test_run_campaign_rejects_missing_or_skewed_sort_contract_binding_before_wal`
  - configに宣言があるのに引数がない場合、引数が違う場合、configと引数を同じ偽値へ変えても module 定数と違う場合のいずれかが authorization/WAL 前に拒否されなければ赤になる。写し元は `test_p3_s4_loop.py:3415-3436`。

- `test_sort_oracle_contract_call_seams_are_keyword_only_default_none`
  - `run_campaign`、`evaluate`、`_prepare_evaluation_core`、`resolve_evidence`、`resolve`、`src_token`、`build_v2`、`build`、`_recheck_source_evidence` の新引数が keyword-only または既定 `None` でなくなれば赤になる。中核の写し元は `test_p3_s4_loop.py:3439-3454`。

- `test_sort_and_backoff_source_bindings_are_mutually_exclusive`
  - `run_campaign()` と `_resolved_src_token()` が両方非 `None` を `ValueError` にしなければ赤になる。

- `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate`
  - 一つの contractが `resolve_evidence()` と `evaluate()` の双方へ届かない、または同じ `SourceEvidence` が引き継がれなければ赤になる。写し元は `test_p3_s4_loop.py:3457-3522`。

- `test_pipeline_forwards_one_sort_contract_to_resolver_and_both_build_apis`
  - legacy と v2 の各経路で、同じ contractが resolver と選択された build API の双方へ届かない、または反対側の build API が呼ばれると赤になる。写し元は `test_p3_s4_loop.py:3525-3643`。

- `test_sort_source_tokens_and_both_cache_identities_are_contract_bound`
  - raw sourceが同じでも contractが違えば sort token、legacy `cache_key`、v2 identityが分かれない場合、別 raw sourceが衝突する場合、または stockが `"stock"` でなくなる場合に赤になる。写し元は `test_p3_s4_loop.py:3646-3705`。

- `test_sort_contract_none_preserves_preexisting_source_evidence_and_cache_identities`
  - 引数省略と明示 `None` で、非 stock raw token、stock token、`SourceEvidence.as_receipt()`、legacy key、v2 preimage/digestのいずれかが旧式の値から変わると赤になる。

- `test_bound_sort_requests_never_open_unbound_legacy_or_v2_entries_and_recheck_contract`
  - raw tokenで置いた旧 legacy/v2 entryが開かれる、fresh/hitの出口再照合に同じ contractが渡らない、または旧 entryを破壊すると赤になる。写し元は `test_p3_s4_loop.py:3708-3842`。

- 既存回帰として `test_p3_s4_loop.py:3394-3842` を変更せず再実行し、backoff経路を固定する。また `test_campaign.py:5346-5363` の inventory testで sort loopの呼出し数が一回のままか確認する。

## 既定経路不変の論証

`run_campaign()` は現在、`backoff_grammar_version=None` のとき `source_options` と `evaluate_options` に keyを追加しない (`loop.py:477-485, 558-591`)。sort引数も同じ条件付き追加にするため、渡さない callerの downstream kwargsは従来と同じになる。

`source_digest` では現行の非 stock 既定経路が `_bind_backoff_grammar_version(raw, None)` を通り、そのまま raw digestを返す (`source_digest.py:2182-2183, 2198-2203`)。新しい選択は次のとおりなので、両引数 `None` では同じ関数、同じ入力、同じ bytesになる。

```text
current == baseline              -> "stock"
sort contract is not None        -> sort binder
otherwise                        -> existing backoff binder
```

したがって、引数を渡さない場合は `SourceEvidence.src_token` と `verification_variant` も同一 (`source_digest.py:2323-2338`)。`SourceEvidence` の field集合と wire schemaも変更しない。

legacy cacheは `src_token == "stock"` なら preimageから `|src=` を省き、それ以外は受け取った tokenをそのまま使う (`buildcache.py:624-642`)。v2も既存 `src_token` fieldだけを使う (`buildcache.py:1295-1324`)。入力 tokenが同じなので、両 cache identityとcache pathは1 byteも変わらない。

pipelineとbuildcacheでも新しい optionは非 `None` 時だけ dictへ加える。出口再照合も引数省略なら従来と同じ `resolve_evidence()` 呼出しになる。sort campaignの `search_config` 自体は `p3_s4_loop_sort.py:298-305` のままなので、`ident.canonical_preimage()` が覆う値 (`ident.py:196-223`) と campaign ID、campaign.lockも不変である。

## P1〜P6 への回答

- P1: 賛成。
  - `ORACLE_CONTRACT_ID` を束縛値にする。これは corpus、checker実装、compile flags、dependency、IR grammar hash/version、TU templateを components hashへ含める (`sort_swo_oracle.py:3089-3107`) うえ、各versionとfull components digestをIDへ含める (`sort_swo_oracle.py:3122-3133`)。
  - `SORT_IR_GRAMMAR_VERSION` だけを使う案では、IR versionを据え置いて corpus、checker、TU templateのいずれかを更新した場合、raw source tokenが同じままなので `cache_key()` の `|src=` も同じになり、旧 contract下の binaryを再利用する。campaign identityだけは新しい `ORACLE_CONTRACT_ID` で変わるため、identity/WALとbinaryの契約が再び分断する。

- P2: 賛成。
  - `backoff_grammar_version` の流用は不可。sort configには backoff keyがなく、引数を非 `None` にしただけで既存 gateが作動し、declared値が `None` のため拒否される (`loop.py:336-349`)。仮にsort configへbackoff keyを足すと、campaign identityを変更し、sort contractをbackoff module定数として偽装することになる。
  - `sort_oracle_contract_id` を並列の keyword-only 引数とし、`sort-src-token/v1` の別ドメインを使う。
  - 両方非 `None` は意味の合成順を定義せず `ValueError` とする。`run_campaign()` 入口と `_resolved_src_token()` で拒否し、backoff binderをsort IDで呼ぶ経路は作らない。

- P3: 賛成。
  - これは仮想リスク向けの新規機構ではなく、D1548が指定した「D1411と同じ campaign由来の明示引数」の写しである。写し元は producer `p3_s4_loop.py:1277-1287`、producer使用 `p3_s4_loop.py:1451`、入口三者照合 `loop.py:336-349`。
  - sort側にも `default_cfg()` の宣言、明示引数、実行中 module定数が分裂する実在の同一性境界がある。既存 oracle結果の照合 `p3_s4_loop_sort.py:222-226` だけでは、後続 source/cache引数の欠落や差替えを検出できない。

- P4: 賛成。
  - `search_config["sort_swo_oracle"]` は既に campaign identityへ入る (`p3_s4_loop_sort.py:298-305`, `ident.py:212-223`) ため、campaign.lockへ新たな値を足す必要はない。
  - 実装後、非 stock accepted candidateでは `SourceEvidence.src_token`、WAL recordのvariant、`build_start.payload["src_token"]`、埋込みbuild admission receiptとそのdigestが変わる (`pipeline.py:1184-1197`, `build_admission.py:662-675`)。ただし `build_start` に平文の `sort_swo_oracle` fieldは増えず、`wal.py:1595-1629` のような個別payload validatorも増えない。
  - 帰結として、単独のbuild_start recordだけから平文contract IDを復元・照合できず、campaign.lockとの組合せが必要になる。

- P5: 賛成。
  - `diffq_variant_id()` はgenomeとraw implementationを材料にし、`record_diff_reject()` は空の `src_token` を書く (`p3_s4_loop.py:525-546, 549-580`)。sort側もこの経路をそのまま使う (`p3_s4_loop_sort.py:256-264`)。
  - scope外のままなら、拒否候補のdiffq variant ID、reject用BUILD_START payload、criticへ渡る拒否tokenは変わらない。accepted candidateのbound `src_token`、variant、cache identityだけが変わる。
  - 拒否候補はcertified母集合へ入らず、変更されるのは診断入力の重複だけというD1412の境界 (`D1412.md:3-11`) を維持できる。

- P6: 賛成。
  - `s1_direct_comparison.py` はconfigにcontract IDを持つ (`s1_direct_comparison.py:471-482`) 一方、source tokenを引数なしで解決し (`s1_direct_comparison.py:923-930`)、`evaluate()` にも新引数を渡さない (`s1_direct_comparison.py:1204-1224`)。このproducerのvariant IDと `s1-build-cache` keyは今回変わらず、oracle contractだけが変わった場合の旧binary再利用余地も残る。
  - `s6_sort_sweep.py` はoracleを使用しないと明記され (`s6_sort_sweep.py:28-30`)、raw `resolve()` と引数なし `run_campaign()` を使う (`s6_sort_sweep.py:398-418`)。そのvariant IDとcache identityは変わらない。
  - 段5 sort loopはbound tokenになるため、これらのraw token producerとcache rootを共有しても互いのkeyは異なり、今回の変更による新しいcross-hitは生じない。

## 残存リスク

- sandboxがread-onlyのため、上記テストは未実走であり、署名追加漏れ、mockのautospec不整合、import cycleは静的検査だけでは確定できない。
- `ORACLE_CONTRACT_ID` はoracle全体を覆うため、binary生成に直接影響しないcorpusやcheckerだけの変更でも非 stock cacheが無効化され、再buildコストが発生する。
- stock/inert sourceは従来どおり `"stock"` へ正規化されるため、contract IDはstock cacheには束縛されない。
- 旧raw-token cache entryは削除されず残る。段5 sort loopからは到達不能になるが、容量は回収されない。
- build_start payloadにcontract IDを平文再掲しないため、record単体の監査性は増えない。
- `s1_direct_comparison.py` のidentity/WALとsource/cacheの分断は意図的なscope外として残る。
- `s6_sort_sweep.py`、screening経路、直接 `evaluate()` を呼ぶ他producerは新引数を渡さない限り従来のraw tokenを使い続ける。

## 総括

段5 sort loopの既存一回の `run_campaign()` 呼出しへ、単一producerが返す `ORACLE_CONTRACT_ID` を明示的に渡し、sort専用binderから両build APIの出口再照合まで同じ値を通す。  
`cache_key()` 自体やcampaign `search_config`、backoff経路、受理集合は変更しない。  
最大のriskは、scope外とした `s1_direct_comparison.py` に同種のidentity/cache分断が残る点と、未実走の四つのbuild出口伝播である。  
段4ではP1のfull contract束縛、P2の両束縛同時指定拒否、P6のs1残存分断を意図したscope境界として最終確認すべきである。