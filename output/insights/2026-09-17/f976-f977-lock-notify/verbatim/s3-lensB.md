## 変異 matrix の帰属

以下、`s1-brief.md`・`s2-plan.md`・`rulings-verbatim.md` は射影で指定されたファイルを指す。全必読範囲を読了した。検算は読取・静的解析のみで、pytest・変異実行・ファイル変更は行っていない。KILLED／SURVIVED は机上予測である。

**所見**：M1／M2 の reader は production 経路を通るが、約1秒の実時間 deadline では高負荷時の失敗を変異へ帰属できない。
**分類**：plausible
**根拠**：`s2-plan.md:92` は「全 actor が production の `_real_repo_file_lock`」、`:95`〜`:100` は pipe 通知・reader 起動要求・解放を経て「writer timeout は約1秒」とする。
**影響**：無変異でも writer が reader 解放前に期限切れになり、M1／M2 の赤と区別できない；生 flock reader への逃避という疑いは反証される。
**推奨**：production reader は維持し、実 flock の EAGAIN と actor 順序を assertion の中心にする；短い wall-clock 成否比較を避け、テスト内時計の制御と child 回収用の実時間 watchdog を分離する。

**所見**：M2 は改訂する既存模擬テストでも検出されうるため、新設 N1 だけへの帰属は不完全である。
**分類**：plausible
**根拠**：`s2-plan.md:134`〜`:140` は gate 取得による cohort 遮断・4 fd の close・取得時刻 `[6.0, 6.0]` を要求する一方、`:267` は M2 の killer を N1 だけとする。
**影響**：writer gate を除去すると既存模擬側の fd／時刻 assertion が先に赤になり、全体の赤だけでは N1 の実 kernel 検出を証明できない。
**推奨**：M1 は N1、M2 は N1 と既存模擬の双方を候補として登録し、変異時は名指し node ごとの結果を残す；M0 の comment-only は機能上等価の SURVIVED 予測と分離する。

**所見**：M3／M4／M5 は検出経路を持つが、各 node が証明する範囲を広く書きすぎないことが必要である。
**分類**：plausible
**根拠**：`s2-plan.md:114`〜`:123` は gate 保持下の昇降格、deadline 引数観測、例外後 EBADF を指定し、`:276` は M3 が昇格側で先に死ぬと認めている。
**影響**：M3 は降格単独の退行を独立実証せず、M4 は実時間配分だけなら flaky、M5 は例外時 close だけで成功時・fork reset の漏れを代表しない。
**推奨**：M3 は昇格／降格を別実行にし、M4 は legacy/common の gate/main 全取得で同一 deadline を比較する；M5 は `[main-timeout]` の EBADF を直接 killer とし、成功時 close は既存模擬、fork close は専用 node に帰属させる。

**所見**：M6〜M9 の予測は成立しうるが、「landed allowlist 拡大は既存 test が検出する」という一般化は成立しない。
**分類**：real
**根拠**：`s2-plan.md:271`〜`:278` に各 killer があるが、既存 status 入力は `test_wave_land_window.py:1602` の `stale-main`・`lock-busy`・`rejected`・`fold-failed`・非文字列で、`fold-rollback-failed` はない。
**影響**：M6＝main-mismatch、M7＝tip-equals-main、M8＝rollback-incomplete、M9＝固定文一致は他条件正常なら KILLED 予測；landed に `fold-rollback-failed` だけを追加する変異はこの既存負例群では SURVIVED 予測となる。
**推奨**：landed 負例へ `fold-rollback-failed` を追加し、各 rolled-back 負例は対象条件以外をすべて受理値に固定する；「allowlist 拡大」を具体的な追加 status ごとに記す。

**所見**：rolled-back の `main_after` SHA 検査削除には、plan の「after 不正」だけでは独立した killer が確定しない。
**分類**：plausible
**根拠**：`s2-plan.md:158`〜`:168` は SHA 検査と `main_before == main_after` を併用し、`:200` の負例列挙は「after 不正」とだけ記している；`wave_land_window.py:71` が型・桁数・hex を検査する。
**影響**：after だけを壊して before を正常 SHA に残すと、SHA 検査を削除しても一致検査が拒否するため、その変異は SURVIVED となる。
**推奨**：before と after に同じ不正値を入れ、tip は正常かつ別値にする専用 case を明示する；tip SHA 検査削除も他条件正常の不正 tip case に帰属させる。

