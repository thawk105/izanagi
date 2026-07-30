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

## 2026-07-30 (67) — [T-188] Claude / Codex dev-wave の並行 session land を直列化 — 所有権付き制御面 + tested SHA + common lock (コード + docs、branch codex/dev-wave-skill、検査 = Pegasus gen_S 計算ノード)

- ユーザー要求「`dev-wave a1` / `a2` の並行開発で、他 session の作業ファイルが最終 main
  取り込みを妨げない」を 9 段 dev-wave で実装。Claude command と Codex Skill は共通
  `DW-O23` / `tools/dev_wave_land.py` を使い、schema-valid handoff と Git admin に双方向登録された
  worktree container だけを非接触例外にする。設計正本=D102、失敗台帳=F55
- 段 2 plan 1、段 3 review 2、段 5 author 1、段 6 review 2 + fix / focused review 3 巡。
  ignored container、lock 前 race、effective config poison、gitlink cleanup、同一 base 二 wave の
  実 subprocess 受入を閉鎖。fix 上限後に残った synthetic command false-positive は living route
  非到達かつ exact topology gate が独立するため backlog と裁定。逐語・裁定 =
  `output/insights/2026-07-29_dev-wave-parallel-land/`
- 実装 `43c4ec4`、mutation 台帳 `16e418b`、main 同期 `08adb89`、記録 `c63a005`、
  resync 停止記録 `59c9484..c0ed6b9`、最新 main `ff82133` の統合 `81be71c`。
  main の別 session 所有 handoff / worktree は削除・stash・commit・上書きしていない
- M1〜M13 は **13/13 KILLED**、SURVIVED 0、復元失敗 0。各 mutation は exact anchor、
  期待 node red、source byte 復元を固定。M13 の再照準と事後性は台帳の erratum に残した
- 2 回の段 9 resync 監査は最初に provenance 欠落と ledger 4件、次に残余2件で NO-GO。
  provenance と token 集計は main 側 T-180 / T-187 で閉鎖。残余2件は実在するが本 wave の
  consumer 閉包外とするユーザー再裁定後だけ、固定 SHA の再同期を継続した
- ログインノードで全走が 2 回 OOM kill され、`/dev/shm` 約15.4 GiB残留と16 GiB cgroupを実測。
  再開後はビルド・テストをログインノードで行わず、Pegasus `gen_S` 計算ノードの `/scr` と
  bounded xdist を使った。resume startup job `874084.nqsv` は48 core / 124 GiB / Python 3.10.12で緑
- 再開managerの初回記録は worklog の挿入位置と T-187 sink を誤り、計算node job
  `874094` / `874099` の D70 gate が各 1 件赤で全走前停止。`874100` は PBS job ID の `:` を
  `TMPDIR` に残して path を分断し、3901 passed / 19 skipped / 41 failed。製品差分を変えず
  entry末尾化・sink保存・job ID正規化で原因を閉じ、赤を受入扱いしていない
- 最終受入は Pegasus job `874116.nqsv` / `bnode112` の32 workerで、関連312 passed、
  repository全走 **3942 passed / 19 skipped** (209.86秒)。`check_docs` / `check_codex_agents` /
  py_compile / staged diff checkは緑、full-history provenanceは549件・違反なし
- campaign の raw 受理集合、certified 選択、proof chain は不変。変更は監査済み開発 commit の
  local-main 反映契約だけ。push と remote branch 操作は人間境界を維持
- エージェント工数: Codex subprocess 14 (plan 1、敵対相談 2、author 1、review 2、
  fix 3、focused review 3、main resync audit 2)。親 = brief・裁定・統合・変異・記録・受入・land

### 次の一手

- [T-188] **完了 (本エントリ、D102、F55)**
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

## 2026-07-30 (68) — [T-182] model routing の限定 shadow pilot を実走し、専用ツールは実装しないと裁定 (docs のみ、branch worktree-dev-wave-t182-model-routing、計測 = 本 worktree・ログインノード、live inference は段 2/3 の codex arm のみ)

- **本 wave に実装差分はない。** 段 4 で「実装しない」と裁定し `4→7→8→9` を辿った。したがって
  変異 matrix と実装面の受入全走は本 wave の射程外である (`DW-S04`)
