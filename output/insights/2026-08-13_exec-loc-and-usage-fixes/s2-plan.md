## 単位 1

### 変更点

- `tools/collect_wave_usage.py:38-52`
  - 現行: 外側 parser も `--project -work-...` を option と解釈し、実測 run2 と同じ `SystemExit(2)` を起こす。
  - 変更後: `_parse_args()` を設け、`argv is None` なら `sys.argv[1:]` を固定した上で、`--project` と `--projects-root` の直後が「`-` 始まりだが既知 option 名でも `--` でもない」場合だけ `--project=<value>` / `--projects-root=<value>` に正規化する。既知 option が直後に来る欠落入力は従来どおり parser error にする。
  - `--wave-id` も型上は任意文字列だが、本件の project slug 契約ではなく現行 wave ID に先頭 dash の要件もないため対象外とする。必要なら呼び手が等号形を使う。
  - `--help` の epilog に終了値契約を明記する。

- `tools/collect_wave_usage.py:94-106`
  - 現行: 全て値と option を別 token で構築する。
  - 変更後: 機械生成 argv は値付き option を全て等号 1 token 形に統一する。
    - `--projects-root=<path>`: `Path` は相対 path を許すため、正当な値が `-` で始まりうる。
    - `--project=<slug>`: 実 slug が該当するため必須。
    - `--cwd-under=<abs>`: 絶対 path 制約上 dash 始まりは正当値にならないが、生成規約統一のため等号形にする。
    - `--since=<ISO8601>` / `--until=<ISO8601>`: `tools/claude_session_ledger.py:152-175` の有効日時は dash 始まりにならないが、同じ理由で統一する。
    - `--max-files=<N>`: `tools/claude_session_ledger.py:97-106` が 1〜1000 に制約するため dash 始まりは無効だが、統一する。
    - `--include-sidechains` は値なしのまま。
  - option 順序と project の反復順は変えない。

- `tools/collect_wave_usage.py:187-220`
  - 現行: artifact を保存後、全 status で 0。
  - 変更後: `_publish_create_only()` を先に実行する現行順序を維持し、その後に status→rc を一意に写像する。

| `collection.status` | rc | 呼び手の意味 |
|---|---:|---|
| `complete` | 0 | 収集できた |
| `incomplete` | 1 | artifact はあるが収集が壊れた／不完全 |
| `missing` | 1 | artifact はあるが観測値を得られなかった |
| `error` | 1 | artifact はあるが collector が壊れた |
| `blocked` | 3 | 実行場所規律により正当に走らなかった |

  - 未知 status は成功へ倒さず 1。
  - 5 status の schema と artifact 保存は変更しない。外側 parse、保存先検証、publish 自体の失敗は status artifact を安全に作れないため例外で区別する。

- `tools/collect_wave_usage.py:223-230`
  - 現行: `SystemExit` と `Exception` を全て 0へ変換する。
  - 変更後: `SystemExit(0)` は help として 0、argparse の `SystemExit(2)` は 2、通常例外は stderr を出して 1。`KeyboardInterrupt` は引き続き握り潰さない。
  - 内側 collector の `SystemExit` は `tools/collect_wave_usage.py:134-147` で `error` artifact になり、最終 rc は 1。

