静的検査のみで起草した。実装、ファイル編集、pytest 実走は行っていない。以下の行番号は現状の行番号である。

### 1. 材料の運搬経路

`tools/acceptance_launcher.py:_launch` が、既存の main/tip 等値検査後に束縛 session を生成する。

- `tools/acceptance_launcher.py:436-440` の同じ `source: bytes` から、SHA-256 と canonical manifest を作る。
- manifest は受領証や作業ツリーではなく、`config.log_file.parent` 配下の launcher 所有 directory に置く。production では `tools/dev_wave_wait.py:2368-2382` が log を repo 外と検査済みだが、launcher 側でも `config.repo_root` 外、canonical absolute path、非 symlink、mode `0700` を再検査する。
- manifest の exact fields は次とする。

```json
{
  "schema_version": "dev-wave-runner-binding-manifest/v1",
  "tested_main": "<40 lowercase hex>",
  "runner_sha256": "<64 lowercase hex>",
  "runner_source_b64": "<canonical base64>",
  "session_nonce": "<64 lowercase hex>",
  "shard_count": 1
}
```

環境変数は次の 3 本だけとする。

- `IZANAGI_ACCEPTANCE_RUNNER_BINDING_MANIFEST`: manifest の canonical absolute path。
- `IZANAGI_ACCEPTANCE_RUNNER_BINDING_MANIFEST_SHA256`: canonical manifest bytes の SHA-256、64 桁 lowercase hex。
- `IZANAGI_ACCEPTANCE_SHARDS`: launcher が確定した `1`、`2`、`3` のいずれか。

`tools/acceptance_launcher.py:199-227` の `_run_blob` に `environment: Mapping[str, str]` を追加し、`subprocess.run(..., env=environment)` とする。現状は `env=` がないため暗黙継承だが、変更後は `dict(os.environ)` に上記 3 値を重ねた明示環境を渡す。`blob_runner` の注入 seam も 4 引数へ合わせる。

無編集の `tools/run_tests.py` では、この環境が次のまま login dispatcher へ届く。

- `tools/run_tests.py:1295-1304`: `_dispatch_environment` が `os.environ.copy()` を作り、上記 key は削除しない。
- `tools/run_tests.py:1320-1324`: `_default_dispatch` がそれを `environ=` へ渡す。
- `tools/pegasus/dispatch_compute.py:2796`: login 側 `_dispatch_impl` が `command_env` として受け取る。

dispatcher は `tools/pegasus/dispatch_compute.py:2796` 直後で 3 key を取り出して `command_env` から削除する。manifest を exact set、canonical JSON、size 上限、外部 directory、SHA-256、base64、main SHA、K の一致まで検証し、runner bytes を一度だけ復元する。

計算ノードへの運搬は `environment` ではなく、`tools/pegasus/dispatch_compute.py:2857-2864` の request payload に optional な専用 object `runner_binding` として載せる。report directory の path は載せない。

`tools/pegasus/dispatch_compute.py:977-994` の `requested_env` / `unexpected_env` 検査、および `TASKS["tests"].env_allowlist` (`:113-130`) は変更しない。新 key は `request_env` を構築する `:2797-2800` より前に dispatcher 自身が消費するため、D397 の allowlist 追加条件は発火しない。consumer は `_dispatch_impl` に実在するが、allowlist の key、値意味論、受理集合は一切広げない。

### 2. dispatcher 側の束縛実装

`tools/pegasus/dispatch_compute.py:99-108` 付近に immutable な manifest/request binding 用 dataclass と検証 helper、`:160-174` 付近に schema、環境変数名、size 上限、compute bootstrap 定数を置く。`base64` import は `:10-26` に追加する。

login 側の発火条件は次の exact 条件とする。

```python
is_bound_runner = (
    task == "tests"
    and spec.argv_policy == "passthrough"
    and spec.child_script == ("tools", "run_tests.py")
    and manifest_environment_is_complete
)
```

- 2 本の manifest 環境変数が両方ない場合は、既存 caller と P 自身の旧 launcher のため現行 pathname 起動を維持する。
- 片方だけ、manifest 不正、manifest K と `IZANAGI_ACCEPTANCE_SHARDS` の不一致なら、`tools/pegasus/dispatch_compute.py:2697-2710` と同じ qsub 前の fail-closed にする。
- manifest があっても mutation、generic、provenance では binding object を作らず、3 key を子環境から除くだけにする。
- 新 launcher は必ず manifest を作り全 report を要求するため、authoritative acceptance が manifest 無しを逃げ道にはできない。

`tools/pegasus/dispatch_compute.py:2857-2864` では、上記条件成立時だけ request に次を追加する。

