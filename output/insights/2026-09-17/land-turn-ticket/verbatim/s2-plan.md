## 前提の検算

**3 点の scope は妥当。ただし P1/P2/P3/P8 は、そのままでは両立しない部分があり、以下の補正が必要である。** 本段は静的調査のみ。ファイル変更、Git 状態変更、pytest 実行はしていない。

以下の `file:line` は指定 worktree の現物を指す。略記は次のとおり。

- `land`＝`tools/dev_wave_land.py`
- `cleanup`＝`tools/dev_wave_cleanup.py`
- `window`＝`tools/wave_land_window.py`
- `land-test`＝`orchestrator/tests/test_dev_wave_land.py`
- `cleanup-test`＝`orchestrator/tests/test_dev_wave_cleanup.py`

検算結果：

| 論点 | 現物と計画への反映 |
|---|---|
| 3 回の lock 取得 | initial は `land:4982`、監査後は `5016`、fold gate 後は `5302`。非 noop fold 経路で最大 3 回であり、全経路が 3 回ではない。 |
| 180 秒 | `land:2645` と `4059` は累積競合待機。監査・gate 時間を差し引かず、期限後も最初の非 blocking 取得は試す。 |
| ff mutation | `land:5567` 付近の **`git merge --ff-only`**。通常 ff の直前に `update-ref` はない。`update-ref` は rollback 側の話である。 |
| receipt 検証位置 | 完全な受入検証は `land:5107`、通常は provenance 後。登録前提の導入には実際の切出しが必要。 |
| `locked_main` 依存 | `land:1060` 付近の bootstrap launcher が、現在 main に存在しないことの検査。1053〜1075 全体を省略してはいけない。 |
| 無関係 worktree | membership は既に snapshot 等価比較・fingerprint から外れている。しかし `land:1676` 以降は無関係 child も開き、`1691` の binding 検証へ進む。 |
| P5 の「名前も読まない」 | `listdir` と protected 判定には名前が必要。正しくは「名前は列挙するが、無関係 child の実体・identity・admin binding を読まない」。 |
| recovery | `land:5144`、`5146` は元 `wave_ref` と着地 tip の一致を要求する。別 wave の通常 request をそのまま recovery に使えない。 |
| JSON | `waited_s`／`window_elapsed_s` は JSON field。**`limit_s` は現状 reason 内の文字列であり JSON field ではない**（`land:239`、`4879`）。 |
| lease | CLI は `land:5664` 以降で renew、`5697` 以降で条件付き release。`land()` の入場権ではないが、副作用はある。 |
| 旧 ticket | `window:126` が「旧版 ticket の release 時掃除用」と明記。現行待ち行列として再利用できない。 |
| M0 | comment だけの等価変異は **SURVIVED が期待値**。「全 KILLED」は非等価変異に限定する。 |

76 分着地ゼロ、手動 GO の所要は brief の報告値として扱う。本段では原ログから再集計していない。

さらに、次の三つは仕様上の要補正点である。

1. **死亡票を完全削除すると、同一 request の外部再試行で seq を復元できない。**
2. **180 秒を総競合待機の厳密な上限として維持しながら、競合したまま 3600 秒まで待つことはできない。**
3. **独立 branch の固定 request 8 本は、FIFO 化だけでは全件 land できない。** 先行 land 後の stale-main と通常の wave-side merge は残る。

## 順番票の構造

**common git-dir 配下を採用する。** 追加する private 型・helper は `land:287` の handle 群と `2573`〜`2860` の lock helper 群に置く。

| 候補 | 束縛・運用上の評価 |
|---|---|
| `<common>/dev-wave-land-turn/` | `_Repository.common_fd` から相対 open でき、既存 lock と同じ common inode に束縛できる。lease 未設定でも動く。採用。 |
| `IZANAGI_WAVE_LEASE_DIR` 配下 | 別 root の identity 検証、common との対応付け、未設定時の扱いが必要。異なる指定で queue が分裂しうる。受入 lease の旧 ticket cleanup とも分離が必要。不採用。 |

構造案：

```text
<common>/dev-wave-land-turn/
    registry.lock
    registry.json
    <seq:08d>-<holder12>.jsonl
```

P1 の `.json` は、**lock inode を保持したまま phase を crash-safe に追記するため `.jsonl` に補正する**。

- `registry.lock` は固定 inode の regular file。短時間の `LOCK_EX|LOCK_NB` で採番・登録・grant 更新を直列化する。
- `registry.json` は `next_seq`、request key と seq の対応、現在の grant、未解決 recovery 対応を保持する。固定 lock file と可変データ file を分け、データ更新は一時 regular file→fsync→rename→directory fsync。
- ticket は `O_CREAT|O_EXCL|O_RDWR|O_NOFOLLOW` で作成し、登録公開前に待ち手が `LOCK_EX` を取得する。以後 terminal outcome まで FD を保持する。
- seq は整数で比較する。8 桁は最低表示幅であり、辞書順や固定桁上限に依存しない。
- `holder12` は表示・名前用。request 同一性の判定には使わない。

