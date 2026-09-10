## 受理集合の変化

- **重大: 5 本の組合せ検査を `pipeline._prepare_evaluation_core` だけに置くと、拒否順序と副作用が変わる。** 例えば `run_campaign(fetchcontent_base_dir=..., source dir 3 本, fetchcontent_dependency_receipt=None)` は、現状なら未知 keyword による呼出し時 `TypeError` だが、プラン実装後は authorization、layout 作成、WAL recovery、source identity 解決まで進んでから core で失敗する。さらに `run_campaign` の catch が `eval-exception` の `STAGE_ABORT` を記録し、その variant を terminal 化する。corrected な 5 本を次回渡しても skip され得る。5 本＋`env_contract` の all-or-nothing 検査は `run_campaign` 冒頭にも必要である。`s2-plan.md:27-30`、`orchestrator/campaign/loop.py:373-395`、`orchestrator/campaign/loop.py:427-463`、`orchestrator/campaign/loop.py:535-624`

- **意図された受理拡大は二つある。** 正しい receipt を持つ新 CLI 入力、および `OTHER` site で receipt を指定した入力が新たに受理され、後者は legacy `build()` ではなく `build_v2()` へ進む。これは P4 の明示採用範囲内であり、無条件の site 拡大ではない。receipt 無しの `OTHER` は従来どおり legacy、未知 site は従来どおり拒否される。`s2-plan.md:83-103`、`orchestrator/campaign/p3_s4_loop.py:132-160`、`orchestrator/campaign/p3_s4_loop.py:1525-1539`、`orchestrator/campaign/pipeline.py:1224-1289`

- **correctness gate の述語・順序を動かす必要はない。** 現行順は preflight/attribution → quarantine → `_require_condition_gate` → `run_campaign` であり、プランも 5 引数を最後の `campaign_options` に足すだけである。既存の condition-order test と quarantine-order test はこの不変条件を直接 pin している。`orchestrator/campaign/p3_s4_loop.py:1453-1529`、`orchestrator/tests/test_p3_s4_loop.py:86-97`、`orchestrator/tests/test_p3_s4_loop.py:6527-6568`

- **`buildcache` の受理集合は緩まない。** full tuple は既存の canonical base、source dir 3 本 all-or-nothing、exact 2-key receipt、base/receipt 同時指定、define 数検査をそのまま通る。部分 tuple は拒否され、driver が `-DFETCHCONTENT_*` を自作する案もない。`orchestrator/campaign/buildcache.py:717-731`、`orchestrator/campaign/buildcache.py:750-762`、`orchestrator/campaign/buildcache.py:823-869`、`orchestrator/campaign/buildcache.py:1936-2001`、`orchestrator/campaign/buildcache.py:2395-2451`

## build identity への影響

- **cache identity は指定時だけ変わる。** receipt の `{masstree_head, config_sha256}` と `"source-dir"` transport bit が pre-image に加わるため、従来の receipt 無し v2 entry は trace/perf とも別 digestになり、`buildcache` まで到達すれば再 build される。未指定 caller の digest は不変である。`orchestrator/campaign/buildcache.py:1343-1362`、`orchestrator/campaign/buildcache.py:2486-2549`、`orchestrator/campaign/buildcache.py:2550-2552`

- **重大: campaign/WAL identity は変わらないため、既存 terminal 結果が prebuild の消費を丸ごと飛ばす。** 同じ cfg/genome が以前 receipt 無しで certified/aborted 済みなら、新 job が receipt を渡しても campaign-id と variant-id は同じである。`run_campaign` は `evaluate` より前に skip し、driver は過去の結果を `_resolve_duplicate` で返すため、新しい cache digestも configure argv も生成されない。これは positive test を fresh layout だけで走らせると見逃す。D1690 の content identity 是正とは分けて、少なくとも「receipt transport 有無」の campaign namespace 分離、または既存 terminal を再利用しない同等の扱いが必要である。mimalloc/googletest 内容を identity に足す必要はない。`orchestrator/campaign/p3_s4_loop.py:1098-1129`、`orchestrator/campaign/ident.py:196-235`、`orchestrator/campaign/pipeline.py:124-130`、`orchestrator/campaign/loop.py:427-463`、`orchestrator/campaign/loop.py:527-531`、`orchestrator/campaign/p3_s4_loop.py:1540-1544`

