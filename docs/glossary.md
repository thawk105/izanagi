# 用語集 — izanagi の docs で説明なしに使われる非自明用語

**この文書は何か。** izanagi の docs / insights は、並行性制御・探索理論・統計・本プロジェクト固有の機構にまたがる専門用語を、多くの場合「読み手は知っている」前提で説明なしに使っている。本用語集は、**専門外の読み手 (並行性制御は知っていても探索理論や統計、izanagi 固有機構には疎い査読者・将来の自分)** が docs を追えるように、それらの用語を平易に定義する。

**位置づけ (戦術文書)。** 各定義は「教科書レベルで何を意味するか」+「izanagi ではどう使われ、なぜ効いているか」の 2 段で書く。正典 (定義の最終根拠) はあくまで各 docs / decisions.md の本文であり、本用語集は理解の補助線。定義は執筆時点 (2026-07-03) のもの。用語の綴りは docs の表記に合わせる (英語のままの技術語も docs の慣用に従う)。

**読み方。** 各項目は `**用語 (読み・展開)** — 平易な定義。*izanagi:* プロジェクトでの使われ方 (参照先)。` の形。関連の深い用語は近くに置いた。

---

## 1. 探索・進化・最適化

izanagi の探索ループ (層2) と Phase 2 主実験 (P2-5) を読むための用語。

**貪欲 (どんよく, greedy)** — 各手番で目先で最良に見える手を選び続け、先読みせず勾配だけを追う最適化戦略。*izanagi:* LLM 抜きで指標の限界効果 (フラグ 1 個反転の差) の勾配だけで次手を選ぶ機械的基準線。これを超えなければ「LLM 固有の知能」は無価値、という切り分けの対照 ([2026-06-29 insight](../output/insights/2026-06-29_p2-5-guided-vs-enumeration.md))。

**オラクル天井 (oracle ceiling)** — 常に正解を知る仮想的な選び手 (神託 = oracle) でも達成できる速さの理論上限。どんな賢い戦略もこれ以上速く正解に到達できない、という性能の天井。*izanagi:* silo の 8 通り空間で最適到達に要する評価回数の下限を `2 − k/N` で見積もり、誘導や貪欲がそこにどれだけ近いかを測る物差し。天井が低いこと自体が「空間は自明」の証拠になった (phase2.md §P2-5)。

**deceptive 構造 (デセプティブ, deceptive landscape)** — 「一見良さそうな手がかりが実は最適から遠ざける」ように配置された探索地形。有望に見える方向を素直に辿ると罠にはまる、最適化の古典的難所。*izanagi:* write-heavy では「abort が少ない = 良い」という素直な手がかりが 2 位の罠 (BACK_OFF=1) へ誘導し、critic がそこへ誤収束する構造を指す (phase2.md §P2-5, phase3-main-experiment.md「deceptive 相当の検証」)。

**誤収束 (ごしゅうそく, premature / false convergence)** — 真の最適に着く前に劣った解を「答え」と確信して打ち切ること。多様性を失い局所解に張り付く進化計算の失敗。*izanagi:* write-heavy の 12 試行中 8 試行で、critic が真の最速を評価しないまま別構成で確信停止した現象。P2-5 の最重要の失敗モード。

**早期停止 (そうきていし, early stopping)** — 十分と判断した時点で反復を打ち切ること。無駄を省くが、早すぎると最適を見逃す。*izanagi:* critic の「確信したら止める」挙動。balanced では効率化だが、deceptive な write-heavy では誤収束を確定させる負債になった (「自信ある早期停止」)。

**ablation (アブレーション, 除去実験)** — ある要素を足す/抜くで結果を比較し、その寄与を因果的に切り分ける実験手法。*izanagi:* critic 有無・profiler 有無・LLM 有無 (誘導 対 貪欲) を比較して各部品の効果を測る。段階導入 (規律5) は各機構を後から ablation できるように足す方針。

**negative result (ネガティブリザルト, 否定的結果)** — 「仮説が支持されなかった」ことを主張とする研究結果。単なる失敗と違い知見として価値を持つ。*izanagi:* P2-5 の主成果。「小空間ではフラグ探索は自明で LLM 誘導は機械的貪欲を超えない」を定量化し、「価値は空間の外の合成にある」という Phase 3 の動機づけにした。

**reward hacking (リワードハッキング, 報酬ハッキング)** — 最適化圧力が本来の目的でなく評価指標の抜け穴を突いて高スコアを得る現象。指標は満たすが実質は破綻する。*izanagi:* LLM variant が「検証を甘くして性能を稼ぐ」方向へ変異するのを絶対規律2 で禁じる際の対策対象そのもの。「最適化圧は必ず正しさを攻撃しに来る」の根拠 (decisions.md D22)。

**winner-tied set / equivalence class (等価クラス)** — 最速のものと測定ノイズの床 (floor) 以内で並び「実質差なし」と判定できる候補の集合。*izanagi:* 探索がいつ正解に着いたと数えるかの定義。読み手 (pivot) に依存せず到達判定できるようにするための工夫 (phase2.md §P2-5)。

