# 最も近い先行研究の表と、その表現範囲の外 (md_23、N1・N2・N3)

- 作成: 2026-09-30 JST。検索の登録 `search-registration.md` の R1 (名指しの起点) と R3 (参考文献の追跡)・R4 (補助探索) で読んだ原典から作った。
  索引検索 (R2) の結果は `search-ledger.md` に別に置く (本 file の表に載せた論文を見つけた経路は各行に書く)。
- 読んだ担当: 親が起動した Claude の子 3 本 (opus、読み取りだけ、2026-09-30 19:49〜20:00 JST)。子の報告を親がこの表にまとめた。
  逐語 (英語) は子が原典から写したもの。**親は原典を再照合していない** (段 6 の独立レビューで抜き取り照合する)。
- 読んだ深さ: Polyjuice・NeurCC・ATCC・Tebaldi・CormCC・ACC・Callas・ADRS v3・2604.06566・2512.14806・2609.19799・2606.15834・2603.02001 は本文 (PDF を文字化。図中の値は読めていない)。
  Vulcan (2512.25065) は要旨だけ。IC3・DRP は本 wave では本文未読 (md_2 のカードの記載だけ)。CormCC の技術報告 TR-2018-06 は取得失敗で未読。

## 1. 表 (N1・N2)

倍率はすべて**原典の基盤・thread 数・workload での値**で、CCBench の値ではない。

