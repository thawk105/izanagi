# [T-139] 劣化版 Silo の梯子 — dev-wave
- 目的: 最適 Silo から段階的劣化版を生成し、登り戻し量を能力の物差しにする仕組みの初回 wave (設計 + 最小実装)
- 状態: 作業中
- 最終更新: 2026-07-28 (wave 開始)
- 基準コミット: 78eedcb (main、worktree = worktree-dev-wave-t139-ladder)

## 完了した中間成果
- クラス 3 起動完了: worklog 末尾 (37) 読了、T-139 定義 = worklog 次の一手 1 項 +
  `output/insights/2026-07-27_external-consultation-scope-and-axes.md` §3/§6-D、
  T-140 廃止 (択 c) で資源移転済み (`output/insights/2026-07-28_t140-datastructure-axis-package.md` §6)
- wave 開始必読節読了: DW-C00 / DW-CTX / DW-STOP (core.md 全文)、skill-self-improvement 全節、
  patches/README.md (positive control 体系)
- codex CLI 確認済み (codex-cli 0.145.0)

## 段 1 brief (確定)

**scope:** 梯子の設計確定 + 最小実装。(1) 設計台帳 = rung の定義様式・隔離規約・回復量 metric・
位置づけ (ability probe)。(2) rung 1 本の out-of-tree patch 実装。(3) characterization driver
(apply→build→run→verifier→revert、s3/s5/s8a 同型) + 機械判定。(4) 生死確認 (DW-G01) = rung が
apply/build/run/certified を通ること。回復ループ実走 (coder に登らせる)・gap の定量計測・
複数 rung 化は scope 外 (後続 wave)。

**確定済みユーザー裁定 (wave 引数):** 並行セッションにより main が動きうるのは既知・想定内。
local main への取り込みまで実施する。ff-only 不能なら停止して報告 (rebase しない)。

**不変条件:**
- 絶対規律 1/2/6。rung は既定 OFF inert (裸マクロ = pipeline から定義不能、broken-silo と同じ
  隔離規約)。baseline・正系列 campaign に混ぜない
- freeze / oracle gate / proof chain / 凍結成果物 bytes に触らない (grep 実測済:
  patches/ の bytes を pin する test は無い)。触る必要が判明したら DW-O09/O10 再評価 + 巻き戻し
- 位置づけ: 既知解への復帰は recovery = ability probe。roadmap §1 研究目標に数えない、と成果物に
  明記 (外部相談 insight §3 の但し書き)
- 性能値の主張なし。Pegasus の throughput を linux-baremetal 値に混ぜない (runbook §7)

