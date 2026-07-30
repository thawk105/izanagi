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
## 2026-07-29 (59) — [T-153(e)] + [T-154(2)(3)] provenance gate を完了 — CAB 最終 trailer block 配置 + policy 9,000-byte 上限 (コード + docs、branch codex/dev-wave-t153e-t15423、計測 = 本 worktree・ログインノード)

- ユーザー裁定どおり、`docs/ai-provenance.md` は 9,000 bytes 上限 (実体 8,832 bytes)、
  `Co-Authored-By` 候補はすべて最終 trailer block に置く受理集合へ変更。D96 手続に従い
  D98・policy・checker・境界 test を実装 commit `9b26b3b` へ同梱
- Codex plan 1、敵対相談 2、実装 + fix 3、敵対レビュー 2 + 焦点再レビュー 2。
  初回レビューの real 10件をfix1、pre-policy parser遡及のR-1をfix2で閉じ、focus2は
  closed 11 / partial 0 / regressed 0 でGO。逐語と裁定 = insight README
- 変異 matrix 8/8 KILLED。divider、hostile Git config、CAB件数、early return、非遡及、
  message-file接続、9,001-byte、過剰拒否正例を単一nodeで検出。SURVIVED / mask / erratumなし
- 実行順は O19 の「tracked mutation本走は統合commit後」に従い、実装commit → mutation →
  全受入 → 本記録commit。裁定予定ではなくこの実手順を記録する
- main は開始後に `180d3c1` まで正常前進。main側 (54)〜(58) を保持し、本エントリを (54) から
  (59) へ振り直して5回のmerge競合を解消。main未追跡・未commitの他session面は変更していない
- 最終受入: main `efa3786` 取込treeで全走 3489 passed / 18 skipped。`180d3c1` 取込後のtree差は
  `docs/worklog.md` だけで、影響194 passed、`check_codex_agents` / `check_docs` 緑、
  `check_ai_provenance` 508件・違反なし
- 低優先残余: commitごとの `git log -S` は線形履歴で二次コストになりうる。現waveの
  timeout・誤受理/誤拒否はなく受入阻害ではないため、受理集合を保つcache化を [T-173] へ分離
- エージェント工数: Codex 9 job (planner 1 / consult 2 / author・fix 3 / review 3)。
  親 = brief・裁定・docs・統合・mutation・受入・記録

### 次の一手

- [T-139] **P1・裁定完了 ((45)) + 着手承認 ((54)) → 恒久実装 wave 実装待ち**: 着手はユーザーの
  タスク開始指示から
- [T-142] **再裁定待ち ((55))**: 親推奨は close。継続なら tie/authoritative selector・live campaign /
  正式 perf・exact floor・paired pilot を先行承認し、自然な skip が無ければ close
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 (本エントリ、9b26b3b)**: (a)〜(d) は (47)、(e) は本waveで完了
- [T-158] 同上
- [T-141] 同上
- [T-143] 同上
- [T-126] **再裁定待ち ((56))**: 親推奨は qualification-first amendment。headline 昇格不能な
  専用系列で known non-repro live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **再裁定待ち ((58))**: [T-172] で事前 mutation 登録を欠いたため、親推奨は bounded な
  事後 mutation audit で補完し、事前登録不能だった逸脱を明記する
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
- [T-150] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-151] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-154] **完了**: (1) は既完了、(2) 9,000-byte上限と (3) CAB配置gateを本waveで完了
- [T-130] **裁定済み ((54) = 短縮する・手段限定) → 実装待ち**: ビルドキャッシュ / 並列ビルドで
  短縮する。ビルド成果物の使い回し (control の意味を薄める経路) は採らない
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
- [T-167] **P3・裁定済み ((54) = 採用、新 pin `c9c1a9c` 承認) → 実装待ち**: [T-163] と同一 wave
  または直前で実装。[T-150]/[T-151]/[T-170] の上流出しを同梱
- [T-168] 同上
- [T-169] 同上
- [T-170] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-171] **完了**: Codex dev-wave Skill と drift 検査を実装
- [T-172] **完了**: Codex rulings Skill と drift 検査を実装
- [T-173] **P3・新規 (本wave focus2 BL-PERF-1)**: per-commit `git log -S` を
  受理集合不変のgraph propagation/cacheへ置換し、496件約66秒の全履歴監査を短縮する

## 2026-07-29 (60) — [T-139] rung 1 恒久実装 wave 完了 — patch + 台帳 + driver + certified evidence + 再束縛 pytest (branch worktree-dev-wave-t139-permanent、計測 = Pegasus 計算ノード)

- `/dev-wave T-139` の全 9 段を実施 (軽量版不可と判断: rung 選定の設計択一 + 受理集合の新設)。
  段 2 プラン + 段 3 敵対 2 レンズ (32 所見) + 段 6 敵対レビュー 2 本 (21 所見 + 親検出 2) +
  焦点再レビュー 3 巡 + targeted fix。DW-O16 の 3 巡上限到達後の残余 3 blocker は親裁定 +
  テスト・変異による直接閉鎖検証で閉じた (レビュー round は増やさず)
- 成果物: `patches/silo_ladder_rung1.patch` (D18 第 4 類 subtype `evaluation_role=ability_probe`、
  中立 stem、REPORT 第 2 マクロで reporter を計測 binary から隔離) + `patches/ledger.json`
  (closed schema、projection_policy) + 契約 checker + 専用 driver (env scrub・tool identity・
  patched-source SHA・receipt sha256 鎖・attempt 封印・閉じた失敗分類・絶対 deadline) +
  射影 tripwire (3 loop loader 配線、字面回帰検知) + PBS 資材 (offline staging、F49 receipt) +
  pytest 4 群 + fixture 正負例
- **実測 (campaign 5 = 873920.nqsv、merge 後 HEAD)**: correctness = trace t4 certified serializable
  (write_intent_violations=0 含む)。gap = trace-disabled t48 N=1m interleave 6 rep で
  W-cal (登録 workload 逐語) stock 3,939k-4,035k vs rung 161k-169k tps (≈4.1%)、
  W-hw (契約転写) stock 1,638k-1,687k vs rung 170k-176k tps (≈10.5%)。両 cell で
  max(rung) < min(stock)。committed JSON + raw bundle + 再束縛 pytest 緑。値は ability-probe
  受理証拠であり headline / RF に転用しない
