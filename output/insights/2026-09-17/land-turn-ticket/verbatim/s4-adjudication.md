# 段 4 裁定 — land-turn-ticket (plan v2・変異事前登録・test 仕様)

親の裁定。plan (s2-plan.md) とレンズ A (s3-a.md、正しさ境界) / レンズ B (s3-b.md、進行保証) の所見を real / refuted、採用 / 不採用、scope 内 / 外で裁いた。**plan v2 = s2-plan.md + 本書の補正**。矛盾時は本書が優先する。

## 0. 裁定 inbox の再走査

wave 開始後に main は 2 commit 進んだ (`ad12ba35b` 第 20 回裁定、`b4631a92e` fold)。編集面 4 file に差分なし。第 20 回 項 34 が「F977 巻き戻し通知を `wave_land_window.py message` へ 1 kind 足す」を裁定しており、同時起動の `dev-wave-f976-f977-lock-notify` の実装対象と見られる。**本 wave は `tools/wave_land_window.py` を編集しない** (順番票は common git-dir 配下、旧 ticket helper は流用しない)。

## 1. 所見の裁定 (real / refuted と採否)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | plan | ff は `git merge --ff-only` (5567)、`update-ref` は rollback 側 | real・採用 (brief P2 の anchor 訂正) |
| 2 | plan | 死亡票を完全削除すると外部再試行で seq を復元できない → registry に seq 対応を残す | real・採用 |
| 3 | plan / A / B | 180 秒を総競合待機の厳密上限として維持しながら 3600 秒待つことはできない → 二層予算、新 D で「180 秒は総待ち上限でなくなる」と明記 | real・採用 |
| 4 | plan / A / B | 独立 branch 8 本は FIFO だけで全件 land しない (先行 land 後は stale-main) | real・採用。**完了判定は依頼どおり「有限 step に 1 本完了」を必須とし**、残りは `stale-main` (retryable、seq 保持) で終わることを正例に含める。累積 tip 列での「8 本全完了」は追加正例 (§4) |
| 5 | plan | grant 非横取り (休止票の復帰は実行中 grant を奪わない) | real・採用 |
| 6 | plan / A | `mutating` phase の marking は ff 前 (5567 直前) と `fold.apply_fold` 前 (4562 付近) の両方 | real・採用。**shape B の mark/finalize 経路 (5200→4727→4755) にも ownership 再確認と marking を接続** (A 未確認 → 採用) |
| 7 | plan | recovery 自動化は「元 request の再入を通常 seq より優先」まで。他 wave による自動復旧は scope 外 | real・採用。裁定パッケージ候補へ (§7) |
| 8 | plan | `_FoldGateFailure` 既定 `retryable_same_request=False`。分類を変えない | real・採用 |
| 9 | plan | lease TTL 2400 < 3600。待機中の lease 保持は保証しない。renew loop を足さない。release の `expected_main_sha=request.tested_main_sha` 維持 | real・採用 |
| 10 | plan / B | thread + 決定的 scheduler。ただし `_execute_fold_gate` (3806) の `signal.signal` は worker thread で失敗 | real・採用。**seam (`_audit_provenance_history` / `_run_fold_gate`) は scheduler の main thread で実物へ委譲して実行する** (§4) |
| 11 | plan | 既存 fixture の罠 (共有 receipt path、`acceptance_wave` 既定値、cwd 共有、patch のネスト) | real・採用 |
| 12 | plan | `_dry_run_candidates` と prune の argv 許可形を廃止 | real・採用 |
| 13 | plan | DW-O28 も exact pin (check_docs 626/662)。DW-O23/O25/O28 は不変更で成立 | real・採用 |
| 14 | A | 「flock が唯一の mutation guard」は広すぎる → 「協調 land による main ref / index / worktree / fold state の mutation は common flock 内」に限定。registry lock と対象限定 cleanup は別面 | real・採用 (不変条件 a を訂正) |
| 15 | A | 「拒否は main 不変」は mutation 前の拒否に限る。admit 後の recovery 失敗 (rollback) は main を変える | real・採用 (不変条件 b を訂正) |
| 16 | A | 失効条件は「main/tip だけ」で不足。既存の control・cleanliness・state・closure・receipt 再検査を全部残す (SHA/fingerprint 一致を単独の続行条件にしない) | real・採用 |
| 17 | A | provenance 非ゼロ payload を grant を持ったまま期限まで保持する経路が plan の疑似コードにある | real・採用。**runner 帰還後、payload の `returncode != 0` なら再取得を待たず既存 `RC_PROVENANCE` (非 retryable) で即終端**。成功 payload の lock 内完全再照合は不変 |
| 18 | A | finalize 後・ticket `done` 記録前の死亡、正常 rollback 後・ticket 更新前の死亡が未定義 → state 有無だけに頼らず死亡票を解消する完了照合手順が要る | real・採用 (§3.3) |
| 19 | A / B | 同一 key の二重再入 (A₁, A₂ 同時) | real・採用: registry lock 内で生存 runtime owner があれば第二の ticket を作らず `RC_LOCK_BUSY` (reason 別文面、retryable) で降りる |
| 20 | A | recovery 中に landing_tip が変わった再入 (origin.tested_tip ≠ 新 landing_tip) | real・採用: 同 key で未解決 `mutating` 票があり landing_tip が異なる再入は fail-closed (`RC_FOLD_RECOVERY_FAILED`、origin を上書きしない) |
| 21 | A | 非接触後に受理へ反転する入力の表 (無関係 child の同名差替え・alias・`.git` 欠損・不正名) は incoming と非衝突。`_CONTROL_CONTAINERS` 自体は常に protected | real・採用。brief 末尾「拒否は狭まらず」を「指定した非接触面の拒否は狭まる (D109 の方向)、他は不変」に訂正 |
| 22 | A | cleanup の完全非接触は実現しない (resolver は他 admin の backpointer を読む) → 主張は「他 wave の admin を削除しない」まで | real・採用 |
| 23 | A | fold 子 process (`git add` / `git commit`) は lock fd を継承しない → 親死亡直後も子が生存する schedule は ticket FD の死亡確認だけで閉じない | real・scope 外 (既存の子 process 境界)。§7 へ |
| 24 | B | 480 秒 timeout の最古 request が再入を繰り返し後続を追い越す (grant 解放と後続への引渡しが原子的でない) | real・採用: **terminal outcome 時、同じ registry 更新で grant を「登録済み・生存・最小 seq の待ち手」へ引き渡す**。復帰した旧 seq は非横取り |
| 25 | B | 各 180 秒枠の deadline を `turn_deadline` で切る | real・採用 |
| 26 | B | 順番期限直前に監査緑になっても期限で成果破棄 → rc=11 | real・受容 (有界の availability cap。seq 保持で再投入は順位を失わない。監査は再走)。新 D に明記 |
| 27 | B | 生存 hang (FD 保持のまま停止) は止める主体がない | real・scope 外。TTL 追越しは採らない。§7 へ |
| 28 | B | 旧 driver 混在期は内部順位保証に留まる | real・採用 (新 D に「進行保証は新 driver 同士、旧 driver の妨害が終息することが前提」と明記) |
| 29 | B | 元 request 不在の fold 途中 state は全体停止を残す | real・部分採用: §3.3 の完了照合で ff 済 / rollback 済 / finalize 済は他 wave が観測で解消できる。**真の途中 state (state file 実在) だけ**が元 request を要する。自動復旧主体は scope 外 (§7) |
| 30 | B | registry flock の公平性は導けない | real・受容: registry の critical section は短く (git 呼出し・sleep 無し)、取得は有界待機 + jitter。公平性は OS flock 依存と新 D に明記 |
| 31 | B | 照合 key `(acceptance_wave, tested_tip, receipt raw sha256)` + wave path / common / tested_main 一致 | 採用 (plan どおり)。receipt 再発行で seq を失うのは設計どおり |
| 32 | B | stale-main 後に seq を消すと正規の前進 merge 再試行で順位を失う | real・採用: **rc 別の seq 処理表** (§3.2) |
| 33 | B | 「実 flock + tmp repo」は real-repo lock (F976) 対象ではない (inventory 未登録) | refuted の確認・採用。新 test も本 repo の可変状態へ触れない |
| 34 | B | 変異の専属帰属は未成立 (M1〜M11)。exact 置換と node 単独結果で実装後に判定 | real・採用 (§5)。**現時点で KILLED 済みは 0 件** と記録 |
| 35 | B | 186 秒 × 13 = 2418 秒 (約 40 分) であり 43 分ではない。186 秒は上限でない | real・採用。3600 の根拠は §3.5 の実測分布に置き換える |
| 36 | B | M1 だけで旧構造の全停止負例にはならない | real・採用: 負例は親の旧 tree probe (§4.3) が担い、M1 は「先頭 gate の必要性」の変異 |
| 37 | B | `run_tests.py` の一律 300 秒執行は現物に無い (shard deadline 5100 秒)。5 分は受入目標 | real・採用 (5 分は D-test-time-regression の運用上限、code の強制上限ではない) |
| 38 | B | cleanup の partial mutation 後の対象限定再入 | real・採用: admin 部分削除後の再入 test を追加 (§4) |
| 39 | A | 「無関係 alias が自 wave の `.git` bytes を複製」しても `.codex/worktrees/alias/**` が incoming に無ければ受理 | 受容 (incoming 非衝突。D109) |