```json
"runner_binding": {
  "schema_version": "dev-wave-runner-binding-request/v1",
  "tested_main": "...",
  "runner_sha256": "...",
  "runner_source_b64": "...",
  "session_nonce": "...",
  "shard_count": 3,
  "shard_index": 0
}
```

この object は既存 `request_text` と同時に `:2865-2868` の request SHA-256 へ束縛される。

計算ノード側では `tools/pegasus/dispatch_compute.py:945-978` で request を読んだ直後に exact fields と型を再検査する。binding があるのに task 条件が上記 exact 条件でなければ拒否する。

同一 buffer 束縛は、`:1009-1022` を次の 2 分岐にすることで保証する。

- binding 無し: 現行 `child_argv` と `subprocess.call(..., stdin=subprocess.DEVNULL)` をそのまま使う。
- binding 有り: strict base64 decode で得た単一の局所変数 `source: bytes` に対し、同じ helper 内の隣接した文で
  `actual_digest = hashlib.sha256(source).hexdigest()` と
  `subprocess.run(..., input=source)` を行う。別 path からの再読や期待 digest の代入を挟まない。

binding 時の argv は次とする。

```python
[
    sys.executable,
    "-I",
    "-c",
    _RUNNER_BOOTSTRAP,
    str(repo_root / "tools" / "run_tests.py"),
    *argv,
]
```

bootstrap は stdin を一度だけ読み、`__file__` を canonical runner path として compile/exec し、`main(sys.argv[2:])` を呼ぶ。pathname は traceback と `_REPO` 導出にだけ使い、source の再読には使わない。

`runner_sha256` と `hashlib.sha256(source)` が違えば subprocess を一度も起動しない。compute result の `runner_binding` 申告にも、manifest の期待値ではなくこの `actual_digest` を入れる。

`tools/pegasus/dispatch_compute.py:1030-1043` の `result.json` 書き込みは、既存 `_write_json_x` から `:456-493` の atomic replace helper へ変える。被検査 child が実行中に `result.json` を先に作っても、child 終了後の dispatcher 書き込みが置き換える。

### 3. 申告 channel

launcher は manifest と同じ repo 外 directory を report channel として所有する。directory 名と session nonce は `secrets.token_hex(32)` から生成し、launcher 以外は report directory path を authority として決めない。

compute result に含める申告は exact object とする。

```json
{
  "schema_version": "dev-wave-runner-binding-report/v1",
  "tested_main": "<40 hex>",
  "runner_executed_sha256": "<actual source digest>",
  "session_nonce": "<64 hex>",
  "shard_count": 3,
  "shard_index": 0
}
```

login dispatcher は `tools/pegasus/dispatch_compute.py:3440-3459` で、PBS job ID、stage、request SHA-256、child rc を検査した後、compute result の report を request binding と照合する。成功した場合だけ、launcher directory に `binding-report-<fresh 32 hex>.json` を atomic replace で書く。index だけを filename にしないため、重複 index の別 dispatch は 2 file として残り、launcher が検出できる。

D859 への対応は次の 3 層にする。

- report directory path は compute request、argv、`requested_env` のいずれにも載せない。login dispatcher の局所 state にだけ保持する。
- `tools/pegasus/dispatch_compute.py:684-687` の job script で manifest 2 key と `IZANAGI_ACCEPTANCE_SHARDS` を unset し、`:999-1006` の `child_env` でも冗長に pop する。
- `result.json` と最終 report は child 終了後の atomic replace。child が同名 regular file を先に作っても trusted writer の公開は失敗しない。launcher は directory fd と `O_NOFOLLOW` で regular file、link count、size 上限、canonical JSON を読む。

shard index の authority は既存経路を使う。

- `tools/run_tests.py:2323-2341`: `acceptance_shards` の `intent_shard_index` を `_default_dispatch` へ渡す。
- `tools/run_tests.py:1332-1340`: 3 個の intent 引数を一組として dispatcher に渡す。
- `tools/pegasus/dispatch_compute.py:2678-2680`: `_dispatch_impl` が index を受ける。
- `tools/pegasus/dispatch_compute.py:2741-2761`: split dispatch の session/index 契約を既に検査する。

K が 2 または 3 なら `intent_shard_index` を必須とし、`0 <= index < K` を要求する。K が 1 だけは非 shard dispatch なので `intent_shard_index is None` を report index 0 に正規化する。internal argv の文字列や dispatcher の自己申告から K を決めない。

### 4. launcher 側の執行

`tools/acceptance_launcher.py:425-475` の `_launch` に次の順序で入れる。

