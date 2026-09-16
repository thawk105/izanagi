## 受理集合と検出力

以下、`T`＝`orchestrator/tests/test_s8b_oracle_driver.py`、`M`＝`orchestrator/campaign/t080_freeze_migration.py`、`H`＝`orchestrator/campaign/s8b_holdout_freeze.py`、`D`＝`orchestrator/campaign/s8b_oracle_driver.py`、`C`＝`orchestrator/tests/conftest.py`。`B`＝指定の `s1-brief.md`、`P`＝指定の `s2-plan.md`、`W`＝指定の前 wave `stage4-ruling.md`。分類は静的検算の確度であり、変異の実走結果ではない。

**所見**：session 中の実 repo 変更まで含めると、proto 化は現行の拒否経路を失う。
**分類**：real
**根拠**：T:829「`visible_output = _git_visible_output_paths(source_root)`」、T:836「`not source.is_file() or source.is_symlink()`」、T:868「untracked の増減を隠す process 内 memo は置かない」に対し、P:305 は最初の snapshot への固定を認める。
**影響**：key A 構築後、非除外 output に三軸 conjunction を追加してから未構築 key B を要求すると、現行 B は発行時に拒否するが、新 B は追加前の proto から発行できる；tracked regular の symlink・directory 化にも同じ差がある。
**推奨**：P:314 の無条件な「受理集合を維持」を撤回し、「構築期間を通じて同一 source である場合」に限定する；時間方向の再観測を捨てる判断は明示的な裁定事項にする。

**所見**：無害な untracked 増減の固定も、単なる実行順の決定性改善だけでは説明できない。
**分類**：real
**根拠**：M:1741–1746 の `_live_scan_sha256` は「`holdouts`」「`positive_control`」を含める一方、H:1000–1003 は「単一軸だけ一致する新規 campaign.lock 等」で件数が経時変動すると説明する。
**影響**：拒否の有無が同じでも、scan 観測や receipt の reconstruction hash が変わりうる；三軸 conjunction の増減なら検出力そのものが変わる。
**推奨**：「判定不変」「観測値不変」「session 内の入力固定」を分け、I1 の比較対象には可視集合だけでなく、その bytes と runtime 世代も含める。

**所見**：「実 repo の ccbench HEAD が pin と不一致なら現行 fixture が必ず拒否する」という前提は成立しない。
**分類**：refuted
**根拠**：T:1450 は clone 後に「`checkout ... known["ccbench_pin"]`」を実行する；M:2409–2413 は `HELD` 時に current-pin 検査を保留し、T:1875–1881 は `HELD=False` の枝で checkout-only 不一致を検出する。
**影響**：実 repo HEAD の単なる移動を、新方式だけが隠す既存拒否の例にはできない；pin object の欠損・fixture 内 gitlink 不一致とは区別が必要。
**推奨**：pin の反例は「貸出元 HEAD」「必要 object の取得可否」「派生 fixture の HEAD/gitlink」「保留解除時の検査」に分解する。

**所見**：runtime sibling のローカルコピーは直ちに stub にはならないが、現行と同じ時点の検査実装を使う保証は失われる。
**分類**：real
**根拠**：T:1465–1467 は key ごとに現行 source をコピーし、T:1508–1511 はその bytes を実行する；T:1541–1557 の確認は loader 型・`__file__`・ROOT であり、元の現行 source との bytes 比較ではない。
**影響**：安定した source なら判定材料の出所は同じだが、途中変更や sibling 内容の取り違えでは古い検査実装が全 key に伝播し、既存の所在 assert は通りうる。
**推奨**：P:51 の任意案を確定し、runtime 相対パス集合と bytes を proto の入力契約・比較テストへ含める；I4 は「実装を実行すること」と「どの世代の実装か」を別記する。

## I1 の定義と検証設計