**refuted (不採用):** 順番票が flock の代わりになる (A) / 交差なしなら即 commit (先行相談) / 同一 process だから実 flock 競合を再現できない (B) / 通常 cleanup が未 land の実行中 wave を消せる (B) / fold の gc_paths が collision 検査から漏れる (A) / 名前衝突だけで他 wave の admin を消す (A)。

## 2. 不変条件 (訂正版、実装子と review 子が守る)

- (a′) **協調 land による main ref / index / main worktree / fold state の mutation は common flock `<common>/dev-wave-land.lock` の内側でだけ行う。** 順番票は flock の上の順序層。順番票を知らない旧 driver と混在しても、既存の `_acquire_land_lock` → `_verify_land_lock_binding` → `_locked_preflight` → fingerprint 再計算 → receipt 再照合をすべて通るので main の正しさは変わらない。順番票の registry 更新 (短い `registry.lock`) と対象限定 cleanup は別面。
- (b′) **mutation 開始前の拒否は main を 1 bit も変えない。** admit 後の失敗 (fold rollback、recovery 失敗) は既存契約 (F977 の巻き戻し) に従い、本 wave では変えない。
- (c) 監査・fold gate 中の common flock 解放 (D254 / DW-O25) 維持。
- (d) receipt (受入・provenance・fold gate) の束縛と `_verify_*` は不変。lock 再取得後の再検査 (control 比較・fingerprint・完全 preflight・receipt 再照合・active state・closure) は 1 つも省かない。SHA / fingerprint 一致を単独の続行条件にしない。
- (e) 生存は待ち手が保持する ticket FD の `LOCK_EX` で判定する。pid / mtime / TTL は判定に使わない。TTL で生存 owner を追い越さない。
- (f′) 死亡 `mutating` 票は §3.3 の完了照合で解消する。真の途中 state (fold state file 実在) は同 key の元 request の再入だけが recovery に入り、通常 grant より優先する。二重採番・二重 commit なし。
- (g′) 先頭は各 mutation 直前 (ff 前 / `apply_fold` 前 / shape B の mark・finalize 前) に、自分が grant 保持者かつ ticket FD 生存かつ binding 不変であることを再確認する。
- (h′) 順番票に登録できるのは、現行 `_verify_acceptance_receipt` の **lock 非依存部分** (schema / authority kind / holder / tested_main・tip / argv / scheduler / env projection / verdict と rc・nodeids の整合 / fingerprint / tested-main・tip 固定 object の blob・bytes / raw digest) を通した request だけ。`non-attributable-only` 旧互換分岐は保持し `child_rc==0` へ狭めない。lock 内の完全検証 (5107) は不変で、登録時 digest との一致を要求する。
- (i) CLI flag・環境変数の knob を作らない。新定数は module 定数。
- (j) 自 wave・衝突対象・自 wave の admin binding・handoff 名前集合・fold state の検査は維持。無関係 child は名前を列挙するが実体・identity・admin binding を読まない。

