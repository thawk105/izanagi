# 受入 1 走の「テストが始まるまで」の内訳 — どこまで決まり、どこが削れないか (2026-09-16)

wave `dev-wave-t2617-acceptance-collection-cost`。依頼は [T-2617]
「受入 1 走の collection 約 93 秒と、収集終了から最初のテスト開始までの 25.6 秒の内訳を確定し、
短縮の可否を判定する。絞り込み以外の手があるかを先に調べ、無ければその結論を insight に残す」。

## 結論 (最初に読む)

**2 区間のうち、片方は内訳が決まり、片方は決まらなかった。そして「絞り込み以外の手」は
存在するが、本区間に二桁秒で効くものは 1 本だけで、それは既に [T-2616] が持っている。**

| 区間 | 実測 (2026-09-16、28 走) | 内訳 | 短縮の手 |
|---|---|---|---|
| session 開始 → collection 終了 (`pre`) | **55.4〜59.1 秒** | **主因は 48 worker が同じ全 collection を並列に払うこと。** 分割 plugin の per-item 費用は CPU 1.74 秒しかなく主因ではない (対照実験で確定) | **無い。** 現行の禁止に触れずに二桁秒を削る手は見つからなかった |
| collection 終了 → 最初のテスト開始 (`disp`) | **20.7〜41.1 秒** (shard-0 だけ。他 2 shard は 0.1 秒) | barrier 31.32 秒のうち 31.32 秒が `_prewarm_receipt_memo`。**ただし barrier と `disp` は同じ量ではない** (差 2.88 秒) | **[T-2616] が所有済み。** 本 wave は新しい手を足さない |

**依頼が挙げた「93 秒」は現行の値ではない。** 93 秒は 2026-09-14 の 1 走 (`531cc7a5`) の値で、
しかも直接観測ではなく `wall − 開始待ち − 実行窓 − 尾` の残差だった。
本 wave が 28 走を測り直すと **55.4〜59.1 秒**で、33 台の別ノード・wall 296〜604 秒にまたがって
**幅 3.7 秒しか動かない。**

### 5 分に入るか

入らない。session `8259cf7f` で両区間を全部ゼロにする反実仮想を置くと、

```
shard-0  307.1 − 56.2 − 28.4 = 222.5 秒
shard-1  223.1 − 56.3 −  0.1 = 166.7 秒
shard-2  211.8 − 56.5 −  0.1 = 155.2 秒
```

**最遅は 222.5 秒**になり、この走なら 300 秒に入る。しかし同じ日の最遅 wall は 604.5 秒まであり、
そこから 84.7 秒を引いても 519.8 秒である。**この 2 区間は 5 分超えの主因ではない。**
主因は実行窓 (最長単体テスト 208〜214 秒) と混雑である。

---

## 1. 何を測ったか

一次資料は `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-<n>/` の
`report.json` (`session_timeline`) と `junit.xml` の `<testsuite name="pytest">` 属性。
**repo の外にある走行成果物なので、古い走行が消えると再現しない。**

- `pre` = `collection_finished_epoch_s − junit の timestamp`
- `disp` = `min(workers[].first_test_started_epoch_s) − collection_finished_epoch_s`

### 1.1 同一 session の 3 shard (`8259cf7fff14f3387347ab25a65a379c`)

| shard | wall | host | tests | worker | `pre` | `disp` | 実行窓 | 尾 |
|---|---|---|---|---|---|---|---|---|
| 0 | 307.1 | bnode030 | 8564 | 48 | 56.2 | 28.4 | 215.2 | 7.2 |
| 1 | 223.1 | bnode026 | 7833 | 48 | 56.3 | 0.1 | 163.5 | 3.3 |
| 2 | 211.8 | bnode040 | 7623 | 48 | 56.5 | 0.1 | 152.2 | 3.0 |

**`pre` は 3 台の別ノードで 56.2 / 56.3 / 56.5。ばらつき 0.3 秒。**

### 1.2 直近 28 走の shard-0 (逐語)

```
10:03:21 pre=56.2 disp=28.4      08:56:57 pre=56.7 disp=27.3
10:01:00 pre=57   disp=30.1      08:55:58 pre=55.6 disp=21.2
09:58:06 pre=55.7 disp=27.7      08:48:27 pre=56.3 disp=25.8
09:53:47 pre=55.9 disp=27.7      08:33:17 pre=55.4 disp=35.1
09:52:14 pre=55.7 disp=25.5      08:37:24 pre=55.7 disp=25.9
09:38:07 pre=56.5 disp=31        08:32:59 pre=56.5 disp=30.6
09:37:53 pre=55.8 disp=20.7      08:31:37 pre=55.6 disp=29.1
09:32:51 pre=56.8 disp=31.3      08:22:48 pre=56.4 disp=30.1
09:29:47 pre=56.7 disp=34.4      08:21:50 pre=56.5 disp=26.2
09:19:24 pre=56.7 disp=24.8      08:05:51 pre=56.1 disp=41.1
09:17:44 pre=56.6 disp=24        08:09:10 pre=55.9 disp=28.1
09:15:04 pre=55.4 disp=28.9      08:13:47 pre=55.4 disp=34
09:01:15 pre=56.5 disp=26.2      08:05:43 pre=57   disp=26.2
09:05:58 pre=55.9 disp=29.5      07:57:23 pre=59.1 disp=35.1
```

host は bnode002 / 003 / 006 / 019 / 021 / 022 / 025 / 028 / 029 / 030 / 031 / 032 / 033 / 034 /
037 / 041 / 074 / 075 / 076 / 077 / 080 / 082 / 095 / 098 / 099 / 101 / 102 / 116 / 118 / 119 /
120 / 125 / 131 に散る。同じ 28 走の wall は 296.2〜604.5 秒。

**この標本は 2026-09-16 の 1 日ぶんで、同じ日の checkout 群を共有している。**
「今後もこの値である」とは言えない — 言えるのは「この 28 走ではこうだった」までである。

---

## 2. `disp` の内訳 — 決まった部分と決まらない部分

現行コードに計測行が残っている (2026-09-14 の wave が入れたもの)。session `8259cf7f` の
shard-0 の job stderr の逐語:

```
IZANAGI_MEMO_PREWARM_V1 {"barrier_s":31.321978736006713,"hook":"xdist_node_collection_finished",
"oracle_environment_memo_s":0.1312759759966866,"receipt_memo_s":31.320316853001714}
```

**決まったこと:** barrier の中では `_prewarm_receipt_memo` が
`_prewarm_oracle_environment_memo` の 238 倍である (31.320317 対 0.131276)。
実体は `orchestrator/tests/conftest.py:876`。shard-1 / shard-2 の `disp` が 0.1 秒なのは、
この prewarm の consumer が選択に入らないためである。

**決まらなかったこと 2 点。どちらも段 3 の相談が親の誤りとして指摘した。**

1. **barrier (31.32 秒) と `disp` (28.44 秒) は同じ量ではない。差は 2.88 秒。**
   barrier は worker ごとの collection 完了通知 hook から起動する
   (`conftest.py:2359`, `:2384`, `:2422`) 一方、報告される collection 終端は
   全 worker の時刻の**最大値**である (`tools/acceptance_shards.py:1075-1092`)。
   先着 worker の通知後に始まった prewarm と、残る worker の collection は重なる。
   **したがって「`disp` の 99.995% が receipt prewarm」とは言えない。**
   言えるのは「barrier の中では receipt が支配的」までである。
2. **計測区間 (`conftest.py:896` 起点) は production の実 repo 走査だけではない。**
   module 取得 (897)、実 repo lock の取得待ち (899)、memo 側の HEAD 取得・cache path 構築・
   別の `flock`・古い cache の掃除・保存 (`real_repo_receipt_memo.py`) を含む。
   **「lustre 走査を速くすればこの 31 秒が消える」は未証明である。**

---

## 3. `pre` の内訳 — 対照実験で主因を 1 つ消した

login node で、同一 worktree・同一 command
`python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` を条件を変えて走らせた。
`/usr/bin/time` の逐語。

### 3.1 bytecode cache の有無

| # | 条件 | load (1 分) | wall | user CPU | sys CPU | %CPU | pytest 報告 |
|---|---|---|---|---|---|---|---|
| 1 | `__pycache__` 不在・page cache も冷 | 44.59 | 129.2 s | 52.99 s | 2.71 s | 43% | 125.37 s |
| 2 | 1 の直後 (`__pycache__` 在) | 約 50 | 43.0 s | 17.40 s | 1.57 s | 44% | — |
| 3 | 2 の直後 (`__pycache__` 在) | 96.38 | 20.77 s | 16.54 s | 1.68 s | 87% | 18.23 s |
| 4 | `__pycache__` を消し page cache は温 | 93.72 | 74.46 s | 56.37 s | 3.23 s | 80% | 71.52 s |

いずれも `23970 tests collected`。
**bytecode 再コンパイルは 1 process あたり user CPU で約 40 秒 (56.37 − 16.54)。**

**ただしこれは受入の regime ではない、と親は判定したが、その判定は弱い。**
`.gitignore:2` が `__pycache__/` を無視するので cache は checkout に残り、
稼働中の 5 つの wave worktree の `orchestrator/tests/__pycache__` の entry 数は
380 / 380 / 381 / 378 / 380 (source の `.py` は 380 file、版は `cpython-310`)、主 checkout は 677 だった。
**しかし entry 数は有効性の証明ではない。** 段 3 の両レンズが次を指摘した。

- 計算ノードの dispatch は `PYTHONDONTWRITEBYTECODE` を既定で `"1"` にする
  (`tools/pegasus/dispatch_compute.py:1633`、`tools/acceptance_launcher.py:70-71`)。
  既存 `.pyc` の**読み出し**は止まらないが、**欠落・陳腐化した cache は受入走行では更新されない。**
- したがって新規 worktree の初回受入、python 版の更新、source の一斉変更のあとは
  冷い状態が持続しうる。**該当 28 走の cache 有効性は確認していない。**

### 3.2 分割 plugin の per-item 費用 — 主因ではなかった

受入だけが載せる `-p tools.acceptance_shards` の費用を、同じ負荷で連続 2 走して測った
(load 1 分値 7.77)。

| 走 | 構成 | wall | user CPU | sys CPU | %CPU | pytest 報告 | 収集 |
|---|---|---|---|---|---|---|---|
| 対照 | plugin なし | 16.19 s | 15.82 s | 1.37 s | 106% | 13.62 s | 23970 |
| 処理 | plugin あり (shard 0/3) | 16.87 s | 17.56 s | 3.09 s | 122% | 14.74 s | 9124/23970 (14846 deselect) |

**差は user CPU で +1.74 秒、collection 報告で +1.12 秒。**

この 1.74 秒の中に、段 3 が数え直した全部が入っている —
`_canonical_item` が item ごとに **2 回**呼ばれること
(`tools/acceptance_shards.py:901` の `records_from_items` と `:906` の `by_identity` 構築)、
その各回の `Path(item.path).resolve()` (`:762`)、marker 列挙 (`:769`)、
`allocate` (`:381`)、2 つの digest (`:917` と `:919`、**入力が別なので重複計算ではない**)。

**23970 item × 2 回 = 47,940 回の正規化が、1 worker あたり 1.74 秒。**
48 worker ぶんを足しても 83.5 CPU 秒で、48 core のノードでは wall 2 秒程度にしかならない。
**分割 plugin は `pre` の主因ではない。**

### 3.3 残る約 38 秒は 48 重の並列実行そのもの

- 単独 process の温い全 collection: **13.62〜18.23 秒** (user CPU 15.82〜16.54 秒)。
- 計算ノードの受入: 48 worker で `pre` = **約 56 秒**。
- 計算ノードは **48 physical core、HyperThreading 無効、1 CPU 構成**
  (`docs/pegasus-runbook.md` §1、gen_S は CPU 48/48 固定)。
  **worker 1 本に core 1 本**であり、48 本の全 collection が同時に走る。
- 理想的に並列なら wall は単独と同じ約 16 秒のはずだが、実測は 56 秒で **3.5 倍**である。
  差は memory 帯域 (1 worker あたり常駐 330 MB × 48 = 約 16 GB)、
  lustre の metadata 応答、および controller が 48 worker ぶんの nodeid を受け取って
  照合する直列処理に入る。**この 3 者の配分は決まっていない。**

**決められなかった理由を明記する。**

- `-n 48` を login で再現しようとしたが、`--collect-only` では xdist が働かず
  `IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}` になり
  14.75 秒 / 105%CPU で終わった。**48 worker 並列 collection の login 再現はできていない。**
- 配分を決めるには、計算ノードで同条件の走行に診断 probe を載せる必要がある。
  D1729 が受入 report への観測 field 追加を見送っているため、probe は schema の外に置くことになる。
  **本 wave の scope (内訳確定のみ、追加実装は scope 外) を超えるので実施していない。**
