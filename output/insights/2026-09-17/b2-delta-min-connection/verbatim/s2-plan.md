## 問い 1〜8 の答え (file:line 付き)

必読の逐語資料を読み、現物から独立回答を記録してから親 brief を読みました。編集・pytest 実走はしていません。以下の Python ファイル名は、特記しない限り `orchestrator/campaign/` 配下です。

**1. 判定器は holdout 軸のないパラメータ object を 1 個受け取る。**

`s8c_result_judge.py:129–143` の frozen dataclass `_ContrastParams` は、`n, delta_min, sd_max, unit, direction, source_binding` を持ちます。`judge()` の引数はこの型の `params` 1 個 (`:1959–1964`)。validator は exact type を要求するため、H1/H2 の辞書を直接渡す契約ではありません (`:293–298`)。

適用経路は次のとおりです。

- formal: `:1978` で検証し、`:2010–2012` で `_evaluate_contrast` へ渡す。
- generation: `:1973–1975` で検証して分岐し、`:1900–1907` で同じ `_evaluate_contrast` へ渡す。
- 共通: `:1434` の holdout ループで各 holdout の on/off を選び、`:1550` で `mean_delta > float(params.delta_min)` を評価する。

したがって、有効な入力でこの比較に到達した各 holdout に、**同じ `delta_min` と `sd_max`** が適用されます。H1/H2 を含む manifest なら両者に同じ値です。

**2. §5 validator は H1/H2 別の 2 block を要求する。**

`s8c_preregistration.py:135–137` が対象欄を定義し、`:968` で validator を登録しています。記入済み欄からの呼出しは `:833–837` にあります。

要求する形は、root が exact keys `{"H1","H2"}`、各 block が exact keys `{"n","delta_min","sd_max","unit","direction"}` の辞書です (`:909–925`)。

検査内容は次のとおりです。

- `n`: bool を含まない整数、2 以上 (`:931–935`)。
- `delta_min`: int/float、float なら有限、正 (`:936–943`)。
- `sd_max`: int/float、float なら有限、非負 (`:944–951`)。
- `unit` / `direction`: 文字列かつ空白だけでない (`:952–961`)。

**この validator 自身は workload 束縛を検査しません。** block に workload や参照 artifact 欄がなく、各値がどの stock 参照から算出されたか、係数 0.03、測定条件、転記元との一致を検査していません。H1/H2 間の値の一致・相違も要求しません。

単位・向きの定数一致は judge 側の `:309–312` が担当し、定数は `:44–45` の `throughput_tps` / `on_minus_off` です。これは参照 artifact の出自検証とは別です。

**3. 調べた現行 production ソースでは、§5→object の変換と対象 `judge()` の caller は見つからない。**

worktree root で次の静的検索を実施しました。

```bash
rg -n --hidden -g '*.py' -g '!.git' \
  -g '!**/tests/**' -g '!**/test_*.py' \
  's8c_result_judge|_ContrastParams|\bjudge\s*\(|SECTION5_ITERATION_CONTRAST_FIELD' .

rg -n --hidden -g '*.py' -g '!.git' \
  '_ContrastParams\s*\(|SECTION5_ITERATION_CONTRAST_FIELD' .
```

結果は以下です。

- `_ContrastParams(...)` の構築箇所は `orchestrator/tests/test_s8c_result_judge.py:104,573` のみ。
- 欄定数の production 出現は `s8c_preregistration.py:135,903,968`。定義、違反報告の欄名、validator 登録であり、judge object の構築ではない。
- 対象 judge の production import・呼出しは検出されない。
- 同名呼出しの `b10_backoff_shape_sweep.py:4014` は同ファイル `:2174` の別 judge。
- `tools/pegasus/probes/t316_sandbox_backend_probe.py:2628` は `:2608–2622` で束縛された sandbox verdict 関数の呼出し。
- C07 は `s8c_preregistration_evidence.py:3037–3078` で、契約が指定するファイルを AST として読む静的検査。対象 judge を実行しない。

Python 以外も含め、tests・docs・output を除く module 名／型名検索を補足し、判定器自身と evidence contract JSON のパス参照だけを確認しました。探索途中の存在しない `scripts/`・`tests/` を指定した検索は rc=2 だったため、不存在の根拠には用いず、上記 root 対象検索でやり直しています。

