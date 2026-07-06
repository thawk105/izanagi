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

## Phase 3 全体の完了定義と主実験の評価設計 — `docs/phase3-main-experiment.md` へ分離 (2026-07-05, D35)

主実験 (後続段 6) の事前登録 = 反証可能な主張・headline 比較 4 対照 (silo stock 最良 / クロスプロトコル
stock 最良 / ランダム変異 / 機械 sweep) とその操作的定義・LLM ablation・統計計画 (floor 流用禁止・
サンプル設計・Holm 補正・天井の不在・deceptive 相当の検証・検証相の配線)・失敗条件 (a)〜(e) は
`docs/phase3-main-experiment.md` に事前登録してある。**coder が性能主張を生む段 (後続段 4 以降) の主張は
すべて同設計に従う。** kickoff は同設計を満たさなくてよい (別スコープ) — 読むのは後続段 4 に入るとき。

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

- [x] **(blocking) cache_key + variant_id の honest 拡張** — source_digest (preprocess 後 `cpp -E` 出力の
      sha256) を cache_key と variant_id (WAL キー) 両方の pre-image に織り込み、同フラグ別 diff の alias を封鎖
      (identity honest の一次防壁、方針 A)。inert template は #else 枝が原本と同一 → stock と同一 digest (D18 継承)。
      詳細 = 当該コミット本文・D23/D24・worklog 2026-07-03。
- [x] **(blocking) EVOLVE-BLOCK template patch** — silo abort-path (BACKOFF_FIXED 軸再利用) に骨格 1 つ。
      既定 inert を preprocess 後ハッシュ一致 → stock genome cache-hit で実証。
- [x] **(blocking) verify の abort 数を WAL に記録** — ccbench stdout の `abort_counts_:` をパースし
      STAGE_VERIFY_DONE payload に `aborts` として記録。集計行が読めない run は fails-closed reject
      (`trace-no-abort-counts`) — 完了条件 2 の「abort > 0」の検査可能性を機械で担保 (規律3)。詳細 = 当該コミット本文。
- [x] **(blocking) apply/revert ハーネス** — `campaign/patchharness.py` の `applied()` context manager。
      flock 直列化 (並走 apply の ABA 対策)・pinned-clean assert・順序固定 apply→resolve→build→revert・
      fails-closed。revert 後 assert は「porcelain 空」より弱く恒久解は段 5 の worktree 隔離 (残存リスク節)。
      詳細 = 当該コミット本文・worklog 2026-07-04。
- [x] **(blocking) build 後の digest 再照合 (TOCTOU 遮断)** — `buildcache._recheck_src_token`。resolve→build 間の
      tree 変動による偽 cache hit (共有ビルドキャッシュへの永続 = 規律2 直撃) を封鎖。不一致は build dir ごと破棄、
      cache hit 側も再照合、transient 失敗でも新規ビルドは破棄 (D25 と意図的非対称 — 残存リスク節)。詳細 = 当該コミット本文。
