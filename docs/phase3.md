# Phase 3 — LLM コード合成 (planner/coder/auditor)

**目的:** roadmap §2 層2(b) **コード粒度の合成**。CCBench コードの `EVOLVE-BLOCK` 領域を LLM (coder) が
diff で書き、フラグ空間の外に最適化 variant を合成する。P2-4 backoff ケーススタディ (critic 帰属が
フラグ空間外の静的 backoff 合成を駆動し certified なまま勝った) がその予告編。Phase 2 の negative result
(P2-5: フラグ探索は自明) が「なぜ合成が要るか」を動機づける。

**最終成果物 (CLAUDE.md):** 新しい CC + なぜ速いかの説明 (層3) + 試行錯誤の記録。

**設計の出所:** 多エージェント workflow (Map5→Design→Critique3→Finalize) + 敵対的安全検証で kickoff を固め、
ユーザー承認 (2026-06-29)。decisions D22。**絶対規律 (特に 1/2/3/5/6) はここで初めて load-bearing になる**
(LLM が正しさを破りうるコードを書く)。

## 読み方 (D35 — セッション開始時に全文を読まない)

- セッション開始時に読むのは 2 箇所だけ: **must 表** (`grep -n "着手前 must" docs/phase3.md` で位置特定) と、
  **「後続段」リストの未了項** — 完了項は行頭が `N. **(完了 <日付>)` で始まるので、それ以外の番号項と
  その未完了サブ項が開タスク。完了/未了の正本はこの後続段リスト (must 表は blocking 分類が主で、
  完了の追記は従)。
- 「残存リスク」節は発火条件付き既知限界の台帳 — セッション開始時には読まず、該当リスクに触れる
  作業時だけ引く。
- 「kickoff の最小スコープ」節の EVOLVE-BLOCK 機構・閉じた領域制約・適用の隔離は**現役の規定** (完了記録ではない)。

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
certified commit する (合格条件の正確な定義は下の「kickoff タスク」節のサマリ + 分離先
`docs/archive/phase3-kickoff-stages1-5.md` の「完了条件 (2 項)」— no-op の identity 後方互換と純 timing の
cache-miss 1 周は別の主張で、両方要る)。新機構の束を**正しさ的に枯れた足場 (純 timing) で先に通す**のが最小手。

### なぜ first target = 純 timing (静的 backoff) か。lock-sort は撤回
draft 第一候補の sort-strategy (lock 獲得経路) は 3 批判者全員が high severity で撤回勧告 (実コード裏取り):
- **verifier は lock 獲得順をトレースしない** (commit 時の (epoch,tid) のみ出力, transaction.cc:517-540)
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
- **適用の隔離:** patch は submodule working-tree への out-of-band 適用 (kickoff/s4-red の campaign 内は
  pin 不動 → campaign-id 不変。**現行 pin の正本は orchestrator/campaign/pin.py の CURRENT_PIN に集約**
  (literal は本文書に再掲しない — 段の前進で必ず腐るため。2026-07-11 監査で 028f34d 再掲が段 5 の
  d706650 前進 (D41/D42) に未追随のまま発見された。前進経緯は pin.py docstring と D38/D41 が正本)。
  歴史的 driver は自分の dff0f1e literal
  を保持し再走は checkout してから)。1 variant 評価ごとに clean→apply→build→revert。apply 前に対象が pinned-clean か
  assert (汚れていたら fails-closed abort)。駆動部 = `orchestrator/campaign/patchharness.py` の `applied()` context
  manager (blocking タスクで実装済み: enter = flock 排他 + pinned-clean assert + apply、exit = revert +
  clean assert。順序固定 apply→resolve→build→revert は context manager の形状で担保)。

---

## kickoff タスク (blocking 順) — 完了 (2026-07-05)。詳細は `docs/archive/phase3-kickoff-stages1-5.md` へ分離 (2026-07-10)

全項目完了。完了条件 2 項 (1 = identity 後方互換: inert no-op variant が src_token=stock で stock genome
cache-hit certified、2 = 合成枝の 1 周: 純 timing variant が別 variant_id・cache-miss 新規ビルドで
verify abort > 0 → bench → certified) とも WAL 機械判定 10/10 PASS (2026-07-05)。各項目の実装詳細・
設計根拠・完了条件の解釈規定 (「純 timing の cache-hit は一次防壁の故障」等) は分離先 (凍結) にある。

- [x] (blocking) cache_key + variant_id の honest 拡張 — source_digest を両 pre-image に織り込み alias 封鎖 (D23/D24)
- [x] (blocking) EVOLVE-BLOCK template patch — silo abort-path (BACKOFF_FIXED 軸) に骨格 1 つ、inert = stock cache-hit 実証
- [x] (blocking) verify の abort 数を WAL に記録 — 集計行が読めない run は fails-closed reject (`trace-no-abort-counts`)
- [x] (blocking) apply/revert ハーネス — `patchharness.applied()` (flock 排他 + pinned-clean assert + fails-closed)
- [x] (blocking) build 後の digest 再照合 (TOCTOU 遮断) — `buildcache._recheck_src_token`
- [x] (blocking) source_digest の #include 死角の閉塞 (最小案) — `assert_includes_match_head` (computed include は残存リスク節)
- [x] (完了・方針 A) H3 hooks = 明白な直接書き込みを止める最小第二防壁 — guard_write / guard_bash 配線済 (D30/D33/D34)
- [x] (完了) 観測者効果の二重検査 = diff-of-diffs — `assert_trace_diff_matches_head` (commit 14d64e6)
- [x] coder.md 生成 + 純 timing variant 1 本で全配線 1 周 — 完了条件 1/2 とも WAL 機械判定 PASS (2026-07-05)
- [x] broken-silo 回帰 — verifier の G2 赤検出が空打ちでないことの実証 (verdict=non-serializable、anomalies 20 件全て G2)

