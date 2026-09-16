## 受理集合の表

指定8ファイルはすべて読めました。以下は静的検査結果です。実装・書込み・pytest・変異実走は行っていません。

参照略号：`L`＝`orchestrator/campaign/p3_s4_loop.py`、`KM`＝`orchestrator/campaign/knowledge_manifest.py`、`T`＝`orchestrator/tests/test_p3_s4_loop.py`。brief・plan・rulings は指定された親ディレクトリ内の各ファイルを指します。

表は **plan 案と emit return 後の対案に共通**です。role 有りは argparse が許す `coder-v4-autonomous-k2`、manifest は解決可能なものとし、他の既存 admission・proposal 検査を満たす場合を示します。「通過」は本件の契約による拒否がない意味で、任意の proposal の成功保証ではありません。

| run | emit | manifest 無し・role 無し | manifest 無し・role 有り | 空 sources・role 無し | 空 sources・role 有り | 非空 sources・role 無し | 非空 sources・role 有り |
|---|---|---|---|---|---|---|---|
| 無し | 無し | fixture 通過 | fixture 通過 | fixture 通過 | fixture 通過 | fixture 通過 | fixture 通過 |
| 無し | 有り | emit 通過 | emit 通過 | emit 通過 | emit 通過 | emit 通過 | emit 通過 |
| 有り | 無し | legacy 通過 | **既存 loader 拒否** | legacy 通過 | K2 検査経由 | **従来通過→新規拒否** | K2 検査経由 |
| 有り | 有り | emit 通過 | emit 通過 | emit 通過 | emit 通過 | emit 通過 | emit 通過 |

manifest 無しでは sources 空／非空は定義されず、独立した組合せにはなりません。空 manifest の追加条件は以下のとおりです。

| 空 sources の内容 | run・emit・role の全組合せでの扱い |
|---|---|
| 有効な declared_scope、completed_empty、result_count=0 | 上表の空 sources 列 |
| retrieval_result が無い | 既存 parser 拒否 |
| status が completed_empty でない | 既存 parser 拒否 |
| declared_scope が無い、status/count が不正 | 既存 parser 拒否 |

根拠：`L:1523`、`:2311`、`:2574`、`:2667`、`:2689`、`:2713`、`:2774`、`:2807`、`KM:273`、`:320`、`:326`。無効な role は全経路で argparse が先に拒否します。

D1878 の決定（`verbatim-d1878.txt:3`）に対応する変更は、表中の **run のみ・非空・role 無しの1セルだけ**です。空取得の維持は同ファイル`:4`、無条件の相互必須化を採らないことは`:16`に対応します。emit と fixture の維持は brief`:11`の scope と既存制御フローによります。

## 所見

**1. 親 P1 の「解決直後＋run guard だけ」は過剰拒否になる。**

- **所見:** run と emit を併記でき、現物では emit が優先します。親 P1 のままでは、非空・role 無しの併記起動を新たに拒否します。plan の追加 guard はこれを防いでいます。
- **仮判定:** **real**。
- **根拠 file:line:** brief`:23`、plan`:12`、`:27`、`L:2567`、`:2570`、`:2689`、`:2713`。
- **推奨:** 親 P1 はそのまま採用しない。後述の emit return 後の対案を採用する。

**2. 空取得の救済が不正 manifest を通す懸念は成立しない。**

- **所見:** 空 sources で retrieval_result が無い／completed_empty でない入力は、新 guard より前に parser が拒否します。plan は既存 parser を迂回しません。ただし親の「空 sources と completed_empty は同義」は双方向の主張として強すぎます。parser は非空 sources に completed_empty が付く逆方向の不整合を、この箇所では拒否していません。
- **仮判定:** 迂回懸念は **refuted**。「同義」という一般化は **real**。
- **根拠 file:line:** rulings`:24`、`KM:287`、`:320`、`:326`、`:335`、`:355`、`:487`。
- **推奨:** 「正常に parse された空 sources は completed_empty を要求される」と記す。判定は sources に置き、status に置換しない。逆方向の parser 契約変更は scope 外であり、必要なら別件の裁定パッケージ候補とする。

