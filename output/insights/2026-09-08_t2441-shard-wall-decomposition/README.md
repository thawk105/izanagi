# [T-2441] 受入 shard の wall 内訳を session timeline で分解する

2026-09-08。branch `worktree-dev-wave-t2441-shard-timeline-decomp`。

D1647 で足した観測 field (`report.json` の `session_timeline`) を実際に読み、[T-2273] が
残していた「shard-0 の wall − 最大 worker 占有 = 95〜207 秒の中身」を分解した。
**測っただけで、gate も検査も台帳も足していない。** 解析の probe は規律により repo へ入れず、
本書に式と入力の場所を書き、生データ (`decomposition.json`、187 行) を同梱して再計算できる形にした。

段 3 相当の敵対レンズ 1 本 (read-only) を本書の初稿に当て、**9 件の所見すべてを real と裁定して
本文を書き直した。** レンズの逐語は `consult-sol-verbatim.md`。うち 2 件 (hook の実行順) は
親が独立に code を読んで確かめた。**初稿の結論のうち 2 つは、この過程で撤回または弱めた。**

## 測った量と、その源

| 量 | 源 |
|---|---|
| shard の wall | shard の `junit.xml` root 要素の `time` |
| session の開始時刻 | 同 root の `timestamp` |
| 実行ノード | 同 root の `hostname` |
| collection 終了時刻 | `report.json` の `session_timeline.collection_finished_epoch_s` |
| 各 worker の最初と最後の test 時刻 | 同 `session_timeline.workers.<gwN>` |
| real-repo lock の保持区間 | 同 `real_repo_lock_intervals` |
| worker の実仕事時間 | `report.json` の `worker_occupancy.<gwN>.duration_s` |

入力は `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-N/` の
`report.json` と `junit.xml`。集計対象は `session_timeline` を持つ 187 本のうち、
K=3 で 3 shard 揃った 62 走 = shard 186 本。

### wall の区間はどこからどこまでか

pytest の JUnit plugin は `pytest_sessionstart` で起点を取り、自身の `pytest_sessionfinish` で
所要を確定して書き出す (`_pytest/junitxml.py` の `LogXML.pytest_sessionstart` /
`pytest_sessionfinish`)。したがって **junit の `time` は「session 開始 → JUnit plugin の
sessionfinish」であり、D1620 が定めた「collection 開始から teardown 終了まで」とは一致しない。**
ずれは 2 方向にある。

- **左端**: session 開始は collection 開始よりわずかに早い。この差は観測点が無く測れていない。
- **右端**: 最後の test teardown の終了より遅い。**その差は本書が `teardown` として測っている量
  そのもの**で、shard-0 が 6.4〜7.1 秒、他 2 shard が 2.8〜3.3 秒である。

D1620 の区間で見た残余 (junit の残余から `teardown` を引いたもの) は次のとおり。

| shard | D1620 区間の残余 (中央値 [範囲]) |
|---|---|
| 0 | 79.8 [69.9 - 117.1] |
| 1 | 52.9 [50.5 - 86.7] |
| 2 | 52.6 [51.0 - 83.4] |

**受入の receipt (`dev-wave-acceptance-receipt/v5`) に wall の欄は無い。** D1620 は測定面を
「receipt が記録する最遅 shard の wall」と定めたが、receipt の field を全走査しても該当する key は
存在せず、D1620 自身が「receipt の field 名と K の証拠位置の明記」を別の AI 手番として残している。
現存する唯一の源が junit の `time` であるため、本書はそれを使い、上記のとおり D1620 の区間との
差を量として示した。

## 分解の式

    残余 = wall − 最大 worker 占有
         = collection + dispatch + 実行中の遊び + teardown

- `collection` = collection 終了時刻 − session 開始時刻 (worker の起動と collection を含む)
- `dispatch` = 最初の test 開始時刻 − collection 終了時刻
- `実行中の遊び` = (最後の test 終了 − 最初の test 開始) − 最大 worker 占有
- `teardown` = session 終了時刻 − 最後の test 終了時刻

**この等式は成分の定義から代数的に成立する恒等式であって、観測の完全性を確かめたものではない。**
`S, C, F, L, E, B` を session 開始・collection 終了・最初の test 開始・最後の test 終了・
session 終了・最大 worker 占有とすると、右辺は `(C−S)+(F−C)+((L−F)−B)+(E−L) = E−S−B` で
左辺そのものである。実測が持つ情報は**境界の値そのもの**と、**下に書く「実行中の遊びが
ほぼゼロ」という非自明な事実**であって、閉じること自体ではない。初稿はこれを
「残余に未分解の区間は残っていない」の証拠として提示していた。撤回する。

