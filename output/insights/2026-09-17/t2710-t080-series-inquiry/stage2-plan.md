## 前提の検算

本段は調査計画の起草のみとし、実装・file 作成・pytest・負例 probe は実施していない。射影資料はすべて読取可能だった。実施した計算は、既存 JSON/XML の読取り、AST による集合抽出、現行 `allocate()` のメモリ上での再計算に限る。

基準 HEAD は `38353207f719acb0871cfe3d9bbe3a02490282bb`。以下の略記を使う。行番号はこの HEAD のもの。

- `ODT` = `orchestrator/tests/test_s8b_oracle_driver.py`
- `RST` = `orchestrator/tests/test_real_repo_serialization.py`
- `MT` = `orchestrator/tests/test_t080_freeze_migration.py`
- `HT` = `orchestrator/tests/test_s8b_holdout_freeze.py`
- `MIG` = `orchestrator/campaign/t080_freeze_migration.py`
- `HD` = `orchestrator/campaign/s8b_holdout_freeze.py`
- `DRV` = `orchestrator/campaign/s8b_oracle_driver.py`
- `AS` = `tools/acceptance_shards.py`

親の provisional 裁定には次の補正が必要である。

| 前提 | 現物による検算 |
|---|---|
| P1：M は 6 function / 11 node | 一致する。`ODT:1285` の pin、`RST:1197` の期待集合、既存 report の nodeid が一致。台帳合計 2,302 秒、最大 240 秒も一致 |
| shared-base 群は 12 node | **現物は 10 function / 13 node**。cleanup の `[False]/[True]` と errno `[13]/[5]/[39]` を含む。実 builder を通すのはうち 1 node |
| snapshot 群は 21〜57 秒 | `ODT` の 3 node は **2.4 / 57 / 21 秒**。実 base builder は通さない |
| M は全 defect を public gate で検査する | そうではない。単一 defect 4 node と履歴 defect 3 node は変異後に `verify_receipt()` を検査する。§1.4 node は helper 直接呼出し。fixture 発行時の public gate 通過と、変異後の検査経路を分ける必要がある |
| P2：`dev_wave_wait.py acceptance --check-only` | **この CLI は存在しない**。`--check-only` は `producer` 専用（`tools/dev_wave_wait.py:1628,1656`）。引数エラーを利用時拒否の証拠にしてはならない |
| P3：M 除外後の最長 node は台帳 161.1 秒 | node の同定は正しいが、**現行台帳は 170 秒**。161.1 秒は T-2559 の実測値 |
| lock union は 186.5 秒 | T-2559 の値。指定 session `895f300a…` では **231.863 秒** |
| P4：定期実行基盤なし | 親の本日再確認を前提とする。本段の repo 内 filename 検索でも cron/timer/workflow 候補は得られなかった。ただし外部 scheduler の不存在まで証明するものではない |

`growth_test_holds.py:154` の `_HOLD_ROWS` は全 50 行を確認した。T-080 に近い行だけでなく、known-axes・measurement の保留も被覆候補の判定に含める。

## M の確定

M は D700/D701 の歴史的対象集合として、以下の **11 node** に固定する。コードブロック内は repo 相対の完全 nodeid である。

```text
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28
orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7
```

以後、順に M1〜M11 と呼ぶ。M′ は上記全 11 node に次の 1 node を加えた **12 node、台帳合計 2,452 秒**とする。

```text
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes
```

M′ は費用感度分析の候補であり、D701 の期待集合そのものではない。採用するなら、cache の別 process 間共有を検査する検出力も毎走から移ることを追加で裁定する必要がある。

base 構築の判定は「関数名が AST に出るか」ではなく、**実 builder の構築本体まで進むか**で行う。