1. `:434` の既存 config/argv 検査。
2. `:436-439` の tested-main/tested-tip blob 等値検査。
3. `:440` の `runner_executed_sha256` 計算。
4. launcher が K、nonce、manifest、repo 外 report channel を作り、明示環境付き `_run_blob` を呼ぶ。
5. child 終了後、`:443-449` の tested-main blob 再取得と digest 再照合を先に行う。
6. 新しい `_validated_binding_reports` を呼び、report file 数が K、各 object の exact fields、nonce、tested main、digest、K が一致し、index の multiset が厳密に `0..K-1` であることを要求する。
7. ここまで成功して初めて `:450-461` の log hash と outcome protocol を書く。
8. `:462-466` の child rc と completion protocol 検査。
9. `:467-475` の受領証生成・書き込み。

したがって main/tip 等値検査は manifest 作成より前、実行後 main blob 再照合は report 執行より前に発火する。report 執行は outcome、completion、受領証より前である。

非 dispatch 走は K にかかわらず report が 0 件なので、手順 6 で fail-closed する。bounded local が rc 0 を返しても outcome と受領証は書かない。

`tools/acceptance_launcher.py:365-397` の受領証 objectには何も追加しない。`_ENV_PROJECTION_FIELDS` (`:36-42`) も不変とする。これにより `tools/dev_wave_land.py:102-130` の exact receipt field set、`:138-143` の env set、`:783-784` と `:967-968` の exact set 検査を変更せず通せる。

### 5. K の所有

launcher に `_resolve_binding_shard_count(environ)` を新設し、runner 起動前に K を確定する。

- `IZANAGI_ACCEPTANCE_SHARDS="1"`: K=1。runner にも canonical `"1"` を明示的に渡す。
- `"2"` または `"3"`: その exact 値を K とする。
- 未設定または空文字: 現行 runner の eligible acceptance default が 2 (`tools/run_tests.py:290-291`) なので launcher が K=2 と決め、子へ明示的に `"2"` を渡す。runner 側の暗黙 default に任せない。
- それ以外: runner 起動前に拒否する。

待ち手は `tools/dev_wave_wait.py:821-845` で、Pegasus LOGIN かつ queue active で未設定の場合だけ `"3"` を launcher 環境へ注入する。launcher はこの値を exact K=3 として採用する。呼出側が既に `"1"`、`"2"`、`"3"` を設定していれば、待ち手は `:824-825` で上書きしない。

K=1 は shard mode ではないが、単一 dispatch が実際に起きれば dispatcher が index 0 の report を書くので受理できる。bounded local や通常 local 実行なら report 欠落で拒否する。

未設定時に launcher が明示した K=2 が runner の eligibility 条件を満たさない site では、`tools/run_tests.py:294-297` が runner を拒否し、report も揃わない。launcher は受領証を作らない。

dispatcher は manifest の K と `intent_shard_index` の整合を検査するだけで、K の発見、縮小、完了数からの推測を行わない。

### 6. テスト計画

`orchestrator/tests/test_acceptance_launcher.py`:

- `test_matching_main_and_tip_runner_blobs_execute_tested_main_source` を更新する。`blob_runner` が manifest 環境を受け、K 個の正規 report を作る positive control とする。main source object identity、既存 3 回の blob read、受領証生成は維持する。
- `test_launcher_projects_exact_k_and_canonical_binding_manifest`: 未設定、1、2、3 を parametrize し、manifest の source、digest、main、nonce、K と `_run_blob` の環境を検査する。K の決定を dispatcher 側へ移すと赤。
- `test_binding_report_missing_is_rejected_before_outcome_and_receipt` — negative (a)。K=3 で report を 1 件消す。完全数検査を外すと赤。
- `test_binding_report_digest_mismatch_is_rejected_before_outcome_and_receipt` — negative (b)。1 shard の実行 digest を 1 桁変える。digest 照合を外すと赤。
- `test_non_dispatch_green_run_is_rejected_without_binding_reports` — negative (d)。`blob_runner` は rc 0 と log だけを返し report を作らない。非 dispatch fail-closed を外すと赤。
- `test_binding_reports_require_exact_index_multiset` — negative (e)。`[0,0,2]` と `[0,2]` を parametrize する。件数だけ、または `set` だけの検査へ弱めると赤。
- `test_binding_report_nonce_mismatch_is_rejected`: 1 shard の nonce を変える。session 照合を外すと赤。
- `test_report_validation_runs_after_main_refetch_and_before_outcome`: event list で main 再照合、report 検査、outcome の順序を pin する。順序を入れ替えると赤。
- `test_receipt_is_exact_canonical_json_bytes` を正規 report 付きに更新し、期待 v5 bytes は一文字も変更しない。receipt field を追加すると赤。

