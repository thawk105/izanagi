# worklog archive — Phase 3 2026-07-30 (71)〜(72)

ローテーションで `docs/worklog.md` から移動した凍結記録 (訂正注記のみ追記可、D35)。

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

