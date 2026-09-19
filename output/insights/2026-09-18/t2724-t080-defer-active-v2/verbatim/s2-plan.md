## 前提の検算 (P1〜P5)

指定の必読fileはすべて読めた。以下は読取り・静的検算に基づく計画であり、編集・pytest・実走は行っていない。行番号は対象worktreeの現物に対するもの。以降、campaign配下を `C/`、tests配下を `T/` と略記する。

| 項目 | 検算結果と修正 |
|---|---|
| P1 | **そのままでは不足。** `C/s8b_ratified_freeze.py:1489` の `_enumeration_digest` は相対ファイル名集合だけのhash。同じ列挙集合なら別rootでも一致し、同名fileの内容変更も検出しない。検証rootの明示的な束縛を追加する。同一世代は既存 `resolve_active_generation` で再解決して照合する。 |
| P2 | **report保持案を推奨。** 自前再走は、v2のexact exemptionを使ったreportとv1 prefix除外のreportを混在させ、費用も増やす。full validationが得たreportを既存validated型へ保持する。この選択によりproductionはbriefの2 fileから**3 file**になる。これは依頼が明示したP2の型変更案による局所的な増分。 |
| P3 | **現状の最初の解決は「静的解決」ではない。** `driver:599,1318` → `migration:2284` → `:2350付近` は全走査を含む。履歴・静的結果を部分再利用する内部状態は存在しない。今回はfull再解決を採り、refusal文字列の削除による結果修復は行わない。 |
| P4 | **方針は可、集合の説明は誤り。** memo登録簿は `conftest:710` にあるとおり34関数／37 node。29 nodeはそのうち26関数。`_run` 以外の直接memo呼出し3関数も切替対象。残りは8関数／8 node。 |
| P5 | **固定SHA scratch方針は可。** `229982652` にofficial run_dirの5 file、G、budget inputがあり、候補X2は無いことを `git ls-tree` で確認。A/Xなしの実木と、合成批准済みfixtureを区別する。 |

その他の修正点：

- floorの5 nodeすべてが `_clone_committed_head_with_ccbench` を使うわけではない。1 nodeは `T/test_s8b_floor_campaign.py:2291`、残り4 nodeは `_protocol_binding_public_preflight:15609` 内の直接clone、`:15625` を通る。
- `_valid_g1` は `T/test_s8b_ratified_freeze.py:225` の説明どおり**structural placeholder**で、`load_ratified_freeze` を通らない。full validation正例には `build_production_emitter_g1:1002` が必要。
- G waveの407秒は **receipt解決全体1回の実測**。scan単体407秒と断定できない。
- 対象worktreeのHEADは指定どおり `24ede1d11`。ただし読取り時点のlocal mainは `386fc515c` へ前進していた。「local mainと同一」は現在では成立しない。差分はt2290側の文書・insightで、今回のproduction/test編集予定とは交差していない。

## 委譲 predicate の署名と置き場

推奨するAPI形は次のとおり。

```python
verify_receipt(*, root=ROOT, path=RECEIPT_REL, launch_validated=None)

static_gate_adapter(
    *, resolution, known_raw, holdout_raw, root=ROOT,
    launch_validated=None,
)

_verify_holdout_live_scan(
    root, holdout_doc, *,
    delegate_to=None,
    validation_head=None,
)

_holdout_layer2_delegation(
    *, root, validation_head, launch_validated,
) -> Optional[Mapping[str, object]]
```

`_holdout_layer2_delegation` は `C/t080_freeze_migration.py:2191` の直前に置く局所helperとする。新しいgate体系やtoken classは作らない。返却値は委譲可能な場合の検証済みreport、条件外は `None`。

`validation_head` は `verify_receipt:2289` が捕捉したHEAD、adapterでは `resolution.validation_head` を渡す。直接呼出しで省略された場合は `_capture_head(root)` を使う。これにより、receipt履歴検査と委譲predicateが異なるHEADを見たまま通過することを避ける。

発火条件は以下をすべて満たすこと。

