---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: diag-login-check-wall
seq: 1
title: dev-wave 1 本が login で回す検査の回数と wall を直近 landed 12 wave から再構成した — モデル上の義務 29.4 件 / wave に対し観測できた実行は 8.2、全史監査の cold は T-2803 着地 (00:12) の前が 17 件中 12、以降は 40 件中 1 (診断のみ・実装 0 行、branch worktree-diag-login-check-wall)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。台帳 ID 未起票。一次資料は
  `output/insights/2026-09-21/login-check-count-wall/README.md` (標本・契約表・3 層の回数・warm/cold・wall の出所・log 間隔・効果見積り・裁定パッケージ・限界)。
  専用 handoff は claude job dir (`/home/SFC/tanab/.claude/jobs/4139b049/tmp/handoff/`)、wave の作業 dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/` (probe・実走出力・codex の prompt と報告)。
- 起点 local main `5efd69367` (開始 gate rc 0、07:36:51 JST。`EnterWorktree` は origin 基準で local main より遅れるので `merge --ff-only main` で揃えてから gate を打った)。
  段構成は軽量版 + 診断 wave の最小 (段 3 相談 1・段 5 author 1 + fix 2 巡・段 6 独立 read-only レビュー 1)。repo の実装面差分 0 で変異 matrix は免除 (DW-S04)。
- **親が「診断の枠」を 2 度撤回した。** 段 3 相談 (所見 18 件、must-fix 14) が P1 (契約必須回数を固定値で数える)・P2 (検査ごとの親手番を平均で一般化する)・P3 (cold 原因は 3 分類で尽きる) を否定し、段 4 で全件採用。
  段 6 レビュー (所見 16 件、must-fix 12) がさらに、cold 率換算の算術・受領証の単位 (unique と延べ)・wall の件数 (出力行数と測定回数)・log 間隔の群比較・「習慣増はほぼ無い / 契約に届いていない」という結論の踏み越えを指摘し、全件を README v2 へ反映した。
  **結論として本 wave は「習慣で増えた回数」を確定できないと書いた** — 対応付けが時刻条件を満たす実行を義務側へ吸収するため、理由未同定の 3 件は上限にならない。
- **親の実機で probe の欠陥を 2 件踏み、fix 2 巡になった** (DW-O16 の「親の実機 blocker は別枠」)。(a) 着地した全 wave 527 本の job dir を `os.walk` していて 10 分無出力 (job dir には repo の丸ごと複製が入る) → 選別を先に、複製木を刈る形へ。(b) 走行中に並走 wave が着地して標本 12 本が動く → `--as-of` で時点固定。**(b) は「同じ依頼の再走が別の答えを出す」型で、並走 wave が 13 本動いている夜には診断 wave 全般に効く。**
- 数え方は 3 層 (モデル上の義務イベント / 出力痕跡 / 時刻近傍の対応候補) に分け、混ぜないことをレビューで担保した。受領証は unique 57 件 (warm 42 / cold 13 / 再構成不能 2)、延べ対応 63 (親 22 / 受入 claim 前 23 / 取り込み後 6 / land 12)、親の unique は 18。**同じ log に 2 件の受領証が対応する例と、別 wave の親 log に対応する例が実測で出たので、wave 帰属と主体は確定ではない。**
- 裁定パッケージ (実装しない、insight §9): A 記録前後の検査の束ね (推奨、DW-O17 が既に許容)、B 親の中間 commit 監査の省略 (現行維持)、C fold dry-run の共有、D 三軸語の凍結イベント定義の明文化、E land env の partition 共有 (並走 wave `dev-wave-provenance-cold-diag` へ参照)、G 契約文の読みの明文化 (ユーザー裁定へ、B と一体)、H 検査 log を残す扱い (記録のみ)。
  **`find-fold-owned.py` を契約に載せる案はレビューの指摘で取り下げた** (痕跡 0・文書上の義務 0 から新契約を提案する形で材料不足、DW-G03 の独立 2 例にも足りない)。
  D908 (受入前の全史監査 2 本は削らない) を段 1 で引いたので、受入 tool 内の 2 本は最初から削減候補にしていない。
- 逐語の凍結で三軸語走査が**本 wave の新 file 1 件**を hit した (標本 wave の走査 log の JSON を証拠行として引用していたため)。D88 と同型の可逆 defang (三軸 key 直後の `=` を全角へ 1:1、9 箇所) を当て、再走で hit が main 既存 4 file だけに戻ることを確認した (`verbatim/NORMALIZATION.md`)。
- 工数: codex 子 4 本 (consult 1 / author 1 / fix 2 / review 1 = 5 本、うち fix 2 本は親の実機 blocker)、親の login 実走 = probe 3 巡 + 検査の直接計測 3 回 + 三軸語走査 2 回。計算ノード job は 0 (焦点走は docs-only のため insight を読む test に限定)。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight §11 に追記)。

## 次の一手差分

### 新規

- {{T:login-check-obligation-reading}} **P2・ユーザー裁定待ち**: `DW-O17` の通常列 (`message → --message-file 検査 → commit -F → full 監査`) を「commit ごと」と読むか「commit 群の後に 1 回 (受入前に必ず 1 回)」と読むかを確定する。診断 (insight `2026-09-21/login-check-count-wall` §4・§9 の択 B / G) では、モデル上の義務 87 件に対し親の痕跡 23 件・親に対応した受領証 18 件だったが、上書き・非保存・対応付けの制限があるため運用実態は確定していない。後者の読みは停止位置と被覆を変えるので受理集合不変ではなく、B (中間 commit の監査省略) と一体の裁定とする。D908 (受入前 2 本は削らない)・D254・DW-O25 の 480 秒・D690 の 5 分は変えない。
- {{T:login-check-batched-call}} **P3・新規**: 記録 commit の前後の検査 (check_docs → 三軸語走査 → fold dry-run → `--message-file` → commit → full 監査) を 1 本の shell script に束ねる手順を dev-wave の reference へ収容する。`DW-O17` が既に許容している形 (先頭 `set -e`、検査 rc を pipe へ渡さない = F37) で、検査の受理集合・回数は変わらず、減るのは log 出力の間隔だけ (続けて呼んでいる 2 wave の 22 区間は中央 44 秒、残り 10 wave の 31 区間は中央 95 秒)。間隔には親の思考・子の起動・待ちが混ざるので削減量は確定していない。
