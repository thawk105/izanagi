---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1480-stage5-author-replayer
seq: 1
title: [T-1480] stage5 author downstream replayer を acceptance unbound のまま実装した (コード + テスト、branch worktree-dev-wave-t1480-stage5-author-replayer)
---

## 本文

- 段構成: 段1〜4 と段5〜6 前半を先行セッションが、段6 後半以降を本セッションが担った。
  Codex 子は 11 本 (plan 1 / consult 2 / author 1 / review 2 / fix 2 / focus 3)。
  `outcome` は 10 本が `accepted`、`t1480-s6-focus1` だけが `not_accepted`。
- **`t1480-s6-focus1` の失敗は実装所見ではなく Codex 利用上限だった。** launcher receipt は
  汎用の `f45_missing_output` (output 0 bytes) で、停止理由と再開可能時刻が receipt へ残らない。
  CLI 逐語にだけ再利用可能時刻が出ていた。後続の focus2 / focus3 は同日中に走っており、
  handoff に残っていた「上限まで待つ」判断は結果として stale だった。
- 段6の敵対 review 2 本は NO-GO で、receipt の自己申告 digest・source integrity・rollback 所有・
  raw stderr・run-root/pass/pin・変異被覆を real と裁定した。fix1 の後の focus2 が F1〜F5 を挙げ、
  fix2 を経た focus3 が **GO (残存 must-fix ゼロ)** を返した。
- 棄却した所見: (a) role 別 pin の分離不足は、`downstream_pins.review` と `.fix` を exact-key の
  別 object にした設計そのものが答えであり refuted。(b) 別 wave との編集面重複警報は、候補 2 file の
  merge index blob が local main blob と byte 同一で、稼働中 author の所有 path は dispatch 系
  だったため refuted。
- **変異 probe の 1 回目は誤診しかけた。** M4 が `timeout_seconds: 300` で TIMEOUT になり
  「hang しうる変異」の形で記録が残ったが、scheduler 逐語では queue 待ち 317 秒・本体 10 秒・
  17 件の test が失敗しており、実際には十分 kill されていた。F32 の恒久対応 3 は timeout を
  fail-open の証拠と定めるため、この誤読は安全側でない。詳細は {{F:mutation-timeout-counts-queue-wait}}。
- 続く `--resume` は orphan-hold を解除しないまま投入したため dispatch が即拒否し、harness からは
  所要 0.113 秒の PARSE_ERROR にしか見えなかった ({{F:orphan-hold-collapses-resume-diagnosis}})。
  本セッションは request 不在を qstat 本文で確認し、source の clean/HEAD を確認してから hold を
  削除し、`timeout_seconds` を 2400 秒へ再登録して probe を全件走らせ直した。
- 親の 2 分 command timeout の中で `check_ai_provenance.py` を走らせ、dispatch job を孤児化させた
  (F333 再発)。この checker は自動判定で計算ノードへ出るため「git を読むだけだから軽い」という
  見積りが誤りである。今回は job が短く終わり hold は自動解除された。
- **変異 probe の待ち時間に同じ worktree へ記録を書き、wrapper を rc=125 で終わらせた** (F383 再発)。
  `mutation_worktree.py` の wrapper は source 共有木の `git status` の stdout bytes が走行前後で
  不変であることだけを主張する。追跡・未追跡も docs・実装面も区別しないので、untracked が 4 件
  増えた時点で主張が破れた。測定は固定 commit の隔離 worktree で走っており実体は健全だが、
  wrapper の保証は無効なので記録を先に commit して木を clean にし、本走を無干渉で走らせ直した。
- **段8の docs 統合は byte 予算で止めた。** 変異 TIMEOUT の誤読を防ぐ 4 行を `DW-M06`
  (hang 変異 = 誤読の発火点) へ入れようとしたが、同節が属する L1.5 層は予算 9566 bytes に対し
  既に 9565 bytes を使っており余裕がゼロだった。条件節側の `DW-M07` も単節予算 1000 bytes に対し
  978 bytes で余裕 22 bytes しかない。自己改善契約は「予算値を上げる変更は通常の自己改善に
  含めず、理由付きの独立審査対象にする」「予算のために安全義務を削除・弱化してはならない」と
  定めるため、既存文の圧縮も予算引き上げも本 wave では行わず**ユーザー裁定へ返す**。
  恒久対応は台帳 2 件と memory `mutation-timeout-includes-dispatch-queue-wait` が担う。
- 設計判断は {{D:stage5-acceptance-unbound}}。逐語と変異台帳は
  `output/insights/2026-08-24_t1480-stage5-author-replayer.md`。

## 次の一手差分

### 完了

- [T-1480] stage5-author-replayer を実装した。固定 plan 入力 hash、author patch の適用先、
  role 別 downstream model/effort pin、receipt 検証手順、fix pass 上限、出力 hash の登録機構を
  `tools/codex_reasoning_ab.py` へ stage2 と別系統で足し、直接 test で覆った。acceptance 判定条件は
  task-specific oracle が無いため `unbound` + eligibility false として正直に登録した
  ({{D:stage5-acceptance-unbound}})。意味的 disposition は {{T:stage5-semantic-disposition}} が持つ。
  remaining: none
  base: 87905885a00812a7c6671be0a3473785123258f716fd25b5a12ed9c5395573d8

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: D674 で 7 論点の処遇が確定している。
  (5) downstream replayer の実装は stage2 が land 済み、stage5 を本 wave で実装したことで閉じた。
  **残るは (4) 装置の横断的 refactor (`price_version` の非 null 拒否 2 箇所の解消を含む) だけで、
  既存の担当項目が持つ。** §8 の独立 oracle ledger は未作成のままで、これが揃うまで台帳の
  `oracle_finding_count` は `not-established` である。
  base: 0f6b32de44a780a779863481c42a6bb5fd44c507ba44deed39c9a785410b5fcc

### 新規

- {{T:stage5-semantic-disposition}} **P2・新規**: stage5 replayer の意味的 disposition を定義する。
  task-specific oracle manifest と独立 oracle ledger を作り、それを根拠に review/fix subprocess
  executor と semantic disposition を足して `task_acceptance_status` を unbound から動かす。
  oracle が無いうちは着手しない ({{D:stage5-acceptance-unbound}})。
