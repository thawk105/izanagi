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
- **land を止めていた未追跡 path は commit 漏れだった (ユーザー裁定 2026-07-31)**。
  `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` は前 wave (72) が
  「並行セッションの成果物」として非接触扱いし、一回限り adapter で回避していたが、本 wave で
  所有を調べ直したところ **(a) lsof で開いているプロセスなし、(b) mtime が 2026-07-30 12:38 で
  20 時間不変、(c) git 履歴に一度も存在しない、(d) どの handoff も所有を宣言していない、
  (e) 稼働中の他セッションも PBS job も掴んでいない**ことを確認した。ファイル自身も
  「read-only の測定。実装は伴わない。次 wave の裁定材料として残す」と書いた完成成果物である。
  ユーザー裁定「誰も触ってないコミット漏れならコミットしちゃえば」に従い、
  **adapter による 1 path 除外をやめて本 wave で commit した** (byte 一致
  `c132098e906682db4d9582c712a6488a9613ec179641bdd170d980d50c165149` を確認、内容は
  wave 開始時に全文監査済み)。**これにより [T-193] の「宣言 path を非接触として受理する正規経路」は
  本件については不要になった** (別の未追跡 path で再発したときに再検討する)
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
  request `874708` / `874709` として計算ノードで取り直した**
  **高速化も同 ID に含める (ユーザー裁定 2026-07-31)**。計算ノード bnode041 で
  実測した (request `874712`、596 commit、**全 arm で findings と forward-correction が
  baseline と完全一致**)。逐次 **25.24 秒** に対し、(a) commit ごとの独立監査を thread pool 化
  すると 4 並列 8.03 / 8 並列 6.18 / 16 並列 5.60 / 32 並列 5.23 / 48 並列 5.23 秒 =
  **最大 4.8 倍だが 16 並列で頭打ち** (git subprocess の fork/exec と I/O が律速で、
  48 コアを使い切る意味はない)。(b) per-commit の pickaxe (`log -S`) と
  `merge-base --is-ancestor` を祖先集合の bitset 演算へ畳むと単独 15.40 秒 = **1.6 倍**。
  596 commit の祖先集合でも数百 KB なので**大量のメモリは要らない**。(a)+(b) で
  **4.58 秒 = 5.5 倍**。ログインノードの 130〜150 秒からは移設だけで 5〜6 倍、合わせて約 30 倍。
  実装方針は `_audit_history` の list comprehension を既定 16 並列の thread pool にし、
  `_has_co_authored_by_policy` / `_is_descendant` を bitset 祖先判定へ置換すること。
  probe は job tmp の使い捨てで repo へは入れていない。詳細は
  `output/insights/2026-07-30_t200-suite-floor/s7-negative-result.md` §11
- [T-206] **P2・ユーザー裁定済み (2a) / 裁定要 (2b) (本エントリ)**: `tools/dev_wave_land.py` の
  control-plane 検査が、land と無関係な実体で止まる。本 wave の land は
  `.codex/worktrees/.izanagi-test-dispatch` (**先頭ドットの空ディレクトリ**、git 未登録、
  滞在プロセスなし、並行セッションの未コミット実装の残骸と推定) で 2 度目の拒否を受けた。
  **(2a) 名前規則が過剰 — ユーザー裁定「無関係を検出してやばいというツールの方がやばい」**。
  子名は `openat` と除外 prefix 生成にしか使われないので危険なのは `.` / `..` / `/` / NUL であり、
  `_SAFE_ADMIN_RE` が途中のドットを既に許す以上、**先頭ドット禁止は先頭 `-` (git pathspec の
  オプション注入) を防ぐ巻き添えでしかない**。先頭 `-` と `.` / `..` は拒否したまま先頭ドットを
  許すべき。**(2b) は別裁定**: 名前規則を緩めても、登録済み worktree でない子は
  `_validate_admin_binding` が `.git` 不在で拒否するため理由コードが変わるだけである。
  「control container の子は全部が登録済み worktree」という不変条件を保つか、
  未登録の子を無関係として無視するかは**受理集合を変える設計判断**なので裁定へ返す。
  今回は不変条件側を復元する `rmdir` で land を通した (ユーザー承認済み、空なので可逆)
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

## 2026-07-31 (74) — [/rulings] ユーザー裁定 10 件を記録し、並行 wave の ID 再利用で落ちた裁定待ち 2 件を復元 (docs のみ、branch worktree-rulings-2026-07-31)

- ユーザー裁定 5 件 (要旨)。索引 16 件を提示し先頭 5 件を詳説した結果への回答である
  1. **[T-193] 前段は推奨どおり (a)** — `tools/pegasus/dispatch_compute.py` を正本にし、
     `dev-wave-improve` の `test_dispatch.py` / `submit_tests.py` / `run_tests_job.sh` は
     取り込んだうえで削除する
  2. **プロセス系凍結の付替えは推奨どおり (a)** — 解除条件を「床値実測の開始」から
     「[T-193] の閉鎖」へ変え、その次の 1 wave は研究側にする
  3. **[T-193] 後段は前提消滅で取り下げ** — 「誰も触ってないコミット漏れみたいだったので、
     コミットしようとしている」。実際に (73) が当該 insight を commit したため、
     `dev_wave_land.py` へ宣言 path 受理を入れる必要はなくなる
  4. **push はユーザーが実行済み**。「毎度 rulings に出るのうざい」「20 件以上未プッシュ
     だったら知らせて欲しい」に従い、`/rulings` の作法を**未 push 20 commit 以上のときだけ
     挙げる**へ改めた (本エントリの skill 自己改善)
  5. **git 整理の恒久化は据え置き (優先度低)** — 「静穏条件は pegasus ならいらないはず」
     「しばらく pegasus で開発する」。履歴監査の根本解決は [T-205] の高速化が担う
