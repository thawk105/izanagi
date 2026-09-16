## 受理集合の差分

静的検査では、**plan の production 案に既存 refuse → allow の拡大は見つからない**。ただし、変異の KILL 分類と正例の登録には修正が必要。

以下の略記を使う。

- `D` = `orchestrator/campaign/s8b_oracle_driver.py`
- `R` = `orchestrator/campaign/s8b_ratified_freeze.py`
- `T` = `orchestrator/tests/test_s8b_oracle_driver.py`
- `B` = 射影の `stage1-brief.md`
- `P` = 射影の `s2-plan.md`
- `V` = 射影の `rulings-verbatim.md`

**A-1 — refuted／severity: should：sha 比較が独立した二入力を比較する、という疑いは成立しない。**

根拠：`D:451`–`456` は `launch_validated` を優先し、その `ratified.document` と `ratified.sha256` を採る。`D:677`–`683` が `verified` と token を同時に渡しても、`verified.sha256` は比較に使われない。旧枝の `active` も同じ `launch_validated.ratified`（`D:490`）。通常の不変 object／文字列という契約では自己比較である。

ただし `freeze_sha is None` は恒偽ではない。plan はこの検査と比較を保持している（`P:65`–`72`、`:87`–`91`）。

推奨：plan どおり条件を残す。「requested freeze と active の独立照合を保証する」とは説明しない。

受理集合の差分は次のとおり。

| 分岐 | 旧→新 |
|---|---|
| 非 exact の非 None token | 同じ型 refusal |
| adapter／v1 | 変更なし |
| v2、`ratified_error` あり | 同じ `freeze-ratify:` |
| v2、exact token あり | 同じ hash 条件・後続診断 |
| v2、token なし、error なし | static ratified による受理可能性を閉じ、必ず新 refusal |

根拠：旧 `D:436`–`508`、新案 `P:54`–`74`。後続診断と `_make_gate_decision` が不変なら、最後の行だけが受理集合を縮小する。

## fail-closed の組合せ表

表の v1/v2 は、**core が実際に選んだ document**の分類。token があればその document が優先される。

記号：

- `M`：新しい exact token 必須 refusal
- `T型`：既存の token 型不正 refusal
- `F/B`：既存の floor-null／budget-null
- `E`：`freeze-ratify: ...`
- `H`：`freeze-not-active-generation: ...`
- `Q`：receipt、known-axes、manifest 等の既存追加 refusal

adapter 非発火、`ratified_error=None` を基本条件とする。

| document／token | 変更後の refusal 集合 | allow |
|---|---|---|
| v1＋None | `{F,B} ∪ Q` | 不可 |
| v1＋exact validated | `{F,B} ∪ Q` | 不可 |
| v2＋None | `{M} ∪ 欠けた側のnull refusal ∪ Q` | 不可 |
| v2＋exact validated、正常 hash | `欠けた側のnull refusal ∪ Q` | 両側 non-null・他検査成功時のみ可 |
| v2＋exact validated、hash None | `{H} ∪ 欠けた側のnull refusal ∪ Q` | 不可 |
| v2＋ReverifiedFreeze | `{T型} ∪ receipt refusal`、早期 return | 不可 |
| v2＋LaunchValidatedFreeze subclass | 同上 | 不可 |
| v2＋`ratified` のみ | `{M} ∪ 欠けた側のnull refusal ∪ Q` | 不可 |
| 再読失敗で freeze=None | holdout 読取 refusal＋known-record 欠落＋`F,B`。manifest 指定時は検証不能も追加 | 不可 |

根拠：`D:436`–`464`、`:509`–`535`、`:186`–`197`、`P:58`–`72`。

`ratified_error` がある v2 は `M/H` より `E` を優先する。型不正 token はそれ以前に拒否される。public の明示 `ratified_error` は `D:607` で早期 return するため、core の診断集約とは別である。

**A-2 — real／severity: should：brief の I1 は実装案より強く書かれている。**

根拠：`B:33`–`34` は token なしでは「gate predicates へ進めない」とするが、plan は refusal 追加後も診断を評価する（`P:74`、`:273`）。既存 error 経路の診断集約を保つ I3 とも字義上衝突する。

