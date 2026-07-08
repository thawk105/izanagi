# Izanagi ロードマップ — 全設計と理由

**版: v1 (初期設計)。** 本ドキュメントは生きた文書であり、試行錯誤の発見に応じて Claude が改訂してよい (改訂規律は CLAUDE.md の「roadmap の更新」参照)。過去の版は docs/roadmap-history/ に凍結保存されており、設計仮説の変遷そのものが研究記録 (論文の方法論セクションの原料) になる。

このドキュメントは、本システムの設計のすべてとその理由を記録する。次の作業者 (人間または Claude) が、設計に至った議論を見ていなくても「なぜこうなっているか」を完全に追えることを目的とする。

**専門用語につまずいたら `docs/glossary.md` (用語集) を引く。** docs は並行性制御・探索理論・統計・本プロジェクト固有の機構にまたがる用語を、多くは説明なしに使う。用語集はそれらを専門外の読み手向けに平易に定義する。

**読み方 (ブートコスト規律、D35):** 全文必読は「Phase の初回セッション」と「roadmap を改訂するとき」のみ。日常セッションでは、現行タスクが参照する節だけを節名 (§) で引く — 全文を毎セッション読み込むのは §3.8 のコンテキスト衛生 (生データでなくダイジェスト) に反する。関連研究 (§7) は `docs/related-work.md` に分離してある。

---

## 1. 究極のゴール

**CCBench を使って、AI が特定ワークロードに特化した CC を自動生成するシステム。**

入力はワークロード仕様。AI が:
1. CCBench を解析し、入力ワークロードに最適なベース CC を選定する (選定・測定のループを回しうる)
2. ベース CC に対し、他の CC 実装を解析して付加できそうな最適化を持ってきて、測定・取捨選択する
3. ベース CC に対する variant が複数でき、それらを比較して最終的に1つを選ぶ

最終成果物は3つ:
- **新しい CC** (既存 CC + 引っ張ってきた最適化)
- **なぜそれが選ばれたかの理由**
- **どれをやるとどうだったか、という試行錯誤の説明**

3番目 (説明可能性) が本システムの差別化の核心。Polyjuice/CCaaLF は policy table という数値の塊を出すだけで「なぜこの CC が速いか」を言語で説明できない。Izanagi は試行ログから因果込みのレポートを生成する。

---

## 2. 三層アーキテクチャ

```
ワークロード入力 (spec cards)
   ↓
層1: ベースCC選定ループ
   CCBench解析 → workload照合 → 軽量ベンチで確定
   ↓ ベースCC確定
層2: 最適化合成ループ (進化探索)
   変異軸合成/最適化抽出 → variant生成 → 評価(正しさ+性能) → 取捨選択
   ↑__据え置きの正しさゲートを壊す変異はreject__|
   ↓
層3: variant比較・選択
   Pareto front上で最終CCを決定
   ↓
最終成果物: 新CC + 理由 + 試行ログ
```

### 層1 — ベース CC 選定 (軽く作る)

ここに凝りすぎるのは罠。理由は2つ:
- 既存研究が強い (CormCC/ACC/Polyjuice が workload→CC選定を既にやっている)。LLM で再発明しても新規性が出ない
- 層2 の進化ループが十分強ければ、ベース CC が多少最適でなくても吸収される。AlphaEvolve 系の経験則として、初期個体の質より mutation operator と evaluator の質が支配的

実装方針: ヒューリスティック + 数回のベンチで十分。「read-heavy & low-contention → OCC系 (Silo/TicToc)、write-heavy & high-contention → 2PL系/MOCC、long-read混在 → MVCC系」程度のルールで初期個体を2-3個選び、軽くベンチして一番マシなものをシードにする。**複数シードから並列に進化させる方が良い** (island model)。

LLM を使うなら「選定ロジック」ではなく「なぜこの workload にこの CC か、を CCBench の insight を引用しながら説明させる」方。これは層3の説明生成の伏線になる。

### 層2 — 最適化合成ループ (心臓部。旧称「最適化移植ループ」— 移植 (b2) は拡張予約に降格、D32)

#### 最適化の粒度: まずパラメータ寄り、余力があればコード移植

3段階の選択肢がある:
- **(a) パラメータ粒度 (Polyjuice式)** — 最適化を事前定義フラグ/数値にする。LLM ほぼ不要、新規性低いがロバスト
- **(b) コード粒度 (AlphaEvolve式)** — CCBench 内の特定関数を `EVOLVE-BLOCK` で囲み LLM に diff を書かせる。新規性高い、本構想の本丸。**(b) の内側に 2 形態がある (順序は D32 で確定)**: **(b1) 空間外合成** = ベース CC の内側で、フラグ空間に無い新しい変異軸を critic の機序帰属から合成する (P2-4 backoff で実証済み)。**(b2) 移植** = 他 CC の最適化を持ち込む (未検証仮説)。Phase 3 の主実験は (b1) で行い、(b2) は主実験後の拡張として予約する (phase3.md 後続段 7)
- **(c) アルゴリズム粒度 (FunSearch式)** — ゼロから書かせる。自由度高すぎて正しさが崩壊。CC では非推奨

**決定: まず (a) を主軸。Phase 3 で (b) を足す — (b) の内側は (b1) 空間外合成が先、(b2) 移植は主実験後の拡張 (D32)。(c) はやらない。**

