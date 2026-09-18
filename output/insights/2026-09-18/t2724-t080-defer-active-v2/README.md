# T-2724/T-2776 中断実装の回収

T-080 receiptの未知性層2をactive v2のfull launch validationへ委譲するA-3と、
4経路45nodeのfixture切離しを回収した。chain/X2/Gの取り込みと実A/Xの発効は今回の範囲に含めない。

## 出所と裁定

- 旧branch: `worktree-dev-wave-t2724-t080-defer-active-v2`、最終実装tip `e2b3cc4839d1bc8e035f3031540a1ec36601a07a`。
- 旧job: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/`。handoff、段2/3、段4、fix1の裁定を引き継いだ。
- 回収branch: `codex-dev-wave-t2724-t2776-recovery`。着手時main `b2037abfa1467507cf92c851c83f262239f81641`から専用Codex worktreeを作成。
- 裁定は `verbatim/rulings-verbatim.md`。A-3を先に整合し、検出力を維持してtestを修正、その後にchainを別waveで導入する。
- 旧木の未commit成果57fileとspool2片はrepo外へbyte一致で保存後、独立監査を経て回収した。
- 実装の統合snapshotは`4dfc6ba83`。共有sinkテストはmain版を保持し、隔離authorが同じsinkの位置2箇所だけを追随した。

## 実装の境界

`_holdout_layer2_delegation`はexact型・resolve済みroot・outer/inner/captured HEAD・active世代の
SHA/番号/commit・列挙digest・凍結文書との束縛を照合する。不成立なら通常scanとzero-hitへ戻る。
成功したfull validationのdeep-freeze済みreportがあるときだけ、層2のzero-hitをC2-4完全一致へ委譲する。
receipt履歴・静的検証・epoch・refusal集約・invalid拒否は保持する。

driverはlaunch判定後にreceiptを解決し、campaign-start前に同じtokenで再解決してepochを比較する。
再launchは既存E3b（検証済み同一objectを消費）に反するため採らない。段4の再launch案は
`verbatim/s6-fix1-findings.md`で訂正済み。同名fileの内容交換は名前集合digestでは検出できず、
single-tenant前提の残余として保持する。campaign-startで内容鮮度まで再検証したとは主張しない。

fixtureの削除集合はofficial namespace全体と候補exact fileだけ。残存mode/OID/bytesと候補siblingを検査する。
実scanのofficial/candidate/both負例と無害bytesの正例、履歴・静的検査の負例を保持する。
接続fixtureはkeyごとのshared-baseをcopyし、copy後のcalibration/selector材料を親rootへfallbackしない。
base構築そのものの親root読取りや、他writerとの完全排他まで解消したとは主張しない。

## 回収した実測

以下は旧checkoutの測定時点の事実であり、新統合tipの受入ではない。所要はpytest報告値。

| 対象 | tip / request | 結果 |
|---|---|---|
| 修正前chain有り対照 | `7679264fc` / 5492 | 45 failed、967 passed、11 skipped、444秒 |
| fix3後chain無し・29file | `8b8bb96f2` / 5664 | 2672 passed、36 skipped、301秒 |
| 最終chain無し・8file | `e2b3cc483` / 5698 | 1211 passed、12 skipped、377.05秒 |
| 最終chain有り・7file | `8298f7430` / 5699 | 1104 passed、11 skipped、432.50秒 |

45nodeの内訳はoutput複製10、floor clone5、memo依存29、g7が1。最終の両木では失敗0。
接続nodeは接続8＋draft1、shared-baseはkeyごと（通常trailerと不正trailerの2base）。
P3のv1経路はchain無しで拒否2件、未発効chain有りで拒否4件を維持する。
実A/Xの発効後の正例は未実測であり、正例は合成Git fixtureでの実検証機構の接続である。

## 変異matrixの回収

旧final A/Bのdoneは双方0、repo_headは双方`e2b3cc483`。baselineは双方247 passed。
spec SHA、各anchorの一意性、expected/failed nodeの完全集合と格納stdoutを照合した。
負例12件すべてKILLED、コメントだけの等価対照m0はSURVIVED、MISMATCH/PARSE_ERROR/TIMEOUTは0。
統合snapshotでもproduction3fileと対象4test fileは旧tipとbyte同一。旧matrixを新tipで再走したとは記録しない。

| 変異 | 期待と一致した失敗node数 |
|---|---:|
| m1 / m2a / m2b / m3 | 2 / 1 / 1 / 11 |
| m4a / m4b / m5 / m6 | 2 / 2 / 6 / 1 |
| m7 / m8a / m9 / m10 | 2 / 7 / 1 / 1 |

m2aは不正R trailerの受理、m2bはinvalidのcompleted到達、m5はreceipt変更後のcompleted到達を検出する。
m5の件数には呼出し回数だけの赤も含むため、挙動変化の独立根拠は`[changed]`である。
m8bは冗長gateによるmask、m11は再走査撤回により登録から外した。これらをkill証拠に数えない。
一次資料は `evidence/mutation-final-A.json`、`mutation-final-B.json`と対応spec。

## 回収監査とerratum

独立read-only Codex 2レンズを使用。双方が新規実装must-fixなし、旧RR-1は静的closedと判定。
旧failures fragmentが修正前NO-GOを解消根拠に参照していた所見REC-1はrealとして訂正した。
一次資料は `verbatim/recovery-review-A.md`、`recovery-review-B.md`、`recovery-adjudication.md`。

review Bの「chain-3に2 errorsを追加」はrefuted。原logのpytest終端は
`2 failed, 1088 passed, 7 skipped in 388.35s`、failure digestは`errors=0`である。
INTERNALERROR/crashitemは別に発生した。旧`evidence/focus-chain-3-summary.txt`の`2 errors`は
集計誤りとして原文を残し、この段落で訂正する。生logは旧job dirの`focus-chain-3.log`。

回収時の共有sink位置修正は隔離authorだけが実装した。型・期待件数・mainの他wave追加を保持し、
`pipeline.evaluate`を1775→1781、`evaluate_fn`を1788→1794へ追随した。

## 検査・記録の所在

統合tip `423bef885` の29file焦点走はrequest6381、2713 passed / 36 skipped、失敗0、309.71秒。
共有sink testの単独走は初回request6404が900秒のqueue待ち上限でchild未開始のrc16となった。
job不在・producer/待ち手終了を確認し、同tipをrunner既定配置で再走してbounded localで
71 passed / 2 skipped、70.85秒、rc0。これはテスト失敗の除外やhold追加ではない。
同tipの全史provenanceは11468件、新規違反0、既知違反56件（解消したとは扱わない）。
修正後の焦点再レビューは `verbatim/recovery-focus-review.md`、限定4項目closed・GO。
ログは `evidence/recovery-focus-1.log`、`recovery-pin-test-1.log`、`recovery-pin-test-2.log`。
最終受入は記録commit後に実施し、回収jobの成功受領証とland応答を正本とする。
既存のqueue待ちoverrideを3600秒、待ち手全体上限を10800秒とし、検査内容は変更しない。
回収job: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t2776-recovery/`。
改善実装と次waveは追加しない。chain/X2/G保存枝と人間A/Xの境界を維持する。