- **同一セッションで追加のユーザー裁定 5 件** (「他に裁定するものはないっけ？」への索引 14 件
  提示に対し、詳説した先頭 5 件をすべて推奨どおり採用)
  6. **[T-201] は (a) + (b)** — 本番 `_history_touches_path` の走査置換を本命とし、`output/` の
     tracked bytes 削減を同時に行う。(a) は正しさ防壁の中核に触るため、**受理集合不変を
     positive control で固定してから入れる**のが受理条件 ([T-173] と同型の扱い)
  7. **[T-204] / [T-177] は (i)** — `docs/dev-wave/**` の 24000 bytes は上げず (T-127 裁定を維持)、
     未使用の L2 節を削って空ける。AI が削除候補を条件付きで洗い出し、削除自体はユーザーが選ぶ
  8. **[T-206] (2b) は「空ディレクトリだけ無視」** — control container の未登録の子のうち、
     中身が空のものは無関係として無視し、ファイルを含むものは従来どおり拒否する。(2a) の
     「無関係を検出してやばいというツールの方がやばい」に沿いつつ受理集合の拡大を空に限定する
  9. **[T-207] は (a)** — `codex/p3-autonomous-trial` の 2 ファイルを、中身を確認したうえで
     取り込む。docs のみで実装への影響がなく、捨てると再取得に実走が要るため
  10. **[T-189] は (a)** — 不正な reasoning 値の拒否 (許可リスト検証) だけ先に実装し、
      served model の attest 経路が無い点 (F56) は実験の限界として明記する
- **並行 wave の ID 再利用で裁定待ち 2 件が正本から落ちていた (F58)**。(72) が land 済みの
  2 ID を (73) が別内容へ再採番したため、D70 の「一度 land した ID は変更・再利用しない」に
  反した。`tools/check_docs.py` の保存則は ID の**存在**だけを検査するので素通りする。
  落ちた内容を [T-207] / [T-208] として復元し、(73) 側の現行の意味は据え置いた
- **本実行の収集は (72) 時点の正本で行った**。詳説中に (73) が land したため、索引 16 件のうち
  git 整理・push・宣言 path 受理の 3 件は回答時点で既に状況が動いていた。裁定はいずれも
  その動きを踏まえたユーザー判断である
- 発火照合: [T-057] の述語 (受入全走 180 秒超) は**再成立**している。(73) の実測は同一コードでも
  bnode002 116.25 秒 / bnode009 200.72 秒 / bnode010 214.34 秒とノード間で 1.8 倍開く。
  台帳の「以後この述語は成立しない」を実測どおりに是正した。以後の所有は [T-201]
- [T-058] / [T-059] は (73) の検査新設で再発火したが、いずれも既裁定の範囲内で記録のみ
- 検査: `python3 tools/check_docs.py`、`python3 tools/check_codex_agents.py`、
  docs 系 targeted test を Pegasus 計算ノードで実行 (D103)
- 記録と skill 是正のみ。実装差分なし

### 次の一手

- [T-193] **裁定済み (本エントリ) → 実施待ち**: 前段は択 (a) 採用 —
  `tools/pegasus/dispatch_compute.py` を正本にし、`dev-wave-improve` の 3 ファイルは
  取り込んだうえで削除する。**後段 (`dev_wave_land.py` への宣言 path 受理) は前提消滅により
  取り下げ** — (73) が当該 insight を commit したため迂回自体が不要になった
- [T-209] **P1・裁定済み (本エントリ) → 実施待ち**: プロセス系凍結の解除条件を
  「[T-088] の実行 (床値実測の開始)」から「[T-193] の閉鎖」へ付け替える。[T-193] を閉じた
  次の 1 wave は研究側 (変異軸をデータ構造水準へ / 既知解までの距離で能力を測る評価設計) にする。
  直近 8 wave ((65)〜(72)) が全て道具・運用の整備で研究の測定が 0 本だったことが根拠
- [T-207] **P2・裁定済み (本エントリ、旧 (72) の落失分を復元) → 実施待ち**: 択 **(a)** 採用 —
  `codex/p3-autonomous-trial` (ahead=2) の `docs/phase3-8c-autonomous-trial-runbook.md` と
  `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` を、**中身を確認したうえで
  取り込む**。docs のみで実装への影響がなく、捨てると再取得に実走が要るため。
  取り込み後は当該 branch と worktree を掃除できる
- [T-208] **P3・実施待ち (本エントリで復元、旧 (72) の落失分)**: F26 追加事象 (submodule 実体化
  worktree の一括 `rm -rf` が timeout で半削除を残す) の運用則を
  `.claude/commands/cleanup-branches.md` §3 へ反映する。同ファイルは Codex skill との whole-file
  SHA-256 parity 契約下にあり、`tools/check_docs.py` の pin 更新と skill 側の同期が要る
- [T-210] **P3・裁定済み (本エントリ、据え置き)**: git のリポジトリ整理 (`gc` /
  `commit-graph write`) の恒久化は優先度低。Pegasus では静穏条件を要さないとのユーザー判断で、
  履歴監査の根本解決は [T-205] の高速化 (計算ノード実測 25.24 → 4.58 秒) が担う
- [T-211] **P2・ユーザー裁定要 (本エントリ、F58)**: 「次の一手」保存則を ID の存在検査から
  内容すり替えの検出まで強めるか。現行の `tools/check_docs.py` は同一 ID で中身が入れ替わると
  恒真になる。強める案 (前エントリの ID ごとに見出し文の対応を要求する等) は正当な推敲まで
  赤にしうるため、validator の受理集合を変える設計判断として裁定へ返す
- [T-200] 変わらず ((73) 参照)
- [T-201] **P1・裁定済み (本エントリ) → 実装待ち**: 択 **(a) + (b)** 採用 — 本番
  `t080_freeze_migration._history_touches_path` の走査を置換し (90 秒中 80 秒に直接効く唯一の案)、
  併せて `output/` の tracked bytes (3437 ファイル / 151MB) を減らす。**(a) は正しさ防壁の中核に
  触るため、受理集合が変わらないことを positive control で固定してから入れる**。(c) session 跨ぎ
  cache と (d) xdist grouping は不採用 ((d) は [T-120] が同型を実測で棄却済み)
