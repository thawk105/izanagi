## 所見

1. **[real / blocker] 現planの新規resolverは行数上限へ入らない。**
   `stage2-plan.md:58-67` の新moduleだけで約220行あり、残147行を73行超過する。さらに `_git.py`、`_manifest.py`、`_binding.py`、`_writer.py` の変更が必要なので、見積りはsubmission_gate純増342〜415行、最終6,395〜6,468行である。成果物はproduction実装全体に影響する。新module案は撤回し、既存のsealed `ApprovedManifest`へeffective authorityを統合するか、上限拡張を裁定へ返すべきである。

2. **[real / blocker] plan内でline-budgetの母集合が矛盾している。**
   親実測は `submission_gate/*.py = 6,053` だが、`stage2-plan.md:230-237` はさらに587行の `approval_payload.py` を足す。このコマンドなら編集前から6,640行で6,200を超える。checkerがsubmission_gate限定ならapproval側統合案を評価できるが、planの合算を正本にするなら着手前からNO-GOである。段4までにexact allowlistを一つへ確定し、他方は参考値として別表示する必要がある。

3. **[real / must-fix] 正しさを削らない最小案はあるが、現planでは収容証明されていない。**
   `_EffectiveApproval`と新moduleを作らず、`approval_payload.py`には非authorityのsuccessor parser/graph判定だけを置き、既存のtoken-sealed `ApprovedManifest`を唯一のeffective authorityにする。`_binding.py`はそれを保持し、writerはbindingからのみ読む。submission_gate側の目標配分を `_git.py <=20`、`_manifest.py <=78`、`_binding.py <=28`、`_writer.py <=8`、semanticは行数中立、合計134行以下とすれば6,187行で13行残る。
   ただし実patchでこの配分を超えたら、cycle・欠落・複数候補拒否などを削らず停止する。この意味でGOは無条件ではなく、line-count prototype合格を前提とする条件付きGOである。

4. **[real / must-fix] indexには世代境界が必要である。**
   `index-v1.json:1-47` は実測で42件、digest `c66953...0643`。旧42個のvector JSONを不変にしても、同じindexへ4行を追加すればindex bytesとdigestは変わる。`stage2-plan.md:118-120` の「旧42を別assert」は、期待値を新indexから読むだけなら同時改変を検出できない。
   `index-v1.json`自体を42件・旧digestのまま残し、新しい46件indexを別path、例えば `index-v2.json` に作るべきである。新payloadは新index三つ組をpinし、テストは旧index digest、42件のID/path/digest projection、新index digestを独立に固定する。

5. **[refuted / nit] 4新vectorの追加自体は旧42 vector JSONのbyte不変を壊さない。**
   各vectorが別fileであるため、旧fileを触らず新index世代から再参照できる。問題はvector bytesではなく、同じindex fileを更新しようとしている点である。

6. **[refuted / must-fix] fixture-only writer正例でも恒常denyは殺せる。**
   resolverが発行したsealed authorityで `_publish_receipt()`を通し、raw bytesのexact publishを確認すれば、現行 `_writer.py:29-36` の無条件例外は失敗する。さらに現行のmissing-authority負例、`test_t338_submission_gate_unit5.py:360-375,439-443` をlegacy D282 authority用に残せば、guardを恒真returnへ変えるmutationも殺せる。
   ただし `_PreregBinding._issue()` を直接呼び、同じfixtureがpayload・manifest・期待digestを全部生成する正例ではresolverや外部pinを検査できない。正例は一時Git repo内で `I -> M -> P` を構成し、publicでない通常resolver経路からbindingを得る必要がある。

7. **[refuted / nit] real-repo authority正例はD292を必ず越えるわけではない。**
   canonical Pを含むHEADのtemp cloneでresolverとwriterを検査し、qsub、計算資源、live `output/receipts`を触らなければ、pilot/main投入ではない。`stage1-brief.md:6-7` と `q1-package.md:219-224` の禁止を維持できる。ただしP fold前には構成できないため、commit順序問題は別に残る。

8. **[refuted / must-fix] private consumer testには純増価値がある。**
   resolver、manifest、binding、semantic validator、writerの結線を一度に通し、D264の4名前をexportせず検査できる。ただしD264 `decisions.md:12185-12205` とD509 `:21195-21216` により、これを単位6または投入gate完成とは記録できない。成果物名は「private publication path integration」に限定し、4名前nonexport testを併存させるべきである。

9. **[real / blocker] planの `I -> M -> P -> C` はdev-wave工程と両立しない。**
   `stage2-plan.md:129-161` はP後にcode/test結線Cを置くが、canonical spool foldは段9だけで、authorはcode/test、親はdocs/commit担当である。Cを段9後に置くとreview・mutation・acceptanceを通せない。
   実行可能な順序は `I -> M -> C -> P` である。CはPのcommit literalを持たず、canonical history上の初出commitを導出する。段6〜8は一時repoのPで検査し、段9で親がPをfoldした後、実canonical HEADに対するfocused resolver/pin検査を追加実走する。段9後検査をworkflowが許さないなら、activationを次waveへ分離しなければならない。