**3. K2 consumer の緩和・迂回を新設する懸念は成立しない。**

- **所見:** role 有りの run は従来どおり projection と role を loader に渡し、`CODER_CONTRACT_K2`、anomaly、参照 index 検査を通ります。空・role 無しの legacy 経路を維持することも明示裁定どおりです。
- **仮判定:** **refuted**。
- **根拠 file:line:** `L:2311`、`:2319`、`:2348`、`:2235`、`:2244`、`:2248`、`:2774`、`orchestrator/codex_roles/policy.py:521`、`:535`。
- **推奨:** loader・consumer・parser を変更しない。非空＋role K2 の新正例 P は実 loader を通す plan の構成を採用する。

**4. 拒否 message は欠けた flag を示すが、sources 件数を返さない。**

- **所見:** plan の message は「非空」「--coder-role が必要」を示しますが、要求された数値の件数がありません。
- **仮判定:** **real**。
- **根拠 file:line:** plan`:18`、`:19`、`:20`、`KM:113`。
- **推奨:** 同じ `ValueError` に `sources_count={len(resolved_knowledge.manifest.sources)}` と不足 flag を含める。新たな台帳や例外体系は不要。負例 N では件数と flag を確認し、変異の kill は message 差だけに依存させない。

**5. P5 は再裁定ではなく、決定に対する test の追随でよい。**

- **所見:** D1878 の「正例を1件も壊さず」は、全既存 test が無変更で緑になるという読みでは成立しません。しかし identity test 後半の入力は、決定が明示的に拒否対象にした「非空＋role 無し」です。test の目的と拒否対象の argv を区別できます。
- **仮判定:** 文言を全 test に一般化する点は **real**。追加裁定が必須という懸念は **refuted**。分類は **(b)**。
- **根拠 file:line:** `verbatim-d1878.txt:3`、`:9`、`verbatim-entry1527.txt:4`、`T:6524`、`:6569`、`:6586`、`:6589`、`L:1531`、`:1545`。
- **推奨:** 後半 argv だけに role を追加し、前半の role 無し emit 正例を残す。新事実として記録する。production に identity test 用の例外を設ける案は、拒否対象を残し規律2・D1878に反するため退ける。

**6. emit return 後の配置が、受理集合・帰属・scope の総合で優れる。**

- **所見:** plan 案も受理集合は正しいものの、配置によって `not emit` 条件と test C が必要になっています。対案は制御フローで同じ優先順位を保存し、prepare 前拒否も満たします。
- **仮判定:** plan が誤った受理集合を作るという懸念は **refuted**。対案で省ける条件・検査を増やす点は **real**。
- **根拠 file:line:** plan`:5`、`:13`、`:95`、`:133`、brief`:11`、`:14`、`L:2713`、`:2714`、`:2728`。
- **推奨:** `L:2713` の後、`:2714` の前に次を置く。test C と M5-route は採らず、変異登録を配置に合わせて更新する。

```python
if (
    a.run_iteration
    and resolved_knowledge is not None
    and resolved_knowledge.manifest.sources
    and a.coder_role is None
):
    raise ValueError(
        "--run-iteration: "
        f"sources_count={len(resolved_knowledge.manifest.sources)}; "
        "--coder-role coder-v4-autonomous-k2 が必要"
    )
```

両案の差は、複数の不正条件が重なった場合の**拒否順序**にはあります。対案では既存 build opt-in・環境 admission が先です（`L:2671`、`:2679`）。受理集合は同じであり、「あらゆる副作用前」ではなく「knowledge campaign の prepare・receipt 前」を保証する、と表現するのが正確です。

## 変異の帰属

記号は plan`:117`の定義を使用します。N＝新負例、E＝既存空・role 無し、K＝既存空・role K2、P＝新非空・role K2、I＝identity 共有、C＝新併記 emit 正例です。以下の kill 集合は静的予測で、実測結果ではありません。

