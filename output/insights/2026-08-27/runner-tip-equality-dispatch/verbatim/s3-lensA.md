静的検査のみで、pytest は実走していない。

### 所見 1: 実 Git blob reader の revision 束縛には mutation kill が無い

**根拠 (file:line)**

- main を選ぶ呼び出し自体は `tools/acceptance_launcher.py:436`、実行引数は `:441`、M3 は `:446-449`。
- しかし実際の Git object spec は `_read_runner_blob` の `tools/acceptance_launcher.py:173-196`、特に `:187` で構成される。
- 改訂予定の launcher test は `orchestrator/tests/test_acceptance_launcher.py:102-120` と同様に `blob_reader` を差し替えるため、`:187` を通らない。
- 実 launcher を通す E2E も、`orchestrator/tests/test_dev_wave_land.py:2026-2050` と `:2111-2139` では main と tip の runner bytes が同じ。
- `_run_blob` の stdin 実行は `orchestrator/tests/test_acceptance_launcher.py:303-315` が殺すが、Git revision 選択は殺さない。

**再現できる形**

等値削除後、`:187` の `f"{revision}:{_RUNNER_PATH}"` だけを `f"HEAD:{_RUNNER_PATH}"` に変える。unit test は reader 差し替えのため影響を受けず、現行 E2E は HEAD と tested main の runner が同じなので通る。初回・tip 読取・M3 再読がすべて HEAD を読むため、M3 も恒真になる。

なお、`:436` を tested tip 読取へ変える mutation は読取順 assertion `test_acceptance_launcher.py:125`、`:441` を tip bytes 実行へ変える mutation は identity assertion `:127` が既に殺す。改訂案の bytes 差はここをさらに強くする。

**成果物影響**

この mutation が入ると、受入受領証の `runner_executed_sha256` と suite verdict は tested tip/HEAD の runner に由来する。正しい land の `dev_wave_land.py:1085-1086` はその受領証を拒否するため、新たに許可するはずの runner 変更 wave が `landed` ではなく `acceptance-receipt-rejected` と記録される。

**重み (must-fix | nit | scope 外)**

must-fix。main/tip が異なる実 Git E2E が少なくとも一つ必要。

### 所見 2: tip runner の実在・blob 条件は独立に殺されていない

**根拠 (file:line)**

- tip/main 欠落拒否は `tools/dev_wave_land.py:1065-1068`。
- tip の blob 条件は `:1081`、main の blob 条件は `:1080`。
- path absence test は二本あるが、どちらも main から runner を削除し tip で再追加する fixture である。`orchestrator/tests/test_dev_wave_land.py:1690-1719`、`:1722-1749`。tip 欠落は試していない。
- non-blob test は main を tree に変え、そのまま tip に継承するため、main と tip が双方 tree である。`orchestrator/tests/test_dev_wave_land.py:1858-1877`。
- このため `:1080` だけ、または `:1081` だけを一行削除しても、同 test はもう片方で拒否される。

**再現できる形**

- main は通常 blob、tip だけ `tools/run_tests.py` を tree にする。
- receipt は tested main runner の SHA-256 を持たせる。
- `dev_wave_land.py:1081` だけを `or False` に変える。

このとき main の type、双方の object ID 形式、main digest はすべて通り、tip の object ID は以後使われないため land できる。既存 non-blob test は main 側 `:1080` で落ち続け、この mutation を殺さない。

tip 欠落についても専用 fixture が無い。`:1067` を弱めた場合は現状 `:1081` の dereference で例外化するだけで、構造化された fail-closed rejection を固定できていない。

**成果物影響**

tip type predicate の退行を放置すると、tested tip の runner が tree/commit でも受領証が受理され、`main_after` がその tip へ進み、worklog/land JSON は `status="landed"` と受領証 SHA を記録する。tip 欠落の退行では構造化 LandResult が出ず、記録値自体を失う可能性がある。

**重み (must-fix | nit | scope 外)**

must-fix。main 非 blob、tip 非 blob、tip 欠落を別 fixture にする必要がある。

### 所見 3: object ID 形式の caller 側二述語は恒真である

**根拠 (file:line)**

- `_runner_tree_entry` は `tools/dev_wave_land.py:838-840` の正規表現で、40桁または64桁の小文字 hex だけを返し、不一致は `:843-844` で拒否する。
- したがって caller の `:1082-1083` は、現行 helper から到達可能な値に対して恒真。
- `_runner_tree_entry` の malformed `ls-tree` 出力を試す test は見つからず、同二行を一行ずつ削除して落ちる test も無い。

