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

## 2026-07-30 (71) — [T-191] Codex cleanup-branches Skill を明示起動専用の安全 adapter として移植 (コード + docs、branch codex/dev-wave-cleanup-branches-skill-t188、計測 = Pegasus 計算ノード)

- `.agents/skills/cleanup-branches/` に、Claude commandを共通dispatcherとして再利用する薄いSkillと
  UI metadataを追加した。明示起動専用、main / primary無条件保持、foreign / lockedのinventory限定、
  破壊直前のeligibility再評価、real prune・権限拡大・push禁止へ安全側に縮退する。
  **本waveではbranch / worktreeの実掃除を行っていない**
- checkerはSkill / commandのwhole-file SHA-256、2 file閉包、exact interfaceを独立pinと負例で固定。
  plan 1、敵対相談2、敵対review2、fix / focus 3巡を行い、最終reviewはGO・blocker 0。
  詳細・逐語・裁定は
  `output/insights/2026-07-30_t188-codex-cleanup-branches-skill-wave/`
- 実装patchは`b5f0460`、初回記録は`24dec31`、記録後受入は`15af7cd`。
  T-188 land後の同期は`401bdeb`、受入記録は`d80ab4b`
- 初回全走は3951 passed / 19 skipped。共有bytecode cacheを使ったmutation job `874224`は
  same-size変異のstale bytecodeを検出して全結果を無効化し、cache namespaceを分離した
  `874229`でunion mutation 19/19 KILLED、復元後focused 197 passed、全履歴provenance
  554件・違反なしを取り直した
- mainがT-182 / T-146を先にlandしたため、旧T-189 / worklog (68)を候補T-190 / (70)へ
  振り直した。固定main `43584d1`との59 path和集合を独立監査し、worklog誤挿入だけを
  内容不変で是正した再監査はGO・指摘0。Pegasus `874276.nqsv`はrepository全走
  3960 passed / 19 skipped / 214.79秒、rc=0
- focused初回 `874277.nqsv` は全走との同時`git write-tree`が共有index lockを競合したため
  受入証拠に使わない。単独再走 `874280.nqsv` は関連286 passed後、merge中を意図どおり拒否する
  startup gateで停止した。startupはmerge前にgreenだった
- その記録追補直後にT-145が先行landし、current mainは`c810ee2`へ前進して(70) / T-190 /
  F57を権威として使用した。同contextではcommitせずfail-closed停止。fresh contextで旧mergeの
  exact stateを照合してabortし、Pegasus startup `874284.nqsv`をgreenにしてから固定main
  `c810ee2`を再統合し、本cleanupをD70により(71) / T-191へ再採番した
- 固定tree `5cf3ee8`の独立監査は和集合85 path、全parent差分積docs 3 path、
  T-145 / T-146 / T-188 / cleanupの検出面、D70、pointer、digestをgreenとしたが、
  worklog 104,576 bytes > 100,000 bytesの1件だけNO-GO。entry (59)〜(67)を
  `docs/archive/worklog-phase3-0729-59-0730-67.md`へ内容不変で移動し、現行は
  並行land文脈の(68)〜(71)を保持した
- rotation後tree `7402431`の独立再監査はGO・指摘0。archive / 現行の重複・欠落なし、
  (58)→(59)と(67)→(68)を含むD70全遷移、worklog 39,259 bytes、全検出面をgreenとした。
  Pegasus pre-commit `874292.nqsv` (bnode016) はrepository全走
  3974 passed / 19 skipped / 211.02秒、check_docs / check_codex_agents /
  message provenance / py_compile / Skill validator / diff・tree安定がgreen、rc=0
- エージェント工数: Codex subprocess 20 session
  (plan 1 / consult 2 / author 2 / review・focus 5 / fix 3 / forward test 2 /
  独立merge監査5)。親 = brief・裁定・統合・変異・受入・docs・記録

### 次の一手

- [T-191] **完了 (本エントリ、実装 `b5f0460`、記録 `d80ab4b`)**
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
  昇格不能な専用系列で live control と機械 receipt を先行し、production gateは別wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172のdrift拒否検査を事後検証する
- [T-145] **完了 ((70)、`64ddf5c` + merge `d5825c5`)**
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

