## 総括

静的検査のみです。pytest、checker、実走は行っていません。

結論は、P5 は必要ですが十分ではありません。`phase=applied` かつ main が fold child の相を受理するなら、復旧時に `mark_fold_committed()` を再実行する分岐が必要です。また rollback 後の `committed` state、standalone との競合、finalize 失敗後の journal 消失は real です。

### 中断点の列挙

| 中断点 | 残る tree / state / ref | 復旧性 |
|---|---|---|
| state atomic write 前後 | tree は未変更、state は旧値または新値 | `_atomic_write()` を使う限り再試行可能 |
| target write 中 | `phase=applied`、main は tested tip、target は before/after 混在 | atomic write なら resume 可能 |
| GC unlink 中 | target は全 after、GC は present/missing 混在 | resume 可能 |
| docs / stage / message 検査中 | `applied`、main は tested tip | resume 可能 |
| `git commit` 前 | `applied`、main は tested tip | resume 可能 |
| `git commit` 後、mark 前 | `applied`、main は fold child | P5 で受理すべきだが、現 plan は finalize へつなぐ手順が欠落 |
| mark の replace/fsync 前後 | main は fold child、state は applied/committed | atomic write なら両方を P5 が受理可能。壊れた JSON は復旧不能 |
| postcondition 中 | `committed`、main は fold child | land recovery 可能 |
| finalize unlink 前 | `committed`、main は fold child | finalize 再試行可能 |
| unlink 後、fsync/例外前後 | state が absent、main は fold child | postcondition 済みなら終端。ただし例外が rollback に流れると journal 消失 |
| rollback の ref 更新後、read-tree/path restore 前 | `committed` state、main は rollback ref | 受理形外で復旧不能 |
| v1 / 壊れた state | tree の状態にかかわらず state reject | 自動復旧不能 |

### LUNA-P5-01 — `phase=applied` + fold child が finalize へ到達しない  
**real**

- 根拠: `s2b-plan.md:148-157,262-278,321-360`、`tools/dev_wave_land.py:1869-1873,1911-1920`
- 中断点: commit 成功後、`mark_fold_committed()` [予定位置 `dev_wave_land.py:1911` 直後] の前で process 死。
- P5 はこの形を `phase ∈ {applied, committed}` として受理する。しかし `finalize_fold()` は `phase=committed` を要求する (`s2b-plan.md:276-278`)。`phase=applied` の fold child に対して、再 apply / 再 commit を行えば commit 失敗、skip すれば finalize が拒否される。
- **成果物影響:** state が残り、fold commit は main にあるのに finalize できず、次 wave の land と certified proof chain が停止する。

この相では、HEAD が fold child なら `mark_fold_committed()` を再実行してから verifier と finalize へ進む分岐を明示しない限り閉じません。

### LUNA-P5-02 — phase は commit の身元を証明しない  
**real**

- 根拠: `s2b-plan.md:15-50,72-74`（`phase` と fold commit SHA が transaction ID に入らない）、`tools/dev_waves/git_state.py:913-940`
- `phase` を atomic write しても、transaction ID は変わりません。P5 では applied/committed のどちらでも fold child を受理するため、phase は B 相の証拠ではありません。
- `verify_declared_fold_commit()` も parent と path shape が中心で、commit metadata、transaction ID、state の `gc_paths` との完全一致を検査しません。
- **成果物影響:** 別 transaction または手動生成された fold-shaped child を古い state の commit と誤認し、別 fragment の GC や誤った provenance を finalize する余地が残る。

phase は lifecycle の監視用 marker に留め、recovery の権威は HEAD、commit tree、state payload の完全一致に置く必要があります。

### LUNA-RB-03 — rollback が ref だけ戻した `committed` state を永久に詰まらせる  
**real**

- 根拠: `tools/dev_wave_land.py:1766-1789`、`s2b-plan.md:362-369,374-390`
- 中断点: `_rollback_fold()` が `update-ref` に成功した直後、`read-tree` または `_restore_fold_paths()` が失敗する位置 (`1777-1783`)。
- 通常 land の rollback ref は `locked_main` / origin base (`dev_wave_land.py:2416`) であり、tested tip ではありません。したがって残るのは `phase=committed`、main=base、tree=部分復元という受理表外の相です。
- plan は rollback 失敗時に phase を書き換えず state を残します (`s2b-plan.md:367`)。次回 land は main が tested tip でも fold child でもないため拒否し、standalone apply は committed state を apply できません。
- **成果物影響:** canonical、fragment、index、main ref の一部だけが戻ったまま transaction state が次 wave を永久阻塞し、certified 台帳の受理も復旧もできない。

