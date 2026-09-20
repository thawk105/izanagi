静的検査では、**安定した root に対する plan の projection memo に反例は見つからなかった**。修正が必要なのは、参照実装の独立性、変異の帰属、被覆の記述である。P5 は遅延読取なら採用できる。

以下、H・T は依頼の略号を使用する。必読資料はすべて読取済み。対象 module は `git show b7f970dfa:…` と現物が一致した。ファイル変更・pytest 実行は行っていない。

## must-fix

**受理集合を変える、確定した設計欠陥はなし。** ただし P5 を eager 読取として実装した場合は例外順序が変わるため不可。条件は下記のとおり。

## should

### S1. 参照実装が変更後 helper を共有しており、旧実装との比較になっていない

- **根拠:** plan:145。参照側も、今回分割する H:4670–4955 の変更後 wrapper を呼ぶ。
- **成果物影響:** 共通 helper の回帰を新旧一致と判定できるため、受理集合の比較証拠が弱くなる。固定 message は列挙した負例にしか効かない。
- **是正:** base `b7f970dfa` の module 全体を固定した参照側にする。比較対象は候補関数への `root / expected_marker / completed_attempt` とし、現行 issuer token は渡さない。

job dir に `git show` で置く案は実行可能。ただし次を満たす必要がある。

- H:31–45 に相対 import があるため、単独のトップレベル module として import しない。例えば `orchestrator.campaign._t2802_base_admission` という別名で `spec_from_file_location` を作る。
- dataclass があるため、`exec_module` 前にその別名を `sys.modules` に登録する。現行 module を置換しない。
- repo root を import 可能にする。job dir を `sys.path` に加えるだけでは相対 import は解決しない。
- `__all__` は属性アクセスを制限しないため、private candidate を直接呼べる。
- import は完全な無副作用ではない。H:103 で scheduler authority literal の検査が走り、H:544–548 で別の state registry と `RLock` が作られる。トップレベルに admission root への書込みはない。
- 別 module の `HoldoutAdmissionError` は別の型オブジェクトになる。例外型は module ごとの対応を定義して比較し、message は全文一致させる。
- 依存 module は現行 package を読むため、比較範囲の依存が base と同じことも固定する。

### S2. 変異台帳は「KILL」「狙った理由での KILL」「新規検出力」を分ける必要がある

- **根拠:** plan:179–187、H:5236、5296、5304、T:2729・2750。
- **成果物影響:** 同じ弱体化を複数防御で拒否した結果や、既存 test による検出を、新規 test の独立した検出力として過大計上する。
- **是正:** 各変異について、旧 test 群／追加 test 群の結果と、実際の最初の拒否位置を別欄にする。

| 変異 | 静的判定・単一理由にする条件 |
|---|---|
| hit で `campaign_run_id` を信用 | **target marker を壊すと帰属が重なる。** 完全再導出を弱めても H:5304、A があれば H:5296 が残る。非 target・A 不在の marker を使う。既存 T:2729 も target による memo 登録後の hit を通るため、message 不一致によって既に KILL し得る。 |
| exact-key を省き extra key も捨てる | T:2729 の既存 extra-key が既に KILL できる構造。さらにこれは二つの防御を同時に弱める**複合変異**であり、「一つの検査の削除」とは数えない。 |
| hit の membership を省く | 正しい claim projection と、未登録だが文字列として妥当な attempt_id を持つ非 target marker を使えば、membership に帰属できる。filename もその attempt_id に合わせる。 |
| canonical filename 比較を省く | **複製ではなく改名**する。複製すると H:5276 の identity 重複が後段で拒否する。非 target marker の改名なら帰属が明瞭。 |
| A identity 重複を省く | 正常 marker に対応する canonical A 行を二重化すれば到達可能。片方が orphan／改竄行では先行拒否される。 |
| main≠expected_main を省く | `records` のみ変更し、shape・identity・manifest・marker を正常に保つ案は妥当。H:4780 と4917 は別 branch なので、v1 と generation の変異を区別して記録する。 |
| completed 拒否を省く | T:2750 が既に検出する。新規検出力には数えない。M+A−で試す。M+A+なら H:5306 が先に `None` を返す。 |
| identity の `str` を除去 | H:5287 成功後の identity は検証済み文字列。静的 JSON root では等価変異として妥当。 |

### S3. 五群の test 計画だけでは I1〜I5 全項目を実証したとは書けない