1. `type(token) is LaunchValidatedFreeze`。
2. tokenが保持する検証rootと `Path(root).resolve()` が一致。
3. `token.activation_head == validation_head == _capture_head(root)`。
4. `token.ratified.activation_head` もそのHEADに一致。
5. 同じrootで `resolve_active_generation(root)` が成功し、返却値のHEAD・`generation_sha256`・`generation_number`・`generation_commit` がtokenのratified情報と一致。
6. `token.search_digest == _enumeration_digest(root)`。
7. reportの凍結docへの束縛検査を完了し、委譲判定の前後でHEAD・列挙digestが変わっていない。

同一世代の再解決には既存 `C/s8b_ratified_freeze.py:1317` を使う。実際にfull validationも `_active_chain_exempt_exact:2983` 内で世代・HEAD・導入commitを再照合している。型とHEADだけに依存する案より、同名namespace fileのdirty化も検出できる。一方、履歴走査は追加される。`load_ratified_freeze` 全体を再実行する必要はない。

report保持の変更は以下に限定する。

- `C/s8b_ratified_freeze.py:816` の `LaunchValidatedFreeze` に `validation_root: Path` と `search_report: Mapping` を追加。
- `:835` の `ReverifiedFreeze` にも同じfieldを追加し、共通の `result_type` 構築契約を維持する。ただしexact type条件により委譲には使えない。
- `_launch_validate:3525–3575` で、**完全一致・陽性対照・artifact再捕捉が成功した後**に、resolved rootとdeep-freezeしたreportを返す。
- 読み込んだ全fileのtextは保持しない。保持するのは既存search reportのみ。
- `_enumeration_digest`、`EXCLUDED_PATHS`、`exempt_exact`導出、完全一致検査は変更しない。

`_verify_holdout_live_scan:2202–2231` の以下の比較は、委譲時もそのまま実行する。

- rr80/rr20の両集合
- `match_convention`
- 各 `candidate_id`
- 各 `unknownness_check.expressions`

条件外では従来の `search_repository(root)` と `_assert_search_pass(report)` を実行する。委譲時だけ、full validationで検査済みのreportを使い、最後のzero-hit要求を行わない。predicateを評価できない場合も委譲不成立として扱い、通常検査へ戻す。通常検査の例外を握り潰さない。

refusalは既存の正規化を維持する。

```text
holdout-freeze-verify: [holdout.unknownness_layer2] …
```

`static_gate_adapter:2490` のindependent列にも同じhelper・同じtoken・同じHEAD条件を適用する。doc束縛違反をadapter経由でも拒否する。

`ReceiptResolution`、observation、`held_checks`には新fieldを加えない。

- observationは `:2252` の17項目と既存epoch schemaを維持する。
- 委譲は検査holdではないため、`held_checks`へ記録すると意味が誤る。
- 委譲根拠は呼出し中のvalidated objectが保持する。実証記録にはroot、HEAD、世代hash、digest、委譲成否を残すが、耐久campaign schemaは広げない。

## driver の呼出し順

`C/s8b_oracle_driver.py:166` のresolverへ `launch_validated=None` を追加し、指定時だけmigrationへ渡す。tokenなしの既存呼出しは `verify_receipt(root=root)` の形を維持する。既存のroot-only spyやmemo endpointへ不要なkeywordを流さない。

公開 `gate_check:587` は次の順序とする。

1. 現行どおり委譲なしのreceipt全検証。
2. freeze読込み・v1/v2判定。
3. v1は現在の `:626付近` からcoreへ直行する。
4. v2は既存loader・`launch_validate:656` を通す。
5. 成功後、同じrootとvalidated objectでreceiptをfull再解決。
6. 新resolutionと同じvalidated objectをcoreへ渡す。

loaderまたはlaunch失敗時は、最初のresolutionのrefusalsを既存factoryで集約する。成功時の再解決も静的検査全部を再実行するので、層2以外のrefusalは消えない。先のrefusal文字列から層2だけを除去する方式は採らない。

`run_block:1280` も同じ方針とする。

- `:1318` の初回receipt解決を維持。
- `:1338` のlaunch成功後、gateに入る前に委譲付きfull再解決。
- `:1393付近` の `_gate_check_validated`、`:1411` の `_campaign_t080_value` にそのresolutionを渡す。
- `:1527` のcampaign-start前再解決にも同じvalidated objectを渡す。
- `_t080_epoch_identity:220` の4要素は変更しない。委譲の有無はepochへ追加しない。比較対象の両resolutionを同じ委譲条件で検証する。