## 3. plan v2 の確定事項

### 3.1 順番票 (plan §順番票の構造 を採用、補正込み)

- 置き場 `<common>/dev-wave-land-turn/` (`registry.lock` 固定 inode / `registry.json` 一時 file→fsync→rename→dir fsync / `<seq:08d>-<holder12>.jsonl` で phase 追記)。
- 生存 = ticket file への `LOCK_EX` 保持。判定は別 open file description からの `LOCK_EX|LOCK_NB` の `EWOULDBLOCK`。他の OSError は fail-closed。
- 安全条件は `_lock_metadata_is_safe` / `_verify_land_lock_binding` (2585〜2643) と同型 (nofollow、inode 照合、uid / nlink 1 / 0o022)。ticket / registry FD は子へ継承しない (`pass_fds` に含めない)。registry lock を保持したまま common lock を待たない (順序: common → 短い registry)。
- request key `(acceptance_wave, tested_tip, receipt raw sha256)` + main path / wave path / common / tested_main 一致。landing_tip は key 外 (前進 merge 後の再試行を許す)。
- **grant は非横取り**。grant 不在時に「登録済み・生存・最小 seq」を選ぶ。休止票の復帰は次の選出から元 seq。
- **terminal outcome 時の原子的引渡し (B-24):** grant を放す registry 更新と同じ更新で、その時点の待ち手 (登録済み・生存・最小 seq) へ grant を渡す。待ち手がいなければ grant 不在にする。
- **同一 key の二重起動 (A/B-19):** registry lock 内で同 key の生存 runtime ticket があれば第二の ticket を作らず `RC_LOCK_BUSY` (reason: `same request already queued`、`retryable_same_request=True`、`release_safe=False`) で降りる。
- `already-landed` no-op と recovery も順番票を取る (provenance は課さない、D254 不変)。同 key の未解決 `mutating` 票がある再入は通常 seq より優先して grant を得る (recovery 優先)。