ticket 初期 record：

- schema、seq、acceptance_wave、tested_main、tested_tip、landing_tip
- acceptance receipt の raw SHA-256
- main/wave の絶対 path、wave ref、request の audited commits
- pid〔診断用のみ〕
- `phase=waiting`
- record 番号と破損検出用 digest

request key は **`(acceptance_wave, tested_tip, receipt_sha256)`**。wave path／common／tested_main も一致を検査する。landing_tip は順位の key に含めず、既存規則による前進 merge 後の再試行を許す。ただし、変更された landing_tip に旧 provenance／fold receipt を流用しない。

生存判定は、別の open file description からの `LOCK_EX|LOCK_NB` に対する競合で行う。pid、mtime、TTL は判定に使わない。`EWOULDBLOCK` 以外の失敗を「生存」「死亡」に畳まない。

安全条件は `land:2585`、`2594`、`2842` と同型にする。

- directory は nofollow open、保持 FD と現在 path の inode を照合。
- regular file は uid、nlink=1、group/world writable 禁止を両側で検査。
- registry lock 取得後、ticket 登録／再開時、grant 取得時、mutation 直前に再束縛。
- ticket／registry FD は子へ継承しない。
- registry lock を保持して common lock の取得を待たない。mutation 前は common lock→短い registry lock の順とする。

**先頭選出と再試行は、grant を非横取りにする。**

- grant 不在時に、生存・登録済み ticket の最小 seq を選ぶ。
- grant は initial→監査→gate→mutation／terminal outcome まで保持する。
- 同一 invocation の lock-busy 待ちは同じ ticket・同じ grant を保持する。
- 外部再試行のために、休止した request の seq 対応を registry に残す。休止票は選出対象にしない。
- 古い seq の request が再開しても、**既に動いている grant は奪わない**。次の選出から元 seq を使う。

これは P2 の「常に生存票の最小 seq」を補正する。休止票の復帰が実行中 owner を失効させる設計では、証拠保持を自分で壊してしまう。

死亡票は登録・選出時に待ち手が回収する。ただし phase record の最後の完全な record を使い、次の区別をする。

| 最終 phase | 処理 |
|---|---|
| `waiting`／`validating` | runtime ticket を回収し、次候補を選出可能にする。再試行用 seq 対応は残す。 |
| `mutating` | 通常 grant を止め、common lock 内で fold state と main を確認する。 |
| `done`／確定した mutation 前拒否 | ticket と不要な seq 対応を削除可能。 |
| 初期 record 破損・対応不明 | 推測して飛ばさず fail-closed。 |

phase は同一 ticket inode へ追記して fsync する。`mutating` record の永続化成功前には mutation へ進まない。末尾の書込み途中 record は、最後の完全 record より後の未完更新として扱う。`mutating` の後の完了 record が未完なら、保守的に recovery 対象に残る。

marking は両方に必要である。

- **ff 前**：`land:5567` の merge 呼出し直前。
- **fold apply 前**：`land:4562` 付近の `fold.apply_fold` 直前。実 state 永続化は `tools/spool_fold.py:3294`。

既存 recovery／already-landed 後の fold も後者を通す。完了 marking は postcondition と finalize が成功した後に限る。

**旧 driver 混在時の正しさは既存 common flock が守る。** 新 driver は順番票だけで ff／apply を実行せず、必ず `_acquire_land_lock` と再検証を通る。旧 driver が監査中に common lock を取り main を変えれば、新 driver は `land:5073` または `5361` の fingerprint 不一致で拒否する。merge child への継承も既存 `pass_fds=(lock.fd,)` を維持する。FIFO の保証対象は新 driver 同士だけである。

## land() への組み込み

`land:4912` に `_LandTurnHandle`、単一の `turn_started`／`turn_deadline`、順番待機実績を追加する。deadline は `_verify_repository` 成功直後の `land:4964` 付近で一度だけ作る。

処理順：

1. SHA と repository の検証。
2. lock 非依存の受入 receipt 検証。
3. 既存の前進 merge topology／replay 検証。
4. ticket 登録、grant 待ち。
5. initial common lock 取得。
6. 既存 preflight、監査、再検証、plan、gate、再検証。
7. mutation 前の grant／生存／binding 再確認。
8. 既存 ff／fold／postcondition／finalize。
9. ticket の terminal 処理、FD close。

topology／replay 赤の request が grant を長く占めないよう、可能な検査は登録前に済ませる。plan 作成 `land:5275` は common lock 内のままである。