## 2026-07-30 (72) — [T-192] Pegasus で重い処理を計算ノードへ強制し最大並列にする (コード + docs、branch worktree-dev-wave-pegasus-compute-node、受入 = Pegasus gen_S 計算ノード request `874299`)

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
- **段 9**: main が wave 中に 2 回前進 (`ff82133` → `c810ee2` → `e02fccf`) したため、rebase / force を
  使わず固定 SHA の wave-side merge を 2 回行い、そのたびに計算ノードで全走し直した
  (4089 → 4098 passed)。ID も 2 回振り直した (`T-188`/`D102`/(71) → `T-191` → `T-192`/`D103`/(72))
- **land は sanctioned `tools/dev_wave_land.py` が 12 回連続 rc=20 で拒否**。理由は最後まで
  未追跡 1 path のみ = 並行セッションの成果物 `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md`。
  ユーザーが非接触を指示済みのため削除・移動・commit・ignore 追加はしない
- **一回限りの land adapter で着地**した (main の (71) が同型の先例を land 済み)。helper を import して
  lock・identity・audit closure・ff-only・collision・postcondition を**そのまま通し**、緩和は
  「main の未追跡分類から宣言 1 path を除く (ちょうど 1 件でなければ拒否)」だけ。非接触は land 前後の
  sha256 / mode / size / dev / ino / mtime / ctime の完全一致で機械証明した
  (`c132098e906682db…` 前後一致)。adapter は repo へ commit せず job tmp に置く
- **並行実装の重複は未解消**: 別 session (`dev-wave-improve`) が `tools/pegasus/test_dispatch.py` /
  `submit_tests.py` / `run_tests_job.sh` を実装中である。**どちらを正本にするかのユーザー裁定が必要**
- 正本は D103、`output/insights/2026-07-30_pegasus-compute-node-dispatch/` (逐語 25 件 + 変異台帳)
- エージェント工数: Codex subprocess 11 session (plan 1 / 敵対相談 2 / 実装 4 / fix 3 + 再 fix 1 /
  レビュー 2 / 焦点 1 のうち並列)。親は brief・裁定・統合・受入・変異・記録を担当。push は行わない



- **`/cleanup-branches` 実行 (2026-07-30)**: worktree 22 → 14、ローカル branch 24 → 15。
  ahead=0 かつ clean かつ滞在プロセスなしの 8 worktree を F26 手順 (detach → `branch -d` →
  削除 → prune) で畳み、9 branch を `-d` で削除した。滞在は `/proc/*/cwd` と cmdline の二重走査で
  実測し、稼働中 4 件 (t181・本 session・t200 locked・improve-u2) と dirty 8 件・ahead>0 の 4 件は残した。
  取り込み漏れ 1 件 = `codex/p3-autonomous-trial` (T-178 の runbook と insight が main に無い)。
  残した `codex/dev-wave-t145` (ahead=1) は、その後の照会で**内容が main に取り込み済み**と判明した
  (追加 test 2 件が main に実在、差分は main 側が新しく、branch 固有 16 行は helper の旧版)。
  完了記録は (70) の `codex/dev-wave-t145-final`。**ユーザー自身が `-D` で削除**し branch は 14 になった
  (AI は skill どおり `-d` のみを使い、`-D` は実行していない)。
  事後検査は `git submodule status` が pin `d706650` 一致・`-` prefix なし、main checkout の
  tracked dirt 0

### 次の一手

- [T-200] **P2・掃除の取り残し**: `codex/p3-autonomous-trial` (ahead=2) の
  `docs/phase3-8c-autonomous-trial-runbook.md` と
  `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` が main に無い。
  取り込むか見送るかを裁定する
- [T-201] **P3・skill 自己改善の残り**: F26 追加事象 (submodule 実体化 worktree の一括 `rm -rf` が
  timeout で半削除を残す) の運用則を `.claude/commands/cleanup-branches.md` §3 へ反映する。
  同ファイルは Codex skill との whole-file SHA-256 parity 契約下にあり、`tools/check_docs.py` の
  pin 更新と skill 側の同期が必要なため本 session では未実施
- [T-192] **完了 (本エントリ、D103)**: Pegasus の重い処理を計算ノードへ強制し、テストと build の
  既定並列度を affinity 全数にした。段 9 は一回限り adapter で local main へ ff-only 着地済み
  (main `5e095d0`)
- [T-193] **P1・ユーザー裁定要**: 並行セッション `dev-wave-improve` の
  `tools/pegasus/test_dispatch.py` / `submit_tests.py` / `run_tests_job.sh` と本 wave の
  `tools/pegasus/dispatch_compute.py` は同趣旨の実装である。**どちらを正本にするか**を裁定し、
  片方へ寄せる。併せて `tools/dev_wave_land.py` へ「宣言 path を非接触として受理する」正規経路を
  入れるか (今回は一回限り adapter で回避、main (71) も同型) を裁定する
- [T-194] **P2・backlog**: dispatcher が子の pytest 出力を親 stdout へ中継しない。失敗時に
  `.o` を開かないと赤の node が分からない。receipt には収集済み tail が入っているので中継は小改修
- [T-195] **P2・backlog (裁定パッケージ)**: `buildcache` の campaign build を site 由来並列にする。
  v2 completion manifest へ actual build argv を足す schema 変更 (+ pin 閉包・consumer 改修) が前提
- [T-196] **P3・backlog (裁定パッケージ)**: `silo_ladder_rung1.py` の直接 cmake と
  `t152_write_intent_coverage.py` (`DEFAULT_JOBS=MAX_JOBS=8`、成果物へ `host_role: login-node`) の
  扱い。本 wave では scope 外にした
- [T-197] **P3・backlog (裁定パッケージ)**: `tools/pegasus/exec_calibrate.py` が JSON の任意 argv を
  `os.execv` する汎用トランポリンである点。sanctioned exact path 列挙で当面は塞いだ
- [T-198] **P3・backlog (裁定パッケージ)**: SIGKILL / OOM / ホスト切断に対する scheduler-side lease と
  heartbeat。現行は SIGINT / SIGTERM / 例外の qdel best-effort まで
- [T-199] **P3・backlog**: dev-wave 改善候補 3 件 — (a) 親が書ける「実装面」の境界 (DW-G01 の
  生死 driver と親の変異 harness) を reference 節へ 1 行で明示、(b) DW-S01 の brief 10〜30 行が
  条件 dispatch 20 件の wave では守れない点の整理、(c) runbook に裁定の反転履歴が積む形を
  worklog / decisions 側へ寄せる。**main の dev-wave 正本が本 wave 中に変わったため、stale な
  branch 側 reference は編集せず候補として繰り越した**
- [T-191] **完了 (本エントリ、実装 `b5f0460`、記録 `d80ab4b`)**
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
  昇格不能な専用系列で live control と機械 receipt を先行し、production gateは別wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172のdrift拒否検査を事後検証する
- [T-145] **完了 ((70)、`64ddf5c` + merge `d5825c5`)**
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

## 2026-07-31 (73) — [T-200] 受入全走の下限は in-scope の施策では動かないと実測し、共有 cache 実装を破棄 (docs のみ、branch worktree-dev-wave-t200-suite-floor、受入 = Pegasus gen_S 計算ノード request `874538` / `874540`)

- ユーザー裁定 (2026-07-30): scope = 「全走の下限を下げる」。材料は
  `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` §7。正本は D104 と
  `output/insights/2026-07-30_t200-suite-floor/` (brief + 裁定 + negative result)
- **段 1 の前提実測で材料の 3 数値がいずれも現状と食い違った**。group 直列和 145.2 → 98.1〜122.6 秒、
  最長 ungrouped node 107.8 → 108.2〜110.8 秒、T-080 base 構築 **15〜22 → 84〜103 秒**。
  [T-128] が 121.7 → 22.1 秒へ縮めた同じ fixture が `output/` の tracked 増加 (3437 ファイル /
  151MB) と計測機の変更で戻っていた
- 直列 probe (`874371`) で cold/warm を分離した。receipt 解決 cold **37.76** / warm **0.09** 秒、
  t080 base cold **85.06〜103.04** / warm **0.91** 秒。全走の 45 秒帯 (走 1、14 件) と 37 秒帯
  (走 2、6 件) は実 receipt 解決 1 回のコストと一致し、**帯の位置そのものが走ごとに移動する**
- **実装は効果を示せず破棄した**。before 2 走 / after 2 走で wall は 207.5 → 206.3 秒
  (差 1.3 秒、ばらつき 13.6 秒の中)、t080 系 work と最長 node は **after 2 走とも before 2 走を
  上回って悪化**した (785.0/842.1 → 972.3/913.9 秒、110.8/108.2 → 112.1/116.0 秒)。
  after は同一ノード bnode002 の 2 走なのでノード差では説明できない
