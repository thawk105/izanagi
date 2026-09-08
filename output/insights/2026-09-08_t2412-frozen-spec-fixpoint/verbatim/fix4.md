## 直した内容

- [orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:66): `_install_git(monkeypatch, root)` に更新し、廃止済みの `spec_relpath` 引数を除去。

## 変更後の挙動

synthetic fixture が現在の `_install_git` signature に適合します。`loaded_head` は引き続き `driver_tests.HEAD` で、模擬 git の HEAD 応答と一致しています。期待値・production・受理集合は変更していません。

## 実走した検査

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` — runner rc=16。Pegasus の `qstat -Q` preflight が失敗し、pytest child は未起動。全 nodeid は未実走です。
- `git diff --check -- orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` — rc=0。
- queue-state 確認 — rc=0。ただしキュー状態は観測不能。

## 波及可能性

テスト用 synthetic source の構築だけに影響します。対象の16件に共通する fixture 呼び出しが修正され、production の挙動には影響しません。

## 未了・判断を仰ぐ点

実装済み・未実走です。Pegasus dispatch が復旧後、対象ファイル全体の再実走が必要です。判断を仰ぐ点はありません。

## 総括

- 古い `spec_relpath` 引数を1箇所から除去しました。
- `loaded_head` と模擬 HEAD の整合を確認しました。
- 期待値・production・他ファイルは変更していません。
- pytest は基盤障害により未実走です。