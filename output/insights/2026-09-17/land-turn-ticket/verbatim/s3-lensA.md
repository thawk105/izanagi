## 前提の検算 (brief・plan の行番号と主張)

**plan の方向は維持できるが、死亡票の解消手順は未完成である。特に「finalize 成功後・ticket 完了記録前」の死亡を、既存 recovery へ渡すだけでは処理できない。**

指定資料とコードの静的検査のみ実施した。ファイル変更、Git 状態変更、pytest・実 flock probe は行っていない。以下の **real はコードまたは計画文の反例が成立すること**を示し、実行済みという意味ではない。

略記：

- `brief`：[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/s1-brief.md)
- `plan`：[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/artifacts/dev-wave-land-turn-ticket/s2-plan.md)
- `rulings`：[rulings-verbatim.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/rulings-verbatim.md)
- `land`：`tools/dev_wave_land.py`
- `fold`：`tools/spool_fold.py`
- `cleanup`：`tools/dev_wave_cleanup.py`
- `test`：`orchestrator/tests/test_dev_wave_land.py`

| 分類 | 主張と検算 |
|---|---|
| **refuted** | 「通常 ff の直前に `update-ref` がある」。実際は `land:5567` の `git merge --ff-only`。`update-ref` は `land:4379` の rollback。plan:19 の補正が正しい。 |
| **real** | brief:16 の「main/tip が変わったときだけ失効」は不足する。plan:158–160 は既存の control・cleanliness・state・closure・receipt 再検査を残して補正している。 |
| **real** | brief:7 の「拒否は main 不変」は範囲指定が必要。mutation 前の拒否と、既に admit 済みの fold recovery 失敗は同じではない。 |
| **real** | plan:425–427 は元 request の再投入を条件としている。brief:3、7、21 から無条件の crash 後自動完了を読み取ることはできない。 |
| **未確認** | 76 分停止の個別原因、共有 FS 上の ticket 動作、変異の KILLED、8 本完了。今回、実測はしていない。 |

## flock が唯一の mutation guard か

**refuted：順番票が既存 common flock の代わりになる、という攻撃。**

plan:113、125–128、158–160 は、common flock 取得と既存検査を明示的に残す。現行 `_acquire_land_lock` は取得後に `_verify_land_lock_binding` を実行する（`land:2663–2677`）。監査後・gate 後には `_locked_preflight` が再実行される（`land:5086`、5365）。

反例候補は「新 A が監査中、旧 B が flock を取得して main を進め、A が旧 receipt で ff」である。これは A の fingerprint 再計算・比較（`land:5064–5085`、5348–5364）で拒否される。plan を記述どおり実装する限り、この経路では排他も再検査も失われない。

**real：『唯一』の対象を全 registry・worktree mutation まで広げると、brief:7 は成立しない。**

- 順番 registry の登録・grant 更新は、initial common flock より前に別の `registry.lock` で行う（plan:58–60、121–125）。
- cleanup は現状も common land flock を取得せず、detach・directory 撤去・Git admin prune・branch 削除を行う（`cleanup:934–998`、1022–1042）。

具体例：A が common flock を保持中でも、B の ticket 登録や、完了済み C の cleanup は動ける。

最小補正は、規範を「**協調 land による main ref/index/worktree と fold state の mutation は common flock 内**」とし、順番 registry の短い flock と対象限定 cleanup を区別すること。cleanup を新たに大域直列化する提案ではない。

**未確認：commit 済み recovery の mutation guard 接続。**

plan:106–111 の明示 anchor は ff と `apply_fold` の二つだが、shape B はどちらも通らず、`land:5200` → 4727 の mark → 4755 の finalize へ進む。いずれも state mutation である。

入力：`main=C`、`C` は A の fold commit、active state は `applied`。A の再入は apply を通らない。common flock は保持されるため、それだけで main 排他違反にはならないが、「mutation 直前の grant/binding 再確認」をこの経路にも接続する必要がある。plan:315 の ff/apply 二種類だけでは被覆しない。

## 証拠保持と receipt 束縛