**low-fidelity proxy (低忠実度プロキシ)** — 本番の高コスト評価の前に、短時間・低精度の簡易評価で候補を粗くふるいにかける代理指標。*izanagi:* bench-first screening v2 は 2026-07-15 に実装済み (D58、監査 must-fix 対応込み)。偵察 sweep / 8b の opt-in に限り、正式な correctness gate や S-1 には使わない (phase3.md「現行チェックポイント」)。

**island model (島モデル)** — 集団を複数の小集団 (島) に分け別々に進化させ時々個体を交換する、多様性を保ち早期収束を防ぐ進化計算手法。*izanagi:* 現行 sequential/hybrid search の機構ではない。多様性不足が実測で律速になったとき population/世代/migration を実装する任意拡張 (roadmap.md §2 層2 / Phase 3.5)。

**Pareto front (パレートフロント, 非劣解集合)** — 複数目的の同時最適化で「どの目的も犠牲にせずには改善できない」解の集合。1 勝者でなくトレードオフ上の最良候補群。*izanagi:* 複数目的が実際に登録された場合だけ層3の選択に使う任意手段。単一目的の現行系や進化探索の必須要件ではない。

**MAP-Elites / quality-diversity (クオリティダイバーシティ)** — 最良 1 個でなく特徴空間のニッチごとに最良個体を保存し、質と多様性を同時に得る進化計算アルゴリズム群。*izanagi:* Phase 3.5 (任意) で多様性保存を本格化する将来オプション。今は安い果実 (複数 variant 保存) だけ取り、完全な機構は予約する (規律5)。

**spec cards (仕様カード)** — 合成の入力要求を数枚の構造化カード (環境・ワークロード・要求) に分けて曖昧さを排す様式 (Jitskit 由来)。*izanagi:* ワークロード入力を 3 枚のカードで与え、要求カードが対象の分離レベルを定義する (三層アーキテクチャの入口, related-work/ §Jitskit)。

**workload descriptor (ワークロード記述子)** — 探索対象の workload を自由文でなく型付きフィールドで表した入力。*izanagi:* read/write 比率・競合水準・scale・最適化目的・正しさ制約を持ち、勝者名や未観測性能値は含めない。build-cache identity でなく campaign/evaluation/report identity に入り、8b で第一級入力へする (roadmap.md §1/§6, phase3.md 段8b)。

**whiteboard memory (ホワイトボードメモリ)** — 却下した案や失敗した試行を「やるな記憶」として捨てず蓄積し、後の判断に活かす記憶機構。*izanagi:* `output/insights/` に却下設計・行き止まりを構造化して蓄積する運用。関連研究 (SkillOpt / DecentMem の二プール記憶) が外部裏付け (related-work/ §SkillOpt / §DecentMem)。

**replay (リプレイ, 再生)** — 新規に計測し直さず、記録済みの測定値を配って探索や解析を回すこと。*izanagi:* P2-5 は P2-2 で実測済みの全 8 通りの値を再生するだけで完結し、新規の直列計測をゼロにした (絶対規律4 のコスト 0)。

**事前登録 (じぜんとうろく, pre-registration)** — 実験前に仮説・比較対象・検定方法を確定・公開し、結果を見てから基準を後付けする (p-hacking) のを防ぐ研究規律。*izanagi:* Phase 3 主実験の主張・比較集合・失敗条件・統計計画を反証可能な形で着手前に固定し、過剰主張を構造的に防ぐ (phase3.md 新設節)。

**validation gate (検証ゲート)** — 検証セットで性能が悪化しない編集だけ採用し他は捨てる、採否の関所。*izanagi:* 関連研究 (SkillOpt / Self-Harness) の機構で、絶対規律2 (正しさゲートを壊す variant は reject) と構造同型と位置づける (related-work/ §SkillOpt / §Self-Harness)。

**OEE (Open-Ended Evolution, 開放型進化)** — 到達目標を固定せず新規性そのものを報酬に無限に探索を続ける進化のパラダイム。*izanagi:* 有限の population-based evolutionary search とは別で、そのさらに先の任意拡張。初手で入れると失敗の切り分けができない (roadmap.md Phase 3.5, decisions.md D9)。

---

## 2. 並行性制御・データベース (トランザクション理論)

CCBench のプロトコル群と、正しさ検証 (verifier) を読むための用語。

**serializability (直列化可能性)** — 並行実行の結果が、何らかの順で 1 個ずつ直列実行した結果と一致すること。並行実行の正しさの最も強い基準。*izanagi:* verifier が守る正しさゲートの中身。これを破る variant は性能が出ても無価値 (絶対規律2)。

**isolation level (分離レベル)** — トランザクションが互いの中間状態をどこまで見せないかの強度の段階。強いほど異常は減るが並行性は落ちる。*izanagi:* 要求カードが対象の分離レベルを定義し、variant が「宣言した分離レベルで通るべき/落ちるべきテスト」の集合を固定する。

**Adya の serialization graph / DSG (直列化グラフ)** — トランザクションを節点、依存を有向辺とし、閉路 (cycle) があれば直列化不能と判定するグラフ (Adya の理論)。*izanagi:* verifier が trace から構築する依存グラフそのもの。閉路検出が anomaly 検出の核 ([isolation-phenomena.md](isolation-phenomena.md))。

