静的結論は、二つの等値述語を削除すれば機械的には `tools/run_tests.py` 変更 wave を land できるものの、tested main の runner を実行するという保護は Pegasus 経路で維持されません。pytest は実走していません。

### 所見 1: 計算ノードで tip 側 runner を再起動するため、D838 の穴が通常経路として再び開く

**根拠 (file:line)**

- launcher は tested main の bytes を読み、working-tree の canonical path を `__file__` に設定して実行する: `tools/acceptance_launcher.py:51-61,425-449`
- その main 版 runner は `__file__` から tip working tree を `_REPO` にし、tip 側 `dispatch_compute` を import する: `tools/run_tests.py:55-61,1307-1323`
- dispatcher の request は `repo_root/task/args` しか束縛せず、計算ノードで `repo_root/tools/run_tests.py` を pathname から再起動する: `tools/pegasus/dispatch_compute.py:112-131,976-1014,2857-2864`
- この残余は既に D524 と T-1374 に明記されている: `docs/decisions.md:21672-21675`, `docs/archive/worklog-phase3-0818-659.md:592-596`
- 段 2 の launcher test は `blob_runner` を fake に差し替えるため、この再進入を通らない: `orchestrator/tests/test_acceptance_launcher.py:102-123`, `s2-plan.md:87-93`

**再現できる形**

tested main=A、`tools/run_tests.py` を 1 行変更した tip=T とする。launcher は A の外側 runner を開始するが、Pegasus dispatch 後の子は T の pathname runner を実行する。例えば `_NPROC_CAP` の 1 行変更でも、計算ノードで観測される値は T 側になる。

**成果物影響**

receipt の `runner_executed_sha256` は A の hash のままなのに、実 pytest を駆動した計算ノード runner は T となり、その receipt を land が受理する。受入受領証と worklog の実行器記録値が実走体を表さなくなる。

**重み (must-fix | nit | scope 外)**

must-fix。二述語の削除だけでは「実行元を tested main の blob に固定する保護」を達成しない。

### 所見 2: claim 後の内部 merge が runner を変えた main を取り込んでも、古い claim main を receipt に残す

**根拠 (file:line)**

- claim に使う main SHA は claim 前に固定される: `tools/dev_wave_wait.py:2891-2898`
- claim 後に main を再解決するが、その戻り値は捨てられ、現在の main を wave へ merge する: `tools/dev_wave_wait.py:3670-3726`
- launcher へ渡す `tested_main` は古い `claim_context.main_sha`、`tested_tip` は merge 後 HEAD である: `tools/dev_wave_wait.py:3783-3801`
- 段 2 文案は、この差では再走しないと明記する: `s2-plan.md:134-136`

**再現できる形**

A で claim した直後、別 wave が `tools/run_tests.py` を変更した S を main へ land する。待ち手は S を merge して T を作るが、receipt は `tested_main=A`, `tested_tip=T`, `runner_executed_sha256=hash(A)` となる。提案変更後は等値拒否が消える。

**成果物影響**

受領証には取り込んだ S やその runner 変更を表す field がなく、land 結果の `incorporated_main_shas` にもこの受入前 merge は入らない。古い main runner による判定として T が certified になる。

**重み (must-fix | nit | scope 外)**

must-fix。D987 の「main 由来 runner 変更だけ再受入」という原則を、受入後だけでなくこの受入前 merge 窓にも適用する必要がある。

### 所見 3: D987 は未実装であり、段 2 の positive test 案は正反対の挙動を固定する

**根拠 (file:line)**

- runner entry の production lookup は tested main と tested tip の 2 回だけである: `tools/dev_wave_land.py:821-848,1065-1086`
- forward-main 経路は landing tip の topology を検査するが、runner を調べず、receipt verifier に landing tip を渡さない: `tools/dev_wave_land.py:4909-4922,5035-5042`
- その後 landing tip へ ff-only land する: `tools/dev_wave_land.py:5492-5504`
- D987 は、取り込んだ main が runner を変えた場合だけ receipt 再利用を拒否すると裁定済み: `docs/decisions.md:34741-34753`
- 現行 positive test は main 側で runner を変更して forward merge し、それでも成功を要求する: `orchestrator/tests/test_dev_wave_land.py:1568-1619`
- 段 2 は tip と locked main を同じ新 runner にして、この forward-main 要素を残す案を示す: `s2-plan.md:101-102`

