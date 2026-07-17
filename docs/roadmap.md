# Izanagi ロードマップ — 全設計と理由

**版: v1 系。** 本ドキュメントは生きた文書であり、試行錯誤の発見に応じて Claude が改訂してよい (改訂規律は CLAUDE.md の「roadmap の更新」参照)。協議改訂は版番号を上げず in-place で反映する (改訂履歴は git log) — docs/roadmap-history/ への版凍結は Claude の自律改訂時のみで、凍結版と改訂理由 (decisions.md) の変遷そのものが研究記録 (論文の方法論セクションの原料) になる。

このドキュメントは、本システムの設計のすべてとその理由を記録する。次の作業者 (人間または Claude) が、設計に至った議論を見ていなくても「なぜこうなっているか」を完全に追えることを目的とする。

**専門用語につまずいたら `docs/glossary.md` (用語集) を引く。** docs は並行性制御・探索理論・統計・本プロジェクト固有の機構にまたがる用語を、多くは説明なしに使う。用語集はそれらを専門外の読み手向けに平易に定義する。

**読み方 (ブートコスト規律、D35):** 全文必読は「Phase の初回セッション」と「roadmap を改訂するとき」のみ。日常セッションでは、現行タスクが参照する節だけを節名 (§) で引く。全文を毎セッション読み込むのは §3.8 のコンテキスト衛生 (生データでなくダイジェスト) に反する。関連研究 (§7) は `docs/related-work/` に分離してある。

---

## 1. 究極のゴール

**ワークロード仕様を入力に、CCBench を素材コーパスとして、正しさを維持したワークロード特化 CC variant を自動合成・選択し、その判断根拠を proof chain 付きで説明する AI システム。**

ここでいう AI システムは LLM 単体ではない。LLM による機序帰属・変異軸提案、有限空間に強い機械探索、正しさ verifier、性能測定、最終選択を一体として扱う。列挙可能な空間で機械探索が LLM より強いなら、機械探索を使うのが正しい設計であり、システムの成功に「LLM が機械探索を上回ること」は含めない。

入力は workload descriptor とする。これは少なくとも read/write 比率、競合水準、スケール、最適化目的、正しさ制約を型付きで持つ。既知の勝者名や性能値は入力に混ぜない。システムは:
1. CCBench の候補を同一条件で比較し、ベース CC 候補と比較基準を定める
2. 指標の機序帰属から変異軸または探索箇所を提案し、LLM 合成と bounded machine search を使い分ける
3. 各 variant を正しさ・identity・性能の据え置きゲートで評価し、採用・棄却・差なしを記録する
4. 証拠が支持する最終 variant を選ぶ。改善を立証できなければ stock または tie を正直に選ぶ

最終成果物は3つ:
- **certified な CC の選択結果** — 証拠が支持すれば新規 variant、支持しなければ stock 選択または tie 判定
- **evidence-bound な材料レポート** — workload、選択、正しさ、性能分布、代替案、仮説を proof chain で結ぶ
- **再現可能な試行台帳** — 採用・棄却・失敗・差なしを含む全評価の provenance

stock/tie は正直な no-improvement 出力として必要だが、「新しい CC」という研究目標の達成には数えない。

主張は次の階層を混同しない:
1. **評価器の主張** — 宣言した point-key YCSB / 観測 trace の範囲で positive control を赤にし、同一 identity を再現できる
2. **システムの主張** — workload ごとに certified な variant を合成・選択できる
3. **LLM 固有の主張** — LLM あり/なしのアブレーションでのみ、軸発見や探索効率への寄与を言う
4. **無人自律の主張** — セッション外から反復を駆動し、人間が候補を手で運ばず完走した場合にのみ言う

下位の成立から上位を推論しない。特に、異なる workload で異なる勝者が出ただけでは workload descriptor が選択を駆動した証明にならず、機序説明はアブレーションなしには因果でなく仮説である。

---

## 2. 三層アーキテクチャ

```
ワークロード入力 (typed descriptor)
   ↓
層1: ベースCC選定ループ
   候補抽出 → 同一条件ベンチ → seed と比較基準を記録
   ↓ seed + baseline
層2: ハイブリッド合成・探索ループ
   機序帰属 → 軸提案/探索箇所 → LLM合成または機械探索
   → 評価(正しさ+identity+性能) → workload別 archive
   ↑__据え置きゲートを壊す変異は reject__|
   ↓
層3: evidence-bound 比較・選択・説明
   分布・floor・代替案・proof chain から最終CCを決定
   ↓
最終成果物: certified variant + 材料レポート + 試行台帳
```

### 層1 — ベース CC 選定 (軽く作る)

ここに凝りすぎるのは罠。workload→CC 選定には CormCC/ACC/Polyjuice など強い既存研究があり、LLM で再発明しても主な新規性にならない。一方で、層2が seed の誤りを必ず吸収するとも仮定しない。seed 選択の誤りと合成能力を混同しないため、軽量ベンチで 2〜3 protocol を同一条件比較し、選んだ seed と棄却した候補を provenance 付きで残す。

実装方針はヒューリスティックで候補を絞り、数回のベンチで seed と stock baseline を確定する。複数 seed や island model は、多様性不足が実測で律速になったときの拡張であり、初期の必須機構ではない。LLM を使う場合も、選択器そのものより「どの workload 特性と実装特性が対応するか」の仮説生成に使い、層3で証拠と照合する。

