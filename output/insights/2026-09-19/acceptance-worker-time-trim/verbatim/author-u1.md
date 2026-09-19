## 変更面

U1 を実装しました。変更は F のみ、V は変更不要でした。以下、F＝`test_s8b_ratified_freeze.py`、V＝`test_s8b_ratified_verify.py`。

| file:line | 内容 |
|---|---|
| [F:1003](/work/1/SFC/tanab/izanagi/.codex/worktrees/awtt-u1-author/orchestrator/tests/test_s8b_ratified_freeze.py:1003) | session basetemp 解決、指定 key と SHA256 |
| F:1020 | Git bytes 取得、copy・refresh・status 一致検査 |
| F:1041 | flock、全木保存、metadata、marker の原子的公開、不完全 entry の再構築 |
| F:1097 | campaign 完了直後までを構築単位化 |
| F:1190 | receipt/selector 経路の迂回、copy 先の属性再設定 |
| F:1376 | 構築元・copy 先の計6本を漏洩検査 |
| F:1387 | 指定の新 test 1 本 |

## 決定性と絶対 path の扱い

決定性の根拠は、固定 Git identity/date・SHA-1・autocrlf（F:280–316）、固定 host/process/receipt（F:393–412）、固定 probe・時計等の seam（F:1164–1168）です。全 key の同一性を実証したとは扱っていません。

| 面 | 扱い |
|---|---|
| cert | 後段の bytes 一致検査と構築元・copy 先の漏洩検査を維持 |
| manifest/result binaries・argv | production の相対化結果を保存し、両側の path で検査 |
| journal/result sessions | 各呼出しで再読込み・再直列化・漏洩検査 |
| durable root policy | 構築時だけ使用。capability は metadata に保存しない |
| prepare 属性 | `ccbench_dir`・`cache_root` を copy 先へ再設定 |
| `.git/izanagi` evidence | legacy/v5 とも既存の削除・再構築を各呼出しで実行 |
| selector 証拠 | valid-cell/payload-hit は memo を迂回 |
| その他の disk bytes | `.git`・cache・output を含め全木を symlink 保持で複製。絶対 path の一括置換なし |

## 他 caller への波及

signature・返却 tuple は維持しています。`load_emitter_g1`、V の baseline、独立 builder、g2 builder は AST 不変です。

静的に確認した所有外 caller は以下です。

| file | caller |
|---|---|
| `test_s8b_oracle_driver.py:5991` | `_build_v2_repo` |
| `test_s8b_oracle_report.py:322` | `_ratified_cli_manifest` |
| `test_s8b_oracle_manifest.py:1418,1442` | 実 g1 の selection gate 正例・rule mismatch consumer |
| `test_s8b_verdict.py:1111,1214` | `_real_g1_with_scan_neutral_earlier_result`、実 g1 verdict consumer |
| `test_t080_freeze_migration.py:2150` | `_real_layer2_token` |

`receipt_root=` は既存構築を通り、R・source closure・ccbench pin を維持します。holdout file に直接 caller はありませんでした。

V では共有 helper `_build_launch_repo` の caller が70関数、baseline の caller が8関数あります。load/launch/assertion は毎回実行します。conftest・共有 fixture・登録簿は変更していません。

## 直接呼出しの検証結果

**DIRECT_CALL_PASS**

小さな親・内側 Git repo（各1 commit＋untracked file）で確認しました。

- 通常・xdist 配置の解決と対象外配置の迂回
- key の再現性と各入力変更による分離
- copy＋refresh 後の status byte 一致、symlink 保持
- marker 欠落時の残骸削除・再構築
- 構築例外時の marker 未公開

両 file の `py_compile`、`git diff --check` も成功しました。AST 比較では F が63→64関数、V が105→105関数。既存168 test の本体・decorator・parametrize は不変、追加は指定の1関数だけです。

## 未実走・未確認

pytest、新 test 本体、builder 本体、別 worker/fork 間の消費、全 key の同一性、変異 kill 集合、A/B 性能、受入全走、docs checker は未実走です。親の計算ノード検証が必要です。任意の `--basetemp` が指定形式に合わない場合は、設計どおり memo を迂回します。

## 総括

U1 の実装と指定の静的・直接検証を完了しました。
変更は F のみで、既存 test 定義と検証処理を維持しています。
性能改善・pytest 成功は未確認です。
`git add` / `git commit` は実行していません。