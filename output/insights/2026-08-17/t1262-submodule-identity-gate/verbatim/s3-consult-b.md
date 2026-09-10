## 所見

**B1**  
**主張** copy/relocate と seal 後の stat cache は、stat 非依存の実 hash を全 initialized repository に適用する限り偽拒否要因にならない。  
**根拠** `measurements.md:35-40`、`tools/codex_reasoning_ab.py:1545-1551`。ただし `test_shared_base_copy_preserves_metadata_and_relocates_submodules` (`orchestrator/tests/test_codex_reasoning_ab.py:1650-1697`) は finish 前に止めるため、新しい marker/admin 比較を含む verify 正例ではない。  
**深刻度** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** `diff-files` や stat cache に戻ると、同じ size/mtime の改変を通すか、skip-worktree/assume-unchanged の正当な copy を落とし、oracle 不生成または誤った `snapshot_manifest_sha256` になる。

**B2**  
**主張** 未初期化 nested submodule の bytes を検査しない方針は正しいが、現 CCBench の Shirakami 未初期化状態は production の `verify_snapshot` では従来どおり拒否される。  
**根拠** 現 worktree の `git submodule status --recursive` は `external/ccbench/third_party/shirakami` を `-fb14...` と表示する。`tools/codex_reasoning_ab.py:1691-1695` は closure の有無にかかわらず未初期化 row を拒否し、`test_uninitialized_nested_submodule_is_manifested_and_accepted` (`orchestrator/tests/test_codex_reasoning_ab.py:2252-2284`) は `_git_closure_reasons` 単体の受理であって oracle 受理ではない。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** Shirakami を含む CCBench snapshot は `submodule_manifest_sha256` を伴う正例にならず、実測 slot と過去 replay の対象集合から外れる。

**B3**  
**主張** raw bytes hash と path-aware hash は異なる受理集合を持ち、path、attributes、filter、Git config を固定しない計画は replay の受理結果を環境依存にする。  
**根拠** `plan.md:68-91` の argv は `--path=<file>` を明示していない。`external/ccbench/.gitattributes:1-3` は `* text=auto eol=lf` であり、read-only probe では CRLF の raw hash が `89bc60...`、attribute-aware hash が `da0c4e...` になった。(a) CRLF は raw 案なら拒否、path-aware 案なら受理可能、(b) `filter=<driver>` は外部 clean driver の変換と副作用を持ちうる、(c) post-seal の `core.autocrlf` / `core.eol` は path-aware hash を変えうるが raw hash は変えない。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 同じ snapshot が verifier の config により受理または拒否され、`snapshot_manifest_sha256` と測定可能な trial 集合が再現不能になる。

**B4**  
**主張** source 側へ full worktree content gate を掛ける strict P4 は、destination が object database から clean checkout される正当な dirty source まで拒否する。  
**根拠** `tools/codex_reasoning_ab.py:715-762` は source の index、HEAD、submodule state を読み、destination を `submodule update --no-fetch` で構築する。`plan.md:59-64` 自身も source full hash は推奨せず、strict 案だけを未裁定としている。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** live source の受理集合だけが不要に縮み、destination が正しい場合でも snapshot oracle、schedule slot、実走機会が生成されない。

**B5**  
**主張** post-seal `submodule.*` config の拒否は内容 gate とは別の契約であり、closure 有効時だけ任意に適用すると受理集合が spec に依存する。  
**根拠** `_seal_git_object_closure` は `tools/codex_reasoning_ab.py:1123-1141` で config section を削除するが、`plan.md:45-50,183-190` は P3 を closure 有効時だけの裁定としている。直接 content gate は `ignore=all` を検出できる一方、`enforce_closure=False` の config 完全性までは保証しない。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 同じ row と `submodule_manifest_sha256` のまま config だけ異なる snapshot が、spec と旧成果物の世代により受理または拒否される。

## 全層適用の判定

**B6**  
**主張** `collect_run`、`make_packets`、verdict CLI を scope 外にしたままでは、全 consumer に効く gate ではなく、T-1263 への未接続な受理穴が残る。  
**根拠** `verify_snapshot` は両 closure 枝で gate され、supervisor は `tools/codex_reasoning_ab.py:2213,2374,2478-2486`、replay は `:4887-4894` で再検証する。しかし `_verify_launch_receipt` (`:2885-2903`) は oracle JSON を bind 用に読むだけで内容を再計算せず、`collect_run` は `:3465-3468` で launch receipt の sha を転記するだけ、`make_packets` (`:5057-5069`) は10 slotの manifestから出力をコピーするだけである。`append-verdicts`、`freeze-verdicts`、`reveal-mapping` も packet 層だけである。`render-prompt` と `score-run` は snapshot consumer ではない。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 未検証 snapshot の `snapshot_manifest_sha256` が receipt、manifest、packet の参照へ流れ、proof chain 上で検証済みと区別できなくなる。

