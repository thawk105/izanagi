## 実装した変更

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:479)
  - loaded publication の manifest に同じ `attempt_id` がちょうど 1 行あることを要求。
  - 不一致時は membership を明示する `B4ProtocolError` で停止。
  - 既存の registry・driver・canonical hash 照合は維持。
- [NON_GUARANTEES](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:172)
  - manifest 外 attempt は拒否する一方、manifest 自体の権威性は保証しないという限定表現へ更新。
- [test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:94)
  - manifest 外 registry attempt の負例を追加。
  - exact tuple pin を更新。

指定された2ファイル以外は編集していません。commit・branch・push 操作も行っていません。

## 受理集合の変更 (前 / 後)

前: registry に一意な attempt があり、driver/hash が一致すれば、manifest 外でも受理されました。

後: 上記すべてに加えて、loaded publication の manifest に同じ attempt がちょうど1行必要です。manifest 外 attempt は campaign 副作用前に拒否されます。publication の権威性や別 root 再発行、continuation、certified 接続には変更ありません。

## 追加した正例・負例

- 正例: 既存 `test_matching_bootstrap_accepts_reordered_spaced_unicode_spelling` を維持し、base/sort/trigger 全てで manifest 内 attempt が受理されることを確認。
- 負例: fixture の typed publication に同一 driver/hash の scheduled row を追加し、manifest を201行のまま保持。registry にのみ存在する attempt が3 driver全てで拒否されることを確認。

## 実走結果 (nodeid と範囲。走れないなら「実装済み・未実走」)

実行:

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_b4_proposal_binding.py
```

結果: `26 passed in 12.95s`

新規負例:

- `test_registry_attempt_outside_analysis_manifest_rejects[base]`
- `test_registry_attempt_outside_analysis_manifest_rejects[sort]`
- `test_registry_attempt_outside_analysis_manifest_rejects[trigger]`

既存正例も `[base]`、`[sort]`、`[trigger]` が通過。対象ファイル全26ケースを実走済みです。`git diff --check` も通過しました。

## 所有外への波及可能性

- `p3_s4_loop.py:2244` の base caller に新しい拒否条件が適用されます。
- `p3_s4_loop_sort.py:494` と `p3_s4_loop_trigger_gating.py:974` も共通関数を呼ぶため、manifest 外 bootstrap を同様に拒否します。
- 共有 fixture は未変更です。通常の registry/manifest 一致 publication の正例は引き続き通ります。
- raw record producer の `_manifest_row()` は下流の同集合ガードとして残りますが、formal bootstrap では今回の検査が先に拒否します。
- issuer、launcher、analysis 系、docs、D1881 関連面には変更ありません。

## 総括

D1880 の実装単位を完了し、formal bootstrap の受理集合を analysis manifest membership で狭めました。対象 suite は全件 green です。