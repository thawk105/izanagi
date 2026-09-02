## M12 再定義の検査

- **refuted 候補: M12 が恒真化する。** plan は実物の `P._fraction_token((1,3))` を直接呼ぶ。入力検査後、分母 3 が残って `ArithmeticError` へ到達する (`s2-plan.md:22-24`, `p3_b4_raw_record_producer.py:341-359`)。この分岐を削除すると後段は `1 // 3 == 0` から整数 `0` を返すため、例外期待は確実に落ちる (`p3_b4_raw_record_producer.py:360-368`)。実体も名指しされており、registry と producer の両方を性質 stub にして緑になる検査ではない。

- **refuted 候補: 上位の registry 検査が先に落とす。** 直接呼出しには registry が介在しない。通常 publication を作ってから `_fraction_token` を patch する第 2 段も、正常な registry を通した後の production 呼出しを検査する (`s2-plan.md:24-31`, `test_p3_b4_raw_record_producer.py:785-793`)。

- **real 候補: `DECIMAL_NOT_TERMINATING` の 2 箇所目は未検査。** plan の常時送出 patch は `_derive_b4_attempt_data()` 内の最初の呼出しと catch だけを通る (`p3_b4_raw_record_producer.py:1530-1551`)。final assembly は先に同関数を再実行してから、もう一度 `_fraction_token` を呼ぶため、`p3_b4_raw_record_producer.py:1967-1974` の catch には到達しない (`同:1928-1942`)。通常の決定的な実装では同じ値に対する 1 回目が成功して 2 回目だけ失敗することはなく、後者は自然入力では実質到達不能である。

- 後者も固定する最小追加は、正常 artifact を 1 件 publish した後、呼出し 1 回目だけ実 `_fraction_token` へ委譲し、2 回目に `ArithmeticError` を送る side effect で `assemble_b4_raw_analysis()` の完全な拒否署名を確認すること。これは M12 の恒真性修正には必須でないが、2 箇所目の catch を検査するなら必要である。

## 既存正例の検算

repo 内の構築点、計算値、`replace`、parametrize、wire loader を追跡した限り、親の「既存 literal では M12 の `(1,3)` だけ」は、**tracked test/code に限定すれば正しい**。

| 入口 | 実際の値 | 判定 |
|---|---|---|
| prereg consumer 自己検査 | `1000 + index` (`p3_b4_analysis_prereg_consumer.py:757-804`) | 分母 1 |
| ledger tests | `(10_000 + index, 1)` (`test_p3_b4_analysis_ledgers.py:23-48`) | 分母 1 |
| analysis-path tests | `100` (`test_p3_b4_analysis_path.py:77-107,207-228`) | 分母 1 |
| issuer tests | `(10_000 + index, 1)` (`test_p3_b4_prerun_issuer.py:30-62`) | 分母 1 |
| raw-producer tests | `(100_001 + 10*index, 10)` (`test_p3_b4_raw_record_producer.py:109-126`) | 既約分母 2 または 10 |
| raw override | `(1,3)`, `(10_000,1)` (`同:1138-1158`) | 前者だけ非有限十進 |

- **refuted 候補: 既存正例が落ちる。** 上記の registry 到達値はすべて有限十進である。`reference_tps=None` の parametrize は `_attempt_is_eligible` の直接検査だけで、seal されない (`test_p3_b4_analysis_ledgers.py:470-497`)。tracked JSON/JSONL に registry 用 literal も見つからなかった。

- **real 候補: この全数は runtime 受理面の全数ではない。** `issue_b4_prerun_publication()` は caller 提供の任意の `Sequence[B4ScheduledAttemptInput]` を受ける (`p3_b4_prerun_issuer.py:707-725,777-780`)。さらに registry loader は wire の任意の canonical ratio を復元する (`p3_b4_analysis_ledgers.py:702-760`)。analysis path と publication loader の双方がこの入口を使う (`p3_b4_analysis_path.py:124-137`, `p3_b4_prerun_issuer.py:1046-1054`)。これは本変更が意図して狭める runtime surface であり、「既存 fixture に無い」ことから入口不在へ一般化はできない。

## 述語の一致

- 通常範囲では、plan の判定順序は producer と一致する。registry は `_exact_ratio` と正値検査を先に行い (`p3_b4_analysis_ledgers.py:263-276,341-343`)、plan はその直後に分母判定を置く (`s2-plan.md:80`)。producer も型、0 分母、正値を先に拒否してから分母を判定する (`p3_b4_raw_record_producer.py:341-359`)。

