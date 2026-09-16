## 変更 hunk 一覧

指定3ファイルだけを変更。計12 hunks、commitなし。

`L` = [orchestrator/campaign/layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2718-impl/orchestrator/campaign/layer3_report.py)
`T` = [orchestrator/tests/test_layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2718-impl/orchestrator/tests/test_layer3_report.py)

| file:line | before → after |
|---|---|
| L:112 | purposeなし・通常decoder固定 → 必須keyword、読取り前exact型検査、purpose別decoder、union返却型 |
| L:205 | HEAD解決の引数注釈 → union |
| L:388 | calibration解決の引数注釈 → union |
| L:767 | 材料入口のreader呼出し → HISTORICAL_RAW明示 |
| L:829 | WALへdecoded object → `.identity` |
| L:951 | 認証入口のreader呼出し → CERTIFIED_ACCEPTANCE明示 |
| T:9 | Enum import追加 |
| T:569 | committed closure・既存issuing contextを使う歴史fixture追加 |
| T:1915 | 新規7テスト関数、14ケース追加 |
| T:2450 | 既存直接呼出しへCERTIFIED_ACCEPTANCE追加 |
| T:2470 | 同上 |
| [tools/t2718_real_corpus_probe.py:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2718-impl/tools/t2718_real_corpus_probe.py:1) | 新規。可変長argv triples、両purpose・builder結果、例外/cause、前後SHA256をJSON記録 |

既存例外変換、decoder／admission／WAL実装、既存テスト期待値は変更していません。

## 追加した test と実走結果

指定の`PYTHONPATH=. python3 -c "...pytest.main(...)"`経路で実走。以下のnodeidはすべて`orchestrator/tests/test_layer3_report.py::`が接頭辞です。

| nodeid末尾 | 結果 |
|---|---|
| `test_historical_exact_grammar_build_report[62]` | PASSED |
| `test_historical_exact_grammar_build_report[24]` | PASSED |
| `test_accepted_report_rejects_historical_exact_grammar_at_lock[62]` | PASSED |
| `test_accepted_report_rejects_historical_exact_grammar_at_lock[24]` | PASSED |
| `test_read_campaign_lock_requires_purpose` | PASSED |
| `test_read_campaign_lock_rejects_non_exact_purpose` | PASSED |
| `test_read_campaign_lock_current_and_v1_by_purpose[CERTIFIED_ACCEPTANCE-63]` | PASSED |
| `test_read_campaign_lock_current_and_v1_by_purpose[CERTIFIED_ACCEPTANCE-v1]` | PASSED |
| `test_read_campaign_lock_current_and_v1_by_purpose[HISTORICAL_RAW-63]` | PASSED |
| `test_read_campaign_lock_current_and_v1_by_purpose[HISTORICAL_RAW-v1]` | PASSED |
| `test_historical_exact_grammar_uses_authority_head_fallback[62]` | PASSED |
| `test_historical_exact_grammar_uses_authority_head_fallback[24]` | PASSED |
| `test_material_knowledge_identity_argument_preserves_current_and_v1[63]` | PASSED |
| `test_material_knowledge_identity_argument_preserves_current_and_v1[v1]` | PASSED |
| `test_artifact_refs_accept_validated_knowledge_receipt_digest` | PASSED |
| `test_artifact_refs_reject_receipt_changed_after_provenance_read` | PASSED |

**16 passed、221 deselected、6.90秒。** Knowledgeテストにはobject／identity両入力の拒否型・文言一致も含みます。

HEAD fallbackは、実admissionによるbuilder完走と記録commitへの一致を検証し、固定40桁値`bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`については実reader＋`_resolve_generated_from_head`で検証しています。架空commitを実admissionへ通す差替えはしていません。

関数名・集合の制約を`orchestrator/tests`で検索し、新規7関数を固定集合へ登録する必要のあるmeta-testは見つかりませんでした。関連するファイル網羅meta-testも実走しました。

| nodeid（接頭辞`orchestrator/tests/test_plain_runner_coverage.py::`） | 結果 |
|---|---|
| `test_every_test_file_is_self_runnable_or_allowlisted` | PASSED |
| `test_allowlist_has_no_stale_or_self_runnable_entries` | PASSED |
| `test_this_metatest_is_itself_self_runnable` | PASSED |

AST比較で既存テスト削除・改名なし、既存変更は指定2関数のみ。`git diff --check`成功。probeは構文確認のみで、未実行です。

## exact-24 固定 epoch の値と出所

`E1:e1e397737e509b550482d3e815bcb69b87c0b5c42f6ac7feb6fccb657856cfc7`

新規fixture helperでexact-24 campaignを作り、実`require_admitted_campaign(..., purpose=HISTORICAL_RAW)`を1回呼んで観測した値です。その後テストへliteralとして固定しました。期待値helperや実装からの再計算はしていません。

## 波及の静的列挙

- **所有外caller:** 既存の`layer3_report._read_campaign_lock`直接callerは指定テスト2箇所だけ。公開builderのsignature変更なし。
- **生産consumer:** `p3_autonomous_workload_trial.py:3116`の`render`、`autonomous_trial_completeness.py:4666`のfresh report再生成。後者のgenerator hash差分は今回も発生します。
- **共有fixture:** `test_artifact_admission`の`_committed_closure_repo`、`_new_schema_campaign`、exact-62／24 rewrite helperを再利用。共有ファイルは未変更。
- **consumer test:** `test_p3_autonomous_workload_trial.py`、`test_autonomous_trial_completeness.py`、`test_layer3_admission_diagnosis.py`、`test_trial_registry.py`、`test_t126_qualification_artifacts.py`。これらの全走は未実施。

## 受理集合の before / after

変更前は、中央の歴史admissionを通ったexact-62／24も材料レポートの通常decoderで再拒否されていました。変更後は歴史grammarを理由とする再拒否を解消し、材料固有条件と認証側の受理集合を維持しています。

## 総括

- 変更3ファイル、12 hunks、新規7テスト関数・14ケース。
- 焦点16ケース＋meta-test 3ケースはPASSED。
- docs・worklog・共有実装は未変更、commitなし。
- 実corpus probe、変異試験、親の全走、63／v1出力の前後比較は未実施。
- 実装済み・焦点実走済み。wave全体のclosed申告はしません。