`_gate_check_core:409–500` は既にexact typeを要求し、validatedのdocumentを使う。`_t080_adapter_refusals:235` にtokenを転送する引数を加え、`:297付近` のadapter呼出しへ渡す。v2のhashは通常v1 receipt artifactと異なるためadapterは発火しないが、独立API経路の条件を揃える。

**v1 freeze pathの `gate-check` では委譲しない。** active v2が存在していても、v1経路はlaunchを実行しない。chainを持つ木で従来のv1 P3を実行すると、層2とv1 verifyの拒否は残る。

費用は次のとおり。正常なissued receiptを前提とする。

| 方式 | 公開v2 gateのscan | campaign-startまでのrun_blockのscan | receipt全検証 |
|---|---:|---:|---:|
| P2自前再走＋P3再解決 | 3回 | 4回 | gate 2回／run 3回 |
| **report保持案** | **2回** | **2回** | **gate 2回／run 3回** |

report保持案でも履歴・closure検査は再実行される。過去の `driver test:2958` の1845 subprocess／22.4秒は旧実測であり、現在の回数・時間として流用しない。追加の世代再解決と列挙時間もauthor段で区分計測する。

## 境界 test の設計

新規test moduleは作らず、既存fileへ追加する。下表の名前は新設候補。

| 配置・関数名 | fixture・期待 |
|---|---|
| `T/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt` | receipt発行済み合成repoにfull emitter由来G/A/Xを積む。実 `load_ratified_freeze` → 実 `launch_validate` → 実 `verify_receipt`。tokenなしは層2でinvalid、tokenありはactive-valid、refusals空。 |
| 同 `::test_t080_unactivated_chain_hit_is_invalid` | R後、GまででA/Xなし。合成official hitが存在し、exact層2refusalを確認。 |
| 同 `::test_t080_failed_launch_preserves_receipt_refusal` | active fixtureへclosure外の合成hitを追加。実launchが `closure-hit-mismatch`、公開gateがlaunch refusalとreceipt層2refusalの両方を保持。 |
| `T/test_t080_freeze_migration.py::test_layer2_delegation_rejects_wrong_activation_head` | 本物のtokenからouter `activation_head` だけを変更した攻撃入力。委譲せずzero-hit拒否。 |
| 同 `::test_layer2_delegation_rejects_foreign_root` | 本物のtokenを別rootへ渡す。異なる列挙集合に加え、同じHEAD・同じファイル名集合のcloneでも拒否する2ケース。 |
| 同 `::test_layer2_delegation_rejects_enumeration_drift` | 同一root・HEADでtoken取得後にgit-visibleな合成hit fileを追加。digest不一致により通常検査へ戻り拒否。 |
| 同 `::test_layer2_delegation_rejects_nonlaunch_type` | `ReverifiedFreeze`、duck型、subclassを各々拒否。 |
| 同 `::test_delegated_scan_keeps_frozen_document_bindings` | 本物のtokenとreportを使い、入力doc側のexpressions、match convention、候補ID、候補集合を1項目ずつ変更。層2reasonで拒否。 |
| 同 `::test_static_adapter_keeps_delegated_document_bindings` | adapterのindependent列でも同じ拒否が出ることを固定。 |
| `T/test_s8b_ratified_freeze.py::test_launch_token_retains_immutable_scan_and_root` | full emitter fixtureから得たtokenのroot、digest、report内容、不変性を確認。historical型はadmissionへ昇格しない。 |
| `T/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt` | gate後、campaign-start前にreceiptを改変・削除。epoch拒否、campaign WAL・evaluate不発火。 |
| 同 `::test_v1_gate_does_not_delegate_with_active_v2` | 同じ批准済みfixtureでもv1 path指定では従来拒否。 |

fixture統合の順序：

