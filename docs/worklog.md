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

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-25 (1) — [T-067] oracle refusal exact 化残余を消化 (test-only、branch worktree-dev-wave-e2e-real-seal、計測なし)

/dev-wave 1 回。D73(10) の refusal 集合未 pin 残余を test-only で消化。code commit = e9014d0
(+64/-28、production・凍結成果物 bytes・guard・calibration・受理集合 無変更)。正本 =
`output/insights/2026-07-25_t067-exact-residual.md` + 同 `-mutation-ledger.json` + 同 `-verbatim.md`。
D 番号なし ([T-067] 正本は D73、設計判断は insight)。

- **中核 (項3 wrong-layer masking 除去)**: contract_sha256 mismatch テストは env-contract 不一致を謳うが
  旧 fixture は manifest-preimage で先に落ち env-guard 未到達 = 退行しても永久緑の masking。preimage 再封で
  env-guard 到達させ reason を exact 化 (Level 2)。env-guard 期待値は env_tag キーの別レジストリ由来で
  manifest 独立ゆえ恒真でない (親独立確認)。
- **他**: store×2 (bespoke parser 廃・一意 victim 動的構成 exact)、extime (全文 exact)、run_block/CLI の
  no-active (`_NO_ACTIVE_REFUSAL` 定数、CLI は stdout JSON transport pin)。PID・subprocess race loser は
  reason 非決定ゆえ意図的 partial 維持。
- **検証** (レンズ各 2 本): codex プラン (xhigh) → 敵対相談 2 → 親裁定 → 実装 (high) → 敵対レビュー 2
  (must-fix 0) → 変異 matrix。相談/レビューが親の当初 lean を 3 点訂正: store は prefix でなく exact が
  負債返済 (refuted churn)、項3 は「実装しない」でなく Level 2 (refuted)、extime は over-determination でない
  (P3 refuted)。私の victim/cell 懸念も refuted (portable record が cell field を必須 key に持つ)。
- **変異 matrix (新 HEAD e9014d0 vs 旧 HEAD~1 0c03609)**: 全 6 EXCLUSIVE。**M4 (env-guard 無効化) = 唯一の
  実 kill** (status refused→completed 反転、旧テストは masking で緑)。M1/M2/M3/M4'/M8 = 排他 diagnostic pin。
  項6 no-active は sibling 既検出 = 非排他 (node 契約完備)。台帳が正本。
- **受入**: 全走 **2919 passed / 18 skipped / 0 failed** (234s、回帰ゼロ)。check_docs / check_ai_provenance /
  repo scan invariant (F34) は本 docs commit 後に再走 <反映>。

### 消化した ID
- [T-067] **消化** (exact 化残余 D73(10))。残る partial (PID・subprocess race loser) は reason 非決定ゆえ
  意図的で、返済すべき負債でない。

### 次の一手
1. [T-011] 科学レーン floor 実測。変わらず (発火前の残 gate = R receipt + [T-088] 設計 + ops + lineage)
2. [T-068] R receipt 発行後に superseded 確定 (D78 (9))。承認済 (発行待ち)
3. [T-077] R receipt 発行後に design_source 再 pin + generator M 化。承認済 (発行待ち)
4. [T-078] R receipt 発行後に S2-4.6 承認 fixture で閉じる。承認済 (発行待ち)
5. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
6. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
7. [T-088] official guard (`_assert_official_permitted`) 解除の設計確定 (floor gate 2a)。実装前に防壁変更として再確認。変わらず
8. [T-089] **新規**: 二重 reason-tag 描画 (`[floor-artifact-invalid]`/`[no-active]` の冗長二重、`RatifiedFreezeError.__init__` + driver 両付け) = production 診断欠陥候補。診断文字列のみ冗長で受理値不変。修正は別 production task、修正時に exact 期待値を同時更新。延期。
9. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
10. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
11. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
12. [T-012] 延期: pilot 凍結維持。変わらず
13. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-25 (2) — [T-088] official 解禁の設計確定 — 両レンズ NO-GO・親裁定 4 件否定 (設計のみ・コード 0 byte、branch worktree-dev-wave-e2e-real-seal、計測なし)