**ww / wr / rw 依存 (write-depends / read-depends / anti-depends)** — トランザクション間の 3 種の依存。ww=両方が同じ物を書く順序、wr=片方の書きを他方が読む、rw=片方が読んだ物を他方が後で書く (anti-dependency)。*izanagi:* 依存グラフの辺の種類。単純な read/write ワークロードならこの 3 種で辺が張れる。

**G2 / anti-dependency cycle** — rw 依存 (anti-dependency) を含む直列化異常の閉路。直列化可能性を狙うならここまで検出が必要 (弱い判定では見逃す)。*izanagi:* verifier が検出すべき最重要の異常。broken-silo パッチが確実に G2 の赤を出すことで verifier の「赤を出せる」能力を実証する。

**G0 / G1a / G1b / G1c、PL-1 / PL-2 / PL-3** — Adya が定義した分離異常 (phenomena) とそれを禁じる分離レベルの階層。G0=dirty write、G1=dirty read 系、G2=上記、PL-3 が直列化可能に対応。*izanagi:* verifier が「どの異常まで見るか」を厳密に位置づける語彙 (isolation-phenomena.md §phenomena)。

**write-skew (書き込みスキュー)** — 2 つのトランザクションが互いの読んだ範囲を書き換え、個別には正しいが全体で制約を破る異常。SI で起きる代表的な G2 異常。*izanagi:* SI 系プロトコルの正しさ検証の典型的な検出対象 (isolation-phenomena.md §phenomena)。

**phantom / 述語異常 (predicate anomaly)** — 「条件に合う行の集合」への操作の途中で、別のトランザクションがその集合に行を出し入れして生じる、単一行の依存では捉えられない異常。*izanagi:* 検証の射程を確認するための語彙 (isolation-phenomena.md §スコープ外)。

**OCC (楽観的並行性制御, Optimistic CC)** — 衝突は稀と楽観し、実行中はロックせず走り、コミット直前にまとめて競合を検証する方式。競合が少ないと速い。*izanagi:* Silo/TicToc が属する系。read-heavy・低競合で強い (ccbench-anatomy.md §2)。

**2PL / SS2PL (strong strict two-phase locking)** — データに触れる前にロックを取り、トランザクション終了までロックを保持する悲観的並行性制御。競合が多いと安定。*izanagi:* OCC の対極として write-heavy・高競合で候補になる系。

**MVCC (多版並行性制御, Multi-Version CC)** — 各データの複数バージョンを保持し、読みは過去の一貫したスナップショットを見る方式。読みと書きが互いにブロックしにくい。*izanagi:* long-read 混在ワークロードで候補になる系。

**MOCC (Mostly-Optimistic CC)** — OCC を基本に、競合が激しい「熱い」レコードだけ悲観的にロックする混合方式。*izanagi:* CCBench のプロトコルの 1 つ。record temperature で熱さを追跡する (ccbench-anatomy.md §2)。

**Silo / TicToc / Cicada / ERMIA / SI (si) / oze / MOCC** — CCBench に載る並行性制御プロトコル群。Silo=epoch ベース OCC、TicToc=タイムスタンプを動的に決める OCC、Cicada=多版 + タイムスタンプの高速 MVCC、ERMIA=SSN 付き SI、SI=スナップショット分離、oze=CCBench 独自系。*izanagi:* 合成の素材コーパス。YCSB 対応は 7 プロトコル、kickoff は Silo に閉じる (ccbench-anatomy.md)。

**Snapshot Isolation (SI, スナップショット分離)** — 各トランザクションが開始時点の一貫したスナップショットを読み、書き込み衝突だけを検出する分離方式。直列化より弱く write-skew を許す。*izanagi:* si プロトコルの基盤。SSN を足すと直列化まで上げられる。

**SSN (Serial Safety Net) / SSI (Serializable SI)** — SI に「危険な依存構造を検出して中断する」安全網を足し、直列化可能まで強める技法。*izanagi:* ERMIA が SI を直列化にするのに使う (ccbench-anatomy.md §2)。

**no-wait / wait-die / delay-on-conflict** — 競合時の待ち方の戦略。no-wait=待たず即 abort、wait-die=優先度で待つか死ぬか決める、delay-on-conflict=一定時間遅延させる。*izanagi:* Silo は no-wait (競合即 abort)。この選択が liveness (デッドロック回避) を左右し、正しさとは別軸 (ccbench-anatomy.md §3)。

**backoff (バックオフ, 指数バックオフ)** — 競合で失敗したとき、次の再試行までの待ち時間を (しばしば指数的に) 延ばして衝突を間引く手法。*izanagi:* P2-4 のケーススタディの主役。abort 時のスピンを制御し、静的 backoff の合成が高競合域で stock 最良を上回った。write-heavy では罠 (deceptive) の源にもなる (ccbench-anatomy.md §3)。

**invisible reads (不可視読み)** — 読み取り時に共有メタデータを書き換えず、他コアのキャッシュを汚さない読み方。read が多いときキャッシュライン競合を減らす。*izanagi:* Silo 由来の最適化。Phase 1 で on/off と正しさ・性能差を検証した題材 (ccbench-anatomy.md §3)。

**epoch (エポック, Silo の epoch)** — Silo が一定間隔で進めるグローバルな世代番号。コミット順序をこの粒度でまとめ、タイムスタンプ競合を減らす。*izanagi:* verifier が読む trace のコミット識別子 `(epoch, tid)` の一部 (ccbench-anatomy.md §4)。