さらに state unlink (`dev_wave_land.py:1784-1789`) に parent directory fsync がなく、rollback 完了後の state が電断で復活して同じ相になる疑いもあります。

### LUNA-FIN-04 — finalize の unlink 後の例外が journal なし rollback に流れる  
**real**

- 根拠: `s2b-plan.md:276-278,349-360`、`tools/dev_wave_land.py:1965-1973`、`tools/dev_wave_land.py:1784-1792`
- 中断・競合点: `finalize_fold()` が state unlink に成功した後、directory fsync が失敗する場合。
- finalize は `_fold_main_locked()` の fallible な `try` 内に置かれる予定です。例外は `_rollback_fold()` へ流れますが、state は既に存在しないため rollback の durable journal がありません。
- rollback がさらに失敗すれば、main/tree が部分状態なのに state 無しになります。rollback が成功しても、既に検証済みの fold を取り消して結果だけ失います。
- **成果物影響:** commit 済み canonical と fragment GC が無記録のまま巻き戻るか、部分 tree が state 無しで残り、certified proof chain を再構築できない。

SIGKILL が unlink 直後に起きるだけなら postcondition 済みの完成相なので概ね安全ですが、unlink 後の通常例外と rollback 失敗を別扱いにする必要があります。

### LUNA-RACE-05 — standalone と land の二重 writer  
**real**

- 根拠: `tools/spool_fold.py:2504-2515,2284-2293`、`tools/dev_wave_land.py:1872-1880,1911-1915,1784-1792`
- standalone は lock を取得せず、state の存在確認と atomic write の間に CAS がありません。
- 具体例:

  1. standalone と land が同時に state 無しを観測する。
  2. standalone が `kind=standalone` の state を書き、target/GC を変更する。
  3. land が `kind=land` の別 transaction ID を見て失敗する。
  4. land の rollback が standalone の state を unlink する。
  5. standalone が rollback 後も target/GC を書き続ける。

- **成果物影響:** canonical と fragment GC が state 無しで進み、別 transaction の rollback が他方の変更を消して、台帳・receipt・proof chain の対応が失われる。

origin/closure の照合は競合を検出するだけで、共有 lock がないためこの二重 writer を直列化しません。

### LUNA-LIFE-06 — standalone apply 後の state が次 wave を詰まらせる  
**real**

- 根拠: `tools/spool_fold.py:2504-2515`、`s2b-plan.md:192-196,321-327`、`tools/dev_wave_land.py:2203-2212`
- standalone apply は新設計で state を削除しません (`s2b-plan.md:248-278`)。完全適用後は `phase=applied`、main は standalone の tested tip、target は after、GC は missing です。
- この完全相は `_discover()` / `check_docs` では受理できる設計ですが、次 wave の tested tip は異なります。land は active state を先に処理し、`locked_main != tested_tip` で通常の merge に進めません。
- **成果物影響:** `check_docs` は通り得るのに次 wave の land と受入全走が停止し、state の手動 quarantine / 削除なしには運用が進まない。

「standalone は state を残す」という裁定を採るなら、同じ wave の land だけでなく、lock-aware finalize/inspect の経路が必要です。

### LUNA-CLOSURE-07 — resume 正規化が外部変更を transaction-owned と誤認する  
**real**

- 根拠: `s2b-plan.md:140-146`、`tools/spool_fold.py:2285-2290,2305-2311,2319-2329`
- target が after から before に戻された場合、closure は stored `before_sha256` を使い、resume は before を正当な状態として after へ再適用します。resume では `_git_clean_preflight()` も再実行されません。
- GC fragment も、全 target が after なら missing を state 内 `content_sha256` で代用します。外部 actor による削除と、transaction が完了した GC を区別できません。
- **成果物影響:** 別 writer の canonical の巻き戻しを検出せず、古い transaction の worklog / decisions / phase3 の値で上書きし、fragment の監査証拠も黙って失う。

before/after だけでなく、transaction の所有世代または writer lease を束縛しない限り、これは closure 検査の抜け道です。

### LUNA-VERIFY-08 — active discovery / finalize が verifier の層を飛び越え得る  
**疑い**