### 層2 — ハイブリッド合成・探索ループ (心臓部。移植 (b2) は拡張予約、D32)

#### 最適化の粒度: (a) は対照・bounded search、(b1) は主経路、(b2) は拡張

3段階の選択肢がある:
- **(a) パラメータ粒度 (Polyjuice式)** — 最適化を事前定義フラグ/数値にする。LLM ほぼ不要、新規性低いがロバスト
- **(b) コード粒度 (AlphaEvolve式)** — CCBench 内の特定関数を `EVOLVE-BLOCK` で囲み LLM に diff を書かせる。**(b) の内側に 2 形態がある (順序は D32 で確定)**:
  - **(b1) 空間外合成** = ベース CC の内側で、フラグ空間に無い新しい変異軸を critic の機序帰属から合成する (P2-4 backoff が成立例)。
  - **(b2) 移植** = 他 CC の最適化を持ち込む (未検証仮説)。

  Phase 3 は (b1) を先にし、(b2) は後続拡張として予約する (phase3.md 後続段 7)
- **(c) アルゴリズム粒度 (FunSearch式)** — ゼロから書かせる。自由度高すぎて正しさが崩壊。CC では非推奨

**決定: (a) は ground truth・機械対照・bounded search として使う。研究上の主経路は、(b1) で LLM が機序帰属から軸や hole を提案し、その軸内を機械探索するハイブリッド構成とする。(b2) は後続拡張、(c) はやらない。**

(a) を対照として使う利点 (本プロジェクトの状況で特に効く):
- パラメータ粒度は「CCBench が元々持つ最適化フラグの組み合わせ」なので、コード合成より探索空間と identity を固定しやすく、trace verifier の検証に向く。ただし組み合わせ安全性を仮定せず、全候補を同じ verifier に通す
- 探索空間が有限 (CCBench の最適化が主に on/off なら高々 2^7=128 + 連続パラメータ数個)。**初手は全探索すら可能**。全探索の最適と LLM 探索の到達速度を比較でき、論文の図になる

  → **この比較は P2-5 で実施済み = negative result。silo 8 の自明空間では誘導は機械的勾配 (貪欲) を超えず、deceptive 構造では貪欲より有意に有害。D21/D29。よって「論文の図」は『誘導が速い』ではなく『小空間ではフラグ探索が自明で価値は空間外の合成にある』という物語に転じた**
- (a)→(b) の移行が自然。パラメータ探索で「invisible reads を on にすると効く」が分かった後、コード移植で「その実装そのものを別 CC 文脈に移植できるか」に進む

  → **実際に起きた移行は違う形だった** — 「効いたフラグの実装を移植」ではなく「フラグ空間の外の新軸を合成」(P2-4 backoff) として起きた。これが (b1) を先にする D32 の根拠

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

**着手時期:** D32 の b1 先行 / b2 後続は維持し、b2 の着手 gate を協議改訂した。カタログ化 + 移植は、workload descriptor (phase3.md 段 8b) と層3材料レポートの最小 E2E を成立させた後の拡張として予約する (phase3.md 段 7)。一歩目はカタログ化の試作 1 枚で、移植の本格投資はその結果 (移植先で前提が満たせるか) で決める。カタログ化の成果物は移植を見送っても層3の説明生成に流用できる。

#### 探索戦略 — 役割分担を先に固定する

1. profiler / critic が leading indicators を集約し、性能差の機序仮説を作る
2. LLM が仮説から新しい変異軸または `EVOLVE-BLOCK` hole を提案する
3. 列挙可能な軸内は sweep・greedy・random などの機械探索で最適化する
4. 各候補を同じ correctness・identity・performance gate に通す
5. workload 別の全結果を archive し、次の帰属と層3へ戻す

P2-5/D29 は、有限で小さいフラグ空間では LLM 誘導を必須にする理由がなく、機械的勾配が同等以上になりうることを示した。P2-4 backoff は空間外の軸を作る価値を示す成立例だが、LLM の自律性や機械探索への優越まで証明しない。したがって「LLM が何でも探索する」のでなく、LLM は主にアクション空間を広げ、機械は境界の明確な空間を漏れなく調べる。

low-fidelity proxy や island model は、正式評価との順位相関や多様性不足を測ってから導入する。population、世代更新、選択、変異/交叉、必要なら migration を実装し、その寄与をアブレーションするまでは、本ループを **進化探索** や GA と呼ばず、sequential/hybrid search と呼ぶ。

#### システム合成と無人自律を名乗るための要件 (D44 + 2026-07-14 協議改訂)

- **軸提案がループ内にあること** — 人間が毎回 hole と勝ち筋を手渡さない
- **workload descriptor が第一級入力であること** — coder が workload を知らないまま結果だけ比較する構成にしない
- **層3が WAL/proof chain から決定論的に生成できること** — 成功例だけを人間が後から物語化しない

