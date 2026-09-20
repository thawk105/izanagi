## B-1. 段9改訂は、同じ木で切り替えた旧fix branchを回収しない

判定: **real（must-fix）**

**根拠:** `docs/dev-wave/workers.md:21` はfix時に同じ木でbranchを切り、manifestを再登録する。`tools/dev_wave_cleanup.py:1488` はpath重複を拒み、entryのbranchは1本だけ。プラン `s2-plan.md:65` の削除記録も現在のbranchだけである。削除一覧140本には、名前に `fix` を含むものが**55本（39.3%）**ある。例えば `deleted-branches.tsv:16` 以降にはt2778のauthor、fix1〜7、m2が並ぶ。

**影響:** 最後の子木・branchを消しても、その木で以前使ったbranchは残る。「統合証明済みの子branchが残らない」という親briefの完了条件を、現在のmanifestだけでは満たせない。55本すべてが同木再利用だったとは確認できないが、生成手順にこの流出経路があることは確実。

**最小修正:** 今回は「manifestの現行branchだけを撤去する」と効果を限定し、旧branchをcleanupの回収対象として明記する。旧branchまで段9で消すなら、作成時のref・tip・所有関係の記録が別途必要で、「postcondition 1か所」の改訂では済まない。

## B-2. 140本の原因別比率は資料から確定できず、残骸全体の解消を主張できない

判定: **real（must-fix）**

**根拠:** [起点brief:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/user-brief-20260921.md:10) と削除TSVには、削除前のmanifest、段9到達状況、integration結果、作成session種別がない。(a)〜(d)は相互排他的でもない。

| 経路 | 今回の分類可能範囲 | 段9改訂の直接効果 |
|---|---|---|
| (a) integration失敗 | t2344-implの1本は起点briefに明記。残りは不明 | 0。rc=20を維持 |
| (b) 停止・中断・裁定待ち | 削除140本から確定不能 | 0。正常landが発火条件 |
| (c) 未登録木・補助ref | archive、backup、saved、mut等の名前はあるが未登録の証拠ではない | 0 |
| (d) dev-wave外session | 名前から作成主体を確定できない | 0 |

名前だけの補助集計では、140本は子らしい名前125、補助・退避らしい名前8、wave本体らしい名前7。**125/140＝89.3%は被覆率ではない**。125本にも(a)〜(c)や旧fix refが混ざる。

**影響:** 「段9で再発防止の本体が完成」とすると、残存経路と回収担当が消える。特に親brief `:24` の「名指し引き渡しも採らない」は、残骸を保持した後の処理を弱める。branch削除だけでは、landを止める壊れたworktree metadataも解消しない。

**最小修正:** 段9を正常終了経路の流入削減、cleanupを既存・例外残骸の回収経路と位置づける。被覆割合は未確定とする。証明不能な子を無条件削除する必要はないが、exact path/ref・理由・回収条件の引き渡しは残す。現資料では「cleanupの方が数量的に本体」とも断定できない。

## B-3. 「所有waveがland済み」の判定手順が欠ける

判定: **real（must-fix）**

**根拠:** `s2-plan.md:153` は「所有waveの記録commitがmainの祖先」とするだけ。branch→所有wave→記録commitの対応をどう取得するかがない。`rulings-verbatim.md:84` は名前・位置による所有判定を認めず、同 `:116` は記録と統合を区別している。

**影響:** T番号の一致やworklogの「完了」を代用すると、別attempt・未採用fixまで許可しうる。逆にexact記録を要求するだけなら、旧branchの多くが判定不能となり、今回解消した手作業の壁が残る。`git cherry` 全 `-` も所有関係・waveのland完了を証明しない。

**最小修正:** 作成時記録／manifest／成果物記録からexact ref・tipと所有waveを対応させ、対応するland記録のfull commitを `merge-base --is-ancestor` で確認する手順を短く定義する。復元不能な旧refは、対象を列挙した個別裁定の経路に分ける。新しい判定CLIは不要。

## B-4. bundleの寿命が未定義で、command予算も未完成

判定: **real（must-fix）**

**根拠:** `s2-plan.md:155` は保存先を「repo外」としか定めない。一方、`brief.md:15` はjob dir削除によるreport消失を記す。D1430もjob領域を恒久記録先としない理由を明記する（`rulings-verbatim.md:193`）。

**影響:** 一時job dirにbundleを置けば、検証済みでも後日まとめて消える。verify成功だけでは、削除直前の対象ref・tipと保存対象の一致も保証しない。

**最小修正:** job自動削除対象外の保存先をexact pathで定め、候補ref/full tip一覧を固定し、bundleの `list-heads` との一致・verify・削除直前のtip不変を確認する。保存先、sha256、検証結果を記録する。

計数ではT-2814適用後**6,201 bytes**、DW-O28案**995 bytes**を再確認した。command案は空行の置き方により7,305〜7,306 bytesとなり、予算6,204には約1,102 bytes不足する。さらに上の不足手順が入るため、**7,306を確定予算にしてはいけない**。完成bytesから最小増枠を算出する。D704型なら既存余白3 bytesを消費でき、プラン `:194` の「余白維持のため+1,105」は必須ではない。