- [x] **(blocking) source_digest の #include 死角の閉塞 (最小案)** — `assert_includes_match_head`:
      EVOLVE_BLOCK_SOURCES の #include 行集合 (順序込み) を HEAD 固定し、1 行でも違えば fails-closed abort。
      恒久案 (行集合の pre-image 織り込み) は敵対検証で却下 — include 先ファイルの中身が identity に乗らず
      variant 間 alias が残るため。computed include (`__has_include`/#define 経由) は残存リスク節。詳細 = 当該コミット本文。
- [x] **(完了・方針 A) H3 hooks = 明白な直接書き込みを止める最小第二防壁 (配線済)** — guard_write / guard_bash を
      最小化し `.claude/settings.json` に配線。payload テキスト検査は物理削除 (D33)、identity/観測者効果は
      一次防壁へ委譲、critical (builtin definedness 偽 cache hit) は D34 で封鎖。3 巡目敵対検証
      (real 9/known-limitation 6/refuted 0) の fix は変異検査で固定。詳細 = D30/D33/D34・hooks/README.md・worklog 2026-07-04。
- [x] **(完了) 観測者効果の二重検査 = diff-of-diffs (commit 14d64e6)** — variant の preprocess(TRACE=1)−(TRACE=0)
      差分が pinned HEAD の同差分と一致することを `source_digest.assert_trace_diff_matches_head` で assert
      (buildcache.build 出口、hit/fresh 両経路、fails-closed)。素の出力 diff は #if TRACE 領域で正当に食い違うため
      述語として不成立 (敵対検証で棄却済)。#ifdef 外の共通常駐メタデータは機械判定不能 = auditor/人間レビュー領域
      (残存リスク節)。詳細 = コミット 14d64e6 本文・worklog 2026-07-05 追補。
- [x] **coder.md 生成 + 純 timing variant 1 本で全配線 1 周** (2026-07-05 完了。完了条件 1/2 とも
      WAL 機械判定 10/10 PASS — no-op が src_token=stock で seed ビルドに cache-hit certified commit /
      static50 が別 id・cache-miss 新規ビルドで verify aborts 41,868 > 0 → bench → certified commit。
      abort>0 が大きく成立したため S2-lite 前倒しは不要。駆動 = patches/variant-*.patch +
      `campaign/p3_kickoff.py`。詳細 = 当該コミット本文・worklog 2026-07-05): coder.md を critic/profiler 体裁で生成
      (agent-architecture.md の coder 仕様予約節 — kickoff の確定制約は同節の ⚠ 注記どおり本文書 + D22/D23/D24/D30 が正典)。**前提 gate: H3 hook (方針 A 最小化版) の settings.json 配線が完了している
      こと** — 未配線の間に coder を実走させない。配線状態は `test_settings_json_wires_both_hooks` の緑で機械確認
      する (over-claim の前歴 = D30 があるため、宣言でなくテストを gate にする)。**まず「#else 枝を逐語複写する
      no-op variant」**を書かせ stock cache-hit で配線実証 → 次に静的 backoff 値 1 つの純 timing variant を
      Tier0→pipeline.evaluate→verify→bench→WAL で 1 周。**COMMIT を書く唯一の経路は pipeline.evaluate()**
      (guided.py の replay-fake certified 経路は live variant に絶対再利用しない)。
- [x] **broken-silo 回帰**: ループ前に broken-silo-norw patch で verifier が確実に G2 赤を返すことを 1 回確認
      (赤検出力の空打ちでない実証)。clean G2 は easy case ゆえ integrity-class fixture は S4 consumer 段で追加。
      (2026-07-05 実証: 高競合 tuple50/skew0.9/rmw/thread4 で verdict=non-serializable・anomalies 20 件
      全て G2・exit 1。一時ビルド/trace は清掃済み。詳細 = worklog 2026-07-05)

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
| S2 (certify=perf) | non-blocking (abort>0 確認は完了条件 2 に反映済み) | 純 timing は lock/validation 論理に触れないが、**abort 経路は踏む** — verify で abort≈0 だと合成枝が空振り認証になる (残存リスク節)。abort>0 確認は完了条件 2 に明記済み (前提 = abort 数の WAL 記録タスク)。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) **→ 構成確定済 (2026-07-06、後続段 1 完了・gate 3 点 all_pass、D36)。残り = 段 5 での pipeline 配線 (D36 決定 4)** |
| S1 (別 protocol trace-hook) | non-blocking (kickoff) / **主実験 headline 2 で発火** | silo 内に閉じる限り不要。ただし発火条件は「別 protocol 移植」だけでなく**主実験 headline 2 (クロスプロトコル stock 最良) も含む** — trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) ため、headline 2 までに S1 移植か「stock 専用計測経路を規律2 と整合させる設計」のどちらかが要る (後続段 6 の前提タスク (a)) |
| C1 (campaign-id drift) | non-blocking | apply→revert で HEAD 不動。読み手 3 本の discover 統一 (065593a, 2026-07-02) で歴史的 campaign の孤立は解消済み。残課題 = driver 宣言値 (phase2.md §C1) と並行合成/patch 常駐で HEAD が動く場合の id 安定化 → 段 5 |

