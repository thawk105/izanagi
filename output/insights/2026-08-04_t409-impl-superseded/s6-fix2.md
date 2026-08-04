G-1〜G-6をすべて修正しました。docs・commit・禁止対象の production ファイルは変更していません。

| 項目 | 状態 | 対応 |
|---|---|---|
| G-1 | closed | `test_campaign.py` に `import pytest` を追加 |
| G-2 | closed | trigger 判定を configuration に限定。sort/backoff/stock は従来の token-only `resolve()` 経路へ復元 |
| G-3 | closed | axis 名による自動 grammar 束縛を廃止し、実装を materialize する自律 trigger loop で明示束縛 |
| G-4 | closed | `quarantine()` の既定 scope を復元。`enforce_trigger_gate_language=True` の明示 opt-in を追加し、A-12 nodeも追随 |
| G-5 | closed | receipt fixture が `genome=` を受け、発行時の完全等値契約を再現 |
| G-6 | closed | driver/report/shared emitter fixtureを、`system_gate`・`ident_all` は7-key、他は5-keyへ追随 |

Campaign ID は以下を静的確認しました。

- default-off sweep: `fc683dde` / `5569ad76` に復帰
- F-L承認済み3値: `362e5961` / `fbceada4` / `4a7be342` のまま
- したがって期待値 literal の再更新は不要

期待値を変更した test nodeは0件です（完全列挙: なし）。G-2/G-5/G-6では fixtureの呼び出し形・証拠形のみ修正しました。

変更ファイルは13件です。

- `orchestrator/campaign/`: `ident.py`, `p3_autonomous_workload_trial.py`, `p3_s4_loop.py`, `p3_s4_loop_trigger_gating.py`, `s1_direct_comparison.py`, `s1_verify_extime_calibration.py`
- `orchestrator/tests/`: `test_campaign.py`, `test_p3_s4_loop.py`, `test_s1_direct_comparison.py`, `test_s1_verify_extime_calibration.py`, `test_s8b_oracle_driver.py`, `test_s8b_oracle_report.py`, `test_s8b_ratified_freeze.py`

静的検査はすべて成功しました。

- `py_compile`: 対象13ファイル成功
- JSON schema parse、`git diff --check`: 成功
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0
- pytest dispatch: **0件**（`pegasus02` login nodeのため未実走）

## 総括

- closed: **6**、partial: **0**、regressed: **0**。
- 残リスクは計算ノードでのpytest再実測が未完であること。
- 親はG-1 collection、G-2 sort 3 param、G-3 default-off IDを実測すること。
- G-4既定scope+A-12 opt-in、G-5 build-target receipt nodeも実測すること。
- G-6はoracle driver 11件・report 10件を含む両ファイル全体を再走すること。
- G-6でfixture追随後も赤が残る場合は、契約を緩めず該当nodeを実装非整合として停止すること。