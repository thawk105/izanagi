# Phase 3 — kickoff タスクと後続段 1〜5 の完了記録 (凍結アーカイブ)

**凍結 (2026-07-10): 追記しない (訂正注記のみ可)。** `docs/phase3.md` (現行 phase doc) から
完了済み記録を分離したアーカイブ。分離時点で本書の全項目が完了しており、完了/未了の
チェックリスト正本・must 表・残存リスク・見送り台帳・段 6 以降の現役タスクは引き続き
`docs/phase3.md` にある。分離の様式は「主実験の評価設計 → `phase3-main-experiment.md`」分離
(2026-07-05, D35) と同型。経緯 = worklog 2026-07-10。

本文は分離時点の逐語写し。原文中の「残存リスク節」「must 表」「完了条件」等の節参照は
分離元 `docs/phase3.md` の節を指す (kickoff の「完了条件 (2 項)」は本書内にある)。

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
- [x] **(blocking) apply/revert ハーネス** — `orchestrator/campaign/patchharness.py` の `applied()` context manager。
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
      `orchestrator/campaign/p3_kickoff.py`。詳細 = 当該コミット本文・worklog 2026-07-05): coder.md を critic/profiler 体裁で生成
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

## 後続段 1〜5 の完了記録 (「後続段 (各々 ablation 点を残して投入)」より分離)

1. **(完了 2026-07-06) S2 verify 構成の確定** — perf 代表 workload と**完全同一** (1m/t48/skew0.9/rr50/
   rmw0/max_ope10/extime3。「縮小」なしで gate 実測 all_pass)。gate 3 点 = 同 genome 対照比の contention
   再現 (abort 率比 1.29 ∈ [0.5,2]・aborts 556k)・trace 規模 (539MB/16.9M 行、verifier 141s/RSS 7.7GB)・
   赤検出力 (norw G2 total 4,053 + 新設 highkey が S2 赤/legacy 緑 = ablation の機械実証)。正本 = D36・
   `output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json`・駆動 =
   `orchestrator/campaign/s2_verify_calibration.py`。**pipeline 配線 (verify 2 本立て) は段 5 で D36
   決定 4 の規定 (identity 組み込み・COMMIT タグ焼き込み・AND 共通ヘルパ・排他・TRACE_DIR 対称化) に従う。**
2. **(完了 2026-07-06) S4 load_rejections consumer 実体化** — coder が初めて赤 variant を出した段。
   実体 (D37): LivenessRejection 別型 (liveness 5 reason + infra 系は正規化件数に集約 — 沈黙させない) /
   render_rejections (verdict 軸 3 形状描画: cycle 型 = edges+total_cycles 併記、integrity 型 = 7 カウンタ+
   notes+空 DSG 明示、liveness 型 = 枯渇・不全・計器破れの帰属枠。性能語彙の否定 assert 付き) / verify
   abort 率シグナル (reject でなく表示 — 機械閾値なし・stock 対照併記。「abort 率異常」の段 2 解釈は D37) /
   critic.md 消費規定 / integrity-class positive control 2 形状 + dup_txids + 既知偽陰性 characterization。
   実走 = 赤 2 本 (`orchestrator/campaign/p3_s4_red.py`、WAL 機械判定 7/7 PASS、campaign
   p3-s4-red-s4-red-consumer-9a1897c4): coder 発 trace-timeout (完全 E2E、1e9µs は orchestrator 供与) +
   fixture trace 注入の verify-red (半実 — broken 変異は buildcache allowlist に正しく拒否されるため。
   **正規経路の verify-red 初発火は編集面が validation に開く段 3 以降**)。fresh critic が 3 形状を
   取り違えなく帰属。**実証の線引き: 「赤 → 構造化 → critic が読んで方向を返す」まで — 「還流」(次
   variant 生成に使用) は段 4、「改善」は段 4〜6** (paper-story の解消条件は入口のみ部分解消)。
   ablation 点 = render_rejections の合流 1 点 (還流 on/off。reason-only 第 3 アームは段 6 で判断)。
