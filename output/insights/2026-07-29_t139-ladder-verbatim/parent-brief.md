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

## 未完の作業と次の一手
- 段 2 preflight: workers.md DW-S02 + operations.md DW-O01/O02/O03/O05 読了 → codex プラン起草

## 落とし穴・気づき
- T-139 の位置づけ制約: 既知解への復帰は recovery であって新規 CC の発明ではない。
  roadmap §1 の研究目標に数えない。ability probe として位置づけを分けて書く (曖昧化は自己欺瞞)
- main checkout に未追跡 `output/env/pegasus/floor/` あり (他セッションの成果物、触らない)

## dev-wave 改善候補
(なし)
