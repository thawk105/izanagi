## 前提と読んだもの

指定の5ファイルをすべて読みました。対象 probe、凍結仕様、レビュー A・B、解析器です。親側 repo は参照していません。

なお、対象分岐の所見はレビュー B にあり、指定のレビュー A にはありませんでした。

## 直した箇所

[probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py:66) の1箇所のみ修正しました。

変更前（66行）:

```python
    contrast['feasibility'] = 'no_high_band_observation' if not right['high_band_pair_count'] else 'no_nonzero_high_band_sign' if not counts[RIGHT][MAIN] else 'no_common_high_band_edge' if not k and counts[LEFT][MAIN] else 'measurement_incomplete' if not counts[LEFT][MAIN] else 'insufficient_common_support' if k < 10 else 'executable'
```

変更後（66行）:

```python
    contrast['feasibility'] = 'no_high_band_observation' if not right['high_band_pair_count'] else 'no_nonzero_high_band_sign' if not counts[RIGHT][MAIN] else 'no_common_high_band_edge' if not k else 'insufficient_common_support' if k < 10 else 'executable'
```

削除した旧69–70行（置換なし）:

```python
    if contrast['feasibility'] == 'measurement_incomplete':
        raise ValueError('left side has no nonzero high-band sign; preregistered feasibility case undefined')
```

実効行数は **97 → 95行**（空行・コメント除外）。`feasibility` の代入候補は仕様の5語だけです。

## 変えていないことの確認

行番号は修正後の probe を指します。

| 項目 | 無変更の箇所 |
|---|---|
| 帯域述語 | 13–14行 |
| 辺と符号の対応 | 53–55行 |
| ゼロ除外 | 56–58行の既存部品呼出し。ゼロ計数保存は34–37行 |
| 推定量 | 34–35行、64行 |
| 重み | 64・70行の既存 `_fixed_edge_comparison` 呼出し |
| JSON field 構成 | 37・59–68・70–85行の構成を維持 |
| 刻み軸の数え方 | 15・83行 |
| 既存 J1 の呼び方 | 47–49行。戻り値保存は82行 |

上記の置換・削除以外は変更していません。解析器、テスト、凍結仕様、docs、台帳は編集していません。Git コマンド・commit・`git add` も実行していません。

## 自己検査の実走

構文確認は **rc=0**。生成キャッシュを `/tmp` に指定しました。

```bash
PYTHONPYCACHEPREFIX=/tmp/t2583-fix-pycache python3 -B -m py_compile /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py
```

起動確認は **rc=0**。ヘルプが表示されました。

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2583-backoff-high-band-sign/output/insights/2026-09-15/t2583-backoff-high-band-sign/probe.py --help
```

本番 trace の再実行、pytest、`run_tests.py` は実行していません。

## 出力が変わらない理由

今回の入力では、依頼文とレビュー B が示すとおり `right['high_band_pair_count'] == 0` です。66行の最初の条件 `not right['high_band_pair_count']` が真になり、修正前後とも `no_high_band_observation` で確定します。

変更した後続条件は評価されず、削除した例外の条件も修正前から偽でした。他の計算・JSON 構成・直列化は無変更なので、同一入力・解析器・引数での出力は変わりません。再実測による出力一致確認は行っていません。

## 総括

指定の分岐修正と例外削除を完了しました。  
実効95行で、構文確認・`--help` はともに rc=0 です。  
今回の入力の出力不変性はコード条件から確認し、再実測は親に委ねています。