1. `T/test_s8b_oracle_driver.py:1364` のstub-free builderで、hitを持たないbasisとRを先に作る。draft時のzero-hitを迂回しない。
2. `T/test_s8b_ratified_freeze.py:642,1002` のemitterを、既存repoへ必要な追加材料を載せる部分に限って局所整理する。既存 `.git`、receipt履歴、ccbenchを作り直さない。
3. calibration、protocol、selectorの合成材料を準備し、cleanな段階で実official preflightとcertificate発行を通す。
4. emitterの結果をGへ、合成の人間trailerをA/Xへ積む。これはtmp fixture内だけ。
5. `migration:1365–1410` のclosureはbasis blobを照合するため、後段G追加そのものと矛盾しない。ただしcurrent ccbench検査とsource再構成の整合は実証が必要。
6. emitterの固定build/measure seamは既存用途の範囲で使用する。今回検査する `search_repository`、`_assert_search_pass`、`launch_validate` は置換しない。

`_repo_with_schema_valid_receipt:322` と `_patch_full_gate_to_pass:383` は履歴単体test用であり、全検証正例の証拠に使わない。既存 `test_live_scan_is_bound…:529` もsearchを置換しているため、今回のDW-O14証拠には数えない。

統合fixtureを成立させられない場合は、実full validationを使うpredicate境界と、stub-free receipt／driver経路のtestを分離して原因を特定する。ただし分離testだけで「full receiptがactive-validになる正例を実証済み」とは報告しない。必要な接続正例が成立するまで着地条件は未達とする。

費用の仮見積りは、共有base構築20〜60秒、境界cloneごとの検査1〜10秒を初期予算とする。これは未実測。根拠にできる既存値はoutput copyの15〜22秒という旧記録であり、現在の全fixture時間ではない。完全なbaseを各paramで再生成せず、既存の隔離・clone支援を使う。

## 4 経路の切り離し

削除集合は走査結果と無関係に宣言する。

```text
S(H) =
  Hが持つ output/env/pegasus/calibration/s8b-floor-official/ 配下の全path
  ∪ {output/s8b-freeze-candidates/holdout_freeze.v2.g1.json} ∩ paths(H)
```

候補側は `C/s8b_holdout_freeze.py:49` の `V2_CANDIDATE_REL` に対応する**exact file**。候補directory全体は削除しない。briefの「候補配下」という略記をprefix全削除へ解釈すると、必須条件に反する。

**(i) T-080 output複製：10 node**

- `T/test_s8b_oracle_driver.py:794` の `_git_visible_output_paths` はGit-visible集合の正確な列挙として維持する。
- `:827` のcopy側で、現行receipt/draft除外に `S` のGit-visible部分を加える。
- copy対象のancestor集合も、削除後の集合から作る。
- `:1660–1714` のcopy契約testへ、official配下、候補exact file、候補directory内の無関係fileを追加する。
- 生のGit-visible集合とproduction列挙の一致は残す。copy後の集合について、差分が「receipt・draft・宣言S」だけで、残存fileのbytesが同一であることを独立に検査する。
- `:1714` の欠落tracked file拒否は残す。
- `:1284` の6関数／11 node consumer pinは、既存の10件＋g7が引き続き同じhelperを使う限り不変。新境界testが同helperを直接使う場合は、その純増を明示追随する。

chain無しでは追加削除集合が空。`229982652` ではofficialの5 fileだけが追加削除され、Gとbudget inputは残る。draftの実zero-hit検査を残したまま、今回の既知hit混入経路を除去できる。

**(ii) floor clone：5 node**

- `T/test_s8b_floor_campaign.py:2291` と `:15625` の**両clone経路**に、同じ宣言Sのtracked pathを `git rm`＋commitで外す局所helperを適用する。
- 実装形は `:2332` の `_remove_post_seal_floor_protocols_from_replay` に合わせる。集合が空ならcommitしない。
- clone作成直後のsource HEAD、gitlink変更commit、clean-base commitを個別に捕捉する。
- `:12118付近` の `HEAD^ == source_head` を単に `HEAD^^` に変えない。gitlink commitのparentとdiffは従来どおりexact、追加clean-base commitのparentと `D` 集合を別にexact検査する。Sが空の場合も扱う。
- 残存tree entryのmode/OIDを前後比較し、変更が宣言削除だけであることを確認する。
- `:15790–15844` のaccepts、hash drift拒否文字列、`bypass_drift_gate=True` の対照は維持する。