**新規実体化は coder のみ** (critic/profiler は既存再利用、auditor/planner は後続)。

**常設の安全規定 (kickoff 完了後も効き続ける):** COMMIT を書く唯一の経路は `pipeline.evaluate()` —
guided.py の replay-fake certified 経路は live variant に絶対再利用しない。

---

## 残り Phase 3 着手前 must の blocking 分類

| must | kickoff | 根拠 |
|---|---|---|
| **H3 hooks** | **完了 (方針 A)** | 最小第二防壁を配線 (D30/D33)。3 巡目検証で real 9/known 6 摘出・全修正 (変異検査済)、critical (source_digest builtin definedness 偽 cache hit) は D34 で封鎖。identity/観測者効果の担保は下 2 行の一次防壁が担う |
| **cache_key+variant_id 拡張** | **完了** (kickoff タスク 1 で消化) | inert 実証の継承 + 同フラグ別 diff alias 防止。**方針 A で identity honest の一次防壁に昇格** (偽 cache hit を hook でなく digest で塞ぐ) |
| **観測者効果二重検査** | **完了 (14d64e6)** | nm だけでは data-structure 観測者効果を見逃す。**方針 A で TRACE 混入検知の一次防壁に昇格** (payload 検査に依存しない)。diff-of-diffs を buildcache.build 出口 (hit/fresh 両経路) で発火、fails-closed |
| **S4** | 完了済 | 規律3 配線 (verify-red の構造化 anomaly を abort payload + load_rejections)。**consumer 実体化も完了 (後続段 2、2026-07-06、D37)** — liveness-red 別型・render 3 形状・critic 消費規定・実走赤 2 本で閉ループ実証 (「読んで方向を返す」まで。還流 = 次 variant 生成への使用は段 4) |
| S2 (certify=perf) | non-blocking (abort>0 確認は完了条件 2 に反映済み) | 純 timing は lock/validation 論理に触れないが、**abort 経路は踏む** — verify で abort≈0 だと合成枝が空振り認証になる (残存リスク節)。abort>0 確認は完了条件 2 に明記済み (前提 = abort 数の WAL 記録タスク)。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) **→ 構成確定済 (2026-07-06、後続段 1 完了・gate 3 点 all_pass、D36)。pipeline 配線も完了 (段 5、D36 決定 4、opt-in = legacy+s2)** |
| S1 (別 protocol trace-hook) | non-blocking (kickoff) / **主実験 headline 2 で発火** | silo 内に閉じる限り不要。ただし発火条件は「別 protocol 移植」だけでなく**主実験 headline 2 (クロスプロトコル stock 最良) も含む** — trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) ため、headline 2 までに S1 移植か「stock 専用計測経路を規律2 と整合させる設計」のどちらかが要る (後続段 6 の前提タスク (a)) |
| C1 (campaign-id drift) | **解消済み (2026-07-09、段5、D40)** | apply→revert で HEAD 不動。読み手 3 本の discover 統一 (065593a, 2026-07-02) で歴史的 campaign の孤立は解消済み。並行合成/patch 常駐で HEAD が動く残課題は git worktree 隔離 (`patchharness.checkout()`、opt-in) で解消 — 各評価が自分の pin を自分の worktree で checkout するため他の並行評価の影響を受けない。driver 宣言値 (phase2.md §C1) がリテラルであること自体は IDENT-1/IDENT-3 により意図的据え置き (変更なし) |

---

## 後続段 (各々 ablation 点を残して投入)

**段 1〜5 は完了 (2026-07-06〜07-10)。完了記録の詳細 (実装内訳・敵対レビュー・実測値・実機検証手順)
は `docs/archive/phase3-kickoff-stages1-5.md` へ分離 (2026-07-10)** — ここには完了サマリ + 現役情報
(ablation 点・残課題・発火条件) + 正本ポインタのみ残す (完了/未了の正本は本リスト、番号は分離前と不変)。
未了の段の完了済みサブ項・段階内訳は、その段が閉じてから同手口で分離する (現役 context のうちは据え置き):

1. **(完了 2026-07-06) S2 verify 構成の確定** — perf 代表 workload と完全同一構成 (「縮小」なし) で
   gate 3 点 (contention 再現・trace 規模・赤検出力) all_pass。pipeline 配線 (D36 決定 4) は段 5 で完了。
   正本 = D36・`output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json`・
   `orchestrator/campaign/s2_verify_calibration.py`。
2. **(完了 2026-07-06) S4 load_rejections consumer 実体化** — LivenessRejection 別型 / render_rejections
   (verdict 軸 3 形状) / verify abort 率シグナル / critic.md 消費規定 / integrity-class positive control。
   赤 2 本実走で「赤 → 構造化 → critic が読んで方向を返す」まで実証 (実証の線引き: 「還流」= 次 variant
   生成への使用は段 4、「改善」は段 4〜6)。**ablation 点 = render_rejections の合流 1 点 (還流 on/off。reason-only 第 3 アームは
   段 6 で判断)。** 正規経路の verify-red 初発火は編集面が validation に開く段 3 以降。正本 = D37・
   `orchestrator/campaign/p3_s4_red.py`。
