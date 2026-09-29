## must-fix

1. **主張:** D-C と境界保持種別の世代付き slot は、公開をまたぐ tx の記録を取り逃す。**根拠:** 世代と rts は `begin()` で固定される（`patches/instr-cicada-version-lifetime.patch:406–417`）。公開後に epoch が進んでも、同じ tx の `mainte()` は旧世代の slot に flag 時刻を書く（同 `:803–818`）。次の公開で leader は新世代だけを読む（同 `:890–906,947–965`）。**放置時の影響:** D-C の有効間隔と保持種別が tx の長さや GC 間隔に応じて欠測し、図の条件間比較が偏る。**推奨:** flag 事象の時点で世代を決め、公開をまたぐ tx の rts・種別も leader が参照できる設計に直す。修正後は各条件の除外率を併記する。

2. **主張:** 計測レコード数が裁定の 1M に固定されていない。**根拠:** 補遺は「1M、md_2 と同じ」と定める（`s4-ruling.md:58–61`）が、較正は RSS により 2M・4M を選び得る（`orchestrator/campaign/vhash_cicada_vlife.py:623–651`）。テストも 2M の受理を期待する（`orchestrator/tests/test_vhash_cicada_vlife.py:428–431`）。**放置時の影響:** 一次資料の測定値と anchor が異なるレコード数の結果になり、md_2 との比較が成立しない。**推奨:** 診断走を 1M に固定し、較正結果は参考値として記録する。

3. **主張:** `readonly_deep` と `readonly_reads` の母集団が一致しない経路がある。**根拠:** 深部計数は選択版の `deleted` 判定前（`patches/instr-cicada-version-lifetime.patch:514–520`）、read 計数は判定後（同 `:535–543`）。driver は前者が後者以下であることを要求する（`orchestrator/campaign/vhash_cicada_vlife.py:237–240`）。**放置時の影響:** deleted 版に到達した走で深部率が膨らむか、計器行全体が拒否される。**推奨:** 両計数を同じ成功 read の位置へ移す。

## should

1. **主張:** D-C の第 3 項には公開後の計器処理時間が入る。**根拠:** `cicadaLeaderWork()` が MinRts を公開して flag を戻した後、epoch 更新と MinRts 読みを経て `now` を採る（`external/ccbench/cc/cicada/util.cc:315–321`; `patches/instr-cicada-version-lifetime.patch:910–919,985–991`）。**放置時の影響:** 図の「leader observation」は leader の公開待ちだけでなく計器自身の遅延を含む。**推奨:** 公開直後の時刻を先に採り、項の名称と定義にも採時点を明記する。

2. **主張:** 観測者効果は条件によって異なる可能性が高い。**根拠:** leader は毎回 256 要素の配列群を初期化し、全 flag と slot を読む（`patches/instr-cicada-version-lifetime.patch:883–906`）。ro commit も `rdtscp`、flag 読み、slot の atomic 更新を行う（同 `:841–860`）。**放置時の影響:** 公開間隔・境界年齢は長い側、ro commit 頻度は低い側へ動き得て、その大きさも ro 率で変わる。**推奨:** 裁定どおり anchor と md_2 を並べ、計器増分と同時刻対照ではない限界を一次資料に記す。

3. **主張:** MUT-7・MUT-8 の静的テストは登録された変異全体を保証しない。**根拠:** MUT-7 は guard 内に `draw.next()` が残れば guard 外への追加抽選を検出しない（`orchestrator/tests/test_vhash_cicada_vlife.py:290–300`）。MUT-8 の正規表現は `__atomic_store_n` による GCFlag 書込みを拾わない（同 `:301–306`）。**放置時の影響:** retry 再抽選または ro 経路の flag 書込みを含む patch が、対応テストを通過し得る。**推奨:** 変異位置を限定した差分テストと、ro block の書込み API を網羅する検査を加える。MUT-2 の fixture も三項不一致に加え公開間隔超過を起こすため、単一理由性を再確認する（同 `:133–159`; driver `:269–277`）。

## nit

- **主張:** D-C の図題は「leader observation」を待ち時間として読ませやすい。**根拠:** `tools/plotting/plot_vhash_readonly_share.py:230–245`。**放置時の影響:** 図の第 3 項の解釈が採時点より強くなる。**推奨:** 採時点を示す表現にする。

## 親の所見 P-1 の判定

**中核は real、量の断定は未確認。** YCSB は `leaderWork()` の後に `begin()` を呼び、retry でも再び `begin()` に入る（`external/ccbench/include/ycsb.hh:102–113,149–165`）。世代はその `begin()` で一度決まり、更新 tx の flag は後の `commit()` 内 `mainte()` で上がる（`external/ccbench/cc/cicada/transaction.cc:949–956`; patch `:406–417,803–818`）。途中で公開されると epoch だけが進み、当該 tx の flag と rts は次回 leader が読む世代に載らない。ro tx も同じ固定世代の slot に観測時刻を残す（patch `:841–855`）。したがって `dc_generation` と `holder_unresolved` への条件依存の偏りは実在する。一方、「gc_inter_us=10 で**大半**」は静的検査からは確定できず、実測が必要。

ro commit が GCFlag・`gcstart_` を書かない点、既定 −1/0 では抽選・書換えへ入らない点、初回手続き guard による retry の保持はコード上確認できた（patch `:347–377,841–865`）。前処理・バイナリ一致と実走は未確認。条件表の新規 86 件、D-F の式、調整済み genome の compile command 照合はコード上整合している（driver `:59–112,360–363`）。

## 総括

**NO-GO。** 世代を固定する計器と 1M 条件の逸脱を直してから測定を受け入れるべきです。今回は指定どおり静的検査のみで、テスト・smoke の実測は行っていません。