## 1 枠組みの検査

静的検査では、前 wave の3本の根拠はいずれも現物で裏が取れた。ただし、3択の分類は完全ではない。

1. **受理枝が発火しない: 裏が取れた。**
   現行 formal consumer は「P6実装が存在しないため fail-closed」と明記し、条件1〜7・9〜10の通過後も無条件に `P6Unavailable` を返す。[reflux_formal_consumer.py:1-8](/work/1/SFC/tanab/izanagi/orchestrator/campaign/reflux_formal_consumer.py:1)、[同:942-1046](/work/1/SFC/tanab/izanagi/orchestrator/campaign/reflux_formal_consumer.py:942)。これは「現行裁定を守る受理枝」の到達不能を証明する。cap-lift receipt 自体は未実装なので、既存 receipt branch の動的到達不能を証明したものではない。

2. **registered manifest が世代数2固定: 裏が取れた。**
   manifest parser は exact built-in `int` かつ `== 2` だけを受理する。[trial_registry.py:743-773](/work/1/SFC/tanab/izanagi/orchestrator/campaign/trial_registry.py:743)。runtime値もmanifest宣言値とcampaign identity導出前に一致必須である。[p3_autonomous_workload_trial.py:1245-1262](/work/1/SFC/tanab/izanagi/orchestrator/campaign/p3_autonomous_workload_trial.py:1245)。正式受入でもreport予算とmanifestの一致を再検査する。[trial_registry.py:5742-5762](/work/1/SFC/tanab/izanagi/orchestrator/campaign/trial_registry.py:5742)。さらにorigin発行は `registered-effective` に限定される。[p3_autonomous_workload_trial.py:1412-1419](/work/1/SFC/tanab/izanagi/orchestrator/campaign/p3_autonomous_workload_trial.py:1412)。

3. **topologyだけで開くと前提条件を迂回する: 裏が取れた。**
   D121は「多世代開放の前提条件を10件に固定する」、D150は `NOT_IMPLEMENTED` を失敗とし申請者に状態を選ばせない、D156はend-to-end calibration・独立attestation・認定記録を要求する。[decisions.md:5842-5850](/work/1/SFC/tanab/izanagi/docs/decisions.md:5842)、[同:7403-7409](/work/1/SFC/tanab/izanagi/docs/decisions.md:7403)、[同:7744-7752](/work/1/SFC/tanab/izanagi/docs/decisions.md:7744)。これらを見ずにcommit topologyだけでcapを開けば明白な緩和になる。

ただし択Bの説明は強すぎる。D121は「10件すべてが機械検査可能」とは主張しておらず、D150は最終状態判定をcap-lift承認者である人間に置いている。したがって、**人間commitを最終権威としつつ、P6実認定記録・hash・対象revision・run conformanceを機械検査する証明書型**は、D121・D150・D156をsupersedeせず成立する。

逆にtopologyだけを証拠にする純粋な択Bなら、少なくとも次を逐語でsupersedeする必要がある。

- D121決定(7): 「**多世代開放 (`MAX_APPROVED_GENERATIONS > 1`) の前提条件を 10 件に固定する。**」
- D150決定(4): 「**申請側の宣言は入力にすぎず状態語を申請側に選ばせない。**」
- D156決定: 「**admission 結線まで含めた end-to-end calibration**」「**監査可能な独立検査者 attestation**」「**認定記録と失効照合**」。

さらに前 wave が数えていない第4の阻害要因がある。P6認定記録は `subject_revision_sha` に束縛され、申請対象revisionとの一致が必要である。[P6契約:156-177](/work/1/SFC/tanab/izanagi/output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md:156)。一方、裁定済みv2 topologyは「子commit Aでreceipt 1ファイルだけを追加する」とする。[design-v2.md:60-68](/work/1/SFC/tanab/izanagi/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:60)。G確定後に作る認定記録をGへ先回りして格納できず、Aもreceipt以外を追加できないため、現 topology には認定記録を置く場所がない。

## 2 第4の道

**第4の道D: exact-G認定を含む二段発効transaction**を提案する。

1. candidate `G` に、P6本体・calibration・admission結線と、receipt機構・manifest v3・全consumerを実装する。mainへはまだlandしない。
2. 独立検査者がexact `G` を認定する。
3. 人間が子commit `A` で、認定記録と、それをhash束縛するreceiptの**ちょうど2ファイル**をcreate-only追加する。両方の対象revisionは親 `G` とする。`G→A` を分割せず一つのland transactionとして入れる。

