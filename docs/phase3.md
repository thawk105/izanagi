# Phase 3 — workload 特化ハイブリッド合成 (planner/coder/auditor)

**目的:** roadmap §2 の **コード粒度の空間外合成 (b1) + bounded machine search** を結び、workload
descriptor に応じて certified な CC variant を選ぶ。CCBench コードの `EVOLVE-BLOCK` 領域を LLM (coder) が
diff で書く一方、列挙可能な軸内は機械探索へ渡す。P2-4 backoff は成立例、P2-5 の negative result
(有限フラグ空間で LLM 誘導は機械探索を上回らない) はこの役割分担の根拠である。

**研究目標 (roadmap §1):** 新規 variant の実証を目指すが、証拠が支持しなければ stock / tie を選び、
判断根拠と全試行を proof chain 付きで返す。

**各 run の正直な出力契約:** 証拠が支持すれば certified な新 variant、支持しなければ stock 選択または
tie 判定 + evidence-bound な層3材料レポート + 全試行台帳を返す。stock/tie は有効な no-improvement
結果だが「新しい CC」という研究目標の達成には数えない。LLM 固有の優越は別のアブレーションでのみ主張する。

**設計の出所:** 多エージェント workflow (Map5→Design→Critique3→Finalize) + 敵対的安全検証で kickoff を固め、
ユーザー承認 (2026-06-29)。decisions D22。**絶対規律 (特に 1/2/3/5/6) はここで初めて load-bearing になる**
(LLM が正しさを破りうるコードを書く)。

## 現行チェックポイント (2026-07-18 更新)

- safe variant loop、軸 onboarding、軸提案のループ内化 (8a) までは成立している。ただし現行の反復は
  人間がセッション間を運ぶ **human-supervised loop** であり、無人の進化探索ではない。
- 旧主実験の主張 S は縮小主張 S' へ後退し、S' も **headline 不成立で確定した** (S-1 本走完走、
  三値判定 = S-1a 不成立 / S-1b 成立。族 4 判定表 2026-07-16 ユーザー承認、最終報告 =
  `output/reports/s_prime_final_report.md`)。主張の S-1/S-2 と、must 表の **S1 trace-hook**・
  verify 構成の **S2** は別物。S' を Phase 3 全体の中心価値には据えない。
- 次の研究上の主経路は **8b workload descriptor + 層3材料レポート**。両者は並行着手できる。
  8c セッション非依存駆動は反復運営が再び律速になると確認した場合、段 7 cross-protocol / b2 移植は
  8b と層3の後に判断する。
- 既知の rr5/rr50/rr95 結果は配線確認・**結果既知の事前登録付き追試** (confirmatory とは呼ばない) にだけ使う。新しい workload 特化主張は、
  結果を見ていない holdout workload/競合条件と全件報告規則を実走前に凍結してから評価する。
- bench-first screening v2 は**実装済み** (2026-07-15、D58。監査 must-fix 対応込み)。positive
  control `backoff-sweep-silo-read-heavy-sweep-6f169f90` で `screen-slower-than-floor` の発火も
  実走確認済み。ablation は初回採用 campaign で設計 insight §5-7 の 4 基準により実施する。適用は
  偵察 sweep と 8b の opt-in に限り、S-1、検証相、LLM loop の評価順は変えない。逐次停止は
  D58 の採用対象に含めず、別設計・別裁定とする。

