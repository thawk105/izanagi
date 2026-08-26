### 所見 1: 二根検査は各 file の検査後に bytes の全体状態を再確認しない

- 深刻度: must-fix
- 壊れる経路: 最終 postflight の二根検査で、sorted 順の前半にある tracked file を正常 bytes のまま読ませ、その file の検査終了後に bytes を A から B へ一方向に変更して残す。各 file は読取中の identity しか検査されず、最後の再 probe は root、HEAD、tracked path 集合しか比較しないため成功する。A→B→A は不要で、関数が戻る時点の実 source は canonical と不一致である。
- 根拠: `orchestrator/campaign/sort_swo_dependency_material.py:376`、`orchestrator/campaign/sort_swo_dependency_material.py:382`、`orchestrator/campaign/sort_swo_dependency_material.py:319`
- 成果物影響: certified binary の値自体は変わらないが、材料レポートと試行台帳は canonical の hash A を保持したまま、`dependency_root` が bytes B を指す試行を受理できる。
- 提案: 各 source file の読取時 identity を保持し、全 file の読取後に path と identity を一括再検査する。最終 check 後の変更禁止まで求める場合は所見 2 の裁定が別途必要。

### 所見 2: 最終 postflight から成果物化までの時間窓と canonical 参照の消失が残る

