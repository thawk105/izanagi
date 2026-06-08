# Izanagi ロードマップ — 全設計と理由

**版: v1 (初期設計)。** 本ドキュメントは living document であり、試行錯誤の発見に応じて Claude が改訂してよい (改訂規律は CLAUDE.md の「roadmap の更新」参照)。過去の版は docs/roadmap-history/ に凍結保存されており、設計仮説の変遷そのものが研究記録 (論文の方法論セクションの原料) になる。

このドキュメントは、本システムの設計のすべてとその理由を記録する。次の作業者 (人間または Claude) が、設計に至った議論を見ていなくても「なぜこうなっているか」を完全に追えることを目的とする。

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
層2: 最適化移植ループ (進化探索)
   最適化抽出 → variant生成 → 評価(正しさ+性能) → 取捨選択
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
- 層2 の進化ループが十分強ければ、ベース CC が多少サブオプティマルでも吸収される。AlphaEvolve 系の経験則として、初期個体の質より mutation operator と evaluator の質が支配的

実装方針: ヒューリスティック + 数回のベンチで十分。「read-heavy & low-contention → OCC系 (Silo/TicToc)、write-heavy & high-contention → 2PL系/MOCC、long-read混在 → MVCC系」程度のルールで初期個体を2-3個選び、軽くベンチして一番マシなものをシードにする。**複数シードから並列に進化させる方が良い** (island model)。

LLM を使うなら「選定ロジック」ではなく「なぜこの workload にこの CC か、を CCBench の insight を引用しながら説明させる」方。これは層3の説明生成の伏線になる。

### 層2 — 最適化移植ループ (心臓部)

#### 最適化の粒度: まずパラメータ寄り、余力があればコード移植

3段階の選択肢がある:
- **(a) パラメータ粒度 (Polyjuice式)** — 最適化を事前定義フラグ/数値にする。LLM ほぼ不要、新規性低いがロバスト
- **(b) コード粒度 (AlphaEvolve式)** — CCBench 内の特定関数を `EVOLVE-BLOCK` で囲み LLM に diff を書かせる。新規性高い、本構想の本丸
- **(c) アルゴリズム粒度 (FunSearch式)** — ゼロから書かせる。自由度高すぎて正しさが崩壊。CC では非推奨

**決定: まず (a) を主軸。Phase 3 で (b) を足す。(c) はやらない。**

(a) を選ぶ利点 (本プロジェクトの状況で特に効く):
- パラメータ粒度なら生成 variant は「CCBench が元々持つ最適化フラグの組み合わせ」だから理屈上は全部正しいはず。これは trace verifier を検証するのに最高の環境 (Phase 1 のゴールと噛み合う)
- 探索空間が有限 (CCBench の最適化が主に on/off なら高々 2^7=128 + 連続パラメータ数個)。**初手は全探索すら可能**。全探索の最適と LLM 探索の到達速度を比較でき、論文の図になる
- (a)→(b) の移行が自然。パラメータ探索で「invisible reads を on にすると効く」が分かった後、コード移植で「その実装そのものを別 CC 文脈に移植できるか」に進む

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

#### 探索戦略

AlphaEvolve/CodeEvolve の island-based GA を借りるのが堅い。ただし CC は評価が高コスト (1 variant = 数十秒のベンチ)。緩和策:
- **low-fidelity proxy**: 本ベンチ前に短時間 (1-2秒) の軽量ベンチでスクリーニング
- **LLM に次の一手を考えさせる**: ランダム変異でなく、過去の試行結果を context に入れて「このワークロードでは delay-on-conflict 系が効いているから次は wait-die 系を試せ」と方向づけさせる。これが LLM-evolution の最大の強みで、ただの GA より遥かに少ない試行で収束しうる

### 層3 — variant 比較・選択 + 説明生成 (差別化の決定打)

Polyjuice/CCaaLF が絶対に出せないのが「なぜ」の説明。Izanagi は層2で試行ログ (どの最適化を入れたら性能がどう動いたか) が全部残るので、LLM に食わせて因果込みのレポートを生成する:

> 「このワークロードは write-heavy かつ中コンテンション。ベースに MOCC を選んだ理由は [CCBench I3: wait/no-wait の有効性は状況依存]。そこに Silo の invisible reads を移植したところ12%向上 (理由: read-heavy phase での cache 汚染削減、I2と整合)。一方 TicToc の timestamp 最適化は移植したが3%悪化したため不採用 (理由: MOCC の temperature tracking と timestamp 管理が二重コストになった、I5の実例)」

(上の数値は narrative の例示。**実際の採否では §3.6 に従い、3% のような noise floor 以下の差は「差なし」に丸め、採否根拠にしてはいけない。** 12% のような差も中央値・CV・有意性を添えて初めて主張になる。)