**現行の着手順:** S-1 計測 gate 閉鎖 → S-1 本走・最終報告、8b 設計発効 (holdout = rr80/rr20)、
8b selector 前半 2 段、holdout freeze 生成 (束縛規則 nearest-read-ratio-v1 ユーザー承認済み、
floor/budget は再実測までの null)、8b 後半 = selector 役 + oracle 評価 driver の実装 (二波監査
反映済み)、層3 renderer v2 + 実レポート、までは完了 — 経緯・commit hash・監査内訳は worklog
2026-07-16 (1)〜(6) と archive を正本とし、ここに再掲しない。
次: (a) ~~§9 再凍結 draft の残り = 項 7〜8 のユーザー承認~~ **完了 (2026-07-16、§9 全 8 項発効。
項 8 = 択 (a) crash 再走なし。A3-3/A3-4/R5 の追加裁定も承認 — 裁定資料 =
`output/insights/2026-07-16_s8b-ruling-package.md`、記録 = §9 承認状態 + worklog (11))**。
前提条件の実装 wave 1 完了 (2026-07-16、worklog (12)): T 層 reservation 台帳 / C 層 status・rc /
R6 強化 (択 a) / S 層 単一 object + git blob 束縛骨格 / R3 runner (at-most-once) / R5 結合
judge / F3 pgrep 修正 — 受入ベクトル V1〜V9 実装済み、s8b 系 222 passed。
wave 2 前半完了 (2026-07-17、worklog 参照): floor protocol 凍結案パッケージ 裁定 F1〜F7
(codex 敵対相談 4 本 47 所見を反映。裁定案 = `output/insights/2026-07-16_s8b-floor-protocol-package.md`、
相談逐語 = 同 `2026-07-16_s8b-floor-protocol-consultations.md`) + formula v1
(`orchestrator/campaign/s8b_floor_stats.py`) + floor driver pilot
(`orchestrator/campaign/s8b_floor_campaign.py`、official mode は承認束縛の §8 裁定まで一律拒否)。
floor protocol パッケージの裁定は 2026-07-18 に完結 (F1〜F7 + B-1/B-2、記録 = §9 承認状態)。
strict v2 verifier wave (F6a 承認束縛 machinery + F7 検証意味論 + manifest per-pair + oracle 結線 +
protocol builder) も実装完了 — **発効なし・実凍結なし** (worklog 2026-07-18 (7) が正本。
逐語・裁定表・追認待ち = `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md`)。
C2-2 検証器本丸 wave も実装完了 (2026-07-18、launch certificate lineage の検証鎖 §8.4 + production
決定化 seam + emitter-bytes fixture + oracle 消費統一) — **発効なし・実凍結なし**。逐語・裁定・実装
結果 = `output/insights/2026-07-18_s8b-c22-consultations.md` §10、worklog 末尾が正本。
**Pegasus env_contract 登録段も完了 (2026-07-19)** — attestation/enforcement 機構一式 + certification
ジョブ実測 (attempt 10 で accepted、CV 1.17%) + registry 登録 (attestation_mode=required)。実機で
確定した運用事実は pegasus-runbook §7.1、経緯の正本 = worklog 末尾 +
`output/insights/2026-07-18_env-contract-pegasus-consultations.md`。
追認リスト 5 項も **2026-07-19 に全項承認済み** (記録 = 同 insights §10.5)。
残 = protocol JSON 実凍結 + 予測封印 →
**floor 実測開始前 gate: §5-(viii) 残存限界 (certificate 前削除・ignored 領域・内容 TOCTOU 等) の一覧をユーザーが読み受諾** →
floor 実測 (既存前提はすべて充足) → v2 候補生成 + 承認 → oracle
実走 (進捗と残課題の正本 = worklog 末尾エントリ)、
(b) floor/budget の再実測 → holdout freeze v2 の再凍結 (それまで oracle driver の run 系が gate
拒否のままなのは設計どおり。実測 env は D59 の env-tag 境界に従う。設計素材 =
`output/insights/2026-07-16_s8b-freeze-v2-design-material.md`)、(c) ~~8b 二波監査の記録の凍結 — 原文全文 (scratchpad 退避分) は消失を確認 (failures F20) したため、
残存証拠 (worklog 要約 + commit 本文 + 回帰テスト) からの再構成 + 消失記録を output/insights へ
凍結する (原文の逐語復元は不能と明記する)~~ **完了 (2026-07-16 — 原文消失を記録し、残存証拠からの
再構成を代替凍結。逐語復元は不能。成果物 = `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md`
+ 第 3 波監査 `2026-07-16_s8b-third-wave-audit.md`、記録 = worklog 2026-07-16 (9)、commit 4bde427)**、(d) 8b + 層3の 1 cycle 後に
必要性を計測して 8c、さらにその後に段 7 / Phase 3.5 を再判断する。

## 読み方 (D35 — セッション開始時に全文を読まない)

- セッション開始時に読むのは 3 箇所だけ: **現行チェックポイント**、**must 表** (`grep -n "^## 現行 Phase 3 must" docs/phase3.md` で位置特定) と、
  **「後続段」リストの開タスク一覧** — `grep -n "^[0-9]\{1,2\}\. \*\*" docs/phase3.md` で番号項の
  タイトル行を列挙し、行頭が `N. **(完了 <日付>)` で始まる完了項を除いたものが開タスク。全文を
  読むのは現行チェックポイントの着手順で選択した現行タスクの項だけとし、選択外の項は未了でも
  読まない (CLAUDE.md「現在地」のクラス 3 導線)。完了/未了の正本はこの後続段リスト (must 表は
  blocking 分類が主で、完了の追記は従)。
- 「残存リスク」節は発火条件付き既知限界の台帳 — セッション開始時には読まず、該当リスクに触れる
  作業時だけ引く。
- 「kickoff の最小スコープ」節の EVOLVE-BLOCK 機構・閉じた領域制約・適用の隔離は**現役の規定** (完了記録ではない)。

---

## 旧主実験の事前登録 — `docs/phase3-main-experiment.md` へ分離 (2026-07-05, D35)

