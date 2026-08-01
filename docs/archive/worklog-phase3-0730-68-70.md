# worklog archive — Phase 3 2026-07-30 (68)〜(70)

ローテーションで `docs/worklog.md` から移動した凍結記録 (訂正注記のみ追記可、D35)。

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