---

## 後続段 (各々 ablation 点を残して投入)

1. **(完了 2026-07-06) S2 verify 構成の確定** — perf 代表 workload と**完全同一** (1m/t48/skew0.9/rr50/
   rmw0/max_ope10/extime3。「縮小」なしで gate 実測 all_pass)。gate 3 点 = 同 genome 対照比の contention
   再現 (abort 率比 1.29 ∈ [0.5,2]・aborts 556k)・trace 規模 (539MB/16.9M 行、verifier 141s/RSS 7.7GB)・
   赤検出力 (norw G2 total 4,053 + 新設 highkey が S2 赤/legacy 緑 = ablation の機械実証)。正本 = D36・
   `output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json`・駆動 =
   `orchestrator/campaign/s2_verify_calibration.py`。**pipeline 配線 (verify 2 本立て) は段 5 で D36
   決定 4 の規定 (identity 組み込み・COMMIT タグ焼き込み・AND 共通ヘルパ・排他・TRACE_DIR 対称化) に従う。**
2. **S4 load_rejections consumer 実体化** — coder が初めて赤 variant を出す段。verify-red (cycle を断つ) と
   liveness-red (trace-empty/abort 率異常/timeout) の両対応。integrity-class fixture も positive control に追加。
3. **auditor.md 生成と起動** — lock 経路変異の段。lock 獲得が write_set を被覆するか assert + in-class positive
   control suite を own。入力隔離を構造で強制 (WAL fitness を scope に入れない)。lock 経路は auditor live を gate に。
4. **guided 検疫層を diff 検疫へ拡張 + planner.md 生成** — coder 自律期。diff が EVOLVE-BLOCK マーカー間かつ
   #if 枝内に収まるか parse 検証。
5. **sort-strategy ターゲット起動 / git worktree 隔離 / C1 残課題 (driver 宣言値・並行時の id 安定化)** — S2 gate を満たした後 + 並行合成の段。**S2 verify 2 本立ての pipeline 配線をこの段の先頭で行う (D36 決定 4 の 6 規定: campaign identity 組み込み・COMMIT タグ焼き込み・AND 共通ヘルパ・red payload の workload タグ・bench 同一排他 + numactl・IZANAGI_TRACE_DIR 対称化)。**
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

## 見送り台帳 (旧「次の一手」の任意項 — 意図的な見送りとして明示)

worklog の過去エントリの「次の一手」に載ったまま現行正本 (worklog 末尾・本文書) に引き継がれなかった任意項。
worklog 全読しないと発掘できない状態を解消するためここに台帳化する (2026-07-05)。**着手義務はない** —
拾うときは該当タスクに昇格させ、捨てるときは理由をここに書く:

- **balanced での backoff profile 対照** (worklog 2026-06-28) — write-heavy の [P0] は閉じたが balanced の対照 profile は未取得。
- **over-throttle 有用 IPC 低下の機序分離** (同上) — MLP 低下 vs cache 余熱のどちらかは未分離。
- **mocc trace-hook** (worklog 2026-06-19) — visible reads の trace 検証 + verifier 2nd エンジン化。S1 発火時に吸収するのが自然。
- **ermia cross-check** (worklog 2026-06-18) — si 赤 / ermia 緑 の同一エンジン ablation。同上 (版 ID 写像の罠は ccbench-anatomy.md §8 に昇格済み)。
- **calibration の K 感度・thread 数変更時の再 calibration** (worklog 2026-06-18) — 後続段 6 前提タスク (b) の protocol 別 calibration が部分吸収する。

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
  **(追記 2026-07-06) S2 構成自体は後続段 1 で確定 (D36・gate 3 点 all_pass)。残りは段 5 の配線のみ。**
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