**所見**：P の I1 は条件付き同値性であり、B の無条件な「現行 build と bytes 同一」をそのまま証明するものではない。
**分類**：real
**根拠**：B:111 は working tree・HEAD tree・receipt の一致を要求するが、P:55 は「同じ source snapshot、key、Git 設定・commit metadata」、P:306 は index stat・reflog・内部 timestamp を除外する；M:1967 は basis commit OID を receipt に格納する。
**影響**：basis tree 一致だけでは receipt bytes・発行後 HEAD tree 一致は導けず、Git 内部 bytes や未統制の別走との一致も対象外になる。
**推奨**：I1 を「同一入力条件下の working tree の path/type/bytes/mode/link target、basis tree、receipt raw/document、発行後 tree の一致」と書き直し、除外項目を同じ箇所に列挙する。

**所見**：「小さいが有効な corpus」は実 production 検査に供給する入力になりうるが、現 plan では実現性と F29 の根拠が未完成である。
**分類**：plausible
**根拠**：P:155–172 は corpus の最小集合を未確認とする；T:1409–1412 は実 receipt の basis OID を読み、T:565 は「`git show {basis}:{relative}`」を要求する；さらに `freeze_verification_hold.py:14` は「`HELD: bool = True`」。
**影響**：historical bytes を並べるだけでは元の basis OID を解決できず、発行が通っても保留中の artifact bytes・pin 検査まで成功した証拠にはならない。
**推奨**：必要な receipt、historical object の供給方法、正規 artifact bytes、独立した ccbench object store を具体化する；保留項目は既存の解除枝と区別し、「production が通ったので全 hash/pin を実証した」と書かない。

**所見**：Git launcher は時刻だけを注入する委譲器なら成立しうるが、合成 receipt や成功応答を返す test double にすると同値性検証を壊す。
**分類**：plausible
**根拠**：T:370 と T:1478–1488 は `GIT_*` を除去するが PATH は除去せず、T:383・1596 は `"git"` を呼ぶため、P:168 の launcher は到達可能である。
**影響**：launcher が引数・stdout・終了コード・Git object を代替すると、自己 hash・参照・pin の成立条件が比較用実装へ移る。
**推奨**：解決済みの実 Git 絶対パスへ全引数をそのまま渡し、commit 時刻以外を変更しない契約にする；basis OID・receipt raw の一致を実 Git の生成物で確認し、実行前に実現済みとは扱わない。

**所見**：小型 Git 同値性＋既存 e2e 11 node＋変異 matrix だけでは、実 corpus の receipt bytes 同一という強い I1 は未証明のまま残る。
**分類**：real
**根拠**：T:1739–1746 は recorded 値、T:1774–1785 は当該 fixture の Git から導いた期待値を検査し、旧経路の receipt とは比較しない；P:170 の旧・新 receipt raw 比較を外すと、この比較面がなくなる。
**影響**：旧・新がともに有効で既存 assert を満たしても、scan 観測・receipt field・コピー集合の差は残りうる。
**推奨**：代案を採るなら「派生機構の同値性と既存受理条件の維持」までの根拠と記す；B の receipt bytes 同一要求を維持するなら、同一入力・独立した旧順序参照・実発行による比較がなお必要。

## 順序交換の論証

**所見**：descriptor を submodule add 後へ移すこと自体が tree や never-issued 判定を変えるという懸念は、同一入力条件では反証される。
**分類**：refuted
**根拠**：T:1438–1440 の変更先は descriptor、T:1443–1450 の操作先は ccbench、T:1451 の最終「`add -A`」は両操作後；M:2066–2073 の never-issued は receipt path の履歴・存在を調べる。
**影響**：nit；ただし descriptor は M:109 の holdout `"/design_source/sha256"` 対象であり、「receipt に効かない file」ではない。
**推奨**：順序交換の説明に「known の path/sha256 closure にはなく、holdout closure に入る」「旧・新とも同じ追記を最終 add 前に行う」を加える；同じ commit metadata なら receipt 全体も同じという条件を維持する。

**所見**：descriptor の変更による差を `migration_basis_commit` だけへ限定してはならない。
**分類**：real
**根拠**：M:1652 は descriptor の basis blob hash を `source_repins` に格納し、M:1721–1734 はその hash を projected holdout と reconstruction hash に反映し、M:1631–1635 は repin report にも含める。
**影響**：追記漏れを basis OID 差だけの非決定性として除外すると、closure・reconstruction の実質的な差を見逃す。
**推奨**：順序交換と追記の有無を別に扱い、distinct case では descriptor raw bytes と関連 receipt field を比較対象から除外しない。

