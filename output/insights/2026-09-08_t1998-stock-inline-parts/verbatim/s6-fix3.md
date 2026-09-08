## 足した負例

- M12: 両 arm の digest を同じ非 canonical hex64 に変更し、manifest 投影と WAL hash を整合させた負例を追加しました。[test_t1998_stock_inline_pair.py:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:667)
- M9: submitter の Python heredoc を実行し、repo 内側は拒否、外側は受理されることを検査します。[test_t1998_launcher_contract.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_launcher_contract.py:82)

## 同型の穴の棚卸し

同型の穴があり、挙動検査へ強化しました。

- `.git` ancestor 拒否も実行して確認。[test_t1998_launcher_contract.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_launcher_contract.py:107)
- receipt の hardlink 拒否も実行して確認。[test_t1998_launcher_contract.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_launcher_contract.py:158)
- queue predicate は `if False and` で fail-open にならないため対象外です。
- 既存 parametrize ID と期待値は変更していません。

## 実走した検査

最終差分で指定 harness を実走しました。

- `test_t1998_stock_inline_pair.py`: 30 passed / 0 failed、rc=0
- `test_t1998_launcher_contract.py`: 7 passed / 0 failed、rc=0
- `git diff --check`: 問題なし

## 単独で赤になることの根拠

- M12: canonical 検査より前は manifest の object 性と digest の hex64 形状しか確認しません。[t1998_stock_inline_pair.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:648)  
  テストでは両 arm の manifest と `result.toolchain` が同一であることを確認してから、digest だけを同値へ変更しています。[test_t1998_stock_inline_pair.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_stock_inline_pair.py:690) 後段の arm 間比較と result 投影も通るため、canonical 再計算だけが拒否します。[t1998_stock_inline_pair.py:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/t1998_stock_inline_pair.py:661)

- M9: 実行断片で先行するのは、存在する path の `resolve(strict=True)` だけです。[submit_t1998_balanced_stock_inline.sh:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/submit_t1998_balanced_stock_inline.sh:51)  
  テストは repo 内入力に `.git` ancestor がないことを明示しており、後続 gate は先に拒否できません。[test_t1998_launcher_contract.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/test_t1998_launcher_contract.py:95) したがって repo 関係 predicate を無効化すると、拒否 assertion が単独で赤になります。

## 総括

変更は所有対象のテスト 2 ファイルだけです。実装 source、docs、output は未変更で、`git add` と commit も行っていません。