3. **(完了 2026-07-06) auditor.md 生成と起動 + write_set 被覆 assert + in-class positive control** —
   auditor は read-only (提案テストを構造化出力で返し人間レビュー gate 下で反映)。**auditor live 定義 =
   機械 4 点 + n=1 定性 2 点、段 6 headline gate の充足条件は機械 4 点。ablation 点 = 被覆 assert on/off の
   lockskip 検出力差。** pin 前進 dff0f1e→028f34d (D38、orchestrator/campaign/pin.py)。正本 = D38・
   `orchestrator/campaign/s3_lock_coverage.py`・`output/insights/2026-07-06_s3-auditor-live-n1.md`。
4. **(完了 2026-07-09) guided 検疫層の diff 検疫拡張 + planner/coder 自律ループ (4a/4b)** — diff 検疫
   (6359aa5)・駆動基盤 (planner-v4/coder-v4-autonomous の registered 定義化・LoopState checkpoint 永続化・
   `--run-iteration` 駆動口・監査硬化 fails-closed 5 点)・実 LLM iteration 1〜4 all certified/success +
   iteration 5 は budget-walltime (3600s) 入口停止 (D39 決定 2 どおり)。**段 6 へ「未査証 (partial)」として
   inherit。** 実走手順 = `docs/phase3-s4b-runbook.md`。正本 = campaign `p3-s4-loop-s4-autonomous-0b53a387`
   の loop_state.json/whiteboard・`output/insights/2026-07-08_s4b-loopstate-audit.json`。
5. **(完了 2026-07-09〜07-10) sort-strategy 軸の起動一式** — S2 verify 2 本立て pipeline 配線 (D36 決定 4、
   opt-in = `search_config["verify"]=="legacy+s2"`) / lock 経路 (cc/silo/transaction.cc) の編集面拡張
   (前提 gate = auditor live、同一コミット束ね) / git worktree 隔離 (opt-in) + C1 解消 (D40) / 起動の
   設計再評価と実装着手前必須条件 7 点 (D41) / 必須条件の機構レベル実装 (permutation 保存検査・
   SORT_VARIANT フラグ・auditor ギャラリー型 13-15、D42) / 兄弟 driver `p3_s4_loop_sort.py` + auditor
   機械 gate (`AuditorGateFailure`、D43) / 実 LLM iteration 1 E2E で初 certified (bench median 274,872 tps、
   CV 0.76%)。**iteration 2 は見送りで決着** (ユーザー協議、worklog 2026-07-10 (10) — 偵察 (D46) で
   軸に floor 超地形が見当たらないため。代替の本筋 = 段 8a 前倒し)。
   **残課題 (現役):** (a) D36 決定 4-2 の「AND 共通ヘルパ」は W (STAGE_COMMIT.verify_configs への書き込み)
   のみ実装 — 読み手 consumer が出た時点で追加 (規律 5)、(b) backoff 軸 driver (`p3_s4_loop.SOURCE_REL`)
   は引き続き backoff.hh 単一マーカーのみを駆動 (sort 軸は兄弟 driver 側)、(c) auditor ギャラリー型 14
   (非 SWO comparator) の機械的プロパティテスト追加は次善タスクとして繰延のまま (規律 5、D42 条件 1 と
   同型 — 現状の防壁は auditor の静的目視 + 残存リスク節の実機確認記録)。実走手順 =
   `docs/phase3-s5-sort-runbook.md`。正本 = D40〜D43・`orchestrator/campaign/p3_s4_loop_sort.py`・
   campaign `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d`。