### 3.2 rc 別の seq 処理表 (B-32)

| 終端 | ticket phase | seq 対応 | grant |
|---|---|---|---|
| `landed` / `already-landed` (finalize + postcondition 成功) | `done` | 削除 | 引渡し |
| `stale-main` (RC 10) | `waiting` へ戻す (休止) | **保持** (前進 merge 後に同 key で再開) | 引渡し |
| `lock-busy` 順番期限 (RC 11) | 休止 | 保持 | (grant 未取得なら不変 / 取得後の期限なら引渡し) |
| retryable な拒否 (provenance timeout・fingerprint 変化・identity の retryable・fold gate の retryable) | 休止 | 保持 | 引渡し |
| 非 retryable な拒否 (provenance rc≠0、監査赤、dirt、control-plane、fold gate 赤、receipt 不一致) | `rejected` | **削除** (直して新規登録) | 引渡し |
| fold 失敗 → rollback 成功 (RC 26/31 系で main 復元済) | `rolled-back` | 保持 | 引渡し |
| rollback 不完全 (RC 28) / recovery 失敗 (RC 27) / postcondition 失敗 (RC 25) | `mutating` のまま | 保持 | **通常 grant 停止** (同 key の再入だけ) |
| process 死亡 (FD 解放) | 最後の完全 record で分岐 (§3.3) | | |

### 3.3 死亡 `mutating` 票の完了照合 (A-18、B-29)

`mutating` record は次を束縛する: `main_before` (= locked_main = rollback_ref)、`landing_tip`、`wave_ref`、`trusted_main_cutoff`、`audited_digest`、`expected_fold` (plan.status が noop か否か)、fold plan の transaction_id (apply 前に判明する場合)。後続 (または同 key の再入) は common flock 内で次を順に判定する。

1. fold state file 実在 → 真の途中 state。同 key の元 request だけが既存 recovery 経路 (`active_plan is not None`) へ入る。他 key の通常 grant は停止 (`RC_FOLD_RECOVERY_FAILED` 相当の reason で降りる、main 不変)。
2. state 不在かつ `main == main_before` → 正常 rollback 済 (または ff 未実行)。票を `rolled-back` にし seq 保持、grant 引渡し。
3. state 不在かつ `main == landing_tip` かつ `expected_fold == noop` → ff 完了 (fold なし)。票を `done`、grant 引渡し。
4. state 不在かつ main の first-parent が `landing_tip` で、その commit が既存 `verify_declared_fold_commit` (trusted_main_cutoff / landed_commits / wave_tip 束縛) を通る fold commit → finalize 済。票を `done`、grant 引渡し。
5. それ以外 → fail-closed。票は `mutating` のまま、通常 grant 停止、reason に観測した main / 期待値を出す。人間または元 request の手番。

ff 完了後・state 前の死亡 (merge child が lock fd を継承して生存中) は、child が終わるまで common flock が取れないので、取れた時点で 2〜5 を判定する。

### 3.4 land() への組み込み (plan §land() への組み込み を採用、補正込み)