**所見**：既存サイズ超過負例をそのまま複製しても、サイズ上限削除の変異は検出できない。
**分類**：real
**根拠**：`test_wave_land_window.py:1774` の負例は `land_json.write_bytes(b" " * 65537)`；`wave_land_window.py:598` は読み込んだ bytes を JSON loader へ渡し、`s2-plan.md:203`〜`:204` は同形の追加を予定する。
**影響**：上限を外しても空白だけの JSON は不正なので rc=3 のままであり、この node ではサイズ上限削除が SURVIVED となる。
**推奨**：P3 を満たす有効 JSON を空白または無視するフィールドで65,537 bytesにし、65,536 bytes の受理例と対にする。

## 正例・負例の対称性

**所見**：reader overlap 正例が gate 全削除でも通ること自体は恒真化ではないが、writer 優先の証拠にはならない。
**分類**：refuted
**根拠**：`s2-plan.md:108` は「A の解放前に B の取得通知」を要求する；既存 `test_real_repo_serialization.py:2047` も reader 2本の overlap を検査し、N1 は別途 writer の先行を要求する。
**影響**：正例は reader を過剰直列化する退行を殺す一方、gate 除去は負例が殺す関係であり、正例だけを writer 優先の実証に数えると保証を過大評価する。
**推奨**：plan v2 では P1 を「並行性維持」、N1 を「gate 除去検出」と明記する；両者を同じ変更単位から分離しない。

**所見**：既存模擬の `[147.0, 147.0]`→`[6.0, 6.0]` は、時刻の置換だけでは新しい意図を pin しない。
**分類**：plausible
**根拠**：`test_real_repo_serialization.py:2086` の模擬は現状 fd を無視する；`s2-plan.md:134`〜`:140` は gate 取得時点・fd 区別・close 順序への変更を予定する。
**影響**：無条件に cohort を6秒で消す実装なら writer gate を外しても時刻 assertion が通り、単なる期待値合わせになる。
**推奨**：cohort の後続入場停止を実際の gate EX 成功イベントだけで切り替え、gate/main の取得・解放順を独立に assert する；実 kernel の保証は N1 に限定する。

## docs の pin と byte 予算

**所見**：入口の置換は予算内だが、plan が編集対象として明示していない現物 byte 数の pin が確実に赤になる。
**分類**：real
**根拠**：`.claude/commands/dev-wave.md:57` の指定置換を UTF-8 で検算すると **9,507→9,519 bytes、+12 bytes、最長121文字**；`test_check_docs.py:2524` は `== 9_507` を独立 literal で要求する。
**影響**：入口・checker の文言・fixture の3箇所だけ更新すると、予算自体は通っても `test_dev_wave_command_budget_literal_is_exact` が失敗する。
**推奨**：author (2) の編集対象へ `test_check_docs.py:2524` の **9_519** 更新を追加する；上限9,520と超過例9,521は維持する。

**所見**：「DW-O23 は L2 の1,000 bytesで満杯」という親の理由は、現物の分類と計数の両方に合わない。
**分類**：real
**根拠**：`operations.md:171` の見出しから次の H2 直前まで **1,036 bytes**；`check_docs.py:5260` はこの raw slice を数え、`:863` は「段9」を L1 に分類し、入口`:80` は段9から DW-O23 を無条件参照する。
**影響**：この節に L2 の1,000-byte上限を適用したという予算説明は誤りであり、追記可否の判断根拠を誤る。
**推奨**：DW-O23 非変更は「通知手順を既存 runbook に集約するため」と説明し直す；同節を変更する場合だけ L1 総量で再検算する。