/dev-wave 1 回。段 4 で「**実装しない**」と裁定し `4→7→8→9`。**実装差分がないため変異 matrix と
受入全走は射程外**。正本 = `output/insights/2026-07-25_t088-official-unlock-design.md` (裁定パッケージ)
+ 同 `-verbatim.md` (逐語 3 本)。D 番号なし (未裁定を decisions へ書かない — 承認後に起票する)。

- **最重要 (B-01、次の一手の前提訂正)**: 前エントリまでの「R receipt **発行待ち**」は **stale**。
  receipt はユーザーが 2026-07-24 に発行済み — `8bec195` (`AI-Agent: none`、receipt 1 ファイル +1 行)
  で、/rulings 記録 commit `0c03609` の**祖先**。protocol 実凍結 `c8cbd17` は receipt が active-valid
  でなければ機械拒否される (`s8b_floor_campaign.py:537-553`) ため、凍結成立が発効の機械証明。
  → [T-068]/[T-077]/[T-078] は blocker 解消済み・承認済みとして繰り上げる (要ユーザー確認 = U-5)。
  見落とし経路 = 「承認待ち」を列挙する際に**既実行かを一次資料 (git) で照合しなかった**こと。
- **検証** (レンズ各 1 本、計 2 本): codex プラン (max) → 敵対相談 2 (max) → 親裁定。
  **両レンズとも NO-GO** (A: BLOCKER 7 + MUST 5 / B: BLOCKER 5 + MUST 4 + SHOULD 2)。
  real 21・partial 1 (A-06 の「B-005 未裁定」部分は 2026-07-24 (6) の受諾で **refuted**)。
- **親の provisional 裁定 8 件のうち 4 件が否定された** — (P2) guard は誤記でなく意図的 dormant 防壁
  かつ floor protocol の承認束縛裁定は「v2 世代承認」であって launch 認可ではない / (P5) 二重評価は
  TOCTOU 増、単一 admission predicate にすべき / (P6) 提案 receipt は campaign 認可でなく revision
  activation / (P8) `AI-Agent: none` は人間証明でなく第二防壁に数えられない。(P1)(P4)(P7) は両レンズ支持。
- **親が独立裏取りした real 3 件**: `script_sha256` は `IZANAGI_RESERVATION_SCRIPT_SHA256` からの
  自己申告で wrapper hash 照合は恒真化可能 (`reservation.py:118-126`) / `cert C が G の厳密祖先でない`
  拒否が実在し activation 手順に C が欠落 (`s8b_ratified_freeze.py:3047-3053`、ただし失効が効くのは
  C 作成後の retry のみ) / `_run_campaign_core` の production caller は guard 付き wrapper 唯一。
- **裁定した設計 v2 = 最小案**: wrapper-only wave を先行 → job-scoped submission artifact →
  **単一** admission predicate へ置換 → CLI は固定拒否削除 + rc=2 翻訳のみ。certificate v1・ratified・
  resume は不変。plan が提案した新 module 2 本・certificate v2・ratified 追加・完全 negative matrix は
  **DW-G04 / DW-G02 / 規律 5 / [T-083] freeze により延期**。
- **前提実測の限界 (正直な記録)**: DW-S01 の「実際にファイルを編集して測る」は、guard の raise 実削除
  までは成功 (`git diff --stat` 1 file 1+/5-) したが、**guard 無効状態でのテスト実行を harness の
  permission classifier が拒否**した。clean tree では同コマンドが通る (復元後 `-k official` 29 passed)。
  DW-O19 手順で即復元・内容一致確認済。よって解除後の実挙動は未実測で、根拠は静的読解と模擬のみ。
- **検査**: repo scan invariant (三軸語 conjunction) **1 passed**・`check_docs.py` 違反なし・
  ベースライン `test_s8b_floor_campaign.py` 197 passed / 2 skipped。記録 commit `3799a65` の**後**に
  再走して repo scan invariant + real-repo serialization 4 passed・check_ai_provenance 332 件違反なし (F34)。