| 群 | 根拠 | 実 base 構築 | 集合への扱い |
|---|---|---|---|
| M | `ODT:964,992,1364` | cache miss 時に実行。hit 時は既成 base を複製 | M に含める |
| `shared_base_builds_real_builder_once_across_processes` | `ODT:1047` | `wraps` で実 builder を実行し、別 process の call count `(1,0)` を assert。`issue_receipt=False` | M には含めず M′ に追加 |
| shared-base の独立性・未完成再構築・lock 待機・process memo・4 key 分離 | `ODT:1069,1087,1107,1121,1173,1186` | `t080_small_cache_builder` で小さい代替 builder を使う | 両集合から除外 |
| shared-base の最終 participant / cleanup 群 | `ODT:1203,1220,1254,1270` | cache container や削除処理のみ | 両集合から除外 |
| temp-root 境界 | `ODT:1717` | builder を呼ぶが `ODT:1370` の入口 assertion で停止。構築しない | 両集合から除外 |
| snapshot 3 node | `ODT:579,597,623` | snapshot/ignore 境界のみ | 両集合から除外 |
| output copy 可視集合 | `ODT:1633` | 小型独立 repo 上で copy と production enumeration を比較。実 base は構築しない | 両集合から除外 |

`RST` 側にも同名 snapshot 検査があるため、抽出は basename の関数名だけで行わず、完全 nodeid で行う。

親の集合 probe は `RST:1197` の `expected_nodeids` を AST の literal として抽出し、prefix を正規化した後、`ODT:1285` の parametrization 展開および `observed_universe` と照合する。pytest collection を新たに起動する必要はない。

## 被覆対応表 (材料 1)

**列 (b) はすべて保留中で、受入では skipped。復帰しなければ現在の検出力はゼロとして数える。** `conftest.py:2230` は collection から消さず skip marker を付けるため、これらは C に残る。本調査では復帰させない。

表は次の単位で作る。

1. 性質・変異を一行にする。
2. `fixture 構築 → 変異 → production 呼出し → assert` を別々に記録する。
3. refusal は exact 集合、単一 reason、prefix/substring、単なる rc のどれかを明示する。
4. stub・`HELD=False`・入力 file 集合の注入を記録する。
5. 同じ reason 名でも、helper 直接検査と public 経路の結合検査を同一視しない。

下表は現物から確定できた初期表である。「未証明」は重複として計上せず、裁定上は e2e 側固有として残す。