3. **(完了 2026-07-06) auditor.md 生成と起動 + write_set 被覆 assert + in-class positive control** — 実体 (D38):
   auditor.md を **read-only** で生成 (Write 非付与 = guard_write が caller 非識別ゆえ「既存テストを弱める書き込み」
   を機械で止められない → 提案テストを構造化出力で返し orchestrator が人間レビュー gate 下で反映。直接 Write は
   段 4)。write_set 被覆 assert を izanagi-trace (028f34d) の #if TRACE に追加 (namespace izanagi_trace で nm ガード
   被覆・2 点検査 = 入口 (獲得) + 各 storeRelease 直前 (保持)・shadow whole-set clear)。X 行 → verifier の
   Integrity.lock_coverage_violations → **indeterminate** (cycle でない。parse/core/model/report + render 汎用描画 +
   critic 機構欠落型 読み分け)。in-class positive control = 新 class「書き lock 欠落」の broken patch 2 本
   (lockskip/early-unlock、実ビルド実走)。**auditor live 定義 = 機械 4 点 (auditor.md 実体化 / assert 発火 /
   positive control suite 赤緑 / 入力隔離構造) + n=1 定性 2 点 (独立検出 / negative control 弁別)。段 6 headline
   gate の充足条件は機械 4 点。** 実走 = `orchestrator/campaign/s3_lock_coverage.py` (all_pass、正本 =
   `output/env/linux-baremetal/calibration/s3_lock_coverage.json`)、n=1 = `output/insights/2026-07-06_s3-auditor-live-n1.md`。**編集面拡張 (transaction.cc を EVOLVE_BLOCK_SOURCES に) は段 5 に繰延** — 「lock 経路は auditor
   live を gate に」を sequencing でなく機械で効かせるため `test_lock_path_edit_surface_requires_auditor_live`
   (段 3 は vacuously true、段 5 で発火) を配線。**ablation 点 = 被覆 assert の on/off が lockskip 検出力に与える差**
   (assert 有=X 検出 / 無=verifier 単独で cycles==0 = 見逃す)。pin 前進 (dff0f1e→028f34d) の扱いは D38・orchestrator/campaign/pin.py。
4. **guided 検疫層を diff 検疫へ拡張 + planner.md 生成** — coder 自律期。diff が EVOLVE-BLOCK マーカー間かつ
   #if 枝内に収まるか parse 検証。**(4a diff 検疫 = 完了 6359aa5。4b 駆動基盤 = 完了 2026-07-08:
   planner-v4/coder-v4-autonomous を registered 定義化・LoopState checkpoint 永続化・--run-iteration
   駆動口・監査硬化 fails-closed 5 点。実 LLM の測定ループ = 完了 2026-07-09: iteration 1〜4 実走
   all certified/success、iteration 5 は提案生成後に budget-walltime (3600s) で入口停止 (D39 決定2
   の予算停止規定どおり)。正本 = campaign `p3-s4-loop-s4-autonomous-0b53a387` の loop_state.json/
   whiteboard、段 6 へ「未査証 (partial)」として inherit。実走手順は `docs/phase3-s4b-runbook.md`、
   監査は `output/insights/2026-07-08_s4b-loopstate-audit.json`)**