## proto の完成 marker と信頼の根

**所見**：plan の「破損時に再構築する」負例と、完成情報を存在確認するだけの共有設計には未接続部分がある。
**分類**：real
**根拠**：P:81 は完成情報が「不在なら」再構築とする一方、P:176 は JSON 破損・root/`.git`/pointer 欠損を対象とする；現行 T:923–940 は `marker.is_file()` 後に JSON を読み、その root を返すだけである。
**影響**：現行規約の単純移植では malformed JSON は再構築されず例外になり、marker 付きの不完全な root は完成品として返されうる。
**推奨**：plan v2 に完成情報の読取り結果ごとの動作を明記する；予定済みの構造欠損負例について、再構築する条件と伝播させる I/O エラーを対応付ける。

**所見**：marker は構築完了の証拠であり、その後の全内容の健全性を保証する証拠ではない。
**分類**：real
**根拠**：P:82 は「builder の正常 return 後」に公開し、P:178 は後発 bit corruption の全件 hash gate を明示的に対象外とする；T:1000 のコピーも内容の再認証を行わない。
**影響**：marker 後の通常 file の改変が production の束縛対象外なら、変更された proto を全 key が黙って使いうる；「破損をすべて再構築する」とは言えない。
**推奨**：保証を「成功後公開・予定した構造欠損の処理・独立コピー」に限定する；任意の後発内容破損の全面検出を must-fix として追加しない。

**所見**：異なる ROOT または run_id の proto が通常経路で同じ共有先になるという懸念は、現 identity からは支持されない。
**分類**：refuted
**根拠**：T:949–953 は「`json.dumps([str(ROOT), run_id])`」の digest を共有 directory 名に使い、P:304 はその内側に proto を置くとする。
**影響**：nit；同じ identity の再利用や同一 process 内で ROOT を monkeypatch する比較テストは、別の cache 分離問題として残る。
**推奨**：新しい共有 identity は不要；小型テストでは key memo と proto memo の両方を reset し、ROOT を差し替えた入力が既存 memo に吸われないようにする。

## 変異 matrix の帰属

以下の KILLED／SURVIVED は机上予測であり、13件とも未実走である。

**所見**：① output regular 1件脱落は、独立した参照集合があれば小型同値性 node で殺せるが、同じコピー helper を双方が使うだけでは生存しうる。
**分類**：plausible
**根拠**：P:190 は `test_t080_proto_derivation_matches_direct_small_source` を指定し、T:1688–1707 の現行可視集合 test は `expected_copied` を別に構成する。
**影響**：旧・新の両経路が同じ欠落を含むと bytes 一致が成立し、SURVIVED になる。
**推奨**：脱落させる path を固定し、参照側の明示集合・bytes が当該 path を含むことを確認する。

**所見**：② descriptor 追記削除に対する「既存 T:1735 が killer」という帰属には根拠がない。
**分類**：real
**根拠**：T:1736–1737 は distinct を要求するが、T:1774–1785 は生成された fixture 自身から hash を導き、追記 suffix の存在や通常 basis との差を assert していない。
**影響**：追記がなくても生成物と独立 Git 導出値は一致し、この node は生存しうる。
**推奨**：killer は旧順序参照との distinct 比較に限定し、入力 descriptor＋指定 suffix の bytes を独立期待値にする。

**所見**：③ 派生コピーから `.git` を除く変異は、実 Git を通る小型同値性 node なら KILLED が見込める。
**分類**：plausible
**根拠**：P:192 の変異に対し、T:1451–1453 は実 Git の add・commit・履歴検査を要求する一方、T:1072–1082 の小型 cache builder は Git を使わない。
**影響**：cache builder の mock のみを通す node では脱落を検出できない；上位 repo を誤参照すると別の理由で失敗する可能性もある。
**推奨**：実 Git 同値性 node を単独実行対象にし、派生 root が独立 repo であることを tree 比較前に確認する。