| 検出対象 | (a) M の node：production 経路 / assert | (b) 保留中の実 repo 検査：潜在的被覆。現受入では 0 | (c) 毎走に残る非 e2e：production 経路 / assert | 分離すべき検出力 |
|---|---|---|---|---|
| known-axes raw bytes 改竄 | M2、`ODT:1835` → `MIG.verify_receipt:2284` → `_load_artifact`。HELD 中は valid＋marker、解除時は単一 `known_axes.artifact_bytes` | known-axes の one-byte 検査が保留表 `:381`。同じ T-080 public 経路の重複は未証明 | `MT:1264` `test_artifact_raw_bytes_are_checked_before_semantic_parse_m08` → `_load_artifact`、解除時に同 reason | bytes helper は重複。正規発行済み fixture と verifier 全体の結合は M 固有 |
| holdout raw bytes 改竄 | M3、同経路。解除時に単一 `holdout.artifact_bytes` | `HT:1367,1381` は CLI 正常系であり、この変異を assert しない | `MT:1264` の holdout 枝 → `_load_artifact`、同 reason | 同上 |
| current ccbench 不一致 | M4、`ODT:1835` → `verify_receipt`。checkout-only と committed gitlink の二状態、解除時に単一 `known_axes.ccbench_current` | known-axes foreign-pin 検査が保留表 `:351`。完全な結合被覆は未証明 | `MT:1179` → `_verify_ccbench_live` / `_verify_ccbench_basis`、`known_axes.ccbench_current` / `known_axes.ccbench_gitlink`。`MT:1381` は hold/release | reason・pin 比較は重複。実 receipt・履歴・worktree の結合は M 固有 |
| holdout unknownness layer2 | M5、fixture に三軸 conjunction を追加 → `verify_receipt` → `_verify_holdout_live_scan:2191` → production scan。単一 `holdout.unknownness_layer2`、observation 無し | `test_s8b_repo_scan_invariant.py:28` → `search_repository`、known hits exact と positive control >0。S8C の wave scan `:623` も production scan | `MT:527` は searcher を stub して frozen expressions 等の不一致を同 reason で拒否。`HT:702` は実 scanner/generate が `rr20: holdout hit` を拒否 | scanner 部品と検証条件は重複。実列挙から T-080 public verifier の exact reason までの結合は M 固有 |
| user commit trailer | M7、`ODT:2156` → `verify_receipt` → `inspect_receipt_history:2055`。単一 `receipt.user_commit_trailer` | この変異を直接 assert する対応 node は未確認 | `MT:677` `test_invalid_r_trailer_is_rejected_exactly` → `inspect_receipt_history`、同 reason の包含 | 履歴 predicate は重複。full-valid base 上で他 reason が混ざらないことは M 固有 |
| introduction diff | M8、同経路。単一 `receipt.introduction_diff` | 対応未確認 | `MT:644` → `inspect_receipt_history` で単一同 reason。後段 verifier は `_patch_full_gate_to_pass` を使う | 履歴 predicate は重複、stub-free 全体結合は M 固有 |
| modify→revert | M9、同経路。単一 `receipt.history_mutated`、observation 無し | 対応未確認 | `MT:697` → `inspect_receipt_history`、`receipt.history_mutated` と `receipt.schema_invalid` の 2 refusal | 改変履歴の検出は重複。「有効 receipt に対して一因だけ」は M 固有 |
| post-R delete の draft 拒否 | M10、`ODT:2182,2274` の隔離 subprocess → `draft_receipt:1934` → `_capture_draft_basis:1824`。`receipt.invalid`、detail に `issued-but-missing` | 対応未確認 | `MT:1028` → `_capture_draft_basis` 直接呼出し、`receipt.invalid`。`MT:687` は history state | precondition は重複。公開 draft 入口・現行 runtime loader の結合は M 固有 |
| never-issued generator tamper | M11、`ODT:4753` → `DRV.gate_check:587` → legacy `HD.verify:1142`。HELD 中は floor/budget のみ。解除時は known pin＋generator hash＋floor/budget の exact 集合。sentinel と call witness あり | `ODT:3450` は正常 receipt の gate、`:5054` は CLI 拒否 transport。generator 変異は assert しない | `ODT:4729` → `HD._verify_source` 直接、generator hash の exact 文言。`HT:803` → `HD.verify` の hold/release。`ODT:3518` は legacy verifier を stub | hash predicate は重複。never-issued 分岐から public gate への実到達は M 固有 |
| draft→finalize→commit→verifier→public gate | M1、builder subprocess `ODT:1568` 以降 → `draft_receipt` / `validate_draft:2000` / `finalize_receipt:2027` / commit / `verify_receipt` / `gate_check`。receipt valid、gate は floor/budget exact 拒否 | `ODT:3450` は実 repo の既発行 receipt と 17 observation、`HT:1367,1381` は CLI の held 表示 | `MT:630` は static gate 群を stub。`ODT:3518` も static checks を stub | 正常発行の全結合は M 固有。「gate allowed=True」の検査ではない |
| report による再導出・current receipt 欠落 | M1、`ODT:1810` 付近 → report `_campaign_t080_observation:276`。envelope 同一、削除後は malformed と exact issue | `ODT:3450` の実 repo observation 独立検算は別の性質 | 同一経路の重複未証明 | M 固有として計上 |

M6 の §1.4 は一括して「public verifier に対する負例」と書かない。`ODT:1924` は次の直接 helper 検査である。

| production 関数 | assert する reason | 毎走側との関係 |
|---|---|---|
| `_verify_known_closure` | `known_axes.source_closure` | `MT:263` の closure 検査を追加照合する。現段階では exact な同変異の重複は未計上 |
| `_verify_holdout_closure` | `holdout.design_closure` | 重複未証明 |
| `_verify_metadata_closure` | `receipt.repin_invalid` | 重複未証明 |
| `_verify_known_schema` | `known_axes.schema` | `ODT:2003` の static adapter 検査との経路差を追加照合 |
| `_verify_known_pairing` | `known_axes.pairing` | 重複未証明 |
| `_verify_ccbench_basis` | `known_axes.ccbench_gitlink` | `MT:1179` に同 helper・同 reason の重複あり |
| `_verify_reconstruction_static` | `receipt.reconstruction_invalid` | `MT:426,471` を追加照合。未計上 |
| `_validate_positive_control` | `holdout.positive_control` | `HT:694` の「陽性対照が 0 件」は scanner 側の別 predicate。代替と数えない |
| `_classify_ancestry` | `known_axes.ancestry_object_type` | `MT:1210` に実 Git blob を用いた同 helper・同 reason の重複あり |

列 (b) はさらに次の補助表を付ける。これは「復帰すれば代替になる」という提案ではなく、被覆差を明確にするための一覧である。