**P3 の予算は、次の二層として明文化する案を採る。**

- `_LAND_TURN_WAIT_SECONDS=3600.0`：登録・順番・再取得待ちに共通の絶対期限。更新しない。
- `_LAND_LOCK_WAIT_SECONDS=180.0`：既存 backoff による累積競合待機枠。取得ごとに補充しない。
- 180 秒を使い切った後は、順番期限までの継続待機へ移る。短い `_land_turn_sleep` と一回の非 blocking 取得を反復する。
- **実際の common-lock 競合待機は 180 秒を超えうる。** 新 D では「180 秒は総実待ち上限ではなくなる」と明記する。単なる予算の付け替えで旧契約を維持したとは説明しない。

`_run_outside_land_lock`（`land:4059`）は runner を一度だけ呼び、その payload を保持して取得 loop を回す。

```text
lock.close()
payload = runner()                  # 一回だけ
while turn_deadline 内:
    grant・ticket binding を確認
    残る180秒枠、または単発tryで common flock取得
    取得できたら payloadを返す
    未取得FDをclose
    順番待機のsleep
期限なら payloadを破棄して rc=11
```

initial も同じ取得 helper を使う。これにより「rc=11 は順番期限で返す」を統一できる。監査赤、gate 赤、identity 拒否は期限まで待たせず、既存の赤として返す。

取得失敗のたびに main HEAD や control snapshot を読む必要はない。**取得後**に既存の比較を実行する。

- provenance：`land:5033`〜`5098` の control 比較、fingerprint 再計算、完全 preflight、receipt 検証を維持。
- fold gate：`land:5333`〜`5404` の control／fingerprint／active state／closure／receipt 検証を維持。
- `main`／wave HEAD が同じでも collision、binding、checker／registry bytes、fold state 等が変われば既存どおり拒否する。「SHA だけ不変なら再利用」にはしない。
- provenance fingerprint 不一致は既存 `RC_PROVENANCE`／retryable を使う。
- fold fingerprint 不一致は現状 `_FoldGateFailure` の既定値が `retryable_same_request=False`（`land:388`）。**既存ですべて retryable という前提は誤り**。本変更ではその分類を勝手に変えない。

待ち期限は処理全体を強制停止する watchdog ではない。mutation 開始前なら期限切れで降りる。mutation 開始後は時間を理由に途中放棄せず、既存 transaction の完了／rollback／recovery 契約を優先する。

JSON の key 集合は維持する。

- `waited_s`：common lock の実競合待機累積。180 秒後の継続分も含む。
- `window_elapsed_s`：既存どおり initial lock 窓以降の経過。
- reason に `turn_waited_s`、`turn_elapsed_s`、`turn_limit_s=3600` を追記する。
- 順番待ちだけで終了した場合は、既存の任意 timing fields を省略し、reason に実績を出す。
- `limit_s=180` は既存の意味を新 D で補足する。純粋な順番待ち timeout に「common lock を他者が保持」と虚偽の reason を使わない。

`land-test:3272`、`3320`、`3488`〜`3558` の reason／取得回数／rc 期待は更新が必要である。

lease は `main()` の開始時 renew と終端 release を維持する。3600 秒は TTL 2400 秒を超えるため、**待機中の lease 保持は保証しない**。land 順番票は失効しない。定期 renew や再 claim は本 scope に追加しない。

release は `land:5735` の `expected_main_sha=request.tested_main_sha` を維持する。着地 tip や待機後 main へ置換しない。他 holder／異なる main の lease を消さない既存検査を、TTL を跨ぐ CLI テストで確認する。

## 登録前提

`land:940` の verifier を次の内部境界へ分割する。

- `_verify_acceptance_static(repository, raw, acceptance_wave, tested_main, tested_tip)`
- `_verify_acceptance_locked_authority(repository, validated, locked_main)`
- 外向けの `_verify_acceptance_receipt(...)` は両方を必ず実行する。

static 側へ移すもの：

- schema、authority kind、holder と wave の一致
- tested_main／tested_tip、argv、scheduler、環境投影
- verdict と rc／nodeids の整合
- pre/post fingerprint
- tested-main／tested-tip の固定 object に対する launcher、waiter、runner、checker の blob／実行 bytes 検査
- raw receipt digest

bootstrap 分岐では、tested_main に launcher が無いことと tested_tip launcher の検査は static 側で行う。**現在 locked_main に launcher が無いことだけを lock 内へ残す**。`locked_main=tested_main` を渡して既存関数を流用する案は、検証済み範囲が曖昧になるため採らない。

登録後も `land:5107` の完全検証を維持し、登録時 digest と完全検証時 digest の一致を要求する。fold gate 後にも完全受入検証と digest 一致を確認し、登録した証拠の差し替えを黙認しない。

