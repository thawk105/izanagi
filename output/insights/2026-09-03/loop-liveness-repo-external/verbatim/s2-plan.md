## 総括

単位 A は、`exploration_campaign_layout` だけを字句 marker として `ast.parse` 前へ置く設計が最小かつ D872 と整合する。`run_campaign` と `CampaignLayout` は単独では必要条件ではない。発見関数の境界・返却型・順序は変えない。

ただし、次の 3 点は親 brief の修正または裁定が必要である。

- repo 外束縛は 3 件ではない。少なくとも B-10 系 2 module も既定の repo 外 measurement root を実際に読む。現状は合計 5 module 束縛、3 unique root である。
- marker のない構文不正 `.py` は、現行では `ast.parse` 例外になるが prefilter 後は見逃される。driver 集合の必要条件は破らないが、発見関数全体の例外挙動は完全同一ではない。
- 「全 test source の走査」と「実 repo を prefilter 有無で二重走査する default test」は、いずれも D335 の成長比例禁止と衝突する。後者は bounded fixture 比較と current-set literal pin に分けるべきである。前者には明示的な例外裁定が必要である。

読取り専用のため実装・pytest 実走はしていない。以下は静的検査に基づくプランであり、緑は主張しない。

## 単位 A の実装プラン

対象は [test_p3_exploration_namespace.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_p3_exploration_namespace.py:51) のみ。

- `:51` の `_CAMPAIGN_ROOT` 直後に `_CAMPAIGN_ROOT_LEXICAL_MARKER = "exploration_campaign_layout"` を置く。`run_campaign` と `CampaignLayout` は marker に含めない。後者二つを含む compound 条件も AST 述語の二重実装になるため採らない。

- `_discover_campaign_drivers` (`:131-144`) は次の順へ変える。

  1. `source_text = source.read_text(encoding="utf-8")`
  2. `if use_lexical_prefilter and _CAMPAIGN_ROOT_LEXICAL_MARKER not in source_text: continue`
  3. `tree = ast.parse(source_text)`
  4. 既存 `_is_campaign_root_creator(tree)` 判定
  5. 既存 import と `(stem, module, tree)` append

  `campaign_root`、`import_modules`、返却 tuple、sort 順、import の位置は変えない。比較テスト用に keyword-only `use_lexical_prefilter: bool = True` を追加する。

- `_CAMPAIGN_DRIVERS` (`:147`) は引き続き既定の prefilter 有効経路を module import 時に呼ぶ。`:148-158` の派生 tuple は変更しない。

- `:502` 付近へ `test_campaign_driver_discovery_names_are_pinned` を追加し、発見順を次の test-owned tuple と完全一致させる。

  ```
  p3_autonomous_workload_trial
  p3_kickoff
  p3_s4_loop
  p3_s4_loop_sort
  p3_s4_loop_trigger_gating
  p3_s4_red
  paper_story_a1_paired
  ```

- 同じ付近へ `test_campaign_driver_prefilter_matches_unfiltered_discovery_on_bounded_fixtures` を追加する。`tmp_path` に固定本数の `.py` を置き、production の `_discover_campaign_drivers(..., import_modules=False, use_lexical_prefilter=True/False)` を両方呼ぶ。fixture は最低限、次を含める。

  - `exploration_campaign_layout` + `run_campaign` の正例
  - `exploration_campaign_layout` + `CampaignLayout`、`run_campaign` なしの正例
  - marker がコメントだけにある負例
  - alias import 後に alias 名を呼ぶ負例
  - `getattr` / 文字列結合による負例
  - plain decorator の負例
  - marker が一切ない負例

  両経路の `(name, tree)` 発見名 tuple が完全一致し、正例 2 件だけになることも literal で pin する。性質だけを再実装した stub は作らない。

- 実 repo を unfiltered でも再走査する default test は追加しない。毎回全 campaign file を parse する新しい成長比例テストになるためである。親が既に行った実 repo 完全一致測定を移行時の one-shot evidence とし、default gate は bounded 両経路比較、現行 7 件 literal pin、既存契約簿 exact assertion の三層にする。

遅延化は適さない。`:574-577`、`:1033-1036`、`:1200-1203`、`:1326-1329`、`:1462-1465` の decorator が import/collection 中に各 tuple を必要とする。fixture 化しても decorator 引数には間に合わず、`pytest_generate_tests` も collection 中なので費用は消えない。単一 node 内の loop へ変えれば実行時へ送れるが、driver 別 nodeid、sharding、duration ledger、失敗局所性を変える大改造になる。局所修復は prefilter が妥当である。