- **段 8 自己改善 (候補 3・採用 2)**: (1) 完了済み人間手番の「発行待ち」繰り越し → **F35 新設** +
  `DW-S01` へ照合義務を統合。(2) 実編集での前提実測を環境が拒否した場合の記録義務を `DW-S01` へ統合。
  (3) 一般 Agent 起動時の model 明示義務は `hooks/README.md` が正本で重複複製になるため**不採用**。
  「発行待ち表記と receipt 実在の機械照合」は未実装のまま裁定パッケージ候補として残す (F35 恒久対応 2)。

### 消化した ID
- [T-088] **消化** (設計確定 = 裁定パッケージ発行。実装は U-1〜U-4 の裁定後に別 wave)。

### 次の一手
1. [T-088] **ユーザー裁定待ち (U-1〜U-5)**。U-1 = guard を correctness gate でなく期限付き activation
   lock と再分類してよいか (解禁は official 受理集合を空集合から非空へ厳密拡大する)。**U-1 未承認なら
   以降すべて停止**。U-2 順序 / U-3 人間認可の形 / U-4 延期の確認 / U-5 次の一手の繰り上げ
2. [T-068] **繰り上げ**: R receipt 発行済みにより blocker 解消。承認済みで着手可能 (D78 (9))
3. [T-077] **繰り上げ**: 同上。design_source 再 pin + generator M 化
4. [T-078] **繰り上げ**: 同上。S2-4.6 承認 fixture で閉じる
5. [T-011] 科学レーン floor 実測。残 gate = [T-088] 裁定 → PBS floor wrapper (未実装) → 実行 revision
   束縛 → lineage (oracle 結線 wave)。R receipt と §5-(viii) 受諾は充足済み
6. [T-090] **新規**: `VerifiedFreeze.document` が mutable `dict` のまま返る (`s8b_freeze_io.py:30-38`)。
   `RatifiedFreeze` の再帰的不変化 (`s8b_ratified_freeze.py:717-733`) と非対称で、result が正しい v1
   SHA を掲げつつ異なる cell schedule の値を保持し得る。1 cycle 後の hardening 候補。延期
7. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
8. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
9. [T-089] 二重 reason-tag 描画は production 診断欠陥候補。延期。変わらず
10. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
11. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
12. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
13. [T-012] 延期: pilot 凍結維持。変わらず
14. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-25 (3) — [T-068][T-077][T-078] を R 発効により確定的に closure (docs-only・コード 0 byte、branch worktree-dev-wave-e2e-real-seal、計測なし)

/dev-wave 1 回。段 4 で「**実装しない**」と裁定し `4→7→8→9`。**実装差分がないため変異 matrix と
受入全走は射程外**。正本 = D78 (10) + `output/insights/2026-07-25_t068-t077-t078-closure.md`
(closure evidence) + 同 `-verbatim.md` (逐語 3 本)。新 D 番号なし (D78 (9) の発火実績なので追記)。

- **[T-088] は着手せず**: U-1 (official guard を activation lock と再分類してよいか = 防壁の性格変更) が
  ユーザー裁定待ちのため停止条件に従った。代わりに承認済みで blocker 解消済みの 3 件を処理した。
  U-5 (次の一手の繰り上げ) は承認済み裁定に対する既知事実なので、親判断で確定して本エントリで消化する
  ([T-088] とは別原子として分離 — レンズ B の指摘)。
- **検証** (レンズ各 1 本、計 2 本): codex プラン (max) → 敵対相談 2 (max) → 親裁定。**両レンズとも
  NO-GO** (A: BLOCKER 3・MUST 5・SHOULD 1 / B: BLOCKER 2・MUST 4・SHOULD 2・NIT 1)。
  **親の provisional 裁定 8 件のうち 3 件が否定** — (P2) 「状態中立契約への conformance」は説明が誤りで
  実際は事実訂正 / (P6) [T-068] の理由付けが不正確 (元は `frozen_at_head` **ancestry** の格下げであり、
  消えた 2 拒否は source/design **drift**。直接根拠は D78 (9) の明示 supersede) / (P7) failures 本文の
  直接修正は追記専用契約の違反。(P8) は部分 refuted。