「受入緑」は現行 verifier の受理契約に従う。現物には `non-attributable-only` の旧互換分岐（`land:1025`）もあるため、登録 helper だけで `child_rc==0` に狭める変更は混ぜない。この扱いは新 D に明記し、receipt 再利用条件の変更と区別する。

追加テストは「赤なら最終的に拒否」だけでは弱い。**ticket 未作成、seq 未消費、initial common lock 未取得、provenance 未起動**まで観測する。

## 非接触

`land:1663` 付近の loop を次の順へ変更する。

```text
名前から child_relative／child_path を構成
protected = 自 wave または protected_paths と重なる
protectedでなければcontinue
安全な名前を確認
protected_beforeへ追加
childをopen
_validate_admin_binding
identities／prefixes／observedへ追加
```

無関係 child の名前形を理由に拒否しないため、`_SAFE_CHILD_RE` の検査も protected 判定後へ移す。`names_after` 側も同じ predicate を使う。

- 自 wave の独立した再 open／binding 検証 `land:1630`〜`1647` は維持。
- `protected_after != protected_before`（`land:1728` 付近）は維持。
- `observed_worktree_identities` は protected child だけを保持する。
- `_surviving_worktree_bindings_unchanged`（`land:1757`）は protected child の同名差し替え検査として残す。現状等価比較と重複しても、今回削除しない。
- `_land_fingerprint`（`land:1983`）の `protected` 構築は変更しない。`worktree_prefixes` は現状から protected child だけなので、この変更で集合は縮まらない。
- handoff の名前集合と directory identity 比較（`land:1533`）は維持。

race は `land:1649` の container open→`1676` の child open→`1691` の binding→`1226` の `.git` read で起きる。無関係 child を `1676` より前で除外すれば、その child の `.git` 消失に land が接触しなくなる。`FileNotFoundError` を binding 全体で握り潰す変更は不要である。

テスト期待値：

| 既存 test | 変更後 |
|---|---|
| `land-test:4203` unrelated appearing | `landed` のまま。 |
| `land-test:4224` unrelated disappearing | `landed` のまま。 |
| `land-test:4246` own replacement | `RC_CONTROL_PLANE` のまま。 |
| `land-test:4272` overlapping appearing | 拒否・main 不変のまま。 |
| `land-test:6871` around status | `file` は成功のまま。foreign `directory` は **成功へ反転**し main==tip を確認。 |
| `land-test:6912` after collision inspection | 同様に foreign `directory` を成功へ反転。test 名・docstring も変更。 |
| `land-test:2742` unregistered alias | 無関係なら成功へ反転。衝突する alias の負例を別途保持。 |
| `land-test:2780` ignored unregistered child | 無関係なら成功へ反転。 |
| `land-test:2865` unsafe foreign name | 無関係なら成功へ反転。protected の不正名は拒否する対照を追加。 |

`_registered_worktree_paths`（`land:3460`）は fold gate の隔離先を守る別の一覧である。`land-test:9271`、`9316`〜`9470` の absent registration／missing `.git`／第三 worktree overlap 検査は変更しない。

## cleanup の対象限定

`cleanup:979`〜`988` を、**事前に束縛した自 wave の admin directory のみの撤去**へ置換する。

1. `_preflight`（`cleanup:782`〜`852`）で admin path を確定する。live wave は `verified.identity.gitdir`、stale wave は `_stale_administrative_gitdir`。
2. `_administrative_gitdirs_for_wave`（`609`）による対応確認は、live／stale とも一意性を要求する。複数一致なら全削除せず拒否。
3. admin directory の保持 FD／inode、`gitdir` backpointer、`commondir` を記録する。
4. 既存 unlock→detach→clean／occupancy 再確認→wave directory 撤去を維持する。
5. admin 撤去直前に同じ実体を再検証する。
6. 自 admin directory のみを削除し、`_verify_record_state(absent=True)`（`897`）を実行する。
7. 既存 branch 再確認→`git branch -d`→postcondition を維持する。

直接削除の条件：

- `<common>/worktrees/<単一直下名>` に閉じること。symlink／別 inode／別 common を拒否。
- `gitdir` backpointer が自 wave の `.git` を指すこと。
- wave path が `lexists` でも存在しないこと。
- `locked` marker が無いこと。既存の明示 unlock 後に再出現した lock を無視しない。
- `index.lock` 等の進行中操作の残存を削除して進めない。
- 自 admin の inode・backpointer が preflight から変わっていないこと。
- partial error 後に branch 削除を続けないこと。

削除 helper は親 registry FD に対する相対操作を使い、symlink を辿らない。既存 `shutil.rmtree` を path 文字列だけで呼ぶ差替えでは、束縛の説明が不足する。

