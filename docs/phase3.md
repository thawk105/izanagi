# Phase 3 — LLM コード合成 (planner/coder/auditor)

**目的:** roadmap §2 層2(b) **コード粒度の合成**。CCBench コードの `EVOLVE-BLOCK` 領域を LLM (coder) が
diff で書き、フラグ空間の外に最適化 variant を合成する。P2-4 backoff ケーススタディ (critic 帰属が
フラグ空間外の静的 backoff 合成を駆動し certified なまま勝った) がその予告編。Phase 2 の negative result
(P2-5: フラグ探索は自明) が「なぜ合成が要るか」を動機づける。

**最終成果物 (CLAUDE.md):** 新しい CC + なぜ速いかの説明 (層3) + 試行錯誤の記録。

**設計の出所:** 多エージェント workflow (Map5→Design→Critique3→Finalize) + 敵対的安全検証で kickoff を固め、
ユーザー承認 (2026-06-29)。decisions D22。**絶対規律 (特に 1/2/3/5/6) はここで初めて load-bearing になる**
(LLM が正しさを破りうるコードを書く)。

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
  「記述統計に留め有意性を主張しない」と先に宣言する (検定力不足由来の偽 negative を「LLM に価値なし」と誤読させない)。
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

## kickoff の最小スコープ (段階導入・規律5)

**完了定義を 1 ループに絞る:** 「EVOLVE-BLOCK 機構 + coder.md + **純 timing variant 1 本**」が
`Tier0(compile/smoke) → pipeline.evaluate → verify → bench → WAL` を 1 周し、stock が cache-hit で
certified commit する (正確な合格条件は下の「完了条件 (2 項)」— no-op の identity 後方互換と純 timing の
cache-miss 1 周は別の主張で、両方要る)。新機構の束を**正しさ的に枯れた足場 (純 timing) で先に通す**のが最小手。

### なぜ first target = 純 timing (静的 backoff) か。lock-sort は撤回
draft 第一候補の sort-strategy (lock 獲得経路) は 3 批判全員が high severity で撤回勧告 (実コード裏取り):
- **verifier は lock 獲得順をトレースしない** (commit 時の (epoch,tid) のみ emit, transaction.cc:517-540)
  → lock 経路の正しさを certify 不能 = **規律2 の穴**。
- silo は no-wait (競合即 abort, transaction.cc:154-157 / Options.cmake:34) ゆえ「sort=デッドロック回避」は
  誤診断。sort が動かすのは liveness で、commit 枯渇 (trace-empty abort) として現れ正しさ違反と検出されない。
- 現 CorrectnessWorkload (tuple200/thread4, pipeline.py:49-51) は同一キー競合をほぼ踏まず lock 経路の
  certify が空振り。

→ **純 timing は abort-path のタイミングにしか触れず lock/validation 論理に一切触れない** = 正しさ攻撃面が
構造的に最小、P2-4 で certified 実証済 (BACKOFF_FIXED, backoff.hh:102-106)。sort は機構が枯れた**2番目の
変異軸**に繰り延べ、そこで S2 を単独 load-bearing にする。

### EVOLVE-BLOCK 機構 (P2-4 inert-patch=D18 の一般化、新構文は発明しない)
- `// EVOLVE-BLOCK-BEGIN <id>` / `// EVOLVE-BLOCK-END <id>` で領域画定。領域内は
  `#if <AXIS>` (= coder 合成枝) `#else` (= stock 逐語温存) `#endif` の二枝。軸の極性は sentinel 規約に従う
  (kickoff の `silo-backoff-magnitude` は `#if BACKOFF_FIXED >= 0`、既定 -1=stock 適応が #else を選び、0 以上で
  合成枝 = D18/Options.cmake の `-1=stock adaptive; >=0=fixed` 契約と一致。`> 0` ではない: 値 0 も合成枝)。
- **マーカーと #else 枝は人間が一度入れる骨格 (template patch)。coder が触るのは #if 枝の中身だけ**
  (auditor のレビュー対象を局所化)。
