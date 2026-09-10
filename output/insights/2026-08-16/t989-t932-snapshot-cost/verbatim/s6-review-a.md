```text
所見 1: 守れていない（コマンド失敗は fail-closed だが、4 操作だけでは意味的な完全性を証明しない）
根拠: tools/codex_reasoning_ab.py:255, tools/codex_reasoning_ab.py:270, tools/codex_reasoning_ab.py:279, tools/codex_reasoning_ab.py:1469, tools/codex_reasoning_ab.py:1477, tools/codex_reasoning_ab.py:1478, tools/codex_reasoning_ab.py:1378
破れの成立条件: 4 操作はいずれも既定の check=True を通るため、子プロセスの非 0 は ValidationError で停止する。一方、index-pack に --strict がなく、update-ref は tip object の存在しか閉包として保証しないため、source の shallow、graft、replace 等により「構造上は有効だが参照 object が欠けた pack」が生成されれば、4 操作までは rc=0 になりうる。ただし後続 repack または verify_snapshot の git fsck が certification 前に検出する。--delta-base-offset を渡さない場合は OFS_DELTA でなく REF_DELTA になるだけであり、--thin を渡していないので欠落 delta base は生じない。--fix-thin も fresh store では欠落 base を隠さない。
深刻度: MINOR
成果物影響 (DW-G05): certified 選択、レポート、台帳の受理集合は後段 fsck により変わらないが、不完全な診断用 base が残り、異常の検出位置が転送直後から後段へ遅れる。

所見 2: 守れている
根拠: tools/codex_reasoning_ab.py:1347, tools/codex_reasoning_ab.py:1354, tools/codex_reasoning_ab.py:1356, orchestrator/tests/test_codex_reasoning_ab.py:1082
破れの成立条件: 正常な _build_snapshot_base は git init から作る非 shallow repository であり、.git/shallow は生成しない。空の shallow file は拒否されず、非空だけが拒否される。is_dir、exists、stat は symlink を追跡するため、非空 file・directory への symlink は拒否、空または dangling symlink は見落とすが、この挙動は既存 6 種と shallow で同一である。
深刻度: なし
成果物影響 (DW-G05): 正常 snapshot の受理は維持され、非空 shallow 境界を持つ snapshot だけが新たに拒否される。

所見 3: 守れている（新設 node の射程は限定されている）
根拠: orchestrator/tests/test_codex_reasoning_ab.py:351, orchestrator/tests/test_codex_reasoning_ab.py:367, orchestrator/tests/test_codex_reasoning_ab.py:892, orchestrator/tests/test_codex_reasoning_ab.py:1289, orchestrator/tests/test_codex_reasoning_ab.py:2118, orchestrator/tests/test_codex_reasoning_ab.py:3409, tools/codex_reasoning_ab.py:1497
破れの成立条件: 新設 node が見ない実 repo 固有性は、実 BASE 閉包の多数 commit・複数 pack、実 TRACKED_PATHS の patch・mode・hash・numstat、実 session corpus の POS/NEG artifact、3 submodule の再帰初期化、実 forbidden commit、source の shallow/graft/replace/alternate/promisor 汚染である。実 repo と submodule は既定3 nodeが共有 fixture を構築する際に通り、submodule と reinjection は各専用 nodeでも見る。一方、numstat、symbolic HEAD、forbidden、commit-graph の独立 pin nodeは既定 skipであり、source metadata 汚染の負例を持つ既定 nodeはない。
深刻度: なし
成果物影響 (DW-G05): 新設 node は転送 argv と exact object 集合を固定し、実 repo の成果物値は既定 fixture の verify_snapshot が守る。独立 pin の検出力は既存保留方針の範囲に残る。

所見 4: 守れていない（M6 の期待赤集合が不完全）
根拠: tools/codex_reasoning_ab.py:1482, tools/codex_reasoning_ab.py:1508, orchestrator/tests/test_codex_reasoning_ab.py:367, orchestrator/tests/test_codex_reasoning_ab.py:1289, orchestrator/tests/test_codex_reasoning_ab.py:2118, orchestrator/tests/test_codex_reasoning_ab.py:3409, orchestrator/tests/test_growth_test_holds_contract.py:254
破れの成立条件: 静的な完全期待集合は、M1・M2・M3＝test_build_snapshot_base_pack_transfers_unreferenced_base_closure_only、M4＝test_snapshot_submodule_object_store_is_recursive、M5＝test_object_info_derived_caches_are_removed_for_root_and_submodule、M7＝test_git_closure_rejects_shallow_without_overrejecting_clean_snapshot。M6 は共有 benchmark_snapshots の POS 導出中に verify_snapshot が reflog を拒否するため、表の snapshot node に加えて test_git_answer_object_reinjection_is_rejected と test_supervisor_launches_pair_and_scrubs_git_environment も fixture setup error になる。この3 nodeはいずれも _HOLD_ROWS に無く、既定 skipではない。
深刻度: MAJOR
成果物影響 (DW-G05): M6 の mutation 台帳が実失敗 nodeを2件欠落し、DW-M08 の完全一致では KILLED と認定できないため、wave の変異証明参照が成立しない。

所見 5: 守れていない（27件の損失記載に誤帰属と過小記載がある）
根拠: orchestrator/tests/growth_test_holds.py:84, orchestrator/tests/growth_test_holds.py:190, orchestrator/tests/growth_test_holds.py:282, orchestrator/tests/growth_test_holds.py:405, orchestrator/tests/test_s1_known_axes_freeze.py:84, orchestrator/tests/test_s1_known_axes_freeze.py:479, orchestrator/tests/test_s1_measurement_freeze.py:44, orchestrator/tests/test_s8b_floor_campaign.py:6159
破れの成立条件:
- known_axes の9件、すなわち generate_selects、build_document_is_self_consistent、generate_refuses、s1b_pairing、foreign_ccbench_pin、generator_sha、non_ancestor_head、one_byte_freeze、tampered_source_copy は、各関数内の固定検査を止めるが module fixture を使わない。全9行の「shared module fixture」共通文は誤りである。個別の固定検査説明自体は過小ではない。
- measurement の11件、すなわち build_document_rejects、generate_builds、generate_refuses、receipt_exists、recorded_ccbench_pin、s1b_pairing、schedule、known_axes_material、one_byte_freeze、one_byte_workload_flag、stats_implementation は、各関数内検査に加えて real_known_axes_doc の full SHA、CURRENT_PIN prefix、独立 golden、K.verify_document をすべて止める。共通記載は概ね正確である。
- 残り7件のうち binding_driftguards、oracle_driver 3件、real_repo_serialization、protocol_builder の記載は主要な固定検査を表している。
- floor_campaign の official core E2E は、記載された protocol・freeze・prediction・journal・receipt・schedule・floor に加え、実 git ancestry、14 path の seal diff、artifact hash、producer 非呼出、attestation、clean digest、trace=False、12 build、96 measurement、reservation claim、source/clone 不変まで止める。growth_test_holds.py:410 の記載はこの損失を明確に過小評価している。
深刻度: MAJOR
成果物影響 (DW-G05): hold inventory と人間向け台帳が失われる防壁を誤表示し、特に official floor 成果物の hash、clean scan、build、attestation、claim の検査停止を提示せずに保留を受理させる。

所見 6: 守れていない（実効 skip 追加と既存 payer 防壁の反転あり）
根拠: orchestrator/tests/growth_test_holds.py:190, orchestrator/tests/growth_test_holds.py:471, orchestrator/tests/conftest.py:404, orchestrator/tests/conftest.py:410, orchestrator/tests/test_real_repo_serialization.py:1122, orchestrator/tests/test_real_repo_serialization.py:1134
破れの成立条件: 59606f29 は27 nodeを GROWTH_TEST_HOLDS に追加し、既存 collection hook が既定 skip を付ける。また test_ratified_memo_has_a_real_resolution_payer は「毎 session の実 direct payer」を守る検査から、payer が恒久保留に入っていることを assert する検査へ反転している。xfail追加、fixtureへの現行 hash 差し込み、個別 body の assert 削除は無いが、skip追加と受理条件の緩和だけで指定どおり BLOCKER である。
深刻度: BLOCKER
成果物影響 (DW-G05): 27正しさ node の赤が既定受入を止めなくなり、実 active-generation 解決を一度も実走しない状態でも受入レポートと台帳が通る。

所見 7: 守れている（production の入力受理集合に限る）
根拠: tools/codex_reasoning_ab.py:1347, tools/codex_reasoning_ab.py:1462, orchestrator/tests/growth_test_holds.py:94
破れの成立条件: production verifier が新たに拒否する入力は非空 .git/shallow だけであり、転送置換は最終 ref、HEAD、working tree、object closure の受理条件を変更しない。S2 は既定テスト実行集合を意図的に27件縮小しているが、これは production snapshot 入力の受理集合変更ではない。ただし、そのテスト防壁の緩和は所見6の独立 BLOCKERである。
深刻度: なし
成果物影響 (DW-G05): snapshot の certified 値と oracle schema は維持され、非空 shallow snapshot のみ受理対象から外れる。
```

## 総括

NO-GO  
BLOCKER 1件。静的監査のみで、pytest実走はしていない。