6. **主実験の実行 (headline 比較 4 対照 + LLM ablation)** — 冒頭「Phase 3 全体の完了定義と主実験の評価設計」を
   実走する段。**Phase 3 の headline 主張はこの段の完了をもって初めて出せる** (段 4/5 の中間結果は評価設計に
   従った暫定として報告)。gate = 変異軸 (sort or それ以降) から headline 候補が出たこと + S2 gate + auditor live。
   ここで仕込む前提タスク: (a) **S1 移植 or stock 専用計測経路の設計判断** (headline 2 の前提。must 表参照。
   D44 注意: stock 専用計測経路を選ぶ場合、対抗馬だけ certified 要件を免除する非対称比較になる — その扱いを
   設計時に明文化する)、
   (b) SPACES への mocc/tictoc/cicada 登録 + protocol 別 calibration + between-run floor の対象別再実測、
   (c) ランダム変異生成器と生成分布の確定 (ベースライン 3)、(d) 機械 sweep 駆動と軸命名手順の固定 (ベースライン 4。
   phase3-main-experiment.md 2026-07-10 追記の sweep-matched / sweep-ceiling 分離に従う)、
   (e) coder リーク制御 (P2-5/D21 の Phase 3 版) の実体化、(f) 検証相 (seed×N・長 extime) の実装、
   (g) サンプル設計 4 点の数値確定 (統計計画の節)、
   (h) **(完了 2026-07-10、D45) planner→coder 経路のリーク遮断 (D44、headline の前提条件)** — planner-v4 を
   tools:[] 化 (Read 剥奪 = file-read 経路を coder (D39 決定7) と同型に構造遮断。入力は従来どおりメイン
   セッションの射影 inline JSON — 運用上 Read の必要はゼロだった)。allowlist 案は棄却 (根拠は D45)。
   同時に文書地雷 4 点を除去/中和: `coder-v4-autonomous.md` の spec_file 例 → leakproof_context に置換、
   design-v1 §3 の「output/insights OK」記述と design-foundation §3 の「tools=read-only」断定に supersede
   注記、`src/coder-spec.md` §7 の旧設計フローに superseded 注記、`src/coder-leakproof-context.md` 内
   template の coder-spec 誘導参照を実運用 (射影 inline) に一致させた。**遮断は Read 経路に限る** —
   justification 自然文経路・射影の自己規律は残存リスク節に維持。3レンズ敵対レビュー済み
   (must-fix 1・should-fix 6 を全て反映)。定義変更は次セッションから有効、
   (i) **(完了 2026-07-10、D46) sort 軸の機械 sweep 先行実測 (D44、安価な先取り)** — sort comparator
   空間を構文契約から機械列挙 (15 候補 + stock、全点 SWO 構成的保証。ランダム変異は D46 決定4 で
   段 6 (c) へ繰延) し、p2_2 確定動作点で balanced/write-heavy 全点 legacy+s2 verify の偵察
   (preliminary、事前登録外カテゴリ — (c) 判定は出さず、正式 grid への firewall を明文化)。実測:
   32+6 点全 certified・anomaly 0。**balanced は全点 floor 内で winner が再測不再現 (差なし方向)、
   write-heavy は sk_ad の stock 超え +3.55%/+4.12% が 2 run 再現するも分解すると各成分 floor 内・
   floor 未較正・n=2 で断定せず。sort 軸に「順序の質」由来の floor 超地形は見当たらない — 軸選定の
   見直し (段 8a 前倒し等) が人間判断事項** (正本 = D46・`output/insights/2026-07-10_s6-sort-sweep-
   preliminary.md`・`orchestrator/campaign/s6_sort_sweep.py`)、
   (j) **(完了 2026-07-10)** related-work の欠落埋め (D44) —
   Web 調査 5 レンズ + 書誌の独立機械検証 (arXiv バルク 9/9・DOI・リポジトリ実在) を経て
   related-work/README.md §7.1/7.2 へ反映: OtterTune 系 (knob tuning 4 本) と learned DB components
   系 (5 本) を系譜まとめエントリで新設、AlphaEvolve/FunSearch を一次資料裏付けへ更新 (EVOLVE-BLOCK
   マーカーの出典 = AlphaEvolve §2.1/2.3 と確定、FunSearch は arXiv プレプリント不在確認)、
   OpenEvolve は「論文なし」を三重根拠で確定。**副次発見: CCaaLF は v4 で NeurCC に改名され
   SIGMOD 2026 採択** (エントリ・逆引き索引に反映)。生データ =
   `docs/related-work/literature-map/gap-research-2026-07-10.md`。**Polyjuice/NeurCC 実測比較は
   見送りで決着** (ユーザー協議、worklog 2026-07-10 (9)。再判断の発火条件 = 「学習型 CC を定量的に
   上回る」の headline 昇格時のみ、材料は worklog 2026-07-10 (8))。
7. **(拡張予約) 最適化移植 + カタログ化** — roadmap §2 層2(b) の当初の本丸「他 CC の最適化を CCBench コーパスから
   移植する」+ 隠れた肝「最適化カタログ化 (前提/効果/競合の三つ組、I5 対策)」は、**主実験 (段 6) 完了後の拡張**として
   ここに予約する (a' 方針、D32)。根拠 = 非対称性: 空間外合成は P2-4 で実証済み・**移植の価値は未検証仮説** (I5 =
   「異なる実装の混合は不適切」という CCBench 著者の警告 + 他 CC のメタデータ前提を持ち込む正しさ攻撃面) なので、
   実証済みの道で主実験まで到達してから投資判断する (規律5 / P2-5 の教訓 = 仮説に工数を先払いしない)。着手時の
   一歩目は**カタログ化の試作 1 枚** (他 CC の最適化 1 つを「前提/効果/競合」でカード化し、移植先で前提が満たせるかを
   判定) で、本格投資はその結果で決める。cicada/oze への空間拡大 (S1 移植を伴う) と束ねるのが自然。カタログ化の
   成果物は移植を見送っても層3 の説明生成に流用できるため無駄にならない。
