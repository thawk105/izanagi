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

## 現行チェックポイント (2026-07-25 更新)

- [x] [T-2514] A-1条件関門の拒否時detail保存を実装 (2026-09-10、D1936項4・D1912)。
  生成済み全arm recordとadmissionをworkload別raw_rootへ保存し、受理集合・元の拒否・成功経路を維持する。
  記録 = `output/insights/2026-09-10_t2514-a1-detail/README.md`。

- safe variant loop、軸 onboarding、軸提案のループ内化 (8a) までは成立している。反復の駆動は
  2 種類ある — 主経路 (8a 軸の探索・S 系実験) は依然として**人間がセッション間を運ぶ
  human-supervised loop** であり、無人の進化探索ではない。一方 8c の bounded MVP
  (`p3_autonomous_workload_trial.py`、D106、[T-207] で 2026-08-01 取り込み) は
  trigger-gating 1 軸に限って **Python が iteration 間を運ぶ**。後者も
  build 手前までの配線実証であり、project 全体の unattended/autonomous 達成は主張しない。
- 旧主実験の主張 S は縮小主張 S' へ後退し、S' も **headline 不成立で確定した** (S-1 本走完走、
  三値判定 = S-1a 不成立 / S-1b 成立。族 4 判定表 2026-07-16 ユーザー承認、最終報告 =
  `output/reports/s_prime_final_report.md`)。主張の S-1/S-2 と、must 表の **S1 trace-hook**・
  verify 構成の **S2** は別物。S' を Phase 3 全体の中心価値には据えない。
- 次の研究上の主経路は **8b workload descriptor + 層3材料レポート**。両者は並行着手できる。
  8c セッション非依存駆動は「反復運営が再び律速なら着手」の条件付きだったが、
  **ユーザーの優先度変更により条件を待たず bounded MVP を先に実装した** (D106)。
  正式実験 (H1/H2 × on/off/swapped) と crash resume は未完で、ここは条件が外れていない。
  段 7 cross-protocol / b2 移植は 8b と層3の後に判断する。
- 既知の rr5/rr50/rr95 結果は配線確認・**結果既知の事前登録付き追試** (confirmatory とは呼ばない) にだけ使う。新しい workload 特化主張は、
  結果を見ていない holdout workload/競合条件と全件報告規則を実走前に凍結してから評価する。
- bench-first screening v2 は**実装済み** (2026-07-15、D58。監査 must-fix 対応込み)。positive
  control `backoff-sweep-silo-read-heavy-sweep-6f169f90` で `screen-slower-than-floor` の発火も
  実走確認済み。ablation は初回採用 campaign で設計 insight §5-7 の 4 基準により実施する。適用は
  偵察 sweep と 8b の opt-in に限り、S-1、検証相、LLM loop の評価順は変えない。逐次停止 v2 は
  D58 と別に 2026-07-27 採用済みだが、2026-07-29 の実装 preflight で source eligibility /
  qualification / formal authority の未見 blocker が判明した。ユーザー再裁定で
  **qualification-first amendment** を採用し、headline 昇格不能な専用系列の live control と
  machine-readable receipt を先行する。production gate / authoritative consumer は証拠取得後の
  別 wave とし、現時点は実装待ち。正本 =
  `output/insights/2026-07-29_t126-implementation-preflight.md`、記録 = worklog (62)。

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

**2026-07-22 改訂 ([T-083] 裁定 = 最短復帰案 (a) 採用):** [T-080] W-0→W-f の全完了を floor 実測の
前提から外す。プロセス系 (supervisor real 開放・dev-wave 自己改善・task-run 拡張・[T-082] 全 caller
移行・新規裁定パッケージ化) は 8b + 層3 の 1 cycle 完走まで freeze し、新規 T 番号は「実走を不可能に
する blocker」に限る。
**2026-07-26 改訂 ([T-115] 裁定 = (a) 採用):** この freeze の解除条件を「1 cycle 完走」から
**「[T-088] の実行 (= 床値実測の開始)」**へ付け替える。凍結の目的は測定への交絡回避であり、
測定が始まっていない間は交絡が生じない。よって **[T-088] 実行までは freeze を解除**し、実測開始後に
再び効かせる。解除されるのは**本番コードに触らない**プロセス系 ([T-009] / [T-060] / [T-012] /
dev-wave 自己改善 / 新規裁定パッケージ化) であり、本番コードに触る項 ([T-082] / [T-089] / [T-090] /
[T-102] / [T-105] / [T-112]) は `DW-G02` (初回 cycle 前 hardening の限定) が別途生きるため
引き続き測定後に回す。新規 T 番号を blocker に限る制限も解除する。次の実装 wave = **一回限りの移行契約** (freeze gate 復旧の最小抽出 — dangling
ancestry の typed 化、D73 の ccbench_pin・機械再構成検査は維持、holdout 二重 drift は人間同席 receipt
で再 pin。[T-068]/[T-077]/[T-078] はここへ統合)。以降は protocol JSON 実凍結 → 予測封印 → [T-011]
受諾 → floor 実測 (**Pegasus 単独** — cygnus は frozen/standby、roadmap §5 可搬性節) → v2 候補生成 +
承認 → oracle 実走 → 層3 実レポート。W 列の恒久一般化 (revocation・expiry・全世代・check registry)
は oracle 後に再開する (承認済み設計 D75/D76 は破棄しない)。正本 = worklog 2026-07-22 (9)、裁定
パッケージ = `output/insights/2026-07-22_direction-audit-recovery-plan.md`。
**移行契約 wave は 2026-07-22 に実装完了 (D78)。人間 receipt は 2026-07-23 に発行済み**
(`8bec195` = ユーザーの `AI-Agent: none` commit、`output/t080-migration/legacy-freeze-repin.receipt.json`)。
発効後の公式 gate 期待 = {floor-null, budget-null} の 2 拒否 exact (実測で確認済み)。
**この R により [T-068] / [T-077] / [T-078] は R 時点で閉鎖済みと確定した** (D78 (10)。機械再確認の
正本 = `output/insights/2026-07-25_t068-t077-t078-closure.md`)。移行契約の発効は official mode の
解禁ではない — official の受理集合は空集合のままである。**protocol JSON 実凍結 + 予測封印の
機構も 2026-07-23 に実装完了 (wave2、D79)** — 人間 CLI (freeze-protocol) と selector 実走配線
(seal CLI) を引き渡し済み。**protocol 実凍結もユーザーが 2026-07-24 に実行済み** (`c8cbd17`。実凍結は
receipt が active-valid でなければ機械拒否されるため、凍結成立自体が receipt 発効の機械証明でもある)。
予測封印実走と [T-011] の §5-(viii) 受諾も完了 (worklog 2026-07-24 (2) / (6))。**D79 (7) のうち
exemption 拡張 + cert 束縛のコード機構は 2026-07-23 に実装完了 (wave3、D80)、統合 E2E は 2026-07-24 に
部分閉鎖 — 残 = lineage 照合 (oracle 結線 wave 再評価)。** **床値の実測は 2026-09-07 の [T-2324] で
固定 official + 明示承認の経路へ入れ替わった** (方式は D926 の submission nonce 束縛。投入 script が
`--mode official` を固定で渡し、実投入に `--confirm-official-floor-run` を要求する。
**起動と API の受理集合はこの時点で変わったが、実投入していないので測定値と freeze / certified の
選択結果は変わっていない。実装の着地は測定認可を兼ねない** (D1641)。2026-08-12 の [T-748] 裁定 (c)
による固定 pilot 経路は、承認束縛が実装されるまでの過渡形だった。pilot 成果物は
`eligible_for_refreeze=false` なので再凍結には使えない)。**再凍結 → oracle → certified を開く gate は依然 official guard 解禁**
([T-088]。設計は 2026-07-25 にユーザー承認済 = D86) → **Pegasus PBS floor wrapper は 2026-07-25 に
実装完了 (D87)、段階 1 は 2026-07-28 に実機で閉鎖** (job 873225 = rc=2 で official guard の実機拒否を
確認。正本 = worklog (33)。qsub の投入規則は F49 (ii) 裁定 (2026-07-29) により「書込永続が実証された
セッション型からの投入 + 直後の有効性検査 (receipt 永続・qstat 可視・会計痕跡)」を許可へ更新 —
規則本文の正本は pegasus runbook §8) → 単一 admission predicate + CLI rc 翻訳 (段階 3・4、未着手)
→ 実行 revision 束縛。

**2026-07-27 改訂 (外部相談を受けたユーザー裁定 8 件):** (1) **スコープを Silo ベースに固定する** —
最適化・組み換え・軽い書き換えの範囲でまず成果を出し、複数プロトコルから選ばせる問題設定は当面
採らない。(2) **8b selector 側の残作業 (床値実測の前提整備・oracle 実走・認証機構の拡張) の優先度を
下げる** — selector の価値は、外部評価・先行研究 Shirakami の設計目標 (「動的プロトコル切り替えを
不要にする」)・本 phase doc 従属文書 `phase3-8b-descriptor-design.md` の自己申告 (「selector 実験は
descriptor-conditioned synthesis の証拠には数えない」) の三方向から独立に下がった。**床値実測は
他候補にも要る測定土台なので廃止ではなく順序の後退**である。(3) **新しい P1 は変異軸の質の転換**
(制御パラメータ水準 → データ構造水準) **と、既知解までの距離で能力を測る評価設計** (劣化版の梯子 /
Shirakami-LTX との中間)。タスク粒度の優先度 (P1/P2/P3) と各項の内容は worklog 末尾の「次の一手」が
正本。裁定の根拠と外部指摘の整理 =
`output/insights/2026-07-27_external-consultation-scope-and-axes.md` (匿名化済み)。
**なお roadmap 本体 (§2 の主経路・§8 のポジショニング) の改訂は本裁定に含まれない** — 必要性が
確認された場合は `docs/roadmap-history/README.md` の改訂セレモニーに従う。

**2026-07-31 改訂 (`/rulings` ユーザー裁定 = 推奨案 (a) 採用):** プロセス系 freeze の解除条件を
2026-07-26 改訂の「[T-088] の実行 (床値実測の開始)」から**「[T-193] の閉鎖」**へ付け替える。2026-07-27 改訂 (2) が床値実測の優先度を下げた結果、freeze が再びかかる条件が
無期延期になり、直近 8 wave が全て道具・運用の整備で研究の測定が 0 本になっていた。付替え後は
当該項の閉鎖直後の 1 wave を**研究側 (2026-07-27 改訂 (3) の変異軸の質の転換と、既知解までの距離で
能力を測る評価設計)** に充てる。対象 ID と進捗の正本は worklog 末尾の「次の一手」、経緯は
worklog 2026-07-31 (74)。本改訂は roadmap 本体と絶対規律を変更しない。

**2026-08-01 改訂 (ユーザー裁定 3 件、[T-209] の閉鎖):** (1) **[T-193] を閉鎖**した — (80) の
「main を正本にする」裁定の執行をもって閉鎖とし、残る accounting footer の `Group Name` exact 束縛は
[T-222] が独立に所有する。(2) **プロセス系 freeze を廃止する (D111)** — 2026-07-22 改訂で導入し
2026-07-26 / 2026-07-31 改訂で解除条件を付け替えてきた freeze は、本改訂をもって恒久に廃止する。
表向きの目的だった「測定への交絡回避」は git の版管理と env-tag / receipt が既に担っており
(F41 = 測定値は測った checkout を併記する、D59 = env-tag 境界)、freeze 自身は prompt 規律であって
機械 gate を持たない (本 wave の実測)。campaign 実行中に道具が動く問題は freeze ではなく本節の
「実行 revision 束縛」で解く。(3) 代わりに**順序付けだけを残す — 直後の 1 wave は研究側 =
[T-144] (スペクトル補間 = Shirakami-LTX との中間)** とする。2026-07-27 改訂 (3) が挙げたもう一方
「変異軸をデータ構造水準へ」は [T-140] が 2026-07-28 に実測して択 (c) (軸の廃止) を適用済みであり、
再開条件は `max_ope` の大きい workload spec を campaign が採用する場合だけである
(一次資料 = `output/insights/2026-07-28_t140-setsize-distribution.md`)。経緯は worklog 2026-08-01 (92)。
以後、2026-07-22 / 2026-07-26 / 2026-07-31 改訂の freeze 条項は履歴として残すが効力を持たない。

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
- **閉じた領域制約:** #if 枝は既存 silo API を呼ぶ straight-line code のみ。ただし `silo-backoff-magnitude` の hole だけは D836 / D901 条項 1 により、初期化子が「value と数値一致する接尾辞なしの数値 literal 1 個」・**ちょうど 1 文**に限定される (受理文法が機械執行)。**#include 追加・新規関数/マクロ
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
- [x] (blocking) source_digest の #include 死角の閉塞 — `assert_includes_match_head` + computed include と
      マクロ文脈乖離の fails-closed 化 `assert_conditional_macros_covered` ([T-148]、D93)
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
| S1 (別 protocol trace-hook) | **現状 non-blocking** / 旧 headline 2 復活または段 7 cross-protocol 着手時に発火 | silo 内に閉じる現行 S-1/8b/層3には不要。trace-hook の無い protocol は verify 不能で COMMIT に到達しない (pipeline.evaluate は verify 必須 → trace-empty abort、fitness が WAL に載らない) 。**成立方法は 2026-08-11 のユーザー裁定で確定済み (T-755 Q1〜Q3 全問 (a)、worklog entry 389)** — trace-hook 移植だけが certified な cross-protocol 比較を成立させる。stock 専用計測経路は非認証の別成果物にしかならず、公式 report・selector・比較表・順位・headline へ入れない (偵察としての解禁も「なし」と裁定)。初手は mocc、trace v2 化を単独 wave で先行。**残るのは裁定ではなく実装** — protocol 別 genome 空間・較正・between-run floor と公式成果物への接続 (後続段 6 の休眠タスク (a) / 段 7) |

---

## 後続段 (各々 ablation 点を残して投入)

- [x] insights の直下過密を日付別配置と旧名索引で解消（2026-09-10）。
  既存資料の内容・固定参照を維持し、深部rawの分割一覧も作成。
  検証記録は `output/insights/2026-09-10/insights-date-layout/README.md`。

- [x] 本体論文の日本語結果・考察草稿（2026-09-10の新規ユーザー執筆依頼）を
  `output/insights/2026-09-10/paper-results-ja/results-discussion.md` に作成。
  取得済みの性能標本・別走行の正しさ・非LLM対照・反例還流の未取得効果を本文と3表で分離した。
  文書成果の完了であり、未landの実験や新規CC合成、Phase 3全体の完了を意味しない。

- [x] rulings 項1・2の人間専任解除を記録し、実行場所分類の手順を AI 担当へ整合した
  (2026-09-10 ユーザー裁定)。T-1998 / T-2557 / T-2267 の測定本体は AI 実行待ちで、
  担当変更は測定完了・認証範囲の拡大を意味しない。手順は `docs/pegasus-runbook.md` §7.0。

- [x] T-2579: D1936項43の限定変更を回収。T1259の実repo snapshotをmodule fixtureへ移し、
  各testへ独立copyを渡し、既存inventory・parent-only・goldenへ登録した。
  production timeout・走査範囲・判定を維持。全worker合計1回や速度改善の主張ではない。
  根拠は `output/insights/2026-09-10_t2579-recovery/README.md`。

- [x] 本体論文の日本語方法節草稿（2026-09-10 の新規ユーザー執筆依頼）を
  `output/insights/2026-09-10/paper-methods-ja/methods.md` と同 `implementation.md` に作成。
  生成・検証・反例還流・独立測定・選択を対応づけ、実装と評価契約を区別した文書成果であり、
  未完の実験や Phase 3 全体の完了を意味しない。

- [x] [T-2340] backoff 単独論文の日本語ストーリーを既着地正典全体から再導出し、
  `docs/paper-story-backoff/2026-09-10.md` に追加した。機序の直接観測・動的化の結果・認証の限定を
  反映した文書成果であり、旧版不変、新規測定・追加認証・本体論文との図表の二重新規利用はない。

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
   **2026-08-12 [T-816]**: 同 driver は自分の歴史 pin (`dff0f1e`、trace v2 以前) から build するため
   出力は v1 形式であり、trace v2 専用化した現行 verifier では correctness leg を再現できない。
   driver と校正値は歴史記録として据え置く (再現するなら trace 形式を v2 へ上げた再 build が要る)。
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
   - [x] 2026-09-10新規依頼の次実験precheckを実装差分ゼロで実施。
     K2新提案1評価→critic→次提案までの最小run-cardと実行側の未充足事項を
     `output/insights/2026-09-10_cc-next-precheck/run-card.md`へ記録。
     現行backoff文法内のパラメータ探索であり、新CC構造の合成・新規実走の完了ではない。
   - [x] [T-2581/T-2548/T-2182] D1936項1・2の新規試行pinを完全SHAへ固定し、直接依存期待値を整合。
     既存verifier v2でK2を1本再投入し、serializable・異常0・1 committedを取得した。
     新campaignだけの判定で過去campaignは再ラベルしない。実測と検査は
     `output/insights/2026-09-10_t2581-k2-pin/README.md`。
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
   (非 SWO comparator) は **[T-316] R2-b の独立 oracle が build 前に閉じた IR への membership で塞ぐ**
   (`orchestrator/campaign/sort_swo_oracle.py`、[T-2145] で受理言語を閉じた 79 値 IR へ縮めた。
   保証は構成的 SWO + 実 TU conformance であり、動的な反例発見器ではなく全入力の証明でもない。
   この縮小は D39 の raw C++ 独立合成の実証点を別実験へ移すが、D344 の実験同一性の論点は
   supersede されていない (D1451)。型 15 fairness の機械観測点は依然として未実装)。実走手順 =
   `docs/phase3-s5-sort-runbook.md`。正本 = D40〜D43・`orchestrator/campaign/p3_s4_loop_sort.py`。
   campaign `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` は oracle 導入前の歴史成果物で再開不可。
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
   (a) **S1 移植の設計判断 — 2026-08-11 ユーザー裁定で決着済み (T-755 Q1〜Q3 全問 (a)、worklog entry 389)**
   (headline 2 の前提。must 表参照。trace v2 単独 wave 先行 → 初手 mocc。stock 専用計測経路は certified 比較を
   成立させないため採らず、偵察としての解禁も「なし」と裁定した。D44 が警告した「対抗馬だけ certified 要件を
   免除する非対称比較」はこの裁定で閉じている)、
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

   **(2026-08-20 TicToc/Cicada タスク分解、段7 発火まで全項目未着手・T 番号なし)** D32 の「一歩目」を
   TicToc/Cicada 2 protocol へ具体化した。[T-109] (2026-07-26、MOCC 対象、3 レンズ全 NO-GO) の
   blocker を今回再実測し、D16 は「一回限りの試作例外」が既に追記済みだが buildcache/source_digest の
   ALLOWLIST は今も silo 専用のままと確認した。技術根拠・precedent 再確認・(P1) 順序推奨の正本は
   `output/insights/2026-08-20_tictoc-cicada-cross-protocol-task-definition.md`:
   - Group A (共有基盤、S1 = native trace-hook strand): (a) buildcache/source_digest の
     protocol-aware 化 (D23 が予約していた繰延先)、(b) SPACES 登録 + protocol 別 calibration/floor
     (段6 dormant (b) と同一項目)、(c) `Integrity.clean()` 非対称ゲート解消設計 (silo 専用 2 カウンタ
     問題)、(d) D16 一回限り試作例外を TicToc/Cicada どちらに使うかの裁定
   - Group B (TicToc、S1 strand): (e) `TsWord` 版 ID の trace-hook 設計、(f) 実装 + positive control
   - Group C (Cicada、S1 strand — cicada は真の多版 MVCC で [T-109] 時点未分析・既存 playbook が
     通用しない構造的新規ケース): (g) MVCC 版管理の feasibility 調査 (カタログ化試作の充当先)、
     (h) ((g) 次第) 実装 + positive control
   - Group D (b2 strand、Group A の blocker を一切踏まない最安の入口): (i) 最適化技法 1 つの
     カタログ化試作 (前提/効果/競合の三つ組、D32 原文どおりの文字通りの一歩目)
   - **(P1) 親の暫定推奨順序 (攻撃対象・ユーザー上書き可):** (i) → (a)(b)(c)(d) → (e)(f)[TicToc] →
     (g) → 分岐[Cicada 着手 or 見送り]。理由 = TicToc は既存 (mocc/silo) playbook に近く低リスク、
     Cicada は playbook 非依存の新規調査が要るため `DW-G03` (族一般化には独立 2 例) の精神で
     2 例目に位置づける。(d) は一方向消費のため着手時に改めて裁定を仰ぐ。

   **(2026-08-21 Group D (i) 試作完了、No-Go)** カタログカード試作 1 枚を実行した。技法 = Cicada の
   commit-streak gated selective precheck (`precheckInValidation()`)。判定 = 現行 Silo の
   EVOLVE-BLOCK 実編集面 (write_set_ ロック順序 comparator + `backoff.hh`) に前提 (per-tuple
   counter・MVCC version chain) が乗らず No-Go (1 事例、全称化しない)。段7 全体の発火条件
   (8b+層3後) はこの結果と無関係に未成立のまま。詳細・見送った候補・今後の芽は
   `output/insights/2026-08-21_cicada-selective-precheck-catalog-card.md`。
8. **探索側を防壁の水準へ引き上げる 3 機構 (8a 完了、8b 進行中、8c は bounded MVP 済み・正式実験と resume は未完)** — 外部評価
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
     - [x] [T-2515] rr5/rr95 の較正投入対応と条件関門の interpreter 修正、既存失敗実測を回収。
       accepted calibration の取得自体は未完。正本 = `output/insights/2026-09-10/t2515-rr95-rr5-calibration/README.md`。
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
     - [x] 床値 result v5 の prefix proof を holdout/ratified consumer へ結線する単位 D2 を実装
       ([T-1851]、2026-09-10)。既存v4受理・凍結23件・FORMULA_IDを維持。実測と統合記録は
       `output/insights/2026-09-10_t1851-unit-d2/README.md`。official実値域の取得は後続C3cに残る。
     - [x] T-2525 / T-2526 (2026-09-10): D1859・D1936 項19に従い、要求側の静的物理量宣言を
       screening へ転送し、T-2418 新走の campaign/report を v2 に整合した。乱択を静的量へ
       変換せず、過去 artifact は保持する。適用範囲は
       `docs/b10-backoff-static-tail-preregistration.md` の 2026-09-10 追補を参照。
   - **(8c bounded MVP 実装済み 2026-07-29、正式実験・resume は未完) 駆動の
     セッション非依存化** — ユーザーの優先度変更を受け、汎用 daemon を先に作らず
     **unattended runner + workload-conditioned generation + 固定 stop + 全件 report** を
     trigger-gating 1 軸へ束ねて最短実装した。
     `orchestrator/campaign/p3_autonomous_workload_trial.py` が planner / coder / auditor /
     critic を headless Claude の fresh・tool-less context で直接呼び、iteration 間の
     descriptor / abstract whiteboard / critic reverse signal を Python が運ぶ。**valid attempt** には
     source role SHA + effective prompt SHA + payload/envelope SHA + session/model/token provenance を
     束縛する (invalid attempt は payload/envelope の path と SHA だけで、provenance は落ちる)。
     各 role は1回・retryなし。固定 generation budget、既存 safe-loop stop、supervisor
     wall 閾値のいずれかで停止し terminal report を書く。performance target による早期停止は
     入れない (Best-of-N / 選択的報告の回避)。

     YCSB A/B/C × 1 generation の fixture no-build は 3/3 dry-pass、実 Claude no-build は
     12/12 role attempt valid・3/3 dry-pass で完走した。初回実 Claude pilot では auditor が
     `list[str]` を返し既存 `list[dict]` gate が 3 cell とも fail-closed にしたため、再試行せず
     partial report を保存し、次 trial で mediated schema を object 配列へ明確化して完走した。
     その出力監査で planner の mechanism 文が coder へ流れうることも検出し、planner→coder 境界を
     `axis/direction/magnitude` 3 field だけに縮退した。運用正本 =
     `docs/phase3-s8c-autonomous-trial-runbook.md`、設計裁定 = D106。
     **2026-08-01 の取り込み ([T-207]) で、起草時の主張と実装の食い違い 6 件を訂正した。**
     一覧の正本は `output/insights/2026-08-01_t207-adoption-audit/README.md` の
     「説明と実装の食い違い 6 件」の表である (`_preview()` の pre-audit 再実装 /
     `max-wall-seconds` が上限でなく境界閾値であること / auditor schema が要素 field まで
     閉じていないこと / auditor payload に common 部も入ること / provenance が valid attempt
     限定であること / 別 run-root でも campaign 状態が再利用されうること)。
     同時に `--provider fixture` + 実 build を fail-closed で拒否した
     (無条件 pass の fixture auditor を実計測経路へ載せない。D106 決定 (6))。
     **規律 3 の還流が human loop より狭い**点は設計択一として未解決であり、
     cross-generation 還流が起きる `--max-generations >= 2` の運転を D106 残余 1 の裁定まで
     禁止する ([T-244])。1 generation/cell は fresh campaign の単一 invocation なら還流が
     起きないため許可する。**2026-08-01 の [T-244] wave (D114) でこの禁止を機械 gate 化した** —
     承認上限 `MAX_APPROVED_GENERATIONS = 1` を CLI・`run_trial()`・`_run_workload()` の 3 入口で
     強制し、`int` サブクラスによる予算偽装を exact 型検査で塞ぎ、最初の provider 呼び出し前に
     campaign checkpoint の freshness を検査する。**機械化したのは予算と freshness だけ**である。
     同じ上限定数は `autonomous_trial_completeness.py` の run-envelope / campaign-chain の
     2 consumer gate も読む。存在しないのは前提条件 10 件と cap-lift receipt の評価器である。
     caller 注入 `providers` (D148) と explicit keyword の `drive` / `preview` 注入
     ([T-244] U-1、2026-08-04) は正式経路の `run_trial()` が artifact 作成前に拒否する。
     拒否できるのは explicit keyword だけ — private sentinel の持込み・module 属性再束縛・
     sentinel を束縛した wrapper / partial・同一 process 実行中の差替えは保証対象外で、
     保存済み artifact からの事後判定もできない。driver 直接反復・並行 start race も
     保証対象外 (D114「保証の限界」)。
     **2026-08-01 の [T-244] 還流設計 wave (D121) で設計 draft を起草した** — ユーザー裁定の軸 (i)
     (機械が failure を単調な safety constraint へ変換し generator は理由を読まない) を主軸、
     軸 (iv) (campaign より上位の origin へ総 iteration・総 query・公開 class を束縛) を併用する。
     軸 (iii) (候補 batch の事前凍結) の必須化は親が決めず裁定へ返し、2026-08-03 に択一 7 件が
     全件裁定され (択一 3 = 必須化)、予算値も 2026-08-04 に裁定された。**方針裁定は済んだが
     cap-lift 可能な設計は完成していない** — P6 の意味的充足と receipt、off アームの予算・
     受理集合の整合、承認上限の機械束縛、D138 が列挙する crash 回復・replicate 数・0 bit 証明が
     未確定または未実装であり、前提条件 10 件のうち満たされているのは
     P10 の 1 件だけである。D114 の承認上限 1 を維持する。設計 draft と裁定パッケージ =
     `output/insights/2026-08-01_t244-reflux-design/`。

     **この完了は「無人で proposal を作り build 手前まで運べる」operational evidence であり、
     workload-conditioned synthesis の科学的主張ではない。** A=rr50/B=rr95 は既知点、C=rr100 は
     read-only negative-control 候補で、全 cell の coder が同じ gate を返しうる。descriptor-on
     だけの rationale 差は因果証拠にならない。次の主経路は (1) A/B/C を 1 generation だけ
     single-tenant live build/legacy+S2/bench で operational pilot、(2) H1 rr80/H2 rr20 ×
     on/off/swapped を同一固定 budget で実装・凍結・実走、の順。MVP 残余は supervisor crash 後の
     in-place resume、axis-proposer、複数軸、正式な bench 実時間 budget accounting。これらが
     閉じるまでは project 全体の究極ゴールに対する unattended/autonomous 達成を主張しない。

     8c で orchestrator が所有する予算の第一単位は
     **ベンチ実時間 (秒)**、LLM 呼び出し回数は第二軸とする。現 MVP の wall budget は前者の
     代替ではない。上限でもなく、次の workload / generation 境界で開始を止める閾値である。Vesper のトークン予算終了基準は直輸入しない —
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

**ID 体系 (D70)**: 生存項目の行頭には worklog「次の一手」と同一体系の安定 ID を付ける
(書式と採番の正本 = `docs/worklog.md` 冒頭「次の一手の ID 規約」)。この台帳は保存則の sink の一つであり、
`tools/check_docs.py` は**この節から「裁定・完了記録」の手前まで**を sink として読む
(完了記録に残った ID が同 ID の脱落を永久に満たす fail-open を避けるため)。
既存の `B-xxx` は 2026-07-19 棚卸しの監査ローカルキーとして**併記のまま残す** — 削除も置換もしない。
terminal な項目 (取り消し線付き・「裁定・完了記録」節) には ID を振らない。

### 正しさ・防壁系

- [T-014] **trigger-loop runbook の verify abort>0 確認** (B-002, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — trigger-loop runbook を再利用し abort>0 gate が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-015] **critic digest への unstable / CV 伝搬** (B-006, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — critic loop が承認され安定性が次提案を左右するのに digest field が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-016] **Gate1 √2 閾値意味論** (B-007, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — Gate1 比較を認証主張に使い √2 意味論が未追認の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- ~~**fresh background session での guard_agent 再検証** (B-008)~~ — **消化 (2026-07-20)**。発火条件 (新規 background job session) が成立しユーザー裁定で実施。daemon 2.1.214 で model 無し `Agent` を probe し **拒否発火・spawn なし** を確認 → 2.1.211 の不発は **version drift** と判定。結果の正本 = `hooks/README.md` hook 4「再検証の結果」+ worklog 2026-07-20 (14)。
- ~~**guard_agent 防衛候補の裁定** (B-009)~~ — **不要化 (2026-07-20)**。価値は B-008 の素通り時にのみ発生する条件付き候補だったが、B-008 が拒否成功のため発生しない。daemon 更新で再 drift した場合に復活しうる。

  (B-008 は 1 点観測のため、daemon の major/minor が上がった新規 background session で同じ probe を再試験する — 手順の正本は `hooks/README.md`。)
- [T-017] **fairness allowlist 反転** (B-010, 出所 `output/insights/2026-07-12_strategy-review-headline-axis.md`) — sort-strategy が headline 候補となり fairness 字句規則が allowlist でない時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-018] **間接 thid_ gallery 追記** (B-058, 出所 `output/insights/2026-07-12_strategy-review-headline-axis.md`) — sort-strategy が headline 候補となり間接 address 型 fixture が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-019] **range predicate の P record** (B-028, 出所 `output/insights/2026-06-18_phantom-predicate-out-of-scope.md`) — range/predicate workload を承認し trace schema に P record が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-020] **predicate anti-dependency 検出** (B-029, 出所 `output/insights/2026-06-18_phantom-predicate-out-of-scope.md`) — B-028 が発火し predicate rw 検出が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