**再現できる形**

`:1082` または `:1083` だけを削除する。helper が返せる値の集合が変わらないため、全 runner fixture の判定結果は変わらない。

**成果物影響**

現行 helper のままなら、受領証・land 受理集合・worklog 値は変化しない。SHA 形式保証の実効主体は `:838-844` であり、プランが `:1082-1083` を独立した発火保証として数える点だけが不正確。

**重み (must-fix | nit | scope 外)**

nit。「謳うだけで発火しない述語」は `dev_wave_land.py:1082-1083`。防御的重複として残すこと自体は問題ない。

### 所見 4: 受理集合以外に retryable/release 分類も変わる

**根拠 (file:line)**

- 現在は runner 不等値が `tools/dev_wave_land.py:1084` で short-circuit し、`:1088` の非 retryable rejection になる。
- 削除後は main content 読取 `:1085-1086`、non-attributable の checker lookup `:1093-1108` まで進む。これらの process failure は `:904` または `:1108` で `retryable_same_request=True`。
- LandResult は `:227-252` で `retryable_same_request` を出力し、`:5527-5540` で `release_safe` もそれに応じて変える。
- 現行 ordering test `orchestrator/tests/test_dev_wave_land.py:1646-1686` は、runner 不等値が checker failure より先に拒否し、`(release_safe, retryable_same_request) == (True, False)` になることを固定している。
- 段2プラン `s2-plan.md:104` はこれを main digest mismatch test に置換するため、runner 不等値時の新分類を覆わない。

**再現できる形**

runner は main/tip で異なるが receipt digest は main に一致させ、non-attributable checker lookup だけを現行 test 同様に return code 128 とする。

- 変更前: runner 等値で先に拒否、`(True, False)`、checker lookup なし。
- 変更後: checker lookup が発火し、`(False, True)`。

child-green でも main blob の `cat-file blob` failure を注入すれば同型になる。

**成果物影響**

land はどちらも拒否するが、JSON/worklog の `release_safe` が true から false、`retryable_same_request` が false から trueへ変わり、CLI の lease は `dev_wave_land.py:5622-5624` により release 対象から retained へ変わる。「受理集合だけが一点広がる」という brief の主張は、外部処理失敗を含む観測可能結果については成立しない。

**重み (must-fix | nit | scope 外)**

must-fix。挙動自体は新しい評価順として自然だが、差分主張を限定し、このケースを明示的に test すべき。

### 所見 5: 親の fixture 観測は正しいが、同型 E2E が二本残る

**根拠 (file:line)**

- land positive test は `orchestrator/tests/test_dev_wave_land.py:1574-1576` で runner blob 同値を明示 assertion しており、main/tip 照合先を区別できない。
- receipt helper の既定も `:354-357` で tested tip digest。
- launcher test は `orchestrator/tests/test_acceptance_launcher.py:92-95` で同じ bytes の別 object、`:127` で identity を見る。親の観測どおり。
- 他に、実 launcher/waiter/land を通す `test_real_waiter_receipt_is_consumed_by_real_land_end_to_end` の `test_dev_wave_land.py:2026-2050`、`test_real_child_green_waiter_receipt_passes_real_land_end_to_end` の `:2111-2139` も main/tip runner が同一。
- `test_m4_runner_executed_digest_mismatch_is_rejected` の `:1062-1079` も同値 fixture だが、これは任意の誤 digest を殺す目的なので、その目的については恒真化していない。

**再現できる形**

実 E2E の tip commit に main と異なる runner bytes を置き、receipt が main digest、実行結果が main runner 固有の結果であることを確認する。現行のままでは所見1の `HEAD` mutation を区別できない。

**成果物影響**

同型 E2E を残すと、unit seam の外で tip runner を実行する退行が受入受領証生成まで到達しうる。land は digest 不一致で拒否するため、受理集合は狭まり、runner 変更 wave の worklog が成功から拒否へ変わる。

**重み (must-fix | nit | scope 外)**

must-fix。親の測り方は過大ではなく、むしろ実 E2E 二本まで一般化が不足している。

### 所見 6: 削除本体は二か所で、三か所目や過剰削除は見つからない

