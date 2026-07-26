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

## 2026-07-25 (6) — [T-094] リテラル placeholder の機械検出を新設 (D88、branch worktree-dev-wave-t094-placeholder-gate、計測なし)

dev-wave 1 本。worklog 2026-07-25 (4) で承認済みだった F36 恒久対応 2 を実体化した。検出対象の
バイト列は本エントリへ再掲せず、`tools/check_docs.py` の `LITERAL_PLACEHOLDERS` を正本として
宣言順に LP-1 / LP-2 / LP-3 と呼ぶ (この gate の自己発火を避ける実務。D88(6))。

- [T-094] **消化 (D88)。** 承認済みだった機械検出を実装し、対象族・台帳の閉性・除外なし方針を確定した。
  F36 の恒久対応 2 は「この exact-literal gate だけ」を実体とし、F36 全体は閉じていない。
- **成果物**: `tools/check_docs.py` (+621 行、`_check_literal_placeholder_guard` と 2 台帳)、
  `orchestrator/tests/test_check_docs.py` (+1372 行、74 test 関数・189 assert)。commit = `8ba4aed`。
  対象族 = `docs/worklog.md` + `docs/archive/worklog-*.md` + `output/insights/*.md` の **raw text**。
- **裁定前提の齟齬 2 件を親が段 1 で実測**: (i) 真の placeholder 4 行のうち **2 行が archive
  worklog** にあり、裁定文の対象族に収まらなかった (archive を追加 = D88(1))。(ii) 対象族内に
  説明的言及が 3 行あり、「既存 4 件の allowlist」だけでは偽陽性が残る (台帳を債務 4 / 言及 5 の
  2 本に分離 = D88(5))。
- **敵対レビュー 6 本すべて NO-GO**。親の provisional 裁定 6 件のうち 4 件 (装飾による除外 2 件、
  path 非依存台帳、D 起票不要) が否定され、親が代わりに採った path 束縛も **regressed** と判定
  された。最終形は H2 エントリ scope 束縛で、正規のローテーションでは台帳を変更しなくてよい。
- **併せて直した既存欠陥 2 件** (D88(7)): 読取失敗が後続 checker の無防備な読取で traceback になり
  集約報告と違反件数が失われていた欠陥、および symlink / 非 regular を追跡して外部 bytes を読む経路。
- **正直な限界** (D88(6)): 既知 9 行は台帳で固定しただけで**解消していない**。意味的に同じ別表記、
  HTML entity、**F36 の再発型である予測値の先書き**、対象 3 族の外 (phase / decisions / failures /
  handoff / `*-mutation-ledger.json` / campaign JSON) は保証しない。
- **記録**: 材料レポート `output/insights/2026-07-25_t094-placeholder-gate.md`、逐語 `-verbatim.md`
  (13 本・27 箇所を全角山括弧へ可逆 defang、原文 SHA-256 併記、置換後 0 hit を機械検査)、
  変異台帳 `-mutation-ledger.json` (erratum 3 件同梱)。
- **検査**: 受入全走 = 2994 passed / 18 skipped (赤 0)。焦点 `test_check_docs.py` = 113 passed。
  `check_docs` 単独 rc=0。波及先 consumer = 177 passed。変異本走 = 13/13 KILLED
  (expected node hit 12/13、単独理由 10 件中 9 件 HIT)。`check_ai_provenance` = 346 件・違反なし。
  三軸語 conjunction (repo scan invariant) = 1 passed。
- **親が独立に実測して子の報告と照合**: 対象族 115 ファイルの hit = 9 logical lines で digest 9/9 一致、
  worklog 族の H2 = 234 件すべて一意、repo 内 symlink 0 件、対象族に CR byte 0 件。
- **記録後検査 (F34)**: 本記録 commit (`fecdd4a`) の後に再走 = repo scan invariant + real-repo
  serialization + 凍結成果物 + 焦点 = **119 passed**。`check_docs` rc=0。
  `check_ai_provenance` = **347 件・違反なし**。
- **段 8 の docs commit 後の再走 (F34)**: 受入全走 = 2994 passed / 18 skipped (赤 0)、
  `check_docs` rc=0、`check_ai_provenance` = 349 件・違反なし。
- **段 8 自己改善 (候補 3・採用 1)**: `DW-S07` の凍結前機械検査を「三軸語 conjunction」だけと
  読める文言から全 gate の検出語へ一般化し、可逆 defang と原文 hash 併記を明示した
  (commit `7d0d51f`、予算は上げず 23986/24000 に縮約)。残り 2 件は予算に収まらず [T-101] へ。
- **変異 harness の自己捕捉 2 件**: (i) pytest の `path::test_name` 形式に対し関数名の完全一致で
  照合したため 13/13 KILLED でも expected node hit が 0/13 と記録された (初回結果は erratum として
  同梱)。(ii) M4 の期待 node 登録が誤っていた (総数 pin 定数を変える変異に、台帳本体の exact map を
  照合する node を登録していた)。