- **login の対照と計算ノードの観測は同じ commit ではない。** 対照は main `262c2993e`、
  観測した session の `observed_universe` は 24,020 件で、対照の 23,970 件と 50 件 (0.2%) 違う。
  差は走行元 wave の tip の違いによる。**したがって 56 − 18 = 38 という引き算は
  同条件の差分ではなく、成分へ配分してはいけない。**

---

## 4. 短縮の手 — 何が使えて何が使えないか

段 3 の 2 レンズ (費用と実効性 / 正しさ境界と既裁定の射程) が独立に列挙し、本節はその合流である。
逐語は `verbatim/` にある。

| 手 | 効果 | 触れる防壁 | 判定 |
|---|---|---|---|
| 自 shard 絞り込み | 大 | D711 gate 2、D1728 | **不可。** D1728 の再訪条件 (独立な全体集合から導いた期待割付の供給設計) は本 wave も満たしていない |
| `Path.resolve()` を字句処理へ置換 | 1 worker あたり 1 秒未満 | E / gate 2〜5 | **不可。** repo 外拒否・symlink alias の重複検出・閉包入力の意味が変わる (`acceptance_shards.py:761-794`) |
| `_canonical_item` の 2 回目の呼び出しを 1 回目の結果で置き換える | **1 worker あたり 0.9 秒未満。48 worker でも wall 1 秒級** | E / gate 2〜5 (条件つき) | **採らない。** 実在の重複ではあるが、得られる wall が 1 秒級で、正規化・重複拒否・marker 検査の等価性証明が要る。**規律 2 の面に触れる変更を 1 秒のために入れない** |
| worker 間で digest を共有する / 親の再計算を子の報告値で代用する | 中 | E の独立性 | **不可。** 自己証明になる。D1728 が名指しで却下した形 |
| worker 数・配布順の変更 | 不明 | D532 が「提案しない」と明記 | **不可** |
| collection 集合の縮小・別系列化と併せた固定費削減 | 大 | D2003 が明示的に却下 | **不可** |
| bytecode cache を事前に用意する | 温なら 0。冷なら 1 worker あたり CPU 40 秒 | 無し (source と rewrite 条件が同じなら) | **条件つき。** 冷の発生が実測されたときだけ。28 走では冷を観測していない |
| prewarm を collection と重ねる | 当該走で 28.4 秒が対象。28 走の対象窓は 20.7〜41.1 秒 | 無し (集合は不変) | **[T-2616] が所有。** 本 wave は足さない。先行 wave は 279.8 秒を出したが赤 4 件で撤去している |
| production resolver の高速化 | 不明 (31 秒の全量ではない) | resolver の受理・拒否の等価性証明が要る | **本 wave では実装しない。** 候補としては閉じない |
| 何もしない | 0 | 無し | **`pre` についてはこれを採る** |

### 判定 (1 行)

**`pre` は削れない。`disp` は削れるが、その手は [T-2616] が持っている。**
どちらも自 shard 絞り込みを必要としない結論である。

---

## 5. 既裁定との関係

- **D1728 の再訪条件は満たされていない。** 本 wave は独立な全体集合から導いた期待割付の
  供給設計を示していない。**絞り込みは採らない。この判断は本 wave で覆さない。**
- **D1729 の再訪条件も満たされていない。** D1729 は「内訳の確定なしには次の一手が決まらない」
  ことを再訪条件にしたが、**本 wave の内訳確定は次の一手を変えなかった** —
  `disp` の手は既に [T-2616] にあり、`pre` には手が無いという結論だからである。
  **したがって D1729 の見送りは正しかったことが事後的に確認された。**
  受入 report の schema は v1 のまま置く。
- **D1894 の「3 shard 共通の collection と shard-0 の dispatch は今回の対象にしない」は、
  当時の短縮 wave の範囲指定であって恒久的な調査禁止ではない。** 両レンズが原文で照合し一致した。
  本 wave は短縮策を実装しないので、D1894 の対象指定と矛盾しない。
- **D1830 の「動く分は主に collection に出る」は 2026-09-08 の 62 走の事実として残る。**
  本 wave の 28 走では `pre` がむしろ最も動かない成分だったが、
  これは当時の記述を訂正するものではない。**測定時点の事実は後から変わらない。**
