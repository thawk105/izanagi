## 総括

**段4へ返すべき衝突があります。P1 の解釈だけで実装へ進める案には反対です。**

主因は、D1737 が却下した「floor 系を残したまま cache/hydrate を追加する」状態を、本案がそのまま作ることです。T-548 の逐語裁定にも「T-585 と同一 wave で閉じる」とあり、親 brief の移行先送りとは一致しません。

また、使用直前の検証範囲と変異の帰属に不足があります。一方、現行 golden の更新自体を歴史改竄とする根拠はありません。

以下、repo 内のパスは指定 worktree 相対、`plan` は指定 `stage2-plan.md`、`D200/D1737/D115/裁定` は指定逐語ファイルを指します。静的読解のみで、編集・commit・テストは実行していません。

## 1. 規律 2 の弱体化

**A1：hydrate の検証結果を、job 使用時まで保証された性質として扱っている。**

`_verify_source` は index 隠蔽 bit、origin、shallow、ignored artifact を検査します。しかし P3 S4 の使用直前検査は directory・HEAD・porcelain だけです。hydrate 後に `assume-unchanged` を設定して tracked source を変更するケースは、後者の検査では保証できません。origin 差替えや ignored artifact 追加も同様です。

これは現行 floor の最低線より弱くなると確認できた回帰ではありません。**新入口が保証する受理集合と、job が実際に受理する集合の不一致**です。plan の「hydrate 後から使用時までの変更を検出する」は範囲を限定すべきです。是正するなら、新しい2依存の引渡し箇所だけで既存検証を適用してください。

根拠：`plan:204`、`tools/pegasus/fetch_third_party.py:400,410,418`、`tools/pegasus/p3_s4_loop_pegasus.sh:409,436`。  
影響：検証後に変わった source からビルドしても試行が先へ進み、調達時の pin 記録と実際のビルド入力が乖離しうる。

**A2：`submission._dependency()` を HEAD・clean の保証と数えてはいけない。**

この関数は expected commit と tree の Git object を解決するだけで、checkout の HEAD と dirty を検査しません。末端 symlink は拒否します。したがって、これを「同等検査」として新経路の不足を埋めることはできません。

根拠：`orchestrator/qualification/submission.py:94`。  
影響：toolchain 記録の commit/tree が正しくても、使用した working tree の同一性は別途未保証になる。

## 2. 恒真化・帰属不成立の変異

**A3：不正 pin 変異は、新列挙関数の検出力に帰属しない可能性が高い。**

既存 `main()` は先に `_load_policy()` を呼び、そこで `_dependency_pins()` が40桁形式と共有 pin の一致を検査します。共有 `gflags_expected_head` だけを壊せば一致検査が、両方を不正形式へ変えても形式検査が先に拒否します。新入口の検査を削っても、その変異は赤のままです。

根拠：`plan:208`、`tools/pegasus/fetch_third_party.py:74,727`、`orchestrator/campaign/silo_ladder_rung1.py:850`。  
影響：新しい gate が無効でも変異 matrix が成功し、新経路の拒否能力を過大評価する。

**A4：「cache の ignored artifact が hydrate に混入しない」は、ignored 拒否 gate の証明ではない。**

fresh clone はそもそも untracked/ignored file を運びません。既存テスト同様に cache へ置くだけなら、hydrate 側の `reject_ignored=True` を削っても通ります。この候補は「コピーでなく clone する」検査には有効ですが、ignored 拒否の検査とは分ける必要があります。

根拠：`orchestrator/tests/test_pegasus_thirdparty_fetch.py:245`、`tools/pegasus/fetch_third_party.py:633,660,676`。  
影響：既存 staging に混入した artifact の受理を見逃したまま、拒否検査を実証済みと記録してしまう。

**A5：job の拒否変異を fetch/hydrate から通すと、job に到達しない。**

HEAD 不一致・dirty・symlink を事前に作って新経路全体を走らせれば、通常は cache/hydrate が先に拒否します。job の検査を証明する変異は、正常 hydrate 後の引渡し境界へ投入する必要があります。また、固定された2名前から列挙する実装なら「列挙名がその2名前である」は構成上成立し、独立した拒否 gate ではありません。