- [T-326] `layer3_report` 本体の深い一致強化 — 理由: (124) の裁定 (b) により**実施しない**。強化は新 verifier 経由だけとし、既存レポートが値の改変を受理する事実は所見として記録に残す。本体側へ着手するには択 (a) の再裁定が要る。
- [T-323] 8c の raw role 出力を追跡するかの方針 — 理由: [T-241] の裁定事項として記録済みで、単独では起票しない。
- [T-302] `_job_run` が子側で env_allowlist を強制していない件 — 理由: [T-250] と同一所見の重複であり、所有を [T-250] に一本化する。
- [T-290] `run_trial` の注入 seam の保証 — 理由: (103) の裁定 (b) で現状維持とし、多世代開放と同時に (c) を入れると決まった。 2026-08-04 の U-1 実装で public run_trial の explicit keyword 注入部分は消化 (直接反復は D114 のとおり保証外のまま)。
- [T-283] 本番開放の前提条件 — 理由: (125) の裁定で [T-246] と同じ束へ入れ、単独では着手しないと決まった。
- [T-285] 予約 block 以外の 7 個の `readarray < <(...)` — 理由: [T-292] と同族で、同じ独立 wave が所有する。
- [T-272] Pegasus shell 3 本の裸 python3 の版数 gate — 理由: (125) の裁定で [T-248] の実装と同じ wave に含めると決まった。 2026-08-04 に floor 実測 wave が発火条件に触れた。certify 経路 (`certify_calibration.sh` / `submit_certify.sh`) には版数 gate が無く、`floor_campaign.sh` だけが持つ非対称が残る。計算ノードの `python3` は 3.9 に解決されるため、3.10+ 構文を持つ module (`env_contract` を含む) を certify 経路から呼ぶ設計は現状すべて失敗する。安価測定の最小 env 化にも同じ壁が掛かる。 2026-08-04 の floor scoping 実測で、裸 python3 の版数に加えて perf 実体のノード個体差 (bnode074 不在 / bnode011・bnode138 実在) も同じ環境 gate の射程だと確定した。scoping 側は job script の preflight (5bec729) で自衛済み、certify 経路は未対応のまま。 2026-08-07 実測 — 「`env_contract` を含む 3.10+ module を certify 経路から呼ぶ設計は現状すべて失敗する」は job 892707 の `calibrate_rc=0` と矛盾する (`calibrator.cli → execution_guard → env_contract` の import は計算ノードで実際に通った)。裸 python の版数 gate 不在という指摘自体は残る。記録のみ、追加裁定なし。
- [T-246] T-126 scope 外の real 所見 4 件 — 理由: (94) の裁定 (b) で、逐次停止を production gate へ昇格させる際の前提条件として束ねると決まった。
- [T-242] `claude_executable_sha256` の allowlist 発火 — 理由: (103) の裁定 (c) で正式系列でだけ発火させると決まり、[T-246] / [T-228] と同じ束に置く。
- [T-197] `exec_calibrate.py` の汎用トランポリン — 理由: (74) の裁定 (b) で sanctioned exact path 列挙のまま置くと決まった。
- [T-198] scheduler-side lease と heartbeat — 理由: (74) の裁定 (b) で入れないと決まり、上限 wall で被害を限定する。
- [T-102] production `_run_git` 2 箇所の ambient env 継承 — 理由: (24) の裁定で [T-096] と同じ wave が所有する。
- [T-122] `verify_receipt` の `search_repository` 重複 — 理由: (24) の裁定で [T-011] の測定後に着手すると決まった。
- [T-103] never-issued 検査 — 理由: (12) の裁定で 1 cycle 後へ先送りと決まった。
- [T-089] 二重 reason-tag 描画 — 理由: (7) の裁定で測定後の hardening と決まり、前倒し対象外である。
- [T-090] `VerifiedFreeze.document` が mutable — 理由: (11) の裁定で測定後の hardening と決まった。
- [T-112] `s1_known_axes_freeze` の root 束縛が不完全 — 理由: (9) の裁定で床値実測の後と決まった。
- [T-114] never-issued の全層 scope 漏れ — 理由: (9) の裁定で一巡後と決まった。
- [T-085] PKG-1 の実装 — 理由: (6) の裁定で floor 実測後の hardening wave と決まった。
- [T-087] post-seal FROZEN_MANIFEST 23 件と恒久設計 12 件の未整合 — 理由: 恒久形 (D75 W-e) の実装時に暫定 pin を撤去して再整合すると記録済みで、それまで発火しない。
- [T-082] 全 caller の移行 — 理由: (10) の裁定で公式 consumer の必要分は充足済み、残りは 1 cycle 後と決まった。

- [T-461] mask と predicate_sha256 の連動改変を検出する 32 点凍結 witness 表 — 理由: 2026-08-05
  ユーザー裁定 (択 (b))。現状は D160 が「検出しない」ことを正直に非主張として記録しており、
  防壁を緩めるものではない。**正式実験で trigger 軸が certified 選択に入る時に再評価する**

- [T-449] **repo 外 cache の同一 UID 敵対者 TOCTOU** — 理由: 裁定 2026-08-11 (境界外宣言): 防御境界に含めない。RP-2 (a) の既裁定と整合。再訪条件 = 信頼モデル自体の見直し (D86 系の再裁定)。
- [T-546] **`git rm --cached` の deletion gate すり抜けと preflight 後 TOCTOU** — 理由: 裁定 2026-08-06: 残余として記録し対策実装はしない。正本 = `output/insights/2026-08-05/t450-t412-preface/README.md` §3 R2。
- [T-560] **publish 済み bytes の別 process verifier + 最終 receipt 束縛** — 理由: 裁定 2026-08-06: 完全形は作らない。同一 process 内再読で足りる (プロトタイプ基準)。
- [T-563] **certification job の immutable snapshot 拡大** — 理由: 裁定 2026-08-06: live worktree bytes 参照を容認する (自 checkout を信頼する。プロトタイプ基準)。
- [T-605] **receipt expectation の top-level structured issue 新設** — 理由: 裁定 2026-08-07 (委任 (a)): 現状の観測経路を受容する (受理集合を変えないため)。根拠 = `output/insights/2026-08-06/t574-world-expansion/README.md` R9。
- [T-608] **`generator_versions` pin の rollover 手順明文化** — 理由: 裁定 2026-08-07 (委任 (a)): 生成器 source bytes の変更が pin を動かすのは設計どおりとし明文化しない (発行済み manifest 0 件、既存受理不変)。同 README R12。
- [T-628] **activation transition の env 集合変化用の別機構** — 理由: 裁定 2026-08-07 (a): 同一 env 集合の世代進行だけを受理し集合変化は永久拒否。別機構は設計しない。再訪条件 = 新 env を実際に追加する実需。
- [T-644] **書込みなし hardware attestation の pre-built probe** — 理由: 裁定 2026-08-08: PBS wrapper の preflight は静的 admission までと明示し別設計は行わない。再訪条件 = 較正運用で最初の書込み前 attestation の実需。
- [T-649] **lease の fencing token / epoch と release 権限証明の nonce 化** — 理由: 裁定 2026-08-08 (D205 委任): 入れない。無くても「本機構が無い場合と同じ競合」までで悪化はしない。再訪条件 = 二重 winner の実害観測、または dev-wave 投入の自動化。
- [T-654] **`dev_wave_land.py` no-touch の byte 不変検査 gate** — 理由: 裁定 2026-08-08 (D205 委任): 所有宣言のままとする。「main land を妨げる検査を作らない」と衝突するため作らない。再訪条件 = no-touch 違反の実害。
- [T-658] **activation receipt の書込み境界への配線** — 理由: 裁定 2026-08-08: 行わない。認可の本丸は sink 必須化 ([T-609]) と contract hash 束縛 ([T-530]) が担い、全書込み口配線は防御的堅牢化 (D205)。再訪条件 = durable receipt の実需。
- [T-703] **receipt publication 後の受理再評価を塞ぐ commit protocol 再設計** — 理由: 裁定 2026-08-09: 行わない (実害未観測の liveness 系、D205)。「最後の可逆点まで」の防御を維持。再訪条件 = 停滞由来の再評価の実観測。
- [T-718] **production 側 cache の設計変更** — 理由: 裁定 2026-08-11 (見送り): 受理集合・proof chain に触れる変更は今は認めない。positive control の実プロセス検査は不変。再訪条件 = R-c 実装後も receipt 解決 2 回が受入 wall の支配項であるとき。
- [T-742] **path 防壁の検査対象拡大** — 理由: 裁定 2026-08-10: 文字列化後の値に限定したままとする (実害経路なし、D205)。再訪条件 = bytes / PathLike を直接渡す新経路の出現。
- [T-744] **二重 namespace への実行時機構** — 理由: 裁定 2026-08-10 (c): 静的検査 ([T-720]) で足りるとする。alias / ImportError はテスト 2 本の supersede と受理集合変更を伴うため見送り (D205)。再訪条件 = 静的検査をすり抜ける再発の実害 1 件。
- [T-751] **epoch 以前の pickaxe evidence を持ち回る恒久機構** — 理由: 裁定 2026-08-12 (同基準): 窓限定の現状を受容し checkpoint 連鎖は作らない。再訪条件 = 外部公開で監査地平の提示が必要になったとき。
- [T-767] **可視文字列の confusable 正規化** — 理由: 裁定 2026-08-11 (c): 現状維持。攻撃は信頼済み経路の内側からしか実行できず最悪ケースは構造側で封じ済み。再訪条件 = 誤用の実測 1 件。
- [T-781] **official 受理集合と proof chain 拡張 (Q1〜Q4)** — 理由: 裁定 2026-08-11 (全問 (a)): 実装なしで保留終端。official は空集合維持、User Attributes は認可に使わない、proof chain 拡張は先送り維持 (D86(5))、[T-139]・A 系列の後まで保留。D86 は 1 項も覆さない。再訪条件 = queue の `qattach` 無効化、または lineage を閉じる設計の登場。材料 = `output/insights/2026-08-11/t781-spool-feasibility/package.md`。
- [T-802] **dry-run の no-write 検査を Git 管理 bytes へ拡大** — 理由: 裁定 2026-08-11 (b): 広げない (index stat cache 等は正当な操作でも変わり誤検知検査になる)。守るべき実体は現検査が覆う。再訪条件 = dry-run 起因の汚染の実害 1 件。
- [T-807] **旧 writer の任意 path 受理を狭める** — 理由: 裁定 2026-08-11 (c): 狭めない。失敗様態は `namespace-dirty` の fail-closed 拒否で、原因ファイルの除去で復旧でき外部入力からは到達しない。再訪条件 = `namespace-dirty` の実発生 1 件。
- [T-837] **`c9c1a9c` の乗せ直し** — 理由: 裁定 2026-08-12: [T-816] Q1/Q2 の裁定により乗せ直しを省略し、`pin.CURRENT_PIN` (値の正本は `orchestrator/campaign/pin.py`) が指す commit へ直接前進する。Q1 (a) の旧裁定は上書きされた。残るユーザー手番なし。2026-08-12 [T-816] 手順 4 で前進済み。
- [T-858] **consumer pin の全称保証** — 理由: 裁定 2026-08-12 (b): 限定 AST inventory + 敵対レビューの併用を続け全称保証は主張しない。再訪条件 = loader-only sink の実増加。
- [T-864] **blob authority (canonical decision) の機械可読 target schema 必須化** — 理由: 裁定 2026-08-12 (同基準): 必須化しない。現行 marker gate が `approved_blobs:` 形式だけを拒否できる状態のままとする。**marker gate の保証範囲の限界記録は [T-793] R4 が行う** (同項は active)。
- [T-868] **承認 receipt の署名と外部 trust root** — 理由: 裁定 2026-08-12 (同基準): 署名方式と trust root は設けない。自己発行可能な性質は `/limitations/approval_receipt_trust_root_absent` の機械可読宣言で明示したまま受容する。再訪条件 = 外部公開時。
- [T-871] **toolchain binding S-3 (a) — attempt 実測値の脚** — 理由: 裁定 2026-08-12 (粗い provenance 基準): S-3 (a) の attempt 実測値の脚は実装しない。再訪条件 = 外部公開で証跡提示が必要になったとき。材料 = `output/insights/2026-08-11/t783-toolchain-binding/package.md`。
- [T-872] **成果物への binding report** — 理由: 裁定 2026-08-12 (同基準): manifest / result に binding report は載せない。exact-key consumer の改修も行わない。
- [T-873] **authority への cxx version / cmake path / module_list / bytes hash 追加** — 理由: 裁定 2026-08-12 (同基準): 追加せず calibration の再発行も行わない。
- [T-874] **束縛の producer 拡大** — 理由: 裁定 2026-08-12 (同基準): floor と silo ladder のまま他 producer へ広げない。

- [T-899] pilot API の seam 注入産物への non-evidence 印 — 理由: 裁定 2026-08-12 (第 4 束、
  推奨どおり見送り): pilot 産物は certified の受理集合に入らず (正規経路の検証を通らない
  ことを実測済み)、W-2 は固定 CLI で seam を公開しない。防御的メタデータの新設は見送り側。
  再訪条件 = seam 注入経路を使う pilot run の実走。
- [T-903] 受入集合を強める 3 案 — 理由: 裁定 2026-08-12 (第 4 束、推奨どおり見送り):
  実害・SURVIVED 未観測の型への受理集合変更はしない (「勝手に強めない」の維持)。
  再訪条件 = 該当型の変異 SURVIVED または実害の観測。
- [T-906] codex 防壁の防護範囲拡大 (launcher 以外の起動経路) — 理由: 裁定 2026-08-12
  (第 4 束、推奨どおり scope 外宣言): read-only 固定経路と runtime blocked の死経路への
  防護拡大は必要性未測定の堅牢化。再訪条件 = blocked 経路の解禁時または read-only 固定の
  変更時に、防護を義務化して再訪する。

- [T-900] cmake の realpath 束縛 (toolchain 束縛が cc/cxx は realpath 照合、cmake は
  version body のみ) — 理由: 裁定 2026-08-12 (第 3 束、推奨どおり見送り): bytes 級
  provenance 機構の新設は既定で見送り (2026-08-12 粗い provenance 基準、一次控え
  `rulings-inbox/2026-08-12-coarse-provenance-45rulings.md`)。当面は W-2 の記録済み
  `cmake.path` を親が照合する運用で埋める。再訪条件なし。

- [T-973] [T-922] 残余 R1 (binary hash authority) — 理由: 裁定 2026-08-13 (第 9 回 #18):
  実需発火まで dormant を明記して固定。発火時は (a) prereg へ binary hash を第一候補とする。
  形だけの結線の禁止は不変。再訪 = [T-922] 系 production 正例経路の実需発火。
- [T-976] [T-922] 残余 R4 (guard producer の production 結線) — 理由: 同裁定 (第 9 回 #18) で
  dormant 固定。偽 allow receipt を通す形だけの結線は不変で禁止。再訪 = 同上。
- [T-977] [T-922] 残余 R5 (budget ledger の canonical path) — 理由: 同裁定 (第 9 回 #18) で
  dormant 固定。再訪 = 同上。
- [T-978] [T-922] 残余 R6 (6 種 producer の不在) — 理由: 同裁定 (第 9 回 #18) で dormant 固定
  ((b) 意図的 dormant のまま §9.1 item 1 を未達に固定)。再訪 = 同上。
- [T-1022] 8c `_HistoryState` の freeze projection exact 一致 — 理由: 裁定 2026-08-13
  (第 9 回 #22): 見送り。再訪 = 実害観測時。
- [T-1030] 非 `tools/pegasus/` path への `local-ok` exact allowlist — 理由: 裁定 2026-08-13
  (第 9 回 #6、(b)): 作らない (D375 の単調性防壁を維持)。再訪 = login 結線 ([T-1029] (a) 側) が
  実需とともに再提起されたとき。
- [T-1041] oracle REJECT tombstone — 理由: 裁定 2026-08-13 (第 10 回): 作らない。[T-1040] の
  終端 status 化が再試行の動機を消すため二重機構にしない。再訪 = 終端化後も同一 proposal の
  再試行が実測 1 件出たとき。
- [T-1044] oracle finding exact schema の producer / WAL 展開 — 理由: 裁定 2026-08-13
  (第 10 回): 見送り (防御的堅牢化の既定)。再訪 = reader 側 exact schema が producer 由来の
  実不整合を 1 件捕まえたとき。
- [T-1046] S1 ledger nested field の読み側 exact 検証 — 理由: 裁定 2026-08-13 (第 10 回):
  見送り ([T-1044] と同じ基準)。再訪 = 同左。

- [T-321] **guard_bash の realpath 非解決・cd 追跡なし・hardlink alias の硬化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。実測された迂回を伴わない一般硬化。実測付きの writer 迂回は [T-1025] が P1 で所有する。再訪条件 = 同型の実害 1 件。
- [T-289] **8c freshness 検査と state 生成の TOCTOU** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。並行実行は計測規律が既に禁じ、build 経路は competing_bench_pids() が部分的に覆う。再訪条件 = 同型の実害 1 件。
- [T-284] **重複 key の扱いが submit と job で非対称** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。非対称の事実は D113 に記録済みで、実害の観測はない。再訪条件 = 同型の実害 1 件。
- [T-256] **_read_regular_at の未捕捉 OSError** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。handoff 経路からは D108 で到達不能。DW-G03 の独立 2 例目が出ていない。再訪条件 = 同型の実害 1 件。
- [T-390] **D122 の opt-in 経路の残置** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (a) で「既定拒否のまま残し使わないを運用規律とする」が確定し撤去もしないと決まった。再訪条件 = opt-in 経路が実際に使われた 1 件。
- [T-408] **symlink 解決の食い違いの調査** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (c) で食い違いを残すと確定し、調査 5 点も完了して実損 0 と実測済み。再訪条件 = 現行挙動を pin するテストを足す wave。
- [T-418] **state_from_dict のエラーが未信頼 checkpoint 文字列を再掲** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本 wave 由来でない既存挙動で、修正は既存テストの期待値変更を伴う。再訪条件 = 同型の実害 1 件。
- [T-460] **compile 中の source 差し替え ABA 対策** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。単独 wave を立てず P3+P4 実装 wave の設計入力に含めると裁定され、入力としては記録済み。再訪条件 = P3+P4 実装 wave の設計段。
- [T-462] **formal report schema の binding receipt と recipient 閉集合** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。単独で決めず D121 P2 面の wave の設計入力に含めると裁定され、入力としては記録済み。再訪条件 = D121 P2 面の wave の設計段。
- [T-673] **本番 guard D の採用** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。D は不採用で終端と裁定済み。残余の運用義務の所在も probe clone 削除で決着した。再訪条件 = 同族の CI 検出が既存テストで担えなくなったとき。
- [T-745] **静的検査の走査対象を Makefile / CMake / qsub script へ広げる** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。両レンズと親が独立に全走査し、現 repo に該当する legacy module 名は 1 件も無いと実測して DW-G04 で見送り済み。再訪条件 = それらの経路に module 名が実際に現れたとき。
- [T-957] **被覆外 3 経路** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。scope 外で終端と裁定済み。再訪条件 = 実害 1 件、または同面を塞ぐ変更への相乗り。
- [T-964] **symlink 経路の閉鎖** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (現行 built-in spec から到達不能・実害ゼロ・塞ぐと正常系も狭める)。再訪条件 = custom spec 経路の実需。
- [T-1024] **hook 検証と spawn の間の窓 / worker 存続中の再検証** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本文自身が「粗い provenance 基準では既定で見送り側」と結論している。再訪条件 = 同型の実害 1 件。

- [T-1073] 旧 v2 artifact を読む明示的な offline 入口 — 理由: 2026-08-15 /rulings 全件の裁定 =
  設けない。現行 materials 経路へ旧世代が流入する risk を新設するだけで、読みたい場面が
  具体的に挙がっていない。再訪条件 = 旧 v2 artifact を読む必要が実作業で生じたとき。
- [T-1074] quarantine reason への UTF-8 byte 長上限 — 理由: 2026-08-15 /rulings 全件の裁定 =
  設けない。上限を超える理由文が実際に出た記録がなく、防御的堅牢化にあたる。
  再訪条件 = 実際に長大な reason が producer から出たとき (その場合も日本語診断が入る余裕を残す)。
- [T-1075] quarantine reason の許可文字を producer の閉語彙へ縮小する案 — 理由:
  2026-08-15 /rulings 全件の裁定 = Letter / Number 全域を維持。縮小すると現行の日本語診断が壊れ、
  producer 側の語彙固定と対でしか実施できない。再訪条件 = producer の語彙を固定する別作業が
  立ち上がるとき。
- [T-1077] 実効 scheduler marker の発行者認証 — 理由: 2026-08-15 /rulings 全件の裁定 = 現状維持。
  同一 process 内で marker を偽造できるのは事実だが、この環境で偽造の動機を持つ主体が実在せず、
  閉じるには受入 env と受理集合の変更という重い代償を伴う典型的な防御的堅牢化である。
  再訪条件 = 受入 env に第三者由来の plugin が入るとき。
- [T-1103] observations 層への封印 token 境界の新設 — 理由: 2026-08-15 /rulings 全件の裁定 = (b)
  現状維持。既裁定「論文主張に要るのは粗い provenance のみ」に照らし封印機構の新設は既定で見送り。
  **主張を「単独 oracle 改竄まで」と限定する記述の維持が条件**であり、これを怠ると過大主張になる。
  再訪条件 = 観測記録の同時偽造を想定すべき第三者が proof chain の消費側に入るとき。
- [T-1119] 起動検査の受理条件を「main landed」から「tracked」へ広げる案 — 理由:
  2026-08-15 /rulings 全件の裁定 = 現行維持 (狭い側)。実装側が示した迂回経路
  (自 wave が自分の handoff を `git add` して commit すれば index に載るだけで受理される) は
  具体的で、広げると防壁が実質無効になる。
  再訪条件 = main landed 判定が正当な wave を実際に止めたとき。

- [T-1330] 閉包 meta-test の検出力の自動検証 — 理由: 裁定 2026-08-17 (第 6 回、見送り)。
  テストのテストが要る二階の仕組みに対し、守る対象が 1 件で費用対効果が合わない。段 6 fix の
  実装子が一時変異で両方向を手で確認した記録で足りるとする。再訪条件 = 閉包 meta-test が緑のまま
  本物の閉包漏れが着地した実例 1 件。

- [T-1339] 比較規則 identity の spec / manifest / runtime 三者一致の鎖 — 理由: 裁定 2026-08-18
  (/rulings 全件 第 7 回、新設しない)。反復数と構成集合は既存機構が凍結し、集約と境界はテストが
  pin しているため純増分は乖離検出だけで、代償に manifest schema の版上げと受理形の変更を伴う。
  プロトタイプ基準の下では見送り側である。再訪条件 = 宣言と実装の乖離による実害 1 件。

- [T-1453] ビルドキャッシュの来歴不一致で行き止まりになる件の復旧手順の runbook 化 —
  理由: 裁定 2026-08-23 (/rulings 全件、来歴はそこまで重要ではないためコストを払わない、
  D677)。失敗自体は fail-closed で正しく
  止まっており誤受理を生む穴ではない。再訪条件 = 当該経路の出力が認証材料へ入るようになったとき。
- [T-1454] 公式扱いを宣言する旧経路のビルド呼び出し 5 件の新経路移行 —
  理由: 裁定 2026-08-23 (/rulings 全件、同上、D677)。
  5 箇所はいずれも探索・デモ・sweep 系で認証経路ではなく、移行は受理集合を変えて凍結証拠の
  再束縛を招く。再訪条件 = 当該経路の出力が認証材料へ入るようになったとき。

- [T-1378] **批准台帳の外部 trust root と署名の新設** — 理由: 裁定 2026-08-23 (/rulings 全件、択 (b) 現状維持): [T-868] (承認 receipt の署名と trust root は設けない) および 2026-08-12 の粗い provenance 方針と同型であり、覆す新事実がない。`hooks/` 配置による AI 追記の機械的遮断を維持し、自己発行可能な性質は機械可読な限界宣言で明示したまま受容する。再訪条件 = 外部公開時 ([T-868] と同じ)。**発火記録: 2026-08-27。D905 (2026-08-25、ユーザー裁定) が
  この見送りを覆した** — 批准の執行経路は「AI が成りすませない実行主体の新設」だけを採ると定めたため、
  外部 trust root と署名を設けない側の前提が失効した。[T-1629] の wave で実装済み。
- [T-1558] **撤去 tool への同一 invocation 所有権証明 (lease / capability)** — 理由: 裁定 2026-08-23 (/rulings 全件、択 (b) 現状維持): 実害の観測がなく防御的堅牢化に当たる (2026-08-12 ユーザー方針・D205 と同基準)。現行の 5 条件 (common git-dir 一致・branch↔tip 束縛・占有 rc=0・clean・ancestry) で代替する。再訪条件 = 別セッションによる誤撤去の実害 1 件。

- [T-1694] **procfs の列挙不完全性を理由に走査全体を rc2 にする形** — 理由: 裁定 2026-08-27
  (/rulings 全件、推奨どおり): rc2 にしない。現環境で当該 mount option は未設定である。
  完全な列挙を保証しない限界を明記する (D1218)。
  再訪条件 = 実環境で対象内の生存 process の欠落を観測した 1 件。
- [T-1772] **到達性検査の must-reach / dataflow への厳密化** — 理由: 裁定 2026-08-27
  (/rulings 全件、推奨どおり): 承認権限が閉じている間は現状維持とする
  (D1218)。
  再訪条件 = 承認権限を開けるとき (開放の条件に厳密化した検査を置く)。
- [T-1986] **鍵の紛失・交代・信頼根 rotation を表現する schema 拡張** — 理由: 裁定 2026-08-27
  (/rulings 全件、推奨どおり): 足さない。固定鍵の限界を明記する。初期実装に rotation を同時搭載する
  必然性がまだない (D1218)。
  再訪条件 = 外部署名主体の設計に着手するとき、または実際の鍵交代要件が生じたとき。
- [T-1987] **批准から official 起動までの非介在を強制する lease** — 理由: 裁定 2026-08-27
  (/rulings 全件、推奨どおり): 作らない。現状は変更を安全側に拒否しており、悪化していない
  (D1218)。
  再訪条件 = 承認の失効が実際に作業を止めた実害と、その頻度の観測。

- [T-337] 種別宣言の機構と field 名は D528 で確定し、D162 決定 (11) の land 禁止も campaign producer に… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-338] **単位5 (writer + conformance vectors) 完了。次は単位6 (統合+4名前export)。** D574決定(… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-311] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-274] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-232] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-361] bnode003/bnode004 間で /work・/home とも cross-node 6/6 BLOCKED、localflock な… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-387] 択 (b) 採用・現状維持 — 受理集合は広げない。実害が無く、受理集合を広げるのは常に慎重にすべき方向である。ただし「実害がない理由は直接読… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-398] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-405] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-478] 撤去採用につき床値 v2 の 発行経路は不要方向で確定した。撤去を実装する wave が最終確認して終端させる。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-500] post-policy の機械 sweep は membership 証拠なしで受理される。共有 validator は機械 lock に空の… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-530] 読み出し境界の残件 6 問は択一の 形の裁定パッケージにしてから再提出する ([T-674] 所有)。D320 により provenance… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-578] 変異 kill 判定で未固定の弱化変異が 他に無いかを、集合関係と正規化以外の軸 (rc 分類、timeout、artifact error)… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-582] current-only を意図として固定し、 直接テストで境界を押さえる (D1084)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-696] 「審査される 側が審査する道具を書き換えられる」構造は、**協調境界として受容すると明文化する**。択 (a) の immutable tru… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-790] ルート A / B の択一は消滅した。 規範 compiler を site compiler へ寄せる以上、g++-13 を生むための隔離… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-824] 択 (a) 採用 — 待ち手に呼び出し受領証 (段・wave・引数・script の指紋の束縛) を発行させ、段 7 の記録検査で照合する。待… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-829] _EXPECTED_FIXTURE_ENTRIES_SHA256 と _EXPECTED_ROW_IDS_SHA256 の 2 つの独立 ha… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-847] 択 (a) 採用 — 呼び出しの権能を排他権の payload へ束縛し、release/renew で一致を要求する。同じ束の 4 点 (T… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-923] 全面拒否を維持し、発火条件を分割先が残した権威・生成側・二相の防壁・予算台帳の解決に貼り直す。床値実測の開始とは結合しない (D915)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-958] qualification/artifacts.py の append_jsonl と campaign/wal.py の lock prei… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1013] 固定 literal 1〜2 変数の注入のみ可。allowlist の 一般化はしない。実装待ち。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1017] perf realpath を toolchain binding へ含める要求は、 D497 により official 化の必須依存ではない… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1018] competing_process / launch_failure の自己申告と保存 probe 証跡 (rc / stdout / std… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1063] 占有の予約制は、本 rulings 第 1 束で「別枠として起票する」と裁定した占有穴の設計と同一の機構であるため、その枠で扱う。個別には決め… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1121] 起動検査の残存限界 2 件。clean/smudge filter や EOL 変換のある path では clean-tree との連言が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1122] tools/check_wave_startup.py の _git は subprocess に timeout を渡していない (既存 6… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1136] 事前登録の判定器を -m で起動すると 12 条件すべてが評価器例外になる。同判定を package import 経由で呼ぶと正しく未定義を… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1158] build 中に依存 tree を差し替えて元へ戻す (ABA) 攻撃への予防を設計する。前後 snapshot の同値検査では検出できない。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1160] 共有 FetchContent base に create-only の 所有権 token を導入する。現状は job 一意な $TMPDI… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1161] 択 (b) 採用 — まず影響範囲を実測する。末端でない path を防壁の対象に含めるとビルド生成やパッチ適用と干渉して正規経路が止まりうる… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1193] pin fast path が _verify_rollout_sha の失敗を 握り潰し、その後の全走査が同じ file を SHA 未検証… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1215] 択 (b) 採用 — 当該 1 箇所の除去漏れだけ直し、族一般化は独立 2 例目を待つ。閾値を満たさないうちに族化するのは規律 5 (盛らない… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1233] dispatch claim・変異 source 復元・evidence 退避・ teardown を直列化する per-checkout の… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1236] qsub 前の永続 claim と、対象束縛された終端証拠による 解決 (tombstone)。SIGKILL・discovery 中の再 s… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1238] 過剰拒否を検出する正例変異を、dispatch 署名・ dispatch 検出・worktree 検出・受入検出の 4 面へ登録する。本 wa… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1242] SWO receipt を 「oracle が実際に走った」証明にする署名機構は**新設しない**。「bytes 級の凍結証拠・署名・束縛 機… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1243] admission 台帳を 削除して同一 bytes で再構成する攻撃への耐性機構は**新設しない**。[T-1242] と同じ理由・同じ条件… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1244] measurement_head は **非権威 field のまま**とし、位置づけを明記する。commit 束縛の新設は「計測は HEAD… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1258] 択 (b) 採用・当面維持 — 投入 script への外部起点の束縛は今は入れない。偽装には repo への書き込み権が要り、それを持つのは… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1266] gate の権威 (保持された authorization_contract.contract) と現行 registry がずれると、gat… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1270] _cleanup_lifecycle は cleanup body の前に ownership を NONE へ消費するため、body 中に別… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1288] -m 実行で判定器 module が二重に読み込まれ全 12 条件が evaluator-exception へ潰れる件は 直す。**呼び出し… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1299] source root repository を信頼済み中核と明文化し、機械可読な限界宣言に残す。config allowlist を掛ければ… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1305] 防御的冗長として明記して 残し、発火する保証にも検出力にも数えない (D1214)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1317] dispatch の IZANAGI_DISPATCH_OUTCOME_V1 attestation は受入 command と同じ stdo… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1322] 床値 driver CLI の --protocol が caller 選択面のまま残っている。段 6 レビュー C / D が real と… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1323] official launch preflight (_PREFLIGHT_FIXED_FILES と legacy bytes 比較) が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1324] v2 candidate producer が legacy path を固定で読む件は、予算承認の材料が揃い official floor… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1325] committed-only 権威は bytes 一致を要求するが、 commit 後の chmod による作業ツリー側の mode drif… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1340] refusal 文字列と識別子に残る floor の語が、 比較の基礎という意味に誤読される。受理集合も certified 選択の値も pr… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1369] 非機械条件 C03 / C07 / C08 の証拠契約に 実在しない関数名 accept_trial が残る (C03 の load_mani… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1370] 実走前 gate の s8b_oracle_driver._store_sha256 を no-follow / regular-file 確… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1375] land verifier 自身も候補コードである。D254 の provenance checker と同型に main へ束縛する。 成果… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1377] 歴史 raw 専用の 4 ツール (s1_report.py / tools/plotting/plot_backoff.py / p2_2_… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1386] 段 6 敵対レビューが real と判定しつつ本 wave の scope 外とした 6 件。 (a) malformed consumer… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1398] 受入待ち手の D486 attempt 2 で、self-claim 前に main がさらに進むと claim-self-unverifie… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1417] _extract_latest_active/ _global_ordinal_entries (tools/spool_fold.py) は… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1435] attempt registry の時点証明機構は「trusted launcher は誠実である」を 前提とする。この前提自体を機構的に検証… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1450] _receipt_schema.py:34-43の ReceiptSchema.__post_init__がdocumentの再ハッシュをせず… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1463] [T-287] 裁定パッケージ§3。値域検査では in-domain 改竄 (許可値の範囲内で rejected→fail+increase+… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1478] journal の reservation-preflight イベントも perf-preflight と同型の resume classi… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1483] D510項目6 (測定近接性ラベル) を実装する将来wave。前提条件: (a) provenance (timestamp・環境/実装/to… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1487] s8b_holdout_freeze.py の _blob_at_head/head 捕捉 (measurement_closure 等 4… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1521] 禁止を入れる前に (a) その禁止が実際に捕まえる負例 2 件と (b) 正当な用法を誤って拒まない境界の試験を実測する (D1213)。 *… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1556] 受入環境の temp root を admission する層は作らない。発火する既存 artifact path も計測 ID も書けない段… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1570] 既定 K=2 である事実を踏まえても、受領証レベルの shard完全性証明は実害が出るまで作らない。実行器内部の完全性検査は維持する。 決定… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1590] 適格判定の後に PYTEST_ADDOPTS を process 内で書き換える 窓が残る。これを行えるのは tools/run_tests.… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1644] 静的に解決できない間接値の 限界は D774 の docstring 明記のまま据え置く。別の証明手段を設計する場合は [T-1642] の別… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1654] 子が読む規範は working tree であり凍結されていない。 authority docs 2 file の 4 節だけが全文比較されて… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1655] snapshot 取得から子の spawn までの間に authority docs を 書き換えられる窓が残る (現行でも同じ窓がある)。凍… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1656] receipt は HEAD snapshot しか持たないため、 後日「どの merge admission で通ったか」を再検証できない。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1661] dangling 監査が抑止根拠に採った外部 copy を、 /cleanup-branches の削除直前に再検証する gate を検討する… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1665] 最終 scan と shutil.rmtree の間に新規 process の 参入を排除する仕組みが無い。checker 自身が「走査後に始… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1666] cmdline 除外の invoker exe allowlist を、 祖先 edge を invoker ごとに証明する条件へ置き換える。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1673] adapter の registry 更新が共有 admission root の 排他 lock を取るため、全 worktree・全 ca… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1679] interpreter の bytes 級同定 (実行 bytes・version・checker source bytes) は、D780… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1701] seccomp allowlist の exact 集合を固定する 検査を置く。現在の検査は hard-code した forbidden s… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1704] _BENCH_PAYLOAD_EXTRA_KEYS に 2 つ目の key を 足した瞬間、1 key だけ渡す既存 caller が mis… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1721] 4 問とも裁定 (D1222)。(1) 稼働 wave の land 後に一体で再設計する (2) 再開 scope の 8 項目への拡大を認… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1723] exploration campaign root producer の discovery は**強化せず、現行の検出範囲を明記して運用する… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1724] p3_autonomous_workload_trial の runtime 側 root 所在検査は**対象外と明記し、空の asserti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1729] s8c_preregistration_evidence.py の C01 は p3 の 3 関数の AST に整数リテラル 1_000_00… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1733] tools/dev_wave_land.py の受領証に **発行元の証明と再送防止を設計する**。署名鍵と発行権限は候補および AI が書け… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1750] 受入 launcher が実行器を起動する interpreter は素の python3 で PATH 解決である (tools/accep… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1778] A-1 の policy 束縛は同一 commit 内で しか効かない。policy・その SHA・source binding を別 com… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1783] digest 中の間接識別子を 中立 label へ射影する型付き renderer は**採らない** (D988)。 make_criti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1802] 明示共有 base を使う複数 job の間で、 oracle 判定後に別 process が prebuild を再入する経路を塞ぐ。D42… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1808] 受入 gate 本体 (照合器・登録器・受領証) を強制ソース閉包へ **入れない**。D956 が「受入 gate を足す実装は閉包の ex… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1811] landed 参照が読む main 側 blob に size 上限が無い。修正前の git show も同じだったので回帰ではないが、mai… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1837] ambient IZANAGI_SORT_SWO_MASSTREE_ROOT から 任意の pin 適合 root を受理する product… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1841] 択 (b) 採用 — D1099 の方針どおり偽造不能受領証の機構へ相乗りする (D1221)。同一主題の項も本裁定で終端した。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1853] 登録しない。D1006 の条件文を 確定形へ改める (D1069)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1854] 分類受領証を封じた後、出力を開く前の crash で封じた bytes が復元不能になり slot が停止する。恒久解は durable な… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1860] patchharness の共有 checkout guard は ContextVar を読むので、別 thread と subproces… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1866] 再訪条件を「必ず通る経路に停止点ができたとき」へ改める (D1072)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1897] 変異 m08 (_evidence_sort の除去) に意味的検出器が無い。凍結 report の accepted_evidence が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1900] orchestrator/tests/test_check_docs.py の 共有ヘルパ _run_check は timeout=None… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1927] 列挙した admin 名から gitdir を 開くまでの ABA 置換と、列挙後に増えた登録を現行 scan は検出しない。「矛盾のない 1… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1945] 択 (iii) 採用 — 予算だけ freeze 単位に残し、台帳を protocol 世代ごとに分ける複合形。 防壁の意味を変えずに世代を収… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1947] FloorRetryAuthorization が公開 dataclass で、runner が isinstance しか検査しないため a… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1949] 案 A (pin 据え置き) を採用した (D1150)。SS2PL は既存 patch で扱い続ける。 案 C の前提 C-1 (sourc… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1951] .gitmodules の branch = izanagi-trace を 実際の pin を含む tip へ揃える。現状 upstream… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1961] 同じ artifact を対象にする gate を 新設するとき、既存 gate と要求の向き (凍結か追随か) が逆でないかを機械検査する仕… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1988] 全史検査と履歴取得の間に履歴 view が 変わると過去の不正を取り逃す。v1 も同一構造。外部の固定実行器を要する。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-1989] qualification lane へ署名 gate を付けるかは evidence-only lane の意味を変えるため別裁定とする。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-2026] 承認 bytes を誰が置くかの 射程衝突を裁定する。D287 は本 pin について「人間がコード diff をレビューして定数を置く」を… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-2039] 末尾 append では user site の .pth が追加する path は復元されない (site.addsitedir() を禁じ… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
- [T-2047] s8b_attempt_registry.py は旧 consumed/ と旧 marker schema だけを読む。現在 producti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。

- [T-163] s6 `cmd_verify` の `n1_provenance_sha256` 検証 — 理由: 裁定 2026-08-29 (/rulings 全件、
  分類不能 8 件の帰属を確定): 2026-07-29 に裁定済みのまま 1 か月動いておらず、論文の主張にも
  受理集合にも触れない。2026-08-28 の過剰実装棚卸しで分類不能として保留された 8 件のうちの 1 件。
  再訪条件 = 同型の実害 1 件。
- [T-168] `read_set_` の intent shadow — 理由: 裁定 2026-08-29 (/rulings 全件、分類不能 8 件の帰属を確定):
  T-152 族の P3 項で、論文の主張にも受理集合にも触れない。再訪条件 = 同型の実害 1 件。
- [T-169] trace stream の I/O fail-open を fail-closed 化 — 理由: 裁定 2026-08-29 (/rulings 全件、
  分類不能 8 件の帰属を確定): trace 層全体の P3 項で、trace-enabled build の正しさ検証は現状 anomaly を
  取りこぼした実測がない。再訪条件 = trace 取りこぼしの実害 1 件。
- [T-424] job script hash の残余 (override 禁止・`$0`/HEAD blob 束縛・interpreter gate・perf ノード
  個体差 gate・将来 consumer 設計) — 理由: 裁定 2026-08-29 (/rulings 全件、推奨どおり見送り):
  実 job の hash は既に `job-result.json` / `final-receipt.json` まで伝播済みで、残余は bytes 級
  provenance にあたる。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ) に従う。
  再訪条件 = 同型の実害 1 件。
