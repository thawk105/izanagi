## 実装した変更

- [tools/codex_reasoning_ab.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:2590)
  - `schema_version` を exact `int` かつ `3` に限定。
  - `_load_task_manifest()` を追加し、UTF-8 strict、重複 key、非有限数、top-level object を検査。
- [tools/codex_reasoning_ab.py:2717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:2717)
  - canonical bytes の SHA-256 計算と exact 一致 helper を追加。
- [tools/codex_reasoning_ab.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:493)
  - 外部 manifest 経路で `SESSION_IDS` / `ROLLOUT_SHA256` を読まない明示 pin 配線へ変更。
- [tools/codex_reasoning_ab.py:3040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:3040)
  - snapshot build/verify 全経路へ manifest を伝播し、snapshot oracle に digest を記録。
- [tools/codex_reasoning_ab.py:7077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:7077)
  - schedule、attempt ledger、launch/completion receipt、collect receipt を digest 連鎖へ接続。
- [tools/codex_reasoning_ab.py:9171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9171)
  - material adjudication で packet state、verdict rows/freeze、revealed mapping の digest を再検査。
- [tools/codex_reasoning_ab.py:10282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10282)
  - material manifest、schedule、attempt ledger、snapshot/collect replay を同じ digest に束縛。
- [tools/codex_reasoning_ab.py:10824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10824)
  - packet source manifestから packet state/private mapping、verdict log、freeze、reveal まで連鎖。
- [tools/codex_reasoning_ab.py:11370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11370)
  - parser option と、外部 manifest 確定後の alias 解決・dispatch を実装。

`_aggregate_verified` と `resource_ledger` は編集していない。

## digest 連鎖の実測

実コード上の連鎖は次の2系統です。

1. `task manifest canonical digest`
   → snapshot oracle
   → schedule
   → supervisor attempt ledger / launch
   → collect receipt
   → material manifest
   → replay / verify / aggregate report

2. `packet source manifest`
   → packet state + private mapping
   → append 済み verdict rows
   → verdict freeze
   → revealed mapping
   → material adjudication

option を追加した verb は以下の10個です。

- `build-snapshot`
- `verify-snapshot`
- `collect-run`
- `supervise-pair`
- `aggregate`
- `verify`
- `make-packets`
- `append-verdicts`
- `freeze-verdicts`
- `reveal-mapping`

追加しなかった verb:

- `render-prompt`: receipt の digest を読む後続 consumer がなく、prompt SHA だけでは exact manifest 同一性を証明できない。
- stage2/stage5 の各 verb、`score-run`: task manifest 非依存。
- option の無い verb は argparse 上で未知引数として拒否される。

既定 manifest と、その canonical JSON を `--task-manifest` で明示した結果の等価テストも追加した。

## 追加・変更したテスト

主な新規 nodeid:

- `test_task_manifest_loader_accepts_only_strict_canonical_json_object`
- `test_m11_task_manifest_loader_rejects_invalid_utf8_before_json_recovery`
- `test_m12_task_manifest_loader_rejects_duplicate_key_with_equal_values`
- `test_m13_task_manifest_schema_version_requires_exact_int`
- `test_task_manifest_loader_rejects_non_object_top_level`
- `test_task_manifest_loader_rejects_nonfinite_json_number`
- `test_task_manifest_loader_rejects_unreadable_path`
- `test_external_manifest_golden_does_not_read_module_session_or_rollout_pins`
- `test_task_manifest_cli_option_surface_is_closed`
- `test_m16_cli_external_manifest_is_loaded_before_alias_resolution`
- `test_default_and_explicit_default_task_manifest_cli_results_are_equal`
- `test_collect_run_rejects_launch_task_manifest_digest_exchange`
- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`
- `test_m15_packet_consumer_requires_exact_task_manifest_digest_once`
- `test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal`
- `test_make_packets_rejects_task_manifest_exchange_before_publication`

署名・fixture 伝播に合わせ、snapshot exact-key、golden pin、supervisor/replay、packet/adjudication の既存テストも更新した。

## 実走結果

pytest の緑はありません。実装済み・未実走です。

実走を試みた nodeid:

- `test_task_manifest_loader_accepts_only_strict_canonical_json_object`
- `test_m11_task_manifest_loader_rejects_invalid_utf8_before_json_recovery`
- `test_m12_task_manifest_loader_rejects_duplicate_key_with_equal_values`
- `test_m13_task_manifest_schema_version_requires_exact_int`

結果:

- `tools/run_tests.py` が Pegasus の `qstat -Q preflight rc=1` で終了。
- child は起動せず `rc=16`。したがって赤でも緑でもない。
- runner が一時生成した `output/pegasus-dispatch/...` は全て除去済み。

静的検査:

- 両編集ファイルの AST parse: 成功
- `git diff --check`: 成功
- `git diff --name-only`: 許可された2ファイルのみ

親 docs 未 land に由来する test 赤は本 nodeid 群には指定していない。docs checker は権限境界に従い未実走。

## 変異 M11〜M16 の単一理由性の確認

- M11: 確認。無効 byte は validator が見ない `task_type` 内へ置き、非 strict recovery なら後段が受理する。意図した strict decode 変異では理由は1件。
- M12: 確認。同値の `manifest_kind` 重複を使用。重複拒否を外すと後勝ち tree は既存 validator を通る。
- M13: 確認。`3.0` は exact 型検査を外すと既存 `!= 3` を通る。
- M14: 単一理由性を確認できない。loader の top-level 検査を外しても `_validate_task_manifest` が同じ配列を拒否する。親は M14 登録を取り下げる必要がある。
- M15: 確認。`freeze_verdicts` の packet-state digest 検査を対象にし、後続 verdict log が存在しない入力で exact mismatch だけを確認する。上流に同じ digest 拒否層はない。
- M16: 確認。外部だけに存在する `alpha` alias を使用。option を無視すると default resolver か dispatch 引数検査だけが赤になる。

## 波及可能性の静的列挙

- 外部 CLI 呼び出し元は schedule と material/packet-source manifest に `task_manifest_sha256` を記録する必要がある。
- 既存の digest 無し snapshot oracle、attempt ledger、launch/collect receipt、packet/verdict artifact は新 consumer で拒否される。
- snapshot oracle と receipt bytes が変わるため、それらを pin する schedule/descriptor は再生成が必要。
- 共有 fixture `_schedule`、`_manual_run`、`_full_manifest`、`_packet_fixture`、`_bound_packet_manifest` を更新した。
- monkeypatch fake は新しい `task_manifest=` keyword を受け取る必要がある。
- `orchestrator/tests/conftest.py` と `test_real_repo_serialization.py` は既存 nodeid を列挙している。改名はしていないが、実行時間と生成 bytes は変わりうる。
- `tools/t189_task_catalog.py` はファイル名タグ参照のみ。
- 検索で見つかった `s8b_oracle_manifest.verify_manifest` は別 module の同名関数で、本変更の署名波及先ではない。

## 現行の受理・拒否挙動と、変更後の差分

変更前:

- 全 verb が `--task-manifest` を未知引数として拒否。
- task manifest は module 定数のみ。
- `schema_version=3.0` を受理。
- task manifest digest の無い schedule、material manifest、packet/verdict artifact を受理。
- manifest 交換は `known_finding_ids` や `oracle_kind` が重なる場合に検出不能。

変更後:

- 上記10 verb のみ外部 manifest を受理。
- UTF-8不正、重複 key、非有限数、top-level 非 object、非 exact-int version を拒否。
- 各 consumer は先行 artifact の digest 欠落・不一致を fail-closed で拒否。
- `render-prompt` と task-neutral verb は引き続き option を拒否。
- option 未指定と既定 manifest の明示指定は同じ digest・dispatch 結果になる。
- 受理集合は、外部 manifest の正規入力を追加する一方、digest の無い旧 artifact を意図的に拒否する方向へ狭めた。

## 総括

実装子 A の A-1〜A-5は実装済みで、編集は指定2ファイルのみ、docs・凍結成果物・`_aggregate_verified`・`resource_ledger`・commit には触れていない。

ただし pytest child が一度も起動できていないため、成果は「実装済み・未実走」であり、`closed` とは申告しない。M14 は既存 validator と拒否理由が重複するため、変異登録の取り下げが必要。