## consumer の全列挙

以下、パスはrepo root相対。`brief`と`plan`は射影された`s1-brief.md`と`s2-plan.md`を指す。全所見は静的検査によるもので、pytest・変異実行・ファイル変更は行っていない。

**所見**：floor側の直接consumerに取り残しは見つからないが、planの参照一覧には材料レポートtestのresolver直呼び1件が欠けている。
**分類**：real
**根拠**：`orchestrator/ tools/ hooks/`の横断検索では、`_floor_cell`・sentinel・regexの実consumerは`p3_b4_floor_artifact_issuer.py:1502,1503,1505`、公開resolverのproduction consumerは`p3_b4_material_report.py:215`のみ；test呼出しはfloor issuer test`:689,697,723,767,781,1327`とmaterial report test`:1009,1065`で、後者`:1065`の`test_present_floor_projects_required_verbatim_non_guarantees`がplanの一覧にない。
**影響**：共通fixture更新とfile単位の焦点走には含まれるため、実行上の取り残しではない。
**推奨**：plan v2のconsumer一覧に`:1065`を追加する。`tools/`・`hooks/`に対象識別子の直接参照は無かった旨も記録する。

**所見**：admission側の直接・間接consumerは概ね焦点集合に含まれるが、path literalだけの参照を実行consumerと区別して列挙すべきである。
**分類**：real
**根拠**：`p3_b4_admission_record.py:801`→§5検査、`p3_b4_closed_critic.py:1268,1931`・`p3_b4_launcher.py:381`→verifier；bytes参照はclosed critic`:646`・raw producer`:995`。間接2段はclosed critic→launcher`:607,617`・raw producer`:33`・base loop`:2102`、launcher→raw producer`:34`・`wal.py:1206`・base/sort/trigger各loop、material report→raw producer test`:30`・producer auth experiment`:590,605`。一覧外のliteral参照は`test_campaign_lock_codec.py:63`、`test_t671_source_binding.py:83`、`test_artifact_admission.py:327,565`。
**影響**：追加で見つかったliteral参照はpath変更を伴わない本変更ではnit；admission・closed critic・launcher・raw producer・3 loop・proposal binding・producer auth experimentの実行経路はplanの再走集合に入っている。
**推奨**：追加3 test fileを「参照あり、今回の焦点追加不要」と明記する。`tools/`・`hooks/`から上記moduleへの直接参照も今回の検索では見つからなかった。

## 既存 test の壊れ方

**所見**：更新対象の最小floor fixtureはplanに揃っているが、共通fixtureを使うtestの列挙が不完全である。
**分類**：real
**根拠**：`test_p3_b4_floor_artifact_issuer.py:188`は「§5見出し＋floor 1行、終端なし」で、利用箇所は`:686,695,719,762,1324`；`:778`は見出しなしの重複2行。`test_p3_b4_material_report.py:137,1004,1113`は単一行書込みで、`:137`のwrapper利用は`:867`のm9と`:1064`のnon-guarantees正例。別系統の`test_p3_b4_analysis_path.py:574`にも`b"## 5. values\n"`だけの最小文書がある。
**影響**：floor fixture未更新なら正例はrow errorで停止し、m7は期待する`path_error`へ届かない；analysis pathの最小文書は§5.1.1 closure用でfloor/admissionを呼ばず、今回の変更では壊れない。
**推奨**：m9とnon-guarantees正例を明示し、analysis path fixtureは「検出したが変更不要」とする。最小文書を一律完全表へ変えない。

**所見**：m05/m06はfixtureが壊れたままでも成功扱いになりうるため、「fixture変更のみ」では対象検査への到達を確認できない。
**分類**：real
**根拠**：`test_p3_b4_floor_artifact_issuer.py:733`の3 modeは`:766`で`pytest.raises(issuer.B4FloorArtifactError)`だけを要求する；一方material report m7は`:1140`で`cause.code == "path_error"`まで確認する。
**影響**：missing/hash/schemaの拒否を試すはずのtestが、手前の§5 row errorで緑になり、artifact検証の退行を見逃す。
**推奨**：plan v2でm05/m06に各modeの期待error codeを固定し、`preregistration_floor_row_error`では通らないようにする。

