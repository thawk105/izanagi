# [T-155] write set 探索構造の crossover 実測 — 反転閾値は n\* ≈ 80 (warm) 〜 98 (cache 汚染下)

探索の妥当性文書 (dev-wave t155-crossover-bench、2026-07-28)。worklog (29)/(30) のユーザー裁定
「n\* crossover マイクロベンチを新タスクとして起票し実測する。`transaction.cc` に触れない。
出口 = selector-8b の workload descriptor 条件『set size > n\* なら container 機構を候補化』」を
実測した一次資料。数値の原本 = 同名 `.json` (job staging からの不変コピー、
sha256 = 0d42cddc1fff24256ddf5faa7cbcf8ddab4ef9b0acdcb93d0cc47cac4b419a7d)。

## 発見

silo の `searchWriteSet` 線形走査 (fat 要素 136B の vector) が side index に負ける反転閾値は、
**支配的な miss 経路 (op ごとに探索 → 挿入) で n\* ≈ 80〜100**。YCSB S2 動作点 (set size
mean≈5、max=10、(29)) より 1 桁上にあり、**(29)/(30) の「workload 条件付き休眠」裁定を定量で
裏付ける**。一方 **hit 経路 (read-own-write / RMW 再探索) の反転は n=2〜5 で既に起きる** —
休眠解除の判断は set size だけでなく再探索率にも依存する。

### build 経路 (miss 探索 → 挿入、ns/txn median、warm)

| n | linear | compact_linear | sorted_index | hash_index |
|---|---|---|---|---|
| 5 | **156** | 202 | 227 | 287 |
| 10 | **338** | 388 | 538 | 601 |
| 30 | **1212** | 1221 | 2636 | 1720 |
| 60 | **3020** | 2663 | 6234 | 3464 |
| 80 | 4712 | 3804 | 8739 | **4709** |
| 100 | 6701 | 5367 | 11459 | **6066** |
| 200 | 20825 | 15326 | 27141 | **12096** |

- 交点 (median 線形補間): linear→hash_index **n\* = 79.9** (warm) / **98.3** (32 MiB 汚染下)。
  linear→compact_linear **n\* = 32.0** (warm) / 79.6 (汚染下)
- **sorted_index (挿入ソート維持 + 二分探索) は build 経路で全域劣後** (O(n) 挿入 memmove が
  支配)。write set の membership 用途では候補から落ちる — 施錠順の整列は検証相で一括 sort する
  既存 sort-strategy 軸の形が正しく、逐次維持は誤設計
- outer 反復間の spread は交点近傍セルで ≤5.1% (n=80 の linear)、交点は 60 < n\* < 100 の帯として
  頑健。tie セル (warm n=80) の median 差は 0.06%

### hit 経路 (サイズ n の set への lookup、ns/lookup median、warm)

| n | linear | compact_linear | sorted_index | hash_index |
|---|---|---|---|---|
| 2 | 5.5 | **1.4** | 2.6 | 3.2 |
| 5 | 9.0 | **2.5** | 3.4 | 3.2 |
| 10 | 14.6 | **3.1** | 3.9 | 3.2 |
| 100 | 143.4 | 21.2 | 7.6 | **3.9** |
| 200 | 272.0 | 48.9 | 8.7 | **4.6** |

linear は n=2 で既に全候補に負ける (平均 n/2 要素 × 2 cache line 相当の走査)。ただし本経路の
重みは workload の再探索率 (RMW / read-own-write / 重複 key 率) に比例し、rmw=false の YCSB では
ほぼゼロ。(29) の S2 動作点で線形が正解である結論は変わらない。

## 再現条件と方法

- **対象操作の忠実度**: 線形走査は `cc/silo/transaction.cc:342-350` の verbatim
  (storage_ 比較 → `std::string == string_view` の key 比較)。要素は実 layout の複製で
  static_assert 強制 — `sizeof(WriteElement)=136` / `OpElement` 部 56B (storage_@0, key_@8,
  rcdptr_@40, op_@48) / `TupleBody`=64B、8B key (SimpleKey<8> 相当の big-endian) は SSO 内。
  挿入は ycsb.hh write op 相当 (4B payload heap 割当 + TupleBody 移動構築)、重複 key は
  `:529` の `goto FINISH_WRITE` 相当で挿入 skip
- **候補 4 系** (要素本体 vector<WriteElement> は全系共通 — 差分を探索構造だけに隔離):
  (L) linear = verbatim / (H) hash_index = `std::unordered_map<u64,idx>` 側索引 /
  (S) sorted_index = 挿入ソート維持の `vector<pair<u64,idx>>` + 二分探索 /
  (C) compact_linear = 同 12B entry の未ソート線形 (fat 要素の cache line 支配と
  アルゴリズムの寄与を分離する対照系)。側索引の u64 化は 8B 固定 key の機構設計自由度