**所見**：文言 pin の閉包に不足は見つからないが、fixture の影響を列挙された数本だけに限定してはならない。
**分類**：refuted
**根拠**：現行文言の有効な pin は入口`:57`、`check_docs.py:467`、`test_check_docs.py:55`；fixture は同ファイル`:62`→`:884`→`:1328` と伝播し、AST 上 `_build_min_repo` の直接呼出し元は273関数ある。
**影響**：fixture 不一致は baseline `:1604`、budget `:2519`、handwritten `:7767`、decoy `:7794`／`:7811`、guard `:9895[stage9-deleted]` を含む広い範囲を赤にする。
**推奨**：全 `test_check_docs.py` を焦点走に残し、実文書検査 `:7754` も確認する；同文の archive 記録は変更しない。

**所見**：README の「新規 reader」と通知文の現在形は、保証対象を明示しないと plan 自身の限定と食い違う。
**分類**：plausible
**根拠**：`s2-plan.md:255` は「新規 reader を…待たせる」、`:313` は同 process の参照追加が gate を通らないとする；通知文`:184` は「main は記載の SHA にあり」とするが、`wave_land_window.py:606` は保存 JSON を読むだけである。
**影響**：前者は非 fresh reader まで止めるように読め、後者は JSON 作成後に main が進んだ場合、送信時点の main について偽になる。
**推奨**：README は「fresh 取得を行う reader」とし、通知文は「この land 結果では main は…」と時点を限定する；固定文変更後は現在の **472／609／610 bytes** の期待値を再計算する。

## consumer と焦点走の閉包

**所見**：焦点走から実 repo 読取 node が欠けるという疑いは反証されるが、その実走確認を file 選択だけで済ませてはならない。
**分類**：refuted
**根拠**：`s2-plan.md:296` は serialization 全体を含む；`test_real_repo_serialization.py:2313` は実 ROOT の repo-tree guard を動かし、`:99` で分類対象に含まれ、`conftest.py:2222` は setup/call/teardown を lock で覆う。
**影響**：新設 tmp-only node だけの初回焦点走で止めると、`core.md:97` の実 repo テスト実走義務を満たした証拠が残らない。
**推奨**：`test_protocol_builder_repo_tree_guard_is_wired_to_real_root` の非 skip 結果を段7前に明示する；private symbol の外部 Python consumer は再検索でも serialization だけで、追加 file は不要。

**所見**：consumer の6 file集合は閉じているが、checker の参照関係について plan に事実誤認がある。
**分類**：real
**根拠**：`s2-plan.md:292` は「`tools/check_docs.py` 自体にも `wave_land_window` の参照」とするが、同 literal の検索は該当なし；実際は `check_docs.py:464` の項9 pin を介した関係である。
**影響**：nit。ただし直接 import と CLI／配置／文書 consumer を混同すると、将来の焦点走選択の根拠が崩れる。
**推奨**：4 test file は window・land・wait・resume と列挙し、resume は配置 consumer、checker test は文書 pin consumer と記す。

**所見**：serialization 全体の所要未測定は正しいが、既存 duration ledger を全体時間と読み替えてはならない。
**分類**：real
**根拠**：`acceptance_duration_ledger.json:14601` は既存優先順 test を31秒、`:14602` は別 node を48秒と記録する；同 file の記録は42 node・合計117.354秒だが、現物には68個の test 関数がある。
**影響**：117.354秒は現 checkout 全体の wall timeでも受入5分内の保証でもなく、新設テストの「数秒」だけでは受入への影響を判定できない。
**推奨**：既存焦点走・受入で setup/call/teardown と wall time を記録し、過去 ledger は参考値と明記する；deadline 延長や並行度制限へ逃がさない。

## scope の逸脱

**所見**：採用 gate の保証は、裁定の「待機 writer がいる間」という条件より狭い。
**分類**：real
**根拠**：`rulings-verbatim.md:9` は「待機 writer がいる間は新規 reader を待たせる」；`s2-plan.md:22` は保証開始を「writer が gate EX を取得した後」と限定し、`conftest.py:1267` は非 blocking polling で待つ。
**影響**：reader が gate SH を連続取得する間に writer が gate EX を取れず、飢餓を gate 側へ移す実行順序は排除されない；N1 は gate 獲得後から観測するためこれを検出しない。
**推奨**：plan v2 で裁定との未充足部分を明示し、N1 成功を全面的な writer 飢餓解消の完了判定にしない；別機構の追加は下の裁定パッケージへ分離する。