| 保留 node の所在 | 通す production 関数 / assert |
|---|---|
| `test_s8b_repo_scan_invariant.py:28` | `HD.search_repository`。rr80/rr20 の hit 集合が空の known ledger と一致、positive control >0。refusal reason の assert はない |
| `HT:1367,1381` | `HD.main` → `verify_cli_with_t080_receipt:1189` → `MIG.verify_receipt` / `static_gate_adapter:2424`。rc=0、`status=held`、`decision=freeze-verification-hold`、marker prefix |
| `ODT:3450` | production receipt memo → `gate_check`。floor/budget exact refusal、実 receipt と ancestry を含む observation の独立 golden |
| `ODT:5054` | CLI `run-block`。rc=2、`status=refused`、`_NO_ACTIVE_REFUSAL` exact、output/budget 不在 |
| `test_s8b_binding_driftguards.py:249,300` | `run_block` / `gate_check`。`manifest-verify: … binding_identity entry schema が不一致`、前者は prepare/evaluate 未呼出し・出力無し |
| `test_s8c_preregistration_invariant.py:389` | `validate_condition_freeze_at`、generation chain と hash 契約。T-080 refusal の直接 assert はない |
| 同 `:429` | 同 validator の `_batch_oids` 呼出し数・要求量境界 |
| 同 `:449` | candidate activation report、freeze valid と current decider version |
| 同 `:603` | ineffective、12 predicates、**C10 のみ SATISFIED**。関数名の “zero” を事実として転記しない |
| 同 `:623` | enumeration → conjunction hits → `search_repository` → `_assert_search_pass`、wave paths 可視・hit 無し・positive control >0 |

親は `MT` の観測済み **60 node** 全件について、上記の reason と呼出しを索引化し、保留表・JUnit terminal と突き合わせる。「同名 reason の helper が残る」ことと「M の全経路が残る」ことを分離する。この差が D700 の受理集合差の具体的内容になる。

## 利用時拒否の負例 probe 設計 (材料 2)

現行コードには、調べた入口で別系列完走記録・24h 判定を読む処理がない。ただし本段では実測していないため、**「負例拒否 0/6 を実測済み」とは書かない**。

また、現行の `gate_check` が floor/budget 等で既に拒否することは、D2002 条件 3 の成立を意味しない。観測項目を「操作全体の成否」と「系列未完走を理由とする拒否」に分ける。

親の job dir probe は次の二層とする。

| 利用面 | 現行挙動を採る最小手順 | 証明できる範囲 |
|---|---|---|
| 受入 wrapper の受領証 | `tools/dev_wave_wait.py:3720` の実処理を、`test_dev_wave_wait.py:2085` の `_FakeEffects` 正常系と同じ seam で駆動。別系列記録は置かず、受領証 publish 到達と payload を保存 | wrapper 判定に系列証跡が含まれないこと。偽の受入完走を公式証拠にしない。実受入を追加起動しない |
| land | `tools/dev_wave_land.py:970,1192,1203` の receipt 検証を、既存正常受領証と独立した期待 identity で呼ぶ。実 `land()` は呼ばず、参照用 fixture は `test_dev_wave_land.py:1009,2193` | land の受領証検証層に系列条件がないこと。実際に land 成功したとは主張しない |
| production | 親が選ぶ既知正常 root で `MIG.verify_receipt(root=...)`、`DRV.gate_check(root=..., freeze_path=...)` を実行し、state/refusals/held markers を保存。別系列記録は存在しない状態 | 実 production 呼出しが系列記録を要求しないこと。予想される `active-valid` や floor/budget 拒否は実測後に確定する |

`acceptance --check-only` は使用しない。fake seam の成功と production の実呼出しを同じ「実効性」の欄に混ぜない。実 repo の全件 scan が必要な呼出しを「必ず秒単位」とは見積もらず、親は実行場所・既存排他を確認する。保留 test 関数を直接呼んで保留を迂回する手順にもしてはならない。

最小完走記録の schema 案は次とする。

```text
schema_version
series_id
series_version
target_commit
expected_nodeids
selected_nodeids
finished_nodeids
terminal_by_nodeid
rc
started_at
completed_at
```

親側の系列定義から期待する `series_version` と M を得る。記録自身の `expected_nodeids` を権威にしない。判定仕様は以下とする。