上の 3 点は human-supervised なシステム合成の最小要件である。**無人自律を名乗るには、さらに反復駆動が
セッション非依存で、checkpoint・予算・再開を orchestrator が所有することが必須**。現況と着手順は
`docs/phase3.md` を正本とする。planner/coder を人間がセッションごとに運ぶ段階は human-supervised loop と呼び、
orchestrator が各 role を呼び予算内で終了まで駆動して初めて unattended/autonomous と呼ぶ。8c を後回しに
することは着手順の判断であって、この要件の免除ではない。どちらの場合も正しさ・identity・リーク制御の
防壁は緩めない。

### 層3 — evidence-bound な比較・選択 + 説明生成

層3は自由作文ではなく、WAL と proof chain を読む material-report renderer を中核にする。**数値・verdict・参照を並べる事実層は完全かつ決定論的な射影**とし、LLM を使いうる機序仮説層とは分離する。最低限、次を結ぶ:

- workload descriptor と選択された variant/source identity
- verifier verdict、seed、trace、build provenance
- baseline/variant の分布、CV、between-run floor、統計判定
- 比較した代替案と採用・棄却・差なしの理由
- leading indicators と code diff に基づく機序仮説
- 各 claim から code・run・artifact への参照

アブレーションで分離できた効果だけを因果として述べ、それ以外は「整合する仮説」と明記する。noise floor 以下を勝敗に使わず、改善が立証できなければ stock/tie を出力する。LLM は構造化された証拠の要約や仮説生成に使ってよいが、数値・verdict・参照を創作できない。成果物は論文本文ではなく、人間が検証可能な材料レポートである (D12)。

差別化の核心は、variant を出すことだけでなく、**どの入力に対し、どの候補を、どの正しさ証拠と性能証拠で選んだかを再検証可能にすること**にある。

---

## 3. 評価器 (evaluator) の設計

evaluator が本システムの成否を分ける。AlphaEvolve/Jitskit/IDS すべてが「evaluator こそが損失関数であり、その質がすべてを決める」と言っている。

### 3.1 正しさ検証の階層化

数千 evaluation を回したいので、安いチェックで枝刈り → 中コストで実検証 → 高コストで形式的保証の段階構成にする。

- **Tier 0: 静的・構文チェック → compile/smoke** — 安いテキスト/構文検査を先に行い、その後にコンパイルと基本 trx のスモークを通す。compile/smoke は別コストなので μ秒とはみなさない
- **Tier 1: トレース検証** — CC特化の最重要パート。実行トレースを取り、後から serializability を検査。read/write 依存グラフを作って cycle 検出 (Adya の serialization graph)。
  - YCSB の point read/write なら辺は ww/wr/rw の3種で、G2 (anti-dependency cycle) まで見る。
  - 自前 mini-verifier が担保するのはこの宣言範囲であり、predicate/phantom、fairness/starvation、未観測実行まで保証しない。
  - TPC-C 等へ広げる場合は形式と verifier を拡張する
- **Tier 2: 既存OSS DBのテスト移植 (秒〜分)** — isolation level 固有の境界条件のカバー。PostgreSQL の isolation tests、Hermitage (Martin Kleppmann) など。「variant が宣言した isolation level で通るべき/落ちるべきテストの集合」を固定
- **Tier 3: 形式検証 (分〜時間)** — TLA+/TLC など。最終候補にだけ。**初期スコープ外** (理由は decisions.md 参照)

### 3.2 二相設計 (IDS式に格上げ)

- **開発相 (短時間 × 大量)** = 回帰検出。短い trace で cycle 検出、anomaly 出たら即 reject。確率的な見逃しは残る。「安く広く」。最後にまとめず毎 iteration 回し、構造化フィードバックを次の proposer/selector へ返す
- **検証相 (長時間 + 精査)** = 最終候補 1 個 (数個) にだけ長時間 trace + 厳密検査を行い、観測証拠を強める。「高く狭く」

seed を変えた複数 run は未観測バグの機会を増やすが、1 run の検出確率と独立性を較正していないため数値的な信頼度や完全保証には変換しない。報告するのは条件、seed、trace 規模、観測 verdict である。

### 3.3 観測者効果の分離 (最重要の計測規律)

正しさ検証用のトレース取得が、計測対象を歪める (Heisenbug 的構造)。対策:

- **trace-enabled build** (トレース口あり、正しさ専用、性能は見ない) と **trace-disabled build** (トレース口を `#if TRACE` で完全に消す、性能専用) を分ける
- トレース取得をランタイムフラグにしない。`#if TRACE` でコンパイル時にコードごと消す
  - `TRACE=0` でも定義有無だけを見るガードは真になるため使わない。
  - ランタイム分岐は分岐予測・命令キャッシュを汚しうる
- 性能比較は variant も baseline も trace-disabled で揃える
- メタデータは「CC本来 (アルゴリズムが要求する。性能比較に含める)」と「検証専用 (verifier にトレースを渡すためだけ。`#if TRACE` で消す)」を区別。この2つを混ぜない
- perf は trace-disabled build に当てる
- ビルド等価性の機械検証: trace-enabled と trace-disabled でトレース有無が CC の意味論を変えていないことを機械確認する。
  - **実装は当初案 (最終 DB 状態の一致比較) から変更**: Phase 1 タスク1 の **symbol 不在検査 (perf binary に trace コードが 1 byte も無い、`nm`)** の方が DB 状態一致より強い証明なので、DB-dump 計装は冗長と判断し未実装 (phase1.md タスク5a 節の判断記録参照)。
  - Phase 3 では方針 A (D30) により、この機械確認が観測者効果分離の**一次防壁に昇格**し、symbol 不在に加えて **diff-of-diffs** (variant の TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と一致することを assert する「観測者効果の二重検査」。素の出力 diff は `#if TRACE` ガード領域で正当に食い違うため不成立と敵対検証で裁定済み) へ拡張済み
  - 2026-07-04 実体化。`source_digest.assert_trace_diff_matches_head` を `buildcache.build` 出口の hit/fresh 両経路で発火、fails-closed