新負例は同fileに `test_clean_scan_rejects_synthetic_chain_artifacts` を追加し、officialだけ／候補だけ／両方をparametrizeする。clean cloneへ `s8b_v2_freeze_fixture._holdout_hit_text` 由来の合成bytesを置き、実 `clean_scan_digest` の拒否を検査する。chain/Gの実bytesは使わない。対照として無害なbytesならclean scanが通ることも確認する。

**(iii) memo依存：29 node＝26関数**

- `_run:2951` の既定側を `_never_issued_resolution:360` の合成値へ切り替える。
- 直接memoを使う以下も同様に切り替える：`:3345` のCLI欠落root test、`:5160` のvalidated object再利用test、`:5240` のmanifest一回検証test。
- `memo_receipt=False` は既存opt-outの入口として残す。名前の整理は今回の必要差分に含めない。
- `conftest:712` とserialization golden `:502` から26関数を除き、**8関数／8 node**へ更新する。
- 残すdriver側4関数は `test_real_freeze_gate_lists_floor_and_budget_null`、`test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`、`test_nonnull_floor_without_active_generation_is_refused`、`test_active_resolution_and_manifest_structure_refusals_are_aggregated`。
- driftguard側4関数はすべて残す。growth holdも変更しない。
- `T/test_real_repo_serialization.py:2853` は現状 `_run` 呼出しをすべてmemo consumerと数える。既定 `_run` はconsumerでなくなるため、直接memo呼出しを数え、`memo_receipt=False` は引き続きopt-outとして検出するよう追随する。
- `:2906–2907` の34／37を8／8へ更新する。これは期待値の緩和ではなく実consumer集合の変更に対するexact pin追随。

静的AST照合では、除く26関数と `_REAL_REPO_NODE_INVENTORY` の積集合は**空**だった。したがって29 node分をそこから削除する変更は不要。floorのclone consumerや新統合fixtureの実root読取りは引き続き分類対象である。

prewarmの判定は `conftest:913–930` の既存selected-consumer条件を維持する。残存consumer選択時はprewarmし、合成化した29 nodeだけを選んだ場合はreceipt prewarmを起動しないことを既存barrier testで固定する。

**(iv) g7：1 node**

`T/test_s8b_oracle_driver.py:4753` は(i)のclean fixtureを使用し続ける。`:4817付近` のexact集合を維持する。

- held：floor-null＋budget-null。
- hold解除対照：known pin拒否＋generator拒否＋floor-null＋budget-null。
- sentinel対照：sentinelのholdout refusal＋floor-null＋budget-null。

chain由来のscan拒否を期待集合へ追加しない。generator tamper拒否を消す変異は引き続きexact集合で捕捉する。

以上は両木で既知4経路が解消する静的根拠であり、両木の緑を意味しない。

## 変異 matrix の候補

| 変異 | 捕捉するtest・必須観測 |
|---|---|
| m1：C2-4を `expected <= current` に緩和 | `test_t080_failed_launch_preserves_receipt_refusal`。closure外の実hitがlaunchを通ってしまい失敗する。既存 `test_undeclared_hit_outside_closure_rejected` も併走。 |
| m2：receipt refusalを集約しない／invalidを受理 | 新 `test_t080_active_v2_preserves_nonlayer2_receipt_refusal`。批准・launchが有効でもR trailer不正等を単独投入し、公開gate拒否と無副作用を要求。factoryとcampaign-valueの変異を別々に実行する。 |
| m3：承認前に委譲 | `test_t080_unactivated_chain_hit_is_invalid`。Gまでの実fixtureでinvalidを要求。 |
| m4：検索規約照合を削除 | `test_delegated_scan_keeps_frozen_document_bindings` とadapter版。expressions、match convention等を個別paramにする。 |
| m5：campaign-start前再検査を削除 | 新delegated campaign-start test＋既存 `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4:3677`。拒否理由とWAL未発行まで要求。 |
| m6：tokenのactivation HEAD比較を削除 | `test_layer2_delegation_rejects_wrong_activation_head`。outer fieldだけ異なるtokenを使い、その比較を単独に攻撃する。 |
| m7：列挙digest比較を削除 | `test_layer2_delegation_rejects_enumeration_drift`。同じroot・HEADで新しいhit fileを追加し、root/世代比較だけでは落ちない入力にする。 |
| m8：test側でsearch拒否を外す | 未発効負例と `test_clean_scan_rejects_synthetic_chain_artifacts[official/candidate/both]` が失敗することを確認。 |