推奨：「exact token なしの v2 を admission しない。拒否理由の集約は継続する」と明確化する。早期 return の追加は不要。

## 到達経路の網羅

**A-3 — real／severity: should：callsite 数と『race のみ』の適用範囲を限定する必要がある。**

production Python の AST 再走査結果は **6 callsite／2 関数／1 module**。

| 呼出元 | 行 | 用途 |
|---|---|---|
| `gate_check` | `D:619` | 初回読取失敗後の再読 |
| `gate_check` | `D:632` | v1 |
| `gate_check` | `D:646`, `:655` | static loader 例外の診断集約 |
| `gate_check` | `D:677` | launch validation 成功 |
| `_gate_check_validated` | `D:702` | exact token を渡す実走経路 |

`ratified=` の実引数は `D:624`、`:638` の2箇所。別 module の production 直接呼出は検出しなかった。これは AST 走査結果であり、権威ある閉包の証明ではない。

通常の loader が作った整合的 object を使う production 経路では、token なしの self-load 到達条件は初回失敗→再読成功である。一方、private core を `verified=<v2>` で直接呼べば race は不要で、さらに `ratified=` を与えれば static loader 自体も不要（`D:454`、`:490`–`496`）。この直接呼出はテストには実在するが、production caller としては見つからない。

推奨：`B:9`、`:54` の「のみ」「唯一」を production 到達条件／public 回帰観測に限定する。core の全入力についての唯一性とはしない。

**A-4 — refuted／severity: should：通常の production v2 が adapter を通って token 必須化を回避する疑いは成立しない。**

根拠：

- adapter は receipt の holdout raw hash との一致を要求：`D:258`–`264`
- receipt の固定値検査：`t080_freeze_migration.py:430`–`450`
- history 検査から当該 schema 検査を呼ぶ：同 `:2133`–`2139`
- `verify_receipt` はその history を利用：同 `:2289`
- 定数：同 `:48`
- 既定 freeze の floor/budget：`output/s8b-freeze/holdout_freeze.json:622`–`623`

実 bytes の SHA-256 は定数と同じ `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`、両 field は null だった。

推奨：親の説明を採用してよい。ただし、hash と document を不整合に手作りした注入 object まで含む保証には一般化しない。型の偽造不能性は元来保証外（`R:754`–`757`）。

## 変異の帰属

**A-5 — real／severity: must-fix：診断差だけの変異を KILLED 候補に混ぜている。**

`docs/dev-wave/mutation.md:7`–`10` は単一理由性、`:18`–`20` は診断文字列だけの赤を KILL に数えないこと、`:62`–`63` は別枠記録を要求する。`P:195` の「exact 集合の差として検出」は、KILL の十分条件ではない。

| plan の候補 | 静的判定 |
|---|---|
| static self-load＋hash 受理を復活（`P:183`） | both non-null、他 refusal 空なら単一理由にできる |
| exact→isinstance（`:184`） | direct core の subclass＋正常 v2 fixture なら単一理由にできる |
| missing append 削除（`:185`） | both non-null なら単一理由にできる |
| core の v2 判定を片側化（`:186`–`187`） | **反対側の null refusal が残る。受理は変わらず診断差** |
| public の v2 判定を片側化（`:188`） | **core の missing refusal／null refusal にマスクされる** |
| ratified のみで受理（`:189`） | both non-null なら単一理由にできる |
| error より missing を優先（`:190`） | **拒否のまま reason が変わる診断差** |
| sha 条件全削除（`:191`） | hash None、both non-null、manifest なしなら単一理由にできる |
| missing refusal 重複（`:192`） | **拒否のまま件数だけ変わる診断差** |
| public error を core へ流す（`:193`） | error を保持するなら **拒否のまま集約・呼出数が変わる**。具体的置換次第 |

推奨：太字の候補は diagnostic sensitivity pin に分離する。特に private wrapper 経由で core の型検査だけを変異させると `D:695` がマスクするため、subclass 負例は plan どおり direct core にする。

`freeze_sha != token.ratified.sha256` だけの削除は、通常契約では等価という plan の分類でよい（`P:199`）。未使用 `ratified` の代入増減も同様。

**A-6 — real／severity: must-fix：v1 の不変性を固定する正例が不足している。**