**所見**：④ submodule pointer の proto 絶対 path 固定は、pin 読取りだけでは生存しうる。
**分類**：plausible
**根拠**：P:193 の killer は relocation test だが、P:68–70 の pointer は現在相対参照であり、絶対参照でも proto が生存中なら同じ object を読める。
**影響**：pin が一致したまま別 key と submodule の Git 状態を共有し、後の変異が漏れる。
**推奨**：pointer/config 比較に加え、派生コピーを移動し、元 proto を利用不能にしても Git が動くこと、片方の操作が他方を変えないことを確認する。

**所見**：⑤ proto lock 削除の検出には、T:1121 型をそのまま転記するだけでは不足する。
**分類**：real
**根拠**：T:1133 は「`operation == fcntl.LOCK_EX`」だけを観測するが、P:88 は最初に shared lock を取り、P:84 は別途 key lock も取る。
**影響**：正しい実装が SH で待つため通知されない、または key lock の通知を proto lock の証拠と誤認する可能性がある。
**推奨**：proto lock の fd/path を識別し、最初の SH 待機も観測する；異なる key、親の lock 保持、子の到達通知、解除後の構築回数を別々に assert する。

**所見**：⑥ 完了前公開は、builder 例外後の再構築だけでは必ずしも殺せない。
**分類**：plausible
**根拠**：P:195 は failure-rebuild node を指定し、P:176 は例外後の完成情報不在を確認する；P:82 の保証はそれより強い「正常 return 後」の公開である。
**影響**：途中公開しても例外処理で marker を消す実装は事後検査を通り、途中の誤公開が SURVIVED になる。
**推奨**：小型 builder を Pipe で正常 return 前に停止し、その時点で完成 marker がないことを親から観測する；失敗後の再要求は追加の確認にする。

**所見**：⑦ 失敗 proto の process memo 格納は、同じ process 内で再要求しなければ検出できない。
**分類**：plausible
**根拠**：T:1016–1018 の fork helper は「process memo を共有しない子」であり、現行 T:992–997 は builder 正常 return 後に memo へ格納する。
**影響**：失敗と再要求を別の fork に置くと失敗 memo が消え、変異が生存する。
**推奨**：同じ process で一度失敗させ、memo 未登録、次回 builder 再実行、完全な payload、以後の成功 cache hit を確認する；Pipe は必須ではない。

**所見**：⑧ key 失敗時の complete 公開は、copy 失敗と finish 失敗を区別しないと対象を取り逃がす。
**分類**：plausible
**根拠**：P:197 は「key 構築失敗の負例」を指定するが、P:176 の具体記述は「copy の途中例外」；T:929–938 の公開は builder 全体の return 後にある。
**影響**：コピー負例だけでは、commit・発行中の失敗を完成扱いする変異を踏まない。
**推奨**：copy 後の finish 失敗も小型 builder で発生させ、complete 不在と次回再構築を検査する。

**所見**：⑨ `symlinks=True` 削除は、proto→key の実コピーを通る symlink がなければ生存する。
**分類**：plausible
**根拠**：T:822 と T:834–840 は output symlink をコピー対象から除き、T:1096–1097 の既存 assert は base→test の link を検査する。
**影響**：output だけの source や wrapper を mock した独立性 test では、新しい派生コピーの dereference を検出できない。
**推奨**：小型 proto の非 output 部分に symlink を置き、実 proto→key コピー後の種類・target を確認する。

**所見**：⑩ distinct field の cache identity 脱落は、既存 T:1186 が semantic killer になりうる。
**分類**：plausible
**根拠**：T:1191 は `distinct_basis_blob=True` を別要求し、T:1199 は返却 arguments、T:1200 は builder 5回を assert する。
**影響**：通常 key と同一 base を返す変異は返却値か回数で赤になるが、単なる tuple 長不足の IndexError は分離性の検証にならない。
**推奨**：変異位置を「cache identity のみから distinct を落とす」と具体化し、他の引数処理を壊しただけの赤と区別する。

