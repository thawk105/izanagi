## 総括

S8B 31 件を種類 A 11 件、種類 B 20 件に分類し、すべて修正した。  
A-2 の 1 件も receipt を再発行する fixture 修正で閉じた。  
補助診断では対象 32 件すべて通過したが、正式 pytest は dispatch 障害で未実走。  
commit、docs 編集、禁止 path の追加変更は行っていない。

## 赤 32 件の原因内訳 (種類 A / B / C と、それ以外があれば)

- 種類 A: 11 件
  - `test_non_mapping_pipeline_payload_is_shared_wal_protocol_violation` の 6 parameter
  - `test_cli_non_mapping_pipeline_payload_emits_observation`
  - `test_bench_failed_rejects_invalid_abort_reason_without_crashing[payload-list]`
  - `test_terminal_outcomes_reject_invalid_abort_reason_without_crashing[build-failed-payload-list]`
  - `test_invalid_line_does_not_mask_definitive_correctness_red`
  - `test_terminated_json_syntax_issue_does_not_mask_definitive_correctness_red`
  - 原因: 壊れた WAL 行の後へ fixture の正常 COMMIT を追記すると、receipt writer が既存行を再 parse して分類前に例外化していた。

- 種類 B: 20 件
  - closed abort reason 14 件:
    - `test_terminal_outcomes_accept_closed_abort_reason` の 11 parameter
    - `test_bench_failed_accepts_closed_abort_reason` の 3 parameter
  - persisted helper の過剰起動 6 件:
    - build / bench / commit attempt mismatch の 3 件
    - `test_stray_attempt_id_without_committed_binding_is_not_flagged`
    - `test_campaign_start_after_completed_terminal_is_one_position_reason`
    - `test_completed_legacy_without_run_contract_or_receipt_skips_contract_checks`
  - 原因: abort fixture が既定の attempt ID を落としていたこと、および helper が既に拒否済み、旧形式、certified eligible でない window にも起動していたこと。

- 種類 C: 1 件
  - `test_partial_authoritative_science_can_remain_inconclusive`
  - 原因: performance verify を 1 件除いた後も、COMMIT receipt が変更前の evidence 列を保持していた。

- それ以外: 0 件。

## 種類 B の過剰拒否: 余分に発火していた述語 (file:line)

- [`s8b_oracle_report.py:1336`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1336)
  - `abort.payload.build_attempt_id == build_start.payload.build_attempt_id`
  - predicate 自体は既存の正当な S8B 検査だが、fixture の custom abort payload が ID を落としたため誤発火していた。

- [`s8b_oracle_report.py:1634`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1634)
  - 修正前は実質 `len(commit_records) == 1` だけで persisted helper を起動していた。
  - 現在は certified eligible、attempt 束縛あり、COMMIT 一意、既存 issue なしをすべて要求する。

- [`s8b_oracle_report.py:1788`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1788)
  - 修正前は certified eligible でない campaign にも lock snapshot 不在を拒否理由としていた。
  - 現在は epoch projection の `certified_eligible is True` の場合だけ snapshot と helper を有効化する。

helper 内の 7 述語は変更していない。削除裁定された `commits`、`aborts`、`commit_witness`、workload exact keys、`verify_configs` は追加していない。

## 所見ごとの closed / partial / regressed 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 種類 A 11 件 | closed | 壊れた履歴を再 parse せず、有効 receipt 付き COMMIT を raw 追記 |
| 種類 B 20 件 | closed | abort attempt ID を保持し、helper を最終 certified admission に限定 |
| 種類 C 1 件 | closed | 残存 verify evidence に一致する COMMIT receipt を再発行 |
| 凍結 pin | closed | report SHA と独立 spec golden を追随 |
| regressed | なし | 補助診断上の新規失敗なし |

## 実装した修正 (file:line)

- [`s8b_oracle_report.py:1630`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1630)
  - consumer 分類後、正常な current certified window にだけ helper を適用。
- [`s8b_oracle_report.py:2029`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:2029)
  - global、lifecycle、既存 protocol issue がある場合は helper を重ねない。
- [`s8b_oracle_report.py:2388`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:2388)
  - epoch projection から campaign 単位の certified eligibility を導出。
- [`test_s8b_oracle_report.py:592`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_report.py:592)
  - 壊れた WAL 後でも有効 receipt を raw 追記する fixture helper を追加。
- [`test_s8b_oracle_report.py:629`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_report.py:629)
  - custom abort payload に既定の `build_attempt_id` を保持。
- [`test_s8b_oracle_report.py:766`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_report.py:766)
  - line issue または truncated tail がある fixture のみ raw receipt 経路を使用。
- [`test_paper_story_a2_certification.py:531`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_paper_story_a2_certification.py:531)
  - inconclusive fixture の COMMIT を取り除き、残存する正常 verify 列へ receipt を再発行。

## 凍結 pin の追随内容

- `s8b_oracle_report.py` SHA-256:
  - `f7ef6259f8feb3a6ccd7812d85132f19bc36e10fa4cd10cea28ecd145769c93b`
- [`test_s8b_oracle_manifest.py:61`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_manifest.py:61)
  - `PIN_GATE_SPEC_SHA256`:
    `5bc52b9335332c37d557ac0be1fd9d8c5bfba5ca10c44db409a3abb01b7e4ff3`
- [`test_s8b_oracle_manifest.py:90`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_manifest.py:90)
  - 独立 golden の report SHA を更新。
- `s8b_oracle_manifest.py` には更新対象 literal がないため変更していない。

## 期待値を変えていないことの確認

assert、期待 status、reason、node 名、parameter ID は変更していない。skip、xfail、削除、反転はない。単位 2 の新規 8 node も保持している。

`git diff --check`、対象 6 Python file の `py_compile`、report SHA と pin の相互検証は成功した。

## 実走した pytest の nodeid と結果

正式 pytest の child 実行は 0 件。

起動した範囲:

```text
python3 tools/run_tests.py -q \
  orchestrator/tests/test_s8b_oracle_report.py \
  orchestrator/tests/test_s8b_oracle_manifest.py \
  orchestrator/tests/test_paper_story_a2_certification.py
```

結果は `qstat -Q preflight rc=1`、child 未起動、runner `rc=16`。

pytest ではない補助診断では以下を確認した。

- focus-12 の S8B 31 test 関数: 31/31 通過
- A-2 対象 test 関数: 通過
- `test_assess_window_requires_persisted_certification[s8b]`: 通過
- pin golden の対象 test 関数: 通過

## 未実走・未完の範囲

正式 pytest としては上記 3 test file 全体、および赤 32 node が未実走。親での再実走が必要。

実装上の未完はない。commit、docs 編集、禁止 path の変更は行っていない。