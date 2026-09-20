# 改訂案 (段 3 相談の攻撃対象、段 4 で確定)

## (a) DW-M08 — 現行 (822 bytes)

```
## DW-M08 — 失敗 node と検出力

harness は rc と失敗 test node を毎回記録する。pytest は `-rf`、node 抽出は F71 に従う
（正本は job stdout 全文、行前置と ANSI を除去、` - ` 無しは行末まで、rc≠0 で 0 件は
fail-closed 停止）。
**期待 node は完全集合**で、同形式へ正規化した記録 node との完全一致だけを KILLED とする（F33）。
確定できない場合に限り初回を probe と明記し erratum を残して再登録・再走する。
受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ
別枠記録する。テスト強化だけの wave は新テストと変更前 HEAD 版の双方へ変異を走らせ、新テスト
だけが検出する差分を示す。
```

## (a)+(b) DW-M08 — 案

```
## DW-M08 — 失敗 node と検出力

harness は rc と失敗 test node を毎回記録する。pytest は `-rf`、node 抽出は F71 に従う
（rc≠0 で 0 件は fail-closed 停止）。
**期待 node は完全集合**で、同形式へ正規化した記録 node との完全一致だけを KILLED とする（F33）。
期待 node は login self-run（変異ごとに注入 → 自走 harness → 原 bytes へ復元し sha256 一致を
assert、`DW-O19`）で観測し、dispatch final を 1 回。pytest 専用 allowlist と、parametrize /
fixture / skip で自走と pytest の node が食い違う test は dispatch probe（初回を probe と明記）へ戻す。final の待ちは job dir で段 7 草稿と検査準備に充て、後は結果値と commit だけ。
受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ
別枠記録する。テスト強化だけの wave は新テストと変更前 HEAD 版の双方へ変異を走らせ、新テスト
だけが検出する差分を示す。
```

## 削減案 (L1.5、安全義務は落とさない)

1. workers.md 前文: 「plan、敵対相談、実装、レビュー・fix worker の正本。入口が指定する leaf 節を worker 起動前に読む。」→「段 2・3・5・6 の worker 契約の正本。」(読み指示は入口の dispatch 表と重複)
2. DW-S06-C 末尾「成立した条件の operations と `DW-G05` を適用する。」を削除 (入口表の段 6 U/C 行と重複)
3. DW-M05 の「同toolは元ソースの固定HEAD束縛、起動/復元時の内容比較、`flock`単一走行、逐次flush、HEAD/spec束縛の`--resume`、signal復元をfail-closedで強制する（F32）。」→「同toolは固定HEAD束縛、復元時の内容比較、`flock`単一走行、`--resume`、signal復元をfail-closedで強制する（F32）。」
4. DW-O01 の「`--max-*`は非権威で増量可。」を削除 (CLI の `--help` が同じ非権威表示を持ち、義務ではない)
5. DW-S05-A の「乖離量は非関門。」を削除 (`check_wave_startup.py --mode midflight` の help「main 乖離量は関門でない」と重複)
