## 前提の検査

- `s1-brief.md:53-66` の「変更面」は不完全。staged root は現在の CLI に存在せず、実運用では submitter が qsub 環境を作り、job body が `run-workload` を起動している。したがって `tools/pegasus/submit_paper_story_a2_certification.sh:13-55,166-183,238-263,304-365` と `tools/pegasus/paper_story_a2_certification.sh:9-14,28-38,281-310` も変更対象になる。
- それ以外の主要前提に反証なし。特に 5 引数の既存素通し、`FETCHCONTENT_FULLY_DISCONNECTED` の不在、golden 4 値 5 箇所、live pin の所在はコードと一致した。

## プラン

- `orchestrator/campaign/paper_story_a2_certification.v2.json:52-72`
- `orchestrator/campaign/paper_story_a6_certification.v2.json:46-66`

  両方の `trace0_cmake_argv.configure` に、同じ位置と内容で次の 1 key を追加する。

  ```json
  "fetchcontent_path_argument_prefixes": [
    "-DFETCHCONTENT_BASE_DIR=",
    "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=",
    "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=",
    "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST="
  ]
  ```

  `dependency_prefix_argument` の直後、`controlled_define_argument` の直前に置く。親案 P1 の 3 key 分解は採らない。

- `orchestrator/campaign/paper_story_a2_certification.py:40,123-127`

  `s8b_floor_campaign` を参照できるようにし、`_TRACE0_CONFIGURE_ARGV_KEYS` に `fetchcontent_path_argument_prefixes` を追加する。

- 同 `:418-460`

  policy loader に次を追加する。

  - exact `list`
  - 長さは 4
  - 全要素が空でない `str`
  - 空白なし
  - 全要素が `=` で終わる
  - 4 要素は一意

  shipped policy の具体的 literal は `test_policy_is_the_exact_literal_four_cell_protocol` と A-6 policy test で固定する。loader 自身に同じ 4 literal をもう一組埋め込まない。

- 同 `:2091-2142`

  `fixed` の後を次の順で位置的に読む。

  ```python
  path_prefixes = (
      grammar["dependency_prefix_argument"],
      *grammar["fetchcontent_path_argument_prefixes"],
  )
  path_tokens = tail[:len(path_prefixes)]
  ```

  各 token が対応する prefix で始まり値部分が空でないことを検査する。FetchContent 4 token の値部分は絶対 path として検査する。その後も次を維持する。

  ```python
  expected = fixed + path_tokens + ordered_define_tokens
  if list(argv) != expected:
      raise CertificationError(...)
  ```

  したがって追加、欠落、並べ替え、未知 token、`FULLY_DISCONNECTED` の混入はいずれも拒否される。

- 同 `:143-151,1282-1294`

  `_QSUB_ENV_KEYS` に `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` を追加する。`-v` の exact key 集合、非空値、`qsub_environment == variables` の既存検査に新 key を含める。qsub argv 自体は `-v` が 1 token のままなので `len(argv) == 18` は変えない。

- 同 `:585-622`

  `_condition_gate_family_context` に verified な `fetchcontent_base_dir` と 3 source dir の mapping を渡す。現在の一時 base 作成 `:605-607` を除き、`:608-615` の prebuild を次の入力へ変える。

  - `fetchcontent_base_dir=<verified root>`
  - `masstree_source_dir=<root>/masstree-src`
  - `mimalloc_source_dir=<root>/mimalloc-src`
  - `googletest_source_dir=<root>/googletest-src`

  `capture_define_inputs` の `configure_args` は次の順にする。

  ```text
  -DCMAKE_PREFIX_PATH=<dependency>
  -DFETCHCONTENT_BASE_DIR=<root>
  -DFETCHCONTENT_SOURCE_DIR_MASSTREE=<root>/masstree-src
  -DFETCHCONTENT_SOURCE_DIR_MIMALLOC=<root>/mimalloc-src
  -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=<root>/googletest-src
  ```

- 同 `:3336-3439`

  `run_workload` に必須の `third_party_source_root` を追加する。root は S8b と同じ `<base>/<name>-src` 契約とし、campaign 開始前に `s8b_floor_campaign._verify_pristine_floor_dependency_sources` を `repo_root=POLICY_PATH.parents[2]` で呼ぶ。`s8b_floor_campaign.py:2572-2789` が canonical absolute root、repo 外、実 directory、Git top-level、policy pin、clean 状態を検査する。

  floor 固有例外は `CertificationError` に変換し、条件 gate や build を開始しない。

