## 実装の要約

[ scratch/t2812_old_series_probe.py ](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2812-probe-author/scratch/t2812_old_series_probe.py) を作成しました。指定順の全 check、create-only 出力、例外全文、所要時間を実装しています。cell ごとの失敗は入れ子の entry に保持します。

以下の `C` は完全修飾名の共通接頭辞 `orchestrator.campaign` です。

| check | 呼出し・kwargs |
|---|---|
| K2-PIN-NEW / H | `C.patchharness.assert_pinned_clean(sub, C.p3_s4_loop.PIN)` |
| POLICY-CURRENT | `C.build_admission.resolve_current_build_admission_policy()`、`sha256`・`as_preimage()`・指定定数 |
| K2-LOCK-PAIR | `C.campaign_lock.decode_campaign_lock(text)`、`C.ident.ADMISSION_POLICY_SEARCH_KEY` で policy を抽出・比較 |
| A1-BOUNDARY-NEW / H | `C.paper_story_a1_paired._load_policy_for_study(STUDY)`、`C.paper_story_a1_paired._assert_ccbench_acceptance(root, policy, boundary="login-submit")` |
| A1-SOURCE-NEW / H | `C.paper_story_a1_source.load_contract(repo_root, STUDY)`、`C.patchharness.assert_pinned_clean(sub, canonical_head)` |
| A1-IDENTITY | `json.loads()` で埋込み JSON を再帰 decode、policy 差分だけを抽出 |
| G1-LOAD | `C.s8b_ratified_freeze.load_ratified_freeze(root)` |
| G1-LAUNCH | `C.s8b_ratified_freeze.launch_validate(ratified, root)` |
| G1-BINARIES | `C.s8b_ratified_freeze._source_record_path_sha(document, role)`、`_parse_official_run_path(result_path, expected_basename="result.json")`、`_capture_g_h_worktree(generation_commit=G, validation_head=HEAD, path=path, root=root)`、`_strict_load(raw, what=role)`、`_validate_published_protocol(document, contract_resolver=_resolve_current_contract_sha256)` |
| G1-BIN-HIST / CURRENT | `C.s8b_binary_admission.validate_portable_binary_record(record, expected_policy=None／現行policy, **段階4の照合kwargs)` |
| B4-PROTOCOL | `C.s8b_floor_campaign.resolve_current_floor_protocol(root=root)`、`_scan_floor_protocol_index_at_commit(root=root, commit_oid=HEAD)`、`_ccbench_gitlink(root, HEAD)`、`C.env_contract.lookup(env_tag)` |
| B4-RECORD-HIST / CURRENT | `C.s8b_binary_admission.validate_portable_binary_record(record, expected_policy=None／現行policy)` |
| B4-W1-HEAD | Git HEAD 読取り、`json.loads(stream.readline())["loaded_head"]` |
| READMIT-STOCK | `C.source_digest.SourceEvidence.from_receipt(recorded_source)`、`C.build_admission.build_run_context(generator_id=GeneratorId.BACKOFF_OVERTHROTTLE)`、`C.build_admission.derive_build_admission(context, evidence)`。非 stock は registry 照合のみ |
| READONLY | 指定の Git status、submodule HEAD、binary store 存在有無を前後比較 |

段階4の kwargs は `expected_ccbench_pin`、`expected_contract_sha256`、`expected_cell_id`、`expected_holdout_id`、`expected_configuration_id`、`expected_entry_sha256`、`expected_binding_sha256` と `expected_policy` です。

## read-only の根拠

- PIN・A1 boundary・READONLY：Git の状態読取り。`GIT_OPTIONAL_LOCKS=0` を設定。
- policy・lock・identity・contract：既存ファイルの読取りとメモリ内比較。
- G1 loader・launch・binary 検査：production の読取り検査関数を直接使用。manifest・protocol 本文は出力しません。
- B4 protocol・record：既存 protocol・receipt の検証だけで、store／place／produce は呼びません。
- W1：各 JSONL は `readline()` 1 回だけです。
- READMIT：記録 source を変更せずメモリ内で評価し、receipt を保存しません。
- `sys.dont_write_bytecode=True` を設定。probe の書込み先は排他的に作成する `--out` だけです。

## 実走結果

**全 check 未実走です。**

- Python 3.10 構文確認：成功。
- `python3 -m py_compile`：成功。bytecode 出力先は `/tmp/t2812-probe-author-pycache`。
- 最終 Git status：新規 probe 1 ファイルだけ。
- test・docs・commit：作成していません。

## 未了・懸念

- 実走による各 check の結果と read-only 前後一致は未確認です。
- manifest path は推測ではなく、`_launch_validate` の式と production の `_RUN_BASENAMES` を使用しています。独立した path 解決 helper はありません。
- `--out` は baseline status の取得前に予約します。その許可済み作成を前後差分へ混入させないためです。
- nested check が失敗した場合、親 entry も `ok=false` とし、`result.checks` に個々の例外全文を残します。

## 総括

指定の probe 1 本を実装し、コンパイル確認を完了しました。**実装済み・未実走**として引き渡します。

実走は PreToolUse の `guard_bash` が拒否しました。理由は「program／script の中身を追えない、または書込み・外部実行の構文を含む」です。制約の迂回は行っていません。