(a) を選ぶ利点 (本プロジェクトの状況で特に効く):
- パラメータ粒度なら生成 variant は「CCBench が元々持つ最適化フラグの組み合わせ」だから理屈上は全部正しいはず。これは trace verifier を検証するのに最高の環境 (Phase 1 のゴールと噛み合う)
- 探索空間が有限 (CCBench の最適化が主に on/off なら高々 2^7=128 + 連続パラメータ数個)。**初手は全探索すら可能**。全探索の最適と LLM 探索の到達速度を比較でき、論文の図になる (**この比較は P2-5 で実施済み = negative result。silo 8 の自明空間では誘導は機械的勾配 (貪欲) を超えず、deceptive 構造では貪欲より有意に有害。D21/D29。よって「論文の図」は『誘導が速い』ではなく『小空間ではフラグ探索が自明で価値は空間外の合成にある』という物語に転じた**)
- (a)→(b) の移行が自然。パラメータ探索で「invisible reads を on にすると効く」が分かった後、コード移植で「その実装そのものを別 CC 文脈に移植できるか」に進む (**実際に起きた移行は違う形だった** — 「効いたフラグの実装を移植」ではなく「フラグ空間の外の新軸を合成」(P2-4 backoff) として起きた。これが (b1) を先にする D32 の根拠)

#### 移植可能性の判定 (CCBench insight I5 への対策)

CCBench の著者は「異なる実装の混合は深い分析には不適切」(I5) と書いている。素朴に「MOCC のコードを Silo にコピペ」するとメタデータ構造の前提が違って壊れる。

対策: 最適化を「前提条件 + 効果 + 実装」の三つ組として抽象化する段階を噛ませる。LLM に各 CC の最適化を解析させてカード化:
```
最適化: invisible reads (Silo由来)
  前提: read set に version を記録する仕組みがある
  効果: read時の cache line 汚染を減らす (CPU cache軸)
  競合: TicToc の timestamp 管理と部分的に衝突
```
この「最適化カタログ化」は隠れた肝。層3の説明生成にもそのまま流用できる。CCBench 著者が最適化を「CPU cache / delay on conflict / version lifetime」の3カテゴリに既に整理しているので、これを LLM の prompt の制約に使える。

**着手時期 (D32):** カタログ化 + 移植 (b2) は Phase 3 の主実験 (空間外合成 b1、phase3.md 段 6) を完了した後の拡張として予約する (phase3.md 後続段 7)。一歩目はカタログ化の試作 1 枚で、移植の本格投資はその結果 (移植先で前提が満たせるか) で決める。カタログ化の成果物は移植を見送っても層3 の説明生成に流用できる。

#### 探索戦略

AlphaEvolve/CodeEvolve の island-based GA を借りるのが堅い。ただし CC は評価が高コスト (1 variant = 数十秒のベンチ)。緩和策:
- **low-fidelity proxy**: 本ベンチ前に短時間 (1-2秒) の軽量ベンチでスクリーニング
- **LLM に次の一手を考えさせる**: ランダム変異でなく、過去の試行結果をコンテキストに入れて「このワークロードでは delay-on-conflict 系が効いているから次は wait-die 系を試せ」と方向づけさせる。これが LLM-evolution の最大の強みで、ただの GA より遥かに少ない試行で収束しうる (**仮説。P2-5/D29 で列挙可能なフラグ空間では反証された** — leading indicators を機械集約した digest 勾配で回す貪欲が同水準に到達し、LLM 固有の付加は貪欲から統計的に分離できず、deceptive 構造では『自信ある早期停止』が負債になった。**LLM 誘導の実証済み価値は「少ない試行で収束」ではなく、指標を機序に帰属させフラグ空間の外に新しい変異軸を合成すること** = P2-4 backoff。空間を広げる (cicada/oze) までは誘導の優位を主張しない)

### 層3 — variant 比較・選択 + 説明生成 (差別化の決定打)

Polyjuice/CCaaLF が絶対に出せないのが「なぜ」の説明。Izanagi は層2で試行ログ (どの最適化を入れたら性能がどう動いたか) が全部残るので、LLM に食わせて因果込みのレポートを生成する:

> 「このワークロードは write-heavy かつ中コンテンション。ベースに MOCC を選んだ理由は [CCBench I3: wait/no-wait の有効性は状況依存]。そこに Silo の invisible reads を移植したところ12%向上 (理由: read-heavy phase での cache 汚染削減、I2と整合)。一方 TicToc の timestamp 最適化は移植したが3%悪化したため不採用 (理由: MOCC の temperature tracking と timestamp 管理が二重コストになった、I5の実例)」

(上の数値は narrative の例示。**実際の採否では §3.6 に従い、3% のような noise floor 以下の差は「差なし」に丸め、採否根拠にしてはいけない。** 12% のような差も中央値・CV・有意性を添えて初めて主張になる。)

これは単なるオマケでなく研究としての主張そのもの。「AI が CC を合成した」だけなら半分既存研究だが、「AI が CC を合成し、その設計判断を人間が検証可能な形で説明した」は新しい。

---

## 3. 評価器 (evaluator) の設計

evaluator が本システムの成否を分ける。AlphaEvolve/Jitskit/IDS すべてが「evaluator こそが損失関数であり、その質がすべてを決める」と言っている。

