## 項目 1

### (a) 入力集合の性質

判定は **設計上限がある**。

`load_claude_inventory()` は `.claude/agents/*.md` を列挙して全件を parse する (`orchestrator/codex_roles/spec.py:320-331`)。`load_role_specs()` は manifest の role 集合との全単射 (`:528-537`)、全 review ledger との一致 (`:538-541`)、現在の絶対数 `EXPECTED_ROLE_COUNT` (`:542-548`) を検査する。

「13」の pin の実体は次であり、親の確認点自体は正しい。

- `CCA.STATIC_ADAPTERS` の件数が 13 (`orchestrator/tests/test_codex_agents.py:121-124`)
- `load_role_specs(_REPO)` の role 件数が 13 (`:127-130`)
- role 集合が各 SHA・schema・I/O ledger の key 集合と一致 (`:131-135`)
- production の `EXPECTED_ROLE_COUNT = 13` (`orchestrator/codex_roles/review_ledger.py:13`) と、その照合 (`orchestrator/codex_roles/spec.py:542-548`)

ただし、13 は永久定数ではなく、role 増減時には ledger の明示更新を要求する review pin である (`spec.py:547`)。したがって D463 の正確な分類は「非比例」ではなく、**比例だが設計上限のある固定用途集合**である。通常の無関係な repository 成長では増えず、承認された role 追加時だけ統制された段差で増える。

### (b) 悪い側

判定は **neither**。ただし三択中の「比例ではない」という説明は D463 と整合しない。正確には「D463 の第三区分であり、テスト側にも対象側にも是正対象となる欠陥がない」である。

各テストは全 role に対する全称命題を検査しており、入力を一部に縮めると未検査 role が生じる。production も manifest、Claude source、review ledger の全単射を fail-closed に検査する必要がある。

wave 606 とも整合する。既存記録は既に `growth_real_bounded_step` と分類している (`output/insights/2026-08-16_t1222-growth-hold-sweep/README.md:84-87`)。同記録は「非比例」から「比例だが設計上限あり」へ訂正済みである (`:98-100`)。したがって新たに「非比例」へ戻す分類訂正は誤りになる。

### (c) 直し方

コード・テストは変更しない。これは保留ではなく、欠陥なしという最終裁定である。既存 insight や archive は歴史記録なので書き換えず、段 7 の新規 worklog fragment に「D463 第三区分、恒久保留なし、実装差分なし」と記録する。

7 node の現在の拒否経路はそのまま残す。

- `test_policy_has_zero_native_and_thirteen_static_dormant_adapters` (`test_codex_agents.py:121-124`): native active 非空、static adapter の 13 件 pin、role 集合不一致。
- `test_review_ledger_independently_pins_all_thirteen_sources_and_io_contracts` (`:127-156`): source・description・schema・manifest SHA、I/O required field の drift。
- `test_current_sources_render_byte_exact_and_native_is_empty` (`:159-161`): render byte drift、native TOML の出現。
- `test_all_adapters_pin_model_policy_and_blocked_runtime_activation` (`:164-213`): model/effort drift、runtime activation、review ledger、input/consumer policy の緩和。
- `test_source_body_is_embedded_exactly_once_before_product_override` (`:216-230`): source body の欠落・重複・override より後への移動。
- `test_claude_tool_capabilities_are_lowered_without_runtime_tool_claim` (`:233-249`): tool と capability mapping の非全単射、runtime claim の混入。
- `test_any_native_discovery_toml_is_rejected` (`:252,255,261`): `auditor.toml`、`planner-v4.toml`、未知の `mystery.toml` をすべて拒否。

### (d) 検出力の証明

分類根拠の mutation anchor は `orchestrator/codex_roles/spec.py:544-548` の絶対件数検査を無効化する変異とする。

期待赤は `orchestrator/tests/test_codex_agents.py:1312` の `test_lockstep_role_deletion_is_rejected_by_absolute_count_floor`。同期して role と ledger を削った入力が拒否されなくなり、finding を要求する assert (`:1329-1331`) が failure になる。既定 skip も `xdist_group` もなく、collection error ではない。

## 項目 2

### (a) 入力集合の性質

判定は **増える**。

fresh child の script は `orchestrator.tests.test_dev_waves_integration` 自身を import する (`orchestrator/tests/test_dev_waves_integration.py:2050-2054`)。`orchestrator` と `orchestrator/tests` に `__init__.py` はなく namespace package なので、主要な比例源は package 初期化ではなく、2726 行ある test module 全体の parse・compile・top-level import 閉包である。新しい integration test や import が同 file に追加されるたび入力 byte と import 閉包が増える。

### (b) 悪い側

判定は **test-side**。

child が必要とするのは `_serve_child_main()` の workload と結果 envelope だけであり、親側の全テスト、parser test、timeout test、残りの integration corpus を import する必要はない。

### (c) 直し方

変更前は `:2051-2054` が巨大な test module を importして `_serve_child_main()` を呼ぶ。

変更後は次の形にする。