- 同 `:3434-3479`

  条件 gate が prebuild と全 condition configure を終えて context を yield した直後、次を呼ぶ。

  ```python
  dependency_receipt = (
      buildcache._observe_fetchcontent_dependency_receipt(
          os.fspath(staged_sources["masstree"])
      )
  )
  ```

  その上で `run_campaign` に次の 5 値を同時に渡す。

  ```python
  fetchcontent_base_dir=os.fspath(third_party_root)
  masstree_source_dir=os.fspath(staged_sources["masstree"])
  mimalloc_source_dir=os.fspath(staged_sources["mimalloc"])
  googletest_source_dir=os.fspath(staged_sources["googletest"])
  fetchcontent_dependency_receipt=dependency_receipt
  ```

- 同 `:4703-4709,4822-4829`

  `run-workload` に必須 `--third-party-source-root` を追加し、`_run_workload_command` から `run_workload` へ渡す。

- `tools/pegasus/submit_paper_story_a2_certification.sh:13-55,166-183`

  必須 `--third-party-source-root ABS` を追加する。comma、`=`、改行を拒否し、`realpath -e` 後に root と 3 個の `<name>-src` が実 directory で symlink でないことを検査する。

- 同 `:238-263,304-365`

  `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` を実 qsub `-v`、receipt 再構築用 inline Python の引数、`qsub_environment` に同じ値で追加する。A-2/A-6 の双方で同じ key とし、A-6 固有なのは従来どおり policy path だけにする。

- `tools/pegasus/paper_story_a2_certification.sh:9-14,28-38,118-121`

  新 env key を必須化し、source root を解決する。

- 同 `:281-310`

  `$scratch/fetchcontent` を排他作成し、入力 root の `masstree-src`、`mimalloc-src`、`googletest-src` を同名でそこへ `cp -a` する。`run-workload` には job-local な `$scratch/fetchcontent` を `--third-party-source-root` として渡す。

- `orchestrator/tests/test_paper_story_a2_certification.py`

  次を更新する。

  - `:139-515,754-956`: condition prebuild の 3 source kwargsと capture の 5 configure argsを exact 比較する。一時 FetchContent base 前提は除く。
  - `:984-1298`: synthetic trace0 argv も `<base>/<name>-src` を作り、`buildcache._v2_commands` に base と 3 source dirs を渡す。
  - `:1358-1370`: submission fixture に新 qsub env key を追加する。
  - `:1690-1741`: policy literal の新 key と順序を固定する。
  - `:1763-1772,1839-1855`: 編集後 bytes から golden 4 値 5 箇所を張り直す。
  - `:4048-4438`: `run_workload` fixtures に staging root を渡し、S8b verifierと receipt observerを差し替えて、`run_campaign` が 5 値を受け取ることを exact 比較する。
  - `:4614-4643`: FetchContent token の欠落、並べ替え、prefix 改変、`FULLY_DISCONNECTED` 混入を追加 mutation にする。

- `orchestrator/tests/test_paper_story_a2_job_contract.py:39-109,390-755,988-1060`

  submitter harness と compute harness に 3 個の `-src` source root を作る。usage、qsub argv、receipt env、job-local copy、`run-workload` CLI を新 root 込みで exact 検査する。

- 変更しないもの

  `buildcache.py`、`loop.py`、`pipeline.py`、`condition_meaning_gate.py`、`s8b_floor_campaign.py`、`fetch_third_party.py` は変更不要。過去の `output/insights/**`、figure provenance、認証値も更新しない。

## 判断