5. **sort-strategy ターゲット起動 / git worktree 隔離 / C1 残課題 (driver 宣言値・並行時の id 安定化)** — S2 gate を満たした後 + 並行合成の段。**(完了 2026-07-09) S2 verify 2 本立ての pipeline 配線** — D36 決定4 の規定 5 点 (campaign identity 組み込み・COMMIT タグ焼き込み・red payload の workload タグ・bench 同一排他 + numactl・IZANAGI_TRACE_DIR 対称化) を `pipeline.evaluate()` に実装 (legacy→S2 の順で複数 verify pass を通し、全通過で certified)。opt-in = `CampaignConfig.search_config["verify"]=="legacy+s2"` (未設定の既存 campaign は無挙動変化)。実機スモーク (stock genome, legacy+S2 実 build/verify) で両パス certified・WAL タグ付けを確認 (137〜166秒)。8 観点 28 エージェントの敵対レビューで是正 4 件 (S2 パスへの competing_bench_pids 追加・numactl 未指定時の fails-closed 化・パス跨ぎの EvalResult.verdict 残留クリア・records_by_stage/load_verify_abort_signals の複数書き込み対応) を実施、テスト 287 本 (新規 14 本) 緑。**残課題**: decision4-2 の「AND 共通ヘルパ」は W (STAGE_COMMIT.verify_configs への書き込み) のみ実装 — 読み手が実際に必要とする consumer が出た時点 (このタスク自体では未発生、S2 を有効化する具体 campaign が無いため) に追加する (規律5: 使われない抽象を先回りで作らない)。正本 = `orchestrator/campaign/pipeline.py` (S2_FLAGS/s2_correctness_workload/evaluate 拡張)・`orchestrator/tests/test_campaign.py` (S2 wiring テスト群)。
   - **(完了 2026-07-09) lock 経路 (cc/silo/transaction.cc) への編集面拡張 (段 3 から繰延、D38)** — coder が lock を変異できるようにする前提作業。survey_B の変更点を同一コミットで実装: source_digest.EVOLVE_BLOCK_SOURCES + ALLOWLIST に `cc/silo/transaction.cc` 追加・hooks/guard_write.py:37 の写し定数を同期・偽 submodule fixture (test_campaign.py `_fake_ccbench_repo`) に transaction.cc 生成追加・test_source_digest_allowlist の反例を `cc/silo/util.cc` (未だ編集面外の隣接ファイル) に差し替え。drift test (`test_constants_match_source_digest`) は既存のまま自動的に新集合へ発火。実機検証 (実 submodule, pin 028f34d): `-Werror=undef` preprocess 成功・stock genome の src_token は "stock" を維持 (後方互換)・includes/trace-diff/allowlist の fails-closed assert 全て緑・guard_write が transaction.cc の Edit を許可しつつ Options.cmake 等は引き続き拒否することを実機確認。**前提 gate = `test_lock_path_edit_surface_requires_auditor_live` の緑を実確認済み** (auditor live の機械 4 点、`s3_lock_coverage.json` all_pass、D38)。この拡張は auditor live 確認と同一コミットに束ね、auditor 不在で lock 経路が編集可能になる窓を作らなかった。**残課題:** 段 4 の coder loop (`p3_s4_loop.SOURCE_REL`) は引き続き backoff.hh 単一マーカーのみを駆動 — 実際の lock 変異 (template patch + marker + diff_quarantine 複数マーカー対応) は未着手の別タスク (本タスクは identity/allowlist 層の地ならしのみ)。非 stock variant の src_token churn は許容済み (再評価方向)。テスト 287 本 (新規0本、フィクスチャ/定数更新のみ) 緑。
   - **(完了 2026-07-09) git worktree 隔離 (opt-in) + C1 残課題の解消 (D40)** — `patchharness.checkout(pin, base_dir)` (使い捨て worktree、呼び出しごとに一意パス) を新設し `applied()` と組み合わせ可能に (責務分離)。`pipeline.evaluate()`/`loop.run_campaign()` に `ccbench_dir`/`cache_root` を実行時引数として素通し (campaign-id には含めない、numactl/do_bench と同じ扱い)。`p3_s4_loop.py` に `--isolate-worktree` opt-in フラグ (既定 OFF、進行中の段4b campaign の識別子・WAL に触れない)。**C1 (並行合成で共有 tree の HEAD が動く場合の id 安定化) は本機構で解消** — 各評価が自分の pin を自分の worktree で checkout するため他の並行評価の影響を受けない (driver 宣言値がリテラルであること自体は IDENT-1/IDENT-3 により意図的据え置き、変更なし)。**sort-strategy ターゲット起動は別タスクへ繰延** (diff_quarantine.py の複数マーカー対応・transaction.cc 用 template patch・mutation_red_gate 実発火など設計検討量が大きく、撤回済みの当初提案と同水準の敵対検証が要るため、規律5 に従い別セッションで扱う)。実機検証: `checkout()` 単体 (実 submodule pin 028f34d、worktree 作成→破棄→base 無傷)・`--isolate-worktree --no-build` dry-run (進行中 campaign の WAL/checkpoint に差分なしを確認)・使い捨て campaign identity での実ビルド(trace+perf)→verify→bench 1 回 (certified, fitness 561,398 tps、本番 campaign 非汚染)。テスト 292 本 (新規 5 本) 緑。正本 = `orchestrator/campaign/patchharness.py`(checkout)・`pipeline.py`/`loop.py`(素通し)・`p3_s4_loop.py`(opt-in フラグ)・D40。
   - **(完了 2026-07-09) sort-strategy 起動の設計再評価 — 3 レンズ敵対レビューで条件付き採用 (D41)** — D22 撤回時の3論点を現基盤 (S2/auditor live/lock経路開放) で再検証し、objection 1/2 は「危険でなく安全 (順序は correctness の入力でない)」に読み替え可能・objection 3 は S2 使用で解消と3レンズ全員が確認 (D22 の全員 reject/high から前進)。一方で新規死角2件 (非 strict-weak-order comparator の std::sort UB・fairness/starvation reward hack が G2 検出をすり抜ける) を発見し、**実装着手前の必須条件7点** (permutation保存assert・ASan/UBSan positive control・fairness観測点・per-variant auditor目視・CCBENCH_*フラグ設計・p3_s4_loop.pyパラメータ化・S2/legacy併存への文言修正) を課した。**実装そのものは本レビューの範囲外、別タスクへ繰延** (規律5、D40 と同型の分割)。正本 = D41・workflow journal (`subagents/workflows/wf_f1bee1e6-de3/journal.jsonl`)。
   - **(完了) D41 必須条件7点のうち機構レベル実装** — 条件2 (permutation保存検査): validationPhase の sort 前後で write_set_.size() と rcdptr_ multiset の不変性を `#if TRACE` で検査 (izanagi-trace へ実装、pin 028f34d→d706650 前進)。trace.hh は変更せず既存の `izanagi_trace::stream()` を直接呼ぶ形に留め (EVOLVE_BLOCK_SOURCES = transaction.cc のみで完結)、verifier 側 (parse/model/core/report の4層、D38 の X 行と同型) に配線。broken patch 2本 (`broken-silo-permutation-erase.patch` = 要素 pop_back で size-changed のみ発火・`broken-silo-permutation-swap.patch` = 要素数不変で rcdptr_ のみ入替え rcdptr-set-changed のみ発火) で「2 検査点が別々に歯を持つ」ことを `s5_permutation_coverage.py` (s3_lock_coverage.py 様式) で実走確認、stock 沈黙含め all_pass。条件5 (CCBENCH_SORT_VARIANT フラグ): `patches/silo-sort-variant.patch` として新設 — protocol 固有 OPTIONS でなく `ccbench_universal_definitions()` に相乗りし `cc/silo/CMakeLists.txt` の ALLOWLIST 拡張を回避 (cmake/Options.cmake のみの改変で完結)。SORT_VARIANT=0 (既定) で src_token="stock"・1 で別 digest に解決されることを `source_digest.resolve()` で実証、`assert_includes_match_head`/`assert_worktree_within_allowlist` も緑。条件1 (ASan/UBSan): 非 SWO comparator (`return &a != &b;`、反対称性違反) を実機検証した結果は残存リスク節に記録 (release/ASan 問わず write_set_.size()>=16 でハング、閾値未満は「クラッシュしない」= 恒真化した安全に見える。UBSan は masstree 側の既存 UB でノイズ)。条件3 (fairness指標) は規律5により実装見送り、指標 (Gini係数/max-min比) と発火条件を残存リスク節に明記。条件4 (auditor目視) は `.claude/agents/auditor.md` に型13-15 (sort marker領域外侵食・非SWO comparator・fairness) を追加 (ユーザー承認済み、サブエージェント定義の自己変更は auto-mode に保護されているため)。条件7 (S2は追加) は実装 (`pipeline.py`) 側が既に正しく「legacy 先頭固定 + extra_correctness で追加」を実装済みと確認、文言修正は不要だった。**条件6 (p3_s4_loop.py パラメータ化) は方針のみ確定・実装は繰延**: `MARKER_ID`/`SOURCE_REL`/`TEMPLATE_PATCH` のモジュール定数パラメータ化でなく、**新規兄弟 driver (`p3_s4_loop_sort.py` 相当) を新設する方針** — genome 構築 (`BACKOFF_FIXED` 前提のハードコード) と attribution 整合チェック (`assert_value_literal_consistent` の `_NOW_BACKOFF_RE` が backoff 固有の変数名・数値リテラル前提) が sort 戦略 (値でなくコード片の変異、attribution チェック自体の形が異なりうる) には転用できないため、既存 backoff 軸の挙動を壊さず併存させるにはモジュール定数の汎用パラメータ化より兄弟 driver 新設の方が安全という判断 (`quarantine()`/`record_diff_reject`/`make_critic_digest`/`check_stop`/`LoopState` 永続化等の汎用ヘルパは共有)。**実際の兄弟 driver 実装・sort-strategy variant を 1 本 coder ループで評価するところまでは本タスクの範囲外、別タスクへ繰延** (規律5、D40 と同型の分割)。正本 = `orchestrator/campaign/s5_permutation_coverage.py`・`patches/{silo-sort-variant,broken-silo-permutation-erase,broken-silo-permutation-swap,broken-silo-sort-nonswo}.patch`・`orchestrator/campaign/pin.py` (d706650)・`orchestrator/verifier/{parse,model,core,report}.py`・`orchestrator/tests/test_verifier.py` (P行 fixture 4本)・`.claude/agents/auditor.md`・`output/env/linux-baremetal/calibration/s5_permutation_coverage.json`。
   - **(完了 2026-07-10) D42 条件6 の残り実装: sort-strategy 兄弟 driver + auditor 機械 gate (D43)** — `orchestrator/campaign/p3_s4_loop_sort.py` を新設 (`p3_s4_loop.py` の汎用ヘルパを `L.` 経由で再利用)。実装前に3レンズ敵対レビュー (workflow `wf_b1b73f25-27d`) を実施し必須修正6点を反映: (1) `coder-v4-autonomous-sort.md` (新設) の出力スキーマから具体戦略の例示 (リーク) を除去、(2) planner direction の意味論をメインセッション側で具体化しない (中立語のみ)、(3) **auditor を機械的な pre-build gate 化** — `auditor.diff_digest` (審査した working_diff の sha256) を proposal JSON 必須フィールドにし `quarantine()` が実際に生成する working_diff の digest と機械照合、不一致は `AuditorGateFailure` (backoff の `AttributionMismatch` 相当) で即停止。verdict=reject/uncertain は diff-quarantine の既存 consumer (`load_diff_rejections`/`render_rejections`) に相乗り (`auditor-violation`/`auditor-uncertain` で subtype 区別、新規 loader を作らない)、(4) `default_cfg()` に S2 verify (`legacy+s2`) を明記 (D41 前提の維持に必須)、(5) `--isolate-worktree` 相当を既定 ON (PIN が backoff driver と異なるため)、(6) `_BASE` に `BACK_OFF:1` 明示・`_resolve_duplicate` に `ccbench_dir` 明示。型14 (非SWO) 機械的プロパティテストの追加は AskUserQuestion で確認の上**次善タスクとして繰延** (規律5、D42 条件1 と同型)。`docs/phase3-s5-sort-runbook.md` (段4b runbook の兄弟) を新設。テスト 312 本 (新規17本) 緑。**実 LLM での 1 iteration 実走は次セッションへ繰延** — `coder-v4-autonomous-sort` はエージェント登録がセッション開始時にのみ読まれるため、本タスクで新設した `.claude/agents/coder-v4-autonomous-sort.md` は同一セッション内で spawn できない (2026-07-08 実証済みの制約、runbook §0 のfresh session ゲート参照)。正本 = D43・`orchestrator/campaign/p3_s4_loop_sort.py`・`.claude/agents/coder-v4-autonomous-sort.md`・`docs/phase3-s5-sort-runbook.md`・`orchestrator/tests/test_p3_s4_loop_sort.py`。
   - **(完了 2026-07-10 (2)) sort-strategy 軸 iteration 1: 実 LLM E2E 実走** — fresh session (agent 登録反映) で runbook §1 のプロトコルを実 LLM (`planner-v4`→`coder-v4-autonomous-sort`→`--preview-diff`→`auditor`→`--run-iteration`) で通し実施。auditor 機械 gate (digest 突合) は初回に転写ミス (impl テキストの末尾改行差) で `AuditorGateFailure` を正しく検出・fails-closed 停止し、正しい digest に転記し直して通過 (設計通りの動作を実地で確認)。coder は `(storage_,key_,rcdptr_)` 3 段辞書式 comparator を提案 (第3段は生ポインタ比較で標準上 unspecified だが `(storage,key)` が write_set_ 内で rcdptr を一意に決めるため到達不能と coder 自身/auditor 双方が独立に指摘)。auditor verdict=pass (nit 2件・proposed_tests 3件、いずれ non-blocking)。`--run-iteration` 実走で **outcome=certified**: verify[legacy] serializable (255074 commits/8026 aborts/0 anomalies)・verify[s2] serializable (1401709 commits/476545 aborts/0 anomalies)・bench median 274,872 tps (CV 0.76%)。D41/D42/D43 が設計した機構 (diff検疫・auditor pre-build gate・S2 verify 併走・git worktree 隔離) が実 LLM 入力で初めて全経路 certified まで到達した実証。critic 呼び出しは n=1 (対照なし、限界効果が退化) のため今回は見送り、次 iteration 着手時に呼ぶ (規律5)。テスト回帰 312 本 (新規0本) 緑。正本 = campaign `output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/` (`loop_state.json`・`runs/wal.jsonl`・`s5_sort_loop_digest.txt`)。**次の一手**: iteration 2 以降の継続 (critic 召喚 → 逆方向判定 → 次 proposal) は別セッションで任意に継続可能 (収束/予算停止まで runbook §3 の規約に従う)。