**再現できる形**

A/T で receipt を作り、main の S で runner を変更し、T へ S を merge して landing tip=L を作る。現行 land は L の runner を一度も引かず成功する。これは D987 が明示的に拒否を要求する入力である。

**成果物影響**

land JSON は `landing_tip_sha=L` と `incorporated_main_shas=[S]` を持ちながら、receipt は T のまま再利用される。D987 が定めた land 受理集合と実装の受理集合が異なる。

**重み (must-fix | nit | scope 外)**

must-fix。D987 は本変更と同じ単位で実装すべきである。同じ verifier と同じ test を変更しながら、D987 違反を positive test に固定するため、親の scope 外判断は維持できない。最低でも forward-main 要素を positive fixture から外し、D987 実装を独立の確定タスクとして残す必要がある。

### 所見 4: `check_acceptance_reds.py` の受理経路は現行待ち手から到達不能で、P4 と runbook が古い

**根拠 (file:line)**

- D690 は自動 checker 起動を削除し、受理を `child-green` だけに限定した: `docs/decisions.md:27259-27289`
- 待ち手は completion の `red_check` を常に `None` にする: `tools/dev_wave_wait.py:3124-3136`
- child rc が 1 を含む非 0 なら completion を送る前に失敗する: `tools/dev_wave_wait.py:3843-3858`
- D873 も「受理は child-green だけ」と再確認している: `docs/decisions.md:32192-32214`
- それでも runbook は二つの受理経路と checker main/tip 等値を現役として説明する: `docs/pegasus-runbook.md:907-925,954-959`
- brief の P4 も「受理経路 ii」を active と扱う: `s1-brief.md:69-70`

**再現できる形**

受入 command を rc=1 にする。待ち手は `acceptance-command` で終了し、`tools/check_acceptance_reds.py` を起動せず、receipt を publish しない。

**成果物影響**

権威ある待ち手が発行できる受入受領証は `child-green` だけである。`non-attributable-only` の receipt や対応する land/worklog 値は現行 production 経路から新規生成できない。

**重み (must-fix | nit | scope 外)**

must-fix。段 2 の二箇所だけでなく、runbook の `907-925` と `954-959` も変更対象に含める必要がある。

### 所見 5: 「既存の受領証・過去の判定結果は 1 件も変わらない」は証明されていない

**根拠 (file:line)**

- brief は拒否を消す変更だから全既存結果が不変と主張する: `s1-brief.md:72-79`
- 権威 receipt は通常 repo 外に置かれる: `docs/pegasus-runbook.md:870-884`
- tracked inventory で確認できる v5 receipt は 1 件で、main/tip runner は同じである: `output/insights/2026-08-21_t1434-wave-d/acceptance-receipt-4.json:1`, `docs/archive/worklog-phase3-0826-960.md:27-29`
- D583 は canonical receipt を静的に組み立てられる残余を明記している: `docs/decisions.md:23559-23566`

**再現できる形**

main/tip runner が異なり、`runner_executed_sha256` が main 内容に一致する canonical v5 receipt を用意する。旧 verifier は `tools/dev_wave_land.py:1084` で拒否するが、提案後は受理する。

**成果物影響**

以前に拒否された divergent receipt の再検証結果は reject から accept へ変わり得る。変わらないと確認できたのは tracked receipt 1 件だけである。

**重み (must-fix | nit | scope 外)**

must-fix。文案は「以前受理された receipt を新たに拒否しない。確認済み tracked v5 1 件は不変。divergent receipt の受理集合は広がる」と狭めるべきである。

### 所見 6: D838 を根拠にした active worklog と後続 decision への追随が段 2 に具体化されていない

**根拠 (file:line)**

- D838 は main 束縛とその代償を明記する: `docs/decisions.md:31681-31697`
- D1103 は現在形で「run_tests を変更した wave は通せない」を根拠にし、同案を却下している: `docs/decisions.md:37224-37236,37271-37274`
- active worklog の T-1932 は依然「ユーザー裁定待ち」で、この制約の解消方法を求めている: `docs/worklog.md:986-990`
- current worklog 本文にも同じ現行制約が残る: `docs/worklog.md:94-97`
- 段 2 の docs 計画は runbook 二箇所だけを具体化している: `s2-plan.md:113-137`