- [T-202] 変わらず ((73) 参照)
- [T-205] 変わらず ((73) 参照)
- [T-206] **P2・裁定済み (2a) / (2b) とも (本エントリ) → 実装待ち**: (2b) は
  **「空ディレクトリだけ無視」**採用 — control container の未登録の子は、中身が空なら無関係として
  無視し、ファイルを含むものは従来どおり拒否する。名前規則の緩和 (2a) だけでは理由コードが
  変わるだけなので、両方を同じ実装で閉じる
- [T-204] **P2・裁定済み (本エントリ) → 実装待ち**: `docs/dev-wave/**` の 24000 bytes 上限は
  上げず ([T-127] 裁定を維持)、**未使用の L2 節を削って空ける**。AI は
  `docs/skill-self-improvement.md` の条件 (発火実績なし × 機械検査で義務代替済み) を満たす
  削除候補を洗い出して提示し、どれを削るかはユーザーが選ぶ。[T-177] も同じ壁なので同時に通す
- [T-203] 変わらず ((73) 参照)
- [T-192] 変わらず ((73) 参照)
- [T-194] 変わらず ((73) 参照)
- [T-195] 変わらず ((73) 参照)
- [T-196] 変わらず ((73) 参照)
- [T-197] 変わらず ((73) 参照)
- [T-198] 変わらず ((73) 参照)
- [T-199] 変わらず ((73) 参照)
- [T-191] 変わらず ((73) 参照)
- [T-189] **P1・裁定済み (本エントリ) → 実装・設計待ち**: 択 **(a)** 採用 — 不正な reasoning 値を
  許可リスト検証で拒否する分だけ先に実装し、**served model の attest 経路が存在しない点 (F56) は
  実験の限界として明記**する。比較実験の設計 (独立 oracle・held-out 複数 task・block
  randomization・盲検裁定・事前非劣性 margin) は限界の明記を前提に進める
- [T-190] 変わらず ((73) 参照)
- [T-188] 変わらず ((73) 参照)
- [T-187] 変わらず ((73) 参照)
- [T-180] 変わらず ((73) 参照)
- [T-181] 変わらず ((73) 参照)
- [T-182] 変わらず ((73) 参照)
- [T-183] 変わらず ((73) 参照)
- [T-184] 変わらず ((73) 参照)
- [T-186] 変わらず ((73) 参照)
- [T-179] 変わらず ((73) 参照)
- [T-185] 変わらず ((73) 参照)
- [T-139] 変わらず ((73) 参照)
- [T-142] 変わらず ((73) 参照)
- [T-136] 変わらず ((73) 参照)
- [T-129] 変わらず ((73) 参照)
- [T-149] 変わらず ((73) 参照)
- [T-152] 変わらず ((73) 参照)
- [T-153] 変わらず ((73) 参照)
- [T-158] 変わらず ((73) 参照)
- [T-141] 変わらず ((73) 参照)
- [T-143] 変わらず ((73) 参照)
- [T-126] 変わらず ((73) 参照)
- [T-059] 変わらず ((73) 参照)
- [T-145] 変わらず ((73) 参照)
- [T-146] 変わらず ((73) 参照)
- [T-134] 変わらず ((73) 参照)
- [T-123] 変わらず ((73) 参照)
- [T-118] 変わらず ((73) 参照)
- [T-109] 変わらず ((73) 参照)
- [T-113] 変わらず ((73) 参照)
- [T-110] 変わらず ((73) 参照)
- [T-097] 変わらず ((73) 参照)
- [T-100] 変わらず ((73) 参照)
- [T-099] 変わらず ((73) 参照)
- [T-009] 変わらず ((73) 参照)
- [T-060] 変わらず ((73) 参照)
- [T-150] 変わらず ((73) 参照)
- [T-151] 変わらず ((73) 参照)
- [T-154] 変わらず ((73) 参照)
- [T-130] 変わらず ((73) 参照)
- [T-135] 変わらず ((73) 参照)
- [T-133] 変わらず ((73) 参照)
- [T-144] 変わらず ((73) 参照)
- [T-088] 変わらず ((73) 参照)
- [T-096] 変わらず ((73) 参照)
- [T-102] 変わらず ((73) 参照)
- [T-122] 変わらず ((73) 参照)
- [T-103] 変わらず ((73) 参照)
- [T-089] 変わらず ((73) 参照)
- [T-090] 変わらず ((73) 参照)
- [T-112] 変わらず ((73) 参照)
- [T-114] 変わらず ((73) 参照)
- [T-011] 変わらず ((73) 参照)
- [T-085] 変わらず ((73) 参照)
- [T-087] 変わらず ((73) 参照)
- [T-012] 変わらず ((73) 参照)
- [T-010] 変わらず ((73) 参照)
- [T-082] 変わらず ((73) 参照)
- [T-121] 変わらず ((73) 参照)
- [T-156] 変わらず ((73) 参照)
- [T-159] 変わらず ((73) 参照)
- [T-157] 変わらず ((73) 参照)
- [T-148] 変わらず ((73) 参照)
- [T-155] 変わらず ((73) 参照)
- [T-140] 変わらず ((73) 参照)
- [T-147] 変わらず ((73) 参照)
- [T-127] 変わらず ((73) 参照)
- [T-137] 変わらず ((73) 参照)
- [T-138] 変わらず ((73) 参照)
- [T-132] 変わらず ((73) 参照)
- [T-131] 変わらず ((73) 参照)
- [T-128] 変わらず ((73) 参照)
- [T-120] 変わらず ((73) 参照)
- [T-125] 変わらず ((73) 参照)
- [T-116] 変わらず ((73) 参照)
- [T-057] 変わらず ((73) 参照)
- [T-117] 変わらず ((73) 参照)
- [T-119] 変わらず ((73) 参照)
- [T-105] 変わらず ((73) 参照)
- [T-104] 変わらず ((73) 参照)
- [T-101] 変わらず ((73) 参照)
- [T-124] 変わらず ((73) 参照)
- [T-108] 変わらず ((73) 参照)
- [T-111] 変わらず ((73) 参照)
- [T-160] 変わらず ((73) 参照)
- [T-161] 変わらず ((73) 参照)
- [T-162] 変わらず ((73) 参照)
- [T-163] 変わらず ((73) 参照)
- [T-164] 変わらず ((73) 参照)
- [T-165] 変わらず ((73) 参照)
- [T-166] 変わらず ((73) 参照)
- [T-167] 変わらず ((73) 参照)
- [T-168] 変わらず ((73) 参照)
- [T-169] 変わらず ((73) 参照)
- [T-170] 変わらず ((73) 参照)
- [T-171] 変わらず ((73) 参照)
- [T-172] 変わらず ((73) 参照)
- [T-173] 変わらず ((73) 参照)
- [T-174] 変わらず ((73) 参照)
- [T-175] 変わらず ((73) 参照)
- [T-176] 変わらず ((73) 参照)
- [T-177] **P3・裁定済み (本エントリ、[T-204] と同根) → 実装待ち**: docs 予算の壁は上限を
  上げずに未使用 L2 節の削除で空ける。F53 恒久対応の DW-O02 統合は空いた予算で通す