`_dry_run_candidates`（`cleanup:874`）と `_PRUNE_LINE_RE` は廃止する。`_validate_git_argv`（`206`）から dry-run／実 prune の二つの許可形も除く。これは M10 の検出を強くする。

なお `_administrative_gitdirs_for_wave` は現状、他 admin の `gitdir` も読む。**対象限定 mutation には使えるが、cleanup 全体が完全非接触になるわけではない。** 本 scope の主張は「他 wave の admin を削除しない」までとする。

テスト更新：

- `cleanup-test:1072` は、自 wave cleanup 成功・他 wave directory／admin／branch 保持へ反転。
- 他 wave の **directory 不在の stale admin** も追加する。live directory だけでは全体 prune 復活を確実に殺せない。
- `cleanup-test:252` の再入状態 a〜e は、prune 呼出し期待から自 admin 撤去期待へ変更。
- `cleanup-test:1159` の allowlist パラメータから prune を除き、明示禁止テストを足す。
- `cleanup-test:1218` の phase 注入は `prune-dry-run`／`prune` を `admin-recheck`／`admin-remove` へ置換し、registry failure 後に branch を消さない期待を維持する。

## test の形

**thread＋決定的 scheduler を採用する。** 同期関数 `land()` を coroutine 化すると production の広範な変更が必要になる。

Linux の `flock` は open file description 単位であり、同一 process が同じ file を別々に open した FD 同士も競合する。`dup`／`fork` で同じ description を共有する場合とは異なる。この意味論は [Linux man-pages の flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html) で確認した。本段で実 flock probe は実行していない。

`land-test:3414` の fixture を次の形で拡張する。

- scheduler が `Condition` と実行 token を持ち、同時に Python コードを進める worker は一つ。
- global fake monotonic clock と、worker ごとの次の実行可能時刻を分ける。8 本の sleep を単純加算しない。
- `_land_lock_sleep`／新 `_land_turn_sleep` は次イベントを登録して yield。
- 登録、grant、監査開始／帰還、gate 開始／帰還、mutation 直前にも test 側 wrapper で交代点を置く。
- registry の短い lock は有限 step で必ず解放する schedule にする。
- real flock、real preflight、receipt verifier、Git mutation を使う。main lock の成否を fake bool へ置換しない。

既存 fixture の罠を先に直す。

- `_Repo._acceptance_receipt`（`land-test:375` 付近）は全 request が同じ `acceptance-receipt.json` を上書きする。wave／request ごとに別 path を用意する。
- `acceptance_wave` の既定値も全員 `test-wave`。8 本で一意にする。
- `_land_real_gate`／`_cwd`（`468`／`129`）の並行利用は禁止。cwd は process 全体で共有される。scheduler が worker 再開前に cwd を設定し、一つだけ実行する。`_verify_repository` の exact cwd 検査は fake にしない。
- `_patched_land_attr`（`4858`）を worker ごとにネストしない。patch は scheduler 外側で一度だけ行う。

主要 test と期待値：

| 新 node 案 | 内容・期待 |
|---|---|
| `test_land_turn_eight_requests_complete_in_sequence` | まず ff 可能な累積 tip 列を fixture で作り、8 request を同時登録。全件 `landed`、grant／mutation が seq 順、有限 step、FD 解放。固定独立 branch の stale を公平性の失敗と混同しない。 |
| `test_land_turn_independent_waves_retry_after_main_advance` | 独立 branch を使う対照。stale は拒否し、test 側の通常 wave-side merge と再 request 後に完了。driver が merge を自動化したとは扱わない。 |
| `test_land_turn_retry_preserves_sequence` | lock-busy 継続と外部再入の双方を確認。古い seq が復帰しても現 grant を奪わず、次の選出順位を保つ。 |
| `test_land_turn_red_head_releases_successor` | provenance rc≠0 は `RC_PROVENANCE`、main 不変。次の受理可能候補が進む。 |
| `test_land_turn_dead_waiter_releases_successor` | FD close で死亡させる。mtime／TTL に依存せず次候補が進む。 |
| `test_land_turn_live_owner_is_not_expired` | clock を 3600 秒以上進めても、別 worker が生存 owner を追い越さない。owner 自身が終了した後だけ交代。 |
| `test_land_turn_mutation_rechecks_owner` | ff／fold apply 直前に ticket 差替え、FD lock 喪失、grant 不一致を注入し、その mutation を開始しない。 |
| `test_land_turn_preserves_evidence_after_lock_budget` | provenance／gate の各帰還後に旧 holder を 180 秒以上保持。その後解放。runner 各一回のまま成功。 |
| `test_land_turn_invalidates_changed_inputs` | 待機中に main／tip／collision または fold state を変更。旧 receipt で進まず既存の拒否を返す。 |
| `test_land_turn_recovery_precedes_successor` | state 永続化後・commit 前の死亡で次候補を止め、元 request の recovery を優先。その後だけ次候補を進める。transaction ID、採番、FOLDED record、commit 数を確認。 |
| `test_land_ignores_unrelated_child_cleanup_race` | container open 後の `.git` 消失を注入。foreign child open が呼ばれないことと成功を確認。旧実装では child open 直後に `.git` を消す注入も発火させる。 |
| `test_cleanup_preserves_foreign_stale_admin` | 自 wave は撤去、他 wave stale admin は bytes／inode とも保持。 |