**根拠 (file:line)**

- launcher の byte 比較は `tools/acceptance_launcher.py:438-439`。
- land の runner object ID 比較は `tools/dev_wave_land.py:1084`。
- waiter は outcome の SHA 型だけを見る `tools/dev_wave_wait.py:3028-3052`。
- `tools/dev_wave_land.py:1124` は checker blob の main/tip 等値で、runner ではない。
- 段2プランは tip 読取 `acceptance_launcher.py:437`、双方 entry の実在/type、main digest `dev_wave_land.py:1065-1086` を残している。

**再現できる形**

production Python source を runner path、runner digest、main/tip entry、旧 error text で静的検索した範囲では、main/tip runner の bytes/object ID を比較する実行述語は上記二つだけだった。

**成果物影響**

予定どおり二項だけを削除すれば、正常に Git lookup できる場合の land 受理集合は「tip runner が main と異なるが、receipt digest は main と一致する」状態だけ広がる。checker、waiter、schema の certified 値は変わらない。

**重み (must-fix | nit | scope 外)**

nit。削除範囲についてはプランを支持する確認結果。

### 所見 7: launcher 先例は source 選択だけの類推で、完全な同型ではない

**根拠 (file:line)**

- waiter の launcher 選択は main に launcher があれば main、無ければ tip bootstrap である。`tools/dev_wave_wait.py:2565-2577`。
- land も `tools/dev_wave_land.py:1021-1044` で同じ分岐を検証し、bootstrap 時は main と locked main の双方に launcher が無いことを要求する。
- main launcher mode では tip launcher の実在・type・等値は検査しない。一方 runner は変更後も tip entry の実在と blob typeを要求する `:1065-1083`。
- receipt も launcher には二つの authority kind がある `tools/acceptance_launcher.py:23-27,365-396` が、runner に bootstrap mode は無い。

**再現できる形**

tested main に launcher がある状態で tip launcher を削除しても main launcher mode は成立する。一方、同じことを runner に行えば提案後も拒否される。また main に launcher が無い初回導入では tip launcher が実行され、「常に tested main launcher」という説明は成立しない。

**成果物影響**

今回の runner コード差分自体には影響しない。ただし docs が「launcher と完全に同じ束縛形式」と記すと、受領証の `launcher_source_revision` と `authority_kind`、tip 実在条件を誤って説明する。類推は「main が存在する通常モードの source 選択」に限定すべき。

**重み (must-fix | nit | scope 外)**

nit。

### 所見 8: 段6 mutation matrix は複合 fixture による誤帰属が起きうる

**根拠 (file:line)**

- divergent launcher positive は、読取 revision `test_acceptance_launcher.py:125`、実行 object `:127`、M3 `tools/acceptance_launcher.py:446-449` を同時に観測する。一本の失敗だけではどの述語が殺したか確定しない。
- tip digest negative は、旧 equality `dev_wave_land.py:1084` が残っていれば main digest `:1085-1086` に到達せず拒否される。
- non-blob test は前述のとおり main/tip 両 predicate が同時に成立する `test_dev_wave_land.py:1858-1877`。
- ordering test は `:1646-1686` の equality short-circuit と checker failure の二条件を含む。

**再現できる形**

各 mutant について、期待する一述語以外の先行 gate を通る positive control を同じ fixture で確認する。特に:

- main digest target mutantには、equality 削除済みの divergent positiveを先に通す。
- main/tip type mutantには片側だけ非 blobの fixtureを使う。
- actual reader mutantには差し替え seam ではなく実 Git E2Eを使う。
- retryable matrixでは checker lookup が実際に呼ばれたことも観測する。

**成果物影響**

誤帰属を放置すると、matrix は「mutation を殺した」と記録しても別 gateだけが発火しており、main 以外の bytesから作られた受領証や tip 非 blobを受理する landを certified と誤記録しうる。

**重み (must-fix | nit | scope 外)**

must-fix。

## 総括

最重は、実 Git reader の revision 束縛を divergent E2E が殺さない点、tip runner の実在/typeを片側 fixtureで殺していない点、runner divergence後の `retryable_same_request` 分類変化を差分に数えていない点。  
削除対象が二か所だけという判断と、正常 lookup時の論理的な受理集合差分は正しい。  
段6では「落ちた」だけでなく、狙った述語まで到達したことを positive controlで帰属させる必要がある。