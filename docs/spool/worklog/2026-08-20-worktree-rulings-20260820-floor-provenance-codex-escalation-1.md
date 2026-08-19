---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-rulings-20260820-floor-provenance-codex-escalation
seq: 1
title: '/rulings セッションでdev-wave起動2件・docs予算超過3件・growth-hold登録1件を裁定し、Codex即死対応と床値measurementのprovenance標準を改めた (docsのみ、branch worktree-rulings-20260820-floor-provenance-codex-escalation)'
---

## 本文

- `/rulings all` の初回出力 (表形式・T番号/DW-O05等の内部コードを主要列に置いた索引) をユーザーが
  「分からん」と拒否した。表 + 内部コードを主要列にする形式は今後避け、平易な日本語の段落で
  状況説明を先に書く形へ改める (memory `plain-language-for-user-docs.md` へ追記済み)。
- docs予算 (L1.5) 超過で書き足せない3件 ([T-956] の2箇所・[T-1395]・[T-1404]) について、ユーザーが
  「機械検査に回せるものを回して余白を作れないか」と提案した。調査の結果:
  - [T-1404] (codex子の即死判定) は道具側の実装 (即時検知+ユーザー通知) へ振り替えるのが筋が良いと判明。
  - [T-956] のうち DW-O13 相当の1件は、CLAUDE.md 本体が既に義務化している「監査・レビュー設計時に
    failures 型タグを攻撃面へ含める」ルールで既にカバーされていると判明 (F280 経由)。
  - [T-956] の残り1件 (DW-O05、敵対レンズの語彙注意) と [T-1395] (DW-S06-B、独立作業の停止波及なし)
    は機械検査に向かず、見送りとした。[T-956] 自体は現行 active 集合に存在しない
    (`spool_fold.py --base-digest` で `base-digest-not-active`、過去のどこかの fold で既に完了扱い
    済みと見られる) ため次の一手差分の対象にせず、本節で決着だけ記録する。
- [T-688] (Codex資源枯渇による実装停止) の裁定中、ユーザーから重要な事実開示があった —
  「レートリミットに達したら自分で判断してアカウント切り替えを行っていた」。これにより、
  F411 (「usage limit表示から8分後に自然回復した、恒久対応は数分待って1回だけ再試行」) の
  根本原因分析は誤りだった可能性が高いと判明した。見かけ上の自然回復はユーザーの手動介入による
  ものであり、機構側が本当にtransientかどうかを待機だけで判別できる根拠ではなかった。
  F411 を supersede 追記で訂正し、恒久対応の設計方針を新しい決定 ({{D:codex-transient-death-escalate-not-wait}})
  へ差し替えた。
- 床値 (floor value) measurement の「official」認証要件について、ユーザーが「AIが嘘をつかない限り、
  実行環境・ビルド・パラメータを記録しておけば後から追試で再現性を確認できる、それで十分では」と
  提起した。D488 (2026-08-17) を読み直したところ、この機構は最初から「AIの虚偽を機械的に見抜く」
  ことを保証しておらず (台帳の値も producer 自身が算出するため)、実際に買っているのは
  (i) 測定前の事前 commitment (後出し選別の防止)、(ii) resume/fresh の取り違え検出、
  (iii) 台帳と artifact の不一致検出、の3つだけと判明した。床値measurementは複数試行から
  良い結果を選ぶ性質の作業ではなく基本1回測って使うため、後出し選別を防ぐ事前登録の必要性が薄いと
  判断し、標準を緩和する裁定とした ({{D:floor-value-coarse-provenance-standard}})。
- 本セッションの役割は裁定の記録と canonical 台帳への land までであり、実装 (worktree init tool・
  [T-1404] の道具化・実際の床値measurement実行) は別セッション (dev-wave / next-tasks) へ委ねる、と
  ユーザーが明示した。
- git push (未push 64 commit、`origin/main` 比) はこのセッションで裁定を得られておらず未決着のまま
  次回へ持ち越す。

## 次の一手差分

### 完了

- [T-1395] 見送りで終端する。`DW-S06-B` への1文追記 (「独立な複数作業は1件の停止で他を止めない」) は
  手順書へ足さない。docs予算 (L1.5) が満杯であることに加え、機械検査への付け替えも成立しないため
  (2026-08-20裁定)。
  remaining: none
  base: eb233e89533e87c53fcb35dcce73a67b9513f0f2eb432bb2b2c1dc75be155323

### 更新