8. **(D44 で追加。着手順・段 6 との前後は着手時に判断) 探索側を防壁の水準へ引き上げる 3 機構** — 外部評価
   (worklog 2026-07-10 (3)) が特定した「CC 自動合成の主張と機構のギャップ」への対策。各々着手時に
   D41 と同水準の敵対検証を課す (設計の具体化はここに書かない — 着手時の設計タスクが正本):
   - **(8a) 軸提案のループ内化 (前倒し決着 2026-07-10 — sort 軸 iteration 2 見送りの代替本筋、
     worklog 2026-07-10 (10))** — LLM の実証済み価値 (機序帰属からの軸発見、P2-4) をループに戻す。
     critic の機序帰属を入力に「次の変異軸候補 (EVOLVE-BLOCK hole の位置と骨格)」を提案する役を新設し、
     人間は承認 gate としてのみ関与する。D41→D43 で 1 回実施した軸オンボーディング手順 (骨格 patch・
     検疫対応・positive control・auditor ギャラリー拡張・verifier 死角の特定) を**再利用可能なテンプレ**に
     固めることが前提作業 — 軸あたり固定費を下げないとループ内化しても回らない。**前提作業は完了
     (2026-07-10、`docs/axis-onboarding.md` 新設 — 3 レンズ敵対レビュー済み、must 3/should 8 全反映。
     偵察 insight → LLM ループの新設 firewall と「削るのは再発見コストでありゲートではない」を明文化)**。
     リーク制御と両立する
     (軸提案に勝ち筋の値は不要、機序帰属のみでよい)。次軸の標準手順 = 機械 sweep 偵察 (D46 の器) で
     軸の生死を先取りしてから LLM ループを回す (worklog 2026-07-10 (10) 決着 3 点目)。
     **本体設計は完了 (2026-07-10、D47 — 3 巡の敵対レビュー: v1 で実効性レンズ reject → must 5/
     should 11/nit 6 反映の v2 → 再判定で新規 must 1 → v3 で adopt-with-conditions)。** 役の常設
     定義 = `docs/agent-architecture.md` §axis-proposer。要点: tools:[] + 二層射影 (勝ち筋の値は
     落とし診断数値は保持・recommend 丸ごと除外・死軸は生死二値のみ)・出口基準の事前定義付き
     n=1 実証・**8a 由来軸は当面「探索補助」限定で段 6 headline の対象軸にしない** (事前登録の
     命名固定と原理的に非両立のため、D47 決定 5)。**実体化完了 (2026-07-10、ユーザー明示承認済み =
     worklog 2026-07-10 (13)。`.claude/agents/axis-proposer.md` 生成 + D47 必須条件 5 点消化 —
     条件 2 は残存リスク節、条件 3/4 は axis-onboarding §2/§3-B、条件 5 は定義の出力スキーマ)。**
     **n=1 実証完了 (2026-07-10、D47 決定 4 の出口基準で成功 — 3 項目全 yes の候補 2 件 /
     提案 3 件、採点は射影非関与の独立コンテキスト)。** 一次資料 = `output/insights/
     2026-07-10_s8a-n1-proposal-and-scoring.json` (提案・採点全文) + `output/insights/
     2026-07-10_s8a-n1-provenance.json`
     (三点セット: raw の脚 = P2-3 要旨 insight — critic 再実行による生出力再生成は勝ち筋を含む
     現行文書経由の記憶汚染リスクで不採用、実体化検証 2026-07-10 の決定 / 射影版入力 / 落とした
     対応表)。観測: 恒真 0/3・既存軸再提案 0・**既開通領域への偏り 3/3 (全提案が transaction.cc
     — 開通・未開通対称の地図でも bias が消えなかった。次回 n を増やすときの観測継続項目)**。
     **人間承認 gate 決着 (2026-07-10、ユーザー判断): 提案 1 (silo-backoff-trigger-gating) のみ
     採用。** 提案 2 (wal-flush-cadence) は軸適格性 no、提案 3 (lock-conflict-retry-bound) は
     スカラー縮退リスクの境界で棄却 (採点 insight の判定材料どおり)。
     **段階 B 完了 (2026-07-10、D48 — シート独立再導出 + 3 レンズ敵対レビューで条件付き採用。
     verdict = 3 レンズとも adopt-with-conditions、must 1/should 7/nit 3 全反映、D47 必須検査
     3 点 = 全 PASS)。** 骨格設計の確定 = #if 囲み stock inert / thread_local 7 点全 store +
     sentinel fail-safe / 構文契約は要因 enum + 定数のみ (偵察空間 = coder 空間)。シート
     (裁定反映済み) = `output/insights/2026-07-10_s8a-stage-b-sheet-backoff-trigger-gating.md`。
     **段階 C 完了 (2026-07-10、D49 — D48 必須条件 7 点全消化)。** 骨格 patch
     (`patches/silo-backoff-trigger-gating-variant.patch`、stock inert・identity 実証済み) +
     positive control (計装/misattr patch + `s8a_trigger_coverage.py`、11 検査 all_pass —
     misattr の赤の歯を実走証明、verifier は緑のまま = 死角の実証) + 中立性 3 レンズ全通過 +
     軸定数 `orchestrator/campaign/axis_trigger_gating.py` (D 偵察器/E driver の import 先、
     構文契約禁止リストの転記元)。実装上の設計判断 (計装の characterization 専用分離・hole の
     述語 1 行化・構造ゼロ検査型) は D49 が正本。
     **段階 D 完了 (2026-07-11、D50 — 必須前提 3 点 + D49 申し送り 3 点全消化)。**
     機械 sweep 偵察 (2^3 subset + ident_all + stock、3 workload、全点 verify legacy+s2) で
     **floor 超地形が 3 workload とも cross-run 再現** (best vs ident_all: balanced g_rl
     +84.5%/再測 +91.0%、write-heavy g_rt +61.2%/+61.3%、read-heavy g_rl +98.9%/+98.7%) =
     軸は生の強い候補。insight =
     `output/insights/2026-07-11_s8a-trigger-gating-recon.md` (裁定台帳・kill 残骸毒の
     教訓を含む)。
     **E 段実装完了 (2026-07-12、D51 — gate はユーザー承認 (worklog 07-12 (2)) で通過。
     実装前 3 レンズ敵対レビュー adopt-with-conditions、must 3/should 10/nit 5 全反映)。**
     provenance 情報源記録義務 (D46 (a) ループ版、監査 L4-1) の宿主 =
     `<campaign root>/reports/p3_s8a_trigger_loop_provenance.json` (driver が自動記録・
     省略不能、書き込み順序と fails-closed 群は D51 決定 1)。成果物 = `auditor_gate.py`
     (共有昇格) + `p3_s4_loop_trigger_gating.py` + `docs/phase3-s8a-trigger-runbook.md` +
     テスト 28 本。残るタスク = **(1) coder 定義のユーザー承認** (草案 =
     `output/insights/2026-07-12_s8a-stage-e-coder-agent-draft.md`。承認後
     `.claude/agents/coder-v4-autonomous-trigger-gating.md` へ配置)、**(2) F 段 = 実 LLM
     iteration 1 E2E** (配置 commit 後の fresh session、runbook §0 の実走前ゲート)。
   - **(8b) workload 次元のループ入力化** — 「ワークロード特化」の実証に必須。最小の一歩 = 既存 3 類型
     (rr5/rr50/rr95) で同一軸の campaign を並走させ特化 (workload ごとに異なる勝ち筋) が出るかを見る。
     coder への入力に抽象化した workload 記述子 (read 比率・競合水準の抽象ラベル。実測値はリークしない形)
     を追加する。P2-4 の 3 類型結果 (+38.3%/+11.3%/−6.6%) が有望性の既存証拠。
   - **(8c) 駆動のセッション非依存化** — 実測の律速は build/verify (66〜175 秒/iteration) ではなく
     エージェント呼び出しとセッション運営 (実 iteration 間隔 8〜25 分、subagent 登録のセッション開始時
     制約)。planner/coder/auditor の呼び出しをセッション登録に依存しない駆動 (orchestrator からの API
     直呼び) に移し、予算時計を暦時間から実行時間ベースへ変える。「ループ主導権は orchestrator」
     (roadmap §3.8) の自然な延長であり、一晩数十 iteration を可能にする。

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
- **ftruncate-xor insight の還元判断欄の追随** (worklog 2026-07-10 (19) 由来) — 上流還元は PR #116/#118 で完了済みだが insight (2026-06-19) は「ユーザー確認待ち」表記のまま。追記訂正はユーザー判断待ち (勝手に書き換えない)。
- **buildcache 残骸破棄の結線統合テスト** (2026-07-11 監査 L2-2 由来) — fc4d3fa の回帰テスト 2 本は helper 単体のみで、build() が configure 前に破棄を呼ぶ結線を assert しない。結線だけ外れる将来 refactor への歯として統合テスト 1 本の余地。

---

## 残存リスク

(発火条件付き既知限界の台帳。解消済み表記の項も未解消 tail を持つため**一括のアーカイブ分離は不可** —
分離するなら項単位で tail の有無を確認する)

- 純 timing first target は**新規性が薄い** (機構の配線実証が主目的、性能新規性は sort 以降)。意図的トレードオフ。
- **S2 non-blocking の根拠に空振り認証リスク (解消 2026-07-06、後続段 1、D36)**: 「純 timing は workload 依存
  パスを持たない」は厳密には不正確 (static backoff は abort 時にのみ実行される競合依存パス) だが、完了条件 2 の
  「verify run の abort > 0 を WAL で確認」で空振り認証を防止済み。S2 構成自体は後続段 1 で確定 (gate 3 点
  all_pass)。pipeline 配線も段 5 で完了 (D36 決定 4)。**timing 純度そのもの (straight-line・API 範囲) は payload 検査
  では機械保証されず、auditor live まで coder diff の人間レビューが gate** (方針 A の帰結、未解消のまま)。
- preprocess 後ハッシュは対象ファイル集合の列挙漏れがあれば偽 cache hit が復活する。固定集合に限定しテストで固定するが
  template patch の改訂で集合が動いたら漏れる残留リスク。**タスク2 敵対レビューで実証 (medium, D24)**: `Options.cmake` は
  ALLOWLIST 内だが `EVOLVE_BLOCK_SOURCES` (= digest 対象) 外で、`VAL_SIZE` 等の build 左右マクロを変えると別バイナリ
  なのに src_token/cache_key/variant_id が不変 (偽 hit)。現状は発火経路が人間 template のみ (coder 未実装) ゆえ潜在。
  **方針 A で塞ぎ方が変わった (D30)**: 旧設計は「H3 hook が coder の編集面を #if 枝に絞ることで塞ぐ」だったが、2 巡目検証
  (SPEC-2) が Bash 経路の `sed -i .../Options.cmake` で hook を丸ごと迂回できることを示した。→ 恒久解は **identity 側
  (configure 最終 -D 集合、or `Options.cmake` の digest 織り込み) を hook 非依存にする**。kickoff では固定集合限定 +
  テスト固定で潜在に留め、cicada/oze 拡張で protocol 写像が load-bearing になった段へ繰延 (D23)。