fold crash は `Exception`／`KeyboardInterrupt` だけでは模擬できない。`land:4650` 付近が rollback するためである。thread harness では専用 `BaseException` で通常 rollback を通さず FD を閉じる crash 注入を使い、**別途一つの subprocess 終了テスト**で実 process 死亡も確認する。commit 後・mark 前と finalize 前も既存 recovery テストへ接続する。

recovery の意味は限定する。現行コードを維持する案では、死亡した元 request の再起動を scheduler が投入する。**他 wave が自動で元 request を起動する機構までは、この正例から主張できない。** その未確定点は後述する。

旧構造の負例は P7 の二本立てを採る。ただし同一 schedule とは、全員を無条件に同時監査させる barrier ではなく、**到達したイベントに反応する同じ scheduler policy**である。新構造では後続が監査に到達しないため、全員到達 barrier は deadlock する。

変更前 tree の「8 本とも予算切れ・main 不変」は親の probe で実証する。M1 は先頭 gate の必要性を恒久化するが、証拠保持が残る M1 単独で旧構造の全停止まで再現できるとは限らない。M1 と旧版全体の負例を同一視しない。

## 変異 matrix の事前登録候補

**M0＋M1〜M11 の計 12 件。** 行番号は変更前 anchor。author 後、各置換箇所・exact nodeid・差分 digest を登録し直す。新 node の接頭辞は前節のものを使う。

| ID | 対象 anchor | 変異 | 期待 |
|---|---|---|---|
| M0 | `land:2573` 付近 | comment のみ変更 | 全焦点走成功、SURVIVED。等価対照。 |
| M1 | `land:4979` 前の新 grant gate | 後続も initial へ進める | `test_land_turn_eight_requests_complete_in_sequence` が grant 前監査流入／順序違反で KILLED。 |
| M2 | `land:4964` 後の登録 helper | 再入ごとに新 seq を発行 | `test_land_turn_retry_preserves_sequence` が KILLED。 |
| M3 | `land:2573` 付近の生存 helper | FD lock でなく mtime／TTL 判定 | `test_land_turn_live_owner_is_not_expired` が KILLED。 |
| M4 | `land:5567`、`4562` の共通 mutation guard | mutation 直前の先頭・生存再確認を省略 | `test_land_turn_mutation_rechecks_owner` の ff／fold parameter が KILLED。 |
| M5 | 新死亡票処理、`land:5126` 接続 | `mutating` を通常死亡票として削除 | `test_land_turn_recovery_precedes_successor` が「元票保持・後続未入場」の assertion で KILLED。 |
| M6 | `land:4059` | 180 秒後に payload を捨て即 return | `test_land_turn_preserves_evidence_after_lock_budget` の provenance／fold parameter が KILLED。 |
| M7 | `land:5073`／`5361` の対象一箇所 | fingerprint 不一致を受理 | `test_land_turn_invalidates_changed_inputs` の対応 parameter が KILLED。後段 verifier でも拒否される変異なら等価として再設計。 |
| M8 | `land:1663`〜`1691` | 無関係 child も open／binding 検証 | `test_land_ignores_unrelated_child_cleanup_race` が KILLED。 |
| M9 | `land:1630` または `2623` 付近の対象検査 | 自 wave 差替え検査を外す | `land-test:4246` と新 mutation 前自己差替え test。別検査に覆われ SURVIVED なら、無理に KILLED と数えず置換対象を再検討。 |
| M10 | `cleanup:979`〜`988` | 自 admin 撤去を全体 prune へ戻す | `test_cleanup_preserves_foreign_stale_admin` と argv 禁止 test が KILLED。 |
| M11 | `land:4964` 後 | 登録前の受入検証を省略 | 新 `test_land_turn_rejects_invalid_acceptance_before_registration` が seq 未消費／ticket 不在 assertion で KILLED。 |

M4／M7 の各実行は一箇所の置換に分ける。複数箇所を同時に外して単一変異と数えない。M9 は特に既存の多重 binding 検査に覆われやすいため、事前登録時の反証対象とする。

