## 所見 1: tip waiter による受領証直作成は残る

所見: runner 単独差し替えは閉じるが、「tip 側だけで偽の緑受領証を作れない」という広い境界は閉じない。tip 束縛の waiter は launcher を迂回して v5 receipt を合成できる。

再現または根拠: 静的根拠。D440:20-22 がこの経路を明示的に開いたままとしている。waiter は tip bytes と照合されるだけである（tools/dev_wave_wait.py:2158-2237）。land が検査する launcher、waiter、runner の SHA 値は署名ではなく Git から再計算可能な値である（tools/dev_wave_land.py:934-1133）。s1-brief.md:10-11 も D583 残余 (i) として非対象化している。

影響: runner が main と同一の通常 wave でも、悪意ある waiter はテストを実行せず child-green receipt を合成できる。D838 の狭い「runner 差し替え」経路は閉じるが、受領証一般の非偽造性は成立しない。

scope 内か外か: scope 外。D440 の意図的非対称かつ D583 残余 (i)。

推奨対応: 本 wave で実装したふりをしない。文書上の保証を「runner 単独差し替えでは偽造できない」に限定する。広い非偽造性が必要なら、waiter の発行権限をどう固定するかを別裁定パッケージにする。

## 所見 2: launcher bootstrap も tip 発行者を許す

所見: `tested_main` に launcher が存在しない場合、tip launcher が正式な発行者になる既存 bootstrap が残る。

再現または根拠: 静的根拠。waiter は main に launcher が無いと `tested-tip-bootstrap` を選ぶ（tools/dev_wave_wait.py:2528-2540）。land も tested main と locked main の双方に launcher が無い場合、tip launcher を受理する（tools/dev_wave_land.py:1026-1043）。テストにも通過正例がある（orchestrator/tests/test_dev_wave_land.py:1043-1055）。

影響: launcher 初回導入状態では、tip が launcher、waiter、receipt を一体で制御でき、runner が main と同一なら偽の child-green を通せる。現在の main には launcher があるため、通常の子孫 wave では発火しない。

scope 内か外か: scope 外の既存 bootstrap 面。新しく開く穴ではない。

推奨対応: bootstrap 時だけ別の人手承認または main 側導入手順を必要とするか、裁定対象にする。通常運用の保証と bootstrap 時の保証を分けて記述する。

## 所見 3: PATH 解決された Python は実行 bytes の保証を破れる

所見: プランは runner blob の読み元を main に移すが、実際にその bytes を解釈する `python3` は PATH 解決のままである。PATH に tip 書込可能ディレクトリが入る環境では、main runner を実行せず緑を作れる。

再現または根拠: 条件付き推測。launcher は runner 子を bare `python3` で起動する（tools/acceptance_launcher.py:214-227）。waiter から launcher への起動では環境を明示固定していない（tools/dev_wave_wait.py:824-830）。例えば PATH に repo root または `.` が先行する環境で、tip に実行可能な `python3` を追加し、scheduler marker を出して rc=0 で終了させる。launcher は main runner の SHA を receipt に記録する一方、偽 interpreter は stdin の runner bytes を無視できるため、land の digest 検査も通る。

実測: 現セッションでは `git` と `python3` はともに `/usr/bin` へ解決され、PATH に repo 配下や `.` は無かった。この環境では上記条件は成立していない。

影響: 条件成立時は、main blob の取得、main/tip 一致、receipt digest の全検査が緑でも、実際の runner は動いていない。

scope 内か外か: scope 内。実行主体を main bytes に束縛する契約の実行層である。

推奨対応: `_run_blob` は検証済みの絶対 Python executable を使う。`_read_runner_blob` の bare `git`（tools/acceptance_launcher.py:173-193）も `/usr/bin/git`、固定 config、全 `GIT_*` 除去へ揃える。D440:9-13 と同じ executable、env 固定を適用し、PATH 汚染負例を追加する。

## 所見 4: land 自身の権威は提示資料から証明できない

所見: land は launcher、waiter、runner を再検証するが、実行中の `tools/dev_wave_land.py` 自身が main 由来であることは自己検証していない。

再現または根拠: 静的根拠と条件付き推測。受領証検証は tools/dev_wave_land.py:908-1139 にあるが、land 自身の blob 束縛は含まれない。CLI は現在実行された module をそのまま使う（tools/dev_wave_land.py:5573-5615）。もし運用 caller が tip pathname の land を直接起動するなら、tip は検証処理自体を削除できる。指定資料には caller 側の source binding が無いため、実運用でこの条件が成立するかは確認できない。

影響: 条件成立時、P3 の「独立検証」は独立した trust layer にならず、runner gate 全体を回避できる。

scope 内か外か: land の起動権威は本 wave の編集 scope 外。real なら新規ではなく既存の trust-root 欠落であり、裁定パッケージ候補。

推奨対応: 実運用 caller が land をどの revision、blob、絶対 executable から起動するかを証拠化する。tip 起動なら tested main または外部固定 blob へ束縛する別設計を裁定する。