## B-5. 台帳を削除前にmainへ追記すると、別のland停止を作る

判定: **real（must-fix）**

**根拠:** `s2-plan.md:137` は台帳編集を許しstage/commitを禁止し、`:157` は削除前のpending追記を要求する。現行台帳 `docs/unreachable-object-ledger.md:46` は削除後に到達不能となったobjectを追記する契約。`docs/dev-wave/operations.md:172` のlandはtracked dirtを拒否する。

**影響:** cleanupがprimary checkoutの台帳を未commitで残し、次waveのlandを止めうる。削除が失敗・中断した場合には、まだ到達可能なobjectを損失として記録する。残骸によるland停止を、台帳のdirtyによる停止へ置き換える。

**最小修正:** 削除前はrepo外にreportと転記候補を保存し、削除後の到達性で確定する。mainへの反映は明示された記録担当・専用waveへ引き渡すなど、cleanに戻る終端まで定義する。cleanupへ一般commit権限を足す解決は避ける。

## B-6. 227件を66件へ縮める案は現行契約に反するが、schema拡張は削れる

判定: **real（schema拡張の過剰）／refuted（66件だけで足りる）**

**根拠:** `docs/unreachable-object-ledger.md:45` は削除損失閉包と監査通知の両方を追記対象にする。保存資料の集合演算で、227件全件がfsck到達不能、監査との共通66件、監査抑止161件を確認した。監査抑止は台帳免除条件ではない。

現行 `:55` はpendingの解決fieldをnullとする。これを変える理由は親のP3であり、ユーザー起点brief `:34` は `resolution_note` の使用を指定していない。

**影響:** 161件をinsightだけへ逃がすと契約違反になる。一方、bundle情報のためだけにvalidator・test・文書pinを変更すると、不要な実装面とレビュー費用が増える。

**最小修正:** 227件は既存schemaで追記する。bundleの共通情報は台帳の説明文またはinsightへ一度置き、entryの既存 `assessment_reason` に由来・参照を記す。`resolution_note=null` を維持し、`check_branch_rescue.py` とそのtestの変更を削除する。

概算追加量は**295 KB**、現行68,533 bytesと合わせ約364 KB。parserは単一走査と集合照合であり（`tools/check_branch_rescue.py:1758`）、静的には容量だけを重大な性能問題とする根拠はない。実時間は未測定。主な費用は長いJSON行の閲覧性とpending通知の継続である。D1430は対象限定の喪失受容であり、今回227件への一般許可ではない。bundleだけで `rescued` にできない直接の理由は、同 `docs/unreachable-object-ledger.md:51` の救出ref要件である。

## B-7. 監査のみ21件の「報告だけ」は未記帳を残す

判定: **real（must-fix）**

**根拠:** `s2-plan.md:219` は追加21件を別集合として報告するだけ。台帳 `:47`、`:121` は `unledgered-audit-finding` も追記対象とする。[ledger-check-1.json:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/ledger-check-1.json:1) の未記帳87件と損失227件の和集合は**248件**である。

**影響:** 227件を全転記しても、21件の未記帳通知は残る。「今回の損失閉包外」と「台帳対象外」を混同する。

**最小修正:** 21件を今回の削除原因へ帰属させず、監査由来の別集合として転記するか、担当と未完了状態を明示して引き渡す。台帳整合完了とは報告しない。

## B-8. A/Bの共有file所有は、並列化より同期費用を増やす

判定: **real（must-fix）**

**根拠:** `brief.md:45` はAを非競合とするが、A/Bとも `check_docs.py` と `test_check_docs.py` を所有する。`workers.md:21` は所有path素集合を要求する。プラン `:354` もfile単位では非競合でないと認めている。

**影響:** hunkが離れていても、完成fileは両親どちらとも異なる実装になる。`operations.md:148` のCodex author要件が掛かり、通常のpost-claim mergeで解決済みとは扱えない。待ち手もmerge後にprovenance preflightを行う（`tools/dev_wave_wait.py:3853`、`:3866`）。さらに各子へ完成fileを再配布する費用が、段9成功のためだけに発生する。

**最小修正:** Aはcleanup toolと専用testのみ。Bにcommand、overlay、**DW-O28を含む全pin・fixture・予算変更**を集約する。これで所有fileを素集合にできる。

T-2814待ちは起点brief `:27`、`:41` の明示条件なので、先行編集案は採らない。待ち時間中にAと親のdocs・台帳準備を進め、T-2814取り込み後にBを一度起動する。同checkerを両親が変更する取り込みが残った場合は、Codex merge authorへ渡す。待ち時間の実測がないため、時間差の数値比較はできない。

## B-9. 親briefの件数には誤記と一般化が混在する

判定: **real（must-fix）**

**根拠と検算:**

