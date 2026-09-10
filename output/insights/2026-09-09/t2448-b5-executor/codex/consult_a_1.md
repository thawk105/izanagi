## 完走述語を緩める経路

1. **real — 軸全体の完走述語が実装対象にない。** `plan_1.md:128-130` は公開面を `run_leaf` までとし、`plan_1.md:244` は axis status と bundle manifest を明示的に除外している。一方、部分登録 §5.2 は 1622 主 query、演算子 control、anchor 包含 control、全補助探索、感度監査、分類、未解決 `要裁定 == 0` の論理積を要求する。

   - 成果物影響: 一部 leaf の `完走` を軸の完走と誤認でき、受理集合と `RW3` の主張が広がる。
   - 是正: 実行器内に、sealed catalog・anchor registry から期待 ID 集合を再導出する軸集約器を置く。分類層まで本 wave に含めないなら `retrieval_complete` までしか出さず、`RW3` は常に出力不能とする。

2. **real — control request の完走と control の発火が混同されている。** `plan_1.md:200` は control stream に条件 2・3・5・6を適用するだけで、部分登録 §4.1 の和集合包含、積集合包含、cutoff 部分集合、DBLP の client-side 和・積の関係を評価する手順がない。予定 test にもこれらの集合関係の負例がない (`plan_1.md:363-373`)。anchor が主 query の登録済み和集合に含まれるかという部分登録 §4.3 の評価もない。

   - 成果物影響: 14 request が正常終了しただけで control を「発火」と記録でき、実行記録の control 値と `RW3` の受理集合が変わる。
   - 是正: request 完走値と `B5-OP-*` / `B5-ANC-*` 発火値を別型にし、登録済み work-ID 集合から各関係を再計算する。全 member の exact set と、不発時の軸 `未完走` を負例で固定する。

3. **real — 実行証拠の exact-set 検証がない。** plan は create-only 出力と schema validation までであり (`plan_1.md:128`, `plan_1.md:371`)、raw body の再 parse、request の再構築、全ページの再評価、欠落・余分な証拠の検査を持たない。軸 1 の先例は manifest の exact set を作り (`axis1_search/runner.py:1107-1152`)、offline verifier が raw body を再 parse している (`axis1_search/validator.py:1334-1464`)。

   - 成果物影響: schema-valid な自己申告だけを残し、ページや raw body を欠落させても完走記録として読める。
   - 是正: B5 実行器の内部に exact-set manifest と offline 再評価を含め、それらの実装・schema も registration seal の対象にする。

4. **refuted — `itemsPerPage` / `meta.per_page` / `@sent` を実数へ流用する経路は、プラン上は塞がれている。** parser は container の `len` を `actual_count` にし (`plan_1.md:41-43`)、条件 3 は非終端実数、offset 最終式、安定総数と distinct ID 数を別々に検査する (`plan_1.md:180-198`)。DBLP `@first`、cursor parent、ページ間重複、最終ページを含む総数 drift の負例も予定されている (`plan_1.md:316-343`)。

   - 成果物影響: 記載どおり実装されれば、この経路による受理集合の拡大はない。
   - 是正: 予定された負例に加え、最終ページでも総数 field 欠落と distinct ID 不一致が必ず赤になることを維持する。

## 事後登録になる経路

1. **refuted — 過去の生応答を fixture として複製すること自体は事後登録ではない。** `plan_1.md:250-263` は生応答を応答形の fixture に限定し、`plan_1.md:283-293` は件数、cursor、ID、期待 AST、echo を凍結文由来の独立値として先に固定するとしている。これは部分登録 §2.3、§5.3の境界に合う。

   - 成果物影響: fixture を oracle に転用しない限り、期待値や受理集合は変わらない。
   - 是正: test の期待値を production builder、parser 出力、fixture の `len` から生成しない。期待 AST と DBLP echo も test 側の独立 literal または独立実装で照合する。

2. **real — 凍結文から一意に読めない値を、plan の推奨値で実装できる余地が残る。** content type、timeout、retry 対象、OpenAlex 終端、arXiv echo、DBLP lookup の中間形は未裁定と明記されている (`plan_1.md:392-407`)。これらは条件 1・2・6や request policyを変えるため、単なる実装詳細ではない。

   - 成果物影響: author が推奨値を採用すると、実行記録の状態値と完走受理集合が、凍結後に実装者が選んだ契約へ変わる。
   - 是正: 実装では未登録 policy を既定値へ落とさず、`unregistered_policy` として issuance 前に失敗させる。値の確定は scope 外の裁定パッケージ候補であり、新しい後継凍結物または人間の明示裁定が必要である。

## fail-closed の穴

1. **real — live preflight が ID lookup 30 件だけへ縮退している。** `plan_1.md:82-116` は anchor lookup しか定義しない。しかし部分登録 §5.3 は、固定済み request の構文・echo・availability・総件数・page 数・rate limit の観測を要求する。閉包登録 §4 も、引用・著者経路の request 形と paging を live preflight の検証点にしている。

   - 成果物影響: 主 query や補助探索の構文が現在成立しなくても走行を開始でき、実行記録は登録済み preflight を満たさない。
   - 是正: 現在の 30 lookup を `anchor membership preflight` と限定する。残りの exact request 集合が裁定されるまで production preflight は必ず失敗させる。集合の新規裁定は scope 外の裁定パッケージ候補とする。