以上は**静的に探索した現行リポジトリ内の結論**です。外部 consumer や任意の動的生成コードまで不存在と証明したものではありません。

**4. H1=rr80 / H2=rr20 の権威は凍結定義。judge はその対応表を持たない。**

- 設計上の対応: `docs/phase3-8b-descriptor-design.md:115–116`。
- コード上の定義: `s8b_holdout_freeze.py:101–103`。
- registry への導出: `trial_registry.py:83–107`。
- trial manifest: `trial_registry.py:780–799` で H1/H2×on/off/swapped を要求。
- runtime workload 照合: `trial_registry.py:1678–1688`。
- 起動記録への投影: `trial_registry.py:5580,5622–5625`。

judge の formal manifest は `s8c_result_judge.py:353,379–384` で cell 由来の holdout 文字列を集め、2 holdouts×3 arms を要求します。ラベルを H1/H2 に限定したり、rr80/rr20 に束縛したりしません。

generation は `:665–678` で holdout と workload 文字列を受け取り、`:893–909` で結果側との一致を検査します。ただし、**manifest 内の文字列との一致であり、凍結側の正規対応との一致ではありません。** 「workload を一切扱わない」と書くのは誤りです。

親 brief を読んだ後の追加照合で、凍結成果物も `output/s8b-freeze/holdout_freeze.json:40–41,307–308` に同じ対応があることを確認しました。

**5. 現行 production 経路は「未接続」。逆接続は確認していない。**

D1640 の値規則は `docs/decisions.md:50301–50308`、ラベル訂正と「各 holdout 自身の参照」は `:62725–62735` です。

これを独立した H1/H2 の値として届けるには、現在存在しない変換／caller に加え、異なる値を保持して適用できる入力・評価契約が必要です。「渡す先が無い」は、**holdout 別値の受口と production 接続が無い**という意味に限定します。単一パラメータの judge 自体は存在します。

`source_binding` も `s8c_result_judge.py:1626–1628` では manifest と object の文字列一致にすぎず、§5 の値や参照 artifact を読み戻す接続ではありません。

**6. 単一 holdout に分割して 2 回呼ぶ案は現行 manifest 契約では成立しない。**

formal は `s8c_result_judge.py:344–345,380–384`、generation は `:645–646,682–690` が、6 cells・2 holdouts・3 arms の直積を要求します。単一 holdout の入力では正常な判定へ進みません。

ただし、**完全な 2-holdout manifest を異なる params で 2 回渡す呼出し自体は禁止されていません。** 各回で両 holdout に同じ境界を適用し、異なる全体結果を返します。そこから H1/H2 の部分結果を選び直すなら、条件の再集約・結論・3 表の扱いを定める追加の consumer が必要です。現行の接続としては存在せず、成立性や同値性も今回実証していません。

**7. 条件 7 は未充足であり、既知の gate 閉と整合する。**

`docs/phase3-8c-preregistration.md:248–256` は、H1/H2 の登録値、完全 block、judge・3 表、validator の production 到達を要求します。§5 は `:208` で未記入です。

要求を満たす接続がないことは、条件 7 が既に充足したという主張とは食い違いますが、**未充足なら発効しないという契約とは整合します。** D649 の既知の production caller 不在・意図的 fail-closed (`docs/decisions.md:25923–25925,25943–25950`) を具体化する所見です。新たな誤受理欠陥の実証とは扱いません。

現行コードでは `SATISFIABLE_CONDITION_IDS` は空集合ではなく `{C10}` です (`s8c_preregistration_evidence.py:3336`)。C07 は依然対象外で、許可外の SATISFIED は ERROR へ倒されます (`:3446–3453`)。

なお、8b §10.2 の「型・単位・範囲は検証しない」 (`docs/phase3-8b-descriptor-design.md:476–478`) と 8c §4 の同趣旨 (`docs/phase3-8c-preregistration.md:178–180`) は、現行の部分的な値 validator を網羅した説明ではありません。ここから「値 validator 自体が無い」とは導けません。

**8. 対応表は入力形状・適用・接続・権威・閉鎖状態を分ける。**

提案表と結論文を以下に示します。不存在の行には、単独の file:line を不存在の証拠として置くのではなく、検索範囲・コマンド・検出結果を併記します。

## 親 brief との突き合わせ (一致 / 食い違い / 見落とし / 過剰断定)