- 実測が検出した欠陥 6 件 (extern 初期化子 -Werror / compile_commands 多ターゲット / **計算ノード
  外部 network 不可** (masstree clone 不能、runbook §7.1 へ追記) / NQSV 会計に exit_status 行なし /
  nm basename vs realpath / --version 第 1 token) を codex fix で是正。R2-4 束縛が fix・merge の
  たびに旧測定を正しく無効化し、campaign 4→5 の再取得で同一結論 (4.4%/10.7% → 4.1%/10.5%) を確認
- 変異 matrix (commit 後本走): PM1 liveness all→any / PM2 exactly-one 弛緩 / PM3 certified 単独
  受理 / PM4 tripwire 素通し — **4/4 KILLED、killer は期待 nodeid 各 1 件**。負例 N1〜N6 + 正例
  P+1/P+2 は suite 常設
- main 統合 2 回 (worklog (46)〜(55)、(56)〜(59)) を wave branch へ merge (D70)。本エントリは
  旧番号 (56)・新 ID T-172〜T-175 で書いたが、並行 land ((56)〜(59) と T-172/T-173 採番) との
  衝突で (60)・T-174〜T-177 へ振り直した。T-152 の verifier 更新へ追随
  (`write_intent_violations` を closed schema + 受入 gate に追加 = 強化)、T-152 の裸マクロ patch
  4 本は棚卸し tripwire が検出し allowlist へ。failures **F53** 起票 (fix 子が退避中 artifact を
  断片上書き — near-miss。私の F52 案は main の F52 と衝突し F53 へ振り直し)
- 受入全走 **3527 passed / 18 skipped / 0 failed** (login node。g++-13 系 18 skip はこの環境で
  検出力なしと記録)。恒久台帳 = `output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md`
  (evidence pytest の実測後逸脱 2 件の記録を含む)
- エージェント工数: 親 1、codex read-only 6、codex author 実装 3 + fix 15、PBS job 5
  (873903/873904 = infra 失敗、873909/873916 = 検証強化で破棄、873920 = 採用)

### 次の一手

- [T-139] **完了 (本エントリ)**: rung 1 恒久化・certified evidence・変異 4/4 KILLED。残余は
  [T-174]/[T-175]/[T-176]/[T-177] へ分離。identity ablation 省略は裁定済み追認 (insight §7-4)
- [T-142] **再裁定待ち ((55))**: 親推奨は close。継続なら tie/authoritative selector・live campaign /
  正式 perf・exact floor・paired pilot を先行承認し、自然な skip が無ければ close
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 (本エントリ、9b26b3b)**: (a)〜(d) は (47)、(e) は本waveで完了
- [T-158] 同上
- [T-141] 同上
- [T-143] 同上
- [T-126] **再裁定待ち ((56))**: 親推奨は qualification-first amendment。headline 昇格不能な
  専用系列で known non-repro live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **再裁定待ち ((58))**: [T-172] で事前 mutation 登録を欠いたため、親推奨は bounded な
  事後 mutation audit で補完し、事前登録不能だった逸脱を明記する
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
- [T-150] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-151] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-154] **完了**: (1) は既完了、(2) 9,000-byte上限と (3) CAB配置gateを本waveで完了
- [T-130] **裁定済み ((54) = 短縮する・手段限定) → 実装待ち**: ビルドキャッシュ / 並列ビルドで
  短縮する。ビルド成果物の使い回し (control の意味を薄める経路) は採らない
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
- [T-167] **P3・裁定済み ((54) = 採用、新 pin `c9c1a9c` 承認) → 実装待ち**: [T-163] と同一 wave
  または直前で実装。[T-150]/[T-151]/[T-170] の上流出しを同梱
- [T-168] 同上
- [T-169] 同上
- [T-170] **P3・裁定済み ((54) = [T-167] wave へ束ねて上流へ)**: 上流 PR / push は人間
- [T-171] **完了**: Codex dev-wave Skill と drift 検査を実装
- [T-172] **完了**: Codex rulings Skill と drift 検査を実装
- [T-173] **P3・新規 (本wave focus2 BL-PERF-1)**: per-commit `git log -S` を
  受理集合不変のgraph propagation/cacheへ置換し、496件約66秒の全履歴監査を短縮する
- [T-174] **P3・裁定要 (新規)**: planner/coder への prompt 因果束縛 (mediated launcher /
  provider receipt)。現 tripwire は「harness が受理する proposal 経路」までの字面回帰検知
  (t139 恒久 insight §7-1)
- [T-175] **P3・裁定要 (新規)**: 射影入力の origin-allowlist 再設計 (semantic copy 対策、
  同 insight §7-2)
- [T-176] **P3 (backlog、新規)**: raw evidence bundle の保存形 (trace 圧縮で 124MB→縮小)。
  driver 変更 = 再測定を伴うため次回 characterization に合流 (同 insight §7-3)