根拠：`plan:40,206`、`tools/pegasus/fetch_third_party.py:613,620`、`tools/pegasus/p3_s4_loop_pegasus.sh:409`。  
影響：job 側の検査欠落が、上流の赤によって隠れる。

## 3. 凍結と歴史の改竄

**A6：独立 golden の方針は成立するが、実装へ渡せる具体性がまだない。**

plan は URL key を挙げるだけで、追加する URL の exact 値・配置・空白・改行を確定していません。「追加内容から独立に算出する」だけでは、実装子が生成した bytes を後から親が追認する手順になりえます。

必要なのは、実装前に親が次を固定することです。

1. 変更前 bytes とその SHA。
2. URL の exact 値、および適用箇所が一意な byte 単位の変更。
3. その変更を変更前 bytes に適用して算出した期待 SHA。
4. 実装後 bytes と期待 SHA の照合。

編集後ファイルからの hash は照合用には使えますが、期待値の導出元にしてはいけません。

根拠：`plan:39,164`、`D200:31`、`orchestrator/tests/pegasus_policy_expected_goldens.py:5`。  
影響：手順を省略すると、誤った URL や無関係な変更まで「承認された現行 bytes」として固定される。

歴史定数と evidence binding を維持する限り、現行 golden の変更は歴史改竄ではありません。更新してはいけないのは `EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256` と過去成果物の binding です。

根拠：`D200:25,62`、`orchestrator/tests/pegasus_policy_expected_goldens.py:8`。  
影響：歴史側まで更新すると、過去の certified 証拠が実際には使用していない policy を参照する。

## 4. pin 閉包の取りこぼし

**追加の「現行 bytes 変更だけで必ず赤になる第3 node」は、この静的調査では特定できませんでした。閉包完了とは判定しません。**

値側の現行 SHA・歴史 SHA、定数名、key 側の policy identity、行番号表記、dataclass hash を追いました。直接 golden の読み手は plan の2 node と一致します。ただし、次は別の影響面です。

- **T-126 の既存 preimage 継続。** 記録 commit の policy と live policy の辞書全体を比較するため、URL 追加も不一致になります。新規 identity の変化だけではありません。  
  根拠：`orchestrator/qualification/identity.py:166`、`orchestrator/qualification/contract.py:76,491`。  
  影響：旧 preimage を新 checkout で継続する試行が拒否される。「名指し外 consumer の受理・拒否不変」とは両立しない範囲がある。

- **plan にない現行 SHA の歴史的保有者。** T-316 の保存済み receipt に現行 SHA が存在します。今回追ったテストから、これが live policy と比較されて赤になるとは確認できませんでした。更新対象に含めてはいけません。  
  根拠：`output/env/pegasus/t316-sandbox-backend/0:999027.nqsv/receipt.json:41`。  
  影響：一括置換すると、過去 probe の実行入力の参照を改竄する。

- **dataclass hash は今回の直接連鎖ではない。** `EnvContract` の hash は field の canonical JSON から作られ、共有 policy bytes を直接取り込みません。登録済み calibration を変更しない限り、この経路を理由に golden を更新する根拠はありません。  
  根拠：`orchestrator/campaign/env_contract.py:168,260`。  
  影響：不要な更新は、既存 calibration・環境世代の参照を変更する。

行番号 pin の検索結果は0件でしたが、間接的な行抽出まで不存在を証明したものではありません。

## 5. 既裁定の逐語との整合

**A7：本案は D1737 の明示的却下に当たります。**

> 「floor 系が既に policy 経由で運んでおり、同じ依存を 2 つの経路で pin することになる。」

この理由は「pin 定数を2箇所へ複製する」と限定していません。floor 系を残し、P3 S4 だけ hydrate へ移す本案は、まさに記述された併存状態です。pin 値の単一正本化では解消しません。

加えて T-548 の裁定は、

> 「[T-585] … と同じ面なので同一 wave で閉じる。」