**refuted：lock-busy 後の保持だけで receipt の束縛が弱まる。**

同一 invocation 内で payload を保持し、再取得後に既存検査をすべて通すなら、監査の再実行は不要である。確認場所は次のとおり。

| 証拠・可変入力 | 再確認場所 |
|---|---|
| provenance の着地 tip・checker blob・実行 bytes・rc | `land:3028–3087`、呼出し `5098` |
| main/wave HEAD、衝突 path 集合 | `land:1983–2024`、比較 `5079`・`5361` |
| tracked/index/submodule dirt | `_locked_preflight` → `land:2731` → `1804–1809` |
| 自 wave・protected child の binding | `land:1630–1647`、再取得後 control 比較 |
| active fold transaction | `land:2702`。gate 後は `5379` で出現を明示拒否 |
| fold 入力 closure・pending fragment 集合 | `land:5383–5399` |
| fold plan identity・transaction・raw digest・registry・nodeids・outcome | `land:3996–4015`、呼出し `5400`・`4555` |
| 受入 receipt の完全検証・登録時 digest | 現行 `land:5107`、追加指定 plan:199 |

具体的な反例入力は、A の監査終了後に旧 B が main SHA を変えず index を汚す、incoming と同じ untracked を置く、または fold state を永続化して死ぬ、である。SHA 比較だけなら見逃すが、上記検査は dirt・collision・active state を別々に扱う。

**real：brief:16 の失効条件は修正が必要。**

`main/tip` と `_LandFingerprint` は同義ではない。また fingerprint 自体も index や fold state の全状態を符号化していない（`land:2005–2007` は非 untracked record を飛ばす）。plan:160 の「既存どおり拒否」を採用し、SHA/fingerprint 一致を単独の続行条件にしないこと。汎用 read-set の追加は不要である。

**real：赤い provenance payload の扱いが plan の疑似コードから抜けている。**

plan:154 は「監査赤は期限まで待たせない」とする。しかし `_audit_provenance_history` は通常の非ゼロ rc を例外にせず receipt として返す（`land:2997–3002`）。rc 判定は再取得後の verifier にある（`land:3055–3066`）。

schedule：

1. A の provenance が非ゼロで終了。
2. 旧 holder が common flock を保持。
3. plan:140–152 の汎用 loop をそのまま使う。
4. A は既知の赤を持ったまま grant を保持し、期限に `rc=11` を返す。

main を誤 admit はしないが、plan:154 と不整合である。非ゼロ payload の早期失敗経路と release 安全性を明記する必要がある。成功 payload の lock 内完全再照合は残す。

## 死亡 owner と recovery

| 停止点 | 現行コードで可能な処理と判定 |
|---|---|
| **(a) ff 完了後・state 前** | **条件付きで成立。** main=L、state 不在なら元 A は provenance を省き（`land:5014`）、plan/gate を経て already-landed 後の fold（`5510`）へ進める。merge child が残っている間は継承 common flock が先行する（`5570`、`test:7213`）。 |
| **(b) state 永続化直後** | **条件付きで成立。** `fold:3294` に保存された plan を再利用する。origin の wave/tip（`land:5144–5147`）、durable gate receipt（`5174–5185`）を検査し、同じ transaction を apply する。 |
| **(c) canonical 書込み途中** | **条件付きで成立。** `fold:3298–3307` は全 target の before/after 状態を検査し、after を再適用しない。第三状態なら拒否する。新しい採番の plan を作り直してはならない。 |
| **(d) commit 後・finalize 前** | **条件付きで成立。** `land:4705` は commit identity を検査し、必要な mark/finalize のみ行う。再 apply・再 commit はしない。`test:6529–6585` の期待もこれに一致する。 |

以上は **元 request の wave binding・着地 tip・受入 receipt が再利用可能で、既存 recovery に到達できること**を条件とする。D254 の provenance 非起動は維持できる（`rulings:247–271`）。

**real・重要：finalize 後、ticket 完了記録前の死亡が未定義。**