- 機序: fixture の 5 variant のうち **4 つは消費者が 1 本**で共有が効かず、最長 node は唯一の
  `distinct_basis_blob` instance なので決して warm 化しない。待ち手は `flock` で build と同じ時間
  ブロックし、待ちが duration に載る。全走の CPU 稼働率は 22% なので CPU 返却は wall へ写らない
- **真の律速を特定した**。`issue_receipt=False` variant が 10.63 秒であることから、base 構築
  90 秒のうち **約 80 秒 (89%) は子 python の migration 検証**で、148MB の copytree は約 10 秒。
  本番 `_history_touches_path` の `diff-tree --find-copies-harder` を 3437 ファイルの basis commit
  へ当てるコストであり、[T-173] と同型の構造。**テスト側では閉じられない**
- **敵対検証 4 本すべて NO-GO** (段 3 = codex `gpt-5.6-sol` reasoning=max 2 本、段 6 = Claude opus
  2 本)。段 3 は**親 brief 自身の誤り 6 件**を real と判定し、親が全件検算して確認した —
  走 2 の割当ノード未記録 (走 1 bnode010 / 走 2 bnode009 で別ノード)、convoy 帯 18 件 (正しくは
  6 件)、「LPT 下限はどの施策でも動かない」(group を下げる施策を模擬していなかった。正しくは
  走 1 で 122.6 → 110.8 秒)、「LPT 下限」の呼称 (LPT は上界推定)、差 91.7 秒の帰属、標本 2 での
  因果断定。`DW-S03` の親レンズが [T-128] に続き **2 例目**として機能した
- 攻撃が失敗し維持された主張: 「t080 はほぼ全部が重複 base 構築」(cold builder が 99.6%)、
  「group 直列和 35 対 golden 42」の不一致 (欠落 8 件は全 phase 0.005 秒未満で pytest が隠す。
  影響 0.04 秒以下)
- 段 6 は must-fix 12 件。中核の「効果が出ない」は設計変更でも in-scope で閉じられない。加えて
  共有 entry を消す経路が無く `/dev/shm` へ 1 走あたり **約 1〜1.5GB を 6 時間残す**ため、
  `conftest.py` の tmpfs 切替ガード経由で**測定計画自体を汚染する**。発火の観測手段も無い。
  規律 5 に従い 1909 行を破棄した (patch sha256 `2f71c770a71b26c5…`)
- **事前登録変異 M7 の帰属不成立を親が検算で確定**。「lock file を prune 対象へ戻す」変異は後続
  2 層に mask される (`.lock` は `ENTRY_SUFFIX` にも `STAGING_PATTERN` にも一致しない)。
  実装子の「8 変異すべて KILLED」は M7 について事実と異なる
- **副産物: main に現存する欠陥 2 件を発見**。`real_repo_receipt_memo` は (a) `--testrunuid` を
  固定して 6 時間以内に 2 回走らせると実 receipt payer が **0 回**になり、(b) `pickle.loads` を
  `isinstance` 判定より先に実行する。どちらも本 wave の変更と無関係に今日の main に在る
- 受入: after 2 = **4112 passed / 19 skipped / 207.42 秒 / rc=0** (`874540`、bnode002)。
  after 1 の赤 1 件は同一ノード単独再走で再現せず (`874539`、1 passed / 2.55 秒)、
  `DW-O18` により差分へ帰属させず **F57 の再発 (48 worker でも発生)** として台帳へ記録した
- **変異 matrix は対象差分が無いため実施していない** (`DW-S04` の「実装しない」裁定と同じ射程)
- **段 9 の追加実測が「効果なし」を更に厳しくした**。main 前進 (`a85de57`) を wave 側 merge した
  tip `b912cd5` の受入は **4098 passed / 19 skipped / 116.25 秒 / rc=0** (`874541`、bnode002)。
  同一 bnode002 の連続 3 走は 205.10 (実装あり) → 207.42 (実装あり) → **116.25 (baseline)** で、
  warm 化が支配なら単調短縮するはずが、**実装を戻した 3 走目だけ約 90 秒落ちた**。
  実装は効果ゼロではなく **wall を約 1.8 倍に悪化させていた**と読むのが素直である