- 処理順: SHA / repository 検証 → 受入 receipt の lock 非依存検証 (登録前提) → 前進 merge topology / replay → ticket 登録 + grant 待ち → initial common lock → 既存 preflight / 監査 / 再検証 / plan / gate / 再検証 → mutation 前の grant・生存・binding 再確認 → 既存 ff / fold / postcondition / finalize → ticket terminal 処理 + FD close。
- `_LAND_TURN_WAIT_SECONDS = 3600.0` (1 invocation の絶対期限、`_verify_repository` 直後に 1 本だけ作る)。`_LAND_LOCK_WAIT_SECONDS = 180.0` は据え置き (累積競合待機枠、補充しない)。180 秒消費後は順番期限まで短い `_land_turn_sleep` + 1 回の非 blocking 取得を反復。**各 180 秒枠の deadline は `min(残枠, turn_deadline)`**。
- `_run_outside_land_lock`: runner は 1 回だけ。**payload の `returncode != 0` (provenance) は再取得を待たず即 `RC_PROVENANCE`** (A-17)。成功 payload は順番期限まで保持して再取得を続け、取得後に既存の全再検査を通す。期限で payload 破棄 → `RC_LOCK_BUSY` (reason に `phase`、`turn_waited_s`、`turn_elapsed_s`、`turn_limit_s`)。JSON key 集合は変えない (`limit_s` は reason 内文字列のまま)。
- 順番待ちだけで期限になった場合の reason は「another cooperative land operation holds the common lock」を使わず、`waiting for land turn (seq=N, ahead=k)` の別文面。
- mutation 開始後は時間を理由に放棄しない (既存 transaction 契約優先)。
- lease: `main()` の renew / release は不変。TTL 2400 < 3600 は新 D に明記。

### 3.5 DW-O13 (時間予算の実測分布)

母集合: `/work/1/SFC/tanab/dev-wave-jobs/**/land-*.json` 468 件 (窓付き 113 件、2026-08〜09-17 06:50)。成功 land の窓 `window_elapsed_s`: n=34、min 186 / median 272 / p90 543 / max 1,180 秒 (regime は混在: 09-17 03:00〜04:30 の手動 GO 直列は 186〜415 秒、混雑時 max 1,180)。3600 秒 ≈ 13 × median ≈ 6.6 × p90 ≈ 3 × max。**13 本が median regime で並ぶとき 1 invocation で捌ける上限**であり、p90 以上の regime では期限到達 → rc=11 → seq 保持の再投入に頼る。有限 N 本の全完了を導く数値ではない (B-35)。記録は `land-window-distribution.txt`。

### 3.6 非接触 (plan §非接触 を採用)

`_worktree_snapshot` の child loop: 名前 → protected 判定 (自 wave または `protected_paths` と重なる) → protected でなければ `continue` (`_SAFE_CHILD_RE` 検査も protected 後) → open → `_validate_admin_binding`。`observed_worktree_identities` は protected child だけ。`protected_after != protected_before`、自 wave の再 open / binding、handoff 名前集合、`_land_fingerprint` の `protected` 構築、`_registered_worktree_paths` (fold gate 隔離先) は不変。既存 test の反転は plan の表どおり (2742 / 2780 / 2865 / 6871 / 6910 は非衝突入力なら成功へ、4246 / 4272 は拒否のまま)。

### 3.7 cleanup (plan §cleanup の対象限定 を採用)

`_mutate` 979〜988 の全体 prune を、preflight で束縛した自 wave admin dir (一意性必須、複数一致は拒否) の対象限定撤去 + `_verify_record_state(absent=True)` へ。削除 helper は registry 親 FD からの相対操作、nofollow、`gitdir` backpointer 再照合、`locked` 不在、`index.lock` 等の残存で停止、preflight からの inode / backpointer 不変。`_dry_run_candidates` / `_PRUNE_LINE_RE` / prune argv 許可形は廃止。partial error 後は branch 削除へ進まない。主張は「他 wave の admin を削除しない」まで (A-22)。部分削除後の対象限定再入を test で示す (B-38)。

## 4. test 仕様 (P8 訂正版)

### 4.1 決定的 scheduler (`test_dev_wave_land.py` 内、既存 `_exercise_cumulative_waits` の隣)