**一致**

- 親表 1・2・3・5・6・7・8・10 の中心的な読みは一致。
- 親表 4 は「rr80/rr20 の正規対応を judge 自身が知らない」という意味で一致。
- 親表 9 の凍結コードと registry 導出は独立導出で一致。成果物 JSON は brief 後の追加確認でも一致。
- P1 の「未接続」、P3 の「条件 7 未充足という既知の閉鎖状態」は一致。
- P4 の decisions fragment 不要は、今回が接続確認であって新規裁定ではないという scope と整合。成果物の作成・検査は親の担当であり、この段では実施していない。

**食い違い・参照修正**

- 親表 3 の `for holdout_id in holdouts:` は `:1436` ではなく **`:1434`**。`:1436` は off cell の取得。
- 親表 1 の全 field を裏付ける範囲は `:129–141` では不足し、**`:129–143`** が必要。
- 親表 8 の「欄定数の読み手は validator 登録のみ」は厳密には不正確。`:903` の違反報告でも使用する。ただし変換経路不存在の結論は変わらない。

**親表に補う事実**

- generation は workload 文字列を読み、結果と照合する (`s8c_result_judge.py:667,895–900`)。
- `source_binding` は非空文字列の一致であって、§5 の値・stock 参照への接続ではない (`:1626–1628`)。
- 不一致は `delta_min` だけに限らない。事前登録は `n` と `sd_max` も holdout 別に表現できる一方、judge の完全 block は共通 `params.n` (`:388–403,1880–1882,1992`)、registry は全 trial の共通 `n` を要求する (`trial_registry.py:800–801`)。
- D649 当時と異なり、現行の充足許可集合は `{C10}`。C07 が閉じているという結論は維持される。

**過剰断定を弱める箇所**

- **P2:** 「2 回呼び分けは成立しない」は「単一 holdout の manifest に分割する案」に限定する。完全 manifest の二重評価と部分結果の再集約まで不可能とは言えない。
- **P2 の二択:** 「holdout 軸を追加する／2 値を 1 値へ潰す」の二択は網羅的ではない。単一 holdout 契約への変更や、新 consumer による二重評価・再集約も設計候補になり得る。どれも現行接続ではない。
- **P1:** 型の非対称だけでは caller 不在まで証明できない。production 検索結果を合わせて根拠とする。
- 「gate は閉じていて測定は起きていない」は、今回の静的確認から測定履歴全体までは導けない。「C07 が充足を許さず、今回も誤受理・測定結果を実証していない」とする。
- 数値が偶然同じ場合まで「単一値では絶対に再現不能」とはしない。欠けているのは holdout 別値を保持して届ける一般の契約である。

## insight の対応表 (提案)

insight 冒頭には親方針どおり `authority: none` / `default_effect: no-state-change` を置きます。表内の Python ファイルは `orchestrator/campaign/` 配下です。

| 主体 | 現物 file:line | 読み |
|---|---|---|
| 値規則・訂正 | `docs/decisions.md:50301–50308,62725–62735` | 各 holdout 自身の stock 参照×0.03。旧ラベルは追補で訂正。 |
| 凍結側の権威 | `s8b_holdout_freeze.py:101–103`、`output/s8b-freeze/holdout_freeze.json:40–41,307–308` | H1=rr80、H2=rr20。 |
| registry の束縛 | `trial_registry.py:83–107,780–801,1678–1688` | 凍結から対応を導出し、trial 集合と runtime workload を検査。 |
| §5 の形・現状 | `s8c_preregistration.py:135–137,909–925`、`docs/phase3-8c-preregistration.md:208` | H1/H2 別 block を要求。現物は未記入。 |
| §5 値 validator | `s8c_preregistration.py:833–837,931–961` | 型・有限性・符号、単位／向きの非空文字列を検査。stock 参照由来は検査しない。 |
| judge 入力・検証 | `s8c_result_judge.py:129–143,293–315,1959–1964` | holdout 軸なしの object 1 個。単位／向きは定数と照合。 |
| formal 適用 | `s8c_result_judge.py:1434–1437,1550,2010–2012` | 各 holdout に同じ `delta_min`・`sd_max`。 |
| generation 適用 | `s8c_result_judge.py:1900–1907,1973–1975` | 同じ object を共通対比評価へ渡す。 |
| judge のラベル知識 | `s8c_result_judge.py:353,379–384,665–690,893–909` | manifest 由来。generation の workload 照合はあるが、凍結対応の知識はない。 |
| 登録元束縛の限界 | `s8c_result_judge.py:1626–1628` | `source_binding` 文字列一致。§5 値や参照 artifact の照合ではない。 |
| §5→judge の橋 | `orchestrator/tests/test_s8c_result_judge.py:104,573`、`s8c_preregistration_evidence.py:3037–3078`、問い 3 の検索記録 | 構築はテスト、C07 は AST 参照。production 変換／caller は検索で未検出。 |
| 分割呼出し・反復数 | `s8c_result_judge.py:344–345,380–384,388–403,645–646,682–690`、`trial_registry.py:800–801` | 単一 holdout 分割は契約外。反復数も共通値の制約がある。 |
| 条件 7 と現在の閉鎖 | `docs/phase3-8c-preregistration.md:248–256`、`s8c_preregistration_evidence.py:3336,3446–3453` | 要求は未充足。現行許可集合 `{C10}` に C07 は含まれない。 |
| 既裁定との関係 | `docs/decisions.md:25923–25925,25943–25950,62763–62770` | 既知の未接続・fail-closed の具体化。逆割当／誤受理の実証ではない。 |