- 新規 `orchestrator/tests/_dev_waves_serve_child.py:1` に、現在の `_serve_child_payload` (`test_dev_waves_integration.py:1817`) と `_serve_child_main` (`:2019`) および child 側だけの依存閉包を移す。
- 新 helper から `test_dev_waves_integration` への逆 import を禁止する。
- `test_dev_waves_integration.py:2051-2054` は新 helper の `main()` だけを importする script に置換する。
- 親側の envelope parser (`:1829-1916`)、timeout・SIGTERM/SIGKILL・reap (`:2055-2150`)、SKIP/FAIL 変換 (`:2152-2161`) は維持する。
- `test_socket_roundtrip_works_beyond_108_byte_repository_path` (`:2165-2167`) は削除も skip もせず、そのまま fresh child を起動する。

これにより、長い repository path での socket roundtrip、child crash、非 canonical envelope、timeout、reap 失敗、SKIP/FAIL の全拒否経路が残る。

### (d) 検出力の証明

`test_dev_waves_integration.py` に、`xdist_group` を付けない新規 node `test_serve_child_entry_import_closure_excludes_integration_module` を追加する。

fresh subprocess で新 helper を importし、実際の `sys.modules` に `orchestrator.tests.test_dev_waves_integration` が存在しないことを child の終了コードで検査する。親側は `assert completed.returncode == 0` とし、error ではなく failure にする。

変異は次のどちらかとする。

- `:2052` 相当を旧 self-import に戻す。
- 新 helper に `test_dev_waves_integration` の逆 import を追加する。

期待赤は上記新規 node。既定実行され、`xdist_group` に属さない。DW-O13 に従い、文字列だけでなく fresh child の実 `sys.modules` を anchor にする。

## 項目 3

### (a) 入力集合の性質

判定は **増える**。

`LIVING_DOCS` は手書き集合 (`tools/check_docs.py:47-78`) に runbook glob (`:84-87`) を加え、`main()` は全件を巡回して本文全行を検査する (`:5258-5324`)。living doc の追加と本文量の増加に応じて入力が増える。

### (b) 悪い側

判定は **test-side**。P3 は real である。

この node が必要とするのは `PREREG_DOC` についての本番 `main()` 読取経路と、二つの negative control だけである。実 inventory への登録は直前の独立 node が `LIVING_DOCS` と `_ENUMERATED_DOCS` の両方を pin している (`test_s8c_preregistration_invariant.py:336-339`)。

したがって test 内で `LIVING_DOCS` を singleton にしても、失われるのは無関係な文書の再検査だけである。`check_docs.main()` 自体、`_safe_read_text`、finding 集約、rc 変換は引き続き通る。

### (c) 直し方

`test_s8c_preregistration_invariant.py:358-359` を次の順にする。

- `monkeypatch.setattr(check_docs, "LIVING_DOCS", [PREREG_DOC])` を追加。
- 現在どおり `_safe_read_text` を `dirty_safe_read` に差し替える。
- 現在どおり `check_docs.main()` を呼ぶ。

`_ENUMERATED_DOCS` は変更しない。実 list への所属検査は `:336-339` が担当する。

拒否経路はすべて残る。

- `PREREG_DOC` が実 inventory から外れると `:338` が failure。
- enumerated pin から外れると `:339` が failure。
- main が対象を読まないと `injected` の assert (`:361`) が failure。
- 不在 path が通ると `PATH_REF` finding (`check_docs.py:5318-5324`) を要求する `:363` が failure。
- 腐敗行番号が通ると line reference finding (`check_docs.py:5285-5291`) を要求する `:364` が failure。

### (d) 検出力の証明

二つの production mutation を事前登録する。

- `check_docs.py:5318-5324` の不在 path finding を無効化する。
- `check_docs.py:5285-5291` の行番号 finding を無効化する。

どちらも期待赤は既存の `test_s8c_living_doc_reference_negative_controls` (`test_s8c_preregistration_invariant.py:342`)。それぞれ `:363`、`:364` の assert failure になる。対象 node は既定 skip されず、`xdist_group` にも属さない。

singleton 修正自体の anchor は `[PREREG_DOC]` を `[]` に変える変異で、同 node の `:361` が failure になる。

## 項目 4

### (a) 入力集合の性質

現状の判定は **増える**。

`_scope_policy_commit()` は暗黙の current HEAD に対して `git log -S "scope="` (`tools/check_ai_provenance.py:1170-1175`)、`_implementation_policy_commit()` も同様に全到達史を検索する (`:1178-1184`)。`_audit_history()` は selected commit が一件でも両方を無条件に呼ぶ (`:1600-1606`)。

一方、対象テストの実質入力は固定 commit である。

- `3f2c43d...^!` 一件 (`test_check_ai_provenance.py:2680-2686`)
- `6b64d217...` と固定された二親 (`:2699-2717`)

current HEAD の後続 commit はこれらの判定に不要である。

### (b) 悪い側

判定は **target-side**。ただし P2 の「履歴上不変の定数」という理由は誤りである。