**再現できる形**

runbook と D838 の代償だけを更新して fold すると、次の pending-task 収集では T-1932 が引き続き「裁定待ち」として現れ、D1103 の現在形説明も旧制約を指し続ける。

**成果物影響**

worklog の記録値が「P1・ユーザー裁定待ち」のまま残り、本 wave が解消したはずの作業を再提示する。決定台帳も現行契約を一意に読めなくなる。

**重み (must-fix | nit | scope 外)**

must-fix。新 decision で D838 の「等値と代償」だけを明示的に supersede し、D1103 には歴史的理由である旨を接続し、T-1932 を解決済みに更新する必要がある。

### 所見 7: 本 wave 自身を止める self-binding はないが、受入は旧 launcher で行われる

**根拠 (file:line)**

- tested main に launcher が存在すれば、待ち手は常に main 側 launcher を選ぶ: `tools/dev_wave_wait.py:2565-2577`
- 本 wave の scope は launcher/land であり、runner 自体は変更しない: `s1-brief.md:34-44`
- land は receipt の launcher digest を tested main 側と照合する: `tools/dev_wave_land.py:1021-1053`

**再現できる形**

本 wave の A/T では runner bytes が同じなので、A の旧 launcher が持つ等値 gateも通る。receipt 発行後は T の新 `dev_wave_land.py` が実行されるが、その receipt は旧 land でも runner 等値を満たす。

**成果物影響**

receipt の `launcher_blob_sha` と `launcher_executed_sha256` は新 tip launcher ではなく旧 tested-main launcher の値になる。本 wave は land 可能だが、新 launcher の production 起動は次 wave からである。

**重み (must-fix | nit | scope 外)**

nit。self-blocker ではないが、受入実測が新 launcher 自身を実行したとは記録できない。

### 所見 8: 変異 harness と fanout は tip HEAD を固定するだけで、main/tip 等値の追加関門ではない

**根拠 (file:line)**

- harness は runner と dispatcher の working-tree bytes を固定 HEAD と照合する: `tools/mutation_harness.py:767-819,825-839`
- fanout contract も runner/dispatcher を同じ固定 HEAD の path 集合に置く: `tools/mutation_fanout_contract.py:35-41`
- fanout の使い捨て checkout path もその HEAD の runner/dispatcher を指す: `tools/mutation_fanout.py:624-633`

**再現できる形**

tip HEAD に `tools/run_tests.py` の変更を commit すれば、harness は変更後 tip bytes と HEAD が一致するため受理する。tested main の runner は参照しない。

**成果物影響**

mutation ledger の `entrypoint_sha256` と `head_blob_sha256` は tip runner を記録する。受入 receipt の main runner 束縛を証明も補強もしないが、変更 wave を追加で拒否もしない。

**重み (must-fix | nit | scope 外)**

nit。

## 裁定パッケージ候補

### 所見 9: 到達不能な `non-attributable-only` land 受理能力を残すかは別判断である

**根拠 (file:line)**

D690 は待ち手の producer 経路だけを削除し、land と checker は編集対象外と明記した: `docs/decisions.md:27265-27268,27285-27289`。land は現在も synthetic/legacy な `non-attributable-only` receipt を検証する: `tools/dev_wave_land.py:992-1018,1093-1129`。

**再現できる形**

正規待ち手では生成不能だが、全 field を満たす receipt を直接渡すと land の当該枝へ到達する。

**成果物影響**

削除すれば land の受理集合が縮み、残せば到達不能な legacy verifier が残る。今回の runner 等値撤去とは独立した選択である。

**重み (must-fix | nit | scope 外)**

scope 外。今回必要なのは runbook を現行 production 経路へ狭めることであり、この枝の存廃は別裁定に分離できる。

## 総括

最重は、計算ノードが tip の runner を pathname 再起動し、main digest の receipt で tip runner を certified にできる点です。  
次に、claim 後 merge と forward-main receipt reuse の両方で、main 由来 runner 変更を見逃します。D987 は同じ変更単位で実装すべきです。  
また runbook の非帰属受理経路は D690 後の実装と逆で、段 2 の二箇所修正だけでは文書整合が取れません。