- worker = thread、**同時に Python code を進める worker は 1 つ** (token)。scheduler (= pytest main thread) だけが fake monotonic clock を進める。event queue は `(time, seq, worker_index)` で全順序。
- 交代点: `_land_lock_sleep`、`_land_turn_sleep` (存在すれば、`getattr` で patch)、registry 登録 / grant 公開 / 死亡回収、監査開始・帰還、gate 開始・帰還、mutation 直前。
- **seam の実行は main thread**: patched `_audit_provenance_history` / `_run_fold_gate` は worker から scheduler へ callable を渡し、scheduler が main thread で実物を呼んで結果を返す (signal 制約の回避、DW-O14 の「実物へ委譲する観測 wrapper」)。
- 実 flock (別 open file description)、実 preflight、実 receipt verifier、実 Git mutation を使う。lock 成否を fake bool にしない。
- fixture の罠: request ごとに receipt path と `acceptance_wave` を一意に、cwd は scheduler が worker 再開直前に設定、patch は scheduler 外側で 1 回。
- in-lock 所要のモデル化: `_locked_preflight` の入口 / 出口 seam で fake clock を指定秒進める (旧 tree 負例の再現に必要、§4.3)。到着を staggered にできる。retryable rc で降りた request を同 key で再投入する policy を持つ (fake horizon 内)。
- **旧 tree 互換**: harness は新 tree にしか無い名前を `getattr(LAND, name, None)` で扱い、旧 tree でも import・実行できる。各 request の 取得 / 解放 / 監査 / gate / 累積待ち / rc / main SHA を trace に残し、assertion message に出す。

### 4.2 正例・負例 (必須 node、名前は plan の案を採用)

| node | 期待 |
|---|---|
| `test_land_turn_independent_waves_one_lands_rest_stale` | 独立 branch 8 本を同時登録。**有限 step に 1 本 `landed`**、残り 7 本は `stale-main` (lock-busy でない、seq 保持)、main == 先頭 tip、順位 = seq 順、全 FD 解放 |
| `test_land_turn_eight_requests_complete_in_sequence` | ff 可能な累積 tip 列で 8 本全 `landed`、grant / mutation が seq 順 |
| `test_land_turn_retry_preserves_sequence` | lock-busy 継続 + 外部再入。旧 seq 復帰は現 grant を奪わず、次の選出で元順位 |
| `test_land_turn_red_head_hands_over_atomically` | 先頭 provenance rc≠0 → `RC_PROVENANCE`、main 不変、**同じ registry 更新で** 次候補へ grant、先頭の seq は削除 (非 retryable)。timeout (retryable) 版は seq 保持 + 引渡し、復帰は非横取り |
| `test_land_turn_dead_waiter_releases_successor` | FD close で死亡。mtime / TTL に依らず次候補 |
| `test_land_turn_live_owner_is_not_expired` | clock を 3600 秒以上進めても生存 owner を追い越さない |
| `test_land_turn_mutation_rechecks_owner` (ff / fold / shape-B の 3 parameter) | mutation 直前に ticket 差替え / FD 喪失 / grant 不一致 → その mutation を開始しない |
| `test_land_turn_preserves_evidence_after_lock_budget` (provenance / fold の 2 parameter) | 帰還後に旧 holder が 180 秒超保持 → 解放後に runner 再実行なしで成功 |
| `test_land_turn_red_provenance_fails_fast` | 非ゼロ provenance payload は再取得を待たず `RC_PROVENANCE` |
| `test_land_turn_invalidates_changed_inputs` | 待機中に main / tip / collision / fold state を変更 → 旧 receipt で進まず既存の拒否 |
| `test_land_turn_recovery_precedes_successor` | state 永続化後・commit 前の死亡 → 次候補停止、元 request の recovery 優先。transaction ID / 採番 / FOLDED record / commit 数を確認 |
| `test_land_turn_dead_mutating_resolved_by_observation` (rolled-back / ff-done / finalized の 3 parameter) | §3.3 の 2〜4 を後続が解消し main 不変で grant 引渡し |
| `test_land_turn_same_key_double_entry_is_single_ticket` | 同 key 同時再入で ticket は 1 つ、第二は `RC_LOCK_BUSY` 別文面 |
| `test_land_turn_rejects_invalid_acceptance_before_registration` | 登録前検証赤 → ticket 未作成・seq 未消費・initial lock 未取得・provenance 未起動 |
| `test_land_ignores_unrelated_child_cleanup_race` | container open 後に無関係 child の `.git` 消失 → foreign child open が呼ばれず成功。自 wave 差替え・incoming 衝突 child は拒否 |
| `test_cleanup_preserves_foreign_stale_admin` (cleanup test) | 自 wave 撤去、他 wave の live / stale admin と branch は bytes・inode とも保持 |
| `test_cleanup_partial_admin_removal_reenters` (cleanup test) | admin 部分削除後の再入が対象限定で完了し、branch 削除へ先走らない |
| subprocess 死亡 1 本 | 実 process 死亡で FD 解放 → 次候補 (thread harness と別) |