これは単なるオマケでなく研究としての主張そのもの。「AI が CC を合成した」だけなら半分既存研究だが、「AI が CC を合成し、その設計判断を人間が検証可能な形で説明した」は新しい。

---

## 3. 評価器 (evaluator) の設計

evaluator が本システムの成否を分ける。AlphaEvolve/Jitskit/IDS すべてが「evaluator こそが loss 関数であり、その質がすべてを決める」と言っている。

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
- (採用済み) ビルド等価性の機械検証: trace-enabled と trace-disabled を同じ workload・同じ seed で走らせ、最終 DB 状態 (全レコードの値) が一致するか比較。一致すれば「トレース有無で CC の意味論は変わっていない」の傍証

### 3.4 reward hacking 対策 (Jitskit §3.2, Appendix B より)

LLM は最適化圧力の下で、書かれていない不変条件を破って性能を稼ぐ。CC 版で起きうるもの:
- 「検証用 trace が見ていないアクセスパターンでだけ正しい CC」を作る → 対策: seed を変えた複数 run で毎回検証
- 「導出可能な ground truth を突く」(値を保存せず再計算) → 対策: 値に再構成不可能なエントロピーを持たせる
- 「探索の自己崩壊」(これ以上は失敗すると恐れて最適化をやめる) → 対策: 探索ポリシー側で継続を促す

これらに対し:
1. **据え置きの正しさゲート** — 壊すと即 reject。「絶対壊しちゃダメ」(serializability anomaly検査、ACID基本) と「壊れていい」(プロトコル固有テスト、variant のキャラクタライズに使う) を分ける
2. **adversarial auditor** (Phase 3 で導入) — N iteration ごとに variant を監査、verifier が見逃した不変条件違反を見つけてテストを追加
3. **hooks による書き込み時防壁** (Phase 1 から薄く) — 観測者効果違反・verifier 迂回を機械的に弾く

### 3.5 leading indicators (収束に必須)

Jitskit が実証: スカラーの throughput だけ渡すと探索は 8-12 iteration で停滞しランダム化する。leading indicator (lock contention / cache hit率 / I/O / memory帯域) を毎 iteration LLM に渡すことが収束に必須。「write-only は allocator contention で診断、read-heavy は cache hit率で診断」のように、どの指標が効くかは workload による。

これは「FlameGraph を見て many-core でヤバいか判断してほしい」という当初の直感の正式版。perf プロファイリングは有望な variant にだけ回す (二段構え: screening 通過 → profiling)。

### 3.6 測定の安定性 (measurement stability)

性能数値は「1 run の点」ではなく「**反復測定の分布**」として扱う。他ユーザー・他プロセス・温度スロットリング等の外乱は一晩の自動ループでは必ず混入するが、人間の「あれ?」は介在しない。だから**ばらつきの監視と再測定を実行時の気まぐれに委ねず、規律として明文化・自動化する**。これは絶対規律1 (観測者効果の分離) / §3.4 (reward hacking 対策) と同じ構造の汚染防止であり、reward hacking の鏡像 ——「**ノイズを最適化シグナルと誤認する**」—— への対策でもある。

**(1) 反復と要約.** 1 measurement = N 回反復 (初期値 N=5、calibration で調整)。各 run の冒頭は warmup として破棄し定常状態のみを採る。報告は単一の throughput でなく **中央値 + 散布度 (変動係数 CV / IQR)** を必ず持つ。WAL (output/runs/) には個々の run 値も残し、後から分布を再構成できるようにする。

**(2) 外れ値検出 → 自動再測定 (=「あれ?」の機械化).** 反復内の CV が閾値 (初期 5%) を超えたら「測定が外乱で歪んだ」とみなし**自動で測り直す**。再測定の前に Admission Control の静定確認 (load average 静定) を必ず通す。規定回数 (初期 3 ラウンド) 測っても CV が収束しなければ、その variant に **`unstable` フラグ**を付けて分布比較から除外し、insight に「測定不能」として記録する。沈黙して 1 点を採用してはいけない。

**(3) noise floor の実測.** 「この差は信じてよいか」の下限を勘で決めない。calibration フェーズで baseline を連続 N 回測って CV を実測し、それを **noise floor** として固定する (§4)。これは環境タグ (mac-devcontainer / linux-baremetal) ごとに持つ。Mac devcontainer は VM 越しで noise floor が大きく出るはずで、その数値自体が「ここでは性能比較するな」(D10) の定量的裏付けになる。

