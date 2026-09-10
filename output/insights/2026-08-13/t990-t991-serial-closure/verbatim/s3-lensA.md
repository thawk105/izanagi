実装前に止めるべき所見があります。親の「20 node で閉包」は少なくとも 1 node 漏れており、新設検査も部分的な導出欠落を緑のまま通せます。

## 所見

1. 判定: `real` / 深刻度: `blocker` — slow oracle canary が系統 2 から漏れている。

   [conftest.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:242) は slow oracle canary を意図的除外している。しかし `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` は実 submodule の HEAD を読み、`prepare_fn=driver.prepare_cell` を渡す（[test_s8b_oracle_driver.py:4613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_oracle_driver.py:4613)、[同:4640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_oracle_driver.py:4640)）。`driver.prepare_cell` は `s1_direct_comparison.prepare_cell` の alias であり（[s8b_oracle_driver.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_oracle_driver.py:51)）、wrapper → materializer → callable 呼出しへ渡る（[同:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_oracle_driver.py:658)、[s8b_materialization.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_materialization.py:126)）。最終的に実 submodule を `base_dir` として `patchharness.checkout()` を呼ぶ（[s1_direct_comparison.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s1_direct_comparison.py:501)）。

   影響: この node が鎖外で動くと linked-worktree 管理領域の競合により、`ccbench_pin`・`src_token`・source evidence が異なる値になり、proof chain と受理集合が変わり得る。

2. 判定: `real` / 深刻度: `must-fix` — 実 repo/submodule clone reader の分類が抜けている。

   `test_real_seal_protocol_to_floor_official_core_e2e` は実 `ROOT` と実 submodule を `git clone --no-hardlinks` の source にする（[test_s8b_floor_campaign.py:4168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_floor_campaign.py:4168)、[同:4199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_floor_campaign.py:4199)、[同:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_floor_campaign.py:972)）。親が系統 3 の `build_snapshot` clone を実資源 reader とした一般化と整合しない。

   影響: race 対象と裁定するなら clone/pin snapshot が変わり、seal→floor の proof-chain 検査結果と受理集合が変わる。immutable reader と除外するなら、その機械的根拠が必要。

3. 判定: `real` / 深刻度: `must-fix` — `real` 対 `tmp/hermetic` の二分類では real-but-disjoint を表現できない。

   `test_sort_swo_oracle.py` は module fixture で実 `_CCBENCH` を compiler include path に渡す（[test_sort_swo_oracle.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_sort_swo_oracle.py:15)、[同:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_sort_swo_oracle.py:83)）。実際の compiler command も実 ccbench include を読む（[sort_swo_oracle.py:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/sort_swo_oracle.py:786)）。これは tmp/hermetic ではないが、現 writer の編集ファイルと disjoint なら直列化不要かもしれない。[s2b-plan.md:13](/home/SFC/tanab/.claude/jobs/a0ae8ab5/tmp/t990-t991/s2b-plan.md:13) の分類にはその第三状態がない。

   影響:誤って hermetic と扱えば oracle の実 header snapshot が変わり、正しさテストが許す comparator の受理集合が変わる。すべて real と扱えば certified 値は不変だが 8 node が直列鎖へ増える。

4. 判定: `real` / 深刻度: `blocker` — positive control は空集合を捕るが、部分集合化と fan-out 欠落を捕らない。

   [s2b-plan.md:37](/home/SFC/tanab/.claude/jobs/a0ae8ab5/tmp/t990-t991/s2b-plan.md:37) の `assert victim in by_kind[kind]` により、導出器が完全な空集合になる変異は赤になる。この点では「導出側 control が皆無」という批判は refuted。しかし control は各系統 1 node だけであり、`broken = configured - {victim}` は assertion 側しか撃たない。

   具体的には、fixture consumer 集約を集合和ではなく「最初の consumer だけ保存」へ壊すと、系統 3 の最初の consumer である control（[test_codex_reasoning_ab.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_codex_reasoning_ab.py:760)）だけ残り、残り 16 node が消えても subset・control とも緑になる。

   影響: 消えた 16 node が鎖外に戻り、snapshot 由来の commit/object closure が混在して proof chain と受理集合が変わり得る。

5. 判定: `real` / 深刻度: `blocker` — 系統 2 の callable/alias 伝播は設計上まだ証明されていない。

   実経路は単純な helper call ではない。

   `test → module属性を keyword 値として渡す → wrapper の formal parameter → 別 module から import した materializer → parameter callable 呼出し → re-export alias → function-local import → checkout`

   根拠は [test_s8b_floor_campaign.py:3467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_s8b_floor_campaign.py:3467)、[s8b_floor_campaign.py:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_floor_campaign.py:115)、[同:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_floor_campaign.py:1084)、[s8b_materialization.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s8b_materialization.py:126)、[s1_direct_comparison.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/s1_direct_comparison.py:501)。

   [s2b-plan.md:11](/home/SFC/tanab/.claude/jobs/a0ae8ab5/tmp/t990-t991/s2b-plan.md:11) は「追う」と宣言するだけで、formal/actual 束縛・keyword callable・module re-export の transfer rule を定義していない。特に control は floor module の alias だけなので、`driver.prepare_cell` の alias 解決を丸ごと落としても緑のままである。

   影響: oracle canary の writer lineage が導出されず、certified build の source identity と受理集合が競合依存になる。

6. 判定: `refuted` / 深刻度: `nit` — collection subprocess の例外は握り潰されない。

   `_run_subprocess()` 自体は `check=True` を使わないが（[test_real_repo_serialization.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:347)）、呼び手が `returncode == 0` を assert する（[同:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:418)）。report が欠落・不正 JSON でも直後の read/parse が例外になる。private API の型不整合を plugin 内で明示例外にすれば外側は赤になる。

   影響: この経路を直さなくても certified 選択結果・proof chain・受理集合は変わらない。

7. 判定: `refuted` / 深刻度: `nit` — 現行の parametrize 正規化自体には取りこぼしがない。

   conftest は `item.originalname` を優先する（[conftest.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:277)）。collection report も同じ `canonical_node` を出す（[test_real_repo_serialization.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_real_repo_serialization.py:381)）。例えば 3 instance の `test_m3_focus_artifact_directions`（[test_codex_reasoning_ab.py:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_codex_reasoning_ab.py:1013)）は 1 canonical node へ正規化できる。新導出器が raw `nodeid` ではなく既存 `canonical_node` を使うことを受入条件にすべきである。

   影響: 現状は値に影響しない。raw nodeid を使う実装なら false red で受理集合が不必要に縮む。

8. 判定: `refuted` / 深刻度: `nit` — `GIT_OPTIONAL_LOCKS=0` が新たに dirty を clean にする経路は確認できない。

   変更対象は optional な on-disk index refresh であり、status の working-tree/index 比較を削除するものではない。既存の同形実装も mandatory lock は抑止しないと明記する（[patchharness.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/patchharness.py:71)）。`source_digest` は status の非 0 を拒否し（[source_digest.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:761)）、さらに status と full tracked diff hash の clean/dirty 一致を検査する（[同:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/source_digest.py:846)）。`assume-unchanged`・fsmonitor・racy stat の限界は optional-lock 設定の有無とは独立である。

   影響: 提案どおり env だけを固定する限り、certified 選択結果・proof chain・受理集合は変わらない。

9. 判定: `real` / 深刻度: `must-fix` — [T-991] の最終 scope が「受入で到達する場所」に縮んでいる。

   [s2a-plan.md:64](/home/SFC/tanab/.claude/jobs/a0ae8ab5/tmp/t990-t991/s2a-plan.md:64) は production の 2 status を「受入で未到達」という理由だけで除外する。しかし両者は pinned-clean correctness gate である（[silo_ladder_rung1.py:959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/silo_ladder_rung1.py:959)、[同:2080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/silo_ladder_rung1.py:2080)）。`scrub_environment()` は全 `GIT_*` を除く（[同:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/campaign/silo_ladder_rung1.py:306)）ため、現在も optional index writer のままである。

   影響: 通常は status 非 0 による fail-closed 側の偽拒否となり受理集合を縮める。競合後の cleanup 異常まで連鎖すれば proof-chain 入力を不安定化する。

10. 判定: `real` / 深刻度: `nit` — 正本には実資源へ触らない over-approximation が少なくとも 4 node ある。

   [conftest.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/conftest.py:177) の 4 node は、実際には tmp source と `patchharness.applied = nullcontext()` を使う。例は [test_p3_s4_loop.py:1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_p3_s4_loop.py:1840)、[test_p3_s4_loop_sort.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_p3_s4_loop_sort.py:762)、[test_p3_s4_loop_trigger_gating.py:2182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2182)、[同:2311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2311)。subset 条件が逆包含を要求しない理由としては成立する。

   影響: certified 選択結果・proof chain・受理集合は変わらず、直列 wall だけが増える。

