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
  ファイルを作成/改変しない (**H3 hook (方針 A) の settings.json 配線済 (2026-07-04, D30/D33) により designated
  ソース面の限定は機械強制**。ただし方針 A の hook は編集面の限定のみを担い、designated ソース内の内容・意味的
  逸脱の判定は auditor / coder diff の人間レビュー領域のまま — coder.md タスクの前提 gate =
  `test_settings_json_wires_both_hooks` の緑で機械確認)。
- **適用の隔離:** patch は submodule working-tree への out-of-band 適用 (HEAD は dff0f1e pin 不動 →
  campaign-id 不変)。1 variant 評価ごとに clean→apply→build→revert。apply 前に対象が pinned-clean か
  assert (汚れていたら fails-closed abort)。駆動部 = `campaign/patchharness.py` の `applied()` context
  manager (blocking タスクで実装済み: enter = flock 排他 + pinned-clean assert + apply、exit = revert +
  clean assert。順序固定 apply→resolve→build→revert は context manager の形状で担保)。

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
- [x] **(blocking) verify の abort 数を WAL に記録**: 旧配線は abort 数をどこにも記録しなかった — `_run_trace` は
      `(ncommit, rc)` のみ返し ccbench stdout を捨て、STAGE_VERIFY_DONE payload は
      verdict/certified/commits/anomalies の 4 項のみ、trace レコードも C/R/W の 3 種で
      abort イベントを持たない = 完了条件 2 の「abort > 0 確認」が**検査不能**だった。実装: ccbench stdout の
      `abort_counts_:` (common/result.cc:34) をパース (`pipeline._parse_abort_counts`、`^` アンカーで
      `batch_abort_counts_` を誤マッチしない) し STAGE_VERIFY_DONE payload に `aborts` として記録。**集計行が
      読めない run は fails-closed reject** (`trace-no-abort-counts`) — 空振り認証の検査可能性を落としたまま
      緑を出さない (規律3: 計器の故障を沈黙させない)。
- [x] **(blocking) apply/revert ハーネス**: 「1 variant 評価ごとに clean→apply→build→revert」(上の機構節) の
      駆動部 = `campaign/patchharness.py`。apply 前の pinned-clean assert (HEAD==pin (7 桁下限、startswith 弱照合
      対策) + tracked 改変ゼロ) + revert 後の tracked-clean + patch 由来新規ファイル残骸ゼロ assert を fails-closed
      で持ち、順序 **apply → resolve(src_token) → build → revert** は `applied()` context manager の形状で担保
      (resolve より後に tree を動かさない)。全 git 呼び出しに `-c core.quotepath=false` (非 ASCII パスの C-style
      quote で残骸削除/leftovers 検査が素通りする穴の対策)。**区間全体を flock (`_tree_lock`) で直列化** — 共有
      working-tree への並走 apply の ABA は TOCTOU 再照合 (両端一致) では原理的に見えない (2026-07-03 敵対検証
      high)。revert 後 assert はタスク定義の「porcelain 空」より弱い (残存リスク節) — 恒久解は段 5 の git
      worktree 隔離。
- [x] **(blocking) build 後の digest 再照合 (TOCTOU 遮断)**: resolve→build 間に working-tree が動くと、digest と
      実バイナリが食い違ったまま**共有ビルドキャッシュ (campaign 非依存) に永続**し以後 cache hit で沈黙再利用される
      (偽 cache hit = 規律2 直撃)。bench_lock はベンチのみ排他・campaign.lock は記録ファイルで mutex ではなく、
      複数セッション並走は現に運用実態。実装: `buildcache._recheck_src_token` — build 完了直後に
      source_digest.resolve で src_token を再計算・照合し、不一致は build dir ごと破棄 (`_discard_build_dir`、
      破棄失敗は明示例外 = 消し残り汚染バイナリの沈黙再利用を防ぐ) して fails-closed abort (再計算は数十 ms で
      規律4 に反しない)。**cache hit 側も再照合** (resolve→hit 判定間の窓。hit の不一致は既存の正当な成果物
      なので破棄せず停止のみ)。resolve の transient 失敗でも新規ビルドは破棄する (D25 と非対称だが意図的 —
      残存リスク節)。git worktree 隔離 = 後続段 5 までの最小防壁。