- 段 3 の敵対相談レンズ B (gate 実効性) を**同一の prompt file** で 3 arm へ投入した。
  `codex_worker_ledger.py` が 3 arm すべてに `prompt_hash=02f8f550583d…` を記録し、
  同一凍結入力であることの機械証拠になった。sol arm は従来どおり authoritative で、
  shadow 2 本は置換ではなく**追加**。production 既定は 1 byte も変えていない
- **結果 (射程つき)**: `gpt-5.6-luna` @ max は authoritative sol @ max の所見 11 件のうち
  **10 件 (91%) を誤検出 0 で再現**し CLI reported token を **31.6% 減**、wall −35.6%。
  `gpt-5.4-mini` @ xhigh は **5 件 (45%)** のみ再現、token −26.8%、**wall +39.0%**。
  誤検出は両 arm とも 0
- **shadow-only の所見が 2 件出た**。luna の「段 3 B のみへ縮小し receipt qualification と
  名乗るべき」は authoritative arm が出さなかったが、独立した別 sol run (レンズ A) が同じ結論に
  到達しており real。軽量 arm が authoritative arm の見落としを拾った実例
- **この被覆率を policy 根拠にしてはならない**。基準集合が authoritative arm 自身で循環し、
  非盲検で、label を shadow 実行**前**に事前登録していない (親の手順上の実欠陥、レンズ A が
  事前に指摘したとおり)。n=1、3 arm 同時起動、同時 codex 実行数 22 (並行 5 wave) で交絡もある。
  wall-clock は model 差の証拠に使えない
- **段 1 の実測を段 3 が自己反証した**。段 1 の trivial probe (820 行のファイルを読んで 3 問に
  答える) では luna 30,262 / sol 34,289 token・wall 70s 対 49s で、親は brief に
  「luna も terra も sol より軽くない」と書いた。段 3 の実レンズ課題では luna が sol より
  31.6% 少ない token で完了し、この一般化は成立しなかった。brief の当該記述は撤回する
- **実測で判明した fail-open 4 件** (F56 として台帳化、一次資料は insight)。(a) 未サポート model
  (`gpt-5.4-nano` / `gpt-5.1-codex-mini`) は rollout に「消費 0 の session」を残し receipt の
  model は要求 slug のままで、素朴な pilot は「軽量 model は finding 0 件」と誤記録できる。
  (b) 不正な `reasoning=ultra` は sol / luna / terra で **rc=0 のまま成功**し receipt に残る。
  (c) receipt の model は要求 slug であり、400 応答だけが実体名を露出する。
  (d) model により reasoning の受理集合が異なる (`gpt-5.4-mini` は `max` を拒否)
- **専用ツールを実装しなかった理由**: 独立 3 レンズ (段 2 planner・段 3 レンズ A・段 3 レンズ B)
  がすべて NO-GO を返し、うち 2 本が「実装せず裁定パッケージへ返す」を推奨した。決め手は
  (i) どの受入経路にも配線されず gate にならない、(ii) 閉じたい穴 (served identity の attest、
  process receipt の真正性) がツールの外にある、(iii) `docs/phase3.md` [T-182] はツールではなく
  証拠を要求しており段 3 の実走で充足済み、の 3 点
- wave path は段 2・段 3 を省略せず実行した。実装面が無いため Codex `role=author` は起動していない
- **段 9 で F55 型の誤りを自分でも踏んだ**。初回の段 9 判定で、別 session 所有の schema-valid
  handoff と `.codex/worktrees/` を「main が clean でない」と読み、先行 land による main 前進も
  停止条件として扱って取り込みを止めた。その後 main に land した F55 / D102 / `DW-O23` /
  `tools/dev_wave_land.py` が同型を恒久対応済みであり、本 wave は再開して新 main を固定 SHA で
  wave へ merge し、受入を再走して land 経路へ載せた
- **番号の振り直し (D70)**: 本エントリは当初 (65) として書いたが、並行 land で (65)〜(67) が
  使用済みとなったため (68) へ、新規 ID は T-186 → **T-189** へ、失敗型は F55 → **F56** へ
  振り直した。当初の worklog ローテーション ((49)〜(52)) は main 側の (49)〜(58) に含まれるため破棄した
- エージェント工数: Codex 5 session (plan 1 / consult 2 / shadow 2)。親 = brief・裁定・実走・
  採点・docs・記録・main 再同期

### 次の一手