- **計測**: 単一スレッド・taskset -c 2、build = [n 個の相異 key を miss 探索 → 挿入 + clear] を
  1 txn として reps 反復 (index clear は候補固有の実費として timed に含む)、hit = サイズ n 構築後
  (untimed) に撹拌順 lookup sweep。n ∈ {2..200} 12 点 × outer 7 反復 (汚染系は 5 点 × 5)。
  汚染系は txn 間に 32 MiB / 64B stride の RMW walk (untimed)。timer overhead 実測 17.75 ns/pair
  (候補間で共通の加算項 — 交点判定には効かない)。key 列・撹拌順は同一 seed で候補間共通
- **実行**: Pegasus gen_S バッチ 1 node (bnode010、Xeon Platinum 8468 48c)、job 872916.nqsv、
  2026-07-28 10:23:32–10:24:05 JST (37 秒)、g++ 11.4.0 -O3 (ノード上でビルド)。
  単独性: run 前 loadavg 0.08、他ユーザー >50% CPU プロセス 0 件 (検知したら rc=4 で停止する
  gate をジョブに内蔵)。一次ログ = `output/env/pegasus/t155-crossover/job-staging/0:872916.nqsv/`、
  ジョブ・ベンチ = 同 `job.sh` / `bench.cc`

## 方法論の裏付け (measurement validity)

1. **意味論の一致 (生死確認、DW-G01)**: selfcheck が 4 候補を同一 key 列 (新規 + 再 lookup 混在、
   n ∈ {1,2,7,33,200}) で駆動し、hit/miss 判定・返却要素・set サイズの完全一致を検査。
   計測ノード上でも pass (`selfcheck.stdout`)
2. **fail-closed**: layout 不一致は static_assert のコンパイル赤、候補間不一致は rc=3、
   単独性破れは rc=4、結果欠損は rc=2 でジョブが止まる。検査はパイプ不使用 (F44)
3. **DCE 防止**: 全 lookup 結果を global sink へ集約し JSON に出力 (sink=268313622644)
4. **規律 1**: trace 系を含まない素の計測。CCBench 本体 (`external/ccbench`) には非接触・
   非改変 (layout の読み取り参照のみ)。本番コード 0 byte
5. **交点の頑健性**: outer 7 反復の median で判定、交点近傍の spread ≤5.1%。warm/汚染の
   2 条件が実 workload の cache 状態を挟む (実測 n\* は 80〜98 の帯)

## 解釈と限界

- **機序帰属**: 60 ≤ n ≤ 100 帯では compact_linear (12B entry) が hash に肉薄〜勝る —
  linear の敗因の大半は**アルゴリズム (O(n)) でなく fat 要素の cache footprint** (136B × n、
  走査が触るのは先頭 40B だがラインは 2〜3 本/要素)。探索構造を変えずとも key だけの
  side array で n\* は 32→80 へ動く。機構カタログ側の第一候補は「hash 置換」でなく
  「compact key 側索引」でありうる
- **保守側の限界**: build 経路の lookup:insert 比は最小の 1:1 で測った。実際は read op も
  write set を miss 走査するため (`transaction.cc:211-220`)、比が上がるほど n\* は下がる
  (本実測は n\* の上界側)。逆に側索引の維持は abort/retry 時の clear 実費を含むが、
  clear は timed に含めてあり、頻繁な abort はどの候補でも同率で clear を増やす
- **単体ベンチの限界**: masstree 走査・検証相・並行干渉との interleave は再現していない
  (汚染系はその近似)。休眠解除して本実装する場合は (27) 差し戻し理由 (a) 正しさ分岐
  ((`:529` の membership 判定が意味論に乗る)・(b) 三すくみが依然立つ — n\* は「いつコストを
  払うか」の入力であり実装 GO ではない

## selector-8b への出口

workload descriptor 条件の材料として凍結する値:

- **`set_size_p50 > 100` (汚染下 n\* の切り上げ) で container 機構 (compact 側索引 / hash) を
  候補化する**。80〜100 は tie 帯のため保守側の 100 を採る
- 32 < set size < 80 の帯は compact_linear のみ有利 — 候補化するなら機構を分けて登録する
- 再探索率 (RMW / read-own-write) が高い workload は hit 経路の n\*≈2〜5 が効くため、
  descriptor に再探索率の軸を足すまで set size 単独条件は保守側 (>100) に留める
- corpus 内の実在 workload: YCSB 族は (29) の検証済み二項モデルで p99 ≤ max_ope ≪ 80 のため
  発火しない。TPC-C (数十 row・可変) は帯の下端に届きうる — 採用時に per-workload の
  set-size 分布実測 ((29) の trace 副産物法) を先に走らせる