- [x] **(blocking) source_digest の #include 死角の閉塞 — 最小案採用**: digest は preprocess 前に `#include` 行を
      無条件除去する (source_digest.py `_INCLUDE_RE`) ため、coder が EVOLVE-BLOCK ファイルに #include を追加/
      差し替えすると**バイナリが変わるのに identity 不変** = stock と alias → 既存バイナリの cache hit で**変更が
      一度もコンパイルされないまま certified 記録**になる。旧状この経路の防壁は道Y の hook 禁止 (D23) だけで hook は
      未配線 — 方針 A が消したはずの単一障害点がこのベクタで復活していた。実装 = **最小案**:
      `assert_includes_match_head` (resolve が駆動) — EVOLVE_BLOCK_SOURCES の #include 行集合 (順序込み) が HEAD
      baseline と 1 行でも違えば fails-closed abort。**恒久案 (行集合を src_token pre-image に織り込んで追加を許す)
      は敵対検証で却下** (2026-07-03 high): include **先ファイルの中身**は identity に乗らず、中身違いの新規 header
      で variant 間 alias が残る (実機 probe で偽 cache hit 再現)。行集合を HEAD 固定にすれば include 追加自体を
      止めるので穴ごと消える (coder の #include 追加は閉じた領域制約で元々禁止)。`__has_include` / #define 経由の
      computed include は #include 行に現れず残る → 残存リスク節 (道Y 一般問題)。
- [x] **(完了・方針 A) H3 hooks = 明白な直接書き込みを止める最小の第二防壁** (配線済, D30/D33/D34):
      `guard_write.py` / `guard_bash.py` を方針 A で最小化し `.claude/settings.json` に配線
      (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash`)。guard_write は payload テキスト検査を物理削除
      (D33) — proof-chain 拒否と designated ソース面の限定だけを担い、identity/観測者効果は一次防壁へ委譲する
      (旧「payload 検査が `#ifdef` の唯一の防壁」= 単一障害点は放棄。GW2R-1/SPEC-2 が反証)。
      配線前に **3 巡目敵対検証 (2026-07-04, Opus 赤チーム 4 系統 19 エージェント・約 93 万トークン)** を回し
      real 9 / known-limitation 6 / refuted 0 を摘出:
      - **critical = source_digest の builtin definedness (`#ifdef __x86_64__`) 偽 cache hit** = 方針 A の委譲先自身の
        穴 (道Y が前提にした「生 #ifdef を hook で禁止」が payload 検査削除で消えた帰結)。**D34 (-undef 廃止) で
        封鎖** = 下記順序 (1) 一次防壁健全化の完遂。
      - hook の bypass 5 (絶対パス/~ の rm/改行がセグメント境界にならず先頭 read-only head が後続 writer 隠蔽/
        heredoc `<<`/symlink root-output fail-open/NotebookEdit decoy) + 過剰拒否 3 (nm/du の純読み・tar/rsync backup)
        を修正。known-limitation 6 (変数展開・部分 glob・computed include・末端 tar backup 等 docstring 明示の限界) 据え置き。
      全 fix は変異検査 (fix を戻すと該当テスト赤・復元で緑) で機械実証。**D30 の順序 = (1) 一次防壁を load-bearing に
      (preprocess ハッシュ・#include HEAD 固定・diff-of-diffs・TOCTOU 再照合・**D34 builtin definedness**) →
      (2) hook 最小化 + 過剰拒否除去 → (3) settings.json 配線、を完了。** 詳細は worklog 2026-07-04。
- [x] **(完了) 観測者効果の二重検査 — 述語 = diff-of-diffs で確定・実装済み (commit 14d64e6, 2026-07-04)**: nm の
      name-based 検査 (buildcache._assert_no_trace_symbols) を補完する一次防壁 (D30)。旧仕様の「両ビルドの
      preprocess 出力を diff」という素朴な述語は**成立しない** — trace ビルド (TRACE=1) と perf ビルド (TRACE=0) の
      preprocess 出力は `#if TRACE` ガード領域で**正当に**食い違うため、素の diff は必ず大量差分を出す (敵対検証で棄却)。
      確定・実装した述語:
      - **diff-of-diffs**: 同一 working-tree の preprocess(TRACE=1) − preprocess(TRACE=0) の差分
        `D_variant` を取り、pinned HEAD (izanagi-trace baseline) から同様に取った `D_stock` と**一致**することを
        assert する。「variant が TRACE 条件付きコードを追加/改変していない = trace/perf の差は stock の trace-hook
        由来のみ」を機械保証し、残存リスク節の「#ifdef TRACE の内側に挙動差を隠す攻撃」も D_variant≠D_stock で捕える。
      - **発火単位** = 毎 variant の trace/perf ビルド直後 (buildcache.build の出口。hit/fresh 両経路)。
      - **fails-closed** = diff 不一致・preprocess 取得不能のいずれも abort (警告に格下げしない)。不一致の新規ビルドは
        build dir ごと破棄。
      - **保証しないこと (正直に)**: 検証専用メタデータが #ifdef の**外** (両ビルド共通) に常駐するケースは
        この述語では判定不能 (機械には CC 本来か検証専用か区別できない)。ただしその場合コストは perf ビルドにも
        乗って fitness が自己ペナルティを受けるため false-green にはならず、意味判定は auditor / 人間レビュー領域。
      実装 = `source_digest.assert_trace_diff_matches_head` (述語 3 面 + 上記限界を docstring に明記) を
      `buildcache.build` 出口で駆動。述語 + 結線を変異検査 3/3 で実証、実 submodule stock 通過 27ms (規律4 に反しない)。
      実施記録は worklog 2026-07-04 の両エントリから漏れていた — worklog 2026-07-05 の追補を参照。
- [ ] **coder.md 生成 + 純 timing variant 1 本で全配線 1 周**: coder.md を critic/profiler 体裁で生成
      (agent-architecture.md の coder 仕様予約節 — kickoff の確定制約は同節の ⚠ 注記どおり本文書 + D22/D23/D24/D30 が正典)。**前提 gate: H3 hook (方針 A 最小化版) の settings.json 配線が完了している
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
| **H3 hooks** | **完了 (方針 A)** | 最小第二防壁を配線 (D30/D33)。3 巡目検証で real 9/known 6 摘出・全修正 (変異検査済)、critical (source_digest builtin definedness 偽 cache hit) は D34 で封鎖。identity/観測者効果の担保は下 2 行の一次防壁が担う |
| **cache_key+variant_id 拡張** | **完了** (kickoff タスク 1 で消化) | inert 実証の継承 + 同フラグ別 diff alias 防止。**方針 A で identity honest の一次防壁に昇格** (偽 cache hit を hook でなく digest で塞ぐ) |
| **観測者効果二重検査** | **完了 (14d64e6)** | nm だけでは data-structure 観測者効果を見逃す。**方針 A で TRACE 混入検知の一次防壁に昇格** (payload 検査に依存しない)。diff-of-diffs を buildcache.build 出口 (hit/fresh 両経路) で発火、fails-closed |
| **S4** | 完了済 | 規律3 配線 (verify-red の構造化 anomaly を abort payload + load_rejections)。consumer 実体化は後続 |
| S2 (certify=perf) | non-blocking (abort>0 確認は完了条件 2 に反映済み) | 純 timing は lock/validation 論理に触れないが、**abort 経路は踏む** — verify で abort≈0 だと合成枝が空振り認証になる (残存リスク節)。abort>0 確認は完了条件 2 に明記済み (前提 = abort 数の WAL 記録タスク)。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) |
| S1 (別 protocol trace-hook) | non-blocking (kickoff) / **主実験 headline 2 で発火** | silo 内に閉じる限り不要。ただし発火条件は「別 protocol 移植」だけでなく**主実験 headline 2 (クロスプロトコル stock 最良) も含む** — trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) ため、headline 2 までに S1 移植か「stock 専用計測経路を規律2 と整合させる設計」のどちらかが要る (後続段 6 の前提タスク (a)) |
| C1 (campaign-id drift) | non-blocking | apply→revert で HEAD 不動。読み手 3 本の discover 統一 (065593a, 2026-07-02) で歴史的 campaign の孤立は解消済み。残課題 = driver 宣言値 (phase2.md §C1) と並行合成/patch 常駐で HEAD が動く場合の id 安定化 → 段 5 |

---

## 後続段 (各々 ablation 点を残して投入)

1. **S2 縮小 verify 構成の確定** (calibrator 実走を gate 条件に) — sort 等データパス分岐変異の prep。
2. **S4 load_rejections consumer 実体化** — coder が初めて赤 variant を出す段。verify-red (cycle を断つ) と
   liveness-red (trace-empty/abort 率異常/timeout) の両対応。integrity-class fixture も positive control に追加。
3. **auditor.md 生成と起動** — lock 経路変異の段。lock 獲得が write_set を被覆するか assert + in-class positive
   control suite を own。入力隔離を構造で強制 (WAL fitness を scope に入れない)。lock 経路は auditor live を gate に。
4. **guided 検疫層を diff 検疫へ拡張 + planner.md 生成** — coder 自律期。diff が EVOLVE-BLOCK マーカー間かつ
   #if 枝内に収まるか parse 検証。
5. **sort-strategy ターゲット起動 / git worktree 隔離 / C1 残課題 (driver 宣言値・並行時の id 安定化)** — S2 gate を満たした後 + 並行合成の段。
6. **主実験の実行 (headline 比較 4 対照 + LLM ablation)** — 冒頭「Phase 3 全体の完了定義と主実験の評価設計」を
   実走する段。**Phase 3 の headline 主張はこの段の完了をもって初めて出せる** (段 4/5 の中間結果は評価設計に
   従った暫定として報告)。gate = 変異軸 (sort or それ以降) から headline 候補が出たこと + S2 gate + auditor live。
   ここで仕込む前提タスク: (a) **S1 移植 or stock 専用計測経路の設計判断** (headline 2 の前提。must 表参照)、
   (b) SPACES への mocc/tictoc/cicada 登録 + protocol 別 calibration + between-run floor の対象別再実測、
   (c) ランダム変異生成器と生成分布の確定 (ベースライン 3)、(d) 機械 sweep 駆動と軸命名手順の固定 (ベースライン 4)、
   (e) coder リーク制御 (P2-5/D21 の Phase 3 版) の実体化、(f) 検証相 (seed×N・長 extime) の実装、
   (g) サンプル設計 4 点の数値確定 (統計計画の節)。
7. **(拡張予約) 最適化移植 + カタログ化** — roadmap §2 層2(b) の当初の本丸「他 CC の最適化を CCBench コーパスから
   移植する」+ 隠れた肝「最適化カタログ化 (前提/効果/競合の三つ組、I5 対策)」は、**主実験 (段 6) 完了後の拡張**として
   ここに予約する (a' 方針、D32)。根拠 = 非対称性: 空間外合成は P2-4 で実証済み・**移植の価値は未検証仮説** (I5 =
   「異なる実装の混合は不適切」という CCBench 著者の警告 + 他 CC のメタデータ前提を持ち込む正しさ攻撃面) なので、
   実証済みの道で主実験まで到達してから投資判断する (規律5 / P2-5 の教訓 = 仮説に工数を先払いしない)。着手時の
   一歩目は**カタログ化の試作 1 枚** (他 CC の最適化 1 つを「前提/効果/競合」でカード化し、移植先で前提が満たせるかを
   判定) で、本格投資はその結果で決める。cicada/oze への空間拡大 (S1 移植を伴う) と束ねるのが自然。カタログ化の
   成果物は移植を見送っても層3 の説明生成に流用できるため無駄にならない。

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
  確立した (D12/D21)。Phase 3 で coder が実際に #if 枝を自律生成する段 (後続段 4) では、この Phase 3 版リーク制御
  (勝ち筋値・機序説明を coder の入力から遮断) を予約する。kickoff (no-op / 人間が値を与える純 timing) では coder が
  値を発明しないので潜在。
- **観測者効果の二重検査の述語 (方針 A で一次防壁に昇格した分、重い)**: 旧仕様「TRACE マクロ以外で差が無いことを
  両ビルドの preprocess 出力で diff」には 2 つの問題があった — (1) trace/perf の preprocess 出力は `#if TRACE` 領域で
  **正当に**食い違うため素の diff は述語として成立しない、(2) coder が `#ifdef TRACE` の**内側**に挙動差を隠す攻撃
  (2 巡目 GW2R-1 の payload が実演した形) を素通しする。**確定仕様 (diff-of-diffs、kickoff タスク参照) は
  両方を同時に解消し、実装済み (commit 14d64e6)**: variant の TRACE=1/TRACE=0 差分が pinned HEAD の同差分と一致する
  ことを assert するので、正当な trace-hook 差分は許容され、#ifdef TRACE 内側への追加/改変は D_variant≠D_stock で
  fails-closed になる。
  残る限界 (タスク定義に明記): 検証専用メタデータが #ifdef の外 = 両ビルド共通に常駐するケースは機械判定不能
  (fitness の自己ペナルティで false-green にはならないが、意味判定は auditor / 人間レビュー領域)。
- **#include 死角の残り (道Y 一般問題)**: identity 核の閉塞 (`assert_includes_match_head`) が捕えるのは literal な
  `#include` 行のみ。`#if __has_include(...)` (preprocess 環境と実ビルドで評価が分岐しうる) や #define 経由の
  computed include は #include 行に現れず素通りする。identity 核だけでは完了条件 1 (骨格の #if 指令は inert) と
  両立して塞げない (骨格 #if と payload #if の区別には skeleton 抽出が要るが、skeleton 抽出は D34 で完了条件 1 と
  両立しないため却下済み)。guard_write の payload テキスト検査も D33 で物理削除済み (designated ソース内の内容は
  検査しない) — したがって受け皿は **auditor + 規律6 監査領域の known-limitation として据え置く** (機械防壁の予約
  なし)。kickoff (no-op / 人間が値を与える純 timing) では coder が #if/#include/#define を発明しないので潜在 —
  後続段 4 (coder 自律期) で auditor のレビュー観点に明示的に含める。
- **共有 working-tree の並走 (ABA) は flock 緩和のみ**: patchharness の `_tree_lock` は単一 tree 上の並走
  apply/build/revert を直列化する最小防壁。恒久解は段 5 の git worktree 隔離 (variant ごとに独立 tree)。revert 後の
  残骸検査も tracked 改変 + patch touch 集合のみでタスク定義の「porcelain 空」より弱い (body 中の事故で作られた
  patch 外 untracked 残骸は捕えない) — worktree 隔離で tree ごと使い捨てにして解消する。
- **_recheck の transient 失敗破棄は D25 と非対称 (意図的)**: build 後再照合 (`_recheck_src_token`) で resolve が
  transient に失敗した場合も新規ビルド成果を破棄する。D25 (identity-error abort は retryable) と層が違う — WAL
  terminal の可否ではなく共有キャッシュの清潔性の問題で、identity 不明のバイナリを残す方が害が大きい (偽 hit 防止 >
  再ビルドコスト)。cache_key で次 run が再ビルドするので D25 の再評価可能性は保たれる。
