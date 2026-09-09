## 読んだもの

- 一次資料全文:
  - `s4-adjudication.md:1-74`
  - `s5-author-out.md:1-82`
  - `s5-impl.diff:1-400`
  - `orchestrator/campaign/backoff_sweep.py:1-530`
  - `orchestrator/tests/test_backoff_sweep.py:1-425`
  - `patches/silo-backoff-fixed.patch:1-77`
- `condition_meaning_gate.py` の関係経路:
  - `MeaningCase`:406-433
  - capture/request:807-878, 1154-1205
  - evaluator:3287-3439
  - admission:4027-4085
  - 実コンパイルと比較:4225-4326
- 追加確認:
  - 6 production caller の呼び出し箇所
  - `condition_meaning_gate/supplied` fixture の3ファイル
  - 関連する既存 real-wrapper test
- pytest は指示どおり実走していない。以下は静的検査結果である。

## 申告と実物の照合

| 申告 | 実物 | 一致か |
|---|---|---|
| 必須 keyword `backoff_fixed_physical_us` を追加 | `backoff_sweep.py:88-94` で既定値なしの keyword-only 引数 | 一致 |
| key は要求された非負値と完全一致、key/value は exact `int`、value は非負、capture 前に拒否 | `backoff_sweep.py:108-150`。capture はその後の `:156` | 一致 |
| intent を binary64 bits 化し、2文脈へ複製 | `backoff_sweep.py:143-154` の `(bits, bits)` | 一致 |
| 非負値へ宣言、`-1` stock branch と他 macro は不変 | `backoff_sweep.py:182-198`。`-1` が先に分岐し、他 macro は `None` | 一致 |
| production caller は6 module、7呼び出し | `backoff_sweep.py:425`、`backoff_extended_sweep.py:545`、`backoff_profile.py:349`、`backoff_repro.py:72`、`backoff_requested_us.py:116,133`、`backoff_overthrottle.py:67` | 一致 |
| overthrottle だけ decode 由来 intent | `backoff_overthrottle.py:76-80,96-100` | 一致 |
| raw 5、raw 3000、F718、key契約のテスト | `test_backoff_sweep.py:145-265` | 一致 |
| M1〜M5 を静的に照準済み | M1とM5の期待 kill set が裁定表どおり分離されていない。後述 | 不一致 |
| wire-domain 一律拒否は追加しない | raw domain の上限検査なし。raw 1000/intent 0、raw 12000/intent 10000 は patch `:70` の計算と一致すれば green | 一致 |
| codec は移動しない | 定義は `backoff_extended_sweep.py:64-79`。差分に定義変更なし | 一致 |
| condition gate、patch、docs、台帳、freeze は変更しない | `s5-impl.diff` の header は申告された7ファイルだけ。対象ファイルの差分 header はない | 一致 |
| 既存期待値の変更は許可箇所だけ | 削除された既存 assert は旧 `test_backoff_sweep.py:166` の1行だけ。現行 `:167-176` へ強化。既存 forwarding node には新 assert `:376` を追加したが、既存期待値の反転・緩和ではない | 一致 |
| pytest は未実走 | `s5-author-out.md:39-50,82` が未実走を明記 | 一致 |

差分の計数は、test node が9個から12個へ増加し、新規3・削除0。字面上の `assert` 行は追加12・削除1、pytest/Evolve marker は追加0・削除0である。skip、xfail、既存 assert の反転や緩和は差分中にない。

新関門は恒真ではない。具体的には次を拒否する。

- 非 `Mapping`、非 exact-int key、要求集合との欠け・余り、bool/負の physical value、binary64化不能値を `backoff_sweep.py:118-150` で capture 前に拒否する。
- raw 1000/intent 1000 は契約検査をすべて通るが、patch `silo-backoff-fixed.patch:69-70` では raw 1000 の結果が両文脈とも `0.0` になる。宣言は `1000.0` なので `condition_meaning_gate.py:4291-4304` で `decoded-meaning-mismatch` となる。
- 期待値は caller mapping由来の `backoff_sweep.py:143-154`、観測値は捕捉した hole を別TUへ埋めて実コンパイル・実行する `condition_meaning_gate.py:4225-4289` 由来であり、同じ述語を再評価する恒真構造ではない。

F718負例は `test_backoff_sweep.py:210-220` で production helper を直接呼ぶ。そこから capture `backoff_sweep.py:156-158`、request構築 `:159-171`、supply evaluator `:172-177`、production declaration選択と meaning evaluator `:178-201` を通る。evaluatorは再capture `condition_meaning_gate.py:3385-3395` と実C++ compiler `:4247-4288` を使う。該当test本体にはstubもmonkeypatchもない。ただし実行環境にcompilerがなければ既存 helper `test_backoff_sweep.py:121-126` によりskipされる。