- [T-429] 拒否理由の多面開示を閉じる — 理由: 裁定 2026-08-29 (/rulings 全件、推奨どおり見送り):
  現行の gate / preview / attempt journal / whiteboard / critic digest が既に subtype・reason・
  禁止識別子・件数を公開しており、leaf 側だけ開示 0 bit にしても経路が残るため効果がゼロである。
  report と投影契約の変更を伴う。再訪条件 = 同型の実害 1 件。
- [T-1247] `loop.py` の例外隔離経路が `build_start` を書かない件の是正 — 理由: 裁定 2026-08-29
  (/rulings 全件、推奨どおり見送り): 読み手側の診断可能性は既に直っており、書き手側の変更は WAL の
  replay / admission topology に触る。実害は診断のしにくさで、それは既に緩和されている。
  再訪条件 = 同型の実害 1 件。
- [T-1294] 層 3 の境界で production の `validate_perf_preflight_receipt` を再実行する — 理由:
  裁定 2026-08-29 (/rulings 全件、推奨どおり見送り): schema の相互整合で閉じており実害未観測。
  再訪条件 = 同型の実害 1 件。
- [T-1306] `UNSATISFIED` を `PROVEN_ABSENT` と `INDETERMINATE` へ分ける — 理由: 裁定 2026-08-29
  (/rulings 全件、推奨どおり見送り): 分離の目的は監査の読みやすさで受理集合は変わらない一方、
  status 語彙の拡張は判定器・射影・凍結記録・ActivationReport の全 consumer へ波及する。
  再訪条件 = [T-1422] の調査で「解析不能」が実際に誤判定を生んでいると判明したとき。
- [T-1714] `s8b_prediction_runner` の envp 順の固定化 — 理由: 裁定 2026-08-29 (/rulings 全件、
  相談で親の初版「固定化する」を反転): 確認されているのは順序の変動だけで、binary・測定値・判定の
  いずれかが変わった事例はない。固定化は s8b freeze bytes の再凍結を伴う。
  再訪条件 = 順序差に起因する実害・cache miss・結果差のいずれかが観測されたとき。
- [T-1965] 判定の構造化診断を凍結される結果表から復元可能にする — 理由: 裁定 2026-08-29 (/rulings 全件、
  推奨どおり見送り): 規律 3 が求める「なぜ壊れたかを次の一手のシグナルにする」は判定器の戻り値が既に
  満たしている。凍結表からの事後復元は監査の便宜で論文の主張に効かず、新しい凍結手続きと consumer の
  設計を要する。再訪条件 = 同型の実害 1 件。

- [T-1844] 事前登録 §5 残り 9 欄の型検査 — 理由: 裁定 2026-08-31 (/rulings 全件、推奨どおり見送り):
  D1000 が §5 の機械検査を構文的非空と grammar に限ると定めており、記入は人間 1 人で型の誤りは
  その場で分かる。防御的堅牢化の既定見送り (D1332)。
  再訪条件 = 記入時の型の誤りが実際に 1 件観測されたとき。

- [T-1477] **批准追記の執行経路の再設計** — 理由: 2026-09-01 ユーザー裁定
  (D1394)。陳腐化 = D1139 が enforcement source closure の
  批准突き合わせ自体を廃止したため、待っていた執行経路の対象が存在しない。
  再訪条件 = 批准突き合わせに相当する関門が新たに設けられたとき。
- [T-2132] **2 つの根クラスへの durable root commitment** — 理由: 2026-09-01 ユーザー裁定
  (D1390)。両根クラス全体へ bytes 級 provenance を導入する設計であり、
  粗い provenance で足りるという方針 (D1139) に当たる。現行成果物への実害も示されていない。
  再訪条件 = origin への帰属を検証できないことに起因する実害 1 件。

- [T-2144] balanced5 の中断 recovery の射程拡大 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): correctness の穴ではない (例外は fail-closed で、独立にも再評価が拒否される)。
  失われるのは「invalid であった」という WAL 上の耐久記録の形だけで、実害は中断した pilot を
  測り直す時間である。D1388 が同じ天秤で「実害が再走時間だけなら受理集合を広げる代償に
  見合わない」と裁定している。再訪条件 = 記録の形の欠落が実際の診断を妨げた 1 件。
- [T-2157] 復元 mask の挙動同値性の判定 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): 現行の 3 対はいずれも挙動上も別物であることが実測済みで、追加実装の
  必要が無い。再訪条件 = 対比の候補を増やすとき。
- [T-2174] 凍結解決系と試行台帳系の git 呼出しの統一 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): 受理集合を同じか狭くする一般硬化で、実害の観測がない。
  2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。
  再訪条件 = 同型の実害 1 件。
- [T-2179] S-1 epoch gate の正例への同一性 assert 追加 — 理由: 裁定 2026-09-02 (/rulings 全件、
  相談で親の初版が覆り見送り): 一次資料自身が「本 wave が作った穴ではなく実在欠陥でもない」と
  判定している。粗い provenance 方針と防御的堅牢化の既定見送りに従う。**親の初版は
  「安価だから足す」だった。** 再訪条件 = 実際の epoch 取り違えを観測したとき。

- [T-2270] 承認 commit の predecessor 無制約の穴 — 理由: 裁定 2026-09-03 第 6 回 (推奨どおり):
  D1578 のとおり正本の部分適合に留め、`A^ == Q` の代替述語は発明しない。Q は permanent family
  の構成要素で未実装であり、世代導入 commit を代替に据えると正本どおりの完全列を逆に拒否する。
  再訪条件 = Q を含む permanent family の実装。
- [T-2274] repo 外束縛の全数走査 gate の新設 — 理由: 裁定 2026-09-03 第 6 回 (推奨どおり):
  D1583 が既に新設せず局所修復に留めると決めており、本項はその再確認である。構造が
  `O(file 数)` で D335 に触れる。全数性は人手の走査に依存し続ける。
  再訪条件 = 一括読み出しへの設計変更が別の理由で入ったとき。
- [T-2281] 承認済み CMake identity の権威の新設 — 理由: 裁定 2026-09-03 第 6 回
  (D1600、推奨どおり): 登録簿・更新手順・機体差の扱いは新設せず、
  判定器が解決した実体の identity を green record へ束縛する現行形 (記録であって拒否ではない、
  D1586) を維持する。2026-08-12 の粗い provenance 方針に従う。
  再訪条件 = 未承認の CMake による測定が実害を出した 1 件。

- [T-2328] `BUILD_START` payload への平文契約 ID 再掲 — 理由: D1680 の
  照合で、per-attempt 単独監査の実需が未観測と確認した。campaign.lock との併読で契約 ID は得られ、
  成果物影響は監査の手間だけで certified 値・受理集合・参照は変わらない。再訪条件 = campaign.lock を
  併読できない状況で per-attempt 監査が実際に要求されたとき。
- [T-2345] 旧 grammar 8 / 12 / 14 / 25 / 27 の歴史 decoder への追加収載 — 理由: D1653 が「収載する grammar は
  実在 corpus が確認できたものだけ」と定めており、当該 5 grammar の実在成果物は未観測で条件が成立しない。
  該当 grammar の成果物が現れるまで何も読めなくならない。再訪条件 = 当該 grammar の成果物を 1 件観測したとき。

### 研究・計測系