- `target_commit` は利用対象 commit と一致する。
- `expected / selected / finished` は M と Counter で一致し、各 count=1。重複を set 化で隠さない。
- 各 M node の terminal は passed。skip/xfail・途中死・未報告を「完走成功」にしない。
- `rc=0`、全 terminal 適格、時刻の順序が正しいことを同時に要求する。
- 利用側が取得した UTC now と `completed_at` で 24h を判定する。起動側の「期限内」フラグや job ID は使わない。
- 欠損・不正 JSON・未知版・未来時刻は拒否する。
- 最新試行の失敗を古い成功が隠す運用にしない。最新試行と最後の適格完走の関係を明示する。
- 実用時は runner が観測した証跡から記録を作る必要がある。手書き JSON の正例が通っても、完走事実の真正性を証明したことにはならない。

判定器は **repo 外 probe の純粋関数仕様**として提示する。本 wave では production 判定器・配線を実装しない。

| case | 正例からの変更 | 期待結果 |
|---|---|---|
| 記録不在 | file 無し | `series.record_missing` |
| 期限切れ | 完了を now−24h−1s にする | `series.expired` |
| commit 不一致 | 別の完全 SHA | `series.commit_mismatch` |
| node 集合不一致 | M の 1 node を欠落／余剰に置換 | `series.node_set_mismatch` |
| rc=0 だが未完走 | selected=M、finished を 1 node 欠落 | `series.incomplete` |
| 失敗あり | 1 terminal を failed にする。rc=0 の矛盾形も拒否 | `series.failed` |
| 正例 | exact commit/version/M、全 node passed、完了から 1h | accept |

各負例は一因ずつ変える。親の出力には入力 hash、期待結果、実結果、拒否理由、時刻、対象 commit を残す。模擬 6/6 拒否＋1/1 受理が得られても、**production 配線前の実効性は未成立**と記す。

判定器を置ける場所と迂回路は次のとおり。

| 入口・consumer | 候補位置 | 単独配置で残る迂回路 |
|---|---|---|
| wrapper 受領証 | `tools/dev_wave_wait.py:3634` publish 前。受領証生成元 `tools/acceptance_launcher.py:477` の scope 記録とも整合 | wrapper を通らない production 利用。古い receipt を読む land |
| land | `tools/dev_wave_land.py:1203`。`:5770,6110` の再検証時にも有効期限を再評価 | production 直接呼出し。tested tip と landing tip/forward merge の関係も別途定義が必要 |
| consumer 1：driver receipt resolver | `DRV:169`、公開入口 `gate_check:587` | resolver を通さない下記 consumer |
| consumer 2：driver adapter | `DRV:299` → `MIG.static_gate_adapter:2424` | 呼出し側が古い resolution を渡せる。`verify_receipt` だけの guard では捕まらない |
| consumer 3：driver CLI | `DRV:2037` | Python API 直接呼出しが残るため CLI のみの guard は不十分 |
| consumer 4：holdout CLI receipt 解決 | `HD:1210`、外側入口 `verify_cli_with_t080_receipt:1189` | `HD.verify:1142` 直接利用・never-issued legacy 経路 |
| consumer 5：holdout CLI adapter | `HD:1247` | adapter API 直接利用 |
| consumer 6：floor protocol freeze | `s8b_floor_campaign.py:1419,1440` | `receipt_verify_fn` seam がある。MIG 内だけに置く guard はこの入口を完全には覆わない |
| consumer 7：historical report | `s8b_oracle_report.py:243,246` | `inspect_receipt_history()` を使い、`verify_receipt()` を通らない |
| consumer 8：current report | 同 `:2364` | 同上。report を検証済みとして利用する外側境界にも判定が必要 |
| receipt 発行 API | `MIG:1934,2000,2027`、CLI `:2524` | CLI だけでは draft/finalize API 直接呼出しが残る |
| verifier API | `MIG:2284` | history / adapter 直接利用、注入済み resolution |

8 箇所は独立した 8 公開 API ではなく、同一経路内の呼出し箇所も含む。親は入口ごとに到達図を作り、guard を通らず同じ検証済み成果を得られる経路が一つでも残れば「実効性が部分的」と報告する。

`inspect_receipt_history` など診断用 primitive 自体を全面停止すると修理や系列自身が起動できなくなる。診断・系列実行は許し、そこから検証済み成果の発行・有効化へ昇格する境界で拒否する設計が必要である。この境界設計は裁定材料とし、本 wave では実装しない。

## shard wall の見積もり手順 (材料 3)

指定 session の 3 report は `observed_universe` が一致し、各 **24,597 record**。現行台帳は **24,379 entry**。`AS:61` の `_DURATION_LEDGER_PATH` は当該 worktree の台帳を指す。

親が job dir に保存する再現 probe の仕様は以下とする。

1. HEAD、台帳 hash、3 report/JUnit の hash と session ID を記録する。
2. `AS.parse_records()` で C を読む。M/M′ の全 node が一度ずつ存在することを確認する。
3. C、C−M、C−M′ に対し `allocate(records, 3)` を呼ぶ。
4. 除外なしの割付が保存済み selected と一致することを確認してから比較する。
5. 各 shard の loads、node 数、components の files/groups、ODT 残存 node の所属、台帳未登録数・fallback 数を出す。
6. weights は `AS:392` の nodeid→`nodeid@group`→1秒という lookup をそのまま使う。
7. 各 shard の残存最長 node と、固定 group/affinity による鎖を別出力する。

本段で再計算した値は次のとおり。これは実走時間ではない。

| 実行母集合 | shard-0 load | shard-1 load | shard-2 load | selected 数 |
|---|---:|---:|---:|---|
| C | 7501.531 | 5328.283 | 5328.282 | 3908 / 11415 / 9274 |
| C−M | 5285.365 | 5285.366 | 5285.365 | 6700 / 10028 / 7858 |
| C−M′ | 5235.365 | 5235.367 | 5235.364 | 7240 / 9683 / 7662 |

`AS:325` は file を頂点とし、file↔group、および宣言済み group conflict edge を union する。同一 file の group 無し node もその成分へ入る。したがって ODT の **147−11=136 node、うち group 付き 6 node** は C−M でも shard-0 に残る。M′ なら 135 node。

該当大成分は 25 files、次の 4 groups を含み、重みは `7501.531 → 5199.531 → 5049.531` 秒となる。

```text
campaign-repository-scan
real-repo
s8c-predicate-snapshot
s8c-preregistration-candidate
```

files はすべて `orchestrator/tests/` 配下である。

```text
test_acceptance_schedule_order.py
test_calibration_freeze_stage6_candidate_gate.py
test_campaign.py
test_campaign_import_invariant.py
test_codex_reasoning_ab.py
test_hooks.py
test_p3_s4_loop.py
test_p3_s4_loop_sort.py
test_p3_s4_loop_trigger_gating.py
test_real_repo_serialization.py
test_ruleops.py
test_s1_9pair_figure_provenance.py
test_s1_known_axes_freeze.py
test_s1_measurement_freeze.py
test_s8b_binding_driftguards.py
test_s8b_floor_campaign.py
test_s8b_oracle_driver.py
test_s8b_protocol_builder.py
test_s8b_repo_scan_invariant.py
test_s8c_preregistration_invariant.py
test_s8c_preregistration_predicates.py
test_sort_swo_oracle.py
test_t1259_qsub_env_delivery_probe.py
test_t810_coordinator.py
test_verifier.py
```

M 除外後は空いた shard-0 に他成分が再配分される。単純な `7501.531−2302` を shard-0 全負荷として使わない。

残存最長 node は両候補とも次である。

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module
```

現行台帳値は **170 秒**。次点は known-axes の 160 秒、M では shared-base の 150 秒も残る。

モデル α は指定された比例換算とする。

\[
W_i' = W_i \times L_i'/L_i
\]

| 候補 | shard-0 | shard-1 | shard-2 | 最遅予測 |
|---|---:|---:|---:|---:|
| M | 238.0秒 | 247.2秒 | 202.4秒 | 247.2秒 |
| M′ | 235.8秒 | 244.9秒 | 200.5秒 | 244.9秒 |

このモデルは固定費まで比例で減らすため、特に shard-0 で楽観側になりうる。

モデル β は次とする。

\[
W_i'=P_i+D_i+\max(T_{\max,i}',R_i',L_i'/E_i)
\]

- P：collection 等の前処理。
- D：collection 完了から実行開始までの待ち。
- R：real-repo lock interval の時間的 union。
- E：実効 worker 数。48 をそのまま使う場合と観測 occupancy から求める場合を併記する。

親の lock union probe は `session_timeline.workers[*].real_repo_lock_intervals` の全区間を開始順に並べ、重なる区間を結合して長さを加算する。worker ごとの保持時間の総和と混同しない。

指定 session を再計算した結果：

| shard | worker 数 | test span | lock union | occupancy 総和 / span |
|---|---:|---:|---:|---:|
| 0 | 48 | 272.348秒 | **231.863秒** | 31.462 |
| 1 | 48 | 171.535秒 | 0秒 | 28.208 |
| 2 | 48 | 125.373秒 | 0秒 | 38.273 |

shard-0 の JUnit wall は 337.860 秒なので、span 外は約 **65.512 秒**。collection→first test は約 0.020 秒であり、T-2559 の dispatch 29.6 秒をこの走の実測値として流用しない。

M 除外後に R を維持すると仮定した shard-0 の感度は以下になる。

- P=60、D=0、R=231.863：**約291.9秒**。
- 指定 session の span 外 65.512 秒を維持：**約297.4秒**。
- T-2559 型の別待ち約29.6秒が再発：**約327秒**。

M′ にしても、このモデルでは lock union が支配すれば wall はほぼ変わらない。なお、元 session の R は移動後の R の実測ではない。interval に node 対応がないため、M の秒を機械的に差し引くこともできない。

裁定パッケージには、**比例モデルの約245〜247秒と、lock・固定費を保持するモデルの約292〜327秒という条件付きの幅**を示す。これは統計的信頼区間でも上下限の保証でもなく、「300秒を切る」とは断定しない。

peer T-2750 が file→node の成分粒度変更を land した場合は、この union・残存 136 node の束縛・割付数値を失効させ、同じ M と新 allocator で再計算する。

## D700 却下理由の現状

| 却下理由 | 材料によって変わりうる点 | 現時点の判断 |
|---|---|---|
| 定期実行基盤がない | 起動・完走記録・独立期限検知・停止時拒否までを用意できれば前提は変わる | 起動基盤も監視も本 wave では新設しない。却下理由は未解消 |
| opt-in の改名になる | D2002 の 4 条件が実装・実測され、未起動が利用拒否に結び付けば「走らなくても何も止まらない」状態は変わりうる | repo 外判定器の 6/6 拒否だけでは解消しない。production 全入口、独立期限検知、関連変更時焦点走が必要 |
| helper と e2e の受理集合が異なる | 材料1により bytes・pin・履歴など predicate 単位の重複は具体化できる | stub-free 発行・public verifier・legacy gate・report 再導出の結合は残る。保留列の潜在被覆では補えない |

材料3は費用判断を更新するが、材料1の検出力差を消すものではない。D700 当時の最長 51.43 秒という費用根拠は現在の台帳・実測と異なる一方、F485 の「未実行が露見しない」という失敗条件は現在も対策が必要である。

## 裁定パッケージの骨子

| 選択肢 | 必要な実装・成立条件 | 費用 | 毎走から失うもの | 得られる可能性 |
|---|---|---|---|---|
| 別系列化しない | 現行 C 全体の実行と D701 を維持 | 新基盤不要。現行受入費用を継続 | なし | 本案による短縮なし |
| 別系列化する | **移動前に** D2002 の 4 条件を成立。D2003 の U 分離、完走証跡、期限検知、利用拒否、関連変更焦点走 | scheduler/runner/証跡管理/期限検知/入口配線/修理経路の設計・検証。M の実行費用自体は別系列に残る | 材料1の M 固有結合検出を、各受入走で観測する機会 | M：比例約247秒、lock 等を残す条件で約292〜327秒 |
| 条件付き | 材料を承認し、上記機構の実装・負例実測を満たすまで M を毎走に残す | 段階的な設計・実装費用。完成前の速度利得なし | 条件成立前はなし。成立後は M と同じ | 検証後に再見積もり |
| M′ を選ぶ追加裁定 | M の条件に加え shared-base 検査の系列所属を定義 | 別系列に 150 台帳秒追加。cache 配線検査の毎走欠落を評価 | process 間「実 builder 1回」の検査も移る | 比例約245秒。lock 支配なら M に対する wall 利得はほぼない |

D2003 の実装範囲は gate 4 の等式置換だけでは足りない。

- `AS:506` と `merge_reports:622` の gate 2/3 は引き続き **C 全体**を比較する。
- `AS:688` 付近の gate 4 は、親が C と系列定義から再導出した **U=C−M** への exact partition とする。
- allocator・selection・`assignment_closure_gate` の対象を U と整合させる。M を含む C をそのまま閉包検査へ渡して、同一 file の部分実行を誤拒否しない設計が必要。
- gate 5 の finished=selected、terminal 検証、残り gate と fallback 禁止は維持する。
- 受領証には毎走の検査範囲 U と、別系列証跡の対象 commit/version/freshness を区別して記録する。後日の M 完走を当該受入での実行として扱わない。
- `SANCTIONED_EXCLUSIONS` は空かつ汎用除外機構ではないため流用しない。

D701 との整合は明記する。`RST:1051` は module 全体の collect-only と、対象 11 node の setup-only を別走で実行する。**collection を保った D2003 型の実行分割はこの probe を通りうる**。D701 の維持は必要だが、毎走で M 本体が実行されたことの保証にはならない。M′ の追加 node も既存 D701 の保証対象外である。

関連変更時焦点走の対象には、少なくとも M の test/helper、MIG、DRV、HD、report/floor consumer、共有 fixture/cache、系列 schema/判定器、selection/receipt 配線を列挙する。具体的な変更分類と target commit の扱いは、採用時の設計事項として残す。

## リスクと未確定点

- **M 除外だけでは real base 構築は消えない。** `ODT:1047` は独自の `t080_shared_cache_probe` を使い、実 builder を `issue_receipt=False` で呼ぶ。M と helper 実装は共通だが、この検査の cache は独立しており、150 秒が残る。
- **台帳秒は仕事量そのものではない。** fixture の cache 待ち、I/O、lock 待ち、process scheduling が混ざる。2,302 秒を CPU 節約や総計算費節約と呼ばない。D357 に従う。
- **1 session の比例は脆い。** shard-0 の負荷構成が大きく変わり、他 shard から仕事が流入する。worker 実効数も一定とは限らない。
- **lock union の将来値は未観測。** 元 interval の union は再計算できても、M 除外後の競合・開始順の変化は再現しない。D358 の排他再設計は扱わない。
- **全件 scan と実 repo 直接 scan は同値ではない。** fixture は output 等を複製し、historical basis と現行 runtime を組み合わせる。T-2559 の可視 file 差や observation 17件中15件の独立検算範囲も残る。
- **模擬判定器は配線の証拠ではない。** 6負例を拒否しても、wrapper・land・report・API の迂回路と証跡真正性が未解決なら実効性は部分的。
- **自己停止の循環がある。** M 自身が未完走を理由に検査対象 API から拒否されると初回完走できない。診断・系列実行と検証済み利用の境界が必要だが、単なる環境変数 bypass にしてはならない。
- **commit 一致と land の整合が未設計。** tested tip、forward merge 後 tip、実際に有効化する版が違う場合に、どの commit の完走を要求するか決める必要がある。
- **独立期限検知は利用時判定だけでは完結しない。** 利用がない期間にも未起動・queue 停止・途中死を検知する経路が必要。
- **計算ノードへの別系列投入経路は未設計。** generic dispatch / PBS、完走回収、queue 停止時の扱い、関連変更焦点走との統合費用を採否に含める。
- **費用の精密値は未確定。** 実装工数や別系列の実 wall を、台帳合計から推定して確定値として出さない。

## 総括

P1 の M=11 node は確定できる。M′=12 node を感度分析として併記する。ただし shared-base 群全体は13 node、残存最長の台帳値は170秒、指定 session の lock union は231.9秒へ訂正する。

材料1では predicate 単位の重複と、M 固有の stub-free 結合検出を分離する。保留中の実 repo 検査は現在の代替被覆として数えない。材料2は親による現行入口の観測と repo 外判定器の負例実測が未完了であり、実効性成立とはまだ言えない。

材料3の再計算では、M 除外の最遅 wall は比例モデルで約247秒、lock・固定費を残す条件で約292〜327秒となる。300秒未満は保証できない。これらを揃えて「別系列化する／しない／条件付き」を諮り、本 wave では実装も実行集合の変更も行わない。