- **D1690 の既知穴はそのまま残る。** base/source の path と mimalloc/googletest の内容は digest に入らない。同じ 2-key receipt と source-dir modeなら別 path・別 mimalloc bytesでも同じ cache entryを引ける。また hit 時の `BuildResult` は現在要求された path から configure command を再生成するため、WAL に記録される command が実際に cached binary を作った過去 argv と異なる余地もある。これは本件で直すべきではないが、プランの「記録される argv」説明には明記すべきである。`rulings-verbatim.md:63-82`、`orchestrator/campaign/buildcache.py:1295-1362`、`orchestrator/campaign/buildcache.py:2565-2641`、`orchestrator/campaign/buildcache.py:2088-2132`、`orchestrator/campaign/pipeline.py:1347-1357`

## pin 閉包の取りこぼし

- **`tools/pegasus/README.md` §7 の prose が確実に stale になる。** 実装後も「driver に seam が無く proxy clone に依存する」「消費配線は後続 wave」と表示される。tagged qsub command 自体は不変だが、編集閉包は production 4 file＋testsだけでは閉じず、この説明と未実測項目も同 commitで更新が必要である。`tools/pegasus/README.md:314-320`、`tools/pegasus/README.md:340-342`、`s2-plan.md:134-155`

- **job contract に copy destination の pin がない。** source dir 変数だけを `*-src` に変え、`destination=$prebuild_source_root/$source_name` を旧値のまま残した入力では、現行 required fragmentsを全部満たせるが、実体は旧 directoryへコピーされ、新しい source dirは存在せず prebuildが拒否される。`destination=$prebuild_source_root/${source_name}-src` 自体の required fragmentと deletion/reversion mutantが必要である。`tools/pegasus/p3_s4_loop_pegasus.sh:328-355`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:249-274`、`s2-plan.md:142-149`

- admission registry、`test_hooks` の二つの golden、runbook投影表、tagged qsub commandは path/class/evidence/envを変えないので同期不要である。`tools/pegasus/admission_registry.json:106-110`、`orchestrator/tests/test_hooks.py:2572-2591`、`orchestrator/tests/test_hooks.py:2745-2749`、`docs/pegasus-runbook.md:484-508`、`tools/pegasus/README.md:326-335`

- materializer registryも entrypointが同じなので変更不要である。caller inventoryも `run_campaign` の呼出し数が一つのままなら赤にならない。`orchestrator/campaign/materializer_admission.py:132-137`、`orchestrator/tests/test_campaign.py:5346-5367`、`orchestrator/tests/test_campaign.py:5431-5448`

- `p3_s4_loop.py` 全体は B4 projection closureで動的に hash されるが、testも現在 bytesから期待値を導出しており固定 SHA goldenではない。現行 preregistrationは値の記入前で、同期対象の admission recordもまだ要求状態にない。`orchestrator/campaign/p3_b4_closed_critic.py:623-684`、`orchestrator/tests/test_p3_b4_closed_critic.py:1969-2025`、`docs/phase3-b4-reflux-ablation-preregistration.md:224-238`

## scope の逸脱

- D1679 が見送った4件はプランへ混入していない。mimalloc/googletest HEADは型検査だけ、toolchain manifestはschema検査だけで共有経路へ渡さず、condition gate recordの保存方法を変えず、`--isolate-worktree` の TMPDIR検査も加えていない。`s2-plan.md:45-52`、`s2-plan.md:122-127`、`rulings-verbatim.md:27-44`

- receipt の exact field/type/path、config bytes hash、base/source equalityは余計な一般化ではない。job receiptを5本へ安全に射影し、`buildcache` が要求する `base/masstree-src` と一致させるための局所条件である。`s1-brief.md:41-47`、`s2-plan.md:36-81`、`orchestrator/campaign/buildcache.py:2792-2816`

- 本題成立に不足しているのは、前節の campaign terminal skip対策と、`run_campaign` 自身の副作用前all-or-nothing検査である。どちらも依存内容の完全 identity、tool identity、durable gate、TMPDIR hardeningではなく、指定された seamを実際に一度だけ正しい形で消費させるための要素である。

## テストの歯

- source path fragment testを消すと、3本を旧 `/masstree` 等へ戻す欠陥が通る。proposal branch fragment/mutantを消すとproposal側だけreceipt option欠落が通り、fixture側を消すと逆が通る。base equality mutantを消すと別 baseへ戻して fresh build後に `effective_root != base/masstree-src` で落ちる欠陥が通る。`s2-plan.md:138-153`、`orchestrator/campaign/buildcache.py:2801-2807`

- production `build_v2` positiveを消すと、driver → `run_campaign` → `evaluate` → `build_v2` のどれか一段が5本を落としても、各層stubだけのtestは通る。assertを production `buildcache.build_v2` と exact kwargsに固定する方針は正しい。ただしfixtureとproposalを明示的に二ケース化しないと、一方の `main` handoffだけ欠落する欠陥が残る。`s2-plan.md:159-170`、`orchestrator/campaign/p3_s4_loop.py:2267-2278`、`orchestrator/campaign/p3_s4_loop.py:2305-2309`

- 「base＋source 3本だがreceipt無し」の負例を消すと、4本案がpipelineを通過してbuildcacheまで到達する。「receipt有りだがsource 2本」の負例を消すと、lenientな部分指定判定が通る。どちらも受理集合を狭める向きで正しい。ただし direct `pipeline` testだけでは、`run_campaign` が副作用後に `eval-exception` abortを書く欠陥を検出できないため、「partial inputでauthorization/layout/WALが一切作られない」loop-level負例が別途必要である。`s2-plan.md:172-181`、`orchestrator/campaign/loop.py:602-624`

- default compatibility pinを消すと、既定 `""` を「指定あり」と数える実装や、未指定時にも新 keyを下流kwargsへ出す実装が通る。presenceは baseだけ `bool(base)`、source/receiptは `is not None` で判定する必要がある。`s2-plan.md:183`、`orchestrator/campaign/buildcache.py:2435-2450`

- configure argv probeを消すと、5 kwargsは届くがdefineが欠落・重複する欠陥をend-to-endで検出できない。production `_v2_commands` を実行して4 prefixを各1本assertする設計は歯がある。`s2-plan.md:185-204`、`orchestrator/campaign/buildcache.py:1952-2001`

- **receipt reader自体の負例が不足している。** 例えば `config_h_sha256` は過去cacheと同じ値を主張するが、`config_h_path` の現在bytesを改変したreceiptを、実装が再hashせず受理する欠陥は、valid positive、部分5本negative、argv probeのすべてを通せる。cache hit側は2-key receiptを再観測しないため、旧binaryを返し得る。少なくとも config hash mismatch、top-level extra/missing key、source名重複/欠落、noncanonical/symlink path、非文字列argv要素を一件ずつreaderへ当てる必要がある。`s2-plan.md:38-52`、`orchestrator/campaign/buildcache.py:2565-2641`、`orchestrator/campaign/buildcache.py:2792-2816`

- さらに「receipt無しでterminal済みの同一candidate → receipt有り再実行」で `build_v2` が呼ばれるtestが必要である。これを欠くと、fresh layoutのpositiveは緑でも本番では過去WALをduplicateとして返し、seamが死んだままになる。`orchestrator/campaign/loop.py:527-531`、`orchestrator/campaign/p3_s4_loop.py:1540-1544`

## 総括

プランは `buildcache` の既存述語や quarantine／condition gateを緩めず、D1679/D1690の範囲も概ね守っている。ただし実装前に直すべき欠陥が三つある。

- 5本検査を `run_campaign` の副作用前にも置く。
- receipt有無を区別しないcampaign/WAL terminal skipを処理する。
- README §7、copy destination pin、receipt reader負例、両main分岐のproduction positiveを閉包へ足す。

これらがない状態では、テスト上は正しいkwargsが届いても、実際のjobで過去WALを再利用してprebuildを一度も消費しない経路が残る。静的読解のみで、pytestや実測は実行していない。