- 深刻度: 裁定パッケージ候補
- 壊れる経路: 最終二根検査が成功した直後、binary admission と built record の生成前に実 source を A から B へ一方向に変更しても、以後の source 再検査はない。また成功時には材料レポートへ記録した `oracle_dependency_root` を含む lease が必ず削除される。このため run 後に残る actual root は B、canonical root は不在、receipt の hash は A という状態になる。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:3775`、`orchestrator/campaign/s8b_floor_campaign.py:4337`、`orchestrator/campaign/s8b_floor_campaign.py:4394`、`orchestrator/campaign/s8b_floor_campaign.py:4438`
- 成果物影響: certified 選択と数値は変わらないが、材料レポートの actual 参照は別材料を指し、canonical 参照は dangling になる。試行台帳には A の portable hash だけが残り、二根等価性を後から再検算できない。
- 提案: これは immutable snapshot、process 間 lock、または durable canonical material を要するため、T-1802 / T-1805 の境界として裁定する。

### 親の疑義 A1 / A2 / A3 への判定

#### A1: refuted

共有値の変更は production の意味を変えていない。新しい値は `fake_sort_swo_pass_attempt()` の `dependency_config_sha256` と同一であり、新設された oracle receipt と source binding の一致検査を通る、整合した共有 fixture に直している。`"b" * 64` のままでも各テストで局所置換すれば実装可能なので、変更方法として絶対必須ではないが、共有 fixture の整合性としては妥当である。

値の全 transitive consumer は次のとおり。

- oracle receipt と一致して目的の後段へ進むため値に依存するもの:
  `test_post_oracle_binding_requires_receipt_to_match_canonical_and_source`、
  `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle`、
  `test_dependency_bound_sort_best_rejects_nonexact_builder_before_call`、
  `test_dependency_bound_sort_best_default_builder_receives_literal_capability`、
  `test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes`、
  `test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`、
  `test_floor_postflight_failure_persists_unavailable_before_binary_admission`、
  `test_sort_best_build_failure_persists_bounded_exception_diagnostic`。

- config mismatch の意味を持つもの:
  `test_floor_postflight_gate_rejects_effective_root_and_content_drift` は新値と `"d" * 64` が引き続き不一致。
  `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced` と
  `test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash` は `"b" * 64` を明示して旧契約を維持している。
  `test_build_cells_production_postflight_rejects_dependency_drift` は実 source の config hash を oracle receipt へ明示し、共有値は fake build adapter 内だけで使う。

- 値を自己伝播するだけ、または config 値を判定に使わないもの:
  `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once`、
  `test_floor_dependency_prebuild_captures_shared_policy_pins_once`、
  `test_floor_postflight_gate_rejects_source_override_and_accepts_base_only`、
  `test_floor_strict_postflight_rejects_captured_payload_pin_mixture`、
  `test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root`、
  `test_floor_postflight_gate_classifies_head_drift`、
  `test_floor_postflight_rejects_build_result_toolchain_mismatch`、
  `test_floor_postflight_rejects_binding_toolchain_hash_only_mismatch`、
  `test_floor_phase_marker_carries_run_local_archive_sha256`。

偶然一致によって mismatch 検査が消えたテストはない。根拠は `orchestrator/tests/test_s8b_floor_campaign.py:328`、`:430`、`:3121`、`:3662`、`:4801`。

#### A2: refuted

旧 observer の三条件は新経路に包含されている。

- canonical non-symlink directory: `_canonical_source_root` が `lstat`、directory 型、strict resolve、absolute path 一致を検査する。`sort_swo_dependency_material.py:126`
- VCS top-level 一致: combined `rev-parse` の第 1 行を strict resolve して root と比較する。`:167`、`:185`
- HEAD の一意取得: stdout が exact 2 行で、第 2 行が lowercase 40 hex であることを要求する。`:179`

旧 `_observe_fetchcontent_dependency_receipt` の残る呼び出し元は次の全部である。

- fresh build の生成後検査: `orchestrator/campaign/buildcache.py:2379`
- 旧経路が tracked byte drift を見逃すことを明示するテスト: `orchestrator/tests/test_buildcache_v2.py:1027`

同じ入力で旧経路と新経路は別判定を出せる。tracked file だけ変更すると旧経路は HEAD/config が同じなので受理し、新経路は拒否することが上記テストに明記されている。ただし post-oracle fresh build では新経路が先に `buildcache.py:2362` で実行され、その後に旧経路が実行されるため、判定は積集合になり fail-open ではない。generic caller が旧経路だけを使うのも post-oracle capability がない既存境界である。

#### A3: refuted

両方の値が食い違う入力は public API から作れるが、`elif` へ到達する前に拒否される。

`build_v2` は `fetchcontent_archive_sha256` と `post_oracle_binding["archive_sha256"]` を `buildcache.py:2116` で比較し、不一致なら例外にする。一致時は binding の値へ正規化した後、post-oracle 分岐の `_assert_post_oracle_dependency_material` が同じ archive を実 source から再観測する。`buildcache.py:994`

production floor は同じ `_FloorOracleDependencyBinding.archive_sha256` から両引数を作るため、通常の呼び手は食い違いを生成しない。`s8b_floor_campaign.py:4224`、`:4228`、`:4231`

したがって `elif` で消える独立検査はない。

### 等価検査が比較しているものの完全な一覧

1. `expected_head` が exact lowercase 40 hex。
2. canonical root に既存 `_verify_dependency_root` を実行。
3. canonical root が non-symlink directory。
4. canonical の再帰 inventory に symlink、特殊 file がない。
5. `SHA256SUMS` が regular file。
6. manifest が strict UTF-8、末尾 LF、64 hex、空白 2 個、正規 relative path、昇順、重複なし。
7. manifest 宣言集合と canonical の全 regular file 集合が exact 一致。
8. canonical の全宣言 file の bytes を読み、各 SHA-256 を manifest と照合。
9. canonical に `config.h` 宣言が存在。
10. optional expected manifest hash と、今回再読した canonical manifest hashが一致。
11. 実 source root が canonical absolute non-symlink directory。
12. Git top-level が実 source root 自身。
13. HEAD が一意な lowercase 40 hexで、`expected_head` と一致。
14. `git ls-files --cached -z` が成功し、stderr が空。
15. tracked 集合が非空、UTF-8、重複なし、正規 relative path。
16. tracked 集合に `PIN` または `SHA256SUMS` が含まれない。
17. canonical 宣言集合から `PIN` を除いた集合が、現在の tracked 集合と `config.h` の和に exact 一致。
18. canonical の `PIN` を hash 付きで再読し、実 source HEADと LF の bytes に一致。
19. `PIN` を除く全 canonical 宣言 pathについて、実 source bytes を fd 起点、全 path component nofollow、regular file、読取前後 identity 安定付きで再読。
20. その実 source bytes の SHA-256が、今回検証した canonical manifest の同 path hash と一致。
21. 全 file 読取後に source root、HEAD、tracked path集合を再 probeし、開始時と一致。
22. build wrapper は返された canonical manifest hash と oracle binding を再比較。
23. build wrapper は canonical の `config.h` hash と oracle receipt を再比較。
24. archive は二根集合とは別に、実 source の `libkohler_masstree_json.a` を再読して binding hashと比較。

境界動作は次のとおり。

- 実 source にある untracked `PIN` は読まず、canonical の `PIN` は HEAD から生成する。
- tracked `PIN` または tracked `SHA256SUMS` は fail-closed で拒否する。
- untracked `SHA256SUMS` は射影対象外である。
- `config.h` が tracked なら集合上は重複せず 1 pathとして扱う。
- `config.h` が無ければ `canonical-copy-failed` で拒否する。
- canonical 生成後から oracle 中までの実 source driftは、persistentなら build の最初の二根検査で閉じる。
- fresh build は cache lookup前、configure 前後、build 後に二根検査する。cache hit は返却前にも再検査する。
- floor は binary admission 前にもう一度二根検査する。
- 全 file の bytes を読み終えた後の bytes 全体再検査がない点は所見 1、最終 postflight 後の区間は所見 2である。

## 総括

HEAD `3e81c730` の二根検査は、canonical の宣言 101 path、実 source の tracked 集合、HEAD、`config.h` を漏れなく対象にしている。A1、A2、A3 はいずれも refuted である。

破れは時間方向に残る。`assert_source_matches_canonical` は file 単位では安定読取だが、全 file を一つの安定状態として再確認しないため、一方向の変更でも成功復帰できる。また最終 postflight 後は source を再確認せず、canonical 参照も cleanup で失われる。

pytest は実行していない。上記は指定どおり静的検査だけによる判定である。