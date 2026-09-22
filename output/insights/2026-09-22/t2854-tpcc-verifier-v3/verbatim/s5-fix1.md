## 原因

新規試験が `DSG.adj` のtupleとsetという表現差を直接比較していました。辺集合に正規化したところ、素のrunnerでは後続 assertion もすべて通りました。

## 変更

[test_verifier.py:3401](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u4/orchestrator/tests/test_verifier.py:3401) に辺集合の変換を追加し、3424・3430行の比較へ適用しました。

- 今回：追加5行・削除2行、計7行。
- R9累計：production **266 / 550行**、tests **436 / 800行**（前段からの通算差分）。
- productionは未変更。既存試験部分と自走runnerはHEADとバイト一致。
- `git diff --check` 成功。

## 実走結果（逐語）

指定pytestは起動前に拒否されました。

```text
Command blocked by PreToolUse hook: [guard_bash] 拒否: interpreter の baseline 重量対象 (pytest) を拒否します: Pegasus ログインノードでは重い処理を実行できません。qsub または qlogin を使い、Pegasus 計算ノードで実行してください。
```

代替の `tools/run_tests.py` も終了コード16、本体未起動でした。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
```

`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` は終了コード0。

```text
132 passed, 0 failed, 0 skipped
```

素のrunnerの失敗nodeid：なし。pytestの件数・失敗nodeid：本体未起動のため未取得。

## 切り分けた実装の誤り

なし。正規化後、versions・producer・result・`result_to_dict_v3` の経路間一致と各試験固有の期待がすべて通りました。期待値の緩和はしていません。

## 変異の位置表

M1〜M15の対象位置は前段から変更なし。変異実走は未実施です。

## 未解決

指定pytestでの確認が残っています。consumer testsも今回は未実走です。

## 総括

新規試験の隣接表比較2か所を辺集合へ正規化しました。
productionと既存試験は変更していません。
素のrunnerは既存114件・新規18件の全132件が成功しました。
後続 assertion に実装不具合は現れませんでした。
R9の規模上限内です。
commit・push・branch操作はしていません。
指定pytestの成功確認は未完了です。

指定pytestの直接起動は自動承認審査（PreToolUse guard）に拒否されました。理由はPegasusログインノードでの直接起動禁止で、代替dispatchもインフラ障害により起動できませんでした。