原本の保全先は回収jobの`recovered-insight`と`recovered-decisions.md` / `recovered-failures.md`。
旧dispatchの参照pathは同jobの`recovered-dispatch/source-wave`および`mut1`〜`mut4`へ対応し、
それぞれ49/65/73/65/73fileのbyte一致を確認した。旧branchを清掃してもこの保全先で追跡できる。

## 停止記録

最終受入attempt1（tip `d899c86aa`）は25153 passed / 69 skipped / 12 setup errorsで失敗した。
成功受領証は発行されていない。全12件はT-1259のmodule fixtureからの
`git ls-files --others --exclude-standard -z` が30秒でTimeoutExpiredとなったもの。
当該test/probeには今回の差分がなく、T-080の委譲を通るtest本体に到達していない。
I/O遅延の個別要因は分離していない。

同tipの正規runner単独走でも51 setup errors、247.47秒、rc1で同じtimeoutを再現した。
DW-O18により受入2を投入せず正式停止。main land・対象branch/worktreeの清掃は未実施で全対象を保全する。
既存T-2790（D2148項12）のfixture待機上限の設計・検証を越えて、今回timeout/hold/除外は変更しない。

判定は `verbatim/acceptance-1-adjudication.md`。生logは回収jobの`acceptance-1.child.log`、
`t1259-single.log`と`acceptance-1-shards/`に保全する。旧変異、焦点走、独立監査の結果を
受入成功に読み替えない。再開位置と停止時mainは専用handoffに残す。
