# worklog アーカイブ — Phase 3 (2026-07-31 (73))

凍結済み。訂正注記のみ追記可。現行は `docs/worklog.md`。
ローテーションの経緯と境界の根拠は `docs/archive/README.md` を参照する。

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