**所見**：⑪ 最初の close で削除する変異は、既存 lifetime test で KILLED が見込める。
**分類**：plausible
**根拠**：T:1208–1212 は first close 後の directory 存在と「`remove.assert_not_called()`」、second close 後の削除1回を要求する。
**影響**：proto 専用 cleanup が既存 parent cleanup と別に追加される場合は、現在の parent 存在確認だけでは取り逃がす。
**推奨**：P:138 のとおり実際の小型 proto payload を置き、first close 後の payload 存在も確認する。

**所見**：⑫ proto 入口の境界検査だけを削る変異は、既存の外側チェックに隠れて SURVIVED になりうる。
**分類**：real
**根拠**：T:1723・1726・1731 は wrapper/helper を呼び、T:976–979 は helper 入口、P:111 は wrapper にも安全確認を置く。
**影響**：外側が先に拒否すると、新 proto builder の境界検査を削っても同じ負例が通る。
**推奨**：境界テスト拡張では新 proto builder 入口を直接呼ぶ case を明記し、書込み前拒否を観測する。

**所見**：⑬ runtime snapshot 省略と historical bytes 置換は、同じ killer が保証される一つの変異ではない。
**分類**：plausible
**根拠**：T:1509 は sibling を実際に読むため欠損は失敗しやすいが、T:1541 の loader 型検査と T:1564 の historical working-tree 比較は、runtime の現行 bytes を確認しない。
**影響**：historical 実装でも同じ receipt を作れる場合、receipt 同値性と既存 e2e がともに通り、検査実装の世代取り違えが生存する。
**推奨**：省略と置換を別 mutant にし、置換側は既知の current runtime bytes と sibling の一致を独立に確認する node へ帰属させる。

## 親 brief 自身の点検

**所見**：正常な active-valid 発行経路の全件 scan は13回であり、brief の5回も plan の12回も誤りである。
**分類**：real
**根拠**：draft は M:1727・1731→H:1029・1985 の3回、明示 validate は M:2022–2023 の3回、finalize は M:2035・2048 の4回、明示 verify は M:2343→2201 の1回；gate は D:606→169 に加え、D:467→299→M:2490 でも scan するため2回。
**影響**：発行費用と将来の変異帰属が1回以上ずれ、「5×5.3秒」「12×5.3秒」の推定も成立しない。
**推奨**：B:45・92、P:13・20–31・286・316 を訂正し、正常 active-valid 経路を「3＋3＋4＋1＋2＝13」と記す；途中拒否や別分岐は別に数える。

**所見**：run1 の verify/search 内訳の矛盾は、一次 profile 上の呼出回数が異なることで説明できる。
**分類**：real
**根拠**：B:49–50 は「4.85秒/回、うち5.3秒/回」；`b5-run1.prof` の M:2284 は10回・cumtime 48.5241秒、H:592 は9回・47.6404秒、H:516 は27回・25.6491秒である。
**影響**：異なる分母の平均を包含として足すと費用を誤配分する；run2 も verify 20回・80.9344秒に対し search 全体17回・89.9118秒で、後者には verify 外の呼出しが含まれる。
**推奨**：run1 は「verify 全10回の総和48.524秒、その内部 search 9回の総和47.640秒」と訂正する；run2 は verify 内15 scan と、別経路2 scan を分ける。

**所見**：brief の add 費用・競合差・critical path に関する複数の文は撤回または限定が必要である。
**分類**：real
**根拠**：B:46 の値は `_run_git` 11回合計であり、profile の builder→`_run_git` は run1 9.5305秒、run2 55回47.4813秒；B:53 は base と test node を比較し、B:81 の式は proto 派生コピーを加えている。
**影響**：「add 単独が8%」「差80–100秒が競合」「非競合経路は縮まないだけ」という帰属が、実装効果の評価を誤らせる。
**推奨**：B:52・103 の「add は8%」を撤回し Git 操作全体へ訂正、B:53–54 の差の競合帰属を撤回、B:81 を「初回 key は派生コピー分増える」へ訂正、B:83 の「index 未作成」と B:84・111 の無条件 bytes 一致も訂正する。

