### B1 壊し B の変異判定は必ず失敗する

重大度: **must-fix**
根拠: `broken-cicada-m-early-reclaim.patch:12–13, 34–38`（適用先 `transaction.cc:934`）は `rts_raised` を EVENT にだけ出す。一方 `launch_cicada_m.py:365–373` は FIRED の `rts_raised` を要求し、欠けた値を 0 とする。
失敗の具体例: MV-B で B 違反が消え、EVENT に `rts_raised=1` が出ても、判定は `survived` になる。
成果物への影響: 事前登録した MV-B の kill を証明できない。
推奨対処: FIRED に `rts_raised` の集計を出すか、EVENT の値を検証して判定する。

### B2 世代更新より先に版の所有状態を変えている

重大度: **must-fix**
根拠: `instr-cicada-trace-m.patch:280–284`（`version.hh:31` への追加）では `trace_owner_=nullptr` と最終事象の store が `trace_gen_` の加算より先。裁定 `s4-ruling.md` の B 仕様は世代加算、release fence、版状態変更の順を指定する。事象の呼出点は同 patch `:170–185, 232–247`（`transaction.hh:173–196, 347–365`）。
失敗の具体例: 読み手が owner の消去後、世代加算前に snapshot を取ると、`g1==g2` のまま `owner!=tuple` となり `B_WINDOW` を出す。
成果物への影響: stock の違反 0 がスケジュール依存で不合格になり、B の診断理由も曖昧になる。
推奨対処: 指定順に直し、owner・事象名を更新する位置を snapshot と終了診断に照らして再検討する。

### B3 母集団の等式が独立した計数になっていない

重大度: **must-fix**
根拠: `instr-cicada-trace-m.patch:107–111, 350–353` で `tx_end_reads_nonempty` と `b_end_checked_*`、`read_calls` と `api_checked` をそれぞれ同じ箇所で増やす。`launch_cicada_m.py:281–286` はその組同士だけを比較し、集計の `tx_begin` も照合に使わない。適用先は `transaction.hh` の `traceEnd` と `transaction.cc:144` の `read()`。
失敗の具体例: 終了経路で `traceEnd` の呼出しが一つ欠けても両側の B 件数が同時に減り、既に照合した tx があれば等式と `b_reached` は通る。
成果物への影響: 「照合済み＝母集団」という一次資料の主張をこの判定では支えられない。
推奨対処: `tx_begin` と終了数の整合を要求し、B の対象 tx 数を照合処理とは別の入口・終了側で数える。API も実際の照合完了数を呼出し数と分ける。

### B4 CUSTOM が裁定外の patch 列を stock として合格にできる

重大度: **should**
根拠: `launch_cicada_m.py:103–107, 640–645, 684–690` は CUSTOM の任意 patch 列を受け取り、`:355–361` は `kind=stock` なら通常の合格を返す。`:395–410` の制限は touch 先と適用だけで、裁定の stock stack との一致は検査しない。
失敗の具体例: CUSTOM に別の `cc/cicada/` patch 列と `kind=stock` を指定し、集計値が整った run を作ると `pass` と記録される。
成果物への影響: `pass` という結果の受理集合が裁定した stack より広がる。
推奨対処: CUSTOM は調査用の分類に限定するか、live の `pass` は固定 patch 列との一致を要求する。

### B5 対照と同一性 build に再実行分がある

重大度: **should**
根拠: `launch_cicada_m.py:82–100` の SMOKE の default K t4 は MAIN-4 に、MAIN-1 の default R t4 は MAIN-5 に再登場する。`:538–546, 709–711` により SMOKE の ycsb 同一性 2 組は IDENT でも再 build される。`:754–756` が同じ job 内の対照しか探さないため共有できない。
失敗の具体例: 先行 job の合格対照があっても、後続 job は対照を再 run・再 build する。
成果物への影響: 生死確認後の node 時間見積りと 2 node 時間の投入判断を押し上げる。
推奨対処: digest と genome・cell・stack・argv が一致する先行結果を対照として参照する。SMOKE 済みの同一性 2 組も IDENT へ引き継ぐ。

## 総括

**NO-GO。** 静的レビューであり、build・適用・実走の合格は確認していない。
417 追加行の主部は、裁定が要求した B の記録、U の三者照合、API 照合、全 field の集計である。単純に行数を見積りへ戻す削除は勧めない。
781 行の起動器では、固定 job の証拠収集と TRACE=0 の 20 build は裁定に必要。一方、CUSTOM の合格経路と重複する対照・build は縮小できる。
壊し U と API、各変異は静的には各一 site・対応する照合に絞られている。B の到達と、既存 mismatch・巡回との単一理由性は実走待ちである。起動器は新壊しでそれらを合否から除外するため、観測値を別途報告すべきである。
TRACE=1 の atomic、fence、集計、版の配置変更は stock のスケジュールを変えうる。TRACE=0 の性能値を使う方針は妥当だが、B の到達と stock の違反 0 は TRACE=1 で実測して評価する必要がある。
**B1〜B3 を直せば、この静的レビューの must-fix は閉じる。** その後も、裁定どおり計算ノードで発火・帰属・母集団・同一性を実証してから GO と判定する。