| 研究 | 何を自動化するか | 探索する空間 (表現範囲、原典の定義) | 探索の方法 | 正しさの保証 | 評価の条件と倍率 (原典の図表) | 範囲の外 (原典の定義から言えるもの) |
|---|---|---|---|---|---|---|
| **Polyjuice** (OSDI 2021、arXiv 2105.10329 v3) | 取引型・アクセス位置ごとの細かい CC 動作の選択 (人が混合 CC の割付けを決めていたものの置き換え、§1・§2) | 状態 = (取引型, access-id) の 2 つだけ (§4.2)。動作 = 型ごとの Wait 位置 (依存先がそのアクセスまで進むのを待つ)、Read-version (clean / dirty)、Write-visibility (private / public)、Early-validation の有無 (§4.3)。別に backoff 表 (取引型 × 直前の結果 × abort 回数 0/1/2+ → 乗数 α、§4.5) | 進化 (変異のみ、交叉なし、300 反復 × 40 方策、1 反復約 80 秒、§5・§7.5)。初期集団に OCC・2PL*・IC3 | 骨格による構成的保証: 依存先の終了待ち → write lock → read 検証 → 反映の 4 段 (§4.4、付録 A)。"we are not concerned with correctness; instead, we rely on a separate validation mechanism" (§2) | TPC-C 48 thread: 2 WH で他の 1.5 倍超、高競合で IC3・Tebaldi に +56% (Fig.4a/b)。TPC-E θ=2〜4 で +42〜55% (Fig.8a)。**48 WH では Silo より 8% 遅い**。1 WH で学習した方策を 48 WH で使うと Silo の 71% (Fig.12a) | 見られない状態 (key・値・実行時の競合度・経過時間)、選べない動作 (特定取引を待つ・優先度・timeout・古い版や snapshot を読む)、変えられない骨格 (最終検証の方式・範囲検索・commit 時の lock 順序・版管理・GC・ログ)、事前順序付け (Calvin 等) |
| **CCaaLF → NeurCC** (arXiv 2503.10036、v4 2026-03 で改題・改名。会議名は本文に無い) | 状態から CC 動作への関数 F を、負荷の変化を検知するたびに短時間で最適化し直す (§1・§3.1) | 入力 = 9 種の特徴 (実行済み SQL 数・dirty read の有無・取引型・access ID・読み書き・データのホットさ・依存先の数・実行中の取引数・out-degree、Table 3) から選んだもの。出力 = 衝突の検出方法 {なし, 重大なものだけ, 全部}・timeout (0 = 即 abort、∞ = block)・優先度・型ごとの pipeline-wait・expose、取引型ごとの backoff (§4.1・§4.2) | ベイズ最適化 + グラフ縮約探索 (§5)。ピーク到達まで平均 9.67 分、Polyjuice の約 11 倍速い (Fig.8e) | 骨格による構成的保証: Polyjuice とほぼ同じ OCC 型 4 段 (Alg.2、§4.5 に帰納法の証明)。対話型では dirty read と部分再試行を禁止 | 24 コア・16 thread。YCSB 拡張 (hotspot θ=1): Polyjuice の最大 3.32 倍、Silo の 4.27 倍 (Fig.7a)。TPC-C 1/4 WH: 2 位の最大 1.14 倍 (Fig.7b/c)。対話型 TPC-C で最大 1.96 倍。**1 thread では Silo より最大 6.2% 遅い、読み取り専用で 2.5% 遅い** | 原典 §3.3: 事前スケジューリング (決定的 CC)・sagas・timestamp ordering は範囲外。§4.4: "NeurCC does not outperform 2PL when all the actions are detect-all, nor does it introduce a new lock-based protocol"。読める版は 2 つ、commit 時の検証は固定 |
| **ATCC** (arXiv 2603.13906 v1、2026-03) | LLM エージェントが生成する取引 (agentic) について、OCC から lock への切替え時期・lock 範囲・優先度上げを RL で決める (§1・§3) | 状態 = 局面の信号 (SQL 間隔・集合の増分など) と競合の指標。動作 = OCC 継続 / {ホット・コールド × 読み・書き} 集合の lock / 優先度上げ (Table 1) | RL (手法名・訓練所要は v1 に記載なし) | 骨格による保証 (Silo 型の最終検証、形式的証明なし) | openGauss-MOT、24 コア。agentic YCSB 高競合で MOCC の約 3.1 倍、Wound-Wait の約 2.2 倍 (Fig.10)。agentic TPC-C 1 WH で Wound-Wait の 2.2 倍 (Fig.12)。低競合で約 3% の損 | lock の解放・降格なし ("ATCC does not adopt the release lock action"、§5.6)。書き込みは commit 時まで遅延で固定 (dirty read・早期公開なし)。衝突解決は Wound-Wait で固定。MVCC なし |
| **Tebaldi** (SIGMOD 2017、DOI 10.1145/3035918.3064031) | なし (CC の木の構成は人が設計する、§8) | 部品 4 種 (2PL・runtime pipelining・SSI・多版 TSO) を取引型の群ごとに割り付ける多層の木 (§3・§6) | 人手 | Adya の DSG に基づく Consistent Ordering の合成条件 (§4) | 20 台 × 20 コアの分散環境、TPC-C 10 WH: 2PL の 20 倍超、Callas の 3.7 倍 (Abstract) | 部品の中身は固定。4 phase で表せない CC は入らない (§5.2 の逐語あり)。衝突の組ごとの割付け不可 |
| **CormCC** (USENIX ATC 2018) | data partition ごとの CC の選択と稼働中の切替え (classifier、§4・§5) | 部品 = COCSR かつ strict な protocol (試作は PartCC・Silo OCC・No-Wait VLL 2PL)。単位 = partition (§4.2) | 二値 classifier 2 つ (中身は TR-2018-06、未読) | 全部品が COCSR であることからの合成の論証 (§4.2) | 32 コア。5 秒ごとに条件が変わる YCSB で PartCC の 2.5 倍・OCC の 1.9 倍・2PL の 1.8 倍 (Fig.9)、TPC-C で 2.8・2.4・1.7 倍 (Fig.10)。選択を誤ると最良の 0.91 倍 | strict でない protocol (dirty read・pipelining) は入らない。部品の中身は固定 |
| **ACC** (CIDR 2017) | data の clustering・core 割当て・cluster ごとの protocol 選択 (DecisionTree) | 部品 = PartCC・Silo OCC・2PL No-Wait、単位 = cluster | classifier (offline に合成 workload で学習) | 4 通りの場合分け (§5) | 32 コア。最大で PartCC の 3.0 倍、OCC の 2.1 倍 (Fig.6) | CormCC と同じ型 |
| **Callas** (SOSP 2015) | 取引の群分けを測定に基づいて自動で決める道具 (§6.2) | 群内 = runtime pipelining か locking、群間 = nexus lock 固定、2 層固定 | 測定による貪欲な探索 | 群内・群間の条件 (§3.2) と nexus lock (§4)。**評価は read-committed** (MySQL Cluster の制約、§6) | MySQL Cluster 比で TPC-C 8.2 倍 (Fig.5) | lock 系の部品だけ |
| **ADRS / Barbarians at the Gate** (arXiv 2510.06189 v3) の取引 scheduling (§5.4) | 取引の集合から実行順を返す関数のコードを LLM (OpenEvolve) で進化 | 出力は取引の全順序 1 つだけ。競合の処理 (後ろへずらして待たせる) は模擬器に固定 | LLM の進化 (100 反復、2 時間未満) | **直列化可能性の機械検査なし**。模擬器は 1 操作 1 単位時間の Python。妥当性検査は番号の範囲しか見ない (2609.19799 付録 D が「全取引が並んだか」を見ない穴を実証) | offline で SMF 比 makespan −34% (§5.4 本文)。同じ v3 の Table 1 は 20%、後継版 2512.14806 は 60% (版で数字が違う) | 待たせる・abort させる・再試行・validation・読む版の選択はどれも表せない (online 設定は abort が模型に無い) |
| **AI-Driven Research for Databases** (arXiv 2604.06566 v1、2026-04、同じ研究グループ) | PostgreSQL のバッファ追い出し方策・Calcite の書換え方策・index 選択のコードを LLM で進化 (評価器も一緒に進化) | 各部品の方策コード (意味論を保存する問題に限る) | LLM の進化 | 単体テスト、書換えは結果行の一致。直列化可能性の検査なし | バッファ: hit rate +19.8% (TPC-H SF10)、書換え: 5.4 倍 (TPC-H)・6.8 倍 (DSB) (Table 1) | §8 の逐語: "Applying ADRS to more complex subsystems, like concurrency control or write-ahead logging remains an open challenge. To safely evolve these critical components, evaluators must integrate rigorous correctness checks (e.g., formal verification or exhaustive fuzz testing)." |
| **Bespoke OLAP** (arXiv 2603.02001 v2、PVLDB 19(11)) | 負荷ごとに C++ の OLAP エンジン全体を LLM agent が合成 | エンジン全体のコード (読み取り専用の分析処理) | LLM agent | DuckDB との結果照合 + fuzzy testing | DuckDB 比 11.17 倍 (TPC-H SF20)、45.33 倍 (CEB) (Fig.1) | 取引・並行性制御を扱わない (本文に "transaction"・"concurren" の語が無い) |
| **Vulcan** (arXiv 2512.25065 v3、EuroSys 2027 採択、要旨のみ) | 状態を持たない判断関数を制限言語で LLM に書かせる | spot VM・cache eviction・メモリ階層の判断関数 | LLM の探索 | 制限言語による構造上の安全 | (要旨のみで数値は写していない) | DB の取引を含まない |