- `excluded-branches.tsv:1`〜`:24` は、稼働11、locked **7**、1h以内1、新規5。起点brief `:16` のlocked **6**は誤り。
- 削除TSV140行、bundle heads140行、retire JSON13件は一致する。
- 削除一覧から最初のT番号を機械抽出すると**45種**。これはwave数ではないが、「40 wave」を実測した根拠にもならない。155本との母集団対応表がない。
- 「1 waveあたり2〜8本」はwave単位の対応表がなく再現不能。t2724関連16本、t2778関連9本もあり、名前をwave単位へ単純変換できない。
- 「39本は内容までmainと同一」は保存されたcherry出力が提示資料にないため再検算不能。仮に全 `-` を確認しても、patch同等性からtree全体同一へ一般化できない。
- `rescue2.json` は保存先一覧に存在しないが、「f9f84e36の削除が原因」は削除ログなしでは独立検証できない。
- **227／87／66／161／21、fsck 1,721件は再計算一致**。1,634＝1,721−87も一致するが、抑止理由の全件内訳は親追加実測に依存する。

**影響:** 誤った分母・最大値がfailureとdecisionへ恒久化され、D2163を覆す効果量の説明まで過大になる。

**最小修正:** lockedを7へ修正。40 wave・2〜8本・39本のtree同一性は、出典付き推定または未検証の観測記述へ下げる。「155本の蓄積があった」と「新方式がその大半を防ぐ」を分離する。

## B-10. 安全条件の重複とCodex全面縮退は、追加義務にしなくてよい

判定: **refuted（全面的な追加・縮退の必要性）**

**根拠:** 現行command `:44`〜`:49` にlocked・所有不明・worktreeの1h条件がある。overlay `SKILL.md:25` は破壊操作直前に全eligibilityを再評価し、棚卸し後のchangeで停止する。

**影響:** 同じ条件を別々のgateとして増やすと判定回数と文面だけが増える。一方、現行1h条件はworktree向けなので、checkoutされていないbranchへ適用する意味は明確化が必要。

**最小修正:** 安い除外条件へ統合し、snapshot後の新規候補は集合に追加しない。削除直前のlock再検査は実事故に対応するため残す。Codex全体を `-D` 禁止へ戻す必要はないが、所有不明・権限不足・cwd固定では既存overlayに従って引き渡す。**本段のread-only環境で実行可能という意味ではない。**

## B-11. 文書の局所修正は可能だが、既存Dへの直接追記は代替にならない

判定: **refuted（新D・新Fが当然に過剰）**

**根拠:** `operations.md:213`〜`:214` の子branch保持・全面 `-D` 禁止を局所置換すればDW-O28の意味変更は表現できる。一方、`docs/spool/decisions/README.md:5` は新D形式のみを持ち、spoolの既存台帳挿入例外はF等に限定される（`docs/spool/README.md:94`）。

F747は削除0件でも記録権限を合成した越権事故であり、今回の「必要な撤去経路がない」と原因が異なる（`f747-verbatim.md:3`）。

**影響:** D2163へ直接supersede追記するためにfold機構を拡張すると、削減目的に反してscopeが増える。F747の再発として扱うと権限逸脱と機能不足を混同する。

**最小修正:** 新Dを1件にまとめ、D204/D703/D2163等の変更箇所だけ明記する。新Fは別型としてよいが、未検証の「40 wave」を原因証拠にしない。DW-O28は末尾2行中心の変更と必要な圧縮に限定する。段9でbundleを実施しない以上、その義務を本文へ足す必要はない。ただし、**内容統合は履歴保全ではない**という限界はDに残す。

## B-12. review二本は必要、固定fix枠と台帳schema実装は不要

判定: **real（分割の修正）／refuted（review二本の過剰）**

**根拠:** `workers.md:49` は実装waveの異なるレンズによるreview二本を要求する。`workers.md:57` のfixはreal所見が出た場合の工程。親の台帳entry・fragment・DW-O28本文と、Codexのtool・test・pinという境界自体は妥当である。

**影響:** author二本を同じfileへ向けることや、P3の注記方式だけのためにvalidator担当を増やすことが固定費になる。fixを必須本数として予約すると、所見がなくても工程が増える。

**最小修正:** B-8の素集合分割でauthor二本、統合後review二本、real所見がある場合だけfixとする。B-6のschema変更を削除し、生成scriptは既存schemaへの転記に限定する。静的確認・資料集計のみ実施し、pytest・変更・commit・branch操作は行っていない。

## 総括

- **must-fix:** 旧fix refと(a)〜(d)の残存経路、land証拠の対応付け、bundle保存先、台帳編集後のcleanな終端を明確にする。
- **must-fix:** A/Bをfile単位で分離し、pending注記のschema変更を削除。監査のみ21件を未処理のまま完了扱いしない。
- **must-fix:** lockedは7本へ訂正し、40 wave・2〜8本・39本の同一性を未検証の効果根拠に使わない。
- **nit:** commandの空行・最終byte数、プラン内の旧worktreeリンクを完成時に揃える。