- [T-177] **P3・裁定要 (新規)**: F53 恒久対応の DW-O02 統合 (退避中成果物の prompt 明記義務、
  1 文 ≈230B) が docs/dev-wave/** の 24000B 上限を超過し、自己改善契約に従い変更を止めて返す。
  択 = 予算内へ他節を縮約 / 上限の独立審査 / memory 運用のまま

## 2026-07-29 (61) — Codex dev-wave 資源効率監査を P1 の 6 原子タスクへ登録 (docs のみ、branch main、計測 = 既存ログ再集計のみ)

- 現行契約を skill 文書と git log に照合した。DW-O01 は全 worker を `gpt-5.6-sol` に固定し、
  plan / consult は reasoning `max`、implementation は `high`、review は明示 routing がない。
  外部 supervisor の token budget はあるが、Codex Skill は実 supervisor を使わず、job 単位の
  token / turn / wall-clock / retry 上限もない
- T-153(e)/T-154 の凍結ログを再集計すると、worker は **10 session / 434 model turns /
  CLI reported 2,757,982 tokens**。stage 別は plan 224,150、consult 392,185、author 171,736、
  review 544,553、fix 605,734、focus 819,624 で、focus2 単独が 498,984 / 71 turns。
  worklog (59) の「9 job」は実ログ 10 session と不一致
- 明白な浪費例は F43 (168k tokens 後に 194-byte 断片、採用不能) と F45
  (85,097 + 243,247 CLI reported tokens の safety-filter 終了、出力なし)。現 validator は
  採用を防ぐが費消後にしか働かず、同一失敗の retry / engine 切替規則は Codex Skill にない
- 一方で同 wave は real issue 10 件 + focused review 1 件を閉じ、mutation 8/8 KILLED。
  品質を壊す一括 downshift はせず、[T-179]〜[T-184] を観測→制限→限定比較→証拠採用の順に登録。
  各 ID は将来セッション 1 回を上限とし、詳細な scope / dependency / acceptance は
  `docs/phase3.md`「Codex dev-wave 資源効率化」を正本とする
- T-178 は別セッションの未統合 handoff が使用中だったため、番号衝突を避け T-179 から採番した。
  他セッション所有の未追跡 handoff と `.codex/worktrees/` は変更していない
- 検査: `test_check_docs.py` 132 passed、`check_codex_agents.py` OK、`check_docs.py` 違反なし、
  `git diff --check` rc=0
- エージェント工数: 親 1、子 0

### 次の一手

- [T-179] **P1・最優先**: worker 資源台帳を正本化し、T-153(e)/T-154 の 10 session と
  stage 別 token/turn、worklog の job 数不一致を live inference なしで機械再現する
- [T-180] **P1・T-179 後**: model/reasoning は変えず、job 単位の resource envelope と
  fail-closed receipt を実装する
- [T-181] **P1・T-179 後**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **P1・T-179 後**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・T-179 後**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する
- [T-184] **P1・T-180〜T-183 後**: 比較済み証拠だけで stage 別 model/reasoning/resource/retry
  policy を採用し、rollback と drift 検査を追加する
- [T-139] **完了 ((60))**
- [T-142] **再裁定待ち ((60))**
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] 同上
- [T-126] **再裁定待ち ((60))**
- [T-059] **再裁定待ち ((60))**
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**

## 2026-07-29 (63) — [T-143] RuleOps v1 完了 — HEAD固定inventory + advisory候補package + 受入preflight (コード + docs、branch codex/dev-wave-t143-ruleops、計測 = 本worktree・ログインノード)

- ユーザー承認済みT-143を9段dev-waveで実装。削除安全を名乗るplan v1は段3の2レンズ
  (real 21 / refuted 0)で破棄し、read-only proposal workflowへ裁定。設計正本=D99、
  運用正本=`docs/ruleops.md`、材料=`output/insights/2026-07-29_t143-ruleops.md`
- 段6は初回review 2本 + focused再review 3巡。最終closureはRA 10 / RB 10 / RR 2 /
  R2R 1の23件すべてclosed、regression 0でGO。主な修正はGit config poisonとlazy fetch遮断、
  captured HEAD固定、exact control除外、receiptの実在祖先/tree blob/全commit path union、
  ledger-wide alias/cycle、最大packageの60秒境界
- 新規R3R-1は、古いreceipt rangeのstdout量が明示boundedでない可用性SHOULD。
  invalid package誤受理・read-only境界破壊ではないため本waveはGO、[T-185]へ持ち越し
- 変異は最終base `17f1235`でM1〜M12 **12/12 KILLED**、unexpected node 0。初回M3は
  managerが`_inventory_item`へ誤注入したinvalid runで、同長fixtureという初期診断も
  56 bytes対38 bytesの直接計測でrefuted。結果を消さずerratumへ残し、実効
  `build_inventory` gateへ再照準してKILLED
- 実装commit `8976c14`、M3 fixture強化 `17f1235`、並行main統合 `74760ee`。
  mainは開始時`eaa2dd2`から`94051a3`へ前進していたがユーザー指示どおりmergeし、
  重複したcheck_docs 2面はRuleOpsとmain側契約を両方保持
- 受入実測 (main統合前の最終mutation base): RuleOps 83 passed、最大package 2.288秒、
  focused 208 passed、plain runner 3 passed、全走3522 passed/18 skipped/rc=0/113.66秒。
  main統合後positiveはRuleOps 83 passed (最大package 2.115秒)、check/docs 217 passed、
  `check_docs` / `check_codex_agents` / provenance 528件がgreen。main統合・記録後の
  最終全走は3674 passed/18 skipped/rc=0/240.45秒
- index/staged-tree束縛、D97 classifier、preflight refusal task-run記録、mutation producer、
  実削除/approvalはscope外のまま。R3R-1以外は新taskを起こさない
- エージェント工数: Codex subprocess 13 (plan 1、敵対相談 2、author/fix 5、
  review/focused review 5、`gpt-5.6-sol` high)。親=brief・裁定・docs・統合・変異・全走・記録

### 次の一手

- [T-179] **P1・最優先 ((61))**: worker 資源台帳を正本化し、T-153(e)/T-154 の 10 session と
  stage 別 token/turn、worklog の job 数不一致を live inference なしで機械再現する
- [T-180] **P1・T-179 後 ((61))**: model/reasoning は変えず、job 単位の resource envelope と
  fail-closed receipt を実装する
- [T-181] **P1・T-179 後 ((61))**: focused review の reasoning `max` 対 `high` を
  凍結入力で限定比較する
- [T-182] **P1・T-179 後 ((61))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・T-179 後 ((61))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する
- [T-184] **P1・T-180〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する
- [T-185] **P3・RuleOps hardening (本エントリR3R-1)**: receipt rangeのcommit数と
  path-union stdout bytes/cardinalityをstreaming上限でfail-closedにし、安定reasonとover-limit
  synthetic negativeを追加する
- [T-139] **完了 ((60))**
- [T-142] **close ((62)のユーザー再裁定)**: formal selectorとlive campaignが揃った場合のみ
  新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 (本エントリ、D99)**
- [T-126] **裁定済み ((62) = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列でlive controlと機械receiptを先行し、production gateは別wave
- [T-059] **裁定済み ((62) = boundedな事後mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172のdrift拒否検査を事後検証する
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**

## 2026-07-29 (62) — [/rulings] 推奨 4 件をユーザー裁定として記録 — T-142 close・T-126 qualification-first・T-059 事後 mutation audit・prior main の push 確認 (docs のみ、branch main、計測なし)

- ユーザー裁定: 直前の `/rulings` 詳説 4 件を「全部推奨通り」で採用
- [T-142] = **close**。現 production 経路では安全な S2 省略枝が到達不能で、出力集合 O の
  authoritative producer も未実装。コード変更なしで閉じ、formal selector と live campaign が
  揃った場合だけ新タスクとして再起票する
- [T-126] = **qualification-first amendment 採用**。headline 昇格不能な専用 qualification
  series で known non-repro live control と machine-readable receipt を先行し、production gate /
  authoritative consumer は証拠取得後の別 wave とする
- [T-059] = **bounded な事後 mutation audit で補完**。事前登録だったとは扱わず、T-172 の
  負例 5 件に対応する operator / 予算 / 第一失敗 assert / 復元後 green を事後台帳へ固定し、
  事前登録不能だった手順逸脱を明記する。実施は別タスク
- push 裁定 = 直前の詳説対象 `180d3c1` を含む prior main の push を承認。作業中に
  `origin/main == main == 2b42da1` と `180d3c1` がその ancestor であることを実測したため、
  当該 push 項目は完了。実行者は推測しない。その後に並行 land した `9dba40f` と本記録 commit は
  この裁定による push 対象へ拡張せず、push は人間が行う境界を維持する
- 既存未追跡 `.codex/worktrees/` と T-143 / T-145 / T-146 / T-173 / T-178 handoff は並行
  セッション所有として不変更
- 検査: `test_check_docs.py` 132 passed、`check_codex_agents.py` OK、`check_docs.py` 違反なし、
  `git diff --check` rc=0
- エージェント工数: 親 1、子 0

### 次の一手

- [T-179] **P1・最優先 ((61))**: worker 資源台帳を正本化し、T-153(e)/T-154 の 10 session と
  stage 別 token/turn、worklog の job 数不一致を live inference なしで機械再現する
- [T-180] **P1・T-179 後 ((61))**: model/reasoning は変えず、job 単位の resource envelope と
  fail-closed receipt を実装する
- [T-181] **P1・T-179 後 ((61))**: focused review の reasoning `max` 対 `high` を
  凍結入力で限定比較する
- [T-182] **P1・T-179 後 ((61))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・T-179 後 ((61))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する
- [T-184] **P1・T-180〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する
- [T-139] **完了 ((60))**
- [T-142] **close (本エントリのユーザー再裁定)**: formal selector と live campaign が
  揃った場合のみ新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] 同上
- [T-126] **裁定済み (本エントリ = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列で live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **裁定済み (本エントリ = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172 の drift 拒否検査を事後検証する
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**

## 2026-07-29 (64) — [T-179] worker 資源台帳を正本化 — 10 session / 434 model calls / 2,757,982 tokens を live inference なしで機械再構成 (コード + docs、branch worktree-dev-wave-t179-worker-ledger、計測 = 本 worktree・ログインノード、既存 rollout ログの再集計のみ)

- `tools/codex_worker_ledger.py` (read-only CLI、書き込みなし) と合成 fixture 回帰を追加。
  データ源は codex CLI の rollout JSONL (`$CODEX_HOME/sessions`、既定は環境変数かコード内定数。
  マシン固有パスは docs へ書かない)。`--cwd-contains dev-wave-t153e-t15423` で
  **10 session / 434 model calls / CLI reported 2,757,982 tokens** を再構成し、stage 別
  (plan 224,150 / consult 392,185 / author 171,736 / review 544,553 / fix 605,734 /
  focus 819,624) が (61) の凍結値と全一致した
- **worklog (59) との不一致を機械検出**: 「Codex 9 job (planner 1 / consult 2 / author・fix 3 /
  review 3)」に対し実測は 10 session。不一致の実体は **review bucket の 3 対 4** (focus2 が
  落ちていた) と総数 9 対 10 で、`--strict` が両方を名指しして rc=2 を返す
- **「CLI reported」の定義を確定**: 各 session の**最後の** `total_token_usage` に対する
  `input - cached_input + output` の総和。per-turn `last_token_usage` の和 (2,765,553) は
  正本ではない。差 7,571 は `context_compacted` を挟む focus2 の 1 session だけに出る。
  台帳は差を `cumulative_minus_per_turn` として因果を名乗らずに出し、
  `context_compacted` / `thread_rolled_back` / `turn_aborted` の件数を別列で公開する
- **用語の訂正**: (61) の「434 model turns」は正確には `token_count` event (`info` 非 null) の
  件数であり、`turn_context` は同 session に 1〜2 個しかない。台帳では `model_calls` と呼ぶ。
  以後この語を使う。(61) 本文は当時の記録として書き換えない
- **stage 正解の裏取り方法を是正**: 「stage 別の合計が一致したから分類が正しい」は循環論法
  (段6 レビュー A 指摘)。誤帰属の対でも合計は一致するため、rollout の raw `user_message` 先頭から
  親が独立に導いた session_id→stage 表と**逐件照合**した (10/10 一致)。表は insight に凍結
- 段 6 の敵対レビュー 2 本が must-fix 17 件 (A 8 / B 9) を返し、親が実データで裏取りした結果
  **3 件が実在の fail-open** と確認された: (a) 最終 cumulative が `null` の session で実消費
  950 tokens が `cli_reported=0` になり `--strict` も rc=0、(b) JSON として妥当な非 object 行
  (`[]`) を壊れ行に数えず黙って読み飛ばす、(c) root 不在 / 空 dir / 選択 0 件が `--strict` で
  rc=0 (1 件も読んでいない台帳が健全として受理される)。いずれも fix 後に rc=2 へ是正
- **fix1 が回帰を 1 件持ち込み、親の実ログ受入で検出した**: 段6 の `fix2 implementation author` を
  `author` へ分類し 188,905 tokens が `fix` から `author` へ移動した。総和・session 数・
  model_calls・worklog gate はすべて不変だったため、それらだけを見る受入では検出できない。
  裁定 = stage を決めるのは**段番号**であり役割語ではない (`role=author` は Codex の権限 role 名)。
  fix2 で `fix` へ是正し、8 パターンの分類を表駆動テストで固定した
- 焦点再レビューは closed 23 / partial 6 / regressed 2 で NO-GO。残 6 件のうち
  「旧 CLI の健全形を過剰拒否している」は親が実測 (626 rollout / 56,336 usage object) で
  **再現しないと確認**したが、受理集合を不当に縮小する向きなので緩和側で採用。
  「`段6 fix 後の` (空白あり) が unclassified になる」は**実測で確認**し fix3 で吸収した
  (fail-closed 方向のため現在値は無傷)。残る「worklog の語彙追随」は docs として本エントリで実施
- 変異は統合 commit `72f8858` の後に本走 (O19)。**kill 計上 10/10 KILLED、SURVIVED・mask・
  erratum なし**。`M7` (retry 正規化) は受理集合も rc も変えないため `DW-M08` に従い
  **diagnostic sensitivity pin** として kill 計上から外した。段 4 登録の `M2`
  (session_id 8 文字短縮) は「session 融合」が起きず赤理由も一意にならないため `M2'`
  (重複検出の無効化) へ再照準し、`M9`〜`M11` を段 6 で新規登録した。改訂の理由は insight
- **scope 外と裁定した real 所見**: cwd 部分一致では wave の受理集合を固定できない (path 再利用・
  接尾辞衝突) → 恒久解は launcher の wave manifest = [T-180]。prompt hash は retry lineage では
  ない → 因果同定は launcher receipt が要る = [T-183]。本 wave は対象 10 件の session_id を
  insight に凍結して監査可能にした
- wave path は軽量版 + 段 6 敵対レビュー 2 本を保持 (段 2 / 段 3 を省略)。省いた理由は
  設計択一を実ログの直接実測で閉じたため。実装面はすべて Codex `role=author` が書き、
  親は brief・裁定・統合・変異・受入・記録・commit のみ担当した。
  変異 harness は wave 成果物ではなく親の監査計器のため job tmp に置き、repo に commit していない
  (実装子が自分を採点する計器を書く構図を避ける読み。異論があれば裁定へ)
- 実行順は O19 に従い 実装 commit (`72f8858`) → 変異 11 本 → 全受入 → 本記録 commit。
  裁定予定ではなくこの実手順を記録する
- 段 8 自己改善: 上記の fix1 回帰を新しい失敗型 **F54** として台帳へ登録した (専用 commit)。
  型 = 「集約不変量だけの受入が、実装子へ委ねた未裁定の択一による要素単位の誤帰属を通しかける」。
  恒久対応は (a) 実装子・fix 子の指示に未裁定の意味論の択一を残さない、(b) 分類・帰属を伴う
  成果物では集約一致を正しさの根拠にせず要素単位の独立 oracle と逐件照合する、の 2 点で、
  実体は insight の session_id→stage 表と表駆動テスト。
  `docs/dev-wave/**` への prose 追記は見送り — 残予算 38 bytes に収まらず、T-127 裁定
  「上限は上げない・恒久対応は prose よりテスト/機械検査を優先」と F43/F45 の同型裁定にも整合する
  ([T-177] が同じ予算問題で裁定待ち)
- 検査: 全受入 **3663 passed / 18 skipped** (249 秒、本 worktree・ログインノード)。
  main `0912975` ((63) [T-143]) 取込後の再走は **3753 passed / 18 skipped** (244 秒)。
  `check_docs.py` 違反なし、`check_codex_agents.py` OK、`check_ai_provenance.py` 違反なし。
  変異の復元後に commit 済み内容との byte 一致を確認済み。
  `git diff --check` は親が書いた面 (`docs/`、コード) で rc=0。凍結逐語 2 ファイル
  (`review-b.md` / `focus.md`) は markdown の行末 2 空白 (hard break) を含むため hit するが、
  逐語は sha256 で pin しており**改変しない**方を採る (F1 の一次資料優先)。
  同型は先行 wave の凍結 commit `08a7e5f` にも 1 件あり、本 wave が初出ではない
- 既存未追跡 `.codex/worktrees/` と T-143 / T-145 / T-146 / T-173 / T-178 handoff は
  並行セッション所有として不変更
- エージェント工数: Codex 7 session (author 1 / fix 3 / review 2 / focus 1)。
  親 = brief・裁定・統合・変異・受入・docs・記録

### 次の一手


- [T-179] **完了 (本エントリ、`72f8858`)**: worker 資源台帳を `tools/codex_worker_ledger.py`
  として正本化。10 session / 434 model calls / 2,757,982 tokens と stage 別内訳を再構成し、
  worklog (59) の「9 job」不一致 (review 3 対 4、総数 9 対 10) を機械検出する
- [T-180] **P1・T-179 完了により着手可 ((64))**: model/reasoning は変えず、job 単位の resource envelope と
  fail-closed receipt を実装する
- [T-181] **P1・T-179 完了により着手可 ((64))**: focused review の reasoning `max` 対 `high` を
  凍結入力で限定比較する
- [T-182] **P1・T-179 完了により着手可 ((64))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・T-179 完了により着手可 ((64))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する
- [T-184] **P1・T-180〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する
- [T-185] **P3・RuleOps hardening ((63) R3R-1)**: receipt range の commit 数と
  path-union stdout bytes/cardinality を streaming 上限で fail-closed にし、安定 reason と
  over-limit synthetic negative を追加する
- [T-139] **完了 ((60))**
- [T-142] **close ((62) のユーザー再裁定)**: formal selector と live campaign が
  揃った場合のみ新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 ((63)、D99)**
- [T-126] **裁定済み ((62) = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列で live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172 の drift 拒否検査を事後検証する
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**

## 2026-07-30 (65) — [T-180] Codex worker job の資源封筒と fail-closed receipt を正本化 — wall-clock を唯一の hard cap とし、live 停止は rollout tail・判定は stdout 最終 usage の二重 metering (コード + docs、branch worktree-dev-wave-t180-resource-envelope、計測 = 本 worktree・ログインノード + 実 Codex job 3 件の dogfood)

- `tools/codex_worker_launch.py` (新規、`run` / `check-receipt`) と wave manifest、
  `tools/codex_worker_ledger.py` の `--manifest` selector を追加した。統合 commit `24d2672`、
  テスト race の修正 `de0a9ad`
- **段 1 前提実測 (模擬でなく実走)**: `codex-cli 0.146.0` は turn/token/wall-clock/retry の
  上限 flag を**持たない**ため封筒は wrapper 側でしか強制できない。probe 2 本で
  (a) stdout `thread.started.thread_id` が rollout の `session_meta.session_id` と
  ファイル名に一致し、(b) rollout JSONL が**実行中に逐次 flush** される
  (`token_count` が 12/20/29/37/39 秒で 1→5) 一方、stdout の usage は `turn.completed` の
  1 回だけ、を確認した。したがって **live 停止は rollout tail、終了判定は stdout 最終 usage**
  の二重 metering になる。`turn.completed.usage` は rollout 最終 `total_token_usage` と完全一致し、
  T-179 の "CLI reported" (`input - cached + output`) がそのまま receipt に載る
- **射程を誇張しない**: hard cap は **wall-clock だけ**である。`model_calls` と token は
  観測可能な proxy による best-effort 停止 + 事後 fail-closed 判定であり、usage は model call
  完了後にしか観測できないため最大 1 call 分の不可視 overshoot がありうる
  (`model_calls_semantics` / `possible_unobserved_overshoot` で表出)。`setsid()` で
  process group を逃れた子の封じ込めは**行わず**残存を receipt に記録するに留める
- **T-179 から継承した実在の欠陥を塞いだ**: `_validated_usage` は
  `cached_input_tokens > input_tokens` を通し、`_billable({input:100, cached:200, output:1})` が
  **-99** を返した (親が実コードで再現)。token 上限をこの値の上に作ると自明に破れるため、
  launcher・ledger の双方で malformed として拒否する
- **dogfood** — DW-O01 の結線は T-184 の明示所有 (「DW-O01 と worker 契約へ一度だけ反映する」)
  かつ `docs/dev-wave/**` の残予算は 38 bytes なので docs は書き換えず、代わりに
  **本 wave 自身の段 6 レビュー 3 本を新 launcher で起動**した。receipt は
  review-a 33 calls / 192,930 tokens / 1,101.5 秒、review-b 34 / 232,757 / 1,229.1、
  focus 66 / 412,833 / 1,106.5 の**計 838,520 tokens**、3 件とも accepted かつ
  `check-receipt` rc=0。本 wave は「全 worker が launcher を通る」とは主張しない
- **dogfood が後方互換破壊を捕まえた**: fix round 1 が `schema_version=1` のまま必須 field を
  27→31 に増やしたため、数時間前に自分が生成した receipt 2 件が rc=2 で拒否された
  (親が実測)。fix round 2 で新規を v2 とし checker が v1/v2 の双方を読めるようにした。
  実運用 1 件を通していなければ wave 内で発見できなかった
- **実データ受入 (親実測、F54 の要素単位照合)**: T-179 凍結の 10 session_id で manifest を作り
  `--manifest --json --strict` を実走。`rc=0 / issues={} / 10 session / 434 model_calls /
  2,757,982 cli_reported` に加え、**stage 別 6 値を逐件照合して全一致**、session 単位の
  `job_id` 束縛 10/10、distinct job_id = 10 を確認した。旧 `--cwd-contains` 経路も同値で drift なし
- 段 3 敵対相談 2 本と段 6 敵対レビュー 2 本はいずれも NO-GO、must-fix 計 17 件 +
  親が独立に発見した 1 件 (`_append_manifest` が attempt 完了後に呼ばれ、途中で殺されると
  費消済み session が台帳から消える → rollout 相関直後へ移動)。fix 3 巡で閉じた
- **変異**: 統合 commit の後に本走 (DW-O19)。初回 10 本は KILLED 7 / SURVIVED 1 / 別理由赤 2 で、
  DW-M02 に従い初回結果を erratum として残し実効 gate へ再照準した — M18 は変異位置が
  terminate 路で期待 node が `_normal_reap` 路 (F28 の誤照準)、M14 は空 manifest が schema の
  `1..1024` 検査で先に落ち records 検査が T-179 M10 に mask される、M19 は fix2 が新設した
  単一理由 node が kill しており spec の記帳誤り。再照準 3/3 KILLED で**最終 10/10 KILLED**、
  復元後 byte 一致
- **変異 harness の中断事故**: セッションが異常終了した際、harness の `finally` 復元が走らず
  M6 (`max_attempts` の off-by-one) が作業ツリーに残った。孤児 process が生存しており
  復元と競合していた。停止 → `git checkout --` → commit 済み内容との byte 一致確認で回復した。
  F32 (外側で親が殺されると `finally` が走らない) と同型の再発であり、
  harness を前景で走らせた設計側の問題である
- **記録後再走で自作の赤を 1 件出した (F34 の再走が拾った)**: 受入全走の**最中に** F32 の
  commit を作って HEAD を動かしたため、repo HEAD へ束縛される
  `test_s8b_oracle_driver.py::...t080...` が期待値と食い違って落ちた (3837 passed / 1 failed)。
  単独再走は 82 passed / 1 skipped で再現せず、HEAD を固定した 3 回目の全走は
  **3838 passed / 18 skipped** で緑。製品欠陥でもフレークでもなく**受入走行中に commit した
  手順ミス**であり、実装差分へ帰属しない (DW-O18 の単独再現実測に従う)
- 検査: 全受入 **3838 passed / 18 skipped** (記録 commit 前 260 秒 / HEAD 固定の記録後再走 236 秒、
  本 worktree・ログインノード)。
  `check_docs.py` 違反なし、`check_codex_agents.py` OK、`git diff --check` rc=0。
  `check_ai_provenance.py` は 535 件中 1 違反だが、これは main `7be05ef` に既存の merge commit
  `6b64d21` であり本 wave の産物ではない (本 wave の 2 commit は commit 前検査を通している)
- 逐語・凍結値・変異台帳は `output/insights/2026-07-29_t180-resource-envelope-wave/`
- 実装面はすべて Codex `role=author` が書き、親は brief・裁定・統合・変異・受入・記録・commit
  のみ担当した。変異 harness は親の監査計器のため job tmp に置き repo に commit していない
- エージェント工数: Codex 9 session (plan 1 / consult 2 / author 2 / review 2 + focus 1 は
  launcher 経由、fix 3)。親 = brief・裁定・統合・変異・受入・docs・記録
- 他セッション所有の未追跡 `.codex/worktrees/` と T-145 / T-146 / T-173 handoff は不変更

### 次の一手


- [T-180] **完了 (本エントリ、`24d2672` + `de0a9ad`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **P1・着手可 ((64))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・着手可 ((64))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する。**T-180 は分類なしの機械的 retry 上限までを実装し、
  失敗型分類・safety-filter 判定・回復経路を本 ID へ送った**
- [T-184] **P1・T-181〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する。
  **DW-O01 の結線と stage 別上限値は本 ID の所有** (T-180 は機構のみ)
- [T-186] **P3・T-180 が返した裁定パッケージ**: manifest の seal ceremony と foreign entry
  後追記の検出、`setsid()` 脱出子の完全封じ込め (cgroup / bwrap)、
  stdout / artifact bytes の上限 (`max_artifact_bytes`) の 3 件
- [T-179] **完了 ((64)、`72f8858`)**
- [T-185] **P3・RuleOps hardening ((63) R3R-1)**: receipt range の commit 数と
  path-union stdout bytes/cardinality を streaming 上限で fail-closed にし、安定 reason と
  over-limit synthetic negative を追加する
- [T-139] **完了 ((60))**
- [T-142] **close ((62) のユーザー再裁定)**: formal selector と live campaign が
  揃った場合のみ新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 ((63)、D99)**
- [T-126] **裁定済み ((62) = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列で live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172 の drift 拒否検査を事後検証する
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**

## 2026-07-30 (66) — [T-187] `6b64d21` AI provenanceを履歴非改変のforward correctionで是正 (コード + docs、branch codex/dev-wave-ai-provenance-main-integration、計測 = 専用worktree・ログインノード)

- ユーザー裁定どおり、main/originと複数系列へ到達済みのmerge commitをrewriteせず、固定
  `AI-Agent-Correction` 1件で対象missing findingだけを相殺する。件名`Merge branch ...`ではなく
  trailer欠落が違反
- 元eventを再抽出して`claude-opus-5 / xhigh / integrator`を復元。session IDは永続化せず、
  sanitized fieldとevent行SHA-256へ射影。旧planner値はNO-GOで不採用
- checkerはraw/canonical/final-block、selected-set両commit、strict lineage、実欠落、
  correction自身greenを連言。一般allowlist/設定/CLI免除なし。D95のmerge pathは全parentとの差分積へ統一
- Stage 6は敵対review 2本のblockerをfix 2巡で閉じ、focused re-review 2本がGO・blocker 0。
  commit後変異はoutcome-changing 9/9 KILLED、pin 2/2、survivor 0
- branch上の`T-186` / `D100`はmain側の先行採番と衝突したため、land時に`T-187` / `D101`へ
  振り直した。履歴非改変のため既存commit件名は元番号を保持
- mainのworklog (59)〜(65)とarchive (49)〜(58)を権威とし、branch側の重複archive (49)〜(64)は
  採用しない。現行mainからfreshな統合worktreeを作り、startup gateを通した
- target抜き補助rangeの赤後に同一shellが`merge --no-commit`まで継続したF37同型再発を記録。
  commitは作らず、target-inclusive range 8件greenを単独確認
- 統合後監査がlocal-only T-180記録`cb79147`のprobe shellにCodex authorがない別違反を検出。
  ユーザー承認で同履歴をrewriteし、Codex authorが実際に最小編集した`677c32a`へ置換した
- 元waveの全受入は3807 passed / 18 skipped、関連116 passed。再構成統合後は
  final 3892 passed / 18 skipped、関連250 passed、full-history provenance 541件green
- 正本はD101、phase3完了記録、`output/insights/2026-07-29_ai-provenance-forward-fix-wave/`
- エージェント工数: 元wave Codex subprocess 10 session。今回のmain統合は親が競合裁定・docs再採番・
  commit・受入・local main着地を担当。push/remote操作は行わない

### 次の一手

- [T-187] **完了 (本エントリ、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **P1・着手可 ((64))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・着手可 ((64))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する。**T-180 は分類なしの機械的 retry 上限までを実装し、
  失敗型分類・safety-filter 判定・回復経路を本 ID へ送った**
- [T-184] **P1・T-181〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する。
  **DW-O01 の結線と stage 別上限値は本 ID の所有** (T-180 は機構のみ)
- [T-186] **P3・T-180 が返した裁定パッケージ**: manifest の seal ceremony と foreign entry
  後追記の検出、`setsid()` 脱出子の完全封じ込め (cgroup / bwrap)、
  stdout / artifact bytes の上限 (`max_artifact_bytes`) の 3 件
- [T-179] **完了 ((64)、`72f8858`)**
- [T-185] **P3・RuleOps hardening ((63) R3R-1)**: receipt range の commit 数と
  path-union stdout bytes/cardinality を streaming 上限で fail-closed にし、安定 reason と
  over-limit synthetic negative を追加する
- [T-139] **完了 ((60))**
- [T-142] **close ((62) のユーザー再裁定)**: formal selector と live campaign が
  揃った場合のみ新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 ((63)、D99)**
- [T-126] **裁定済み ((62) = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列で live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172 の drift 拒否検査を事後検証する
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**
## 2026-07-30 (67) — [T-146] capability probe cleanup fault path を閉鎖 — partial bind / FNF / no-op / preexisting を直接観測 (コード + docs、branch codex/dev-wave-t146-probe-cleanup、計測 = 本worktree・ログインノード + Pegasus計算ノード)

- T-146を9段dev-waveで実装。production `tools/dev_waves/`、isolation meta-test、
  product artifactはno-touchとし、`orchestrator/tests/test_dev_waves_integration.py` 1枚で閉じた
- 段2 plan v1は段3のownership / acceptance 2レンズでNO-GO。preexisting entryを
  capability `False`へ潰さないこと、recovery前のpathname直接観測、exception種別と
  pathname状態の分離をplan v2へ採用した
- 段6の初回review 2本もNO-GO。path-absent bind failureで不要な`getsockname()`を呼ぶ退行と、
  cleanup変異が等価になるfixtureをfixし、focused再reviewは実装blocker 0でGO
- helperはliteral `.s` と既存の `socket → bind → chmod → stat → listen` を維持。
  partial bindはbound addressで所有を確認して回収し、cleanup FNFは不在再確認時だけ受理、
  非FNFは元例外を送出、unlink成功後の不在もpostconditionとして固定した
- preexisting regular file / broken symlinkは`FileExistsError`、identity保存、socket非生成を直接固定。
  hostile writer、close複合fault、production partial-bind一般化はsingle-writer test helperの
  独立再現を越えるためscope外のまま
- 実装commit `5b65072`、並行main統合merge `df546fc`。変異本走は統合commit後に行い、
  M-T146-A〜C **3/3 KILLED**、unexpected node 0、SKIP 0、各復元後にHEAD blob一致を確認
- pre-fix controlは6 failed / 4 passed。旧穴3種類4 node、regression guard 4項目、
  identity再固定＋新policy 2 nodeを分離し、全parameterを旧欠陥数として数えていない
- 受入実測: focused 11 passed、関連2 test fileは変異前後とも92 passed、復元後control 10 passed。
  並行main統合・記録前の全走は3683 passed / 18 skipped / rc=0 / 239.72秒。
  記録commit後は関連92 passed / 84.16秒、全走3683 passed / 18 skipped / rc=0 / 237.57秒。
  `check_docs` / `check_codex_agents` green、provenanceは実装後501件・merge後530件・
  記録後531件で違反なし
- 構造化記録=`output/insights/2026-07-29_t146-probe-cleanup.md` と同
  `-wave/`。D88 exact-literal再帰走査はhit 0、逐語defang / erratumなし
- 段8自己改善: worker逐語の末尾空白と`git diff --check`の衝突を実測したため、
  原文hash・byte数・復元方法を併記する可逆最小正規化を`DW-S07`へ明記。防壁・段構成は不変
- 段9再開: landed済みT-179が(64)を使用したためD70どおり本エントリを(64)→(65)へ振り直し、
  `main` `7be05ef`を統合。統合後102KBとなったworklogは(49)〜(60)をarchiveへ移動した
- 段9再開2: forward-only是正 `c9c3de5` を統合し、provenance欠落を履歴非改変で解消。
  landed順を反映して本エントリを(65)→(66)へ再採番し、(49)〜(60) archiveは内容同一の
  包括archive (49)〜(64)へ置換した
- 段9再開3: local main `ff82133` のT-180 / T-187完了系列を統合し、D70のland順に合わせて
  本エントリを(66)→(67)へ再採番した。再受入はユーザー指示に従いPegasus計算ノードで行う
- エージェント工数: Codex subprocess 8 (plan 1、敵対相談 2、author 1、review 2、fix 1、
  focused review 1)。親=brief・裁定・統合・変異・全走・docs・commit

### 次の一手

- [T-187] **完了 ((66)、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **P1・着手可 ((64))**: critical stage を維持し、第二レンズ 1 箇所だけ軽量 model を
  shadow 比較する
- [T-183] **P1・着手可 ((64))**: F43/F45 型の断片出力 / safety-filter 終了を早期分類し、
  retry 上限と fail-closed 回復を固定する。**T-180 は分類なしの機械的 retry 上限までを実装し、
  失敗型分類・safety-filter 判定・回復経路を本 ID へ送った**
- [T-184] **P1・T-181〜T-183 後 ((61))**: 比較済み証拠だけで stage 別
  model/reasoning/resource/retry policy を採用し、rollback と drift 検査を追加する。
  **DW-O01 の結線と stage 別上限値は本 ID の所有** (T-180 は機構のみ)
- [T-186] **P3・T-180 が返した裁定パッケージ**: manifest の seal ceremony と foreign entry
  後追記の検出、`setsid()` 脱出子の完全封じ込め (cgroup / bwrap)、
  stdout / artifact bytes の上限 (`max_artifact_bytes`) の 3 件
- [T-179] **完了 ((64)、`72f8858`)**
- [T-185] **P3・RuleOps hardening ((63) R3R-1)**: receipt range の commit 数と
  path-union stdout bytes/cardinality を streaming 上限で fail-closed にし、安定 reason と
  over-limit synthetic negative を追加する
- [T-139] **完了 ((60))**
- [T-142] **close ((62) のユーザー再裁定)**: formal selector と live campaign が
  揃った場合のみ新タスクとして再起票
- [T-136] 同上
- [T-129] 同上
- [T-149] 同上
- [T-152] 同上
- [T-153] **完了 ((60))**
- [T-158] 同上
- [T-141] 同上
- [T-143] **完了 ((63)、D99)**
- [T-126] **裁定済み ((62) = qualification-first amendment) → 実施待ち**: headline
  昇格不能な専用系列で live control と機械 receipt を先行し、production gate は別 wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172 の drift 拒否検査を事後検証する
- [T-145] 同上
- [T-146] **完了 (本エントリ)**
- [T-134] **裁定済み・実施待ち ((62))**
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
- [T-151] **P3・裁定済み ((60))**
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
- [T-172] **完了 ((60))**
- [T-173] **P3 ((60))**
- [T-174] **P3・裁定要 ((60))**
- [T-175] **P3・裁定要 ((60))**
- [T-176] **P3・backlog ((60))**
- [T-177] **P3・裁定要 ((60))**