11. 判定: `refuted` / 深刻度: `nit` — 段 2A に正本削除・検査弱化案はない。

   [s2a-plan.md:136](/home/SFC/tanab/.claude/jobs/a0ae8ab5/tmp/t990-t991/s2a-plan.md:136) は 20 node 追加・既存 node 非削除を要求し、status 内容と fails-closed assertion も維持する。過剰 node を認識しつつ削らないため、brief の追加のみ不変条件には従っている。

   影響: certified 選択結果・proof chain・受理集合は変わらない。

12. 判定: `real` / 深刻度: `blocker` — pytest 内の検査が緑でも、runner 層で排他を明示的に無効化できる。

   `tools/run_tests.py` は既定 `loadgroup` を先に置くが、ユーザー `--dist` を後勝ちにする（[run_tests.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/tools/run_tests.py:369)）。非 `loadgroup` は拒否せず警告だけで実行する（[同:1865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/tools/run_tests.py:1865)）。さらに `--dist` は full-suite shape として許可される（[同:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/tools/run_tests.py:85)）。この opt-out はテストでも明示的に固定されている（[test_run_tests_nproc.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t990-t991-serial-closure/orchestrator/tests/test_run_tests_nproc.py:150)）。

   影響: `--dist load` の「full suite」が closure 検査には合格しながら実行時排他を失い、source identity・proof chain・受理集合を競合依存に戻す。

13. 判定: `refuted` / 深刻度: `nit` — 独立した「新規 Git object writer」は確認できず、段 2A の (b) は支持される。

   `patchharness.checkout()` が行うのは linked worktree の add/remove/prune であり、確認した経路では blob/tree/commit の新規生成ではない。したがって第 4 の object-writer 系統ではなく、系統 2 の common-dir writer である。ただし所見 1 により、その系統の node 数は 2 ではなく少なくとも 3。

   影響: 系統名の違い自体は certified 選択結果・proof chain・受理集合を変えないが、漏れた node は変え得る。

## 新設検査への反例

1. consumer fan-out の部分欠落

   `benchmark_snapshots` の consumer 集約を、集合への追加ではなく最初の 1 node だけ保持する実装へ壊す。control は最初の `test_parent_numstat_controls_remain_pinned` なので残る。`victim in by_kind`、subset、`broken configured` の三つがすべて通り、残り 16 node の導出消失が緑になる。witness 登録簿も fixture 自体には一致するため赤にできない。

2. module alias 系統の丸ごと欠落

   resolver が `s8b_floor_campaign.prepare_cell` は追うが、`driver.prepare_cell` の re-export alias を追わない変更を入れる。登録済み control の floor canary は残るが、所見 1 の oracle canary は消える。現 control は module-alias の多様性を検査していない。

3. callable keyword edge の消失を別 witness が隠す

   `prepare_fn=` の formal/actual 伝播を削除しても floor canary 自身には実 submoduleへの `git rev-parse` がある。この直接 path witness だけで node membership が残る設計なら、writer lineage が全損しても control は緑になる。必要なのは node membership だけでなく、`test → prepare_fn → prepare_cell → checkout` の provenance chain assertion である。

4. 未登録構文の恒真化

   実 root の `git clone` や compiler include-path を candidate extractor がそもそも列挙しなければ、「登録規則が最低 1 件に一致」「抽出された候補は全分類」の両方向検査は緑になる。登録簿は登録済み universe の完全性しか証明せず、未知規則の不存在を証明しない。

5. autouse 系統の全損

   `names_closure` から明示 fixture だけを残し autouse fixture を落とす変異を入れても、3 control はすべて明示 fixture/direct test なので緑になり得る。autouse・transitive fixture・parametrize fan-out をそれぞれ撃つ detector-level mutation control が必要である。

なお、private API 取得時の明示例外は subprocess 外へ赤として伝わるため、そこは反例にならない。

## まだ漏れている node の候補