1. 文法拡張

   親案 P1 ではなく、1 key の ordered literal 配列 `fetchcontent_path_argument_prefixes` を採る。4 個の実 token と policy 要素が一対一になり、prefix、names、順序を3フィールドから再合成する必要がない。

   `buildcache._v2_commands:1965-1971` と突き合わせた 0-based 順序は次のとおり。

   1. `[0]` cmake realpath
   2. `[1]` `-S`
   3. `[2]` CCBench source root
   4. `[3]` `-B`
   5. `[4]` build root
   6. `[5]` `-DCMAKE_BUILD_TYPE=Release`
   7. `[6]` `-DENABLE_SANITIZER=OFF`
   8. `[7]` C compiler
   9. `[8]` CXX compiler
   10. `[9]` dependency prefix
   11. `[10]` FetchContent base
   12. `[11]` masstree source
   13. `[12]` mimalloc source
   14. `[13]` googletest source
   15. `[14]` `CCBENCH_BACKOFF_FIXED`
   16. `[15]` `CCBENCH_BACKOFF_NOINLINE`
   17. `[16]` `CCBENCH_BACK_OFF`
   18. `[17]` `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION`
   19. `[18]` `CCBENCH_NO_WAIT_OF_TICTOC`
   20. `[19]` `CCBENCH_WAL`
   21. `[20]` `CCBENCH_TRACE=0`

   define 順は `model.py:61-63` の名前順と `buildcache.py:1935-1936` の TRACE 最後置きに一致する。

   新規の二重管理は全て次の3面である。

   - base prefix: policy 2 本と `buildcache.py:1940-1942`
   - source prefix: policy 2 本と `buildcache.py:872-877`
   - source names、個数、順序: policy 2 本と `_FETCHCONTENT_SOURCE_NAMES` `buildcache.py:58`

   既存の二重管理は `-S`、`-B`、fixed 2 token、compiler 2 prefix、dependency prefix、controlled `-D`、build subcommand/target/jobs である。

   食い違いが黙って通る trace0 経路はない。prefix と位置を検査した上で最終的に全 argv を比較するため、producer 側だけ、policy 側だけの変更はいずれも拒否される。同時変更は新 protocol hash を伴う明示的な protocol 改訂である。

2. `FETCHCONTENT_FULLY_DISCONNECTED`

   本経路には出ない。`run_campaign` は5値だけを受ける `loop.py:240-269`。それを `:562-571` で `evaluate` へ渡し、`pipeline.py:1298-1307` は同じ5値だけを `build_v2` に渡す。`post_oracle_dependency_binding` は pipeline の引数にも `common` にもない。

   `buildcache.py:1944-1950` は `post_oracle_dependency_binding is not None` の場合だけ disconnected token を生成する。receipt の存在だけでは生成しない。文法へは入れない。

3. 5引数の配線先と綴り

   必須 CLI `--third-party-source-root`、qsub env `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT`、job body の job-local copyを採る。既存定数による固定 path は採らない。

   認証経路の唯一の綴りは `<base>/<name>-src` とする。永続 cache は `fetch_third_party.py:525-537` の `<cache>/<name>`、hydrate は `:605-679` の `<staging>/<name>` なので直接は渡さない。

   `<base>/<name>-src` は S8b verifier `s8b_floor_campaign.py:2637-2658` と同型であり、`buildcache._canonical_fetchcontent_source_dir:823-845` の absolute、non-symlink、canonical directory 条件を満たす。さらに build 後の実効 masstree root は `buildcache.py:2793-2815` で必ず `<base>/masstree-src` と比較されるため、この綴り以外を直接採ると失敗する。

4. receipt の作り手

   `prepare_masstree_fetchcontent` の戻り値は `buildcache.py:703-708,2080-2085` の base、build dir、configure argv、build argvだけで、receipt を含まない。

   したがって prebuild と condition configure の完了後、`buildcache._observe_fetchcontent_dependency_receipt` `:938-984` を `<base>/masstree-src` に直接呼ぶ。得られる exact key は `masstree_head` と `config_sha256` で、`_FETCHCONTENT_RECEIPT_KEYS` `:59-61` と一致する。build は `:2808-2815` で同じ観測をやり直す。

5. 条件 gate

   `_condition_gate_family_context` の prebuild と `capture_define_inputs` の両方へ base と source 3本を渡す。source override が片方だけにある状態は認めない。

   この configure argv は trace0 文法の検査対象外。condition 側では `CapturedDefineInputs.configure_args` `condition_meaning_gate.py:802-841` が、独自 configure `:1643-1695` に展開される。一方、trace0 validator は WAL の `perf_configure_cmd` を `paper_story_a2_certification.py:3232-3240` から作り、`:2201-2244` でのみ `_exact_trace0_configure_argv` を呼ぶ。したがって condition 配線は専用 test で exact に守る必要がある。