## 焦点テスト集合と影響範囲

`tools/`、`orchestrator/` を参照検索した結果、直接 consumer は次のとおり。

| 起点 | consumer |
|---|---|
| land | `tools/acceptance_shards.py:46` の import、`218` の `_CONTROL_CONTAINERS`。`tools/check_docs.py:789` 以降の helper path 契約。 |
| cleanup | `tools/check_docs.py:631` の DW-O28 literal。`orchestrator/test_selection_contract.py:41` の test path 契約。 |
| window | `land:44`、`5670`、`5732`。`tools/dev_wave_wait.py:664`、`2871` の lease command。 |
| 直接 test | `test_dev_wave_land.py`、`test_dev_wave_cleanup.py`、`test_wave_land_window.py`、`test_dev_wave_wait.py:29`〜`52`、`test_run_tests_shards.py:1993`。 |

二段目は `acceptance_shards→tools/run_tests.py`、`test_selection_contract→tools/run_tests.py／orchestrator/tests/conftest.py`、`dev_wave_wait→acceptance_issuer_reference／waiter tests` を確認した。

`tools/dev_waves/*.py` には対象三 helper と `dev_wave_wait` の直接文字列参照は見つからなかった。spool fold が使う共有型・検証側としては影響確認対象に残す。`tools/check_wave_startup.py:198` は waiter を案内する文面で、land／cleanup の実行 caller ではない。

再走予定：

- **変更面・直接 consumer**：`test_dev_wave_land.py`、`test_dev_wave_cleanup.py`、`test_wave_land_window.py`、`test_dev_wave_wait.py`、`test_run_tests_shards.py`。
- **fold／recovery**：`test_spool_fold.py`、`test_fold_gate_nodes_contract.py`。
- **二段目・収集境界**：`test_run_tests_preflight.py`、`test_pytest_collection_config.py`、`test_real_repo_serialization.py`、`test_dev_wave_wait_compute.py`、`test_resume_gate_acceptance_boundary.py`。
- **docs／台帳 consumer**：`test_check_docs.py`、`test_check_wave_startup.py`、`test_flaky_test_holds_contract.py`、`test_branch_rescue_ledger.py`、`test_t139_approval_payload.py`、`test_t793_approval_d291.py`。
- **一覧・allowlist**：`test_plain_runner_coverage.py`、`test_skip_classification.py`。

README の pytest-only allowlist consumer は `test_plain_runner_coverage.py:52`。既存 test file 内に追加する案なので、新規 file 登録は不要である。

lineno については、`test_run_tests_shards.py:2066` は AST 上の相対実行順、`test_skip_classification.py:334` の固定値は別の Silo test 契約だった。**land／cleanup の行番号を固定した consumer は今回の検索では確認できなかった。** 関係のない数値を一括更新しない。

duration 台帳の読み取り集計：

| file | 台帳内 node 数 | 記録値合計 |
|---|---:|---:|
| `test_dev_wave_land.py` | 312 | 136.355 秒 |
| `test_dev_wave_cleanup.py` | 104 | 5.230 秒 |
| `test_wave_land_window.py` | 95 | 0.409 秒 |

これは現在 tree の実測でも、受入 wall-clock でもない。累積 wait tests の記録はこの台帳に無かった。

追加所要の設計見積りは、小さい 8-wave ff fixture＋境界 tests で **10〜30 秒程度**、実 fold gate／subprocess crash を含め **20〜60 秒程度**を暫定枠とする。N 本すべてで実 fold gate の内側 pytest を繰り返す設計は避け、実 gate 接続を少数の統合 test で検証する。いずれも未測定であり、受入 5 分以内を保証する数字ではない。

author 後は `tools/run_tests.py` 経由で変更 test file の単独走→consumer 焦点走→親の受入全走を行う。brief の「login 先例」は実行場所の根拠にせず、runner の admission 判定に従う。

## docs 変更の一覧

新 D は spool fragment で作り、番号を事前に確定しない。骨子：

1. **D432／D1996 supersede**：受入後の land 順番票、非横取り grant、3600 秒期限、180 秒の位置付け、lock-busy による証拠破棄の撤去。
2. **D109 部分改訂**：無関係 child の実体／admin 観測と同名差替え拒否を外す。名前列挙、自 wave、incoming 衝突、handoff、共有 Git 検査を維持。
3. **D702 部分改訂**：自己撤去義務は維持し、全体 prune を自 admin のみの撤去へ変更。
4. D254、D1393、D662 と receipt 再利用条件は維持。
5. 混在期の FIFO 非保証、復旧可能性、通常 merge 再試行を進行保証の前提として明示。

追加成果物：

