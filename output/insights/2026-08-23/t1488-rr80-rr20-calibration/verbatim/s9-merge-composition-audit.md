## 合成監査の結論

判定: 安全

## 確認した項目

| 項目 | 判定 | 根拠 (file:line または git 出力) |
|---|---|---|
| 重複 path の main 側 entry | 安全 | `_verify_pristine_floor_dependency_sources: 2` は値を変えず残存 (`orchestrator/tests/test_ccbench_spawn_sites.py:124-126`)。production の実 site も2箇所 (`orchestrator/campaign/s8b_floor_campaign.py:2369`, `:2435`)。 |
| calibration issuer AST 検査群 | 安全 | visitor と走査 helper が完全に残存 (`orchestrator/tests/test_ccbench_spawn_sites.py:270-377`)、期待述語も残存 (`:394-401`)。静的実行結果は call=`calibrator/cli.py::_certify_main` 1件、import=`calibrator/cli.py` 1件で完全一致。 |
| process launch exact Counter | 安全 | exact 述語は `:384-391`。HEAD の helper を静的実行し `PROCESS_EXACT_EQUAL True`、actual/expected とも102、unexpected/missingとも空。走査対象も従来どおり calibrator/campaign (`:25-28`)。 |
| wave production の新規 subprocess | 安全 | base/wave/HEAD の個別AST比較で、holdout・sweepは0件、cliとrunnerの site Counterも不変。走査外の `orchestrator/holdout_observation.py` も別途AST検査して0件。 |
| 新規 test node の収集・hold | 安全（静的） | wave 新規10 nodeはHEADにすべて実在。`pytest.ini:12-14` が `orchestrator/tests` 全体を対象とし、恒久除外は空 (`orchestrator/test_selection_contract.py:39-42`)。growth/flaky台帳との静的集合積はいずれも空。skipは登録nodeの完全一致だけに適用 (`orchestrator/tests/conftest.py:1023-1089`)。 |
| collection meta-test | 安全 | exact pin は ini の2 option (`orchestrator/tests/test_pytest_collection_config.py:141-170`) と空の恒久除外表 (`:314-334`)。test file/node全集合を固定する述語はなく、新規node追加と衝突しない。 |
| `run_tests.py` / mutation経路 | 安全 | runner既定対象はtests全体 (`tools/run_tests.py:55-61`) で、active除外表は空 (`:174-180`)、command構築も空除外なら narrowing なし (`:452-474`)。mutationの新制約はflaky台帳との完全一致のみ (`tools/mutation_harness.py:1056-1065`, `:1257-1267`) で、新規10 nodeとの積は空。 |
| holdout consumer/API の意味的交差 | 安全 | baseとmainのproduction consumer集合は同一で、mainによる新規import/callなし。既存consumer群はHEADでmainと同一。旧 tokenless/formal admission 分岐は引き続き同じ拒否・consume・`None` return (`orchestrator/holdout_observation.py:848-899`)。waveの直接依存面について `MAIN_DIRECT_WAVE_DEPENDENCY_DIFF:none`、HEADはwave親と一致。 |
| interpreter解決・PATH順序 | 安全（静的） | candidate順はdispatchと同じ `python3.10`, `/usr/bin/python3.10`, `/bin/python3.10` (`tools/pegasus/dispatch_compute.py:169-173`, `tools/pegasus/certify_calibration.sh:733-748`)。certifyは選定perfの `$TMPDIR/bin` を最優先 (`certify_calibration.sh:729-760`)。mainのdispatch変更はT-080 env削除、floor変更はFetchContent stagingであり、この順序面は変更していない。 |
| `external/ccbench` gitlink | 安全 | main親・HEADとも `160000 commit 511c9538e4e8efa54b45cda62e72389ed3b706ec external/ccbench`。 |
| registered凍結成果物 | 安全 | mainのrr50 2件はHEADでも同一blob OID、waveのrr80/rr20 2件もHEADで同一blob OID。HEADは計4件。新2件のSHA-256は各filename prefixと一致し、JSONはrr80/rr20・accepted。publish receiptも各targetへの `link-unlink` (`output/env/pegasus/calibration/attempts/0_936025.nqsv/publish.json:1-4`, `0_936044.nqsv/publish.json:1-4`)。publish実装はdigest target＋no-replace (`orchestrator/calibrator/cli.py:925-956`)。 |
| snapshot非変更 | 安全 | 最終 `git status --short --branch` は `## HEAD (no branch)` のみ。両親からの重複file差分に対する `git diff --check` も出力なし。 |

## 危険と判定した点

なし。

## 未検証として残した点

- pytest、`--collect-only`、受入テストは実走していない。静的には収集・hold・Counterが整合しており、実走は親が行う。
- issuer visitor自身が明記する代入alias・`getattr`・`importlib`・`eval` 等の動的経路は完全検査していない (`orchestrator/tests/test_ccbench_spawn_sites.py:285-292`)。
- merge HEAD上でのPegasus実機実行は未検証。`bash -n` も保護hookに実行体起動として拒否されたため未実施。

## 総括

唯一の重複fileはmainの2起動site登録とwaveのissuer AST検査をともに保持している。  
HEAD production ASTは期待Counter 102件と完全一致し、wave追加コードによる未登録spawnもない。  
mainの収集・hold・runner変更はwave新規10 nodeを除外せず、holdout consumerや直接依存面にも新規交差はない。  
gitlinkはmain pinを維持し、rr50 2件とrr80/rr20 2件は同一blobのままcreate-onlyに共存する。  
静的には合成整合。pytest・Pegasus実走は行っておらず、最終実測は親が行う。