`_DRIVER_CONTRACTS` (`:377-468`) と `_driver_contract` (`:471-473`) は変更しない。発見 tuple の形・順序を保つため、既存の次の二重検出も維持される。

- `test_driver_contract_registry_is_exact` (`:502-505`) の完全一致
- 各 consumer の `contracts[name]` と `test_missing_driver_contract_is_hard_failure` (`:549-553`) の `KeyError`

## 単位 A の D872 論証と反例検討

`_call_name` (`:54-59`) が返す対象は `ast.Name.id` または `ast.Attribute.attr` である。したがって、`_is_campaign_root_creator` が `exploration_campaign_layout` call を認識した parse 済み source には、その ASCII identifier token が source text に連続して存在する。字句 marker hit は AST 発見集合の上位集合であり、driver 名や除外対象を指定する述語ではない。

3 識別子の個別判定は次のとおり。

- `exploration_campaign_layout`: 使用可。`:85-90` の外側 `and` により、すべての creator に必須。
- `run_campaign`: 単独使用不可。`CampaignLayout` branch だけで creator になれる。
- `CampaignLayout`: 単独使用不可。`run_campaign` branch だけで creator になれる。

想定反例はいずれも membership 必要条件を破らない。

- 文字列結合した関数名: `getattr(x, "exploration_" + "campaign_layout")()` の外側 call.func は `ast.Call` で、現行 `_call_name` は対象名を返さない。unfiltered 経路にも編入されない。
- alias import: `as layout_fn; layout_fn()` は call 名が `layout_fn` なので unfiltered 経路にも編入されない。import 文に元名が残れば prefilter の false positive になるだけである。
- `getattr` 経由: 同様に現行 AST 述語の発見対象外。
- decorator: `@exploration_campaign_layout` は `ast.Call` ではない。`@exploration_campaign_layout(...)` は source に marker が存在するので prefilter を通る。
- コメントまたは文字列中だけ: prefilter の false positiveになり parse されるが、AST creator 判定で除外される。false negative ではない。

一方、親の「同一性」主張には反例がある。

```python
# marker のない campaign/broken.py
def broken(
```

現行は `ast.parse` が `SyntaxError` を上げて collection を止める。prefilter 後は marker 不在として parse せず、発見関数は成功する。したがって「parse 可能な source に対する driver membership」は同一だが、「発見関数の全 observable behavior」は同一ではない。

D872 決定 1 自体には抵触しないものの、構文検査を暗黙に担っていたなら検出力低下になる。author 投入前に、全 campaign source の構文妥当性が別 gate で保証されているか確認し、なければこの差を受容する裁定が必要である。

## 単位 B の実装プラン

[test_t189_oracle_wiring_slice.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_t189_oracle_wiring_slice.py:38) では次の変更を行う。

- `:43` 付近へ `_pinned_jobs_relative_paths()`、`_missing_pinned_jobs(jobs_root)`、`_require_pinned_jobs(jobs_root)` を置く。
- 必須集合は checked-in slice から production test helper `_slice_value()` を通して導出する。2 task の `catalog_join.prompt`、`catalog_join.receipt`、`relative_to == "jobs-root"` の evidence を集約し、次の 4 unique file と完全一致させる。

  - `T-1222-population-closure/stage2-plan-prompt.md`
  - `T-1222-population-closure/T-1222-population-closure-plan-c7d8a2085d4bacb773d2a1a240801409d1c754541d424fffe87fbf21e1305ff3/receipt.json`
  - `dev-wave-t1393-finish-trial-indeterminate/stage2-prompt.md`
  - `dev-wave-t1393-finish-trial-indeterminate/dev-wave-t1393-finish-trial-indeterminate-plan-8501201db4c59d0a3d53591b3b0c373cccccf2c67159a53b4e9a2c35b2b62a3c/receipt.json`

- `:84` の root-only `skipif` を削除し、`test_optional_jobs_root_audits_pinned_prompt_and_receipt_bytes` (`:85-94`) の本体冒頭で `_require_pinned_jobs(_JOBS_ROOT)` を呼ぶ。
- `Path.exists()` で不在だけを skip する。存在する directory、symlink、内容不正、SHA 不一致は guard で隠さず、従来の verifier に失敗させる。
- root が存在するが 1 file 欠ける正例、全 4 file が存在すれば skip しない正例、要求集合の literal 完全一致テストを同 module に置く。