### 3.4 reward hacking 対策 (Jitskit §3.2, Appendix B より)

LLM は最適化圧力の下で、書かれていない不変条件を破って性能を稼ぐ。CC 版で起きうるもの:
- 「検証用 trace が見ていないアクセスパターンでだけ正しい CC」を作る → 対策: seed を変えた複数 run で毎回検証
- 「導出可能な ground truth を突く」(値を保存せず再計算) → 対策: 値に再構成不可能なエントロピーを持たせる
- 「探索の自己崩壊」(これ以上は失敗すると恐れて最適化をやめる) → 対策: 探索ポリシー側で継続を促す

これらに対し:
1. **据え置きの正しさゲート** — 壊すと即 reject。「絶対壊しちゃダメ」(serializability anomaly検査、ACID基本) と「壊れていい」(プロトコル固有テスト、variant のキャラクタライズに使う) を分ける
2. **adversarial auditor** (Phase 3 から使用) — N iteration ごとに variant を監査、verifier が見逃した不変条件違反を検出し、それを捕らえる positive control テストを設計・**提案**する。auditor は read-only (Edit/Write 非付与、D38 決定 3) — 提案の反映は orchestrator の人間レビュー gate が行い、「既存テストを弱める書き込み」は構造的に不可能にする
3. **hooks による書き込み時防壁** (Phase 1 から薄く) — verifier 迂回・成果物への直接書き込みを機械的に弾く**最小の第二防壁**。**方針 A (D30) 以降、hooks は「唯一の防壁」ではない**: identity の honest さ (偽 cache hit / `#ifdef`) は source_digest の preprocess 後ハッシュ、観測者効果の分離は観測者効果の二重検査 (diff-of-diffs、§3.3) が**一次防壁**として担い、hook はテキスト検査の完全性に依存しない範囲 (堅牢なパス検査) に責務を絞る。2 巡の敵対検証で「テキスト検査に C++/shell の完全性を負わせる設計は原理的に破れる」と実証したため (規律5 と両立させる責務再配置)
4. **検証エージェントの入力側隔離** — 「導出可能な ground truth を突く」への入力側の対策として、正しさ検証エージェント (verifier) のコンテキストに性能数値や期待結果を一切混入させない。verifier は trace のみを入力とし、throughput 等の報告済み数値を受け取らない。
   - これは verifier に専用書き込みツール (Edit/Write) を与えない出力側隔離 (Bash 経由は prompt 規律で禁止 — 完全なツール権限隔離ではない、audit-2026-06-30 §4) と対をなす入力側隔離で、「期待値をコピーして捏造する」経路を入力データレベルで断つ (ARA / 2604.24658 の anti-fabrication isolation、§7)

### 3.5 leading indicators (診断シグナル)

Jitskit では、スカラーの throughput だけより leading indicators を併用する方が探索診断に有効だった。Izanagi でも lock contention / cache hit率 / I/O / memory帯域を候補シグナルとして構造化するが、どの指標が有効か、LLM 解釈が必要かは workload と対照実験で決める。

**P2-5 の含意 (D29):** silo 8 の小空間では**指標を機械集約した digest 勾配 (貪欲、LLM なし) だけで同水準の収束に届いた**。つまり「診断シグナルを探索器へ渡すこと」の価値と「LLM に解釈させること」の価値は分けて考える必要があり、どちらも全 workload での必須条件とはまだ言えない。後者 (LLM 固有の付加) は小空間では貪欲から分離できなかった。機序帰属からフラグ空間外の軸を提案する局面 (P2-4 backoff が成立例) が次に検証すべき役割仮説であり、LLM あり/なしの軸提案アブレーションなしには優位や因果的必要性を主張しない。

これは「FlameGraph を見て many-core でヤバいか判断してほしい」という当初の直感の正式版。perf プロファイリングは有望な variant にだけ回す (二段構え: screening 通過 → profiling)。

### 3.6 測定の安定性 (measurement stability)

性能数値は「1 run の点」ではなく「**反復測定の分布**」として扱う。他ユーザー・他プロセス・温度スロットリング等の外乱は一晩の自動ループでは必ず混入するが、人間の「あれ?」は介在しない。だから**ばらつきの監視と再測定を実行時の気まぐれに委ねず、規律として明文化・自動化する**。これは絶対規律1 (観測者効果の分離) / §3.4 (reward hacking 対策) と同じ構造の汚染防止であり、reward hacking の鏡像 ——「**ノイズを最適化シグナルと誤認する**」—— への対策でもある。