評価の健全性を扱う近傍 (手法ではない): **Evolution or Illusion?** (arXiv 2609.19799 v1、IBM) は ADRS の取引 scheduling の評価器の穴 (全取引が並んだかを検査しない) で、
最良プログラムが各負荷 1 取引だけを並べて約 4 倍の score を得たことを実証した。**AIChilles** (arXiv 2606.15834 v2) は、進化した方策が評価器の見ない負荷で元より悪くなる弱点を
差分検査で探し、取引 scheduling の改善が 49% から 3.9% に下がった。どちらも「最適化圧力は評価器の穴を突く」という izanagi の規律 2 の前提 (reward hacking) の外部実例である。

## 2. 表から言えること

1. **学習・自動化で CC を特化する先行 (Polyjuice・NeurCC・ATCC・CormCC・ACC・Callas) は、どれも「正しさを固定の骨格に置き、骨格の上の方策の値か、
   既存 CC 部品の割付けを探す」構成である。** 検証の方式・版管理・commit 時の lock の順序・GC は、どれも探索空間の外にある (各行の「範囲の外」)。
2. **LLM がコードを生成する先行 (ADRS・2604.06566・Bespoke OLAP・Vulcan) は、取引の並行性制御の判断を対象にしていない。** ADRS の取引 scheduling は
   順序だけを返し、競合時の判断は模擬器に固定で、直列化可能性の検査も無い。2604.06566 は並行性制御を「未解決の課題」と明言し、
   厳密な正しさ検査が要ると書く。
