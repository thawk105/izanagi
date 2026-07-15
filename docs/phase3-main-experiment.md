# Phase 3 主実験の評価設計 (事前登録) — phase3.md から分離

`docs/phase3.md` 冒頭にあった「Phase 3 全体の完了定義と主実験の評価設計」の本体。2026-07-05 に分離した
(D35 — kickoff とは別スコープのため。読むのは coder が性能主張を生む段 = 後続段 4 以降に入るとき)。
**事前登録としての効力は分離前と同一** — coder の性能主張はすべて本設計に従う。

---

## Phase 3 全体の完了定義と主実験の評価設計 (kickoff の先)

**なぜこの節が要るか:** 下の kickoff 完了条件は「純 timing variant 1 本が certified commit し全配線が 1 周」= 機構の
配線実証にすぎない。Phase 2 は主実験込みの「Phase 2 完了の定義」(phase2.md 冒頭) を持っていたが、Phase 3 全体で
**「AI が合成した CC が優れている」を何と比較し・どう検定すれば主張できるか**が未定義だった。P2-5 で高い代償を払って
得た方法論 (機械ベースライン ablation・オラクル天井・deceptive 構造での検証・between-run floor 採否) の Phase 3 版を
事前登録する。ここは kickoff とは別スコープ (kickoff は本節を満たさなくてよい) だが、**coder が性能主張を生む段
(後続段 4 以降) の主張はすべて**この設計に従う (「sort 段以降」だと sort より前に来る coder 自律期 = 段 4 が拘束から
漏れる)。主実験そのものの実行は**後続段 6** に割り付ける (段 4/5 の中間結果は本設計に従った暫定として報告する)。

**主張 (反証可能な形で事前登録):** *coder が合成した variant が、certified serializable を保ったまま、フラグ空間最適
(P2-2 の silo 全探索 ground truth) を **between-run noise floor 超**で上回り、cross-run 再現と機序帰属
(profiler) が付く。かつその利得が **非 LLM ベースラインでは到達できない**。* (floor は比較対象ごとに再実測する —
統計計画「floor の流用禁止」参照。silo stock の実測値 3.0% を他対象に固定流用しない。)

**headline 比較対象の集合 (backoff ケーススタディの弱点への対策):** P2-4 の +38%/+11% は **silo 内 stock 最良との
比較に閉じている** (他プロトコルとも、grid 定数を調整した適応 backoff とも未比較)。Phase 3 主実験では最低限:
1. **silo stock 最良** (P2-2、同一 workload/skew/thread)。
2. **クロスプロトコル stock 最良** (mocc/tictoc/cicada 等の同一 workload 最良) — roadmap 層1 の「workload→ベース CC
   選定」を初めて実走する。mocc が write-heavy で silo+static-backoff を上回る可能性は現状未検証。
3. **ランダム EVOLVE-BLOCK 変異** (同じ編集面をランダムに埋めた対照)。
4. **「人間が変異軸を命名し機械 sweep」ベースライン** (LLM なしで軸だけ与えて grid 探索) — 利得が機械 sweep で
   再現できるなら LLM は不要という帰無仮説。

**ベースライン 3/4 の操作的定義 (最低要件を先に固定、数値詳細は後続段 6 の設計タスクで本節に追記):**
- ランダム変異 (3) は **coder と同じ編集面・同じ試行予算**で生成し、**Tier0 (コンパイル+スモーク) を通過した変異のみ**を
  比較対象に数える (通過率も報告)。コンパイル不能変異で埋めた対照は案山子であり、失敗条件 (c) の帰無仮説判定に使えない。
- 機械 sweep (4) の**変異軸の命名は coder の出力を見る前に固定**し、命名の情報源 (リポジトリ内の既知知見のどこまでを
  見たか) を記録する — 軸の**発見**自体が LLM の実証済み価値 (P2-4) なので、命名手順が曖昧だと (c) の判定がどちらにも
  倒せてしまう。coder 側のリーク制御 (残存リスク節) と対で事前登録する。

**LLM の価値の ablation:** coder に critic の機序帰属を入力する系列と、しない系列 (指標素通し) を比較する。P2-5 が
「指標を渡すこと」と「指標を LLM に解釈させること」を分けたのと同じ切り分けを合成側で行う。

**後続段 4 で配線した事前登録要素 (数値詳細は段 6、実体・不変条件のみ段 4 で固定):**
- **ablation 還流スイッチの実体:** on アーム (critic の機序帰属を次 iteration の coder/planner へ還流) と off アーム
  (緑 leading-indicators のみ渡す) の**合流 1 点** = `campaign/p3_s4_loop.py` の `make_critic_digest(reflux=)`
  (= `render_rejections` を合流するか否か)。reflux は campaign identity (search_config) に焼き別 campaign に物理分離する
  (D39 決定4)。第 3 アーム reason-only は段 6。