**TID / Tidword (トランザクション ID)** — Silo が各コミットに振る識別語。状態ビットや順序を詰め込む。*izanagi:* trace のコミットイベントが emit する識別子。verifier の順序復元に使う。

**rts / wts (read-timestamp / write-timestamp)** — タイムスタンプ順序方式で各データに付く「最後に読まれた/書かれた時刻」。順序の妥当性判定に使う。*izanagi:* TicToc/Cicada 系の内部状態を読むための語彙 (ccbench-anatomy.md §2)。

**record temperature / temp_threshold (レコード温度, MOCC)** — レコードごとの競合の激しさ (熱さ) を数値で追跡し、閾値を超えたら悲観ロックに切り替える MOCC の仕組み。*izanagi:* MOCC の最適化を移植するとき「TicToc のタイムスタンプ管理と二重コストになる」等の競合を判定する対象 (ccbench-anatomy.md §3)。

**zipf skew (zipfian 分布のスキュー)** — アクセスが一部の人気キーに偏る度合い。高いほど同じキーへの競合が増える。*izanagi:* ワークロードの競合度を決めるパラメータ。calibration は skew=0.9 で固定した (ccbench-anatomy.md §3)。

**deadlock (デッドロック) / wait-for graph (待ちグラフ)** — 複数のスレッドが互いの保持する資源を待ち合い、どれも進めなくなった状態。待ちグラフは「待ち手 → その資源の実 holder」を辺にした有向グラフで、その閉路がデッドロックの証拠になる。*izanagi:* 「走行が終わらなかったこと」は証拠にしない。受理条件は D791 の 4 つ — 整合した snapshot 上で各辺が実 holder を指し要求 mode が非両立であること、連続 3 snapshot で閉路の全 node の属性と辺の形が同一であること、その間 commit・abort カウンタが不変であること、走行が hard timeout で終わっていること。証拠は計装ビルドのものであり未計装ビルドでの発生率ではない。症状から引く診断手順は `docs/cc-diagnostics.md`。

**livelock (ライブロック)** — 各スレッドは動き続けるが、互いに譲り合って/衝突し続けて全体として前に進まない状態。*izanagi:* no-wait で両者が即 abort し合うと起きうる。Silo の 8 通りから両 0 の組み合わせを除外した理由 (P2-0)。

**ODR (One Definition Rule, 単一定義規則)** — C++ で「同じ実体の定義は 1 つだけ」という規則。破ると未定義動作。*izanagi:* CCBench 側で見つけた本物のバグ (ODR 違反) を上流 master へ還元した事例 (D16)。

---

## 3. 評価・測定・統計

calibrator と測定安定性 (roadmap §3.6)、P2-5 の統計を読むための用語。

**noise floor (ノイズフロア, 雑音の床)** — 測定に必ず乗る揺らぎの下限。この幅より小さい差は雑音で有意と見なせない、という採否の基準線。*izanagi:* 「この差を信じてよいか」を勘で決めないための定量的な床 (roadmap §3.6)。

**within-run / between-run noise floor** — 雑音の床の 2 種。within-run=同一セッション内の連続測定の揺らぎ (1 測定の品質ゲート, 2.28%)、between-run=別セッション間の代表値の揺らぎ (採否の床, 3.0%)。*izanagi:* variant と baseline は別セッションで測るので、採否には between-run を使う。within-run を採否に流用すると偽の「速い」を出す (D19)。

**変動係数 (へんどうけいすう, CV = coefficient of variation)** — 標準偏差 ÷ 平均。散らばりを平均に対する割合で表し、単位の違う量の揺らぎを比較できる。*izanagi:* 反復測定の揺らぎの尺度。閾値を超えたら測定が外乱で歪んだとみなし自動で測り直す (roadmap §3.6)。

**IQR (四分位範囲, interquartile range)** — データを小さい順に並べ、下 1/4 から上 1/4 までの幅。外れ値に強い散らばりの指標。*izanagi:* 中央値と併記する散布度の 1 つ。

**calibration (キャリブレーション, 較正)** — 本番の測定の前に、測定条件 (ここではレコード数) を「妥当性を保ちつつ最小コスト」に自動決定する準備工程。*izanagi:* calibrator が担う。cache miss 率の飽和点または下限基準でレコード数を決め、noise floor も実測する (roadmap §4)。

**飽和点 (saturation point)** — パラメータを増やしても指標がほとんど動かなくなる点。それ以上は時間の無駄。*izanagi:* レコード数を倍々に増やし、cache miss 率が飽和する最小点を採る。飽和が出ない場合 (masstree) は下限基準に切り替える (D15)。

**working set (ワーキングセット, 作業集合)** — プログラムが実際に頻繁に触るメモリの量。これがキャッシュに収まるかで性能が大きく変わる。*izanagi:* 飽和点が出ないとき「working set が L3 キャッシュを K 倍超える最小レコード数」を下限基準にする (D15)。

**L3 / LLC miss (last-level cache miss)** — CPU の最終段キャッシュで目的のデータが見つからず、遅い主記憶まで取りに行く事象。多いほど遅い。*izanagi:* calibration が飽和を判定する主指標。throughput でなくキャッシュ利用率を見る (CCBench I1)。

**cacheline bouncing / cache line 汚染** — 複数コアが同じキャッシュライン (キャッシュの最小単位) を書き換え合い、行がコア間を往復して遅くなる現象。*izanagi:* invisible reads が減らす対象。many-core で正しさ検証専用のメタデータが常駐するとこれを悪化させるので、観測者効果として排除する (phase1.md §タスク5b)。

**IPC (instructions per cycle, 1 サイクルあたり命令数)** — CPU が 1 クロックで実行する命令数。高いほど CPU が有効に働いている。*izanagi:* profiler が読む指標。スピンループのような無駄な命令を分離した「有用 IPC」で backoff の機序を診断した (P2-4)。

**TSC (Time Stamp Counter, タイムスタンプカウンタ)** — CPU が刻むサイクル数の高精度カウンタ。時間計測に使う。*izanagi:* 実測周波数 (1800MHz) を確定して計測の基準にした (decisions.md D15)。

**admission control (アドミッションコントロール, 受入制御)** — 測定を始める前に、システムが静定している (他プロセスの負荷が落ちている) ことを確認してから走らせる関所。*izanagi:* 再測定の前に load average の静定を必ず通す。calibrator の責務 (roadmap §3.6)。

**warmup (ウォームアップ, 暖機)** — 測定の冒頭、キャッシュや分岐予測が定常状態に達する前の過渡区間。通常は破棄する。*izanagi:* CCBench の一括計測に従属するため warmup 分離は意図的に非対応。下限基準がこの影響を実質無効化する (D28)。

**scale sensitivity (スケール感度)** — 小規模では良いのに大規模で頭打ちになる、規模による性能の伸び方の違い。*izanagi:* variant を最低 2 スケールで測り、「小で良いが大で頭打ち」の variant に「スケールしない疑い」フラグを立てる (roadmap.md §4)。

**確率優越 a (かくりつゆうえつ, common-language effect size)** — 2 群からランダムに 1 個ずつ取ったとき一方が他方より良い確率。同分布なら 0.500、引き分けは半分ずつ数える。*izanagi:* 誘導 対 貪欲/random の速さ比較の主指標。旧指標 p_lt が引き分けを勝ちに数えず 0.5 から系統的にずれていた欠陥を D29 で修正した ([insight:96](../output/insights/2026-06-29_p2-5-guided-vs-enumeration.md))。

**p_lt / p_le** — `P(戦略 < random)` と `P(戦略 ≤ random)`。前者は引き分けを勝ちに数えないので、同分布でも 0.5 を下回る系統バイアスを持つ。*izanagi:* D29 で確率優越 a に置換され、下限/上限の括弧として格下げされた旧指標。

**帰無仮説 / 帰無分布 (null hypothesis / null distribution)** — 「効果は無い・差は無い」とする既定の仮説と、その仮説の下でデータが取る分布。これを十分否定できて初めて「効果あり」と主張する。*izanagi:* 「利得が機械 sweep で再現できる = LLM 不要」を帰無仮説に置き、有意性をこの帰無分布との比較で判定 (phase3.md)。

**Mann-Whitney U 検定 (マンホイットニー U 検定)** — 2 群に差があるかを、正規分布を仮定せず順位だけで判定するノンパラメトリック統計検定。少数・非正規データでも使える。*izanagi:* floor を超える差の有意性判定に使うが、反復 5 回では完全分離で常に有意になる弱い sanity。主防壁は floor 丸め (D19)。

**permutation 検定 / exact 検定 (置換検定 / 厳密検定)** — 群のラベルを総当たりで入れ替えて帰無分布を直接構成し p 値を求める、分布の仮定を置かない検定。*izanagi:* 確率優越 a の有意性を、t 検定 (分散縮小を速さと誤認しうる) の代わりに厳密に判定する ([insight:102](../output/insights/2026-06-29_p2-5-guided-vs-enumeration.md))。

**Holm 補正 (ホルム補正)** — 複数の検定を同時に行うとき、偶然の当たりで偽陽性が増えるのを抑える多重比較補正。*izanagi:* 6 検定を通しても誘導が有意でないことを確認する厳しさの担保。

**session-median (セッション中央値)** — 1 セッション (1 run) の反復測定の代表値 (中央値)。*izanagi:* between-run の床は、この session-median どうしの揺らぎで測る (roadmap.md §3.6)。

**複数 seed 検証** — ランダムな seed を変えて検証し、未観測バグを踏む機会を増やす方法。*izanagi:* 検証相で観測証拠を強めるが、1 run の検出確率と独立性を較正していないため `1 − εⁿ` のような数値的保証には変換しない。条件・seed・trace 規模・verdict をそのまま報告する (roadmap.md §3.2)。

---

## 4. 合成機構・identity・オーケストレーション

Phase 3 のコード合成と、探索ループの中枢 (orchestrator) を読むための用語。

**genome (ゲノム)** — 進化計算で 1 個体を表す設計変数の符号列。ここでは 1 つの候補構成 (どのフラグをどう立てたか) の符号化。*izanagi:* Silo の最適化フラグ 1 通り = 1 genome。no-wait の XOR 制約で有効 8 genome。探索の基本単位 (phase2.md 冒頭「目的」)。

**variant (バリアント)** — genome から実際にビルドした 1 つの候補実装。genome が「設計」なら variant は「実体」。*izanagi:* 評価 (正しさ + 性能) の対象。Phase 3 では coder が EVOLVE-BLOCK に書いた差分で生まれる。

**fitness (フィットネス, 適応度)** — 進化計算で個体の良さを表すスコア。最適化の目的関数の値そのもの。*izanagi:* genome の実測 throughput。「実 fitness」は実機計測値、「replay」は記録済み fitness の配布、という対比 (orchestrator-design.md §環境タグ)。

**campaign (キャンペーン)** — 1 回の探索実験のまとまり。その入力・WAL・レポートを 1 つのディレクトリに束ねる単位。*izanagi:* 出力レイアウトの軸。入力依存の成果物 (WAL + レポート) を `output/campaigns/<id>/` に置く。id は内容から決まる (D13)。

**exploration / 探索 (エクスプロレーション、2 義)** — 一般には「未知の候補を試して情報を集める」段階。*izanagi:* 同じ語が 2 つの別物を指す。(a) campaign の **use class** `exploration` — producer が `declared_use_class` で宣言する利用意図の 1 値 (閉表は `official` / `exploration` / `qualification` / `dry`、D528)。campaign root の namespace (`<base>/exploration/campaigns/<id>/`、base の既定は `output/`) と出力先の解決規則を決めるだけで、その測定値が正式標本に入るかは決めない。(b) D1813 の**探索** — 静的 backoff の 1000 マイクロ秒超を測る 2 段構成の第 1 段。探索値は正式標本へ混ぜず、開示だけする (実装は `run_kind = t2418-explore`、D1848)。(b) の探索走は (a) では `official` であり、逆に (a) が `exploration` の campaign (例: A-1 対測定) の標本帰属は (a) の宣言では決まらない。環境変数・job script との対応表は `pegasus-runbook.md` §7.9。

**certify / certified (認証・認証済み)** — variant が特定の workload/config で正しさゲート (直列化検証) を通ったことを確定させること。*izanagi:* certified でない variant は性能に関わらず reject。判定は `(variant, workload/config)` ごとで、同じ binary でも別 workload へ横流ししない。COMMIT を書ける唯一の経路は `pipeline.evaluate()` (phase3.md §kickoff タスク, roadmap.md §6)。

**機序帰属 (きじょきぞく, attribution)** — 観測された性能差を「どの設計選択がなぜ効いた可能性があるか」という機序仮説へ結ぶこと。*izanagi:* critic/profiler の仕事で、単なる数値でなく diff と指標の対応を層3へ渡す。アブレーションなしには因果と断定しない (roadmap.md §2 層3)。

**EVOLVE-BLOCK** — ソースコード中に「ここだけ LLM が書き換えてよい」と明示的に囲った領域。マーカーで画定し、その外は逐語温存する。*izanagi:* coder の編集面を局所化する機構 (P2-4 の inert patch の一般化)。`#if` 枝 (合成) / `#else` 枝 (stock 逐語) の二枝構造 (phase3.md §EVOLVE-BLOCK 機構, D22)。

**hole (ホール, 変異穴)** — 骨格の中で「ここだけ書き換えてよい」と開けた空白部分。周囲の骨格は不可触で、穴の中だけが編集面。*izanagi:* EVOLVE-BLOCK の `#if` 枝の中身。「hole の位置と骨格」はどのソースのどの処理に穴を開け、どんな枠 (マーカー・二枝構造) で囲うかを指す (axis-onboarding.md §2)。

**stock (ストック, 無変異の原型)** — 手を加えていない、供給されたままの状態。変異側 (variant) に対する原型であり比較基準。*izanagi:* CCBench 本来のコード・動作。EVOLVE-BLOCK の `#else` 枝は stock を逐語温存し、性能比較の基準線も stock (D16/D22)。

**source_digest / preprocess 後ハッシュ** — ソースをプリプロセッサ (`cpp -E`) に通した正規化出力のハッシュ値。マーカーコメント有無など「意味に効かない差」を吸収し、実ビルドがコンパイルする中身の同一性だけを見る。*izanagi:* variant の同一性 (identity) を「コードの差」まで正しく捉える一次防壁。方針 A (D30) で偽キャッシュヒット防止の要になった (phase3.md §kickoff タスク, D23)。

**cache_key / variant_id** — ビルドキャッシュの鍵と、WAL 上で variant を一意に指す ID。source_digest を織り込み「同じフラグでも中身が違えば別物」と扱える。*izanagi:* 同フラグ別コードが WAL/critic で取り違えられる穴を塞ぐ (D23)。

**inert patch (イナートパッチ, 不活性パッチ)** — 適用しても既定ではビルド結果を変えない (不活性な) パッチ。合成の骨格や診断計器を、本体をクリーンに保ったまま置く。*izanagi:* patches/ に置く合成 variant・診断計器の形式。既定 (sentinel = -1) で stock と同一ハッシュになることを実証済み (D18)。