**所見**：t080 stub-free e2e が real-repo lock の対象外という記述は現物と一致するが、これは source snapshot 固定の根拠にはならない。
**分類**：real
**根拠**：C:612–659 の access map の元集合に該当 e2e はなく、C:2227 は「`REAL_REPO_ACCESS_BY_NODE.get(node_id)`」、C:1454–1456 は `access is None` なら lock なしで進む。
**影響**：他の実 repo 操作や外部 session と並行して source が変化する可能性を、既存 lock が排除しているとは言えない。
**推奨**：B:134・P:226 の事実記述は残し、P:305 の snapshot 固定を既存機構で保証済みとは記さない。

**所見**：`config.h` の既存脱落を本 wave で直さないこと自体は、proto 化による新しい差ではない。
**分類**：refuted
**根拠**：W:72–76 は tracked source を新規 repo の add が拾わないと説明し、実 `.gitignore:8` は「`/config.h`」；T:1380 で実体をコピーし、T:1451 は新規 repo に `add -A` する。
**影響**：nit；proto の index に同 file を新たに stage しない限り、実体はあっても Git 可視集合に入らない既存挙動が続く。
**推奨**：この wave の比較基準は実 repo HEAD ではなく現行 fixture とする；小型同値性には「source では tracked、destination では ignored」の case を含め、意図せぬ是正を検出する。

## scope 外の層

**所見**：単独 process と共有経路は plan の scope に入っているが、実 builder の既存跨 process test は異なる key の proto 共有まで証明しない。
**分類**：real
**根拠**：P:97・120–121・239 は両経路を対象とする一方、T:1057・1065–1067 の実 builder test は同じ no-issue key を2 process で要求し「`(1, 0)`」を確認する。
**影響**：新 proto が別 key では使われない配線でも、この既存実 builder test と新 wrapper の call count は通りうる。
**推奨**：小型の異 key test が実際の proto 管理・派生コピーを通ることを明記し、実 builder test の証明範囲は「同 key の共有」に限定する；wrapper mock の回数だけで全層実証としない。

**所見**：受入3 shard は3つの層すべてで proto が構築されるという意味ではなく、現行の file 単位配置ではこの file の実行は一つの shard に閉じる。
**分類**：real
**根拠**：`tools/acceptance_shards.py:477–485` は file ごとの shard 集合が1要素であることを要求し、T:949–953 の共有範囲は `[ROOT, run_id]` である。
**影響**：3 shard の受入成功だけから process memo 経路や shard 間共有を実証したとは言えず、「session 1回」の単位も誤解されうる。
**推奨**：単独 memo、同一 xdist run の異 key 共有、受入3 shard の全体回帰を別の証拠として記す；受入では実際に担当した shard と proto 構築回数を対応させる。

## 裁定パッケージ候補

**所見**：session snapshot 固定を受理契約として採るか、key ごとの実 repo 再観測を残すかは、性能改善の実装詳細だけでは決められない。
**分類**：real
**根拠**：T:868 は増減を隠さない設計理由を明記し、P:305 はその時間的同値性が成立しないと認める；指定裁定 D2068 は可視 file の脱落による拒否経路消失を不採用理由にする。
**影響**：snapshot 固定を採れば、初回取得後に出現した欠陥の検出責任がこの fixture から外れる。
**推奨**：裁定には「source 不変を前提として時間的再観測を対象外にする案」と「再観測の責任を維持する案」を提示する；source lock・再検査 gate・全件 hash 台帳の新設は本レビューの must-fix に混ぜない。

## 総括

**所見**：plan v1 は、無条件な受理集合不変、I1 の証明範囲、変異 killer の帰属、scan 回数を訂正するまで、そのまま実装の正しさ根拠にはできない。
**分類**：real
**根拠**：主要な反例は T:829・836・868 の再観測消失、T:1774–1785 の fixture 自身からの期待値導出、T:1133 の EX 限定通知、M:2490 の追加 scan；本段は静的読解と既存 profile 読取りのみで、編集・Git 状態変更・pytest・変異実走は行っていない。
**影響**：未訂正なら、snapshot の変更を受理集合不変と呼び、未証明の receipt 同値性や未実走の KILLED を成果として扱う危険がある。
**推奨**：plan v2 ではまず時間的契約と I1 を確定し、13変異の対象・独立期待値・観測時点を具体化する；正常 active-valid 経路の scan は13回へ訂正する。