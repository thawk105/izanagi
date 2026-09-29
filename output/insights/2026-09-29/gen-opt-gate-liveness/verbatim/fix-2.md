## N1 の対応

**closed（実装済み・未実走）。** [起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py:243) で JSON の `results[0].verdict` を確認し、[同ファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py:260) で判定器の rc 0・1・3 を判定結果として扱うよう変更しました。終了値の意味は `orchestrator/verifier/cli.py` の `main()` 末尾で確認し、コメントに出典を記しました。

## 終了値と JSON の扱い

| 判定器 rc | 有効な JSON と `results[0].verdict` | 起動器の動作 |
|---|---|---|
| 0 | あり | 判定を記録し、`prereg` を評価して続行 |
| 0 | なし | 実行失敗、rc 1 |
| 1 | あり | non-serializable の判定を記録し、`prereg` を評価して続行 |
| 1 | なし | 実行失敗、rc 1 |
| 3 | あり | indeterminate の判定を記録し、`prereg` を評価して続行 |
| 3 | なし | 実行失敗、rc 1 |
| その他 | あり | 実行失敗、rc 1 |
| その他 | なし | 実行失敗、rc 1 |

有効な判定結果では B1 の verdict は記録のみ、stock は診断です。fix は serializable かつ certified という期待から外れ、照合器の到達可能性が pass なら事前登録不一致として rc 4 になります。

## 検査と作業木

変更ファイルは起動器のみ。**306 行、SHA-256 `9ecf2ca132214b452ce2918c516f04ce18c98438734ec4763d12ed5bde7621c0`**。`python3 -m py_compile` は rc 0、`git diff --check` も rc 0 でした。

`git -C external/ccbench status --porcelain` の出力は空です。

## 総括

N1 のコード修正は完了しました。起動器は**実装済み・未実走**です。