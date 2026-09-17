## 判定と検査範囲

**修正して採用**を推奨する。設計には純増があるが、現状では後続実装者が、同一性の比較対象・36走の受入条件・軸オンボーディングとの境界を再設計する必要がある。

指定資料は読取可能だった。静的検査のみで、変更・build・テスト・compute 実走はしていない。以下、`plan` は `s2-plan.md`、`M` は指定された e9e477ca の `transaction.cc` を指す。

## 1. proof 用 template と正式な軸採用の境界が未確定

- **対象:** brief:3–4、12、plan:49–66、251–264、309–313。
- **severity:** **must-fix**
- **主張:** 「実証の設計」でありながら、正式な軸名・template・`axis_mocc_temperature.py`・読取契約を成果物として置くため、後続がこれを段階B採用済み・C着手可能と読める。「探索を解禁しない」だけではA/B/Cの区別が足りない。
- **根拠:** `docs/axis-onboarding.md:24–39` はAの人間承認、Bの3レンズレビュー、Cの機構実装を区別する。本相談は2レンズで、軸定義シートの偵察列挙空間・計測動作点等を確定する仕事でもない。D2114項1は準備着手、D579はtrace-hook限定である。
- **是正案:** 決定文に「温度述語は**proofの接続先候補**として採用し、正式な軸A/B完了を意味しない」と明記する。証拠を次の二つに分ける。
  - 経路共通部分：固定producer上のX/P、hot/cold条件、負例の検出。
  - template依存部分：4 callsite、読取契約、DQ、identity、auditor A/B、template SHA。

  軸変更時は依存部分を再検証する。旧X/P証拠まで無条件に捨てる必要も、別templateへそのまま移せる根拠もない。

## 2. 同一性の比較対象と patch 積層順を固定する必要がある

- **対象:** plan:53–66、152–154、255–258。
- **severity:** **must-fix**
- **主張:** OFFで原文比較を残す方針は妥当だが、`src_token="stock"`、D1687の論理行列、D297のpin間比較は別の検査である。新templateを重ねた際の既存`#line`との整合が未設計。
- **根拠:** 計装patchは `17 / 990 / 991 / 1158 / 1169 / 1187 / 1195` を復元する。templateはその前方へhelperと4分岐を挿入するため、**同じtemplate状態**というだけでは、計装なし側の論理行と計装あり側の復元番号が揃わない。D1687:3–15、T-2294 README:48–51。`source_digest.py:1647–1729` の正規化はincludeを除いた方式で、実buildの行番号維持とは同義ではない。
- **是正案:** 次の比較表とpatch適用順を設計書へ追加する。

| 比較 | 合格として主張するもの |
|---|---|
| 無template ↔ template OFF、診断計装なし | 実resolverによる `src_token="stock"` |
| template OFF ↔ ONのB、診断計装なし | ONの別identity、実TUへのflag供給 |
| 同一template状態の計装なし ↔ あり | D1687のTRACE=0論理行列一致 |
| 旧pin ↔ pin候補 | 別タスクのD297検査 |

既存計装patchのSHAを保つなら、その復元番号と両立するtemplate側の行番号方針を明記する。binary比較を残す場合はsource/build path等長条件も引き継ぐ。D1687のTRACE計装向け例外を、そのままCC-native骨格の承認根拠にはしない。

## 3. 36走の期待表と `all_pass` のチェック集合が一致していない

- **対象:** plan:96–157、279。
- **severity:** **must-fix**
- **主張:** 走数は **3 regime × 2 thread ×〔Wの4対象＋Uの負例・stock〕＝36走**で正しい。しかし、表の期待値すべてを判定するcheckがない。
- **根拠:** 例えばpermutation/early-unlockのt4、default/Wの複数条件は期待表にあるが、対応する新checkが列挙されていない。`matrix_runs_complete_and_terminated` は存在・完走検査であり、期待reasonやverdictの検査ではない。旧14 checkはtemplateなしの歴史的結果なので、新しいdefault/template ON走の代用にはならない。
- **是正案:** 各runを「受入必須」「観測のみ」に分け、必須runからcheckへの対応を全件記す。観測のみの結果に未実測の正数を要求しない一方、hang・欠落・別integrity異常の扱いを明示する。必須条件が欠落した場合に赤になる検査を付ける。