根拠は plan:111、425、`fold:3521–3522`、`land:2799–2816`、2552–2569。

schedule：

1. A が L を ff し、fold commit C を作る。
2. finalize が state を削除・fsync する。
3. ticket の `done` 永続化前に A が死ぬ。
4. B は死亡 `mutating` 票を見て通常 grant を停止。
5. 同じ A を再投入しても、state はなく、main=C、landing_tip=L。
6. 前進 merge なしの A では C は audited closure に含まれず、既存 preflight が `stale-main` を返す。`active_plan` recovery には入れない。

これは「元 request を再投入すれば解消する」の反例である。plan:322 の finalize **前**の死亡テストだけでは捕まらない。

最小補正は、**state の有無だけに頼らず死亡票を解消できる、ticket の完了照合手順**を定義すること。既存の commit identity 検証を利用できる情報を完了前に束縛し、main は変更せず完了済みを確認して票を閉じる。`done` を finalize より前に置いて回避してはいけない。

**real：F977 の正常 rollback 後にも terminal 遷移が必要。**

plan:99–101 は死亡 `mutating` を recovery 対象とする一方、削除可能な失敗を「mutation 前拒否」としている。正常 rollback 完了後の失敗が明記されていない。

schedule：A が ff→fold 失敗→`land:4379`、4387、4416 で main/index/state を復元→ticket 更新前に死亡。state が無いので、これも active recovery には入らない。

正常 rollback の確認済み終端、rollback incomplete、commit 済み finalize failure を区別する必要がある。`LandResult.rc != 0` や `release_safe` だけを ticket 削除条件に流用しないこと。後続へ渡せるのは rollback の整合を確認した後である。

**未確認：同じ request key で着地 tip が変わった recovery。**

plan:73 は landing_tip を key に含めず変更を許すが、active recovery は `origin.tested_tip == landing_tip` を要求する（`land:5146`）。

反例入力：A の L で state が残り、再試行時に wave が L′ へ前進。key は同じでも recovery は拒否される。通常の休止票再開と、未解決 mutation の復旧を区別し、後者の origin を新 L′ で上書きしないこと。

**refuted：別 wave の fold がそのまま混入し、二重 commit される。**

B の通常 request で A の state を処理しようとしても `land:5144–5147` が拒否する。shape B の commit 検査も親・author・message・変更 path・出力 bytes を束縛する（`fold:3426–3462`）。これらを維持する限り、提示された経路で混入は成立しない。ただし「拒否して止まる」と「復旧して進む」は別である。

## 登録前提と受理集合

**refuted：P4 の static 検査が、それ自体で現行の完全検証より強くなる。**

plan:182–201 の分割は、現行 verifier の固定 object に対する検査を前へ出し、現在の locked_main に関する bootstrap 条件だけを残すもの。通常の不変入力について、完全検証を通る request を static 部分だけが拒否する条件は見つからなかった。

特に `child_rc==0` のみへ狭めず、現行の `non-attributable-only` 分岐（`land:1024–1050`）を保持する方針は必要である。

**real：登録済み＝land 可能、ではない。**

具体例：

1. tested_main に launcher が無い bootstrap receipt が static 検査を通る。
2. 登録前後に旧 driver が launcher を含む main へ進める。
3. A が先頭になる。
4. locked_main 側の検査（`land:1063–1070`）で拒否される。

これは head-of-line の無駄を作るが、既存完全検証を残す限り誤受理ではない。brief:7(h) の「受入緑」は、**現行 receipt verifier の lock 非依存部分を満たすこと**と定義すべきである。

**未確認：死亡票への同一 key の二重再入。**

plan:60、73、90–91 は新規 ticket 作成・順位保持を述べるが、同じ key の二つの invocation が同時に再入した場合の扱いは明示していない。

入力：A₁、A₂ が同じ receipt digest で同時再試行。registry lock 内で既存 runtime owner を確認し、生存 owner があれば二つ目の実行所有権を作らない必要がある。共通 flock と既存検査は main を守るが、ticket の所有権と recovery 優先の説明には、このケースの仕様が要る。

