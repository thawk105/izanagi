## 対応表

| 所見 | 判定 | 対応 | 実走 |
|---|---|---|---|
| F1 | closed | monkeypatch を廃止し、descriptor のない partial report から理由を落とした実 bytes を full verify | 実装済み・未実走 |
| F2 | closed | report・run-start・receipt・参照 hash を協調更新し、pairwise／descriptor gate を単一拒否理由化 | 実装済み・未実走 |
| F3 | closed | receipt・report・run-start の3箇所で `input_schema_version == "8b-v1"` を値ごと消費 | 実装済み・未実走 |
| F4 | closed | projection を parsed trial に保持し、full verifier で report と canonical bytes 完全一致を要求 | 実装済み・未実走 |

## 変更点

- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_acceptance_receipt.py:96)
  - `origin_terminal_projection` を parsed 型へ保持。
  - report との presence・object 型・canonical JSON bytes 一致を検証。
- [test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:246)
  - F1/F2/F4 の full-verifier 負の対照を追加・修正。
- [test_reflux_originless_compatibility.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_reflux_originless_compatibility.py:675)
  - 三者の値付き pop と、協調不正値・report 単独・run-start 単独の対照を追加。
- [test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_trial_registry.py:1190)
  - producer 由来 projection が parsed trial に保持されることを確認。

F1 の静的論証: 新テストでは1 trial の `cells=[]` と対応する report hash を実 bytes に反映し、理由集合から `c02-arm-binding-unproven` を落としています。現実装では proof 列に `False` が入り最終 gate が拒否します。関数を `return True` にするとその最終条件だけが無効になり、他の照合はすべて成立して verifier が正常終了するため、`pytest.raises` が失敗して新テストは赤になります。

`certifying=True` へ至る経路は追加していません。

## 実走

pytest は未実走です。以下を `tools/run_tests.py` 経由で試しましたが、いずれも pytest 開始前に `qstat -Q` が `Can't create socket` となり、dispatch `rc=16` で停止しました。

- `test_s8c_acceptance_receipt_v2.py` 全体
- `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`
- `test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`

実行済み検査:

- `python3 tools/check_codex_agents.py` — OK
- `python3 tools/check_docs.py` — OK
- 対象4ファイルの AST parse — OK
- `git diff --check` — OK

## 未解決

- pytest 実走のみ未完了です。
- 初回の横断 `rg` で巨大 golden 行が検索結果へ一致しました。編集はしておらず、同 literal は diff hunk 外・未変更です。
- 所有外の並行差分は触っていません。docs 編集・commit も行っていません。

## 総括

F1〜F4 はすべて実装上 closed。pytest は Pegasus dispatch infrastructure failure のため未実走です。