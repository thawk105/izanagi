## 総括

親の「3 系統 6 hit だけ」は **real な誤り**である。planner SHA は `test_reflux_originless_compatibility.py:372` に 7 回あり、実際は coder 3 出現、planner 10 出現、合計 13 出現である。  
ただし `s1-addendum.md` と `s2-plan.md` が追加した T-2249 baseline 追随 helper まで含めれば、静的に確認できた bytes pin 閉包は閉じる。追加の xdist・行数・byte 数・adapter 全体 SHA pin は見つからなかった。  
4 定数を動かさない判断と新 source・semantic・adapter SHA は正しい。再生成コードも repo root なら動くが、Python の直接書込みではなく renderer を読取り oracle として `apply_patch` で適用すべきである。  
最大の残件は、完全協調 rollback が生存する P2 と、`last_delta_pct: null` を今も指示する 2 本の live runbook である。

## pin 閉包の検算 (漏れの file:line)

- **real — planner の独立 golden を落としていた。** `orchestrator/tests/test_reflux_originless_compatibility.py:372` の `_PRE_WAVE_ORIGINLESS_BASELINE` は旧 planner SHA を `journals/*/*/provenance/role_file_sha256` に 6 回、`reports/*/cells/*/generations/*/roles/planner/provenance/role_file_sha256` に 1 回、計 7 回保持する。巨大 JSON が物理 1 行なので `git grep -c` はこれを `1` としか数えない。  
  成果物影響: certified 選択値は変えないが、材料レポートの pin 閉包は「3 系統」から「planner の originless 独立 golden を含む 4 系統」へ訂正し、試行台帳の受理 SHA を旧値から新値へ 7 leaf 分追随させる。

- **real — exact 値の実数は 6 hit ではない。** `git grep -o` と個別 `grep -o | wc -l` の実測では、coder 旧 SHA は adapter 2 + ledger 1 = 3 出現、planner 旧 SHA は adapter 2 + ledger 1 + baseline 7 = 10 出現である。  
  成果物影響: 材料レポートは「13 literal 出現」と記録する。試行台帳側の変更対象は planner の 7 leaf だけで、coder の保存済み trial provenance は動かない。

- **refuted — addendum 後にも別の bytes pin が残る、という疑い。** 次を非 archive repo と `output/` に対して実測した。

  - 旧 source SHA、旧 semantic digest、現 adapter 全体 SHA の `git grep -n/-o`
  - role 名、対象 4 path、`last_delta_pct`、`delta_pct` の `rg`
  - `xdist_group` の `orchestrator/tests/` と `pytest.ini` 検索
  - 現行 byte 数 2833、2771、9719、8532、行数、adapter 全体 SHA を対象 role 名と組み合わせた検索

  `review_ledger.py:25,41`、adapter の対象 field、planner baseline 以外に、対象 bytes を固定する literal pin は出なかった。`ROLE_MANIFEST_SHA256`、`DESCRIPTION_SHA256`、`SCHEMA_SHA256`、`ROLE_IO_CONTRACTS`、`policy.py` の role 名 key、checker の `_SOURCE_EXAMPLE_PARITY_ROLES` は role 名を key にするが本文 bytes の pin ではない。  
  成果物影響: corrected plan の pin 受理集合に追加する bytes 台帳はない。材料レポートには検索対象集合と hit 0 を明記すればよい。

- **refuted — xdist group、行番号、行数、byte 数、adapter 全体 SHA の隠れ pin。** `test_codex_agents.py` と originless test に `xdist_group` はなく、現 adapter SHA `774080...` / `feeb6e...` は adapter 自身以外の repo・`output/` に出現しなかった。  
  成果物影響: certified 選択、材料レポートの参照先、試行台帳の受理集合はいずれも追加変更なし。

## 動く hash / 動かない hash の検算

- **real —動く source SHA。**

  - coder: `4073ac...` → `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806`
  - planner: `089364...` → `523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4`

  `spec.py:582-590` が role file 全 bytes を直接 hash して `SOURCE_FILE_SHA256` と比較する。  
  成果物影響: 材料レポートと未来の planner 試行台帳は新 SHA を参照する。現行 trial の coder は `p3_autonomous_workload_trial.py:263-265` の trigger-gating role なので coder 試行台帳値は変わらない。