- **同時に before/after の wall 比較自体が交絡していた**。同一 baseline コードの wall は
  bnode010 で 214.34 秒、bnode009 で 200.72 秒、bnode002 で 116.25 秒と**ノード間で 1.8 倍**開く。
  破棄の根拠は wall 比較ではなく、機序・duration 台帳の悪化・段 6 の must-fix・M7 の帰属不成立の
  4 点である。段 3 `REPRO-07` と段 6 `MEASURE-01` の警告が実測で裏付けられた
- **land 再試行 (2026-07-31)**: 阻害要因だった T-126 handoff の状態行が `中断` へ是正されたため
  再試行した。その間に main が `aa67805` へ前進していたので固定 SHA の wave-side merge
  (`32c0b4a`) で取り込み、受入を取り直した (request `874704`、bnode040)。赤 1 件は
  `test_manifest_is_appended_while_correlated_session_is_running` で、bnode041 単独再走は
  1 passed / 2.85 秒 (`874705`) と再現せず **F57 の 3 回目の発現**として台帳へ記録した。
  **provenance 監査はユーザー裁定 (T-205) に従い計算ノードで取り直した** — request `874708`、
  bnode043、HEAD `32c0b4a`、595 件・違反なし
- **段 9 の land は拒否され、local main へ着地していない**。`tools/dev_wave_land.py` は
  `status=rejected` / `reason=handoff state is unknown` を返した。原因は他セッション所有の
  `docs/handoff/2026-07-29-t126-sequential-stopping-resume.md` の状態行が
  `段6 NO-GO / DW-O16 有界終端` であり、`docs/handoff/README.md` が定める 3 値
  (`作業中` / `計測中` / `中断`) の外にあること。**他セッション所有物なので編集せず、
  rebase / force / adapter で迂回もしない** (`DW-O23`)。main は `a85de57`、
  wave tip は `96c9f83` (受入 green、request `874542`) のまま branch に残す
- ユーザー裁定 (2026-07-30): codex のレートリミットが近いため段 5・段 6 の子を **Claude
  サブエージェントで代替**した (D95 の Codex author 必須を本 wave 限りで免除)
- エージェント工数: codex 3 session (plan 1 + 廃棄 1 / 敵対相談 2)、Claude 3 session
  (実装 1 / レビュー 2)。親は brief・裁定・全走 4 走・帰属 probe・検算・記録を担当。push は行わない

### 次の一手

- [T-200] **完了 (本エントリ、D104、実装差分なし)**: 受入全走の下限は in-scope のテスト側施策では
  動かないと 4 走の実測で確定し、共有 cache 1909 行を破棄した。真の律速は base 構築 90 秒のうち
  約 80 秒を占める本番 `_history_touches_path` の `--find-copies-harder` 走査である
- [T-201] **P1・ユーザー裁定要 (本エントリ)**: 全走の下限を実際に下げる 4 択の裁定 —
  (a) 本番 `t080_freeze_migration._history_touches_path` の走査置換 ([T-173] と同型、
  正しさ防壁の中核に触る)、(b) `output/` の tracked bytes 削減、(c) session を跨ぐ base cache
  (stale 検出設計が必要、初回 wall には効かない)、(d) xdist の grouping / 順序化
  ([T-120] が同型を実測で棄却済み)。**(a) だけが 90 秒中 80 秒へ直接効く**
- [T-202] **P1・新規 (本エントリ)**: `real_repo_receipt_memo` に現存する 2 欠陥を閉じる。
  (a) `--testrunuid` は呼出し側が固定でき `run_tests.py` が素通しするため、同一 UID・HEAD で
  6 時間以内に 2 回走らせると実 receipt payer が 0 回になる。(b) `pickle.loads` が `isinstance`
  判定より先に実行され、subclass・field 不整合も型検査を通る。閉じ方は controller 所有の
  非再利用 nonce と closed-schema JSON
- [T-205] **P1・ユーザー裁定済み・実装待ち (本エントリ)**: **Pegasus では `check_ai_provenance.py`
  も計算ノードへ投げる**。ユーザー裁定 (2026-07-31)「cygnus は良いが pegasus は計算ノードに
  投げるべき」。本 wave は同監査をログインノード `pegasus02` で 6 回走らせた (1 回 130〜150 秒 /
  git subprocess 約 3000 本 = 合計約 15 分の共有ノード負荷)。runbook §7 の「ログインノードに
  残してよいのは編集・静的検査・docs 検査・スケジューラ操作」を親が過大解釈したもの。
  実装は (a) `tools/pegasus/dispatch_compute.py` が pytest 引数しか受けない点の一般化、
  (b) runbook §7/§8 と `AGENTS.md` の「重い処理」列挙へ provenance 監査を明記、
  (c) 可能なら `run_tests.py` と同型の fail-closed 強制。**本 wave の land 前検査は
  request `874708` として計算ノードで取り直した**
