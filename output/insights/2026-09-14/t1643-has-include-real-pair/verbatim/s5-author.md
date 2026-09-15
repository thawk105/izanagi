## 実装したもの

[tools/t1643_has_include_pair_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1643-impl/tools/t1643_has_include_pair_probe.py) のみ作成しました。

実 checker 関数の subprocess を観測し、実 argv・env・生出力・compiler 情報・拒否発生箇所を JSON に保存します。5 種の対照、上書き拒否、未測状態の区別を実装しました。

## 実走したもの (nodeid・argv・結果)

nodeid：なし。probe 自体を実走しました。

```bash
python3 -B tools/t1643_has_include_pair_probe.py --output /tmp/t1643-author-login.json
```

最終版は cwd=`/tmp` からも実走しました。

```bash
python3 -B /work/1/SFC/tanab/izanagi/.codex/worktrees/t1643-impl/tools/t1643_has_include_pair_probe.py --output /tmp/t1643-author-cwd-check.json
```

両方 rc=0。各回の結果：

- 真偽取得 960、preprocess error 640、compiler 不在 400。
- compute 未測の placeholder 2。
- guard 直呼び 500 件。
- configure 全 10 回失敗。探索列は再構成として保存。
- g++／g++-11／g++-12 の対照成立。g++-9／g++-13 は一部不成立。

既存出力への再実行は rc=2。JSON の値・rc・反転対照・実関数出力との対応・最終ソース hash を検証しました。

## 実装済み・未実走のもの

compute 実走、compile command 取得成功経路、既存テスト全走は未実施です。親の受入全走を代替しません。

header 補助列は所有制約により `/tmp` の相対構造を使用しています。実 header 位置との違いは `limitations[]` に記録しました。

## 現行の受理・拒否挙動

現行 guard は対象 3 ファイルを非再帰走査します。条件指令・define 本体の include operator と貼り合わせを拒否しますが、前段のマクロ照会失敗は `other_error` です。

今回、安全な対照の受理 36 件、専用拒否 284 件、前段エラー 180 件を記録しました。受理集合は変更していません。

## 波及可能性の静的列挙

- caller：`pipeline`、`loop`、`buildcache` の `resolve_evidence` 呼出し。
- 共有入力：CCBench の Options・protocol CMake・include ファイル。
- consumer test：`test_source_digest_has_include_rejected`、`test_source_digest_token_paste_bypass_rejected`、関連マクロ試験。

これらへの編集はありません。

## 総括

probe は実装・login 実走済みです。compute と admission 実 pair は未完了であり、`closed` とはしません。対照不成立を含む生データを保存し、欠陥・安全性の結論は出していません。docs 編集・commit・push はしていません。