6. golden の張り直し

   具体値は推測しない。編集後に各 policy について次を導出する。

   - bytes hash: `hashlib.sha256(path.read_bytes()).hexdigest()`
   - protocol hash: `load_policy(path).protocol_sha256`
   - 後者の定義は `_protocol_preimage` `paper_story_a2_certification.py:290-300` を `_canonical_json` し、`:551-557` で SHA-256 化した値

   A-2 bytes 値を test `:1768` と `:1770` の2箇所へ、A-2 protocol 値を `:1772` へ、A-6 bytes 値を `:1852-1853` へ、A-6 protocol 値を `:1854-1855` へ置く。

7. 凍結 bytes の pin 閉包

   値検索では A-2 の旧 hash が main test以外にも旧 `output/insights/2026-08-24_paper-story-a2-certification/*:1`、旧 run README、`docs/paper-story/figures/fig5_a2_certification_reject.provenance.json:84` に存在する。これらは歴史 receipt/provenance であり張り直さない。A-6 の2値は main test以外に見つからなかった。

   path検索では次を確認した。

   - `FROZEN_MANIFEST` `orchestrator/tests/test_frozen_artifacts.py:41-88` に policy 2本なし。
   - provisional key set `:93-117` にもなし。
   - `s1_expected_goldens.py:10-15` は編集可能な production source hashを意図的に pin しない。
   - `Policy` dataclass `paper_story_a2_certification.py:189-196` の bytes/hash は load時導出で、外部 literal pinではない。
   - `_protocol_preimage` `:290-300` は全 field 由来の同一性 hashだが、その外部 pinは main testの goldenだけ。
   - `canonical_policy_path` `:304-316` は2 pathを trust rootとして固定するが bytes hashは固定しない。
   - study/role による `_qsub_job_name` と env 分岐 `:319-336` は routingであり bytes pinではない。
   - 当該2 test fileに `pytestmark`、`xdist_group` はなく、repo設定にもこの2 file名を使う同一性 pinは見つからなかった。
   - admission registryは2 shell pathの実行区分を固定するだけで、script/policy bytesは固定しない。

   よって live に張り直す pin は親調査どおり main testの5箇所だけ。

8. 受入・焦点走の file 集合

   production 変更との grep 参照関係は次のとおり。

   - `test_paper_story_a2_certification.py:26,985,995,1358-1370,1690-1776,1839-1855`
   - `test_paper_story_a2_job_contract.py:12,17-18,23-36`
   - `test_campaign.py:5359`: `run_campaign` caller inventory
   - `test_ccbench_spawn_sites.py:142-149`: certification subprocess site inventory
   - `test_official_perf_closure.py:56-60`: production perf surface inventory
   - `test_hooks.py:3052,3088,3217,3433`: job bodyとsubmitterの実行区分

   焦点走には上の2つの A-2 test fileを全走し、依存契約として次も加える。

   - `test_buildcache_v2.py::test_prepare_masstree_fetchcontent_emits_all_three_staged_source_dirs`
   - `test_buildcache_v2.py::test_v2_source_dir_transport_reaches_configure_and_completion_identity`
   - `test_p3_s4_loop.py::test_run_campaign_rejects_invalid_prebuild_tuple_before_side_effects`
   - `test_p3_s4_loop.py::test_pipeline_rejects_invalid_prebuild_tuple_before_build_or_wal`
   - `test_p3_s4_loop.py::test_prebuild_reaches_production_build_v2_and_v2_commands_in_both_main_routes`
   - `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
   - `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
   - `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`
   - `test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized`

9. 変異方針

   semantic mutation は grammar、staging、receipt、5値 forwarding、qsub env、condition argv に分ける。golden hash mismatch や source文字列検査だけを semantic mechanism の証明には数えない。

## 変異事前登録の候補

- `paper_story_a2_certification.py:123-127`: 新 policy keyを集合から削除する
  → `test_paper_story_a2_certification.py::test_policy_is_the_exact_literal_four_cell_protocol`

- 同 `:418-460`: list長、重複、空白、末尾 `=` のいずれかの検査を除く
  → 新設 `test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list`

