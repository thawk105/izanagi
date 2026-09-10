## 観点 1 の所見

- **refuted — 実装プランの主要な伝播層に抜けはない。** `s2-plan.md:3-58` は、sort driver の唯一の呼出し、`loop` の skip 用 resolver と評価用 kwargs、`pipeline.evaluate` から core、pre-build resolver、legacy/v2 build、`build_v2` wrapper、四つの build 出口、出口 resolver までを列挙している。実コード上の対応点は `p3_s4_loop_sort.py:397-401`、`loop.py:477-485,558-591`、`pipeline.py:1090-1101,1232-1278,1855-1871`、`buildcache.py:2594-2598,2836-2840,2980-3015,3176-3180,3241-3245,3320-3328`。

- **refuted — `src_token` 引数と `source_evidence.src_token` が不一致のまま鍵へ入る経路はない。** legacy は `buildcache.py:3128-3130`、v2 は `buildcache.py:2342-2344` で不一致を拒否し、その後に必ず `src_token = source_evidence.src_token` とする。legacy はその値を `cache_key()` へ渡す (`buildcache.py:3136-3139`)。v2 は `cache_key()` を呼ばず、同じ値を `_v2_identity()` へ渡す (`buildcache.py:2527-2531`)。したがって「`build_v2` 内で `cache_key` へ届く」という前提は誤りで、v2 の鍵は `_v2_identity.preimage["src_token"]` (`buildcache.py:1295-1324`) である。なお admission receipt も `SourceEvidence.src_token` を含むため (`build_admission.py:662-675`)、実際の鍵は direct `src_token` と admission digest の二経路で変わる。

- **real — 一層だけ欠落した場合は、多くの場合 stale hit ではなく偽の停止になる。** `loop` の skip resolver だけが無束縛なら、旧 raw variant が terminal のとき `loop.py:522-527` で誤 skip する。評価側だけが無束縛なら、caller の bound evidence と pipeline の current evidence が `pipeline.py:1102-1109` で不一致になり pre-build abort する。pipeline/build wrapper/四出口の kw だけが欠けた場合、鍵は evidence 由来で bound のままだが、出口の再計算だけ raw になり `buildcache.py:3337-3347` で停止する。hit は既存 entry を残して停止、fresh は staging を破棄して停止する。全 resolver 層から一貫して束縛が欠落した場合だけ、raw evidence・raw key・raw recheck が内部整合し、旧 entry が素通りする。
  成果物影響: 誤 skip または偽 abort では certified 母集合から候補が欠落し、全面欠落では旧 binary の測定値が新しい COMMIT として残る。

- **real、nit — 親 brief の実行経路表現は過剰である。** 段 5 の実経路は `resolve_evidence()` から直接 `_resolved_src_token()` へ進む (`source_digest.py:2294-2323`)。`resolve()` と `src_token()` はこの実経路では呼ばれない (`source_digest.py:2206-2216,2342-2360`)。両 public seam を変更するなら独立の伝播テストが必要で、不要なら変更面から外す方が局所適用に忠実である。
  成果物影響: 現在の段 5 certified 成果物には影響しないが、現プランのままでは両 seam の伝播削除 mutant が変異 report で生存する。

- **refuted — `run_campaign` 呼出し増加と duplicate ID 不整合はない。** 呼出しは `p3_s4_loop_sort.py:397-401` の一箇所だけで、inventory は `test_campaign.py:5355` で 1 を固定する。sort の `_resolve_duplicate` は共有実装そのもの (`p3_s4_loop_sort.py:336-340`) で、`summary.skipped_variants` の ID を直接使い (`p3_s4_loop.py:1339-1355`)、source を再解決しない。bound token から作られた新 ID と整合する。

## 観点 2 の所見