- **両レンズ収束の決定打 2 件**: (a) **decisions は追記型記録なので D78 既存本文の in-place 置換は
  禁止** (`tools/check_docs.py` が「書いた時点で凍結」と分類) → プランの置換案 4 件を全部不採用にし
  additive な (10) だけにした。(b) **receipt 発行日は 2026-07-23** (`8bec195` = 21:49:33 +0900、
  `confirmed_at=2026-07-23T12:49:16Z`) であり 3 箇所の `2026-07-24` は誤記。**プラン起草 codex 自身が
  置換案へ誤日付を再転写しており、同一 wave 内で誤りの自走が実証された**。`c8cbd17` (protocol 実凍結)
  の 07-24 は正しいので一括置換はしていない。
- **erratum 2 件を台帳へ**: F1 (日付誤記) に「再発: 2026-07-25」、F35 に本文不変の erratum を追記
  (F35 は「一次資料に照合せよ」の教訓なのに本文自身が一次資料未確認だった)。
- **F36 新設**: 受入・検査の結果欄の `<反映>` プレースホルダが独立 3 wave + insight 1 本で残存し、
  F34 恒久対応の実行が空証明になっていた。**retroactive に埋めない** (捏造になる)。ただし全走値
  2919/18 自体は T-086/T-067 の insight に現存し、欠けているのは記録 commit **後**の検査結果だけ。
- **実測** (すべて public API): `verify` rc=0 / `active-valid` / refusals 空 / observation 17 item、
  `gate-check` rc=2 / `allowed=false` / 拒否 {floor-null, budget-null} の 2 件 exact /
  GateDecision observation = `null` (refusal 残存中は envelope を載せない設計の帰結。receipt
  resolution 側の 17 item と混同しない)。baseline 全走 2919 passed / 18 skipped / 0 failed (239s)。
- **検査**: 記録 commit **前** = repo scan invariant (三軸語 conjunction) 1 passed・`check_docs`
  違反なし・`check_ai_provenance` 333 件違反なし。記録 commit **後の再走** (F34) = repo scan
  invariant + real-repo serialization **4 passed**・`check_docs` 違反なし・`check_ai_provenance`
  **334 件違反なし**。初回 commit は trailer の `role=planner` が許可値外で provenance が赤になり、
  慣行どおり `role=author; scope=closure-plan` 等へ直して amend した (迂回せず修正)。
- **自己捕捉 (F36 の初回適用)**: 本エントリの検査欄を最初「実測値は下記」とだけ書いて値を伴わない
  前方参照にしており、**新設した F36 と同型の空証明を自分で作りかけた**。記録 commit 後の再走で
  気づき、上の実測値で埋めた。テンプレートを先に書く運用の危険がそのまま再現した。
- **段 8 自己改善 (候補 6・採用 3)**: (1) プレースホルダ・値なし前方参照を残して記録 commit しない →
  `DW-S07` へ統合 (F36 の恒久対応 1 = 台帳のポインタ実体)。(2) 記録する属性 (日付・hash・件数) も
  周辺記述から転写せず一次資料の field から取る → `DW-S01` へ統合 (F1 の再発を受けて)。(3) 親 brief と
  前段の子成果物は wave 専用 subdirectory のファイルに置き prompt へ全文複製せず絶対パスで読ませる +
  読めなければ停止させる → `DW-O02` へ統合 (context 無しの子出力をレビューと数えない)。
  **不採用 3**: trailer の role 対応表は `docs/ai-provenance.md` が正本で重複複製になる /
  `DW-O20` と handoff 契約の緊張は同節が既に解決済み / 親の provisional 裁定の否定率は設計どおりの挙動。
  command 入口 (`.claude/commands/dev-wave.md`) は 0 byte 変更。

### 消化した ID
- [T-068] **消化** — R commit をもって「移行契約により superseded」(D78 (9)(10))。
- [T-077] **消化** — R の design_source 再 pin + generator M 化。holdout generator は recorded ≠ observed
  でも通る = M 化が非恒真に効いている。