**(1) 反復と要約.** 1 measurement = N 回反復 (初期値 N=5、calibration で調整)。各 run の冒頭は warmup として破棄し定常状態のみを採る (※現実装は ccbench の extime 一括計測に従属し warmup 分離なし — 意図的非対応、D28 参照)。報告は単一の throughput でなく **中央値 + 散布度 (変動係数 CV / IQR)** を必ず持つ。WAL には個々の run 値も残し、後から分布を再構成できるようにする (campaign スコープ `output/campaigns/<id>/runs/`。出力レイアウトと campaign 同一性は orchestrator-design.md / D13)。calibration/noise floor は env スコープ `output/env/<env-tag>/` に置くが、thread 数・代表 workload/config の署名で別物としてキーする。

**(2) 外れ値検出 → 自動再測定 (=「あれ?」の機械化).** 反復内の CV が閾値 (初期 5%) を超えたら「測定が外乱で歪んだ」とみなし**自動で測り直す**。再測定の前に Admission Control の静定確認 (load average 静定) を必ず通す。規定回数 (初期 3 ラウンド) 測っても CV が収束しなければ、その variant に **`unstable` フラグ**を付けて分布比較から除外し、insight に「測定不能」として記録する。沈黙して 1 点を採用してはいけない。

**(3) noise floor の実測.** 「この差は信じてよいか」の下限を勘で決めない。calibration フェーズで baseline を連続 N 回測って CV を実測し、それを **noise floor** として固定する (§4)。これは環境タグ (mac-devcontainer / linux-baremetal) ごとに持つ。Mac devcontainer は VM 越しで noise floor が大きく出るはずで、その数値自体が「ここでは性能比較するな」(D10) の定量的裏付けになる。