- **refuted — `ROLE_MANIFEST_SHA256` が動く。** `spec.py:566-577` の preimage は manifest の role entry だけで、role Markdown 本文は含まない。  
  成果物影響: certified 選択、材料レポートの manifest pin、試行台帳参照は不変。

- **refuted — `DESCRIPTION_SHA256` が動く。** `spec.py:584-593` は frontmatter から得た `source.description` だけを hash する。  
  成果物影響: description pin と受理集合は不変。

- **refuted — `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` が動く。** `spec.py:550-557` は `DEVELOPER_INSTRUCTION_TEMPLATE` 自身だけを hash する。本文は後段の `{body}` へ入る。  
  成果物影響: template pin は不変。材料レポートでは本文埋込みの変更と template 変更を分離できる。

- **refuted — `SCHEMA_SHA256` が動く。** `spec.py:655-672` の preimage は manifest schema。実物は coder の `whiteboard={"type":"array"}`、planner の `current_perf={"type":"object"}` で内部が open である。  
  成果物影響: schema pin と logical input の受理集合は不変。これは同時に、例中の `delta_pct` 値や `last_delta_pct` 不在を shape test が守らないことも意味する。

- **real — `semantic_digest` は動く。** `spec.py:745-792` は `SOURCE_FILE_SHA256` を `:771`、本文を `:790-791` でそれぞれ preimage に入れる。in-memory で再導出した値は coder `4e8cd61c...500150`、planner `8721278d...5bdfb` で plan と一致した。  
  成果物影響: adapter の意味 digest だけを新値へ更新する。既存 certified 選択や過去 journal は遡及変更しない。

- **real — adapter の差分は両 role とも 4 JSON pointer だけ。** in-memory の旧新 JSON 比較で `/developer_instructions`、`/review_ledger/source_file_sha256`、`/semantic_digest`、`/source/sha256` のみだった。adapter 全体 SHA は coder `70cb1be6...b54a`、planner `1b094960...31ea`。新 byte 数は coder 9719、planner 8501。  
  成果物影響: 材料レポートの expected bytes と受理集合はこの 4 pointer、新 SHA、新 byte 数へ更新する。

## adapter 再生成手順の実効性

- **refuted — import、cwd、root の食い違いで動かない。** repo root からなら stdin Python の `sys.path[0]` は cwd、`root=Path.cwd().resolve()` と `expected_adapters(root)` の `_repo(root)` は同じ絶対 path になる、`render_adapter()` は `spec.py:803-805` で root を意図的に使わない。`target` key と `expected` key も一致する。ledger 更新前は `spec.py:587-590` で止まり、更新後にだけ生成できるという順序も正しい。  
  成果物影響: expected adapter bytes、新 source pin、材料レポートの生成手順は plan の順序で確定できる。試行台帳には影響しない。

- **real — verbatim 手順の Python 直接書込みは採用しない方がよい。** `tools/check_codex_agents.py --write` の禁止を意味上迂回してはいない。checker 自身も `:354-355` で「renderer の期待 bytes を review して apply」と指示する。ただしこの Codex の file 編集契約では Python による repo file 書込みを使わず、renderer は読取り oracle とし、対象 4 field を `apply_patch` で反映して最後に expected bytes と比較すべきである。  
  成果物影響: 生成される adapter bytes と受理集合は同じだが、材料レポートの実行手順を「Python write」から「renderer で導出、patch で適用、byte 比較」へ変更する。

- **refuted — repo 内に新 script/probe が必要。** `expected_adapters()` と `render_adapter()` だけで必要 bytes と hash を導出できる。新しい tracked generator は不要。  
  成 影響: certified 選択、試行台帳、実装 file 集合は増えない。