- **閉じた領域制約:** #if 枝は既存 silo API を呼ぶ straight-line code のみ。**#include 追加・新規関数/マクロ
  定義・struct/global/型定義の追加改変を禁止** (型レイアウト変更は trace/perf 両ビルドに入り nm 検査も
  name-based hook も素通りする = observer-effect-by-data-structure 対策)。coder は対象 1 patch 以外の
  ファイルを作成/改変しない (**H3 hook 配線後に機械強制。配線までは coder diff の人間レビューが唯一の gate** —
  coder.md タスクの前提 gate 参照。hook は未配線 = 現在形の保証ではない, D30)。
- **適用の隔離:** patch は submodule working-tree への out-of-band 適用 (HEAD は dff0f1e pin 不動 →
  campaign-id 不変)。1 variant 評価ごとに clean→apply→build→revert。apply 前に対象が pinned-clean か
  assert (汚れていたら fails-closed abort)。**この駆動部 (apply/revert ハーネス) は現状記述のみで実装が無い
  (歴代の patch 適用は手動) — 下の blocking タスクで実装する。**

---

## kickoff タスク (blocking 順)

- [x] **(blocking) cache_key + variant_id の honest 拡張**: source_digest を **preprocess 後 (`cpp -E`)
      正規化出力の sha256** で計算し、buildcache の cache_key (buildcache.py) と **variant_id (WAL キー,
      pipeline.py:41)** 両方の pre-image に織り込む。マーカーコメント挿入は生バイトを変えるが preprocess 後は
      #else 枝が原本と同一 → inert template が真に同一 digest (D18 inert 実証を継承、生 sha256 だと全 miss)。
      variant_id が現状 canonical() のみ hash ゆえ**同フラグ別 diff が WAL/critic で alias する穴**を identity
      端から端まで塞ぐ。対象は固定集合 (EVOLVE-BLOCK ファイル + Options.cmake + CMake)。Genome.canonical 生
      表現は据え置き (後方互換)。同 campaign 内で異なる source_digest が同一 variant_id を共有しない assert。
- [x] **(blocking) EVOLVE-BLOCK template patch**: silo abort-path 周辺 (BACKOFF_FIXED 軸再利用) に骨格を 1 つ。
      既定 inert を preprocess 後ハッシュ一致 → stock genome cache-hit で実証。
- [ ] **(blocking) verify の abort 数を WAL に記録**: 現配線は abort 数をどこにも記録しない — `_run_trace` は
      `(ncommit, rc)` のみ返し ccbench stdout を捨て (pipeline.py:94-102)、STAGE_VERIFY_DONE payload は
      verdict/certified/commits/anomalies の 4 項のみ (pipeline.py:187-189)、trace レコードも C/R/W の 3 種で
      abort イベントを持たない。よって完了条件 2 の「abort > 0 確認」が**検査不能**。ccbench stdout の
      `abort_counts_:` (common/result.cc:34) をパースして STAGE_VERIFY_DONE payload に `aborts` として記録する。
- [ ] **(blocking) apply/revert ハーネス**: 「1 variant 評価ごとに clean→apply→build→revert」(上の機構節) の
      駆動部を実装する。apply 前の pinned-clean assert + revert 後の `git status --porcelain` 空 assert を
      fails-closed で持ち、順序を **apply → resolve(src_token) → build → revert** に固定する (resolve より後に
      tree を動かさない)。
- [ ] **(blocking) build 後の digest 再照合 (TOCTOU 遮断)**: resolve→build 間に working-tree が動くと、digest と
      実バイナリが食い違ったまま**共有ビルドキャッシュ (campaign 非依存) に永続**し以後 cache hit で沈黙再利用される
      (偽 cache hit = 規律2 直撃)。bench_lock はベンチのみ排他・campaign.lock は記録ファイルで mutex ではなく、
      複数セッション並走は現に運用実態。build 完了直後に src_token を再計算して resolve 時の値と照合し、不一致は
      build dir を破棄して fails-closed abort する (再計算は数十 ms で規律4 に反しない。git worktree 隔離 =
      後続段 5 までの最小防壁)。