10. **[unclear / blocker] D95/DW-S05による全file単一author権限は射影資料から確定できない。**
    promptで確定している境界だけでも、一人のauthorがdocs fragmentまで扱う案は不成立である。production、tracked manifest JSON、vector/index/test fixture、testsは一人のcode/test authorへまとめ、canonical decisions/worklog fragmentと全commitは親が扱う必要がある。段5 dispatch前にD95/DW-S05のexact allowlistを親が照合する。別code authorへ分割する必要はない。

11. **[real / must-fix] successor history契約が未確定である。**
    `stage2-plan.md:61-74` の「first-parentまたはcanonical fold規約」は択一のままである。`docs/decisions.md`のpayload fenceは後続commitにも残るため、各snapshotをcandidateとして数えると同じpayloadが重複する。merge時の導入commit、payloadの後日mutation/removal、unrelated decision追加も結果を分岐させる。
    path変更commitを祖先順に読み、decision IDごとの初出、以後のbyte不変、唯一predecessor、唯一tip、base到達、全candidate接続をexactに定義する必要がある。

12. **[real / must-fix] briefのproduction consumer到達主張は過大である。**
    `stage1-brief.md:18` は材料レポートや試行台帳への到達を結果として挙げるが、本scopeにはproduction caller、selector、report sinkがない。private testが通っても実運用consumerは0件のままである。writerの恒常拒否解消という成果は実在するが、「reportへ到達可能になった」とは記録せず、unit6またはK2/K3 consumer waveへ残すべきである。

13. **[unclear / must-fix] B2閉包が親briefから抜けている。**
    `q1-package.md:209-217,244-247` は `series_id`、sealed set、`receipt-set.json`を未着手としてK2へ残す。一方、今回のwriterはseries IDを含む固定namespaceへpublishする。unit4 authorityがこれを既に閉じたかは射影資料だけでは確認できない。今回のscopeへ無断追加せず、private writer完成がB2完成を意味しないことをstage9の新worklog entryへ記録する。

14. **[real / must-fix] mutation planには自己整合survivorが残る。**
    `test_t338_submission_gate_unit5.py:72-86` はindex/vectorをworktreeから読み、`:328-334` はindexとvector同士だけを照合する。index、vector、期待値を同時に変えれば通る。新しい三差替え負例も、fixtureが差替え後にdigestを再生成すると自己整合する。
    旧index tripleとcanonical P側pinを独立literalにし、mutationはmanifest、payload、indexの片側1 fieldだけを変更する。productionと期待値を同一mutationで変えない。productionがHEAD同名fileでなくcommit Iのtreeを読むことも、HEAD側だけを差し替えるテストで固定する。

## 予算と最小実装表

| 案 | submission_gate純増見積り | 最終行数 | 判定 |
|---|---:|---:|---|
| planどおり新 `_approval_resolver.py` | 342〜415 | 6,395〜6,468 | blocker。上限超過 |
| parser/resolverをすべて `approval_payload.py`へ逃がす | 37〜72程度 | 6,090〜6,125 | 行数だけは通るが、Git/history責務の逆流とchecker回避になるため不可 |
| 既存seal統合案 | 119〜150 | 6,172〜6,203 | 唯一のGO候補。上限配分134以下を事前固定 |
| mechanism-only、real repoは恒常deny | 0〜小 | 6,053付近 | D626の現状と実質同じ。briefの成果を満たさない |
| 新moduleを維持し上限拡張 | 342〜415 | 6,395〜6,468 | 正しさは保てるが新裁定が必要 |

最小案の構成は次である。

- `approval_payload.py`: successorのstrict bytes parserとgraphの純判定。parsed dataclassはauthorityにしない。
- `_git.py`: canonical path history取得helper一つだけ。
- `_manifest.py`: 既存sealed `ApprovedManifest`へmanifest ref、base/effective fold、vector indexを追加し、ここで唯一authority化する。
- `_binding.py`: 同じ`ApprovedManifest`を保持し、blob・commit順序・sealを再検査する。
- `_writer.py`: binding内authorityのvector有無とpayload/manifest一致だけを検査する。
- `_semantic_validator.py`: `:1038-1042`相当の誤説明を行数中立で修正し、predicateは変えない。

## consumer・test閉包