v2 exact token の正例は `P:163` にある。一方、v1 の代表として挙げる既存テストは、baseline が拒否されることと known-axes 診断の差を検査するだけで、baseline 全体を exact 固定しない（`test_s1_known_axes_freeze.py:1154`–`1157`、`:1173`–`1175`）。v1 に誤って新 missing refusal を常時追加しても、そのテストは検出しない可能性がある。

推奨：小さい v1 fixture で既存 refusal 集合と新 refusal の不在を固定し、過剰拒否の正例として登録する。v1 は floor/budget-null により元来拒否されるため、`allowed=True` を要求する正例ではない。

P3 は plan の hash 一致 fake を推奨する。brief の AssertionError fake では旧 fallback 自体も例外を捕捉して拒否する（`D:499`–`502`）。呼出禁止や診断差は見えても、受理境界の単一理由にはならない。

## 親の実測値の検算

**A-7 — real／severity: should：静的整合・部分検索から実行済み／閉包確認済みへ一般化しない。**

| 主張 | 検算結果 |
|---|---|
| 既存5本は無変更で緑 | **未確認**。静的整合は支持するが、この段では実行していない。`P:38` の留保が正しい |
| no-active test が core の拒否を保証 | 不成立。`T:4217` は `run_block` を呼ぶ。core の新枝の直接証拠ではない |
| 既定 freeze は v1 | 実 bytes／field／hash で確認 |
| t1338-u2 の dirty hunk は非重複 | 実 diff で確認。旧行890、895、926、934、1050、1063、1066、1778付近で、対象402–685と非重複 |
| DW-O09 不成立 | 直接 hash pin なしは支持するが、全 pin 閉包の確認までは証明できない |

driver の変更前 SHA-256 `87161d752e18807c4afb6781ba813c591e65f1f9e53f6a2e10bbf7fe0432dff5` を `output/` で検索し、hit 0 を確認した。manifest の generator key→path 表にも driver はない（`s8b_oracle_manifest.py:65`–`73`）。

ただし DW-O09 は path/hash だけでなく、role key、集合 digest、output 外の台帳・schema を含む（`docs/dev-wave/operations.md:64`–`70`）。`B:72` の根拠だけで全閉包を終えたとはいえない。

推奨：「現物で確認した範囲」と「未検証」を記録する。dirty hunk の非重複も、その時点のテキスト差分についての事実であり、統合テスト不要の根拠にはしない。

## 裁定との整合

**A-8 — real／severity: should：D1984 逐語の矛盾を省略して要約している。**

`V:102`–`103` は exact 必須化を明示する。一方、D1984 の `V:159` は「二読 fallback の択一は未裁定」と記し、`V:124`–`125` も扱いを変えないとする。したがって「D1984 はメタテストと出所だけを決めた」という `B:28` は逐語の全内容を表していない。

ただし、より後の持ち越し本文 `V:176`–`180` が D1872 を「裁定済み」と明示し、今回のユーザー指示も実装裁定を確定している。実装を止める理由にはならない。

推奨：D1984 の未裁定記述には不整合があることを明記し、今回の根拠を D1872・後続持ち越し・現指示に置く。

**A-9 — refuted／severity: nit：ratified 引数保持だけで D1872 より弱くなるわけではない。**

`P:54` は既存 exact-type 検査を維持し、`P:60` は token 欠落を拒否する。core の `ratified` を未使用にすれば、引数の存在は admission を与えない。public 注入は引き続き `D:664` の full launch validation を通る。

推奨：P2 の保持案は許容できる。削除案も安全だが、その場合は直接注入負例が構造化 refusal ではなく引数エラーになるため、観測契約を揃える。P1 の再読維持も、v1／二読失敗の既存診断を保つ最小差分として妥当。library 強制や新しい一般 gate への拡張は不要。

## 総括

production 案は、通常の入力契約では **受理集合を狭める変更として支持できる**。sha 比較と adapter に関する受理拡大の疑いは refuted。

段4前の必須修正は **A-5：診断差を KILL から分離すること**、**A-6：v1 不変性の正例を登録すること**。併せて、I1、caller 数、race の適用範囲、D1984 の不整合、実測済み範囲を訂正することを推奨する。

ファイル編集・pytest・変異実行は行っていない。緑／KILLED はいずれも未確認。