- [T-189] **P1・T-181 land 後 ((68))**: model routing の**妥当な**比較実験を設計する。
  独立 oracle、held-out 複数 task、block randomization、cache 条件分離、価格 version、
  盲検裁定、事前非劣性 margin。T-182 の pilot は n=1・非盲検・後付け採点のため根拠にしない
- [T-188] **完了 ((67)、D102、F55)**
- [T-187] **完了 ((66)、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **完了 (本エントリ、実装差分なし)**: 段 3 レンズ B を同一凍結入力で sol / luna / mini の
  3 arm へ投入し、被覆・誤検出・token/wall と receipt を凍結した。専用ツールは独立 3 レンズの
  NO-GO を受けて実装しない裁定
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

## 2026-07-30 (69) — [T-146] capability probe cleanup fault path を閉鎖 — partial bind / FNF / no-op / preexisting を直接観測 (コード + docs、branch codex/dev-wave-t146-probe-cleanup、計測 = 本worktree・ログインノード + Pegasus計算ノード)

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
  本エントリを(66)→(67)へ再採番。統合mergeは`f2c29ba`
- merge前preflight `874111.nqsv`はincoming mainの凍結逐語にある既知trailing whitespaceを
  検出したが、scriptの`set -e`欠落で後続greenがrc=0を上書きしたため不採用。F37同型再発として
  台帳へ追記し、手動解消したworklogだけをdiff-checkするfail-fast再走`874113.nqsv`をgreenにした
- ユーザー指示に従いmerge後受入をPegasus計算ノード2台・各32 pytest workerで並列実行。
  full `874117.nqsv`=`bnode114`は**3900 passed / 19 skipped / 214.99秒**、
  focused `874118.nqsv`=`bnode117`は**390 passed / 23.22秒**。startup resume gate、
  `check_docs`、`check_codex_agents`、`main..HEAD` diff-check、full-history provenance
  **549件・違反なし**もgreen。PBS会計痕跡と両job rc=0を確認した。記録commit後再走
  `874123.nqsv`=`bnode083`も134 passed、同checks green、full-history provenance
  **550件・違反なし**、rc=0
- 段9再開4: landed済みT-188が(67)を使用したため本エントリを(68)へ再採番し、local main
  `72e3800`をmerge `b222885`で統合。commit前`874196.nqsv`は274 passedと必須checksがgreen。
  merge後は全走`874201.nqsv`=`bnode065`が**3951 passed / 19 skipped / 275.53秒**、
  focused`874202.nqsv`=`bnode067`が**274 passed / 22.76秒**。startup、docs、Codex agent、
  diff-check、full-history provenance **559件・違反なし**、両rc=0、PBS会計痕跡を確認した
- 段9再開5: 受入中にT-182がlandしてlocal mainを`e7295c0`へ前進させ、`DW-O23`は
  `stale-main`で非変更停止した。fresh contextでそのdocs-only 3 commitを監査し、固定SHA
  `e7295c0`をwave側へ再統合。T-182の(68) / T-189 / F56を権威として本エントリを(69)へ再採番した
- 統合mergeは`e3216c6`。merge前`874249.nqsv`=`bnode068`は432 passed / 23.04秒と
  message provenance / docs / Codex agent / staged diff-checkがgreen。merge後は
  全走`874252.nqsv`=`bnode105`が**3951 passed / 19 skipped / 222.18秒**、
  focused`874253.nqsv`=`bnode106`が**432 passed / 23.46秒**。startup、docs、Codex agent、
  diff-check、full-history provenance **564件・違反なし**、全3 job rc=0、PBS会計痕跡を確認した
- エージェント工数: Codex subprocess 8 (plan 1、敵対相談 2、author 1、review 2、fix 1、
  focused review 1)。段9再開5の追加Codex subprocess 0、PBS job 3。親=brief・裁定・統合・変異・
  全走・docs・commit・land

### 次の一手

- [T-189] **P1・T-181 land 後 ((68))**: model routing の**妥当な**比較実験を設計する。
  独立 oracle、held-out 複数 task、block randomization、cache 条件分離、価格 version、
  盲検裁定、事前非劣性 margin。T-182 の pilot は n=1・非盲検・後付け採点のため根拠にしない
- [T-188] **完了 ((67)、D102、F55)**
- [T-187] **完了 ((66)、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **完了 ((68)、実装差分なし)**: 段 3 レンズ B を同一凍結入力で sol / luna / mini の
  3 arm へ投入し、被覆・誤検出・token/wall と receipt を凍結した。専用ツールは独立 3 レンズの
  NO-GO を受けて実装しない裁定
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

## 2026-07-30 (70) — [T-145] long-path serve shutdown testをlatest mainへ安全に統合 (test + docs、branch codex/dev-wave-t145-final、検査 = Pegasus gen_S計算ノード)

- 段1〜8の実装・変異・敵対reviewは不変。`thread.join(120)`のwall-clock合否を、
  実listener / SignalRelay FD、real long-path exchange、shutdown / release / serve returnの
  ordered observationと、`INFRA_TIMEOUT / NOT_EVIDENCE`へ倒す外部child containmentへ置換した
- mutationはM1/M5 **2/2 KILLED**、M2〜M4/M6 **4/4 diagnostic KILLED**。
  T-136 preservation PM1〜PM4v2も**4/4 KILLED**で元台帳と同一node・reason/state署名。
  production bytesとcampaignのraw受理集合 / certified選択 / proof chainは不変
- 実装commit `64ddf5c`、変異・保存台帳`c0659c7`、初回記録`e08e3e2`。
  段9でlatest main `43584d1`を固定SHAでmergeし、T-146のcleanup fault testとT-145の
  long-path shutdown harnessを両方保持した。統合mergeは`d5825c5`
- merge前request `874264` / bnode016はfocused **443 passed**、docs / Codex agent /
  diff / index・status安定がgreenだったが、commit message provenanceだけがredだったため
  受入に数えなかった。既存T-145/T-146 author帰属を明記した再走`874265`はgreen
- merge後受入request `874267` / bnode016は全走 **3965 passed / 19 skipped / 226.23秒**、
  focused **443 passed / 24.07秒**。startup resume、`check_docs`、`check_codex_agents`、
  `main..HEAD` diff-check、full-history provenance **573件・違反0**、tree / HEAD / main /
  ancestry安定を含む11項目がすべてgreen、PBS会計痕跡とrc=0を確認した
- 先行の32-worker全走2回はT-180 launcher normal fakeの異なるnodeが各1件赤となり、
  受入扱いにしていない。各失敗node単独1/1、同file直列58/58、旧treeの16-worker全走
  3956 passed / 19 skipped、latest統合treeの16-worker全走3965 passed / 19 skippedを分離。
  原因断定はせずF57へ記録し、失敗artifact保存とfixture hardeningを[T-190]へ送った
- landed順を反映してT-182の(68) / F56 / T-189とT-146の(69)を保持し、本記録を(70) /
  F57 / T-190へ採番。push / remote branch操作は行わず、local main取り込みはDW-O23だけを使う
- エージェント工数: 段1〜8のCodex subprocess 12 (plan 1、相談 2、author/fix 3、review 5、
  初回author 1)。段9再開の追加subprocess 0。親=最新main統合・競合裁定・計算ノード受入・
  フレーク分離・記録・land

### 次の一手

- [T-189] **P1・T-181 land 後 ((68))**: model routing の**妥当な**比較実験を設計する。
  独立 oracle、held-out 複数 task、block randomization、cache 条件分離、価格 version、
  盲検裁定、事前非劣性 margin。T-182 の pilot は n=1・非盲検・後付け採点のため根拠にしない
- [T-190] **P2・新規 ((70)、F57)**: launcher normal fakeの32-worker負荷フレークを
  失敗artifact保存つきで原因分離し、production gateを緩めずfixtureをhardenする
- [T-188] **完了 ((67)、D102、F55)**
- [T-187] **完了 ((66)、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **完了 ((68)、実装差分なし)**: 段 3 レンズ B を同一凍結入力で sol / luna / mini の
  3 arm へ投入し、被覆・誤検出・token/wall と receipt を凍結した。専用ツールは独立 3 レンズの
  NO-GO を受けて実装しない裁定
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
- [T-145] **完了 (本エントリ、`64ddf5c` + merge `d5825c5`)**
- [T-146] **完了 ((69))**
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

## 2026-07-30 (71) — [T-191] Pegasus で重い処理を計算ノードへ強制し最大並列にする (コード + docs、branch worktree-dev-wave-pegasus-compute-node、受入 = Pegasus gen_S 計算ノード request `874299`)

- ユーザー裁定 (逐語 2 件): 「hostname が pegasus なら、ビルドやテストなど負荷のかかる処理は全て
  計算ノードで」「計算ノードのリソースを最大限使って最大限並列で」。runbook §7 の 2026-07-27 裁定
  (ログインノードで可) の**再反転**であり、こちらが現行。正本 = D103、runbook §7/§8、AGENTS.md
- **branch の `T-188` / `D102` は main 側の先行採番と衝突**したため記録を `T-191` / `D103` へ
  振り直した。commit `a34266d` の件名は履歴非改変のため元番号 (`T-188`) を保持する
- DW-G01 の生死確認を先行 (request `874129`): 計算ノードで pytest 全走が成立し、`~/.local` の
  xdist が network 不可でも見えることを実測。**この probe が無ければ dispatcher の前提は
  ログインノード実測の一般化 (F46 同型) だった**
- 段 3 敵対相談 2 本が S4 を blocking 判定。`jobs` は cache identity には入らないが `build_argv` →
  floor manifest → ratified `floor_source` へ流入するため、**`buildcache` の `-j` 既定 16 は変えない**
  (cache hit で架空値を記録すると provenance を偽る)。build は実行場所だけ計算ノードへ強制した
- **ユーザー再裁定 (同日) により build 並列度も site 由来にした**。「16 並列と 48 並列の
  バイナリは等価であるべきで、そうでなければコンパイラのバグであり我々の問題ではない」との
  裁定で cache hit 時の `-j` 記録差を受理し、`buildcache` の `jobs` 既定を `None` →
  `site_policy.default_build_jobs()` にした (`98427aa`)。cache identity・`bin_sha256` 照合・
  trace diff・`src_token` 再照合は緩めていない。事前登録変異 **M15** を追加し KILLED を確認
- 段 6 敵対レビュー 2 本が共に NO-GO (must-fix 11 + 7)。会計照合の一単語 OR による偽陽性、
  F49(a) の自己確認、qsub parse 失敗時の孤児、qstat 瞬断での恒久ラッチが real。fix 3 巡で閉鎖
- **親の実走 (dogfood) が静的レビューで出ない 2 件を掴んだ**。(a) `qstat -f <終了 ID>` は
  `does not exist` を **rc=0** で返すため状態機械が END を認識せず 35 分空回りし子の緑を rc=16 に
  潰す。(b) PBS job name を付けた結果 `.o`/`.e` 実名が変わり収集が失敗する。両方 fix 済み
- 焦点再レビューで FA-9 が **regressed**: 「qstat 失敗ではラッチしない」は過剰補正で、実 F47 の
  signature は `Not permitted` の非ゼロ応答だった。権限系 = ラッチ / 一時系 = 再試行のみ /
  成功かつ不在 = ラッチ の 3 分類へ直した
- 保証の言い方を狭めた。敵対監査は 47 経路中 hook で止まるのは 13 件と算定。script 越し・
  変数展開・`python3 -c`・Codex 子 (hook 未配線)・端末・IDE・cron は**機械保証しない**と明記
- 受入: 計算ノードで **4012 passed / 19 skipped / 205.12s**、dispatcher rc=0。skip 19 の内訳は
  template patch 未適用 4 / g++-13 系 6 / Codex runtime 4 / gnuplot 1 / real-build canary 3 /
  Silo sample 1。**g++-13 は計算ノードにも無く、移設で C++ 検出力は増えない**
- 変異 **7/7 KILLED** (M1〜M4, M11, M13, **M15**)、SURVIVED 0、復元失敗 0。赤 node 名は各 job の `.o` から
  取得。M5/M7/M11 は当初 mask されており、両層変異・3 層分割・configure/build 独立 gate へ再照準
- 逐語検査 (D88): insights 25 ファイルへ placeholder 検出を機械実行し hit 2 件。いずれも
  `rg TODO .` の検査コマンド例と `bnodeXXX` の hostname 表記であり defang 不要と裁定
- **段 9 は停止**。main が wave 開始基準 `ff82133` から `c810ee2` まで進み、`tools/dev_wave_land.py`
  (DW-O23) を含む land 直列化契約が入ったため `--ff-only` 不能。rebase / force / 他 session 差分の
  巻き込みはしない
- **並行実装の重複あり**: 別 session (`dev-wave-improve`) が `tools/pegasus/test_dispatch.py` /
  `submit_tests.py` / `run_tests_job.sh` を同時に実装中である。統合前に**どちらを正本にするかの
  ユーザー裁定が必要**
- 正本は D103、`output/insights/2026-07-30_pegasus-compute-node-dispatch/` (逐語 25 件 + 変異台帳)
- エージェント工数: Codex subprocess 11 session (plan 1 / 敵対相談 2 / 実装 4 / fix 3 + 再 fix 1 /
  レビュー 2 / 焦点 1 のうち並列)。親は brief・裁定・統合・受入・変異・記録を担当。push は行わない


### 次の一手

- [T-191] **完了 (本エントリ、D103)**: Pegasus の重い処理を計算ノードへ強制し、テストの既定並列度を
  affinity 全数にした。段 9 は main 分岐により停止 (下記 T-192)
- [T-192] **P1・ユーザー裁定要**: 本 wave の branch を最新 main へ統合する経路を決める。
  main の `tools/dev_wave_land.py` (DW-O23) を使うか、現行 main から fresh 統合 worktree を作るか。
  併せて `dev-wave-improve` の `tools/pegasus/test_dispatch.py` 系との**重複をどちらの正本に寄せるか**
  を裁定する
- [T-193] **P2・backlog**: dispatcher が子の pytest 出力を親 stdout へ中継しない。失敗時に
  `.o` を開かないと赤の node が分からない。receipt には収集済み tail が入っているので中継は小改修
- [T-194] **P2・backlog (裁定パッケージ)**: `buildcache` の campaign build を site 由来並列にする。
  v2 completion manifest へ actual build argv を足す schema 変更 (+ pin 閉包・consumer 改修) が前提
- [T-195] **P3・backlog (裁定パッケージ)**: `silo_ladder_rung1.py` の直接 cmake と
  `t152_write_intent_coverage.py` (`DEFAULT_JOBS=MAX_JOBS=8`、成果物へ `host_role: login-node`) の
  扱い。本 wave では scope 外にした
- [T-196] **P3・backlog (裁定パッケージ)**: `tools/pegasus/exec_calibrate.py` が JSON の任意 argv を
  `os.execv` する汎用トランポリンである点。sanctioned exact path 列挙で当面は塞いだ
- [T-197] **P3・backlog (裁定パッケージ)**: SIGKILL / OOM / ホスト切断に対する scheduler-side lease と
  heartbeat。現行は SIGINT / SIGTERM / 例外の qdel best-effort まで
- [T-198] **P3・backlog**: dev-wave 改善候補 3 件 — (a) 親が書ける「実装面」の境界 (DW-G01 の
  生死 driver と親の変異 harness) を reference 節へ 1 行で明示、(b) DW-S01 の brief 10〜30 行が
  条件 dispatch 20 件の wave では守れない点の整理、(c) runbook に裁定の反転履歴が積む形を
  worklog / decisions 側へ寄せる。**main の dev-wave 正本が本 wave 中に変わったため、stale な
  branch 側 reference は編集せず候補として繰り越した**
- [T-189] **P1・T-181 land 後 ((68))**: model routing の**妥当な**比較実験を設計する。
  独立 oracle、held-out 複数 task、block randomization、cache 条件分離、価格 version、
  盲検裁定、事前非劣性 margin。T-182 の pilot は n=1・非盲検・後付け採点のため根拠にしない
- [T-190] **P2・新規 ((70)、F57)**: launcher normal fakeの32-worker負荷フレークを
  失敗artifact保存つきで原因分離し、production gateを緩めずfixtureをhardenする
- [T-188] **完了 ((67)、D102、F55)**
- [T-187] **完了 ((66)、D101)**
- [T-180] **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と
  fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave manifest により
  cwd 部分一致に依存しない受理集合を作り、ledger の `--manifest` で T-179 の凍結値を再現した
- [T-181] **P1・着手可 ((64))**: focused review の reasoning `max` 対 `high` を凍結入力で限定比較する
- [T-182] **完了 ((68)、実装差分なし)**: 段 3 レンズ B を同一凍結入力で sol / luna / mini の
  3 arm へ投入し、被覆・誤検出・token/wall と receipt を凍結した。専用ツールは独立 3 レンズの
  NO-GO を受けて実装しない裁定
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
- [T-145] **完了 (本エントリ、`64ddf5c` + merge `d5825c5`)**
- [T-146] **完了 ((69))**
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