manifestは現行v2をexact `G=2` のまま残し、receipt-backed `3..10` は新しいv3だけに置く。現在の事前登録は「`G>=3`への延長を認めない」と明記しているため変更しない。[phase3-8c-preregistration.md:89-95](/work/1/SFC/tanab/izanagi/docs/phase3-8c-preregistration.md:89)。D882が固定した現行系列の証拠要求・評価器も維持できる。[decisions.md:32466-32483](/work/1/SFC/tanab/izanagi/docs/decisions.md:32466)。

この道で必要なsupersedeは、D121・D150・D156ではなく、v2の次の一文だけである。

> 人間が `G` を検分し、子 commit `A` で receipt 1 ファイルだけを追加する。

これを「認定記録とreceiptのexact 2ファイル」に狭く置換する。承認topologyが緩む範囲は追加可能pathが1件から2件になる点だけで、それ以外の変更・削除・merge・親違いは引き続き拒否する。正しさ条件やP1〜P10は緩めない。

**今mainへlandできるT-434の部分集合はない。** receiptだけはD841違反、consumerだけは到達不能、manifest v3だけは無受領証経路を作る。道Dではbranch上でGとAを完成させ、同じ変更単位としてlandするため、D841の「受領証だけを先に作らない」を満たす。[decisions.md:31735-31745](/work/1/SFC/tanab/izanagi/docs/decisions.md:31735)。

## 3 推奨

**択Dを推奨する。**

理由は3点である。

1. D150の人間判定とD156の実認定を両立し、既存の正しさ・承認条件をsupersedeしない。
2. exact-G認定記録をAでreceiptと同時追加するため、v2と択Aが残したrevision自己参照問題を解消できる。
3. 現行manifest v2と事前登録の `G=2` を保存し、receipt-backed拡張だけをv3へ隔離できる。

選ばない択:

- **択A:** P6を先に認定しても後続T-434変更で対象revisionが変わり認定が失効するため、提示順のままでは完了しない。
- **択B:** topologyだけで開く版はP6認定を迂回して承認ゲートを緩める。実認定を残す版は実質的に択Dである。
- **択C:** 実正例なしの恒久dead branchを増やし、既存の到達不能なLayer 3先例を重ねるだけである。[layer3_report.py:682-702](/work/1/SFC/tanab/izanagi/orchestrator/campaign/layer3_report.py:682)。

## 4 最初の一手

**ユーザーが道Dのtopologyを裁定し、記録waveがdecision fragmentを1件書く。**

書込み先は `docs/spool/decisions/<authored>-<wave>-1.md`。書式は[decisions fragment正本:3-18](/work/1/SFC/tanab/izanagi/docs/spool/decisions/README.md:3)に従う。裁定文には次の3点を明記する。

- [design-v2.md:64-66](/work/1/SFC/tanab/izanagi/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:64)の「receipt 1ファイルだけ」をsupersedeし、Aの許可diffを「認定記録+receiptのexact 2ファイル」とする。
- manifest v2のexact `G=2` は保存し、receipt-backed `3..10` は新manifest v3だけに認める。
- `G→A` を別々にmainへlandせず、実認定と正例確認後に一つのtransactionとしてlandする。

この裁定が無いままコードへ進むと、実装者は現行のreceipt-only topologyを独断で変更することになる。

## 5 費用

完了までの変更単位は**2単位**と見積もる。

1. **裁定・設計単位: 10^0ファイル。**
   decision/worklog fragmentとdesign-v4程度。認定記録を置くtopology、manifest v2/v3分岐、循環しないapplication preimage、Layer 3互換規則を確定する。

2. **実装・発効単位: 10^1ファイル、2commit構成。**
   candidate Gは数十ファイル規模。P6 handler・4 adapter・calibration・mutation、formal consumer、manifest v3、3入口、journal/report/completeness、Layer 3、runbook、schemaと各テストを含む。人間Aは認定記録とreceiptを中心とする1桁ファイルで、Gと同じland transactionへ入れる。

独立検査者によるexact-G accreditationは第2単位の途中に必要だが、別のコード変更単位とは数えていない。

pytest・buildは実行しておらず、以上は現在のmainに対する静的検査である。

## 総括

推奨は、P6と全consumerをcandidate Gへ揃え、独立認定後に人間Aが認定記録+receiptを同時発効する択D。
最大の懸念は、前 wave が見落とした「exact revision認定記録をreceipt-only Aでは配置できない」循環である。