- [T-078] **消化** — S2-4.6 承認値の外部固定 fixture + predicate 単独 mutant 1→0→1。
- U-5 (次の一手の繰り上げ) **消化** — 3 件の繰り上げを本エントリで確定。ID なし ([T-088] の子でなく
  独立原子として処理)。

### 次の一手
1. [T-088] **ユーザー裁定待ち (U-1〜U-4)**。U-1 = official guard を correctness gate でなく期限付き
   activation lock と再分類してよいか。**U-1 未承認なら以降すべて停止**。U-5 は消化済み。変わらず
2. [T-011] 科学レーン floor 実測。残 gate = [T-088] 裁定 → PBS floor wrapper (未実装) → 実行 revision
   束縛 → lineage。変わらず
3. [T-091] **新規**: `_verify_receipt_derivation` を public `verify_receipt()` 経由で撃つ negative test が
   無い (期待テストは内部関数直呼びと consumer へのエラー注入 mock のみ、full-gate fixture は当該関数を
   no-op stub 化)。今日の判定値は変えないため 1 cycle 後の hardening へ。延期
4. [T-092] **新規**: real-repo gate test が R の OID を pin せず、履歴除去で pre-R 4 拒否分岐を正解化する。
   通常の追加 commit 経由の削除は production が拒否するので fail-open ではない。1 cycle 後。延期
5. [T-093] **新規**: D78 (6)(f) の observed 15 件は H_mig 確定により独立 literal pin が可能になった。
   現状は期待値を receipt 自身から組み立てている。1 cycle 後。延期
6. [T-094] **新規**: リテラル placeholder の機械検出 (F36 恒久対応 2)。族条件は満たすが、既存 4 件の
   allowlist と対象ファイル族・引用/verbatim 除外の設計が先。裁定パッケージへ。延期
7. [T-090] `VerifiedFreeze.document` が mutable `dict` のまま返る hardening 候補。1 cycle 後。変わらず
8. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
9. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
10. [T-089] 二重 reason-tag 描画は production 診断欠陥候補。延期。変わらず
11. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
12. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
13. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
14. [T-012] 延期: pilot 凍結維持。変わらず
15. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-25 (4) — /rulings: 裁定待ち 5 件をユーザーが推奨どおり一括裁定 — official 解禁を承認 (D86 起票、計測なし)

/rulings 1 回。前エントリ (3) 後に索引化した裁定待ち 9 件のうち詳説 5 件を、ユーザーが
「全部推奨通りで」と一括裁定。read-only 収集 → ユーザー裁定 → 本記録 (クラス 2 昇格)。
実行系 (push) は Pegasus 規約によりユーザー手番で、AI は実行しない。**本記録に実装は含まない**。

- **[T-088] official 解禁**: U-1 を**承認** — `_assert_official_permitted` を correctness gate ではなく
  **期限つき activation lock** と再分類する。併せて U-2 = (a) wrapper-only wave 先行、U-3 = (a) 明示
  qsub + job-scoped submission artifact (新 Git receipt を作らない)、U-4 = 一括延期 を承認。
  前エントリ (2) が「D 番号なし (未裁定を decisions へ書かない — **承認後に起票する**)」と明記して
  いたため、承認を受けて **D86 を起票**した。解禁は official 受理集合を空集合から非空へ厳密拡大する
  ので、実装 wave の段 1 で防壁変更として再確認する。
- **[T-094]**: 機械検出を**採用**し設計も確定 — 検出は `<反映>` / `<受入結果を反映>` /
  `<受入全走結果を反映>` の exact 3 文字列、対象は `docs/worklog.md` と verbatim でない
  `output/insights/*.md`、既存 4 件は行 digest で例外登録。F36 恒久対応 2 の実体化。
- **[T-091]/[T-092]/[T-093]/[T-089]/[T-090]**: 延期を**追認**。床値実測後の hardening wave で一括処理。
- **push**: local main (`5932010`、未 push 7 commit) の push を**承認** → ユーザー実行
  (`git push origin main`。AI は push しない = Pegasus 規約。前例 = 2026-07-24 (6))。