- [T-021] **balanced での backoff profile 対照** (B-011, 出所 `docs/phase3.md`) — balanced を凍結機序 profile に含め qualifying rr50 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-022] **over-throttle 有用 IPC 低下の機序分離** (B-012, 出所 `docs/phase3.md`) — MLP または cache 余熱への因果帰属を対外説明・consumer が採る時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-023] **mocc trace-hook / verifier 第2 protocol** (B-013, 出所 `docs/phase3.md`) — 旧 headline 2 / 段 7 cross-protocol で mocc を採る時、または visible-invisible correctness ablation を承認した時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。 発火記録: 2026-08-11 の S1 設計択一 Q2 裁定 (初手 mocc) で発火条件が成立し、mocc trace-hook は実装・pilot 実走・G2 判別子の実機 1 セルまで到達した。追加裁定はせず記録のみ。
- [T-024] **ermia cross-check の再定義 (前提消滅・要再定義)** (B-014, 出所 `docs/phase3.md`) — si と ermia を cross-check protocol 集合へ再採用する時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-025] **calibration 下限 K 感度** (B-015, 出所 `docs/archive/worklog-phase1-2.md`) — 裁定 2026-07-19: K=4 を設計定数として明示承認し、感度主張は行わず終了。論文の機序図または K=4 依存主張の凍結直前に再評価、証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- [T-026] **thread 数変更時の再 calibration** (B-016, 出所 `docs/archive/worklog-phase1-2.md`) — 承認 performance thread に qualifying calibration が無く live floor carrier も無い時。裁定 2026-07-19 保留承認、between-run floor は現行チェックポイントの floor 実測工程が部分的に運ぶ。述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-027] **Threats to Validity の集約** (B-017, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 対外 claim set の凍結直前に限界索引が未集約の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-028] **backoff +38%/+11% の別 boot 再現** (B-018, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 当該値を対外主張へ採り別 boot 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。 2026-08-26 の /rulings 全件で発火条件の成立を確認した (論文素材 2026-08-26 版で 2 値とも採用済み、参照する一次資料は旧環境の sweep で別 boot 証拠を持たない)。ユーザー裁定 = 別 boot で取り直す (D1100)。既存の走査手順をそのまま 1 回回す形でよい。
- [T-029] **critic 軸提案の再現率測定** (B-019, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — critic 提案の再現性を claim / gate に使い replay report が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-030] **backoff 再現の rounds≥3** (B-020, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — cross-round 再現性を主張し qualifying round が 3 未満の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-031] **stock 第2・3位 base 上の fix5/fix10 一般性** (B-021, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — stock base 横断の改善を主張し第2・3位 base 成果物が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-032] **backoff 動作点 thread/skew/records 拡張** (B-022, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — 単一点を越える動作領域を主張し登録 sweep が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-033] **backoff ピーク位置 fix2/3/5/7 reps≥15** (B-023, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — backoff peak を名指す主張に qualifying grid が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-034] **待ち方と待ち量の直交化 (SMT 分離)** (B-024, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — wait shape / amount へ因果帰属し直交 SMT ablation が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-035] **backoff rmw=1 一点測定** (B-025, 出所 `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md`) — backoff claim を rmw=true まで広げ qualifying point が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-036] **calibration maxrss 固定オーバヘッド控除** (B-026, 出所 `output/insights/2026-06-18_calibration-no-cache-miss-saturation.md`) — 固定 overhead が maxrss の 5%以上で控除により selected N が変わる時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-037] **calibration sweep の 1m 未満拡張** (B-027, 出所 `output/insights/2026-06-18_calibration-no-cache-miss-saturation.md`) — K 感度の再評価で左打切りが示され最小測定点が 1m の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-038] **axis-proposer 用の既存軸台帳** (B-030, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 発火述語は未定義で、入力文書・axis/hole 集合・review 失敗判定の定義時に再評価。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-039] **共有相手決定時の review snapshot** (B-031, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 外部研究相手と問いを凍結し curated snapshot が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

- [T-237] role ごとの実所要時間の計測 — 理由: 目的である [T-236] の role_cap 裁定が設計凍結となったため、発火条件が成立しない。
- [T-142] 旧 headline 候補の再起票 — 理由: (62) のユーザー再裁定で close 済み。formal selector と live campaign が揃った場合だけ新規に起票する。
- [T-156] selector-8b workload descriptor への set-size 条件反映 — 理由: (36) で条件成立まで保留と裁定済み。発火条件は「8b descriptor の拡張を設計するとき」または「TPC-C 級 workload corpus を採るとき」で、着手前に workload 別の set-size 分布を測る順序も決まっている。
- [T-176] raw evidence bundle の保存形 (trace 圧縮) — 理由: (60) の裁定で driver 変更を伴うため次回 characterization に合流すると決まった。

- [T-549] Pegasus 全 probe 共通の単独性 witness (process / cgroup / PSI) — 理由: 2026-08-09
  ユーザー裁定で見送り (プロトタイプ基準の防御的堅牢化)。現行の runbook 手順 + probe 毎対応を
  維持する。再訪 = [T-139] campaign 本走の直前に再評価。

- [T-539] **α 取得の事後証拠の versioned schema 凍結** — 理由: 裁定 2026-08-06: 行わない (プロトタイプ基準)。再訪条件 = 論文化・外部公開で attestation 証跡の提示が必要になったとき。
- [T-542] **α 巡回の暖機持ち越し ablation** — 理由: 裁定 2026-08-06: 行わない。再訪条件 = 変異比較で説明不能な系統差が観測されたとき。
- [T-595] **reasoning=max→high の非劣性 A/B campaign** — 理由: 裁定 2026-08-07: 着手しない (D205、運転コスト最適化であり研究成果に寄与しない)。D223 の機械 pin を恒久 latch とする。再訪条件 = ユーザーが token 予算の逼迫を理由に明示的に再開を指示したとき。
- [T-645] **NQSV / PBS 証拠による計算ノード判定の分類条件化** — 理由: 裁定 2026-08-08: 行わない。権威は bnode hostname と affinity のまま。再訪条件 = 誤検出の実測 (CI・別施設ホスト名での実害)。
- [T-647] **bench なし correctness-only COMMIT の計測契約束縛** — 理由: 裁定 2026-08-08: 束縛の対象と数えない。numactl 等は宣言値に留まると正直に記録する現状を正とする。
- [T-676] **launcher テストの時間予算の据え置き** — 理由: 裁定 2026-08-09: 実負荷 artifact 1 件が取れるまで変更しない。[T-663] の計装が次回再発時に失敗署名を自己申告するので、それを根拠にパッケージで再提示する。根拠なき受理緩和はしない。 発火記録: 2026-08-25 の `/rulings` 全件で再訪条件「実負荷 artifact 1 件」の成立を確認した (2026-08-23 の受領証が予算 3.0 秒に対し実測 3.268 秒・負荷平均 39・codex_exit_code=0・termination_verified=True を含む)。ユーザー裁定 = 据え置きを解き、本体時間で測る形へ直す (D783)。実装は [T-1649] が持つ。

- [T-901] 床値 run の途中死に対する正式な救出経路 — 理由: **前提が崩れ、ユーザー裁定へ戻った 2026-08-18 に再訪条件が成立した ([T-1337] で D496 決定 3 を優先すると裁定、測り直し単位は落ちた構成だけへ狭めた)。事前割当 attempt registry への改訂再凍結を伴う救出経路として起票し直す。 2026-08-22 ユーザー裁定によりD510(2026-08-18)の設計・優先順位を床値/8b系にも適用する前提で実装wave [T-1484] を起票した。以後の残作業は同項で追跡する。
  (D496 決定 3)。** 当初の見送り理由「当面は新規 job で最初から再実行する」は成り立たない —
  実走マーカーが freeze の byte hash を identity として出力先非依存に排他作成され、存在すれば
  同じ freeze の再走を全拒否する (この resume 拒否は §9 項 8 の択 (a) が凍結した挙動である)。
  加えて v1 freeze の verify は毎回 repository novelty search の pass を要求し、初回観測後の
  再走と両立しない。D496 決定 3 は「比べる構成ごと測り直す」「設計上の終端は認めない」と
  定めたが、測り直しそのものが上記 2 つに塞がれている。再訪条件 = §9 項 8 の resume 拒否と
  D496 決定 3 のどちらが優先するかのユーザー裁定 (択 (b) の attempt registry への改訂再凍結を含む)。

- [T-293] F89 (perf 受理集合の食い違い) の残余 — 理由: 裁定 2026-08-13 (第 9 回 #19、(a)):
  記録だけして閉じる。**再訪条件の意味が変わった (D497)** — 計測器の有無を性能主張の権威の
  条件として扱わないと定まったため、official 化の着手がそれだけでこの項の再訪を意味しなくなった。
  再訪条件 = perf 受理集合の食い違いが certified 選択の値または受理集合を実際に変える実例が
  観測されたとき。
- [T-1045] oracle 証拠の S1 report / critic digest への露出 — 理由: 裁定 2026-08-13 (第 10 回):
  今は見送り。再訪 = 次に S1 report を再生成する wave (そこで同梱する)。

- [T-316] **R2-b-1 の (a) 追認 (native comparator 干渉残余の受容)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。干渉残余は台帳・runbook への明示記録で受容すると追認済みで、本項に残作業がない。再訪条件 = 同一 process 内 comparator 干渉の実害 1 件。
- [T-308] **百分率の固定桁 round の role 契約化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-322] **campaign-id / lock preimage への namespace 束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-310] **DW-O09 のファイル集合 pin digest (F39)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-249] **凍結 file に残る共有・サイト値の移設** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-293] の D96 手続を要し、共有・サイト値の更新実需が出ていない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-286] **未参照の予約 policy key の削除** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-273] **toolchain version に floor を課す** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-252] **dispatcher receipt への request SHA / repo commit / driver SHA の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-126] **逐次停止 v2 の attempt staging 回収順序** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。実装・main 統合・land まで完了済み。live qualification は本項の scope 外と明記されている。再訪条件 = live qualification を実施するとき。
- [T-109] **クロスプロトコル対応の裁定パッケージ** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。protocol 移植は [T-755] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-099] **凍結成果物に placeholder が入った場合の waiver 契約** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。凍結成果物への placeholder 混入が一度も観測されていない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-060] **WAL 記述から改竄耐性 / 証明可能を外す明文化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-159] **重複解決が汚染した過去成果物の救済** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-315] **陳腐化した停止理由メッセージの訂正** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-336] **候補 2 件の現行版での有効性確認** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-378] **capability 発行器の同一 process 内 caller からの隔離** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。別 process / OS capability / 署名鍵への移設が必要で、信頼境界は docstring に明記済み。再訪条件 = 同型の実害 1 件。
- [T-379] **pegasus/*.sh と calibrator の任意 binary path の閉包** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提で、正常系を狭める。再訪条件 = 同型の実害 1 件。
- [T-380] **旧 campaign 値を内包する freeze 経由の laundering** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-381] **全 receiptless 歴史成果物の遡及再分類** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-382] **T126 control の receiptless 旧 campaign pin の張り替え** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-383] **eligible_for_refreeze を receipt chain から決める** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-384] **evidence 発行と build の間の ABA / 混在 snapshot** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。source root の同一束縛と記録までは実施済み。再訪条件 = 同型の実害 1 件。
- [T-409] **EVOLVE hole 文法 v1 の実装** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(a) land せず破棄が確定し、残余 3 点は別 T へ分離済み。うち 2 件は既に非 active で、残りは [T-473] が保持する。再訪条件 = なし ([T-473] が所有)。
- [T-416] **in-domain 改竄 (rejected -> fail 等)** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。値域検査では防げず、閉じるには entry 件数上限と origin 束縛が要る同一 UID 敵対者前提の面。再訪条件 = 同型の実害 1 件。
- [T-421] **numactl prefix の代理条件の置き換え** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。Pegasus entry は numactl=() で当該分岐が発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-433] **意味的充足契約 v1 の採用 (D156 発効)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。U1〜U4 が全問採用されて D156 として発効済み。機械実装は [T-941] P6 実装 wave の所有。再訪条件 = なし ([T-941] が所有)。
- [T-436] **cap-lift 記述への実 D 番号の反映** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `docs/phase3.md` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-444] **取得経路の proof chain 束縛 (acquisition receipt 新設)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-457] **exploration campaign の resume root drift** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本文自身が「発火 artifact が無い間は設計メモ (DW-G04)」と結論している。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-463] **予算・新鮮性を cell key で数える方向** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。方向は裁定済みで、詳細設計は P3 台帳面の実装 wave の設計入力に含めると決着した。再訪条件 = P3 台帳面の実装 wave の設計段。
- [T-465] **duplicate-key parser が raw key 名を例外へ反射** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。journal に残る診断面で、受理集合は変わらない。再訪条件 = 同型の実害 1 件。
- [T-466] **auditor nits producer schema の閉形化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-468] **registry の canonical authority** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。詳細は確定し、実装は [T-470] の配線 wave に同梱すると決着した。同 wave は完了済み。再訪条件 = registry authority の実害 1 件。
- [T-477] **content-addressed path の強制と publish receipt 束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-499] **Q1/Q4 の保留と (A) 承認手番** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。Q1 = (b) 保留 / Q4 = (b) 保留で確定し、承認手番は前提 (active ratified freeze v2) が揃うまで保留のまま。再訪条件 = active ratified freeze v2 が揃ったとき。
- [T-501] **admission validator の WAL 側 ABA** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。lock 側は D170 で閉じており、残るのは bytes 同一性の保証という provenance 面。再訪条件 = 同型の実害 1 件。
- [T-502] **implementation field の build source への束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-517] **壁 1 の非認証 probe lane** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。設計項として保持し実装しないと裁定済み。要否の再評価も [T-419] U-2 の完了に従属する。再訪条件 = [T-419] U-2 の完了時。
- [T-533] **holdout 凍結の known 直接読み** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-531] の世代移行統合に同梱すると裁定済みで、統合先が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-534] **受理集合の権威の凍結 proof chain への帰属** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-535] **trust root を Python module origin と制御ファイルの閉集合へ** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-544] **name<->mask 束縛の迂回** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-531] の受入条件として同項に反映済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-569] **guided の no-build pseudo-WAL の attempt schema** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-606] **v2 oracle manifest の production producer** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。v2 manifest を要する consumer の実需が出るまで作らないと裁定済み (プロトタイプ基準 D205)。再訪条件 = v2 manifest を要する consumer が現れたとき。
- [T-660] **末尾巻き戻し検査の検出力確認** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。chain が 1 record の間は空 chain 拒否に mask され観測できない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。 2026-08-17 に旧 branch `worktree-dev-wave-t657-t660-g2-activation` を破棄した際、変異台帳 (検出力 5/5) を `output/insights/2026-08-17/t657-activation-rebuild/preserved-t657-t660/` へ保全した。再訪時は同 path を一次資料とする。
- [T-704] **receipt atomic create 後の例外で受理主張と実在が食い違う** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。既存欠陥で悪化させておらず、構成が必要な稀な組合せ。再訪条件 = 同型の実害 1 件。
- [T-705] **_atomic_publish が例外時に rollback しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同上。再訪条件 = 同型の実害 1 件。
- [T-706] **KeyboardInterrupt / SystemExit で receipt rc と process rc が分離** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同上 (診断の一貫性のみ)。再訪条件 = 同型の実害 1 件。
- [T-707] **staged temp の同一 UID 別 process による置換** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提。再訪条件 = 同型の実害 1 件。
- [T-708] **os.replace 経路の staged temp 同一性の回帰固定** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。os.link 経路は固定済みで、片側のみの欠落。再訪条件 = 同型の実害 1 件。
- [T-722] **lock/WAL の外側への authority digest 固定** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-723] **非偽造の lane marker の設計** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-735] **contract_loader_* の wire key 改名** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-747] **床値 build の toolchain 束縛** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(B) を実装し混用不可を機械検査で固定済み。残る非束縛量は手順書 §5 R-4 に明記して終端した。再訪条件 = 非束縛量 (cxx version / cmake path / module_list) が実害を出した 1 件。
- [T-748] **W-2 投入と SWO oracle 停止点の特定** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。実作業の所有は [T-971] (原因と診断) と [T-1094] (FetchContent の閂) へ移り、本項は W-2 の歴史的証拠への参照になっている (敵対レビュー A の指摘を親が受け入れた)。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-763] **65 env x 2 世代の合成 calibration 成果物** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。作らないで確定済み (段階導入の原則に反する)。再訪条件 = 同層の受理集合を変える変更時。
- [T-783] **S-3 (a) attempt 脚と成果物への binding report 追記** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-797] **設計正本 §11.2 の row 抽出が表形式を取りこぼす** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-803] **pinned literal を人間承認の恒久形として承認** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。承認済みで、記入時点は将来の実凍結手番と決着した (署名方式は不採用維持)。再訪条件 = なし。
- [T-816] **凍結チェーンが gitlink 前進を塞ぐ件** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。手順 4 を完了し、D328 の保留執行で閂を外して受入も赤ゼロにした。再訪条件 = 凍結チェーン検証の保留を解除するとき。
- [T-833] **WAL と stdout への共通 execution nonce** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-859] が同一内容を裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-838] **hard block (凍結 v1 raw trace と歴史 pin 再現経路)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-816] の裁定へ吸収され、実体 (bytes 据置での trace 再検証退役と歴史再現 driver の記録) も処理済み。再訪条件 = なし。 2026-08-22 再検査 (dev-wave-t839-verifier-v2-trace): `validate_raw_bundle` (`orchestrator/campaign/silo_ladder_rung1.py:2770-2882`、CLI `collect`/`verify-result` から到達可能) の `verify_trace_dir` 呼び出しは `fb5e74a1` で変更されておらず、tracked v1 raw bundle (`0_873920.nqsv`) に対し実行すれば未捕捉 `ParseError` で停止する。現行テストは witness-only 検査に置換済みで到達しないため受入は緑 (crash であり false-green ではないため絶対規律2には抵触しない)。再訪要否はユーザー判断に委ねる。 2026-08-23 /rulings 全件で再訪要否を裁定 = **再訪しない**。現行テストは当該経路へ到達せず受入は緑で、旧形式の束を実際に流す consumer も現存しない。停止するとしても crash であって偽の緑ではないため絶対規律 2 に抵触しない。再訪条件 = 旧形式 raw bundle を実際に検証する必要が生じたとき。
- [T-840] **copyout 系 Q1〜Q5** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。全問親推奨どおり裁定済みで、Q4 は既存 cache entry の拒否・再発行をしないと決着した。再訪条件 = なし。
- [T-857] **legacy manifest 由来 observations の位置づけ** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。明文化のみで終端と裁定済み。certified への到達は [T-804]/[T-856] 側が閉じた。再訪条件 = なし。
- [T-862] **公表台帳の予約 writer を land lock 内へ** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。着手条件の R2 は [T-793] で保留終端となり発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-883] **性能値主張時の dispatch receipt の worktree 外退避** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-913] **公表台帳 R2 番人 4 function の保留可否** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置を追認済み。保留したい場合は D320 とは別の個別裁定を新たに取ると決着した。再訪条件 = 個別裁定を取るとき。
- [T-915] **holdout live scan の保留可否** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。保留対象外で確定し、ファイル数比例をやめる最適化として [T-902] 実装側が扱うと決着した。再訪条件 = なし ([T-902] が所有)。
- [T-942] **材料レポート renderer の結線 (V-12)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。P6 実装 wave へ同梱すると確定済み。残は V-8 のみで別 ID が保持する。再訪条件 = なし ([T-941] が所有)。 2026-09-03 の [T-941] wave で V-12 の同梱を見送った。段 3 の 2 レンズが独立に「P6 が `NOT_IMPLEMENTED` のまま繋ぐことは本項の裁定理由に反する」と判定し、親が採用した。裁定候補 U3 (延期するか、P6 不在でも診断専用の非完全 projection を許すか) をユーザーへ返す。親推奨 = 延期。 2026-09-03 の /rulings 第 5 回で裁定。P6 の認定完了まで延期し、P6 不在でも診断専用の非完全 projection として繋ぐ例外は作らない (D1566)。見送り台帳に留め置き、再訪条件 = P6 の認定完了。
- [T-955] **guard bytes 期待値の trust root** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置で確定済み。独立 trust root・launch receipt 化はいずれも作らないと決着した (粗い provenance 基準)。再訪条件 = なし。
- [T-961] **strict extension 保証の直接テスト** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-962] **B4 の第 5 案** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(c) 今は足さないで確定済み。再訪条件 = manifest R1 (Q-D の同一 land 再解釈) の裁定後。
- [T-965] **PRNG byte grammar の事前登録文書への昇格** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置で確定済み (段 4 裁定 + transcript で足り、grammar 選択は結論を左右しないと感度実測済み)。再訪条件 = なし。
- [T-969] **予約式の見直し** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (全滅系は journal 早期停止で有界化済み)。再訪条件 = 予約超過の実測 1 件。
- [T-970] **perf_candidates の採用** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (「使わないが evidence として記録」の現状維持)。再訪条件 = F89 の裁定時。
- [T-988] **Q1/Q4 保留下の機構状態** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。裁定済みで、実装項目は別タスク・機構は fail-closed 維持と決着した ([T-499] と同束)。再訪条件 = [T-499] の保留が解けたとき。
- [T-1006] **_durable_json の read-back 検証** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。short-write ループと fsync は既に持ち、欠けるのは read-back のみ。再訪条件 = 同型の実害 1 件。
- [T-1070] **axis_trigger_gating.py の sha256 と記録値の不一致の整理** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-1088] **receipt を持たない旧 portable artifact の棚卸し** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-1104] **_write_create_only の truncated JSON 残留** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。共有 helper のため consumer 全体の受理集合に触れる割に、書き込み途中失敗の観測がない。再訪条件 = 同型の実害 1 件。

- [T-1094] 床値 build 経路への `FETCHCONTENT_SOURCE_DIR_*` 配線 — 理由: 2026-08-15 /rulings 全件の
  裁定 = (a) 実装しない。起票時の前提 (計算ノードで FetchContent が通らない) が計算ノードの実測で
  反証され (`SOURCE_DIR` 無しの configure が rc=0 / 5.520 秒)、かつ network 経路のほうが
  正しさで優る (GIT_TAG pin の fresh clone は汚染を持ち込まないが、共有 source tree は build 自身が
  書き換える対象で実測 71 件の生成物を抱えていた)。設計判断は D412。床値クラスタの残作業は
  [T-1128] へ移る。再訪条件 = offline 再現性が実需になったとき、または network 経路が実際に
  計算ノードで落ちたとき。

- [T-339] **RF consumer の独立 task としての保持** — 理由: 2026-08-17 裁定 (陳腐化 = 所有が別 ID へ
  移り本項は参照のみ)。ユーザー裁定 (2026-08-16) の択 B により
  `producer → pilot → validator/consumer` を 1 scope へ戻したため、残作業の所有は [T-338] が持つ。
  完了ではない。再訪条件 = 後続裁定が [T-338] から consumer の所有を再分離したとき。

- [T-1216] **ratified document 内 `floor_protocol.path` pointer の namespace 束縛** — 理由:
  2026-08-20 /rulings 裁定 (b)。[T-1436] の残る限界4番と同一論点。封印済み記録を書き換えられる
  立場は記録作成の権限者と同じであり単独の実害シナリオが薄い。一次資料 = `docs/decisions.md`
  D589「残る既知の限界」節。再訪条件 = [T-1436] の再訪条件と同時 (floor protocol の実 consumer
  結線が始まる wave の着手時)。
- [T-1436] **床値再封印の残る限界5点、実 consumer 結線まで様子見** — 理由: 2026-08-20 /rulings
  裁定 (a)。仕組みは dormant (未結線) で実害ゼロ。一次資料 = `output/insights/
  2026-08-16_floor-reseal-authority/README.md`「残る限界」節 (1: pin 前進での測り直し抜け穴、
  2: 同一組の複数回実走・[T-1140] 問1と関連、3: 履歴不変条件は凍結チェーン保留 (M-7) に従属、
  4: ratified pointer の namespace 制約欠如は [T-1216] へ集約、5: 共有 helper の同型注入面は
  DW-G03 の独立2例要件が未充足のため対象外)。再訪条件 = floor protocol の実 consumer 結線
  (g2 環境契約の活性化と同一 chain) が始まる wave の着手時。

- [T-1996] **正式 S8b の cache 同一性を root-neutral 化する案** — 理由: 裁定 2026-08-27
  (/rulings 全件、推奨どおり): 採らない。root-neutral 化は cache の受理集合を広げ、
  正式測定の意味互換性が別途証明されない限り測定の意味を変えうる
  (D1220)。
  再訪条件 = 意味互換性が独立に証明されたとき、または cache hit 不在が測定予算の支配項になったとき。

- [T-096] driver 側 timeout を予約式と整合させる — 理由: 裁定 2026-08-29 (/rulings 全件、分類不能 8 件の
  帰属を確定): 2026-07 の裁定済み実装待ちのまま 1 か月動いておらず、論文の主張にも受理集合にも触れない。
  再訪条件 = timeout と予約式の不整合による実害 1 件。
- [T-1658] `sort_best` cell の build cache が job を跨いで必ず cold な件の是正 — 理由: 裁定 2026-08-29
  (/rulings 全件、推奨どおり見送り): **cold を前提に所要を見積もる**側を採る。是正は
  `fetchcontent_archive_sha256` を含む cache preimage の変更を伴い凍結面に触る。cold を明示して
  見積もれば科学的な虚偽はない。再訪条件 = 床値 campaign の所要が cold 前提の見積りを超えたとき。
- [T-1659] `valid: false` の材料レポートから packet 由来の axis ledger を外す — 理由: 裁定 2026-08-29
  (/rulings 全件、推奨どおり見送り): 宣言は「certified なのは `valid` だけ」であり虚偽ではない。
  report shape と受理集合を変える費用に見合わない。再訪条件 = 同型の実害 1 件。
- [T-1906] 実走での要求待ち量の分布を測る診断ビルドの新設 — 理由: 裁定 2026-08-29 (/rulings 全件、
  推奨どおり見送り): 段 4 で既に scope 外と裁定済みで、診断ビルドの値は D20 により headline に使えない。
  再訪条件 = 機序説明の帯域外拡張 ([T-1905] 系) が診断値を必要と確定したとき。

- [T-2151] 実 CLI の remote serialization bytes を捕捉する観測点 — 理由: 裁定 2026-09-02
  (/rulings 全件、推奨どおり見送り): D962 は捕捉を必須とせず open と明記する側を許している。
  外部 provider へ向けた通信の観測基盤は現在の主張水準に対して過大で、従量経路や代替 provider
  配線を作らない規律にも近接する。事前登録 §4 の領域 (ii)(iii) は open のまま明記する。
  再訪条件 = 当該領域の主張を headline へ昇格させる必要が生じたとき。
- [T-2152] provider 応答からの不可視性を測る手段 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): 上項と同じ天秤。未測定のまま open と書けばよく、fake runner を証拠へ
  昇格させないことが要点である。再訪条件 = 同左。
- [T-2168] 軸 1 実行器と軸 3 実行器の重複の統合 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): transport 部品は似ていても catalog・語・枝・cutoff・完走述語が別物で、
  統合は自明でない。共通化は既にユーザー指示で scope 外とされており、現在の主経路に
  統合の利益が示されていない。重複範囲の記録だけを維持する。
  再訪条件 = 二重保守が実際の契約乖離を生んだ 1 件。

- [T-2196] archive の独立期待権威の他 consumer への展開 — 理由: 裁定 2026-09-03 第 6 回
  (推奨どおり): D1469 が既に対象 file の所有解消まで保留と決めており、本項はその再確認である。
  実害の観測がない。再訪条件 = D1469 と同じく対象 file の所有解消、または実害 1 件。
- [T-2282] calibration の依存道具の内容 hash を receipt へ束縛する — 理由: 裁定 2026-09-03
  第 6 回 (推奨どおり): D320 の粗い provenance 方針と、同じ面で cmake の realpath 束縛を
  見送った先例に従う。絶対 path 固定と path / version の記録までで止める。
  再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-2286] 集約が全ジョブの終端を機械的に確かめる経路の新設 — 理由: 裁定 2026-09-03 第 6 回
  (D1601、推奨どおり): D1590 の「完全性は開示であって
  受理規則にしない」境界を維持する。block record 側の検査は現に効いている。
  再訪条件 = 未終端ジョブの部分結果が集約へ入った実害 1 件。

- [T-2028] 軸 3 の登録済み検索の実行 — 理由: D1931。
  完走して得られるものの上限が低く (7.7.3)、費用は live preflight だけで外部 request 1929 本・
  約 19.5 時間、主目的の CC 自動合成を 1 歩も進めない。軸 3 は `RW0` 据え置きで
  世界の不在を主張しない。凍結物・登録 seal・実装は残すので、再訪条件が成立すれば同じ登録から始められる。
- [T-2567] 軸 3 の resolver と control 評価器の実装 — 理由: 走らせない決定
  (D1931) により前提が消えた。実装しても完走で得られるものの
  上限は変わらない。
- [T-2568] DBLP 題名 lookup 5 本の意味的 amendment — 理由: 同上。走らせないので
  anchor 到達性を閉じる必要が無い。
- [T-2569] 軸 3 の未確定 attempt intent の回復強度の裁定 — 理由: 同上。走行が起きないので
  再開の強度を今決める理由が無い。実装済みの範囲 (通信失敗は in-process で処理し
  未確定 intent を残さない) はそのまま残る。
- [T-2570] 軸 3 transport の本体 byte 上限と wall-clock 上限の裁定 — 理由: 同上。
  socket timeout 30 秒だけが停滞を縛る状態のままとし、走らせる決定が出たときに再訪する。

### プロセス文書系

- [T-040] **CLAUDE.md 作業手順 5 への provenance pointer 配線** (B-032, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — hot path への provenance pointer を承認し現行導線に無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-041] **workflow 要旨返し規律** (B-059, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — workflow 出力を context 境界越しに使い必須 summary schema が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-042] **fan-out 3 本以上の multi-agent 規則** (B-033, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 比較可能な 5 run 以上で独立 task が 3 未満かつ起動・統合・手戻り時間が並列短縮を上回る時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-043] **ultracode 常時オンの見直し** (B-034, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 既定利用が rate/cost 制約を生むか監査品質差を実測した時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-044] **Codex runtime の nested tool exact allowlist** (B-036, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — native runtime 再開をユーザーが承認し exact allowlist または denied-event E2E が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-045] **Codex hook adapter と parity test** (B-037, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 安定した Codex tool-input contract が得られ parity test が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-046] **07-12 (6) の無名「ほか should-fix」** (B-039, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 一次資料から未包含の named should-fix が復元された時。裁定 2026-07-19 保留承認 (現状は裏取り不能)、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-047] **S6 盲検で入力構成への言及禁止** (B-040, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 新しい blind proposal 設計で入力構成への言及禁止が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-048] **S6 c1「軸」定義の明文化** (B-041, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — c1 / axis を rubric で再利用し作用点と政策集合の意味論が未固定の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-049] **Phase 1〜2 failures 4 件の回収** (B-042, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 新 review が Phase 1/2 または該当 failure path を対象にし 4 件が未索引の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-050] **新 workflow 起動前の model lint 継続規則** (B-043, 出所 `docs/worklog.md`) — workflow script を追加・変更し候補へ model lint を未実行の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

- [T-314] 裁定待ちの目印の正規化 — 理由: (130) の再裁定で [T-294] の補助へ降格し、機械検査に持つかは実装 wave が決める。
- [T-228] effort 値域検査と receipt 側 effort 記録 — 理由: (101) の裁定で D74 (6) の real 開放前ユーザー裁定へ併合済み。
- [T-236] transport と domain result の分割 — 理由: (94) の裁定 (b) で実装せず設計を凍結した。分割の必要が実際に生じた時点で再評価する。
- [T-226] 段 2 (`DW-S02`) の reasoning 見直し — 理由: (90) の据え置き裁定。段 2 限定の測定が得られた時点で再評価する。
- [T-253] `dev_waves` の main-dirty gate の恒常発火 — 理由: 実害未確認の観測にとどまる。daemon 経路の運用が始まった時点で再評価する。
- [T-240] 段 1 前の所在・所有確認と族横断要求の `DW-S01` 追記 — 理由: (88) の裁定で予算配分の束として [T-208] / [T-219] と扱うと決まり、単独では着手しない。
- [T-210] git リポジトリ整理の恒久化 — 理由: (74) の据え置き裁定で優先度低。履歴監査の根本解決は完了済みの [T-205] が担った。
- [T-150] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。
- [T-151] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。
- [T-012] task-run pilot の凍結解除可否 — 理由: (33) の裁定で解除しないと確定した。復活させる場合は新規に裁定を起こす。
- [T-170] CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う。

- [T-648] 受入免除判定の証拠記録義務の契約本文への明文化 — 理由: 義務は fallback
  (本エントリ + memory) で発効済みで、契約 1 文の追加は dev-wave docs 予算 (空き 1 byte) に
  入らない ([T-641] (c) 同型)。再訪 = [T-313] 実装などで `docs/dev-wave/**` 予算に空きが
  出たとき、本文 1 文への昇格を再検討する (2026-08-09 ユーザー裁定 (B') による再訪条件)。

- [T-635] DW-S01 の「decision 本文」の射程明文化 — 理由: 2026-08-09 ユーザー裁定で (b)
  F158 の恒久対応 (failures 台帳の再発検査レンズ) で足りるとした。再訪 = [T-664] の予算裁定で
  空きが出たら (a)「成立済み台帳に限る」の明文 1 行を再検討。

- [T-317] **親が子に書かせる規律の射程** — 理由: 裁定 2026-08-10 (b): 射程は repo へ入る artifact に限る。wave 運転用の使い捨て script は repo 外に置く限り射程外で親が直接書いてよい。worktree session の Bash 複雑度制限との衝突は解消。
- [T-454] **子起動の単一経路化 (R1)** — 理由: 裁定 2026-08-08: 現状維持。再訪条件 = 子起動由来の実害、または R8 安全前提を満たす実需。R5 は [T-577] 裁定が、R4 は [T-625]/[T-632] が解消済み。
- [T-537] **docs-only wave の変異・受入射程と軽量版の境界** — 理由: 裁定 2026-08-06: (a) は [T-577] の優先列で扱う (所有移管)。(b) は現行慣行の追認とし規約化しない。
- [T-545] **`DW-O11` 第 2 文の機械化 (acceptance mode + receipt + land 消費)** — 理由: 裁定 2026-08-06: 起票者推奨どおり見送り。正本 = `output/insights/2026-08-05/t450-t412-preface/README.md` §3 R1。
- [T-555] **admission registry の `reason` / `primary_gate` の docs 投影** — 理由: 裁定 2026-08-06: 行わない (プロトタイプ基準)。`submit_silo_ladder_rung1.sh` の説明齟齬は実測時に手で直す運用のまま。
- [T-556] **分類 claim を書ける living doc の閉集合化** — 理由: 裁定 2026-08-06: 行わない。検査対象を runbook と Pegasus README に限る現状を正とする。
- [T-558] **`DW-M08` への kill 判定明記** — 理由: 裁定 2026-08-06 ([T-577] 傘下): 回収 207 bytes の優先列に入らないため見送り。予算の独立審査は行わない。教訓は worklog (258) と `output/insights/2026-08-06/t454-testification/ruling-package-drafts.md` が保持する。
- [T-576] **dev-wave 子起動の単一経路化 (二経路の統合)** — 理由: 裁定 2026-08-06 (c): 行わず現状の二経路を受容する (プロトタイプ基準)。摩擦の最悪部は guard 解析強化が対処する。
- [T-616] **見送り裁定と依存タスクの突き合わせの機械化** — 理由: 裁定 2026-08-07 (b): 起動読了の prompt 規律に留める。fold 時の相互参照機械化は D205 基準で不採用。都度訂正は規律の下位互換として併存。
- [T-640] **fragment と fold の「同じ変更単位」要求** — 理由: 裁定 2026-08-08 (α): fragment が wave commit 時点の署名済み決定であり fold は採番と転記だけ、という解釈で充足と認める。不可分性は wave commit が担保する。
- [T-641] **予算超過で撤回した恒久対応の扱い** — 理由: 裁定 2026-08-08 (c): failures 台帳と memory の記録で担う。予算の独立審査は行わず、縮約余地も尽きていると実測済み。「制度化条件を満たした改善が予算で止まる」構造は受容する。
- [T-661] **段 8 改善 2 行の dev-wave 参照文書への本文編集** — 理由: 裁定 2026-08-08: 行わない。台帳の記録 (F169 と F112 独立 2 例目) で担う。節の削除もしない。再訪条件 = 同型失敗の再発で本文契約化の実需。
- [T-664] **docs 予算の 2 経路審査** — 理由: 裁定 2026-08-09 (R1〜R5 全問推奨どおり): 2 経路とも予算は空かないと確定して閉じる。R4(a) の需要は [T-313] の実装へ集約済み。正本 = `output/insights/2026-08-08/t664-docs-budget/package.md`。
- [T-666] **規範文 pin の強度** — 理由: 裁定 2026-08-08: 意図した設計として受容する。再訪条件 = 正当な文面改善の需要が実測で頻発したとき。
- [T-667] **`DW-S05-A` の `high` と `DW-S06-B` への pin 拡大** — 理由: 裁定 2026-08-08: 行わない (防御的堅牢化、D205 既定。`DW-S05-A` は D207 の pin が別途ある)。再訪条件 = 当該節の drift の実測。
- [T-668] **CR-only 改行の文書への対応** — 理由: 裁定 2026-08-08: UTF-8 / LF 契約の想定外入力として非対応とする。checker は変更せず、非対応の明示は本台帳の記録が担う。
- [T-679] **preflight / publication 失敗時の早期 receipt** — 理由: 裁定 2026-08-12 (同基準): 置かない (プロトタイプ基準)。
- [T-686] **insights `verbatim/` 配下の guard 対象外明記** — 理由: 裁定 2026-08-09: 逐語凍結の場として placeholder guard・三軸語検査の対象外とし、明記は本台帳の記録が担う。再帰 guard は作らない (D205、過去逐語への偽陽性を避ける)。再訪条件 = 実害。
- [T-687] **xdist internal error / pre-item crash の診断項目化** — 理由: 裁定 2026-08-12 (プロトタイプ基準): 診断項目は増やさず既存 xdist summary を正本と定める。
- [T-689] **dispatch 中継の耐久経路** — 理由: 裁定 2026-08-12 (同基準): best-effort の中継を正とする。耐久経路も手順追記もしない (プロトタイプ基準)。
- [T-691] **終端ダイジェスト failure stash の session 束縛化** — 理由: 裁定 2026-08-12 (同基準): module global のまま現状維持 (経路実在未確認、回帰 pin 維持)。
- [T-695] **`DW-O25` の trigger の preflight 契約化** — 理由: 裁定 2026-08-11 (a 受容): 現行のまま維持する。(b) L1 再分類は §60 既裁定の不採用を維持。再訪条件 = 条件 25 の読み違いによる実害 1 件。
- [T-701] **全層 + event 加重の複合 envelope** — 理由: 裁定 2026-08-09: 作らない。unique footprint との乖離 (10,625 vs 12,670) は台帳記録が担い、読み過ぎは JIT 読みの規律で抑える。再訪条件 = 実害。
- [T-716] **s8c candidate 3 node の canonical group 移動** — 理由: 裁定 2026-08-11 (見送り): 単独では行わない (+58.35 秒の受入増、t553 の git 時間予算定数の前提破壊)。排他閉包の体系化は [T-826] (M0) の設計で一括判断する。
- [T-738] **待ち手の pid 死判定禁止の明文化** — 理由: 裁定 2026-08-10 (c): memory (`waiter-death-check-by-pid`) と F32 の記録運用を正とする。L1 の圧縮審査と予算の独立審査は行わない。再訪条件 = pid 判定由来の実害の再発。
- [T-743] **レビュー子の欠陥判定基準の `DW-S06-A` 統合** — 理由: 裁定 2026-08-10 (c): wave ごとに prompt へ手書きする現運用を正とする。統合は L1.5 予算 191 bytes 超過のため行わない。再訪条件 = 手書き漏れの実害 1 件、またはテスト化で 191 bytes の見込みが立ったとき。
- [T-760] **`DW-O01` への `--sandbox` caller 必須の規範化** — 理由: 裁定 2026-08-11 ([T-786] 審査): L1.5 の残余は 2 bytes で再訪条件「余白が出たとき」は成立しない。
- [T-774] **待ち手 rc を受入証拠と誤読させない機械化** — 理由: 裁定 2026-08-11 (b 現状維持): 誤読の実例はゼロで、受入完了の証拠規律 (成果物実在 + done marker + producer 死の 3 点照合) が別途確立しているため機械化しない。再訪条件 = 誤読の実例 1 件。
- [T-786] **docs 予算の未入庫 6 件の棚卸し** — 理由: 裁定 2026-08-11 (審査受諾): 予算引き上げは行わない ([T-127] 既裁定と整合)。被覆項の終端化は本 wave で実施した ([T-789]、[T-788]、[T-760]、[T-738])。正本 = `output/insights/2026-08-11/t786-docs-budget/verbatim/package.md`。
- [T-788] **`DW-O02` への制御 byte 走査の入庫** — 理由: 裁定 2026-08-11 ([T-786] 審査): docs でなく機械検査で閉じるため [T-825] へ移管した。
- [T-789] **`DW-O02` への必読 path 実在確認と正本不変の入庫** — 理由: 裁定 2026-08-11 ([T-786] 審査): (3) は `DW-O18` へ入庫済み。(1)(2) は 105 bytes 必要で入らず、既存義務が実質的に (2) を覆う。再訪条件 = 同型の空費が 2 例目に達したとき。
- [T-813] **受入全走のノード横断分割** — 理由: 裁定 2026-08-11 (package どおり 4 点): いま入れない (2 通りの分割の両方で別々のテストが静かに消えた実測 = 「全走が緑」の意味が分割の取り方に依存する、規律 2 の面)。M0 = [T-826]、M5 = [T-827] として起票済み。再評価条件 3 つを確定。正本 = `output/insights/2026-08-11/t813-acceptance-sharding/`。 2026-08-23 に D724 で Pegasus LOGIN の受入形に限り既定有効化した (2026-08-11 の「いま入れない」判断は D711 の 6 段 gate 着地で解消済み)。

- [T-261] **provenance scope / Codex-author epoch の per-lineage 判定** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-262] **--message-file preflight への exact waiver 排他** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-263] **provenance dispatch の data row 束縛の fail-closed 化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-245] **codex/p3-autonomous-trial branch の残務** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起票時に本文が途中で切れており内容を復元できない。branch 自体は取り込み済みと本文が述べている。再訪条件 = 同 branch 由来の未回収成果が具体的に判明したとき。
- [T-234] **完了 wave の handoff 3 件の残置と削除責任者** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。現行 main の docs/handoff は README のみで残置ゼロ。削除契機の恒久化は [T-1038] が所有。再訪条件 = なし ([T-1038] が所有)。
- [T-348] **fold 適用後 git add 前の SIGKILL からの自動 rollback** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。fail-closed で止まり false green にはならない。手動回復で足りている。再訪条件 = 同型の実害 1 件。
- [T-353] **FOLDED receipt の canonicalized body digest 化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同じ本文を別 seq で再投入する攻撃者を前提とする面。再訪条件 = 同型の実害 1 件。
- [T-365] **fold 署名 2 条件を heuristic と明記して現状維持** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (b) で現状維持が確定し、意味検証は [T-347] の単独所有と決まっている。再訪条件 = なし ([T-347] が所有)。
- [T-366] **receipt schema への tested main cutoff の永続化・binding** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-413] **記録誤りの検出を入口へ書き足すか** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (d) で書き足さないと確定し、検出は稼働 wave の前提実測と収集経路が担うと決着した。再訪条件 = なし。
- [T-557] **過去 commit checkout での防壁の版** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状是認で裁定済み。外部の最新 hook を維持する設計は起こさないと決着した。再訪条件 = なし。
- [T-590] **競合なし auto-merge の実装面 path の扱い** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。恒久策 (merge 判定を path から内容へ寄せる) は [T-938] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-598] **前向き収集の律速** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。収集の login 結線は作らないと [T-1029] (b) で裁定され、残る修正は [T-999] が所有する。再訪条件 = なし ([T-999] が所有)。
- [T-621] **監査結果を消費しない層 (land が full-history を強制しない)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-680] **不在の証明の表現規約** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。「N 回連続緑。不在は主張しない」の正直形に固定すると裁定済み (規律 3 整合)。再訪条件 = なし。
- [T-791] **DW-S07 へ正本化する規則の差し替え** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。内容は [T-836] (c) と同一で、収容は docs 予算に従属する。再訪条件 = docs 予算に余白が出たとき ([T-959])。
- [T-800] **_rollback_fold の state 型検査を復元 try/except の後の独立 phase へ置く** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。rollback 途中失敗という稀な窓の堅牢化で、実害の観測がない ([T-801] と同面)。再訪条件 = 同型の実害 1 件。
- [T-801] **rollback lifecycle の 3 細部欠陥** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。いずれも同一 UID 敵対者または稀な例外時の窓で、実害の観測がない。再訪条件 = 同型の実害 1 件。
- [T-825] **制御 byte 混入の機械検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。NFC 検査の追加は [T-855] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-836] **受入数値の正本を insights + land 報告にする** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(c) で裁定され運用としては確立済み。docs への正本化は [T-791] と同じ予算制約下にある。再訪条件 = docs 予算に余白が出たとき ([T-959])。
- [T-891] **fold commit への transaction ID 刻印** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状維持で終端と裁定済み (D320 の見送り側 — commit 級 provenance)。再訪条件 = なし。
- [T-1008] **index 意味比較が index extensions を見ない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/tests/test_codex_reasoning_ab.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-1037] **land 済みで撤去不能な docs/handoff 残置** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。現行 main の docs/handoff は README のみ。checker 側の恒久修正は [T-1038] が裁定済みで所有。再訪条件 = なし ([T-1038] が所有)。 2026-08-15 に所有先の [T-1038] が checker 側の恒久修正を実装した (main landed だけを通す)。再訪不要。
- [T-1039] **docs/handoff 滞留による起動検査の恒常赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。952fd45d で滞留 handoff を撤去済みで、2026-08-15 の check_wave_startup.py は rc=0。構造的な再発防止は [T-1038] が所有。再訪条件 = なし ([T-1038] が所有)。 2026-08-15 に所有先の [T-1038] が checker 側の恒久修正を実装した。S-2 (README の削除契約) は裁定どおり現状維持。
- [T-1099] **受入 waiter が checker receipt を再検証しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。checker 側が壊れた場合の二重防壁で、倒れる向きは fail-closed。再訪条件 = 同型の実害 1 件。
- [T-1106] **receipt 本体生成の例外がどの段か分からない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-1108] **acceptance-scheduler-attestation 段の detail が絶対 path と repr を載せる** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID の受入 log を読める者にしか届かず、非漏洩規律の拡張は正常系の診断を狭める。再訪条件 = 同型の実害 1 件。

- [T-1102] gate 導入前に起動した待ち手の被覆外の窓を閉じる案 — 理由: 2026-08-15 /rulings 全件の
  裁定 = (c) 現状維持。親推奨は (b) 経過措置だったが、**稼働中 wave 0 本の実測**により当時の
  待ち手は既に全滅しており窓は空である。経過措置という新概念と 2 段活性化を導入して得るものが無い。
  再訪条件 = 同型の gate を長期稼働の待ち手がいる状態で導入するとき。

- [T-1168] 理由: 2026-08-16 /rulings 全件 第 2 回、択 (d) 見送り。`DW-O01` への 1 文追記は行わない — 追記しようとした文言そのものが同 wave 中に反証されたため。条件付きだった「背景 task の完了通知が producer 稼働中に発火する実測を failures 台帳へ記録すること」は F352 (2026-08-16、6 件以上の実例と DW-O01 既定規則の実証記録) で充足済みと本 wave が確認した。再訪条件 = 同型の見落としが F352 の 3 点照合を経てなお再発したとき。

- [T-213] 択 (a) 採用 — 隔離複製の置き場を共有ファイルシステムへ移す。検査の実行場所契約を変える案は受理集合と実行場所の両方を動かすため影響が広… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-309] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-305] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-298] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-300] ログイン側の headroom admission gate は本 wave で実装・受入・変異まで 完了した (D209)。**残るのは本丸… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-301] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-294] 択 (a) 採用 — 着地直前の再収集を手順へ入れ、収集は判定語に依存しない形にする。2026-08-25 の全件収集で、語で絞る収集が変種を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-248] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-280] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-270] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-255] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-254] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-258] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-231] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-233] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-212] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-211] 択 (a) を緩い形で採用 — 完全一致ではなく「見出し文が大幅に変わったら警告」とする。carry 検査の強化 (本 rulings 第 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-223] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-347] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-349] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-351] /rulings の収集経路に、現 branch の valid pending fragment を加える。記録先は spool へ変えたが… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-354] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-355] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-364] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-368] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-370] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-388] 専用の一時ツリーへ隔離する (D1217)。 **着手前に、除外集合の導出を変えた裁定 (同日着地) の後でも再現するかを確かめる。** 20… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-389] まず現状を実測する。射程の訂正 = 受入ツールが自分で main を merge する経路と、着地 tip を指定して再走を避ける経路が既に在… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-392] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-411] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-442] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-448] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-456] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-464] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-467] 択 (a) 採用 — 合成のみの merge の記録規則 (著者出所行 / waiver / 判定変更のいずれか) を明文化する。D770 が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-491] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-508] docs/dev-wave 予算は機械検査・ ツール化への移管 (b) を主、陳腐化削除 (a) を従として余白を作る。(c) 予算の独立審査… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-511] 択 (b) 採用 — 任意コマンドを計算ノードへ送る汎用の投入種別を足す。初回走行の規定を足す案は「1 走目はログインノードで」を制度化する方… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-515] 択 (b) 採用・現状維持 — 指紋の導出は変えない。certified 選択に入らないため実害は台帳の重複だけで、導出変更は複数の利用側を持… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-518] 択 (b) 採用 — ディレクトリ移動を追跡しない穴と再帰打ち切りの穴を先に閉じ、引数形式の差と起動方式の穴は測定経路の裁定と同時に決める。後… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-520] 資源分類の実測がユーザー端末の手番である ことを docs/pegasus-runbook.md §7.0 と tools/README.md… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-526] python3 -m orchestrator.campaign.s8c_preregistration check が二重 import で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-550] 択 (a) 採用・制度化 — 使い捨て試験コードの規模上限を族として制度化する。独立 2 例で閾値を満たしている。制度化の中身は文書 1 行な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-591] tools/pegasus/fetch_third_party.py を admission registry へ local-ok として登… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-599] ログインノードでの build 解禁は、**そもそも今も必要かを先に確認する**。この項が「ユーザー依頼の未達」と記録されて から時間が経ち、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-604] ログインノードの bounded scope 実行が memory.max / memory.oom.group を走行中に attest で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-611] tools/mutation_worktree.py の分類 実測は、軽い複製への変更 (裁定済み) の実装後に行う — 今の重い clone… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-612] 択 (b) 採用 — 実残骸の場所を観測してから設計する。中止時の自動片付けは docs 予算に阻まれた収容として D782 の AI 側処理… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-613] tools/mutation_harness.py が run_tests.py へ D209 決定 10 の --force-dispatc… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-617] orchestrator/tests/test_pegasus_tools.py:632 の _acquisition_probe_docum… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-620] --runner-mode の経路要求と spec / out の置き場は docs 追記でなく変異ハーネス側の機械検査にする ([T-508… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-637] 条件 dispatch の parser が 3 列未満または backtick path 不一致の行を黙って無視する挙動を、無視でなく赤にす… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-638] tools/claude_session_ledger.py (既定 argv) は計算ノード 2 台・有効 5 走で charged del… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-650] land が到達点ごとに release_safe / retryable_same_request を宣言し、 両方成立するときだけ受入 l… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-659] 対象は列挙できる閉集合に限り、機構は作らず手順で担う (発行 tool の head 書込み案は不採用)。 活性化専用の作業窓を手順で置き、採… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-669] dev-wave の子投入 preflight に local main の SHA 比較を 足す。現状は親の手検査で代替しており、並行 wa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-681] 親が実編集 probe を行う前に作業ツリーが clean で あることを機械確認する。未 commit の子成果がある状態での復元は復旧不能… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-693] tools/wave_land_window.py の claim は 非 acquired (held / queued / stale-h… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-711] docs/spool/failures/ の fragment に **更新 節を足す** (対象 F と差し替える行を base diges… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-713] [T-692] R3 = (a) の裁定に基づく起票。 実 repo を読む重い git テスト群 (s8c candidate、ruleop… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-724] tools/spool_fold.py:1151 の carry_re が 変わらず (前エントリ参照) という序数なしの旧形式 stub を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-754] tools/check_wave_startup.py は local main との乖離と handoff の実在を見るが、**同じ wor… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-777] 住所構造 lint を受入経路で 走らせる形だけ入れる。偽 edge (Markdown 意味解釈) の対処は却下維持 (DW-G03 独立… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-778] 期待 node の完全一致と走行範囲の 絞りの注意は runner 側の検査・警告にする ([T-508] (b))。DW-M08 への追記は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-782] Q1 は読み替える、 Q3 は生成点で凍結し世代更新と対にする、Q4 は既存設計資産を起点にする。 Q2 は D992、Q5 は D961 で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-826] M0 = 受入テストの分割不変性と real-repo 排他閉包を機械検査で成立させる。排他閉包の欠落は 分割と無関係に同時 dispatch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-830] tools/check_docs.py の fence scanner が indent を**表示 column ではなく文字数**で数えて… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-835] 択 (a) 採用 — 固有条件で確立した直し方 (slot + nonce の先行固定) を一般規範へも適用する。「条件を満たす方法が存在しな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-845] --artifact-root の親 dir 取りと <root>/<wave>/<job-id> の事前作成は dev_wave_codex… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-846] test_p3_s4_loop.py::test_checkpoint_direction_and_magnitude_domains_mat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-853] 択 (a) 採用 — 文面を「実装面差分ゼロ」にする。誤分類の向きが免除拡大であり絶対規律 2 の面に当たる。「実装面」は入口が既に定義済みの… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-855] 択 (a) 採用 — 分解済みの 2 行を正規化し、非正規形を弾く機械検査も入れる。判定は 2 秒で、混入時点で止まれば子を走らせてから捨てる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-865] test_spool_fold.py の _copy_real_canonical_family が dependency closure を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-870] dev-wave-t870-lease-timingwaveがclaim→land/release実時間を実測した (output/insig… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-875] 段別 argv 契約の検証は launcher が 投入前に --dry-run 相当を自動実行して弾く形にする。DW-O01 への追記はしな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-876] _normalize_node() で xdist の @<group> 接尾辞を剥がし、**xdist_group marker 付きテスト… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-878] orchestrator/tests/test_s8b_approved.py:31 の from tests.skiputil import… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-880] 択 (b) 採用 — 対象 repo の tools を import 文脈へ束縛する。現状維持は「別 repo を対象にすると誤った版を読む… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-882] 受入全走の短縮を (a) batch 化と (b) opt-in 化へ分解する。 IZANAGI_T080_E2E=1 で同一 workloa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-884] 択 (a) 採用 — セッション記録の全件解析へ索引か上限を入れる。約 106 ファイル/日で増え約 26 日で倍になる速度は放置できない。p… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-885] 隔離の保証が変わらないことを確認の うえ --no-checkout / hardlink 等の軽量形へ変える。[T-893] と同一裁定 (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-887] 択 (a) 採用 — 限定 group を別案として再提示可能とする。退けた根拠が D91 の逆読みだった以上再提示は正当である。実測は並列数… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-889] state 無しの検証済み fold commit を already-landed と認識する経路を land へ足す。受理集合を 広げる変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-890] lock-aware finalize / inspect command を作り standalone apply を封鎖する。[T-799… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-892] 本 wave の変異 1 巡目で、 この赤が **baseline を FAILED にして harness の production wri… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-893] [T-885] と同一裁定。E2E の repo 全体 clone は隔離意味論の確認つきで hardlink / --no-checkout… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-894] 受入待ち手の merge 競合診断に競合 path を 出させる。現状は stage=merge rc=70 だけで、親が git merge… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-895] 「次の一手」の項が裁定で終端したまま active に残り続ける構造を検知する。本 wave の実測では 62 件が滞留し、うち 52 件は残… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-896] 二重在籍 8 件は **worklog の active 側を正本とし、見送り台帳側の項を消せる手段 (更新 型) を足す**。残作業が ある… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-912] [T-709] が裁定した部分集合一致の判定枠 (期待 node が実測失敗集合に含まれれば KILLED) は tools/mutation… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-928] 段 2A が挙げた残り約 40 function を 一次証拠で検証し、成長比例と確認できたものを台帳へ追加する。証拠 (file:line… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-935] submodule gitlink の前進は Git 操作の 機械的代行であって著作ではないと docs/ai-provenance.md へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-937] _scan_session_rows が 全 corpus の全行を parse する。現在はテストが実 corpus を渡していないため律速… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-938] provenance checker の merge 判定を path の積集合から内容へ寄せる。git diff-tree --cc が空の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-939] 比例項の真の除去 (session-id 索引または直接解決可能な path 契約)。本 wave は係数を下げただけで walk の線形項は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-952] worktree-dev-wave-testops-observation の未 land commit 3 本は、所有が曖昧なまま置くと b… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-959] L2 経路で収容する裁定は変わらない。収容対象に、entry 859 本文へ実測付きで記録されながら T 項を持たない段 8 候補 4 件を含… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-960] tools/run_tests.py が --noconftest と suite 下を指す --confcutdir を fail-clos… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-963] 残る 3 本 (backup-rulings-land-20260812-first-attempt、 backup-rulings-land… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-980] 受入成果物へ worker ID・worker 別開始終了時刻・receipt memo の cache hit/miss・ lock 取得待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-981] 「evidence_status=invalid の理由を receipt へ記録する」は 本 wave で実装した (schema v5 の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-995] 既知違反台帳の各 entry が「実在する commit で 実際にその違反を持つ」ことを検査する positive coverage を足す… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-997] 択 (a) 採用 — 拒否は維持したまま理由を出す形に直す。受理集合は変わらない。「repo 外からは走らない」ことを明示する診断は、相対パス… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-998] claude_session_ledger.py が 並列 subagent の transcript 間で共有される message id… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-999] collect_wave_usage.py が 内側 collector へ --project を空白区切りで渡すため、先頭が - の実 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1002] codex 成果物の検証器が要求する ## 総括 見出しを dev-wave の prompt 定型へ入れる。今回 1 投入 (64 秒・mo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1004] 択 (b) 採用 — 検査間の競合 (検査後に main が進むと緑になる) と対象 main OID の未認証の 2 件を閉じ、残りは記録に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1005] 裁定条件が不成立という実測は変わらない。本族の赤は D498 の実装で閉じる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1009] 変異 runner は **dispatch recipe (--force-dispatch) を正とする** ([T-613] の運用規約… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1010] docs/dev-wave/** と入口の圧縮が exact pin を 跨いだかを、圧縮前に機械で洗い出す手段がない。本 wave は 4… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1011] 変異 harness の起動前 abort 4 型 (--wrapper-attempt の型、-rf 必須、container 残骸、--o… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1016] 実資源に触るが現 writer と path-disjoint な reader の第三分類。read path と writer path… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1021] tools/run_tests.py は Pegasus login の headroom が足りる経路で bounded test を先に実… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1023] check_acceptance_reds.py の probe worktree は SIGTERM / SIGHUP / SIGINT で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1026] hooks/guard_bash.py の docstring (39-45 行付近) が現状と 2 点食い違う。(1)「Codex subp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1032] 択 (a) 採用・引数単位 — 同じ script が引数次第で軽い処理にも重い処理にもなるため path だけでは分類できない。測定対象を本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1033] 実 1,045 file 入力の 30 collision 群を 現行 resolver へ通して全群が解けることを確認する。実行場所の手番が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1036] 択 (a) 採用 — 実行場所の分類に失敗したときは閉じる側 (実行拒否) に倒す。ログインノードで重い処理を走らせる事故は共有環境への外乱で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1056] tools/dev_wave_wait.py producer が、 .done も成果物も存在せず producer が生存している状態で、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1057] checker 全体の timeout (i) と checker 実行中の lease heartbeat (ii) を実装する。 (ii)… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1058] test_dev_wave_wait.py の signal handler 復元テストが変異 harness の走行間で揺れる。 2 巡目で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1059] tools/codex_worker_launch.py の --evidence-grace-s 既定は 5 秒で、この時間内に codex… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1061] test_dev_wave_wait.py の fake effects は期待 event 列を固定するため、共有定数や共通呼び出しを変異さ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1064] 択 (a) 採用 — 生の worktree 削除と登録済み worktree への強制削除を防壁の破壊系集合へ入れる。防壁を強める方向であり… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1079] test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1080] 択 (2) 採用 — 完全なやり取りの生涯 (開始ちょうど 1 回 → 完了) を「証拠が完全」の必要条件にする。択 (3) (CLI に機械… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1081] orchestrator/tests/test_codex_worker_launch.py は dispatch 走行でも走ごとに 1〜40… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1082] test_codex_worker_launch.py は計算ノード前提と明記する。1 file のために前回ピーク由来の 予算算出方式を変え… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1084] evidence_forced_stop が receipt に出ないため、SIGTERM が evidence deadline 由来か 外… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1085] 子が正しさで拒否されると output が公開されず、dev_wave_wait.py producer は それを producer-fil… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1091] 背景の待ち手が producer 生存・.done 未生成の 状態で rc=0 復帰する事象を 1 session で複数回観測した。tool… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1093] dev-wave の codex 子が成果物を書き終えた後、 producer script が .done を書く前に落ちる事象を 1 se… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1097] 択 (a) 採用 — 3 者の順序を「診断の出力 → bytes 契約 → 本件」とする。診断が出るようになれば残り 2 件の誤診が止まるため… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1098] 受入 lease の critical section の内訳は pytest 156 秒 + **親が受入成功後に lease を握ったまま… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1101] 受入試行の終端 (成功・失敗 stage・所要秒) を機械集計する仕組みが無く、本 wave は job dir の mtime と log… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1105] codex 子の sandbox から tools/run_tests.py が走らない (local 予約台帳を更新できず dispatch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1107] 族の member に **4 つ目の file** が加わった。2026-08-16 01:38 JST の 受入で orchestrato… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1114] tools/check_docs.py へ 「spool fragment の 更新 / 完了 item の本文が carry stub 形式… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1118] 非帰属 checker は子 pytest へ渡す環境から pytest 選択系の変数しか除去せず、task-run 記録の変数を残す。これが… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1120] 択 (a) 採用 — main に着地した引き継ぎ文書の所有・寿命・回収を一体で定義する。定義が食い違ったままだと、着地した文書が「生死不明」… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1123] --forbid-worktree-handoff の help は 「README.md 以外の worktree-local handof… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1124] DW-O20 は新規 worktree について最上位の git submodule update --init しか書いていないため、入れ子… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1126] codex 子の writable root へ job 用一時領域を明示追加して恒久化する。変異 harness 側の 「spec / ou… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1127] run_tests.py の bounded local が前回ピークから 見積もる予算では cgroup attest が落ち rc=16… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1138] テスト実行器が計算ノード投入の待ち行列上限と 全体猶予を下位へ渡していないため、キューが滞留すると猶予を延ばす手段が無く基盤失敗になる。 本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1145] 変異 harness の「期待 node が pytest collection に実在しない」診断が、parametrize を持つ関数へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1147] land API へ段 6 の実施証拠を要求させる。ただし全証拠の一括必須化は過去形の wave を着地不能にするため、 **まず mutat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1149] 内容が健全で digest も記録済みの attempt を、NFC 逸脱という provenance 形式だけで全損させる現行設計へ、 **… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1150] 変異 harness が 実行のたびに変化するファイル (dispatch receipt 等) を含む木を走査対象にすることを、 **禁じる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1152] 読み取り専用の 計測解析 script は **repo 外なら親が書いてよい**旨を明文化する。[T-317] 裁定 (2026-08-10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1153] land 時の path 交差検査を tools/dev_wave_land.py の fail-closed 検査として**機械化する**。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1154] 軽量版 wave に 実装面があるときのレビュー段の要否を、**要る側で明文化する** (DW-C00 軽量版と DW-S06-A の 不整合… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1162] 問い返しの前提だった「flock はノード跨ぎで効かない」が誤りだった。/work は lustre を flock オプションで mount… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1163] tools/run_tests.py から dispatch の --queue-wait-timeout / --overall-grace… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1164] test_dev_wave_wait.py の 3 node は 2da49c56 が production の mask 汚染を閉じ、_ha… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1165] tools/dev_wave_wait.py producer が **pid file 不在を「producer 死亡」と解釈して即座に正常… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1169] 受入全走 2 回が orchestrator/tests/test_dev_wave_wait.py の**別々の nodeid**で 1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1171] 択 (b) 採用 — まず発生率を既存記録から数える。発生率が未計測のまま上限を入れると正当な並行投入を切りうる。計数は既存記録から無料で得ら… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1173] 親 command は tools/dev_wave_wait.py acceptance で lease を release すると書くが、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1176] role 応答の JSON parse 失敗への再試行。D936 が「D935 が入れる失敗分類の記録を先に運用へ流し、 実測を得てから再試行… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1177] attestation を runbook の正規手順へ揃える schema v2 を**別 wave で起票して直す**。gate の受理集… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1189] land の採番順序は **現状維持とし、番号を参照する成果物は wave を分割して次 wave へ回す**。択 (b) 決定 fragme… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1190] 事前登録の例外型は理由属性を reason で持つのに、評価器側の分類は reason_code を読むため、当該例外がすべて blob 読取… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1191] session_meta 行が 複数ある rollout について、**完全一致する重複行だけを 1 行として扱う**。compaction… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1192] _session_meta_rows の decode 失敗と OSError を silent skip せず、**MATCH / NO_M… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1194] F342 の恒久対応は **L2 節 (合計上限なし) へ置く**。択 (b) L1.5 の他節を縮約する案は、同族 docs で折り返しの変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1196] **「判定不能」が 2 種類できたのに、運用者が区別できる記述が無い。** DW-O18 は「tools/check_acceptance_r… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1201] 評価器を持たない条件を machine_checkable: true にすると、原因は評価器 registry の欠落なのに commit-… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1203] dev-wave docs の 予算は**機械検査への移送を主、別 reference の新設を従**として空ける。[T-508] の既裁定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1204] 成果物を加工してから hash した pin を 機械で列挙する検査を置く。F345 の恒久対応は 現状 memory 止まりである。DW-O… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1205] 受入待ち手の test_public_main_failure_restores_handler_without_release が全走 (1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1206] 変異 harness の期待 node は --collect-only の空間で検査され、実際の照合は FAILED 行の空間で行われる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1217] 変異 harness の報告 node と collection 実在検査の空間差を機構側で正規化する。詳細は F346。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1220] 択 (b) 採用 — 生成側にも範囲の事後条件とテストを足す。欠番を挟む同時ローテーションはまとめ処理の失敗として全 wave の land… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1221] F347 の 恒久対応は DW-O02 へ直接書かず、**機械検査への移送 (主) と別 reference の新設 (従)** で 枠を作っ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1224] 択 (a) 採用 — 閉包検査の判定基底を lstat へ変える。壊れた symlink を不在扱いするのは「不在の実測」を誤らせる型で、既定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1225] 変異 harness の _failed_nodes は **ERROR  行も読む**。変異検査は規律 2 の実効性を測る道具なので、mod… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1227] 「差分が 到達しえない path の赤」を構造的に非帰属へ寄せる (DW-O18 の機械化) を主とし、差分が触った file に限り 2 回… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1237] fan-out の driver report と top-level stderr へ hold path・request ID・submi… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1245] dev-wave docs の予算で滞留している是正は、**dev-wave 以外に正本を持つものは外の文書へ移し、 dev-wave 固有の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1261] 新設した構造テストが floor_campaign.sh の unset 対象集合を「ちょうど 3 個」と固定しており、 将来 unset L… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1264] tuple(numactl or ()) が str を 1 文字ずつの tuple へ分解するため、numactl に list/tuple… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1271] tools/mutation_harness.py の失敗 node 抽出が FAILED  行しか見ないため、fixture teardow… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1272] 同形の return-to-store gap が tools/mutation_harness.py:1076 と orchestrator… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1273] 子への Web 検索禁止は DW-C01 へ 1 行で収容したが、 裁定が主とした機械移送は**未実施**である。tools/codex_wo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1276] 受入 lease の claim / release / TTL 失効に監査証跡が無く、 「release が機械化されたか」「待ち時間がどれ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1277] 既知の land 再試行 script は rc を自前分類し、 終端的な赤でも lease を再取得せずに land を再実行する。自動解放… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1278] 走行形で結果が変わる テストは正しさシグナルに使えない (規律 3)。原因分離は諮らず進め、揃える方向が確定したら 実装まで進めてよい。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1290] pipeline.evaluate を loop.run_campaign を 経ずに呼ぶ 4 経路 (screening_driver.py… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1297] 退避 bundle の run 単位 index は index.jsonl まで作ったが、列挙・読解の CLI は作っていない。 親は初回の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1304] 択 (b) 採用 — 義務を新設せず、段 3 の敵対レンズの既定項目へ「成果物が目的へ到達するか」を含める。既存項目が「成果物が実際に効く全層… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1308] fix 子への適用範囲指定は dev-wave 固有なので新規 L2 節へ収容する。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1318] 単独再走の rc=0 に 「対象 nodeid が call phase まで実行され PASSED した」証拠を要求する。現在は rc=1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1319] 初回全走と単独再走の argv・環境変数・pytest 選択・scheduler を同形にする。現在は checker が PYTEST_DI… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1321] 「main で決定的に赤なので受入全走を必ず非緑にし、 受入は毎回 checker の非帰属判定に依存している」は**耐久受領証と矛盾する**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1332] 同一タスクを扱う wave の二重着手を、docs でなく既存の起動検査ツール (tools/check_wave_startup.py) の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1344] tools/mutation_worktree.py の receipt が local 停止の理由を分類できるようにする。現在は wrapp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1345] test_s8b_floor_campaign.py と test_dev_waves_integration.py の成長比例 node を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1350] read-only codex 子の web 検索を **機械的に禁止する**。F217 の恒久対応は「子 prompt に web 検索禁止… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1351] dev-wave 固有の作法なので新規 L2 節へ収容する。圧縮での捻出は exact pin を壊すため 引き続き採らない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1359] ファイル数比例項は当面残す。(a) 恒久保留は、この検査が封印後の混入を見張る唯一の番人であり、 成長比例テストの恒久保留規律が想定していた「… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1360] 択 (a) 採用 — prompt 以外の軸 (レンズ設計・入力の射影・独立性の取り方) で多様性を回復する。モデルを増やす方向は採らない (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1363] tools/check_wave_startup.py と tools/run_tests.py の診断文は今も git submodule… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1364] 層予算が読了量の上限として機能しているかの 再点検は、[T-959] の収容 wave の設計入力として扱う (単独では起こさない)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1365] DW-C01 の 10 規則は予算 (残り 9 bytes) のため通る正例を添えられていない。 DW-S04 は gate の禁止に正例 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1366] 変異 container で test_real_repo_clean が実行されない。skipif は無い。実 repo を読む 検査を変異… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1368] 変異 harness の期待 node と xdist group marker の名前空間の食い違いは harness 側で解消する。 回避… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1383] 受入全走の固定費 約 26 秒 (wall − real-repo 鎖長、 14 走で 20.6〜28.8 秒) の内訳を測り、削減可否を判定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1399] merge-message-provenance (tools/dev_wave_wait.py:3816-3825) は merge の 3… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1404] 当初案 (DW-O05 へ1文追記) を撤回し、道具側の実装へ 切替える。「症状 (usage limit/401等 exit code・ev… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1406] registration schema version を昇格する。 先に test_redundant_registry_duplicate… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1407] 独立予算審査を待たず、 dev-wave 作法 5 件を収容できるだけ上限を引き上げて結線してよい (D671)。個別の (a)/(b)/(c… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1410] 択 (a) 採用 — 段 2/3 を飛ばす軽量経路を正式な dispatch 規則として明文化する。4 回使われた経路が未明文化なのは、次に使… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1412] 独立予算審査へ 回さず、上限引き上げを含む収容 wave でまとめて処理する (D671)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1413] (b) 採用。 分類の測定対象を本番 caller が実際に渡す argv (現行の --max-files=1000 相当) に合わせる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1415] DW-S01 の前提実測 範囲の明文化は、上限引き上げを含む収容 wave で入れる (D671)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1424] docs/dev-wave/core.md の DW-C01「--laneは--stage consult専用。他段はrc=2で落ちる。」とい… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1425] 新設テスト test_real_repo_clean (実測8.3秒、 orchestrator/・tools/ 全 .py を AST 走査… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1426] output/ のさらなる tracked bytes 削減。t419-probe-causality の path 参照対応、output/… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1429] job wrapper の durable checkpoint / partial-log 実装 (2026-08-18 に段3敵対相談がC… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1430] DW-S07 への 「fragment は最終受入より前に commit する」1 文と、段 8 の修正候補を次 wave の段 1 冒頭で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1432] 択 (a) 採用 — 4 箇所に分散した会計証拠の検証を 1 つの判定へ寄せ、group name の束縛を足す。分散した検証は「1 箇所直し… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1439] producer --check-only の 運用契約への結線は、既存文言の圧縮を先行させる必要はなく、上限を必要分だけ引き上げて 結線して… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1443] tools/mutation_worktree.py の期待node事前登録 (collection存在チェック) が @<xdist_gro… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1446] 予算超過で滞留して いた段 8 自己改善候補の束ねは、上限引き上げを含む収容 wave でまとめて設計し直す (D671)。候補が編集面で重な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1448] DW-O19 (段6の一時変異手順) の 「変異前をclean確認し」を、file 単位の差分確認でなく git status --porce… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1452] ## 総括 見出し必須の明示統合は [T-959] の 収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1457] 背景 job で EnterWorktree 前に 起動した Agent fork (および再委任先) で Bash が worktree 判… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1459] dev-wave の codex prompt 構築 (tools/dev_wave_codex.py) が、plan/consult/aut… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1460] 変異 matrix runner の除外条件の追記は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1465] docs/phase3.md 見送り台帳の [T-1090] (1 dispatch job で複数node を扱う設計、有界並列化の 不採用… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1466] /rulings の収集 手順 2 件の是正は、上限引き上げを含む収容 wave で入れる (D671)。 収容先の .claude/comm… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1467] 択 (a) 採用・分割して実施 — 恒久保留 59 件を個別レビューするが、正しさの関門付きのものから10 件程度ずつ行う。一度に 59 件を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1471] 受入全走の xdist collection 固定費の 現在値を再測定する。2026-08-18時点 (12951件・単一process 4.… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1479] 探索目的の全走も隔離 worktree で 行う旨を DW-O20 (984/1000 bytes、空き16 bytes) へ追記する候補。d… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1485] role 呼び出しの retry=False 実装可否を判断するには、fixture provider ではなく実 provider (cla… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1489] reasoning-pin の authority/admission 分割、 detached mutation の実 detach、mut… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1491] _message_file_paths() (commit前preflight) が本waveと同型のpairwise-intersectio… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1492] tools/dev_wave_wait.pyの producerサブコマンドへ、poll loop到達を示すreadiness marker機… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1493] test_s8b_floor_campaign.pyの build_cells呼出しの区間別計測 (cache lookup/実ビルド/val… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1494] test_real_repo_ serialization.py::test_real_repo_priority_order_is_lite… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1496] 択 (b) 採用 — 当該テストを growth-test hold registry へ登録しない (D845)。 再訪条件 = 実 pac… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1497] 恒久除外集合を task-run receipt / aggregate / acceptance launcher receipt へ証跡化… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1498] 変異 harness の 焦点走対象に、入れ子でスイート全体を subprocess 実行するメタテスト file (test_growth_… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1499] masstree の config.h 欠落が 解消したら、tools/run_tests.py の恒久除外表から該当 entry を 1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1500] 共有契約 module orchestrator/test_selection_contract.py は production module… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1501] F373 の恒久対応 (FORCE_COLOR/COLORTERM を外して起動する) は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1502] 自分の変更に起因しない受入の赤を dev-wave で直す。対象は 2 つの wave が独立に観測した 27 件 — test_sort_s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1503] 受入の親子が互いの完了を待って停止する経路 (F466) を塞ぐ。結果の読み取りから完了通知の 送出までの区間を try/finally で囲… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1504] 赤の帰属を判定する検査 (tools/check_acceptance_reds.py) が、受入が成功した回でも 41 分以上を要する件を調… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1507] 既知赤と判定済みのテストを受入の実行対象から機械的に外す配線を入れる (D679、D678)。 現状は各 wave が実行時に個別指定して回避… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1508] 赤の帰属判定を**全走差分方式**へ作り替える (D680)。 probe 作業ツリーを廃し、tested main 側で全走を 1 回だけ回… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1509] 段 2 / 段 3 の reasoning effort を docs pin から subprocess argv へ機械強制する。現在 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1511] 非帰属 probe の worktree 再利用を 実現するには、まず「probe の状態隔離を何によって証明するか」の設計が要る。 work… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1512] worktree 再利用を維持する。非帰属判定の並列化は同時実行数の上限機構を新設することになり規模が見合わない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1513] 非帰属判定の所要は **目標 3 分 (計算ノードを全力で使って)・実態許容上限 5 分**とする (D726)。畳み込み単独の 26 回 →… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1514] tools/check_acceptance_reds.py の _authoritative_command_stdout は、dispat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1515] red-check receipt の schema 変更は行わない。 分割取りこぼしまたは空結果受理の実害1件で T-1570 と同時に再訪… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1517] 全走差分方式の R_main は tested_main の SHA だけで決まり wave に依存しないので、 <main SHA, run… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1518] D671 の下で入れ直す 2 件も、まず [T-959] の L2 経路で収まるかを試す。収まらない分だけ D671 の引き上げを使う。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1519] orchestrator/tests/test_dev_wave_land.py::test_exploration_external_roo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1522] 全走差分方式の tested main 側の赤集合を <main SHA, runner 内容ハッシュ> を key として repo 外へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1523] **production が pin / cache / 索引を使う経路を、テストだけが素の全走査で叩いている箇所**を 横断で洗い出し、受入… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1528] --attempt-out / --wrapper-attempt の runner-mode 依存の是正は [T-959] の収容 wave… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1530] 択 (b) 採用・現状維持 — 未取得経路での判定なし再試行は許さない。受入の排他は結果の意味を守る仕掛けであり、緩める側に倒す根拠が弱い。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1531] 択 (a) 採用 — no-op になった 2 引数は稼働 wave がゼロになった時点で削除する。何もしない引数を残すと「指定すれば効く」と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1532] 入口 command 段 6 を、no-op フラグ名でなく 「lease の取得可否で受入投入を止めない」という条件そのもので pin し直… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1533] login node でのみ再現的に落ちる test_exploration_external_root_keeps_wave_clean を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1534] claim が holder に自己 digest を返しつつ holder_self:false を返した場合、受入は未取得として進み le… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1535] 「変異走行中に tree へ書かない」の追記は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1537] 択 (a) 採用 — 追加時点で重複を弾く関門を作る。D99 決定 1 の閉じた CLI 集合の改訂を含めて一変更単位で設計する。11 日で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1538] mutation.md への追記 2 件は [T-959] の 収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1540] _validate_hold_rows を拡張し、barrier_nodes が保留集合に入っていないことを既存の import 時 enfo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1541] 変異期待 node の正本と 保留 registry の整合を機械検査する。本 wave では 7 件の矛盾が人手の読みでしか 見つからなかっ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1542] 択 (a) を警告のみで採用 — pin 無し全走査に上限は設けず警告を出す。上限は正当な走査を切りうる。同じ探索関数の伸長 (セッション記録… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1543] L1.5 満杯で入らない自己改善候補 5 件は [T-959] の L2 経路で収容する。予算値の引き上げも routing 先の変更も単独で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1544] 予算が空いた時点で、 親の焦点走を FORCE_COLOR / COLORTERM を外して走らせる義務と、親の実走も 終端マーカーと終了 r… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1545] 変異まわりの手順事実 3 件は [T-959] の 収容 wave で L2 節へ入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1550] 隔離集合を acceptance receipt へ束縛する。 現状は走行末尾の IZANAGI_FLAKY_HOLD_SUMMARY_V1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1552] 失敗 digest の byte 予算は上げず、**捨てた分の manifest 実体を記録側に残す**形にする。 予算は「記録が無限に膨らま… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1553] 準備区間に物理 hard cap を与える。 現状の準備上限は既存 wall 上限と同じ polled admission 検査であり、imp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1554] 並行セッションが F57 修理で 23 node へ入れた max_wall の引き上げが、準備費の控除後も必要かを実測して戻す。 引き上げは… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1557] nodeid 正規化の非対称は harness 側で解消する。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1559] 択 (a) 採用 — land 後の記録 commit を段 9 の正式な遷移として許す。中途半端な撤去の残骸は全 wave の land を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1560] /cleanup-branches §3 の撤去順 (branch 削除が 2 番目) が本 wave の順 (branch 削除が最後) と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1561] codex launcher の evidence_status=invalid が 健全な成果物を not_accepted にする条件を特… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1562] 既存の worktree 31 本・branch 114 本を 掃除する。zombie 修正で /cleanup-branches §3 の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1564] verify_snapshot の呼出し扇形を縮約する。 1 node 内で 47 回呼ばれており、内訳は fixture 2 / super… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1565] real-repo 鎖の 2〜4 位を含む test 構成を見直す。 いずれも同じ module snapshot に対する closure… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1566] group 注釈付き node を期待 node として 扱えるようにする。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1567] 択 (a) 採用 — 第 2 の直列鎖の内訳を測る。ただし D820 が分割数による解決を退けたため、本項に残るのは内訳の実測だけである。単独… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1568] 自分が原因でない決定的な赤で 塞がれた側は、**所有者が修理中であると確認できた場合に限り一時隔離してよい**。 隔離の理由を「赤だから」にし… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1569] orchestrator/tests/test_dev_wave_cleanup.py::test_landed_attached_workt… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1572] 実 tree を snapshot して不変を要求するテスト 9 関数 / 11 node と、基盤が repo 内へ書く path を突き合… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1573] shard session directory が走行後に残る。 1 走あたり約 15 MB。land への影響は無くなったが、共有 file… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1575] 受入 lease の排他範囲を他 wave の codex 子まで広げるのは**当面行わない**。排他を広げると 並行度が落ち、それは今まさに… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1576] 使い捨て worktree に生成される「proof chain ではない campaign 形の runtime 出力」は、 **campa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1577] failures 台帳が「裁定パッケージへ送る」で止めたまま担い手の無い機械検査の新設 3 件を **1 回でまとめて設計する**。(i) F… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1580] tools/check_docs.pyの DEV_WAVE_WAITER_DISCLAIMER_REが英語語彙 (optional/manua… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1581] tools/codex_worker_launch.py の _evidence_status() が invalid を返したとき、どの条件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1585] collection 環境の対称化を先に試み、費用が見合わなければ非対称な走行を不適格にする。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1586] 正式なテスト母集合の権威は別 commit 由来の台帳へ置く。実行時の inventory は環境で揺れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1587] 分割の片方が早期 infra failure、 もう片方が既に RUN のとき、親は worker を止めるが PBS job は継続し、回収… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1588] #PBS -b 2 で 1 要求 2 ノードを取れば queue 要求を 1 回にできる。現 dispatcher は 1 ノード・1 結果・… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1589] 負荷に応じて K を動的に選ぶ案。**2026-08-26 の実測で「K を増やす方向は 当面効かない」は失効した。** 排他鎖の細分化後に測… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1595] 欠落 2 件の 収容も [T-1639] と同じ手順で AI が判定してよい。(ii) は独立 3 例目として例外の要件を満たす。 正本 =… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1596] orchestrator/tests/test_dev_wave_land.py::test_exploration_external_roo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1598] 段数上限ちょうどの前方取り込みを、topology 検査だけでなく land の端から端まで (再演・lock・provenance・ff-o… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1599] /rulings の land 直前に、**裁定本文が根拠にしている事実がまだ成立しているか**を照合する 手順を入れる。現行の防壁は spo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1608] git merge --no-edit と git revert --no-edit が trailer を 1 行も持たない commit… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1609] output/insights/**/*.py が実装面判定に 当たるため、解析 script を insight へ置いた docs com… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1610] real-corpus テストの fixture anchor に、 既に完了して archive され二度と実体更新されない task_id… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1612] Codex dev-wave skill の 4 命題 (.codex/worktrees/ の配置と再利用契約、隔離 codex exec… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1614] sandbox 化 Codex 子が .agents/ へ 書けない制約を dev-wave の reference へ収容するか判断する。本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1615] workspace-write の Codex 子で evidence_status=invalid が再現し、read-only では起きな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1619] 受入の高コスト側にある「同じ前置きを何度も払っている」型を共有化する。 s8c predicate 族 (test_current_repos… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1620] 所要台帳の定期再生成の運用を決める。 被覆率 gate が 90% を下限にしているが、再生成の契機は誰も持っていない。 値の精度は要らない… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1624] ungrouped node (1 件 = 1 work unit) の 順序依存を測れるようにする。現状 targeted の AB/BA… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1625] 実 repo 利用 node の直列集合への 登録漏れを、共有 submodule の checkout 経路以外でも機械強制する。現行 gu… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1626] 43% を 現状追認しない。correctness gate 付きの growth hold 34 件を対象に所要と重複を実測し、戻せる分を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1627] worker を跨ぐ overlap 依存を測る設計を立てる。 共有 submodule の apply 窓、patch lock、tmp 上… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1628] 受入投入前に HEAD..main が 束縛対象の実行体 (待ち手・launcher・runner) の bytes を変えるかを検査し、変え… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1634] docs/handoff/ の 残骸棚卸しを本セッションで実施し、**9 件すべてが台帳で終端した死んだ wave の残置**である ことを確… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1637] repo 内監査が報告した到達不能 30 commit (probe・TEMP・superseded 由来が大半) と、上記 2 branch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1639] DW-O17 への 統合は D730 の手順 (既存記述の削減 → 独立 3 例の例外収容 → それでも作れない場合にだけ上限引き上げ) を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1640] 変異 harness が xdist group 接尾辞を 正規化しないため、group を新設した wave は KILLED 判定を構造的… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1645] DW-S05-C への 追記も同じ手順で AI が判定してよい。「予算に 137 bytes 以上の空きができたとき」という再訪条件は D73… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1646] 重複測定の基点を DW-O18 へ書く案は、事故を伴わない 1 例であり D730 の原則どおり 実施しない。実体は本エントリと起票元 wav… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1649] launcher テストの時間予算を、attempt 本体の時間で測る形か固定費を予算から除く形へ直す。 予算の一律引き上げは採らない (暴走… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1650] 着地済み branch の削除を承認する。削除直前に branch 名・先端・main 上の対応 commit の一覧を保存し、内容一致と占有… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1651] worker_collection.index() を O(1) の index map へ置き換える試作を作り、現行 K=2 の受入全走で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1652] 同一の slot probe 数 (104,654,278) に対し collection 順で CPU が約 2 倍違う機序を特定する。 候… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1653] 択 (b) 採用 — 当面は閉じたまま運用する。該当 30 commit には親が直接 merge する 1 commit 限りの例外が確立し… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1657] hooks/guard_bash.py の head 判定を是正し、直書き形と shell 変数間接形で判定が一致することを要求する posi… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1662] PR 2 本を送る。内容は 2026-08-25 の択 (b) のまま変えない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1663] 実証済みの範囲で射程を確定し限界として明記する。一般化は需要が実測で現れた時点で再訪する (D916)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1664] D821 の 3 択のうち説明を狭める 案を当面採る (D839)。可用性を捨てて閉じる側単独は不採用。 予約制と全層同時切替は別枠で起票し、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1667] hang 変異の timeout 後に計算ノード job の終端を 確認できず orphan-hold が張られる。hang 変異用の走行だけ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1674] DW-O01 の effort 記述は plan / consult で実測と逆であり、誤記の是正なので D730 の 原則落ちには当たらない… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1676] known-violation の 群別件数を受入 receipt と land result へ投影する。D800 が「群の値は rc の入… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1681] growth-hold 側の worker 経路 stale 検査に 感度 control が無い。現実装は静的には検査しているが、_is_c… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1682] suite root に別 target を足した上位集合は 完全 collection と見なされず、stale 検査が発火しない。coll… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1684] 受入 shard 経路が output/task-runs/ と output/runs/ へ書くため、_real_output_snapsh… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1685] evidence_status=invalid の第 3 の原因を 特定する。web 検索と非 NFC は本 wave で反証済みで、最終 a… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1686] 択 (a) 採用 — 繰越 fixture 5 件へ段と担当を個別に割り付け、完了判定へ配線する (D844)。射程の訂正 = 三者一致は D… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1687] 繰越義務述語を段 6 候補提出の前提関門 adapter へ結線済み (D946)。残件だった operational caller 0 件に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1688] 択 (b) 採用 — 未裁定側へ揃え、当該 1 件を改めて裁定へ載せる。pin が resolved であることは「誰かがそう書いた」以上の意… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1689] D752 (2026-08-24 ユーザー裁定) が定めた fold 適用後 tree の land 前関門を実装する。fold の決定的な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1691] K=3 の実測は行わない。D820 が分割数の増加を既定の手段から外しており、実測が良い値でも採用経路が無い。受入短縮は node 単位の費用… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1692] orchestrator/tests/acceptance_duration_ledger.json を変更後の実測で再生成する。対象 nod… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1693] shard wall のうち test phase に入らない残余 (12 session で 57.34〜93.00 秒、critical… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1695] main thread が pthread_exit() した後も 別 thread が実行中で cwd を保持する thread group… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1707] tools/mutation_worktree.py が 使い捨て worktree で外部 benchmark の submodule を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1715] 新規 worktree の初回受入全走は output/runs/pytest-launcher-failures が走行中に新規作成されるた… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1716] docs/dev-wave/** の L1.5 予算に 安全義務の是正が入らない件は、**D782 の手順を AI が適用して閉じる**。 d… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1717] 証拠が無効になった理由を受領証の attempt record へ 1 field 記録する。本セッションの author 子 1 本目がこの… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1720] 段 8 の自己改善 2 件 (refuted の 2 種を分けて書く / fix 子の担当所見を prompt 本文で列挙する) が byte… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1725] docs/dev-wave/** の 層予算が満杯で安全義務の追記が入らない件は、D961 が 手順を定めた。予算のために安全義務を削る選択肢… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1730] DW-O01 の「採用は check_codex_output.py の rc=0」は一文だけ読むと十分条件に読め、 本 wave の親はそれ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1734] 新規 F を要する決定的な非帰属赤は、 **保留の登録簿が未着地 fragment を証拠に取れるようにする。ただし採番・正本化・有効化を 着… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1735] D690 の 5 分は **計算ノードの順番待ちを含めない。テスト実走と帰属判定の合計を 5 分以内とする。** 診断のみへ狭める形も、順番待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1736] FlakyTestHold の cause は **自由記述を権威にせず、独立に検証された分類の受領証へ束縛し、受領証が無ければ 保留を発効さ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1737] 「予算に張り付いた対象への変異登録では変異後 bytes も赤理由の層に数える」を DW-M01 / DW-M04 へ統合する件は、D961… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1740] 「実装が production 経路から到達するかをレンズに答えさせる」を dev-wave の正本へ入れる件は、 D961 の収容表へ載せる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1743] lane と model の束縛を外し、 旧値は読み取りのみ受理する (D1085)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1744] /rulings の収集で、前回セッションが 残した索引ファイルを差集合の母集合に使わない。本実行は前回索引の 102 項から採用済み 92… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1746] 受入 shard の残余 (pytest wall − pole、shard-0 で 62 秒 / shard-1 で 47 秒) のうち、w… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1747] login preflight の全史 provenance 監査 2 本の 冗長は**削らず現状維持とする**。速くするなら、取り込み差分だ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1751] landing tip の実行器が受領証の 検査対象外である件は、**取り込んだ main 側が実行器を変えている場合だけ受領証の再利用を 拒… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1753] /cleanup-branches §1 へ監査の所要時間 (1 時間級・ 無出力) の注記を入れる。入口は byte 予算が満杯のため、re… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1754] 内容として着地済みだが main の祖先でない branch を /cleanup-branches の削除対象へ**入れる**。削除は -D… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1755] fold receipt に無い fragment が 着地済みかを決定的に判定する本文比較器。re-home 追跡と placeholder… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1757] 再生成される不透明 baseline (test_reflux_originless_compatibility.py の 1 行) の着地を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1758] 共有 main checkout の untracked 集合を 変える操作の直前に pgrep -af mutation_worktree.… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1761] 依存物の staged 運搬を driver の既定にする変更は**承認しない**。先に staged 運搬を canonical trans… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1763] Pegasus の orphan hold 解除文言に、 gate を成立させた実 path を列挙させる。現在は要約 marker の pa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1764] 非採番 archive の carry が構造的に 検査対象外である件は、**検査を拡張して母集団へ入れる**。名前で対象外を固定している 既… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1765] 既知違反台帳・固定総数・exact テストを 同一 patch で書き換えれば無裁定で緑にできる件は、**保護レビュー境界**で塞ぐ。 **そ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1766] carry 文法を読む consumer (fold、land、rulings 収集) と checker の 2 regex が一致する保証… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1767] 母数の粗い下限を fold と原子的に ratchet する。凍結 entry ごとの期待件数を固定し、現行 worklog は fold の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1775] DW-M05 へ 「tools/mutation_worktree.py --source-repo には固定 commit の独立 clon… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1776] D935 が 記録するようになった failure_phase を実運用の journal から集計し、 role / provider ごと… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1786] 自走 harness が monkeypatch / tmp_path を 取るテストを実行できず、test_calibration_free… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1790] 実 output/ の窓内書き手のうち output/task-runs/reports/ の書き手が未特定のまま残っている。 現行の除外は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1791] docs/dev-wave/** の L1.5 に 実測した手順 1 行 (150 bytes) が入らない件は、D961 の 手順で閉じる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1793] 背景 job の待機作法を dev-wave docs へ 入れる余地を作る。本 wave の段 8 は候補を 2 件出し、DW-O03 の射… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1796] hook が dispatch gateway の内側 argv を 綴りによって拒否したりしなかったりする件は、**D427 が定める「防護… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1797] 変異の共有 lock 移行は task 経路についてだけ 閉じている。harness 直接起動は共有 lock を通らないため、repo 全体… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1801] 作り方であると明示する。 受理集合は変えない (D1089)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1809] 親が子へ渡す文書で 非 ASCII を chr(...) 表記に固定する規律を docs/dev-wave/ へ入れる件は、 D961 の収容… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1810] 到達不能 commit 監査の残る律速は **古い wave 成果物の退避で探索根を縮める**運用側の変更で対処し、**所要上限は現状のまま*… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1812] finding path の metadata 取得は commit ごとの argv 上限つき batch なので fork 数が find… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1813] hang する変異を dispatch 経路で 清算する件は、択 **(c) 現状維持として DW-M06 に「dispatch では han… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1823] 場所の指定は 未了のまま (D1030)。**共有 filesystem の 2 か所は同一の故障単位ではないが同一の ストレージサーバ群を指… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1824] repo 外に置いた救出物・退避物の恒久索引。 現在は worklog 本文だけが手掛かりで、半年後の第三者が directory 名を知らな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1827] 共通 base bundle と薄い rescue bundle の 保管・復元方針。現行は救出のたびに main 履歴を丸ごと複製し、1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1829] dev-wave の子 prompt へ Web 検索禁止を 必ず入れる義務の機械化。本 wave で子が Web 検索を始めて成果物を捨てた… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1833] 段 8 の自己改善で DW-S01 へ 「裁定の N 箇所は実アンカーで数え直し、同名の非対象は対象外行に残す」「受理集合を変えるなら 広がる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1838] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1839] IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT を dispatch の tests task env allowli… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1845] 検査器側を直す。下書きへの検証追加は 費用を見積もってから別途判断する (D1088)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1846] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1849] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1857] D961 の射程内。契約文面の書き換えが未着地であることが真因である (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1859] 受入の固定費 56.4 秒の内訳が未分解。 本 wave 後は wall の約 27% を占める。D532 が認める 3 手のうち (c) に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1862] 択 (a) 採用 — 検査が要求する状態を同じ file の中で自分で作る。判定器の基準変更と明示的な skip は不採用 (D1045)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1863] gen_S の混雑 (実測 RUN 31 / QUE 16) により、 受入や焦点走を計算ノードへ分散すると外側 wall が queue 待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1864] D961 のとおり D782 の手順を AI が適用して閉じる。個別に裁定へ返さない (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1865] 1 commit 手順へ戻す。条件 3 点付き (D1068)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1867] 合成監査の子に安定した job 識別子を与え、 receipt 台帳から機構の工数を機械集計できるようにする。現状は wave ごとに名前が違… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1868] node 故障時の State Transition Reason が未観測である。共有環境で誘発できないため、 偶発事例を取りこぼさず拾う経… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1877] 統合せず、 両方へ相互参照を追記する (D1091)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1884] 占有検査は判定器を 作り替える。完全観測を表す旗を空集合判定とは別に設け、証明可能な部分集合だけを判定に使う。 除外の再投入と区分単位の保留は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1885] 掃除の成功時診断 retry_count に 自動の読み手を作る。本 wave は実 /proc を走査する成功 6 node を stub… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1887] 既定の分割数は ノードで揃えた対測定を取るまで据え置く (D1047)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1888] 所要台帳を重み付けに使う機構は作らない。台帳は分析用途に留める (D1052)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1890] 道具名を実在するものへ 正し、逐語 pin も同じ変更単位で更新してよい (D1048)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1891] 同一 tip・同一選択・同一割付の 受入走で、直列総仕事量が 10585.7 対 14862.6 秒 (1.40 倍)、pytest wall… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1896] 限定例外を条件 3 点付きで書き足す (D1074)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1898] 既知違反の目標指標を 「基準時点以降の新規違反 0 件」へ改める作業。既存の違反は別指標で可視のまま保持し、 残置扱いへ格下げしない (D10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1903] 期待値を更新する。 D1152 の形に従い**所要値は性質の述語として更新し、対象集合は基準時点に対する exact な同一性を 保つ** (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1904] 静的な件数 gate は**置かない** (D1154)。 producer が commit 済みになったことは gate の必要性を作らな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1914] 共有 /tmp へ断続的に現れる空の .git の作成元を 特定し恒久遮断する。全 wave の受入を確率的に赤にする。repo 内に作成コー… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1915] output/task-runs/ は tracked 24 file で git-visible、並行 shard が run direct… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1916] output/variants/*/bin/ のような wildcard 規則は有限展開できないため、実在後に git ls-files 側で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1917] test_receipt_memo_real_xdist_order_has_no_worker_payer は内側で pytest -n 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1918] info/exclude の contract test は git init の通常 repository しか作らないので、実装を rep… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1919] 修理済み hold が黙って生き残ることを 検出する機構。DW-G04 により本 wave では設計メモに留めた (output/insigh… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1920] docs/dev-wave/** の L1.5 層予算に 阻まれた収容を D782 の手順で閉じる。**裁定へ返す案件ではない** (D961… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1923] orchestrator/tests/acceptance_duration_ledger.json が hold#1 の node を 10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1926] 生きた worktree 登録を読む production の競合をどう閉じるか。有界な取り直し・missing_ok 相当・ 走行開始時 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1928] tools/dev_wave_land.py の _worktree_snapshot と _validate_admin_binding が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1929] _registered_worktree_paths の resolve 失敗は _FoldGateFailure の既定 (retryabl… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1930] coordinator の登録 scan には 時間上限が無い。親の実測で単一 process でも 808.553 ms の外れ値が出ており… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1931] 変異 harness の node 抽出器は FAILED  行だけを読むため、fixture / setup で落ちる変異を rc=1 でも… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1932] **実行器の tip 等値要求は外さない** (D1151)。 択 B (一度きりの land 例外) は受理する authority が無く… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1935] dev-wave reference の byte 予算に 余白がゼロで、実測した手順の穴を 1 行も書けない。本 wave は 4 件を候補… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1937] orchestrator/tests/acceptance_duration_ledger.json を変更後の受入 JUnit 群から全再生… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1938] 受入 wall の律速は総 work (7874.186 秒、W/48 = 164.046 秒) であって排他鎖ではない。work の上位は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1939] 本 wave が足した HEAD 不変 gate は、 helper の恒真化変異は殺せるが、**呼び出し行そのものを消す変異は殺せない**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1952] 定期更新の担い手を land 側に置く。**pin は 2 種へ分ける** — 所要値は性質述語へ、 node 集合は基準時点に対する exa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1953] docs/dev-wave/** の L1.5 予算 9,566 bytes が 満杯で、実測に基づく短い注意書き (数十 bytes) すら… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1954] tools/audit_dangling_commits.py の 外部控え抑止から basename 一致条件を外せるかを検討する。安全側の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1959] 裁定を確定する前に、同じ主題の 既裁定を主題語で全文検索して抵触を洗い出す手順を、裁定を作る側の command へ足す。 本 wave の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1960] [T-1952] と同じ変更単位で扱う。所要値の exact pin は測定機の個体差を assert する型なので 性質述語へ緩めるが、**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1964] 変異契約の事前登録節へ 「静的に単一理由性を確定できない変異は、登録前に一時変異と焦点走 1 回で落ちる node を実測する」を 足す。本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1972] 後継表・規則の正本・ README 導線の 3 点で充足と認める。原表だけを開いた読者へ届かない残余は限界として明記する (D1208)。本項… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1976] 実行器を初めて編集し、 (i) bounded local 再入も main blob 実行へ移す、(ii) 外側の dispatcher i… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1977] 実行器束縛の検出力不足 3 件を閉じる。 (i) blob 読取の revision 指定を殺すテストが無い — unit test は re… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1979] docs/pegasus-runbook.md の受入節が 受理経路を 2 つとも現役として説明しているが、D690 以降 tools/che… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1982] 一回性を撤去した後、 「holdout の値を見てから選択・凍結・主張を変えない」がどこで守られているかを棚卸しする。 一回性が実質的な防壁と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1990] test_t1574_changed_suite_ledger_node_delta_is_exact の added 12 node は**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1991] flaky_test_holds.py の evidence_id は ^F[0-9]+$ かつ docs/failures.md に実在する… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1992] 起動ツールが指示文へ 機械的に前置する形にする (D1216)。 **人の注意を関門にしない。** 文書量の枠は D961 / D1046 /… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-1993] 隔離環境の codex 子は 実行場所判定が scheduler を叩くため pytest を実走できず必ず rc=16 になる。 本 wav… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2003] 実 repo の手順書 exact pin を照合する 唯一の test が docs_bytes の growth hold で既定スイート… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2007] 「批准を維持するか撤去するか」という問いの立て方自体が誤っていた。 **争点は批准ではなく、現行コードとの差を有効性の条件にしていたことである… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2011] D1159 を実装する。land 側の到達不能な non-attributable-only 検証枝を撤去する。受理集合を縮める方向。 正本は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2013] D1158 により D1054 の残余は閉じない。 免除路を既存の限界として docs/archive/README.md か検査器の doc… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2014] /rulings の収集に、**持ち越し項の解決本文が裁定前に書かれたまま carry されている型**を 検出する手順を足す。本 wave… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2015] /rulings が起動する consult 子の依頼文に、check_codex_output.py が要求する出力形式 (## 総括 節)… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2019] 択 (A) 採用 — 全 live Git 経路へ抑止を入れて閉包を広げる。reader 分類の前提を壊す書き込みが残ると D1008 の a… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。 2026-09-01 に登録外 reader の file:line 証拠が増えた (`test_b10_backoff_shape_sweep.py:1096`、`test_s8b_approved.py:34`、`orchestrator/tests/conftest.py:576` 経由の oracle environment 25 node、`test_mocc_trace_pair.py:121`/`:154`)。追加裁定はせず記録のみ。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2020] 共有 filesystem 上の lock を採る。成立しなければ親 tree と共有ベンチマークの双方を隔離する (D1210)。 **親の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2021] canonical node と共有される function scope fixture が実 repo へ触れているかを個別に監査する。 本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2023] 手順書の規則を正とし、 実測なしで登録されている 2 本を実測待ちへ戻す (D1212)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2040] 配線しない。 代わりに D1149 が決めた stdout telemetry と成果物 evidence の分離を実装する (D1215)。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2041] 択 (a) 採用 — fixture を実行時合成へ変え repo 内 bytes を NFC に保つ (D1216)。 **(b) は ev… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2042] DW-C01 の docs 行を旧文へ戻す変異が変異 matrix で SURVIVED した。 原因は test_normative_exa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2054] docs/dev-wave/** の L1.5 予算の 実余裕を main 取り込み後に測り直し、収容できなかった 2 件を該当 leaf 節… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2055] DW-S06-A の reasoning=xhigh が採用 pin として exact 照合されているため、 「段 5 / 6 の effo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2056] 期限付き root が保持する祖先 commit へ retention source と失効下界を伝播させる。現行は完全一致だけを見るため、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2057] merge確認後のbranch削除をexpected OID付きの最小CASにする。単独waveは立てず、次のDW-O28変更へ相乗りする (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2059] 既存startupで台帳の期限接近・超過だけを非阻止通知する。daemon、全object走査、停止gateは作らない (D1250)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2064] 並行 land 中の mutation wrapper を共通 main 進行で rc=125 にしない fixed-source clone… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
- [T-2071] dispatch変異のtimeoutをqueue / Pre-runningと child実行に分離し、child開始前の混雑でsource変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。

- [T-2128] **land の plan 作成を協調 lock の外へ移す** — 理由: 2026-09-01 ユーザー裁定
  (D1393)。land 前 `--dry-run` の義務化で同じ実害を塞いでおり、
  既存策の不足を示す実測が無い。D1368 の scope 外判断を追認する。
  再訪条件 = `--dry-run` の義務化をすり抜けた重複 plan の実害 1 件。

- [T-2175] 追記型 docs-only wave への `DW-C00` 例外 — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): 独立 2 例目の候補も自発的にレビューを起動しており、「省いたら見逃した」
  という直接の観測ではない。`DW-G03` の族一般化の条件が成立していない。
  再訪条件 = レビューを省いた追記型 wave が現在地を誤って凍結した直接の観測 1 件。

### 外部環境系

- [T-051] **資金提供元回答の送付判断** (B-044, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 回答がなお期待され承認文面があり送付確認が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-052] **ソルバ・量子質問への回答作成** (B-045, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 質問がなお open で現行回答が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-053] **他マシン clone の reset / reclone** (B-046, 出所 `docs/worklog.md`) — rewrite 前 history を含む clone を再利用する時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-054] **GitHub PR 本文の session URL 監査** (B-047, 出所 `docs/worklog.md`) — GitHub 接続と対象 PR があり URL 監査記録が無い時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-055] **GitHub refs/pull の Support GC** (B-048, 出所 `docs/worklog.md`) — 物理消去を要求し refs/pull が旧 object を保持して Support 処置が未完の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。
- [T-056] **fetch --prune 後の tracking ref 最終整合** (B-049, 出所 `docs/worklog.md`) — 実 fetch --prune の実行直前に、実行後の最終 tracking-ref 検査が未設定の時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。

- [T-259] 他マシン作業時の除外設定 — 理由: (101) の裁定で repo 側へは追記せず、別マシンで作業を始める時点で runbook に 1 行足す運用と決まった。

- [T-296] **roadmap §5 未達 (1) 専用 env-tag** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。既に閉じている (pegasus は env_contract registry へ登録済み)。残る層 C の floor 取得は [T-088] が所有。再訪条件 = なし ([T-088] が所有)。
- [T-278] **transport 断の同型経路 (env 継承の非対称)** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。provider 2 本の非対称は記録済みで、秘密境界を破った実測はない。再訪条件 = 同型の実害 1 件。
- [T-275] **dispatch 成果物 root の owner / mode / symlink 検査** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。脅威モデル自体が未定義で、同一 UID 前提では得られる保証が小さい。再訪条件 = 同型の実害 1 件。
- [T-267] **linux-baremetal の正の machine attestation** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。未知の第三の機械での実行は運用上起きない (Pegasus 専用運用)。再訪条件 = 同型の実害 1 件。
- [T-268] **pegasus を本軸の runnable env にするか** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。Pegasus は既に主戦場で、env_contract registry へ登録済み ([T-296] が実測)。問い自体が事後的になった。再訪条件 = 別の機械を本軸へ据えるとき。
- [T-250] **_job_run が env allowlist を子側で強制しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。単発事故で局所修復が既定。値契約の設計は [T-1089] と同面で、そちらも同じ基準で見送る。再訪条件 = 同型の実害 1 件。
- [T-196] **silo_ladder_rung1 / t152 の site gate 通し** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同一対象の site gate 欠落は [T-303] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-332] **site_policy の fail-open** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。分類失敗時の既定の裁定は [T-1036] が所有する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-404] **request ID discovery の部分一致** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同じ nonce 接頭辞を持つ旧 job を掴む実害の観測がない。再訪条件 = 同型の実害 1 件。
- [T-406] **receipt 永続化中に到着した signal の競合窓** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。閉じるには receipt 永続化の atomicity が要り、費用に対し得られる保証が小さい。再訪条件 = 同型の実害 1 件。
- [T-445] **hydrate の機械的強制** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。呼び忘れても悪化はせず、強制には凍結 submitter の書き換えが要る。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-486] **probe leg の実施** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-503] の設計採用により deferred で確定済み。再訪条件 = 実機受入 (生死確認実験) を実施するとき。
- [T-519] **collect_receipt.py の入力有界化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。cap 上限入力での §7.0 実測が前提で、費用に対し得られる保証が小さい。再訪条件 = 同型の実害 1 件。
- [T-538] **本番 α 取得手続きの静穏ノード事前実測** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。実測は行わず運用へ回すと裁定済み (計算ノード job は scheduler が占有を保証)。再訪条件 = 運用中に過剰拒否が観測されたとき。
- [T-547] **dispatch の非許可 key を黙って落とす件** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起票者推奨どおり落とすと裁定され、専用 wave は立てず次の dispatch 面 wave へ同梱と決着した。再訪条件 = dispatch 面を触る wave。
- [T-552] **未改名 .e を受理する終端実証第 3 経路の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-573] **crash receipt への scheduler 側独立 anchor の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-600] **判定量から reclaim 可能な file cache を差し引くか** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。[T-985] (D354) が回収不能量への変更として裁定・実装済みで本項の問いは決着した。再訪条件 = なし。
- [T-601] **local 完了 / cap 到達 / 余裕不足 / dispatcher 失敗の 4 値の永続化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-602] **user systemd 経由で cap の外へ逃げられる** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。任意 argv launcher を作らない設計のため現実的射程が小さく、閉じるには実行 sandbox が要る。再訪条件 = 同型の実害 1 件。
- [T-655] **runbook §7.0 実測表 parser の一般化** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本文自身が「それまでは着手しない」と再訪条件を定めている。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-670] **elapstim_req 増加による queue 待ちへの影響** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。既存 receipt の比較で測れるが、40 分化で待ちが伸びた実測がない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-810] **測定装置の第 1 slice と実測投入** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-831] **走行前提 (N-job barrier ほか) の実装** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-832] **pegasus-node-variance-protocol の LIVING_DOCS 登録** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-866] **§9.1 item 1 の残余と production 正例経路** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-867] **並走ガードと投入 admission の実効化** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-920] **計算ノードへの linux-tools 導入** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。閂ではなくなり、ユーザーが「今はやらない」と裁定済み (perf があれば使い無ければ無しで測る)。再訪条件 = perf counters を要する主張を立てるとき。 発火記録: 2026-08-16 に再発火 (述語 `perf counters を要する主張を立てるとき` = 8c live pilot の bench 段が `perf not found for kernel 5.15.0-173` で abort、request `0:913859.nqsv`)。同日の `/rulings` 全件 第 3 回で裁定 = 見送りは維持し、探索経路へ perf preflight を結線して degrade する ([T-1240])。perf 導入自体は正式系列の着手時に再評価する。
- [T-922] **caller 外 authority を要する残余** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-966] **admission registry への登録** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (本走完走済みで再走の実需がなく、登録には 2 同期が付随する)。再訪条件 = 再走の実需が生じたとき。
- [T-974] **staged package の依存 file manifest 化** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-975] **qsub 直前 bytes 一致と node 実読 bytes の乖離** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
- [T-985] **login headroom の判定占有量を回収不能量へ** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。実測で確認 — 本 wave の bounded local が「回収不能量=5415566904 bytes、判定占有量=5415566904 bytes」を出力しており D354 は実装済み。再訪条件 = 上限付近での過剰拒否・過剰許可が観測されたとき。
- [T-1035] **local 予算 peak record への metric / schema 版の付与** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-1078] **dispatch relay framing の wire 契約化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-1089] **dispatch request environment の値契約と receipt 束縛** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現行 key は全て単調で、非単調な key を足す予定がない。再訪条件 = 同型の実害 1 件。

- [T-1065] `tools/check_worktree_occupancy.py` の Pegasus 実行場所分類 — 理由:
  2026-08-15 /rulings 全件の裁定 = 実測を保留し、当面 login node では実行しない扱いとする。
  判定量 (cgroup charged memory ピーク) の実測はユーザー端末の手番であり、[T-1063] / [T-1064] の
  lease 化が入ればこの tool 自体の必要性が下がるため、実測のためだけに手番を使わない。
  再訪条件 = lease 化の後もこの tool を常用する必要が残ったとき。

- [T-1090] 理由: 2026-08-15 /rulings 全件、着手保留。1 dispatch job で複数 node を扱う設計は [T-1116] の実装後に再評価する — 既知赤 registry が入ると再走回数の見積りが無効になるため。有界並列化の不採用は変わらない。再訪条件 = [T-1116] の実装完了 (本 wave 時点で worklog/decisions/phase3.md のいずれにも land 記録なし、条件は未充足)。

- [T-1400] **`dispatch_compute.py` の node 側 SIGKILL 診断被覆の実測** — 理由: 裁定 2026-08-23 (/rulings 全件、択 (b) 見送り): 実害の観測がなく防御的堅牢化に当たる (2026-08-12 ユーザー方針)。親が観測する pre-start 失敗はコード構造上被覆済みである。再訪条件 = 計算ノード側の強制終了で原因が追えなかった事例 1 件。

- [T-167] ccbench pin を `c9c1a9c` へ更新する — 理由: 裁定 2026-08-29 (/rulings 全件、分類不能 8 件の
  帰属を確定): 2026-07 に新 pin が承認済みのまま 1 か月動いていない。pin の前進は測定同一性を動かすため
  再測定を伴い、現在の論文の主経路 (A-1 / A-2 / H1H2) はいずれも現行 pin で設計されている。
  **承認済みの新 pin `c9c1a9c` の記録は残す** — 再訪時は承認をやり直す。
  再訪条件 = 現行 pin では測れない要求が主経路から出たとき。
- [T-446] mimalloc の `fetchcontent_ref` (annotated tag) と `pin` (commit SHA) を照合する gate — 理由:
  裁定 2026-08-29 (/rulings 全件、相談で親の初版「採用」を反転): tag が動いても現行検査は通るのは事実だが、
  tag が実際に動いた例も arm 間で allocator が変わった実害も示されていない。exact pin を保証として
  名乗らず、解決された版と hash を粗く記録するに留める。再訪条件 = 実不一致が一度でも観測されたとき。
- [T-1129] `third_party_source_contract` の pinned-clean 判定へ ignored file 検査を加える — 理由:
  裁定 2026-08-29 (/rulings 全件、推奨どおり見送り): 実測で 71 件の生成物を抱えた tree を clean と
  宣言しているのは事実だが、既存 record schema の `clean` の意味を上書きすると旧凍結 evidence の
  読み方が変わり、影響半径が床値の外 (Silo ladder correctness/gap job) へ出る。変異 harness 側
  ([T-581]) だけを採用する。再訪条件 = 汚染 tree で得た値が凍結 evidence へ載った実害 1 件。

### テスト衛生

- [T-057] **survey #6 ratified_verify git fixture 共有化** (B-055, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — 同一 runner/env の全走が 180 秒を超える時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。発火記録: 2026-07-26 の `/rulings` が述語 `P6_source := full_suite_duration_s > 180` の**成立**を確認 (worklog 記録の全走 = 239s (2026-07-25) / 1811.26s (2026-07-26))。2026-07-19 時点の「180 秒未満」は現状と一致しない。**再走はしておらず記録値の照合のみ**で、239s → 1811s の差が runner/env・並列度の違いによるかは未確認。X5 派生述語の 20% 条件は依然 unknown。ユーザー裁定待ち。→ **裁定・消化済み (2026-07-26)**: 裁定 = (a) 原因を測る調査を 1 回入れる (+ テストのみで済む改善は同 wave で実施)。実施結果 = 全走 1811 秒 → 75 秒 → **69 秒** (2026-07-27、worklog (13)(14)(15))。
**2026-07-31 再成立**: 計算ノードでの受入全走は同一コードでも bnode002 116.25 秒 / bnode009 200.72 秒 /
bnode010 214.34 秒とノード間で 1.8 倍開き、180 秒を超えるノードがある (worklog (73))。
以後の所有は [T-201] (下限を実際に下げる 4 択)。**この項からは追加の裁定を起こさない**。
- [T-058] **survey #7 coverage 観測 (X5 派生)** (B-056, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — 新 test-hygiene wave または safety gate 変更時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。発火記録: 2026-07-19 approved-waves wave で消化 (baseline/final を観測値として記録、gate 化なし。worklog 参照)。2026-07-25 に**再発火** ([T-094] の gate 新設 = 述語 `safety_gate_changed` 成立、同 wave は網羅率を観測していない)。ユーザー裁定 = 発火の記録のみ残し、観測の実施は 1 cycle 完走後 (プロセス系 freeze の対象、worklog 2026-07-25 (7))。2026-07-27 に**三度目の発火** ([T-117] の test-hygiene wave = 述語 `new test-hygiene wave` 成立、同 wave も網羅率を観測していない)。既裁定の範囲内なので追加裁定はせず発火の記録のみ (worklog 2026-07-27 (16))。2026-07-29 に**四度目の発火** ([T-149] の編集面 literal 正本 + 機械検査テスト新設 = 述語 `safety_gate_changed` 成立、同 wave も網羅率を観測していない)。既裁定の範囲内なので追加裁定はせず発火の記録のみ (worklog 2026-07-29 (45))。2026-07-29 に**五度目の発火** ([T-141] の label 正規化 + `assert_position_only` 強化、および [T-171] の `check_docs.py` 閉包・interface・必須 adapter 検査の新設 = 述語 `safety_gate_changed` 成立、いずれの wave も網羅率を観測していない)。既裁定の範囲内なので追加裁定はせず発火の記録のみ (worklog 2026-07-29 (54))。2026-07-29 に**六度目の発火** ([T-172] の `check_docs.py` 閉包・interface・必須 adapter 検査の新設)。同 wave は網羅率を観測していないが、既裁定どおり追加裁定はせず発火記録のみ。 2026-08-02 の D125 / D127 / D128 と 2026-08-03 の fold 機構 wave で計 4 回再発火した (述語 `safety_gate_changed`)。既裁定どおり追加裁定はせず記録のみで、いずれの wave も網羅率を観測していない。記録経路が無かったため滞留していた分をまとめて書き戻した。 さらに 2026-08-03 の (132) land 署名判定変更と (135) reasoning 許可リスト新設で 2 回再発火した (述語 `safety_gate_changed`)。既裁定どおり追加裁定はせず記録のみで、いずれの wave も網羅率を観測していない。(133) の dispatch 欠陥修正は受理集合を変えないため数えていない。 2026-08-06 再発火 ((230)〜(233) ほか安全 gate 新設群)。追加裁定なし記録のみ (D:prototype-robustness-bar)
- [T-059] **survey #7 差分 mutation 標準化 (X5 派生)** (B-057, 出所 `output/insights/2026-07-19_test-suite-hygiene-survey.md`) — validator / reject gate 変更または escaped defect 観測時。裁定 2026-07-19 保留承認、述語の正本 = `output/insights/2026-07-19_backlog-triage.md`。発火記録: 2026-07-19 approved-waves wave で消化 (11 変異を実装前に事前登録、全 KILL + 生存 2 の是正。worklog 参照)。2026-07-25 に**再発火** ([T-094] の reject gate 新設 = 述語 `validator_or_rejection_gate_changed` 成立)。ユーザー裁定 = **追認のみ** — 同 wave が 13 変異を実装前に事前登録し 13/13 KILL と復元後 green を記録したため真時 action は実質履行済み (worklog 2026-07-25 (7))。2026-07-29 に**三度目の発火** ([T-149] の編集面機械検査テスト新設 = 述語 `validator_or_rejection_gate_changed` 成立)。ユーザー裁定 = **追認のみ** — 同 wave が変異 9 件を実装前に事前登録し 9/9 KILLED と最終 commit への anchor 再検証を記録したため真時 action は実質履行済み (worklog 2026-07-29 (45))。2026-07-29 に**四度目の発火** ([T-141] の provenance 構造検証 + 閾値検査、および [T-171] の `check_docs.py` drift 拒否検査の新設 = 述語 `validator_or_rejection_gate_changed` 成立)。既裁定の範囲内なので追加裁定はせず記録のみ — [T-141] wave が変異 3 件を実装前に事前登録し 3/3 KILL を記録したため真時 action は履行済み (worklog 2026-07-29 (54))。2026-07-29 に**五度目の発火** ([T-172] の `check_docs.py` drift 拒否検査の新設)。同 wave は負例 5 件を追加したが、真時 action が求める実装前の mutant/operator・予算・第一失敗 assert の事前登録記録はない。2026-07-29 ユーザー再裁定で **bounded な事後 mutation audit** を採用し、事前登録不能だった手順逸脱を明記した上で operator / 予算 / 第一失敗 assert / 復元後 green を事後台帳へ固定する。実施は別タスクとして待機中 (worklog (62))。2026-08-01 に**六度目の発火** ([T-118] の provider lifecycle guard 新設 = 述語 `validator_or_rejection_gate_changed` 成立)。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 16 件を実装前に事前登録し 16/16 KILLED / canonical 一致 16/16 を記録したため真時 action は履行済み。ただし**初回本走は harness の抽出不良で全件 SURVIVED になり、erratum として残置した** (F71。worklog (97))。 2026-08-02 の D125 / D127 / D128 と 2026-08-03 の fold 機構 wave で計 4 回再発火した (述語 `validator_or_rejection_gate_changed`)。fold 機構 wave は真時 action を履行し、24 変異を実装前に事前登録した。記録経路が無かったため滞留していた分をまとめて書き戻した。 さらに 2026-08-03 の (132) と (135) で 2 回再発火した (述語 `validator_or_rejection_gate_changed`)。真時 action は両 wave とも履行済み — (132) は 8 変異すべて kill、(135) は 11/11 KILLED。(133) は数えていない。 発火記録の追補 (2026-08-03 棚卸し): 2026-08-01 の (98) [T-247] 予約 envelope 拒否・(99) [T-244] generation 予算 + freshness validator・(100) [T-249] 閉集合 gate も述語 `validator_or_rejection_gate_changed` を成立させていた (計 3 回)。既裁定の範囲内のため追加裁定はせず記録のみ ([T-297] の指摘を確認して書き戻した)。 2026-08-06 再発火 (同上)。追加裁定なし記録のみ (D:prototype-robustness-bar) 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = 住所 (address edge) の構造 lint 新設)。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 8 件を実装前に事前登録し 8/8 KILLED を記録したため真時 action は履行済み。ただし事前登録のうち 2 件は当初「殺せない負例」で不成立であり、実装前の検算で是正した。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = [T-739] の凍結発行・履歴検証層への NUL 検査 gate 新設、worklog (406))。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 6 件 (M6 は段 6 で追加登録) を事前登録し 6/6 KILLED・期待 node 完全一致を記録したため真時 action は履行済み。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = [T-657] 段 0 裁定実施 wave の設計正本 drift 機械束縛 + HTML comment 拒否検査の新設、worklog (414))。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 7 件を事前登録し 7/7 KILLED・全件事前登録一致 (erratum 1 件は同エントリに記録) を記録したため真時 action は履行済み。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = [T-750] 統合実装 wave の `verify_manifest` cell-product 検査新設、worklog (417))。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 8 件を事前登録し 6 KILLED + 2 MISMATCH (単独再走で不再現、erratum 残置) = 実質 8/8 を記録したため真時 action は履行済み。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = [T-787] の凍結発行・検証層への CR/LF 拒否 gate 新設、worklog (421))。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 14 件を事前登録し 14/14 KILLED (初回 1 件は期待側の誤りで MISMATCH、訂正後に一致) を記録したため真時 action は履行済み。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = [T-756] commit-witness wave の trace 外 counter 突き合わせ検査新設、worklog の同 wave エントリ)。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 14 件を事前登録し 14/14 KILLED + drift control SURVIVED (事前登録どおり) を記録したため真時 action は履行済み。 2026-08-11 に**再発火** (述語 `validator_or_rejection_gate_changed` = codex-hook-parity wave の PreToolUse 拒否 hook 新設、worklog (427))。既裁定の範囲内なので追加裁定はせず記録のみ — 同 wave が変異 5 件 (wave 前の形への revert を含む) を事前登録し 5/5 KILLED・harness rc=0 を記録したため真時 action は履行済み。
- [T-190] **Codex worker launcher の高 xdist 負荷フレークを証拠保存つきで閉じる** (F57) —
  normal fakeが32-worker全走で失敗したときのreceipt / stop reasonを保持し、
  単独・同file・16/32-worker対照で原因を分離する。production wall-clock gateは緩めず、
  fixture readinessまたはtest専用予算のどちらを直すかを実測後に裁定する。

- [T-271] closure wave の T-126 submitter 赤の原因究明 — 理由: 原因不明・再現不能・追跡不能として扱うと記録済み。再発を観測した時点で request ID・ノード・生ログを添えて新規起票する。
- [T-230] 受入全走のフレーク率が上がった可能性 — 理由: `DW-O18` により差分へ帰属させず、再発時に insight §8 を一次資料として起票すると記録済み。
- [T-136] 受入テストの timing 依存フレーク除去の残余 — 理由: 機序自体は (35) で完了 (baseline 10/10 赤 → fix 40/40 緑)。insight §7 の残余リスク (固定短窓・無界 WAL/fsync・0.5 秒 durability 窓) は当時「新規タスク化せず」と裁定されており、再観測した時点で起票する。
- [T-135] T-080 E2E の key C/D を amend で導出する案 — 理由: (36) で却下済み (stub-free 契約を弱めるため、規律 2)。
- [T-010] B-008 (guard_agent) の再試験 — 理由: (16) の実照合で daemon の major/minor が同一のため未発火と確定した。次に major/minor が上がった新規 background session で再試験する (手順の正本は hooks/README.md)。
- [T-121] real-repo group の reader/writer 分離 — 理由: (22) で実質不要と判明した (直列和 0.1 秒でもはや制約でない)。
- [T-131] worker 間 fixture 共有 — 理由: (23) で却下済み (効果は CPU work −13.9% / wall ゼロなのに、正しさ基盤へ偽緑経路を持ち込むため)。当時の代替 2 件のうち [T-132] は完了済み、[T-135] は (36) で別途却下された。
- [T-161] check_docs の positive control に段 5 operation 行削除の focused ケースが無い件 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み。
- [T-164] s6 freshness テストの fake ls-tree 引数 pin と型境界 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み。

- [T-299] **test_s8b_oracle_driver の 40 件が local main で赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 に当該 file を単独実走し **82 passed / 14 skipped / 赤 0** を実測した (敵対レビューが「440 件の緑受入は当該 nodeid の消失を示さない」と指摘したため、推論でなく直接測り直した)。再訪条件 = 同 file の系統的な gate 拒否が再発したとき。
- [T-118] **provider neutral tree の残留の再測定** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。残留の帰属は [T-280] (production 例外経路) が持つ。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-281] **テスト側の素の mkdtemp 60 箇所** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/tests/test_p3_s4_loop.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-218] **中継まわりのテスト衛生 3 件** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-134] **xdist 並列度の再最適化** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。受入 wall の実測最適化は [T-989] 系が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-123] **daemon.py の _atomic_json (デッドコード) の削除** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-113] **source_resolver root-isolation 変異を殺す control** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-130] **_uses_real_build_v2 のビルド時間短縮** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-989] 系が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-377] **変異本走 V9 の xhigh node の無関係な赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
- [T-423] **非 UTF-8 probe file による受入全走の赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 の実測で python3 tools/ruleops.py inventory --repo . が rc=0。受入を止める赤は存在しない。再訪条件 = 同型の inventory 拒否が再発したとき。
- [T-427] **test_check_receipt_rejects_impossible_truth_table の 16 並列時の赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
- [T-430] **ruleops inventory の rc=2** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同上の実測で rc=0。[T-423] と同一事象。再訪条件 = 同上。
- [T-431] **test_check_receipt_rechecks_all_manifest_header_fields の 1 回だけの赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
- [T-447] **test_agent_sandbox_binds_exclude_attempt_receipt_directory の setup error** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
- [T-480] **real-repo テストが並列全走で落ちる構造** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。族一般化は [T-826] (M0 = 分割不変性と real-repo 排他閉包) が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-509] **standalone entry point への import root 挿入の横断確認** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-603] **check_docs の command 文書 guard positive control の 1 回だけの偽赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
- [T-663] **受入全走限定フレークの自己申告計装** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。計装は済み、残りは実負荷で artifact を 1 件得るだけの受動待ち。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。 発火記録: 2026-08-25 の `/rulings` 全件で再訪条件の成立を確認した。F273 の 2026-08-23 再発記録が stop_reason と receipt の限度・実測値を含む artifact を与えており、計装が待っていた受動条件は満たされた。以後の扱いは D783 の実装へ合流する。
- [T-698] **test_exploration_external_root_keeps_wave_clean の両ノードでの赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。決定的な再現条件を特定した [T-1079] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-731] **同 test の走行範囲依存の赤 (3 例目)** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-1079] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-736] **local 実行モードで常に赤くなる exploration output root 系 5 件** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-764] **発行 tool test の sys.path 復元漏れ** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-771] **依存物ガードが CalledProcessError / UnicodeError まで skip に落とす** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-772] **launcher 終了観測フレークの帰属** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。帰属先の production 欠陥はエントリ 548 で修正済み。再訪条件 = 同上。
- [T-844] **launcher 終了検査の受入フレーク** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。エントリ 548 が production 欠陥 (/proc 全走査中の一過性読取失敗で residual=None) を特定して修正し、永続 unknown と一過性の双方を検査する試験を新設した。再訪条件 = 同 2 述語の余剰が再発したとき。
- [T-888] **test_t793_report の supersession 走査が D305 で赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同実測で緑。main を止める赤は解消済み。再訪条件 = 同 file の supersession 固定が再び破れたとき。
- [T-992] **real_repo_receipt_memo の flock 待ち 950 node 秒** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-993] **benchmark_snapshots の worker 跨ぎ重複構築 165 node 秒** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/tests/test_codex_reasoning_ab.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-996] **保留の import 時拒否が session 印の残留で無効化される** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-1003] **_assert_history_transition の n 親一般化と main の赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 の実測で test_s8c_preregistration_invariant.py + test_t793_report.py が 17 passed。赤は解消済み。残る「3 親以上の merge を禁じるか」は防御的堅牢化の既定見送り側。再訪条件 = octopus merge 由来の赤が再発したとき。
- [T-1007] **benchmark_snapshots の worker 跨ぎ共有** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/tests/test_codex_reasoning_ab.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。

- [T-1066] 受入投入前に ignored file を撤去する 1 行 — 理由: 2026-08-15 /rulings 全件の裁定 = 2026-08-16 にフレーク本体を解消した (本エントリ)。見送り対象である「受入投入前に ignored file を撤去する 1 行」は据え置きで再訪条件も変わらない。
  据え置き。実効経路を code から示せず、`output/pegasus-dispatch/` の無限定撤去は投入停止ラッチを
  消しうる。#10 自身が定めた順序 (まず実受入で再発の有無を観測する) に従い、以後の受入で
  この原因の失敗は報告されていない。再訪条件 = 同じ原因の受入失敗を実際に観測したとき。

- [T-097] 変異台帳 JSON を placeholder 検出の対象族へ足す — 理由: 裁定 2026-08-29 (/rulings 全件、
  分類不能 8 件の帰属を確定): 2026-07 の裁定済み実装待ちで、以後 placeholder 取りこぼしの実測がない。
  再訪条件 = 同型の実害 1 件。
- [T-100] 検出語彙へ表記ゆれ・HTML entity を足す — 理由: 裁定 2026-08-29 (/rulings 全件、分類不能 8 件の
  帰属を確定): [T-097] と同じ族で、実害の観測がない。再訪条件 = 同型の実害 1 件。
- [T-133] テスト用 git の fsync 無効化、または TMPDIR を tmpfs に — 理由: 裁定 2026-08-29 (/rulings 全件、
  分類不能 8 件の帰属を確定): 受入全走の所要は D820 が「直列性と分割数では解かず費用側だけを下げる」と
  決めており、本項は当時の測定でも律速でなかった。再訪条件 = 受入全走の所要上限を侵食すると実測されたとき。

- [T-2142] 凍結した変異 spec の期待 node が後から hold に入る件 — 理由: 裁定 2026-09-02
  (/rulings 全件、推奨どおり見送り): 択 (a) 何もしない。新規 gate となる (b)(c) は
  `DW-G03` の独立 2 例を要するが、本走が観測したのは 1 例だけである。実走時に判明すれば足りる。
  高費用テストの保留解除も、保留理由が費用であって正しさではないため併せて見送る。
  再訪条件 = 同型の 2 例目を観測したとき。
- [T-2143] M02 / M10 の期待集合の登録漏れ — 理由: 裁定 2026-09-02 (/rulings 全件、
  推奨どおり見送り): erratum を残して現状のまま置く。再登録して MISMATCH を消すと、
  実測に合わせて凍結期待を書き換える前例を作る。規律 7 の趣旨を優先する。
  再訪条件 = 凍結 spec の世代を正規手続きで更新するとき。

### Codex dev-wave 資源効率化 (P1、2026-07-29 監査)

以下は 1 ID = 1 将来セッションを上限とする。品質面では T-153(e)/T-154 wave が must-fix 11 件と
mutation 8/8 を閉じたため、一括 downshift はせず、観測→制限→比較→採用の順で進める。

- [T-179] **(完了 2026-07-29) worker 資源台帳の正本化** — `tools/codex_worker_ledger.py`
  (read-only) と合成 fixture 回帰を追加。rollout ログから session/stage/model/reasoning/
  model_calls、input・cached input・output・CLI reported token、終了分類、validator、retry を
  決定的に集計する。live inference なしで T-153(e)/T-154 の 10 session・434 model calls・
  2,757,982 CLI reported tokens と stage 別内訳を再構成し、worklog (59) の「9 jobs」との不一致
  (review 3 対 4、総数 9 対 10) を `--strict` rc=2 で検出する。実装・検査・変異 10/10 KILLED の
  正本は worklog 2026-07-29 (64)、逐語と凍結値は
  `output/insights/2026-07-29_t179-worker-ledger-verbatim/`。
  wave 受理集合の確定 (cwd 部分一致の限界) は [T-180]、retry の因果同定は [T-183] へ送った。
- [T-180] **(完了 2026-07-30) job 単位 resource envelope** — `tools/codex_worker_launch.py`
  (`run` / `check-receipt`) と `CodexWorkerSessionManifest`、ledger の `--manifest` selector を
  追加。`codex-cli 0.146.0` は上限 flag を持たないため wrapper 側で強制し、**hard cap は
  wall-clock だけ**、`model_calls` と token は観測可能な proxy による best-effort 停止 +
  事後 fail-closed 判定と明示する。live 停止は rollout tail、終了判定は stdout 最終
  `turn.completed.usage` の二重 metering。上限停止・metering 欠落・終了未確認は無条件で非採用。
  T-179 の凍結値 (10 session / 434 model_calls / 2,757,982 cli_reported と stage 別 6 値) を
  manifest 経路で逐件再現し、`cached_input_tokens > input_tokens` で `cli_reported` が負になる
  継承欠陥も塞いだ。本 wave の段 6 レビュー 3 本を launcher 経由で起動し実 receipt を得た
  (dogfood)。実装・検査・変異 10/10 KILLED の正本は worklog 2026-07-30 (65)、逐語と凍結値は
  `output/insights/2026-07-29_t180-resource-envelope-wave/`。
  **DW-O01 の結線と stage 別上限値は [T-184] の所有**、失敗型分類・retry policy は [T-183]、
  seal ceremony / 脱出子封じ込め / artifact bytes 上限は [T-186] へ送った。
- [T-181] **(装置完了 2026-07-30・認証済み再走 2026-08-09) reasoning routing の限定 A/B** —
  `tools/codex_reasoning_ab.py` (read-only) と回帰 194 件を追加し、focused review の
  `max` 対 `high` を**歴史 prompt 由来の新規凍結 benchmark**上で比較した (歴史入力の byte 再現は
  不可能と実測。歴史 run は指定 9 入力以外も実読していた)。既定値は変更していない。
  primary (label-masked 裁定、親 + 独立第二読者が 10/10 一致) は名指し R-1 正例で
  `high` 3/3・`max` 3/3、限定負例で偽 R-1 は両 arm 0 件。資源は max が一貫して大きい。
  変異 kill 12/12 (両層同時 M6p 込み)。2026-07-30 の `aggregate`/`verify` は
  `experiment_complete=false` (全 run の snapshot oracle replay mismatch) であり、
  **同成果物は job tmp 削除により 2026-08-09 時点で再検証不能**である (引用しない)。
  正本は worklog 2026-07-30 (65)、逐語は `output/insights/2026-07-30_t181-reasoning-ab/`。
  **2026-08-09 に同一プロトコルを最終版装置で 10 run 再走し認証した** —
  `aggregate`/`verify` とも rc=0 / `experiment_complete=true`、両読者一致 10/10、
  正例 `high` 3/3・`max` 3/3、負例の偽 R-1 は両 arm 0 件で 4 run とも GO。
  台帳は `output/insights/2026-08-09_t181-certified-rerun/`。
  ただし機械 `decision` 行は採点器の decision 抽出欠陥 (F176) に汚染されている。
  **2026-08-09 のユーザー裁定 (b) により 10 run は再走せず、採点器だけを是正し、
  台帳へ erratum を添えて [T-184] へ渡す** ([T-685])。汚染閉包 8 field と、
  [T-184] が使ってよい human-derived の join は
  `output/insights/2026-08-09_t181-certified-rerun/erratum-f176.md` が正本である。
  **機械 `decision` 行・`primary_judgment_ledger`・両 eligibility を実質的に引用してはならない。**
  充足されるのは [T-184] の [T-181] 依存だけで、[T-184] 全体の開始可否は別条件による。
  logical turn は測れておらず、finding dedup は意味同値判断、masking は
  same-owner advisory である (limitation は insight に全文)。
- [T-182] **(完了 2026-07-29) model routing の限定 shadow pilot** — 段 3 敵対相談レンズ B を
  同一凍結入力 (`prompt_hash` 一致) で `gpt-5.6-sol`@max (authoritative) /
  `gpt-5.6-luna`@max / `gpt-5.4-mini`@xhigh の 3 arm へ投入した。shadow は置換でなく追加で、
  production 既定は不変。結果 = luna が sol の所見 11 件中 10 件 (91%) を誤検出 0 で再現し
  token −31.6%、mini は 5 件 (45%) で wall +39.0%。**実装差分なし** — 専用ツールは独立 3 レンズの
  NO-GO (未配線で gate にならない、attest 経路が外部にある) を受けて実装しない裁定。
  被覆率は循環・非盲検・事前登録なし・n=1 のため **policy 根拠にしない**。
  **2026-08-08 追記: production 既定はその後ユーザー裁定で変わった** — 段 3 は sol 1 本 +
  luna 1 本の混成になった。根拠はユーザー裁定であって本 pilot の被覆率ではない。
  正本は同日の decisions と worklog、材料は
  `output/insights/2026-08-08_t182-luna-stage3-hybrid.md`。
  正本 = worklog 2026-07-30 (68)、分析と裁定パッケージ =
  `output/insights/2026-07-29_t182-model-routing-shadow-pilot.md`、逐語 = 同 `-verbatim/`。
  妥当な比較実験の設計は [T-189] へ送った。
- [T-183] **P1、T-179 後: F43/F45 型の早期停止と回復** — exit 0 の短小/断片出力と
  safety-filter 非ゼロ終了を別分類し、同一失敗の無制限再試行を禁止する。F43/F45 由来 fixture で
  zero-output、validator reject、retry 上限、代替経路不能時の fail-closed を検証する。
- [T-184] **P1・reasoning 面は採用済み (2026-08-10)、resource/retry は残: 証拠に基づく既定
  policy 採用** — 各 pilot の台帳を比較し、model/reasoning/resource/retry の stage matrix を
  DW-O01 と worker 契約へ一度だけ反映する。受入は docs drift 検査、選択理由 receipt、
  critical stage の品質不変、旧 policy への明示 rollback を含み、
  新たな比較実験はこの ID に持ち込まない。
  **2026-08-10 に reasoning 面だけを確定した** — 段 2 / 段 3 = `max`、段 5 = `high` は
  **対象工程の直接比較証拠が無いことを明記した保守的据え置き**として採用し、
  段 6 の `high` は D243 の追認とした。**値は 1 つも変更していない。**
  [T-181] の認証再走と erratum は待機条件の充足にだけ使い、段 6 focused review の限定観測を
  他工程へ外挿しない (台帳に工程軸の field は無く、束縛された 2 prompt はいずれも段 6)。
  **機械 pin は増やしていない** — 段 5 節への pin 拡大は [T-667] が「見送りで終端」と裁定済みで、
  再訪条件 (当該節の drift の実測) は workers.md の全 19 commit 走査で **drift 0 件**、すなわち
  不成立だった。選択理由・実測・rollback・裁定パッケージ 3 件は
  `output/insights/2026-08-10_t184-reasoning-policy-adoption.md`。
  **本項は完了していない。** resource envelope (DW-O01 の launcher 結線と stage 別上限値) は
  設計択一として裁定へ、retry policy は [T-183] 未完了で依存が未充足。
  **reasoning 面の採用を [T-316] / [T-665]/[T-662] の待ち解除根拠にしてはならない** —
  それらが待つのは canonical stage matrix と起動前 policy であり、本項は未発行である。

- [T-345] **敵対レンズ prompt の書き分け (DW-S03)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-346] **完了済みタスクを引数に受けた場合の作法 (DW-S01)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-341] **consumer 不在の粒度規律 (DW-S01)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-328] **従属 4 件の収容先の確定** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-279] **テストを実走できない子に緑を主張させない** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-312] **新 gate 群への事前登録変異の dogfood** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。tools/mutation_harness.py は以後ほぼ全 wave の本走で使われており dogfood は実績で満たされた。併記された機械化余地は個別 ID が保持する。再訪条件 = harness 自身の検出力を疑う事象が出たとき。
- [T-219] **dev-wave 改善候補 4 件の枠づくり** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-214] **分割 commit の gate 通過確認義務** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-264] **実装子 prompt への「テスト実走は親」の明記** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-208] **cleanup-branches.md への F26 / F63 の運用則** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-215] **試行台帳の collected_node_digest が空 (sidecar 還送)** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-216] **_bounded_log の省略注記が literal 2 文字** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-217] **中継中シグナルの複合副作用のテスト** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-204] **未使用 L2 節を削って docs 予算を空ける** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。削除候補の洗い出しは 3 度とも候補ゼロ。空きは [T-959] が実測した L2 の 7,252 bytes が持つ。再訪条件 = なし ([T-959] が所有)。
- [T-199] **dev-wave 改善候補 3 件 (親の実装面境界ほか)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-009] **実装子が負う規律の所在の明文化** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-160] **DW-CTX への背景 job handoff 置き場ポインタ** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-166] **隔離 checkout への modules cache 複製と rc 13/14 の粒度** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-174] **渡した prompt bytes の保存による事後監査** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-175] **射影入力の人可読記録** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-177] **未使用 L2 節削除による DW-O02 統合** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同上 — 削除経路は尽きており、収容先は [T-959] の L2 枠設計が持つ。再訪条件 = なし ([T-959] が所有)。
- [T-224] **DW-S06-A への親の実測主張の義務ほか 3 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-335] **DW-O09 の pin 閉包列挙が凍結文書のソース sha256 pin を拾えない** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同型は failures 台帳に F301 として型で記録済みで、手順側は「編集面 path も検索する」として実務に定着した。再訪条件 = 同型の再発 1 件。
- [T-359] **運用の穴 3 件の外出し** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-369] **条件読み層への 2 件の統合** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-371] **model x reasoning 非対応組の事前検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。許可リスト機構が所有し、同機構は実装済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-373] **requested_reasoning と validity の分離記録** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-375] **DW-M01 への受理集合縮小変異の literal 機械検索** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-376] **DW-S01 への「(Pn) には最も安い反証実測を併記」** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-385] **M02 / M08 の帰属不成立と M11 の未説明 2 node** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-386] **条件読み層への 2 件の統合 (同型)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-394] **外部 supervisor の DW-CTX 読了の結線** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。supervisor は現在 fake-only で runtime blocked。無人継続を実運用に入れるまで発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-395] **DW-O18 への計算ノード pytest の正規経路** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-412] **剪定の発火実績観点での再開** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-417] **real-repo 直列化 node の期待表現 (F95)** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。node ID 正規化の設計は [T-876] が所有する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-432] **予算残に阻まれた是正 7 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-451] **run_tests の queue 待ち timeout の指定経路** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同 file の timeout flag 通し口は [T-870] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-458] **変異 category への diagnostic sensitivity pin 別枠** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-494] **到達不能 commit 検出の Codex 再著述と land** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。監査本体が実用時間で完走せず ([T-1000])、branch 削除はユーザー手番で稀。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-498] **campaign 固定 prompt prefix の byte-identical cache** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。LLM 実行はサブスク経路で従量課金されないため、得られるのは待ち時間だけ。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-503] **使い捨て専有 worktree の活性化** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。第一 slice は land 済みで、活性化は [T-610] が shadow 凍結の継続を裁定済み。再訪条件 = なし ([T-610] の再訪条件に従う)。
- [T-504] **_assert_clean_tracked の ignored / skip-worktree 盲点** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同一の盲点を [T-581] が実装可能な形で保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-505] **docs 予算の恒久 3 機構** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起草を担う [T-454] は既に非 active で、docs 予算方針の正本は [T-508] の (b) 主 (a) 従へ移った。再訪条件 = なし ([T-508] が所有)。
- [T-512] **loadgroup marker 付き node の事前登録** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-876] と同一の正規化問題。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-516] **audit_dangling_commits への第 2 警告カテゴリ** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同上 — 監査本体が実用時間で完走しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-521] **DW-S06-B への F112 / F124 恒久対応** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-572] **DW-G01 への driver 使い捨て既定の明文化** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-577] の 207 bytes 優先列に入らなければ見送りと裁定され、実際に入らなかった。再訪条件 = docs 予算に余白が出たとき ([T-959])。
- [T-577] **回収 207 bytes の配分** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。上位のみ採録し残りは見送りで確定済み。再発防止は failures 台帳と inbox 控え義務が担うと決着した。再訪条件 = なし。
- [T-579] **L2 削除候補の棚卸しを delta 監査へ変える** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。3 度とも候補ゼロと実測され、以後の独立 2 wave も同じ結論に達して棚卸し経路は尽きた。代替は [T-959] の L2 空き枠。再訪条件 = L2 節の membership が大きく増えたとき。
- [T-589] **到達不能 commit 検出の再著述** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-494] と同一内容の重複起票。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-593] **audit_dangling_commits の 3 事項** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同上。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-594] **DW-O01 系の記載を実挙動へ合わせる** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-610] **隔離実装の activation package** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。shadow 凍結の継続で裁定済み。独立 wave は D205 基準で現時点では起こさないと決着した。再訪条件 = L-B 実機受入の成立、または隔離を実運用で要する実害 1 件。
- [T-622] **codex_reasoning_ab の case family 一般化と protocol 凍結** — 理由: 2026-08-15 棚卸し (価値小 = 研究の本筋から外れる)。本プロジェクトの主張は workload 特化 CC の合成であり、LLM の model routing の優劣は主張に要らない。LLM 実行はサブスク経路で従量課金もされない。再訪条件 = routing 選択が結論を左右する主張を立てるとき。
- [T-626] **-rf 検査が後勝ちの -rs を防がない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-631] **DW-M01 の単一理由性の読み違え対策** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-633] **待ち手 3 条の遵守を後から確認できる field** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-634] **条件 dispatch 表の文言の機械検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同面は [T-391] が P1 で保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-636] **DW-M08 の両走が定義できない場合の代替証拠** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-651] **lease 効果の 2 wave 実運用計測** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-652] **受信側規則と release 義務の JIT 正本節への移設** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-657] **stage0 残余 2 件の機械検査への移管** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-662] **model 実引数の権威行からの導出** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。land 済みで、残余は [T-665]/[T-759] と同一束として別途裁定済み。再訪条件 = なし。
- [T-665] **effort 束縛の残余** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(b) 延期で裁定済み。発火条件と内容は [T-759] の項が保持する。再訪条件 = [T-759] の発火条件が成立したとき。
- [T-690] **DW-S05-C / DW-S01 への追記 2 行** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-702] **supervisor の DW-CTX 実読取の結線** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-394] と同一内容の重複起票。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-709] **部分集合一致の判定枠の新設** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。未実装分は [T-912] へ分離済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-710] **codex_reasoning_ab の決定 grammar の限界 3 面** — 理由: 2026-08-15 棚卸し (価値小 = 研究の本筋から外れる)。本プロジェクトの主張は workload 特化 CC の合成であり、LLM の model routing の優劣は主張に要らない。LLM 実行はサブスク経路で従量課金もされない。再訪条件 = routing 選択が結論を左右する主張を立てるとき。
- [T-712] **相反決定と冒頭 grammar 不良の failure reason の区別** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-719] **expected_nodes 完全一致による MISMATCH の量産** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。部分集合一致の判定枠は [T-709] が裁定し [T-912] が実装を持つ。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-746] **wave worktree に残った untracked campaign dir** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。当該 wave worktree は既に存在せず、撤去対象そのものが消えた。再訪条件 = 同型の campaign dir 残留が再発したとき。
- [T-753] **DW-M08 への過小予測 MISMATCH の扱い** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-759] **段 7 集合等価 gate と期待 job 台帳の freeze** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本項自身が (b) 延期で裁定済みで、発火条件の canonical stage matrix は現時点で発行されていない (matrix が発行されれば見送り台帳から拾い直す)。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
- [T-761] **U+2028 / U+2029 拒否分岐の要否** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-779] **段 5 実装子投入直前の local main 確認** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-780] **裁定文の数値は手段であって義務ではない** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-806] **DW-O01 / DW-O02 への手順欠落 3 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-811] **DW-O01 への「lane は段 3 だけ」** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-814] **DW-G05 への scope 分割時の受理集合の問い** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-819] **enforcement source closure 変異の runner 作法** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-08-17 に発火し消化 (D473 が同一ファイルを編集)。runner を drift 非感受 node へ絞る作法は本 runner 範囲で既に成立しており、閉包 member を変異させても F358 の共通核は出ず 4 node しか落ちなかった。
- [T-849] **fan-out merge index の偽造耐性** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 Unix user 前提で、プロトタイプ基準で既に見送り済みの面。再訪条件 = 同型の実害 1 件。
- [T-852] **legacy 単発経路が reservation を取らない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-08-20 [T-540] が `reservation.py` を改変し再訪条件が字面上成立したが、legacy 単発経路の reservation 欠如という実体との関連は薄いと /rulings が判定し、静観で見送りを継続する (追加裁定はせず記録のみ)。
- [T-854] **機械 gate 不在時の代替証拠の明文化** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-877] **--artifact-root の親 dir 未作成による rc=2** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。自動作成への移管は [T-845] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-909] **lease 残留の窓** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状維持 + 既知限界の明記で確定済み (窓はマイクロ秒で TTL 有界、実害実測 0 件)。再訪条件 = lease 残留の実測 1 件。
- [T-918] **DW-M03 への実行ごとに変わる生成物の除外** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-924] **M6 (terminal_reduced 誤判定) の再照準** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-926] **M7 (retry 表) の単一理由化か冗長確定か** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-927] **待ち手の偽の完了通知** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。通算 7 例を持つ [T-1056] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-931] **変異台帳の measured_seconds の記入** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-943] **本走に載せられなかった変異 15 点の再照準** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-954] **未走の変異 6 件と正例 2 件の消化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
- [T-982] **3 scan の containment 走査の共有** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/campaign/s8b_holdout_freeze.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-984] **docs/dev-wave L1.5 層の棚卸し wave** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。独立 2 wave が「削除可能な節ゼロ件」を実証し、[T-579] と同じ結論に達した。空きは [T-959] の L2 枠が持つ。再訪条件 = なし ([T-959] が所有)。
- [T-1000] **audit_dangling_commits の実行時間と rc=124 の手順** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同監査は login で 3300 秒でも完走せず、branch 掃除自体がユーザー手番で稀。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。 2026-08-26 に再訪条件が成立し、本 wave が所要を 2:22:57 から独立 3 走の最大 283.27 秒へ短縮して解消した。rc=124 の手順は `timeout` で打ち切らない方針を決定へ明記したため不要になった。
- [T-1015] **新設 detector の edge を 1 本ずつ撃つ変異 matrix** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。 2026-09-07 に再訪条件 (同一 file 相乗り) が `orchestrator/tests/conftest.py` の編集で成立。第 13 回 /rulings が索引へ戻した。 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 (D1780)。相乗り時に直す。
- [T-1054] **帰属 checker の dispatch 2n 回** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。設計案と裁定待ちは [T-1090] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
- [T-1060] **DW-** への [T-908] land 契約の収容** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
- [T-1083] **evidence_grace_s の receipt v4 での封印** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-1100] **受入試行の一次資料の所在 2 行** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。

- [T-1933] 受入 wall の nodeid から worker への対応表 — 理由: 裁定 2026-08-31
  (/rulings 全件、推奨どおり見送り): D1298 が単一 node の短縮では makespan が動かないことを
  実測で確定しており、内訳が分かっても打ち手が増えない (D1327)。
  再訪条件 = 受入 wall が再び実害として観測され、かつ frontier の構成が変わったとき。

### RuleOps hardening (P3、T-143 残余)

- [T-189] **P1、T-181 land 後: 妥当な model routing 比較実験の設計** — 独立 oracle、
  held-out 複数 task、block randomization、cache 条件の分離、価格 version、盲検裁定、
  事前非劣性 margin を備えた実験を設計する。[T-182] の pilot は n=1・非盲検・後付け採点のため
  採用根拠にしない。未裁定の論点 (served model の attest 経路が存在しない、不正 reasoning 値が
  silent に通る) は同 insight の裁定パッケージが正本。

- [T-185] **P3: receipt range 出力量の明示上限** — 非常に古い receipt range に対する
  commit 数と path-union stdout の bytes/cardinality を streaming 上限で fail-closed にし、
  上限超過時の安定 reason と synthetic negative を追加する。現行は child timeout で
  fail-closed だが、安定 reason 前の過大な stdout / memory 消費を明示的には抑えていない。

- [T-439] **許可 rc の Git stderr を strict decode しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。非ゼロ rc の分岐でしか検査せず、任意 bytes が素通りする経路の実害観測がない。再訪条件 = 同型の実害 1 件。
- [T-440] **validate_candidate_ledger の decode 非対称** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。inspect が拒否する target を check が受理しうるが、実例の観測がない。再訪条件 = 同型の実害 1 件。
- [T-629] **_scope_policy_commit の -S "scope=" の一意化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
- [T-630] **_build_ancestry の ARG_MAX 限界** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現行 1,702 commit に対し約 49,000 commit の余裕がある既存 scale 限界。再訪条件 = 同型の実害 1 件。
- [T-727] **receipt range log の走行全体 deadline** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本番 ledger は候補 0 件で発火せず、DW-G02 に従い送られたまま。再訪条件 = 同型の実害 1 件。
- [T-728] **_default_controls が git-timeout を握り潰す** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。既存挙動で、握り潰しが誤った受理を生んだ観測がない。再訪条件 = 同型の実害 1 件。
- [T-729] **cat-file --batch の返却 bytes を予算に入れていない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現状 6,494 要求 / 95 MiB の実測で収まっており上限に遠い。再訪条件 = 同型の実害 1 件。
- [T-752] **info/grafts による偽 topology** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提。DW-G02 に従い 1 cycle 後へ送られたまま。再訪条件 = 同型の実害 1 件。
- [T-994] **既知違反台帳の exact type 固定** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。str 派生型で SHA をすり替える同一 UID 敵対者前提。段 4 でも wave 前から存在する穴として scope 外裁定済み。再訪条件 = 同型の実害 1 件。
- [T-1051] **_git が PATH 上の git を起動する** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。絶対 path 固定は運用を狭め、PATH を差し替えられる敵対者を前提とする。再訪条件 = 同型の実害 1 件。
- [T-1052] **_git の timeout と stdout 上限** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。受入台帳が欠測または infra red になる診断面で、受理集合は緩まない。再訪条件 = 同型の実害 1 件。

### T-180 が返した裁定パッケージ (P3)

- [T-186] **P3: resource envelope の残余 3 件** — (a) manifest の seal ceremony と 2026-08-04 ユーザー裁定: 8c 正式実験の着手時に再評価する条件付き見送り。(a) seal ceremony は P3+P4 実装 wave の receipt 設計入力に含める。
  foreign entry 後追記の検出 (現行 membership は部分集合検査であり、receipt 発行後に
  同 wave_id へ entry を足せる)、(b) `setsid()` で process group を逃れた子の完全封じ込め
  (cgroup / bwrap。現行は残存を receipt に記録するのみ)、(c) stdout / artifact bytes の上限
  (`max_artifact_bytes`。現行の封筒射程は compute-usage に限定)。
  いずれも T-180 段 3 / 段 6 で real と裁定したが scope 外とした所見。

### 裁定・完了記録

- [T-2417] **(完了 2026-09-10) policy 腕の既存18 blockの性能解析** — 全6 permutationの
  記録値への登録式の適用を再確認した (H1 accepted / H2 rejected / H3 rejected)。compiler完全identityは
  未確認の条件付き結果であり、集約出力も未認証を明示する。認証拡大・headline昇格は含めない (D1814)。正本は
  `output/insights/2026-09-08_t2417-policy-arm-performance/README.md`。

- [T-191] **(完了 2026-07-30) Codex cleanup-branches Skill 移植** —
  `.agents/skills/cleanup-branches/` に Claude command を共通 dispatcher として再利用する薄い
  Codex adapter と生成済み UI metadata を追加。明示 `$cleanup-branches` 専用とし、
  main / primary / foreign / locked / process residency / real prune / permission / push 境界を
  Codex 固有の安全側 overlay で固定した。`check_docs.py` は Skill と command の全 bytes、
  2 file 閉包、exact interface を独立 pin と負例で拒否する。材料・レビュー・変異 =
  `output/insights/2026-07-30/t188-codex-cleanup-branches-skill-wave/`、記録 = worklog (71)。
- [T-187] **(完了 2026-07-30) `6b64d21` AI provenance forward-only是正** — 共有済みmerge
  commitはrewriteせず、固定target/payload・strict lineage・selected-set両commit・実欠落・
  correction自身greenを連言する一回限り`AI-Agent-Correction`でmissing findingだけを相殺する。
  mergeのD95 pathを全parentとの差分積へ統一し、O17を`--no-commit` preflight→`commit -F`→
  full-history監査へ更新。設計判断=D101、材料・レビュー・変異=
  `output/insights/2026-07-29/ai-provenance-forward-fix-wave/`、記録=worklog (66)。
- [T-188] **(完了 2026-07-30) dev-wave 並行 session land** — Claude command / Codex Skill が
  共有する `DW-O23` と `tools/dev_wave_land.py` を導入。別 session の handoff と
  Git admin に双方向登録された worktree container を非接触で保ち、tested SHA・ordered closure・
  common lock・SHA 指定 ff-only・stale 時の fresh-context 再受入を機械化した。設計判断=D102、
  失敗台帳=F55、材料・逐語・変異=`output/insights/2026-07-29/dev-wave-parallel-land/`、
  記録=worklog (67)。**非接触例外の条件は 2026-08-01 の D109 ([T-220]) が上書きし、
  handoff は書式を問わず非接触・拒否は incoming との衝突軸だけになった。**
- [T-145] **(完了 2026-07-29) long-path serve test の固定 join 二律背反除去** —
  `join(120)`のwall-clock合否を、実listener/SignalRelay・real exchange・shutdown/release/returnの
  ordered observationと、`INFRA_TIMEOUT / NOT_EVIDENCE`へ倒す外部child containmentへ置換。
  M1/M5は旧test SURVIVED→新test KILLED、M2〜M4は旧121秒台のthread-alive赤→新0.7〜1.7秒の
  専用diagnostic failure、T-136 preservationは4/4同一署名KILLED。逐語・裁定・台帳 =
  `output/insights/2026-07-29_t145-join-dichotomy-wave/README.md`。
- [T-143] **(完了 2026-07-29) RuleOps v1** — tracked HEAD tree の直下testと
  `output/insights/`をread-only inventoryし、人間裁定用draftとauthorityを持たない候補ledgerを
  fail-closedに検査するCLIを導入。削除・apply・approval・安全判定は行わず、受入全走へempty
  production ledgerの軽量preflightだけを結線した。設計判断=D99、運用正本=`docs/ruleops.md`、
  材料・逐語・変異=`output/insights/2026-07-29_t143-ruleops.md`。
- [T-172] **(完了 2026-07-29) Codex rulings Skill 移植** — `.agents/skills/rulings/` に
  Claude command を共通 dispatcher として再利用する薄い Codex adapter と生成済み UI metadata を追加。
  通常クラス 1、裁定記録 / 自己改善時のクラス 2 昇格、引数・hook・push 境界を明示し、
  `check_docs.py` の 2 file 閉包・interface・必須 adapter 検査と負例で drift を拒否する。
  実装・検査・commit の正本は worklog 2026-07-29 (57)。
- [T-171] **(完了 2026-07-29) Codex dev-wave Skill 移植** — `.agents/skills/dev-wave/` に
  共通 dispatcher / reference を再利用する薄い Codex adapter と生成済み UI metadata を追加。
  runtime-blocked role adapter、未配線 hook、supervisor 非互換、fresh-context 終端を明示し、
  `check_docs.py` の閉包・interface・必須 adapter 検査と positive control で drift を拒否する。
  実装・検査・commit の正本は worklog 2026-07-29 (51)。
- **(完了 2026-07-20) oracle 後処理裁定パッケージ P-A1(b)/P-B5/P-B6/P-A2/P-A5** (D64 残余、
  裁定の正本 = worklog 2026-07-20 (2)(3)、設計判断 = D65) — 探索 namespace/型隔離 (Stage 0)、
  outcome 段階 truth-table leaf、全 stage payload guard、reps=5 証拠件数検査、standalone gate-check
  の launch_validate 必須化。受入 = 対象テスト + 全走 7 連続緑 (2111 passed) + 変異 22/22 KILLED
  (台帳 = `output/insights/2026-07-20_wave2-mutation-ledger.json`)。ループ逐語と新裁定パッケージ
  P-C1〜C3 = `output/insights/2026-07-20_wave2-adjudicated-package-loop.md`。P-A1(a) は D65 の
  段階導入条件へ (worklog 参照)。
- **D39 決定 1 の wording 訂正** (B-035, 出所 `docs/archive/worklog-phase3-0702-0713.md`) — 裁定 2026-07-19: 独立検証性低下を明記する erratum として D39 へ反映。証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **locked strategy-review-freeze worktree 残骸** (B-038, 出所 `docs/archive/worklog-phase3-0714-0716.md`) — 裁定 2026-07-19: 現物不在・過去の処分証拠なしを terminal 記録。証拠と証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **user settings の model=fable→opus** (B-050, 出所 `docs/worklog.md`) — 裁定 2026-07-19: fable 既定の継続は意図的として終了し、opus は監査・統合時だけ個別指定。証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **writable 環境で全走 3 連続 rc=0** (B-054, 出所 `docs/worklog.md`) — 裁定 2026-07-19: 3 走各 1899 passed と commit ancestry を根拠に完了記録。証拠と証拠・述語の正本 = `output/insights/2026-07-19_backlog-triage.md` (裁定の正本 = worklog 2026-07-19 (7))。
- **(完了 2026-07-19) 実 repo 接触テストの xdist 単一直列 group 化** (2026-07-19 棚卸しの昇格
  B-051/052/053、worklog 2026-07-19 (7) 承認、D63) — 競合閉包 26 node を conftest 正本リスト +
  collection hook で単一 `xdist_group("real-repo")` 化、収集監査 (instance 単位・独立 golden)、
  runner の `--dist loadgroup` 既定化、snapshot 保証を porcelain -z uall raw bytes helper +
  positive control 4 種へ強化。受入 = 全走緑 + 対象反復 17/17 + worker 同載証拠 (-n2/-n32) +
  `--dist load` 対照で flake 実再現 (競合相手 = submodule patch 窓を同定)。変異 6/6 KILLED。
  排他保証は単一 runner invocation 内 (再発時は worktree 隔離 = 裁定済み escalation)。
- **(完了 2026-07-19) EVOLVE hole の禁止 delimiter byte 規則** (2026-07-19 棚卸しの昇格 B-001、
  worklog 2026-07-19 (7) 承認、D62) — 挿入行の `//`・`/*`・行末 backslash を機械 reject (文字列内も
  拒否する保守則)、テンプレ原文は文脈漏洩 delimiter (`/*` `*/` 行末 backslash) のみ禁止、content 系
  HOLE_ESCAPE evidence を非逐語化し raw WAL + critic digest の sentinel 非再掲を E2E 固定、coder
  契約 4 本 + role ledger 同期。親変異 M1〜M4 = 4/4 KILLED + レビュー所見 3 件是正。残余
  (文字列・識別子の自然言語面) は残存リスク節へ。
- **(完了 2026-07-19、隣接 3 穴も 2026-07-20 完了) oracle report の abort reason 閉表検査**
  (2026-07-19 棚卸しの昇格 B-003、
  worklog 2026-07-19 (7) 承認) — `s8b_oracle_report.py` の bench-failed 分岐に単一連言 (abort 1 件 ∧
  payload Mapping ∧ reason が str ∧ 閉表内) を追加。閉表は issuer/verifier 共有の stdlib-only leaf
  `s8b_abort_reason_contract.py` に置き、テストは leaf 非依存の golden 閉表を持つ (負例 6 種 + 変異
  3/3 KILLED)。当時 scope 外だった timeout / build-failed の同型穴と verify-inconclusive の型堅牢性も
  ユーザー承認後に閉鎖済み (worklog 2026-07-20 (1)、D64)。
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
- **hole 挿入行の自然言語混入面は comment-delimiter 経路のみ閉鎖 (2026-07-19、B-001/D62)**: 文字列
  リテラル・識別子名に載る自然言語は検疫で閉じない (一般検出は偽陽性が原理的に大きく D33 と衝突)。
  auditor / critic への残余混入面として存続。緩和 = 規律6 (入力はデータ)、auditor の人間 gate、
  必要なら軸別 token allowlist・射影の非逐語化を別項目で設計。
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
- **#include 死角の残り (道Y 一般問題) — computed include は解消 (2026-07-28、[T-148]、D93)**:
  identity 核の閉塞 (`assert_includes_match_head`) が捕えるのは literal な `#include` 行のみで、
  `#if __has_include(...)` や #define 経由の computed include は #include 行に現れず素通りしていた。
  D34 は skeleton 抽出 (骨格 #if と payload #if の区別) が完了条件 1 と両立しないとして機械防壁を予約せず、
  auditor + 規律6 の監査領域へ据え置いた。[T-148] は**選別せず一律拒否**することで skeleton 抽出なしに塞いだ —
  骨格・stock ソースはいずれも `__has_include` を使わないため、出現そのものが逸脱である。実体 =
  `assert_conditional_macros_covered` (条件式の literal 出現と `#define` 本体の両方を fails-closed)。
  **同節で塞いだ同族の穴**: 単体 preprocess の環境乖離 (TU 注入マクロ・言語標準・実 TU 供給集合・字句) は
  D93 決定 (1)〜(3) を参照。**残るのは** 未知の文脈マクロを「停止」でなく「被覆」させたい場合の設計
  (`CONTEXT_MACROS` 登録は人手) と、`resolve()` を経ない legacy `buildcache.build(src_token=None)` 経路で
  ガードが build 出口まで遅れる点。
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
  提案の消費前に実行し、欠落は差し戻す — 「機械」検査になるのは 8c の駆動配管が
  **axis-proposer を含めて**載ってから。2026-08-01 に land した 8c bounded MVP (D106) は
  trigger-gating 1 軸に固定で axis-proposer を呼ばないため、この backstop はまだ人間 gate のまま。
  実体化検証 2026-07-10 の指摘)、mechanism_hypothesis の実質性 (恒真で
  ないか・attribution 実在項目に論理的に繋がるか) は人間 gate の意味判断に依存する。機械 lint 化は
  自然文の意味検査の恒真化リスク (D30/D45 却下 (b) と同根) のため見送り。**指標 = 恒真提案の
  差し戻し率 (n=1 から記録)、発火条件 = 差し戻しが頻発するなら attribution の構造化 ID 化 +
  提案側の機械参照照合への格上げを検討。** 併せて既知限界 3 点 (主張時に限定表現する): (a) 射影
  内容の選別は手動解釈 (provenance 三点セットで事後検証可能にするのが代償)、(b) 射影者 =
  信頼中核の記憶汚染 (D46 残存リスク (a) と同型)、(c) n=1 出口採点の射影者からの分離が運用上
  不能な場合は自己採点バイアスが残る (分離不能時は provenance 記録)。
