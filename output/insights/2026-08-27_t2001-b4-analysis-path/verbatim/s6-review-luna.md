## 前提の確認

全文を読んだ必読資料:

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s4-ruling.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/parent-measurements.md`

全文を読んだレビュー対象:

- `orchestrator/campaign/p3_b4_analysis_contract.py`
- `orchestrator/campaign/p3_b4_analysis_adapter.py`
- `orchestrator/campaign/p3_b4_analysis_ledgers.py`
- `orchestrator/campaign/p3_b4_analysis_path.py`
- `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py`
- `orchestrator/tests/test_p3_b4_analysis_contract.py`
- `orchestrator/tests/test_p3_b4_analysis_adapter.py`
- `orchestrator/tests/test_p3_b4_analysis_ledgers.py`
- `orchestrator/tests/test_p3_b4_analysis_path.py`
- `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`

比較対象として `orchestrator/campaign/reflux_formal_consumer.py` の実在照合経路と、既存の一覧走査を静的確認した。Web 検索とテスト実走はしていない。緑として扱うのは親の記録した 121 passed、79 passed、24 passed / 6 skipped のみである。

## 所見

### F1

- 重大度: blocker
- 対象: `orchestrator/campaign/p3_b4_analysis_contract.py:749`、`同:787`、`orchestrator/campaign/p3_b4_analysis_path.py:181`、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:955`
- 根拠: `evaluate_analysis()` は公開され、`__all__` にも残り、統合経路と同じ `B4AnalysisResult` を返す。結果型には「artifact 経路を通った」ことを示す receipt、seal、provenance が無い。consumer 自身が 955 行から、自己作成した `contract_binding`、`registry_violation_count=0`、`assignment_followed=True` の block を直接渡して `ESTABLISHED` を作っている。production 全体の呼出 grep でも、非テスト直呼びを拒否する一覧検査や、後段が `evaluate_b4_artifacts()` 由来の結果だけを受理する機構は存在しない。
- 成果物影響: 呼び手は台帳から導出していない違反件数と割当遵守値から、統合経路の verdict と区別不能な成立結果を作れる。
- 反証されうる形: `B4AnalysisResult` の downstream 受理点が、偽造不能な統合 receipt を必須とし、直呼び結果を拒否する実在 gate、または production 直呼びを閉じる全域走査が提示されれば反証される。

### F2

- 重大度: blocker
- 対象: `orchestrator/campaign/p3_b4_analysis_path.py:161`、`同:288`、`orchestrator/tests/test_p3_b4_analysis_path.py:109`
- 根拠: `source_artifact_sha256` は各 bytes から再計算されるが、照合は digest の `Counter` 同士だけである。block・arm との一対一対応を失い、source bytes の内容から `assignment_observation`、status、throughput、`treatment_fired`、`contaminated`、`protocol_ok` を再導出しない。実際、path test は source を単なる `b"source-000-on"` のような任意 bytes とし、全意味値を別の raw JSON に自己申告して成立させている。digest を arm 間で入れ替えても multiset は同じなので検出されない。既存 idiom は `reflux_formal_consumer.py:466-519` で実 bytes を parse して ledger member と一意に対応付け、`同:639-678` で member identity・outcome・candidate・WAL を実内容から再照合しており、本実装より明確に強い。
  
  3 hash の判定は次のとおり。

  - `manifest_sha256`: manifest 実 bytes から再計算し、canonical load、registry からの再生成、呼出 binding との完全一致まで行う。
  - `registry_sha256`: registry 実 bytes から再計算し、canonical chain 再生成、呼出 binding との完全一致まで行う。
  - `source_artifact_sha256`: 実 bytes の digest は再計算するが、申告 digest との multiset 一致だけで、申告された意味と arm/block の対応は信頼したままである。
- 成果物影響: 無関係な source bytes を添えた自己申告 JSON から status、slot、protocol 値を作り替え、成立 verdict を得られる。
- 反証されうる形: 各 source artifact の strict parser が block・arm identity と全 raw 意味値を独立再導出し、manifest/registry の対応行へ一意に束縛する経路が示されれば反証される。

### F3

