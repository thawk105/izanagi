# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

各「次の一手」に角括弧の `T-` + 連番を置き、1〜999は3桁ゼロ埋めする。

- **位置**: トップレベル項目先頭。1原子 = 1項目 = 1 ID
- **採番**: 現行・archive・見送り台帳の最大値+1。並行branchは予約でなくland直前に振り直す
- **不変性**: land済みIDは変更・再利用しない
- **保存則**: 後続entryの消化/継続か見送り台帳へ必ず現す。archive境界も検査対象
- **本節には有効IDを書かない**

## ローテーション

Phase境界または100KB閾値前後で過去entryを`docs/archive/worklog-<範囲>.md`へ移動する。
archiveは凍結し、一覧は`docs/archive/README.md`を正本とする。

---
## 2026-07-30 (65) — [T-186] `6b64d21` AI provenanceを履歴非改変のforward correctionで是正 (コード + docs、branch codex/dev-wave-ai-provenance-forward-fix、計測 = 本worktree・ログインノード)

- ユーザー裁定どおり、main/originと8系列以上へ到達済みのmerge commitをrewriteせず、固定
  `AI-Agent-Correction` 1件で対象missing findingだけを相殺する。件名`Merge branch ...`ではなく
  trailer欠落が違反
- 元eventを再抽出して`claude-opus-5 / xhigh / integrator`を復元。session IDは永続化せず、
  sanitized fieldとevent行SHA-256へ射影。旧planner値はNO-GOで不採用
- checkerはraw/canonical/final-block、selected-set両commit、strict lineage、実欠落、
  correction自身greenを連言。一般allowlist/設定/CLI免除なし。D95のmerge pathは全parentとの差分積へ統一
- Stage 6は敵対review 2本のblockerをfix 2巡で閉じ、focused re-review 2本がGO・blocker 0。
  関連testは親実走116 passed、py_compile/diff check rc=0
- commit後変異はoutcome-changing 9/9 KILLED、structural/diagnostic pin 2/2、survivor 0。
  正制御3件と復元SHA一致を`mutation-ledger.json`へ固定
- 最終受入は3807 passed / 18 skipped、関連116 passed、docs / Codex agents /
  diff check / full-history provenanceがgreen
- 段8自己改善はF25/F37の同型再発として追記し、O17をfast-forward/merge commit分岐、
  `--no-commit` preflight、`commit -F`、既定full-history監査へ更新。予算値は上げず、重複例を縮約
- worklogは追記で100KB閾値を越えるため、(49)〜(64)を
  `docs/archive/worklog-phase3-0729-49-64.md`へローテーション。次の一手98件を全件引き継いだ
- エージェント工数: Codex subprocess 10 session (plan 1 / consult 2 / author 1 / review 2 /
  fix 2 / focused re-review 2)。親 = brief・証拠回収・裁定・統合・docs・commit
- 正本: D100、phase3完了記録、本wave insight。push/remote操作は行わない

### 次の一手

- [T-186] **完了 (本エントリ、D100)**
- [T-179] **完了 ((64))**
- [T-180] **P1・着手可 ((64))**
- [T-181] **P1・着手可 ((64))**
- [T-182] **P1・着手可 ((64))**
- [T-183] **P1・着手可 ((64))**
- [T-184] **P1・T-180〜T-183後 ((64))**
- [T-185] **P3・RuleOps hardening ((64))**
- [T-139] **完了 ((60))**
- [T-142] **close ((62))**
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 ((63)、D99)**
- [T-126] **裁定済み・実施待ち ((62))**
- [T-059] **裁定済み・実施待ち ((62))**
- [T-145] 同上
- [T-146] 同上
- [T-134] 同上
- [T-123] 同上
- [T-118] 同上
- [T-109] 同上
- [T-113] 同上
- [T-110] 同上
- [T-097] 同上
- [T-100] 同上
- [T-099] 同上
- [T-009] 同上
- [T-060] 同上
- [T-150] **P3・裁定済み ((60))**
- [T-151] 同上
- [T-154] **完了 ((60))**
- [T-130] **裁定済み・実装待ち ((60))**
- [T-135] 同上
- [T-133] 同上
- [T-144] 同上
- [T-088] 同上
- [T-096] 同上
- [T-102] 同上
- [T-122] 同上
- [T-103] 同上
- [T-089] 同上
- [T-090] 同上
- [T-112] 同上
- [T-114] 同上
- [T-011] 同上
- [T-085] 同上
- [T-087] 同上
- [T-012] 同上
- [T-010] 同上
- [T-082] 同上
- [T-121] 同上
- [T-156] 同上
- [T-159] 同上
- [T-157] 同上
- [T-148] 同上
- [T-155] 同上
- [T-140] 同上
- [T-147] 同上
- [T-127] 同上
- [T-137] 同上
- [T-138] 同上
- [T-132] 同上
- [T-131] 同上
- [T-128] 同上
- [T-120] 同上
- [T-125] 同上
- [T-116] 同上
- [T-057] 同上
- [T-117] 同上
- [T-119] 同上
- [T-105] 同上
- [T-104] 同上
- [T-101] 同上
- [T-124] 同上
- [T-108] 同上
- [T-111] 同上
- [T-160] 同上
- [T-161] 同上
- [T-162] 同上
- [T-163] 同上
- [T-164] 同上
- [T-165] 同上
- [T-166] 同上
- [T-167] **P3・裁定済み・実装待ち ((60))**
- [T-168] 同上
- [T-169] 同上
- [T-170] **P3・裁定済み ((60))**
- [T-171] **完了 ((60))**
- [T-172] 同上
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] 同上
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**