**DW-O13についても追記が必要。** 既存driver:343–435はargv・終了状態をrun recordへ保存せず、異常時は例外にする。279行のJSONを得るには新producer側の記録処理が必要である。`certified`・txn数は既存 `_verify()` が取得するが、要約JSONにないfieldを旧証拠へ要求してはいけない。また、要約の `condition_gates[].verdict.supply=null` を失敗扱いせず、実producerが出す `supply`・`meaning`・`admission` の構造を参照すること。

## 4. gateの「登録」の意味と執行範囲が曖昧

- **対象:** brief:13、plan:213–237。
- **severity:** **must-fix**
- **主張:** 現状で前件が成立しないことは確認できた。一方、「軸として登録される」の検出元が未指定で、template／軸module検知だけではdriver直書きの導入を検出できるとは言えない。
- **根拠:** 現行 `patches/` のmocc対象は計装1本・負例3本で、いずれもmarkerなし。提案templateとaxis moduleは不存在。campaign直下のトップレベル `SOURCE_REL="cc/mocc/transaction.cc"` は既存proof driverだけで、`MARKER_ID`／`TEMPLATE_PATCH`を持たない。

  `materializer_admission.py:2–18` は登録をinventory metadataと明記し、登録自体は下流build拒否やquarantine実行を保証しない。`p3_s4_loop.py:126–128` はdriver内に定数を直接置く実例である。
- **是正案:** gateを「どのファイル群の、どの宣言・patch hunkを検査する導入時テストか」まで限定する。driver内定数を対象に含めるか、正式なmocc driver導入時の接続義務として残すかを明記する。**任意の直書き経路を機械的に閉じたとは主張しない。** そのための汎用台帳・全経路解析を本waveへ追加する必要はない。

なお、`patches/ledger.json` は存在するが、`patches/README.md:16、481–497` によればability probe専用・現行entry数1固定である。mocc mutationの鍵や登録先への流用は不適切。

## 5. 温度述語1 holeは妥当だが、RLLへの効果を別記すべき

- **対象:** brief:12、plan:38–64、89。
- **severity:** **should**
- **主張:** 4 siteを一つの純粋述語へまとめる実装は成立し得る。`construct_RLL`だけ別holeにする必要は現資料からは導けない。ただし、これは現在の早期施錠と、abort後の再試行集合を同時に変える設計である。
- **根拠:** M:905–913はwrite-setを無条件にRLLへ入れ、970行はread-setを温度またはfailed-verificationで追加する。read側にはRLL優先経路もある（M:280–295）。plan自身がhot負例で証明するのはupdate分岐だけと限定している。
- **是正案:** 4 siteの効果・静的確認・動的確認を表にし、RLLとDELETEについて未実証部分を残す。今回の契約を「4 siteで同じ温度分類を使う」と明示すれば1 holeでよい。再試行だけ独立政策にする場合は別軸設計として扱う。

対抗候補の比較は概ね妥当。温度上昇則は乱数・shift・CASを伴い、`vioctr > 100` は既存max_ope=5でstock枝の被覆が難しい。ただしbackoffを見送る理由は、実装費用よりMOCC固有性を優先した選択として書くのが正確である。

## 6. 既存資材の保存方針は支持するが、費用と再利用境界が不足

