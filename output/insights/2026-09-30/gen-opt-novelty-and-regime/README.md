# gen-opt で論文が成り立つか — 新しさの地図・勝負する条件・SOTA と余地の測定・判定 (md_23、2026-09-30)

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_23.txt` (2026-09-30 19:31 JST 版、sha256 `6702a2c0…`) と同じ directory の `common-5.txt`。
- 背景 (ユーザーの発言、2026-09-30 夜、依頼文の逐語): 「性能が良くなった、めっちゃ良い性能を生み出したとかじゃないと論文にできません。」
  「one fit allを出すのはほぼ無理なのが今の世界です。だから多くの論文では「こういう環境下でこういう手法がsotaより良くなった」みたいなものです。」
  「あなたは新規性の考慮を結構できてないと思う。考え直して」
- 着手時の main: `d79fd3524`。CCBench の pin: `68106660686232781bca3be792a750d3e19d7a8a` (C)。LLM による生成はしていない。repo の code・patches/・submodule は変えていない。
- 本 dir の file:

| file | 中身 |
|---|---|
| `search-registration.md` | 検索の事前登録 (主張 N1〜N5 と検索式の対応、結果前に commit `a28f9111d`) と改訂 1・2 |
| `search-ledger.md` | 補助探索 26 本 (R4)、索引検索 (arXiv 完走・OpenAlex 未完走) の記録、N4・N5 の結論 |
| `search-judgments-arxiv-run1.jsonl` | arXiv の hit 76 行の判定 |
| `prior-work.md` | 最も近い先行 11 本の表 (N1・N2) と評価の健全性を扱う近傍 2 本、範囲外の型 T1〜T6 (N3) |
| `conditions-registration.md` | 条件 R1〜R5 と SOTA 集合・上限の目安・余地の閾値の事前登録 (測定前に commit `ba6e86342`) と改訂 1・2 |
| `measurements/results.md` | 測定の集計表 (条件ごとの S・B1・B2・r1・r2・区分と、全構成の 3 rep) |
| `measurements/points.csv` | 全 261 点の値 (集計 JSON から機械的に抜き出したもの) |
| `measurements/raw-sha256.txt` | repo の外に置いた生データ・driver・spec・plan の sha256 |
| `measurements/*.png` | 条件ごとの図 |

---

## 0. 結論

**推せる条件は R1 (YCSB の高競合 hotspot) の 1 個だけで、しかも条件付きである。R2・R3 は、登録した判定規則では推せない。**
今の izanagi の hook のままでは、R1 でも「先行研究の表現範囲の外の仕組み」を主張できる見込みは薄い。gen-opt を論文の芯にするには、
新しい口 (validation の方式・実行前の並べ替え・その組み合わせ) を開き、R1 で学習型 CC (NeurCC) 級の SOTA を上回る必要がある。

| 条件 | 余地 (登録の閾値) | 文献の SOTA が既に取っている余地 | 範囲外の仕組みが効く筋道 | 判定 |
|---|---|---|---|---|
| R1 YCSB hotspot (zipf 0.99、read 50%、10 op、48 thread) | **大**: S = 2.28M tps (Silo の静的 backoff 5 µs、abort 率 68%)、B1 = 8.19M、B2 = 7.18M、r1 = 3.59、r2 = 3.15 | NeurCC が hotspot の YCSB 拡張 (θ=1、16 thread) で Silo の最大 4.27 倍・Polyjuice の 3.32 倍 (Fig.7a) | abort に消える 68% は同じ hot な行への書き込みの衝突。T1 (施錠順)・T2 (validation の方式)・T3 (hot な取引の実行前の並べ替え)・T6 (組み合わせ) が効きうる。T5 (待ち方) は NeurCC の範囲と重なる | **条件付きで推す** |
| R2 TPC-C 1 warehouse (48 thread) | **中**: S = 463K tps (TicToc・BACK_OFF=0、abort 率 71%)、B1 = 679K (48 warehouse の緩い目安)、B2 = 1.60M、r1 = 1.47、r2 = 3.46 | IC3 (1 WH・64 thread で 434K、2PL・OCC は 50K 未満)、DRP (OCC の 6.6 倍)、Polyjuice (高競合で IC3・Tebaldi に +56%)、NeurCC (2 位の最大 1.14 倍)。学習型 CC と手作りの特化 CC の本拠地 | 同上。ただし CCBench の stock の 21 構成のうち 13 構成 (SI の参考 2 構成を含む) が成功 2 回未満 (§3.2) で、比べる相手の集合が健全でない | 推さない |
| R3 BoMB の長短混在 (L1 1 本 + 短い取引 47 本) | **小** (登録の指標 = 短い取引の throughput): S = 40.3M、B1 = 39.2M、r1 = 0.97、r2 = 1.00 | Oze (BoMB で L1 を commit させつつ短い取引を保つ)、Shirakami | **登録の指標の外で大きな無駄がある**: 測れた直列化可能なプロトコルは全構成で、混在の L1 を 3 秒間に 1 回も commit しない (単独なら 5〜7 回。SS2PL は segfault で未観測)。T4 (版の管理) や L1 の優先・予約が効きうるが、VHash (別 manager) と主題が重なる | 登録の規則では推さない。次の登録の候補として記録 (§4.3) |

- **新しさの地図 (§1):** 学習・自動化で CC を特化する先行 (Polyjuice・NeurCC・ATCC・CormCC・ACC・Callas・Tebaldi) は、どれも正しさを固定の骨格に置き、
  骨格の上の方策の値か既存 CC 部品の割付けを探す。LLM がコードを生成する先行 (ADRS 系) は取引の順序だけを返し、直列化可能性の検査を持たない。
  **「生成物の直列化可能性を探索の反復の中で機械検査する」(N5) は、arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲では未検出** (RW2、1 索引。OpenAlex は未完走)。
  一方、登録した N4 (LLM が取引の CC の判断を実装するコードを生成し性能を評価) は、ADRS 系 3 本の検出で**成り立たない**。
- **今の izanagi の hook の位置 (§1.3):** 開いているのは T1 (commit 時の施錠順) と T5 (待ち・abort・backoff) だけ。T5 は NeurCC・Polyjuice の表現範囲と重なり、
  T1 は手作りの既知機構 (Cicada の競合度順の施錠) と同じ型である。

---

## 1. 新しさの地図 (手順 1)

### 1.1 最も近い先行研究

表と逐語は `prior-work.md`。要点:

- **学習型 CC** (Polyjuice OSDI 2021・NeurCC 2503.10036 v4・ATCC 2603.13906): 状態 (取引型・アクセス位置、NeurCC はホットさ・依存数など) から動作 (待ち・dirty read・書き込みの公開・
  early validation・timeout・優先度・backoff) への表を、進化・BO・RL で学ぶ。正しさは OCC 型の 4 段の最終検証 (骨格) による構成的保証。
  NeurCC 自身が「事前スケジューリング (決定的 CC)・sagas・timestamp ordering は範囲外」「新しい lock ベースのプロトコルは導入しない」と書く。
- **組み合わせ系** (Tebaldi・CormCC・ACC・Callas): 既存 CC 部品 (2PL・OCC・SSI・RP など) を取引型の群か data partition に割り付ける。部品の中身は変えない。
  割付けは人手 (Tebaldi)・貪欲な探索 (Callas)・classifier (CormCC・ACC)。
- **LLM のコード生成** (ADRS 2510.06189 とその後継・LEVI・AI-Driven Research for Databases 2604.06566・Bespoke OLAP・Vulcan): ADRS の取引 scheduling は
  1 操作 1 単位時間の模擬器で「取引の並べ順」を返す関数を進化させ makespan を評価する。直列化可能性の検査は無く、評価器の穴 (全取引が並んだかを見ない) を
  2609.19799 が実証した。2604.06566 §8 は "Applying ADRS to more complex subsystems, like concurrency control or write-ahead logging remains an open challenge.
  To safely evolve these critical components, evaluators must integrate rigorous correctness checks" と書く (親が原文テキストで照合)。

### 1.2 検索の結論 (N4・N5)

`search-ledger.md` §2.3。登録どおりの判定語で書く。

- N4: **不成立** (arXiv A2・A4 で 2510.06189・2512.14806・2605.09764 を検出。3 本とも ADRS の取引 scheduling 課題)。
- N5: **arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲では未検出** (RW2)。OpenAlex は匿名検索の一時停止と時間切れで run1〜run3 とも未完走、DBLP は不使用。
  無限定の「先行なし」は書かない。陽性対照 (Polyjuice・NeurCC・ADRS) は現れたが、2604.06566 は arXiv の登録式に現れなかった (偽陰性の記録)。

### 1.3 範囲の外の型 (N3) と、今の izanagi の位置

`prior-work.md` §3 の表。**正直な読み: 今の hook で作れる仕組みは、先行研究の範囲と重なる (T5) か、手作りの既知機構と同じ型 (T1) である。**
先行研究の範囲の外にあり、かつ手作りの SOTA と別物になりうるのは T2 (validation の方式)・T3 (実行前の並べ替え・worker への寄せ)・T6 (組み合わせ) で、
いずれも izanagi の hook は閉じている。これらを開けるには、新しい hook と、その型に効く正しさ関門 (規律 2・3) が要る。

---

## 2. 勝負する条件の候補と SOTA 集合 (手順 2)

`conditions-registration.md`。R1〜R5 を測定前に登録し、R1〜R3 を測った。R4 (読み主体の高 skew) は既存記録で余地が小さい見込み、R5 (大きい取引・中競合) は文献の根拠が 1 本だけのため測っていない。
文献の手法の試作は作っていない (理由は登録 §3: 試作は SOTA 側で新しさに寄与せず、trace build と検査器の往復が要る)。

---

## 3. 余地の測定 (手順 3)

### 3.1 やり方

- 計算ノード (Pegasus、48 コア・HT 無効) で、stock の CCBench の各プロトコル (BACK_OFF 0/1) と Silo の静的 backoff (B-10 の固定形 genome 5・10・25 µs、ycsb・tpcc のみ) を
  trace 無効・計器無効 (`CCBENCH_TRACE=0`・`CCBENCH_ADD_ANALYSIS=0`、compile 命令の -D 値を build 後に照合) で build した。性能だけの測定で、直列化可能性の検査は回していない。
- 1 job に「ある条件の変種の全構成」を入れ、rep で job を分けた (処置とノードを 1 対 1 にしない)。job 内は seed 23 の乱順。48 thread、extime 3 秒、3 rep、1 走の上限 60 秒。
  各 job の開始時と各 binary の実行直前に単独性を確かめた (driver の `_assert_single_tenant`)。
- 投入前に数えた job の中身と見積り: 9 job (YCSB と TPC-C 目標の job 42 点・約 198 秒 × 3、TPC-C 上限と BoMB の job 36 点・約 263 秒 × 3、L1 単独の job 9 点・約 48 秒 × 3)。
  実測の Elapse は 479・374・65・430・383・63・487・384・64 秒 (合計 2,729 秒)。**YCSB と TPC-C 目標の job は見積りの約 2.4 倍で 5 分を超えた** (TPC-C の timeout 60 秒の走が 1 job に 5〜6 回入ったため)。
- 計算ノードの合計: build (失敗 9 本を含む) 約 585 秒、smoke 235 秒、本測定 2,729 秒、計 約 3,550 秒 (**約 1.0 node 時間**、2 node 時間未満)。
- 生データ・driver・spec・plan は repo の外 (`/work/SFC/tanab/tmp/md23-gen-opt-novelty-2026-09-30/`) に置き、sha256 を `measurements/raw-sha256.txt` に記録した。
  driver は Codex author が書いた (子木 `md23-author`、最終 `2260b86a2`。本測定は `e0a0c4bde` 版 sha256 `4e8b5a88…`、集計と図は `2260b86a2` 版。集計表は `7c72eea08` 版の出力と byte 一致)。

### 3.2 結果

全値は `measurements/results.md` と `points.csv`。

**R1 (YCSB hotspot)**: 最良は Silo の静的 backoff 5 µs (2.28M tps、abort 率 68%)、次いで 10 µs (2.17M)、25 µs (1.79M)、Silo・BACK_OFF=0 (1.54M)、TicToc・BACK_OFF=0 (1.50M)、
Cicada・BACK_OFF=0 (1.22M)。MOCC は 0.40〜0.48M、ERMIA は 0.06〜0.29M。一様分布の上限目安は Silo の 8.19M。全構成 3/3 成功。

**R2 (TPC-C 1 warehouse)**: 成功が 2/3 以上の構成は TicToc (463K・286K)、MOCC (42K・58K)、Cicada (13K)、Oze (68〜76 tps) だけ。
**stock の失敗**: Silo の全 5 構成 (BACK_OFF 0/1・固定 5/10/25 µs) と MVTO は "insert order failed" を出し続けて 60 秒の上限で打ち切り (Silo は 3 回中 2〜3 回)、
ERMIA・SI は `garbage_collection.cc` の `gcRecord` で ERR 終了、Cicada・BACK_OFF=0 は `transaction.cc` 853 行の `gc_records` で 1 回 ERR、SS2PL は segfault (rc=-11)、Oze は 1 回 abort (rc=-6)。
48 warehouse の上限の変種では全プロトコルが成功した (Silo 679K が最大)。

**R3 (BoMB の長短混在)**: 短い取引の throughput は Silo 40.3M・TicToc 38.6M・MOCC 24.4M・Cicada 2.9M・MVTO 1.8M・Oze 1.4M・ERMIA 1.2M・SI 1.1M で、
L1 が居ない場合 (Silo 39.2M) と差が無い。**L1 は、測れた直列化可能なプロトコルの全構成 (Silo・TicToc・MOCC・Cicada・ERMIA・MVTO・Oze の各 BACK_OFF 0/1、3/3 成功) で 3 秒間に commit 0 回 (Oze 以外は abort 5〜8 回)。SS2PL は BoMB で 3/3 segfault したので観測していない。** L1 単独なら 5〜7 回 commit する。
L1 を混在で commit したのは SI (直列化可能でない、6 回) だけ。Oze は単独・混在とも L1 の commit と abort が 0 回 (3 秒で L1 が終わらない)。SS2PL は BoMB で segfault。

### 3.3 目安の限界

- B1 は同じ hot な行を書く取引を順に並べる待ちを無視し、R2 では 48 倍の大きさの database の効果を含む。達成できる値ではない。
- B2 の算法: 集計は「最良構成の rep ごとの throughput/(1−abort 率) の中央値」で計算した (driver への指示どおり)。登録 §4 の文面 (最良構成の throughput / (1 − abort 率)) を
  中央値同士で読むと、R2 の B2 は 1,602,873 (掲載 1,603,105) で r2 は 3.46 のまま、R1 も区分は変わらない (段 6 レビューの所見 F1)。
- B2 は abort した試行が commit と同じ費用だと仮定し、待ち・backoff の休止に消えた時間を含まない (trace・計器なし build では測れない)。
- 値は stock の CCBench の性能で、どの構成も本 wave で直列化可能性を検査していない。R2 の比べる相手の多くが stock の欠陥で失敗しており、R2 の S (TicToc) は健全な SOTA 集合の最良ではない。
- CCBench の YCSB は書き込みで値が実質変わらない (md_2 §7)。値の一致で検証を通す型の仕組みは R1 で過大に見える。

---

## 4. 判定 (手順 4)

登録 §5 の規則: 推す条件は「余地が大か中、かつ範囲外の仕組みに筋道がある」もの。

### 4.1 R1: 条件付きで推す

- 余地は大 (r1 3.59、r2 3.15)。48 thread の 68% の試行が abort で消えている。
- 文献の SOTA: NeurCC が hotspot の YCSB で Silo の最大 4.27 倍を報告しており (基盤・thread 数が違う)、**余地の相当部分を学習型 CC が既に取っている可能性が高い**。
  Plor (YCSB-A θ0.99 で Silo に +9%)、Bamboo (単一 hotspot で Wound-Wait の最大 19 倍) も比べる相手になる。
- 範囲外の筋道: abort の原因は同じ hot な行への書き込みの衝突で、(a) 衝突する取引を実行前に同じ worker へ寄せる・並べ替える (T3、NeurCC が範囲外と明記)、
  (b) hot な行に限って validation の方式を変える (T2)、(c) それらを施錠順と連動させる (T6)、は NeurCC・Polyjuice の表の外にある。
- **条件**: (1) T2・T3・T6 の口を開ける新しい hook と、その型の正しさ関門を作る (今の hook の T1・T5 だけでは範囲外を主張できない)。
  (2) 比べる相手に NeurCC 級の学習型 CC を入れる (CCBench への移植か、公開実装の基盤での比較。7.1 の「実測比較は見送り」の再判断が要る)。
  (3) 手作りの SOTA (Cicada の競合度順の施錠、TsDefer、BCC) を人の試作で同じ条件に並べ、M がそれらの再発見でないことを示す。

### 4.2 R2: 推さない

- 余地は中 (r1 1.47 は緩い目安)。TPC-C 少 warehouse は IC3・DRP・Polyjuice・NeurCC・Tebaldi の本拠地で、学習型 CC と手作りの特化 CC が既に大きな倍率を報告している。
- stock の CCBench の比べる相手が 21 構成中 13 構成 (SI の参考 2 構成を含む) で成功が 2 回未満になり、公正な SOTA 集合を作る前に基盤の修理が要る (memory の「基盤の欠陥は比較から外さず使い続けて直す」方針なら、修理自体が別の作業になる)。

### 4.3 R3: 登録の規則では推さない (次の登録の候補)

- 登録した指標 (短い取引の throughput) では余地は小 (r1 0.97)。**しかし L1 の commit が、測れた直列化可能なプロトコル (SS2PL は segfault で未観測) の全構成で 0 回であり、長い取引の飢えという大きな無駄が登録の指標の外にある。**
  結果を見た後で指標を差し替えないので、本 wave では推さない。
- 次に登録するなら、指標を「短い取引の throughput を保ったままの L1 の commit 率」にし、SOTA 集合に Oze (CCBench では本 wave の設定で L1 が 3 秒で終わらない) と Shirakami を入れる。
  長い取引の版の扱い (T4) は VHash (別 manager) と主題が重なるので、担当の切り分けが先に要る。

### 4.4 gen-opt を論文の芯にするかの判断材料

- **芯にできる形は「R1 × (T2・T3・T6 の新しい口で LLM が作った機構) × (NeurCC 級の学習型 CC + 手作りの SOTA)」だけ**で、今の hook のままの gen-opt (T1・T5) では
  「既存手法の表現範囲の外」を主張できない。
- 新しさの主張として使えるのは N5 の「arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲では未検出」(RW2、1 索引。直列化可能性を探索の反復の中で機械検査する CC 合成) と、2604.06566 自身が CC を「厳密な正しさ検査が要る未解決の課題」と書いていること。
  ただし N5 は方法の新しさであり、ユーザーの基準 (大きな性能向上) を満たすには R1 での性能の勝ちが別に要る。
- 反対の材料: R1 の余地の相当部分を NeurCC が既に取っている可能性、R2 の基盤の欠陥、R3 の主題の重なり。

---

## 5. 確かめたこと / 確かめていないこと

| 確かめたこと | 確かめていないこと |
|---|---|
| 検索の登録 (主張→式) を結果前に commit (`a28f9111d`)、条件の登録を測定前に commit (`ba6e86342`)。改訂は結果を見る前に追記 (時刻と理由つき) | OpenAlex の枝 (未完走)、DBLP、venue 本体の年次一覧 (母集合の外) |
| arXiv 4 式の完走 (totalResults と取得数の一致) と 76 行の判定の件数 (jq で検算) | arXiv の判定は題名・要旨による (検出 3 本と要裁定 3 本は原典で確認) |
| 先行研究の表の逐語は子が原典から写し、2604.06566 §8 は親が原文テキストで照合 | 他の逐語の親による再照合 (段 6 の review で抜き取り) |
| 261 点の測定値 (plan の 3 × (42+36+9) と一致)、構成ごとの成功数、失敗の種類と本文 | 性能値の直列化可能性 (検査していない)。文献の手法の CCBench での性能 (試作していない) |
| 静的 backoff の genome の binary が互いに異なること、stock の -D 値の照合 (driver の build) | NeurCC・Polyjuice の R1 相当の条件での実測 (原典の倍率の引用だけ) |

## 6. 子の工数と経過

- Claude の子: 探索 1 (sonnet)、原典読み 3 (opus)、arXiv の判定 1 (opus)、要裁定の原典読み 1 (sonnet)。
- Codex: author 1 (計測 driver と取得 script)、fix 8 (BoMB の割付けと parse、TMPDIR、503 の再試行、third-party の cache、compile 命令の照合、plan の見積り、失敗の集計、図)。
  計算ノードで 1 件ずつ欠陥が出る型 (TMPDIR → cache → compile 命令) を 3 回踏んだ。
- 計算ノード: 約 1.0 node 時間 (§3.1)。
- 段 6 の独立 read-only レビュー (Codex 1 本、報告は repo の外 `stage6/review.md`): must-fix 5 件 (B2 の算法、prior-work の N4 の古い記述、R3 の L1 の全称、N5 の RW2 の限定語、先行の本数) を
  real と裁定し親が本文で直した。判定は変わらない。nit 2 件 (R3 の指標の差し替え・単独性の確認の実在) はレビュー子が refuted とした。
  照合された数字: R1・R2・R3 の S・B1・r1、13/21 構成、261 点、76 行、ADRS の 20%・34%・60%、Bespoke OLAP の 11.17・45.33 倍、依頼の逐語 3 件、2604.06566 の 2 文。
  Polyjuice・NeurCC・ATCC の逐語は文字化原典が job dir に無く再照合していない。