**所見**：cross-test importがcollection・xdist・受入分割だけを理由に破綻するという懸念は、現物からは支持されない。
**分類**：refuted
**根拠**：`test_p3_b4_material_report.py:964`にはpackage-qualifiedな`_aggregate_public_sources` importが既存；`test_p3_b4_admission_record.py:26`の定数生成と`:81`のbuilderは実repo文書を読まない。`tools/run_tests.py:563`は`python -m pytest`を構築し、`tools/acceptance_shards.py:3`は「deselect前の全collection」から割付ける。
**影響**：対象testが別shardでもhelper moduleのimportは可能で、現物上の障害は確認できない；実走保証ではない。
**推奨**：`from orchestrator.tests.test_p3_b4_admission_record import _section5_document`の関数内importに表記を統一し、単一file走と受入走で確認する。専用helper module新設は不要。

## 切り出しの振る舞い不変性

**所見**：planの移動順は現実装と一致するが、「既存testで例外の送出順序まで保証できる」という解釈は成立しない。
**分類**：real
**根拠**：`p3_b4_admission_record.py:665`のlabel集合不一致と`:686`のsentinel拒否は、ともに`B4AdmissionRecordError(_SECTION5_SOURCE_CELL_CONTRACT_FAILED)`。`test_p3_b4_admission_record.py:405`以降は単独不正とexact messageを検査し、集合不一致＋sentinelを併発させた順序観測はない。
**影響**：両検査を逆転しても同じmessage bytesで拒否するため、既存testでは順序変化を識別できない。
**推奨**：plan v2では「処理順は差分レビューで維持、既存testは観測可能な例外契約を確認」と分ける。異なるsignatureが出るsentinel＋model mismatchの複合例なら、外部挙動として順序を検査できる。

**所見**：raw／normalized二系列を保つ計画に明白な破綻はないが、二重grammar検査の順序自体をtestで証明することはできない。
**分類**：refuted
**根拠**：現実装は`:658`でstrip、`:660`でNFKC、`:663,664`で両系列を保存し、`:687,688`でraw→normalizedの順にgrammar検査する。plan`:42,53`は同じ順序を残す。既存test`:667`はNBSPと`ﬀ`を含むraw expectationを拒否させ、raw系列をnormalizedへ置換する退行を検出する。
**影響**：raw検査欠落は受理集合を広げるが、両検査の順序交換は同じ失敗signatureのため観測できない；raw grammarに通る文字列はASCIIなので、その後のNFKCでも不変である。
**推奨**：二重検査は指定どおり保持する一方、順序交換・normalized側だけの検査削除を「必ずKILLEDになる変異」と扱わない。

## P4 の検算

**所見**：admission bytes変更によって、コミット済みadmission recordや固定closure goldenの再発行が必要になるという懸念は、確認範囲では反証された。
**分類**：refuted
**根拠**：`p3_b4_closed_critic.py:646,668,681`はadmission bytesを3 driverのhashへ含めるが、`git ls-files`とworking-tree検索で指定recordは0件；実文書`:166`はexpectation=`未記入`。`test_p3_b4_closed_critic.py:2027`は`hashlib.sha256(path.read_bytes())`で期待値を生成し、admission test`:28`のhashはsynthetic値である。
**影響**：live closureは変わるが、確認した現行登録対象・test goldenの再発行対象はない；外部や未追跡の過去receiptの不存在までは示さない。
**推奨**：P4の結論は「確認した登録対象について失効処理不要」に限定する。古いreceiptを新hashへ書き換えない。

**所見**：closureの発火箇所と材料レポートの固定goldenを混同すると、不要なgolden更新や不変性の過大主張につながる。
**分類**：real
**根拠**：live照合はclosed critic`:918,1283,1936`とlauncher`:386`で発火し、対応testはclosed critic`:1235,1294,1342,1393`とlauncher`:593,633`。raw producer`:1019`もclosureを再構成する。一方material reportの固定golden test`:732`は`:795`で`_load_and_evaluate`をstub化している。
**影響**：固定goldenが保護するのはrendering bytesであり、実文書→resolver→評価器の接続ではない。
**推奨**：固定goldenは更新せず維持し、resolverの実文書正例・m9・aggregate・CLIの結果を別々の証拠として記録する。