lease TTL 跨ぎの CLI test (他 holder の lease を消さない、land 結果と release 結果を区別) を 1 本。

### 4.3 旧構造の負例 (P7 訂正版)

親が段 6 で実測する probe: base tree (abc7085ae) の container worktree に新 harness (test file) だけを重ね、同じ scheduler policy (staggered 到着 + in-lock 所要 + retryable rc の再投入、fake horizon 4,560 秒 = 76 分) で `test_land_turn_independent_waves_one_lands_rest_stale` 相当を走らせ、**landed 0・main 不変・全 request が lock-busy または証拠破棄で終わる** trace を記録する。旧 tree で新 hook に到達しないことによる ImportError / AttributeError は負例にならない (harness は旧 tree で走り切ること)。記録は insight へ。M1 は「先頭 gate の必要性」の変異で、旧構造の全停止再現とは別 (B-36)。

## 5. 変異 matrix の事前登録 (M0 + M1〜M11、DW-M01)

anchor は変更前の行。author 後に exact 置換箇所・nodeid・差分 digest を登録し直す。**専属帰属は実装後に node 単独結果で判定** (B-34)。既存 test が同時に赤になる変異は「新 node も KILLED」を記録し、新 node 単独の結果を併記する。後段 verifier が同じ拒否を返す等価変異は KILLED と数えず再照準する (F820 / F28)。

| ID | 対象 | 変異 | 期待 KILLED node |
|---|---|---|---|
| M0 | `_land_lock_now` 付近 (2573) | comment のみ | 等価対照、SURVIVED |
| M1 | 新 grant gate (initial lock 前) | 後続も initial へ進める | `test_land_turn_eight_requests_complete_in_sequence` (順序違反 / grant 前流入) |
| M2 | 登録 helper | 再入ごとに新 seq | `test_land_turn_retry_preserves_sequence` |
| M3 | 生存 helper | FD lock でなく mtime / TTL | `test_land_turn_live_owner_is_not_expired` |
| M4a / M4b / M4c | ff 前 / apply 前 / shape-B 前の再確認 | 各 1 箇所を省略 | `test_land_turn_mutation_rechecks_owner[ff|fold|shape-b]` |
| M5 | 死亡票処理 | `mutating` を通常死亡票として削除 | `test_land_turn_recovery_precedes_successor` |
| M6a / M6b | `_run_outside_land_lock` | 180 秒後に payload 破棄で即 return | `test_land_turn_preserves_evidence_after_lock_budget[provenance|fold]` |
| M7a / M7b | 5073 / 5361 の fingerprint 比較 | 不一致を受理 | `test_land_turn_invalidates_changed_inputs[...]` (後段で拒否されるなら等価として再照準) |
| M8 | child loop | 無関係 child も open + binding | `test_land_ignores_unrelated_child_cleanup_race` |
| M9 | 自 wave 差替え検査 (1630 / 2623 のどちらか 1 箇所) | 外す | `test_provenance_audit_rejects_own_worktree_replacement` (4246) + 新 mutation 前自己差替え test。他層で覆われ SURVIVED なら再照準 |
| M10 | cleanup 対象限定撤去 | 全体 prune へ戻す | `test_cleanup_preserves_foreign_stale_admin` (argv 禁止 test は補助) |
| M11 | 登録前検証 | 省略 | `test_land_turn_rejects_invalid_acceptance_before_registration` |
| M12 | terminal の原子的引渡し | grant 解放と引渡しを分離 (解放→再選出) | `test_land_turn_red_head_hands_over_atomically` (timeout 版) |
| M13 | provenance 非ゼロの早期終端 | 期限まで待つ (旧疑似コード) | `test_land_turn_red_provenance_fails_fast` |

## 6. docs 変更 (段 7)

- 新 D (spool fragment、番号は fold 時): (1) D432 / D1996 を supersede — 順番票、非横取り grant、原子的引渡し、3600 秒期限と 180 秒の位置付け (総待ち上限でなくなる)、lock-busy による証拠破棄の撤去、rc 別 seq 処理、死亡票の完了照合、進行保証の前提 (新 driver 同士・旧 driver の妨害終息・先頭が有限時間で進む・元 request の再入・registry lock の公平性は OS 依存)、lease TTL < 順番期限。(2) D109 部分改訂 — 無関係 child の実体 / admin 観測と同名差替え拒否を外す。(3) D702 部分改訂 — 自己撤去は維持、全体 prune を自 admin 限定へ。D254 / D1393 / D662 / receipt 再利用条件は不変。
- 新 F: 2026-09-16 21:09〜22:25 の 76 分着地ゼロ (取得競争と snapshot race を区別)。
- DW-O23 / O25 / O28 は不変更。`check_docs.py` の予算・pin は緩めない。