| 所見 | 仮判定 | 根拠 file:line | 推奨 |
|---|---|---|---|
| **M1 条件削除:** 有効な flattened proposal なら loader の相互必須検査は両方 None で通り、N の drive 到達失敗に帰属できる。 | **refuted**：別層に隠される懸念 | plan`:55`、`:56`、`:59`、`L:2311`、`:2775` | plan の N を採用。K2 wrapper をそのまま負例に使わない。 |
| **M2 sources 反転:** N が通ってしまう過少拒否と、E の過剰拒否を検出する。 | **refuted**：帰属不明の懸念 | plan`:130`、`T:7209`、`:7234` | 期待失敗集合 N・E を維持。 |
| **M3 role 反転:** 親が挙げた K は sources 空で短絡し、殺せない。N・P・修正後 I が失敗する。 | **real**：親の kill 予測誤り | brief`:26`、plan`:131`、`T:7245`、`:6524` | K を期待失敗集合から外し、N・P・I とする。 |
| **M4 return 0:** drive 未到達のまま成功扱いになるため、殺すのは N の `raises`。 | **real**：「未到達 assert が殺す」とする親の説明誤り | brief`:26`、plan`:60`、`:132`、`:135` | `return 0` に固定し、「必要な拒否が発生しない」が赤理由と記す。 |
| **M4 drive 後への移動:** N の drive spy が即 fail するため、移動後の拒否には達しない。移動先の曖昧さも残る。 | **real**：二択のままでは変異が未確定 | brief`:26`、plan`:59` | plan が選んだ return 0 版だけを登録する。 |
| **親 M5 run guard 除去:** 親の元配置なら I 前半が検出するが、plan の `not emit` を残すと I・C は検出しない。 | **real** | plan`:13`、`:139`、`T:6546` | 元の期待 kill を流用しない。 |
| **plan M5-route:** 2つの経路条件を除去すると I・C が新 guard で拒否される。複数 node が赤でも、理由は同じ経路限定の消失。 | **refuted**：複数 node だけを理由とする単一理由性違反 | plan`:133`、`:146` | plan 配置に限れば説明可能。ただし対案ではこの変異を廃止する。 |
| **対案の run guard 除去:** 非空・role 無しの fixture 起動を新たに拒否する。emit は既に return 済みで I・C は検出不能。 | **real**：非等価だが既存検出が見当たらない | `L:2713`、`:2807`、`:2813`、`T:6546`、`:7195` | 対案の N・E・K・P・I 集合では期待失敗 node は空。実走で赤がなければ **SURVIVED** と記録し、等価・KILLED と呼ばない。 |

**別層拒否による帰属の混同**

- **所見:** 不正 role、manifest 無し＋role 有り、job body 経由の欠損 env、不正な空 manifest は、それぞれ argparse、loader、shell、parser が独立に拒否します。本 guard の有効性を示す入力には使えません。plan の N はこれらを避けています。
- **仮判定:** plan の N に複数拒否層が残る懸念は **refuted**。上記入力を代替負例にする案は **real**。
- **根拠 file:line:** `L:2574`、`:2311`、`KM:320`、`tools/pegasus/p3_s4_loop_pegasus.sh:74`、`:95`、plan`:55`。
- **推奨:** driver の `main` 直接呼出し、有効な非空 manifest、有効な legacy proposal、role 省略という N の入力を維持する。

**過剰拒否の正例登録**

- **所見:** plan は E→M2、P・I→M3、I・C→M5-route を登録しており、「受理集合を縮小する wave なのに過剰拒否を検査していない」という批判は当たりません。ただし fixture 境界の検出はありません。
- **仮判定:** 登録皆無という懸念は **refuted**。fixture の検出欠落は **real**。
- **根拠 file:line:** plan`:125`、`:130`、`:131`、`:133`、`T:7195`。
- **推奨:** 対案でも E・P を維持する。「全 KILLED」（brief`:30`）を先に結論にしない。M5 の未検出を閉じる必要がある場合だけ、実際に変異で失われる fixture 正例1本を対象にする。未検出を隠すための再照準はしない。

## 親の前提実測への反証