- **見送り台帳**: 発火条件が成立している項は今回**確認できず** (35 項すべて未発火の保留承認)。
- **検査**: 記録 commit 後の再走 = repo scan invariant + real-repo serialization 4 passed・
  `check_docs` 違反なし・`check_ai_provenance` 337 件違反なし。

### 次の一手
1. [T-088] **承認済み・着手可能**: official 解禁の実装。順序 = wrapper-only wave 先行 → 実 artifact
   確認 → 単一 admission predicate へ置換 → CLI は固定拒否削除 + rc=2 翻訳。設計正本 = D86 +
   `output/insights/2026-07-25_t088-official-unlock-design.md` §4。実装 wave の段 1 で防壁変更として再確認
2. [T-011] 科学レーン floor 実測。残 gate = [T-088] 実装 → PBS floor wrapper (未実装) → 実行 revision
   束縛 → lineage (oracle 結線 wave)。変わらず
3. [T-094] **承認済み・着手可能**: placeholder 機械検出を上記確定設計で実装 (F36 恒久対応 2)
4. [T-091] 延期追認: `_verify_receipt_derivation` を public 経路で撃つ negative test。hardening wave へ
5. [T-092] 延期追認: real-repo test の R OID pin。hardening wave へ
6. [T-093] 延期追認: observed 15 件の独立 literal pin。hardening wave へ
7. [T-089] 延期追認: 二重 reason-tag 描画 (production 診断欠陥候補)。hardening wave へ
8. [T-090] 延期追認: `VerifiedFreeze.document` が mutable dict のまま返る。hardening wave へ
9. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
10. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
11. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
12. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
13. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
14. [T-012] 延期: pilot 凍結維持。変わらず
15. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-25 (5) — [T-088] 段階 1: floor 専用 PBS wrapper を実装 (D87、branch worktree-dev-wave-t088-floor-wrapper、計測なし)

dev-wave 1 本。D86(2) が定めた順序の第 1 段 (wrapper-only wave) を実装した。
`orchestrator/campaign/s8b_floor_campaign.py` は 1 byte も変更していないため、**official の受理集合は
空集合のまま**である (D86(1) の「実装 wave の段 1 で防壁変更として再確認」は、本 wave が admission を
変えないことの確認として履行)。**本 wave は段階 1 の完了を主張しない** — dry-run の synthetic ID は
DW-G04 の発火条件ではなく、実 submit artifact の確認は人間の明示 `qsub` を待つ。

- **成果物**: `tools/pegasus/submit_floor.sh` (新規)、`tools/pegasus/floor_campaign.sh` (新規)、
  `tools/pegasus/policy.json` (`floor_walltime` / `floor_walltime_s` を追加)、
  `orchestrator/tests/test_pegasus_floor_tools.py` (新規 49 テスト)。commit = `b2b6e5c` + `82c9055`。
- **親が独立に実測した設計入力 3 件** (両敵対レンズとも未検出): (i) driver の envelope は実 protocol +
  実 freeze から `required 28200 + finalize 600 = 28800` 秒 = 8.0 時間ちょうど、(ii) floor driver の
  build 経路は `-DCMAKE_PREFIX_PATH` を渡さないが CCBench は gflags/glog を `REQUIRED` で要求し
  計算ノードに存在しない、(iii) CMake は環境変数 `CMAKE_PREFIX_PATH` を尊重する (最小 project で実証)。
  (ii)(iii) が無ければ解禁後の初回実走が build 失敗で 10 時間の allocation を捨てていた。
- **親の provisional 裁定 8 件のうち 4 件が否定された** (D87): dry-run 完了の主張 / walltime 29400 /
  実装子の並列化 / `REQUESTED_S` の policy 由来。**相談・レビュー・再レビューの 5 本すべてが NO-GO**。
- **実装した束縛**: 実行中 bytes (`sha256sum "$0"`) と commit blob の二重照合 / scheduler の実
  `Elapse Time Limit` との一致検査 / receipt `job_id` と `PBS_JOBID` の一致 (replay 遮断) /
  interpreter の isolated mode (`-I -B`) / path component の symlink 検査 + 凍結・campaign namespace の
  除外 / driver rc と起動前失敗の分離 / git 失敗を clean と扱わない。