`-1` は `backoff_sweep.py:162-170,182-195` で非負宣言より先にstock分岐へ入る。さらに `MeaningCase.__post_init__` は `condition_meaning_gate.py:413-424` で selected-branch宣言を `define_value == -1`、bitsなし、stock branch名に限定している。patchの三項式変更は synthesized branch内の `silo-backoff-fixed.patch:70` だけで、`#else` stock branch `:71-73` は差分対象外である。

## 所見

所見 1: M1とM5の変異帰属が裁定どおり分離されていない

根拠: `s4-adjudication.md:64-74`、`backoff_sweep.py:178-205`、`test_backoff_sweep.py:145-244`、`s5-author-out.md:8`

失敗シナリオ: M1として `backoff_sweep.py:195` の非負宣言を `None` に戻すと、正例A・Bは `green` ではなく `unestablished` となって落ちる。それだけでなく、raw 1000/intent 1000も `unestablished` のままraw admissionに受理され、F718負例 `test_backoff_sweep.py:205-220` も「例外なし」で落ちる。したがって裁定表のA・Bだけではない。一方、M5を例えば `backoff_sweep.py:146` で全physical値を1ずらす具体的な一行変異にすると、正例A・Bに加え、既存のreal-wrapper node `test_backoff_extended_sweep.py:919-933` と `test_backoff_profile_pegasus.py:864-897` もhelper呼び出し時に落ちる。M1/M5は正例A・Bを共有し、裁定 `s4-adjudication.md:72-74` が要求した再照準は差分にない。

成果物影響: M1相当の宣言欠落をA・Bだけの問題と誤帰属すると、F718型の誤意味点が `unestablished` のまま受理され、certified選択やreportへ混入する退行の評価を誤る。

深刻度: must-fix

所見 2: F718負例のhelper側assertは複数red理由を許す

根拠: `test_backoff_sweep.py:210-220`、`backoff_sweep.py:206-215`

失敗シナリオ: supply armもredになり、meaning armも期待どおりredになった場合、helperは全red理由を連結する。テストは文字列に `BACKOFF_FIXED=red/decoded-meaning-mismatch` が含まれることしか見ないため、二重理由でも通る。後半 `test_backoff_sweep.py:222-244` はmeaning evaluator単体だけを再実行し、production helper内のsupplyがgreenだったことは確認しない。現行fixtureではsource分岐が異なるため静的にはsupply greenだが、test自体は単一理由性を固定していない。

成果物影響: 直接影響なし。二重redでも成果物投入は拒否されるため、弱いのは変異帰属の証拠だけである。

深刻度: nit

## 変異の単一理由性

| 変異 | 裁定上の期待 | 静的に予測される結果 | 他層の先行red | 判定 |
|---|---|---|---|---|
| M1 宣言を `None` | 正例A・B | A・Bに加えF718負例も「例外なし」で赤 | supplyはgreen。meaningがunestablishedになりraw admissionが通る | 期待集合と不一致 |
| M2 bitsをphysicalからrawへ | 正例Bのみ | raw 5は不変、raw 3000は期待3000対観測1000でBのみ赤 | key一致、supply green | 単一理由 |
| M3 key完全一致検査を外す | 負例2 | `{}` が拒否されず最初の `pytest.raises` が赤。extraも単独なら拒否されない | capture後もmissingはunestablishedとして受理、extraは未使用 | 単一理由。ただし同一node内の後続caseは最初の失敗後に未到達 |
| M4 extended mappingをraw→rawへ | extended正例 | raw 3000のkeyは一致し、宣言3000対観測1000で正例Bが赤 | key gateとsupplyはgreen | 単一理由。ただしM2と同じnode/reasonでkill |
| M5 非負を全拒否 | 正例A | 具体的一行変異が未定義。自然な宣言値ずらしではA・Bと既存positive wrapperも赤 | supplyはgreen、meaning拒否 | 事前登録だけでは単一kill setを確定不能。M1との再照準条件も未達 |

現行コードについては、F718、M2、M4の入力でkey検査やsupply armが先に同じ入力を拒否する静的経路はない。過剰決定として名指しすべきなのはM1/M5のpositive test共有と、M1がF718負例まで落とす点である。

## 裁定候補

- 本reviewで新たにscope外へ送る実装欠陥はない。
- 親が既にscope外裁定した既知事項として、`backoff_extended_sweep.py:99-101,660,1181` のT2418 `meaning_witness_status` は現在も「positiveはunestablished」と記す。再走reportの表現は新しいgreen witnessと食い違うが、`s4-adjudication.md:12` に従い本waveでは変更対象にしない。
- freeze hash mismatchは `s4-adjudication.md:10` の親裁定だけを根拠としており、本reviewでは当該verifierを読んで独立確認していない。

## 総括

関門は恒真ではなく、F718はproduction宣言と実C++観測の不一致として拒否される。  
`-1` stock branch、patch、condition evaluator、既存正しさassertの弱体化は認めない。  
ただしM1/M5の変異帰属は裁定どおりに分離されておらず、must-fix 1件。  
F718負例が複数red理由を許す点はnit 1件。  
pytest未実走のため、動的な合否は親の実走待ちである。