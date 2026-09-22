**知識解決以外は実装済み・未実走です。** 指示間の衝突が1点残っています。既存の `KM.load_and_resolve_manifest()` は内部で `subprocess.run(["git", ...])` を呼ぶため、「既存関数を使う」と「toolはsubprocessを起動しない」を間接呼出しまで含めて両立できません。確認への回答がないため、`knowledge_input()` は明示的な `NotImplementedError` で停止させています。

**1. 着手前の現行挙動**

試走版の入出力は次のとおりです。

| subcommand | 入力 → 出力 |
|---|---|
| `inputs a` | request・台帳・知識・直前critic → request写し、planner入力／prompt、coder skeleton |
| `coder a` | planner逐語・skeleton → coder入力／prompt |
| `proposal a` | planner／coder逐語・保存済み入力 → 検査後、handshakeへ inputs → proposal |
| `reject a reason` | 理由 → `proposal-a.rejected.json` |
| `critic k job window` | slot・digest → critic入力／prompt |

固定箇所は `REPO`、`J`、`MAT`、`LEDGER`（`B5_LLM_LEDGER`による例外あり）、`HANDSHAKE`、`MANIFEST`、`KI_R2`、`LEAKPROOF` とcontextのhash。文面には「試走」「T-2797」「write-heavy 系列1」、rr5の動作点、stockを「同時刻対照」とする説明、欠測CVを0にする式があります。

driverは `request-<a>.json`、`inputs-<a>.json`、`proposal-<a>.json`、`proposal-<a>.rejected.json`、`slot-<k>.json` を使います。継承検査は、評価番号の連続性、whiteboard、直近のcertified・品質正常値によるcurrent_perf／baseline、初回の診断不在、以後の両入力の同一6項目診断を確認します。

知識解決は指定commitのblob種別・raw hashを検査し、sourceを正準順に並べます。manifestの正準digestが指定値に一致し、`planner_projection` を `ensure_ascii=False, sort_keys=True, indent=2` でUTF-8化したbytesが照合先と一致することが条件です。元scriptと照合先の指定SHA-256は一致しました。

**2. 作成ファイル**

- [tools/b5_llm_round.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/tools/b5_llm_round.py)：534行。context描画は156–175行付近、`RoundTool`は196行、各変換は220行以降、`record_models`は412行、7 subcommandのCLIは478行。
- [orchestrator/tests/test_b5_llm_round.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/orchestrator/tests/test_b5_llm_round.py)：340行、13 test node。fixtureは一時dirへ作成し、自走入口も追加。

所有外のrepoファイルは編集せず、commitも実行していません。

**3. 試走版からの変更**

- D-3(1)：headerのpurpose・cohort・workload・seriesからラベルを生成。
- (2)：動作点とcontextを実体の `calibrated_perf()` から整形。共通説明・文法・知識集合は保持。
- (3)：stockの逐次測定を明記。
- (4)：coderの「B-5 試走」を「B-5 本走」へ変更。
- (5)：欠測CVを `null (欠測)` に変更。
- (6)：repo rootを `__file__` から導出し、各root／manifestを引数化。
- (7)：repo内の照合先定数は追加済み。**知識解決・bytes照合の接続は未完**。

その他の差は、`record-models`追加、クラス／argparse化、台帳sourceの読取りを`SeriesLedger.events`へ変更、公開を一時file＋hard linkによる上書き拒否へ変更、単独ファイル名への出力対応です。欠測表現の要求に合わせ、criticの他の欠測指標・反復数も `null (欠測)` にしています。これはCV以外にも及ぶ差として明記します。

**4. 静的検査**

- `PYTHONPYCACHEPREFIX=/tmp/t2797-eb-unit-b-pycache python3 -m py_compile tools/b5_llm_round.py orchestrator/tests/test_b5_llm_round.py`：**rc=0**
- `python3 -B`による両ファイルのAST解析・末尾空白確認：**rc=0**、末尾空白なし。
- `sha256sum`による元script／知識照合先確認：**rc=0**、指定値一致。

テスト・docs checker・provenance監査は実行していません。

**5. meta-testの静的確認**

| 対象 | 影響・対応 |
|---|---|
| `test_plain_runner_coverage.py` | 新testが対象。`__main__ → _run()` の定型を追加 |
| `test_ccbench_spawn_sites.py` | process目録の走査先はcampaign／calibrator。新規spawn siteなし。既存KMのGit siteは登録済み |
| `test_hooks.py` のadmission検査 | `tools/pegasus/`外への新tool追加による登録変更なし |
| `test_login_headroom.py` | toolsもAST走査するが、資源上限定数を追加していない |
| `test_pegasus_dispatch_compute.py` | toolsも走査するが、qdel関連参照なし |
| `test_check_docs.py`／`check_docs.py` | tools README・指定入口・registryを検査。`tools/*.py`全件を列挙登録する要求なし |
| `test_t338_submission_gate_unit5.py` | repo全体のreceipt発行呼出しを走査。対象APIの呼出しなし |
| materialization／WAL／B4／floor系の閉集合検査 | 主にorchestrator productionを走査。対象経路の追加なし |

以上は静的判断であり、通過実績ではありません。

**6. MB1〜MB8の対応**

以下はすべて新testファイル内です。

| 変異 | test node／検出箇所 |
|---|---|
| MB1 | `test_context_uses_calibrated_workload`：3 workloadのCLI出力で表・測定文を確認 |
| MB2 | `test_rejected_opportunity_preserves_evaluation_number`：拒否後のa=3／k=2でcritic-1と評価番号を確認 |
| MB3 | `test_initial_and_inherited_inputs`：初回診断なし、以後の両入力と実継承検査 |
| MB4 | `test_critic_missing_metrics_remain_missing`：欠測CVと実測0を別々に描画 |
| MB5 | `test_models_collect_all_assistant_ids`：異なるmodel IDが混在する3 assistant行 |
| MB6 | `test_model_record_metadata_and_raw_hashes`：meta両fieldとraw bytesのhash |
| MB7 | `test_model_record_flags_mismatch`：正常対照、別ID・role不一致・欠落・破損とrc=0 |
| MB8 | `test_registered_round1_prompt_golden`：保存promptへの独立した`bytes.replace`期待値 |

**現在、MB2・MB3・MB8は未完の知識解決で先に停止します。変更箇所への到達やKILLEDを達成済みとは報告できません。** goldenの置換で表せない実差も未確認です。

**7. 所有外への波及**

既存caller・共有fixtureの変更は不要です。親は新CLIへroot／manifestを渡し、逐語を所定のmaterials layoutへ配置する必要があります。既存driver・K2 loader・射影・文法関数をそのまま参照しています。試走insightは読取り専用fixtureであり、model記録は既存reportのgateへ接続していません。

**8. 親が実走する候補**

知識解決の未完を解消した後、計算ノードで以下を候補としてください。

- `orchestrator/tests/test_b5_llm_round.py` 全体と、上記MB1〜MB8の各node
- `test_plain_runner_coverage.py`
- `test_b5_generator_contrast.py`
- `test_ccbench_spawn_sites.py`
- admission／docs／資源規約の関連node

**実装済み部分も未実走です。実行時間が数秒に収まることも未測定です。**

## 総括

2ファイルを作成し、構文検査は通りました。完成を阻んでいるのは知識resolverの間接process起動に関する指示の衝突です。**既存resolver内の読み取り専用 `git cat-file` 起動だけを許容できるか、ご指定ください。** 許容を推測せず、該当部分を明示的に未完として残しています。