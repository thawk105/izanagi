4 系統すべて実装しましたが、sandbox の dispatch 失敗によりテストは未実走です。そのため判定はすべて `partial` とします。

## 対応表

| 系統 | 判定 | 対応 |
|---|---|---|
| 1. site 非決定性 | partial | autouse fixture で既定 site を `OTHER` に固定。site-policy 単体テストは明示 fixture で実 detector を選択。M5 は引き続き `PEGASUS_COMPUTE` を明示 |
| 2. 検査順序 | partial | qualification・screening・既存 shape 検証を認可より先へ戻し、認可は最初の書込みより前を維持 |
| 3. 認可入力漏れ | partial | AST で全対象 caller を列挙し、通常経路の漏れゼロを確認 |
| 4. env literal | partial | `execution_guard.py` の環境 tag literal を registry の一意解決 API へ置換。AST 検査で禁止 literal なし |
| 回帰 | なし（静的確認） | ただしテスト未実走のため最終確定ではない |

## 変更ファイル

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/tests/conftest.py:36)
  - `current_site()` を既定 `OTHER` にする autouse fixture。
  - テスト自身による monkeypatch・直接差替えが後勝ちになる構造。

- [test_site_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/tests/test_site_policy.py:23)
  - site detector 自体を検査するモジュールとして明示宣言。

- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/campaign/pipeline.py:595)
  - qualification、screening、extra-correctness shape 検証の後へ認可検査を移動。
  - WAL/build 書込み前という境界は維持。

- [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/campaign/screening_driver.py:98)
  - floor JSON と既存入力検査を先行。
  - 認可は `layout.ensure()` と WAL repair より前。

- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/campaign/env_contract.py:393)
  - required-attestation 契約を registry から一意解決する fail-closed API を追加。

- [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/campaign/execution_guard.py:84)
  - `"pegasus"` literal を上記 API に置換。
  - A2 の5条件は削除・緩和していない。

- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/tests/test_screening_driver.py:150)
  - 認可負例へ有効な floor 入力を追加。期待値は変更せず、認可拒否を単独理由化。

変更量は7ファイル、66追加・15削除です。docs、commit、add、push はありません。

## 系統3の機械列挙

`rg` で271候補行を抽出後、import alias・相対 import を解決する AST 列挙で絞り込みました。

| API | 総数 | 認可引数あり |
|---|---:|---:|
| `pipeline.evaluate` | 43 | 42 |
| `run_campaign` | 39 | 39 |
| `prepare_screening_campaign` | 8 | 8 |
| `evaluate_candidate` | 8 | 8 |

`pipeline.evaluate` の残る1件は [M1の必須引数欠落負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix2-a/orchestrator/tests/test_campaign.py:2205) です。これを除く実効 caller の認可漏れはゼロです。

## 期待値不変更の確認

変更したテストについて、HEAD と worktree の全 `assert` および `pytest.raises` AST fingerprint を比較しました。

- `conftest.py`: 0 → 0、一致
- `test_screening_driver.py`: 21 → 21、一致
- `test_site_policy.py`: 61 → 61、一致

regex、assert、skip、xfail、期待結果の反転・削除はありません。変更したのは fixture 宣言と認可負例の入力だけです。

## 検証

成功:

- 変更Python 7ファイルの `ast.parse`: 7/7
- env literal 静的検査: `execution_guard.py` 0件、`env_contract.py` の許可領域外0件
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

未実走:

- 焦点テスト
- 単一 env-literal node
- `--collect-only`

いずれも `tools/run_tests.py` が計算ノード dispatch を選び、sandbox 内の `qstat -Q` preflight が失敗して rc=16でした。pytest は直接起動していません。最初の試行では未初期化 submodule marker の警告も出ましたが、テスト開始前に dispatch で停止しており、submodule由来のテスト赤ではありません。

## 総括

4系統の修正、caller漏れゼロの静的証明、期待値不変更の監査まで完了しています。残件は親環境での焦点再走と受入全走のみです。現状態は「実装済み・静的検査済み・テスト未実走」です。