**(4) 採否は点比較でなく分布比較.** variant vs baseline の優劣判定は単一値の大小でなく**分布の比較**で行う:
- 差が noise floor 以下なら「**差なし**」に丸める。層3 narrative の「3%悪化だから不採用」のような **noise floor 以下の差を採否根拠にしてはいけない** (3% はラップトップ/devcontainer ではほぼノイズ)
- noise floor を超える差については、信頼区間の重なり、または分布フリーな検定 (Mann-Whitney U 程度で十分) で有意性を判定する。重い統計機構は要らない
- 層3 のレポートは差分値だけでなく **「N 回測定の中央値、CV、noise floor、有意か否か」** を添える。これは「なぜこの variant を採った/外した」の説明可能性 (本システムの差別化の核心) を統計的に裏打ちする

**(5) スコープ.** Phase 1 では (1)(3) を骨格として実装 (calibrator が noise floor を出し、ベンチが反復+中央値+CV を返す)。(2)(4) は性能採否が実際に走る Phase 2 で必須化する。Phase 1 は Mac devcontainer 中心で性能採否をしない (D10) ため、(2)(4) は配線だけ用意して Linux 実機到着後に有効化する。

---

## 4. レコード数の自動キャリブレーション

実験パラメータ (レコード数) を、measurement validity を保ちつつ最小コストになるよう自動決定する。これは CC 探索とは別レイヤーなので分離する (calibrator が担当)。

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

注意: 飽和点は thread 数に依存する。探索に使う thread 数を決めたらその thread 数でキャリブレーションする。thread 数を変えたら測り直し。

LLM の役割は数値を見て判断 + 説明し、`output/insights/` に妥当性を文書化すること。査読で必ず問われる「なぜそのレコード数?」に先回りで答えられる。

**noise floor の実測 (§3.6 と接続).** calibrator はレコード数の飽和点に加えて、その環境の **noise floor** も実測する責務を持つ。確定した実験条件 (レコード数・thread 数) で baseline を**連続 N 回**測って throughput の CV を出し、「この差以下は信用するな」の下限として固定する。これは環境タグごと (mac-devcontainer / linux-baremetal) に持ち、§3.6(4) の分布比較が「差なし」に丸める閾値の根拠になる。Mac devcontainer で noise floor が大きく出ること自体が D10 (性能比較は Linux 実機のみ) の定量的裏付けになる。あわせて、ベンチ前の load average 静定確認 (admission control、orchestrator-design.md) も calibrator の責務に含める。

スケール感度の検出: variant 評価を単一スケールでやらず最低2点で測る (small: 4thread/100万, medium: 10thread/1000万)。「small→medium での性能の伸び方」を特徴量として LLM に渡し、small で良いのに medium で頭打ちの variant は「スケールしない疑い」とフラグを立てる。これが層3の「なぜこの variant を最終選択から外したか」に直結する。

---

## 5. 計算リソースと現実

初手はローカルラップトップで回しっぱなしで良い。CCBench の VLDB 論文は 1run 3秒程度。1億レコード/100thread をスケール落として 1000万レコード/10thread にすればラップトップで回る。3秒/run なら一晩 (8時間) で約1万 run。sample 効率の心配はかなり緩む。

ただし前述の通りスケールダウンには非線形の落とし穴 (コンテンション率の変化、cache 階層の効き方) があるので、calibrator とスケール感度検出で対処する。

---

## 6. リポジトリ構成と CCBench の扱い

AI システムのリポジトリ + CCBench を submodule で参照する。**submodule は v1 (thawk105/ccbench) を使う** — VLDB 論文の実体で、7プロトコル×7最適化のコーパスが揃っているため (v2 は書き直し中で本プロジェクトの前提を満たさない)。理由:
- CCBench を汚さない (還元すべき差分が綺麗に切り出せる)
- CCBench のバージョンを commit hash で固定 (再現可能)
- CCBench への改変を「パッチ」で管理できる

CCBench の走らせ方: orchestrator が patches/ を適用 → cd external/ccbench && make → 走らせて output/runs/ にログ → 実験後 git checkout で ccbench をクリーンに戻す。これで「CCBench本体は常にクリーン、改変は patches/ に明示的に存在」が保てる。

trace 吐く口 — ビルド時 vs ランタイム: CCBench の最適化フラグが `#define` (ビルド時) かランタイムかで探索ループの形が変わる。CCBench は性能ベンチなのでおそらく多くがビルド時 `#define`。だとするとパラメータ探索は「ビルドし直し型」になり make 時間が評価コストに乗る (緩和: 組み合わせごとにバイナリをキャッシュ)。**これは Phase 1 タスク0 で実物を読んで確認する最優先事項。**

CCBench 還元スキーム: 探索中に CCBench 自体の問題を見つけたら `output/insights/` に構造化レポートを吐く。必ず「還元判断: ユーザー確認待ち」を付ける。AI は発見を構造化するところまで、上流に出すかは人間が決める (誤検出 = verifier のバグを CCBench のバグと誤認、を防ぐ関所)。