**B7**  
**主張** plan の「維持する既存5 node」は不足しており、新 gate の静的影響範囲はそれより広い。  
**根拠** 直接影響する synthetic node は `test_verify_snapshot_submodule_gate_rejects_custom_spec_without_closure`、`...with_closure`、`...checks_every_manifest_row`、`...rejects_default_spec_path`、`...accepts_all_initialized`、`...accepts_empty_manifest` (`orchestrator/tests/test_codex_reasoning_ab.py:2139-2249`)、`test_uninitialized_nested_submodule_is_manifested_and_accepted`、`test_uninitialized_nested_submodule_gitlink_pin_rejects_change`、`test_shared_base_copy_preserves_metadata_and_relocates_submodules`、parameterized の `test_snapshot_relocation_preflight_rejects_absolute_gitdir` 2 node、`test_snapshot_relocation_preflight_rejects_absolute_core_worktree` 2 node、`test_derived_preflight_rejects_path_dependent_absolute_core_worktree` である。さらに `conftest.py:227-244` の17 real fixture node、すなわち `test_parent_numstat_controls_remain_pinned`、`test_forbidden_commits_are_unreachable_in_both_cases`、`test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`、`test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`、`test_m1_snapshot_head_pin_is_independent`、`test_m3_snapshot_mode_change`、`test_m3_symbolic_head_is_required`、`test_m3_ignored_extra_and_missing`、`test_m3_focus_artifact_directions`、`test_snapshot_submodule_object_store_is_recursive`、`test_pos_neg_submodule_initialization_state_mismatch_is_rejected`、`test_git_answer_object_reinjection_is_rejected`、`test_supervisor_launches_pair_and_scrubs_git_environment`、`test_agent_sandbox_binds_exclude_attempt_receipt_directory`、`test_verify_replays_complete_fake_codex_experiment`、`test_attempt_four_is_rejected_before_launch`、`test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` が影響を受ける。pytest は未実行なので赤は観測していない。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 期待 node 集合、serial 制約、正例の受理根拠が過少申告になり、既存 fixture の赤を新 gate の仕様変更と区別できない。

**B8**  
**主張** synthetic test 方針は成長比例コストを避けているが、real `benchmark_snapshots` に新 node を接続すると既存の growth policy に反する。  
**根拠** `plan.md:141-170` は `tmp_path`、固定サイズ、履歴走査なしを明記している。一方 `growth_test_holds.py:58-60,114-129` は real session corpus を列挙する node の費用が output artifact 数に比例すると明記し、`conftest.py:227-244` はそれらを serial 化している。  
**深刻度** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 新テストの実行時間と serial queue が成果物量に比例して増え、test coverage と実走前の検査時間の参照値が不安定になる。

**B9**  
**主張** P5 の「1秒未満」は CCBench 405 file の一点測定であり、path-aware hash 実装の一般的な上限ではない。  
**根拠** `measurements.md:25-40` は cold CCBench の Python raw hash 0.199秒を示すが、提案する Git path-aware batch hash、subprocess 起動、複数 submodule、argv chunking は未測定である。file 数・総 bytes・submodule 数と深さ、cold page cache、共有 FS metadata latency、長い path、外部 filter 起動で費用は増える。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** supervisor の schedule gap、実走 budget、性能報告の「1秒未満」という参照値が過小評価になる。

## 凍結成果物への波及

**B10**  
**主張** `schedule.json` の二件は単なる保存 field ではなく runtime consumer を持ち、`manifest.json` には加工後の `snapshot_oracle.sha256` も残る。  
**根拠** `output/insights/2026-07-30_t181-reasoning-ab/schedule.json:11-102` と `output/insights/2026-08-09_t181-certified-rerun/schedule.json:1` は `snapshot_manifest_sha256` と `submodule_manifest_sha256` を保持する。実装は `supervise_pair:2478-2486` と `_replay_manifest:4875-4892` でそれらを読む。両 run の `manifest.json:1` には各 attempt の `snapshot_oracle` / `snapshot_after` sha もある。`verdict-freeze.json:1` は直接 submodule pin ではなく packet、state、verdict log hash だけである。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 「live consumer は rollout だけ」「path に exact key が無ければ pin なし」という判定が誤り、旧 schedule/manifest の replay 失敗や stale oracle 参照を見落とす。

**B11**  
**主張** 「コード外の tool pin は0件」という広い pin 閉包の主張は、`apparatus-pin.json` の whole-tool hash により反証される。  
**根拠** `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json:3-5` は `tool_path` と `tool_sha256` を固定し、README `:49,153-154` と erratum `:4-14,73-91` は装置 hash を歴史的に不変として扱う。`docs/archive/worklog-phase3-0816-604.md:24-30` も、過去の検索がこの pin を落としたと記録している。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 現行 tool を過去装置として誤参照するか、逆に歴史 artifact を再発行して `tool_sha256`、manifest 参照、認証根拠を変更する。

**B12**  
**主張** P1 reject-only は replay 互換性のため維持すべきだが、三者照合の証拠を永続化した案と同じ proof strength ではない。  
**根拠** `verify_snapshot` の oracle schema は `tools/codex_reasoning_ab.py:1706-1727`、replay は保存 oracle の canonical bytes 完全一致を `:4887-4892` で要求する。reject-only は A-D を検出するが、どの照合が通ったかを保存しない。証拠 field を oracle row に足せば `submodule_manifest_sha256` と `manifest_sha256`、top-level field でも `snapshot_manifest_sha256` が変わり、schedule と manifest の再発行が必要になる。証拠だけを足して再計算しなければ mutation detection は増えない。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** reject-only なら clean な過去 oracle、両 SHA、schedule は不変だが proof chain は検査理由を保存しない。evidence 案なら監査性は増すが、既存 frozen artifact の hash と replay 受理集合を変える。

## 総括

判定は「実装前に継続」だが、B3、B5、B6、B10、B11 は裁定なしで着手不可。  
stat cache と未初期化 nested の扱いは、直接 hash と full verify の区別を守れば防御側で整合する。  
P1 は replay 互換性のため採用し、証拠力の限界を明記するのが妥当。  
T-1263 は中間層の未検証を引き受ける契約と、manifest/packet の precondition を明示すべきである。  
pytest は実行しておらず、上記は静的検査と read-only probe の判定である。