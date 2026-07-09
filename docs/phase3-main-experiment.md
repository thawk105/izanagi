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