## 非接触と拒否集合

**refuted：P5 により incoming と衝突する child まで保護から落ちる。**

plan:210–225 は、名前から自 wave／path overlap を判定してから無関係 child を除外する。さらに ff 衝突検査では `_CONTROL_CONTAINERS` 自体を常に protected に含める（`land:1959–1964`）。child identity を読まなくても、container 配下への incoming は受理されない。

変更後に受理可能になる具体例は次のとおり。

| 入力 | 旧拒否理由 | incoming との関係 |
|---|---|---|
| 無関係 child の同名 directory 差替え | surviving identity 不一致 | 通常の `wave.txt` 等とは非衝突 |
| 無関係 alias が自 wave の `.git` bytes を複製 | admin backpointer 不一致 | `.codex/worktrees/alias/**` を incoming に含めれば引き続き拒否 |
| 無関係 child の `.git` 消失・欠損 | binding 読取り失敗 | 同上 |
| 無関係 child の不正名 | `_SAFE_CHILD_RE` 不一致 | protected なら名前検査を残す |

`test:2742`、2780、2865、6871、6910 の成功への反転は、現物の入力が非衝突であることと整合する。自 wave 差替え（`test:4246`）と重なる child 出現（4272）の拒否は維持すべきである。

**refuted：fold の gc_paths が collision 検査から漏れる。**

`_fold_plan_paths` は targets と gc_paths の和を取る（`land:4258–4268`）。新規 fold は `land:5442–5447` でその集合を cleanliness 検査へ渡す。durable plan の GC は `docs/spool/<ledger>/<fragment>`、targets は canonical・archive の許可形へ制限される（`fold:2743–2765`）。今回の変更で control container 内へ fold path が流れる経路は確認できなかった。

handoff の直下名前集合・directory identity と `_CONTROL_CONTAINERS` の保護も残る（`land:1533–1579`、1959）。「無関係 child の検査を除く」を「handoff 比較も除く」へ広げてはいけない。

**real：brief:18 の「名前も読まない」は不正確。** 名前列挙は protected 判定に必要であり、plan:23、210 の補正を採るべきである。

## cleanup の対象限定

**refuted：plan の条件下でも、名前衝突だけで他 wave の admin を削除する。**

現行 resolver は admin basename と wave basename の一致ではなく、`gitdir` backpointer が対象 wave の `.git` を指すことを使う（`cleanup:609–636`）。plan:252、261–269 は、さらに一意性・直下 directory・inode・common・backpointer・nofollow 相対操作を要求する。

入力：admin `foo` と `foo1` が両方同じ wave を指す。**どちらかを選ぶ／両方消すのではなく拒否**する仕様であり、複数一致の誤削除は封じられる。途中 symlink 化・別 inode への差替えも同様である。

**未確認：HEAD/index と削除途中の crash に対する具体的手順。**

plan:264–267 の `locked`・`index.lock`・partial error 停止は必要だが、実際の削除 helper は未実装である。

確認すべき具体的入力は二つある。

- preflight 後、同じ admin inode・backpointer のまま HEAD/reflog が変化する。inode 不変だけでは内容不変を証明しない。既存 `cleanup:562–605`、852 の HEAD・到達可能性検査と、削除直前の対象照合の接続が必要。
- admin の `HEAD` または `gitdir` を削除した直後に死亡する。次回、porcelain record と resolver の片方だけから対象が消える可能性がある。既存 `cleanup:820–821` の「record 無し・admin 有り」拒否も含め、部分撤去を成功扱いせず branch 削除へ進まないことを確認する。

これらから直ちに他 wave 誤削除が起こるとは確認していない。**一回の正常削除の安全性と、部分削除後の再入可能性を同じ保証にしない**ことが要点である。

**real：cleanup の完全非接触は実現しない。** resolver は他 admin の backpointer も読む（`cleanup:616–625`）。plan:273 の限定、「他 wave の admin を削除しない」が正しい主張である。

## 親 brief への反証