- [T-204] **P2・ユーザー裁定要 (本エントリ、段 8 の候補)**: 子 prompt が参照する絶対 path の
  実在を投入前に親が確認する義務を `DW-O02` へ 1 行足したいが、`docs/dev-wave/**` は
  hard ceiling 24000 bytes に対し 23983 bytes で余白 17 bytes しかなく入らない。予算は上げず
  (T-127 裁定)、L2 節の削除はユーザー裁定に限るため実施していない。**実測あり** — 本 wave で
  main の未追跡成果物を worktree 基準の path で渡し、reasoning=max の planner 1 本を丸ごと捨てた
- [T-203] **P2・backlog (本エントリ)**: 性能施策の一次証拠を duration にしない仕組み。
  builder と waiter が同じ duration を出すため代理にならない。同一 allocation 内の paired
  比較 (A-B / B-A) と機構の実発火回数の直接観測を受入手順へ入れる。`--durations` が 0.005 秒
  未満を隠す点も、集計器を canonical 不一致で fail-closed にして塞ぐ
- [T-192] **完了 ((72)、D103)**
- [T-193] **P1・ユーザー裁定要**: 並行セッション `dev-wave-improve` の
  `tools/pegasus/test_dispatch.py` / `submit_tests.py` / `run_tests_job.sh` と本 wave の
  `tools/pegasus/dispatch_compute.py` は同趣旨の実装である。**どちらを正本にするか**を裁定し、
  片方へ寄せる。併せて `tools/dev_wave_land.py` へ「宣言 path を非接触として受理する」正規経路を
  入れるか (今回は一回限り adapter で回避、main (71) も同型) を裁定する
- [T-194] **P2・backlog**: dispatcher が子の pytest 出力を親 stdout へ中継しない。失敗時に
  `.o` を開かないと赤の node が分からない。receipt には収集済み tail が入っているので中継は小改修
- [T-195] **P2・backlog (裁定パッケージ)**: `buildcache` の campaign build を site 由来並列にする。
  v2 completion manifest へ actual build argv を足す schema 変更 (+ pin 閉包・consumer 改修) が前提
- [T-196] **P3・backlog (裁定パッケージ)**: `silo_ladder_rung1.py` の直接 cmake と
  `t152_write_intent_coverage.py` (`DEFAULT_JOBS=MAX_JOBS=8`、成果物へ `host_role: login-node`) の
  扱い。本 wave では scope 外にした
- [T-197] **P3・backlog (裁定パッケージ)**: `tools/pegasus/exec_calibrate.py` が JSON の任意 argv を
  `os.execv` する汎用トランポリンである点。sanctioned exact path 列挙で当面は塞いだ
- [T-198] **P3・backlog (裁定パッケージ)**: SIGKILL / OOM / ホスト切断に対する scheduler-side lease と
  heartbeat。現行は SIGINT / SIGTERM / 例外の qdel best-effort まで
- [T-199] **P3・backlog**: dev-wave 改善候補 3 件 — (a) 親が書ける「実装面」の境界 (DW-G01 の
  生死 driver と親の変異 harness) を reference 節へ 1 行で明示、(b) DW-S01 の brief 10〜30 行が
  条件 dispatch 20 件の wave では守れない点の整理、(c) runbook に裁定の反転履歴が積む形を
  worklog / decisions 側へ寄せる。**main の dev-wave 正本が本 wave 中に変わったため、stale な
  branch 側 reference は編集せず候補として繰り越した**
- [T-191] **完了 (本エントリ、実装 `b5f0460`、記録 `d80ab4b`)**
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
  昇格不能な専用系列で live control と機械 receipt を先行し、production gateは別wave
- [T-059] **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**:
  事前登録不能だった逸脱を明記し、T-172のdrift拒否検査を事後検証する
- [T-145] **完了 ((70)、`64ddf5c` + merge `d5825c5`)**
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