**成果物の形:** patches/*.patch (rung 1) + patches/README 追記 / orchestrator/campaign/ の
ladder driver + tests / insight (設計台帳) / decisions (D 新設) / worklog (38)。

**環境 (DW-S01):** 受入全走 = pegasus02 login node `tools/run_tests.py` (g++-13 依存群 skip =
検出力欠落を記録)。生死確認の build/run = login node の動作確認扱い (runbook §7 裁定 2026-07-27)。
login node で CCBench が system g++ 11.4 で build できるかは未実測 — 生死確認の最初に実測し、
不能なら qlogin 短時間ジョブ (runbook §2) へ切替。

**provisional 裁定 (攻撃対象):**
- (P1) rung の表現 = out-of-tree patch + 裸マクロ `IZANAGI_DEGRADE_*` (D16 に第 6 類として追記)。
  submodule ブランチに焼かない
- (P2) rung 1 の劣化内容は「構造的に遅いが serializable 不変」なもの (例: 施錠経路への global
  lock-manager 様直列化)。正しさに触れる劣化は禁止
- (P3) 回復量 metric = recovery fraction (X−degraded)/(stock−degraded) を設計台帳に定義するに
  留め、本 wave では実測しない
- (P4) driver は s3/s5/s8a coverage driver 同型の機械判定 (apply round-trip / inert 確認 /
  certified 緑)
- (P5) 分割方針: 設計 = codex 起草 + 敵対相談 2 本 (設計択一が割れる → DW-C00 により子を省かない)。
  実装は patch + driver 所有一体で 1 系統、レビュー 2 本

**DW-G05 (成果物影響):** 実装しない場合、certified 選択・レポート・台帳の既存値は不変 (評価系の
追加)。失われるのは能力測定の解像度 (天井問題が未解決のまま、能力主張が「改善余地の薄い山頂での
無差」に退化する)。

**被覆確認:** ladder/degraded を扱う既存テストは無し (新概念)。純増検出力 = rung patch の
apply/inert/certified 機械判定。既存 coverage driver 群に専用 pytest は無い (実証 JSON が正本)。

## 環境実測 (brief の未実測前提を確定、2026-07-28 23:18)
- **login node (pegasus02) で CCBench trace build 成功**: system g++ 11.4 + gflags/glog を
  pinned ソース (~/github/{gflags,glog}) から static build (certify_calibration.sh §iv の作法、
  wave dir に使い捨て)。qlogin 切替は不要
- 動作確認 run (t4/tuple50/skew0.9/rmw/1s): throughput 283,303 tps 表示 (性能主張には使わない)、
  trace 4 file / 220 万行
- verifier: `python3 -m orchestrator.verifier <trace dir>` → **SERIALIZABLE certified rc=0**
  (txns=283303, edges=1695475)。生死確認の全経路 (build→run→verify) がログインノードで成立

## 段 2 完了 (プラン = ~/.claude/jobs/496a8b50/tmp/dev-wave-t139/s2-plan.md、rc=0)
- 推奨: rung 1 = lockWriteSet の CAS を中央 lock manager (global mutex) 経由化、裸マクロ
  `IZANAGI_DEGRADE_SILO_LOCK_MANAGER`、driver = silo_ladder_characterization.py、
  疑義 4 点 (劣化未実測 → 「rung candidate」呼称 / compiler 既定 / RF 定義 / source_digest 隔離)
- **worktree 基準の訂正**: EnterWorktree は origin/main (588f6a0) 基準で切られていた。
  local main (78eedcb) へ `--ff-only` 済み。次の空き D 番号は **D95** (プランの「D94」は誤り)。
  codex 子 (段 2・段 3) は旧 tree を読んでいるが、差分は T-160 の docs (dev-wave 入口/core/
  operations/skill-self-improvement/worklog/D94/check_docs) のみで、プラン対象 (silo ソース・
  patches・patchharness・D16/18/20) は不変 — プラン自体は有効。段 4 で D 番号と worklog 参照だけ
  親が訂正する
- check_docs 予算対象 = command + docs/dev-wave/** のみ (patches/README・decisions は対象外)。
  基準 tree で check_docs 緑を確認済み

## 段 3 レンズ B 完了 (s3-lensB.md、rc=0) — 判定 NO-GO (scope 縮小勧告)
- must-fix: (1) DW-G04 consumer 不在 + DW-G01 順序逆転 (gap 生死確認より先に 350 行 driver)、
  (2) DW-G05 主張過大 (梯子でなく rung candidate 1 本)、(4) 候補 A は「例の鵜呑み」で、
  central CAS gate は競合抑制で速くなる可能性すら未排除、(5) preprocess witness が実 binary と
  未結線 (stock binary でも全緑になりうる)、(6) 答えの露出 (マクロ名 DEGRADE/LOCK_MANAGER +
  隣接 #else に stock 逐語 → 将来 coder が copy して RF=1)、(7) JSON の proof 再束縛なし、
  (10) D94 衝突 (次は D95、親も独立確認済み)
- should: 第 6 類でなく D18 第 4 類の subtype (evaluation_role=ability_probe)、RF は provisional、
  変異 M1-M5 の自己言及排除、命名 stem 統一
- 予算衝突なし (patches/README・decisions に byte cap なし) は親も独立確認済み

## 段 4 裁定 (親、確定) — scope v2 = 生死 probe 先行、恒久機構は後続 wave

**採用した骨格 (lensB 判定を採用):** DW-G01/G04 により、恒久 patch・350 行 driver・pytest・
D 新設・README 第 6 類は本 wave で**実装しない** (裁定パッケージへ)。本 wave の実装物 =
(1) 使い捨て probe (patch + スクリプト ≤100 行級 ×2 本 + 結果) を
`output/insights/2026-07-28_t139-ladder-probe/` に凍結、(2) 設計台帳 insight
`output/insights/2026-07-28_t139-silo-degradation-ladder-design.md` (全裁定込み)、
(3) patches/README 分類表への第 5 類 (診断計器, D20) 行追記 (lensB-12 の既存不整合是正)、
(4) worklog (38)。probe は候補 A (CAS 中央 gate) と候補 B (writePhase 直列化) の両方を測る
(lensB-4: A は劣化にならない可能性すら未排除 → データで選定)。

**probe 設計 (lensA must-fix を反映):**
- patch 1 本・裸マクロ 2 個 `IZANAGI_T139_PROBE_CAS_GATE` / `IZANAGI_T139_PROBE_COMMIT_GATE`
  (中立命名 = lensB-6 の答え露出回避)。追加行は全て #if ブロック内。CAS は wrapper 関数化せず
  lock_guard スコープで包む (lensA-3 の参照渡し破壊を構造回避)
- inert 証明 = 同一 build dir での逐次 binary 同一性 (unpatched → hash → apply(macro OFF) →
  rebuild → hash 一致) + nm で probe シンボル 0 個。ON 証明 = nm にシンボル出現 +
  CMakeCache の flags (lensB-5 の「witness と実 binary の未結線」を binary 側で閉じる)
- 正しさ leg (login node、動作確認扱い): ON trace build → t4 高競合 run → verifier certified +
  **per-worker liveness (trace C 行の thid 全員 >0、lensA-2)** → revert clean
- gap leg (計算ノード qsub 1 job、trace-disabled): stock/A/B を同一ノードで build、
  高競合 + 中競合の 2 workload、interleaved 5 reps、median 比較。単独性 pgrep 確認・
  compiler realpath/version 記録。**probe 値であり headline 非混入** (runbook §7)
- 規律 1 遵守: 正しさ = trace build、gap = trace-disabled build の別 build・別 run (lensA-10)

**個別裁定 (real/refuted・採否):**
- lensA-1 (A の永久 deadlock 不成立) = refuted 確定。lensA-2 (hold-and-wait 飢餓) = real 採用
  (per-worker liveness を probe と台帳の受理基準に)。lensA-3 (CAS 参照同値) = real 採用 (inline 化)。
  lensA-4 (B/C/D 非等価) = real 採用 (probe は A/B、C は gap 識別不能・D は人工遅延として台帳で却下記録)。
  lensA-5/6 (preprocess witness の穴) = real 採用 (probe は binary 同一性へ置換。恒久 driver 要件
  として台帳へ)。lensA-7 (裸マクロ注入経路) = real (probe job は CXXFLAGS scrub。恒久要件は台帳)。
  lensA-8 (意味的空 patch) = real (probe の gap 実測が経験的に検出。静的契約は台帳)。
  lensA-9 (JSON 再束縛) = real、後続 wave 要件。lensA-10 (trace→perf 非転移) = real 採用 (二 leg 分離)。
  lensA-11 (親実測は stock canary であって rung G01 ではない) = real 採用 (probe が rung G01 を完了させる)。
  lensA-12 (M1-M5 単一理由不成立) = real、本 wave は恒久 gate/テスト追加なしのため**変異事前登録なし**
  (対象が存在しない。射程は worklog に明記)。lensA-13 (include 差分 = 第 2 の fails-closed) = real、
  台帳に recovery_measurement_eligibility=false / dedicated-driver-only を明記
- lensB-1 (G04/G01) = real 採用 (scope v2 の根拠)。lensB-2 (梯子過大表現) = real 採用 (成果物は
  「rung candidate の生死確認」と表記、brief の G05 行を是正)。lensB-3 (第 6 類→D18 subtype) = real、
  制度化は後続・裁定パッケージへ。lensB-4 = real 採用 (A/B 両測)。lensB-5 = real 採用 (binary witness)。
  lensB-6 = real 採用 (probe 中立命名 + 台帳に構造的対策を設計、schema field は後続)。
  lensB-7 = real 後続要件。lensB-8 = real 後続要件。lensB-9 (RF は provisional) = real 採用。
  lensB-10 (D95) = real 採用 (本 wave は D 新設なしのため参照のみ)。lensB-11 (命名 stem) = real 後続。
  lensB-12 (第 5 類未反映) = 事実確認済み・本 wave で是正。lensB-13 (予算衝突なし) = 確認済み

**ユーザーへ返す裁定パッケージ (実装せず):** (a) 恒久 rung の置き場と型 — D16 第 6 類 vs
D18 subtype (evaluation_role=ability_probe、lensB-3 推奨は後者)、(b) 恒久 driver + pytest +
JSON 再束縛 + 変異登録の実装 wave 起票 (probe 結果を前提に)、(c) 答え露出の構造的対策
(命名・schema・射影規則)、(d) RF 規範化の時期

## 段 5 進捗 (親作、2026-07-29 00:5x 時点)
- probe patch 完成 (67 行、候補 A = CAS gate / B = commit gate、裸マクロ、Edit ツール経由で
  submodule を一時編集 → diff 凍結 → Edit 逆適用で復元。guard_bash は ccbench への git
  checkout/stash を拒否する — Edit が正規チャネル)
- **inert 一次知見**: patched-OFF の同一 dir binary hash は不一致 (74c787…)、revert 後は
  f9991d40… へ完全復帰 = build 決定的。probe は patched-OFF 構成を使わない設計に変更、
  知見は insight §3.4 に記録
- **correctness leg 全緑** (t139-probe-correctness.json): A/B とも certified SERIALIZABLE、
  per-worker liveness 全 worker >0、nm 活性証明
- **gap leg job 873583 投入済み (gen_S、QUE 中)**。監視 bg = b8taj2dho。
  出力先 = worktree の output/env/pegasus/t139-probe/<jobid>/
- 設計台帳 insight 起草済み (gap 結果はプレースホルダ `<!-- GAP_RESULTS -->` — **commit 前に
  必ず実測値で置換**)。patches/README 第 5 類行 追記済み。逐語凍結 dir 作成済み
  (2026-07-29_t139-ladder-verbatim/)。check_docs 緑・repo scan invariant 緑

## gap leg 結果 (job 873583、bnode011、01:44 完了) — 生死確認 完全成立
- median tps: W1 (高競合 write t48) stock 790,027 / A 96,787 (12.3%) / B 657,927 (83.3%)。
  W2 (中競合 mixed t48) stock 10,581,616 / A 1,038,968 (9.8%) / B 1,503,646 (14.2%)
- **lensB-4「A は速くなるかも」は実測で反証** (8〜10 倍劣化)。両候補 certified + 全 worker 生存
  (correctness leg) + 劣化方向成立 = rung 候補の生死は緑
- nm witness 全通過 (stock probe_syms=0 / A・B =1 / izanagi_trace 全 binary 0 = 規律 1 witness)
- 単独性: 投入時 load 0.75・外部 ycsb なし (pgrep rc=1)。insight の GAP_RESULTS 置換済み

## 段 6 レビュー結果と fix (02:0x-02:4x)
- R1 (主張) = must-fix 7 + refuted 4 で NO-GO。R2 (記録・規約) = must-fix 7 + should 3 で NO-GO
- fix 方針 (親裁定): 再実走せず (1) 主張縮約 (2 セル局所観測・未較正・non-acceptance)、
  (2) post-hoc provenance (manifest.json + correctness sidecar)、(3) R1-7 因果訂正
  (ERR→NNN→__LINE__ を実確認 — patched-OFF は真に非 inert、witness は正しく検出した)、
  (4) 裁定追跡表を台帳 §9 へ恒久化、(5) namespace README 新設、(6) patches/README 行を
  witness 条件付きへ、(7) PBS 会計ファイルを job dir へ移動、(8) 段 6 逐語 + sha256 表を
  verbatim へ
- **DW-O12 訂正**: 段 4 裁定に書いた「probe job は CXXFLAGS scrub」は実装されなかった。実態 =
  scrub なし (manifest の unrecoverable に明記)。実行手順の正はこちら
- 焦点再レビュー走行中 (bg 待ち = bbbzj2n4k)。GO なら受入再走 → 段 7

## 焦点再レビュー結果 (round 1) と fix round 2
- 20/23 closed (縮約による closed 含む)、R2-7 partial (射影 gate は §6-5 後続要件へ —
  成果物の値・受理集合・参照を変えないため残余として受理)、regressed 3 = (1) 標本数誤記
  「全 30」→「候補 20 標本が同 workload の stock 最小を下回る」に訂正、(2) .rodata 断定 →
  「__LINE__ シフトは確実、section/単独原因は未確定 (仮説)」に緩和、(3) verbatim README を
  64 桁 hash + handoff-final 実体化で是正。3 件とも親が一次資料の再計算で closed を検証
  (min/max 標本値・debug.hh 実読・hash 再計算)

## 未完の作業と次の一手
- check_docs + repo scan + 受入全走再走 → 段 7: worklog (38) + commit (DW-O17) → 段 8 → 段 9
  (local main へ ff-only)
- 段 8 候補メモ: C1 = EnterWorktree が origin/main 基準で切る罠 (local main 照合の手順化)、
  C2 = ccbench への git checkout は guard_bash 拒否・Edit が正規チャネル、C3 = DW-O20 の
  handoff 場所義務の発火時点が遅い (dispatch 欠陥の疑い)
- 変異 matrix = 対象外 (恒久 gate/テスト追加なし)。受入 1 回目 = 3141 passed / 18 skipped rc=0

(本ファイルはこの状態で `2026-07-29_t139-ladder-verbatim/handoff-final.md` に凍結し、worklog
(38) へ吸収後に削除する)

## 落とし穴・気づき
- T-139 の位置づけ制約: 既知解への復帰は recovery であって新規 CC の発明ではない。
  roadmap §1 の研究目標に数えない。ability probe として位置づけを分けて書く (曖昧化は自己欺瞞)
- main checkout に未追跡 `output/env/pegasus/floor/` あり (他セッションの成果物、触らない)

## dev-wave 改善候補
(なし)
