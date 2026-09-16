---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2067-exact-launch-validated
seq: 1
title: [T-2067] oracle gate core の v2 二読 fallback を廃し、exact LaunchValidatedFreeze を必須にした (コード + docs、branch worktree-dev-wave-t2067-exact-launch-validated、変異 matrix = baseline PASSED・受理境界 6/6 KILLED + 診断 pin 3/3 赤・対照 M0 SURVIVED・期待 node 完全一致・MISMATCH 0)
---

## 本文

- ユーザー依頼は「`_gate_check_core` の二読 fallback を廃し exact な `LaunchValidatedFreeze` を必須にして D65 決定 (5) の
  不変条件を全分岐で成立させる (D1872、択 (ii))。D1241 / D1313 の上限は解除しない。t080 系が `test_s8b_oracle_driver.py` を
  扱うので重なるなら test 側は触らず production + 新規 test file。Codex author + 変異事前登録。本題の fallback 廃止だけ」。
- 一次資料は `output/insights/2026-09-17/t2067-exact-launch-validated/README.md` (逐語は同 `verbatim/`)。prompt・log・receipt・
  受入 log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-exact-launch-validated/` に保全した。
- 編集面の重複検査: `impl-dev-wave-t080-accept-speed` が `test_s8b_oracle_driver.py` 865〜1950 行を保持し、他 5 worktree でも
  同 file が dirty → 既存 test file は 1 行も触らず、新規 `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py` (17 node) に
  回帰を置いた。driver 側の dirty は t1338-u2 の別領域 (887 行以降) のみで非重複。
- 設計判断は {{D:gate-core-drops-ratified-injection-port}} (P2 = core の `ratified` 引数削除、P1 = 再読維持、P3 = hash 一致 fake、
  D1984 本文の「未裁定」記述との不整合の扱い)。
- 段 3 (plan への 2 レンズ) の must-fix 3 件はいずれも裁定・登録の文言と分類 (診断差の変異を KILL から分離、v1 不変性の正例、
  I1 の量化) で、実装方向は不変。親の brief の「core 呼出 4 箇所」は 6 箇所 (`gate_check` 5 + `_gate_check_validated` 1、AST 走査) に
  訂正された。
- **親の実測で退けた懸念:** plan が「最小差分に含めない」と留保した adapter 発火時の経路は、発火条件が定数
  `HOLDOUT_RAW_SHA256` (現行 v1 freeze の bytes) に束縛されるため v2 freeze が入れず、「全分岐」の穴ではない (両レンズが現物で裏付け)。
- 段 6 (実装への 2 レンズ) は **must-fix 0**。real は I1' の量化 (裁定文言)、変異の完全集合、docstring の精度 2 件で、後者を
  Codex fix (`cb64c51ed`、docstring のみ 7+/5−) で閉じた。fix 後の焦点再レビューは docstring 2 箇所 (コード行 0) につき親の現物
  読解で代替した。
- author の sandbox で赤だった既存 3 node (`run_block_reuses_launch_validated…` 等) は親環境 (計算ノード) で緑 → sandbox 由来
  (`official-output-root` の repo 内 tmp、sealed fixture の fork 切断) で実装差分に帰属しない。
- 焦点走 (計算ノード dispatch): 新規 file 17 passed (4.69 秒)、既存 consumer 28 passed / 6 skipped (skip は既存 growth hold)。
- 変異 matrix (container worktree `t2067-mutcontainer`): probe 走 (`cb64c51ed`、全件 SURVIVED 期待) で観測 node の完全集合を採り、
  本走 (`b625a1671` 固定、02:20〜03:35 JST) は baseline PASSED、10 変異 = 対照 M0 SURVIVED + 9 KILLED (期待 node 完全一致、
  MISMATCH 0)。受理境界を変える KILL は 6 件 (static self-load 復活、isinstance 化、refusal 削除、`ratified` 注入口復活、
  hash 条件削除、exact token でも拒否する過剰拒否の対偶)、拒否のまま reason が変わる 3 件 (v2 判定の片側化、error/token の
  順序入替、v1 枝への追加) は診断 pin として別枠。観測集合は段 6 レンズ A の静的予測と完全一致した。
- 受入全走 post-1 (tip `cb64c51ed`): child 2 failed / 24401 passed / 67 skipped。赤 2 件は本 wave 起因 —
  `test_ccbench_spawn_sites.py` の `run_block` sink 行番号 pin (1783 → 1775、本 wave の行シフト) と、新規 test file の
  `orchestrator/tests/README.md` pytest 専用 allowlist 未登録 — で Codex fix-2 (`b625a1671`、2 file 各 1 行) で閉じ、変更 test
  file の単独走 67 passed で確認した。wrapper は `postrun-clean` rc=70 (受領証なし): 親が走行中に `output/insights/` へ逐語を
  書いた untracked が原因で、F350 の再発として failures fragment に記録した。最終受入 final-1 は記録 commit の tip で走らせ、
  結果は land の受領証 (job dir の `acceptance-receipt-final-1.json`) が持つ。
- commit: `d6d3360f8` (production + 新規 test、Codex author) → `cb64c51ed` (docstring fix、Codex author) → `b625a1671` (受入赤 2 件の fix、Codex author) → 記録 commit。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 2、全段 `gpt-6-astra` / `medium`)。計算ノード job: 焦点走 3、
  変異 (probe 11 + 本走 11 走)、受入 post-1 と final-1 の 2 走。

## 次の一手差分

### 完了

- [T-2067] D1872 の実装を着地した。`_gate_check_core` の v2 枝は exact `LaunchValidatedFreeze` が無ければ必ず refusal を積み、
  static self-load を撤去した。core の `ratified` 注入口も削除。D1241 / D1313 の advisory / non-certifying 上限は解除していない。
  remaining: none
  base: 3d7e845700cdaa74633f0131abbf7a97b29c135888d5a2ac64986094dca64e2d