完全一致を逆方向の包含へ変える変異は別mutationとして扱う。既存の「消失hit」testはsearchを置換するものがあるため、それを今回のDW-O14実証に流用しない。

各mutationは、baseline成功→単一変異→意図したassertionで失敗→復元後成功を記録する。constructor引数不足、fixture構築失敗、timeoutはkillとして数えない。冗長な比較により同じ拒否が残る変異も、kill済みと粉飾しない。

## runbook 段階別 preflight の文案

`docs/phase3-8b-restart-runbook.md:122–144` は、単体v1 verifyの歴史的hash不一致の説明を残し、「生死の判定は次の1本」以降を次の趣旨へ置き換える。

> oracle preflightの期待は、checkoutにchainがあるか、active v2が発効しているか、指定したfreeze pathがv1かv2かで異なる。
> chainを持たない基準木のv1 gate-checkは、rc=2、floor-nullとbudget-nullの2件だけという実測がある。
> X1′＋Gを持ちA/Xがない木のv1 gate-checkは、rc=2、receiptの未知性層2、v1 verifyのlive scan、floor-null、budget-nullの4件という実測がある。既知のofficial成果物hitによるこの2件を、artifact破損とは判定しない。
> A/X後はactive v2の世代fileを指定してgate-checkする。同一root・HEAD・世代でfull launch validationが成功すれば、receipt層2の重複したzero-hit要求は委譲される。これは設計上の期待であり、productionでの発効後実測はまだない。その他の拒否条件は独立に評価する。

旧文「`holdout-freeze-verify:` が混ざったら本物の破損」は削除し、次に限定する。

> 各段階の記録済みexact refusal集合から外れた場合は、次段へ進まず原因を調べる。prefixだけで破損と断定しない。既知の層2hitと、artifact bytes・検索規約・closure等の不一致をreasonと対象pathで区別する。

§2 `:156` のP3行は「§1.1の段階別条件と照合」へ変更し、期待を次の3行で示す。

| 段階 | freeze指定・期待 |
|---|---|
| chain無し基準木 | v1 path。rc=2、拒否2件exact。既存実測。 |
| chain＋G、A/X前 | v1 path。rc=2、既知4件exact。G wave実測。 |
| A/X後 | active v2世代path。receipt層2・floor-null・budget-nullが解消する設計期待。production未実測。全gateが成立した場合のみallowed。 |

v1 pathを指定し続けた場合には委譲されないことを併記する。W-4 specやmanifestの独立した未成立を、A/Xだけで解消すると書かない。

## 分割と所有

**Codex author 1本を推奨する。** 理由は、root/report field追加、full receipt＋emitter統合fixture、driverの再解決回数が同じ変更で接続するため。親は文書・統合・実測記録・commitを担当する。

2本に分けるなら、並列ではなくAPIとfixture契約を固定した直列とする。

| 所有 | file |
|---|---|
| A | production3 file、`test_t080_freeze_migration.py`、`test_s8b_ratified_freeze.py`、型field追加だけが必要な周辺test |
| B | `test_s8b_oracle_driver.py`、`test_s8b_floor_campaign.py`、conftest、serialization、driver行番号pin |
| 親 | runbook、decisions/worklog fragment、insight、受入記録 |

Aのemitter変更とBのT-080 builder変更を接続する必要があるため、authorを2本にする利益は小さい。同一fileを2子へ渡さない。

型の直接constructorは現物検索で7箇所。

- driver test：`:2835,2847,4112,4993`
- `test_s8b_oracle_report.py:477`
- `test_s8b_gate_core_exact_launch_validated.py:50`
- `test_s8b_holdout_admission.py:547`

偽tokenは委譲不能なroot/reportを明示する。新fieldに受理側のdefaultを付けて互換化しない。

新規test fileは作らない。`T/test_plain_runner_coverage.py:64` はtests READMEのpytest-only allowlistを検査するため、新file追加は別の追随を生む。