- `bool` は両側とも exact-type 検査で拒否される。registry の bare `True` と tuple 内の `True` は `type(...) is int` を満たさず (`p3_b4_analysis_ledgers.py:263-275`)、producer も同様である (`p3_b4_raw_record_producer.py:342-347`)。**refuted 候補: bool による不一致。**

- registry の型域は `Fraction | int | tuple[int,int]` だが (`p3_b4_analysis_contract.py:94`)、producer の直接入力は tuple のみである。`1` や `Fraction(1,2)` は producer へ直接渡せば拒否されるが、registry は seal 時に canonical tuple へ変換する (`p3_b4_analysis_ledgers.py:439-458`)。manifest もその tuple を渡す (`同:1077-1083`)ため、**end-to-end の数値集合には型差による不一致はない**。

- 非既約 object `(2,6)` は Fraction 化後に新検査で非有限十進として落ちるが、wire `[2,6]` はそれ以前に `"wire reference_tps is not reduced"` で落ちる (`p3_b4_analysis_ledgers.py:288-302`)。同じ数値でも表現境界によって拒否理由が違う。`(-1,-2)` も object/producer では正の `1/2` として受理される一方、wire では負分母が canonical 違反になる。これは既存 codec の仕様である。

- **real 候補: 巨大な有限十進で厳密一致しない。** 具体値 `(1, 2**6200)` は plan の分母 2/5 判定を通る。read-only の直接 probe では現行 registry の hash と seal が成功した。一方 `_fraction_token` は token 化した `5**6200` を文字列化する `p3_b4_raw_record_producer.py:366` で、現在の 4300 桁制限による `ValueError` を送出した。これは publish 側では `DECIMAL_NOT_TERMINATING` でなく `EVIDENCE_SCHEMA` に写る (`同:1542-1551`)。したがって「有限十進述語」と実 `_fraction_token` の操作上の受理集合は厳密には一致せず、本変更後も seal できるが publication で必ず落ちる値が残る。

## 変異の帰属

`(1,30)` は既約であり、`_ratio_from_payload([1,30])` は reduced 検査を通る (`p3_b4_analysis_ledgers.py:288-302`)。candidate の他 field は既存の正しい `_attempt` 由来なので、`scheduled_attempts_sha256()` で発火するのは新検査だけである (`s2-plan.md:77-80`)。

| 変異 | 殺す検査 | 判定 |
|---|---|---|
| 述語を恒真化 | 負例 `(1,3)`, `(1,30)` が例外を出さない | 殺せる |
| 述語を恒偽化 | 正例 `(1,10)` の seal が失敗 | 殺せる |
| 5 を除く処理を削除 | `(1,10)` の残分母が 5 | 殺せる |
| 2 を除く処理を削除 | `(1,10)` の残分母が 2 | 殺せる |

- **refuted 候補: 指定された 4 変異に生存変異がある。** plan の正例・負例で全て殺せる (`s2-plan.md:75-81`)。
- **real 候補: この matrix は巨大な有限十進の操作上の不一致を検出しない。** 最小追加は `(1,2**6200)` を producer-unrepresentable control とし、seal 前に拒否されることを固定する検査である。受理集合を広げる必要はない。

## 親 brief の欠陥

- **P1-1 は妥当。** `_validate_attempt` 限定なら standalone manifest codec を変更せず、完全な registry/manifest 組は registry 再検証を通る (`p3_b4_analysis_ledgers.py:1042-1053`)。ただし「封印時だけ」という時間的説明は不正確で、最初の拒否は seal より前の scheduled hash で起きる (`p3_b4_prerun_issuer.py:724-731`)。plan の訂正が正しい。

- **P1-2 は strict な一致要求の下では real 候補。** 親は分母から 2/5 を除く処理だけを独立実装するとしている (`parent-brief.md:56-58`)。それでは `_fraction_token` の後段 token 化失敗を再現せず、巨大分母の不一致を残す。共有 helper が必ず `as_b4_exact_fraction` と結合するという根拠もコードにはない。少なくとも producer の操作上の tokenability を反映する別拒否が必要で、親の「述語 1 つだけ」という scope (`parent-brief.md:14-16,27-28`) は不足する。

- **real 候補: 実測値の一般化が過大。** 親は 443,911 観測と 2,010 exact 比を「ユーザー提示」と正しく帰属し、再測しないとも明記する (`parent-brief.md:76-77`)。したがって親自身の再実測ではない。443,911 件の throughput は float として生成される (`benchparse.py:45-62`, `pipeline.py:285-294,1738-1746`)ため、非有限十進 0 件そのものは exact scheduled ratio の直接測定ではない。そこから exact 前身不存在へ進む部分は推論である (`s4-ruling.md:60-80`)。