- **broken-silo は clean G2 の easy case (解消 2026-07-06、後続段 2、D37)**: coder が出す赤の多くは
  integrity-class (verdict indeterminate) になりうる懸念に対し、integrity-class positive control 2 形状 +
  dup_txids の verdict 級テストを新設して閉ループ実証。既知偽陰性 2 形状は characterization テストとして
  可視化 (S1 形式拡張時の回帰点、詳細は D37)。
- **coder のリーク制御 — 段 4 の tools:[] 構造遮断 (coder-v4-autonomous、D39 決定 7) で部分消化。
  完全版 (入力射影の体系化) は後続段 6 前提タスク (e) に予約済み・実体化未了** (見出しの現状追随
  2026-07-11 監査 — 旧見出し「未予約」は (e) の予約と自己矛盾していた。以下は経緯の記録):
  kickoff の題材 BACKOFF_FIXED は、勝ち筋
  (contention 域で stock 最良 +38%/+11%、sweet-spot 値) が docs・insights・WAL・CLAUDE.md にリポジトリ内既知として
  書かれている。coder のコンテキストにこれが混入すると「合成できた」のか「答えを読んだ」のか分離できない。P2-5 は
  誘導アームで **fresh context + 最適解 literal の物理削除 (`critic-experiment`) + 評価済みのみ digest** のリーク制御を
  確立した (D12/D21)。Phase 3 で coder が実際に #if 枝を自律生成する段 (後続段 4) では、この Phase 3 版リーク制御
  (勝ち筋値・機序説明を coder の入力から遮断) を予約する。kickoff (no-op / 人間が値を与える純 timing) では coder が
  値を発明しないので潜在。
- **観測者効果の二重検査の述語 (解消、commit 14d64e6)**: 旧仕様 (TRACE マクロ以外の差分無し diff) は
  trace/perf の正当な差分を誤検出する・#ifdef TRACE 内側への攻撃を素通しする、の 2 欠陥があったが、
  diff-of-diffs (variant の TRACE=1/TRACE=0 差分が pinned HEAD の同差分と一致することを assert) で解消。
  **残る限界: #ifdef の外 = 両ビルド共通の検証専用メタデータは機械判定不能** (auditor / 人間レビュー領域、未解消)。
- **#include 死角の残り (道Y 一般問題)**: identity 核の閉塞 (`assert_includes_match_head`) が捕えるのは literal な
  `#include` 行のみ。`#if __has_include(...)` (preprocess 環境と実ビルドで評価が分岐しうる) や #define 経由の
  computed include は #include 行に現れず素通りする。identity 核だけでは完了条件 1 (骨格の #if 指令は inert) と
  両立して塞げない (骨格 #if と payload #if の区別には skeleton 抽出が要るが、skeleton 抽出は D34 で完了条件 1 と
  両立しないため却下済み)。guard_write の payload テキスト検査も D33 で物理削除済み (designated ソース内の内容は
  検査しない) — したがって受け皿は **auditor + 規律6 監査領域の known-limitation として据え置く** (機械防壁の予約
  なし)。kickoff (no-op / 人間が値を与える純 timing) では coder が #if/#include/#define を発明しないので潜在 —
  後続段 4 (coder 自律期) で auditor のレビュー観点に明示的に含める。
- **共有 working-tree の並走 (ABA) — 解消済み (2026-07-09、段5、D40、opt-in)**: patchharness の
  `_tree_lock`/`applied()` (共有 tree 1 本 + flock 直列化) は既定のまま残るが、`checkout()` (使い捨て
  git worktree、呼び出しごとに一意パス) を新設し組み合わせ可能にした。opt-in した呼び手 (現状
  `p3_s4_loop.py --isolate-worktree`) は worktree ごと使い捨てるため revert 後の残骸検査の既知の弱さ
  (「porcelain 空」より弱い) も実害が無くなる。opt-in していない他 4 driver (歴史的 campaign 再現用) は
  従来どおり `_tree_lock`/`applied()` のみで動作 (規律5: 使われないものを先回りで変えない)。
- **_recheck の transient 失敗破棄は D25 と非対称 (意図的)**: build 後再照合 (`_recheck_src_token`) で resolve が
  transient に失敗した場合も新規ビルド成果を破棄する。D25 (identity-error abort は retryable) と層が違う — WAL
  terminal の可否ではなく共有キャッシュの清潔性の問題で、identity 不明のバイナリを残す方が害が大きい (偽 hit 防止 >
  再ビルドコスト)。cache_key で次 run が再ビルドするので D25 の再評価可能性は保たれる。
- **lock 被覆 assert の既知盲点 (後続段 3、D38)**: (a) memory-race 型 (CAS→素 store の非原子 lock) は verifier も
  被覆 assert も見逃す — 段 3 scope 外の characterization 台帳項。「相補的」は {書き lock 欠落} と {読み検証弱化}
  に限定、この盲点は両者の外。(b) INSERT/insert 経路変異はスコープ外 (段 3 は lockWriteSet の write lock 欠落
  class 限定)。(c) tidword に owner 無しゆえ lock stomp/二重保持は raw∧shadow を満たしスコープ外。(d) auditor が
  段 4 で自律追加する assert の mutation 非恒真性は、段 4 で driver の mutation-red 汎用ゲート `mutation_red_gate`
  として実装 (構文一次篩 + positive control 実走、D39 決定5)。(e) auditor の書き込み面 path-scoped 機械執行は
  段 4 で「read-only 据え置きが正解」と裁定 (guard_write は caller 非識別ゆえ原理的に不能、D39 決定6)。
  詳細は D38/D39 の残存リスク節。