| 対象 | 分類・反例と補正 |
|---|---|
| **(a) flock が唯一** | **real：文言が広すぎる。** 順番 registry と cleanup は別の mutation 面。協調 land の main/fold transaction に限定する。 |
| **(b) 拒否は main 不変** | **real：失敗全般には成立しない。** main=L で始まる recovery が失敗し、保存済み `rollback_ref=B` へ戻れば、その invocation は非成功で main を変える（`land:5257`、4650、4379）。mutation 前拒否と post-mutation failure を分ける。 |
| **(c) 監査中 lock 解放の利得** | **refuted：解放が無意味。** 旧 driver 等の common-lock 利用者には効く。一方、後続の新 driver は grant 待ちなので進まない。plan:88 の非横取り grant の下で「新 driver の recovery が監査中に必ず割り込める」とは言えない。 |
| **(e) FD lock は既存と同じ前提** | **未確認。** 同じ FS を置き場にしても、多数 ticket の生存 probe、registry rename/fsync、client 障害後の挙動まで既存一個の flock 実測で証明できない。plan:439 の留保を維持する。TTL による追越しは代案にしない。 |
| **(f)(g) 死亡 recovery** | **real：停止点が足りない。** finalize 後・done 前、正常 rollback 後・ticket 更新前、shape B の mark/finalize を追加する。 |
| **(h) 受入緑だけ登録** | **real：定義不足。** 現行互換 verdict を含む static receipt 検証と定義する。登録時点で locked authority の成立まで主張しない。 |
| **P1/P2** | **real：単純な最小 seq と再開順位保持は衝突する。** 旧 seq の復帰で実行中 grant を失効させない plan:85–93 の補正が必要。 |
| **P3** | **real：180 秒総上限と3600秒継続待機は両立しない。** plan:133–138 の明示改訂が必要。 |
| **P7/P8** | **real：完了判定の限定が必要。** 固定独立 branch は先行 land 後に stale となる。累積 tip の正例と通常 merge 再試行の対照を分ける。等価変異 M0 は SURVIVED が正しい。 |
| **brief:22** | **real：P5 と矛盾。** 「拒否は狭まらず、進行だけが変わる」は、無関係 alias・差替えを受理へ反転する P5 と両立しない。「指定した非接触面の拒否は狭まる」と訂正する。 |

## 裁定パッケージ候補 (scope 外)

- **他 wave が死亡 owner を自動起動・復旧する機構。** plan:426 が挙げる cwd、元 receipt、起動主体、結果帰属が必要。元 wave の origin 照合を緩めて代替しない。
- **旧 driver を含む、fold 子 process 生存中の crash 排他。** merge は FD を継承するが、現行 fold の `git add`・`git commit` は継承指定を持たない（`land:4577`、4608）。親死亡直後も commit 子が生存する schedule は、ticket FD の死亡確認だけでは閉じない。今回の四停止点の正常な recovery と区別して、既存の子 process 境界として扱う。
- **共有 FS の client 障害・lock 喪失を含む保証。**今回の静的検査で実証していない。既存 flock より強い障害耐性を宣伝しない。
- **F977 の rollback 自体、receipt 再利用条件、OCC・lease・汎用 read-set の再設計。** 本件の修正案には含めない。

## 総括

**author 前に閉じるべき中心点は、死亡票と既存 fold transaction の終端を対応付けること。**

最低限、次を plan に追記すべきである。

1. finalize 後・ticket 完了記録前の死亡を、main 無変更で完了解消する手順。
2. 正常 rollback、rollback incomplete、finalize failure の ticket 遷移。
3. shape B の mark/finalize に対する ownership 再確認。
4. recovery 中の landing_tip 固定と同一 key の二重再入処理。
5. provenance 非ゼロ payload を長時間保持しない失敗経路。

既存の receipt・closure・cleanliness・binding 再検査を残す証拠保持と、protected child だけを開く P5 は、検査した範囲では成立する。**main の誤受理へ直結する新経路は確認しなかったが、元 request の再投入だけで全死亡票が解消するという保証は反証された。**