です。親 brief と plan が T-585 を後続へ残すことは、この文言から導けません。段階移行を許す再裁定、または同一 wave の閉じ方の修正が必要です。

根拠：`D1737:28`、`裁定:11`、`plan:5,126,224`。  
影響：新経路完成後も floor/certify 側の機体固有 locator 依存が残り、共通調達への移行完了を名乗ると成果物の到達範囲を誤る。

**D200 の hydrate 却下は、恒久禁止ではありません。**

> 「復旧の最小変更を超える。別タスクへ送る。」

T-548 はこの別タスクに相当する内容です。ただし、歴史 binding 書換えの却下は引き続き適用されます。

根拠：`D200:58`。  
影響：調達経路追加は可能でも、過去 certified 証拠の再 binding を付随作業にできない。

**D115 の却下と、P3 S4 結線案は同一ではありません。**

> 「索引と gate だけを作り consumer を付け替えない」

本案は1本の live consumer を移すので、この却下そのものには当たりません。ただし、全体の構造問題を解消したとは言えません。案 X は共有値の全面移設でもなく、歴史 evidence の再 binding も予定していません。

根拠：`D115:54`、`plan:80`。  
影響：P3 S4 の供給改善は成立しうるが、他 consumer の locator 依存は残る。

## 6. 受理集合が効く層の被覆

| 層 | plan の被覆 | 判定 |
|---|---|---|
| fetch | 新列挙・新入口 | 対象内。ただし不正 pin の検査帰属を分離する |
| cache verify | `_verify_source` 再利用 | 対象内。shallow を許可しない方針は明確 |
| hydrate | clone・再検証・ignored 拒否 | 対象内。job 使用時までの保証ではない |
| P3 S4 job | source 出所の変更、HEAD・dirty 維持 | 強い検証との引渡し境界が未被覆 |
| 実 configure | fresh prefix と実 finder の証拠 | 対象内だが、これから取得する証拠 |
| 他 job・T-126 submission | 旧 locator のまま | 明示的 scope 外。共通移行完了とは呼べない |

根拠：`plan:97,124,185`、`tools/pegasus/p3_s4_loop_pegasus.sh:539`、`orchestrator/qualification/submission.py:160`。  
影響：P3 S4 の成功証拠を、certified 経路や T-2625 の供給問題解消へ一般化すると、材料レポートの結論が証拠の範囲を超える。

**裁定パッケージ候補は2件です。**

- D1737 と T-548/T-585 の逐語に対し、旧経路を残す段階移行を認めるか。
- 完了名義を「新調達経路＋P3 S4 の実 configure」に限定し、他 consumer と T-2625 の解消を未完として残せるか。

## 7. 攻めたが壊れなかったもの

- **cache→staging の通常の HEAD 差替え。** cache は clone 前と後、staging は publish 前後と最終返却時に検査される。再利用だけで単純な差替えが通るとは言えない。  
  根拠：`tools/pegasus/fetch_third_party.py:613,642,648,656,670`。影響：検出された不一致は成功記録にならない。ただし継続的な不変性の証明ではない。

- **shallow 例外の混入。** `allow_shallow=True` は旧 `verify-deps` に限定され、新 cache 経路の既定値は False。  
  根拠：同 `364,525,691`。影響：plan どおりなら新 cache の受理集合は shallow を含まない。

- **origin と ignored の役割分担。** cache の origin は upstream URL、hydrate の origin は cache path と照合する。cache の ignored file は許すが staging では拒否する。  
  根拠：同 `534,625,645,660`。影響：これらの違い自体は検証漏れではない。

## 8. nit

- plan の「既存項目の行番号を保つ」は既存値の行を保てても、末尾の閉じ括弧の行番号までは保ちません。実際の行番号 pin は未発見なので、現時点では nit です。根拠：`plan:39`、`tools/pegasus/policy.json:101`。
- 推測した `orchestrator/tests/test_t316_sandbox_backend.py` と `orchestrator/campaign/sandbox_backend.py` は不在でした。必読対象ではないため停止せず、実在する `test_t316_sandbox_probe.py` 等を追いました。