| node | 判定 | 根拠 |
|---|---|---|
| `test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` | 確定漏れ | 実 `driver.prepare_cell → checkout(base_dir=実 submodule)`。系統 2 の 3 件目 |
| `test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e` | 強い候補 | 実親 repo と実 submodule を clone source にする。系統 3 の一般化との整合が必要 |
| `test_sort_swo_oracle.py` の `compiled_oracle_artifacts` 消費 8 node | 要境界裁定 | module fixture が実 ccbench headers を compiler include path として読む。現 writer と path-disjoint なら機械的な第三分類が必要 |
| autouse fixture 経由 | 新規確定なし | 調べた autouse は env/cache の monkeypatch・clear が中心。現 control は将来の autouse 資源 fixture を守らない |
| skip 条件付き | 上記 oracle/floor canary 以外なし | skip 条件成立時は資源 body に入らないが、成立しない環境では接触するため canonical 追加が必要 |
| parametrize suffix | 新規 node なし | `originalname` による base node 正規化でよい。`test_m3_focus_artifact_directions` は 3 instance 全て同じ canonical node |

`compiled_oracle_artifacts` 消費 8 node は以下である。

- `test_cpp_e2e_clean_generic_lambda_positive`
- `test_cpp_e2e_stable_cross_allocation_pointer_positive`
- `test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning`
- `test_cpp_e2e_reports_each_axiom_and_exact_indices`
- `test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing`
- `test_cpp_e2e_rejects_corpus_mutation_with_dedicated_reason`
- `test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness`
- `test_real_compile_budget_is_fixed_positive_and_negative_only`

確定分だけでも、追加数は親の 20 ではなく 21。新検査自身も加える段 2B の案では最小 22 node 追加になる。clone reader 1件と sort fixture 8件も real と裁定すれば計 31 node 追加である。

## 裁定パッケージ候補 (scope 外)

1. acceptance と diagnostic `--dist` の分離

   推奨は、full-suite/acceptance shape では並列 `--dist != loadgroup` を拒否し、`--dist load` は明示的な diagnostic-only option に移して「受入全走」と記録できなくすること。D63 の opt-out を変更するためユーザー裁定対象。

2. scheduler の実測 receipt

   pytest 内の collection 検査だけでなく、runner が実際に選んだ `nproc`・xdist version・scheduler を task-run receipt に固定し、acceptance 記録が `loadgroup` でなければ拒否する。hooks は subprocess 内の scheduler を担保しない。

3. `silo_ladder_rung1.py` の production status

   [T-991] に含めて `_run()` の scrub 後へ固定値を注入するか、「受入到達箇所だけ」が本 wave scope だと明記し follow-up を発行する。現状の黙示的除外は不可。

4. real-resource 境界の三値化

   `real-racy` / `real-but-machine-proven-disjoint` / `tmp-hermetic` のどこまでを正本対象にするか裁定する。clone reader と sort oracle fixture はこの境界で決まる。単なる理由コメントではなく、read path と writer path の交差を検査する必要がある。

5. detector 自身の mutation matrix

   fixture fan-out、autouse、param canonicalization、import alias、keyword callable、wrapper forwarding、未登録 sensitive-call の各 edge を 1 個ずつ壊し、対応 control が赤になることを事前登録する。現行の 3 membership control だけでは detector の完全性を証明できない。

## 未確認のまま残した点

- sandbox 指定に従い pytest・受入全走・変異テストは実行していない。緑は確認していない。
- `item._fixtureinfo.names_closure` / `name2fixturedefs` の現 pytest 版での具体 shape は実走確認していない。
- Git 実装ソースや動的 probe は調べていない。`GIT_OPTIONAL_LOCKS=0` の判定は既存コード契約と静的な status/diff 消費経路に基づく。
- sort oracle の実 header read set と現 writer の編集集合が完全に disjoint かは未確定。
- real-repo 全候補の再棚卸しは行っていない。限定検索で上記漏れを発見したため、さらに存在する可能性がある。
- 40 回上限には達していない。Web 検索は行っていない。

## 総括

段 2A の「独立した Git object writer はなく系統 2 の言い換え」という分類は支持するが、「20 node で閉包」は refuted である。少なくとも slow oracle canary 1件が確定漏れであり、clone reader と real-header module fixture も境界裁定が必要である。

段 2B の検査は完全空集合を捕る一方、subset 条件と代表 3 node だけの control では consumer fan-out・autouse・module alias・callable keyword の部分欠落を緑のまま通す。実装前に、導出 provenance と detector edge ごとの mutation controlを追加した plan v2 が必要である。