- F：76 分着地ゼロの観測、取得競争と snapshot 構築 race を区別して記録。
- worklog fragment：`{{T:land-turn-ticket}}`。
- insight README：旧 tree probe、scheduler、変異事前登録、実測結果、残余。
- 既存 tests の期待反転理由と、M0 の扱い。

**DW-O23、DW-O25、DW-O28 は変更しない案で成立する。** DW-O28 も `tools/check_docs.py:626`、`662` 付近で exact pin されている点は brief に補足すべきである。

関係箇所：

- L1 上限：`tools/check_docs.py:358`＝10,625 bytes。
- DW-O23 の段 9 無条件 dispatch：`910`。
- 三層予算算定：`5285`、L1 判定：`5376`。
- DW-O25 literal／exact 登録：`612`／`658`。
- helper path の位置・件数制約：`789`、`6357`〜`6374`。

D432 の 10,783 > 10,625 は過去の追記実験値であり、現在の footprint 再測定とは区別する。新契約を decisions／insight に置き、規範 leaf へ長文を足さない。checker の予算・pin 自体を緩める変更は不要である。

## リスクと未確定点

**author 前に明文化が必要なのは、特に recovery の自動化範囲である。**

- **元 request の recovery 再入を優先するところまでは、既存契約を維持して実装できる。** 死亡 `mutating` 票は消さず、通常 grant を止め、同じ request key の再入を通常 seq 順より優先する。common lock 内で `active_plan` を確認し、`land:5126` の既存経路へ渡す。
- **「次 wave が自動で他 wave を復旧してから自分を land」までは P1 の payload と既存結果契約だけでは決まらない。** 元 wave の cwd／binding、receipt path、起動主体、復旧結果の報告が必要である。B の invocation が A を復旧後に B を拒否すると、「拒否 invocation は main 不変」とも衝突する。別 wave の origin 照合を緩めて解消してはいけない。
- したがって現案の crash 進行保証は、**元 request の recovery が再投入されることを条件にする**。完全な自動復旧まで完了条件とするなら、この一点は次段 consult／裁定で詰める必要がある。

その他：

| リスク | 方針・限界 |
|---|---|
| 旧 driver | 共通 flock により mutation の排他は維持。旧 driver に FIFO を強制できず、3600 秒 timeout は残る。 |
| ff child が親死亡後も生存 | ticket FD は閉じても merge child が common lock を保持する。取得するまで復旧判定しない。既存 `land-test:7213` を維持。 |
| ff 後・state 前の死亡 | `mutating` mark を ff 前に置く理由。active state 不在だけで安全終了と決めず、元 request で main／pending fold を検査する。 |
| no-op | 分岐を確定するための common lock は必要。通常順番票を要求するが provenance は課さない。active recovery は通常 grant より優先。 |
| 生存したままハング | TTL で追い越さない。owner の処理／終了がなければ進行保証はない。 |
| lease TTL | 2400 秒超で失効しうる。順番票は別で保持。release の holder／tested_main 照合を維持。 |
| 共有 FS | common と同じ FS を使うが、NFS の flock は client／mount 設定に依存する。既存 lock の実測が ticket の全動作を自動的に証明するわけではない。NFS の排他 lock には書込み open が必要。[flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html) |
| 待機中の自 wave cleanup | 再束縛で拒否。自 wave を再作成したり alias として引き継がない。 |
| ticket 肥大 | terminal 票は削除、死亡 runtime 票は回収。外部再試行用の seq 対応は残るため、無期限の順位保持と完全 GC は同時に保証できない。 |
| seq 復帰 | 現 grant 非横取りを優先する。休止期間を含めた厳密な成功順 FIFO は主張しない。 |
| 赤の先頭 | 赤は拒否して次候補へ。全候補が赤なら成功ゼロが正しい。 |
| main 前進 | 順番票は merge を代行しない。独立 branch の stale-main は既存の通常再試行が必要。 |
| cleanup の残る全体観測 | `_administrative_gitdirs_for_wave`／porcelain は一覧を読む。今回除くのは他 admin の削除と land の無関係 child binding 観測。 |
| F977 | rollback 契約は変えない。ticket の `done` 判定を merge 成功直後に置かず、fold／postcondition／finalize まで待つ。 |

## 総括

実装の中心は、**common 配下の非横取り順番票、同一 invocation 内の証拠保持、protected child だけの binding 観測、自 admin だけの cleanup**である。既存 receipt 検証と common flock は維持できる。

P1/P2 の再試行順位と死亡回収、P3 の 180 秒の意味、P8 の固定 branch／cwd／receipt fixture は補正が必要である。特に、**死亡 fold の元 request 再入を優先する設計と、他 wave による完全自動復旧は別物**として次段で確定する。

本段の成果は静的実装計画であり、テスト成功・変異 KILLED・3600 秒以内の全件着地は未検証である。