- 重大度: must-fix
- 対象: `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:15`、`同:357`、`orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:194`
- 根拠: docstring は「exact raw bytes hash is pinned」と主張するが、実条件は `raw hash が一致 OR semantic hash が一致` である。テストも heading の強調、空白、段落改行による raw bytes 変更を意図的に受理している。これは裁定の「§5.1.1 exact section bytes hash」と「doc を 1 byte も編集しない」に反する。現行 doc の section hash 自体は 357-361 行で独立に再計算されているが、期待値は実装側定数である。意味変更時は両 pin が外れて拒否される一方、定数を doc と同時更新すれば通る。「先頭 n 行」から「末尾 n 行」への改訂は semantic hash が変わるため、現コードとテストで拒否される。
- 成果物影響: 凍結文面が byte 単位では維持されず、変更後の section hash を持つ closure receipt が consumer 成功として発行可能になる。
- 反証されうる形: 裁定が semantic-equivalent な byte 改訂を正式に許可している証拠、または raw hash 不一致を無条件拒否する実装が示されれば反証される。

### F4

- 重大度: must-fix
- 対象: `orchestrator/campaign/p3_b4_analysis_path.py:79`、`同:422`、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1091`
- 根拠: A11 は source closure receipt に「consumer 実行結果」を canonical に含めることを要求した。しかし receipt の field は schema、5 member の path/hash、section hash、自身の canonical bytes/hash だけである。`generate_analysis_source_closure_receipt()` は公開され、consumer を一度も実行せず直接生成できる。`verify_repository_preregistration_contract()` は consumer 成功後に receipt を生成するものの receipt を返さず、成功結果も receipt に格納しない。
- 成果物影響: 後続 §5 wave は、文面一致 consumer が成功した証拠を含まない path/hash を分析実装の closure として記録できる。
- 反証されうる形: consumer の canonical 結果 bytes と hash が receipt に束縛され、receipt の生成 API がその検証成功なしには到達不能であることが示されれば反証される。

## 一覧検査の閉包 (独立確認)

独立走査では既存の自動 node を 32 件確認した。裁定の `26 + 4 = 30` 件との差は 2 件で、名前からは走査と分かりにくい次の helper 経由 node である。

- `test_s8b_oracle_manifest_contract.py:87::test_loader_production_consumer_sets_are_pinned_for_spec_reverification`
- `test_s8b_oracle_manifest_contract.py:99::test_verify_manifest_production_consumer_set_is_auxiliary_pin`

両 node は `_production_calls()` 内の `CAMPAIGN.glob("*.py")` で全 production module の内容を AST 走査する。新 5 module は対象 loader / `verify_manifest` を呼ばないため、静的には期待集合を増やさない。

確認した 32 node の全体:

- `test_campaign_import_invariant.py`: 1078、1218、1222、1227、1231、1235 の real-repo 6 node
- `test_ccbench_spawn_sites.py`: 476、486、496
- `test_plain_runner_coverage.py`: 60、77
- `test_p3_build_authority_cli.py`: 630、1190
- `test_s8b_floor_campaign.py`: 1586、6290
- `test_s8b_oracle_manifest_contract.py`: 87、99
- `test_t1286_commit_receipt.py`: 657、683
- `test_acceptance_schedule_order.py:660`
- `test_calibration_freeze_stage6_candidate_gate.py:375`
- `test_campaign.py:4641`
- `test_login_headroom.py:1625`
- `test_p3_s4_loop.py:1117`
- `test_pegasus_dispatch_compute.py:2232`
- `test_pytest_collection_config.py:423`
- `test_reflux_ir.py:274`
- `test_s1_known_axes_freeze.py:520`
- `test_s8b_floor_stats.py:875`
- `test_s8b_oracle_report.py:5488`
- `test_s8b_ratified_freeze.py:2399`
- `test_t338_submission_gate_unit5.py:490`

加えて `test_p3_exploration_namespace.py:123-139` は collection 時に全 campaign Python を AST parse するが、新 module は campaign-root creator ではないため新 parametrized node は作らない。これは上の node 数には含めていない。

静的適合:

- production 5 file は legacy `campaign.*` import、`sys.path` 変異、`__main__`、絶対 sibling import を持たず、relative sibling import で統一されている。
- test 5 file はすべて `__main__` と `pytest.main` を持つ。名前に `verifier` / `oracle` は無い。
- real-repo 6 node が要求する import 形、bootstrap 形、exception ledger 形は満たす。親実測どおり通常走では 6 node とも growth hold で skip され、受入全走でのみ実効化する。
- `test_p3_build_authority_cli.py:630` の母集合は `git ls-files` である。現在 10 file は全て untracked なので現時点の走査には入らない。track 後は全 10 file が入るが、対象 build-authority helper、動的解決、star import は静的に見当たらない。
- acceptance duration ledger は親実測で slack 1958 node。新規数十 node は 90% 閾値を割らない。
- 以上は静的判定であり、32 node の緑を主張しない。

## 限界申告の点検

過大な保証:

- `p3_b4_analysis_path.py:190` の「actual artifact bytes」と、冒頭の「unique received byte string」は F2 の Counter 照合より強い。
- `p3_b4_analysis_prereg_consumer.py:15` の「exact raw bytes hash is pinned」は F3 の semantic fallback と一致しない。
- `test_p3_b4_analysis_ledgers.py:156` の「issuer-bound schedule receipt」はテスト自身が receipt を自作している。`issuer_sha256` は形式検査されるだけで、署名、発行台帳、opaque seal は無い。
- consumer の「Independent」は、doc 抽出の独立性という限定なら成立するが、live implementation を import し、その値と挙動を使うため、独立実装や独立 authority を意味しない。

正直に申告できている限界:

- ledgers 冒頭は権威 producer 不在と file-drawer 未閉包を明記している。
- path 冒頭は sanctioned CLI、writer、report、certified-selection 配線が scope 外であり、入力 bytes は authority にならないと明記している。
- seed の一様性と実走前発行を証明しないことも明記されている。
- 「§6 前提条件 9 を充足した」「file-drawer を閉じた」という禁止文言は見当たらない。
- `assert_scheduled_registry_complete()` と `assert_analysis_manifest_complete()` は、呼出側が自作できる receipt と registry に相対化されている。異なる receipt や欠落行は拒否するが、外部の全予定 attempt を証明しない。
- schedule receipt と seed receipt はどちらも自作すれば通る。これは scope 外の issuer 不在そのものである。
- violation count は `generate_analysis_manifest()` 1058-1067 行で eligibility filter より前に全 registry violation から導出される。
- `assignment_followed` は manifest schedule と raw JSON の observation を比較しており、同一オブジェクト同士の比較ではない。ただし raw observation が source artifact の実内容から導出されないため、authority 上の循環は F2 として残る。

consumer の保証範囲:

- A は定数、enum、verdict 分岐形、順位・閾値 behavior を検査する。
- C は first-201 slice、違反導出順、first-n behavior を検査する。
- D は violation → adapt → evaluate の呼出順と一部統合 behavior を検査する。
- B adapter は closure member hashには入るが、source AST の意味検査対象ではなく、runtime path probeで間接的に通るだけである。
- 実装 module A/B/C/D が現行 doc を読んで値を決める経路は無い。doc を読むのは consumer と source-closure 生成である。
- AST 検査は指定定数、enum、限定した関数形以上を証明しないと docstring 自身が正しく限定している。

所有と重複:

- 既存 `Arm` は `p3_b4_closed_critic.py:70`、新型は `B4Arm` なので Python 識別子衝突は解消されている。
- `design_not_feasible` は T-139 に既存だが、新側は `B4ManifestState` と `p3-b4-*` schema に束縛されている。
- `block_id` は s8b oracle 等にもある別概念だが、B4 dataclass と versioned schema 内の field であり、裸の共有型は作っていない。
- manifest / registry は既存概念が多数あるが、新しい公開型は全て `B4` 接頭辞付きである。`attempt_registry_core` から再利用するのも stateless canonical JSON / chain primitive に限る。
- この 5 語について、新たな D75 の同名識別子二義化は確認しなかった。

## 総括

blocker は 2 件、must-fix は 2 件である。  
最重は F1: `evaluate_analysis()` の直呼び結果が統合経路由来の結果と区別不能で、path が閂になっていない。  
加えて F2 により、path 内でも source artifact の実内容と自己申告 raw 値が結ばれていない。  
manifest と registry の bytes hash・再生成照合、および filter 前の violation count は実装されている。  
§5.1.1 の「先頭」から「末尾」への意味改訂は拒否するが、1 byte 不変は守っていない。  
一覧検査は独立に 32 node を確認し、裁定の 30 件に対して内容走査型 2 node の追加差分を確認した。