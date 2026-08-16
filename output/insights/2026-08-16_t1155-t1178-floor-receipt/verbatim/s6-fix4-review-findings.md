## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| M1 | partial | completed-only fallback を削除し、常に canonical start coverage を要求。未実走のため closed 申告なし |
| M2 | partial | 共通 authorization validator を consume・inspector・resume・ratified に接続。未実走 |
| M3 | partial | holdout freeze に manifest、journal sessions、binary receipt の外部束縛を追加。未実走 |
| M4 | partial | 公開 verifier に mode 条件付き result v4 exact-key gate を追加。未実走 |
| M5 | partial | 非権威的 field である保証境界を明文化し、同期変更／片側変更を別 nodeid 化。未実走 |
| regressed | 静的には未観測 | AST・NFC・import は成功したが、親の 13 ファイル再実測前なので回帰なしとは確定しない |

## 直した内容

- [s8b_floor_contract.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:104)
  - result v4 の mode 条件付き exact-key 契約を共有化。
  - [同:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:114) に planned/retry の正準 attempt ID、seq、retry ordinal、一意性を検査する共通 validator を追加。
  - [同:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:189) に manifest v3 の exact key、schema、protocol mirror、cells、binaries、schedule 束縛を追加。
- [s8b_holdout_admission.py:1358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1358)
  - consume 前に全 start を共通 validator で検査。
  - [同:1843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1843) で completed→start coverage を無条件化し、completed-only fallback を削除。
  - [同:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1480) に `measurement_head` の非権威性と保証範囲を日本語で明記。
- [s8b_floor_campaign.py:5671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5671)
  - resume manifest に共有 v3 validator を接続。
  - [同:5917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5917) で resume start を共通 authorization validator に通す。
- [s8b_ratified_freeze.py:1830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1830)
  - 既存の強い manifest 検査を残したまま共有 validator を追加。
  - [同:2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2115) に共通 authorization 検査を追加。
- [s8b_holdout_freeze.py:1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1427)
  - sibling manifest を strict parse 後、共有 v3 契約で検証。
  - [同:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1452) で journal sessions と result sessions の完全一致を要求。
  - [同:1463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1463) で journal receipt から `expected_binaries` を導出。
  - [同:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1490) で live verifier へ渡す。
- [s8b_floor_stats.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:637)
  - 公開 verifier 自身に result v4 exact-key gate を追加。
- [s8b_v2_freeze_fixture.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/s8b_v2_freeze_fixture.py:320)
  - `{}` 前提だった候補 fixture を canonical v3 manifest、start＋session journal、測定 binary receipt 付きへ更新。
  - `{}`／v2 manifest を、result・admission evidence の hash まで整合させた負例として生成可能にした。

## 追加した positive control

すべて**未実走**です。

- M1
  - `orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_completed_sessions_without_session_starts`
- M2
  - `orchestrator/tests/test_s8b_floor_contract.py::test_canonical_authorization_rejects_attempt_id_transplanted_from_other_seq`
  - `orchestrator/tests/test_s8b_floor_contract.py::test_canonical_authorization_rejects_attempt_id_transplanted_from_retry_ordinal`
  - `orchestrator/tests/test_s8b_floor_contract.py::test_canonical_authorization_rejects_duplicate_cell_retry_ordinal`
  - `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_rejects_planned_attempt_id_transplanted_from_another_seq`
  - `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_rejects_retry_attempt_id_transplanted_from_another_ordinal`
  - `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_rejects_duplicate_cell_retry_ordinal_with_markers`
- M3
  - `orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_result_only_session_throughput_tamper`
  - `orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_semantically_invalid_manifest_with_consistent_evidence[empty]`
  - `orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_semantically_invalid_manifest_with_consistent_evidence[v2]`
  - `orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_result_only_binary_and_swo_identity_tamper`
- M4
  - `orchestrator/tests/test_s8b_floor_stats.py::test_live_verifier_rejects_result_v4_unexpected_top_level_key`
  - `orchestrator/tests/test_s8b_floor_contract.py::test_result_v4_key_contract_is_mode_conditional_and_exact`
- M5
  - `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_accepts_synchronized_non_authoritative_measurement_head_change`
  - `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_rejects_one_sided_measurement_head_change`

## 受理集合を緩めていない根拠

- M1: completed session が一件でも start 集合に無ければ、無条件に `session-start-coverage-mismatch` が発火する。fallback は残していない。
- M2: planned は `cell::seqN`、retry は `cell::retryN` を再導出する。seq、attempt ID、`(cell_id, retry_ordinal)` の重複も拒否する。fix2 の marker／ledger 双方向完全一致は変更していない。
- M3: holdout freeze は manifest v3 semantic validation、`result.binaries == manifest.binaries`、journal/result session 完全一致、journal-derived `expected_binaries` の全辺を通過しなければならない。
- M4: schema 検査より前に mode 条件付き top-level exact 集合を検査し、欠落・余分 key の双方を拒否する。
- M5: production の受理集合は変更していない。同期変更は既裁定どおり受理し、片側変更は既存の claim/ledger 完全一致で `claim-file-mismatch` になることを別 nodeid へ固定した。

## 緑の 13 ファイルへの波及可能性

- `test_s8b_sort_swo_receipt.py`: holdout 経路で SWO binary identity が manifest/journal の外部値にも束縛される。
- `test_s8b_binary_admission.py`: result／manifest 完全一致により portable binary exact 契約が sibling manifest にも波及する。
- `test_s8b_floor_contract.py`: 新しい三共有契約の直接変更面。
- `test_s8b_holdout_admission.py`: start coverage、canonical attempt、measurement head の直接変更面。
- `test_s8b_floor_stats.py`: result v4 exact-key gate の直接変更面。
- `test_s8b_materialization.py`: portable binary record が manifest validator 経由でも検査される間接波及。
- `test_s8b_freeze_io.py`: resume manifest の exact/semantic 拒否が追加される。
- `test_s8b_ratified_freeze.py`: 既存 ratified manifest／journal 検査の後段に共有 validator が追加される。
- `test_s8b_holdout_freeze.py`: manifest、journal、binary receipt の直接変更面。
- `test_s8b_oracle_driver.py`: 共有 v2 candidate fixture の manifest/journal 形状変更が波及しうる。
- `test_s8b_oracle_report.py`: 同じ共有 fixture と result exact-key 契約が波及しうる。
- `test_s8b_floor_campaign.py`: resume manifest signature、resume authorization、test live-inspector lifecycle が直接波及する。
- `test_s8b_ratified_verify.py`: ratified 共通 validator の拒否順序・cause に間接波及しうる。

静的確認は変更 12 ファイルの AST parse、NFC・結合文字検査、production 6 module の import が成功しました。pytest、`tools/run_tests.py`、git、commit、Web、docs、`freeze_verification_hold.py`、`output/`への操作は行っていません。

## 総括

閉じた所見: 実装面では M1〜M5 の指定辺と positive control を追加したが、未実走契約に従い closed 申告は 0 件。

閉じきれなかった所見と理由: M1〜M5 はすべて partial。親による焦点走と 13 ファイル全走が未実施で、回帰の有無を確定できない。

緩めていない根拠: fallback や optional 化を導入せず、exact equality、正準再導出、双方向 coverage を追加した。M5 だけは裁定どおり実装保証を増やさず、既存の非権威性を明文化・固定した。