## 所見 5: gate の各層と未被覆面

所見: プランは runner 固有の中核三層を覆うが、実行 interpreter、発行権限の例外、land 自身、受入後 landing tip は覆わない。

再現または根拠: 静的整理。

1. launcher 選択: tested main launcher。既存実装で被覆（tools/dev_wave_wait.py:2521-2559）。
2. runner bytes 取得と suite 前 equality: プランで被覆（plan.md:15-28）。
3. 実際の interpreter: PATH 解決のため未被覆（tools/acceptance_launcher.py:214-227）。
4. receipt 発行: 新 launcher では equality 後だけ発行するが、tip waiter と bootstrap は例外。
5. receipt 公開: tip waiter が担う（tools/dev_wave_wait.py:3958-3964）。
6. land 独立検証: exact `tested_main` と `tested_tip` を使う計画で被覆（plan.md:38-57）。
7. land 実行体の権威: 提示資料では未証明。
8. 受入後の `landing_tip`: receipt 検査には渡されず未被覆（tools/dev_wave_land.py:5039-5045）。

影響: 「runner 単独差し替えを launcher と land の双方で拒否する」は成立する。一方、「全発行経路」「実行 process 全体」「最終 landing tip」まで閉じたという説明は過大である。

scope 内か外か: interpreter は scope 内。他は既裁定または scope 外。

推奨対応: 成果物の保証を層ごとに限定して記載し、未被覆面を明示する。scope 外面は裁定パッケージへ分離する。

## 所見 6: main/tip equality は恒真ではないが、二つの検査は冗長になる

所見: main と tip の runner blob equality 自体は恒真ではなく、有効な gate である。ただし equality 成立後に receipt digest の照合先を tip から main へ変えることは論理的に同値で、独立保証ではない。また exact main SHA の M3 再取得不一致は正常な Git object store では通常発火しない。

再現または根拠: 静的根拠。runner を変更、追加、削除した wave、claim 後に runner を変更した main を merge した場合、または merge 解決で別 blob を選んだ場合に equality は偽になる。plan.md:80-84 には main 側 runner 欠落の実在履歴もある。一方、main/tip object ID equality を先に要求するなら、tools/dev_wave_land.py の digest をどちらの同一 blobへ照合しても結果は同じである。M3 は同じ exact tested-main SHA を再取得するため、通常の Git 不変性の下では同じ bytes になる。

実測: 現在は HEAD `bb7753fa...`、main `a068b7f5...` と commit は異なるが、双方の runner は blob `b1b1b374...`、content SHA-256 `65f7f84f...` で一致した。plan.md:97 の「HEAD == main」は既に stale だが、runner equality は保たれている。

影響: equality は本変更の実効保証である。一方、M3 と「digest の main 側化」を別々の強い保証として数えると、実効層数を過大評価する。

scope 内か外か: scope 内の説明とテスト意味付け。

推奨対応: primary guarantee を「suite 前 equality」と「land の独立 equality」に置く。M3 は retrieval/execution seam の故障注入検査、digest 照合先変更は将来の gate 退行に対する防御として説明する。

## 所見 7: 本 wave は現状受入可能だが、plan の revision 記録は既に古い

所見: 現時点の runner 条件は満たす。ただし HEAD と main は既に異なり、受入中の main merge 後に生成される exact tested tip を使う必要がある。

再現または根拠: 実測では HEAD `bb7753fa...`、main `a068b7f5...`。指定4 control file の blob は HEAD/main で同一で、runner も前記のとおり一致した。waiter は claim 後に behind を検出すると main を merge し（tools/dev_wave_wait.py:3633-3689）、receipt の `tested_main` には claim 時 main、`tested_tip` には merge 後 HEAD を渡す（tools/dev_wave_wait.py:3746-3769）。新 land は `locked_main` ではなく receipt の exact tested main/tip を検査する（tools/dev_wave_land.py:5039-5045）。

崩れる条件:

- claim 後、内部 merge 前に main の runner が変わると、旧 launcher は tip runner receipt を発行できるが、新 land の main/tip equality が拒否する。
- receipt 発行後に main が audited closure 外へ進めば、land は stale-main で拒否する（tools/dev_wave_land.py:2767-2784）。
- receipt と別の merge 後 tip を `tested_tip` として渡せば、receipt field binding で拒否される。
- main の進行を明示的な forward-main `landing_tip` として扱う場合は次所見の例外がある。

影響: plan.md:164-173 の互換性説明は条件付きで正しい。現在の静的状態に blocker は見つからないが、plan.md:97 の revision 値を受入根拠には使えない。

scope 内か外か: 本 wave の受入確認として scope 内。

推奨対応: P4 は実装 commit 直後だけでなく、waiter 内部 merge 後の receipt `tested_main`、receipt `tested_tip`、両 tree entry を対象に実施する。main が途中で runner を変えた場合は同じ receipt を救済せず再受入する。