## 実 repo を読む正例 test

**所見**：既存の実文書読取先例があることだけでは、新規nodeの分類登録を省略できない。
**分類**：real
**根拠**：`test_p3_b4_analysis_prereg_consumer.py:23,59`は実文書を直接読むが、同file名は今回調べた分類集合にない；一方`conftest.py:260`は親working treeへ触るnodeの分類正本を宣言し、`:626`でparent-onlyを`RealRepoAccess("read", None)`へ対応させる。独立goldenは`test_real_repo_serialization.py:52,212`にある。
**影響**：先例の未登録を踏襲すると、新規nodeが既存の資源分類から漏れる。
**推奨**：planの4集合更新を実施する。既存analysis consumerの分類漏れまで本waveのmust-fixへ広げない。

**所見**：実repo文書に対する恒久的な`None`期待は、将来floorが正式登録された時点で正しい実装を失敗させる。
**分類**：plausible
**根拠**：plan`:199`はworktreeの実文書から無条件に`None`を期待するが、現物の不在根拠は文書`:162`の`未記入`という可変状態である。resolver`:1513`は有効pinならartifactを読む。
**影響**：別waveの§5更新を取り込むと、コード退行なしで正例が失敗し、artifact読取量も変わりうる。
**推奨**：このtestを「現在の未登録状態の回帰」と明記し、floor登録waveで更新する対象として残す。恒久的な不在契約と説明しない。5分上限への追加負荷は現状小さいと読めるが、達成判定は受入実測に留保する。

## 変異 matrix の帰属

**所見**：M4は2か所を同時に壊すため、KILLEDでもstrip処理の独立した有効性を証明しない。
**分類**：real
**根拠**：plan`:254`は「raw valueをstripせず保存」と「それをsentinel比較する」を同一patchに含める；現実装`:658,664`ではrawもstrip済みである。
**影響**：sentinel testの失敗を、共有helperのraw保存契約とresolverの比較契約のどちらへ帰属すべきか分離できない。
**推奨**：raw保存だけの変異をpadded pin／helper二系列testで検査し、比較対象だけの変異は等価性を別判定する。複合M4を残す場合は「旧挙動再現」であり単一防御の証明ではないと記す。

**所見**：killer帰属はfloor側だけに閉じず、共有helperの変異には既存admission testが先に反応する。
**分類**：plausible
**根拠**：M1→新outside-pin正例、M2→新unrecorded-owner負例、M3→新unknown-label負例、M4→padded sentinel、M5→既存admission`:667`、M6→既存admission`:731`のfence testと新decoy正例、M7→既存admission`:762`のcomment testと新decoy正例、M8→新raw-pin test、M9→新exact-label test、という静的対応になる。
**影響**：suite全体の失敗だけを採ると、新floor testが欠落していても共有helperの既存testだけでKILLEDと報告できる；M3は指定されたadmission`:405〜858`だけでは検出根拠を確認できない。
**推奨**：matrixに「指定killer単独」と「全焦点」の結果を分けて記録する。M1はbytes→tupleという新signatureに適合した実行可能patchとし、型エラーをkillerに数えない。

**所見**：M0は含まれており、機能上等価な変異をすべてKILLEDへ揃える目標は置くべきでない。
**分類**：refuted
**根拠**：plan`:250,263`はM0をcomment/docstring変更・SURVIVED期待と明記する；admission`:687,688`のgrammar順序交換やnormalized側検査だけの削除も、現行ASCII grammarでは機能上等価になりうる。
**影響**：等価変異のSURVIVEDを欠陥と数えると、成果物挙動を変えないtestやgateを追加する方向へ逸れる。
**推奨**：M0の機能等価とclosure bytes非等価を区別し、追加変異にも同じ区別を適用する。

## 親 brief 自身の点検