- [ ] **(blocking) source_digest の #include 死角の閉塞**: digest は preprocess 前に `#include` 行を無条件除去する
      (source_digest.py `_INCLUDE_RE`) ため、coder が EVOLVE-BLOCK ファイルに #include を追加/差し替えすると
      **バイナリが変わるのに identity 不変** = stock と alias → 既存バイナリの cache hit で**変更が一度も
      コンパイルされないまま certified 記録**になる。現状この経路の防壁は道Y の hook 禁止 (D23) だけで hook は
      未配線 — 方針 A が消したはずの単一障害点がこのベクタで復活している。identity 核で塞ぐ:
      EVOLVE_BLOCK_SOURCES の #include 行集合が HEAD と異なれば fails-closed abort (最小)、または #include
      行集合の生ハッシュを src_token の pre-image に織り込む (恒久。stock 正規化との後方互換に注意)。
- [ ] **(進行中・方針 A で再設計) H3 hooks = 明白な直接書き込みを止める最小の第二防壁** (実装済・**未配線**, D30):
      `guard_write.py` / `guard_bash.py` は実装済みだが、**2 巡目敵対検証で real 13 件 (critical 1 = コメント行連結
      (backslash-newline splice) でコメント除去器を騙し `#define TRACE`/`__DATE__` を素通しさせる GW2R-1) が残存**し、
      `.claude/settings.json = {}` で**未配線 = 第二防壁は現状ゼロ** (insight `2026-07-03_phase3-task3-h3-hooks-round2-handoff.md`)。
      2 巡目 real の質が「テキスト検査で C++ 翻訳フェーズ (行連結・単独 CR 正規化) や shell (glob/here-string/pipe) を
      完全再現するのは原理的に無理」を実証したため、**方針 A (ユーザー承認 2026-07-03) = hook の責務を一次防壁へ委譲**する:
      - **identity の honest さ (偽 cache hit / `#ifdef` / build 時マクロ由来のバイナリ差)** → **source_digest の
        preprocess 後ハッシュ** (上の「cache_key+variant_id 拡張」タスク、完了済) が一次防壁。coder が `Options.cmake` や #if 枝内で
        バイナリを動かせば digest が変わり cache_key/variant_id が動く = テキスト検査の完全性に依存しない
        (#include 死角は上の blocking タスクで閉塞)。
      - **観測者効果の分離 (TRACE の perf ビルド混入)** → **観測者効果の二重検査** (下の blocking タスク、述語 =
        diff-of-diffs) が一次防壁。data-structure 由来も含めて捕える。
      - **hook (第二防壁) に残る責務は「明白な直接書き込み」だけ**: WAL/lock/build-variants/campaign dir への
        Bash/Edit 直接書き込みと designated ソース外への Write を拒否 (規律2 の verifier 迂回阻止)。
        **「payload 検査が `#ifdef` の唯一の防壁」という旧設計 (単一障害点) は放棄** — GW2R-1/SPEC-2 が反証した。
        盛らない (この 2 本だけ)。
      配線を戻す前に、方針 A の順で消化する: (1) 一次防壁 (preprocess ハッシュ・観測者効果二重検査) を先に
      load-bearing にする、(2) hook を最小防壁へ軽量化 + false-positive (計測層の過剰拒否 4 件) を除去する、
      (3) settings.json 配線 (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash`)。実装・2 巡の検証の詳細は
      insight `2026-07-02_...adversarial-review.md` / `2026-07-03_...round2-handoff.md`。
- [ ] **(blocking) 観測者効果の二重検査 — まず述語仕様を確定してから実装**: nm の name-based 検査
      (buildcache._assert_no_trace_symbols) を補完する一次防壁 (D30)。ただし旧仕様の「両ビルドの preprocess 出力を
      diff」という素朴な述語は**成立しない** — trace ビルド (TRACE=1) と perf ビルド (TRACE=0) の preprocess 出力は
      `#if TRACE` ガード領域で**正当に**食い違うため、素の diff は必ず大量差分を出す。仕様確定が実装より先:
      - **比較基準の候補 = diff-of-diffs**: 同一 working-tree の preprocess(TRACE=1) − preprocess(TRACE=0) の差分
        `D_variant` を取り、pinned HEAD (izanagi-trace baseline) から同様に取った `D_stock` と**一致**することを
        assert する。「variant が TRACE 条件付きコードを追加/改変していない = trace/perf の差は stock の trace-hook
        由来のみ」を機械保証し、残存リスク節の「#ifdef TRACE の内側に挙動差を隠す攻撃」も D_variant≠D_stock で捕える。
      - **発火単位** = 毎 variant の trace/perf ビルド直後 (buildcache.build の出口)。
      - **fails-closed** = diff 不一致・preprocess 取得不能のいずれも abort (警告に格下げしない)。
      - **保証しないこと (正直に)**: 検証専用メタデータが #ifdef の**外** (両ビルド共通) に常駐するケースは
        この述語では判定不能 (機械には CC 本来か検証専用か区別できない)。ただしその場合コストは perf ビルドにも
        乗って fitness が自己ペナルティを受けるため false-green にはならず、意味判定は auditor / 人間レビュー領域。
      この 3 点 + 限界の明記をタスク定義として確定するまで blocking 完了としない。
- [ ] **coder.md 生成 + 純 timing variant 1 本で全配線 1 周**: coder.md を critic/profiler 体裁で生成
      (agent-architecture.md:66-71)。**前提 gate: H3 hook (方針 A 最小化版) の settings.json 配線が完了している
      こと** — 未配線の間に coder を実走させない。配線状態は `test_settings_json_wires_both_hooks` の緑で機械確認
      する (over-claim の前歴 = D30 があるため、宣言でなくテストを gate にする)。**まず「#else 枝を逐語複写する
      no-op variant」**を書かせ stock cache-hit で配線実証 → 次に静的 backoff 値 1 つの純 timing variant を
      Tier0→pipeline.evaluate→verify→bench→WAL で 1 周。**COMMIT を書く唯一の経路は pipeline.evaluate()**
      (guided.py の replay-fake certified 経路は live variant に絶対再利用しない)。
- [ ] **broken-silo 回帰**: ループ前に broken-silo-norw patch で verifier が確実に G2 赤を返すことを 1 回確認
      (赤検出力の空打ちでない実証)。clean G2 は easy case ゆえ integrity-class fixture は S4 consumer 段で追加。

**新規実体化は coder のみ** (critic/profiler は既存再利用、auditor/planner は後続)。

**完了条件 (2 項に分離。どちらも WAL で機械確認する):**
1. **identity 後方互換:** inert no-op variant (#else 逐語複写) が stock と同一 identity に解決され (src_token=stock)、
   **stock genome が cache-hit** で certified commit する — マーカー挿入が既存 identity を動かさないことの実証。
2. **合成枝の 1 周:** 純 timing variant 1 本 (静的 backoff 値 1 つ) が **stock と別の variant_id / cache_key に解決され
   cache-miss で新規ビルド**され、Tier0→pipeline.evaluate→verify→bench→WAL を 1 周して certified commit する。かつ
   **verify run の abort > 0 を WAL の verify payload で確認する** (= abort-path 上の合成枝が verify 中に実行された
   証拠。abort ≈ 0 なら空振り認証なので S2-lite = 競合度を上げた縮小 verify を前倒す。残存リスク節)。
「純 timing variant が cache-hit する」状態は完了ではなく**一次防壁 (source_digest) の故障**として扱う (別 digest =
cache-miss が正しい動作)。1 と 2 の両方が揃って kickoff 完了 — 「or」ではない (no-op 単独は合成系固有の配線 = 別 id
生成・新規ビルド・digest 分岐を何も実証しない)。
critic 出力は kickoff では「帰属が正しいか」の検証のみ (次手は人間。P2-5/D21 の deceptive 帯誤収束を再演しない)。

---

## 残り Phase 3 着手前 must の blocking 分類

| must | kickoff | 根拠 |
|---|---|---|
| **H3 hooks** | 進行中 (方針 A) | 実装済だが 2 巡目で real 13 件・**未配線**・最小第二防壁へ再設計中 (D30)。identity/観測者効果の担保は下 2 行の一次防壁へ委譲したので、kickoff の唯一の防壁ではなくなった |
| **cache_key+variant_id 拡張** | **blocking** | inert 実証の継承 + 同フラグ別 diff alias 防止。**方針 A で identity honest の一次防壁に昇格** (偽 cache hit を hook でなく digest で塞ぐ) |
| **観測者効果二重検査** | **blocking** | nm だけでは data-structure 観測者効果を見逃す。**方針 A で TRACE 混入検知の一次防壁に昇格** (payload 検査に依存しない) |
| **S4** | 完了済 | 規律3 配線 (verify-red の構造化 anomaly を abort payload + load_rejections)。consumer 実体化は後続 |
| S2 (certify=perf) | non-blocking (abort>0 確認は完了条件 2 に反映済み) | 純 timing は lock/validation 論理に触れないが、**abort 経路は踏む** — verify で abort≈0 だと合成枝が空振り認証になる (残存リスク節)。abort>0 確認は完了条件 2 に明記済み (前提 = abort 数の WAL 記録タスク)。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) |
| S1 (別 protocol trace-hook) | non-blocking (kickoff) / **主実験 headline 2 で発火** | silo 内に閉じる限り不要。ただし発火条件は「別 protocol 移植」だけでなく**主実験 headline 2 (クロスプロトコル stock 最良) も含む** — trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) ため、headline 2 までに S1 移植か「stock 専用計測経路を規律2 と整合させる設計」のどちらかが要る (後続段 6 の前提タスク (a)) |
| C1 (campaign-id drift) | non-blocking | apply→revert で HEAD 不動。housekeeping。並行合成/patch 常駐の段で恒久対応 |

---

## 後続段 (各々 ablation 点を残して投入)

1. **S2 縮小 verify 構成の確定** (calibrator 実走を gate 条件に) — sort 等データパス分岐変異の prep。
2. **S4 load_rejections consumer 実体化** — coder が初めて赤 variant を出す段。verify-red (cycle を断つ) と
   liveness-red (trace-empty/abort 率異常/timeout) の両対応。integrity-class fixture も positive control に追加。
3. **auditor.md 生成と起動** — lock 経路変異の段。lock 獲得が write_set を被覆するか assert + in-class positive
   control suite を own。入力隔離を構造で強制 (WAL fitness を scope に入れない)。lock 経路は auditor live を gate に。
4. **guided 検疫層を diff 検疫へ拡張 + planner.md 生成** — coder 自律期。diff が EVOLVE-BLOCK マーカー間かつ
   #if 枝内に収まるか parse 検証。
5. **sort-strategy ターゲット起動 / git worktree 隔離 / C1 恒久対応** — S2 gate を満たした後 + 並行合成の段。
6. **主実験の実行 (headline 比較 4 対照 + LLM ablation)** — 冒頭「Phase 3 全体の完了定義と主実験の評価設計」を
   実走する段。**Phase 3 の headline 主張はこの段の完了をもって初めて出せる** (段 4/5 の中間結果は評価設計に
   従った暫定として報告)。gate = 変異軸 (sort or それ以降) から headline 候補が出たこと + S2 gate + auditor live。
   ここで仕込む前提タスク: (a) **S1 移植 or stock 専用計測経路の設計判断** (headline 2 の前提。must 表参照)、
   (b) SPACES への mocc/tictoc/cicada 登録 + protocol 別 calibration + between-run floor の対象別再実測、
   (c) ランダム変異生成器と生成分布の確定 (ベースライン 3)、(d) 機械 sweep 駆動と軸命名手順の固定 (ベースライン 4)、
   (e) coder リーク制御 (P2-5/D21 の Phase 3 版) の実体化、(f) 検証相 (seed×N・長 extime) の実装、
   (g) サンプル設計 4 点の数値確定 (統計計画の節)。

---

## 残存リスク

- 純 timing first target は**新規性が薄い** (機構の配線実証が主目的、性能新規性は sort 以降)。意図的トレードオフ。
- **S2 non-blocking の根拠に空振り認証リスク**: S2 (certify workload = perf workload) を non-blocking とする根拠
  「純 timing は workload 依存パスを持たない」は厳密には正しくない — static backoff は **abort 時にのみ実行される
  競合依存パス**であり、現 CorrectnessWorkload (tuple200/thread4) は同一キー競合をほぼ踏まない (本ファイル冒頭で自認)。
  競合を踏まない ⇒ abort がほぼ出ない ⇒ **coder が書いた #if 枝が verify 中に一度も実行されないまま緑 certify** に
  なりうる (空振り認証)。緩和 (**完了条件 2 に反映済み**): **「verify run の abort > 0 = 合成枝が実行された証拠」を
  WAL の verify payload で確認**する。前提 = abort 数の WAL 記録 (blocking タスク。旧配線は abort 数をどこにも
  記録しておらず、この確認自体が実行不能だった)。abort ≈ 0 なら S2-lite (CorrectnessWorkload の競合度を上げた縮小
  verify) を純 timing にも前倒す。timing 純度そのもの (straight-line・API 範囲) は payload 検査では機械保証されず、auditor live まで
  coder diff の人間レビューが gate (方針 A で hook が唯一防壁でなくなった帰結)。
- preprocess 後ハッシュは対象ファイル集合の列挙漏れがあれば偽キャッシュヒットが復活する。固定集合に限定しテストで固定するが
  template patch の改訂で集合が動いたら漏れる残留リスク。**タスク2 敵対レビューで実証 (medium, D24)**: `Options.cmake` は
  ALLOWLIST 内だが `EVOLVE_BLOCK_SOURCES` (= digest 対象) 外で、`VAL_SIZE` 等の build 左右マクロを変えると別バイナリ
  なのに src_token/cache_key/variant_id が不変 (偽 hit)。現状は発火経路が人間 template のみ (coder 未実装) ゆえ潜在。
  **方針 A で塞ぎ方が変わった (D30)**: 旧設計は「H3 hook が coder の編集面を #if 枝に絞ることで塞ぐ」だったが、2 巡目検証
  (SPEC-2) が Bash 経路の `sed -i .../Options.cmake` で hook を丸ごと迂回できることを示した。→ 恒久解は **identity 側
  (configure 最終 -D 集合、or `Options.cmake` の digest 織り込み) を hook 非依存にする**。kickoff では固定集合限定 +
  テスト固定で潜在に留め、cicada/oze 拡張で protocol 写像が load-bearing になった段へ繰延 (D23)。
- broken-silo は clean G2 の easy case。coder が現実に出す赤の多くは integrity-class (verdict indeterminate) に
  なりうる → S4 consumer 段で integrity fixture を別途用意 (clean G2 だけで規律3 閉ループを certify しない)。
- **coder のリーク制御が未設計 (P2-5/D21 の Phase 3 版が未予約)**: kickoff の題材 BACKOFF_FIXED は、勝ち筋
  (contention 域で stock 最良 +38%/+11%、sweet-spot 値) が docs/insights/WAL/CLAUDE.md にリポジトリ内既知として
  書かれている。coder のコンテキストにこれが混入すると「合成できた」のか「答えを読んだ」のか分離できない。P2-5 は
  誘導アームで **fresh context + 最適解 literal の物理削除 (`critic-experiment`) + 評価済みのみ digest** のリーク制御を
  確立した (D14/D21)。Phase 3 で coder が実際に #if 枝を自律生成する段 (後続段 4) では、この Phase 3 版リーク制御
  (勝ち筋値・機序説明を coder の入力から遮断) を予約する。kickoff (no-op / 人間が値を与える純 timing) では coder が
  値を発明しないので潜在。
- **観測者効果の二重検査の述語 (方針 A で一次防壁に昇格した分、重い)**: 旧仕様「TRACE マクロ以外で差が無いことを
  両ビルドの preprocess 出力で diff」には 2 つの問題があった — (1) trace/perf の preprocess 出力は `#if TRACE` 領域で
  **正当に**食い違うため素の diff は述語として成立しない、(2) coder が `#ifdef TRACE` の**内側**に挙動差を隠す攻撃
  (2 巡目 GW2R-1 の payload が実演した形) を素通しする。**blocking タスクの新仕様 (diff-of-diffs、タスク定義参照) は
  両方を同時に解消する**: variant の TRACE=1/TRACE=0 差分が pinned HEAD の同差分と一致することを assert するので、
  正当な trace-hook 差分は許容され、#ifdef TRACE 内側への追加/改変は D_variant≠D_stock で fails-closed になる。
  残る限界 (タスク定義に明記): 検証専用メタデータが #ifdef の外 = 両ビルド共通に常駐するケースは機械判定不能
  (fitness の自己ペナルティで false-green にはならないが、意味判定は auditor / 人間レビュー領域)。仕様確定時に
  この述語で確定するまで blocking 完了としない。