[test_t1434_t1222_science_slice.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_t1434_t1222_science_slice.py:21) では次の変更を行う。

- `_jobs_descriptors` (`:33-46`) の直後へ `_all_pinned_jobs_relative_paths()`、`_missing_pinned_jobs(jobs_root, relative_paths)`、`_require_pinned_jobs(...)`、registry 用 `_require_all_pinned_jobs(jobs_root)` を置く。
- 全物理検証の要求集合は `_jobs_descriptors(_artifact_value())` から導出する。現在の unique 21 file は以下である。

  - T-1222 の plan prompt/output/receipt、author prompt/output/receipt、`acceptance-receipt-2.json`
  - `dev-wave-t1434-science-slice/stage3-lensA-{prompt.md,md}` と receipt
  - `dev-wave-t1434-science-slice/stage3-lensB-{prompt.md,md}` と receipt
  - `dev-wave-t1434-science-slice/readerA-{prompt.md,md}` と receipt
  - `dev-wave-t1434-science-slice/readerB-{prompt.md,md}` と receipt
  - `dev-wave-t1434-science-slice/oracle-ledger-freeze-v1.json`
  - `dev-wave-t1434-science-slice/projections/oracle-source-bundle.md`

- `_copy_physical_jobs_fixture` (`:49-56`) の冒頭で全 21 file guard を呼ぶ。これで `test_ss_m6...` (`:230-249`) を覆う。
- 全 21 file を読む次の node は本体冒頭で `_require_all_pinned_jobs(JOBS_ROOT)` を呼ぶ。

  - `test_physical_real_jobs_root_is_valid_negative_observation` (`:77`)
  - `test_ss_m4_stored_coverage_tampering_is_rejected` (`:209`)
  - `_copy_physical_jobs_fixture` 経由の `test_ss_m6...` (`:230`)

- reader-A output だけを読む次の node は、その 1 file のみを guard する。無関係な 20 file の不在で skip させない。

  - `test_reader_table_rejects_missing_duplicate_extra_and_bad_verdict` (`:293`)
  - `test_reader_markdown_rejects_duplicate_blindness_attestation` (`:315`)
  - `test_reader_markdown_rejects_markdown_equivalent_duplicate_attestation` (`:337`)

- `test_physical_rejects_symlink_component` (`:374-383`) は guard しない。`:378` の外部 path は symlink の文字列 target として使われ、target を読む前に symlink component を拒否する負例である。外部内容の実在はテストの前提ではない。

skip 理由は例えば次とする。

> `pinned repo-external jobs inputs unavailable; missing exact files: ...; absence guard only—the complete input set still runs all physical assertions`

「root 不在」ではなく欠けた relative path を列挙し、完全な場合は全 assertion が走ることを明記する。既存期待値は一切変えない。

## 単位 B のメタ gate 設計

新規 `orchestrator/tests/external_path_bindings.json:1` を登録簿とする。Python source に置かないのは、source scanner が登録簿自身の absolute path を再発見する自己参照を避けるためである。

各実束縛 row は最低限次を持つ。

- `classification: "external-resource"`
- `absolute_path`
- `test_module`
- `root_symbol`
- `guard_function`
- `requirements_function`
- `absence_policy: "skip-only-when-required-content-is-missing"`

非束縛 literal は次を持つ。

- `classification: "inert-literal"`
- `absolute_path`
- `test_module`
- `reason`

consumer は新規 `orchestrator/tests/test_external_path_bindings.py:1` とし、登録簿 schema、source scan 完全一致、requirements 完全一致、実 guard の skip を検査する。各対象 module は既存の module-local guard test も持つ。

メタ gate (a) は次の構造にする。

- `orchestrator/tests/test_*.py` を列挙する。
- source text に `/home/`、`/work/`、`~/` がなければ AST parse を省く。
-残りを `ast.parse` し、空白を含まない `^(/home/|/work/|~/)\S+$` の `ast.Constant[str]` を `(module, literal)` で集める。隣接文字列は AST が結合した完全 path として扱う。
- 発見集合と registry の `external-resource ∪ inert-literal` を完全一致させる。
- external-resource row は guard/function field が全て非空、inert row は guard を持たず理由が非空であることも閉じる。

静的確認した現在の対象は 19 `(module, literal)` である。例示された誤検出は次のように分類できる。