- **正直な限界**: submission record は authorization ではない (人間と AI の生成物が区別不能) /
  driver の予算定数は hard cap でない / PATH 由来ツールの実体は未検証 / 実 PBS 上では未実行。
- **記録**: 材料レポート `output/insights/2026-07-25_t088-floor-wrapper.md`、逐語 `-verbatim.md`、
  変異台帳 `-mutation-ledger.json` (初回・再照準ラウンドを erratum として同梱)。
- **検査**: 受入全走 = 2968 passed / 18 skipped (赤 0)。焦点 3 ファイル = 104 passed。
  変異本走 = 12/12 KILLED。`check_ai_provenance` = 340 件・違反なし。
  三軸語 conjunction の機械検査 = 子出力 11 本すべて 0 hit。
  fix round 1 直後の全走で `test_dev_waves_worker.py::test_stdout_stderr_have_one_combined_cap` が
  1 件赤になったが、単独 4/4 緑・同 commit の再走で再現せず、並列負荷下の timing flaky と判定した。
- **記録後検査 (F34)**: 本記録 commit の後に再走 = repo scan invariant + real-repo serialization +
  凍結成果物 + 焦点 3 ファイル = 110 passed。`check_ai_provenance` = 341 件・違反なし。
  `check_docs` = 違反なし。
- **段 8 の docs commit 後の再走 (F34)**: 受入全走 = 2968 passed / 18 skipped (赤 0)、
  `check_ai_provenance` = 344 件・違反なし、`check_docs` = 違反なし。
- **段 8 で自己捕捉した失敗 (F37 新設)**: 自己改善 commit の前に `check_docs` を `| tail` へ通したため
  pipeline の rc が `tail` のものになり、`docs/dev-wave/**` の byte 予算違反 (24379 > 24000) を
  報告していたのに `&&` の右辺が実行されて commit が入った (`419fa70`)。予算値は上げず、入口と
  重複する reference 記述の削除で 23960 bytes へ収めた。恒久対応は DW-O17 へ統合した。

### 次の一手
1. [T-088] **段階 1 の閉鎖は人間手番**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて `tools/pegasus/submit_floor.sh` を明示実行して実 job ID を得る。期待は driver rc=2
   (official guard 生存) で、`job-result.json` の `driver_rc=2` が記録されれば wrapper 配線の実機確認が
   完了し、DW-G04 の発火条件が満たされる。手順は `tools/pegasus/README.md` §5 と材料レポート §6。
   実 artifact 確認後に段階 3・4 (単一 admission predicate + CLI rc 翻訳) へ着手できる
2. [T-095] **裁定待ち (新規)**: D86(3) の「人間の明示 qsub を authorization とする」文言と、
   submission record が人間性を証明しない (人間と AI の生成物が byte-level で区別不能) という実体の差。
   文言の再確認または修正。正本 = `output/insights/2026-07-25_t088-floor-wrapper.md` §5-1 / §7-1
3. [T-096] **裁定待ち (新規)**: driver 予算定数の hard cap 化。`buildcache` は configure と build に
   各々 900 秒を適用し、測定は rep ごと 120 秒 × 5 rep のため、envelope の 900/セル・145/attempt は
   見積であって上限でない。独立 prerequisite wave で driver 側を直すか walltime を厚く取り続けるかの択一
4. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage
5. [T-094] 承認済み・着手可能: placeholder 機械検出 (F36 恒久対応 2)
6. [T-091] 延期追認: `_verify_receipt_derivation` を public 経路で撃つ negative test。hardening wave へ
7. [T-092] 延期追認: real-repo test の R OID pin。hardening wave へ
8. [T-093] 延期追認: observed 15 件の独立 literal pin。hardening wave へ
9. [T-089] 延期追認: 二重 reason-tag 描画 (production 診断欠陥候補)。hardening wave へ
10. [T-090] 延期追認: `VerifiedFreeze.document` が mutable dict のまま返る。hardening wave へ
11. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
12. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
13. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
14. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
15. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
16. [T-012] 延期: pilot 凍結維持。変わらず
17. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず
