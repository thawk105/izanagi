# 5 手法比較基盤の設計 — random・sweep・BO・進化探索・LLM を同じ候補適用・検証・計測の口で比べる ([T-2849]、2026-09-22、計算なし)

- 位置づけ: 設計文書。採用判断の正本は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- 作成: 2026-09-22、dev-wave `worktree-dev-wave-t2849-comparison-harness-design` (基準 local main `8fd2a2f5c`、開始 gate rc 0 は 08:54 JST)。実装・build・計算投入はしていない。実装は後続 wave で Codex author が行う。
- 根拠のユーザー裁定: D2212 (VLDB 方針。項 4 = 1 タスクの job 合計が 2 node 時間以上なら投入前に確認)、/rulings 第 31 回 (2026-09-22) 項 1 (開発の検査も同じ線で数える)・項 6 (H100 の open-weight LLM は今は採らない)・項 8 ([T-2858] の ccbench branch の push は人間手番)。
- 一次資料: `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2。依頼の逐語は `verbatim/request.md`。
- 段の記録: 段 1 brief・骨子・事実表 (`verbatim/s1-*.md`)、段 3 の Codex 相談 2 本 (`verbatim/s3-consult-A.md` / `s3-consult-B.md`)、段 4 裁定 (`verbatim/s4-ruling.md`)。本文は段 4 で訂正した後の設計で、骨子と食い違う箇所は本文が正しい。
- **性質の断り:** すべて静的調査 (ソースと文書を読む・grep・login での import 確認) による設計である。「案」と書いた値は凍結前の提案で、較正済み・実装済み・実証済みを意味しない。file:line は基準 commit の worktree で確かめた。

## 0. 要約

1. **共通化するのは 4 つの契約だけ。** 候補の identity、評価の要求 (経路)、結果の分類、費用の計上。候補を運ぶ入口 (proposal 文書・IR JSON) は空間ごとに別で、「全候補が文字通り同じ役割経路を通る」とは書かない (§2)。
2. **具体化するのは S1 (silo の backoff 値 1..1000 µs) だけ。** 現に口が実在するのは S1 だけである。S2 (MOCC の backoff 値) は [T-2858] の pin 前進後に差し込む口、S3 (D2214 の policy IR) は差し込むときの条件だけを書く (§9・§10)。汎用 runner・汎用台帳・S3 の表現設計は作らない。
3. **S1 の 5 手法。** random = B-5 の log-uniform、sweep = B-5 の 28 点格子 (hash 順、非適応。1 次元では座標探索が格子の走査順に退化する)、BO = 逐次 GP-EI、進化 = (1+1) 変異、LLM = K0 (外部の実験知識の射影なし) の planner・coder・critic 親運用 (§3)。
4. **BO と進化は「再実装」と名乗る。** repo に実装は無く (検索範囲は §6.1)、login の python3 で使える外部 package は numpy だけ。S1 は小さいので標準ライブラリで足りる。EGO (Jones ら 1998) と、Polyjuice (OSDI 2021) の整数変異規則を下敷きにし、変えた点を書く (§6)。
5. **揃え方。** 全 arm が読める共通入力と、各手法が実際に消費する field を分ける。主構成 R0 では、生成器へ渡すのは系列開始 stock と空間内の初期点の観測だけ。`p2_2_flag_opt` (BACK_OFF=0、空間の外) は同じ block・同じ条件で測る報告用の対照で、値を生成器へ渡さない。渡す構成は R1「既知結果を条件とする探索」として別に名乗る (§4)。
6. **初期点。** S1 は静的 5 µs・10 µs の 2 点 (案)。系列ごとに fresh に測り、最初の提案の前に全 arm へ渡す。総評価数は k + B で、初期点の費用も時間軸に入れる。初期点は endpoint の候補に含め、探索で初期点を超えたかを別に報告する (§4.5)。
7. **費用。** A = 候補提出機会 (空出力・不正出力を含む)、B = pipeline 投入。重複 (複製候補) は A・B を消費して fresh に測る。Tier0 の compile / smoke 不通過は A だけを消費し、pipeline 内の build 失敗と anomaly は B を消費する。物理費用は job ごとの Elapse を 1 回、slot の wall を内訳にし、LLM の役割呼び出し・親の待ち・人間の介入を別欄にする。時間原点・打切り・統計単位の意味は本書で固定し、値は [T-2850] の事前登録へ残す (§5)。
8. **B-5 の再利用。** 規則 (A/B・retry・品質欠測・endpoint・fallback・Tier0・walltime) は継承し、S1 で呼べる関数は呼び、B-5 固有の結合 (arm 3 固定・slot 接頭辞・K2 必須・系列番号 1..12) は変える。B-5 の cohort・判定規則・標本は使わず混ぜない (§7)。

## 1. 依頼・範囲・主張の射程

### 1.1 依頼

random・sweep (座標探索)・BO・進化探索・LLM を同じ候補適用・検証・計測の口に通す形と、観測情報・stock・既知最良 `p2_2_flag_opt`・初期候補の揃え方を定める。B-5 (`docs/b5-generator-contrast-preregistration.md`) の生成器 arm の再利用範囲、BO / 進化探索の実装の出所 (移植は「再実装」と明記)、費用の計上単位 (複製候補・compile 失敗を含む) も定義する。MOCC は [T-2858] の pin 前進後に差し込む口だけ。実装・投入は含めない。本題だけで、gate・検査・台帳・一般化の追加は scope 外 (逐語は `verbatim/request.md`)。

### 1.2 本書がやらないこと

- 実装・build・計算投入。値の凍結 (B・A・系列数・費用上限・checkpoint などは [T-2850] の事前登録で決める)。
- 新しい gate・検査・台帳。汎用の系列 runner。S3 の IR の表現設計と S3 用の BO / 進化の方式選択。
- sort (79 値)・trigger (32 点)・flag genome (有効 8 点) の空間への展開。
- B-5 事前登録と `orchestrator/campaign/b5_generator_contrast.py` の編集 (B-5 の発効束は並走の [T-2797] wave が扱う)。
- [T-2849] の起票文の完了条件のうち「第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload)」。本書は設計だけで、疎通は pin 前進と計算確認の後である。

### 1.3 主張の射程

この基盤で言えるのは、次の形の比較に限る。

> 登録した空間と各手法の支持集合、共通の初期点と情報構成 (R0 / R1)、固定した予算 (評価数または費用)、指定した workload・動作点の下で、探索法を含む構成どうしを比べた結果。

主張しないこと:

- LLM の必要性 (「LLM でなければ到達できない」)。非 LLM 生成器一般に対する優越 (D1067)。
- 有限空間 (S1・S2) の結果を、コード合成一般へ広げること (差分分析 §4 P2 の注意)。S3 の比較 B (LLM×C++ による空間拡張、D2214 §5) と、同じ空間内の探索法比較 (比較 A) を混ぜること。
- LLM 単体・critic・知識・情報の使い方それぞれの因果効果。各手法は「どの観測を使うか」まで含めて定義した構成であり、差をその 1 要素へ帰属しない。
- K0 を「事前学習知識なし」と読むこと。K0 は外部の実験知識の射影を入れないという意味である。
- 評価数を揃えた優越を、時間・費用を揃えた優越と読むこと (逆も同じ)。
- 未知条件への転移 ([T-2851] が別に扱う)。他 protocol・他環境での成立。
- certified を全実行の正しさの証明と読むこと。certified は観測した有限の trace の判定である。
- S1 の結果を headline へ戻すこと。backoff 値の軸はスカラー 1 個の探索に還元できるので headline 候補にしない (B-5 §1、D52)。

## 2. 共通の口 — 4 つの契約

### 2.1 層

生成器 → 候補の入口 (空間ごと) → 共通評価 → 結果の分類 → 生成器 (自系列の結果だけ)。

### 2.2 候補の identity

候補は protocol・genome flags・CCBench の PIN・材料化した全 source の内容で決まる (D2214 §5 と同じ定義、`orchestrator/campaign/source_digest.py`)。S1 では genome と PIN を固定するので、実質は hole literal の整数 v で決まる。同じ本文でも flags や PIN が違えば別候補である。

### 2.3 評価の要求

手法によって評価経路を変えない。S1 の経路は B-5 と同じで、`p3_s4_loop --run-iteration <proposal>` → 文法・帰属整合 (value == literal)・diff 検疫 → Tier0 (perf build + 固定スモーク、D2215) → `run_campaign` / `pipeline.evaluate` (trace build で verify、trace-disabled build で bench) である (`orchestrator/campaign/b5_generator_contrast.py:506-528` の `slot_argv`、`p3_s4_loop.py:3450` 以降の CLI)。動作点は較正済みの 1M records・48 threads・3 秒・5 rep、workload は write-heavy / balanced / read-heavy (B-5 §5.2)。correctness は性能と別 build・別 run で性能 workload と同じ構成を明示し、anomaly が 1 件でもあれば即 reject する (B-5 §5.5、規律 1・2)。

### 2.4 結果の分類

1 slot の結果は、B-5 の分類をそのまま使う: certified (品質正常 / 品質欠測)、Tier0 不通過 (`rejected-tier0`)、pipeline 内の build 失敗、anomaly による reject、機械故障 (retry 対象)。性能値は certified かつ品質正常の session median だけを使う。

### 2.5 生成器の契約

- 形は ask / tell。ask は候補を 1 件返し、tell はその slot の結果を受け取る。
- 入力は、空間の定義・seed の preimage・**自系列の結果**だけである。他系列・他 arm・block stock・floor・endpoint の再計測・参照点の測定値 (R0 のとき)・偵察の結果・既知結果の文書は、実行時の入力に入れない (例外入力は §4.2)。
- **A (原提案) は候補提出の機会**である (B-5 §3.1)。空出力・schema 不合格・値域違反も A を 1 消費する。上限 A は全 arm に掛ける。
- A を消費しない内部計算は次に限る: 獲得関数による候補点の採点と最大化、乱数の偏り除去の引き直し (B-5 §4.2)、事前に定めた構成規則 (整数への丸め・値域への切り詰め・§3.3 の「親と同じ値なら ±1」)。具体的な候補を compile・smoke・verify した後の棄却と再生成、結果を見た修復・選び直しは、どの手法でも A を消費する。
- LLM は 1 回の提出機会の中で planner・coder・critic を呼ぶ。役割の呼び出しは A ではなく物理費用として数える (§5.5)。隠れた再生成 (複数案から選んで提出) は、選び直した分だけ A を消費する。

### 2.6 入口は空間ごとに別

- S1: 既存の閉じた proposal 文書 (`planner` / `coder` / `prior_critic_reverse`、`p3_s4_loop.py` の `load_proposal_file` と `projection_guard.assert_closed_proposal_schema`)。機械生成の 4 手法は B-5 の `machine_proposal_document` (`b5_generator_contrast.py:139-153`) と同形の文書を作り、`--machine-generated-proposal` を付ける。由来は proposal に入れず、台帳の arm と build admission の分類 (`build_admission.py:92-104` の `MACHINE_GENERATED` / `CODER_AUTHORED`) で残る。
- K0 の LLM は機械生成の印を付けず、knowledge manifest なしで `--allow-coder-derived-build` の既存経路を使う (`p3_s4_loop.py:3675-3682`。知識 source が非空のときだけ K2 の coder role を要求する :3731-3741)。
- S3: planner を外し、IR JSON (LLM×IR と非 LLM) と C++ 本文 (LLM×C++) を兄弟 driver で受ける (D2214 §4)。S1 の proposal 文書へ統一しない。

### 2.7 今のコードで外す必要のある結合 (実装単位は §11)

- `--machine-generated-proposal` は `--b5-slot` を必須にし、slot key は B-5 の接頭辞を要求する (`p3_s4_loop.py:3550`・`:3557-3559`)。
- `machine_proposal_document` は arm を random / sweep-matched に限る (`b5_generator_contrast.py:140`)。`slot_argv` は LLM に K2 の引数を必須にする (:509-510)。
- `slot_key` は ARMS・予算定数・PREREG_VERSION に、random / sweep の生成は系列 1..12・A ≤ 30 に拘束される (:105-168)。
- loop の genome は silo 固定である (`p3_s4_loop.py:2314`・`:2465`・`:3160`、`b5_generator_contrast.py:588`)。S2 で効く。
- D2155 の critic 診断の射影は K2・非 B-4・還流ありに限る。K0 の LLM に同じ還流を渡すには適用範囲を広げる必要がある (射影の中身と 6 field は変えない)。
- B-5 の whiteboard は探索評価の event だけから作られ (`expected_inputs`、:451-477)、初期点を運ぶ場所が無い。

## 3. S1 での 5 手法の操作的定義

空間 S1 = {1, 2, …, 1000} (µs、整数)。genome は silo・BACK_OFF=1・NO_WAIT_LOCKING_IN_VALIDATION=1・NO_WAIT_OF_TICTOC=0・WAL=0、hole の合成枝を `double now_backoff = <v>;` に置き換え、BACKOFF_FIXED = v とする (B-5 §2・§5.2)。seed の preimage は B-5 と別の名前空間 `t2849-harness-v1|<arm>|<workload>|<系列>|…` にする (案)。

| 手法 | 支持集合 | 消費する観測 | 定義の要点 |
|---|---|---|---|
| random | S1 全体 (全点に正の確率) | なし (open loop) | B-5 §4.2 の離散 log-uniform (整数重み `floor(2^128 × ln((v+1)/v))`) を、名前空間だけ変えて使う |
| sweep | B-5 の 28 点格子から初期点の値を除いた 26 点 | なし (open loop) | 格子を preimage の SHA-256 昇順に並べ、先頭から B 点を評価する。候補起因の不通過なら次点、格子が尽きたら枯渇として記録 (B-5 §4.3)。初期点の除外は実行前に決まる構成規則 |
| BO | S1 全体 | 自系列の certified・品質正常の (v, fitness) と、候補起因で失敗した v の集合 | 逐次 GP-EI (§3.2) |
| 進化 | S1 全体 | BO と同じ | (1+1) 変異 (§3.3) |
| LLM (K0) | 保証しない (S1 の全点へ到達しうるとは証明しない) | whiteboard の 5 field、current_perf、critic 診断、初期点の射影 (§4.1) | B-5 §4.1 の運用契約から knowledge manifest を除いた構成 (§3.4) |

### 3.1 sweep の名前について

依頼の「sweep (座標探索)」は、座標が複数ある空間では、1 座標ずつ格子を走査して現行最良を更新する手続きを指す。S1 は座標が 1 本なので、座標探索は格子の走査順を決めることに退化する。本書は S1 の sweep を B-5 の非適応な hash 順の格子走査に固定し、「適応的な座標探索」と同一視しない。多座標の空間での定義は、その空間を足すときに決める (§10)。

### 3.2 BO — 逐次 GP-EI (案)

- 入力 x = ln v、出力 y = ln (session median tps)。学習点は自系列の certified・品質正常の点 (初期点を含む)。系列開始 stock と参照点は空間の外なので学習点にしない。BACK_OFF=0 を ln v = 0 などへ写さない。
- 初期 design の追加は 0 点。共通の初期点 (k 点) を最初の学習データにし、最初の ask から獲得関数で提案する (B = 8〜10 程度で獲得がほぼ起きなくなるのを避けるため)。
- 代理モデル: Matérn 5/2 kernel の GP。長さ尺度と信号分散は固定した格子の上で対数周辺尤度を最大にする値を選ぶ (同点は長さ尺度の小さい方)。観測雑音の分散は測った値でなく事前に固定した定数 (案: (ln 1.03)^2、B-5 §7.2 の 3 % 保守下限に合わせる)。行列が特異に近いときは固定の jitter を足す。
- 獲得: 期待改善 (EI、現行最良は学習点の y の最大)。S1 の 1000 点を全列挙して最大化し、同点は v の小さい方。候補起因で失敗した v (Tier0 不通過・build 失敗・anomaly) は獲得の対象から外す。品質欠測と機械故障の上限超えは外さない。
- 評価済みの v を再び選ぶことは許す (雑音つきの GP では起こりうる)。その場合は §5.2 の重複として fresh に測る。
- 学習点が 0 点 (初期点がすべて失敗) のときは、random と同じ規則で別名前空間 (`…|bo-fallback|…`) から引く。

### 3.3 進化 — (1+1) 変異 (案)

- 親 = 自系列の certified・品質正常の点 (初期点を含む) のうち fitness 最大の点 (同点は v の小さい方、次に slot の早い方)。
- 子: ln v' = ln v_親 + δ、δ は [−λ, λ] の一様乱数 (preimage から決定的に引く)。v' を整数へ丸めて 1..1000 に切り詰め、v' が親と同じなら δ の符号の向きへ ±1 動かす (境界では内側へ)。λ は案として ln 4。
- 子が certified・品質正常で、fitness が親より真に大きければ親を置き換える。同値・失敗なら親を保つ。親の fitness は 1 session の値で、測り直さない (雑音に弱いことは定義の一部として開示する)。
- 親が無いときは BO と同じ fallback。

### 3.4 LLM (K0) — 主比較の構成

- B-5 §4.1 の運用契約 (系列ごとに fresh context、評価ごとに `p3_s4_loop` の単回評価を fresh layout で呼ぶ、親は機械的な射影だけを行い性能を見た助言・候補の修正・再抽選をしない、各役割の実入力と出力を全件保存) を継承する。
- K2 構成との差を knowledge manifest の有無 1 点にするため、役割構成 (planner-v4・coder-v4-autonomous・critic、還流あり) は同じにする。critic 診断の射影 (D2155) を K0 に広げる実装が要る (§2.7)。
- B-5 の LLM arm (K2 知識つき) は B-5 cohort の構成のまま残す。本基盤で K2 を走らせるなら「K2 構成」と呼び分け、5 手法の主比較には入れない。
- 1 系列に親 session 1 本、同時に走る LLM 系列は親の本数以下、1 機会の待ち上限 2,700 秒 (D2216 の運用を継承)。

## 4. 揃えるもの

### 4.1 共通入力と、各手法が消費する field

全 arm が読める共通入力 (いずれも自系列の slot の記録):

- slot の種別 (系列開始 stock / 初期点 / 探索)、候補 v、結果の分類 (§2.4)。
- certified・品質正常のときの fitness (採用 round の 5 rep の session median)、rep の CV、leading indicators (abort 率など)。
- anomaly のときの verifier の構造化 digest (どの取引間のどの依存か、規律 3)。
- slot の開始・終了・結果が使えるようになった時刻。

各手法が消費する field は §3 の表のとおりで、手法の定義の一部である。非 LLM の 3 手法が leading indicators や anomaly の digest を使わないのは定義上の選択で、結果はその定義を含む構成の比較として読む (§1.3)。

既存の記録から入力への対応 (新しい producer は作らない):

| 入力 | 既存の出所 | 変える点 |
|---|---|---|
| BO / 進化の (v, fitness) | 台帳の `evaluation-result` event の `fitness_tps`・`outcome`・`quality` (`b5_generator_contrast.py:69-73`) | 初期点の event を同じ形で足す |
| LLM の whiteboard 5 field | `expected_inputs` (:451-477) | 初期点を、手法の出力でないと区別できる閉じた値で前置きする |
| LLM の current_perf | `expected_inputs` の「最新の certified・品質正常」 (stock-start を含む) | 初期点も候補に入る。規則 (最新であって最良でない) は B-5 と同じ |
| LLM の critic 診断 | D2155 の射影 | K0 へ適用範囲を広げる。診断の材料は自系列の記録だけ |
| (どの手法にも渡さない) | Tier0 のスモークの数値 (D2215)、block stock、endpoint 再計測、参照点の測定値 (R0) | — |

拒否されたときの tell: Tier0 不通過・build 失敗・anomaly・品質欠測・機械故障の上限超えは、fitness なしの結果として自系列の履歴へ入る。BO / 進化は §3.2 の規則で扱い、LLM は whiteboard の result に分類が載る。最後の正常値を補って代入しない。

### 4.2 読取範囲と例外入力

- 実行時に生成器へ入るのは §4.1 の自系列の記録と、系列開始 stock、初期点の観測だけである。
- LLM の親は、役割の入力を上の記録から機械的に射影するだけで、自分の context で知った他系列・偵察・既知結果を自由文で足さない。critic の role は file を読む道具を持つので、自系列の記録以外を渡さないことは手順上の約束であって機械的な遮断ではない。
- 入力と出力を保存することは、「他の情報を見ていない」ことの証明ではない (B-5 §4.1 と同じ限界)。新しい gate は足さない。

### 4.3 stock

- 系列開始 stock: 各系列の最初に、同じ機体・同じ job で stock (同じ flags で BACKOFF_FIXED = −1、適応 backoff) を 1 session 測る (B-5 §5.4)。LLM の current_perf の初期値に使う。全 arm に同じ値が届くが、非 LLM の 3 手法は消費しない。探索予算 B に入れない。
- block stock: workload × block ごとに 5 session 測り、endpoint の fallback と floor に使う (B-5 §5.4・§6・§7.2)。生成器へは渡さない。
- stock は無 backoff (BACK_OFF=0) ではない。

### 4.4 既知最良 `p2_2_flag_opt` と情報構成

- `p2_2_flag_opt` は flags = BACK_OFF=0 / NO_WAIT_LOCKING_IN_VALIDATION=1 / NO_WAIT_OF_TICTOC=0 / WAL=0 (balanced・write-heavy、label B0-L-W0)、read-heavy は B0-T-W0 (`output/s1-freeze/known_axes_freeze.json:90-99`・`:544`)。S1 の外にある。
- 測り方: exact flags のまま、block ごとに比較と同じ動作点・同じ session 契約・同じ correctness の条件で fresh に測る。旧い性能値 (S-1a の記録など) を新しい条件の性能値として代入しない。
- **主構成 R0:** その値を生成器へ渡さない。endpoint の報告 (stock 比と `p2_2_flag_opt` 比の両方) にだけ使う。空間外の参照値を使えるのは LLM だけなので、渡すと LLM だけに情報が増え、差が情報の差か探索の差か分からなくなるためである。
- **別構成 R1:** 参照値を全 arm の共通入力に入れる。「既知結果を条件とする探索」と名乗り、R0 と同じ族で比べない。
- 目標水準に達したら止める運用は、R0 / R1 のどちらでも採らない (性能を理由とする早期停止をしない、B-5 §3)。

### 4.5 初期点

- S1 の初期点は静的 5 µs と 10 µs の 2 点 (案、k = 2)。D2214 §5 の新骨格内 seed の静的 5 / 10 µs と同じ値で、既知の結果を見て選んだ (§8)。
- 各系列で fresh に測る (系列間で測定値を共有しない。共有すると系列が独立でなくなる)。順序は固定 (5 → 10)。最初の ask の前に、全 arm に同じ観測として渡す。
- 費用: 初期点は探索予算 B の外に置き、総評価数は k + B と書く。初期点の費用は時間・費用の軸から除かない。
- endpoint の資格: 初期点も endpoint の候補に含める (含めないと、初期点より劣る探索点が endpoint になりうる)。報告では、endpoint が初期点か探索点か、探索点の最良が初期点の最良を超えたかを系列ごとに別に数える。
- 初期点が不成立 (anomaly・失敗・品質欠測) でも差し替えない。その系列の履歴にそのまま残る。
- S1 では静的 5 / 10 µs を「元の適用方法」(BACKOFF_FIXED の macro 経路) で別に測る必要はない。macro 経路の同じ値は意味が同じでも source が違うので別 identity になり、S1 の比較には要らない (D2214 §5 の exact reference は S3 の新骨格で意味を持つ)。

### 4.6 anomaly の波及と endpoint

- 生成器への tell は自系列だけである。
- endpoint の資格は集約側で決める。値 v について workload w で anomaly が 1 件でも観測されたら (探索・初期点・再計測のどこでも、どの系列・arm でも)、v は w の全系列で endpoint の資格を失う (B-5 §6)。この判定は生成器へ還流しない。
- endpoint は、自系列の初期点と探索点のうち資格のある certified・品質正常の点で session median が最大のもの (同値は v の昇順、次に slot の昇順)。N_eval 個の fresh session で再計測し、その median を score にする。資格のある点が無ければ block stock の median を score にする (fallback)。再計測で anomaly が出れば採用せず、次点へ選び直さない (B-5 §6)。
- 既に score が確定した系列に後から波及した場合は、B-5 §6 と同じく日付付きの「結果の訂正」として扱う。系列単位のコード (`run_series` の自系列内の失格集合、`b5_generator_contrast.py:815-816`) だけでは全系列への波及を実装していないので、集約は本基盤の側で持つ (§11)。

## 5. 費用の計上単位

### 5.1 論理単位

| 単位 | 数え方 |
|---|---|
| A (原提案) | 候補提出の機会。空出力・不正出力を含む。全 arm に上限を掛ける |
| B (評価) | 文法・帰属整合・検疫・Tier0 を通って pipeline へ投入した回数。anomaly で reject されても、投入後の候補起因の失敗でも返さない |
| k (初期点) | 系列ごとの初期点の評価数。B の外 |
| 系列開始 stock | 系列ごとに 1 session。B の外 |
| endpoint 再計測 | 系列ごとに N_eval session。探索の費用でなく「選定の費用」として別に数える |
| block stock・参照点 | block ごとの共有費用。arm へ割り付けない |

### 5.2 重複 (複製候補)

- 同じ系列で、既に評価した identity (S1 では同じ v) を再び提案した場合も、A と B を 1 ずつ消費し、fresh に測る (B-5 §2)。過去の性能値を新しい評価として再利用しない。
- 台帳には重複元の slot を残し、系列ごとに「一意な identity の数」と「重複率」を B と別に報告する。
- 既存 loop の `duplicate` / `duplicate-skip` (単一 layout で WAL から結果を復元する) の経路は使わない。評価ごとに fresh layout で呼ぶ (B-5 §4.1 の運用)。
- 系列が違えば同じ v でも重複ではない (系列は独立)。

### 5.3 compile 失敗

- Tier0 (perf build + 固定スモーク) の compile 失敗・スモーク失敗は A だけを消費し、B を消費しない (D2215)。ただし compile とスモークの時間は物理費用に入れる。無料で捨てられるのは予算上の B だけで、費用からは消えない。
- Tier0 を通った後の pipeline 内の build 失敗は B を消費する (結果の分類は build 失敗)。
- 候補と独立な依存物の供給障害による build 失敗は機械故障として retry する (B-5 §3.3)。
- S1 の literal は compile で落ちにくいが、規則は空間によらず同じにする。S3 で LLM 由来の候補だけに掛かる auditor の拒否は、pipeline 投入前なので A だけを消費し、所要を物理費用に入れる。これは正しさの契約上の差として開示する。

### 5.4 anomaly・品質欠測・機械故障

- anomaly: B を消費。即 reject し、性能値を取らない。
- 品質欠測 (3 round で静定しない): B も A も返さず、fitness なしの結果として残す。fallback で埋めない (B-5 §5.3)。
- 機械故障: 同じ候補・同じ入力・同じ論理 slot で追加 2 回まで retry (B-5 §3.3)。論理の A / B は増やさず、物理の試行と費用は全件記録する。上限を超えたら欠測。

### 5.5 物理費用

- **job Elapse は job ごとに 1 回**数える (scheduler の記録)。同じ job の Elapse を slot ごとに載せない。queue 待ちは別欄。
- slot の subprocess wall (今の B-5 の記録、`b5_generator_contrast.py:618-645`) は job Elapse の内訳として、Tier0・build・verify・bench・retry に分けて残す。
- 生成器の計算時間 (BO の獲得、進化・random・sweep の ask) も wall で残す。
- LLM: 提出機会ごとの役割呼び出しの回数と wall、親の待ち (handshake)。LLM を待つ間も node を確保しているので、その時間は job Elapse に入る (D2214 §6)。
- 人間の介入: 定めた運用の外の手作業 (再起動・再投入・手での修復) の回数と内容。
- token 数は報告された値を残すが、金額に換算しない。サブスクリプションで動いている限り、CLI が示す費用の値は請求額ではない。

### 5.6 時間原点・打切り・統計単位 (意味を本書で固定する)

- **統計単位は独立な探索系列**である (fresh context、系列ごとの seed preimage)。rep・session・endpoint の再計測は独立な探索の数に数えない。block stock を共有する系列どうしの依存は開示する。
- **時間原点 t0** は、系列の最初の slot (系列開始 stock) の開始時刻。queue 待ちは t0 の前で、別に記録する。
- 各 slot に開始・終了・結果が使えるようになった時刻を残す。
- **経過時間の軸**は t0 からの wall (LLM の待ちを含む)。**node 秒の軸**は job Elapse の和。2 つは別の量として残し、混ぜない。
- **checkpoint T での最良**は、結果が T までに使えるようになった候補だけから求める。T をまたいで走っている候補は T の最良に入れない。その候補の費用は、費用の軸では T までの分を含める。
- 評価数の軸の checkpoint は B の値で切る。初期点は B = 0 の時点で既に観測済みとして扱う。
- 欠測・A の枯渇・fallback は系列の結果として残し、系列を差し替えない (B-5 §3.2)。

[T-2850] の事前登録へ残すもの: B・A・k・系列数・費用上限・checkpoint の実値、N_eval (B-5 の 5 を継承するならそう明記)、主 endpoint と曲線の要約、比較の族・多重性・同等幅、割当順と block の設計。いずれも新しい cohort の結果を見る前に決める。

## 6. BO と進化探索の実装の出所

### 6.1 現状 (2026-09-22、基準 commit)

- repo の `orchestrator/` と `tools/` の `.py` を BO・進化の語 (gaussian process、expected improvement、bayesian optimization、optuna、skopt、botorch、smac、crossover、genetic algorithm、CMA-ES、tree-structured Parzen) で検索して 1 件だけ hit し、それは Codex 実験の「sequential crossover block」の文字列で無関係だった。**この検索範囲では実装は見つからない** (repo 全体・全表記の不在の証明ではない)。`orchestrator/campaign/evolve_block.py` は marker の text 処理で探索器ではない。
- login の `/usr/bin/python3` (3.10.12) で import できたのは numpy 2.2.6 だけで、scipy・sklearn・optuna は `ModuleNotFoundError` (親が実測)。skopt・botorch・torch・smac・nevergrad・deap も無いと調査子が報告した (親は未照合)。計算ノードの python は未測定。

### 6.2 方針

- S1 は学習点が高々数十、獲得の候補が 1000 点なので、GP も EI も標準ライブラリ (`math`・`random` 相当の決定的 hash) で書ける。外部 package の移植・呼び出しはしない。
- numpy を使わないことは研究上の要件ではない。計算ノードでの可用性を実装 wave が測ってから使ってよい。使うかどうかで手法の定義は変えない。
- 自作の数値計算の誤り (Cholesky の不安定、EI の同点処理) が比較に混ざらないよう、実装 wave は固定入力に対する値を手計算・別実装と照合する単体試験を持つ (新しい gate ではなく、実装の通常の試験)。

### 6.3 名乗り

- **BO:** 「EGO (Jones, Schonlau, Welch 1998, *Journal of Global Optimization*) の考え方に沿った逐次 GP-EI の再実装」。EGO の DACE 型の相関関数と連続最適化は使わず、Matérn 5/2・格子による超パラメータ選択・離散 1000 点の全列挙に変えた。
- **進化:** 「(1+1) 進化戦略の最小形の再実装。変異幅の一様分布は Polyjuice (Wang ら, OSDI 2021) の整数 cell の変異規則 ([−λ, λ] の一様幅) に倣い、尺度を log に変えた」。Polyjuice の EA 学習 (各世代で上位 8 方策 × 変異 4 通り、cell ごとに確率 p で変異、2 値は反転) の再現とは呼ばない。方策表と backoff 値 1 個は別物である。
- 出典の確認: Polyjuice の EA の記述は 2026-09-22 に Web で確認した ([USENIX 原典](https://www.usenix.org/system/files/osdi21-wang-jiachen.pdf)、[arXiv 2105.10329](https://arxiv.org/pdf/2105.10329))。EGO・下の TPE・SMAC・型付き GP の書誌は本 wave で原典を取り直していない。

### 6.4 S3 での BO / 進化 (本書では決めない)

S3 の表現が固まった後の別の択一とする。候補は TPE (Bergstra ら 2011)、random forest 型 (SMAC、Hutter ら 2011)、型付き GP (Montana 1995) の subtree 変異・交叉。小予算だけを根拠に他方式の有効性を断定しない。D2214 は BO を最初の結果の必須にせず後段へ送っている。

## 7. B-5 の再利用範囲

B-5 の事前登録と実装 (`b5_generator_contrast.py`、基準 commit の版) を 3 つに分ける。

| 区分 | 項目 |
|---|---|
| **継承する規則** (意味を引き継ぐ) | A / B の分離と上限の考え方 (§3.1)、予算未消化の系列を差し替えない (§3.2)、機械故障の retry と候補起因の失敗 (§3.3)、Tier0 は A だけ (D2215)、session の契約と品質欠測 (§5.3)、stock の 2 種 (§5.4)、correctness の条件 (§5.5)、endpoint の選び方・anomaly の波及・再計測・fallback (§6)、全 arm 同一の walltime の決め方 (D2217)、LLM arm の親運用 (§4.1・D2216)、既知結果台帳の書き方 (§8) |
| **S1 で呼べる関数** (同じ wire 形式なら) | `integer_log_weights` / 重み表 (random)、`EXTENDED_SWEEP_US` と格子 (sweep、ただし順序の preimage は名前空間を変える)、`validate_backoff_value`、`SeriesLedger` (arm も値も検査しない、:207-248。schema 名は B-5 固有なので別名にする)、`classify_session` / `classify_slot` の分類 (:255-438)、`wal_timing`、`select_endpoint` の同値規則 |
| **変更が要る結合** | ARMS の 3 固定、slot key の接頭辞と定数、random / sweep の系列 1..12・A ≤ 30 の拘束、`machine_proposal_document` の arm 制限、`slot_argv` の K2 必須、whiteboard に初期点が入らないこと、`run_series` の自系列内だけの失格集合 |
| **使わないもの** | B-5 の判定規則 (LLM 対 2 対照の対差 permutation・Holm・6 比較の族、§7)、B-5 の cohort と標本、K2 の知識射影 (主比較)、`sweep-ceiling` の副次記述 |

- S1 では値の文法 (1..1000) と、値による endpoint の同値処理は変えずに使える。
- B-5 の結果と本基盤の結果は別の登録の標本で、混ぜない。並べて報告するときは、LLM の構成 (K2 / K0)・初期点の有無・arm の集合が違うことを添える。B-5 との関係の整理は [T-2850] の起票文が求めている。

## 8. 設計時に見ていた既知結果

本書の選択は、backoff 研究の結果を見た後に行った。前向きに固定するのは、将来の新 cohort の生成・測定の規則である。

| 選択 | 見ていた既知結果 |
|---|---|
| random = log-uniform、sweep = 28 点格子 | B-5 §8 と同じ (B-10 拡張格子の地形、sweet-spot が 0〜10 µs) |
| BO の x = ln v、進化の log 尺度、λ = ln 4 (案) | 同上 (性能が値の桁で変わること) |
| 初期点 = 静的 5 / 10 µs | Pegasus の固定 backoff の結果 (無 backoff 比で fixed 10 µs が write-heavy +63.5 %、fixed 5 µs が balanced +14.4 %、n = 5、差分分析 §1)、D2214 §5 の seed |
| GP の雑音定数 3 % (案) | 旧環境の between-run floor 3.0 %、B-5 §7.2 の保守下限 |
| 主構成 R0 (参照値を渡さない) | S-1a で合成した trigger-gating 構成が `p2_2_flag_opt` 比 −9.3 %〜−55.1 % だったこと (差分分析 §1) |
| S1 = 1..1000 | B-5 §2 の受理集合 |

実行時の K0・open loop は「結果を知らずに設計した中立な対照」を意味しない。試走で調整する定数があるなら、その範囲と、本比較の前に凍結することを [T-2850] の事前登録に書く。結果を見て最良の設定だけを主比較に選ばない。

## 9. 第 2 プロトコル MOCC の差し込み口

### 9.1 前提 (この順を崩さない)

1. ccbench の branch `izanagi-mocc-xp-instrumentation` (候補 commit C = `68106660…`) を人間が GitHub へ push する (D16、[T-2858]、第 31 回項 8)。
2. D1603 の材料 3 点 (候補 commit・D297・波及表、`output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md`) を添えて、D2114 項 3 の見送り台帳の経路で pin の再承認を提示し、ユーザーが承認する。
3. 別 wave が gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を更新する。

それまで S2 は無効で、比較に入れない。今の pin は gitlink・`pin.CURRENT_PIN`・`s8b_approved.CCBENCH_FULL_SHA` とも e9e477ca で、C はどの driver 定数にも現れない (調査子の報告)。

### 9.2 S2 の定義 (差し込み候補)

「pin 前進後、固定した MOCC flags の上で、S1 と同じ literal の材料化が成立する場合の差し込み候補」とする。

- MOCC も `include/backoff.hh` を include し (`external/ccbench/cc/mocc/transaction.cc:7`、`cc/mocc/include/transaction.hh:6`)、BACK_OFF のとき `Backoff::backoff` を呼ぶ (`transaction.cc:1079-1087`)。`patches/silo-backoff-fixed.patch` は BACKOFF_FIXED を全 protocol 共通の define に足す (:12-23)。**これは差し込みが可能だという根拠であって、S2 が成立する証明ではない。**
- 合成枝の既定式は BACKOFF_FIXED の千の位で待ち方の形を切り替える (`silo-backoff-fixed.patch:69-70`。0〜999 は固定値、1000 以上は jitter などの別の形で、1000 ちょうどは jitter の幅も中心も 0 になり待機 0)。**macro の値だけを流用すると S1 と同じ 1..1000 µs の意味にならない。** S2 でも合成枝を `double now_backoff = <v>;` に置き換える literal の材料化を使う。
- flags: BACK_OFF=1 は必須。KEY_SORT と TEMPERATURE_RESET_OPT は結果を見る前に固定する (案: `orchestrator/campaign/between_run_floor.py:67` の MOCC baseline と同じ KEY_SORT=0・TEMPERATURE_RESET_OPT=1)。
- MOCC の stock は同じ flags で BACKOFF_FIXED = −1 (適応 backoff)。
- MOCC 側の温度述語 hole (`axis_mocc_temperature.py`) は proof-only で、探索・pin 前進・軸採用を認可していない (D2134 項 9)。使わない。

### 9.3 差し込むときに要るもの

- loop の genome の protocol 化 (silo 固定の 4 箇所、§2.7)。hole の marker 名 `silo-backoff-magnitude` は共有 header の中にあるが名前が silo 固有なので、S2 の記録で取り違えないよう区別する。
- MOCC の動作点の較正 (calibrator)。MOCC の certified の実績は T-2294 (tuple 200・extime 1 秒・thread 1 / 4、rratio 0・rmw) と、候補 C 上の正例・負例の 6 走の行列 (正例の stock 2 走が certified) だけで、性能規模の実績は無い。
- 性能 workload と同じ構成での correctness (新しい pin の X/P の証拠つき) と、MOCC の binary に対する Tier0 のスモーク。
- 既知最良: MOCC には `p2_2_flag_opt` に当たる実測が無い (MOCC_SPACE = BACK_OFF・TEMPERATURE_RESET_OPT・KEY_SORT の 2^3 = 8 点を消費する driver も無い、調査子の報告)。MOCC の比較は stock 比で報告し、既知最良の参照が無いことを明記する。8 点を列挙するなら、それは「指定の YCSB・PIN・条件の下での flag 参照最良」で、差し込みの必須前提ではない別の研究として計算確認を取る。
- 疎通 ([T-2849] の起票文: 20〜40 候補 × 3 workload、検証だけで約 8〜16 node 時間、準備・build・性能測定は別) は本書では再見積りしない。投入前にユーザー確認が要る (D2212 項 4)。

## 10. S3 (policy IR) を足すときの条件

S3 の設計は D2214 と `output/insights/2026-09-21/silo-function-synthesis-space/README.md` が正本で、本基盤へは未接続である (実装コードは識別子の検索で 0 件、調査子の報告)。足すときに満たす条件だけを書く。

- identity は D2214 §5 (genome flags + 骨格 / PIN + source_digest)。入口は IR JSON と C++ 本文で、S1 の proposal 文書に統一しない (§2.6)。
- **支持集合:** 5 手法の主比較 (比較 A) では、全 arm が同じ支持集合を探索するか、支持集合の制限を含む構成比較と明記するかのどちらかを、結果を見る前に選ぶ。sweep / BO だけが template の部分集合を動く構成を、純粋な探索法の比較とは呼ばない。
- 座標探索の座標、BO の方式、進化の変異・交叉は S3 の表現が固まった後に決める (§6.4)。
- LLM×C++ は比較 B で、5 手法の族に入れない。
- auditor の段は LLM 由来の候補だけに掛かる。その拒否は A だけを消費し、所要を物理費用に入れる (§5.3)。
- `.claude/agents/` の変更 (coder 新設・auditor 改訂) はユーザーの明示承認が要る (D2214)。

## 11. 実装単位 (後続 wave、本 wave では実装しない)

いずれも Codex author が実装し、新しい gate・検査・台帳は足さない。

1. 機械生成の proposal の slot を B-5 の接頭辞から外す (本基盤の名前空間の slot key を受ける。`p3_s4_loop.py:3550`・`:3557-3559`)。
2. S1 の 5 手法の系列制御: B-5 の `run_series` と同じ手順に、初期点の slot、5 arm、全 arm の A 上限を足した薄い制御。汎用 runner にしない。B-5 の module は並走の [T-2797] が発効束を扱っているので、同じ file を編集せず兄弟 module に置くのを推奨する。台帳は `SeriesLedger` を schema 名だけ変えて使う。
3. 生成器: BO (§3.2)・進化 (§3.3) を標準ライブラリで。random / sweep は B-5 の関数を名前空間を変えて呼ぶ。固定入力での値の照合試験を持つ。
4. K0 LLM の入口: 機械生成の印なし + `--allow-coder-derived-build` の経路の slot 実行、D2155 の射影の K0 への適用、初期点の whiteboard 前置き。
5. endpoint の集約: 全系列への anomaly の波及、初期点を含む資格、`p2_2_flag_opt` の block ごとの測定。
6. 費用の field: job ごとの Elapse、生成器の計算時間、LLM の役割呼び出しの回数と wall、人間の介入の記録。
7. (並列に流すときだけ) node-local の bench lock を B-5 mode の外でも使えるようにする (D2209 は B-5 mode 限定。無いと共有 lock で直列化する、D2214 §6)。
8. ([T-2858] の pin 前進の後) genome の protocol 化と MOCC の動作点の較正 (§9.3)。

計算: 上の実装に伴う開発の検査 (受入・焦点走・変異) も含め、1 タスクの job 合計が 2 node 時間以上になるなら、見積りを示してユーザー確認後に投入する (D2212 項 4、第 31 回項 1)。見積りは job Elapse の実測単価で出す。

## 12. 本 wave の経緯

- 段 1 (親): 起点 `8fd2a2f5c`、開始 gate rc 0 (08:54:15)。読取り専用の調査子 3 本 (Claude、sonnet: コードの口・裁定と後続 T・MOCC) の報告を、親が要所を file で照合して事実表にした (`verbatim/s1-facts.md`、[親] と [子] を区別)。
- 段 2: 省略 (docs のみ。親の骨子 `verbatim/s1-skeleton.md` を plan とした)。
- 段 3 (Codex read-only、reasoning medium): 相談 A (比較の公平性・情報の漏れ・正しさ境界・統計単位、09:20:49〜09:24:07) は must-fix 8 / should 3、相談 B (実効性と過剰・削除・再利用の実在、09:20:54〜09:25:05) は must-fix 7 / should 3。
- 段 4 (親): 21 件をすべて real と判定し採用した。主な訂正は、(1) S3 の具体設計と汎用 runner・汎用台帳を削り S1 の具体化に絞った (B1)、(2) 共通入力と消費 field を分けた (A2・B4)、(3) 初期点を系列ごとに fresh に測り endpoint 候補に含めた (A3・B8)、(4) A を候補提出機会とし無料の内部計算を狭めた (A4・B7)、(5) 小予算で退化しない逐次 GP-EI と (1+1) にした (B5)、(6) MOCC で macro 値だけを流用すると意味が変わることを patch の式で確かめ、literal の材料化を条件にした (B9)。裁定の全文は `verbatim/s4-ruling.md`。
- 段 5 (親): 本書を起草。

## 13. 検査の記録

(段 6・段 7 で追記する。)