## 内訳 (2026-09-08、K=3 の 62 走)

中央値 [最小 − 最大]、秒。

| 成分 | shard-0 (n=62) | shard-1 (n=62) | shard-2 (n=62) |
|---|---|---|---|
| collection | 52.1 [50.9 - 84.0] | 52.7 [50.4 - 84.2] | 52.4 [50.9 - 82.8] |
| dispatch | 26.3 [18.4 - 51.9] | 0.1 [0.1 - 0.8] | 0.1 [0.1 - 0.8] |
| 実行中の遊び | 0.0 [0.0 - 1.9] | 0.0 [0.0 - 2.1] | 0.0 [0.0 - 0.1] |
| teardown | 6.6 [6.4 - 7.1] | 2.8 [2.8 - 3.1] | 3.1 [2.8 - 3.3] |
| **残余** | **86.4 [76.8 - 123.8]** | **55.8 [53.3 - 89.7]** | **55.6 [54.0 - 86.7]** |
| 最大 worker 占有 | 231.1 [168.3 - 701.4] | 236.9 [70.6 - 780.6] | 225.6 [188.4 - 672.3] |
| wall | 320.0 [254.3 - 799.9] | 295.7 [125.7 - 843.2] | 285.6 [243.7 - 736.8] |

**最遅 shard は shard-0 とは限らない。** 62 走のうち shard-0 が最遅なのは 33 走、shard-1 が
17 走、shard-2 が 12 走である。最遅 shard の残余は中央値 82.1 [53.3 - 113.4] 秒。

**実行中の遊びはほぼゼロである。** 186 本の中央値 0.01 秒、最大 2.13 秒、1 秒を超えたのは
9 本だけ。これは恒等式ではなく実測で、**いちばん働いた worker は自分の担当区間をほぼ隙間なく
働いている**ことを示す。worker が互いを待って wall だけが伸びる区間は現行コードに残っていない。

## 判定 — 走ごとに動く分は残余の 1 割前後で、残りは shard の構成で決まる

「受入形固有か host 差か」を、**走を跨いで動かない部分と動く部分**に分けて答える。

各成分の観測最小値の和を「この標本で観測された下限」とすると、

| shard | 観測下限の和 | 内訳 | 残余中央値 | 割合 |
|---|---|---|---|---|
| 0 | 75.6 秒 | collection 50.9 + dispatch 18.4 + 遊び 0.0 + teardown 6.4 | 86.4 | 88% |
| 1 | 53.2 秒 | collection 50.4 + dispatch 0.1 + 遊び 0.0 + teardown 2.8 | 55.8 | 95% |
| 2 | 53.7 秒 | collection 50.9 + dispatch 0.1 + 遊び 0.0 + teardown 2.8 | 55.6 | 97% |

下限からの超過は中央値で shard-0 が 10.7 秒、shard-1 が 2.6 秒、shard-2 が 1.9 秒である。
**すなわち残余の 88〜97% は、どの計算ノードで走っても払っている。**

### この読み方に付く 3 つの限界

**(1) 標本最小値は「必ず払う下限」ではない。** 標本を増やすと下がりうる。実際 shard-0 では
時刻順の prefix で次のように下がった。

| shard | n=5 | n=10 | n=20 | n=40 | n=62 |
|---|---|---|---|---|---|
| 0 (成分別最小値の和) | 79.6 | 77.1 | 77.1 | 75.7 | 75.6 |
| 1 | 53.2 | 53.2 | 53.2 | 53.2 | 53.2 |
| 2 | 54.0 | 54.0 | 53.7 | 53.7 | 53.7 |

62 走で 4.0 秒下がった。**初稿の「下限は 76.8 秒で動かない」は誤りである。** 下がり方は
緩やかで、この標本の範囲では 75 秒台で止まっているが、母集団の下限がここだとは言えない。

**(2) 「下限からの超過」は host 差ではない。** その中には host、repo の状態、時刻、
テストの結果、走間ノイズがすべて入る。**本 wave のデータで host の寄与を分離することはできない。**
shard-0 の 62 走は 46 種の計算ノードに散っており、大半のノードは 1 走しかない。同じノードの
反復が無いので、ノード間の差とノード内の走間差を切り分けられない。**初稿の「host 差は残余の
1 割前後」は言い過ぎで、正しくは「走ごとに動く分が残余の 1 割前後で、そこに host 差が含まれる」
である。**