1. **real、MF-1 — `test_sort_oracle_contract_has_one_config_producer_and_exact_gate` と driver test の帰属が重なる。** `default_cfg()` の定数束縛は既存 `test_default_cfg_wires_s2_verify` (`test_p3_s4_loop_sort.py:769-775`) が既に固定しているため、新テストでも同じ assertion を持つと config 行の mutant で二 gate が赤になる。また repository 全体では `s1_direct_comparison.py:471-482` も同じ config key の producer なので、「one config producer」は段 5 driver 内に限定すべきである。既存テストに実定数の担当を残し、新テストは `_require_sort_oracle_contract()` の valid/invalid だけに絞る。driver forwarding testでは helper を sentinel contract を返す fake に差し替える。
   成果物影響: そのままでは mutation matrix の config 行が複数 gate 帰属となり、段 6 report の owner 判定が不成立になる。

2. **real、MF-1 — driver forwarding testで呼出し数まで検査すると inventory と重複する。** `s2-plan.md:73-74` の「呼出し数が増えると赤」は `test_campaign.py:5355` と二重である。新テストは既存一呼出しの kwargs が helper の sentinel と同一かだけを担当し、個数は inventory のみに帰属させる。
   成果物影響: 呼出し追加 mutantで二 gate が赤になり、mutation report の単一帰属が崩れる。

3. **refuted — `test_run_campaign_rejects_missing_or_skewed_sort_contract_binding_before_wal` は単一理由にできる。** sort専用 compound gateを一つの所有面とし、authorization・layout・WAL を poison spy にして、三者不一致の各 case がそれらへ到達しないことを確認すればよい。例外 message も sort専用に固定すれば、後段の別例外による偽 kill を避けられる。

4. **refuted — signature testは mutation の選び方を限定すれば帰属できる。** 各 signature 行の mutantを「keyword-only から positional」「default `None` を sentinel」に限定すれば、明示 keyword で呼ぶ伝播テストは赤にならず、`test_sort_oracle_contract_call_seams_are_keyword_only_default_none` だけが赤になる。引数削除 mutantは downstream テストも赤になるので、この gateの単独帰属には使えない。

5. **real、MF-2 — mutual exclusion testは偽 kill になりうる。** sort cfg に `backoff_grammar_version` だけを追加して両引数を渡すと、相互排他行を消しても既存 backoff gate (`loop.py:336-349`) が拒否する。両 config 宣言を実物定数に一致させ、二つの個別 gateが通る fixtureで初めて相互排他行を kill できる。`_resolved_src_token()` 側も current と baseline を異なる値にして、stock short-circuit に依存させない。
   成果物影響: 現状案では相互排他 mutantが生存しているのに matrix が killed と誤記録しうる。

6. **refuted — `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate` は適切に分離できる。** resolver を bound evidence を返す spy、evaluate を結果だけ返す spyにし、二つの kwargs と evidence object identityだけを見る形なら `loop.py` の二つの pass-through 行を単一理由で検査できる。

7. **real、MF-3/MF-4 — pipeline testだけでは source public seam、`build_v2` wrapper、四出口を検査できない。** `s2-plan.md:88-89` の test は build API 自体を mock するため、`build_v2()` から `_build_v2_impl()` への `common` (`buildcache.py:2980-3015`) へ到達しない。また段 5 実経路外の `resolve()` と `src_token()` に追加する pass-through 行にも behavior test がない。前者は `_build_v2_impl` spyで contract 一件だけを見る独立 test、後者は `_resolved_src_token` spyで各 public seam の一段だけを見る testにする。反対側 build API の非呼出しは既存 branch behaviorであり、新しい contract 行の mutation ownerから外す。
   成果物影響: wrapperまたは public seam の kw削除 mutantが無検出のまま mutation reportに残り、該当 API利用時の raw identityを許す。

8. **real、MF-5/MF-6 — token/cache property testは、鍵の権威値と exact preimageを証明しない。** `s2-plan.md:91-92` のように helperへ同じ bound tokenを直接渡すだけでは、build実装が caller `src_token` を採る改変を検出できない。`src_token=None` と bound `source_evidence` を渡して、legacy key/v2 digestが evidence側の tokenで作られることを観測し、raw tokenを明示して evidenceと食い違わせた場合は cache open前に拒否されることも分けて確認すべきである。また contract fixtureは必ず `sort_swo_oracle.ORACLE_CONTRACT_ID` を importし、期待 hash はその実値と exact bytes `b"sort-src-token/v1\\0contract=" + id + b"\\0source=" + raw` から独立計算する。自作 `"contract-a"` だけの性質検査では preimage の一文字違いを検出できない。
   成果物影響: 誤った権威値または preimageでもテストが通り、variant ID、WAL参照、legacy key、v2 digestが仕様値と異なる。