`T/test_ccbench_spawn_sites.py:3382` はdriverのevaluate sinkを**1788行**でpinしている。driver上部の変更だけでもずれるため、同じsinkであることを確認して新行番号へ追随する。allowlist拡大やsink分類の緩和は行わない。

## 受入で赤になりうる test

直接・間接consumerを次の範囲まで確認する。

| 起点 | 直接consumer | さらに影響する検査 |
|---|---|---|
| migrationのAPI・層2 | driver、known axes verifier、holdout verifier、receipt memo | `test_t080_freeze_migration`、`test_s1_known_axes_freeze`、`test_s1_measurement_freeze`、`test_s8b_holdout_freeze`、driftguards |
| driver呼出し順 | 公開gate、run_block、report側driver参照 | `test_s8b_oracle_driver`、`test_s8b_gate_core_exact_launch_validated`、`test_s8b_oracle_report`、`test_s8b_oracle_artifacts` |
| validated型・emitter fixture | launch/reverify、holdout admission、materialization | `test_s8b_ratified_freeze`、`test_s8b_ratified_verify`、`test_s8b_holdout_admission`、`test_s8b_materialization` |
| oracle/floor test helper | driftguards、serializationのimport・AST検査 | consumer集合、default collection、tmp境界、resource分類golden |
| 行追加・import追加 | 静的sink・import検査 | `test_ccbench_spawn_sites`、`test_official_perf_closure`、`test_campaign_import_invariant` |

特に予測できる赤：

- `test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result:3636` の `call_count == 2`。full再解決採用後は成功経路3回をexactに固定する。名前と説明も実際の契約に合わせる。
- epoch drift test `:3677` のside effect列を「初回・launch後・campaign-start直前」に対応させる。opt-outは維持し、最後の再検査を抜く変異を必ず殺す。
- driver `:3550付近` のfactory／return AST検査。新しいreturnを追加しない実装なら既存15 refusal-return pinを維持できる。
- migration `:563付近` の例外正規化testのroot-only lambda。引数変更で生じたTypeErrorを意図したscan拒否と誤認しないよう追随する。
- serialization `:2853,2902` のconsumer導出、34／37 count、代表consumerを選ぶbarrier test。
- conftestの新しい統合fixture／clone負例の実resource分類と、serialization `:52,212,278,288` の対応golden。
- driftguardのmemo4件、root拒否、cache往復。`ReceiptResolution`のshapeを維持するためwire format変更は不要。
- `test_frozen_artifacts.py:236` の23件pinは変更しない。凍結bytesを触らないため期待差分はない。
- `test_plain_runner_coverage` は新moduleなしならallowlist変更不要。

依頼にある「B-4静的inventoryのmodule数pin」は、その名称に一致する現物を今回の検索では特定できなかった。見つかった `test_s8c_preregistration_predicates.py:2800` の65 moduleは合成reachability graphのtestであり、今回のproduction module数pinとは断定しない。未特定のpinを想像して変更する計画にはしない。

`tools/check_docs.py` とtools配下の検索では、runbook名・「拒否2件exact」・旧破損文のliteral pinは見つからなかった。実装後の `check_docs.py` は必要だが、「既知literal pinを変更する」とは扱わない。

焦点走はG waveの既存6 fileにmigrationを加え、さらに上記の型constructor、serialization、driftguard、sink検査を実行する。その後、chain無し／有り両木の焦点走と通常受入を行う。全て既存 `tools/run_tests.py` 経由とし、このplan段での未実行を明記する。

## fragment の骨格

decisions fragmentは、例えば次の名前・frontmatterを使う。

```text
docs/spool/decisions/2026-09-18-dev-wave-t2724-t080-defer-active-v2-1.md

schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2724-t080-defer-active-v2
seq: 1
```

本文のD slug案は `t080-layer2-delegation-bound-to-live-validation`。

記録する内容：