- **fairness/starvation reward hack の機械観測点は未実装 (段5、D41 決定3、規律5により意図的に見送り)**:
  多数派キー優先で少数派キーを飢餓させる write_set sort comparator は、直列化可能性を壊さないため G2 検出を
  すり抜けたまま見かけの throughput を稼げる (D41 死角2)。**発火条件:** sort-strategy の variant が実際に段6
  主実験の headline 候補になったとき (= 見かけの性能差が fairness 由来でないことを示す必要が生じたとき)。
  **観測すべき指標:** per-key または per-thread の commit 数分布から Gini 係数 (0=完全平等・1=完全不平等) または
  max-min 比 (最大 commit 数/最小 commit 数)。**想定される実装場所:** critic の leading indicators
  の算出部 (専用モジュールは未実装 — 実装場所は着手時に確定) または段6 headline 判定に先立つ専用 driver。現状の唯一の防壁は
  auditor ギャラリー型15 (静的目視、`.claude/agents/auditor.md`) — 機械観測点が無いことを沈黙させないための記録
  (規律3)。
- **planner→coder 経路の遮断は Read 経路のみ構造化済み — justification 自然文経路と射影の自己規律は
  残存 (D44→D45、段 6 前提タスク (h) は 2026-07-10 完了)**: planner-v4 の tools:[] 化で file-read 経路は
  coder (D39 決定7) と同型に構造遮断され、文書地雷 (coder-v4-autonomous.md の spec_file 例・design 文書の
  「output/insights OK」記述・coder-spec.md §7 旧設計フロー・leakproof-context 内の誘導参照) も除去/中和
  済み — headline 前提条件 (phase3-main-experiment.md 2026-07-10 追記 4) は「Read 無制限の解消」の字義で
  充足。**残る限界 2 点** (headline 主張時は「Read 経路の構造遮断済み・以下は既知限界」と限定表現する):
  (a) spawn 時入力の射影はメインセッションの自己規律のまま — runbook §2 チェックリストは prompt 規律で
  あり「テキスト検査・自己申告は唯一防壁にできない」(D30) はこの面に未適用、(b) planner_direction の
  justification 自然文が機序含み語を coder へ運ぶ経路は構造的に開いたまま (D43 の敵対レビューで「乖離度」
  「再順序化」等の機序含み語の具体化案が一度採用されかけ撤回された = 同種漏洩がプロンプト設計レベルで
  起きうることの実証)。
- **非 strict-weak-order comparator の UB は write_set_ サイズ依存で顕在化する (段5、D41 決定1、実機確認)**:
  反対称性違反 comparator (`return &a != &b;`) を `-DSORT_VARIANT=1` で実機ビルド・実行したところ、
  release/ASan (UBSan 無し) 問わず write_set_.size() が **16 要素以上** (libstdc++ introsort の insertion-sort
  閾値) でハングし、閾値未満では release/ASan とも「クラッシュしない」= 恒真化した安全に見えた。**「小さい
  write_set では動く」ことを非 SWO comparator の安全性の証拠にしてはいけない** (auditor ギャラリー型14)。
  UBSan (`-DENABLE_UB_SANITIZER=ON`) は masstree (third-party 依存、`kpermuter.hh`) 側の既存の無関係な UB
  (shift-exponent-too-large) を stock でも検出してしまいノイズになり、この検証には使えなかった —
  sort-strategy の ASan/UBSan positive control (D41 決定1) を将来ドライバ化する際は UBSan を対象から外すか
  masstree 側の既知 UB を許容リストする設計が要る。broken patch = `patches/broken-silo-sort-nonswo.patch`
  (silo-sort-variant.patch 込み)。実装そのもの (sort-strategy の実運用 coder ループ) は本タスクの範囲外、
  別タスクへ繰延 (規律5)。
- **axis-proposer の恒真提案検出に機械 backstop が無い (段 8a、D47 必須条件 2、規律 3 の見送り)**:
  提案の fails-closed 検査はフィールド存在検査のみで (n=1 の手動運用ではこの検査は信頼中核が
  提案の消費前に実行し、欠落は差し戻す — 「機械」検査になるのは 8c の駆動配管が載ってから。
  実体化検証 2026-07-10 の指摘)、mechanism_hypothesis の実質性 (恒真で
  ないか・attribution 実在項目に論理的に繋がるか) は人間 gate の意味判断に依存する。機械 lint 化は
  自然文の意味検査の恒真化リスク (D30/D45 却下 (b) と同根) のため見送り。**指標 = 恒真提案の
  差し戻し率 (n=1 から記録)、発火条件 = 差し戻しが頻発するなら attribution の構造化 ID 化 +
  提案側の機械参照照合への格上げを検討。** 併せて既知限界 3 点 (主張時に限定表現する): (a) 射影
  内容の選別は手動解釈 (provenance 三点セットで事後検証可能にするのが代償)、(b) 射影者 =
  信頼中核の記憶汚染 (D46 残存リスク (a) と同型)、(c) n=1 出口採点の射影者からの分離が運用上
  不能な場合は自己採点バイアスが残る (分離不能時は provenance 記録)。