- **real 候補: 「production の既存 artifact では発火しない」は空集合を混ぜている。** production の封印済み registry は 0 件で、2,010 値は全て pytest fixture である (`s4-ruling.md:19-37`)。したがって `parent-brief.md:94-99` の production artifact 非発火は registry については恒真であり、443,911 件の別母集合からの推論でしかない。

- **real 候補: 測定根拠文書の exact な key 数は誤り。** `s4-ruling.md:74-76` は WAL commit payload を 4 key だけとするが、実コードは `verify_configs`、build 関連 hash、contract hash 等も記録する (`pipeline.py:1742-1765`)。追加 key は高精度 throughput 材料ではないため結論を直ちに反転しないが、実測説明としては誤りである。

- **real 候補: 親の anchor 誤記。** `parent-brief.md:39` は `seal_scheduled_attempt_registry` を ledgers `:446` とするが、実定義は `p3_b4_analysis_ledgers.py:662`。`:446` は `_normalize_attempts` 内の `_validate_attempt` 呼出しである。

- **refuted 候補: scope が仮想リスクへ過剰拡張。** closure 検査は ledger 自身が source closure member で、digest が live bytes から計算されるため実成果物に直結する (`p3_b4_analysis_path.py:67-73,503-536`)。manifest codec、contract、adapter、値域再測定を scope 外とした判断も本題に沿う (`parent-brief.md:101-107`)。

- **疑い:** 443,911 件、2,010 件という件数自体は、射影された測定 artifact が無いため今回は再現確認できない (`parent-brief.md:76-77`, `s4-ruling.md:45-56`)。pytest も実行しておらず、緑は主張しない。

## 所見一覧

- **real 候補 R1:** `(1,2**6200)` が registry を seal できる一方 `_fraction_token` で失敗し、述語の厳密一致と wave の目的を破る。`p3_b4_analysis_ledgers.py:341-359,439-481`; `p3_b4_raw_record_producer.py:341-372,1542-1551`。
- **real 候補 R2:** M12 は `DECIMAL_NOT_TERMINATING` の publish 側だけを検査し、assembly 側を通らない。`s2-plan.md:22-31`; `p3_b4_raw_record_producer.py:1928-1974`。
- **real 候補 R3:** production registry 非発火の主張は、production registry 0 件なので恒真。`parent-brief.md:94-99`; `s4-ruling.md:19-37`。
- **real 候補 R4:** P1 の独立した分母判定だけでは producer の操作上の受理集合を再現できず、scope が不足。`parent-brief.md:14-16,56-58`。
- **real 候補 R5:** 親の seal anchor が誤っている。`parent-brief.md:39`; `p3_b4_analysis_ledgers.py:439-446,662-675`。
- **refuted 候補 F1:** M12 再定義が恒真化する。実 `_fraction_token` の分岐削除で落ちる。`s2-plan.md:22-31`; `p3_b4_raw_record_producer.py:341-368`。
- **refuted 候補 F2:** tracked の既存正例が新検査で落ちる。構築点はいずれも分母 1、2、10。`test_p3_b4_analysis_ledgers.py:23-48`; `test_p3_b4_raw_record_producer.py:109-126`。
- **refuted 候補 F3:** `(1,30)` が既存 not-reduced 検査で落ちる。`p3_b4_analysis_ledgers.py:288-302`。
- **refuted 候補 F4:** 指定された恒真、恒偽、2 除去、5 除去の各変異が生存する。`s2-plan.md:75-81`。
- **refuted 候補 F5:** `bool` による registry/producer の不一致。両側とも exact-type 検査で拒否する。`p3_b4_analysis_ledgers.py:263-275`; `p3_b4_raw_record_producer.py:342-347`。
- **疑い S1:** 親から引き継いだ測定件数の再現性。`parent-brief.md:76-77`; `s4-ruling.md:45-56`。

## 総括

- M12 の直接 `_fraction_token((1,3))` 検査は実分岐を刺しており、恒真化していない。
- ただし final assembly 側の同名拒否生成は未検査のまま残る。
- tracked の既存正例は落ちず、指定された 4 変異も全て殺せる。
- 最大の must-fix は、巨大な有限十進 `(1,2**6200)` が registry と producer の受理集合を分ける点である。
- 親の production 非発火主張は空の production registry と float 値域を一般化しており、plan は現状のまま author へ渡せない。