**所見**：編集面は分離できるが、Markdown を author 2本の所有に含める割当は現行実装子契約と衝突する。
**分類**：real
**根拠**：`s2-plan.md:319` は (1) に tests README、(2) に runbook・入口を割り当てる一方、`.claude/commands/dev-wave.md:36` は「実装子はコード・テストだけを編集し、docs 編集・commit をしない」とする。
**影響**：そのまま dispatch すると、局所修正の内容に問題がなくても作業主体の境界違反になる。
**推奨**：author (1)＝conftest・serialization、author (2)＝window・window test・check_docs・test_check_docs、親＝README・runbook・入口と明記し、文言 pin は同じ統合変更で揃える。

## 親 brief 自身の点検

**所見**：「acceptance_shards にロック実装は無い」は成立するが、「shard affinity のみ」は現物の役割を過小記述している。
**分類**：real
**根拠**：`acceptance_shards.py:79` は cross-host 衝突辺を定義し、`:838`／`:856` は lock interval の検証・記録を実装する；flock 取得・解放の実装は検索で見つからない。
**影響**：nit。変更不要という結論は維持できるが、lock の観測 consumer まで存在しないと誤解させる。
**推奨**：brief を「取得実装は conftest、shards は affinity と取得区間の観測を担当」に訂正し、同 file は変更しない。

**所見**：別 pid の READ holder という F976 の観測は、飢餓が process 間だけで起きる証明にはならない。
**分類**：real
**根拠**：射影の F976 再発記録は READ 2本の pid を示すだけで、`conftest.py:1341` は互換性待ちで `condition.wait()` を呼び、`:1308` は他 holder が read だけなら新 reader を許す。
**影響**：同 process の writer 待機中に reader が追加される経路は残り、brief P1 の「process 内優先は不要」を一般契約にすると取り逃す。
**推奨**：P1 を「kernel flock 待機区間では RLock が新規進入を止める」に限定し、単 thread worker という対象条件と一般的な multithread 保証を分ける。

**所見**：brief の主要 pin 行番号は合うが、ロック変更範囲と helper の案内は不足している。
**分類**：real
**根拠**：`s1-brief.md:6` は1250〜1410行を挙げるが、plan の state 追加は `conftest.py:1047`、安全 open は`:1215`、取得全体は`:1410`以降；helper は serialization の先頭200行でなく`:545`と`:798`にある。
**影響**：案内範囲だけ読む author は state・安全検査・共通 deadline・subprocess 回収の契約を取り逃す。
**推奨**：plan v2 の必読範囲を現物位置へ更新する；checker`:467`・fixture`:55`・入口`:57` の位置は維持してよい。

## 裁定パッケージ候補

**所見**：gate EX 獲得後だけの優先を今回の達成条件とするか、待機開始からの優先を要求するかは明示的な裁定が必要である。
**分類**：real
**根拠**：`rulings-verbatim.md:9` の待機 writer 条件と、`s2-plan.md:311` の「厳密な契約は満たすと断言できない」が一致していない。
**影響**：前者を要求するなら現在の設計・負例では受理根拠が足りず、後者を採るなら既裁定の保証範囲を狭めることになる。
**推奨**：待機登録など別の公平性機構が必要な案は scope 外としてここに留め、追加 gate・台帳・deadline 延長・同時実行数制限を今回の must-fix に混ぜない。

## 総括

**所見**：plan v1 は、文書 byte pin の更新漏れと writer 優先の保証差を解消しないまま実装完了条件に使えない。
**分類**：real
**根拠**：`test_check_docs.py:2524` の9,507固定値、`s2-plan.md:100` の約1秒負例、`:22` の優先保証境界が主要な未解決点である。
**影響**：確実な文書テスト赤に加え、高負荷による偽の変異検出と、裁定未充足のままの受理が起こりうる。
**推奨**：plan v2 で byte pin・負例の条件独立性・actor 同期・所有分担を修正し、優先保証の範囲を裁定へ返す；本レビューは静的予測であり、テスト成功や変異 KILLED の実測報告ではない。