- **ベースライン 3/4 の substrate anchor (段 4 が固定 → 段 6 が「同じ編集面・同じ試行予算」を守るための実値):**
  編集面 = diff 検疫の hole (silo-backoff-magnitude、`include/backoff.hh` の #if 合成枝 1 行、D39 決定1)。試行予算 =
  iteration budget (10 iteration または 3600 秒、D39 決定2)。変異軸 = backoff (人間命名、coder の値提案より前に固定
  = ベースライン 4 の「軸命名を coder 出力前に固定」を自明に満たす)。生成分布・sweep grid の数値は段 6 タスク (c)(d)。
- **段 4 中間結果の報告作法:** 段 4 の 1 iteration 実走は「配線が E2E で通る」の機械実証に留め、**有意性を主張しない**
  (n 小・検証相なし・kickoff CorrectnessWorkload は同一キー競合をほぼ踏まない — 残存リスク節)。上の統計計画の guard
  「予算上 n を確保できない比較は記述統計に留め有意性を主張しない」を段 4 に適用する (検定力不足の偽陰性を
  「LLM に価値なし」と誤読させない)。

**統計計画 (P2-5/D29 を継承):** 採否は点比較でなく分布比較。差が between-run floor 以下は「差なし」に丸め、
floor〜1.5×floor は `near_floor` として cross-run 再現で裏取り。優劣は確率優越 a (同分布で 0.500) + exact/permutation
検定。headline は必ず「中央値・変動係数・floor・有意か否か・機序帰属」を添える (層3 説明可能性の統計的裏打ち)。
- **floor の流用禁止:** 3.0% は **stock silo で実測した** between-run floor (D19)。クロスプロトコル比較 (headline 2) と
  high-abort 域の合成 variant には流用しない — roadmap §3.6(3') 自身が「high-abort genome ほど run 間ドリフトが大きい」と
  明記している。headline 比較に使う floor は**比較対象のプロトコル / contention 域ごとに再実測** (between_run_floor.py)
  し、保守側 (最大) を採る (後続段 6 の前提タスク)。
- **サンプル設計 (実行前に数値を確定して本節に追記):** P2-5 の統計 (n=12 系列, exact permutation) は replay = 新規計測
  ゼロで成立した。Phase 3 は全試行が**直列実計測** (規律4) なので、(i) アームあたり系列数と 1 系列の試行予算、(ii) 検定
  単位 = **系列** (P2-5 と同じ。試行は path-dependent で独立でない)、(iii) その n で exact/permutation の最小可能 p が
  有意水準を下回るかの検定力概算、(iv) 実計測の総予算上限、の 4 点を実行前に確定する。予算上 n を確保できない比較は
  「記述統計に留め有意性を主張しない」と先に宣言する (検定力不足由来の偽陰性を「LLM に価値なし」と誤読させない)。
- **多重比較:** headline の有意主張は比較族 (ベースライン × workload) で Holm 補正する (P2-5 では Holm が実際に有意主張を
  1 つ落とした。D29)。
- **天井の不在を明示:** コード空間は列挙不能なので、P2-5 のオラクル天井に相当する真の天井は**原理的に得られない** —
  効果量は「削減余地の何割」でなく絶対差でしか語れない。代替として (i) 高試行予算の機械 sweep (ベースライン 4) の
  漸近最良値 = **経験的天井**、(ii) 既知軸 (BACKOFF_FIXED grid) の最良 = **局所天井**、を併記して効果量を規格化する。
- **deceptive 相当の検証:** P2-5 の最大の発見 (自信ある早期停止の負債、誤収束 8/12) を合成側でも検査する — リポジトリ内の
  既知勝ち筋がそのまま最適にならない workload / contention 域を主実験に最低 1 つ含め、誤収束率を報告する。含められない
  場合は「早期停止の負債は本実験では検出できない」を限界として明記する。
- **検証相 (roadmap §3.2) の配線:** headline に載せる最終候補は、開発相の 1 run 短 trace 検証だけでなく**検証相 (seed を
  変えた N 回反復 + 長 extime の trace、信頼度 1-εⁿ)** を通過していること。LLM が任意コードを書く Phase 3 でこそ「検証用
  trace が見ていないアクセスパターンでだけ正しい CC」(roadmap §3.4 の reward hack 第 1 項) が現実の脅威になる。実装は
  後続段 6 のタスク。

**失敗条件 (何が出たら negative か、正直に):** (a) 合成が certified を破る → その variant は無価値 (規律2)。
(b) 利得が between-run floor 以下 → 「差なし」。(c) 利得が機械 sweep / ランダム変異で同等に再現できる → LLM 合成
固有の価値は示せず (P2-5 と同じ negative の形)。(d) silo 内では勝つがクロスプロトコル stock 最良に負ける → 「ベース
選定を誤っただけ」で合成の価値でない。(e) target workload では勝つが**他の workload で floor 超の退行**がある →
「workload 特化」として退行込みで全 workload の結果を報告する (勝った workload だけを headline 化する選択的報告の禁止。
特化はそれ自体が本システムの目的なので負けではないが、隠すと over-claim になる)。これらを事前に失敗と定義することで
over-claim を構造的に防ぐ。

---

## 2026-07-10 追記 — 外部評価 (D44) による事前登録の穴埋め (段 6 実行前)

段 6 未着手の時点での追記。段 4/5 の中間実測 (backoff 30/40、sort comparator 1 本) は存在するが、
以下はいずれも**主張を制約する方向の強化**であり、判定を coder 有利に倒す自由度を増やさない。
出所 = Fable5 外部評価 (worklog 2026-07-10 (3)、D44)。

1. **軸適格性 (headline 候補の制約):** スカラー値 1 個の探索に還元できる軸 (backoff 等) は headline
   候補にしない。P2-5/D21/D29 が「この型の空間では LLM は機械探索から分離できない」ことを既に実証
   しており、失敗条件 (c) を構造的に誘発するため。headline 候補は**コード片合成軸 (sort 以降) に限る**。
   phase3.md 段 6 の gate 文言と同内容だが、事前登録側にも固定する (運用文書の改訂で消えないように)。
2. **失敗条件 (c) の同等性判定手続き:** 「同等に再現できる」を優越性検定の非有意で代用しない
   (検定力不足の偽陰性を「同等」と誤読する経路を塞ぐ)。事前定義: coder 最良と機械 sweep 最良
   (同一試行予算) の差が between-run floor 以下なら「同等 = (c) 成立」、floor 超なら cross-run 再現を
   経て「coder 固有」。n 不足で判定不能なら「判定不能」とそのまま報告する (どちらにも倒さない)。
3. **ベースライン 4 の二重役割の分離:** 「headline 対抗馬としての機械 sweep」(coder と同一試行予算 =
   sweep-matched) と「経験的天井としての機械 sweep」(高試行予算 = sweep-ceiling) は**別実験構成として
   別名で報告**する。両者の混同は「sweep に勝った」と「天井に迫った」の主張を混線させる。
4. **リーク制御の系全体化 (headline の前提条件):** coder 単体の遮断 (tools=[]、D39 決定7) だけでなく、
   **planner→coder 経路の遮断** (planner-v4 の Read 無制限の解消 — orchestrator 射影入力化 or 機械
   allowlist、段 6 前提タスク (h)) を headline 主張の前提条件に含める。未達のまま得た利得は
   「リーク制御不完全」の限定付きでのみ報告する。

---

## 2026-07-12 追記 — headline 主張の系レベル再構成 (D52。headline 差し替えを含む複合改訂)

**改訂の類型 (正直な二層書き分け):** 本追記は headline 主張の**差し替え**を含む (2026-07-10 追記 =
純粋な制約追加とは類型が異なる)。差し替えの正当化 = 現行 headline を成立させうる軸の不在
(backoff = 追記 1 の軸適格性違反、sort = D46 で地形なし、trigger-gating = D48 決定 2
「偵察空間 = coder 変異空間」により失敗条件 (c) が構造発火) + ユーザー承認 (2026-07-12、
worklog 07-12 (5)→(7))。付帯する個別変更は D44 決定 1 の作法 (制約方向のみ・LLM 有利の自由度を
増やさない) に従う。**設計論証・3 レンズ敵対レビュー裁定 (adopt-with-conditions ×3、must-fix
9 系統全反映) の一次資料 = `output/insights/2026-07-12_s6-headline-system-level-reframe-draft.md`**
(操作的定義の詳細もそちらが正本 — 本節は拘束力の骨子)。

**改訂時点の既知結果台帳 (HARKing 境界):** 本改訂は D50 偵察 (+61〜99% cross-run)・F 段
iteration 1〜2・axis-proposer n=1 採点・既知軸側全実測を**見た後**に行われた。S-1 = 結果既知の
「事前登録付き追試」(confirmatory と呼ばない限定表現義務)、S-2 = n=1 ピーク済み、S-3/C4/C5 =
prospective。

**主張 S (新 headline):** *合成系 (axis-proposer 軸提案 + 人間承認 gate + 軸オンボーディング +
機械偵察) は、certified serializable を保ったまま、既知軸集合の実測最良 (単軸最良の凍結集合 —
合成未探索の下界) を between-run floor 超で上回る変異軸を発見でき、利得は cross-run 再現と機序
帰属を伴う。かつ軸発見能力は診断数値の入力に依存する。* 分解: **S-1a** (系レベル発見優越、対象軸 =
trigger-gating 1 本に事前固定・交絡許容の系主張) / **S-1b** (軸寄与 = 同一 backoff 条件の gate
on/off 差分 = D50 vs ident_all、機序裏書き) / **S-2** (提案ラウンドの適格率が C4 無作為選定対照
から分離) / **S-3** (C5 帰属遮断で適格率が退化。主要 endpoint は適格率 1 本)。

**拘束力のある操作的定義 (骨子):**
- 既知軸集合 (2026-07-12 凍結、以後追加しない) = P2-2 フラグ最適 / BACKOFF_FIXED grid 最良 /
  sort 全列挙最良 (列挙定義再利用・数値は D46 firewall で再計測)。判定 workload = 3 類型全て。
  headline 判定に使う比較点は全て同一 campaign 系列で再計測 (既存実測は参考併記のみ)、絶対
  throughput の分布比較 + 共通 stock 併記、floor 対象別再実測。二段階判定 (偵察型スクリーニング
  → 検証相の分布比較 + 確率優越 + exact/permutation)。deceptive 相当検証 = D50 の勝ち gate
  workload 間入れ替わりを充足根拠に報告義務化。
- C4 = 選定のみ無作為 (mapped 全領域から seed 固定 RNG 抽出)・記述は同一条件 (同一プロンプト・
  同一射影入力で提案生成 — 差分は hole 位置選定のみ)。C5 = diagnostics 除去のみ。**採点は全アーム
  共通基準** — D47 決定 4 基準 (2) は C5 で恒真 fail するため (2')「機序仮説が対象コードの実在
  構造に繋がり反証可能な観測を指定するか」に置換 (attribution 接続は本アームのみの追加観測に降格)。
  由来盲検 (混合ランダム順・ラベル除去・1 件ごと fresh 採点)。入力射影は pinned HEAD で凍結
  (hash を provenance 記録)。n = 20/アーム基準 (検定力概算: 0.6 vs 0.1 を Holm 初段 α=0.0125・
  検定力 80% で分離。最終 n と成功閾値は着手時に本節へ追記 — **確定済み、本追記末尾の
  2026-07-13 節**)。ラウンド二値判定・実質同一出力の縮約規則・(f)(g) とも三値判定
  (成立/不成立/判定不能)。
- trigger-gating の headline 昇格の形式要件 = 独立再命名 canary (匿名化骨格 patch からの構造 3 項
  再導出、最終裁定者は人間、不一致時は headline 使用停止。circular ゆえ一致を肯定的証拠に使わない)。
  命名 provenance 完全記録は必須条件。
- substrate anchor (旧対照 3/4 の編集面) は backoff hole のまま**休眠** — trigger hole への差し
  替えはしない ((c') 自認の hole での軸内対照は主張なき計測)。発火 = 旧主張の復活条件成立時に
  日付付き追記で固定。

**失敗条件 (改訂版):** (a)(b)(d)(e) 不変。**(c) 系レベル版** = S-1a が既知軸実測最良と floor
以下の差 → 軸発見の固有価値なし (判定不能はそのまま報告)。**(f)** = S-2 ラウンド二値が C4 と
分離しない (三値判定)。**(g)** = C5 で適格率が退化しない → S-3 棄却、**このとき主張 S から帰属
依存節を削除した縮小主張として報告** (headline 文言を変更し棄却事実を併記)。**(c') 事前自認** =
trigger-gating の軸内探索で LLM は機械列挙を上回れない (D48 決定 2) — 主張範囲外として最初から
明記。F 段実測 (iteration 1〜2、本動作点で探索停止推奨) と整合。

**旧 headline 主張の扱い:** 削除せず scope 限定で保存 — 非列挙のコード片軸 (D48 差し戻し事項の
消化後または将来軸) が実体化し偵察が floor 超地形を確認した場合にのみ検証可能。**F 段の拘束:**
主張 S の下で trigger-gating の軸内実計測は headline 判定に寄与しない — F 段継続は 8c 配線検証の
最小 iteration に限定、動作点再ホストは 8b または非列挙軸の事前登録と束ねた別途正当化を要する。

**多重比較:** Holm 族 = S-1〜S-3 の検定のみ ((c') は宣言事項ゆえ族外)。

**既知限界 (主張時に必ず限定表現):** 既知軸集合はリポジトリ探索履歴依存の凍結有限集合 (合成
未探索の下界 — S-1a のマージンが合成で埋まりうる規模かの議論を報告義務化) / S-1 対象軸は n=1 /
S-1 は結果既知の登録追試 / 射影者の記憶汚染 (provenance が代償) / 採点の意味判断に機械 backstop
なし・C5 の構造的 unblind / 再命名 canary の circular / workload 特化 (8b) は本改訂の主張に
含めない。

### 2026-07-13 着手時確定 — 提案ラウンド束の n・成功閾値・採点工数上限 (+ 付帯規則の二層書き分け)

上記「最終 n と成功閾値は着手時に本節へ追記」の履行。**認可ブランクの充足 (層 1 = 最終 n・
成功閾値 (適格率の下限)・採点工数上限の 3 点) と、実走に必要な付帯規則の確定 (層 2) を書き
分ける** (「数値確定のみ」とは称さない — 層 2 は新規則の確定を含む)。3 レンズ敵対レビュー
(統計 / 事前登録作法 / fails-closed 実効性、独立コンテキスト) の must-fix 全反映。**裁定台帳 =
`output/insights/2026-07-13_s6-n-determination.md`** (レビュー全文 JSON 同梱)。

**層 1 — 認可ブランクの充足:**
- **最終 n = 20/アーム** (本アーム / C4 / C5、計 60 提案ラウンド)。n=19 で検定力 0.81 に達するが
  基準どおり 20 へ保守丸め。
- **成功閾値 = 連言**: (i) Fisher 正確検定・片側 (本アーム適格率 > 対照)、Holm 族 4 (S-1a /
  S-1b / S-2 / S-3、p 値昇順に α = 0.05/4, 0.05/3, 0.05/2, 0.05/1) で有意、**かつ** (ii) **本
  アーム適格率 ≥ 0.5** (10/20。§上記の「適格率の下限」— 対照が構造的低率のとき相対検定単独で
  通る偽勝を塞ぐ絶対フロア。出所 = n=1 実証 0.67 の保守丸め)。S-3 (本 > C5、片側) も同型・同
  フロア。C5 想定率 0.1 (S-2 と同型計算)。
- **採点工数上限 = 総採点 120 件** (60 + 補充上限 60)。超過が必要になった時点で当該検定は
  判定不能として報告。
- **検定力 (厳密計算・全数総和 = `orchestrator/campaign/s6_proposal_rounds_power.py`):** 仮定
  効果量 0.6 vs 0.1・α = 0.0125 (Holm 初段 = 単独検定の保守下界) で**連言 0.802 ≥ 0.80** (Fisher
  単独 0.846)。効果量の出所自認: p1 = 0.6 は n=1 実証 (3 提案中 2 適格) の保守丸めで n=1 由来、
  p2 = 0.1 は実測裏付けなしの事前推定。

**層 2 — 付帯規則の確定 (いずれも fails-closed 方向):**
- **補充規則:** 「実行失敗」= 提案内容と独立に採点前へ機械判定できる閉じた列挙のみ — (a) API
  エラー (transport 異常・timeout 含む)、(b) 構造化出力の schema 不合格 (必須フィールド欠落)。
  列挙外 (内容が空虚・退化した提案を含む) は実行失敗でなく採点に回す。補充はスロットごと retry
  上限 2、判定根拠 (ステータス / schema 違反名) を provenance 記録。上限内で 20/アーム 未達なら
  当該検定は判定不能 (§5 (f) の具体化 — 補充は純機械故障のみを救済し、判定不能原則を置換しない)。
- **scored-but-undecidable** (採点に到達したが採点者が二値を決めきれない) は不適格 (= 0) に倒す。
- **C4 抽出粒度 (今確定 — 実走前への繰延を撤回):** 母集団 = n=1 実証で凍結済みの
  edit_surface_map (`output/insights/2026-07-10_s8a-n1-provenance.json`、pinned HEAD)。抽出 =
  seed 固定 RNG による領域一様・**復元**抽出 (n = 20 > 領域数のため復元は必然)。seed・列挙物
  hash を provenance 凍結。記述工程は本追記本文どおり同一条件 (差分は hole 位置選定のみ)。
- **パイロット除外:** n=1 実証の 3 提案は検定標本に含めない (n = 20 は全アーム fresh 生成)。
- **判定規則の条件節 (誤読防止):** 「非有意 = 不成立」と読むのは n = 20/アーム 完走時。検定力
  0.802 は仮定効果量の下での値であり、完走が保証する量ではない — 真の対照率が仮定より高い場合の
  実効検定力は低い (感度: 0.6 vs 0.2 → 0.56、0.6 vs 0.3 → 0.29。n = 40 でも 0.6 vs 0.3 → 0.64)。
  その帰結は不成立 / 判定不能側 = 本主張に不利 = 保守的な事前規約として受け入れる (観測効果量に
  よる事後の言い逃れをしない)。S-2 / S-3 の Holm 族調整済み最終判定は S-1a / S-1b (検証相、n は
  別途固定) の p 値確定まで閉じない。
- **縮約規則との関係:** 縮約は副指標 (相異なる適格軸数) のみに作用しラウンド二値に触れない
  (提案内 dedup でも代表が残るため「ラウンドに適格提案 ≥ 1」は不変)。(g) の判定語法は「退化を
  示せない (fail to reject)」— 証拠の不在を不在の証拠と読まない。採点は全アーム共通基準 (2')
  (本追記本文)。
- **実走運用の解釈正本 (2026-07-13 追記):** 本節の曖昧語の操作化 (採点単位・補充トリガの
  三分・盲検保証の範囲・seed の人間確定等) は
  `output/insights/2026-07-13_s6-round-execution-design.md` (3 レンズ敵対レビュー済み v2) が
  正本 — 凍結値は変更していない。

---
### 2026-07-15 着手時確定 — S-1 サンプル設計 4 点 (性能分布比較の n・検定単位・検定力・総予算)

統計計画「サンプル設計 (実行前に数値を確定して本節に追記)」4 点の履行。2026-07-13 節と同じ
二層書き分け (層 1 = 認可ブランクの充足、層 2 = 実走に必要な付帯規則の確定)。3 レンズ敵対
レビュー (統計 / 事前登録作法 / fails-closed 実効性、独立コンテキスト = codex gpt-5.6-sol
reasoning high) の must-fix 反映済み。裁定台帳 =
`output/insights/2026-07-15_s1-sample-design.md` (レビュー全文 JSON 同梱、同一 commit)。

**改訂の類型 (正直な開示):** 本追記の大半は認可ブランク (「実行前に数値を確定」) の充足と
fails-closed 方向の付帯規則だが、**1 点だけ実質改訂を含む** — 統計計画本文の「検定単位 =
系列」の S-1 への適用を「独立セッション」に確定する箇所 (層 1 (ii))。これは検定を可能にする
方向 (n 増) の変更であり D44 作法 (制約方向のみ AI 改訂可) の範囲外のため、**ユーザー承認を
発効条件とする。承認までは S-1 実走禁止** (未承認のまま計測に入ったら protocol 違反として
当該計測を無効とする)。

**2026-07-15 改訂時点の既知結果台帳 (HARKing 境界):** 本節の数値は次を閲覧済みの状態で確定
した — D50 偵察 (gate on/off +61〜99%、3 workload cross-run 再現)、fresh between-run CV
実測 (silo stock baseline: write-heavy 0.67% / balanced 1.07% / read-heavy 0.11%)、wired
保守 floor 3.0% (D19)、P2-2 / BACKOFF_FIXED / sort 各既知軸の過去実測、s8a F 段 iteration
1〜2。したがって S-1 は結果既知の登録追試 (confirmatory と呼ばない)・対象軸 n=1 という
限定は不変であり、以下の N・検定方向・統計量・gate 規則はこれらを見た後の固定である。

**層 1 — 認可ブランクの充足 (4 点):**

- **(i) アームあたり系列数と 1 系列の試行予算:** アーム = 比較セル (構成 × workload)。
  セル構成 = 3 workload (rr50/rr5/rr95) × 6 構成 {系側 best gate (balanced/read-heavy =
  g_rl、write-heavy = g_rt に事前固定), ident_all (S-1b 対照), P2-2 フラグ最適,
  BACKOFF_FIXED grid 最良, sort 全列挙最良 (read-heavy は sk_ad 事前固定 — §2.1 既定),
  共通 stock} = **18 セル**。検定標本 = **N = 8 独立セッション/セル** (時間分離した 2
  campaign ブロック × 4、計 144 セッション)。これと**別に** floor 推定標本 = N_floor = 8
  独立セッション/セル (先行 floor campaign、計 144 セッション。検定標本と floor gate 入力の
  分離 — 同一標本から gate と検定を両方導出しない)。1 セッション = 確定動作点 (RECORDS=1M /
  THREADS=48 / EXTIME=3s / REPS=5) の measure_point 1 回、観測値 = セッション reps median。
  sort read-heavy の欠測補充 (sk_ad + stock) と対象別 between-run floor 再実測は上記に
  **包含** (別枠計上しない — checklist 該当 2 項はこの campaign 群で閉じる)。
- **(ii) 検定単位 = 独立セッション (S-1 限定・ユーザー承認待ち):** 統計計画本文の「検定単位
  = 系列 (P2-5 と同じ。試行は path-dependent で独立でない)」は LLM 探索実験の規定であり、
  探索実験を復活させる場合はそのまま生きる。D52 で登録追試に再構成された S-1 は固定構成の
  再計測であり path-dependence が存在しないため、S-1 に限り検定単位を独立セッションとする。
  セッション間の独立は**操作的仮定** (プロセス分離 + RNG の run ごと自己シード —
  `external/ccbench/include/random.hh` Xoroshiro128Plus は std::random_device で初期化され
  ycsb に CLI seed はない) であり、時間ドリフト等の系列相関は除去されない — その対処は
  層別化・ランダム化 schedule (層 2) が担い、独立性の証明とは主張しない。within-run reps は
  セッション内相関のため観測単位にしない (median に縮約)。
- **(iii) 検定と検定力:** 検定 = **層別 exact permutation** (campaign ブロック内の割付数を
  保存する全列挙 = C(8,4)² = 4,900 分割、片側)、**主統計量 = 層別 rank-sum** (層内 rank-sum
  の和、van Elteren 型。確率優越 A と単調同値)。tie は tail 包含の保守則 (P(T ≥ T_obs))。
  中央値差・確率優越 A・セル CV は効果量として併記 (判定には使わない)。完全分離時の達成 p =
  1/4,900 ≈ 2.0×10⁻⁴ < Holm 初段 α = 0.0125 (族 4 = S-1a/S-1b/S-2/S-3、2026-07-12 追記)。
  N=8 の根拠 = **p 値解像度の確保** (完全分離時に Holm 全段を通る + 少数の順位交差への耐性)
  と between_run_floor.py の独立 8 セッション前例。**prospective power は未保証と明記する**
  (対象セル、特に high-abort 構成の分散は floor campaign まで未実測のため)。参考の感度計算
  (既知結果条件付き・N 選定の根拠にしない): 中央値差 > 3.0% かつ CV ≈ 1.1% (stock fresh 実測)
  なら標準化差 d ≥ 2.7 で事実上完全分離、S-1b は D50 実測 +61〜99% が floor の 20 倍超。
  事後の「判別力再評価」は行わない — N=8 完走時は常に p*・効果量・CV を報告し、判定不能の
  発火は層 2 の機械条件のみ。
- **(iv) 実計測の総予算上限 = 合計 12 時間 (宣言値、拘束):** 時間計上 = S-1 の全 campaign
  プロセスの monotonic wall time を**成功・失敗・timeout・機械故障 retry・build・verify・
  bench・floor campaign・検証相校正・検証相のすべて込み**で台帳に累積する。driver は各
  セッション起動前に残予算を検査し、不足なら起動せず、その時点で未完走の**全比較を対称に**
  判定不能へ倒す (観測値を見た選択的な打ち切りをしない)。内訳概算 (拘束は総額のみ): floor
  campaign ≈ 1.5h、検定 campaign ≈ 1.5h、variant build + 開発相 verify (18 構成) ≈ 1h、
  検証相校正 ≈ 0.5h、検証相 ≤ 4h、機械故障 retry 予備 ≈ 2h。予備枠の使途は機械故障 retry
  のみ (層 2 の閉じた列挙)、枠の目的間移転は禁止。
- **(iv 付属) 検証相の拘束数値 (繰延べの撤回):** 対象 = headline 最終候補 = 系側 gate 構成
  のみ (g_rl / g_rt、§7 既定)。**N_verify = 8 独立反復/workload** (計 24 verify)。long
  extime = 校正で確定: trace-enabled build で extime {3, 6, 10}s 各 1 回の verify 所要を
  実測し、**1 verify ≤ 10 分に収まる最大値**を採る (下限 3s = S2 前例)。確定値は本節へ
  日付付き追記。総検証相予算 ≤ 4h、超過見込み時は extime を下げ **N_verify は削らない**
  (信頼度の指数を観測後に弱める自由度を残さない)。判定 = 24 verify 全て anomaly ゼロで
  pass、1 件でも anomaly → 当該 variant は失格 (規律 2)。**形式的信頼度 1-εⁿ は主張しない**
  (ε の定義・seed identity の記録・trace の永続保全 (現行 pipeline は verify 後に trace を
  削除する) のいずれも無いため) — 「独立反復 n=8 × 3 workload で anomaly ゼロ」という操作的
  事実として報告する。roadmap §3.2 の 1-εⁿ 表現は本 S-1 報告では限定表現に置換する。
- **(iv 付属の校正確定 — 2026-07-16 追記) long extime = 3s に確定:** read-heavy (rr95) ×
  系側 gate `g_rl` の trace-enabled build で extime {3, 6}s を各 1 回実測した (10s は
  「600 秒超過で残候補打ち切り」の規則により未実測)。verifier wall time = 433.3s / 974.7s、
  いずれも verdict = serializable・certified。600 秒以下の最大値として **extime = 3s** を
  採る。検証相の総所要見込み ≈ 433.3s × 24 verify ≈ 2.9h ≤ 4h (予算内)。全候補の生値・
  構成 provenance・選定規則は `output/env/linux-baremetal/calibration/s1_verify_extime.json`
  (人間可読版は同名 `.md`) に凍結した。

**層 2 — 付帯規則の確定 (いずれも fails-closed / 機械判定可能な形で):**

- **スクリーニングの gate 連言化 (選択推論の遮断):** 全 18 セル・全 N=8 を**無条件に完走**
  する (途中結果による比較の除外・差し替え・停止をしない)。比較ごとに
  p\* = p_perm (下記 gate を全通過した場合) / p\* = 1 (いずれかの gate 不通過)。
  gate = {(1) 中央値差の点推定 > floor_cmp、(2) 2 campaign ブロック間で差の方向が一致
  (cross-run 再現)}。**S-1a = max over 9 比較 (3 workload × 3 既知軸基準点) の p\*、
  S-1b = max over 3 比較 (workload 別 gate on/off) の p\*** を各 1 本 Holm 族 4 へ投入
  (intersection-union、α inflation なし)。gate 不通過はそのまま (c) 系レベル失敗条件の
  評価に入る。本設計は「独立な検証相」を持たない — ブロック化した単一登録追試 + gate 連言
  であり、その旨を報告に明記する (§2.1 の「スクリーニング → 検証相」の二段階は本 gate 連言
  として実装される、の読み替えを含む)。
- **floor_cmp の定義 (純関数):** floor_cmp = max(floor campaign での当該比較両側セルの
  between-session CV, 3.0%)。floor campaign 標本のみから計算し、検定標本を使わない。
  near_floor 帯 (floor_cmp〜1.5×floor_cmp) の cross-run 裏取りは gate (2) が担う。欠測・
  非有限値・入力 hash 不一致は判定不能へ倒す。
- **比較点の事前固定と freeze (改竄検出込み):** 系側 = D50 の workload 別勝ち gate に事前
  固定 (再計測での構成再選択をしない)。既知軸側 = 過去実測 argmax 構成に事前固定。
  **machine-readable freeze (workload × 構成ごとの canonical genome/構成・選定元 artifact
  のパスと hash・argmax/tie-break 規則・CCBENCH_COMMIT pin・生成時 HEAD) を S-1/floor 計測
  開始前に生成・commit し、driver は毎起動時に freeze の存在と hash を照合、不在・不一致は
  起動拒否** (positive control: 改変 freeze で起動拒否することをテストで確認)。freeze には
  workload ごとの {gate_on, ident_all} 対応表と「gate 述語以外の構成が同一」の機械 diff
  検査を含める (S-1b が別構成差に化ける経路の遮断)。再計測での順位入れ替わりは観測として
  報告するが基準点は動かさない (§2.1 既定)。
- **certified gate の consumer 登録:** 性能標本はすべて pipeline.evaluate 経由 (COMMIT を
  書く唯一の経路) で取得し、S-1 report は各標本について certified evidence (variant_id・
  src_token・verify 構成) との照合を hard gate とする。measure_point 直接呼び出しによる
  標本投入は driver が拒否し、負例テスト (certified を欠く標本が report 生成を fail させる)
  を実装完了条件に含める (規律 2 の consumer 実在化)。
- **schedule の凍結と実行照合:** campaign × 周回 × セルの実行順は事前固定 seed の均衡
  ランダム化で生成し、schedule 本体の hash を freeze と同時に commit。実行時は event
  ledger (WAL) と schedule の完全一致 (重複・欠落・順序逸脱なし) を report 生成の hard gate
  とする。逸脱 = 当該 campaign を判定不能 (schedule mutation の positive control を実装
  完了条件に含める)。時間分離の最小条件: campaign ブロック間は別プロセス起動 + 開始時刻を
  ledger に記録 (定量閾値は置かない — ブロック間差は層別化が吸収し、ブロック efect の観測
  値は報告に併記)。
- **機械故障 retry の閉じた列挙:** retry を許すのは (a) プロセス異常終了 (非ゼロ exit /
  signal)、(b) build 失敗、(c) measure_point の例外、のみ。retry ≤ 2/セッション、判定根拠を
  provenance 記録。観測値の内容 (差が小さい等) を理由とする再測は禁止。retry 上限超過で
  当該セル n 未達 → 当該セルを含む全比較を判定不能。
- **「seed×N」の操作的定義:** ycsb は CLI seed を持たず RNG は run ごとに自己シードする —
  検証相・性能計測とも「seed×N」は**独立 N 反復**を意味し、決定論的 seed 固定は導入しない
  (CCBench 改変 (D16) を要するため)。独立性は操作的仮定 (層 1 (ii) と同じ限定)。
- **統計実装の凍結 (S-1 計測開始の前提条件):** 層別 exact permutation・層別 rank-sum・tie
  規則・p\* 純関数の実装は、数式・テストベクトル (完全分離 → 1/4,900、既知の順位交差
  パターン数例、tie ケース) とともに S-1 計測開始前に commit し、実装ファイルの hash を
  freeze に含める。
- **判定不能の発火条件 (機械化・三値判定):** (1) retry 上限超過による n 未達、(2) 総予算
  12h 超過 (起動前検査で発火)、(3) freeze / schedule ledger / certified 照合の失敗、
  (4) floor_cmp 入力の欠測。いずれも成立/不成立に倒さずそのまま報告する。

**S-1 計測開始 gate (すべて成立するまで実走禁止):** (1) 本節のユーザー承認 (検定単位)、
(2) freeze 生成 + commit、(3) driver の schedule/ledger/certified/時間台帳/判定純関数と
positive control テストの完備、(4) 統計実装 + テストベクトルの commit、(5) 検証相校正の
完了と extime 確定値の本節追記。

---

**2026-07-15 承認記録:** 上記の検定単位の実質改訂 (層 1 (ii) の「系列 → 独立セッション (S-1 限定)」) を含め、本追記はユーザー承認済み・発効。承認により「承認までは S-1 実走禁止」の条件は解除された (計測開始 gate の残り 4 条件 (2)〜(5) は引き続き未充足のものが gate として生きる)。