9. **不確定、MF-7 — `None` 不変 testは「旧式の値」の作り方が未指定である。** 省略呼出しと明示 `None` の二つを比較するだけなら、両方が同時に変わる mutantを検出しない。raw non-stock token、stock、receipt keys、legacy preimage、v2 preimageを変更前の独立式または固定 fixtureと比較する必要がある。
   成果物影響: 既定経路の同時 drift が見逃されると、非対象 campaign の variant/cache pathと台帳参照が一斉に変わる。

10. **real、MF-4 — 四出口 testは既存 D1411 testの単純コピーでは不足する。** 写し元 `test_p3_s4_loop.py:3708-3842` は legacy/v2とも fresh buildしか通さず、mock resolverも `lambda *_args, **_kwargs: evidence` で kwを検査しない (`同:3745-3749`)。legacy/v2 × hit/fresh の4 parameter nodeで `_recheck_source_evidence` を spyし、`built_fresh` と実 `ORACLE_CONTRACT_ID` の二点だけを各 nodeの理由にする必要がある。旧 raw entry非到達の testとは分離する。
    成果物影響: hit側欠落なら正当な bound cache hitがabortし、fresh側欠落なら新buildが破棄され、いずれも候補がcertified集合から欠落する。

- **refuted — 既存 D1411 群は静的には赤にならない。** signature testは backoff引数だけを見る (`test_p3_s4_loop.py:3439-3454`)。forwarding testsは sort引数を渡さず、プランは非 `None` 時だけ新keyを加えるため call kwargsは変わらない (`同:3457-3643`)。`_resolved_src_token()` は既存三位置引数を維持する計画なので `同:3656` も保たれる。build testsも新引数のdefault `None`で従来通りである。未実走なので緑とは判定していない。

- **refuted — 既存 sort testの fake signature破損はない。** `S.run_campaign` の差替えは `test_p3_s4_loop_sort.py:461` の一箇所だけで、`lambda *args, **kwargs` のため新keywordを受け取れる。しかも oracle reject後に到達しないことを検査する fakeである。他に同関数の差替えはない。

## scope 外の帰結

- **real — P4をscope外にすると、平文契約とbuild attemptの構造的リンクは増えない。** oracle PASSは `p3_s4_loop_sort.py:251-257` で `diffq_variant_id` 側の WAL recordに契約IDを持つ一方、build開始は別のbound variantで `src_token`、admission receiptを持つ (`pipeline.py:1184-1197`)。新実装でそれらのhash値は変わるが、同じ build attempt の平文 `sort_swo_oracle` fieldや個別validatorはない。
  成果物影響: WAL全体には契約IDが見えるが、単独の BUILD_START/COMMIT から契約IDを復元・照合できず、campaign.lockと実装規約を併読する必要が残る。scope外支持。per-attempt監査が必要なら別裁定候補。

- **real — P5をscope外にすると reject variantは契約改版を跨いで同じままになる。** `diffq_variant_id()` は genomeとimplementationだけを使い (`p3_s4_loop.py:525-546`)、reject BUILD_START の `src_token` は空 (`同:549-580`)。一方、ABORT内の oracle rejection digestは `oracle_contract_id` を含むため (`sort_swo_oracle.py:3482-3503`)、payloadの診断内容は改版時に変わる。
  成果物影響: 同じ reject variant参照に異なる契約世代の診断attemptがぶら下がりうるが、certified母集合・選択値は変わらない。D1412どおりscope外支持。