- **根拠:** H:1346–1358、1384–1405、5255–5310、plan:143–169。
- **成果物影響:** 対応表にある検査を未試験のまま「被覆済み」とした証拠が残る。
- **是正:** 以下を追加対象／既存被覆／静的に到達不能に分けて台帳化する。

| 項目 | 現状と必要な扱い |
|---|---|
| M+A−回復、同 attempt 再発行、書込み順 | T:2633 が既存被覆。 |
| M+A+拒否 | T:2581・2685 が既存被覆。候補関数自身は拒否例外ではなく `None`、consume が H:4386 で拒否する。 |
| marker 不在、orphan A、completed | T:2668・2699、2714、2750 が既存被覆。 |
| exact shape、marker と authority の不一致 | T:2729 が既存被覆。ただし複数 claim・非 target の帰属は追加が必要。 |
| unsafe entry、directory 不在 | T:2581–2770 には該当負例なし。H:5258／5262 の全文 message と先行順序を追加。 |
| canonical document reader | claim の読取不能／非 regular／一行でない／非 canonical／JSON 不正を分ける。H:1351・1353・1355・1358 と `_strict_json` の例外を固定する。marker の symlink は reader 前の H:5260 で拒否される点も区別する。 |
| filter の順序 | 対象外 schema／role の marker でも bytes 検査は先行する。対象外の正常文書は無視、不正 bytes は拒否、を追加。A ledger も全 bytes 検査が filter より先。 |
| main ledger reader | plan の非 canonical bytes 一種類では不足。byte 上限、末尾 LF、空行、JSON、非 regular、読取不能と、claim エラーとの優先順位を分ける。 |
| claim/main の miss 検査 | claim shape・key・identity・attempt_ids の型／重複・entry/seams・main 件数0/2・manifest の値と出所を明示する。特に v1 は main 由来、generation は claim 由来（H:4759／4889）。 |
| memo 寿命 I4 | claim 改竄だけでなく、呼出し間の main 改竄も追加。P5 採用時は main 生読取1回／call、claim 読取1回／claim と区別して数える。 |
| I5 | T:2676 は公開 query signature の一部を検査する。`__all__`、他 wrapper signature、変更外の書込み箇所・書式は別途差分確認が必要。 |

`target != canonical_target`、A≠marker、marker identity 重複は、以下の静的不可能性を記録すべきであり、authority helper を偽装した負例で埋めるべきではない。

## nit

### N1. 受理集合の対応表は、安定した読取結果という条件下では成立する

- **根拠:** H:4675–4937、5236–5287。
- **成果物影響:** この条件下で受理・拒否・message の変化は見つからない。無条件の実行履歴同値と書くと保証を過大表示する。
- **是正:** brief I1 を plan と同じ「一呼出し中、読取対象・読取結果が安定」に揃える。

具体的な反証結果は次のとおり。

- **schema と path:** `(attempt_schema, claim_digest)` で十分。root は memo の一呼出し内で固定され、schema が claim path を決める。さらに候補関数は target schema を marker/A filter に使うため、一つの memo に両 attempt schema は通常入らない。
- **v1 全 floor 行検査の回数:** 静的 root で「検査中に別 row が壊れる」は構成できない。全行は JSON から作った通常の dict で、当該検査に書込みはない。途中の外部変更や読取失敗を持ち込めば差は作れるが、静的 root の反例ではない。
- **target が最初の登録:** 旧実装でも target が最初に完全検査される。成功済み部分だけを省き、今回の membership・constructor・equality を残すなら順序差は生じない。

### N2. P5 は「最初の miss の入口」ではなく、既存の main 読取位置で初期化する

- **根拠:** H:4720–4737、4861–4884、4946、1384–1405。
- **成果物影響:** eager 化すると、例えば「target の coverage 不正＋main の末尾 LF 欠落」で、旧 coverage エラーが ledger エラーへ変わる。遅延化なら静的 root で差はない。
- **是正:** candidate ローカルの未読 sentinel を設け、H:4737／4946 相当へ初めて到達したときだけ `_read_ledger` を呼ぶ。空リストと未読状態を区別し、成功した行列を変更せず再利用する。

最初の projection miss は必ず target。ただし、その claim／coverage／seams が失敗すれば **main は0回読取**で終わる。この点まで回数 test に含める。