2. **real — runner と preflight 証拠の束縛方法が未指定である。** `plan_1.md:114` は「結果が真になる前に request を出さない」とだけ書き、bool、caller 作成 record、古い preflight record を排除していない。軸 1 の先例は実際に bool を受け付ける (`axis1_search/runner.py:1519-1523`) ため、写経すると `True` だけで迂回できる。

   - 成果物影響: lookup を一件も行わず走行を開始でき、軸全体の開始受理集合が無制限に広がる。
   - 是正: production entrypoint 自身が registration preflight と live preflight を順に実行し、exact 30 member、sealed registry、同じ registration seal、時刻つき raw evidenceを持つ構造化結果だけを受ける。bool と外部 record 注入は test-only private seam に限定する。

3. **real — 3 値のどれにも入らない正常応答の既定動作が未裁定である。** 例として DBLP の HTTP 200 JSON、`@total > 0`、当該 DOI 無しは closure registration §2.4(b) の `収録` にも `非収録` にも合わない。plan 自身も erratum が必要と認める (`plan_1.md:399-400`)。

   - 成果物影響: 実行記録の値が `非収録`、`不達`、例外のいずれになるか実装者次第になる。
   - 是正: 無断で三値へ丸めず、分類不能として `passed=False`、`may_start_run=False` を返す。三値への割当ては前項と同じ裁定待ちにする。

4. **refuted — member の削除と一件だけの成功による通過は、plan 上は明確に禁止されている。** exact 16/1/13、欠落・余分・重複の拒否、全件が `収録` の場合だけ開始可とされる (`plan_1.md:84-114`)。これは closure registration §2.4(c) と整合する。

   - 成果物影響: 記載どおりなら `非収録` を見て member から外すことによる受理集合の拡大はない。
   - 是正: registry membership を lookup 結果から再生成する APIを置かず、member exact-set testを維持する。

## D1895 との整合

1. **real — production 面が leaf 単位しかなく、登録済み全体集合と実行順を強制しない。** `plan_1.md:130` の公開面は `run_leaf` で、部分登録 §5.3 の「索引順、query ID 辞書順、枝を足さない・削らない」を強制する軸実行面がない。さらに anchor 依存の 61 stream を明示的に scope 外としている (`plan_1.md:404`)。

   - 成果物影響: caller が leaf、枝、control、補助探索を選別でき、実行記録の取得集合が登録集合より狭くなる。
   - 是正: `run_leaf` は内部 primitive とし、完走を名乗れる production 面は exact schedule を再導出して全項目を処理するものだけにする。61 stream は既存 closure record と sealed registry から導出でき、凍結 catalog の変更は不要である。

2. **real — DBLP の cutoff 適用が実装計画から抜けている。** 部分登録 §2.2 は全 record を取得した後、`year <= 2026` を client 側で判定し、欠落は除外せず `要裁定` とする。plan は year の parse だけを書き (`plan_1.md:35`)、runner 条件と test に cutoff 内外の分離がない (`plan_1.md:174-200`, `plan_1.md:304-373`)。

   - 成果物影響: 2027年以後の record が候補集合へ混ざるか、逆に総数照合前に削られて query が誤って `未完走` になる。
   - 是正: raw retrieval ledger と cutoff 後の候補集合を分離する。総数・重複条件は全 raw occurrence で評価し、`year > 2026` は候補外、欠落・不正 year は record を保持した `要裁定` とする。

3. **real — `LeafSpec 正規化` の許容範囲が定義されていない。** `plan_1.md:123` は catalog entry の「正規化」とだけ書く。送信 template の byte equalityは `plan_1.md:146-151` が守るが、term group や期待 AST を lower-case、set 化、空 group 除去することは明示的に禁じられていない。D1895 の逐語は検索構造を登録どおり走らせることを要求する (`rulings-verbatim.md:41-45`)。

   - 成果物影響: 送信 bytes と異なる緩い echo/AST を受理し、条件 1 の受理集合が広がる。
   - 是正: `resolve_leaf` は validate-only とし、語、語 ID、group の順序と多重度、大小文字、ハイフンを byte-preserving に保持する。正規化は部分登録 §5.1 が列挙した echo 比較だけに限定する。

## seal の漏れ

1. **real — exact file list はあるが、実行 surface の directory exact set になっていない。** `plan_1.md:62-80` は列挙 path と fixture 25件だけを束縛する。新しい `.py`、別 schema、production wrapper を package 周辺へ追加しても、その path を status/tree 対象へ渡さなければ検出できない。軸 1 の先例は directory を walk して extra path も拒否している (`axis1_search/validator.py:730-746`, `axis1_search/validator.py:801-807`)。

   - 成果物影響: seal 後に追加した未束縛 entrypoint や helper を実行でき、「実行器の bytes を束縛した」という主張が偽になる。
   - 是正: `orchestrator/axis_b5_search/`、B5 schema 群、fixture root の実 file setを commit treeとworktreeの双方で exact 比較し、production entrypoint も同じ集合へ含める。