## 2026-07-31 (75) — [T-181] reasoning `max` 対 `high` の限定 A/B — 名指し R-1 正例で両 arm 3/3、装置は 194 test + 変異 12/12、ただし replay 未認証 (コード + docs、branch worktree-dev-wave-t181-reasoning-ab、計測 = 実走はログインノード / テストと変異は Pegasus 計算ノード bnode1xx)

- `tools/codex_reasoning_ab.py` (read-only 集計・検査 CLI) と回帰テストを追加し、
  focused review の reasoning 比較を**凍結 benchmark 上の限定 A/B** として正本化した。
  既定 policy (DW-O01 の reasoning 値) は変更していない。本 wave は観測のみ。
- **枠組みの訂正 (最重要)**: 歴史 focus1 の byte 再現は**不可能**と実測で確定した。歴史 run は指定 9 入力
  以外に `CLAUDE.md` / `AGENTS.md` / `docs/dev-wave/**` / `worklog` / `phase3` /
  `adjudication-plan-v2` / skill 定義を実読していた (親が rollout の tool call 27 件を走査)。
  よって「歴史 prompt 由来の新規凍結 benchmark」へ再定義し、「同一入力の再走」とは書かない
- **primary 結果 (label-masked 裁定、親 + 独立 Codex 第二読者が 10/10 一致)**:
  名指し R-1 正例で `high` **3/3**、`max` **3/3**。事前登録表の該当行に従い、
  許される裁定は「**この 6 run で劣化を観測しなかった**」だけで、非劣性・同等・採用の証明にはしない。
  限定負例では両 arm とも偽 R-1 は 0 件。`high` の 1 run が NO-GO を返したが理由は
  「snapshot に author patch が無く所有 gate を独立確認できない」で、benchmark 設計の副作用である
- **機械層と意味層が食い違った**: 機械の字句規則では `high` 2/3 だったが、意味裁定では 3/3。
  正しい別表現を 1 件落としていた。primary を意味裁定にした段4 裁定が実際に効いた事例
- **資源は max が一貫して大きい**: POS の model_calls は high 24/25/28 対 max 30/26/39、
  CLI reported 合計 591,173 対 765,335、wall 中央値 479,830 ms 対 730,583 ms。
  NEG は high 878,383 対 max 1,139,937、wall 中央値 730,355 ms 対 1,398,787 ms。
  要求 arm と実効 `turn_context.effort` は 10/10 一致
- **認証の欠落を明記する**: `aggregate` / `verify` は rc=24 / `experiment_complete=false`。
  全 10 run の `snapshot oracle replay mismatch` で、実体は「実走が fix9 前の oracle 下で行われ、
  記録済み `snapshot-before.json` を現在の oracle で再現できない」ことである。receipt 側は
  最終版コードで全 10 run を再収集して解消した。実走時の oracle を後から作り直すのは provenance の
  改竄なので行わない。**したがって数値は replay 認証済みではない**。認証済み台帳には最終版装置での再走が要る
- **漏洩遮断を実装した**: 通常 clone は 894 commit 全部を持ち込み `git log --all -- focus1.md` で
  答えの commit `08a7e5f2` に到達できた。bwrap の path 遮断はこの経路に無力。閉包を `8c8dc5e`
  到達可能集合 (834 commit) へ限定し、答え commit の到達不能を oracle 化した。
  隔離自体は親 probe 2 本で live 確認済み (bwrap + 新規 CODEX_HOME で `focus1.md` が ENOENT)
- **静的レビューでは出ず実走・変異で出た欠陥 4 件**: (a) `MAX_SCHEDULE_GAP_MS=60_000` が装置自身の
  検証コスト (実測 350,980 ms) で block 間を必ず違反 → intra 60 秒 / inter 900 秒へ分離、
  (b) 事前登録 M6 の期待 node が swap→restore を検査していなかった → 実再現テストを追加、
  (c) 上流 CLI が per-turn `last_token_usage` に全構成要素 0 / total 非ゼロを 1 件出す →
  `zero_component_total_only` として件数を公開し run を無効化しない (最後の累積が同型なら fatal を維持)、
  (d) clone が stale commit-graph を持ち込み `git fsck` rc≠0 を「unreachable objects」と誤報告 →
  cache 除去と理由分離
- **`--dry-run` の取り違えを回避した**: これは「起動しない」ではなく「**bwrap 無しで実走する**」意味だった。
  隔離なし run が始まっていたので停止・破棄した。receipt に `dry_run` が残る設計なので混入は検出できる
- **計算ノード運用 (ユーザー指示 2026-07-30)**: テスト・変異・snapshot 構築・aggregate を qsub へ移し、
  子には pytest を禁じた。結果、**計算ノードでの実測が実在欠陥 2 件を検出**した
  (git 2.34.1 で `ls-files --stage --recurse-submodules` 不可、入れ子 submodule 未初期化の無条件拒否)。
  計算ノードは外向き DNS 不通のため codex 実走のみログインノードに残した