target の main 読取が成功した後は、同じ raw bytes の reader 検査が後続 claim で初めて失敗する静的状態はない。claim ごとの行選択・shape・件数・expected_main 比較は従来位置で残す。事前の意味的 index 検査は加えない。

したがって、**P5 自体は棄却不要。eager な実装だけを棄却する。**

### N3. lock の限界は既存契約として記録する。新 gate／再読は不要

- **根拠:** consume H:4361→4372→5320、query H:5340→5348。validate は **H:5082** が入口で、H:5094 に lock、H:5010 に active handle 検査がある。
- **成果物影響:** 確認した production 経路で、候補関数が lock なしに走る例はない。契約外の同時変更や一過性 I/O を含めれば結果差はあり得るが、今回新たに開く production 経路ではない。
- **是正:** plan の限界を insight に残す。wrapper は memo なしのまま保つ。

H:5676 は候補関数ではなく単文書 wrapper の呼出しである。registry trigger helper 自身は lock を取得しないが、consume の authorization、H:5800 の retry query、H:6193 の shared-lock inspector から到達する。無 lock の候補関数経路とは扱えない。

### N4. A≠marker と target≠canonical_target は静的 root では到達不能と結論できる

- **根拠:** H:5270・5287・5293–5297・5304、constructor H:4564／4613。
- **成果物影響:** これらの比較削除を「必ず KILL する弱体化」に含めると変異台帳が成立しない。
- **是正:** plan の「可能性が高い」を、対象領域を明記した到達不能の説明へ置き換える。production の防御は残す。

固定 schema・claim digest・attempt_id に対し、成功する canonical 文書を `F(identity)` と置ける。marker と A は各々完全再導出を通り、同 identity なら双方とも同じ `F(identity)` になる。別 attempt の正しい文書を A に置けば identity が変わり、対応 marker があればその marker と一致、なければ H:5295 で拒否される。

target も H:5236 で同じ `F(target_identity)` に検証されるため同様。marker 重複も、同 identity の canonical path が一つなので、別名なら先に H:5272 が拒否する。

### N5. legacy fixture は現行 producer の試験ではないが、削除は不適切

- **根拠:** H:4398 は generation digest のどちらかが `None` の場合。現行 reservation/finalize は H:1704、1926–1930 で generation を設定する。legacy inspector state は H:6631 以下にあるが、通常 issuer state として登録されない。
- **成果物影響:** 現行 producer の到達性として説明すると誤り。ただし fixture を削ると、変更対象 H:4670 の legacy branch の同値性が未検証になる。
- **是正:** 「legacy 読取互換性の unit fixture」と明記して維持する。現行 consumer の性能証拠には数えない。

### N6. brief の前提・アンカー・所有範囲には訂正が必要

- **根拠:** brief P1〜P4、H:3168–3173、5236、5330、5082、plan:204–225。
- **成果物影響:** 主に説明・A/B 対表の解釈が変わる。これだけを理由に production の受理集合修正は不要。
- **是正:**
  - P3 の「最初の marker」は「target を含む最初の利用」に直す。target claim の拒否が loop 前という後半は正しい。
  - main ledger の四 append 箇所には R33 H:3168 が既に含まれる。**五つ目の main writer の見落としではない。** 不足は R33 claim 公開 H:3171–3173 を含む claim 書込み説明。
  - `floor_attempt_requires_cut6_replay` の定義は H:5330。H:5327 は前関数の末尾。validate の定義は H:5082 で、H:5040 はその内部 helper。
  - P2 の v1 digest 費用は代表 generation node の直接説明にならない。「1秒未満」は未測定の仮説。
  - P4／A/B は A=base、B=implementation なので「同一 SHA 比較」ではない。plan の条件内 SHA 固定という修正を brief にも反映する。
  - 「fixture 側の変更は scope 外」は、既存 fixture の高速化を除外する趣旨と、新規 regression fixture を許す趣旨を区別する。
  - launcher／集計器は別 author の job-dir 所有物。production author の編集対象に混ぜない。

## 総括

plan：**修正のうえ採用**。安定した root で受理集合の反例はなく、参照実装・変異帰属・被覆記録を修正する。
P5：**条件付き可**。既存 main 読取位置で遅延初期化し、生読取結果だけを一呼出し内で共有する。
検証：静的検査のみ。lock 契約外の実行履歴同値は保証せず、pytest・変異実測・A/B は親で行う。
