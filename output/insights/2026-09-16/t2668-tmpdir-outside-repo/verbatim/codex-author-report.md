## 総括

プラン v2 の修正を指定 2 file に実装しました。s1 は焦点実走 passed。hardlink は sandbox 制約により「実装済み・未実走」で、closed ではありません。

## 変更内容

- `orchestrator/tests/test_hooks.py`：17・34 行に import、1512〜1522 行で `.izanagi-t2146-hardlink` への移設と配置 assert。
- `orchestrator/tests/test_s1_9pair_figure_provenance.py`：1055〜1060 行で `output/runs` への移設と配置 assert。76〜90 行は未変更。

`git diff --stat`：

```text
 orchestrator/tests/test_hooks.py                   | 13 +++++++++++--
 orchestrator/tests/test_s1_9pair_figure_provenance.py |  5 ++++-
 2 files changed, 15 insertions(+), 3 deletions(-)
```

最終 diff に変異は残っていません。`git diff --check` 成功。commit 操作はしていません。

## 実走結果

- 両 module の import：成功。
- `orchestrator/tests/test_s1_9pair_figure_provenance.py::test_p9_production_provenance_keeps_historical_marker_for_every_campaign`：**1 passed**。M3 の in-memory 変異は追加した配置 assert で **KILLED**。
- `orchestrator/tests/test_hooks.py::test_t2146_authority_hardlink_alias_is_denied_in_both_guards`：pytest は **failed**。1520 行の `mkdir` が `/work/1/SFC/tanab/.izanagi-t2146-hardlink` に対する `EROFS` で停止。`tempfile.mkdtemp()` を渡した直接呼出しも同じ結果でした。

hardlink は実 authority `/work/1/SFC/tanab/dev-wave-authority/acceptance-issuer-public-key.pem` の存在・両 guard の inode index 検査まで通過しました。hardlink 作成と synthetic fallback はどちらも未到達で、`synthetic_authority` は未初期化です（`None` 判定前）。

## 波及可能性

- `same_device_root` は対象関数のローカル変数で、他 test と共有しません。
- `_REPO`、authority 定数、共有 fixture は未変更。canonical／lexical alias・許可境界などの他 test の入力は変えていません。
- module import に `tools.acceptance_shards` の依存が加わります。import 成功を確認しました。
- test 名・数・引数は不変で、`_REAL_REPO_NODE_INVENTORY` の登録変更は不要と判断します。
- s1 の generator・campaign 入力・共有 helper は未変更。並列 consumer に対しては repo 直下の一時 dir 生成を解消します。

静的差分上、scope 前後で既存の受理・拒否条件は同じです。追加検査は指定された配置 assert のみです。

## 未実走・未完了

hardlink の拒否判定完走と M1／M2 の変異検証は未実施です。親による sandbox 外での実走が必要です。今回の焦点検証は親の全走を代替しません。