`git log` は current HEAD から到達可能な履歴を検索するため、rebase、履歴再構築、policy 導入 commit の置換、別 tip からの実行によって戻り値は変わりうる。単純 memoize は一 process 一回の全史走査を残し、repository 成長比例を消さない。さらに `REPO` を差し替える unit test では無条件 cache が stale result を返す危険がある。

対象側の実際の欠陥は、固定 selected commit を既に受け取っているのに、policy 探索 revision を暗黙の HEAD に固定している点である。

### (c) 直し方

`tools/check_ai_provenance.py` を次の形にする。

- `:1170` を `_scope_policy_commit(revision: str = "HEAD")` に変更し、`git log` の pathspec 前へ `revision` を渡す。
- `:1178` も `_implementation_policy_commit(revision: str = "HEAD")` に変更する。
- revision が不正・不在の場合は HEAD へ fallback せず、現行どおり Git 失敗を上へ伝播して `main()` の rc=2 経路 (`:2619-2621`) に入れる。
- `_audit_history():1603-1606` は、selected commit が一件ならその commit を policy revision とし、複数件では現行の `"HEAD"` を維持する。空集合の early return は維持する。
- `test_forward_correction...:2718-2721` は両 resolver に `spec.target` を明示する。
- `test_ledgered...:2680-2686` では両 resolver を wrapper し、受け取った revision が固定 `commit` であることを assert してから元関数へ委譲する。

静的確認では、現履歴の scope epoch `2f0245c196f82dddef91a9966e19b78a4b3f62e9` と implementation epoch `8c6d3f3bdc716c1ede8febb83ced1b0351a99118` は、二つの固定 target のどちらにも ancestor である。修正後は同じ epoch を固定祖先閉包から得るが、将来の HEAD 追加では入力集合が増えない。

二つの拒否経路は維持される。

- ledger node (`:2680-2696`): malformed trailer が `missing-ai-agent` の既知違反一件としてのみ受理され、registry drift、finding 消失、余分な stderr、rc 変化を拒否。
- forward-correction node (`:2699-2729`): target literal、correction key/payload、二親 merge、target の trailer/correction 不在、通常 finding が exact `missing-ai-agent` 一件、candidate count 0 を pin。

### (d) 検出力の証明

`test_ledgered_3f2c43d7580b_is_known_and_rc0` に入れる resolver wrapper を mutation anchor にする。

変異は `_audit_history():1605-1606` のどちらかを引数なし呼出し、または `"HEAD"` 呼出しへ戻すこと。wrapper の `assert revision == commit` が失敗する。

期待赤は既存の `test_ledgered_3f2c43d7580b_is_known_and_rc0`。既定 skip も `xdist_group` もなく、AssertionError は pytest failure として記録される。

## 親 brief への反論

- **P1: refuted。ただし no-edit 結論は real。** 「非比例」は D463 の語義に反する。正しくは設計上限のある第三区分である。13 pin は実在するが変更不能な永久上限ではない。wave 606 も同じ `growth_real_bounded_step` としており、保留却下とは整合するが、「非比例」への再分類とは整合しない。
- **P2: refuted。ただし target-side 判定は real。** resolver の値は rebase・履歴再構築で変わる。memoize では比例を消せない。固定 selected commit を policy 探索 revision に使うのが修正点である。
- **P3: real。** `LIVING_DOCS` を `[PREREG_DOC]` に縮めても `check_docs.main()` 自体は通る。実 inventory 所属は直前の独立 node が守るため、main 経路の検出力は失わない。
- **P4: real と確定。** 比例源は namespace package ではなく、`:2052` が fresh child で巨大な test module 自身を importすること。test-side helper 分離で除去できる。

## 実装単位の分割

段 5 の編集面は次の素集合に分ける。

- 項目 2 worker:
  - `orchestrator/tests/test_dev_waves_integration.py`
  - 新規 `orchestrator/tests/_dev_waves_serve_child.py`
- 項目 3 worker:
  - `orchestrator/tests/test_s8c_preregistration_invariant.py`
- 項目 4 worker:
  - `tools/check_ai_provenance.py`
  - `orchestrator/tests/test_check_ai_provenance.py`
- 項目 1:
  - 段 5 worker なし。親が段 7 で専用 worklog fragment に最終分類を記録する。既存 insight・archive は編集しない。

結合後、親が対象 11 node、新規 mutation anchor、関連 file 全体を `tools/run_tests.py` 経由で実測する。さらに `tools/check_codex_agents.py` と `tools/check_docs.py` を実行する。

## 総括

項目 1 は D463 の「比例だが設計上限あり」であり、保留も実装修正も不要である。項目 2 と 3 は test-side、項目 4 は selected revision を無視する target-side が原因である。項目 2 は child helper 分離、項目 3 は `LIVING_DOCS` の singleton 化、項目 4 は policy 探索を固定 selected commit の祖先閉包へ束縛する。11 node はすべて残し、恒久保留も production 緩和も導入しない。pytest は実行しておらず、緑は主張しない。