**(3') noise floor は用途で 2 種に分かれる (A2 で分離).** 「N 回測った CV」には測り方が 2 つあり、用途が違うので混同してはいけない:
- **within-run noise floor** = 1 セッション内で反復 (rep) を back-to-back に取った CV。これは「**その 1 測定の品質**」(外乱で歪んでいないか) の尺度で、(2) の自動再測定 (CV 超→測り直し→unstable) の品質ゲートに使う。
- **between-run noise floor** = **独立したセッション** (別 run、別ビルド、campaign の別時点) の代表値 (session-median) 間の CV。これは「**差が信用できるかの下限**」で、(4) の分布比較が「差なし」に丸める閾値 (compare の floor) に使う。

variant と baseline は決して同一セッションで測らない (別ビルド・別時点) ので、**採否の floor は within-run でなく between-run であるべき**。
- within-run はセッション内の warm cache・同一熱状態・同一周波数定常を共有するため run 間ドリフトを過小評価し、これを採否 floor に流用すると between-run ドリフト帯の差を「有意」と誤判定して**偽 faster** を出す。
- なお fresh な back-to-back セッションは cold-boot/温度/数時間ドリフトを含まない**下限**なので、確定する between-run floor は fresh 実測と cross-campaign の genuine データ (別時間窓の同一 genome 反復) を突き合わせ保守側 (最大) に採る。
- high-abort genome ほど run 間ドリフトが大きい (abort 率が分散源)。

**(4) 採否は点比較でなく分布比較.** variant vs baseline の優劣判定は単一値の大小でなく**分布の比較**で行う:
- 差が noise floor 以下なら「**差なし**」に丸める。層3 narrative の「3%悪化だから不採用」のような **noise floor 以下の差を採否根拠にしてはいけない** (3% はラップトップ/devcontainer ではほぼノイズ)
- noise floor を超える差については、信頼区間の重なり、または分布フリーな検定 (Mann-Whitney U 程度で十分) で有意性を判定する。重い統計機構は要らない。**ただし反復数が小さい (reps≈5) と MWU の弁別力は弱く、完全分離は常に p≈0.012 を返す** (within-run cluster が tight なため)。
  - よって MWU は between-run 有意性検定ではなく within-run の分布重なりを弾く弱い sanity にすぎず、**主防壁は between-run floor 丸め ((4) の第1項、noise floor 以下を「差なし」に丸める)**。
  - floor を僅かに超える差 (floor 〜 1.5×floor) は MWU が無力な帯なので、headline にする前に cross-run 再現で裏取りする (A2: compare が `near_floor` フラグを立てる)
- 層3 のレポートは差分値だけでなく **「N 回測定の中央値、CV、noise floor、有意か否か」** を添える。これは「なぜこの variant を採った/外した」の説明可能性 (本システムの差別化の核心) を統計的に裏打ちする。各主張をその根拠 (WAL の run 値) まで辿れる形で紐づける構造は、ARA の forensic binding (claim→code→evidence の proof chain) と同型 (§7・D12)

**(5) スコープ.** Phase 1 では (1)(3) を骨格として実装 (calibrator が noise floor を出し、ベンチが反復+中央値+CV を返す)。(2)(4) は性能採否が実際に走る Phase 2 で必須化する。Phase 1 は Mac devcontainer 中心で性能採否をしなかった (D10) ため (2)(4) は配線のみ用意し、Linux 実機 (env-tag `linux-baremetal`) 確保後の Phase 2 (A2) で有効化した — noise floor を within-run (品質ゲート) と between-run (採否 floor) に分離した上で (§3.6(3'))。

### 3.7 Phase 完了監査と引き継ぎ監査 (劣化の遡及検出)

§3.4 (reward hacking 対策) と §3.6 (測定の安定性) は「書き込み・評価の**その時点**で正しさ/測定を守る」前向きの層である。だがこのプロジェクトの履歴が示すように、AI が一度入れた作業は後から劣化が露呈しうる ——
- reward hacking の鏡像 (偽 faster: between-run でなく within-run floor を採否に流用した A2/D19)、
- consumer 取り残し (D23 src_token を loop が追従せず再評価冪等性 D を破った D25)、
- 謳う保証が恒真な空証文 (online_digest の「二重の関所」D26)、
- 計測汚染 (前セッションの孤児 livelock が read-heavy を 2.2x 歪めた)。

これらは**入った時点でなく後から**捕まった。

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

**対策の設計原理: セッションの延命ではなく、短命でも仕事が途切れない構造.** izanagi はセッションを捨てるコストが構造的に低い ——
- CLAUDE.md「現在地」
- worklog
- WAL リプレイ
  - campaign-id は入力から再計算できるため、状態を持たずに再開できる。orchestrator-design.md
- handoff insight

この再開性を活かし、「長い 1 セッションで完走を粘る」のではなく短いセッションを確実に繋ぐ方向に寄せる。

**運用ルール (4 本、盛らない):**
1. **粘らず捨てる.** 1 論理タスク = 1 セッションを基本とする。自動圧縮が入ったら (= コンテキストが要約されたと気づいたら) 新しいサブタスクを始めない。進行中の作業を区切りまで進め、worklog / handoff を書いてセッションを終える
2. **handoff の自己完結基準.** 次の fresh セッションが「handoff + CLAUDE.md 現在地 + worklog 末尾」だけで再開できる品質で書く。未完タスクは「何をどこまで・次の一手・既知の罠」を構造化する。これは §3.7 の引き継ぎ監査が読む対象でもある
3. **コンテキスト衛生.** 生 trace・生ビルドログ・WAL 全文をメインコンテキストに読み込まない。サブエージェント (独立コンテキスト) に読ませて構造化された結論だけ受け取るか、digest (online digest 等) を読む。必要な断片は tail / grep で絞る。「生データでなく構造化された要約が層間を流れる」は規律3 (構造化 anomaly) と同じ設計思想の運用面
4. **圧縮跨ぎの再読.** 自動圧縮の後に編集するファイルは、要約の記憶で触らず必ず再読してから編集する

**ループ主導権の原則 (Phase 3 の完成形).** 反復ループの主導権は orchestrator (Python) に置き、LLM (coder / critic) は iteration 単位で fresh に呼ぶ。

現行は LoopState/checkpoint と機械評価までは実体化しているが、role 呼び出しはセッション運営に依存する human-supervised loop であり、本原則は 8c 完了まで部分実装である。完成形で各呼び出しに渡すのは digest + 構造化 anomaly + 前回の構造化ログだけ。

Claude のセッションが数十 iteration のループを自分で回すと、iteration が進むほど評価ログがメインコンテキストに堆積して上記 3 つの劣化が起きる。

orchestrator 主導なら各呼び出しのコンテキストは常に小さく、**品質がセッションの寿命に依存しない**。これは orchestrator-design.md「サブエージェントは中間状態を観測できないトランザクション (構造化ログで引き継ぐ)」の帰結である。

subagent 登録がセッション開始時にのみ読まれる制約 (2026-07-08 実証) の下では、登録ベースの LLM 呼び出し自体がセッション運営を律速にするため、orchestrator からの API 直呼び駆動への移行を phase3.md 段 8c に予約した (D44)。

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

閾値適用と採用点の決定は calibrator が機械的に行う。LLM の役割は異常仮説と説明の補助に限定し、`output/insights/` に「なぜそのレコード数か」を証拠付きで文書化する。

**noise floor の実測 (§3.6 と接続).** calibrator はレコード数の飽和/下限点に加えて、その実験署名の **noise floor** も実測する責務を持つ。確定した条件 (env、record 数、thread 数、代表 workload/config) で baseline を**連続 N 回**測って throughput の CV を出し、env スコープ内で署名別に保存する。**ただし、この「連続 N 回」の CV は within-run であり、1 測定の品質ゲート (§3.6(3)) にのみ使う。§3.6(4) の分布比較が「差なし」に丸める採否の閾値には使わない。採否の floor は between-run (§3.6(3')、D19) で、calibrator でなく別ドライバ (orchestrator/campaign/between_run_floor.py) が対象別に確定する。within-run の流用は run 間ドリフトを過小評価して偽 faster を出す (D19 が塞いだ経路)。**Mac devcontainer で noise floor が大きく出ること自体が D10 (性能比較は Linux 実機のみ) の定量的裏付けになる。あわせて、ベンチ前の load average 静定確認 (admission control、orchestrator-design.md) も calibrator の責務に含める。

スケール感度の検出: variant 評価を単一スケールでやらず、calibrator が確定した thread/record 動作点から最低2点を選ぶ。固定の `4thread/100万` 等を全環境へ流用しない。small→larger の性能変化を構造化特徴量として selector と層3へ渡し、larger で頭打ちの variant は「スケールしない疑い」とフラグを立てる。

---

## 5. 計算リソースと現実

正式計測の正本環境は **bare-metal x86_64 サーバ (env-tag `linux-baremetal`: 96スレ/2NUMA、247GiB、perf HW カウンタ動作)** である。既存の正式測定値・calibration・noise floor はすべてこの env-tag に束縛され、この環境は共有スケジューラ環境が使えない時期の退避先としても残す。開発・ビルド・デバッグは共有スケジューラ型の計算環境 (スパコンのノードをジョブで確保する形) でも行えるが、そこで得た throughput を既存 env-tag の測定値へ混ぜてはいけない。

別環境を正式計測へ採用する条件は
- (1) 専用 env-tag、
- (2) その env-tag での calibration と noise floor の取り直し、
- (3) 計測を走らせるノード上での単独性・静定確認 (スケジューラの割当てを専有の保証と見なさない)、
- (4) module・コンパイラ・CCBench pin・ジョブスクリプトの成果物追跡、

である (凍結済み実験を別 env-tag で取り直さない — D59)。どのマシンをいつ主に使うかは可変状態で worklog を正本とし、マシン固有の確保・実行手順は当該環境の runbook (`docs/README.md` の地図から引く) を正本とする。

CCBench の raw bench だけなら数秒でも、1 evaluation は build・複数 verify・bench・再測を含み数十〜数百秒になりうるため、「一晩の件数」は full pipeline の実測から予算化する。スケール (record 数・thread 数) は calibrator が D15 の飽和点または working-set 下限で決める。絶対規律4 (cache 競合の再現) のためのスレッドピンニング要件は env-tag ごとにトポロジが異なる — `linux-baremetal` (96スレ/2ソケット) では `-DLinux`/numactl が要る (ccbench-anatomy.md §7)。単一ソケットのノードでは binding 設計を当該 env-tag の calibration で決め直す。

ただし前述の通りスケールダウンには非線形の落とし穴 (コンテンション率の変化、cache 階層の効き方) があるので、calibrator とスケール感度検出で対処する。

---

## 6. リポジトリ構成と CCBench の扱い

AI システムのリポジトリ + CCBench を submodule で参照する。**submodule は v1 (thawk105/ccbench) を使う** — VLDB 論文の実体で、最適化が交換可能単位で整理されたコーパスが揃っているため (v2 は書き直し中で本プロジェクトの前提を満たさない)。解剖時点のスナップショットは `33d74a3` = CMake 再構成版。現行 submodule pin は `orchestrator/campaign/pin.py` が正本、D38。実物は **10 プロトコル (YCSB 対応は 7: silo/tictoc/mocc/cicada/ermia/si/oze)** ×3カテゴリの最適化フラグ群を持つ (解剖結果は `docs/ccbench-anatomy.md`)。理由:
- CCBench を汚さない (還元すべき差分が綺麗に切り出せる)
- CCBench のバージョンを commit hash で固定 (再現可能)
- CCBench への改変を「パッチ」で管理できる

CCBench の走らせ方: orchestrator が pinned-clean を確認した隔離 worktree (`patchharness.checkout()`、または直列 context) に variant patch を適用 → buildcache で identity を解決・ビルド → `pipeline.evaluate()` が verify/bench と WAL 記録を実行 → context 終了時に revert/破棄と clean assert、の順に固定する。共有 submodule を素の `make → git checkout` で運用しない。

改変の所在は D16 の三分岐に従う:
- 本物のバグ修正は上流 master へ還元、
- trace-hook は `izanagi-trace` ブランチ (submodule pin)、
- patches/ 行きは意図的バグ (broken-silo)・合成 variant (D18)・診断計器 (D20) のみ。

CCBench の protocol は build target、最適化軸と trace 有無は CMake define、read 比率・record 数・thread 数などは gflags で渡す実行時 workload である (Phase 1 タスク0で確認済み)。したがって variant 探索はビルドし直し型だが、build cache は protocol/genome、CCBench commit、TRACE、preprocess 後 source digest、toolchain を identity に含め、同一 build identity のバイナリだけを再利用する。

workload descriptor は build-cache key からは外してよいが、**campaign・evaluation・report identity には必ず含める**。同じバイナリを複数 workload で実行することはできても、certification は `(variant, workload/config)` ごとであり横流ししない。各 workload で perf と同一構成の verify を別に通し (D36)、その組に対する verdict と性能だけを proof chain へ載せる。

CCBench 還元スキーム: 探索中に CCBench 自体の問題を見つけたら `output/insights/` に構造化レポートを吐く。必ず「還元判断: ユーザー確認待ち」を付ける。AI は発見を構造化するところまで、上流に出すかは人間が決める (誤検出 = verifier のバグを CCBench のバグと誤認、を防ぐ関所)。

---

## 7. 関連研究からの借用 — `docs/related-work/` へ分離 (2026-07-05, D35)

関連研究 (Polyjuice/CCaaLF→NeurCC・ATCC の学習型 CC 系譜、ShinkaEvolve/AlphaEvolve/DGM の
進化合成系譜、Jitskit・IDS・VibeServe、SkillOpt・Self-Harness・DecentMem・ARA・
知識労働の経済分析・12-factor-agents・ECC など — 完全な一覧は同文書の逆引き索引が正本) と、
各々から何を借用し何を借用しないかの記録は `docs/related-work/` にある。読むのは論文執筆・ポジショニング検討・新規関連研究の追加時のみ —
日常セッションのブートには不要 (これがこの分離の理由)。本文中・他文書の「§7」参照は同文書を指す。

---

## 8. 本システムの新規性 (ポジショニング)

- Jitskit/IDS/VibeServe 系の evaluator-in-the-loop 合成を、single-node CC の serializability と many-core 性能へ適用する
- CCBench を単なるベンチでなく、ベース選択・実装比較・変異軸の着想に使う **local corpus** とし、機序帰属からアクション空間を広げられる設計にする。P2-4 は実現可能性を支持する一事例で、LLM の因果的必要性は未実証
- 広げた bounded space は機械探索し、各 iteration を fail-closed な正しさ検証と source identity に結ぶ。機械 sweep の勝者もシステム成果に含め、LLM 固有成果とは分ける
- workload descriptor、variant、verifier、性能分布、棄却案を proof chain で結んだ evidence-bound な説明を出す

ポジションは、**コーパス駆動の局所コード合成 × workload 別のハイブリッド探索 × serializability verifier × evidence-bound explanation** の交点に置く。空間外合成 (b1) を主経路とし、他 CC からの移植 (b2) は前提条件をカード化できた場合の拡張とする。精密な先行研究との差分と優先権主張は `docs/related-work/` で管理し、ロードマップだけから「世界初」を断定しない。

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

Phase 2: bounded search の ground truth と対照を作る
  - 全探索・貪欲・ランダム・LLM誘導を同じ予算で比較
  - leading indicators の価値と LLM 固有寄与を分離する
  + critic (指標の解釈), profiler (スケール懸念検出)

Phase 3: workload 特化ハイブリッド合成
  A. EVOLVE-BLOCK + verifier + identity で safe variant loop を成立させる
  B. workload descriptor を第一級入力にし、固定候補の選択と descriptor-conditioned な生成を分けて検証する
  C. WAL/proof chain から evidence-bound な層3材料レポートを生成する
  D. unattended/autonomous を主張する前に、orchestrator から role を呼び反復をセッション非依存化する
  E. 以上の後に cross-protocol と最適化移植 (b2) を判断する
  + planner/coder (分離), auditor (reward hack監査), axis-proposer (軸提案)

Phase 3.5 (任意): population-based evolutionary search
  - 非列挙空間または多様性不足が実測上の律速になった場合だけ着手する
  - population・世代・選択・変異/交叉・migration を実装し、sequential search と区別する
  - MAP-Elites/quality-diversity の寄与を ablation する
  - Open-Ended Evolution はさらに先の任意拡張とし、有限 population-based search と同義にしない
```

各 Phase の詳細タスクは該当する docs/phase<N>.md に。現在どの Phase かの正本は CLAUDE.md「現在地」が指す worklog 末尾と現行 phase doc (roadmap は現況を主張しない)。

---

## 10. スコープ外 (明示的にやらないこと)

- 完全な形式証明 (IDS式 Rocq) — 将来拡張。C++ many-core 実装の形式化が重すぎる
- Open-Ended Evolution の完全機構 — Phase 3.5 以降に予約。初手で入れると失敗の切り分けができなくなる
- ECC のような汎用ツール化・多言語・marketplace — 単一研究目的に不要
- 層1 の凝った選定器 — 既存研究が強く、同一条件の seed/baseline 比較を越える投資は主題から外れる
- **列挙可能な軸で LLM が機械探索を上回ることを成功条件にすること** — 役割分担に反し、P2-5 の negative result も無視する
- **制約なしのコード生成** — `EVOLVE-BLOCK`、designated source、verifier を外した生成は比較可能性と正しさを失う
- **アブレーションなしの因果説明** — workload と勝者の相関や leading indicator との整合だけなら機序仮説に留める
- **sequential loop を進化探索と呼ぶこと** — population/世代/選択/変異等が実装・評価されるまでは用語を予約する
- **論文執筆・推敲そのもの (narrative 生成)** — Izanagi のスコープ外。Izanagi は材料レポート (ARA 的 artifact) の生成までを担い、自動執筆は別システムに委ねる (D12)
- **ARA Compiler (フォーマット変換器)** — CCBench は既に構造化済みの C++ コーパスで変換対象が存在しない。取り込めば純粋なスコープ膨張 (規律5)
- **ARA Live Research Manager (背景監視による推測的ハーベスティング)** — Izanagi の orchestrator は各 variant 評価を能動的・決定論的に WAL へ書く設計なので、自由形式セッションから研究イベントを事後収集する機構の必然性が薄い (規律5)。7種イベント taxonomy と ai-suggested の人間確認ゲート思想のみ、decisions.md / output/insights/ のエントリ構造化と roadmap 改訂セレモニーの人間確認に響く思想参照として留める (機構は実装しない)

OEE について補足: 完全機構 (新規性報酬・無限走行) は Phase 3.5 より先の任意拡張に回すが、安い果実は初手から取る — (a) archive に特性の違う variant を複数残す、(b) whiteboard memory (既に採用)。この多様性保存だけでは、population-based search や OEE を実装・実証したことにはならない。