- 裁定A-3を実装する具体的なpredicate署名。
- exact型、resolved root、receipt検証HEAD、active世代再解決、列挙digest、凍結doc束縛。
- reportを既存validated型へ保持する理由とproduction3 fileへの増分。
- 維持する履歴・静的検査・epoch・refusal集約・invalid拒否。
- 未発効、別root、別HEAD、別型、列挙変化、doc束縛違反の拒否。
- production正例は人間A/X後にしか到達しないこと。
- 自前scanによる重複費用、refusalの部分削除、無条件免除を採らない理由。
- 名前集合digestと内容TOCTOUの保証限界。

G waveのslugを `{{D:…}}` 参照しない。裁定控えの日付と保存commit `229982652` を通常の参照として記す。同waveのworklogからのみ新Dのplaceholderを参照する。

worklog fragmentは `docs/spool/worklog/README.md` のH2「本文」「次の一手差分」の2節契約に従う。骨格は次の内容。

- 本文：委任済み裁定、P1〜P5との差、両木の固定SHA、実／合成の区別、mutationの実際の失敗箇所、残余。
- T-2724：整合実装の到達点を**更新**し、G/X2取り込み、人間A/X、W-4/W-5を残す。全体完了にしない。
- T-2776：4経路の是正・両木受入・mutation実証が揃った時点で、現台帳のtask scopeと照合して完了または更新とする。未実測の段階で完了宣言しない。
- `base:` はland先mainの現itemから取得する。今回の開始HEADに固定したdigestを使い回さない。

canonical台帳は編集せず、既存の `check_docs.py` とspool dry-runで確認する。

## リスクと未確定点

1. **report再利用のTOCTOU。** digestは内容hashではない。別rootは追加fieldで拒否できるが、同名fileの内容交換は検出できない。token取得からcampaign-startまでの再利用にはこの窓が残り、receiptの再検証だけでv2全artifactを再検証したとは言えない。既存のsingle-tenant前提を明示し、新しい内容不変保証を主張しない。

2. **一時的な列挙変化。** 前後digestは、間にfileが増えて元へ戻った事象を必ず検出するものではない。追加・削除が比較時点に残れば拒否する。委譲直前のdigest不一致はzero-hit経路へ戻るため、予期しない出力fileの生成が性能・可用性に影響する。

3. **ignored領域。** `C/s8b_holdout_freeze.py:370` は親repoのtracked regular fileと非ignored untracked regular file、ccbenchのtracked regular fileを列挙する。親のignored untracked、ccbenchのuntracked、symlink等は同じ保証に含まれない。`output/s8b-freeze` は列挙digestに入り、v1 searchで後からprefix除外される。これらの集合は変えない。

4. **合成fixtureの接続。** `_valid_g1` の流用では足りない。full emitterとT-080履歴の接続が最大の実装不確定点。検査をstubしてactive-validを作る解決は禁止する。

5. **費用。** 推奨案はrun_blockのfull scanを2回に抑えるが、receipt履歴全検証は3回。407秒を3倍した値を予測値にせず、履歴・scan・世代再解決を分けて計測する。

6. **scratch実測木。** author完了tipから、例としてbranch `scratch-t2724-t080-defer-active-v2-chain`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/scratch-t2724-t080-defer-active-v2-chain` を作り、`22998265212c43a6b0f42051d7bf1b49735f77e9` を固定SHAでmergeする。scratchはlandしない。X2は無いため候補側の拒否は合成負例で補う。git操作は各worktreeをcwdとして単一commandで行い、親guardを迂回しない。

7. **並行wave。** `docs/pegasus-runbook.md` は読取りのみで、t2627の編集fileと今回の予定集合は交差しない。ただし他waveの未commit状態まで確認したとは主張しない。local mainが既に前進しているため、統合時には固定SHAを捕捉し直し、spool baseも再確認する。

## 総括

推奨は、**rootと実scan reportを既存validated型に保持し、厳密なpredicateの下で層2だけを委譲する局所実装**。productionは3 fileとなる。receipt全検証・epoch・refusal集約は維持し、成功経路では履歴再検査3回、full scan2回を見込む。

test側は宣言した削除集合だけでfixtureを清浄化し、floorの2つのclone入口、memoの26関数／29 node、g7のexact集合を扱う。Codex author 1本を推奨する。着地条件は、合成批准済み正例、全負例、mutation検出、chain無し／有り両木の実受入である。今回は静的計画のみで、それらの成功は未実測。