**(3) 成分別最小値の和は、実在する 1 走の固定部分ではない。** 別々の走で得た成分ごとの最小値を
足したものである。実際の残余の最小値は shard-0 で 76.8 秒 (下限の和 75.6 より 1.2 秒大きい)。

### 動く分がどの成分に出るか

残余が上位 25% の走について、各成分の平均から成分ごとの中央値を引くと次のようになる。
(基準を明示する — 残余の平均から残余の中央値を引いた値は shard-0 で +22.4 秒であり、
成分ごとに引いて足した +23.7 秒とは基準が違う。)

| shard | 成分超過の合計 | collection | dispatch | 遊び | teardown | collection の割合 |
|---|---|---|---|---|---|---|
| 0 | +23.7 | +16.6 | +6.7 | +0.3 | +0.1 | 70% |
| 1 | +19.0 | +18.4 | +0.4 | +0.2 | +0.1 | 97% |
| 2 | +17.8 | +17.3 | +0.5 | −0.0 | +0.0 | 97% |

**走ごとに動く分は主に collection に出る。** shard-0 では dispatch にも 28% 出る。
初稿は「ほぼ全量 collection」と書いたが、shard-0 では 7 割である。

## shard-0 だけに出る dispatch 26.3 秒

`dispatch` は 3 shard のうち shard-0 だけで 2 桁秒になる。対応は完全である。

- dispatch ≥ 5 秒の shard は 62 本、**すべて shard-0**、範囲 18.4〜51.9 秒。
- dispatch < 5 秒の shard は 124 本、**すべて shard-1 か shard-2**、範囲 0.06〜0.81 秒。
- prewarm consumer (`RECEIPT_MEMO_CONSUMER_NODES` 34 関数 /
  `ORACLE_ENVIRONMENT_CONSUMER_NODES` 26 関数) を選択に含む shard は 62 本ですべて
  dispatch ≥ 18.4 秒、含まない 124 本はすべて 5 秒未満。**consumer を載せて 5 秒未満は 0 本。**

配線もこれと整合する。`tools/acceptance_shards.py` の `_controller_state` は xdist 経路で
`collection_finished_epoch_s` を **worker payload の最大値だけ**から作り、controller 自身の
`pytest_collection_finish` を含めない。一方 `orchestrator/tests/conftest.py` の
`pytest_collection_finish` は `workerinput` を持たない controller のときだけ
`_prewarm_receipt_memo` と `_prewarm_oracle_environment_memo` を呼び、どちらも
consumer が選択に含まれるときだけ実体を走らせる。

**言えるのはここまでである。** 次の 3 つは言えない。

1. **26.3 秒の全量が prewarm だとは言えない。** 観測点は prewarm の開始と終了を採っていない。
   この区間には controller 側の collection 集約・digest 照合・scheduler の初期割付も入る。
2. **「shard-0 だから」と「consumer を載せているから」は分離できない。** 分割が file 単位なので
   consumer 群は毎回 shard-0 に載る。分離には consumer を別 shard へ寄せた反実仮想の走行が要る。
   **本 wave は測るだけなので走らせていない。**
3. **hook の `tryfirst` / `trylast` は controller と worker の別 process 間を順序付けない。**
   controller の prewarm 全体が worker の最大 collection 時刻より後に始まる保証は、
   静的な code だけからは出ない。

補助証拠として、shard-0 の dispatch と各量の相関を測った。

| 相手 | 相関 |
|---|---|
| 最大 worker 占有 | 0.23 |
| collection | −0.02 |
| 選択 node 数 | 0.48 |
| session 開始時刻 | 0.32 |

その走の仕事量にはほとんど連動せず、repo の規模を表す量に緩く連動する。ただし選択 node 数と
時刻は互いに強く相関しており (レンズの再計算で 0.73)、両者を同時に入れた線形回帰の決定係数は
0.23 でしかない。**dispatch のばらつきの 8 割近くは、この 2 つでは説明できない。**

## teardown の中身は分かっていない

shard-0 の teardown は 6.6 秒、他 2 shard は 2.8 / 3.1 秒である。**初稿はこの差を
「prewarm した memo session の後始末」と説明したが、それは誤りなので撤回する。**

- `_finish_memo_sessions` は `pytest_sessionfinish` ではなく `pytest_unconfigure` から呼ばれる
  (`orchestrator/tests/conftest.py`)。`pytest_unconfigure` は JUnit plugin の `sessionfinish` より
  **後**に走るので、測っている wall の外にある。
- 受入の `report.json` の組み立てと書き出しも、acceptance plugin の
  `pytest_sessionfinish(trylast=True)` の中で行われる (`tools/acceptance_shards.py`)。
  `trylast` は同 hook の中で最後に呼ばれることを意味するので、JUnit plugin が所要を確定した
  **後**である。**したがって report 生成も測っている wall の外にある。**