**所見**：briefの「受理集合の変化は2種類だけ」と「他欄の値は見ない」は、指定する共有解析と矛盾する。
**分類**：real
**根拠**：brief`:18,26`に対し、admission`:647,660,665`は固定行数・全値セルの正規化拒否・全label集合を検査する。また旧floor読取`:1473`は全文で2行あれば拒否するが、新経路は真正§5＋外側decoyを受理する。
**影響**：縮小は構造不正・他欄のdefault-ignorable等にも及び、拡大もstripだけでなく外側重複の無視を含む。
**推奨**：briefとplan v2の不変条件を、「全セルの構造・正規化を共有し、非空／sentinel述語は責任者だけに適用」「真正§5外の同prefixは無視」と書き直す。

**所見**：「責任者未指名を拒否する」という一般的説明は、維持するadmission述語の保証より広い。
**分類**：real
**根拠**：admission`:668〜686`はD2079形の追加受理に失敗しても通常の非sentinel値を受理する；既存builder`:89`は責任者に`fixture-value-10`を置き、admission正例`:405`がそれを受理する。module docstring`:29`もmeaningを検査しないと宣言する。
**影響**：本変更で拒否できるのは行欠落や予約sentinel等であり、人間が実際に指名済みかという意味的保証は得られない。
**推奨**：完了説明を「責任者セルを既存admission述語へ接続」に限定する。意味検証は追加しない。

**所見**：P6の作業量見積りは不足しているが、authorを分割すべきという実測根拠はない。
**分類**：plausible
**根拠**：brief`:23`は「2 module＋3 test file」とするが、plan`:201〜206`自身が分類2fileを追加し、material report`:6`にはP2と矛盾する`verbatim sentinel`が残る。
**影響**：変更file数と焦点・変異・受入の所要を過小評価すると、author終了時に検証や文書修正が残る。
**推奨**：author 1本は維持可能だが、最低3 module＋5 test関連file＋成果物文書としてscopeを数え直す。所要・予算の断定は避ける。

**所見**：floor labelのindex pinと文書更新計画には、不要な結合と更新漏れがある。
**分類**：real
**根拠**：brief`:27`は`_SECTION5_LABELS[4]`を要求する一方、parser`:665`は集合として照合する。plan`:166`はissuerのdocstringだけを直し、material report`:6`の`verbatim sentinel`を残す。事前登録§7.2（`:797〜868`）にはfloor読取経路の説明はなく、現行接続説明は`:1064〜1070,1303〜1307`にある。
**影響**：labelの並べ替えだけでtestが壊れるのはnit；material reportの説明は新しい受理集合と食い違う。
**推奨**：独立literalとの一致＋admission label集合への所属をpinする。material report docstringを更新対象へ追加する。§7.2の修正は不要；`docs/phase3.md:19`以下の完了記録は親の統合対象として明示し、事前登録本文の編集へ広げない。

## 裁定パッケージ候補

**所見**：新しいgate・台帳・汎用validatorを必要とする、成果物への具体的影響を伴う候補は確認できなかった。
**分類**：refuted
**根拠**：既存の§5 parser・セル述語・real-repo分類で本件の接続を実装できる；D2079決定2は責任者への意味検証追加を明示的に退けている。
**影響**：追加一般化は本件で必要なfloor参照先・受理集合の修正を超える。
**推奨**：裁定パッケージ候補は追加しない。既存real-repo分類の全件監査も本waveのmust-fixへ混ぜない。

## 総括

**所見**：plan v2では、fixtureの拒否理由固定・M4の帰属分離・briefの保証範囲訂正・material report docstringの更新を優先すべきである。
**分類**：real
**根拠**：`test_p3_b4_floor_artifact_issuer.py:766`、plan`:254`、brief`:18,26`、`p3_b4_material_report.py:6`で、それぞれ検出力・帰属・説明の不足を確認した。
**影響**：放置すると、誤った理由で緑になるtestや、実際より広い保証を主張する完了報告が残る。
**推奨**：上記を修正してからauthorへ渡す。consumerの致命的取り残し、cross-test importの必然的破綻、確認済み登録対象の再発行義務は見つからなかった。実走結果は未判定。