| 所見 | 仮判定 | 根拠 file:line | 推奨 |
|---|---|---|---|
| **未着地:** git log の T-2502／D1878 一致0件は再確認。現物にも新 guard はない。ただし「最新の持ち越しは1578」は古く、1579がある。 | **real**：最新 entry 番号。未着地判断への反証は **refuted** | rulings`:17`、`docs/worklog.md:2819`、`L:2667`、`:2714` | 最新番号だけ訂正する。履歴検索0件だけを未実装の証明にはしない。 |
| **後続裁定:** 指定語検索は D1878 自身の2行。D1999 は source の文種選定であり role 条件を変えない。 | **refuted**：確認した裁定の衝突 | rulings`:18`、`docs/decisions.md:56844`、`:56847`、`:60609` | 現時点で再裁定不要。ただし語検索だけから全後続裁定の不存在を証明したとは書かない。 |
| **main→legacy の穴、prepare の先行、loader 契約、role choices:** 現物と一致する。 | **refuted** | rulings`:20`、`:21`、`:22`、`:25`、`L:1545`、`:1555`、`:2311`、`:2574`、`:2728`、`:2775` | 本 wave の根拠として採用する。 |
| **2種類の sources は同じ長さ:** 正常な resolver の生成物では1 source ごとに resolved source を追加するため成立。dataclass 自体が同長を強制するわけではない。 | **real**：型そのものの不変条件への一般化 | rulings`:23`、`KM:141`、`:461`、`:469`、`:474` | 「実 resolver の正常な返り値では同長」と限定。新検査は不要。 |
| **空 sources＝completed_empty:** 空から status への含意は正しいが、逆は parser で保証されていない。 | **real** | rulings`:24`、`KM:320`、`:326`、`:355` | 所見2の表現に訂正する。 |
| **既存2正例、helper、非空 fixture:** 記載どおり。既存2正例はいずれも空 sources で、非空＋role 有りの main 正例の代わりにはならない。 | **refuted**：記載誤りの懸念 | rulings`:27`、`:28`、`:29`、`:30`、`T:1037`、`:7170`、`:7193`、`:7209`、`:7245` | 新正例 P を採用する。 |
| **baseline 26 passed／21.52s:** 今回読んだ資料には親の報告があり、独立した実走ログを検証したわけではない。 | **real**：こちらの再実測値として扱う場合 | rulings`:31` | 親の報告値としてのみ引用。今回の緑・変異結果には流用しない。 |
| **「P5以外に赤はない」:** manifest argv・resolver patch の静的検索は plan の棚卸しと整合する。ただし動的呼出しや全 suite の成功を証明しない。plan 自体は既に留保している。 | **refuted**：plan が全緑を断定しているという批判 | plan`:99`、`:110`、`T:6541`、`:6639`、`:7197` | 「見当たらない」を維持し、受入実走で確定する。 |
| **pin 閉包:** 指定 consumer path と変更前 SHA は一致。SHA 文字列の通常の `rg --hidden` 検索は一致0件。ただし単体 SHA の不在は、集約 closure hash の影響なしを意味しない。 | **real**：影響なしへの一般化 | rulings`:32`、`p3_b4_closed_critic.py:635`、`:681`、`:687`、`p3_b4_raw_record_producer.py:1034`、`p3_b4_wiring_probe.py:1625`、`.codex/role-adapters/coder-v4-autonomous-k2.json:5`、`orchestrator/codex_roles/manifest.json:965` | 「列挙箇所は path／live hash、単体 SHA の一致なし」に限定。集約 closure と既存 admission の整合は親の確認に残し、凍結値を自動更新しない。 |

## 総括

**emit の `return 0` 後・`build_run_context` 前の対案を推奨します。** D1878 の拒否対象だけを狭め、emit 優先と knowledge receipt 前拒否を、追加の emit guard なしで保存できます。

採用すべき是正は、sources 件数を含む message、負例 N、非空＋role K2 の実 loader 正例 P、P5 の後半 argv 修正です。空取得の既存2正例・loader・consumer・parser は維持します。

変異は M1〜M4 の帰属を上記に訂正し、配置に合わなくなる M5-route と test C は外します。対案の run guard 除去は**非等価の未検出候補**です。実走結果なしに全 KILLED とせず、検出されなければ SURVIVED と記録してください。追加裁定を要する production の仕様変更は見つかりませんでした。