- **対象:** plan:131–135、258、281–290、323。
- **severity:** **should**
- **主張:** 別driver・別JSONにする判断は正しい。旧JSON再生成は、旧patch・schema・check契約を変えなければ不要。ただし「1 batch、8〜10 binary」は所要時間の見積りになっていない。
- **根拠:** `test_mocc_proof_surface.py` の `test_driver_check_keys_are_exact` と `test_compute_positive_control_json_is_all_pass_and_bound` は14 keyとpatch SHAを固定する。T-2294は6走でElapse 130秒、今回提示された変異matrix実績は1,711秒で、別費用である。
- **是正案:** build、36 trace/verifier走、condition gate、変異検査、再走を分けて概算する。130秒の単純6倍＝780秒は粗い参考値にすぎず、build共有・trace量によって変わると記す。

登録先の主要分類はplanに揃っている。ただし既存 `_require_condition_gate()` はdriver IDを固定し、`_apply_owned_patch()` はtransaction単独touchを要求する。Optionsも触るtemplateにそのまま流用できない。新driver側で特殊化する箇所を明記し、旧driverを変更して歴史的証拠を巻き込まないこと。

## 7. F-dの方向は正しいが、現行loopのPIN説明は訂正が必要

- **対象:** brief:11、plan:245–249、axis定数の引き渡し。
- **severity:** **should**
- **主張:** proofは「現行pinを前進させず実施可能」であって、pin非依存ではない。e9e477caとpatch SHAへ強く依存する。また、現行loopがすべて `pin.CURRENT_PIN` を読むという前提は現物と異なる。
- **根拠:** proof driver:42はe9e477caのfull SHA固定。`p3_s4_loop.py:111–112` はD1936のコメント付きで `511c9538…` をfull SHA固定する。plan:249の「e9単体ではX/P absent」は既存テストとも一致する。
- **是正案:** proof用OIDと探索用の承認済みOIDを別契約として記す。新軸moduleのPIN方式は現行承認契約を確認して決め、旧 `axis_trigger_gating.py` の方式を機械的に転写しない。D297合格を、既存の事前登録・identity・凍結の張替え承認と扱わない（D2114:43–49）。

## 8. docs-only成果物には価値があるが、採用文を狭めるべき

- **対象:** brief:3–4、plan:293–323。
- **severity:** **should**
- **主張:** チェックリスト再掲には留まっていない。hot実証不足、RLLによるcold解釈の限定、balanced負例のworkload制約、file-scope helperとA/Bの整合、X/P producerとpinの未接続は具体的な純増である。
- **根拠:** D579・D38・D1686はこれらの接続設計を固定していない。D2114一次資料§6の設計T完了条件にも対応する。
- **是正案:** insightの節構成は採用し、決定文には所見1の正式軸との境界を追加する。worklogには「設計確定」「実測未了」「正式軸・探索未解禁」を区別して記録する。briefが示す運用前提では、phase3.md非編集は妥当。

本件のために一般的な新台帳、未知のdriver全経路を覆うgate、追加の性能評価を要求する必要はない。具体的な新template・負例・consumerとの接続に限定すればDW-G05と整合する。

## 総括

**must-fix一覧**

1. proof用接続候補と、正式な軸A/B/Cの完了を区別する。
2. template／計装の適用順、同一性の比較対象、`#line`整合を固定する。
3. 36走の各期待値を必須checkまたは観測項目へ対応させ、JSONの生成元を明記する。
4. gateの登録検出元と執行範囲を限定し、driver直書きまで閉じたと過大主張しない。

**planの採否：修正して採用。** 純増があるため、設計Tを却下して実証waveのplanへ吸収する必要はない。

**後続は2 waveを推奨する。**

- **Wave 1：経路共通の実証。** hot/cold条件、Uの実挙動、balanced負例、登録閉包を確定する。完了判定は新producerの実測証拠と入力由来checks、旧14 check・旧patch SHAの保持。正式なmutation template導入はまだ完了としない。
- **Wave 2：templateへの接続実証。** 正式軸のA/Bとの関係を確定した上で、実templateのidentity・DQ・gate・auditor入力・fresh A/Bを検証する。完了判定は当該templateに束縛された機械証拠と別記のn=1素材が揃うこと。**pin前進・certified探索の開始は、この2 waveの完了から自動的には導かない。**