### 3.1 正しさ検証の階層化

数千 evaluation を回したいので、安いチェックで枝刈り → 中コストで実検証 → 高コストで形式的保証の段階構成にする。

- **Tier 0: 静的・構文チェック (μ秒)** — コンパイル通る、基本 trx 実行のスモーク。LLM は壊れたコードを平気で吐くので必須
- **Tier 1: トレース検証 (ミリ秒〜秒)** — CC特化の最重要パート。実行トレースを取り、後から serializability を検査。read/write 依存グラフを作って cycle 検出 (Adya の serialization graph)。YCSB の単純 read/write なら辺は ww/wr/rw の3種。**Serializable 狙いなら G2 (anti-dependency cycle) まで見る必要がある**。自前 mini-verifier で十分。既存ツール (Cobra/Elle) を繋ぐのは TPC-C のような複雑 trx まで見るとき
- **Tier 2: 既存OSS DBのテスト移植 (秒〜分)** — isolation level 固有の境界条件のカバー。PostgreSQL の isolation tests、Hermitage (Martin Kleppmann) など。「variant が宣言した isolation level で通るべき/落ちるべきテストの集合」を固定
- **Tier 3: 形式検証 (分〜時間)** — TLA+/TLC など。最終候補にだけ。**初期スコープ外** (理由は decisions.md 参照)

### 3.2 二相設計 (IDS式に格上げ)

- **開発相 (短時間 × 大量)** = 回帰検出。短い trace で cycle 検出、anomaly 出たら即 reject。確率的に見逃しはあってよい。「安く広く」。**ただし IDS の教訓により、最後にまとめて回すのでなく毎 iteration 回し、構造化フィードバックを LLM に返す**
- **検証相 (長時間 + 精査)** = 最終候補の保証。層3で選んだ1個 (数個) にだけ長時間 trace + 厳密検査。確率的に高い確信度まで上げる。「高く狭く」

確率的保証は「ランダム seed を変えて N回回して全部 cycle 無し → 信頼度 1-εⁿ」という素朴なもので十分。これは Jitskit の reward hack 対策 (seed を変えて複数 run) とも合致する。

### 3.3 観測者効果の分離 (最重要の計測規律)

正しさ検証用のトレース取得が、計測対象を歪める (Heisenbug 的構造)。対策:

- **trace-enabled build** (トレース口あり、正しさ専用、性能は見ない) と **trace-disabled build** (トレース口を `#ifdef` で完全に消す、性能専用) を分ける
- トレース取得をランタイムフラグにしない。`#ifdef TRACE` でコンパイル時にコードごと消す (false でも分岐予測ミス・命令キャッシュ汚染で性能に効くため)
- 性能比較は variant も baseline も trace-disabled で揃える
- メタデータは「CC本来 (アルゴリズムが要求する。性能比較に含める)」と「検証専用 (verifier にトレースを渡すためだけ。`#ifdef TRACE` で消す)」を区別。この2つを混ぜない
- perf は trace-disabled build に当てる
- ビルド等価性の機械検証: trace-enabled と trace-disabled でトレース有無が CC の意味論を変えていないことを機械確認する。**実装は当初案 (最終 DB 状態の一致比較) から変更**: Phase 1 タスク1 の **symbol 不在検査 (perf binary に trace コードが 1 byte も無い、`nm`)** の方が DB 状態一致より強い証明なので、DB-dump 計装は冗長と判断し未実装 (phase1.md タスク5a 節の判断記録参照)。Phase 3 では方針 A (D30) により、この機械確認が観測者効果分離の**一次防壁に昇格**し、symbol 不在に加えて **diff-of-diffs** (variant の TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と一致することを assert する「観測者効果の二重検査」。素の出力 diff は `#if TRACE` ガード領域で正当に食い違うため不成立と敵対検証で裁定済み) へ拡張済み (2026-07-04 実体化。`source_digest.assert_trace_diff_matches_head` を `buildcache.build` 出口の hit/fresh 両経路で発火、fails-closed)

### 3.4 reward hacking 対策 (Jitskit §3.2, Appendix B より)

LLM は最適化圧力の下で、書かれていない不変条件を破って性能を稼ぐ。CC 版で起きうるもの:
- 「検証用 trace が見ていないアクセスパターンでだけ正しい CC」を作る → 対策: seed を変えた複数 run で毎回検証
- 「導出可能な ground truth を突く」(値を保存せず再計算) → 対策: 値に再構成不可能なエントロピーを持たせる
- 「探索の自己崩壊」(これ以上は失敗すると恐れて最適化をやめる) → 対策: 探索ポリシー側で継続を促す

