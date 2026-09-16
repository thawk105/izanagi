## 前提と読んだもの

指定の8ファイルを全文確認しました。裁定ファイルの SHA-256 は指定値と一致しました。補足として PBS の指定逐語も読みました。

## 実装したもの

作成ファイル：  
[/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2635-high-band-control-feasibility/output/insights/2026-09-16/t2635-high-band-control-feasibility/probe_t2635.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2635-high-band-control-feasibility/output/insights/2026-09-16/t2635-high-band-control-feasibility/probe_t2635.py)

実効 **188行**（空行・comment 除外）。主要関数：

- `module`: 29行 — 無改変 import
- `inventory`: 51行 — 狭窓側の辺在庫
- `auxiliary`: 57行 — 生 JSON の補助要約
- `driver_admission`: 91行 — driver 受理・拒否の確認
- `analyze`: 113行 — J1・記述統計・代理計算
- `selftest`: 157行 — 手で固定した期待値との照合
- `main`: 180行 — 引数・create-only 出力・失敗処理

JSON の top-level keys：

`schema_version`, `input`, `analyzer`, `driver`, `preregistration`, `headline_eligible`, `throughput_scope`, `certified`, `scope`, `grounds`, `reference_only`, `candidates`, `limitations`, `omitted`。

## 自己検査の実走

以下を実行し、いずれも **rc=0** でした。

```bash
PYTHONPYCACHEPREFIX=/tmp/t2635-author-pycache python3 -B -m py_compile /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2635-high-band-control-feasibility/output/insights/2026-09-16/t2635-high-band-control-feasibility/probe_t2635.py
```

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2635-high-band-control-feasibility/output/insights/2026-09-16/t2635-high-band-control-feasibility/probe_t2635.py --help
```

コンパイルキャッシュは `/tmp` に配置しました。本番 trace への実行と `--selftest` は未実行で、親が行います。

## 現行の受理・拒否挙動

以下はコードの静的確認です。

| 条件 | 挙動・rc |
|---|---|
| 出力先が既存 | 書き込まず rc=1。最終書込みも `open('x')` |
| 必須引数不足・絶対パス違反 | argparse が拒否、rc=2 |
| 解析器 import 失敗 | `measurement_incomplete`、rc=1 |
| driver import 失敗 | 該当項目を `measurement_incomplete` / `source: "static_reading"` として継続。他が成功すれば rc=0 |
| selftest 不一致 | 不一致項目を報告、通常出力を書かず rc=1 |

## 波及の静的列挙

既存 caller・共有 fixture・consumer test への変更による波及は無いです。probe だけを追加し、既存コードへの接続、module 属性の差替え、fixture・テスト編集を行っていません。import の実行時依存は未確認です。

## 未実装・未確認

未実装はなし。窓統計・ACF も含め、`omitted: []` です。

実データ集計、driver import・受理検証、selftest の成否、実行時メモリ使用量は未確認です。

## 総括

指定の probe 1 本を作成しました。  
構文検査・`--help` は rc=0 でした。  
docs・解析器・driver・既存テストは編集せず、git add・commit も行っていません。  
本番実行と固定期待値の照合は親へ引き継ぎます。