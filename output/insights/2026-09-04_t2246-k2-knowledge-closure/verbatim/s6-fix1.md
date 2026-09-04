## 所見の対応表

| # | 状態 | 対応箇所 |
|---|---|---|
| 1. flattened 経路 | partial（実装済み・未実走） | [p3_s4_loop.py:2150](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/p3_s4_loop.py:2150)、[test_p3_s4_loop.py:6384](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py:6384)、[test_p3_s4_loop.py:6419](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py:6419) |
| 2. duplicate key | partial（実装済み・未実走） | [p3_s4_loop.py:1768](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/p3_s4_loop.py:1768)、[test_p3_s4_loop.py:6561](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py:6561) |
| 3. legacy golden | partial（実装済み・未実走） | [test_knowledge_manifest.py:139](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_knowledge_manifest.py:139)、[test_knowledge_manifest.py:203](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_knowledge_manifest.py:203) |
| 4. 射影テスト | partial（実装済み・未実走） | [test_p3_s4_loop.py:5821](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py:5821) |

## 実装した変更

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/p3_s4_loop.py)
  - `main` は `--coder-role` 指定時だけ `knowledge_input` を loader へ渡すよう変更。
  - exact K2 role と knowledge input の組だけ、既存の `knowledge_manifest._reject_duplicate_keys` を `json.load` に適用。

- [test_knowledge_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_knowledge_manifest.py)
  - 指定された実在 manifest と、その歴史的 source bytes を自己完結 fixture 化。
  - digest、v1 schema literal、receipt 全 canonical bytes を literal golden で固定。

- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/tests/test_p3_s4_loop.py)
  - main の flattened／K2 wrapper 両経路を実 loader で検査。
  - duplicate anomaly key の負例と unique-key 正例を追加。
  - 射影期待値を production producer の再呼び出しから独立した literal に変更。

## 現行挙動との差（受理・拒否）

- 変更前: manifest 単独の main 経路は片側指定として拒否。変更後: loader には marker を両方省略し、flattened proposal を受理。
- manifest と K2 role の両指定は引き続き K2 wrapper を受理する。
- 変更前: K2 proposal の duplicate key は後勝ちで上書き。変更後: schema／anomaly 検査前に拒否。
- K2 以外は従来どおり通常の `json.load` を使用する。K0／K1 相当の flattened 経路、片側指定拒否、sort／trigger／B4 loader、正しさ・identity・性能ゲートは変更していない。

## テスト

対象 nodeid:

- `test_knowledge_manifest.py::test_historical_k2_legacy_manifest_and_receipt_match_literal_golden`
- `test_p3_s4_loop.py::test_main_passes_resolved_knowledge_projection_to_proposal_loader`
- `test_p3_s4_loop.py::test_main_manifest_only_accepts_legacy_flattened_proposal`
- `test_p3_s4_loop.py::test_main_manifest_and_k2_role_accept_k2_wrapper`
- `test_p3_s4_loop.py::test_k2_load_proposal_rejects_duplicate_instruction_like_content_key`

duplicate `instruction_like_content_detected=true,false` を持つ K2 proposal を拒否し、同内容の unique-key proposal を受理するテストを追加した。manifest 単独の flattened proposal と、manifest＋K2 role の wrapper proposal を main の実 loader 経路で受理するテストを追加した。

実走は未了。`tools/run_tests.py` を通常および `-n 1` で試したが、いずれも `qstat -Q preflight rc=1`、`child_started=false`、終了コード 16 で、pytest 子 process は開始されなかった。`git diff --check` と U+0300〜U+036F の静的検査は通過した。

## 波及可能性

- `p3_b4_launcher.py` の base driver registry は `L.main` を呼ぶが、knowledge marker を渡さないため従来経路のまま。
- `test_p3_b4_closed_critic.py` の直接 loader caller は K2 marker を渡さず、通常 parser のまま。
- `test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_campaign_import_invariant.py` は main/import 契約の consumer。
- `test_pytest_collection_config.py` と `test_acceptance_schedule_order.py` は新 node の collection／cost consumer。指示どおり duration ledger は未更新。
- `test_layer3_report.py`、`test_codex_agents.py`、sort／trigger の consumer は共有 manifest・schema 周辺の波及候補だが、production 差分はない。

## 未了・疑問

- pytest は実走できていないため、4 件とも `partial`。
- runner が失敗時の dispatch receipt を ignored な `output/pegasus-dispatch/` 配下へ自動保存した。削除・変更はしていない。
- docs、変異 spec、duration ledger、output 成果物、commit は触れていない。
- 実装判断上の未解決点はない。

## 総括

manifest 単独の既存 flattened 経路を復旧し、明示 K2 経路だけ duplicate key を拒否するようにした。  
legacy manifest digest、v1 schema、receipt 全 bytes を歴史的 literal golden で固定した。  
main 射影テストは producer 再利用を除き、必須 4 field を literal で検査する。  
最大の残リスクは、Pegasus dispatch 障害により対象 pytest が未実走であること。