- 根拠: `s2b-plan.md:192-196,276-278,349-360`、`tools/dev_waves/git_state.py:913-940`、`tools/dev_wave_land.py:1946-1955`
- commit 後、`mark_fold_committed()` と `verify_declared_fold_commit()` の間で死ぬと、main には未検証の fold commit が残ります。plan の `_discover()` 受理条件には verifier 呼出しが明記されていません。
- また `finalize_fold()` 自身の契約は phase、HEAD/parent、tree、closure を列挙するだけで、`verify_declared_fold_commit()` を必須にしていません。
- `git_state.py:913-940` は commit message、author、transaction の正確な deleted fragment 集合を見ません。
- **成果物影響:** `check_docs` または別 caller が未検証 commit を正常相として扱い、誤った fold provenance、fragment 喪失、または trailer 無しの commit を main に残す可能性がある。

通常 land の `1946-1955` は verifier を呼びますが、active discovery と public finalize API でも同じ防壁を契約化すべきです。

### LUNA-REF-09 — Git ref の durable ordering が state unlink より弱い  
**real（電断・FS crash 条件）**

- 根拠: `tools/dev_waves/git_state.py:37-43`、`tools/dev_wave_land.py:1911-1915`、`tools/spool_fold.py:2148-2162`、`s2b-plan.md:276-277`
- state write は file と directory を fsync しますが、land の `git commit` は subprocess 呼出しだけで、ref の fsync 契約がありません。
- 電断で commit ref が旧 tested tip に戻った一方、`phase=committed` state が durable なら、`committed + main=tested_tip` となり受理表外です。finalize 後に state だけ消えて ref が戻れば、`state absent + dirty canonical` となり journal もありません。
- **成果物影響:** fragment GC 済み・canonical after の変更が main history に無いまま state も失われ、certified report と台帳を自動復旧できない。

親の SIGKILL 実測では発火しにくい相ですが、node failure / power loss まで含む crash 完全性には別の注入が必要です。

### LUNA-V1-10 — 旧 v1 in-flight state は新 code で復旧不能  
**real（fail-closed の意図された残余）**

- 根拠: `tools/spool_fold.py:2236-2245`、`s2b-plan.md:56,389,473-474`、`s1-brief.md:83-84`
- v2 へ移行した後、旧 code が残した v1 state は拒否されます。移行 code を書かない裁定自体は fail-closed ですが、「あらゆる中断点から復旧」ではありません。
- **成果物影響:** upgrade 境界で crash した transaction の partial canonical / GC / ref は自動復旧不能となり、次 wave の land を手動 quarantine まで停止する。

### LUNA-TEST-11 — test-only helper が recovery 契約を隠す  
**疑い**

- 根拠: `s2b-plan.md:424-442`、実際の protocol 境界 `tools/spool_fold.py:2284-2364`、`tools/dev_wave_land.py:1911-1955`
- apply→commit→mark→finalize helper は、第二 transaction を開始できる状態を作るには必要です。しかし helper が直接 synthetic commit を作り、land lock、staged path closure、postcondition、`verify_declared_fold_commit`、crash-before-mark を通らないなら、正常系の state cleanup しか検査しません。
- helper の前後で `phase=applied` state の存在、mark 後の committed state、verifier 通過、finalize 後の absent を各 assert しなければ、期待値を緩めていなくても coverage が甘くなります。
- **成果物影響:** テストは連続 fold を通すのに、実 land では state 残存・未検証 commit・誤 phase を受入まで検出できず、certified 台帳の欠落を本番相で初めて発見します。

## 親 brief 自身への反論

親 brief の「現行の窓は commit で閉じている」は、`s1-brief.md:32-40` の一回の SIGKILL 実測としては妥当ですが、一般化はできません。

- 測ったのは現行 code の commit 直後一注入点です。新 protocol の state write、target/GC、mark、postcondition、finalize、rollback は未測定です。
- state が無かったのは、現行 `apply_fold()` が state を `tools/spool_fold.py:2357` で削除する設計だからです。新設計ではその削除を finalize へ移すため、同じ観測結果は phase lifecycle の証拠になりません。
- brief 自身が `s1-brief.md:39-40` で `verify_declared_fold_commit` が一度も走っていないと認めています。したがって、その実測で「certified fold が安全」とは言えず、未検証 commit が main に載る相を実際に残しています。
- synthetic fixture 一回では、standalone 無排他、別 wave の古い state、rollback 二重故障、mark の atomic write、電断による ref 巻き戻りを反証できません。

したがって段 4 では、少なくとも P5 の applied-child 分岐、rollback 後の committed state、standalone race、finalize unlink 後例外、active discovery の verifier 呼出しを仕様として固定しない限り、実装へ進めるべきではありません。