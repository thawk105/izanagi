# 受入 collection の内訳 — 費用の 4 分の 1 が 1 file に集まっており、conftest の hook は費用ではない

authority: none
default_effect: no-state-change

T-2097 の残差分解 (`output/insights/2026-09-02_t2097-residual-breakdown/`) が
「残差 58.16 秒の 95% は A、A の大半は 48 worker が各自で全テストを collection する時間」まで
測り、**「worker 内部の import・conftest・fixture 収集・deselect の別は測っていない」**と明記した。
本 wave はその内側を測った記録である。**実装は 1 行も入れていない。**
状態の正本は worklog、採用済み判断は decisions とする。

一次資料は同 directory の `collect-profile.txt` (cProfile の生出力)、
`collect-per-file.json` (file 別 collector 所要)、`verbatim/s2-plan.md` (段 2 プラン全文)。
解析 script は repo 外の job dir に置いた。probe を repo へ入れていない。

## 測った環境と、その限界

**ログインノード pegasus02、単一 process、loadavg 42、`orchestrator/tests` 全 20144 件。**
計算ノード 48 並列ではない。T-2097 が測った計算ノードの collection 約 51.7 秒に対し、
ここでの単一 process warm collection は 12.06〜14.36 秒である。**約 3.6 倍の開きがあり、
その原因は本 wave では分解していない。** 以下の比率を計算ノードの wall へそのまま掛けてはいけない。

同一 worktree で連続 4 回測った。

| 走 | 状態 | collection 所要 |
|---|---|---|
| 1 | `__pycache__` が空 | 54.83 秒 (user CPU 47.41、87% が CPU) |
| 2 | warm + cProfile | 21.28 秒 |
| 3 | warm | 14.36 秒 |
| 4 | warm | 12.06 秒 |

**走間のばらつきが大きい (12.06〜14.36 秒)。** loadavg 42 のログインノードで測ったためである。

## 結論 1 — 費用の 4 分の 1 が 1 file に集まっている

warm 14.36 秒の走で、319 file の collector 所要を個別に測った (`collect-per-file.json`)。

| 量 | 値 |
|---|---|
| 全 file collector の合計 | 12.54 秒 (collection 全体の 87%) |
| 最重量 1 file | **3.44 秒 = file collector 合計の 27.4%** |
| 上位 10 file | 5.63 秒 = 44.9% |
| file 数 | 319 |

最重量は `orchestrator/tests/test_p3_exploration_namespace.py` である。この module は
`:70` の module 直下 setcomp で、187 個の source を読んで `ast.walk` で全走査する。
cProfile ではこの 1 箇所が 2.91 秒だった (`collect-profile.txt`)。

**この費用は 48 worker × 3 shard + login の collect-only、合わせて 145 回払われている。**

## 結論 2 — conftest の collection hook は費用ではない

collection を変える案を考えるとき `orchestrator/tests/conftest.py` の hook が疑われるが、
実測ではほぼゼロである。

| hook | 所要 |
|---|---|
| `pytest_collection_modifyitems` (全実装の合計、20144 item を走査) | 0.375 秒 |
| `pytest_collection_finish` (controller prewarm を含む) | 0.388 秒 |

**合わせて 0.76 秒で、collection 全体の 5% 未満である。** growth hold / flaky hold の
完全性検査も、shard の deselect も、費用ではない。**ここを触っても速くならない。**

## 結論 3 — 費用は import と item 構築で、cache の書き換えではない

cProfile の 21.28 秒の走の内訳 (profiler の負荷を含む値であり、比率だけを見る)。

| 項目 | 秒 |
|---|---|
| `perform_collect` 全体 | 21.05 |
| test module の import (`import_path`) | 12.97 |
| うち assert 書き換え (`compile` 2.19 + `ast.walk` 2.90) | 約 5.1 |
| `posix.stat` 45764 回 | 1.61 |
| `io.open` 1237 回 + `open_code` 909 回 + close 1770 回 | 約 2.9 |

**`__pycache__` を空にすると 54.83 秒、満たすと 12.06 秒**という差 (約 43 秒) は
本 wave でも再現した。ただし D918 が既に測ったとおり、**計算ノードの子に渡る
`PYTHONDONTWRITEBYTECODE=1` は書き込みだけを止め、読み出しは効く**ので、
実運用の受入はこの cold 側に入らない。**cold cache は本番の説明にならない。**

## 結論 4 — report 外費用は仕事量に依らず、universe 件数で動く

`report.json` の `worker_occupancy` と job stdout から
`report 外費用 = pytest wall − 最大 worker occupancy` を全走で求めた
(3 shard 構成・worker 40 本以上、n=1221)。

**同一 session 内の対照 (n=401 session)。** 同じ session の 3 shard は universe が同一で、
仕事量だけが違う。

| 量 | 中央値 | p90 |
|---|---|---|
| shard-1 と shard-2 の仕事量比 (大 / 小) | 1.38 | 2.32 |
| 同 2 shard の report 外費用の差 | 1.0 秒 | 7.3 秒 |
| 同 相対差 | 1.7% | 11.9% |

仕事量比が小さい半分でも大きい半分でも差は 0.9 秒と 1.1 秒で、**仕事量比と一緒に広がらない。**

**universe 件数との関係 (shard 別)。**

| shard | n | 傾き (秒 / 1000 件) | r | 切片 (秒) | report 外費用 中央値 |
|---|---|---|---|---|---|
| shard-0 | 409 | 8.96 | 0.196 | -78.9 | 81.2 |
| shard-1 | 405 | 4.68 | 0.548 | -30.3 | 56.5 |
| shard-2 | 407 | 4.03 | 0.485 | -18.3 | 56.7 |

**時期交絡は小さい。** universe を 3 帯に切り、各帯の中で前半と後半を比べると
差は +1.2 / +1.6 / +2.0 秒だが、帯をまたぐと 51.7 秒から 58.6 秒へ約 7 秒動く。

**切片はすべて負なので比例ではない。** universe の観測範囲は 17455〜20166 で幅は 15.5% しかなく、
**この範囲外へ外挿してはいけない。**

## 結論 5 — D747 が「未証明」と書いた穴の向きは支持されたが、大きさは範囲内でしか言えない

D747 は「所要 0.01 秒未満の 7750 件 (54%) を消しても 48 並列 wall は 0.31 秒しか縮まない」と
見積もったうえで、**「削除は collection 処理も減らす。これらは 15.1 秒に含まれておらず、
安いテストを減らしても wall に効かないは未証明」**と自ら穴を明記していた。

観測範囲内での値は **1000 件あたり各 shard 4.0〜4.7 秒**である。
D747 の実行 work 側の値 (7750 件で 0.31 秒 = 0.04 秒 / 1000 件) と比べると
**1 件あたりおよそ 100 倍**である。

**ただし「7750 件消せば約 46 秒」という外挿は成立しない。** 切片が負であり、
観測範囲は 15.5% しかない。本 wave は一度この外挿を書いてから撤回した。

**そして結論は「テストを消せ」ではない。** D747 が削除を却下した理由 (検出力を失う、規律 2) は
そのまま有効である。**費用が collection にあるなら、1 件も消さずに collection 側を安くできる。**

## 結論 6 — 費用の伸びは件数だけでは説明できない (差を数で置いた)

T-2097 は D711 (2026-08-23) の同型の値 12.86 秒 (14479 node) と今回の 55.73 秒 (19572 node) を
並べ、**「node 数だけでは説明できない。本 wave はこの差の原因を分解していない」**と書いた。

本 wave の傾き (各 shard 4.0〜4.7 秒 / 1000 件) を当てると、
node が 14479 から 19572 へ 5093 件増えたことで説明できるのは **約 24 秒**である。
実際の増加は **約 43 秒**なので、**約 19 秒が件数では説明できない。**

