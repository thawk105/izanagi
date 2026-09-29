# 並行性制御の最適化の文献カード化と、段 A の試し候補 (2026-09-29)

- 目的: 多コア・インメモリの並行性制御 (CC) の論文から、個々の最適化を「前提・効果・実装」のカードにし、CCBench に既にあるもの / 無いものを分ける。
  段 A (文献にあるが CCBench に無い最適化を Silo に入れる試し) の候補を選び、段 B (文献に無い仕組み) の新しさを判定するときの既知集合の土台にする。
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_2.txt` と同 directory の `common.txt` (repo 外、並行 wave md_1〜md_4 の 2 本目)。
  背景の逐語と提案は同 directory の `user-verbatim.txt`・`proposal.md` (md_1 が repo へ写す)。
- 着手: 2026-09-29 (専用 handoff の作成 09:45 JST、検索の事前登録 09:47:35 JST)。入力 commit: `1887f56e46c9e43b94f02572fe13d9b16ba39e41` (local main)。CCBench の pin: `68106660686232781bca3be792a750d3e19d7a8a`。
- 実装・計測はしていない。計算ノードは使っていない。本文は日本語、原典の逐語だけ英語。

---

## 0. 結論

**本集合はカード 295 枚 (49 本の論文)。** 別に、登録の包含条件の外 (ディスク主体) だが読んだ参考カード 4 枚 (Freitag 2022) を `cards.json` に
`in_population: false` で残した (本集合の件数には数えない)。分類は次のとおり (件数の母集合は本集合 295 枚、分類の定義は §2)。

| 分類 | 件数 | 効果の 3 分類の内訳 (CPU cache / delay on conflict / version lifetime / 3 分類外) |
|---|---|---|
| CCBench にある (同じ機構が pin のどれかの CC にある) | 80 | 30 / 17 / 12 / 21 |
| CCBench に無いが Silo に入る見込み | 33 | 7 / 10 / 1 / 15 |
| 前提が合わず Silo に入らない | 182 | 30 / 36 / 28 / 88 |

**段 A の試し候補 — 登録した 4 条件 (§6.1) をすべて満たすのは、本集合 295 枚を判定した範囲では 2 つだけだった。**

1. **上限つきの施錠待ち** — commit 時の write lock が他者に取られていたら、すぐ abort せず上限つきで待ち、上限を超えたら abort する。
   根拠: Abyss §4.2・Fig. 5 (2PL の lock 待ちの timeout)、STOv2 §4.6 (bounded spinning を推奨)。どちらも OCC の commit 時の施錠での効果は示していない。
   CCBench の Silo は「即 abort」か「取得済みを全部外して上限なく取り直す」の 2 択で、上限つきで待つ経路は pin のどの CC にも無い (§5.1)。
2. **乱数つき指数 backoff** — abort 後の待ち幅を指数的に広げ、乱数で散らす。
   根拠: STOv2 §4.2・Fig. 4 (randomized exponential backoff を contention regulation の基準として推奨)。原典が指定するのはここまでで、
   「worker ごとの連続 abort 数で倍々にし、commit で縮める」は v1 の hook に載せるための実装案である。CCBench の `BACK_OFF` は全 worker 共有の 1 値を
   commit 数の勾配で ±100 µs 動かす山登りで、乱数も worker ごとの状態も無い (§5.1)。izanagi が済ませた「静的 backoff」(固定値の格子) とも別物である。

**3 つ目は見つからなかった (範囲: 本集合 295 枚を登録の 4 条件で判定した結果)。** 今の関数単位の空間 (v1) は abort 後の待ち・施錠衝突時の待ちか abort か・
commit 通知の 3 口しか開いておらず、観測も abort 要因・試行番号・乱数・worker 内の履歴に限られる。本集合のカードでこの形に収まったのは「待ち方」の 2 つだけだった。

**重要な注意: この 2 つは、関数方策ループが既に同じ形を書いている。** 段階 F の実 LLM 候補
(`output/insights/2026-09-27/t2865-silo-policy-stage-f/verbatim/e2e/coder-output-1.json`) は、連続 abort で待ち幅を倍々にして乱数で散らし commit で
縮める abort 後の待ちと、施錠衝突で 20 回まで小さく待ってから abort する施錠方策を組み合わせたもので、certified になっている。
したがって段 A を「文献の最適化を正しく入れられることを示す」試しにするなら、上の 2 つは**文献の名前つきの対照** (人が文献どおりに書いた方策) として
安く作れるが、LLM がこの空間で出す案とほぼ重なる。**段 A の本命は、空間を 1 段広げる別枠 (§6.3) にある**、というのが本 wave の見立てである。

**別枠 (空間を広げれば書ける、上位)** — 詳細と「何を広げるか」は §6.3。

| 順 | 最適化 | 広げるもの | 正しさ検査 | 原典の根拠 |
|---|---|---|---|---|
| 1 | 開始前の先送り (TsKD の TsDefer) / 衝突する取引を同じ worker に寄せる (Ding 2018 の thread-aware reordering) | 取引の予定 key 集合の観測と、開始前の口 (TsDefer は他 worker の実行中 key 集合という共有状態も) | CC 本体を変えないので今の検査器で見られる | TsDefer: §6.3・Fig. 5a、Ding: Fig. 23〜25 (YCSB で Silo 比) |
| 2 | BCC (false abort の削減、原典が Silo 上の実装) | validation、共有状態 (thread ごとの最新 TID・他 thread の read set 履歴)、tuple の書き手 thread の識別 | 条件付き (版順から依存辺を作ることが要る) | Fig. 5・Fig. 7 (TPC-W 風・TPC-C)、Fig. 9 (YCSB の 32 thread で OCC の 1.99 倍・2PL の 1.63 倍) |
| 3 | 競合度順の施錠 (Cicada) | 施錠順の比較に tuple の TID word (競合度の近似) を見せる | 見られる | Cicada Table 2 の No-sort |
| 4 | 年齢・優先度による待ちか abort か (Abyss の WAIT_DIE、Polaris) | lock 保持者の開始時刻や優先度 (tuple メタデータか共有状態) | 見られる / 条件付き | Abyss Fig. 9a (2PL の値)。Polaris は本文未取得 |

**横断の注意 (§7):** CCBench の YCSB は書き込みで値が実質変わらない (`include/ycsb.hh:128-143`)。値の一致で検証を通す型の最適化
(Transaction Healing の偽 invalidation 除去など) や STOv2 の commit-time updates は、この YCSB では効果が workload の作りの産物になる。
段 A の根拠にしない。正しさ関門の設計 (md_3) への申し送りでもある。

---

## 1. 何を確かめ、何を確かめていないか

| 確かめたこと | 確かめていないこと |
|---|---|
| 本集合 49 本の論文の「読んだ節」に書かれていること (本集合 295 枚のうち 291 枚は本文、Polaris の 3 枚は公開 source、One-shot GC の 1 枚は要旨だけ。各カードの `read_sections` と `not_read`) | 読んでいない節 (証明本体、評価の細部、関連研究の多く) に書かれていること |
| カードの英語の逐語が原典の抽出テキストに実在すること (読んだ子が機械照合。段 A の根拠の 3 か所 (STOv2 §4.2・§4.6、Abyss §4.2) は親が抽出テキストで再照合) | 図の軸目盛から読む数値 (抽出テキストに出ないので使っていない) |
| 「CCBench にある / 無い」を pin の実ソースで照合したこと (照合の子 3 本 + 親。`なし` には読んだ file と grep の語を `ccbench.searched` に残した) | 「無い」は CCBench の pin の中での不在 (内部の不在) であり、**世界の文献に無いことではない** |
| 段 A の 2 候補と横断の注意 (§7) に関わる CCBench の箇所は親が実ソースで直接確かめた (§5.1) | 照合の子が書いた行番号の全件 (抜き取りで 3 か所を見て 2 か所一致、1 か所は 1 行ずれ。行番号は ±数行ずれうる) |
| 検索の登録・実行・判定の全記録 (§8、`search-ledger.json`) | 索引の登録母集合検索 (`docs/related-work/README.md` 7.7.4 の RW3)。本 wave の索引検索は OpenAlex 1 索引の RW2 相当で、DBLP・arXiv は使っていない |
| 分類 (§2) は子 4 本 (opus) の一次判定に、親が「Silo に入る見込み」の全枚数を見直し、他から 8 枚を抜き取って検算し、段 6 の独立レビュー (§11) の所見で直したもの | 「前提が合わない」「CCBench にある」の全 262 枚の親による 1 枚ずつの見直し (抜き取りと、段 6 のレビューの抜き取り 21 枚のみ) |
| 性能の数値に表・図番号が付いていること (段 6 の所見 5 の後、全カードを機械走査して是正、§11) | 本文の値と表・図の値の一致の全件 (抽出テキストで読める範囲を抜き取りで照合) |
| 性能・正しさ | 本 wave は文献と source の読みだけで、どの最適化も実装・計測していない |

読み手への注意: 「CCBench に無い」は pin の source の中での記述であり、「文献に無い」「新しい」とは一切書いていない。
本 wave のカード集合に無い最適化について何かを言うときは「本 wave のカード集合に無い (範囲: §3 の R1〜R4)」とだけ言える。

---

## 2. 用語と判定の基準

- **効果の 3 分類:** CCBench 論文の分け方 — "CPU cache, delay on conflict, and version lifetime" (Abstract)。どれにも当てはまらないものは「3 分類外」。
  CCBench 以外の論文の最適化への当てはめは読んだ子の判断で、カードに根拠を書いた (`effect_category_note`)。
- **カードの種類 (`kind`):** `protocol-core` = protocol の中核機構、`optimization` = 中核に足す技法、`design-dimension` = 評価論文が比べた設計の軸。
- **分類 (`class`):**
  - `ccbench-present` (CCBench にある): 同じ機構が pin のどれかの CC の flag・関数・常時の実装にある。照合が「一部」でも要がある場合を含む。
    Silo に無いものは「Silo へ持ち込む移植候補」(§5.2)。
  - `absent-silo-feasible` (CCBench に無いが Silo に入る見込み): 単版 OCC の Silo の前提で入る見込みがある。迷ったらこちらに置き、足りない前提を `silo_prereq` に書いた。
  - `absent-prereq-mismatch` (前提が合わない): 多版・事前宣言・batch・partition・2PL の lock 表と dirty read・ディスク・HW・分散が要る、または
    YCSB の点読み・点書きで効きようがない (scan・列の分割・可換演算の型が要る)。
- **関数単位の空間 v1** (`orchestrator/campaign/silo_function_policy_api.hh`・`silo_function_policy_coder_spec.md`、設計 D2214):
  hook は abort 後の待ち時間 (上限 1000 µs)、commit 時の write lock 衝突での retry / abort と待ち時間 (1 回 50 µs、1 tuple 32 回まで)、commit 通知の 3 つ。
  観測できるのは abort 要因・同じ tuple での試行番号・乱数・worker ごとの持続状態 (16 field 以下) だけ。時刻・key・set の大きさ・他 worker の状態・
  tuple のメタデータは見えず、read の経路・validation・write phase・施錠の仕方そのものは開いていない。
  `function_space` 欄: `v1` / `extend:<足すもの>` / `n/a`。
- **今の検査器:** commit した取引の trace (各 read の key と読んだ版 = その版を書いた取引の commit TID、各 write、commit 順) から依存グラフを作り、
  G2 を含む閉路を探す (`docs/isolation-phenomena.md`)。見えないもの: abort した取引・未 commit の値の読み (G1a/G1b)、述語の phantom、
  trace の差し込み点を通らない読み書き。`verifier` 欄の値は `observable` (そのまま見られる、本集合で 76 枚)、`conditional:<条件>` (差し込み点を合わせれば、162 枚)、
  `not-observable:<理由>` (57 枚)。
- **本集合 (`in_population`):** 登録の包含条件 (§3) を満たす論文のカード。条件の外で読んだ参考カードは `false` とし、件数に数えない。

---

## 3. 母集合の作り方

経路・検索式・包含条件・読む順番・段 A の選定規則は、検索結果を見る前に登録した (`search-registration.md`、seal 2026-09-29T00:47:35Z)。
登録後の変更は同 file 末尾に追記した (改訂 1: 429 で無効になった 6 本の取り直し、改訂 2: 読む上限 45 本の撤廃、時刻の訂正 2 行)。

| 経路 | 中身 | カードにした論文 |
|---|---|---|
| R1 起点 | CCBench が実装する protocol の原典と CCBench 論文 | Silo、TicToc、MOCC、Cicada、ERMIA、SSN、Oze、Abyss (2PL 系の原典として)、CCBench (9 本。MVTO は原典 (Reed 1978) を読まず、MVCC 評価 2017 の設計次元カードで扱った) |
| R2 既存資料 | `cc-candidates-2026-09-17.md` の母集合内の行、VHash 文献調査で本文を読んだ CC の論文 | Rebirth-Retire、Bamboo、Polaris、Plor、Shirakami、IC3、Brook-2PL、Caracal、CormCC、Tebaldi、ESSN、Hekaton、HyPer、Steam、HANA GC、vDriver、LeanStore SI、BOHM、Lomet 2012、MV3C (20 本。Freitag 2022 は下の注) |
| R3 索引検索 | OpenAlex の題名・要旨検索 9 本 (§8) → venue 選別 → 判定 | 新規: HDCC、TsKD、AOCC、Ding 2018、BCC、VLL、Aria、Case for determinism、One-shot GC |
| R4 参考文献の追跡 | anchor 5 本 (CCBench、Abyss、STOv2、MVCC 評価 2017、Cicada) の参考文献の全件 | anchor 自身 (STOv2、MVCC 評価 2017) と新規: Transaction Healing、Doppel、PWV、No False Negatives、Strife、ACC、Orthrus、Deuteronomy の多版範囲 CC、Deferred Runtime Pipelining |

- 学習型 CC (Polyjuice、NeurCC、ATCC) は登録の理由コード `learn` で除外した。行動空間の各選択肢 (早期 validation、待ちなど) は他のカードが扱う。
- Freitag 2022 はディスク主体で、登録の包含条件 (1) (単一ノードの多コア・インメモリ) の外である。VHash 調査の読書対象だったので読んだが、
  4 枚は `in_population: false` の参考カードとし、本集合の件数 (295 枚・49 本) に数えない (段 6 の所見 4 で直した。初版は 299 枚・50 本と数えていた)。
- 論文単位の版の注意 (掲載版でなく preprint・技術報告を読んだもの) は §10 と各カードの `paper.title` にある。

---

## 4. 集計

いずれも本集合 295 枚の値。

- 効果の 3 分類: CPU cache 67、delay on conflict 63、version lifetime 41、3 分類外 124。3 分類外が多いのは、abort の削減・順序付け・
  事前解析・一括処理の技法が「待ち」でも「cache」でも「版の寿命」でもないためである (例: BCC、Healing、IC3、決定論 CC)。
- 事前宣言・静的解析・batch を要するカード (`requires_predeclared_sets`): true 78、false 185、不明 32 (評価論文の設計次元など)。
- CCBench 照合 (`ccbench.presence`): あり 54、一部 96、なし 145。

---

## 5. 分類ごとの要点

### 5.1 段 A の 2 候補に関わる CCBench の事実 (親が実ソースで確認)

- **backoff:** 全 protocol の abort 後の待ちは `include/backoff.hh` の `Backoff::backoff` 1 つで、全 worker 共有の `Backoff_` (atomic double) を
  leader が 10 µs ごとに commit 数の勾配で ±100 µs (0〜1000 µs) 動かす。乱数・worker ごとの状態・指数は無い。
  `cmake/Options.cmake:20` の説明文は "exponential backoff on abort" だが、実装は指数ではない (説明と実装の食い違い)。
  CCBench 論文 §6.2 もこの方式を "AdaptiveBackoff uses only global information across all worker threads" と書く。
- **施錠衝突:** Silo (`cc/silo/transaction.cc` の `lockWriteSet`) は `NO_WAIT_LOCKING_IN_VALIDATION=1` (既定) で即 abort、`NO_WAIT_OF_TICTOC=1` で
  取得済みを全部外して最初から取り直す (上限なし)。TicToc は両方 0 で lock word を読み直して上限なく待つ。ss2pl の `DLR0` は
  `cc/ss2pl/README.md:43` が "Dead lock resolution is timeout" と書くが、実装 (`include/rwlock.hh` の `r_lock`・`w_lock`) は上限なしで回るだけで
  timeout は無く、既定 build は `DLR1` (no-wait) だけを定義する。MOCC の `LOCK_TIMEOUT_US` (`cc/mocc/include/lock.hh:10`) は定義だけで使われていない。
  **上限つきで待ってから abort する経路は pin のどの CC にも無い。**

### 5.2 CCBench にある (80 枚) — Silo に無いもの (移植候補) の主なもの

80 枚のうち 54 枚は Silo に無い (`ccbench.in_silo` = なし)。Silo へ持ち込む候補として目立つのは次のとおり (いずれも段 A の条件 (a) は満たさない)。

- MOCC: 温度による選択的な悲観 lock、abort 後の RLL (次の試行で先に lock を取る)、温度の epoch つき reset。
- Cicada: 版の設置前に write set 側の版を調べる早期検査 (`precheckInValidation`)、commit が続く record では検査を省く適応、abort 後の時計の前進 (clock boost)。
- (TicToc の preemptive abort は CCBench には read 中に lock を見たときだけの一部しか無く、論文の「施錠前に read set を調べる」形は無い。
  親は初版で「CCBench にある」へ訂正したが、段 6 の所見 3 で取り消し、「Silo に入る見込み (validation を開く拡張)」に戻した。)
- D2PL の sort 済み一括施錠 (Orthrus の計画的な施錠に当たる)。

### 5.3 CCBench に無いが Silo に入る見込み (33 枚)

`function_space` が `v1` なのは 2 枚 (上限つき施錠待ち = `abyss-lock-wait-timeout`、乱数つき指数 backoff = `stov2-basis-contention-regulation`)。
初版は `tcm-block-instead-of-abort` も v1 に数えていたが、TCM の block は timestamp 範囲が許す場合に限る判断で v1 の hook には載らないため、
段 6 の所見 2 で「前提が合わない」へ直した。残り 31 枚は拡張が要る。うち 5 枚 (Silo の inline record・NUMA allocator、
Abyss の thread ごとの malloc、STOv2 の hash 索引・取引内部の hash 表) は CC の機構でなく実装上の要因である。

### 5.4 前提が合わない (182 枚) の主な理由

多版が要る (版の連結・GC・古い版の読み: MVCC 系エンジンと GC の論文のほぼ全件)、事前宣言・静的解析・batch が要る (IC3、BOHM、PWV、MV3C、
決定論 CC、Strife、Caracal、Tebaldi)、2PL の lock 表と未 commit 値の読みが要る (Bamboo、Rebirth-Retire、Plor の大半)、
YCSB の点読み・点書きで効きようがない (scan・述語・列の分割・可換演算: HyPer の述語系、STOv2 の timestamp splitting、Doppel)。

---

## 6. 段 A の試し候補

### 6.1 選定の規則 (登録どおり)

(a) CCBench の pin に無い (他 CC の flag・関数にも無い)、(b) 関数単位の空間 v1 で書ける見込みがある、(c) 今の検査器で正しさを見られる、
(d) 勝ちそうな workload を YCSB の既存パラメタで作れる。静的 backoff は除外。順位は (b) の見込みの強さ → 原典の性能根拠 → (d) の作りやすさ。
(b) だけを満たさないものは別枠とし、何を広げれば書けるかを添える。

### 6.2 本枠 (4 条件を満たす) — 2 つ

**1. 上限つきの施錠待ち (bounded wait、待ってから abort)**

- カード: `abyss-lock-wait-timeout` (Abyss §4.2・Fig. 5)、`stov2-basis-deadlock-avoidance` の bounded spinning の部分 (STOv2 §4.6)。
  関連: `ccbench-nowait-or-wait` (CCBench §6.1・Fig. 9a・Insight 3。Fig. 9a は 2PL-Wait と 2PL-NoWait の比較)。
  `tcm-block-instead-of-abort` (Lomet 2012) は timestamp 範囲による判断が要るので根拠に使わない (§5.3)。
- 原典の逐語: "We added a timeout threshold in the DBMS that causes the system to abort and restart any transaction that has been waiting for a lock
  for an amount of time greater than the threshold. We note that when timeout is zero, this algorithm is equivalent to NO_WAIT." (Abyss §4.2)、
  "we recommend bounded spinning for deadlock avoidance" (STOv2 §4.6)。
- (a) 無い (§5.1)。(b) v1 の施錠衝突 hook (retry と待ち時間、1 回 50 µs・1 tuple 32 回) がそのまま担う。Silo は write set を key 順に sort してから施錠するので、
  待っても deadlock しない。(c) 施錠と validation の条件を変えないので今の検査器で見られる。
  (d) 原典の傾向はどちらも 2PL の値である: 高競合 (Abyss は theta 0.8) で core 数が少ないと短い timeout が良い (Abyss Fig. 5)、取引が長いほど
  2PL-Wait が 2PL-NoWait を上回り始める (CCBench Fig. 9a)。同じ CCBench §6.1 は、Silo では NoWait が元の Silo を上回ると書く (Fig. 10c)。
  YCSB の zipf skew 0.8〜0.99・max_ope を大きく・rratio 0.5 前後・thread 数を振る workload は作れるが、Silo の commit 時の施錠待ちがそこで有利かは未測定。
- 限界: 根拠の値はすべて 2PL の実行中の lock 待ちで、OCC の commit 時の施錠での効果は原典のどれも示していない。

**2. 乱数つき指数 backoff (v1 では worker ごとの状態で実装する案)**

- カード: `stov2-basis-contention-regulation` (STOv2 §4.2・Fig. 4)。関連: `ccbench-adaptive-backoff` (CCBench §4.1・Fig. 2c、全体共有の山登り)。
- 原典の逐語: "We recommend randomized exponential backoff as a baseline for contention regulation. This is not optimal at all contention levels –
  under medium contention, it can cause some idleness" (STOv2 §4.2)。同じ節は、元の Silo の実装は設定で指数 backoff を持つが既定で無効だと書く
  ("Silo supports exponential backoff through configuration")。
- (a) 無い (§5.1)。(b) v1 の abort hook で書ける。原典が指定するのは randomized exponential backoff までで、「連続 abort 数を worker 状態に持ち、
  commit hook で戻す」は v1 に載せるための実装案である。(c) 待つだけなので見られる。
  (d) 効果の根拠は Fig. 4 の "No contention regulation" の線 (backoff 無しは高競合で性能の揺れと崩壊を招く、数値は本文に無い)。YCSB の zipf 0.99・
  rmw あり・thread 数最大で作れる見込み。中程度の競合では遊休を招く (原典の限定)。
- CCBench の全体共有の山登りとの違い: 山登りは全 worker に同じ待ち時間を課し、worker ごとの競合の違いを区別しない。

**3 つ目は見つからなかった (範囲: 本集合 295 枚)。** v1 に収まる他の案 (abort 要因ごとに待ちを変える等) は izanagi の既存軸 (trigger-gating) で、
本集合に文献の最適化としてのカードは無かった。

**本枠 2 つの位置づけ:** 関数方策ループの段階 F の LLM 候補が両方を組み合わせた形を既に書き、certified、同じ job の stock との比 2.80 (1 回の観測、
`output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md` §0 項 6。比較の主張ではない)。段 A でこの 2 つを使うなら、文献どおりに人が書いた
名前つきの方策を対照に置き、LLM の方策・stock と同じ動作点で比べる安い試しになる。

### 6.3 別枠 — 空間を広げれば書ける (順位つき)

順位は、(1) 正しさの防壁 (validation・施錠の機構) を開かずに済むか、(2) 原典の性能根拠、(3) YCSB での作りやすさの順で付けた。

1. **開始前の先送り・同じ worker への寄せ** (`tskd-tsdefer-proactive-deferment`・`tskd-tsdefer-lockfree-probing`、`ding-thread-aware-reordering`)
   - 何を広げるか: 取引の予定 key 集合を方策に見せる口と、取引を始める前の口 (いつ・どの worker で始めるか)。TsDefer は他 worker の実行中 key 集合
     (共有状態) も要る。Ding は取引を束ねて worker に配る入口 (driver) が要る。
   - CC 本体 (Silo) は変えないので、今の検査器で見られる。予定集合が誤っても正しさは Silo が守る。
   - 根拠: TsDefer は YCSB 高競合で throughput を上げ retry を減らす (TsKD §6.3・Fig. 5a)。Ding の thread-aware は YCSB (16 op/取引、read 50%・RMW 50%、
     skew 0.99) で Silo ほかとの比較 (Fig. 23〜25)。
   - 注意: 予定集合は CCBench の YCSB が実行前に作る操作列 (`include/ycsb.hh` の `makeProcedure`) から得られるが、対話型の取引では得られない。
     「実行前に key が分かる workload に限る」という限定が付く。共有状態の開放は設計 §3.4 の見送り (型 3・12・15 と liveness 崩しの経路) に当たる。
2. **BCC** (`bcc-essential-pattern-validation` ほか 3 枚、PVLDB 9(6) 2016。原典は Silo の拡張として実装)
   - 何を広げるか: validation、共有状態 (thread ごとの最新 TID の配列、他 thread の read set 履歴)、tuple の書き手 thread の識別 (TID word は 64 bit を使い切る)。
   - 検査器: 条件付き — read set が変わっても commit する取引が出るので、依存辺を版順から作ることが要る。
   - 根拠: TPC-W 風 DoCart で OCC に対し Fig. 5、TPC-C 50:50 で Fig. 7、YCSB の 32 thread で OCC の 1.99 倍・2PL の 1.63 倍 (Fig. 9、§6.2 本文の値)。
     低競合 TPC-C では OCC より低い (Fig. 4・Table 1)。(初版は TPC-C の 2PL 比 1.84 倍を YCSB の値と取り違えていた。段 6 の所見 1 で直した)
   - 注意: validation を開くことは、設計 (`output/insights/2026-09-21/silo-function-synthesis-space/README.md` §2.2) が前提に置く
     「意味の異なる CC 変異 20〜40 個での検出力測定 (P0)」に触れる。正しさ関門 (md_3) の設計と一緒に扱う候補である。
3. **競合度順の施錠** (`cicada-write-set-sort-by-contention`、Cicada Table 2 の No-sort)
   - 何を広げるか: 施錠順の比較に tuple の TID word (新しさ = 競合度の近似) を見せる。izanagi の sort-strategy 軸の比較 (79 値の IR) が見られるのは
     `storage_`・`key_`・`rcdptr_` だけなので、この軸の外である。Silo の既定の no-wait 施錠なら key 順から外しても deadlock しない
     (v1 の施錠待ちと組むと上限つき再試行の空転はありうる)。
   - CCBench の Cicada は key 順の部分 sort で、競合度順ではない (照合の記録)。
4. **年齢・優先度による待ちか abort か** (`abyss-wait-die`、Polaris 3 枚)
   - 何を広げるか: lock 保持者の開始時刻や優先度を施錠衝突 hook に見せる (TID word の空き bit か共有表)。Polaris は read の経路での予約も要る。
   - 根拠: Abyss Fig. 9a は 2PL の値。Polaris は本文未取得で性能の表・図番号を添えられない。

別枠の下位 (効果の根拠が薄い、または workload の作りの影響を受ける): STOv2 の commit-time updates (§7 の注意)、DRP (TPC-C と STAMP の根拠、
拡張が大きい)、NWR 系の non-visible write (原典は提案のみ)、ACC の競合推定 counter (それ単独では性能を変えない)。

### 6.4 段 A の起票に要る計算の見積り (本 wave では投入しない)

本 wave は計算ノードを使っていない。起票時の目安として、proposal の単価 (1 候補の評価が約 13 分 = 0.21〜0.22 node 時間、
`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/proposal.md`) を使うと、本枠 2 候補 × 文献どおりの方策 1 本ずつを stock と同じ job で比べる pair
(1 job で候補と stock の 2 評価) を workload 3 点で 1 回ずつ流すと、6 job × 2 評価 × 0.21〜0.22 ≈ 2.5〜2.6 node 時間 (試算。単価は proposal の値で、
本 wave では測っていない)。2 node 時間以上なのでユーザー確認の対象になる。

---

## 7. 横断で見つけた注意

- **CCBench の YCSB は書き込みで値が実質変わらない。** `include/ycsb.hh:128-143`: WRITE は新しく確保した YCSB 値をそのまま書き、RMW は旧値を
  `memcpy` で写して書く。値の一致で検証を通す技法 (`healing-false-invalidation-elimination`) はこの YCSB では read 検証の abort をほぼ全て消しうる (推論、未実測)。
  STOv2 の commit-time updates は updater が恒等写像になる。どちらも YCSB 上の効果が workload の作りの産物になりうるので、段 A の根拠にしない。
  LLM が値の一致を使う検証を書いた場合も同じ問題が起きる (規律 2 の報酬ハックの型)。正しさ関門 (md_3) への申し送り。
- **CCBench の説明と実装の食い違い (記録のみ、上流への還元は人間の判断):** `cmake/Options.cmake:20` の "exponential backoff on abort" (実装は指数でない)、
  `cc/ss2pl/README.md:43` の "Dead lock resolution is timeout" (実装に timeout は無い)、MOCC の `LOCK_TIMEOUT_US` は未使用、MOCC の `MQLOCK` 枝は既定で無効で
  照合の子は build できない見込みと書いた (未確認)、Oze の protocol 切替の判定関数は常に false を返す TODO、ERMIA の readers bitmap は `1 << thid_` が int 幅で
  32 thread を超えると bit が立たない疑い (照合の子の推測、未確認)。
- **Polaris の source の出所:** 読んだ子は第三者の fork (`ssya23/polaris`、2026-09-18 作成) から取っていた。親が原典 repo (`chenhao-ye/polaris`) の同じ 3 file を
  取り直し、SHA-256 の一致を確かめた (2026-09-29T01:14Z)。カードの所在は原典 repo に直した。

---

## 8. 検索の記録

- 索引: OpenAlex works API。`filter=title_and_abstract.search:<式>,publication_year:2008-2026`、`per-page=200`、cursor 終端まで。
  取得の成否は JSON の `meta.count` と `results` で判定した。生の応答本文は repo の外に置き、`search-ledger.json` に page ごとの SHA-256 と件数を置いた。
- 1 回目の走行 (09:49 JST) は Q01・Q02・Q04・Q05・Q06・Q08 が HTTP 429 で途中終了した。この 6 本は判定に使わず、同じ式を 2 回目 (要求間隔 5 秒) で取り直した。

| ID | 式 (title_and_abstract.search) | 有効な走行 | meta.count | distinct | venue 一致 |
|---|---|---|---|---|---|
| Q01 | "concurrency control" AND ("in-memory" OR "main-memory" OR "main memory") | run2 | 730 | 730 | 65 |
| Q02 | "concurrency control" AND (multicore OR "multi-core" OR "many-core" OR manycore) | run2 | 180 | 180 | 19 |
| Q03 | "optimistic concurrency control" AND (contention OR abort OR aborts OR validation) | run1 | 150 | 150 | 13 |
| Q04 | (multiversion OR "multi-version" OR MVCC) AND ("in-memory" OR "main-memory" OR "main memory") AND (transaction OR transactions) | run2 | 167 | 167 | 21 |
| Q05 | (transaction OR transactions) AND ("high contention" OR hotspot OR "hot records" OR contended) AND ("in-memory" OR "main-memory" OR multicore OR "multi-core") | run2 | 264 | 264 | 15 |
| Q06 | "concurrency control" AND ("garbage collection" OR "version management" OR "version chain") | run2 | 61 | 61 | 8 |
| Q07 | "concurrency control" AND (reordering OR batching OR "transaction scheduling" OR "transaction repair") | run1 | 159 | 159 | 18 |
| Q08 | "concurrency control" AND (timestamp OR timestamps) AND ("in-memory" OR "main-memory" OR multicore OR "multi-core") | run2 | 42 | 42 | 6 |
| Q09 | ("two-phase locking" OR 2PL OR "lock manager") AND ("in-memory" OR "main-memory" OR multicore OR "multi-core") | run1 | 81 | 81 | 10 |

- 9 本の和集合は distinct 1,309 件。venue 選別 (登録の正規表現) で一致 98 件、venue 外 861 件、venue 不明 350 件。
- venue 一致 98 件の判定: 検出 21、近傍 13、除外 64 (理由: other 18、nonvenue 15 (TKDE・VLDB Journal など同名の対象外誌)、dist 13、disk 10、hw 6、theory 1、bench 1)、要裁定 0。
  判定の根拠は題名 66 件・要旨 32 件。要旨で判定したのは、初回の 10 件 (題名で決められない 9 件と Diva) と、段 6 の所見 6 を受けて見直した 22 件
  (題名が 1 語だけ、または題名に除外理由の語が無いのに題名で除外・近傍にしていた行) である。見直しで判定が変わったのは 2 件
  (Lotus: 除外 dist → 近傍 (H-Store 系の partition 前提、分散か単一ノードかは要旨で確定できない)、G-tran: 理由 other → dist (RDMA の分散 graph DB)) と、
  理由だけが変わった 1 件 (unbundled な key 範囲施錠: dist → disk)。Diva は題名で検出としたが、要旨で PostgreSQL・MySQL (ディスク主体) への適用と分かり近傍へ直した。
  題名だけで判定した残り 66 件の内訳: 除外 44 件 (題名に除外理由の語 (graph・disaggregated・geo-replicated・NVM・LSM・flash・cracking など) があるか、
  対象外の同名誌)、検出 16 件 (R1〜R4 と重複する 12 本と、題名で検出としその後に本文を読んだ Aria・VLL・Case for determinism と、本文を取れず要旨だけ読んだ One-shot GC)、
  近傍 6 件 (TxnSails、LeanStore SI、Freitag 2022、Appuswamy 2017 の 2 つの work ID、PostgreSQL の SSI)。
- 限界 (偽陰性): venue 不明の 350 件は判定していない (SIGMOD の会議録は OpenAlex で年ごとに別 source に割れ、source の無い hit も多い)。題名・要旨の検索は
  語の違う論文を落とす。本 wave の主な発見経路は索引検索でなく R1・R2・R4 だった (R3 の新規は 9 本)。母集合の外: venue 本体の年次一覧、ACM DL、DBLP、
  arXiv、書籍、技術報告、学位論文、非英語文献、索引化されていない実装。
- R4 は anchor 5 本の参考文献を全件見た (CCBench 65 件、Cicada 67 件、MVCC 評価 2017 49 件、STOv2 58 件、Abyss 44 件)。追加した論文と、近いが包含条件の外
  (venue 外・disk・hw・分散) としたものは `search-ledger.json` の `r4_anchor_scan` にある。venue 外の近いものとして、STM の contention manager
  (Guerraoui ほか PODC 2005) と、timeout つきの queue lock (Scott・Scherer PPoPP 2001) がある。本枠 2 候補の近縁だが、登録の venue の外なのでカードにしていない。
- 要旨の取得は 34 件 (初回 12 件、段 6 の所見 6 の見直しで 22 件) で、うち 1 件 (vmcache、W4380433184) は work ID の打ち間違いで取った無関係の論文である (判定にもカードにも使っていない)。

---

## 9. 次の段への申し送り

- **段 A の起票:** 本枠 2 候補 (§6.2) は「文献どおりの名前つき方策」を対照として安く作れるが、LLM の方策 (段階 F) とほぼ重なる。文献の最適化を正しく
  入れられることを示す本命は別枠 1〜3 (§6.3) で、いずれも関数単位の空間の拡張 (予定 key 集合と開始前の口、validation と共有状態、施錠順の比較への TID) が要る。
  どの拡張を開くかは、正しさ関門 (md_3) の設計と roadmap の改訂 (md_1) に従属する。
- **段 B の既知集合:** `cards.json` の本集合 295 枚 (`in_population: true`) が「本 wave のカード集合」である。段 B で「新しい」を判定するときは、この集合を既知の土台にしつつ、
  `docs/related-work/README.md` 7.7 の手続き (検索式と主張の対応の事前登録、別 AI の反証) を別に行う。本 wave の集合は網羅でない (§8 の限界)。
- **YCSB の値の問題 (§7):** 段 A・段 B のどちらでも、値に依存する最適化を YCSB で評価する前に、workload の書き込み値を実際に変える必要がある (CCBench の改変になる)。

---

## 10. 書誌と取得記録

論文ごとの取得元 URL・取得時刻・SHA-256・読んだ節は `reading-notes/<班>.md` の冒頭表にある。PDF と抽出テキストは repo の外
(`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md2-literature-cards/src/` と `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/`) にある (生存保証なし)。

版の注意 (掲載版そのものを読んでいないもの): SSN は arXiv 1605.04292 v5 (VLDB Journal 版でない)、Oze は arXiv 2210.04179 の改題後の拡張版、
MV3C は arXiv v1 (2016、旧題)、IC3 は NYU 技術報告 TR2016-981、Strife は arXiv 1810.01997 v1 (2018、旧題)、Orthrus は arXiv 1512.06168 v3 (草稿)、
vDriver は技術報告版、Brook-2PL は arXiv v1 (DOI 未確認)、TsKD は Edinburgh の accepted version (DOI は ACM DL の URL と表紙で 10.1145/3588706 と
10.1145/3603164 が食い違う)、Polaris は論文本文なしで公開 source のみ、One-shot GC は要旨のみ、Diva は本文を取得できず近傍としてカードにしていない。

| 班 | 論文 | venue・年 | 所在 | 枚数 |
|---|---|---|---|---|
| A | Speedy Transactions in Multicore In-Memory Databases | SOSP 2013 (pp. 18-32) (2013) | DOI 10.1145/2517349.2522713 | 11 |
| A | TicToc: Time Traveling Optimistic Concurrency Control | SIGMOD 2016 (2016) | DOI 10.1145/2882903.2882935 | 6 |
| A | Mostly-Optimistic Concurrency Control for Highly Contended Dynamic Workloads on a Thousand Cores | PVLDB 10(2), pp. 49-59 (2016) | https://www.vldb.org/pvldb/vol10/p49-wang.pdf | 5 |
| A | An Analysis of Concurrency Control Protocols for In-Memory Databases with CCBench | PVLDB 13(13), pp. 3531-3544 (2020) | DOI 10.14778/3424573.3424575 | 15 |
| A | Staring into the Abyss: An Evaluation of Concurrency Control with One Thousand Cores | PVLDB 8(3), pp. 209-220 (2014) | https://www.vldb.org/pvldb/vol8/p209-yu.pdf | 18 |
| B | Cicada: Dependably Fast Multi-Core In-Memory Transactions | SIGMOD 2017 (2017) | DOI 10.1145/3035918.3064015 | 14 |
| B | ERMIA: Fast Memory-Optimized Database System for Heterogeneous Workloads | SIGMOD 2016 (2016) | DOI 10.1145/2882903.2882905 | 5 |
| B | Efficiently making (almost) any concurrency control mechanism serializable | The VLDB Journal 2017 (読んだ版は arXiv v5, 2017-05-04) (2017) | arXiv:1605.04292 | 8 |
| B | Oze: Decentralized Graph-based Concurrency Control for Long-running Update Transactions (Extended Version) | PVLDB 18 (arXiv 拡張版)。依頼文の題名 'Real-world Long Transactions on BoM Benchmark' は同論文の旧題 (2025) | arXiv:2210.04179 (v3) | 6 |
| B | An Empirical Evaluation of In-Memory Multi-Version Concurrency Control | PVLDB 10(7), 2017 (2017) | PVLDB Vol.10 No.7 pp.781-792 | 8 |
| C | High-Performance Concurrency Control Mechanisms for Main-Memory Databases | PVLDB 5(4) (2011) | DOI 10.14778/2095686.2095689 | 6 |
| C | Fast Serializable Multi-Version Concurrency Control for Main-Memory Database Systems | SIGMOD 2015 (2015) | DOI 10.1145/2723372.2749436 | 6 |
| C | Scalable Garbage Collection for In-Memory MVCC Systems | PVLDB 13(2) (2019) | DOI 10.14778/3364324.3364328 | 6 |
| C | Hybrid Garbage Collection for Multi-Version Concurrency Control in SAP HANA | SIGMOD 2016 (2016) | DOI 10.1145/2882903.2903734 | 7 |
| C | Long-lived Transactions Made Less Harmful [Technical Report] | SIGMOD 2020 (技術報告版を読んだ。camera-ready と本文が同一である保証はない) (2020) | https://github.com/hyu-scslab/vDriver/raw/master/vdriver_techreport.pdf | 5 |
| C | Scalable and Robust Snapshot Isolation for High-Performance Storage Engines | PVLDB 16(6) (2023) | DOI 10.14778/3583140.3583157 | 6 |
| C | Memory-Optimized Multi-Version Concurrency Control for Disk-Based Database Systems | PVLDB 15(11) (2022) | DOI 10.14778/3551793.3551832 | 4 (包含条件外の参考、本集合に数えない) |
| D | Releasing Locks As Early As You Can: Reducing Contention of Hotspots by Violating Two-Phase Locking (Extended Version) | SIGMOD 2021 (2021) | arXiv:2103.09906v1; DOI 10.1145/3448016.3457294 | 7 |
| D | Rebirth-Retire: A Concurrency Control Protocol Adaptable to Different Levels of Contention | PVLDB 18(9): 3162-3174 (2025) | DOI 10.14778/3746405.3746435 | 7 |
| D | Polaris: Enabling Transaction Priority in Optimistic Concurrency Control | SIGMOD 2023 (PACMMOD 1(1), Article 44) (2023) | DOI 10.1145/3588724 (本文 PDF は未取得。source: 原典 repo github.com/chenhao-ye/polaris (main) の README.md と concurrenc | 3 |
| D | Plor: General Transactions with Predictable, Low Tail Latency | SIGMOD 2022 (2022) | DOI 10.1145/3514221.3517879 | 6 |
| D | Opportunities for Optimism in Contended Main-Memory Multicore Transactions | PVLDB 13(5): 629-642 (2020) | DOI 10.14778/3377369.3377373 | 9 |
| D | Shirakami: A Hybrid Concurrency Control Protocol for Tsurugi Relational Database System | arXiv preprint (v3, 2 Jul 2026 の版を読んだ) (2026) | arXiv:2303.18142v3 | 9 |
| E | Repairing Conflicts among MVCC Transactions (MV3C の arXiv v1 版。SIGMOD 2017 版 'Transaction Repair for Multi-Version Concurrency Control' の本文は未取得) | arXiv preprint (cs.DB) (2016) | arXiv:1603.00542v1 | 4 |
| E | Transaction Healing: Scaling Optimistic Concurrency Control on Multicores | SIGMOD 2016 (2016) | DOI 10.1145/2882903.2915202 (取得元 https://www.comp.nus.edu.sg/~chancy/sigmod16-occ-healing.pdf) | 5 |
| E | Scaling Multicore Databases via Constrained Parallel Execution | SIGMOD 2016 (読んだ版は NYU Technical Report TR2016-981) (2016) | DOI 10.1145/2882903.2882934 / https://cs.nyu.edu/media/publications/TR2016-981.pdf | 5 |
| E | Phase Reconciliation for Contended In-Memory Transactions | OSDI 2014 (2014) | https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-narula.pdf | 4 |
| E | Rethinking serializable multiversion concurrency control | PVLDB 8(11) (2015) | PVLDB Vol. 8, No. 11, pp. 1190-1201 (bohm-pvldb2015.pdf) | 5 |
| E | Multi-Version Concurrency via Timestamp Range Conflict Management | ICDE 2012 (2012) | lomet2012.pdf (IEEE ICDE 2012) | 4 |
| E | High Performance Transactions via Early Write Visibility | PVLDB 10(5) (2017) | PVLDB Vol. 10, No. 5, pp. 613-624 (https://www.vldb.org/pvldb/vol10/p613-faleiro.pdf) | 3 |
| F | BCC: Reducing False Aborts in Optimistic Concurrency Control with Low Cost for In-Memory Databases | PVLDB 9(6) (2016) | DOI 10.14778/2904121.2904126; http://www.vldb.org/pvldb/vol9/p504-yuan.pdf | 5 |
| F | Adaptive Optimistic Concurrency Control for Heterogeneous Workloads | PVLDB 12(5) (2019) | DOI 10.14778/3303753.3303763; http://www.vldb.org/pvldb/vol12/p584-guo.pdf | 5 |
| F | Improving Optimistic Concurrency Control Through Transaction Batching and Operation Reordering | PVLDB 12(2) (2018) | DOI 10.14778/3282495.3282502; http://www.vldb.org/pvldb/vol12/p169-ding.pdf | 6 |
| F | Transaction Scheduling: From Conflicts to Runtime Conflicts | Proc. ACM Manag. Data 1(1), art. 26 (SIGMOD 2023); Edinburgh peer-reviewed (accepted) version (2023) | DOI 10.1145/3588706 (ACM DL URL); the Edinburgh copy prints DOI 10.1145/3603164; https://www.pure.ed.ac.uk/ws/ | 3 |
| F | A Hybrid Approach to Integrating Deterministic and Non-deterministic Concurrency Control in Database Systems | PVLDB 18(5) (2025) | DOI 10.14778/3718057.3718066; http://www.vldb.org/pvldb/vol18/p1376-lu.pdf | 7 |
| G | Aria: A Fast and Practical Deterministic OLTP Database | PVLDB 13(11):2047-2060 (2020) | https://doi.org/10.14778/3407790.3407808 | 3 |
| G | Lightweight Locking for Main Memory Database Systems | PVLDB 6(2) (2012) | https://www.vldb.org/pvldb/vol6/p145-ren.pdf | 2 |
| G | The Case for Determinism in Database Systems | PVLDB 3(1) (2010) | https://www.cs.umd.edu/~abadi/papers/determinism-vldb10.pdf | 2 |
| H | No False Negatives: Accepting All Useful Schedules in a Fast Serializable Many-Core System | ICDE 2019 (2019) | doi:10.1109/ICDE.2019.00071 (PDF: https://db.in.tum.de/~durner/papers/no-false-negatives-icde19.pdf) | 7 |
| H | Improving High Contention OLTP Performance via Transaction Scheduling (arXiv 版。SIGMOD 2020 掲載版 'Handling Highly Contended OLTP Workloads Using Fast Dynamic Partitioning' の 2018 年プレプリント v1。掲載版そのものは未取得) | arXiv:1810.01997v1 (SIGMOD 2020 の前身稿) (2018) | arXiv:1810.01997v1 | 5 |
| H | Adaptive Concurrency Control: Despite the Looking Glass, One Concurrency Control Does Not Fit All | CIDR 2017 (2017) | https://www.cidrdb.org/cidr2017/papers/p63-tang-cidr17.pdf | 4 |
| H | Design Principles for Scaling Multi-core OLTP Under High Contention (arXiv 版 v3。脚注に 'draft of work accepted to appear at SIGMOD 2016' とある。掲載版そのものは未取得) | SIGMOD 2016 (arXiv 草稿 v3) (2016) | arXiv:1512.06168v3 | 5 |
| H | Multi-Version Range Concurrency Control in Deuteronomy | PVLDB 8(13):2146-2157 (2015) | doi:10.14778/2831360.2831368 (PDF: https://vldb.org/pvldb/vol8/p2146-levandoski.pdf) | 5 |
| I | Brook-2PL: Tolerating High Contention Workloads with A Deadlock-Free Two-Phase Locking Protocol | arXiv v1 (2025-08-26); 本文の書式は SIGMOD '26 (依頼文では PACMMOD、DOI 10.1145/3769767 とされる。この DOI は取得した v1 PDF からは確かめられない) (2025) | arXiv:2508.18576 | 5 |
| I | Caracal: Contention Management with Deterministic Concurrency Control | SOSP 2021 (2021) | DOI 10.1145/3477132.3483591 | 7 |
| I | Toward Coordination-free and Reconfigurable Mixed Concurrency Control | USENIX ATC 2018 (2018) | https://www.usenix.org/conference/atc18/presentation/tang | 3 |
| I | Bringing Modular Concurrency Control to the Next Level | SIGMOD 2017 (2017) | DOI 10.1145/3035918.3064031 | 6 |
| I | Extended Serial Safety Net: A Refined Serializability Criterion for Multiversion Concurrency Control | arXiv v1 (2025-11-28) (2025) | arXiv:2511.22956 | 5 |
| J | Deferred Runtime Pipelining for contentious multicore software transactions | EuroSys 2019 (2019) | doi:10.1145/3302424.3303966 | 6 |
| P | One-shot Garbage Collection for In-memory OLTP through Temporality-aware Version Storage | SIGMOD 2023 (PACMMOD 1(1)) (2023) | DOI 10.1145/3588699 | 1 |

---

## 11. 段 6 の独立レビューと訂正

read-only の Codex レビュー 1 本 (2 レンズ: 一次資料との照合 / CCBench の有無・分類・段 A の選定) が NO-GO で所見 8 件 (must-fix 6・should-fix 2) を出し、
親は全件を real と裁定して直した。レビューは件数 (カード・分類・効果・presence・verifier・R3・Q01〜Q09) を再計算して一致を確かめ、段 A の 2 機構の
CCBench での不在も pin の source で支持した。

| # | 所見 | 裁定 | 直したもの |
|---|---|---|---|
| 1 | BCC の「YCSB で 2PL 比 1.84 倍」は TPC-C の値。YCSB は Fig. 9 で OCC 比 1.99 倍・2PL 比 1.63 倍 | real (原典の写しで確認) | `bcc-essential-pattern-validation` の効果欄と段 A 注記、§0・§6.3 |
| 2 | TCM の block を v1 の単純な待ちとして扱っていた | real | `tcm-block-instead-of-abort` を「前提が合わない」へ。v1 は 2 枚、§5.3・§6.2 |
| 3 | TicToc の preemptive abort の「CCBench にある」への親の訂正は粗い | real (Cicada の precheck は write set 側で、施錠前の read set 検査ではないことを親が source で確認) | 親の訂正を取り消し「Silo に入る見込み」へ、§5.2 |
| 4 | Freitag 2022 (ディスク主体) は登録の包含条件の外 | real | 4 枚を `in_population: false` にし、本集合を 295 枚・49 本に、§0・§3・§4 の件数 |
| 5 | 表・図番号の無い性能の数値がカードに残る | real | 全カードの欄を機械走査して、数値を含み同じ文に表・図番号の無い 103 文を拾い、1 文ずつ原典で判定した (opus の子、親が検算): 設計の定数・実験条件 38 文は変えない、同じ欄の番号が出典と確かめられた 9 文は変えない、表・図番号を足した 19 文、数値を外して定性的に書いた 37 文。あわせて原典と食い違っていた 3 欄 (SSN の実験条件、Strife の節番号 2 か所) と、HyPer の値の出典の誤り (Fig. 10 でなく §4.4 本文の測定) を直した。Strife のもう 1 欄 (`strife-spot-stage`) は、2 段組の抽出で節の境界を確定できないため「§4.6〜§4.7」と幅を持たせた。是正後の再走査で残る 48 文は、設計の定数・実験条件と確認済みの番号の文である |
| 6 | 題名だけでは決められない R3 の除外がある (idx 90・59・97 ほか) | real | 同型の 22 件を要旨で判定し直した (§8)。判定の変化 2 件・理由の変化 1 件 |
| 7 | 施錠待ちの根拠 (CCBench Fig. 9a) は 2PL の比較で、Silo では NoWait が有利 (Fig. 10c) | real | §0・§6.2 に 2PL の値であることと、Silo での有利さは未測定と明記 |
| 8 | 「3 つ目は無い」の範囲と、backoff の「worker ごと・commit で縮める」が原典の指定か実装案か | real | 範囲 (本集合 295 枚を登録の 4 条件で判定した結果) を同じ文に置き、実装案であることを明記 |

---

## 付属ファイル

| file | 中身 |
|---|---|
| `cards.json` | カード 299 枚 (本集合 295 枚 + 包含条件外の参考 4 枚、`in_population` で区別) の正本 (機械可読)。原典から取った欄、CCBench 照合 (`ccbench`)、分類 (`class`・`silo_prereq`・`function_space`・`verifier`・`stage_a_notes`)。親が直した欄は `parent_override` に列挙 |
| `cards.csv` | cards.json と同じ中身の表 (1 行 1 枚) |
| `cards.md` | 人が読む表 (分類ごと、列を絞ったもの) |
| `search-registration.md` | 検索の事前登録の逐語 (改訂・訂正は末尾に追記)。`registration-seal.txt` は登録時の時刻と SHA-256 |
| `search-ledger.json` | 検索の実行記録 (走行ごとの件数・page の SHA-256・429 の記録、venue 選別、R3 の判定 98 件、要旨の取得、R4 の走査、hit 1,309 件の一覧) |
| `reading-notes/` | 原典を読んだ子 10 本のメモ (取得元・SHA-256・読んだ節・カードにしなかった候補) |

作業の script (取得・統合・判定の書き出し) は repo の外 `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md2-literature-cards/` にある。
