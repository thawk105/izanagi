## 前提と読んだもの

指定6ファイルを全文読み、段4裁定を優先しました。親側 repo は読んでいません。

## 実装したもの

[probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py) の1本だけを作成しました。実効 **97行**。

主要関数：`absolute`:18、`identity`:24、`summarize`:31、`analyze`:39、`main`:89。

生の計数、無改変J1、高域比較、低域集計、刻み軸全10組を実装。`omitted` は空です。

## 自己検査の実走

bytecode の保存先指定：

```bash
export PYTHONPYCACHEPREFIX=/tmp/t2583-probe-author-pycache
```

以下を実行し、それぞれ **rc=0**。

```bash
python3 -B -m py_compile /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py
```

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py --help
```

**本番 trace への実行はしていません。**

## 現行の受理・拒否挙動

以下は静的確認です。

- 既存 `--output`：書き込まず rc=1。作成時も `open('x')` で上書きを防止。
- 必須引数不足：`argparse` が rc=2 で終了。
- 解析器 import 失敗：標準エラーへ `measurement_incomplete` を出し、rc=1。出力JSONは作成しません。

正しさ判定・受理集合は変更していません。

## 波及の静的列挙

直接の変更波及はありません。既存 caller・共有 fixture・consumer test を編集せず、解析器の bytes・module 属性も変更しない独立CLIです。既存側からの参照有無の横断調査はしていません。

## 未実装・未確認

裁定の未実装項目：なし。

数値結果、失敗分岐の実走、Python 3.10実機での動作は未確認です。

## 総括

指定の probe 1本を実装し、構文・起動確認は成功しました。
docs・解析器・テスト・台帳は未変更です。
`git add`・commit・その他のgit操作はしていません。
本番実測は親側に残しています。