- 同 `:2091-2140`: baseとmasstreeの期待順を交換する
  → 新設 `test_trace0_fetchcontent_segment_matches_v2_command_order`

- 同 `:2091-2140`: source prefix検査を1本削除する
  → 新設 `test_trace0_fetchcontent_prefix_mutations_are_rejected`

- 同 `:2138-2140`: 全一致を部分一致へ変える
  → `test_trace0_argv_closed_grammar_rejects_unconsumed_tokens[unknown-configure-token]`

- 同 `:2091-2140`: disconnected tokenを許す
  → 新設 `test_trace0_argv_closed_grammar_rejects_unconsumed_tokens[fully-disconnected]`

- 同 `:3336-3439`: staged verifier呼出しを削除する
  → 新設 `test_run_workload_verifies_staged_sources_before_condition_gate`

- 同 `:608-615`: prebuildからsource dirを1本落とす
  → `test_paper_story_a2_certification.py::test_paper_condition_gate_is_p_strict_and_precedes_campaign`

- 同 `:616-622`: condition `configure_args` からsource dirを1本落とす、または順序を変える
  → 同 test内の runtime kwargs検査と、新設 `test_condition_gate_uses_exact_offline_fetchcontent_argv`

- 同 `:3434-3479`: receipt observerをprebuild前へ移す、または呼出しを削除する
  → 新設 `test_official_run_observes_dependency_receipt_after_condition_prebuild`

- 同 `:3467-3479`: 5値のいずれかを `run_campaign` へ渡さない
  → 新設 `test_official_run_forwards_exact_fetchcontent_five_tuple`

- 同 `:143-151,1282-1294`: qsub env keyを削除、または異なる値を receipt に受理する
  → 新設 `test_submission_rejects_missing_or_changed_third_party_source_root`

- `submit_paper_story_a2_certification.sh:238-365`: 実 qsubとreceipt再構築の片方だけに新 envを追加する
  → `test_paper_story_a2_job_contract.py::test_submitter_success_uses_production_cli_qsub_and_exact_stdout_contract`

- `paper_story_a2_certification.sh:281-310`: `name-src` を `name` へ変更する、1依存のcopyを削除する
  → 新設 `test_job_body_stages_exact_three_src_suffixed_dependencies`

恒真または不十分になりうる箇所:

- golden 5箇所は正当な policy bytes変更でも必ず赤になるため、文法機構の mutation testには数えない。
- `inspect.getsource` の文字列存在だけでは dead code化を殺せない。必ず runtime kwargs検査と対にする。
- 現在の `test_condition_gate_prebuild_runs_once_for_multiple_cells` は call回数しか見ず、source kwargs欠落では緑のままになりうる。exact kwargs検査を追加する。
- 既存 `extra-env` mutationは未知 key拒否しか証明せず、新しい必須 keyの欠落や値の不一致は殺せない。
- staged verifierを全 testでmockすると verifier呼出し削除が緑のままになるため、呼出し順と例外伝播を独立に検査する。

## 残る不確実性

- `fetch_third_party.py hydrate` は `<staging>/<name>` を生成し、採用する `<base>/<name>-src` を直接生成しない。実投入前に login側で hydrate後のcopyまたはrename手順を一度実測し、qsubへ渡す rootが3個の `-src` directoryを持つことを段3・段4で確認する。
- S8b の private verifierを別 driverから再利用するため、import依存と例外変換が許容されるかを段3レビューで攻撃する。新しい一般 verifierへの抽出は本scopeでは行わない。
- 新しい policy bytes hashとprotocol hashは、実装後の実 bytesからのみ導出する。
- read-only環境のためテスト、shell harness、実CMake configureは未実行。

## 総括

policyには ordered 4-prefix配列を追加し、closedな全argv一致を維持する。
供給契約はS8bと同じ `<base>/<name>-src` に一本化する。
submitterからqsub env、job body、Python CLIへrootを通し、job-local scratchへcopyする。
条件 gateを同じ3 source overrideでoffline化し、その完了後にmasstree receiptを直接観測する。
既存loop/pipeline/buildcacheの5値素通しは変更しない。
最大のriskは、hydrateの実在綴りと採用した `-src` 綴りの間のlogin側staging手順である。