**template patch (テンプレートパッチ) / sentinel (センチネル, 番兵値)** — EVOLVE-BLOCK のマーカーと `#else` 枝を人間が一度だけ入れる骨格が template patch。どの枝を選ぶかを決める既定の目印値が sentinel。*izanagi:* coder が触るのは `#if` 枝の中身だけで、骨格は人間専有。sentinel の既定値 (-1 = stock) が不活性を保証する (phase3.md §EVOLVE-BLOCK 機構)。

**straight-line code (直線コード)** — 分岐やループを含まず、上から順に実行されるだけのコード。*izanagi:* EVOLVE-BLOCK の `#if` 枝に許すコードの制約。既存 API を呼ぶ直線コードのみとし、型・ヘッダ・マクロ定義の追加を禁じる (観測者効果の混入防止, phase3.md §EVOLVE-BLOCK 機構)。

**observer effect / 観測者効果** — 測定するために入れた計器 (トレース取得) が、測定対象そのものを歪めてしまう現象 (Heisenbug 的)。*izanagi:* 最重要の計測規律 (絶対規律1)。正しさ検証用の trace は数値マクロ規約の `#if TRACE` でコンパイル時に消し、性能計測ビルドに 1 バイトも残さない (D14, orchestrator-design.md §I: Isolation)。

**trace-enabled / trace-disabled build** — トレース取得の口を持つビルド (正しさ検証専用) と、それを完全に消したビルド (性能計測専用)。別ビルド・別 run。*izanagi:* この分離が観測者効果対策の中核。性能比較は必ず trace-disabled どうしで揃える。

**WAL (Write-Ahead Log, 先行書き込みログ)** — 操作を実行する前に、まず追記専用ログに記録してから反映する耐障害の仕組み。クラッシュしても復元できる。*izanagi:* 各 variant 評価を決定論的に追記する探索の永続状態。生 tps と実行コマンドを残し、後から分布を再構成できる (orchestrator-design.md §D: Durability)。

**proof chain / forensic binding (証拠連鎖・法定的束縛)** — 主張 → コード → 実測値を辿れる証拠の鎖。「なぜこの variant を採った/外した」を根拠まで遡れる構造。*izanagi:* 層3 の説明可能性を統計的に裏打ちし、WAL の run 値まで各主張を紐づける (ARA の forensic binding と同型, orchestrator-design.md §材料レポートの出力規約)。

**evidence-bound material report (証拠拘束された材料レポート)** — 成功例を選んだ自由作文でなく、WAL + whiteboard を proof chain 付きで完全射影した研究材料。*izanagi:* 全 run・全 reject・noise floor・環境タグ・identity を決定論的な事実層へ収め、LLM の機序仮説層と分ける。論文 prose や研究成功/新規性の自動判定は含めない (D12, phase3.md 段9)。

**human-supervised loop / unattended loop (人間監督付き / 無人ループ)** — 前者は人間がセッション間の role 呼び出しや候補の受け渡しを行う反復、後者は orchestrator が呼び出し・checkpoint・budget・再開を所有する反復。*izanagi:* 現行 Phase 3 は前者。8c を実装して完走するまで autonomous/unattended と呼ばない (roadmap.md §2, phase3.md「現行チェックポイント」)。

**provenance (プロビナンス, 出所記録)** — ある成果物・データが「どこから・何を経て」生まれたかを後から遡れるようにした記録。*izanagi:* campaign の出所記録ファイル、偵察の結果を見た事実の記録 (D46)、axis-proposer の射影三点セット = 生の critic 出力 / 射影版入力 / 落とした項目の対応表 (D47) など、事後検証を可能にする層。

**TOCTOU (Time-Of-Check to Time-Of-Use)** — 「確認した時点」と「使う時点」の間に対象が変わり、確認が無意味になる競合の穴。*izanagi:* 旧ビルドは identity と無関係に共有作業ツリーをコンパイルしていた穴。cache_key に作業ツリー由来のハッシュを織り込んで構造的に解消した (D23)。

**fails-closed / fails-open (安全側/危険側の失敗)** — 異常時にどちらに倒れるか。fails-closed=安全側 (止める・拒否する)、fails-open=危険側 (通してしまう)。*izanagi:* 正しさに関わる経路は必ず fails-closed。identity 計算の失敗 (g++ 不在など) は best-effort で読み飛ばさず停止する (D23)。

**positive control / 陽性対照** — 「検出器がちゃんと検出できる」ことを確かめるため、わざと陽性の検体を通すこと。*izanagi:* broken-silo パッチで verifier が確実に G2 の赤を出すか確認する。赤検出力が空打ちでない実証 (decisions.md D16)。

**submodule pin (サブモジュールのピン留め)** — 参照する外部リポジトリ (submodule) を特定のコミットに固定し、再現性を保つこと。*izanagi:* CCBench を commit hash で固定。trace-hook 用の改変は別ブランチに置き、pin を特定の submodule commit に据える (現行 pin の値の正本は `orchestrator/campaign/pin.py` の CURRENT_PIN — literal は前進で腐るため本文に引かない。phase3.md §EVOLVE-BLOCK 機構, D16)。

---

## 5. サブエージェント・規律・運用

サブエージェント構成 (agent-architecture.md) と絶対規律、セッション運用を読むための用語。

