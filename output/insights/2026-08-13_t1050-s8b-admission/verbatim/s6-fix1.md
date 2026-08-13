## 赤の根本原因

- oracle 経路 8 件: `LaunchValidatedFreeze.binaries_by_cell` の再帰 `mappingproxy`／tuple を canonical JSON へ直接渡し、正当 receipt が全件 `admission-mismatch` で拒否されていました。JSON 組込み型へ射影してから exact schema と outer SHA を検査するよう修正しました。`events` の `KeyError` 2 件も、この先行 refusal の派生です。
- floor 実測分類 3 件: receipt を持たない既存の低位 `_run_session` unit seam に、新 gate が無条件で挿入されていました。receipt 検査を public `_Runner.run()` の全件 preflight へ移し、production は fail-closed のまま既存 seam を回復しました。
- real-repo floor E2E 1 件: 段 5 の fixture 適応で build 呼出しの `src_token` が cell ID から source SHA へ変わっていました。build seam へ渡す既存 token は維持し、durable receipt の binding だけを権威ある `SourceEvidence` へ正規化しました。

## 所見対応表

pytest 未実走のため、DW-S05-C に従い全件 `partial` とします。静的に判明している実装残はありません。

| 所見 | 状態 | 対応 |
|---|---|---|
| R-A1 | partial | store、portable、resume、public runner 実走直前で current policy、ccbench pin、contract を外部期待値として照合 |
| R-B1 | partial | subject を record 自身と外部 expected tuple の双方へ、一つの tuple gate で束縛 |
| R-A2 | partial | historical は current policy 非依存を維持し、記録 policy の cell 間一意性だけを追加 |
| R-A3 | partial | runtime record の exact key、cell、hash、argv、cached、path、binding、receipt を全件 preflight 後に書込み開始 |

## 変異帰属の再設計

- M1: receipt 欠落は後段 validator も拒否するため、単独変異の証拠にはできません。追加テストから診断文字列依存を除き、単なる schema 拒否テストへ戻しました。
- M2: 専用 None／空分岐は object 型検査と nested exact-key 検査に冗長だったため削除しました。実在する None／空入力の拒否は維持しますが、単独変異の kill とは数えません。
- M5: `subject == record` と `store bytes == record` から導かれる冗長比較と、validator の事後条件を壊す mock を削除しました。同じ nodeid は実 store bytes 改変を既存 record SHA gate が拒否する実入力テストへ変更しました。
- M3 は binary SHA equality を維持しました。M4 は R-B1 の record 照合と外部 tuple 照合を一つの gate に統合し、単独有効性を維持しています。

## 実装した変更

- [s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_binary_admission.py:63): immutable JSON 射影、冗長 missing 分岐削除、subject↔record↔external tuple 束縛。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1333): build token 回帰修正と receipt identity 正規化。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1515): portable、resume、floor の pin／contract 外部照合。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:2245): store の全 runtime record preflight。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:2839): public runner の実測前全件 admission gate。
- [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:1651): historical cross-cell policy 一意性。
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:933): 冗長な M5 比較を削除。
- [test_s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_binary_admission.py:138)、[test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:5333)、[test_s8b_ratified_verify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_ratified_verify.py:691)、[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:4521): 各回帰テスト。

## 実走結果

指定 12 nodeid を `python3 tools/run_tests.py` へ一括投入しましたが、全 node が pytest collection 前に停止しました。

- `test_real_seal_protocol_to_floor_official_core_e2e@real-repo`: rc=16
- `test_v2_store_hash_mismatch_is_refused`: rc=16
- `test_rep_integrity_precedence_uses_completed_measure_evidence` 3 parameter: 各 rc=16
- `test_v2_store_missing_is_refused`: rc=16
- `test_v2_floor_disk_swap_after_launch_uses_same_validated_object`: rc=16
- `test_v2_store_bytes_are_checked_against_admission_subject_independently`: rc=16
- `test_v2_gate_happy_path_completes_and_binds_env_store_receipt`: rc=16
- `test_v2_completed_driver_adapter_campaign_is_accepted_by_report`: rc=16
- `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`: rc=16
- `test_transient_prepare_failure_retries_once`: rc=16

原因は `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` です。緑とは申告しません。

静的検査は以下が rc=0 です。

- 変更 15 Python ファイルの AST、NFC、結合文字不在
- production module import
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 期待値を疑った箇所

ありません。12 件の既存期待値はすべて正本として扱い、実装または段 5 追加 fixture 側を修正しました。

## 波及

- `store_binaries` の内部 caller は live pin／contract の明示が必須になり、既存 caller を全件更新しました。
- historical freeze でも cell 間で policy が混在する artifact は新たに拒否されます。current policy 一致は要求しません。
- receipt のない repo 外旧 artifact、schema 移行、互換 loader、遡及再取得には触れていません。
- docs、tracked `output/s8b-freeze`、`buildcache.py`、oracle report／judge、V1 trust root は非接触です。
- commit と `git add` は行っていません。

## 総括

実測 12 件の共通原因を 3 系統へ分解して修正しました。  
oracle の正当経路を拒否した immutable Mapping の canonical 化回帰を閉じました。  
floor の既存 build token と低位 unit seam を回復しました。  
live pin／contract、subject↔record、historical policy 一意性を実装しました。  
store は runtime record 全体を全件検査してから書込みます。  
M1／M2／M5 は冗長性を正直に扱い、偽の mutation kill を撤去しました。  
M3／M4 の単独有効性は維持しています。  
pytest は dispatch 障害で未実走のため、所見は `partial` と報告します。