- 検査: テスト **194 passed / rc=0** (計算ノード、python 3.10.12 / pytest 9.1.1)。
  変異 **kill 12/12**。再照準前の 7/12 は erratum として保存。M6 は冗長 2 層に守られ単層で生存したため
  DW-M04 の両層同時変異 M6p を追加登録し KILLED を確認。復元検査 OK、変異後も tree clean。
  `check_docs.py` 違反なし
- wave path は全段を使った。段2 plan + 段3 敵対相談 2 本 + 段5 author + 段6 レビュー 2 本 +
  fix 9 巡 + 焦点再レビュー 3 巡 (DW-O16 上限に到達し、以後は親が変異で裏取りして閉じた)。
  実装面はすべて Codex `role=author` が書き、親は brief・裁定・統合・実走・変異・受入・記録のみ担当した。
  変異 harness と run driver は親の監査計器のため job tmp に置き commit していない (T-179 と同じ読み)
- limitation (insight に全文): logical turn は測れない / finding dedup は文字列一致で下限値 /
  masking は same-owner advisory で盲検ではない / 親は verdict 記入前に機械層の arm 別集計を観測した /
  backend の実計算量は証明できない
- 逐語と台帳 40 ファイルは `output/insights/2026-07-30_t181-reasoning-ab/`
- **番号振り直し (D70)**: 本エントリは branch 上で (65) として記録した。
  並行 wave の land ((59)〜(72)) と衝突したため、統合時に (73) へ振り直し、
  次の一手は main 側 (72) のリストを基底に再構成した。
  段 8 の失敗型も main の F55〜F57 と衝突したため **F58〜F60** へ振り直した
- **番号振り直し (D70、2 回目)**: branch 上では (65) → 統合時 (73) と振り直したが、
  並行 land が (73)(74) を先に使ったため最終的に **(75)** とした。
  次の一手は main 側 (74) のリストを基底に再構成した
- **land 規則の是正を同梱**: 他 session の成果物が main 上に存在するだけで land が止まる件は
  main 側でも [T-206] として起票されていた。本 wave の実装 commit がこれを閉じる
  (危険な名前と実衝突だけを拒否、`git merge --ff-only` の未追跡保護を二重の防壁にする)

### 次の一手

- [T-193] **裁定済み (本エントリ) → 実施待ち**: 前段は択 (a) 採用 —
  `tools/pegasus/dispatch_compute.py` を正本にし、`dev-wave-improve` の 3 ファイルは
  取り込んだうえで削除する。**後段 (`dev_wave_land.py` への宣言 path 受理) は前提消滅により
  取り下げ** — (73) が当該 insight を commit したため迂回自体が不要になった
- [T-209] **P1・裁定済み (本エントリ) → 実施待ち**: プロセス系凍結の解除条件を
  「[T-088] の実行 (床値実測の開始)」から「[T-193] の閉鎖」へ付け替える。[T-193] を閉じた
  次の 1 wave は研究側 (変異軸をデータ構造水準へ / 既知解までの距離で能力を測る評価設計) にする。
  直近 8 wave ((65)〜(72)) が全て道具・運用の整備で研究の測定が 0 本だったことが根拠
- [T-207] **P2・ユーザー裁定要 (本エントリで復元、旧 (72) の落失分)**: `codex/p3-autonomous-trial`
  (ahead=2) の `docs/phase3-8c-autonomous-trial-runbook.md` と
  `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` が main に無い。
  取り込むか見送るかを裁定する
- [T-208] **P3・実施待ち (本エントリで復元、旧 (72) の落失分)**: F26 追加事象 (submodule 実体化
  worktree の一括 `rm -rf` が timeout で半削除を残す) の運用則を
  `.claude/commands/cleanup-branches.md` §3 へ反映する。同ファイルは Codex skill との whole-file
  SHA-256 parity 契約下にあり、`tools/check_docs.py` の pin 更新と skill 側の同期が要る
- [T-210] **P3・裁定済み (本エントリ、据え置き)**: git のリポジトリ整理 (`gc` /
  `commit-graph write`) の恒久化は優先度低。Pegasus では静穏条件を要さないとのユーザー判断で、
  履歴監査の根本解決は [T-205] の高速化 (計算ノード実測 25.24 → 4.58 秒) が担う
- [T-211] **P2・ユーザー裁定要 (本エントリ、F58)**: 「次の一手」保存則を ID の存在検査から
  内容すり替えの検出まで強めるか。現行の `tools/check_docs.py` は同一 ID で中身が入れ替わると
  恒真になる。強める案 (前エントリの ID ごとに見出し文の対応を要求する等) は正当な推敲まで
  赤にしうるため、validator の受理集合を変える設計判断として裁定へ返す
- [T-200] 変わらず ((73) 参照)
- [T-201] 変わらず ((73) 参照)
- [T-202] 変わらず ((73) 参照)
- [T-205] 変わらず ((73) 参照)
- [T-206] **本 wave で解消 ((75))**: land の control-plane 検査が無関係な実体で止まる件を、
  危険な名前と実衝突だけの拒否へ是正し回帰を追加した
- [T-204] 変わらず ((73) 参照)
- [T-203] 変わらず ((73) 参照)
- [T-192] 変わらず ((73) 参照)
- [T-194] 変わらず ((73) 参照)
- [T-195] 変わらず ((73) 参照)
- [T-196] 変わらず ((73) 参照)
- [T-197] 変わらず ((73) 参照)
- [T-198] 変わらず ((73) 参照)
- [T-199] 変わらず ((73) 参照)
- [T-191] 変わらず ((73) 参照)
- [T-189] 変わらず ((73) 参照)
- [T-190] 変わらず ((73) 参照)
- [T-188] 変わらず ((73) 参照)
- [T-187] 変わらず ((73) 参照)
- [T-180] 変わらず ((73) 参照)
- [T-181] **実装完了・結果は replay 未認証 ((75))**: 装置 (`tools/codex_reasoning_ab.py`、
  受入全走 4197 passed、変異 12/12) と 10 run の実測は揃った。**最終版装置での 10 run 再走**により
  `experiment_complete=true` の認証済み台帳を得ることが残件。再走なしに T-184 で引用してはならない