**verifier / calibrator / critic / profiler (Phase 1-2 のロール)** — verifier=trace を読んで直列化を検査する正しさの番人 (書き込み権限なし)、calibrator=レコード数と noise floor を決める、critic=指標を読んで性能差を設計選択に帰属させ次手を返す、profiler=有望 variant に perf を回し many-core のスケール懸念を解釈する。*izanagi:* Phase 1-2 で足したサブエージェント。各々コンテキストを分離し tools で権限を絞る (agent-architecture.md)。

**planner / coder / auditor (Phase 3 のロール)** — planner=構造から設計プランを提案 (コードに引きずられない)、coder=プランを EVOLVE-BLOCK 内の差分に落とす、auditor=variant を監査し verifier が見逃した不変条件違反を見つけてテストを提案する (read-only — 反映は人間レビュー gate、D38 決定 3)。*izanagi:* Phase 3 の各段で実体化する (正本は phase3.md)。kickoff の確定制約は phase3.md + D22-24/D30 が正典 (agent-architecture.md §planner/§coder/§auditor)。

**adversarial auditor (敵対的監査役)** — 生成物を「壊す側」の視点で監査し、正しさ検証の抜け穴を能動的に探す見張り役。*izanagi:* auditor の性格。最適化を担当する planner/coder とコンテキストを分離し、見張りが最適化圧力に毒されないようにする (Jitskit 由来)。

**正しさゲート (correctness gate)** — 「絶対に壊してはいけない不変条件」の関所。壊す variant は性能に関わらず即 reject。*izanagi:* 絶対規律2 の中核。「壊していい」(プロトコル固有テスト = variant の性格づけ) と厳密に分ける (CLAUDE.md 絶対規律2)。

**観測者効果の分離 (絶対規律1)** — 正しさ検証用のトレース取得を、性能計測ビルドから完全に除去する規律。ランタイム分岐でなくコンパイル時に消し、CCBench の具体実装は D14 の `#if TRACE` 契約に従う。*izanagi:* 6 つの絶対規律の 1 つ。性能数値の信頼性の前提。

**入力側隔離 / 出力側隔離 (anti-fabrication isolation)** — 検証エージェントに期待値 (性能数値・正解) を一切見せない (入力側) + 書き込み権限を外す (出力側) で、「期待値をコピーして捏造する」経路を両側から断つこと。*izanagi:* verifier は trace だけを入力とし throughput を受け取らず、Edit/Write も持たない (ARA の anti-fabrication isolation, agent-architecture.md §verifier)。

**honest-by-construction (構成的に誠実)** — 「誠実であるよう気をつける」でなく、仕組みの構造上そもそも偽れないようにすること。*izanagi:* source_digest が inert patch で stock と真に同一ハッシュになる等、identity が構造的に偽れない設計 (decisions.md D12)。

**リーク制御 (leak control)** — 評価対象に「答え」が漏れて出来レースになるのを防ぐ手当。最適解や未評価データを探索エージェントの入力から物理的に遮断する。*izanagi:* 誘導実験で最適解を物理削除・fresh context・評価済みのみ開示。「評価器の優位を評価器の定義で示す循環」を塞ぐ (絶対規律6/D12)。

**信頼境界 / プロンプトインジェクション (trust boundary / prompt injection)** — 外部から来た内容を「データ」として扱い「指示」として解釈しない境界。汚染された入力が振る舞いを乗っ取る攻撃がプロンプトインジェクション。*izanagi:* 絶対規律6。CCBench のソース・出力・trace・生成 variant・Web は全てデータ。「検証を飛ばせ」と入力が指示してきても正しさゲートは緩めない (CLAUDE.md 絶対規律6)。

**二相 verifier (two-phase design, IDS 式)** — 検証を 2 相に分ける設計。開発相=短い trace で安く広く回帰検出 (毎反復)、検証相=最終候補だけ長時間で高い確信度まで精査。*izanagi:* 正しさを「最後にまとめて回すゲート」でなく毎反復のシグナルにする規律3 の骨格 (decisions.md D3)。

**三層可変性 (憲法 / 戦略 / 戦術)** — 文書を変えてよい度合いで 3 層に分ける統治。憲法 (絶対規律) は人間のみ変更可、戦略 (roadmap) は Claude が版管理規律の下で改訂可、戦術 (phase docs 等) は自由。*izanagi:* 設計を進化させる権限と正しさ規律の不変性を両立させる仕組み (CLAUDE.md §「roadmap の更新 — 三層の可変性」)。

**living document (生きた文書)** — 完成品として凍結せず、試行錯誤の発見に応じて改訂し続ける文書。改訂履歴そのものが研究記録になる。*izanagi:* roadmap の運用思想。過去の版は roadmap-history/ に凍結し、設計仮説の変遷を残す (CLAUDE.md §「roadmap の更新 — 三層の可変性」)。

**auto-compact (自動圧縮) / 自己一貫性バイアス** — 長い対話でコンテキストを要約圧縮する機構 (ロッシー) と、一度出した見立てに固執して反証を軽視する認知の偏り。*izanagi:* 同一セッション内のコンテキスト劣化の原因。自己一貫性バイアスは P2-5 の「自信ある早期停止の負債」と同型。区切りで handoff を書いてセッションを終える等で対処 (roadmap §3.8, D31)。