- **real — P6のうち `s1_direct_comparison.py` には明確な残存分断がある。** 全roleのconfigに契約IDが入るため (`s1_direct_comparison.py:471-482`)、契約改版でcampaign ID、lock、WAL rootは変わる。一方、prepareは無束縛の `resolve()` (`同:923-930`)、evaluateも無束縛 (`同:1204-1224`) なので variant、build admission、cache keyはrawのまま再利用される。
  成果物影響: 新campaignのevent/reportが、旧契約と同じvariant/cache binaryを参照しうる。今回はscope外支持だが、P6裁定パッケージはs1単独の後続タスクとして切るべきである。

- **real — `s6_sort_sweep.py` はs1と同列ではない。** configにoracle契約がなく (`s6_sort_sweep.py:182-204`)、oracleも呼ばず (`同:28-30`)、raw resolve/run_campaignを使う (`同:398-418`)。契約改版だけではcampaign ID、WAL、provenance report、variant、cache keyのいずれも変わらない。段5の非stock tokenとはkeyが分かれるが、stock/inertは双方 `"stock"` のままである。
  成果物影響: s6成果物は契約改版で変化せず、既存 `reports/s6_sort_sweep_provenance.json` の参照も維持される。scope外支持。

## 親 brief への指摘

- **real、MF-8 — `s1-brief.md:29` は現行campaign IDと歴史成果物を混同している。** 現行 `default_cfg()` の ordinary IDは `p3-s5-sort-loop-s5-sort-autonomous-6f6a8cf1` と固定される (`test_p3_s4_loop_sort.py:955-974`)。`3be89e0d` はoracle導入前で再開不可の歴史成果物 (`docs/phase3-s5-sort-runbook.md:218-220`, `docs/phase3.md:326`) で、lockも旧PINかつ `sort_swo_oracle` を持たない (`output/campaigns/...3be89e0d/campaign.lock:1`)。
  成果物影響: briefのpathを現行ledgerと扱うと、レビュー・再開判断・report参照がoracle導入前の別成果物へ向く。現行ID不変の根拠は `6f6a8cf1` に直す必要がある。

- **real、MF-9 — `s1-brief.md:30` の「変わるのは src_token と cache keyだけ」は誤りで、同brief内とも矛盾する。** 実際には `verification_variant`、WAL variant、BUILD_START `src_token`、build admission receiptとdigest、cache pathが変わる (`source_digest.py:2330-2338`, `pipeline.py:1184-1197`, `build_admission.py:662-675`)。`s2-plan.md:135-138` は後半で正しく列挙している。
  成果物影響: mutation specや期待差分がsrc/cacheだけに限定されると、WAL・receipt・report参照の正当な変更を漏れまたは回帰として誤分類する。

- **real、nit — `s1-brief.md:9-10` の `resolve_evidence / resolve / src_token` 連鎖は実コードと一致しない。** 実経路は `resolve_evidence -> _resolved_src_token` である。
  成果物影響: certified値自体は変わらないが、変更面とmutation ownerを誤って広げる。

- **real、nit — `s1-brief.md:43` の「互いのkeyは異なる」は非stockに限定すべきである。** brief自身が `s2-plan.md:154` で認める通りstock/inertは `"stock"` のままである。ただし同じsource binaryなので、このcross-hitは今回の新しい偽hitではない。
  成果物影響: stock cache参照は従来と同じまま残る。must-fixではなく文言修正で足りる。

## 総括

must-fix は9件。最重要は `build_v2` wrapperとlegacy/v2 × hit/fresh四出口のcontract伝播が、現テスト案ではmutation帰属も実効検査もできない点である。  
実装プランの主要伝播経路自体は揃っており、鍵の権威値は両build APIとも `source_evidence.src_token`、不一致は鍵生成前に拒否される。  
親は段4で、実経路外の `resolve` / `src_token` seamを残すか、P6のs1残存分断を独立後続裁定へ送るかを確定すべきである。  
親 briefは現行ID `6f6a8cf1` と歴史成果物 `3be89e0d` を分離し、変化するWAL・receipt・variant参照を不変条件へ反映する必要がある。pytestは実走していない。