- **D532 は固定費削減そのものは認めている。** 本 wave が `pre` を「削れない」と結論するのは
  D532 の禁止のためではなく、**安全に削れる量が 1 秒級しかないという実測のため**である。

---

## 6. 段 3 の相談が親を覆した点 (棄却ゼロ)

親の段 1 の provisional 裁定 5 件のうち **3 件が real として覆った。** 棄却した所見は無い。

| 親の主張 | 判定 | 何が違ったか |
|---|---|---|
| (P1-A) 93 秒は残差であり現行は 56 秒台 | **維持** (標本の範囲に限定) | 「今後も動かない」とは書かない |
| (P1-B) `disp` の内訳は確定済み | **撤回** | 99.995% は `receipt/barrier` であって `receipt/disp` ではない。差 2.88 秒 |
| (P1-C) 38 秒は並列と plugin に帰属する見込み | **条件を訂正** | 同条件比較ではない (host・plugin・commit・集合が違う)。配分してはいけない |
| (P1-D) lever は集合不変なので gate に触れない | **撤回** | 集合不変は等価性の証明ではない。lever ごとの条件つき判定へ書き換えた |
| (P1-E) D1728 の再訪条件は未充足 | **維持** (両レンズが独立に支持) | — |

さらに親が数え落としていた事実を 2 件受け取った。

- `_canonical_item` は item ごとに **2 回**呼ばれる (親は 1 回と数えていた)。
- `:917` と `:919` の digest は **別入力**であり、重複計算ではない (親は重複と書いていた)。

---

## 7. 再現手順

**集計 script は repo へ入れない** (所在を問わず Python / Shell は実装面であり、親が書いたものを
置けない)。代わりに手順を書く。

- **§1 の表:** 各 session root の `shard-<n>/report.json` を `jq` で読み、
  `.session_timeline.collection_finished_epoch_s` と
  `[.session_timeline.workers[].first_test_started_epoch_s] | min` を取る。
  `shard-<n>/junit.xml` の先頭 400 byte から `<testsuite name="pytest" ...>` の
  `timestamp` / `time` / `hostname` / `tests` を読む。`timestamp` は `date -d` で epoch へ直す。
- **§3.1 の対照:** wave worktree で
  `/usr/bin/time python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider`。
  冷条件は
  `find <worktree> -name __pycache__ -type d -prune -exec rm -rf {} +` のあとに走らせる
  (`__pycache__` は `.gitignore` 対象なので作業ツリーは汚れない)。load は `/proc/loadavg` で記録する。
- **§3.2 の対照:** 上と同じ command に `-p tools.acceptance_shards` を足し、
  環境変数 `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` へ
  `{"session_root":"<repo 外の実在 dir>","shard_count":3,"shard_index":0}` を与える。
  `session_root` は repo の外に置く。**対照と処理は同じ負荷で連続して走らせる** —
  本 wave は load 1 分値 7.77 のときに 2 走を連続させた。
- **§2 の marker:** `shard-0/dispatcher.log` の `IZANAGI_MEMO_PREWARM_V1` 行。
  この行は計算ノード job の stderr から転記されている。

---

## 8. この dir の中身

- `verbatim/s1-brief-and-measurements.md` — 親が段 1 で書いた brief と実測の逐語 (子へ射影したもの)。
  **この brief の (P1-B) (P1-C) (P1-D) は段 4 で覆っている。** 上の §6 が正本。
- `verbatim/s3-consult-sol-cost-lens.md` — 費用と実効性のレンズの逐語 (gpt-6-astra / reasoning medium)。
- `verbatim/s3-consult-luna-correctness-lens.md` — 正しさ境界と既裁定の射程のレンズの逐語 (同上)。

## 9. 限界

- **標本は 2026-09-16 の 28 走 1 日ぶんである。** 同日の checkout 群は cache と共有資源の状態を
  共有しており、28 個の独立した環境条件ではない。
- **約 38 秒の配分は決まっていない。** 決めるには計算ノードで同条件の診断走が要る。
- **bytecode cache の有効性は確認していない。** entry 数だけで「温」とは言えない。
  冷が実測された時点でこの結論は見直す。
- **`pre` を「削れない」と言うのは「安全に削れる量が 1 秒級である」という意味であって、
  「物理的に短縮不能である」の証明ではない。**