3. **本 wave の読んだ範囲では、LLM が取引の並行性制御の判断を実装するコードを生成し、取引処理の性能を評価した研究は見つからなかった。**
   これは R1・R3・R4 (補助探索 26 本の検索語、子の報告に時刻つきで記録) の範囲の記述で、世界の不在の主張 (N4) は索引検索 (R2) の判定が済むまで書かない。

## 3. 表現範囲の外にあり、izanagi の関数単位の合成なら作れる仕組みの型 (N3)

「作れる」は「hook を開ければ、LLM がその口の関数を書ける」の意味であり、**今の izanagi の hook がその型を開いているか**を別の列に書く。
「手作りの既知機構」は md_2 のカード集合 (295 枚 / 49 本) の範囲で、同じ型の人が設計した機構があるかを書く (世界の不在ではない)。

| 型 | 先行研究の範囲の外である理由 | 今の izanagi の hook | 手作りの既知機構 (md_2 のカード集合の範囲) |
|---|---|---|---|
| T1 commit 時の lock の取得順 | Polyjuice・NeurCC・ATCC は commit 時の手順を骨格に固定。組み合わせ系は部品の中身を変えない | **開いている**: 段 A の施錠順の軸 (`silo_lock_order_api.hh`、TID word から優先度を返す) | Cicada の競合度順の施錠 (Cicada Table 2 の No-sort) |
| T2 validation の方式 (何を・どの順で・どこまで検証するか) | 上と同じ (最終検証は骨格) | 閉じている | BCC (false abort の削減)、TicToc (timestamp の後付け)、SGT |
| T3 実行前の取引の並べ替え・worker への寄せ | NeurCC §3.3 が「事前スケジューリングは範囲外」と明記。Polyjuice も枠組みの外。ADRS は順序を返すが abort・待ちの判断を持たず、直列化検査も無い | 閉じている | TsDefer (TsKD)、Ding 2018 の thread-aware reordering、Strife |
| T4 版の管理・GC・読む版の選択 | 学習系はいずれも MVCC を持たないか、読める版が 2 つに固定 | 閉じている (VHash は別 manager の担当で本 wave の scope 外) | Cicada、HANA の Hybrid GC、Steam、vDriver |
| T5 待ち・abort・backoff の判断の関数 | **範囲の内側と重なる**: NeurCC は timeout (0 = 即 abort、∞ = block) と取引型ごとの backoff を学習し、Polyjuice は backoff 表を学習する。違いは表現 (izanagi は worker 内に状態を持つ任意の関数、先行は離散化した表) だけ | **開いている**: Silo の関数方策 (abort 後の待ち・施錠衝突で待つか abort か・commit 通知、観測は abort 要因・試行番号・乱数) と MOCC 版 (待ち方だけ) | 静的・指数 backoff (STOv2 §4.2)、上限つき施錠待ち (Abyss §4.2・STOv2 §4.6) |
| T6 上の型の組み合わせ (1 つの取引処理の中で順序・検証・待ちを連動させる関数) | 学習系は各動作を独立の表の列として持つ。部品の組み合わせ系は部品の中身に入らない | 閉じている (hook は軸ごとに独立) | 特定の組み合わせを設計した手作りの CC は多い (IC3・DRP など) |

**正直な読み:** 今の izanagi が開いている hook は T1 と T5 だけである。T5 は学習型 CC の表現範囲と重なり、観測はむしろ先行より少ない
(取引型・アクセス位置・ホットさを見ない)。T1 は学習型 CC の範囲の外だが、手作りの既知機構 (Cicada の競合度順の施錠) が同じ型にある。
**したがって、今の hook のままでは「既存手法の表現範囲の外にある仕組み」を主張できる余地は T1 の一点に限られ、その T1 でも手作りの SOTA との差を示す必要がある。**
T2・T3・T4・T6 は先行研究の範囲の外にあるが、izanagi の hook も閉じている。gen-opt の新しさを「範囲の外の仕組みを自動で作った」に置くには、
これらの型の口を開けて (新しい hook と、その型に効く正しさ関門)、その条件の SOTA を上回ることを示す必要がある。
どの型がどの条件の無駄に効きそうかは、余地の測定の後に `README.md` の判定で書く。