- **real — D95 の実装面は addendum の 6 file 中 4 file。** `.codex/role-adapters/*.json` 2 件、`review_ledger.py`、originless test が実装面で、role Markdown 2 件は非実装面である。brief の「3 file が実装面」は baseline 追加後には古い。  
  成果物影響: 材料レポートと provenance は 4 implementation path を Codex author commit に束縛する。certified 選択と trial 値は変えない。

## consumer test の漏れ (nodeid)

- **real — source pin、adapter drift、`--write` 禁止の negative control が focused 集合から漏れている。**

```text
orchestrator/tests/test_codex_agents.py::test_claude_body_or_description_drift_requires_independent_ledger_review
orchestrator/tests/test_codex_agents.py::test_adapter_byte_drift_and_runtime_claim_injection_are_rejected
orchestrator/tests/test_codex_agents.py::test_write_mode_does_not_create_native_or_adapter_files
```

  `review_ledger`、adapter path、checker を直接参照し、今回依存する三つの機構を独立に検査する。安全なのは `test_codex_agents.py` を file 全体で走らせること。  
  成果物影響: certified 選択値は変えないが、材料レポートの focused 受理集合を 3 node 追加または file 全体へ拡張する。

- **real — runtime consumer の通常確認が漏れている。** `.codex/agents/README.md:94-97` は `test_codex_agents.py` と `test_codex_role_runtime.py` を組で通常確認に指定する。少なくとも次の 2 node は `launcher -> spec -> load_role_specs` を通り、全 role source pin を load する。

```text
orchestrator/tests/test_codex_role_runtime.py::test_launcher_uses_actual_adapter_and_rejects_schema_invalid_input
orchestrator/tests/test_codex_role_runtime.py::test_command_keeps_legacy_readonly_layer_and_disables_surfaces
```

  成果物影響: material report の consumer 参照へ runtime adapter load を追加する。runtime は blocked のままで、certified 選択と trial ledger は不変。

- **real — live planner producer と delta 防壁の consumer が漏れている。**

```text
orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_metric_payloads_convert_only_percent_fields
orchestrator/tests/test_p3_autonomous_workload_trial.py::test_freshness_wraps_delta_pct_leak_with_cause
orchestrator/tests/test_p3_s4_loop.py::test_loop_state_roundtrip
```

  前者は `current_perf` の exact key 集合に `last_delta_pct` がないこと、後二者は保存・trial freshness 経路でも `delta_pct is None` であることを検査する。  
  成果物影響: planner の未来 trial payload と provenance を材料レポートへ結ぶ。既存 certified 選択値は不変。

- **refuted — role 名・path の全 grep hit を focused test に入れる必要がある。** `test_effort_levels.py::test_role_manifest_reasoning_policy_is_subset_of_repo_policy` は不変な effort 定数だけ、`test_run_tests_task_run.py::test_check_wrapper_executes_only_fixed_argv` は固定 argv だけ、`test_hooks.py::test_agent_all_project_roles_pinned` は不変な frontmatter だけを見る。今回の本文・hash 差分には非識別的である。  
  成果物影響: これらを省いても今回の certified 選択、材料レポートの意味受理集合、trial ledger は変わらない。

## 変異候補の再照準案 (期待 node 完全集合付き)

- **real — M1-C は単一理由で */}
  ではない。adapter 内で本文、ledger source pin、source SHA、semantic digest の 4 pointer が同時 drift し、byte parity、ledger metadata、body embedding の三層が赤になる。plan の期待 node 集合自体は正しいが、DW-M01 の証拠には使えない。  
  成果物影響: mutation ledger では M1-C を「冗長検出、単一理由性なし」へ変更し、KILLED の単独帰属から外す。

- **real — M1-P はさらに不適格。** 上の三層に originless baseline mismatch が加わる。adapter drift と live planner provenance drift は別理由である。  
  成果物影響: mutation ledger の期待 4 node は維持しても、単一理由の KILLED 判定には使わないe's
  ない。

- **real — M2 は二層、M3 も二層。** M2 は byte parity と exact body embedding、M3 は byte parity と adapter ledger equality が同時に拒否する。  
  成果物影響: M2/M3 は redundant-gate 記録へ移し、certified 選択を守る単独変異証拠から外す。