- `docs/failures.md:4432-4448` の F159 と `docs/decisions.md:10936-10938` の D233 は変更しない。`blocked` 時に collector 呼出し 0という契約を保持する。
- `docs/decisions.md:10393-10394` の D220 により収集は wave 完了 gate ではない。したがって段 9 は rc 3 を正常な未実行、rc 1/2 を収集故障として報告するが、いずれも既に完了した wave を失敗へ戻さない。
- `docs/dev-wave/core.md:109-112`
  - 現行の L1 footprint は静的計算で 10,624/10,625 bytes と余白 1 byteしかないため追記は禁止し、置換で収める。
  - 親が次の短縮を行い、rc の詳細は tool の `--help` に一元化する。
    - `:110` → `` `tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路。``
    - `:111` → `` `DW-O23` 失敗時は `DW-STOP` に従い、main HEAD/branch を報告する。``
    - `:112` → ``段 9 後に `tools/collect_wave_usage.py` を実行する（rc は `--help`）。``
  - checker が固定する `tools/dev_wave_land.py` の唯一経路 literal と `:109` の受入順序 literal は残る。

### テスト案

- `orchestrator/tests/test_collect_wave_usage.py::test_collector_argv_uses_equals_tokens_for_every_value_option`
  - `_collector_argv()` の全値付き token を完全一致で固定し、run3 の内側 parser 退行を落とす。
- `...::test_split_leading_dash_project_is_normalized_and_collected_once`
  - `--project -work-1-SFC-tanab-izanagi` を外側から渡し、collector へ等号形で1回だけ届くことを固定する。
- `...::test_project_value_does_not_consume_a_known_option`
  - `--project --cwd-under ...` を rc 2 にし、正規化が欠落引数を飲み込む退行を落とす。
- `...::test_collection_status_exit_code_contract_preserves_artifact`
  - 5 status を 0/1/1/1/3 に parameterize し、全ケースで artifact が先に保存されることを確認する。
- 既存の `test_zero_model_calls_*`、`test_limit_reached_is_incomplete`、`test_issues_make_a_nonzero_collection_incomplete` は rc 1へ更新する。
- `test_unclassified_site_is_blocked_without_calling_collector` と `test_collector_site_classification_fails_closed_without_evidence` は呼出し 0の期待を弱めず、rc だけ 3へ更新する。
- `test_collector_exception_is_error_but_main_returns_zero` は `...returns_one` へ、`test_process_returns_zero_when_required_arguments_are_missing` は `...returns_two` へ改名する。
- 保存先不正、既存 artifact、親 directory 不在の各テストは rc 1へ更新する。`test_output_below_empty_git_directory_is_accepted` と正常 complete は 0のまま。

### 受理集合

- 新規受理: 外側 CLI の split 形で渡された先頭 dash の project slug、および同型の relative `--projects-root`。
- 維持: 既知 option を project 値として誤消費しない。5 status と artifact schema は不変。
- process-level の成功集合は「何が起きても 0」から complete/help のみに縮む。段 9だけが rc 3を正常未実行として明示的に受理する。

## 単位 2

### 変更点

- `tools/claude_session_ledger.py:4-7`
  - `model_calls` の説明を「file 内 alias dedup」に加え、「同一 `message.id` の検証済み cross-file replica は全体で1回」と更新する。

- `tools/claude_session_ledger.py:412-430`
  - request state に非空 `parentUuid` の集合を追加する。`agentId` は replica transcript の配置情報であり model call identity ではないため fingerprint に含めない。

- `tools/claude_session_ledger.py:644-737`
  - 各 canonical へ `parentUuid` を蓄積する。
  - model call の replica fingerprint は次を含める。
    - `parentUuid` 集合
    - `terminal_has_usage`
    - `USAGE_FIELDS` 順の terminal usage
    - `usage_seen` と `usage_maxima`
    - terminal model
    - timestamp 有無・件数、選択に使う実効時刻、cwd
    - tool identity。ID付きは ID、IDなしは path を除いた record 内位置へ正規化する
  - file path、sidechain bit、global sequence、`agentId` は比較対象外とする。

- `tools/claude_session_ledger.py:744-751`
  - `_mark_cross_file_collisions()` を replica resolver に置き換える。
  - `message.id` group を先に処理する。
    - 全 member が有効な terminal usage を持ち、fingerprint が完全一致する場合だけ benign replica。
    - representative は rootを最優先し、その中で `(resolved path, ordinal)` の辞書順最小。root がなければ sidechain の同順最小。
    - `state["representative"]` へ loser→winner を記録し、issue は立てない。
    - root/sidechain 跨ぎは rootへ1回、sidechainだけなら sidechainsへ1回計上する。
    - usage、maxima、model、parent、選択時刻、cwd、tool accounting のいずれかが違えば従来の `message_id_collision` を立て、group 全体を `invalid_requests` に入れる。
    - 既に invalid な member が1件でもあれば benign 化せず、代表にも invalid を伝播する。

- `requestId` も同じ resolver 内で後段処理する必要がある。実測 transcript は同じ replicaに `request_id_collision` も伴うため、ここを放置すると message dedup 後も rc 2のままになる。
  - requestId group の canonical を message representative へ写像し、写像後が1件なら「message replicaにより説明済み」として `request_id_collision` を立てない。
  - 写像後が2件以上なら、別 model call 間の requestId 再利用なので従来どおり fatal。元 memberと代表を全て invalid にする。
  - requestIdだけが一致する groupは dedupしない。model call identity の根拠は `message.id` で、requestId は file-local transport aliasだからである。

- `tools/claude_session_ledger.py:46-90`
  - `FATAL_ISSUES` / `STRICT_ISSUES` から両 collision を外さない。降格は採らない。

- `tools/claude_session_ledger.py:868-875`
  - `population.request_identity` を、例えば `file_provenance_aliases_with_verified_cross_file_message.id_replica_dedup` に更新する。repo 内で現値を完全一致しているのは `test_claude_session_ledger.py:203-205`。
- `tools/claude_session_ledger.py:956-964`
  - representative mapを state に追加する。
- `tools/claude_session_ledger.py:1016-1045`
  - resolver 実行後、invalid と非 representative を集計から除外する。winnerだけを `_selected()` と `_add_request()` へ渡す。

### テスト案

- 既存 `test_raw_ids_do_not_merge_across_file_or_sidechain_provenance` は分割する。
  - `...::test_request_id_does_not_merge_distinct_cross_file_calls`
    - requestId一致・message.id不一致を rc 2、両 metric 0のまま固定する。
  - `...::test_message_id_replica_with_different_usage_remains_fatal`
    - message.id一致・usage不一致を `message_id_collision`、rc 2、過小／過大計上なしに固定する。
- `...::test_replicated_message_id_across_four_sidechains_counts_once`
  - 4本の `subagents/agent-*.jsonl` に同一 parent/message/request/usageと異なる agentIdを置く。rc 0、collision issueなし、sidechains model call 1、各 tokenが1回分であることを固定し、4重計上を落とす。
- `...::test_replicated_message_id_prefers_root_attribution`
  - rootとsidechainに同じ callを置き、root=1、sidechains=0を固定する。
- `...::test_request_id_collision_is_suppressed_only_when_explained_by_message_replica`
  - benign replicaへ第三の異なる message callを同じ requestIdで加えた場合は rc 2になることを固定する。
- `test_request_dedupe_uses_final_usage_and_all_three_input_fields` の `request_identity` 期待値だけ更新し、token期待値は弱めない。
- `test_strict_issue_matrix_covers_every_classification` は期待集合を一切変えない。両 collision が fatal/strict に残ることの tripwire とする。

### 受理集合

- 新規受理は、同一 `message.id` かつ accounting fingerprint が完全一致する cross-file replicaだけ。
- usage等が違う同一 ID、requestIdだけが重複する別 call、alias graph conflictは従来どおり拒否する。
- metric受理集合は広がるが、各 replica groupの寄与は常に1 call分であり、token・tool callの重複加算は許さない。

## 単位 3

### `local-ok` へ直接変えた場合に壊れる箇所

- `tools/pegasus/admission_registry.json:4-9` の classだけを変えると、`tools/pegasus_admission_registry.py:105-107` が非 `tools/pegasus/` の `local-ok` として registry全体を拒否する。
- `tools/check_docs.py:2588-2637` は共有 loader の失敗を「canonical registryを確定できない」にするため、投影検査まで進まない。
- `hooks/guard_bash.py:232-314` は loader障害を空 registryへ縮退させ、ledgerは fallback denyのままになる。class変更だけでは許可されない。
- loaderを緩めても `hooks/guard_bash.py:270-272` の wrapper再検証が拒否する。
- そこも緩めても `hooks/guard_bash.py:275-288` の `local_ok_paths` は `tools/pegasus/` 配下しか sanctionedへ投影しない。
- `hooks/guard_bash.py:604-615` は非 Pegasus local-okを `_PEGASUS_UNREGISTERED` に戻すため、`hooks/guard_bash.py:1195-1205` で拒否される。
- 実際に許可するには上記全てへ ledgerだけの exact例外が必要になる。ただし一般の非 Pegasus local-ok禁止は残し、次の negativeを削除・反転してはならない。
  - `test_pegasus_registry_loader_rejects_non_pegasus_local_ok`
  - `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree`
  - `test_bash_non_pegasus_local_ok_corruption_cannot_borrow_sanctioned_allow`
- `hooks/guard_bash.py:195-218` の fallbackと raw mention detectorは削除せず、正常 registryでは allow、loader障害／hook内部例外では exact ledgerをdenyする二重契約にする必要がある。
- `docs/pegasus-runbook.md:411-413,434-436,446-452` の「canonical測定による local-ok」「非 Pegasus local-ok禁止」「新規 local-okには本節実測が必要」という規範も変わる。
- `tools/check_docs.py:2892-2926` の投影表は class/evidenceの完全一致を要求する。
- `tools/check_docs.py:2929-2989` の unknown表は `:2947-2948` で非 Pegasus pathを除外するため、ledger行は追加しない。
- `tools/check_docs.py:2992-3026` は evidenceが厳密に `runbook §7.0 実測` の全 entryを期待集合へ入れる一方、`:3004` は `tools/pegasus/` pathしか解析できない。ledgerにこの完全一致値を使うと実測表へ表現不能な期待値が生じる。
- `orchestrator/tests/test_hooks.py:1708-1759,2413-2440,2041-2076,2746-2770` の class、entry、local evidence、正規化綴り、login/suspect acceptance goldenが全て変わる。専用 positiveを追加しつつ上記 negativeは維持する必要がある。

したがって class flipは単なる台帳反映ではなく、非 Pegasus exact allowlistという新しい admission architectureである。

### entryを削除した場合

- registryは他 entryがあるので `tools/pegasus_admission_registry.py:93-95` の非空条件には抵触しない。
- `docs/pegasus-runbook.md:460` の投影行も消さなければ `tools/check_docs.py:2916-2926` が集合差を出す。
- fallbackを残すと `hooks/guard_bash.py:613-615` がledgerを引き続き拒否する一方、`test_bash_non_pegasus_fallback_set_matches_registry_projection` が不一致を検出する。
- fallbackも消すと、非 `tools/pegasus/` の未登録 pathとして login/suspectで許可され、保護を失う。
- さらに fallback集合が空だと `hooks/guard_bash.py:212-218` の `"|".join(...)` は空文字になり、`re.compile("")` は全入力へ一致する。hook内部例外時に無関係な `git status` 等まで `:1646-1662` で拒否する。
- 空集合を許す一般化をするなら never-match regexを明示構築する必要があるが、ledger保護喪失は直らない。削除案は不採用とする。

### 採用案: `unknown` 据置と証拠更新

- `tools/claude_session_ledger.py:29-38` には file数、総bytes、line、record、request、tool identity等の hard capがある。現 reasonの「input caps ... are incomplete」は誤り。
- 一方、実測は既定 `--json` の25 fileであり、専用 scopeではなく共有 `nqs-jsv.service` のdeltaである。runbook `docs/pegasus-runbook.md:377-403,411-423` の canonical測定を満たさず、cap境界も測っていない。このため classは `unknown` が妥当。
- `tools/pegasus/admission_registry.json:6` の reason案:
  - `inputs are hard-capped; canonical isolated-scope and cap-boundary measurements are unavailable`
- `tools/pegasus/admission_registry.json:8` の evidence案:
  - `compute-node shared-service memory.current delta for default --json/25 files (non-certifying; no delegated per-job cgroup): 5 valid runs, max +20.6 MiB; +128 MiB margin = 148.6 MiB; 1 negative run excluded`
- `:5` の classと `:7` の primary gateは変更しない。
- 親が書く `docs/pegasus-runbook.md:460` の投影行案:

  `| tools/claude_session_ledger.py | unknown | <上記 evidence を単一 backtick literalで記載> |`

- `tools/check_docs.py` の production変更は不要。
  - reasonは投影対象外。
  - evidenceは投影表と完全一致させる。
  - evidenceを厳密な `runbook §7.0 実測` にしないため、`:3016-3020` の実測期待集合は変わらない。
  - 単なる matcher回避ではなく、文字列自身に `non-certifying` と方法論差を明記する。

### テスト案

- `orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`
  - `:1754-1759` の reason/evidence goldenを新値へ更新する。class期待は `unknown` のまま。
- `...::test_bash_registered_non_pegasus_unknown_site_matrix`
  - 変更せず、login/suspect拒否と other/compute許可を固定する。
- fallback集合一致、raw spelling、実在 regular fileの各テストも変更しない。
- `orchestrator/tests/test_check_docs.py::test_admission_non_pegasus_registry_entry_requires_projection_only`
  - fixture、期待差分、投影行を新 evidenceへ更新し、unknown表・実測表を要求しないことを固定する。
- `...::test_admission_non_pegasus_exact_measured_sentinel_requires_measured_projection`
  - 非 Pegasus entryの evidenceを厳密な `runbook §7.0 実測` にした場合、実測表 path集合不一致になる負例を追加する。

### 受理集合

- 採用案では hookの受理 bitは一切変わらない。ledgerは login/suspectでdeny、other/computeでallowのまま。
- 変わるのは台帳の説明精度だけであり、「hard capなし」という誤記を除去し、非 canonical実測を証拠として残す。
- `local-ok` 案なら exact ledger実行の login/suspect受理が新規に広がる。削除案でfallbackも消す場合は、より広い意図しない受理拡大になる。

## 所有分割案 (段 5 で並列投入するための素集合)

- A — collector:
  - `tools/collect_wave_usage.py`
  - `orchestrator/tests/test_collect_wave_usage.py`
- B — ledger dedup:
  - `tools/claude_session_ledger.py`
  - `orchestrator/tests/test_claude_session_ledger.py`
- C — admission metadata:
  - `tools/pegasus/admission_registry.json`
  - `orchestrator/tests/test_hooks.py`
  - `orchestrator/tests/test_check_docs.py`
- 親専有 docs:
  - `docs/pegasus-runbook.md:460`
  - `docs/dev-wave/core.md:109-112`
  - spool、insights、裁定パッケージ
- `tools/pegasus_admission_registry.py`、`hooks/guard_bash.py`、`tools/check_docs.py` は採用案では非変更。class flipを選ぶ場合だけ、これらをまとめた独立の admission architecture単位へ切り出す。

## 親 brief への反論 (P1〜P5 のどれに、なぜ)

- P1: `unknown` 結論には賛成だが、主理由は構造的防壁ではなく「実測が runbookの canonical方法を満たさず、cap境界も未測定」である。exact allowlistなら一般 negativeを維持したまま非 Pegasus local-okを作れるため、「全防壁撤去が必須」は強すぎる。ただしそれは規範変更なので本 waveでは採らない。
- P2: 賛成。ただし evidenceは checkerを避けるための別文字列ではなく、非 certifying方法を正確に表す文字列でなければならない。
- P3: dedup方向は正しいが、requestId側の衝突を条件付きで解消しないと実測入力は依然 rc 2になる。message replicaで説明できる場合だけ抑止する必要がある。
- P4: 専用 rcだけでは不十分。DW-S09が rc 3を正常未実行、rc 1/2を非 gateの収集故障として解釈する契約と、外側 argparseの rc 2復元が同じ変更単位に必要である。また L1余白が1 byteしかないため追記ではなく圧縮置換が必要。
- P5: 内側の等号形は正しいが、run2で確認済みの外側 parser問題が未解決である。projectの split dash入力を正規化し、同時に機械生成する全値付き optionを等号形へ統一する。

## 総括

推奨案は、単位1で artifact-firstのまま rcを `0/1/2/3` に分離し、単位2で検証済み `message.id` replicaを代表1件へ寄せ、単位3では classを `unknown` に据え置いて hard capと非 canonical実測を正確に記録する構成である。実装・編集・commit、pytest、`check_docs` の実走は行っておらず、上記は必読資料とraw evidenceに基づく静的プランである。