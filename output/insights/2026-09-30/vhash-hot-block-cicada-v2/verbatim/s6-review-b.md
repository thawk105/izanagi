### B1: fig-write の保存が失敗する
重大度: **must-fix**
根拠: `tools/plotting/plot_vhash_cicada_hot_block.py:149–150,176`。入力 aggregate の Path を計数値の辞書で上書きし、`_save()` が `source.resolve()` を呼ぶ。
成果物への影響: COUNT 行がある通常の集計では fig-write とその provenance を生成できない。
推奨: 計数値には別の変数名を使い、実際の `_save()` を通す作図テストを追加する。

### B2: 図の系列を見分けにくい
重大度: **should-fix**
根拠: `tools/plotting/plot_vhash_cicada_hot_block.py:103–104,117–123`。B の 2 腕は同色・同マーカー、post の 2 腕も同色・同マーカーで、fig-ro では GC 間も同じ表示になる。
成果物への影響: fig-k・fig-ro から K と GC ごとの差を判読しにくく、回復幅の図示が弱くなる。
推奨: 腕ごとに色またはマーカーを分け、fig-ro では GC ごとに線種も分ける。

### B3: 見積りで build を二重計上しうる
重大度: **should-fix**
根拠: `orchestrator/campaign/vhash_cicada_hot_block.py:209,1115–1117,1162–1167`。`smoke_seconds` は全 build を含む一方、estimate は `build_seconds` を別に加算する。
成果物への影響: smoke から本走へ進む経路では上限判定が過大になり、不要な格子縮小や停止を招きうる。
推奨: 実際に投入する独立 build job の有無に合わせて加算する。perf・COUNT・trace の全走数、変異、焦点走・監査は見積りに入っている。

### B4: 厳密適用できない旧壊しへの切替が残る
重大度: **nit**
根拠: `orchestrator/campaign/vhash_cicada_hot_block.py:35–41`。`USE_ORIGINAL_POST_BREAKS = False` は固定で、実装子の報告では旧 B1・B2 patch の post 上への厳密適用は失敗している。
成果物への影響: 現行の判定結果には影響しない。切替時に build を失敗させる分岐が残る。
推奨: 固定フラグと旧 patch 側の分岐を削り、post 用 patch を直接指定する。

## 総括

**NO-GO**。B1 を直してから作図を実走確認する必要がある。変更は裁定 B8 を含む所有範囲内で、指定外への変更は見当たらない。旧テスト関数 24 本は現行にもあり、求められていない機能・検査・assert の削除は静的確認では見つからなかった。post 248 行、各壊し 76～131 行、driver 本体差分 432 行で目安内。計器は post の待ち・保持・CAS 再試行・隣接失敗を備え、T-2927 の四項目を調べる経路もあるが、build・trace・判定器・性能計測は未実走である。