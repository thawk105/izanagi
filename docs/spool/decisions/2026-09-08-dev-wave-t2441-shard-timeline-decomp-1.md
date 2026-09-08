---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2441-shard-timeline-decomp
seq: 1
---

## {{D:acceptance-residual-is-mostly-run-invariant}}. 受入 wall の残余は 9 割が走を跨いで動かず、動く分は主に collection に出る

**決定:** 受入全走の残余 (shard の wall − 最大 worker 占有) を次の 4 成分で読む。
`collection + dispatch + 実行中の遊び + teardown`。ここで `dispatch` は collection 終了時刻から
最初の test 開始時刻までを指す。**この等式は成分の定義から代数的に成立する恒等式であって、
観測の完全性の検証ではない。** 情報を持つのは境界の値そのものである。

**この分解の上で次を確定する。** 数値は 2026-09-08 の K=3 が 3 shard 揃った 62 走・shard 186 本、
生データは `output/insights/2026-09-08_t2441-shard-wall-decomposition/decomposition.json`。

- **残余の 88〜97% は、どの計算ノードで走っても払っている。** 成分別の観測最小値の和は
  shard-0 で 75.6 秒 (collection 50.9 + dispatch 18.4 + teardown 6.4)、他 2 shard で 53 秒台。
  残余の中央値はそれぞれ 86.4 / 55.8 / 55.6 秒である。
- **走ごとに動く分は主に collection に出る。** 残余上位 25% の成分超過は shard-0 で
  collection が 70%、dispatch が 28%。他 2 shard では collection が 97% を占める。
- **実行中の遊びはほぼゼロである** (186 本の中央値 0.01 秒、最大 2.13 秒、1 秒超は 9 本)。
  これは恒等式ではなく実測であり、worker が互いを待って wall だけが伸びる区間は現行コードに
  残っていないことを示す。
- **D1369 が「未計測」と書き残した最遅 shard 固有の約 21.9 秒は、consumer を載せた shard に
  固有の controller 側処理である。** dispatch が 5 秒以上になった shard は 62 本すべて shard-0 で、
  すべて prewarm consumer を選択に含む。含まない 124 本はすべて 0.06〜0.81 秒であり、
  consumer を含んで 5 秒未満は 0 本。配線も整合する — 観測される collection 終了時刻は
  worker payload の最大値だけから作られ、controller 側の `pytest_collection_finish` を含めない。
  その hook が controller かつ consumer 選択時だけ prewarm を呼ぶ。
- **最遅 shard は shard-0 とは限らない。** 62 走のうち shard-0 が最遅なのは 33 走である。

**この決定に付く限界を、決定の一部として明記する。**

- **標本最小値は「必ず払う下限」ではない。** shard-0 では時刻順 prefix の成分別最小値の和が
  n=5 の 79.6 秒から n=62 の 75.6 秒へ 4.0 秒下がった。母集団の下限がここだとは言えない。
- **「最小値からの超過」から host の寄与は分離できない。** そこには host、repo の状態、時刻、
  テスト結果、走間ノイズがすべて入る。shard-0 の 62 走は 46 種のノードに散り大半が 1 走なので、
  ノード間の差とノード内の走間差を切り分けられない。**「host 差は 1 割」とは言えない。
  言えるのは「走ごとに動く分が残余の 1 割前後で、そこに host 差が含まれる」までである。**
- **dispatch の全量が prewarm だとは言えない。** 観測点は prewarm の開始と終了を採っておらず、
  区間には controller 側の collection 集約・digest 照合・初期割付も入る。shard-0 と
  「consumer を載せている」は file 単位分割のため観測上分離できず、hook の `tryfirst` /
  `trylast` は controller と worker の別 process 間を順序付けない。
- **測定された `teardown` の中身は決まっていない。** memo session の後始末は
  `pytest_unconfigure` から、受入 `report.json` の生成は acceptance plugin の
  `pytest_sessionfinish(trylast=True)` から呼ばれ、**どちらも JUnit plugin が所要を確定した後**
  なので測定区間の外にある。shard-0 の 3.5 秒超過がどの処理かはこのデータでは決まらない。

**理由:**

- D1647 が足した観測 field を読めば、残余の境界値が取れる。「受入形固有か host 差か」は
  走を跨いで動かない部分と動く部分の比で答えるのが、このデータで正当化できる最も強い形である。
- 記録された 95〜207 秒との連続性を確かめた。同じ式・同じ源で 2026-09-04〜05 の走を測り直すと
  shard-0 は 79.0〜207.3 秒になり、**上端は一致する。下端は記録の 95 に対し 79.0 で 16 秒低く、
  母集団の取り方が違う。** これは wall の源が正しいことの証明ではなく、当時と同じ量の系列を
  見ていることの確認である。その後 09-07 で上端 184.9 秒、09-08 で 131.0 秒と裾だけが細り、
  下限 76.8〜82 秒は 5 日間ほぼ不変だった。**当時の値は当時の事実として残す。裾を細らせた
  変更の特定は、当時の走に観測 field が無いためこのデータでは決まらない。**
- wall の源には shard の `junit.xml` root の `time` を使った。受入の receipt
  (`dev-wave-acceptance-receipt/v5`) には wall の欄が無く、同じ系列を測る現存の源はこれだけである。
  **ただし D1620 が定めた区間とは一致しない。** JUnit plugin は `pytest_sessionstart` で起点を
  取り自身の `pytest_sessionfinish` で終端を取るため、左端は collection 開始より早く、右端は
  最後の test teardown 終了より遅い。**右端のずれは本 wave が `teardown` として測った量そのもの**
  であり、D1620 の区間で見た残余は shard-0 で中央 79.8 秒、他 2 shard で 52.9 / 52.6 秒になる。

**却下した選択肢:**

- **timeline に基づく gate や検査を足す** — D1647 が「観測と判定を同じ変更単位にしない」と
  定めた線をそのまま守る。本決定は読み方を固定するだけで、受理集合も成果物の値も変えない。
- **短縮策をここで決める** — 依頼が判定までを範囲としている。
- **host 差の大きさを主張する** — 上記のとおりこのデータでは識別できない。
- **D1369 の記録を訂正する** — D1369 は「21.9 秒の正体は未計測である」と限界を正しく書いた。
  本決定はその限界の解消を追記するのであって、当時の記述は誤りではない。