つまり測定された `teardown` (2.8〜7.1 秒) は、最後の test の終了から JUnit plugin の
sessionfinish までの区間であり、terminal summary の出力、xdist worker の停止、
JUnit plugin より先に呼ばれる他の sessionfinish hook が入る。**shard-0 の 3.5 秒超過が
このうちどれかは、本 wave のデータでは決まらない。**

なお `report.json` の大きさは 3 shard とも 6.0 MB (6.02 / 6.08 / 6.04) でほぼ同じであり、
`junit.xml` も 1.15〜1.20 MB でほぼ同じである (値は `decomposition.json` の
`report_bytes` / `junit_bytes` にある)。書き出す量に shard 間の差は無い。

## 記録された 95〜207 秒との関係

[T-2273] が書いた「shard-0 の wall − 最大占有 95〜207 秒」は 2026-09-04〜05 の走行から出た値で、
当時 `session_timeline` は無かった。同じ式・同じ wall の源で当時の走を測り直すと次のようになる。

| 日 | shard-0 の残余 (n) | shard-1 | shard-2 |
|---|---|---|---|
| 09-03 | 82.2〜246.9 中央 93.6 (42) | 58.3〜215.8 中央 61.5 | 56.4〜83.4 中央 60.6 |
| 09-04 | 79.7〜207.3 中央 109.3 (34) | 56.9〜79.4 中央 59.3 | 56.6〜76.3 中央 58.2 |
| 09-05 | 79.0〜206.5 中央 94.5 (28) | 57.0〜67.9 中央 58.5 | 57.6〜71.7 中央 58.4 |
| 09-07 | 80.1〜184.9 中央 91.3 (68) | 52.5〜96.1 中央 59.1 | 52.5〜96.1 中央 58.9 |
| 09-08 | 76.8〜131.0 中央 86.8 (103) | 52.9〜89.7 中央 55.3 | 53.4〜86.7 中央 55.5 |

**上端は一致する** (207.3 / 206.5 対 207)。**下端は一致しない** — 記録は 95、再計算は 79.0 で
16 秒低い。母集団の取り方が違うためと思われる。本書の走査は artifact root にある K=3 の走を
すべて含み、canonical 起動に限っていない。当時の値がどの集合から取られたかは記録から追えない。

**この再計算は wall の源が正しいことの証明ではない。** 同じ源に同じ式を当てれば同じ値が出るのは
当然であり、両方が同じ不適切な区間を測っている可能性を排除しない。示せたのは
「上端が一致するので、当時と本書は同じ量の系列を見ている」までである。

その上で、**下限 (76.8〜82 秒) は 5 日間ほぼ不変のまま、裾だけが細った。** 上端は
207.3 → 206.5 → 184.9 → 131.0、p75 は 143.5 → 152.1 → 103.8 → 98.5 と下がった。
何が細らせたかは、当時の走に観測 field が無いためこのデータでは決まらない。

規律 7 に従い、当時の 95〜207 秒は当時の事実として残す。現行分布と違うことは、当時の測定を
無効にしない。

## この判定が [T-2273] に対して意味すること

5 分 (300 秒) 目標に対し、**残余のうち走を跨いで動かない部分が shard-0 で 75.6 秒、
他 2 shard で 53 秒台ある。** その内訳は collection 約 51 秒 (3 shard 共通)、
shard-0 の dispatch 約 18 秒、teardown 約 3〜6 秒である。

したがって「その日たまたま遅いノードに当たった」で説明できるのは残余の 1 割前後で、
残り 9 割は shard の構成と走らせ方で決まっている。短縮の候補は次の 3 つに絞られる。

- 3 shard 共通の collection 約 51 秒
- shard-0 の dispatch 約 18〜26 秒 (交絡があり、consumer を別 shard へ寄せた走行で分離が要る)
- 最大 worker 占有 (中央値 231 秒。D1369 が下界を `max(最長単体, 総仕事量 ÷ worker 数)` と定めた層)

**本 wave は判定までで、短縮策は実装も裁定もしていない。**

## 生データ

`decomposition.json` に 187 本すべての行を置いた。1 行が 1 shard で、上の式の各項、host、
session、選択 node 数、`report.json` と `junit.xml` の byte 数、lock 保持 (worker 合計 /
和集合 / 最大 worker) を持つ。本書の表はすべてこの file から再計算できる。
`consult-sol-verbatim.md` は敵対レンズの逐語である。