### 次の一手
1. [T-088] **段階 1 の閉鎖は人間手番** (変わらず): `tools/pegasus/submit_floor.sh --dry-run` で receipt を
   確認し、続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。
   手順は `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6
2. [T-097] **裁定待ち (新規)**: placeholder 検出の対象族拡張 — `docs/phase3.md` / `decisions.md` /
   `failures.md` / `*-mutation-ledger.json` / handoff。変異台帳 JSON は実際に受入結果を記録しており
   同型欠陥が残る。claim-bearing artifact 族の定義が必要。正本 =
   `output/insights/2026-07-25_t094-placeholder-gate.md` §7
3. [T-098] **裁定待ち (新規)**: campaign selector の `rationale` が sentinel を非空文字列として受理し
   freeze へ seal する (`orchestrator/campaign/s8b_selector_output.py`)。producer validator で拒否するか
4. [T-099] **裁定待ち (新規)**: 凍結成果物に将来 placeholder が入った場合の専用 waiver 契約。
   bytes 修正は freeze 違反・実測値を埋めるのは捏造・一般台帳へ足すのは gate 弱体化の三択になる
5. [T-100] **裁定待ち (新規)**: 検出語彙の拡張 (別表記・HTML entity) と、予測値先書きの構造的検出
   (結果欄に実走 artifact 参照を必須化する別 checker)。F36 の再発クラスは本 gate では閉じない
6. [T-101] **裁定待ち (新規、dev-wave 自己改善)**: 予算に収まらず reference へ統合できなかった作法 2 件 —
   (a) 背景 job の cwd が既に worktree のとき `EnterWorktree` が新規作成を拒否する場合の扱い
   (本 wave は前 wave の worktree で branch だけ切り、ディレクトリ名と branch 名が食い違った)、
   (b) 焦点再レビューが NO-GO を返し続ける場合の収束条件 (本 wave は fix 3 巡の後、親が変異で
   裏取りして閉じた)。`docs/dev-wave/**` は 23986/24000 で追記余地がなく、予算値は上げない
7. [T-095] 裁定待ち: D86(3) の「人間の明示 qsub を authorization とする」文言と、submission record が
   人間性を証明しない実体の差。変わらず
8. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
9. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage
10. [T-091] 延期追認: `_verify_receipt_derivation` を public 経路で撃つ negative test。hardening wave へ
11. [T-092] 延期追認: real-repo test の R OID pin。hardening wave へ
12. [T-093] 延期追認: observed 15 件の独立 literal pin。hardening wave へ
13. [T-089] 延期追認: 二重 reason-tag 描画 (production 診断欠陥候補)。hardening wave へ
14. [T-090] 延期追認: `VerifiedFreeze.document` が mutable dict のまま返る。hardening wave へ
15. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
16. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
17. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
18. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
19. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
20. [T-012] 延期: pilot 凍結維持。変わらず
21. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-25 (7) — /rulings: 裁定待ち 12 件を索引化し 7 件をユーザーが一括裁定 — hardening のテスト前倒しを承認 (docs-only・コード 0 byte、branch worktree-dev-wave-t094-placeholder-gate、計測なし)

/rulings 1 回。直前の `/dev-wave` が「候補 21 件すべてが人間手番・裁定待ち・実測後送り・cycle 後送り」
で着手可能 scope ゼロと判定し、段 1 に入らず fail-closed 停止した (DW-STOP)。その塞がりを解く裁定を
収集した。read-only 収集 → ユーザーが「すべて推奨通りにする」と一括裁定 → 本記録 (クラス 2 昇格)。
**本記録に実装は含まない** (コード 0 byte)。実行系 (floor 投入・push) は Pegasus 規約でユーザー手番。

- [T-095] **消化 (D86 erratum)。** 「明示 `qsub` + submission artifact を authorization とする」を
  文言修正と裁定。認可の実体は**ユーザーの明示指示**であり、artifact はその指示が実行された記録に
  とどまる (人間実行と AI 実行の生成物は byte-level で区別不能 = 材料レポート §5-1 の実測)。
  D86 に (8) erratum を追記し、「記録があるから認可済み」の fail-open な読みを閉じた。防壁は増やさない。
- [T-091] / [T-092] / [T-093] **前倒しを承認** — 2026-07-25 (4) の条件付き追認 (「床値実測後の
  hardening wave で一括処理」) を**部分改訂**した。床値実測が人間手番で止まり AI 手番が空になったため、
  親が 5 件を交絡リスクで二分した。テストのみ 3 件は本番コードを 1 byte も変えず測定への交絡がないので
  前倒し可、本番コードに触る [T-089] / [T-090] は測定直前の変更が原因切り分けを濁すため据え置き。
- [T-098] **生成側で拒否を承認。** 選択理由欄の検査は型・非空白・最大長のみで、LP 族の文字列は非空の
  ため通ることを親が実測 (`orchestrator/campaign/s8b_selector_output.py:110-116`)。seal 後は bytes 修正が
  freeze 違反になるため、producer validator が唯一の安価な阻止点。実装は次 wave。
- [T-058] / [T-059] **見送り台帳 2 項の発火を確認 (今回初)。** [T-094] の gate 新設が両項の述語
  (`safety_gate_changed` / `validator_or_rejection_gate_changed`) を成立させた。[T-058] = 発火記録のみ残し
  網羅率観測は 1 cycle 完走後、[T-059] = 前 wave の 13 変異事前登録 + 13/13 KILL で真時 action が実質
  履行済みのため追認のみ。両項の台帳行へ発火記録を追記した。2026-07-25 (4) の「35 項すべて未発火」は
  本エントリで 2 項が発火に転じた。
- [T-088] は**裁定でなく人間手番**。未実行を親が実測で確定した (F35 照合) —
  `output/env/pegasus/floor/` 不在、`output/claims` 不在、git に受領 commit なし。既実行なら stale と
  裁定して依存項目を繰り上げる規則だが、その条件は成立しなかった。
- **push**: local main (`ce2111d`、未 push 12 commit) の push を**承認** → ユーザー実行
  (AI は push しない = Pegasus 規約。前例 = 2026-07-25 (4))。
- **裁定待ちのまま残した 5 件**: [T-097] / [T-099] / [T-100] / [T-096] / [T-101]。索引には出したが詳説
  5 件に入らず AI 推奨を出していないため、「すべて推奨通り」の射程外として**閉じない** (推奨なき項目を
  一括承認で黙って閉じる経路を作らない)。
- **スキル自己改善 (rulings gate 発火・採用 2)**: 今回 2 つの収集漏れを実測した — (i) 見送り台帳の
  述語照合に方法がなく、発火済み 2 項が偶然でしか surface しない (前回「35 項すべて未発火」は今回の
  未発火を意味しない)、(ii) 条件付き追認項の前提が未成立で後続が塞がった場合を裁定待ちに立てる規則が
  なく、本セッション最大の裁定 (hardening 前倒し) はどの規則からも導かれなかった。`rulings.md` の
  収集節へ照合方法と項 6 を追加した。事故は発生していないため failures / decisions は変更しない。
- **検査 (記録 commit 前の実測)**: `check_docs` rc=0 (違反なし)、焦点 = `test_check_docs.py` +
  repo scan invariant + real-repo serialization の **117 passed**、`check_ai_provenance` =
  **350 件・違反なし**。
- **記録後検査 (F34)**: 記録 commit (`58b8793`) の後に再走 = `check_docs` rc=0、焦点 **117 passed**、
  `check_ai_provenance` = **351 件・違反なし**。
- **自己改善 commit 後の再走 (F34)**: `check_docs` rc=0、焦点 **117 passed**、
  `check_ai_provenance` = **353 件・違反なし**。自己改善の初回編集は最長行予算 180 を 207 で超えて
  赤になり、規則を 3 行へ分割して解消した (`check_docs` が機械捕捉)。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。手順は
   `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6
2. [T-091] **承認済み・着手可能 (前倒し)**: `_verify_receipt_derivation` を public `verify_receipt()`
   経由で撃つ negative test。現状の期待テストは内部関数直呼びと consumer へのエラー注入 mock のみ
3. [T-092] **承認済み・着手可能 (前倒し)**: real-repo gate test の R OID pin。現状は履歴除去で pre-R の
   4 拒否分岐が正解化する
4. [T-093] **承認済み・着手可能 (前倒し)**: D78 (6)(f) の observed 15 件の独立 literal pin。現状は
   期待値を receipt 自身から組み立てている
5. [T-098] **承認済み・着手可能**: 選択理由欄の LP 族拒否を producer validator へ追加
   (`s8b_selector_output.py`)。検出語彙は `tools/check_docs.py` の台帳と共有するか要設計
6. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
7. [T-097] 裁定待ち: placeholder 検出の対象族拡張 (claim-bearing artifact 族の定義)。変わらず
8. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
9. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
10. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
11. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
12. [T-089] **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を
    同時更新する
13. [T-090] **測定後の hardening と裁定** (前倒し対象外): `VerifiedFreeze.document` が mutable dict の
    まま返る (`s8b_freeze_io.py:30-38`)
14. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
15. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
16. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
17. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
18. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
19. [T-012] 延期: pilot 凍結維持。変わらず
20. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (1) — [T-091][T-092][T-093] receipt gate の検出力を独立 oracle へ引き上げ (テストのみ・本番 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-25 (7) でユーザーが前倒しを承認した hardening 3 件を消化した。
**本番コードは 1 byte も変えていない**ので、certified 選択・gate の受理集合・凍結成果物の bytes は
不変であり、変わったのは検出力だけである。材料レポートと逐語は
`output/insights/2026-07-26_t091-t093-hardening.md` / 同 `-verbatim.md`、変異台帳は
同ディレクトリの `2026-07-26_t091-t093-mutation-ledger.json` を正本とする。

- [T-091] **消化**。改竄 receipt を public `verify_receipt()` 経由で撃つ負例を新設。fixture は
  導出値反映後・canonical 化前に改竄 callback を 1 回だけ適用する (commit 後改竄では
  `receipt.issued_but_missing` が先に出て証拠にならない)。**stub のまま残した 4 gate を
  テスト内に明記**し、「全 gate を検証した」とは主張しない。
- [T-092] **消化**。real-repo test を post-R 固定にし R OID・R blob raw sha256・H_mig を literal pin。
  R 不在時は skip でなく明示 fail。削除した pre-R 分岐は post-R では**到達不能**であることを
  親が実測し、敵対相談 A-6「既存検査を弱める」を**部分 refuted**と裁定した。
- [T-093] **消化**。observed 15 cell を real-repo 専用の新定数へ literal pin し receipt からの zip を廃止。
  既存 3 要素 golden は不変 (同ファイルの stub-free E2E が 3 要素で比較しており、その basis は
  current source の複製のため H_mig literal を混ぜられない = 敵対相談 A-1/B-1)。
- **素材: literal 化だけでは検出力にならなかった。** 敵対相談 A-3 が「単一 real-repo vector では
  production が receipt を無視して実 repo の値を返す退化を検出できない (期待値が恒真化する)」と指摘。
  親は hermetic E2E の basis blob を fixture 内で分岐させる**第 2 vector**へ設計変更し、
  これが変異 M6 として実際に KILL した。当初案のままなら T-093 は固有帰属を持てなかった。
- **変異 matrix (親実測、統合 commit 後)**: 事前登録 M1〜M7 の **7/7 が実測と一致**。
  M1-M4=T-091 / M5=T-092 / M6=T-093 はいずれも新テストのみ KILL・旧テスト SURVIVE。
  M7 は事前登録どおり**帰属不成立** (新旧とも KILL) で新規検出力に計上しない。
  DW-M08 に従い各変異を新テストと変更前 HEAD 版テストの双方へ全走させた。
- **エージェント工数**: codex 子 9 本 (プラン 1・敵対相談 2・実装 2・レビュー 2・fix 1・焦点再 1)。
  段 3 は両レンズ NO-GO・所見 14、段 6 は A=GO / B=NO-GO・所見 4、焦点再は closed 3 / partial 1。
- **検査 (記録 commit 前の実測)**: 受入全走 **2995 passed / 18 skipped / 0 failed**
  (baseline `be40317` = 2994 passed / 18 skipped、node 消失 0)、`check_docs` rc=0、
  `check_ai_provenance` = 355 件・違反なし。
- **記録後検査 (F34)**: 記録 commit (`2e6b2ee`) の後に再走 = `check_docs` rc=0、
  焦点 (`test_check_docs` + repo scan invariant + real-repo serialization) **117 passed**、
  `check_ai_provenance` = **356 件・違反なし**。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は `DW-M01` への 1 行
  (テスト強化 wave は `DW-M08` の新旧両走も事前登録する)。今回この導線が無く、親が気づかなければ
  片走で M7 の先取り KILL を新規検出力と誤記録する経路が開いていた。予算は hard ceiling 24000 に対し
  HEAD 時点で 23986 (余裕 14 bytes) だったため、`DW-O15` が `DW-M07` 本文を複製していた無駄を
  取り (条件 dispatch は両節を同時に読ませる) 場所を作った。事故は発生していないので failures /
  decisions は変更しない。残り 2 件は予算に収まらず [T-104] として裁定へ送る (前例 = [T-101])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。手順は
   `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6。変わらず
2. [T-098] **承認済み・着手可能**: 選択理由欄の LP 族拒否を producer validator へ追加
   (`s8b_selector_output.py`)。検出語彙は `tools/check_docs.py` の台帳と共有するか要設計。変わらず
3. [T-102] **新規 (scope 外 real 所見)**: production の git runner が ambient `GIT_*` を継承する
   (`s1_known_axes_freeze.py:89`、`s8b_holdout_freeze.py:147`)。poisoned env の敵対走で 2 failed を
   実測済み。本 wave は本番 0 byte のため未修正。本番コードに触るので測定前後の扱いに裁定が要る
4. [T-103] **新規 (敵対相談 A-6 の対案、scope 外)**: never-issued 状態の real artifact 由来
   refusal vector を別 node で撃つテストの新設。pre-R 分岐削除で失った実効検出力は 0 だが、
   検出力の**追加**として価値がある
5. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
6. [T-097] 裁定待ち: placeholder 検出の対象族拡張 (claim-bearing artifact 族の定義)。変わらず
7. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
8. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
9. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
10. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
11. [T-104] **新規・裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件 —
    (i) decision 本文と要約の食い違いが別集合を指す場合に双方を brief へ書き分ける規則 (`DW-S01`)、
    (ii) 段 1 の前提実測を下流の子出力の独立検証に使える形で残す規則 (`DW-S01`)。
    `docs/dev-wave/**` は hard ceiling 24000 に対し 23966 で余裕 34 bytes しかない。
    [T-101] と併せ、予算値の引き上げ可否を独立審査するか、reference の再編で場所を作るかの裁定が要る
12. [T-089] **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を
    同時更新する。変わらず
13. [T-090] **測定後の hardening と裁定** (前倒し対象外): `VerifiedFreeze.document` が mutable dict の
    まま返る (`s8b_freeze_io.py:30-38`)。変わらず
14. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
15. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
16. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
17. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
18. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
19. [T-012] 延期: pilot 凍結維持。変わらず
20. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (2) — [T-098] selector の選択理由欄で literal placeholder を fail-closed 拒否 (本番 13 行、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-25 (7) でユーザーが承認した「生成側で拒否」を実装した。本番差分は
`s8b_selector_output.py` の 13 行だけで、受理集合は「長さ 1〜2000 の既存受理文字列のうち LP を
含むもの」だけ縮小する。凍結成果物の bytes は不変。材料レポートと逐語は
`output/insights/2026-07-26_t098-selector-lp-reject.md` / 同 `-verbatim.md`、変異台帳は
同 `-mutation-ledger.json` を正本とする。commit = `ef9ef76`。
表記は D88 (6) を継承し、検出 3 語は LP-1 / LP-2 / LP-3 の記号参照で書く。

- [T-098] **消化**。`parse_selector_output` に decode 済み `rationale` の LP 包含を拒否する
  fail-closed gate を追加した。新 code は `rationale_placeholder` の 1 個で、検査位置は
  `rationale_blank` / `rationale_too_long` の後。既存 code と既存拒否挙動は不変。
  語彙は parser 内に別名で持ち、本番から docs lint を import しない (parser bytes は selector
  journal header に pin される資産のため)。
- **裁定前提は成立**。親が実装前に実コードへ 6 パターンを投入し **6/6 受理**を実測した。
  既存 seal 済み 6 rows に LP は 0 件で、`_reparse_agent_raw` の再 parse 結果は不変。
- **親 brief の誤りを訂正 (段 3 レンズ A の A-1、real)**。brief は「floor / ratified の両検証は
  `pre_oracle_head` blob 射影なので worktree 編集に不感」と書いたが、これは parser の **hash pin** に
  だけ当てはまる。floor は `s8b_floor_campaign.py:1365-1367` で `verify_prediction_freeze` を呼び
  **現行 parser で raw を再 parse する**。既存 6 rows が無事なのは**データ依存**であって構造保証ではない。
- **素材: 正例が検出力になった。** 当初設計は負例だけだった。レビューが「承認外の**過剰拒否**も
  受理集合の改変である」と指摘し、全角山括弧・HTML entity・token 内空白・非承認の類似語・片側
  delimiter 欠落の**受理を固定する正例**を追加した。これらは変異 S2 / S7 / S8 で実際に KILL しており、
  正例なしでは検出できなかった。負例だけを数えて「検出力」と呼ぶ設計は片肺だった。
- **語彙束縛は 2 度否定された。** 親案 (ast でトップレベル `Assign` を 1 個取り docs と parser を等号
  照合) は `LITERAL_PLACEHOLDERS += (...)` を静かに取りこぼす (B-4)。改訂案 (テスト内独立 3 語との
  三者照合 + Store 個数検査) も `globals()["…"] += (…)` を捕まえられない (RB-2)。最終形は
  **ast 検査 + テストからの実行時 import による実効値照合**の併用。両経路は変異 S1 / S11 で実測 KILL。
- **変異 matrix (親実測、統合 commit 後)**: 事前登録 **23/23 が実測と一致**。帰属成立 22 件
  (新テストのみ KILL・変更前 HEAD 版テストは SURVIVE)、非帰属 control 1 件 (N1 = 最大長 3000、
  新旧とも KILL のため新規検出力に計上しない)。`DW-M08` に従い全 23 件を新旧両走した。
  harness は flock 単一走行・アンカー一意性 assert・注入 diffstat・内容比較による復元検査を持ち、
  全走後の tree は clean。
- **エージェント工数**: codex 子 9 本 (プラン 1・敵対相談 2・実装 1・レビュー 2・fix 2・焦点再 1)。
  段 3 は両レンズ NO-GO・所見 11、段 6 は A=GO 所見なし / B=NO-GO 所見 4、焦点再は closed 4 /
  partial 1 + 残存誤実装 2 で NO-GO、fix 巡 2 で全 closed。**相談・レビュー・再レビュー 4 本すべてが NO-GO**。
- **検査 (統合 commit 直前の実測)**: 受入全走 **3058 passed / 18 skipped / 0 failed**
  (基線 `c129e73` = 2995 passed / 18 skipped、node 消失 0)、`check_docs` rc=0、
  `check_ai_provenance` = 358 件・違反なし。
- **受入で 1 度だけ出た赤を差分へ帰属しなかった。** fix 巡 1 後の全走で
  `test_dev_waves_integration.py::test_artifact_aggregate_cap_stops_before_next_wave_side_effect` が
  `FileNotFoundError` で赤になった。単独再走 3/3 passed のフレークで、差分 4 ファイルに
  `tools/dev_waves/` を含まないため帰属しない。原因は [T-105] として起票した。
- **記録後検査 (F34)**: 記録 commit を作った直後に再走した = `check_docs` rc=0、
  `check_ai_provenance` = **359 件・違反なし**、焦点 (`test_check_docs` + selector output /
  selector freeze / prediction runner) **288 passed**。
  実測値を本欄へ埋めるため同 commit を `--amend` したので、記録 commit の hash は amend 後の値である
  (本欄は自己参照を持たない。手順の正本はこの記述であり、amend 前の hash は破棄されている)。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は `DW-S07` の 1 文置換
  (再走値は amend で埋め、hash 自己参照を書かない)。**今回これは near miss として実発現した** —
  F34 と F36 の恒久対応を両方守ると再走値は記録 commit 後にしか書けず、amend で埋めると
  欄に書いた記録 commit hash が amend 自身によって dangling になる。同 wave 内で是正したが、
  前 wave の欄も同型の自己参照を持つ。**F38 を新設**した (F36 とは機序が異なる — F36 は実測前の値、
  本件は実測値を埋める手順の副作用)。予算は合算 24000 に対し変更後 23987 (余裕 13 bytes)。
  残り 2 件は予算に収まらず [T-108] として裁定へ送る (前例 = [T-101] / [T-104])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。手順は
   `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6。変わらず
2. [T-106] **新規・裁定待ち (scope 外 real 所見)**: ratified proof chain が selector raw を再 parse
   しない (`s8b_ratified_freeze.py` に `verify_prediction_freeze` / `parse_selector_output` の呼び出しが
   grep 0 件)。floor は新 gate を実行するため両者で受理が分岐する。選択肢 = (a) 現状維持 + 射程の明記、
   (b) ratified にも再 parse を入れる (歴史射影の設計変更)、(c) 封印時点の parser 判定を artifact へ
   刻む。**(a) を推奨** — 生成経路は本 wave で閉じたので残余は偽造 evidence という別の脅威モデル。
   正本 = `output/insights/2026-07-26_t098-selector-lp-reject.md` §6-2 / §7
3. [T-107] **新規・裁定待ち (scope 外 real 所見)**: 出力 schema と selector role が新しい受理集合を
   表現していない。両者は封印済み prediction の `sources` に sha pin されるため bytes 変更が既存
   freeze の検証を割る。選択肢 = (a) parser-authoritative 契約の明文化、(b) versioned schema/role
   への移行。[T-106] の受理差を固定する境界テスト新設も同じ裁定に従属する
4. [T-105] **新規 (scope 外 real 所見)**: `tools/dev_waves/daemon.py:626-638` の
   `_run_artifact_bytes` が `os.walk` の列挙後に `path.lstat()` するため、atomic-write の一時ファイル
   (`*.tmp.<pid>.<tid>`) が列挙と lstat の間に消えると `FileNotFoundError` が素通しされ
   `DevWavesError` の fail-closed にならない。本 wave の受入で 1 度発現し単独再走 3/3 passed を実測。
   本番コードに触るので測定前後の扱いに裁定が要る
5. [T-102] **scope 外 real 所見**: production の git runner が ambient `GIT_*` を継承する
   (`s1_known_axes_freeze.py:89`、`s8b_holdout_freeze.py:147`)。本番コードに触るので測定前後の
   扱いに裁定が要る。変わらず
6. [T-103] **未着手**: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つ
   テストの新設。検出力の追加として価値がある。変わらず
7. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
8. [T-097] 裁定待ち: placeholder 検出の対象族拡張 (claim-bearing artifact 族の定義)。変わらず
9. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
10. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
11. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
12. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
13. [T-104] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。予算値の引き上げ可否の
    独立審査か reference 再編かの裁定が要る。変わらず
14. [T-108] **新規・裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件 —
    (i) 差分が到達しえないファイルで出た赤の扱い (単独再走で再現性を実測し、帰属せず新規所見として
    起票する。`DW-O06` は submodule 由来の偽赤、`DW-O18` は import path 由来の偽赤しか扱っておらず、
    無関係モジュールのフレークに規則がない)、(ii) 受理集合を**縮小する** wave では、承認外の
    **過剰拒否**を検出する正例も変異事前登録に含める規則 (`DW-M01`)。本 wave では正例が
    変異 S2 / S7 / S8 を実際に KILL しており、負例だけでは検出できなかった。
    `docs/dev-wave/**` は hard ceiling 24000 に対し 23987 で余裕 13 bytes。[T-101] / [T-104] と
    併せ、予算値の引き上げ可否を独立審査するか reference を再編するかの裁定が要る
15. [T-089] **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を
    同時更新する。変わらず
16. [T-090] **測定後の hardening と裁定** (前倒し対象外): `VerifiedFreeze.document` が mutable dict の
    まま返る (`s8b_freeze_io.py:30-38`)。変わらず
17. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
18. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
19. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
20. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
21. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
22. [T-012] 延期: pilot 凍結維持。変わらず
23. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (3) — [T-109] クロスプロトコル対応: 実装可能性を調査し「実装しない」と裁定 (設計のみ・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回 (引数「クロスプロトコル対応」)。段 4 で **実装しない**と裁定し `DW-S04` の
`4→7→8→9` を採った。**実装差分がないため変異 matrix と受入全走は対象外**である。
材料レポート = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md`、
逐語 = 同 `-consultations.md` (原文 sha256 併記) を正本とする。

- **裁定の骨子**: cross-protocol の実装経路が**すべて**ユーザー承認済みの決定で塞がっている。
  (i) D86(3)/D87 が AI の `qsub` を明示禁止するため、生死実験の実測自体が人間手番、
  (ii) D16 に trace-hook の out-of-tree patch 例外はなく (却下リストに「全て patch」がある)、
  branch へ置けば gitlink 前進で承認定数 `CCBENCH_FULL_SHA` と衝突、
  (iii) D32 (ユーザー承認 2026-07-03) が cross-protocol を主実験後へ降格し一歩目をカタログ化試作と定める。
- **最重要の発見 — 凍結 bytes を触らなくても承認済み手番は割れる。** 親は当初「`genome.py` を触らず
  gitlink も動かさなければ無害」と考えたが誤り。floor launch certificate の `clean_scan_digest` は
  **実 repository file 一覧を preimage に含む** (`s8b_floor_campaign.py:1597-1639`)。patch/driver を
  commit するだけで [T-088] receipt の `source_commit` と `clean_scan_digest` が承認時点から変わる。
  `submit_floor.sh:181-245` は `output/` 外の untracked と未 commit script を明示拒否し、
  PBS ログの既定戻り先 (投入 dir) がこれに抵触する。
- **素材: 移植順序は protocol の系統でなく版 ID の安定性で決まる。** OCC 同士の silo→tictoc は
  直感的に近いが、tictoc は validation の rts 拡張が delta overflow 時に**新版を書かずに wts を前進**
  させる (`cc/tictoc/transaction.cc:425-440`)。mocc は hybrid だが bitfield 抽出は恒等。
  ただしその恒等性も **UPDATE-only 限定**で、`absent`・INSERT/reinsert・scan で前提が崩れる。
- **素材: 「移植した」と「同じ強度で検証できる」は別である。** `Integrity.clean()` の 9 カウンタのうち
  `lock_coverage_violations` と `permutation_violations` は **silo の `#if TRACE` assert が emit する
  X 行 / P 行だけが検出源**。si 型の最小 hook を移植すると同 2 項は常時 0 の恒真ゲートになり、
  同じ lockskip を silo は indeterminate、mocc は certified としうる受理集合の非対称が生じる。
- **親 brief の誤りを 10 件 real と認めた。** P4 (AI qsub 可) / P5 (D16 例外) / P1・P2 (一歩目は S1) /
  P6 (patches 追加は無害) / P7 (live 軸 2 本) / 実測2 (verifier に silo 出現 0) /
  実測3 (`is_clean()` が 4 カウンタ) / 実測6 (恒等写像) / R-1 (手動 cmake は gate 迂回でない)。
  特に R-1 は親が段 2 の blocker 指摘に反論したものだが、レンズ A が「s5 の手動 build は trusted な
  HEAD 済み hook の上に broken 差分を重ねるもので、新規 hook を作る本件と非同型」と否定した。
- **エージェント工数**: codex 子 3 本 (プラン 1・敵対レンズ 2)。**3 本すべて NO-GO**。
  段 2 が blocker 2 件、段 3 が must-fix 17 件。実装子・レビュー子は起動していない (実装しない裁定のため)。
- **検査**: 逐語・材料レポート凍結前に検出語 gate を機械検査した = literal placeholder **hit 0**
  (語彙 3 件)、三軸 conjunction **hit 0** (holdout rr80/rr20 の両方、走査 3 ファイル)。
  可逆 defang と erratum は不要だった。`check_docs` rc=0。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は **F39 の起票** (routing 1) —
  「凍結 bytes を触らない」を安全条件と誤認し、ファイル追加が `clean_scan_digest` 経由で
  承認済み手番を割ることを見落とした near miss。実害なし (段 3 が実装前に検出) だが、
  親は誤前提を handoff へ「解決済み」と凍結までしていた。残り 2 件 (`DW-S01` の依存棚卸しが
  別ノード実行を扱っていない / 同節に「未実行の承認済み手番を自分の変更が失効させないか」の
  逆向き照合が無い) と F39 の恒久対応は、`docs/dev-wave/**` が上限 24000 に対し 23987
  (余裕 13 bytes) で収まらないため [T-109] に束ねて裁定へ送る (前例 = [T-101] / [T-104] / [T-108])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。
   **[T-109] により優先度が上がった** — 本手番より先に repo へファイルを足すと
   `source_commit` / `clean_scan_digest` が変わり再承認が要る
2. [T-109] **新規・裁定待ち (本 wave の成果)**: クロスプロトコル対応の裁定パッケージ 6 件 —
   (a) D16 の prototype 例外 (一回限りの trace-hook patch) の可否、(b) [T-088] との順序
   (**AI 推奨 = [T-088] を先に完了**)、(c) 最小 trace-hook smoke の scope、
   (d) observer-effect baseline の protocol 拡張 (手動 cmake 経路が規律 1 の機械防壁を通らない)、
   (e) MOCC lock coverage package、(f) 本物の cross-protocol package の順序 (D32 の一歩目 =
   カタログ化試作)。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5。
   併せて dev-wave 自己改善 3 件も同裁定に束ねる — (g) F39 の恒久対応 (`DW-O09` の pin 閉包既定対象へ
   「ファイル集合を pin する digest」を追加)、(h) `DW-S01` の依存棚卸しが別ノード実行を扱っておらず
   ログインノードの値で偽充足しうる、(i) `DW-S01` に「未実行の承認済み手番を自分の変更が失効させないか」
   の逆向き照合が無い (F35 は stale 検出の一方向のみ)。いずれも予算 13 bytes に収まらない
3. [T-106] 裁定待ち: ratified proof chain が selector raw を再 parse しない。**(a) 現状維持 + 射程明記**
   を推奨。変わらず
4. [T-107] 裁定待ち: 出力 schema と selector role が新しい受理集合を表現していない。変わらず
5. [T-105] scope 外 real 所見: `tools/dev_waves/daemon.py` の `_run_artifact_bytes` が
   `FileNotFoundError` を素通しする。変わらず
6. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
7. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
8. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
9. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
10. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
11. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
12. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
15. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
17. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
18. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
19. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
20. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
21. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
22. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
23. [T-012] 延期: pilot 凍結維持。変わらず
24. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (4) — /rulings: 裁定待ち 16 件を索引化しユーザーが 4 件を裁定 + 再承認コストの誤報告を訂正 (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` 1 回。索引 16 件・詳説 5 件を提示し、ユーザーが 4 件を裁定した。あわせて、直前エントリ
2026-07-26 (3) が報告した「ファイル追加が [T-088] の承認前提を変える」を**過大報告として訂正**する。

- **ユーザー裁定 (2026-07-26)**:
  - **[T-106] = (a) 現状維持 + 射程の明記。** ratified 側に再 parse を入れず、適用範囲を文書化する。
  - **[T-107] = (a) parser-authoritative 契約の明文化。** 出力 schema と selector role の bytes は変えない。
  - **[T-105] = 計測後に回す。** 本番コードに触るため [T-011] の後。
  - **[T-109] の順序 = クロスプロトコル対応を先行してよい (親の推奨を却下)。** 判断の前提として
    ユーザーが再承認コストを問い、親が実測して「不要」と回答した (下記訂正)。作業は新セッションで行う。
- **訂正 (erratum) — 直前エントリの「承認前提が変わる」は過大報告だった。**
  `clean_scan_digest()` (`s8b_floor_campaign.py:1597-1639`) は**投入時にその場で計算して記録する値**で、
  承認済み定数との照合を持たない。`s8b_approved.py` の承認定数一覧 (`:42-67`) に
  `clean_scan_digest` も `source_commit` も無い。`source_commit` は `submit_floor.sh:183` の
  `git rev-parse --verify HEAD` を投入時に取るだけで、同一投入内の pre/receipt 一致
  (`test_pegasus_floor_tools.py:806`) しか見ていない。
  `submit_floor.sh:181-245` が実際に要求するのは (i) tracked 作業ツリーが clean、(ii) index が clean、
  (iii) `output/` 外に untracked が無い、(iv) job script が tracked かつ作業ツリー bytes = commit 済み
  blob、の 4 点であり、**いずれも人間の再署名ではない**。
  したがって **repo へファイルを足しても [T-088] の再承認は発生しない。**
  親は段 3 レンズ B の指摘を裏取りせずに受け入れ、worklog・材料レポート・F39 へ書いた。
  **retroactive に直さない** (F38 の前例に従う) — 既 land エントリは本 erratum で訂正する。
- **訂正後も残る真の制約 (こちらは実在する)**:
  - **gitlink 前進は別物。** submodule ブランチへ置くと `CCBENCH_FULL_SHA` (承認定数、
    「現在値の追認を拒否」) と衝突し、`test_ccbench_full_sha_matches_real_gitlink` が赤になる。
    解消にはユーザーによる新 pin の承認と、`known_axes_freeze` / `floor_protocol` の再凍結を要する。
    **これは実際に手間がかかる。**
  - 新規ファイルは三軸 conjunction に一致してはならない (本 wave の 4 ファイルは hit 0 を実測済み)。
  - `output/s8b-freeze/` 配下に未知 file を置けない。
  - PBS ログの既定戻り先は投入 dir なので、`#PBS -o/-e` を `output/` 配下へ向ける必要がある。
- **F39 の射程も縮む。** 「ファイル追加が承認済み手番を割る」の部分は誤りで、正しくは
  「ファイル集合が digest の preimage に入るのは事実だが、その digest は事前承認されていない」。
  F39 本文の恒久対応 (`DW-O09` へ「ファイル集合を pin する digest」を加える) は、
  **pin 一般の見落としとしては依然有効**だが、緊急度は下がる。[T-109]-(g) として裁定へ残す。

### 次の一手
1. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す** (ブランチ側は再承認と再凍結という実コストが確定しているため)。
   残る (c)〜(i) は次セッションの段 1 で scope 化する。正本 =
   `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
2. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。**[T-109] との順序制約は解消した** (再承認は不要) ため、どちらが先でもよい
3. [T-106] **裁定済み → 実施待ち**: (a) 現状維持 + 射程の明記。ratified が selector raw を再 parse
   しない事実と、その適用範囲を文書化する
4. [T-107] **裁定済み → 実施待ち**: (a) parser-authoritative 契約の明文化。[T-106] と同じ wave で扱う
5. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し修正
6. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
7. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
8. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
9. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
10. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
11. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
12. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
15. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
17. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
18. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
19. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
20. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。**条件見直しを /rulings で提起済み** (16 番)
21. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。同上
22. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。同上
23. [T-012] 延期: pilot 凍結維持。同上
24. [T-082] 延期: 全 caller 移行は 1 cycle 後。同上

## 2026-07-26 (5) — [T-106][T-107] parser-authoritative 契約を確定し受理差を境界テストで固定 (テストのみ・本番 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-26 にユーザーが裁定した (a)/(a) を実施した。差分は
`test_s8b_ratified_verify.py` の 199 行 (純追加) だけで、production・schema・role・凍結成果物の
bytes は不変、受理集合は拡大も縮小もしない。設計裁定は D90、材料は
`output/insights/2026-07-26_t106-t107-parser-authoritative.md`、逐語は同 `-verbatim.md`、
変異台帳は同 `-mutation-ledger.json`。実装 commit = `c4efa3b`。
検出 3 語は D88 (6) を継承し LP-1 / LP-2 / LP-3 の記号参照で書く。

- [T-106] **消化**。ratified に再 parse を入れず、射程を D90 (3)(4) に明記した。
- [T-107] **消化**。受理集合の正本を **parser module** (関数単体でなく module) と明文化した。
  定数・helper で受理集合が動くため関数名では抜け道が残る、という段 3 の指摘 (A-5) を採用した。
- **裁定前提は実ファイル編集で実測した (模擬なし)**。role と output_schema に 1 byte 追記すると
  既存封印 prediction の検証が実際に割れ (`sources.*.sha256 が実ファイルと不一致`)、
  `git checkout --` 復元後に緑へ戻ることを確認した。これが [T-107] の根拠である。
- **親の実測を段 3 が訂正した (A-6、real)**。親は「ratified は parser の blob sha を照合するだけ」と
  書いたが、ratified は selector freeze module を import し、それが parser module を module-level で
  import する。**ratified は parser の import 可能性には感応**し、非感応なのは raw 分類の意味論だけ。
- **D89 の射程漏れを補完した**。D89 は floor だけを挙げていたが、parser 感応は生成層
  (`record_agent_attempt`) と検証層 (`verify_prediction_freeze`) の 2 層で、検証層の消費者は 4 経路。
  **うち floor は dormant** (official が core で無条件拒否される)。
- **scope 外として 2 件を不採用にした**。consumer 閉集合の AST テスト (構文形状しか固定せず
  `if False`・alias・`getattr` を見逃す一方、無害な refactor で偽赤になる) と、D90 の統治機構
  (「全受理集合変更に新 D 必須」「新 consumer は必ず verify 経由」)。後者はユーザー裁定 2 件の射程外の
  新設で、DW-G03 の独立 2 例も無い。裁定パッケージへ送る ([T-110])。
- **素材: レビューが実在の検出漏れを見つけた。** 当初実装は private 関数 `_reparse_agent_raw` を
  直呼びして「status 照合の変異を殺す」と主張していたが、公開経路では `valid` 行の
  `parser_error_code` が手前で `None` に強制されるため**等価変異**であり、偽の KILL だった (RA-1)。
  実効的な変異 (記録 error code の照合を消す) は当時**誰も捕まえていなかった**。公開経路の負例
  (`invalid` + 誤 code) へ差し替えた結果、この変異が新テスト固有の KILL になった。
- **変異 matrix (親実測、統合 commit 前)**: 事前登録 **5/5 が実測と一致**。帰属 3 (S3 = 記録 error code の
  照合、S4 = 正例による過剰拒否検出、S6 = 診断シグナル pin)、非帰属 control 2 (S1 / S2 は既存テストも
  KILL)。control は**変更前 Git HEAD のテスト集合**とし、本差分が純追加であることを利用して
  新 node の `--deselect` で exact に再現した。harness は アンカー一意性 assert・注入 diffstat 記録・
  `git checkout --` 復元 + 内容一致検査・flock 単一走行を持ち、全走後の tree は clean。
- **事前登録の誤りが 3 件あり、erratum として台帳に残した** (材料 §8)。S3 の等価変異 (RA-1 が検出)、
  S5 の到達不能 (RA-2 が検出。`_fixed_commit_all` へ戻すと直後の base commit が空 commit で先に落ちる)、
  S6 の期待値誤り (親の誤り。本走で判明)。**S1 が非帰属だった**ことも収穫で、ratified に再 parse を
  足すと既存 42 node が落ちる — この性質は本 wave 以前から既存テスト群が厚く守っていた。
- **エージェント工数**: codex 子 6 本 (プラン 1・敵対相談 2・実装 1・レビュー 2 は max/high、fix 1・
  焦点再 1)。**相談 2 本・レビュー 2 本・焦点再 1 本のすべてが NO-GO**。親の provisional 裁定は
  (P2) が否定され、「delta 4 点」も水増し (実質 3 点) と判定された。
- **検査 (統合 commit 直前の実測)**: 受入全走 **3059 passed / 18 skipped / 0 failed** (1811.26s)。
  基線 3058 (前 wave 実績) に対し +1 = 本 wave の新テスト 1 本、node 消失 0。`check_docs` rc=0。
- **task-run pilot は非発火** ([T-012] で凍結維持のため。DW-O07 の発火条件を満たさない)。

### 次の一手
1. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す**。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
2. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。[T-109] との順序制約は解消済み。変わらず
3. [T-110] **新規・裁定待ち**: 本 wave が scope 外として不採用にした 2 件の扱い。
   (i) parser 感応 consumer の閉集合を機械的に固定するか (現行 AST 案は構文形状しか固定できず不採用。
   到達意味論を固定する別機構が要る)、(ii) 受理集合変更時の手続義務 (新 D・境界テスト同時更新) を
   制度化するか。どちらも DW-G03 の独立 2 例が無いため、制度化には裁定が要る。正本 =
   `output/insights/2026-07-26_t106-t107-parser-authoritative.md` §6 と D90 (6)
4. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し修正。変わらず
5. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
6. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
7. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
8. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
9. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
10. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
11. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
12. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
13. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
14. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
15. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
16. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
17. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
18. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
19. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
20. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
21. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
22. [T-012] 延期: pilot 凍結維持。変わらず
23. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず
