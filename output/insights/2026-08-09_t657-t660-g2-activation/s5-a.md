実装済み・未実走です。pytest/build/commit/stage は行っていません。

### 編集内容

- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:373)
  - activation head を serial 2、state hash `398b1920…bed8` へ更新。
  - production 差分は指定された2行のみです。

- [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:343)
  - genesis golden を singleton head=1 として保持し、実 authority は2 record・Pegasus g2 current・3 hash ever-active として検査。
  - [空 chain の独立 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:476)を追加し、理由を完全一致で固定。
  - [production tail deletion](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1516)を指定の head 不一致 regex に限定。
  - valid suffix と never-active 検査を singleton head=1 合成 authority へ分離。
  - fork child の current 期待値を g2 に更新。

- [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:270)
  - Pegasus current golden を g2 path/SHA/object identity に更新。
  - [active index](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:379)を `{linux-baremetal: 0, pegasus: 1}` に更新。
  - [never-active 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:622)を singleton head=1 authority に隔離。
  - calibration 自己整合検査を current registry だけでなく全3 generationへ拡張。
  - [g1 hash golden](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:1163)は generation 0 参照に変更し、値は不変。

- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_t419_probe_causality.py:1586)
  - authority dirty-path 検査を `00000001.json` / `00000002.json` の2値 parameterize。

- [test_silo_ladder_rung1_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1262)
  - committed g1 hashを `resolve_by_contract_sha256(..., expected_env_tag="pegasus")` で historical 解決。
  - exact `GenerationEntry` を確認してから contract/path/SHAを照合。historical golden は変更していません。

全ファイル走査の結果、段2表外で追加修正が必要な g1-current/head=1 仮定はありませんでした。残る head=1 参照は genesis、issuer unit test、合成 authority の歴史検査です。

### 静的検査

成功:

- 変更5 Pythonファイルの `ast.parse`
- `git diff --check`
- authority serial/state/active rows と g2 calibration SHA の固定値照合
- production 差分が `env_contract.py` の2行だけであること
- `00000001.json` に tracked diff がないこと
- 新設・改名 nodeを拘束する activeなmeta-test／test tableがないこと

`00000001.json` SHAは `6a44b5…34d`、親発行済み `00000002.json` SHAは `f7d15f…c53` のままです。後者は未編集の untracked file として残っています。

pytest nodeid実走は0件です。したがって「緑」「closed」とは申告しません。

### 期待赤と波及可能性

floor未再発行中の期待赤は `certified_writer_admission` 系、floor系、prediction seal系です。それ以外の赤は回帰扱いです。

所有外への静的波及:

- `conftest.py` のsingleton合成 authorityは意図的にhead=1のまま。
- `certified_writer_fixtures.py` はg1 floorをコピーするため、ユーザー再発行前は期待赤。
- T126はprotocol admission不変ですが、`env_contract.py` がcode identityに入るためseries identityは回転します。
- P3 gating、T419、silo producer/driver、env attestation等のcurrent lookupはg2を参照します。
- T419 dirty scopeはauthority directory全体を追跡し、新旧両recordをテストで固定しました。
- silo productionと`validate_current_bindings`は変更していません。

docs、output、floor/freeze関連、`00000001.json`、`00000002.json`は編集しておらず、commitもありません。

## 総括

- g2 activation headと追従テストを実装済みです。
- genesis/g1 goldenとever-active拒否述語は維持しました。
- T-660は非空tail rollbackと空chain理由を分離しました。
- silo committed evidenceは記録hashによるhistorical解決になりました。
- 静的検査は成功、pytestは未実走です。
- floor再発行前の期待赤は未修正のままです。