- **refuted — M4、M5、M6 の単一理由性。** これは成立する。期待 node 完全集合は次のとおり。

```text
M4-C / M4-P:
  orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty

M5-C / M5-P:
  orchestrator/tests/test_codex_agents.py::ea
  test_current_sources_render_byte_exact_and_native_is E
  _empty

M6:
  orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key4
  _set
```

  M4/M5 は各 1 field の renderer parity、M6 は baseline overlay だけが理由になる。  
  成果物影響: mutation ledger の certified KILLED 集合は M4-C/P、M5-C/P、M6 を主集合にする。

- **real —意図した意味変更そのものを守る gate がない。** checker の shape 検査は `tools/check_codex_agents.py:169-173` で open object 内部を検査せず、coder whiteboard は items 定義すらない。したがって完全協調 rollback は導出 pin を全部合わせれば生存する。次の 2 test を追加するのが再照準案である。

```text
orchestrator/tests/test_codex_agents.py::test_coder_v4_autonomous_source_example_has_null_delta_pct
orchestrator/tests/test_codex_agents.py::test_planner_v4_source_example_omits_last_delta_pct
```

  新たな期待 node 完全集合:

```text
M-SEM-C:
  変異 = coder source + SOURCE_FILE_SHA256 + coder adapter 全体を旧 bytes へ協調 rollback
  期待赤 =
    orchestrator/tests/test_codex_agents.py::test_coder_v4_autonomous_source_example_has_null_delta_pct

M-SEM-P:
  変異 = planner source + SOURCE_FILE_SHA256 + planner adapter 全体を旧 bytes へ戻し、
         T-2249 originless baseline overlay も旧 SHA へ戻す
  期待赤 =
    orchestrator/tests/test_codex_agents.py::test_planner_v4_source_example_omits_last_delta_pct
```

  成果物影響: 受理集合から coherent な旧例 rollback を除外でき、材料レポートが `delta_pct=null` と `last_delta_pct` 不在を durable に certify できる。過去 trial ledger は不変。

- **real だが「既存ゲートの弱化」ではない — P2。** P2 は `p3_s4_loop` の既存二重防壁を消さないため、狭義には規律 2 を緩めていない。しかし新しく主張する role contract の受理集合は旧例を許したままであり、durable な漏出防止の証拠にはならない。  
  成果物影響: test 追加を拒むなら coordinated rollback は `SURVIVED/non-equivalent to intended semantics` と記録し、材料レポートで未保証を明記する。test を追加するなら上記 2 変異で KILLED にできる。

## 凍結成果物への到達

- **refuted — `FROZEN_MANIFEST` が対象 role file を含む。** `test_frozen_artifacts.py:41-88` の全 23 key は `output/` 配下で、対象 role、adapter、ledger、originless test はない。  
  成果物影響: FROZEN_MANIFEST の bytes、key set、certified freeze は変更しない。

- **real — reflux baseline は保存済み artifact を読まず live 再生成する。** `_bundle():41-123` は fixture repository を作り、`:72` で `A.run_trial()` を実行し、生成直後の report と attempts を読む。`FixtureRoleProvider` は `p3_autonomous_workload_trial.py:680-683` で `ROLE_FILES["planner"]` の現在 bytes を hash する。比較は test `:1264-1269`。  
  成果物影響: baseline の planner SHA 7 leaf を新値へ追随しない限り受理集合が赤になる。既存保存済み trial journal は変更しない。

- **real — plan の T-2249 helper 方式は F27/F39 に対して妥当。** 全 baseline 再採取ではなく、旧 SHA の 6 journal row と report `[[old,6]]` を assert してから 7 leaf だけ置換する。T-2145 の `:574-595` と同型で、他の非 volatile leaf を甘くしない。  
  成果物影響: certified 選択値と baseline 構造は不変、試行台帳の role provenance 参照だけ新 SHA へ移る。