主実験 (後続段 6) の事前登録 = 反証可能な主張・headline 比較 4 対照 (silo stock 最良 / クロスプロトコル
stock 最良 / ランダム変異 / 機械 sweep) とその操作的定義・LLM ablation・統計計画 (floor 流用禁止・
サンプル設計・Holm 補正・天井の不在・deceptive 相当の検証・検証相の配線)・失敗条件 (a)〜(e) は
`docs/phase3-main-experiment.md` に事前登録してある。同文書は元の本文を消さず、既知結果を開示した
日付付き改訂だけを append-only で重ねる契約である。D52 は D50/F 段等の結果を見た後の複合改訂で、
主張 S と「失敗条件 (g) 発火時に S' へ縮小する規則」を固定した。その規則が 2026-07-13 の S-3 棄却で
実際に発火した。一方、8b の workload 特化は旧比較の結果から
独立した新しい主張なので、既知結果を pilot と明示し、未見 holdout・descriptor ablation・全件報告を別の
前向き設計として凍結する。kickoff は旧主実験を満たさなくてよい (別スコープ)。

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
  pin 前進 (D41/D42) に未追随のまま発見された。前進経緯は pin.py docstring と D38/D41 が正本。
  2026-07-12 から literal 再掲は check_docs.py が機械検出する)。
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

## 現行 Phase 3 must と発火条件

| must | kickoff | 根拠 |
|---|---|---|
| **完了群**: H3 hooks / cache_key+variant_id 拡張 / 観測者効果二重検査 / S4 / C1 | **完了・解消済み** | **現役の一次防壁 (方針 A):** 偽 cache hit は cache_key+variant_id digest で、TRACE 混入は観測者効果二重検査 (payload 検査に依存しない diff-of-diffs、buildcache.build 出口 hit/fresh 両経路、fails-closed) で塞ぐ。H3 hooks は最小第二防壁 (D30/D33)。規律3 配線 = S4 (verify-red 構造化 anomaly → abort payload + load_rejections、還流は段 4 で消化)。C1 は worktree 隔離 (`patchharness.checkout()`) で解消、driver 宣言値リテラルは IDENT-1/IDENT-3 により意図的据え置き。詳細・経緯は archive (`phase3-s6-s8a-completed-details.md`) と D30/D33/D34/D37/D40 |
| S2 (certify=perf) | non-blocking (abort>0 確認は完了条件 2 に反映済み) | 純 timing は lock/validation 論理に触れないが、**abort 経路は踏む** — verify で abort≈0 だと合成枝が空振り認証になる (残存リスク節)。abort>0 確認は完了条件 2 に明記済み (前提 = abort 数の WAL 記録タスク)。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) **→ 構成確定済 (2026-07-06、後続段 1 完了・gate 3 点 all_pass、D36)。pipeline 配線も完了 (段 5、D36 決定 4、opt-in = legacy+s2)** |
| S1 (別 protocol trace-hook) | **現状 non-blocking** / 旧 headline 2 復活または段 7 cross-protocol 着手時に発火 | silo 内に閉じる現行 S-1/8b/層3には不要。trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) ため、cross-protocol 比較を復活させる場合は S1 移植か「stock 専用計測経路を規律2 と整合させる設計」のどちらかを先に決める (後続段 6 の休眠タスク (a) / 段 7) |

---

## 後続段 (各々 ablation 点を残して投入)

**段 1〜5 は完了 (2026-07-06〜07-10)。完了記録の詳細 (実装内訳・敵対レビュー・実測値・実機検証手順)
は `docs/archive/phase3-kickoff-stages1-5.md` へ分離 (2026-07-10)** — ここには完了サマリ + 現役情報
(ablation 点・残課題・発火条件) + 正本ポインタのみ残す (完了/未了の正本は本リスト、番号は分離前と不変)。
未了の段の中の完了済みサブ項・段階内訳も、後続作業が参照する現役情報 (裁定・発火条件・正本ポインタ) を
サマリとして残せるなら同手口で分離してよい (2026-07-15 改訂、worklog 2026-07-15 の読書量診断による。
段 6 (h)〜(j)・段 8a・must 表解消済み行の詳細 = `docs/archive/phase3-s6-s8a-completed-details.md`):

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
4. **(完了 2026-07-09) guided 検疫層の diff 検疫拡張 + planner/coder human-supervised loop (4a/4b、当時の呼称「自律ループ」)** — diff 検疫
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
6. **(完了 2026-07-16) 旧主実験の縮小主張 S' を閉じる** — D52 で旧 headline を主張 S に再構成したが、
   S-2 は不成立、S-3 は棄却済みで、帰属依存節を削った S' だけが残った。これは登録済み family を最後まで
   報告するために安価に完走するものであり、roadmap 改訂後の Phase 3 中心価値や「LLM が機械探索を上回る」
   成功条件にはしない。**S-1 が成立しても、適格率次元の発見再現性は未実証のまま**と併記する。

   **S-1 closure checklist (未チェックを上から実施):**
   - [x] 独立再命名 canary の人間追認
   - [x] S-2/S-3 提案ラウンド、凍結集計、reason 監査、報告文言の確定
   - [x] サンプル設計 4 点の数値を事前登録へ追記し、独立レビューする (v2 承認 2026-07-15、
     検定単位 = 独立セッション (S-1 限定) を含め発効。裁定台帳 = 2026-07-15_s1-sample-design)
   - [x] S-1 直接比較 driver、既知軸基準点の machine-readable freeze、計測 freeze generator、
     層別統計、report 判定系を実装する (2026-07-15)。freeze **実体の生成・commit は未了**
   - [x] 検証相 (seed×N・長 extime) の extime 校正 driver を実装する (2026-07-15)。校正の**実走と
     確定値の事前登録追記は未了**
   - [x] sort read-heavy 欠測を補い、対象別 between-run floor を再実測する (2026-07-16、
     floor campaign 144/144 = 18 セル × 8 標本)
   - [x] S-1 本走、再測を完走し report を生成する (2026-07-16、develop v2 → floor → block1 →
     block2 全 success、report = `output/reports/s1_direct_comparison/`。三値判定 = S-1a 不成立 /
     S-1b 成立。開発相 v1 は driver 実体化バグで 3 セル abandoned → 修正 d2a46f1 後に v2 で
     完全再走、経緯は failures.md F19)
   - [x] Holm 族 4 全体の裁定と S' 報告文言を人間確認で確定する (2026-07-16 判定表ユーザー承認 =
     S' headline 不成立で確定、最終報告 = `output/reports/s_prime_final_report.md`、worklog 2026-07-16 (2))

   正本は canary = `output/insights/2026-07-13_s6-canary-rename.md`、提案ラウンド =
   `output/s6-rounds/`、内容分析 = `output/insights/2026-07-13_s6-rounds-content-analysis.md`、
   確定文言 = `output/insights/2026-07-13_s6-report-language.md`、棚卸し = worklog 2026-07-13 (11)。
   Holm 上界により S-2/S-3 の非有意は S-1 の結果に依存せず確定しており、族判定表は S-1 三値判定
   (S-1a 不成立 / S-1b 成立) を受けて 2026-07-16 に完成・ユーザー承認済み。

   以下の前提タスク台帳は旧 headline の契約を保存する。(a)〜(e) は旧 headline を復活させない限り休眠、
   (f)(g) は上の S-1 checklist で現役、(h)〜(j) は完了済み:
   (a) **S1 移植 or stock 専用計測経路の設計判断** (headline 2 の前提。must 表参照。
   D44 注意: stock 専用計測経路を選ぶ場合、対抗馬だけ certified 要件を免除する非対称比較になる — その扱いを
   設計時に明文化する)、
   (b) SPACES への mocc/tictoc/cicada 登録 + protocol 別 calibration + between-run floor の対象別再実測、
   (c) ランダム変異生成器と生成分布の確定 (ベースライン 3)、(d) 機械 sweep 駆動と軸命名手順の固定 (ベースライン 4。
   phase3-main-experiment.md 2026-07-10 追記の sweep-matched / sweep-ceiling 分離に従う)、
   (e) coder リーク制御 (P2-5/D21 の Phase 3 版) の実体化、(f) 検証相 (seed×N・長 extime) の実装、
   (g) サンプル設計 4 点の数値確定 (統計計画の節)、
   (h) **(完了 2026-07-10、D45) planner→coder 経路のリーク遮断 (D44、headline の前提条件)** — planner-v4 を
   tools:[] 化 (Read 剥奪 = file-read 経路を coder (D39 決定7) と同型に構造遮断。入力はメインセッションの
   射影 inline JSON)。文書地雷 4 点の除去/中和を含む実施内訳は archive
   (`phase3-s6-s8a-completed-details.md`)。**遮断は Read 経路に限る** — justification 自然文経路・射影の
   自己規律は残存リスク節に維持 (現役)。正本 = D45、
   (i) **(完了 2026-07-10、D46) sort 軸の機械 sweep 先行実測 (D44、安価な先取り)** — comparator 空間を
   構文契約から機械列挙 (15 候補 + stock、全点 SWO 構成的保証) し、balanced/write-heavy 全点を偵察
   (preliminary、事前登録外カテゴリ — 正式 grid への firewall を明文化)。32+6 点全 certified・anomaly 0
   だが **sort 軸に「順序の質」由来の floor 超地形は見当たらず、軸選定の見直し (段 8a 前倒し) で決着済み**。
   実測内訳は archive (`phase3-s6-s8a-completed-details.md`)。正本 = D46・
   `output/insights/2026-07-10_s6-sort-sweep-preliminary.md`・`orchestrator/campaign/s6_sort_sweep.py`、
   (j) **(完了 2026-07-10) related-work の欠落埋め (D44)** — Web 調査 5 レンズ + 書誌の独立機械検証を経て
   related-work/README.md §7.1/7.2 へ反映 (OtterTune 系・learned DB components 系の系譜エントリ新設、
   AlphaEvolve/FunSearch/OpenEvolve の一次資料確定、CCaaLF→NeurCC 改名 + SIGMOD 2026 採択の反映)。
   調査内訳は archive (`phase3-s6-s8a-completed-details.md`)。**Polyjuice/NeurCC 実測比較は見送りで決着 —
   再判断の発火条件 = 「学習型 CC を定量的に上回る」の headline 昇格時のみ** (ユーザー協議、worklog
   2026-07-10 (9)、材料は worklog 2026-07-10 (8))。生データ =
   `docs/related-work/literature-map/gap-research-2026-07-10.md`。
7. **(8b + 層3の後に再判断) cross-protocol 最適化移植 + カタログ化** — roadmap §2 層2(b) の当初案
   「他 CC の最適化を CCBench コーパスから移植する」+「最適化カタログ化 (前提/効果/競合の三つ組、I5 対策)」は、
   **workload descriptor と evidence-bound report の最小 E2E を先に成立させた後の拡張**として
   ここに予約する (a' 方針、D32)。根拠 = 非対称性: 空間外合成には P2-4 の成立例がある一方、**移植の価値は未検証仮説** (I5 =
   「異なる実装の混合は不適切」という CCBench 著者の警告 + 他 CC のメタデータ前提を持ち込む正しさ攻撃面) なので、
   現行 Silo 内でシステム主張を成立させてから投資判断する (規律5 / P2-5 の教訓 = 仮説に工数を先払いしない)。着手時の
   一歩目は**カタログ化の試作 1 枚** (他 CC の最適化 1 つを「前提/効果/競合」でカード化し、移植先で前提が満たせるかを
   判定) で、本格投資はその結果で決める。cicada/oze への空間拡大 (S1 移植を伴う) と束ねるのが自然。カタログ化の
   成果物は移植を見送っても層3 の説明生成に流用できるため無駄にならない。
8. **探索側を防壁の水準へ引き上げる 3 機構 (8a 完了、8b 進行中、8c は条件付き)** — 外部評価
   (worklog 2026-07-10 (3)) が特定した「CC 自動合成の主張と機構のギャップ」への対策。各々着手時に
   リスクに応じてレビューする。新しい統計主張・不可逆な決定は D41 相当の 3 レンズ、可逆な schema/文言は
   1 レンズまたは事後監査、反復可能な整合検査は機械 lint とする (worklog 2026-07-14 (3))。これはレビュー
   資源の配分であり、correctness/identity/measurement gate は一切緩めない:
   - **(8a 完了 2026-07-12) 軸提案のループ内化 (前倒し決着 — sort 軸 iteration 2 見送りの代替本筋、
     worklog 2026-07-10 (10))** — critic の機序帰属から次の変異軸候補 (EVOLVE-BLOCK hole の位置と骨格)
     を提案する axis-proposer を新設し (人間は承認 gate としてのみ関与)、採用軸 silo-backoff-trigger-gating
     を段階 B〜F (シート独立再導出 → 骨格 patch + positive control → 機械 sweep 偵察 → E 段 driver 実装 →
     実 LLM iteration 1〜2 E2E 両 certified・auditor pass・provenance 全 entry 記録) で完走 — 軸提案から
     探索までループ内で閉じた初の軸。偵察 (D50) で floor 超地形が 3 workload とも cross-run 再現
     (best vs ident_all: balanced +84.5%/+91.0%、write-heavy +61.2%/+61.3%、read-heavy +98.9%/+98.7%)。
     設計・実装・実測・裁定台帳の詳細は `docs/archive/phase3-s6-s8a-completed-details.md` へ分離
     (2026-07-15)。**現役の規定・発火条件:**
     - 役の常設定義 = `docs/agent-architecture.md` §axis-proposer + `.claude/agents/axis-proposer.md`。
       軸オンボーディング手順テンプレ = `docs/axis-onboarding.md`。いずれも完了記録でなく現役の規定
     - **8a 由来軸は当面「探索補助」限定で段 6 headline の対象軸にしない** (事前登録の命名固定と
       原理的に非両立のため、D47 決定 5)
     - **2026-07-14 裁定:** 低競合動作点 (records=100k/threads=4、abort 約 2.3%、critic 帰属は両
       iteration ともノイズ内 tie) での性能探索はクローズし、単独の再ホストはしない。高競合で再利用
       するなら、結果既知の追試でなく 8b 前向き設計へ統合する。auditor proposed_tests は軸を再利用
       するときだけ採否を再開する
     - 観測継続項目: 軸提案の既開通領域への偏り (n=1 で提案 3/3 が transaction.cc — 開通・未開通対称の
       地図でも bias が消えなかった)。次回 n を増やすときに観測を継続する
     - 正本 = D47〜D51・`docs/phase3-s8a-trigger-runbook.md`・checkpoint campaign
       `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` (最終成果物)・
       `orchestrator/campaign/axis_trigger_gating.py`・`auditor_gate.py`・`p3_s4_loop_trigger_gating.py`
   - **(8b 着手済み — 現在地・着手順は現行チェックポイントが正本) workload 次元のループ入力化 (次の主経路)** — 「ワークロード特化」のシステム主張に必須。
     coder / selector への入力に型付き workload descriptor (read/write 比率、競合ラベル、スケール、目的、
     正しさ制約。勝者名と実測性能値は除外) を追加し、同一 variant 集合を同一予算で比較する。
     既存 rr5/rr50/rr95 と D50/P2-4 の結果はすでに既知なので、**配線 demo または結果既知の
     事前登録付き追試 (confirmatory とは呼ばない) にしか使わない**。新しい科学的主張には次を実走前に凍結する:
     - **selector 実験:** 固定 variant 集合から descriptor 条件付きで選ぶ。これは workload-aware selection を
       検査するが、descriptor-conditioned synthesis の証拠には数えない
     - **generation/search 実験:** proposal/search 開始前に descriptor を与え、on/off または swapped 対照を置く。
       「ワークロード特化合成」の主張にはこちらが必要

     1. 結果を見ていない holdout workload/競合条件と除外不能な全件報告規則
     2. descriptor on/off と、必要に応じ blind/swapped descriptor 対照
     3. variant 集合、探索予算、correctness gate、対象別 floor、選択規則
     4. 「異なる勝者」だけでなく descriptor が選択を駆動したと判定する基準

     高競合動作点で 8a 軸を再利用する場合もこの設計に含め、既知 rr 比率の winner switching を新発見として
     数えない。D50 の機械 sweep は pilot/既知証拠であり、将来の自動システム成果へ遡及的に再分類しない。
     bench-first screening v2 は D58 の範囲で実装済み (監査 must-fix 対応込み)。positive control
     `backoff-sweep-silo-read-heavy-sweep-6f169f90` で `screen-slower-than-floor` の発火を実走確認済みで、
     初回採用 campaign では設計 insight §5-7 の 4 基準により ablation を行う。reconnaissance/8b へだけ
     opt-in できる。計測反復・検証 seed 数の逐次停止 (Best-of-∞ 型の適応的打ち切り、related-work §7.2) は
     D58 の対象外で、別設計・別裁定のまま据え置く。将来採用しても偵察 sweep / 8b の opt-in に限り、
     S-1 の事前登録済みサンプル設計には適用せず、採否判定の between-run floor 丸め
     (roadmap §3.6(4)) は変えない。
   - **(8c 未着手・条件付き) 駆動のセッション非依存化** — planner/coder/auditor を orchestrator から
     呼び、checkpoint・budget・再開を Python 側が所有する。過去には build/verify よりセッション運営が遅かったが、
     8b の前向き設計と層3最小 E2E を 1 cycle 回してなお反復運営が律速なら実装する。単発の workload
     descriptor 配線やレポート生成を先送りしてまで先に作らない。実装しない間は human-supervised scope に
     留まり、究極ゴールの unattended/autonomous 達成を主張しない。8c で orchestrator が所有する予算の第一単位は
     **ベンチ実時間 (秒)**、LLM 呼び出し回数は第二軸とする。Vesper のトークン予算終了基準は直輸入しない —
     Izanagi の律速資源はトークンでなくベンチ実時間であり、ベンチは排他実行のため並列化で回収できない
     (related-work §7.2)。
9. **層3材料レポート (事実層は v2 まで完了、機序仮説層は設計凍結済み)** — 最小完了条件は
   2026-07-16 消化 (renderer 15d9e7c + 実レポート 24202e2)。同日 v2 で対象拡大: loop_state 非
   保持の sweep campaign 対応 (whiteboard_provenance)、floor の workload 込み within/between
   二種照合、abort stage 射影を追加し、p3-s8a-trigger-sweep 系 6 campaign の実レポートを生成
   した。bench-first screening campaign (D58 の `screening` payload) は対象外のまま (拡張時は
   schema 再凍結)。機序仮説層の原料配線は
   `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` に設計を凍結し、実装は v3
   (次の loop 再走と同時) に繰延。以下は当初仕様の正本:
   WAL/proof chain から次を決定論的に結ぶ renderer を作る:
   workload descriptor、selected/baseline identity、verifier/seed/trace provenance、性能分布と floor、
   採用・棄却・差なし、leading indicators + diff に基づく機序仮説、artifact 参照。機序仮説層の原料として、
   coder/critic の構造化出力に含まれる「なぜ効くと考えたか」(アプローチと根拠) を WAL から決定論的に拾って載せ、
   事実層 (数値・verdict・参照) との分離を保つ。これは形式の強制より鍵概念の言語化が成否を分けた D2I の事例研究に
   よる外部補強である (related-work §7.5)。アブレーションのない説明は因果でなく仮説と表示し、改善が立証できなければ
   stock/tie を出す。事実層は機械的な完全射影、LLM を使う仮説層は別区画とし、数値・verdict・参照を LLM に作文させない。

   **最小完了条件:** 新しい計測を行わず、既存 campaign 1 件について WAL + whiteboard の全 run・全 reject、
   noise floor、環境タグ、variant/source identity、artifact 参照を漏れなく schema 検証済みレポートへ再生成する。
   WAL event ID / whiteboard item ID (ID がなければ canonical record hash) の入力 multiset と、レポートの
   source-ref multiset が完全一致する双射検査を持つ。件数一致だけでは不可。未知 event 種別、重複、脱落、
   参照不能は fails-closed とし、全 claim の参照先が存在し、同じ入力から同じ事実層を再生成できる。
   operational な selected/stock/tie は凍結規則の機械適用結果として記録してよいが、研究としての成功・新規性を
   自動判定しない。論文 prose の自動生成は対象外 (roadmap §2 層3 / D12 の 2026-07-14 協議追記)。

---

## 見送り台帳 (旧「次の一手」の任意項 — 意図的な見送りとして明示)

worklog の過去エントリの「次の一手」に載ったまま現行正本 (worklog 末尾・本文書) に引き継がれなかった任意項。
worklog 全読しないと発掘できない状態を解消するためここに台帳化する (2026-07-05)。**着手義務はない** —
拾うときは該当タスクに昇格させ、捨てるときは理由をここに書く:

### 正しさ・防壁系

- **trigger-loop runbook の verify abort>0 確認** (B-002, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — trigger-loop runbook を再利用し abort>0 gate が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **critic digest への unstable / CV 伝搬** (B-006, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — critic loop が承認され安定性が次提案を左右するのに digest field が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **Gate1 √2 閾値意味論** (B-007, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — Gate1 比較を認証主張に使い √2 意味論が未追認の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **fresh background session での guard_agent 再検証** (B-008, 出所 `docs/worklog.md`) — 新しい background job session の開始時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **guard_agent 防衛候補の裁定** (B-009, 出所 `docs/worklog.md`) — B-008 の再検証で model 無し spawn が通った時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **fairness allowlist 反転** (B-010, 出所 `output/insights/2026-07-12_strategy-review-headline-axis.md`) — sort-strategy が headline 候補となり fairness 字句規則が allowlist でない時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **間接 thid_ gallery 追記** (B-058, 出所 `output/insights/2026-07-12_strategy-review-headline-axis.md`) — sort-strategy が headline 候補となり間接 address 型 fixture が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **range predicate の P record** (B-028, 出所 `output/insights/2026-06-18_phantom-predicate-out-of-scope.md`) — range/predicate workload を承認し trace schema に P record が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **predicate anti-dependency 検出** (B-029, 出所 `output/insights/2026-06-18_phantom-predicate-out-of-scope.md`) — B-028 が発火し predicate rw 検出が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

### 研究・計測系

- **balanced での backoff profile 対照** (B-011, 出所 `docs/phase3.md`) — balanced を凍結機序 profile に含め qualifying rr50 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **over-throttle 有用 IPC 低下の機序分離** (B-012, 出所 `docs/phase3.md`) — MLP または cache 余熱への因果帰属を対外説明・consumer が採る時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **mocc trace-hook / verifier 第2 protocol** (B-013, 出所 `docs/phase3.md`) — 旧 headline 2 / 段 7 cross-protocol で mocc を採る時、または visible-invisible correctness ablation を承認した時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **ermia cross-check の再定義 (前提消滅・要再定義)** (B-014, 出所 `docs/phase3.md`) — si と ermia を cross-check protocol 集合へ再採用する時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **calibration 下限 K 感度** (B-015, 出所 `docs/archive/worklog-phase1-2.md`) — 裁定 2026-07-19: K=4 を設計定数として明示承認し、感度主張は行わず終了。論文の機序図または K=4 依存主張の凍結直前に再評価、証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **thread 数変更時の再 calibration** (B-016, 出所 `docs/archive/worklog-phase1-2.md`) — 承認 performance thread に qualifying calibration が無く live floor carrier も無い時。裁定 2026-07-19 保留承認、between-run floor は現行チェックポイントの floor 実測工程が部分的に運ぶ。述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **Threats to Validity の集約** (B-017, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 対外 claim set の凍結直前に限界索引が未集約の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **backoff +38%/+11% の別 boot 再現** (B-018, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 当該値を対外主張へ採り別 boot 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **critic 軸提案の再現率測定** (B-019, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — critic 提案の再現性を claim / gate に使い replay report が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **backoff 再現の rounds≥3** (B-020, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — cross-round 再現性を主張し qualifying round が 3 未満の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **stock 第2・3位 base 上の fix5/fix10 一般性** (B-021, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — stock base 横断の改善を主張し第2・3位 base 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **backoff 動作点 thread/skew/records 拡張** (B-022, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — 単一点を越える動作領域を主張し登録 sweep が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **backoff ピーク位置 fix2/3/5/7 reps≥15** (B-023, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — backoff peak を名指す主張に qualifying grid が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **待ち方と待ち量の直交化 (SMT 分離)** (B-024, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — wait shape / amount へ因果帰属し直交 SMT ablation が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **backoff rmw=1 一点測定** (B-025, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — backoff claim を rmw=true まで広げ qualifying point が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **calibration maxrss 固定オーバヘッド控除** (B-026, 出所 `output/insights/2026-06-18_calibration-no-cache-miss-saturation.md`) — 固定 overhead が maxrss の 5%以上で控除により selected N が変わる時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **calibration sweep の 1m 未満拡張** (B-027, 出所 `output/insights/2026-06-18_calibration-no-cache-miss-saturation.md`) — K 感度の再評価で左打切りが示され最小測定点が 1m の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **axis-proposer 用の既存軸台帳** (B-030, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 発火述語は未定義で、入力文書・axis/hole 集合・review 失敗判定の定義時に再評価。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **共有相手決定時の review snapshot** (B-031, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 外部研究相手と問いを凍結し curated snapshot が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

### プロセス文書系

- **CLAUDE.md 作業手順 5 への provenance pointer 配線** (B-032, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — hot path への provenance pointer を承認し現行導線に無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **workflow 要旨返し規律** (B-059, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — workflow 出力を context 境界越しに使い必須 summary schema が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **fan-out 3 本以上の multi-agent 規則** (B-033, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 比較可能な 5 run 以上で独立 task が 3 未満かつ起動・統合・手戻り時間が並列短縮を上回る時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **ultracode 常時オンの見直し** (B-034, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 既定利用が rate/cost 制約を生むか監査品質差を実測した時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **Codex runtime の nested tool exact allowlist** (B-036, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — native runtime 再開をユーザーが承認し exact allowlist または denied-event E2E が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **Codex hook adapter と parity test** (B-037, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 安定した Codex tool-input contract が得られ parity test が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **07-12 (6) の無名「ほか should-fix」** (B-039, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 一次資料から未包含の named should-fix が復元された時。裁定 2026-07-19 保留承認 (現状は裏取り不能)、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **S6 盲検で入力構成への言及禁止** (B-040, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 新しい blind proposal 設計で入力構成への言及禁止が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **S6 c1「軸」定義の明文化** (B-041, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — c1 / axis を rubric で再利用し作用点と政策集合の意味論が未固定の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **Phase 1〜2 failures 4 件の回収** (B-042, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 新 review が Phase 1/2 または該当 failure path を対象にし 4 件が未索引の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **新 workflow 起動前の model lint 継続規則** (B-043, 出所 `docs/worklog.md`) — workflow script を追加・変更し候補へ model lint を未実行の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

### 外部環境系

- **資金提供元回答の送付判断** (B-044, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 回答がなお期待され承認文面があり送付確認が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **ソルバ・量子質問への回答作成** (B-045, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 質問がなお open で現行回答が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **他マシン clone の reset / reclone** (B-046, 出所 `docs/worklog.md`) — rewrite 前 history を含む clone を再利用する時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **GitHub PR 本文の session URL 監査** (B-047, 出所 `docs/worklog.md`) — GitHub 接続と対象 PR があり URL 監査記録が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **GitHub refs/pull の Support GC** (B-048, 出所 `docs/worklog.md`) — 物理消去を要求し refs/pull が旧 object を保持して Support 処置が未完の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **fetch --prune 後の tracking ref 最終整合** (B-049, 出所 `docs/worklog.md`) — 実 fetch --prune の実行直前に、実行後の最終 tracking-ref 検査が未設定の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

### テスト衛生

- **survey #6 ratified_verify git fixture 共有化** (B-055, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — 同一 runner/env の全走が 180 秒を超える時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **survey #7 coverage 観測 (X5 派生)** (B-056, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — 新 test-hygiene wave または safety gate 変更時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- **survey #7 差分 mutation 標準化 (X5 派生)** (B-057, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — validator / reject gate 変更または escaped defect 観測時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

### 裁定・完了記録

- **D39 決定 1 の wording 訂正** (B-035, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 裁定 2026-07-19: 独立検証性低下を明記する erratum として D39 へ反映。証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **locked strategy-review-freeze worktree 残骸** (B-038, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 裁定 2026-07-19: 現物不在・過去の処分証拠なしを terminal 記録。証拠と証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **user settings の model=fable→opus** (B-050, 出所 `docs/worklog.md`) — 裁定 2026-07-19: fable 既定の継続は意図的として終了し、opus は監査・統合時だけ個別指定。証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **writable 環境で全走 3 連続 rc=0** (B-054, 出所 `docs/worklog.md`) — 裁定 2026-07-19: 3 走各 1899 passed と commit ancestry を根拠に完了記録。証拠と証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **(完了 2026-07-15) ftruncate-xor insight の還元判断欄の追随** (worklog 2026-07-10 (19) 由来) —
  ユーザー承認を受け、insight (2026-06-19) に WAL ftruncate XOR の PR #116 master マージ完了を
  日付付きで追記訂正した。別件 ODR 違反の PR #118 と合わせ、探索由来の上流還元 2 件が完了済み。
- **(完了 2026-07-17) buildcache 残骸破棄の結線統合テスト** (2026-07-11 監査 L2-2 由来) — fc4d3fa の回帰テスト 2 本は helper 単体のみで、build() が configure 前に破棄を呼ぶ結線を assert しない。結線だけ外れる将来 refactor への歯として統合テスト 1 本の余地。
  `test_buildcache_stale_marker_discarded_before_configure` (orchestrator/tests/test_campaign.py) を追加し、
  build() が configure 前に残骸破棄を呼ぶ結線と `["configure", "build"]` の呼び出し順序を固定した。

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