- [T-1404] **P2・実装待ち (2026-08-20裁定)**: 当初案 (`DW-O05` へ1文追記) を撤回し、道具側の実装へ
  切替える。「症状 (usage limit/401等 exit code・events末尾の message本文) を即座に検出し
  ユーザーへ通知する」仕組みを実装し、「少し待って自動で1回だけ再試行する」という transient前提の
  自動リカバリは作らない (根拠は本 fragment 本文および F411 supersede 追記)。再試行や
  アカウント切り替えの要否はユーザーが判断する。次の dev-wave 起票時にこの裁定を brief へ渡すこと。
  base: 525bd845690ca7069657dbda6e10dda72e4668809ada04311fd0db88c9c007c1

- [T-1425] **P3・登録する (2026-08-20裁定)**: 新設テスト `test_real_repo_clean` (実測8.3秒、
  `orchestrator/`・`tools/` 全 `.py` を AST 走査) を `orchestrator/tests/growth_test_holds.py` の
  growth-hold registry へ登録する。既存の `_HOLD_ROWS` は単一の過去裁定定数
  (`RULING_2026_08_12_BUNDLE_3`) にしか紐付かない設計であるため、実装 wave は本裁定
  (2026-08-20 rulings) を新しい裁定定数として registry 機構へ足してから対象を登録すること。
  base: 47e9665d6936dd268403dbdf51941e4cd1047807714ee28f96c60d7e73484425

- [T-1393] **P1・着手承認 (2026-08-20再確認)**: 実装方針は確定済みのまま変更なし。本セッションで
  ユーザーが改めて着手を承認した。`/dev-wave T-1393` の起動はユーザー自身の手番のまま変わらない
  (`disable-model-invocation` により AI からは起動できない)。
  base: 822f17ef51f96d8256d67d3554323f1f7557f878ae87211de4412d5ebd4015d3

- [T-1414] **P1・着手承認 (2026-08-20再確認)**: 実装方針は確定済みのまま変更なし。本セッションで
  ユーザーが改めて着手を承認した。`/dev-wave T-1414` の起動はユーザー自身の手番のまま変わらない
  (`disable-model-invocation` により AI からは起動できない)。
  base: 2426f921bfc4c2546b1d05d255d663d8ec6ee3d9e014e50b14f5c7ac99ea8a57

### 新規

- {{T:worktree-submodule-init-tool}} **P2・新規 (2026-08-20裁定)**: worktree再作成時の
  `git submodule update --init` が本環境では file transport 既定禁止により必ず失敗する。
  手順書 (`DW-O20`/`DW-O08`) の文言修正ではなく、worktree作成をtool側 (専用スクリプト) へ寄せて
  手作業手順自体を無くす方針を採る (2026-08-20裁定)。既存4tool (`tools/dev_wave_land.py` 等) が
  既に正しい flag を使っており、同じ知識の重複を避ける。一次資料は rulings-inbox
  `2026-08-13-worktree-submodule-init-flag.md`。

- {{T:t688-codex-durable-checkpoint-resume}} **P2・新規 (2026-08-20裁定)**: job wrapper の
  durable checkpoint / partial-log 実装 (2026-08-18 に段3敵対相談がCodex利用枠の一時的な
  枯渇で停止していた wave) を再開する。段2成果物は流用可能。Codex即死時の扱い自体の設計方針は
  {{D:codex-transient-death-escalate-not-wait}} に従う。一次資料は rulings-inbox
  `2026-08-18-t688-codex-quota-exhausted.md`。

- {{T:dw-s07-fragment-before-acceptance-note}} **P3・新規 (2026-08-20裁定)**: `DW-S07` (段7記録) へ
  「fragment は最終受入より前に commit する (受入後の追記は land を rc=23 で拒否する。詳細は
  `docs/pegasus-runbook.md` §7.3)」の1文を追記したいが、docs予算 (L1.5) が満杯で入らない。
  他の docs 予算超過候補とまとめて独立審査へ回す (2026-08-20裁定)。あわせて、段8で見つけた
  `docs/dev-wave/` 側の修正候補が「受入直後の tested_tip 固定」により同じ wave では land できない
  構造問題について、「次waveの段1冒頭で拾う」運用ルールを明記することも独立審査の対象に含める。
  一次資料は rulings-inbox `2026-08-19-t828-dw-s07-acceptance-ordering-note.md`。

- {{T:floor-measurement-coarse-provenance-run}} **P2・新規 (2026-08-20裁定)**:
  {{D:floor-value-coarse-provenance-standard}} に従い、床値 (floor value) の実測を実行する。
  事前登録・凍結儀式を経ずに、実行環境・ビルドコマンド・プロトコル・最適化・ワークロードの
  各パラメータを記録した上で計測する。[T-419] の生成移行chainの完了を前提条件にしない
  (旧前提はT-987が要求していたが、T-987は現行 active 集合から既に外れている)。実行は
  `docs/README.md` が指す環境runbook (単独性確認・共有計算機での実行作法) に従うこと。