- **real — `output/` に関連する `-1.2` はあるが、live copy ではない。**

  - `output/insights/2026-08-01_t288-recipient-matrix/s2-plan.md:143`
  - `output/insights/2026-09-02_t2200-k2-role-contract/README.md:66,151`
  - `output/insights/2026-09-02_t2200-k2-role-contract/verbatim/s6-lens-c.md:40`

  これらは過去の plan・診断・review の歴史記録であり、追随編集しない。他の `rg --fixed-strings -- '-1.2' output` hit は性能測定値、節番号、DOI の部分一致で、対象 role field の copy ではない。旧 source SHA 2 値は `output/` で hit 0 だった。  
  成果物影響: 保存済み材料・性能証拠・trial ledger は歴史記録として不変。新材料レポートから旧例の出所として参照するだけにする。

## 親 brief の誤り

- **real、addendum で訂正済み — baseline は保存済み `output/` 値なので動かない。** 実際は live 再生成。  
  成果物影響: planner provenance baseline を新 SHA へ追随。

- **real、addendum で訂正済み — planner は 35 行目だけ削除。** 34 行目の comma も除かないと `json.loads()` が拒否する。  
  成果物影響: planner source SHA と adapter bytes は plan の新値になる。

- **real、addendum で訂正済み — coder role が現行 autonomous trial の因果入力。** 現行 coder は trigger-gating role で、変更対象 coder は live consumer を持たない。  
  成果物影響: future trial ledger で動く対象 role SHA は planner だけ。coder 修正は静的契約是正として材料レポートへ分離する。

- **real、addendum でも未訂正 — `git grep last_delta_pct` の hit は role・adapter・decisions だけ。** 実測では `docs/phase3-s4b-runbook.md:45` と `docs/phase3-s5-sort-runbook.md:44` に `last_delta_pct: null` があり、両方とも planner の手動入力を指示する operational reference である。  
  成果物影響: planner role から field を削るだけでは材料レポートと手動試行手順の参照が不一致になる。certified 選択値は直ちには変わらないが、将来の手動 trial payload が二義化する。

- **real — file 数と実装 数。** brief の列挙は当初から role 2 + ledger 1 + adapter 2 = 5 file。baseline 追随後は 6 file、実装面は 4 file。  
  成果物影響: provenance と材料レポートの changed-path 集合を 6/4 として記録する。

- **refuted —親の「動かない 4 hash」判断。** 4 定数についてはコードと in-memory 再導出が親を支持する。動くのは source SHA と、それを含む adapter semantic digest である。  
  成果物影響: 4 定数の ledger 値は更新しない。

## 未確定・要裁定

- **real — P1 と 2 本の runbook をどう整合させるか。** 推奨は planner role から field を削除し、`phase3-s4b-runbook.md:45` と `phase3-s5-sort-runbook.md:44` からも `last_delta_pct` を削除すること。runbook を残すなら planner 側を `null` にする対抗案の方が逐語整合するが、production が生成しない field を残す。  
  成果物影響: 前者は変更 file が 2 件増えるため、両 docs の pin 閉包を別途再確認する。後者は trial payload の不要 field を受理し続ける。

- **real — P2 を known survivor のまま受け入れるか、意味 gate を追加するか。** 推奨は上記 2 test の追加。scope を厳密に固定するなら、P2 は KILLED とせず未保証として材料レポートへ残す必要がある。  
  成果物影響: test 追加なら coherent rollback を受理集合から除外できる。追加しない場合、certified と呼べるのは導出整合だけで、例の意味不変ではない。

- **real — adapter 適用方法。** renderer の出力値は検算済みだが、直接 Python write と `apply_patch` のどちらを実装手順に採用するかを親が確定する必要がある。推奨は `apply_patch` 後の expected byte 比較。  
  成果物影響:最終 bytes は同じ。材料レポートの手順証拠だけが変わる。

- **未実走。** pytest、checker、受入全走は実行していない。確認したのは静的コード読解、検索、書込みを伴わない hash・renderer 再導出だけである。  
  成果物影響: 本文の node 集合と hash は親の実走で確定し、未実走を緑として記録しない。