これらに対し:
1. **据え置きの正しさゲート** — 壊すと即 reject。「絶対壊しちゃダメ」(serializability anomaly検査、ACID基本) と「壊れていい」(プロトコル固有テスト、variant のキャラクタライズに使う) を分ける
2. **adversarial auditor** (Phase 3 で導入) — N iteration ごとに variant を監査、verifier が見逃した不変条件違反を見つけてテストを追加
3. **hooks による書き込み時防壁** (Phase 1 から薄く) — verifier 迂回・成果物への直接書き込みを機械的に弾く**最小の第二防壁**。**方針 A (D30) 以降、hooks は「唯一の防壁」ではない**: identity の honest さ (偽 cache hit / `#ifdef`) は source_digest の preprocess 後ハッシュ、観測者効果の分離は観測者効果の二重検査 (diff-of-diffs、§3.3) が**一次防壁**として担い、hook はテキスト検査の完全性に依存しない範囲 (堅牢なパス検査) に責務を絞る。2 巡の敵対検証で「テキスト検査に C++/shell の完全性を負わせる設計は原理的に破れる」と実証したため (規律5 と両立させる責務再配置)
4. **検証エージェントの入力側隔離** — 「導出可能な ground truth を突く」への入力側の対策として、正しさ検証エージェント (verifier) のコンテキストに性能数値や期待結果を一切混入させない。verifier は trace のみを入力とし、throughput 等の報告済み数値を受け取らない。これは verifier に専用書き込みツール (Edit/Write) を与えない出力側隔離 (Bash 経由は prompt 規律で禁止 — 完全なツール権限隔離ではない、audit-2026-06-30 §4) と対をなす入力側隔離で、「期待値をコピーして捏造する」経路を入力データレベルで断つ (ARA / 2604.24658 の anti-fabrication isolation、§7)

### 3.5 leading indicators (収束に必須)

Jitskit が実証: スカラーの throughput だけ渡すと探索は 8-12 iteration で停滞しランダム化する。leading indicator (lock contention / cache hit率 / I/O / memory帯域) を毎 iteration LLM に渡すことが収束に必須。「write-only は allocator contention で診断、read-heavy は cache hit率で診断」のように、どの指標が効くかは workload による。

**P2-5 の含意 (D29):** 指標が収束に必須であることは変わらないが、silo 8 の小空間では**指標を機械集約した digest 勾配 (貪欲、LLM なし) だけで同水準の収束に届いた**。つまり「指標を LLM に渡すこと」の価値と「指標を LLM に解釈させること」の価値は分けて考える必要がある — 前者は必須、後者 (LLM 固有の付加) は小空間では貪欲から分離できなかった。LLM 解釈の価値は、指標を**機序に帰属**させフラグ空間の外に新軸を合成する局面 (P2-4 backoff) で現れる。空間を広げる (cicada/oze) までは LLM 解釈の優位を主張しない。

これは「FlameGraph を見て many-core でヤバいか判断してほしい」という当初の直感の正式版。perf プロファイリングは有望な variant にだけ回す (二段構え: screening 通過 → profiling)。

### 3.6 測定の安定性 (measurement stability)

性能数値は「1 run の点」ではなく「**反復測定の分布**」として扱う。他ユーザー・他プロセス・温度スロットリング等の外乱は一晩の自動ループでは必ず混入するが、人間の「あれ?」は介在しない。だから**ばらつきの監視と再測定を実行時の気まぐれに委ねず、規律として明文化・自動化する**。これは絶対規律1 (観測者効果の分離) / §3.4 (reward hacking 対策) と同じ構造の汚染防止であり、reward hacking の鏡像 ——「**ノイズを最適化シグナルと誤認する**」—— への対策でもある。

**(1) 反復と要約.** 1 measurement = N 回反復 (初期値 N=5、calibration で調整)。各 run の冒頭は warmup として破棄し定常状態のみを採る (※現実装は ccbench の extime 一括計測に従属し warmup 分離なし — 意図的非対応、D28 参照)。報告は単一の throughput でなく **中央値 + 散布度 (変動係数 CV / IQR)** を必ず持つ。WAL (campaign スコープ `output/campaigns/<id>/runs/`。出力レイアウトと campaign 同一性は orchestrator-design.md / D13) には個々の run 値も残し、後から分布を再構成できるようにする。calibration/noise floor は入力非依存なので env スコープ `output/env/<env-tag>/` に置く。

**(2) 外れ値検出 → 自動再測定 (=「あれ?」の機械化).** 反復内の CV が閾値 (初期 5%) を超えたら「測定が外乱で歪んだ」とみなし**自動で測り直す**。再測定の前に Admission Control の静定確認 (load average 静定) を必ず通す。規定回数 (初期 3 ラウンド) 測っても CV が収束しなければ、その variant に **`unstable` フラグ**を付けて分布比較から除外し、insight に「測定不能」として記録する。沈黙して 1 点を採用してはいけない。

**(3) noise floor の実測.** 「この差は信じてよいか」の下限を勘で決めない。calibration フェーズで baseline を連続 N 回測って CV を実測し、それを **noise floor** として固定する (§4)。これは環境タグ (mac-devcontainer / linux-baremetal) ごとに持つ。Mac devcontainer は VM 越しで noise floor が大きく出るはずで、その数値自体が「ここでは性能比較するな」(D10) の定量的裏付けになる。