| 面 | 現資料で見える取り残し | 必須対処 |
|---|---|---|
| `_PreregBinding._issue()` | `test_t338_submission_gate_unit5.py:384-392` に新authority引数が無い | sealed legacy authorityを渡す |
| guard monkeypatch | 同`:401,545` は引数なしlambda | `lambda *, binding: None`等へ更新 |
| structural deny test | 同`:439-443` は`vector_index` field不存在を前提 | legacy authorityの`vector_index=None`拒否へ置換 |
| 件数・分類 | 同`:315-322` は42件、分類 `new=2` | 46件、positive=2、negative/API=44、新classification総数へ更新 |
| 実行分岐 | 同`:474-498,501-561` に新authority entrypointが無い | writer positiveと三差替えを独立実行 |
| historical pin | 同`:72-86` はworktree読取のみ | 旧index digest literal、新index triple、commit I tree読取を追加 |
| raw bytes | `_writer.py:53-76` は入力bytesをそのまま渡す | positiveでpublished bytes exact一致と2回目EEXISTを確認 |
| semantic binding | `_semantic_validator.py:594-646` はrecord 9 fieldを比較 | manifest ref=M、fold=Pがbinding recordへ入ることを維持 |
| nonexport | D264の4名前test本体は未射影 | no-touchではなく、exact four absentを必ず再実走 |
| unit1〜4 | callsite一覧がplanに無い | author開始前に全 `_issue`、`ApprovedManifest(`、loader、guard callsiteを列挙 |
| AST allowlist | unit5 `:446-471` はdirect nameだけを見る | 今waveでは維持。alias迂回は別記録 |
| line checker | exact allowlistが矛盾 | canonical checkerを一つに固定し、untracked新fileも計上 |
| pin closure | 旧indexと新indexの境界が無い | 旧indexを不変保存し、新payloadは新世代だけをpin |

「unit1〜5を全数」とするには、未射影のunit1〜4およびnonexport checkerのcallsite実測がまだ必要である。planの「unit3等」だけでは閉包一覧になっていない。

## 親briefへの直接攻撃

- **[real / blocker]** `stage1-brief.md:15` の「外部pin済みpayload authority」と、`:19` の段5author分割規則は、Pが段9foldである工程を扱っていない。成果物定義は正しいが同wave内の順序が欠けている。
- **[real / must-fix]** `:12` の「凍結済みbytesは変更しない」と、`:10` のindexはlive assetという分類が曖昧である。旧indexを保持し新世代を作れば両立する。
- **[real / must-fix]** `:18` のreport/台帳到達は本scopeで証明できない。private writer availabilityまでへ狭める。
- **[unclear / must-fix]** Q1 packageで残ったB2をbriefが扱っていない。少なくとも「本waveでは閉じない」と明記する。
- **[refuted / nit]** D264 nonexportのままprivate integrationを作ること自体は矛盾しない。ただし投入gate完成や単位6完成と記録してはならない。

## planへの直接攻撃

- 新module約220行は、他変更を数える前に失格である。
- `stage2-plan.md:230-237` のline-countコマンドは親baselineと母集合が違う。
- `:118-120` のin-place index更新は旧index pinを失う。
- `:131-150` の `I -> M -> P -> C` は段9fold規則と衝突する。
- `:58-68` の別 `_EffectiveApproval` は既存`ApprovedManifest` sealと責務が重複し、行数とmutation面を増やす。
- `:67,89,96` はbinding integrityとwriter guardに同じ検査を重複配置している。seal/blob intactはbinding、vector非Noneと二つの宣言一致はwriter、という責務分離が必要である。
- `:120` の件数更新だけではclassification Counter、module docstring、新entrypoint、legacy missing-authority vectorが取り残される。
- `:190` の恒真guard mutationは、legacy D282負例を新authority fixtureへ置換するとsurviveする。legacy負例を独立保持する。
- `:191-195` のtrust-edge mutationsは、fixtureが期待digestを再生成するとsurviveする。片側mutationに限定する。
- `:241` の単一author案はcode/test面に限れば正しいが、docs/commitまで含めると権限違反になる。

## scope外

- `series_id`、sealed set、`receipt-set.json`、production consumerはT-139 K2/K3または単位6の次waveへ記録する。
- D264の4名前export、`submit_pilot`、driver、collector、PBS、D292解除は実装しない。
- AST allowlistのimport-alias迂回は `vector-authority-design.md:63-71` の既知限界として別hardening waveへ残す。
- D95/DW-S05のexact author権限、canonical line-checker allowlistは親の段4計画へ記録する。
- entry 874は変更せず、今回の部分完成、B2未閉包、post-P検査結果は新しいworklog entryへappendする。
- canonical P fold後のreal-repo authority検査を段9で実行できない場合は、activation専用waveを起票する。

## 総括

現planのままは**NO-GO**である。新resolverだけで行数上限を破り、index世代、段9fold、所有、post-P検証も閉じていない。

タスク自体は**条件付きGO**を維持できる。条件は次の4点である。

1. 新moduleを撤回し、既存sealed `ApprovedManifest`へauthorityを統合する。
2. submission_gate純増を134行目標、147行絶対上限で事前計測する。
3. 旧indexをbyte不変で残し、46件の新index世代を別pathにする。
4. commit順を `I -> M -> C -> P` に変え、P fold後にcanonical HEADのfocused検査を実走する。

今回はread-only相談であり、pytest、checker、mutation、acceptanceはいずれも実走していない。緑とは判定しない。