- [T-182] 変わらず ((73) 参照)
- [T-183] 変わらず ((73) 参照)
- [T-184] 変わらず ((73) 参照)
- [T-186] 変わらず ((73) 参照)
- [T-179] 変わらず ((73) 参照)
- [T-185] 変わらず ((73) 参照)
- [T-139] 変わらず ((73) 参照)
- [T-142] 変わらず ((73) 参照)
- [T-136] 変わらず ((73) 参照)
- [T-129] 変わらず ((73) 参照)
- [T-149] 変わらず ((73) 参照)
- [T-152] 変わらず ((73) 参照)
- [T-153] 変わらず ((73) 参照)
- [T-158] 変わらず ((73) 参照)
- [T-141] 変わらず ((73) 参照)
- [T-143] 変わらず ((73) 参照)
- [T-126] 変わらず ((73) 参照)
- [T-059] 変わらず ((73) 参照)
- [T-145] 変わらず ((73) 参照)
- [T-146] 変わらず ((73) 参照)
- [T-134] 変わらず ((73) 参照)
- [T-123] 変わらず ((73) 参照)
- [T-118] 変わらず ((73) 参照)
- [T-109] 変わらず ((73) 参照)
- [T-113] 変わらず ((73) 参照)
- [T-110] 変わらず ((73) 参照)
- [T-097] 変わらず ((73) 参照)
- [T-100] 変わらず ((73) 参照)
- [T-099] 変わらず ((73) 参照)
- [T-009] 変わらず ((73) 参照)
- [T-060] 変わらず ((73) 参照)
- [T-150] 変わらず ((73) 参照)
- [T-151] 変わらず ((73) 参照)
- [T-154] 変わらず ((73) 参照)
- [T-130] 変わらず ((73) 参照)
- [T-135] 変わらず ((73) 参照)
- [T-133] 変わらず ((73) 参照)
- [T-144] 変わらず ((73) 参照)
- [T-088] 変わらず ((73) 参照)
- [T-096] 変わらず ((73) 参照)
- [T-102] 変わらず ((73) 参照)
- [T-122] 変わらず ((73) 参照)
- [T-103] 変わらず ((73) 参照)
- [T-089] 変わらず ((73) 参照)
- [T-090] 変わらず ((73) 参照)
- [T-112] 変わらず ((73) 参照)
- [T-114] 変わらず ((73) 参照)
- [T-011] 変わらず ((73) 参照)
- [T-085] 変わらず ((73) 参照)
- [T-087] 変わらず ((73) 参照)
- [T-012] 変わらず ((73) 参照)
- [T-010] 変わらず ((73) 参照)
- [T-082] 変わらず ((73) 参照)
- [T-121] 変わらず ((73) 参照)
- [T-156] 変わらず ((73) 参照)
- [T-159] 変わらず ((73) 参照)
- [T-157] 変わらず ((73) 参照)
- [T-148] 変わらず ((73) 参照)
- [T-155] 変わらず ((73) 参照)
- [T-140] 変わらず ((73) 参照)
- [T-147] 変わらず ((73) 参照)
- [T-127] 変わらず ((73) 参照)
- [T-137] 変わらず ((73) 参照)
- [T-138] 変わらず ((73) 参照)
- [T-132] 変わらず ((73) 参照)
- [T-131] 変わらず ((73) 参照)
- [T-128] 変わらず ((73) 参照)
- [T-120] 変わらず ((73) 参照)
- [T-125] 変わらず ((73) 参照)
- [T-116] 変わらず ((73) 参照)
- [T-057] 変わらず ((73) 参照)
- [T-117] 変わらず ((73) 参照)
- [T-119] 変わらず ((73) 参照)
- [T-105] 変わらず ((73) 参照)
- [T-104] 変わらず ((73) 参照)
- [T-101] 変わらず ((73) 参照)
- [T-124] 変わらず ((73) 参照)
- [T-108] 変わらず ((73) 参照)
- [T-111] 変わらず ((73) 参照)
- [T-160] 変わらず ((73) 参照)
- [T-161] 変わらず ((73) 参照)
- [T-162] 変わらず ((73) 参照)
- [T-163] 変わらず ((73) 参照)
- [T-164] 変わらず ((73) 参照)
- [T-165] 変わらず ((73) 参照)
- [T-166] 変わらず ((73) 参照)
- [T-167] 変わらず ((73) 参照)
- [T-168] 変わらず ((73) 参照)
- [T-169] 変わらず ((73) 参照)
- [T-170] 変わらず ((73) 参照)
- [T-171] 変わらず ((73) 参照)
- [T-172] 変わらず ((73) 参照)
- [T-173] 変わらず ((73) 参照)
- [T-174] 変わらず ((73) 参照)
- [T-175] 変わらず ((73) 参照)
- [T-176] 変わらず ((73) 参照)
- [T-177] 変わらず ((73) 参照)

## 2026-07-31 (76) — [/cleanup-branches] land 済みの自 worktree branch を 1 本畳む — 稼働中 2 wave・dirty 1・取り残し 1 は残置 (docs のみ、branch main、計測なし)

- 棚卸し: worktree 14、local branch 13。ahead=0 が 9 本、ahead>0 が 4 本。
  ahead>0 は `git cherry main <b>` で `+` 行を確認し、rewrite 由来と真の取り残しを分けた
- **削除したのは 1 本だけ**: `worktree-dev-wave-t181-reasoning-ab` (ahead=0、main `cb5780e` に
  取り込み済み)。F26 手順の detach → `git branch -d` まで実施した。
  自セッションが cwd 固定の背景 job で当該 worktree 内に居るため、F51 に従い
  **ディレクトリ削除と `git worktree prune` は行わずユーザーへ引き渡す**