## 7. 裁定パッケージ候補 (scope 外、ユーザーへ返す)

1. 元 request 不在の fold 途中 state を他 wave が自動復旧する主体 (cwd / binding / receipt / 起動主体 / 結果帰属)。
2. 生存 hang の先頭を止める・停止確認する・引き継ぐ監督主体 (TTL 追越しは不採用)。
3. fold 子 process (`git add` / `git commit`) が lock fd を継承しない既存境界。
4. lease 保持を land 待機全体へ広げる契約 (定期 renew / 再 claim)。
5. 新 receipt でも wave の順位を引き継ぐ契約 (request 同一性の裁定)。
6. 共有 admin 一覧 (`_administrative_gitdirs_for_wave` / porcelain) の完全非接触化。

## 8. 段 5 の分割

- U1 (author、workspace-write): `tools/dev_wave_land.py` + `orchestrator/tests/test_dev_wave_land.py`。
- U2 (author、workspace-write、別 worktree): `tools/dev_wave_cleanup.py` + `orchestrator/tests/test_dev_wave_cleanup.py`。
- 親: merge / add / commit、焦点走、旧 tree probe、変異、受入、docs。

## 9. 追補 (段 6 の実測による裁定の訂正・補正)

- **#17 / §3.4 訂正 (08:10):** 非ゼロ provenance payload の即終端は維持するが、rc / flag は既存 `_verify_provenance_receipt` の分類に従う (`_PROVENANCE_VIOLATION_RC` だけ非 retryable、他の非ゼロ = infra / signal / timeout は retryable)。既存 test 2 本の期待が正。
- **§4.2 / fixture (08:29):** `test_provenance_checker_missing_and_symlink_components_are_rejected_clean` の ancestor-symlink case は `tools` 全体が symlink で受入 receipt が原理的に成立しないため、登録前提 h′ により rc=23 (登録時拒否、main 不変) へ期待値を変える。'missing' case は有効 receipt で rc=29 を維持。symlink 祖先の束縛拒否は `_bind_provenance_checker` の直接 test で保つ。
- **N1 の範囲 (09:05):** 同 key 再入の完了観測で解消するのは ticket の状態だけ。LandResult は既存経路 (preflight → already-landed / D16 postcondition) から返す (fix-3 の早期 return は D16 gitlink test 4 本を退行させた)。
- **poll の I/O (09:05):** `_turn_registry` は内容が変わったときだけ保存する。実測: `/tmp` (xfs、load 55) で 1 保存 37 ms、poll ごと保存では 8 本の正例 node が runner 外で 270 秒 (runner 内は数秒)。
- **§3.2 補正 — order の回転 (09:20):** 「再試行で順位を失わない」は grant を得る前の終端 (順番期限 lock-busy、registry busy) に適用し order を完全保持する。grant を消費して終端した request (stale-main、retryable 拒否、rollback 成功) は seq (identity) を保ちつつ order をその時点の発行済み最大 seq の後ろへ回す (新規到着より前)。根拠: fix-4 後の新 tree probe `storm-e` で、独立 branch の request 1 / 2 が stale-main 再入で先頭を交互に占め、seq 4〜13 の 10 本が 3600 秒の順番期限で `lock-busy` (probe-new-6.json)。
- **旧 tree 負例 (08:46):** policy `storm-e` (13 本、20 秒間隔、in-lock 240 秒、監査 430、gate 130、rc=11 は 120 秒後に再投入、fake 4560 秒) で旧 tree abc7085ae は着地 0・main 不変・監査 18 回・終端 151 回 (全 rc=11、最終 initial 12 / post-provenance 1)。in-lock 30〜200 秒の policy では 1 本着地するので、嵐の本体は「lock 内作業 > 180 秒 + 到着率 > 処理率」。新 tree (fix-4) の同 policy: 着地 1・監査 1。
- **U2 (08:05):** Lustre (`/work`, `/home`) は `renameat2(RENAME_NOREPLACE)` が EINVAL。journal の no-replace 公開は `os.link` + unlink (実 `.git` dir で probe 済み: EEXIST / nlink 2→1)。