## 結論文 (提案)

> 現行リポジトリを静的に確認した結果、事前登録 §5 は H1/H2 別の対比パラメータ block を要求する一方、`judge()` は holdout 軸のない `_ContrastParams` 1 個を受け取り、formal・generation の両経路で同じ `delta_min` を各 holdout に適用している。§5 の block を判定器用 object に変換する production コード、および対象 `judge()` の production caller は、記載した探索範囲では見つからなかった。
>
> したがって、D1640/D2049 の「各 holdout 自身の stock 参照から定めた `delta_min = 0.03 × R_h`」を holdout 別値として届ける現行 production 接続は確認できず、所見の型は「未接続」である。H1 に rr20 の値が渡る逆接続や、それによる誤受理を実証したものではない。条件 7 の未充足は既知の gate 閉と整合し、本確認は値の記入・測定・接続実装・照合 gate の新設を認可しない。

## 裁定へ返す候補 (実装しない。変えるべき箇所の列挙)

1. **登録値から consumer への接続の所在。**  
   `s8c_preregistration.py:833–837` の値処理から、登録済みの H1/H2 block を取得して判定器へ渡す変換／production caller をどこに置くか。

2. **holdout 別値を保持する入力・適用契約。**  
   `_ContrastParams`、`judge()`、`_validate_contrast_params`、`_evaluate_contrast`、formal／generation 双方の引渡し箇所。既存の共通値契約との互換性も含めて決める。値を単純に 1 個へ潰す案は、一般に D1640 と同値ではない。

3. **`n`・`sd_max` の扱い。**  
   §5 の holdout 別表現に対し、共通 `n` とする制約を明確にするのか、完全 block・registry の契約まで変更するのか。`delta_min` 接続の名目で自動的に一般化しない。

4. **登録元・ラベルを何から引き継ぐか。**  
   現在の opaque `source_binding` と、登録内容・manifest の関係を接続設計で定める。workload 対応は既存の凍結定義から引き継ぐ。参照 artifact の holdout・条件・算出値を結ぶ新規照合は、項 12(b) により今回の候補へ混ぜない。

5. **二重呼出し案を採る場合の追加契約。**  
   単一 holdout manifest を許す変更、または完全 manifest を二重評価して部分結果を再集約する consumer の設計が必要。現在の全体 `conditions`・`conclusion`・公式状態・3 表との整合を定めず、代替が成立したとは扱わない。

6. **条件 7 と記入解除条件への反映。**  
   将来接続を実装する際に必要な文書上の説明と既存評価器の扱いを決める。今回、C07 の許可集合や gate を変更する提案にはしない。

## 総括

独立導出は親の「未接続」という中心結論に一致しました。親 brief には、P2 の二回呼出し不能の範囲、generation の workload 照合、共通 `n`、現行 `{C10}`、参照行番号を補正する必要があります。

この段の成果は上記の対応表・結論・裁定材料です。実装変更、値の記入、検査・gate・台帳の新設、テスト実走は行っていません。