---

## 7. 関連研究からの借用

### Polyjuice (OSDI 2021) / CCaaLF (2025)
層2の思想的祖先。CC をアクション (wait粒度 / dirty read有無 / write expose / early validation) に分解して進化的に学習。ただし両者は「事前定義したアクション空間の中での最適配合探索」。Izanagi の (b) コード移植は「アクション空間自体を LLM が拡張する」点で質的に違う。

### Jitskit (arXiv 2605.24096)
KVストアをワークロード仕様から丸ごと合成。本システムの設計レベルの予言書。借用:
- **spec cards (3枚)**: 環境カード / ワークロードカード / 要求カード。要求カードが isolation level を定義する (保留だった「対象 isolation level をどこで決めるか」がこれで解決)
- **reward hack カタログ**: §3.2 と Appendix B。CC 版に翻訳して自前のギャラリーを作る
- **leading indicators**: 収束に必須 (§3.5)
- **adversarial auditor**: N iteration ごとに監査しテストを増やす
- **planner/coder 分離**: コードに引きずられず構造を考えるため。Phase 3 で効く
- **whiteboard memory**: 却下した設計を蓄積。output/insights/ と統合

### IDS (arXiv 2605.23109)
コードと証明を同時に育てる verified synthesis。借用は「思想」:
- **正しさを後付けにしない**: verifier を毎 iteration 回し、構造化診断を LLM に返す (単なる accept/reject に落とすと性能が激減する、と ablation で実証)
- 完全な形式証明 (Rocq) 自体は初期スコープ外 (C++ many-core 実装の形式化が重すぎる、decisions.md 参照)

### VibeServe (arXiv 2605.06068)
LLM serving システムを deployment target ごとに bespoke 合成する agentic loop。outer loop が永続計画状態 (issues / long-term memory / git commit graph) 上で探索を計画し、inner loop の Implementer / Accuracy Judge / Performance Evaluator が候補を実装・検証・計測する。Jitskit/IDS と同系譜で、「単一汎用システム」から「ターゲット特化の自動合成」へという賭けが Izanagi と同じ。Accuracy Judge の reward-hacking 検査は Jitskit の auditor と同思想。outer loop の永続状態は orchestrator-design.md の D (durability) の先行例。

### ECC (github.com/affaan-m/ECC)
Claude Code の運用パターンの参考。借用は3点だけ (巨大さは反面教師):
- agent定義に `tools` と `model` を明示。verifier には書き込み権限を与えない (見張り役をツール権限で隔離)
- hooks で規律を機械執行 (観測者効果違反・verifier 迂回を書き込み時に弾く)
- continuous-learning/instinct は whiteboard memory の進化形として将来予約

---

## 8. 本システムの新規性 (ポジショニング)

- Jitskit は KVストア、IDS は分散KVの consistency。**誰も single-node の CC protocol の serializability を対象にしていない**
- 両者とも「ゼロから合成」か「証明付き合成」。Izanagi の「既存 CC (CCBench) を解析して最適化を移植する」コーパス駆動の合成は空きポジション
- CCBench という「7プロトコル×7最適化が交換可能単位で整理された資産」を使う点が独自

ポジション: **Jitskit/IDS のループ方法論を継承しつつ、対象を CC の serializability にし、合成方式を CCBench 資産からの最適化移植にする。** 系譜の3本目として乗れる。

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

Phase 3: コード移植
  - EVOLVE-BLOCK で他CCの最適化を LLM が移植
  + planner/coder (分離), auditor (reward hack監査)

Phase 3.5 (任意): Open-Ended Evolution
  - コード移植でアクション空間が開いて初めて意味を持つ
  - 多様性保存を完全な MAP-Elites/quality-diversity に格上げ
  - ablation で OEE 有り/無しの探索効率を比較
```

各 Phase の詳細タスクは該当する docs/phaseN.md に。現在は Phase 1 = `docs/phase1.md`。

---

## 10. スコープ外 (明示的にやらないこと)

- 完全な形式証明 (IDS式 Rocq) — 将来拡張。C++ many-core 実装の形式化が重すぎる
- Open-Ended Evolution の完全機構 — Phase 3.5 に予約。初手で入れると失敗の切り分けができなくなる
- ECC のような汎用ツール化・多言語・marketplace — 単一研究目的に不要
- 層1 の凝った選定器 — 既存研究が強く、層2が吸収するため軽くて良い

OEE について補足: 完全機構 (新規性報酬・無限走行) は Phase 3.5 に回すが、安い果実は初手から取る — (a) 多様性の保存 (層3で「throughput最強の1個」でなく特性の違う variant を複数残す)、(b) whiteboard memory (既に採用)。