- **残置とその理由** (すべて実測):
  - `codex/dev-wave-improve` と `-u1`〜`-u5`: ahead=0 だが `/proc` 実測で
    **親 worktree に 19 プロセス稼働中**。u1〜u5 はその wave の実装単位のため一体で残す
  - `codex/dev-wave-t126-sequential-stopping`: ahead=0 だが滞在 1 プロセス
  - `worktree-rulings-2026-07-31`: 滞在 1 プロセス + locked、HEAD 21 分前
  - `codex/dev-wave-t153e-t15423-author`: ahead=0 だが**未コミット差分 4 件** (dirty)
  - `codex/p3-autonomous-trial`: **真の取り残し**。`docs/phase3-8c-autonomous-trial-runbook.md` と
    `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` が main に不在
  - `codex/dev-wave-ai-provenance-main-integration`: `+` 1 件 (T-180 記録) だが D100 と
    archive ファイルは main に到達済み。`-d` が拒否するため止めて報告に回す
  - `codex/dev-wave-cleanup-branches-skill`: `+` 行なし (取り残しなし) だが ahead>0 のため同上
  - `t181-selfauthored-backup`: T-181 wave で自著実装を退避した branch。内容は Codex 著版として
    main に到達済み (`_landed_paths` 7 hit、`_SAFE_CHILD_RE` 更新済み) だが `-d` が拒否したため残置
- `-D` は一度も使っていない。`git submodule deinit` も使っていない
- 事後検査: `git worktree list` は期待どおり、`git submodule status` は `-` prefix なしで
  `d706650` に一致、main は `cb5780e` で未追跡は他セッション所有の handoff 3 件と
  worktree コンテナのみ

- **ユーザー引き渡し (AI は push・強制削除をしない)**: 自 worktree
  `.claude/worktrees/dev-wave-t181-reasoning-ab` のディレクトリ削除と `git worktree prune`、
  および `t181-selfauthored-backup` の削除 (内容は main 到達済みだが `-d` 拒否のため `-D` が要る)。
  remote branch の削除も未実施

### 次の一手

- [T-193] **裁定済み ((74)) → 実施待ち**: 前段は択 (a) 採用 —
  `tools/pegasus/dispatch_compute.py` を正本にし、`dev-wave-improve` の 3 ファイルは
  取り込んだうえで削除する。**後段 (`dev_wave_land.py` への宣言 path 受理) は前提消滅により
  取り下げ** — (73) が当該 insight を commit したため迂回自体が不要になった
- [T-209] **P1・裁定済み ((74)) → 実施待ち**: プロセス系凍結の解除条件を
  「[T-088] の実行 (床値実測の開始)」から「[T-193] の閉鎖」へ付け替える。[T-193] を閉じた
  次の 1 wave は研究側 (変異軸をデータ構造水準へ / 既知解までの距離で能力を測る評価設計) にする。
  直近 8 wave ((65)〜(72)) が全て道具・運用の整備で研究の測定が 0 本だったことが根拠
- [T-207] **P2・裁定済み ((74)) → 実施待ち**: 択 (a) 採用 — `codex/p3-autonomous-trial` の
  runbook と insight を中身確認のうえ取り込む。取り込み後に当該 branch と worktree を掃除できる
- [T-208] **P3・実施待ち ((74)で復元、旧 (72) の落失分)**: F26 追加事象 (submodule 実体化
  worktree の一括 `rm -rf` が timeout で半削除を残す) の運用則を
  `.claude/commands/cleanup-branches.md` §3 へ反映する。同ファイルは Codex skill との whole-file
  SHA-256 parity 契約下にあり、`tools/check_docs.py` の pin 更新と skill 側の同期が要る
- [T-210] **P3・裁定済み ((74)、据え置き)**: git のリポジトリ整理 (`gc` /
  `commit-graph write`) の恒久化は優先度低。Pegasus では静穏条件を要さないとのユーザー判断で、
  履歴監査の根本解決は [T-205] の高速化 (計算ノード実測 25.24 → 4.58 秒) が担う
- [T-211] **P2・ユーザー裁定要 ((74)、F58)**: 「次の一手」保存則を ID の存在検査から
  内容すり替えの検出まで強めるか。現行の `tools/check_docs.py` は同一 ID で中身が入れ替わると
  恒真になる。強める案 (前エントリの ID ごとに見出し文の対応を要求する等) は正当な推敲まで
  赤にしうるため、validator の受理集合を変える設計判断として裁定へ返す
- [T-200] 変わらず ((73) 参照)
- [T-201] **P1・裁定済み ((74)) → 実装待ち**: 択 (a) + (b) 採用 — 本番
  `t080_freeze_migration._history_touches_path` の走査置換 (90 秒中 80 秒に直接効く唯一の案) と
  `output/` の tracked bytes 削減。(a) は受理集合不変を positive control で固定してから入れる
- [T-202] 変わらず ((73) 参照)
- [T-205] 変わらず ((73) 参照)
- [T-206] **本 wave で解消 ((75))**: land の control-plane 検査が無関係な実体で止まる件を、
  危険な名前と実衝突だけの拒否へ是正し回帰を追加した
- [T-212] **P2・ユーザー裁定要 (新規)**: [T-206] の着地実装が 2026-07-31 の裁定より**広い**。
  裁定は「control container の未登録の子は**中身が空のものだけ**無視」だったが、`8adea51` は
  (a) 非衝突の未追跡 path を**すべて**無視し (`git merge --ff-only` を第二防壁とする)、
  (b) 子名の許可規則を「区切り・NUL・自己/親参照だけ拒否」へ緩めて**先頭ダッシュの子名も許可**した。
  (b) は (73) の分析が「先頭ダッシュ (git pathspec のオプション注入) は拒否したまま」と
  名指ししたものである。現状を追認するか、空ディレクトリ限定と先頭ダッシュ拒否へ戻すかを裁定する
- [T-204] **P2・裁定済み ((74)) → 実装待ち**: `docs/dev-wave/**` の 24000 bytes 上限は
  上げず、未使用の L2 節を削って空ける。削除候補の洗い出しは AI、選択はユーザー