2. **real — 完走を担う production entrypoint が未定義なので、その bytes も seal できない。** plan の path 集合には leaf runner はあるが、全 query・control・補助探索を列挙し、live preflight を所有する CLI または関数がない (`plan_1.md:118-130`, `plan_1.md:62-80`)。

   - 成果物影響: 実際の呼出し側が leaf 選択と preflight 通過を決め、seal 外の bytes が実行記録を左右する。
   - 是正: 軸全体の唯一の production entrypoint を runner package 内へ置き、seal 対象にする。任意 leaf 実行は完走主張を生成しない内部面に限定する。

3. **refuted — seal record が自分自身を hash する自己参照はない。** `plan_1.md:51-59` は外部の registration commit treeを信頼根にし、実行時 seal record 自体を binding から除外している。これは自己 hash ではない。

   - 成果物影響: この点による seal 不成立や受理集合の変化はない。
   - 是正: 現方針を維持し、seal record の digest fieldを後付けしない。

## 親 brief への反論

1. **P1 は refuted。** B5 専用 parser は妥当である。軸 1 parser は offset 次位置を `position + len(elements)` で作り (`axis1_search/parsers.py:189-191`, `axis1_search/parsers.py:382-384`)、軸 1 validator は `itemsPerPage` や `@sent` を条件 3 に使う (`axis1_search/validator.py:309-312`)。そのまま import するとB5契約へ不適合で、依存 file も seal 対象に増える。

   - 成果物影響: 自前 parser を sealed にすれば、B5 の実要素数と固定 step の受理集合を維持できる。
   - 是正: P1 を維持し、軸 1 は写経元にだけ使う。

2. **P2 は refuted。** 軸 1 runner は catalog policy と fallback を読む (`axis1_search/runner.py:329-357`) が、B5 catalog にはそれらがない。B5専用の sealed policyを持つ判断は正しい。

   - 成果物影響: P2 を維持すれば、軸 1 の別 epoch の policyで request・retry・完走値が変わることを防げる。
   - 是正: 自前 runnerを維持する。ただし未裁定 policyを推奨値で埋めない。

3. **P3 は real。ただし registration preflight だけを閉じるという狭い目的では成立する。** 部分登録 §5.3 は窓をまたぐ実行に機械可読 checkpointを要求し、§5.1 は複数窓にまたがる枝へ独立2走の digest一致を要求する。plan は両方を除外している (`plan_1.md:202`, `plan_1.md:244`)。軸 1 先例は WAL、outcome-unknown、resume requestを明示的に持つ (`axis1_search/checkpoint.py:121-250`)。

   - 成果物影響: 本 wave の成果物は「registration preflight を閉じられる leaf library」に留まり、実行記録は生成せず、`RW3` の主張は一切進まない。
   - 是正: scope 外のままなら成果物名と受入をそのように狭める。完全な「実行器」を名乗るなら checkpoint、resume、独立2走の束縛が必要である。

4. **real — brief の完了判定は live preflight の完了を過大に表現している。** 30 member の requestを fixture で組み立てられること (`brief.md:11-12`) は、部分登録 §5.3 の live preflight 全体の代わりにならない。

   - 成果物影響: registration preflight rc=0 と request builder の緑だけで、実行可能になったと誤記される。
   - 是正: 受入値を「registration preflight rc=0」と「anchor lookup builder/classifier の静的検査」に限定し、live preflight は未実施・未完備と記録する。

5. **本 wave で live preflight を実行しない裁定は refuted、すなわち親判断が正しい。** closure record §0 は registration preflight、live preflight、人間の実行認可を別の残条件としている。実装と fixture の静的検査に live request は不要である。

   - 成果物影響: 実行しなければ現在の索引状態を見た値は増えず、軸は正しく `RW0`、実行記録なしのまま残る。
   - 是正: 本 wave では実行しない。実行にはユーザー本人の認可が必要で、実行すると外部 request、rate/quota 消費、時刻つき観測、結果を見たという事実が不可逆に生じる。

## 総括

現 plan は B5 専用 parser、実要素数、固定 offset、cursor parent、総数 drift、重複拒否、member fail-closed の局所設計は堅い。一方で、現状のまま「軸 B5 の実行器」として受理するのは不可である。

主な blocker は、live preflight の縮退、軸全体の exact-set 実行・control 発火評価・61補助 stream の欠落、DBLP cutoff の欠落、checkpoint/resume の除外、実行証拠の offline 再検証不在、seal 外の production entrypoint である。これらを本 wave に入れない場合、成果物は「registration preflight と leaf primitive」に明確に狭め、実行記録を作らず、`RW3` に関する主張を一切進めないのが正しさ境界である。