**(3') noise floor は用途で 2 種に分かれる (A2 で分離).** 「N 回測った CV」には測り方が 2 つあり、用途が違うので混同してはいけない:
- **within-run noise floor** = 1 セッション内で反復 (rep) を back-to-back に取った CV。これは「**その 1 測定の品質**」(外乱で歪んでいないか) の尺度で、(2) の自動再測定 (CV 超→測り直し→unstable) の品質ゲートに使う。
- **between-run noise floor** = **独立したセッション** (別 run、別ビルド、campaign の別時点) の代表値 (session-median) 間の CV。これは「**差が信用できるかの下限**」で、(4) の分布比較が「差なし」に丸める閾値 (compare の floor) に使う。
variant と baseline は決して同一セッションで測らない (別ビルド・別時点) ので、**採否の floor は within-run でなく between-run であるべき**。within-run はセッション内の warm cache・同一熱状態・同一周波数定常を共有するため run 間ドリフトを過小評価し、これを採否 floor に流用すると between-run ドリフト帯の差を「有意」と誤判定して**偽 faster** を出す。なお fresh な back-to-back セッションは cold-boot/温度/数時間ドリフトを含まない**下限**なので、確定する between-run floor は fresh 実測と cross-campaign の genuine データ (別時間窓の同一 genome 反復) を突き合わせ保守側 (最大) に採る。high-abort genome ほど run 間ドリフトが大きい (abort 率が分散源)。

**(4) 採否は点比較でなく分布比較.** variant vs baseline の優劣判定は単一値の大小でなく**分布の比較**で行う:
- 差が noise floor 以下なら「**差なし**」に丸める。層3 narrative の「3%悪化だから不採用」のような **noise floor 以下の差を採否根拠にしてはいけない** (3% はラップトップ/devcontainer ではほぼノイズ)
- noise floor を超える差については、信頼区間の重なり、または分布フリーな検定 (Mann-Whitney U 程度で十分) で有意性を判定する。重い統計機構は要らない。**ただし反復数が小さい (reps≈5) と MWU の弁別力は弱く、完全分離は常に p≈0.012 を返す** (within-run cluster が tight なため)。よって MWU は between-run 有意性検定ではなく within-run の分布重なりを弾く弱い sanity にすぎず、**主防壁は between-run floor 丸め (上記第1項)**。floor を僅かに超える差 (floor 〜 1.5×floor) は MWU が無力な帯なので、headline にする前に cross-run 再現で裏取りする (A2: compare が `near_floor` フラグを立てる)
- 層3 のレポートは差分値だけでなく **「N 回測定の中央値、CV、noise floor、有意か否か」** を添える。これは「なぜこの variant を採った/外した」の説明可能性 (本システムの差別化の核心) を統計的に裏打ちする。各主張をその根拠 (WAL の run 値) まで辿れる形で紐づける構造は、ARA の forensic binding (claim→code→evidence の proof chain) と同型 (§7・D12)

**(5) スコープ.** Phase 1 では (1)(3) を骨格として実装 (calibrator が noise floor を出し、ベンチが反復+中央値+CV を返す)。(2)(4) は性能採否が実際に走る Phase 2 で必須化する。Phase 1 は Mac devcontainer 中心で性能採否をしなかった (D10) ため (2)(4) は配線のみ用意し、Linux 実機 (Dell R760) 確保後の Phase 2 (A2) で有効化した — noise floor を within-run (品質ゲート) と between-run (採否 floor) に分離した上で (§3.6(3'))。

### 3.7 Phase 完了監査と引き継ぎ監査 (劣化の遡及検出)

§3.4 (reward hacking 対策) と §3.6 (測定の安定性) は「書き込み・評価の**その時点**で正しさ/測定を守る」前向きの層である。だがこのプロジェクトの履歴が示すように、AI が一度入れた作業は後から劣化が露呈しうる —— reward hacking の鏡像 (偽 faster: between-run でなく within-run floor を採否に流用した A2/D19)、consumer 取り残し (D23 src_token を loop が追従せず再評価冪等性 D を破った D25)、謳う保証が恒真な空証文 (online_digest の「二重の関所」D26)、計測汚染 (前セッションの孤児 livelock が read-heavy を 2.2x 歪めた)。これらは**入った時点でなく後から**捕まった。

棚卸しすると、こうした劣化の大半は既に体系的に捕まっている —— (a) 出荷前の敵対検証 (verify-the-verifier / STAGE2 レビュー)、(b) 別セッション作業物の独立裏取り (規律6)、(c) Phase 完了監査 (B→A) のいずれかで。穴は「捕まえる手段」でなく「**回す契機**」にある: 計測汚染だけは計測前の pgrep 目視でほぼ偶然に検出され、audit-2026-06-30 の 43 項目は別セッションで偶発的に監査されるまで蓄積した。Phase 境界・セッション引き継ぎという最も危険な瞬間に監査が発火する保証が規律化されていなかった。

→ **だから「Phase 完了時・別セッション/別 AI の作業物の取り込み時には、独立コンテキストのエージェントで敵対監査を回す」を方法論として固定する。** 監査の作法は実績がテンプレになる: 最悪モード (false-green / 規律違反 / over-claim) を集中攻撃し、各 finding を別エージェントで再検証して誤検出を除き、`git show HEAD` で「説明と実装の食い違い」を照合する (Phase1 完了監査 B→A で A1/A2 を発見・D19、audit-2026-06-30 では蓄積した 43 項目のうち裏取りサブセット 11 件を real 10/refuted 1 に選別)。

**ただし必須ゲートにはしない (規律5 と両立).** 重い Phase・別セッション引き継ぎ・overnight ループ後に回す**推奨手順**であり、小さな増分では省略してよい。列挙したトリガは最小限であって、疑いがあれば常に回してよい (列挙外を「監査不要」と読まないこと)。Phase 3 の auditor (生成 variant の前向きレビュー) とは射程が直交する —— auditor は coder が出す variant を事前に見張り、本監査は過去に入った作業物を遡及的に裏取りする。補完関係であり重複しない。

**この監査自身の限界 (正直に).** 監査者も AI なので「誰が監査者を監査するか」は本質的に解けない —— 独立コンテキスト・敵対性・多エージェント再検証で確率的に下げるだけ。また本監査はトリガ駆動ゆえ、同一セッション内の緩やかな劣化は捕えない (それは §3.4 / §3.6 / verifier ゲート / テスト、および §3.8 のセッション運用の前向き層に委ねる)。

### 3.8 セッション運用 — 同一セッション内のコンテキスト劣化への前向き対策

§3.7 はトリガ駆動の遡及層であり、「同一セッション内の緩やかな劣化は捕えない」と限界を明示した。本節がその対の前向き層 —— 長時間セッションでコンテキストが膨れたときに品質が下がるメカニズムを名指しし、**劣化してから頑張るのではなく、劣化する前にセッションを畳む**運用を規律化する (D31)。

**敵は 3 つ.**
- **非可逆な圧縮**: コンテキストが上限に近づくと自動圧縮 (auto-compact) が履歴を要約に置き換える。細部 (数値・ファイルパス・「なぜ却下したか」) が落ち、以後は要約の要約で作業することになる
- **自己一貫性バイアス**: コンテキストが長いほど、序盤に立てた誤った仮説・方針に固執しやすい。P2-5 で観測した「自信ある早期停止の負債」(D21/D29) と同型の失敗モード
- **読んだつもりドリフト**: 圧縮後、元ファイルを再読せずに要約の記憶でコードやドキュメントを編集する

**対策の設計原理: セッションの延命ではなく、短命でも仕事が途切れない構造.** izanagi はセッションを捨てるコストが構造的に低い —— CLAUDE.md「現在地」+ worklog + WAL リプレイ (campaign-id は入力から再計算できるため、状態を持たずに再開できる。orchestrator-design.md) + handoff insight。この再開性を活かし、「長い 1 セッションで完走を粘る」のではなく短いセッションを確実に繋ぐ方向に寄せる。

**運用ルール (4 本、盛らない):**
1. **粘らず捨てる.** 1 論理タスク = 1 セッションを基本とする。自動圧縮が入ったら (= コンテキストが要約されたと気づいたら) 新しいサブタスクを始めない。進行中の作業を区切りまで進め、worklog / handoff を書いてセッションを終える
2. **handoff の自己完結基準.** 次の fresh セッションが「handoff + CLAUDE.md 現在地 + worklog 末尾」だけで再開できる品質で書く。未完タスクは「何をどこまで・次の一手・既知の罠」を構造化する。これは §3.7 の引き継ぎ監査が読む対象でもある
3. **コンテキスト衛生.** 生 trace・生ビルドログ・WAL 全文をメインコンテキストに読み込まない。サブエージェント (独立コンテキスト) に読ませて構造化された結論だけ受け取るか、digest (online digest 等) を読む。必要な断片は tail / grep で絞る。「生データでなく構造化された要約が層間を流れる」は規律3 (構造化 anomaly) と同じ設計思想の運用面
4. **圧縮跨ぎの再読.** 自動圧縮の後に編集するファイルは、要約の記憶で触らず必ず再読してから編集する

**ループ主導権の原則 (Phase 3 の配線).** 反復ループの主導権は orchestrator (Python) に置き、LLM (coder / critic) は iteration 単位で fresh に呼ぶ。各呼び出しに渡すのは digest + 構造化 anomaly + 前回の構造化ログだけ。Claude のセッションが数十 iteration のループを自分で回すと、iteration が進むほど評価ログがメインコンテキストに堆積して上記 3 つの劣化が必ず起きる。orchestrator 主導なら各呼び出しのコンテキストは常に小さく、**品質がセッションの寿命に依存しない**。これは orchestrator-design.md「サブエージェントは中間状態を観測できないトランザクション (構造化ログで引き継ぐ)」の帰結であり、新設計ではなく既存原則の適用である。

**限界 (正直に).** 本ルールは Claude の自己申告ベース —— 劣化しつつある Claude 自身が圧縮に気づいて従う必要がある (§3.7「監査者の劣化」と同型の自己言及)。だから守れなくても正しさは壊れない構造が下にある: 機械的ゲート (hooks / pipeline.evaluate の fails-closed / WAL proof chain) は Claude の品質に依存せず (規律2)、劣化した成果物は §3.7 の遡及監査が捕まえる。本節の前向き層が守るのは正しさではなく**成果物の質と手戻りコスト**である。

---

## 4. レコード数の自動キャリブレーション

実験パラメータ (レコード数) を、測定の妥当性を保ちつつ最小コストになるよう自動決定する。これは CC 探索とは別レイヤーなので分離する (calibrator が担当)。

本番の CC 探索を始める前にキャリブレーションフェーズを噛ませる:
```
1m → 2m → 4m → 8m... と倍々で上げ、各点で
  - cache miss率 (perf stat: LLC-load-misses)
  - throughput
  - 1runあたり実時間
を記録
```
そして **cache miss 率が飽和する点** を探す。見るべきは throughput でなく cache 利用率 (CCBench I1: OCC の read-only 性能は cardinality 増加で急落、L3 miss が無くても)。

判定: 「次に倍にしても miss率が +Δ% 未満しか動かない」最小レコード数を採用。それ以上は時間を食うだけで測定値が変わらない (=「バカ」)。小さすぎると many-core の cache 競合が再現されず測定が楽観的に歪む。両方の罠を避ける。

**補強 (D15, タスク4b 実測):** CCBench の index = masstree では N増で木が深化し miss 率が単調上昇して**飽和点が出ない** (uniform も skew0.9 も実測で飽和せず)。この場合「飽和点 → 無ければ最大点」では最も遅い run を選んでしまい規律4 に反する。そこで**第二基準 = 下限**を足す: 飽和点が範囲に無ければ「working set (実測 maxrss) が L3 を K 倍 (既定4) 超える最小 N」= many-core cache 競合が確実に再現される最小点を採る。また**飽和/下限点は skew (局所性) に依存する**ので calibration は (env, thread, 代表 workload) でキーする (D13 改訂)。

注意: 飽和点は thread 数に依存する。探索に使う thread 数を決めたらその thread 数でキャリブレーションする。thread 数を変えたら測り直し。

LLM の役割は数値を見て判断 + 説明し、`output/insights/` に妥当性を文書化すること。査読で必ず問われる「なぜそのレコード数?」に先回りで答えられる。

**noise floor の実測 (§3.6 と接続).** calibrator はレコード数の飽和点に加えて、その環境の **noise floor** も実測する責務を持つ。確定した実験条件 (レコード数・thread 数) で baseline を**連続 N 回**測って throughput の CV を出し、「この差以下は信用するな」の下限として固定する。これは環境タグごと (mac-devcontainer / linux-baremetal) に持ち、§3.6(4) の分布比較が「差なし」に丸める閾値の根拠になる。Mac devcontainer で noise floor が大きく出ること自体が D10 (性能比較は Linux 実機のみ) の定量的裏付けになる。あわせて、ベンチ前の load average 静定確認 (admission control、orchestrator-design.md) も calibrator の責務に含める。

スケール感度の検出: variant 評価を単一スケールでやらず最低2点で測る (small: 4thread/100万, medium: 10thread/1000万)。「small→medium での性能の伸び方」を特徴量として LLM に渡し、small で良いのに medium で頭打ちの variant は「スケールしない疑い」とフラグを立てる。これが層3の「なぜこの variant を最終選択から外したか」に直結する。

---

## 5. 計算リソースと現実

計算層は**専有 Linux サーバ (Dell R760, bare-metal x86_64, 96スレ/2NUMA, 247GiB, perf HW カウンタ動作) を確保済み** (旧計画のラップトップ前提を更新)。CCBench の VLDB 論文は 1run 3秒程度。3秒/run なら一晩 (8時間) で約1万 run。sample 効率の心配はかなり緩む。スケール (レコード数・thread 数) は calibrator が cache miss 飽和点で決める。many-core (96スレ/2ソケット) では絶対規律4 (cache 競合の再現) のためスレッドピンニング (`-DLinux`/numactl) が要る — ccbench-anatomy.md §7。

ただし前述の通りスケールダウンには非線形の落とし穴 (コンテンション率の変化、cache 階層の効き方) があるので、calibrator とスケール感度検出で対処する。

---

## 6. リポジトリ構成と CCBench の扱い

AI システムのリポジトリ + CCBench を submodule で参照する。**submodule は v1 (thawk105/ccbench) を使う** — VLDB 論文の実体で、最適化が交換可能単位で整理されたコーパスが揃っているため (v2 は書き直し中で本プロジェクトの前提を満たさない)。実物 (解剖時点のスナップショットは `33d74a3` = CMake 再構成版。現行 submodule pin は `orchestrator/campaign/pin.py` が正本、D38) は **10 プロトコル (YCSB 対応は 7: silo/tictoc/mocc/cicada/ermia/si/oze)** ×3カテゴリの最適化フラグ群を持つ (解剖結果は `docs/ccbench-anatomy.md`)。理由:
- CCBench を汚さない (還元すべき差分が綺麗に切り出せる)
- CCBench のバージョンを commit hash で固定 (再現可能)
- CCBench への改変を「パッチ」で管理できる

CCBench の走らせ方: orchestrator が patches/ を適用 → cd external/ccbench && make → 走らせて output/runs/ (= campaign スコープ `output/campaigns/<id>/runs/` の短縮表記、D13/orchestrator-design.md) にログ → 実験後 git checkout で ccbench をクリーンに戻す。これで「CCBench本体は常にクリーン、改変は patches/ に明示的に存在」が保てる。※この「全改変を patches/ で」は D16 で三分岐に改訂済み: 本物のバグ修正は上流 master へ還元、trace-hook は `izanagi-trace` ブランチ (submodule pin)、patches/ 行きは意図的バグ (broken-silo)・合成 variant (D18)・診断計器 (D20) のみ (decisions.md D16 参照)。

trace 吐く口 — ビルド時 vs ランタイム: CCBench の最適化フラグが `#define` (ビルド時) かランタイムかで探索ループの形が変わる。CCBench は性能ベンチなのでおそらく多くがビルド時 `#define`。だとするとパラメータ探索は「ビルドし直し型」になり make 時間が評価コストに乗る (緩和: 組み合わせごとにバイナリをキャッシュ)。**これは Phase 1 タスク0 で実物を読んで確認する最優先事項。**

CCBench 還元スキーム: 探索中に CCBench 自体の問題を見つけたら `output/insights/` に構造化レポートを吐く。必ず「還元判断: ユーザー確認待ち」を付ける。AI は発見を構造化するところまで、上流に出すかは人間が決める (誤検出 = verifier のバグを CCBench のバグと誤認、を防ぐ関所)。

---

## 7. 関連研究からの借用 — `docs/related-work.md` へ分離 (2026-07-05, D35)

関連研究 (Polyjuice/CCaaLF・Jitskit・IDS・VibeServe・SkillOpt・Self-Harness・DecentMem・ARA・
知識労働の経済分析・12-factor-agents・ECC) と、各々から何を借用し何を借用しないかの記録は
`docs/related-work.md` にある。読むのは論文執筆・ポジショニング検討・新規関連研究の追加時のみ —
日常セッションのブートには不要 (これがこの分離の理由)。本文中・他文書の「§7」参照は同文書を指す。

---

## 8. 本システムの新規性 (ポジショニング)

- Jitskit は KVストア、IDS は分散KVの consistency。**誰も single-node の CC プロトコルの serializability を対象にしていない**
- 両者とも「ゼロから合成」か「証明付き合成」。Izanagi の**コーパス駆動の合成**は空きポジション — CCBench 資産をベース CC 選定 (層1)・クロスプロトコル比較 (Phase 3 主実験 headline 2)・変異軸のアイデア源として使い、実証済みの空間外合成 (b1、P2-4) を軸に、他 CC からの最適化移植 (b2) を拡張として持つ (D32)
- CCBench という「10 プロトコル (YCSB 対応は 7: silo/tictoc/mocc/cicada/ermia/si/oze) × 最適化フラグ群が交換可能単位で整理された資産」を使う点が独自 (§6 の実体調査に一致)

ポジション: **Jitskit/IDS のループ方法論を継承しつつ、対象を CC の serializability にし、合成方式を CCBench 資産を土台にした帰属駆動の合成 (実証済みの空間外合成 b1 + 拡張予約の移植 b2、D32) にする。** 系譜の3本目として乗れる。

---

## 9. Phase 計画

```
Phase 1: 評価器を信頼できる状態にする
  - CCBench 解剖 (タスク0)
  - mini trace verifier 実装 (構造化フィードバックを返す)
  - verifier が「赤を出せる」ことの証明 (わざと壊した CC で anomaly 検出)
  - calibrator 実装
  - 手動で invisible reads on/off → verifier緑 & 性能差が CCBench I2 と整合
  サブエージェント: verifier, calibrator

Phase 2: パラメータ探索
  - 全探索 vs LLM誘導 の比較
  - leading indicators を LLM に渡す
  + critic (指標の解釈), profiler (スケール懸念検出)

Phase 3: コード粒度の合成
  - EVOLVE-BLOCK で LLM がフラグ空間外の変異軸を合成 (b1 = 主実験)
  - 他CC の最適化移植 (b2) + カタログ化は主実験後の拡張予約 (D32)
  + planner/coder (分離), auditor (reward hack監査)

Phase 3.5 (任意): Open-Ended Evolution
  - コード移植でアクション空間が開いて初めて意味を持つ
  - 多様性保存を完全な MAP-Elites/quality-diversity に格上げ
  - ablation で OEE 有り/無しの探索効率を比較
```

各 Phase の詳細タスクは該当する docs/phaseN.md に。現在どの Phase かの正本は CLAUDE.md「現在地」が指す worklog 末尾と現行 phase doc (roadmap は現況を主張しない)。

---

## 10. スコープ外 (明示的にやらないこと)

- 完全な形式証明 (IDS式 Rocq) — 将来拡張。C++ many-core 実装の形式化が重すぎる
- Open-Ended Evolution の完全機構 — Phase 3.5 に予約。初手で入れると失敗の切り分けができなくなる
- ECC のような汎用ツール化・多言語・marketplace — 単一研究目的に不要
- 層1 の凝った選定器 — 既存研究が強く、層2が吸収するため軽くて良い
- **論文執筆・推敲そのもの (narrative 生成)** — Izanagi のスコープ外。Izanagi は材料レポート (ARA 的 artifact) の生成までを担い、自動執筆は別システムに委ねる (D12)
- **ARA Compiler (フォーマット変換器)** — CCBench は既に構造化済みの C++ コーパスで変換対象が存在しない。取り込めば純粋なスコープ膨張 (規律5)
- **ARA Live Research Manager (背景監視による推測的ハーベスティング)** — Izanagi の orchestrator は各 variant 評価を能動的・決定論的に WAL へ書く設計なので、自由形式セッションから研究イベントを事後収集する機構の必然性が薄い (規律5)。7種イベント taxonomy と ai-suggested の人間確認ゲート思想のみ、decisions.md / output/insights/ のエントリ構造化と roadmap 改訂セレモニーの人間確認に響く思想参照として留める (機構は実装しない)

OEE について補足: 完全機構 (新規性報酬・無限走行) は Phase 3.5 に回すが、安い果実は初手から取る — (a) 多様性の保存 (層3で「throughput最強の1個」でなく特性の違う variant を複数残す)、(b) whiteboard memory (既に採用)。