- `test_hooks.py:1096` の `~/t956-repo/...`: `expanduser` 防護を試す入力データ。
- `test_t316_sandbox_probe.py:962` の `/home/tester/...`: 注入 receipt の同一 target 値。
- `test_real_repo_serialization.py:5399` の `/home/u/x`: synthetic mountinfo の disk 判定データ。
- `test_codex_reasoning_ab.py:397`、`test_paper_story_a1_paired.py:873`、`test_paper_story_a2_certification.py:2464`、`test_mocc_trace_pair.py:256,403,413`、`test_pegasus_tools.py:427,461` も byte fixture または checked-in contract literal で、test process はその path を読まない。

一方、次の 5 module row は実束縛である。

- `test_codex_reasoning_ab.py` → `/home/SFC/tanab/.codex/sessions`
- `test_t189_oracle_wiring_slice.py` → `/work/1/SFC/tanab/dev-wave-jobs`
- `test_t1434_t1222_science_slice.py` → 同上
- `test_b10_extended_figure_provenance.py` → `/work/1/SFC/tanab/b10-backoff-grid-runs5`
- `test_plot_b10_extended_backoff.py` → 同上

したがって B-10 2 module を scope に加え、内容 guard を実装しない限り、この exact gate は意図どおり赤になる。3 件だけを登録して gate を通す設計は不可である。

メタ gate (b) は registry の各 external-resource rowで parameterize する。module と guard 名を文字列から import/resolve し、`tmp_path / "nonexistent-root"` を実 guard に渡して `pytest.skip.Exception` を要求する。stub guard や guard 判定 helper の差替えはしない。ID は module basename に固定する。

この正例だけでは root-only guard も通る。そこで各 module の「root directory は存在するが、要求 file が 1 件欠ける」test を必須とする。完全な file set では skip しない対照も置く。これで metagate が恒真になるのを防ぐ。

新規 test file には `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))` を置く。これにより README allowlist 編集は不要だが、全 `test_*.py` を列挙する [test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_plain_runner_coverage.py:44) の次の 2 nodeを焦点走へ含める。

- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_allowlist_has_no_stale_or_self_runnable_entries`

## 編集面の素集合性と consumer 波及

単位 A と、修正後の単位 B は編集面が素集合である。

- 単位 A: `test_p3_exploration_namespace.py`
- 単位 B: `test_t189_oracle_wiring_slice.py`、`test_t1434_t1222_science_slice.py`、新規 registry JSON、新規 metatest
- 全数性を守るための追加 scope: B-10 test module 2 本と、必要なら B-10 共通 test-support manifest

新規 metatest は A の source を走査するが、A file を編集しないため編集競合ではない。B-10 追加も A とは重ならない。B 全体は registry・guard・metagate が一つの契約なので、分割せず一人の author に持たせるべきである。

変更予定はすべて test または test-support file で、production file は変更しない。したがって「変更する production module 名を `orchestrator/tests/` から検索した consumer test」の集合は空である。`tools.t189_oracle_wiring_slice` と `tools.t1434_t1222_science_slice` は利用するが変更対象ではない。

親が実走する焦点対象は次である。

- `orchestrator/tests/test_p3_exploration_namespace.py`
- `orchestrator/tests/test_t189_oracle_wiring_slice.py`
- `orchestrator/tests/test_t1434_t1222_science_slice.py`
- 新規 `orchestrator/tests/test_external_path_bindings.py`
- `orchestrator/tests/test_plain_runner_coverage.py`
- scope 修正後は B-10 2 module

## 変異事前登録の候補

- A-prefilter 必要条件変異: `_CAMPAIGN_ROOT_LEXICAL_MARKER` を `"run_campaign"` へ 1 箇所変更する。`CampaignLayout` だけの bounded fixture と `p3_autonomous_workload_trial` が落ちるべきである。期待赤 node 集合:

  - `test_campaign_driver_prefilter_matches_unfiltered_discovery_on_bounded_fixtures`
  - `test_campaign_driver_discovery_names_are_pinned`
  - `test_driver_contract_registry_is_exact`

- A-literal pin 変異: expected 7-tuple の `p3_kickoff` を 1 文字変更する。期待赤は `test_campaign_driver_discovery_names_are_pinned` のみ。

- D872 hard-fail 変異: `_driver_contract` の `contracts[name]` を `contracts.get(name)` に変える。期待赤は既存 `test_missing_driver_contract_is_hard_failure` のみ。prefilter 変更後もこの発火を維持する。

- t189 内容 guard 変異: missing 判定を `if not jobs_root.is_dir()` に置き換える。期待赤は新規 `test_physical_jobs_guard_reports_missing_file_under_existing_root` のみ。root-only guard の偽実装を直接殺す。

- t1434 内容 guard 変異:同じく root-only 判定へ置換する。期待赤は新規 `test_physical_jobs_guard_reports_missing_file_under_existing_root` のみ。

- requirements 変異: t189 の receipt 1 件、または t1434 の reader-A output 1 件を requirements factory から除く。期待赤は各 module の `test_physical_jobs_guard_requirements_are_exact` と registry requirements exact node。期待値を同じ factory から導出してはならない。

- registry scan 変異: `test_t316_sandbox_probe.py` に新しい `/home/tester/unregistered-binding` literal を 1 件足す。期待赤は `test_machine_bound_path_literal_registry_is_exact` のみ。

- guard 発火変異: t189 `_require_pinned_jobs` の `pytest.skip(...)` を `return` にする。期待赤:

  - t189 module-local missing-file guard test
  - `test_registered_external_guard_skips_missing_root[test_t189_oracle_wiring_slice]`

- registry row 削除変異: t189 row を JSON から削除する。source literal は残るため、期待赤は `test_machine_bound_path_literal_registry_is_exact`。parameter row 自体が消えることを利用した偽緑にはならない。

scanner main gate は実 repository source と registry の比較であり stub ではない。補助として、tmp source から `/home/...` を抽出できる scanner 単体正例を置いてよいが、それだけを main gate の代替にしてはならない。

## 主張してよい範囲と、してはいけない範囲

主張してよいのは次だけである。

- 現況では当該 module collector が file collector 合計の 27.4%を占める。
- 親の単一-process component probe では discovery scan が `1.676 s → 0.245 s`、85.4%削減された。
- marker hit 13 に対して AST 発見 7 であり、現在の parse 可能な source 上では発見集合が一致した。
- 実装後の効果は同じ collection 計測を再実走し、`(旧 file collector 合計 - 新 file collector 合計) / 旧合計` の比率で報告する。
- 85.4%を module collector 全体へ機械的に掛けた約 23.4 percentage point は上限寄りの試算にすぎず、実測結果としては扱わない。

主張してはいけないのは次である。

- 48 worker × 3 shard の acceptance wall が何秒短くなるか。
- 145 回分の単一-process savings を足し合わせた wall 改善。
- collection 約 51.7 秒が同じ比率で減ること。
- acceptance が 5 分以内になること。
- CPU、Lustre metadata、memory bandwidth contention のどれが縮むか。
- pytest が緑であること。
- 構文不正 source を含む場合まで発見関数の observable behavior が完全同一であること。

## 親 brief への異議

1. 「repo 外束縛の全数は 3 件」は破れている。[test_b10_extended_figure_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_b10_extended_figure_provenance.py:21) は `:221`、`:287`、`:308` などで既定 measurement root の内容を読む。[test_plot_b10_extended_backoff.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-loop-liveness-repo-external/orchestrator/tests/test_plot_b10_extended_backoff.py:15) も `:148` で同 root を `load_measurements` へ渡す。両 module は acceptance duration ledger にも node が存在し、hold 登録は見つからなかった。Unit B の scope をこの 2 file まで広げる必要がある。

2. P3 の必要条件論証は「parse 可能な source の発見集合」については成立するが、marker のない構文不正 file を現行だけが落とす反例を扱っていない。別 syntax gate を確認できなければ、検出力変更として親裁定が必要である。

3. 実 repo の prefilter 有無比較を default test にすると、新しい file 数比例 scan になる。D335 に従うなら bounded production-function 比較と current 7 literal pin に分け、実 repo unfiltered 比較は one-shot 移行検査に限定すべきである。

4. repo 外 literal の完全走査も file 数比例であり、D335 と形式上衝突する。P2 の「新設してよい gate」は gate 数の裁定であって、成長比例費用の例外を逐語的には与えていない。author 投入前に例外を明示すべきである。

5. 「すべての絶対 path literal」を字義どおり走査すると、現在 995 unique `(module, literal)` があり、大半は `/tmp`、`/fixture`、`/proc`、架空 path、JSON pointer である。提案 scanner は現事故と例示に対応する `/home/`、`/work/`、`~/` の machine-bound literal へ対象を明記する。これを「全 repo 外依存」と呼ぶのは過大主張であり、`/mnt/...` 等を将来検出する一般保証にはならない。