- [T-203] 変わらず ((73) 参照)
- [T-192] 変わらず ((73) 参照)
- [T-194] 変わらず ((73) 参照)
- [T-195] 変わらず ((73) 参照)
- [T-196] 変わらず ((73) 参照)
- [T-197] 変わらず ((73) 参照)
- [T-198] 変わらず ((73) 参照)
- [T-199] 変わらず ((73) 参照)
- [T-191] 変わらず ((73) 参照)
- [T-189] **P1・裁定済み ((74)) → 実装・設計待ち**: 択 (a) 採用 — 不正 reasoning 値の
  許可リスト拒否を先行し、served model の attest 経路が無い点 (F56) は限界として明記する
- [T-190] 変わらず ((73) 参照)
- [T-188] 変わらず ((73) 参照)
- [T-187] 変わらず ((73) 参照)
- [T-180] 変わらず ((73) 参照)
- [T-181] **実装完了・結果は replay 未認証 ((75))**: 装置 (`tools/codex_reasoning_ab.py`、
  受入全走 4197 passed、変異 12/12) と 10 run の実測は揃った。**最終版装置での 10 run 再走**により
  `experiment_complete=true` の認証済み台帳を得ることが残件。再走なしに T-184 で引用してはならない
- [T-182] 変わらず ((73) 参照)
- [T-183] 変わらず ((73) 参照)
- [T-184] 変わらず ((73) 参照)
- [T-186] 変わらず ((73) 参照)
- [T-179] 変わらず ((73) 参照)
- [T-185] 変わらず ((73) 参照)
- [T-139] 変わらず ((73) 参照)
- [T-142] 変わらず ((73) 参照)
- [T-136] 変わらず ((73) 参照)
- [T-129] 変わらず ((73) 参照)
- [T-149] 変わらず ((73) 参照)
- [T-152] 変わらず ((73) 参照)
- [T-153] 変わらず ((73) 参照)
- [T-158] 変わらず ((73) 参照)
- [T-141] 変わらず ((73) 参照)
- [T-143] 変わらず ((73) 参照)
- [T-126] 変わらず ((73) 参照)
- [T-059] 変わらず ((73) 参照)
- [T-145] 変わらず ((73) 参照)
- [T-146] 変わらず ((73) 参照)
- [T-134] 変わらず ((73) 参照)
- [T-123] 変わらず ((73) 参照)
- [T-118] 変わらず ((73) 参照)
- [T-109] 変わらず ((73) 参照)
- [T-113] 変わらず ((73) 参照)
- [T-110] 変わらず ((73) 参照)
- [T-097] 変わらず ((73) 参照)
- [T-100] 変わらず ((73) 参照)
- [T-099] 変わらず ((73) 参照)
- [T-009] 変わらず ((73) 参照)
- [T-060] 変わらず ((73) 参照)
- [T-150] 変わらず ((73) 参照)
- [T-151] 変わらず ((73) 参照)
- [T-154] 変わらず ((73) 参照)
- [T-130] 変わらず ((73) 参照)
- [T-135] 変わらず ((73) 参照)
- [T-133] 変わらず ((73) 参照)
- [T-144] 変わらず ((73) 参照)
- [T-088] 変わらず ((73) 参照)
- [T-096] 変わらず ((73) 参照)
- [T-102] 変わらず ((73) 参照)
- [T-122] 変わらず ((73) 参照)
- [T-103] 変わらず ((73) 参照)
- [T-089] 変わらず ((73) 参照)
- [T-090] 変わらず ((73) 参照)
- [T-112] 変わらず ((73) 参照)
- [T-114] 変わらず ((73) 参照)
- [T-011] 変わらず ((73) 参照)
- [T-085] 変わらず ((73) 参照)
- [T-087] 変わらず ((73) 参照)
- [T-012] 変わらず ((73) 参照)
- [T-010] 変わらず ((73) 参照)
- [T-082] 変わらず ((73) 参照)
- [T-121] 変わらず ((73) 参照)
- [T-156] 変わらず ((73) 参照)
- [T-159] 変わらず ((73) 参照)
- [T-157] 変わらず ((73) 参照)
- [T-148] 変わらず ((73) 参照)
- [T-155] 変わらず ((73) 参照)
- [T-140] 変わらず ((73) 参照)
- [T-147] 変わらず ((73) 参照)
- [T-127] 変わらず ((73) 参照)
- [T-137] 変わらず ((73) 参照)
- [T-138] 変わらず ((73) 参照)
- [T-132] 変わらず ((73) 参照)
- [T-131] 変わらず ((73) 参照)
- [T-128] 変わらず ((73) 参照)
- [T-120] 変わらず ((73) 参照)
- [T-125] 変わらず ((73) 参照)
- [T-116] 変わらず ((73) 参照)
- [T-057] 変わらず ((73) 参照)
- [T-117] 変わらず ((73) 参照)
- [T-119] 変わらず ((73) 参照)
- [T-105] 変わらず ((73) 参照)
- [T-104] 変わらず ((73) 参照)
- [T-101] 変わらず ((73) 参照)
- [T-124] 変わらず ((73) 参照)
- [T-108] 変わらず ((73) 参照)
- [T-111] 変わらず ((73) 参照)
- [T-160] 変わらず ((73) 参照)
- [T-161] 変わらず ((73) 参照)
- [T-162] 変わらず ((73) 参照)
- [T-163] 変わらず ((73) 参照)
- [T-164] 変わらず ((73) 参照)
- [T-165] 変わらず ((73) 参照)
- [T-166] 変わらず ((73) 参照)
- [T-167] 変わらず ((73) 参照)
- [T-168] 変わらず ((73) 参照)
- [T-169] 変わらず ((73) 参照)
- [T-170] 変わらず ((73) 参照)
- [T-171] 変わらず ((73) 参照)
- [T-172] 変わらず ((73) 参照)
- [T-173] 変わらず ((73) 参照)
- [T-174] 変わらず ((73) 参照)
- [T-175] 変わらず ((73) 参照)
- [T-176] 変わらず ((73) 参照)
- [T-177] **P3・裁定済み ((74)、[T-204] と同根) → 実装待ち**: 上限を上げずに未使用 L2 節の
  削除で空け、F53 恒久対応の DW-O02 統合を通す