`orchestrator/tests/test_pegasus_dispatch_compute.py`:

- `test_binding_manifest_becomes_dedicated_request_field_not_requested_env`: `:522-552` の fake scheduler seam を使い、request の `runner_binding` は存在する一方、`environment` は従来 exact set のままと検査する。allowlist へ新 key を足すと赤。
- `test_bound_tests_child_hashes_and_executes_the_same_source_object`: `:4002-4067` の helper を `subprocess.run` も記録できる形へ更新し、hash 関数が受けた object と `input=` が同一 object、argv が `-I -c` bootstrap、pathname file は読まれないことを検査する。stdin を別 read や pathname bytes に変えると赤。
- `test_bound_tests_child_rejects_transcribed_expected_digest` — negative (c)。期待 digest は source A、request の source buffer は B とする。正規実装は subprocess 未起動で infra。`actual_digest = request["runner_sha256"]` と転記する変異では child が起動して赤になり、期待値の転記が恒真になる危険を直接示す。
- `test_bound_tests_child_reports_digest_computed_from_stdin_buffer`: positive caseで compute result の値が source buffer の hash であることを検査する。manifest 値の単純コピーへ変えると赤。
- `test_binding_is_exactly_limited_to_tests_passthrough_runner`: provenance、mutation、generic を parametrize し、manifest 環境が存在しても従来 argv と `stdin=DEVNULL` のままとする。条件を `argv_policy == "passthrough"` だけへ広げると provenance case が赤。
- `test_unbound_tests_request_keeps_pathname_execution`: manifest 無しの通常 tests dispatch が従来 `child_argv` と `DEVNULL` を使うことを pin する。P 自身の旧 launcher 互換を壊すと赤。
- `test_result_and_report_atomic_replace_survive_child_precreation`: fake child が先に同名 `result.json` と report file を作る。dispatcher の正規 bytes が最後に残ることを要求する。`O_EXCL` 書き込みへ戻すと赤。
- `test_binding_report_preserves_intent_shard_index`: K=3、index=1 を渡し、request、compute result、launcher report がすべて 1 になることを検査する。internal argv や自己採番へ切り替えると赤。
- 既存 `test_tests_task_env_allowlist_is_exact` (`:4583-4592`) は変更せず、新 key が allowlist に入っていないことの回帰検査に使う。

`orchestrator/tests/test_dev_wave_land.py::test_sharding_does_not_add_receipt_fields_or_expand_land_acceptance` (`:1012-1024`) と `::test_m4_runner_executed_digest_mismatch_is_rejected` (`:1062-1079`) は無変更の回帰対象とする。

この段では実走していないため、上記を緑とは記録しない。

### 7. 危険な箇所

1. D859 の channel 分離が最も壊れやすい。現状は compute child の後に `result.json` を create-only で書くため (`tools/pegasus/dispatch_compute.py:934`, `:1016-1021`, `:1040-1043`)、child の先行作成で trusted write を妨害できる。report path を request/envへ混ぜないこと、child 終了後の atomic replace、compute child 環境からの key 除去を一組で維持する必要がある。

2. K の二重解釈が壊れやすい。runner は未設定時の K=2、明示 1、明示 2/3 の eligibility を `tools/run_tests.py:253-298` で決め、実 dispatch 分岐は `:2472-2491` と `:2620-2637` にある。launcher が K を決めた後、canonical `IZANAGI_ACCEPTANCE_SHARDS` を子へ再注入しなければ、launcher の期待 K と runner の実効 K がずれる。

3. queue 待ち中の schema 混在と P 自身の初回受入が壊れやすい。dispatcher は in-flight request 互換を `tools/pegasus/dispatch_compute.py:160-174` と `:719-735` で保っている。manifest 無しを dispatcher だけで拒否すると main の旧 launcher が走る P の受入を落とす一方、launcher の report 検査を条件付きにすると恒久的な逃げ道になる。dispatcher は manifest 無しで現行動作、new launcher は無条件執行、という非対称を崩さないこと。

## 総括

- main blob、digest、nonce、exact K は launcher 所有 manifestを明示環境で login dispatcherへ渡す。
- 計算ノードでは同一 `source` objectを hashし、そのまま stdinへ渡す。
- launcherは main再照合後、受領証より前に `0..K-1` のreportを完全照合する。
- receipt v5、`run_tests.py`、wait、shards、landは変更しない。
- 最大の残余は、tip側dispatcher自体も同時改変するwaveをPだけでは排除できない点であり、段階Rの対象となる。