## 所見 8: forward-main landing tip の runner は検査対象外

所見: 受入後に clean forward-main merge を追加した `landing_tip` は、receipt の再利用が許されるが、その landing tip の runner は今回の gate で比較されない。

再現または根拠: 静的根拠。land は receipt 検証へ original `tested_tip` を渡し、`landing_tip` を渡さない（tools/dev_wave_land.py:5039-5045）。既存テストは acceptance 後に main の commit を merge しても receipt bytes がそのまま生きる契約を固定している（orchestrator/tests/test_dev_wave_land.py:6580-6628）。

影響: forward merge された main が `tools/run_tests.py` を変更していれば、最終 landing tip は receipt が実行した runner と異なる。これは tip 単独攻撃ではなく、変更元が trusted main で、既存の forward-main receipt survival 契約による。ただし「最終 landing 内容がその runner で受入済み」という広い主張はできない。

scope 内か外か: scope 外の既存 landing 契約。real な裁定パッケージ候補。

推奨対応: runner を変更する incorporated-main merge だけ receipt 再利用を拒否して再受入させるか、保証を original tested tip に限定するかを裁定する。

## 所見 9: Git failure の retryable 分類が広すぎる

所見: 新規 Git 検査の全 nonzero rc を一律 `retryable_same_request=True` にする根拠は不足している。

再現または根拠: 静的根拠。`ls-tree` の任意の非zero rc は retryable（tools/dev_wave_land.py:821-835）、`cat-file` の任意の非zero rc も retryable（tools/dev_wave_land.py:898-904）。永続的な object 欠損、破損、Git 非互換、実行 file 欠落も同じ分類になる。計画テストは合成 rc=128 を一時故障として固定するだけである（plan.md:137-139）。

影響: 永続拒否でも lease が保持され、同一 request の再試行対象になり続ける。安全側ではあるが、拒否が運用上確定せず滞留する。

逆方向: path 欠落、非 blob、SHA 不正、main/tip 不一致、digest 不一致は exact immutable revision の構造的事実であり、permanent 分類は妥当だった。新条件で、通常環境の一時障害を明確に permanent 扱いする逆方向の誤りは見つからなかった。

scope 内か外か: scope 内。

推奨対応: subprocess start/OSError、signal、資源障害と、Git が正常に返した構造的 object 不在を分離する。少なくとも「欠損 object が反復しても retryable」の負例を追加し、一律 rc 判定を裁定し直す。

## 所見 10: 変異三件とテスト検出力

所見: 中核二変異は計画テストで殺せるが、tip runner 読取失敗時のフォールバック変異は生存する。

再現または根拠: 静的変異設計。

1. 変異: launcher の main/tip equality を `_run_blob` 後へ移す。  
   殺すテスト: `test_main_tip_runner_blob_mismatch_is_rejected_before_execution`。`blob_runner` が未呼出しであるという assertion が殺す。

2. 変異: land の runner equality を従来どおり `non-attributable-only` 内だけに残す。  
   殺すテスト: `test_land_rejects_child_green_runner_blob_divergence`。child-green の通過を RC_AUDIT へ反転するため殺せる。

3. 変異: `tested_tip` の読取だけが失敗した場合、取得済み main bytes を比較用 tip bytes として代用して receipt を発行する。  
   殺すテスト: なし。通過正例、bytes 不一致、M3 main drift、main 欠落はいずれも tip 読取例外を発生させない。plan.md:101-120 に tip 欠落専用負例が無い。

影響: 変異3では land が最終的に tip path 欠落を拒否するため着地は防げるが、「issuer も欠落時に発行しない」という層別 fail-closed 契約がテストされない。

scope 内か外か: scope 内のテスト計画穴。

推奨対応: `test_missing_tested_tip_runner_is_rejected_before_execution` を追加し、main 読取成功、tip 読取失敗、`blob_runner`、outcome、completion、receipt の全未到達を固定する。

## 総括

- 最重は、PATH 解決された `python3` により条件付きで main runner を実行せず緑を作れる点で、scope 内修正が必要。
- tip waiter の受領証直作成は D440/D583 が意図的に残した scope 外経路であり、広い非偽造性は成立しない。
- launcher bootstrap も初回導入時には tip を発行者にする既存例外である。
- land 自身の実行権威は提示資料から証明できず、tip 起動なら別の trust-root 穴になる。
- main/tip runner equality は恒真ではなく有効だが、M3 と digest 照合先変更は独立保証としては弱い。
- 本 wave の runner blob は現在 main と一致するが、HEAD と main は既に異なり plan の revision 記録は stale。
- acceptance 内部 merge で runner が変われば新 land が安全側に拒否するため、再受入が必要。
- forward-main landing tip の runner は未検査で、最終 landing 内容まで保証するなら別裁定が要る。
- Git failure の一律 retryable は永続故障まで保持するため分類を狭めるべき。
- tip runner 欠落時フォールバックを殺すテストがなく、負例追加が必要。