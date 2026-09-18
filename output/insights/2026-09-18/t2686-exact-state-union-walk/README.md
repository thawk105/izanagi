# T-2686 exact-state union walk 回収

着手mainは b2037abfa1467507cf92c851c83f262239f81641。元author実装は
6ac18eb40a336e3022ad3f9e06f792cbca2e7b9e、固定検証anchorは
977cda2ead6cb9d9a90741428babccbb416a3deb。
productionの受理述語を変えず、候補供給のunion化とtip entry memoを回収した。
既存定義のAST比較では72個が不変、接続先の変更は_find_exact_state/_proof_unit/assessの3個。
追加は供給classとNUL parser。全DAGでの候補順同一性や時間内完走集合の保存を証明したものではない。

## 根因と独立レビュー

元focus1は370 passed/3 failed。履歴walkの観測が --name-only だけを見てgit diffも数えたことが根因。
隔離authorは7つの観測/注入selectorをlogとの積へ限定し、productionと既存assertを維持した。
独立レビュー2本が実差分を確認。親焦点走はchecker/rescue/schedule/duration制約の4fileで
373 passed / 52.10秒（正規run_tests、上限付きlocal、peak2637873152 bytes）。

比較driverには2回の局所修正を行った。最初は同じtimeout結果でも比較成功にできた欠陥。
次は、仕様上git cherryがmergeを省略する非決定的patch-id観測を実行失敗と誤認した欠陥。
最終版はproducerのexactなmerge省略経路だけを許し、timeout reason、parse error、別層truncation、
件数不整合を拒否する。親の実raw4正例/16負例と独立焦点レビューで確認した。
raw/canonicalのpatch-id fieldは除去せず、不完全表示を保持する。任意に改ざんされたJSONの検証器ではない。

## 計算ノードでの対測定

固定target 559bcbc29cfa27412f103b608e8ac708dcfae6b9、同一aux worktree、各assess予算900秒。
採用走ab-run2はbnode050、Python3.10.12/Git2.34.1、driver rc0。
全4走のmainは56be58448ae7ddbbcdfce5d38d17d63b8231791aで開始/終了とも同じ。
elapsed_seconds全出現とtop-level timingだけを除いたcanonical JSONはbyte一致
（SHA256 74b230ebfd81b87a20f8ae070e2e77bce27807eb91b00a998c768684c76addf3）。

| 走 | assess秒 | Git子process | 新供給walk |
|---|---:|---:|---:|
| old-1 | 40.001 | 244 | 該当fieldなし |
| new-1 | 25.789 | 161 | 1 |
| old-2 | 38.196 | 244 | 該当fieldなし |
| new-2 | 26.065 | 161 | 1 |

全走の判定はindeterminate/one-or-more-states-unprovenで一致。patch-idは8closure中2mergeを省略し、
6件報告・不完全の表示を保つ。これは実行timeoutではなく、summaryにも許容した省略を明示した。
旧source SHA256は80cd92ccb6604da35bfa731458a3db62a7db1362d0a83a14bfca61ba52d73b51、
新sourceは25008cc75735cc439ecc8000e950bd6ed57f4996294e55bedf3d05f83847b50a。
最終driver SHA256は701351ee66212c61063e78b8277172695c1aad05ba9f65102869d1443cd4cfd0。

wallはこの2対の観測値に限る。loadavgの1分値は約17.5から2.8へ低下し、端点psだけでは同居や途中の
I/O外乱を除外できない。wall差を実装単独の因果効果や一般的な高速化率としない。
process減はunionとtip memoを含む変更全体の比較。初回unit elapsedとwalk秒数は重複するので加算しない。
rescueの8秒予算内への収束は完了条件でも達成主張でもない。

ab-run1（bnode034、main b2037abfa）も4payload一致/244→161だったが、旧driverが正常merge省略を
拒否してrc1となった記録を保持する。旧36.404/37.273秒、新25.678/25.192秒。
修正後に取得したab-run2と分け、run1を遡って成功へ変更しない。

## 変異の解釈

最初の17件probeはbaseline153 passed、16 MISMATCHと等価m16 SURVIVED。
MISMATCHは失敗node取得用の期待SURVIVEDとの差で、正式KILLEDに数えない。
正式16件（m04以外）はbaseline green、15 KILLED/m16 SURVIVED、失敗node完全集合一致、MISMATCH0。
m04はuniversal OID sortの追加失敗が生成OIDに依存するため、既登録の非lexical保証付きkillerへ分離した。
テスト期待値やfixtureは変えず、変異自体も同じ。

m04の初回単独走はbaseline PASSED/期待1node KILLED、復元済みだったが、外側wrapperが
source/mainの観測bytes変化を検出してrc125。前後bytesは保存されず、変更主体は断定しない。
赤を無視せず同一anchorの独立local cloneをsource/primaryとした再走を行い、
baseline PASSED・期待1node KILLED・wrapper rc0・shared snapshot一致・teardown完了を確認した。
この走が証明する共有木不変は独立cloneに限り、稼働中の実repo primary全体の不変を主張しない。
正式17件を合わせるとraw statusは16 KILLED/等価1 SURVIVED、MISMATCH/PARSE_ERROR/TIMEOUTは0。

rawのKILLEDという語を全部正しさの検出力に換算しない。
m04は候補順序、m09は再走査呼出し、m12はfallback方式、m14は対象path、m15は失敗memo、
m17は旧per-pathへの復帰を検出する契約感度を別枠で記録する。
特にm17の意味論は旧供給なので維持され、process/union固有の契約が破れる。
m16はdocstringのみの等価対照である。

## 記録上の訂正と境界

- 元s4のargv説明「65536+固定費約700が128KiBの半分未満」は算術誤り。
  正しくはpath部分64KiBに制限して残りを固定費等に残す。閾値・受理述語は変えない。
- anchorの初期READMEに既知provenance違反を2件と書いたのは抜粋の読み違え。
  正本summaryは56件（既存baseline以前53/以後3）、11461件監査で新規違反なし。
- author初回はCLI0でも総括見出し欠落でlauncher1/f43_fragmentの未受理。実装残差を保存し、
  DW-O01に従って独立review2本が実コードを監査した。未受理報告を緑にしていない。
- 初回provenanceは監査中のauthor終端commitによるHEAD変化でrc2。HEAD固定後の再監査を採用した。
- 初回焦点job6380とprobe job6407はQUEのまま正規SIGTERM/qdelで取消し、終端を確認して再投入。
  signal-abortのrc16をテスト成否としない。新規gate・台帳機構・一般化・次waveは追加していない。

元資料はoriginal-evidence/、レビューはverbatim/。末尾空白だけを正規化した6資料は
whitespace-restoration.jsonで元bytes/SHA256へ復元一致を確認済み。原job資料も保持する。