**この 19 秒の正体は本 wave でも分解していない。** 2 つの値は日付・機体・checkout が異なり、
同一条件の対ではない。**「超線形である」と断定できるだけの対照は取っていない。**

## 実装しない理由

**Codex の使用枠が尽きた** (2026-09-02 23:48、復帰は 2026-09-07 23:06)。
dev-wave の凍結境界により実装面は Codex の実装子だけが書けるので、本 wave は実装へ進まない。
従量経路への切り替えは行わない (CLAUDE.md 鉄則)。

段 3 の敵対相談 2 本も同じ枠切れで出力 0 byte で終わった。
**したがって本書の内容は独立した敵対検査を受けていない。** 本 wave 中に親自身が
3 件の誤りを見つけて訂正したが (下記)、それは独立検査の代わりにならない。

## 親自身の誤りと訂正

1. **shard-0 固有分を「約 37 秒」と書いた。** shard-0 の中央値 (n=15) から
   shard-1/2 の中央値 (別の n=15) を引いた、**異なる集合の中央値どうしの差**だった。
   同一 session 内で対にすると中央値 **23.5 秒** (p10 16.5、p90 57.0、n=401) で、
   T-2097 の 21.9 秒と整合する。
2. **「7750 件消せば約 46 秒」と外挿した。** 切片が負で観測範囲が 15.5% しかないので無効。撤回した。
3. **report 外費用 97.4 秒を「テストが 1 件も動いていない時間」と書いた。**
   `worker_occupancy` は TestReport duration の和にすぎず、その外側には lock 待ち・
   worker idle・scheduler gap も入る。段 2 プランがこれを指摘した。
4. **段 1 の閉包で D918 と D634 と T-2097 の残差分解を引けていなかった。**
   いずれも同じ対象を既に測っており、うち T-2097 は本 wave 開始の数時間前に land していた。
   `git grep` を「受入」「collection」で引いたが、これらは `output/insights/` の
   別名の artifact に入っていた。

## 次の一手の候補 (ユーザー裁定へ返す)

いずれも受理集合・node id・skip 集合を変えない。**どれも実測で確認していない。**

1. **`test_p3_exploration_namespace.py` の module 直下 AST 全走査に字句 prefilter を置く。**
   段 2 プランの候補 C1。全 187 file の `read_text()` と `ast.parse()` は残し、
   source text に対象 identifier が無い file では `ast.walk` を省く。該当は 13 file。
   AST に identifier があるなら source text にも必ずあるので false negative は無い。
   単一 process で 3.44 秒のうち約 2.7 秒が上限。**計算ノードの wall への効果は未測定。**
2. **duration ledger を workerinput で圧縮する。** 段 2 プランの候補 C3。
   現物 19519 entry・2513728 bytes を 48 worker へ送っており shard あたり約 118 MB。
   圧縮すると約 19 MB。効果は worker bootstrap 側で 1〜5 秒と見積もられているが未測定。
3. **controller prewarm を背景化して worker の collection と重ねる。**
   段 2 プランの候補。上限は 22 秒程度だが、通知のばらつきが小さければ 0 秒。
   `conftest.py` は T-2145 と編集面が衝突しているので、同 wave の決着まで着手できない。
4. **計算ノードの collection 51.7 秒と、ログインノード単一 process の 12〜14 秒の
   約 3.6 倍の開きを分解する。** 48 並列の contention が CPU なのか、Lustre の
   metadata なのか、memory 帯域なのかで、上の 1〜3 の効果量が変わる。

D634 が閉じたのは controller-only collection と collection manifest 共有である。
**上の 1〜4 はいずれもそれに当たらない** — 1 回の collection を安くする話であり、
worker が各自で全 universe を collect するという不変条件 (`tools/acceptance_shards.py:913-953`
で 48 worker の digest 一致を要求) を保つ。
