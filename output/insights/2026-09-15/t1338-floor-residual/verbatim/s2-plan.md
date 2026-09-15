## 残件同定の照合

**依頼が名指す 3 述語は撤去済みです。台帳の R1〜R3 は、それとは別の残件です。** 指定資料に読めない path はありませんでした。

撤去前の [worklog 643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/archive/worklog-phase3-0818-643.md:597) は、名指しの 3 述語と R1〜R3 を併記しています。撤去後の [worklog 1479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/archive/worklog-phase3-0914-1479.md:186) は、前者を撤去済み、後者を scope 外の残件と記録しています。直前 wave の README:137–138 も一致します。

以下のコード位置はすべて `orchestrator/campaign/` 配下です。

| 対象 | 現物との照合 |
|---|---|
| per-pair 床値対表 exact 検査 | 撤去済み。`s8b_oracle_manifest.py:600–628` は null・外形・holdout 集合・budget 値・共有性を検査し、pair 内部を検査しない。同ファイルに `pairs` / `scalar_alt` の参照なし。 |
| `floor_budget_snapshot_sha256` | 撤去済み。同 manifest の key 集合:55–60、生成:719–737 に存在せず、:965 の exact key 検査で旧 key は拒否される。 |
| oracle driver の `expected_perf_sha256` 供給 | 撤去済み。`s8b_oracle_driver.py` に当該識別子と `perf_sha_by_cell` は存在しない。store 検査:1005–1058 は残り、:1783 の `pipeline.evaluate` へ旧期待値を供給しない。 |

親 brief の実アンカー表は、**行番号のずれなし**です。ただし R3 の範囲には補正が必要です。

| 残件 | 現物 | 判定 |
|---|---|---|
| R1 | `s8b_oracle_driver.py:524–527` | floor/budget null refusal がそのまま存在。 |
| R2 | `s8b_budget.py:96–118`、driver:1433 | loader と呼出しが存在。返した limits は driver:1586 の `create_ledger` に供給される。 |
| R3 | `s8b_oracle_report.py:2548` | 指定した assertion は存在。ただし「解決経路」全体は:2547–2560 の load → selection 検査 → reverify → manifest 検証 → consumer 引渡し。台帳の短文だけから R3 を assertion 1 行と一意に同定できない。 |

## 授権の逐語照合

### D501 決定 8 は R1〜R3 を名指していない

[decisions.md:20824–20829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/decisions.md:20824) は次を挙げています。

> 「manifest の per-pair 対表 exact 検査」  
> 「floor/budget の部分 hash」  
> 「driver の測定 binary bytes 照合」

さらに、

> 「いずれの撤去も受理集合を広げるため、本決定では実装しない。」

したがって、D501 決定 8 を R1〜R3 の撤去授権として使うことはできません。名指した 3 述語の実際の撤去決定は D1985:59966–59973 です。

### R1：floor-null の個別解除は明示的に却下

[D811:30961–30962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/decisions.md:30961)：

> 「床値を空のまま `floor-null` の拒否だけを個別に解く — 拒否は床値が無いことの正しい表現であり、表現だけを変えると門が守っていた性質が失われる。」

これは **floor-null の個別解除**を却下しています。budget-null まで D811 が名指す、とは読めません。

ただし [D1985:59975–59978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/decisions.md:59975) は、

> 「残すものを同時に確定する。」  
> 「floor/budget の null 拒否と外形・budget 値・共有性の検査。」

と明示するため、R1 全体の単純撤去は残置決定に反します。

### R2：検査契約の残置は明示、関数名の保存までは明示していない

D1985 の上記引用に **budget 値・共有性の検査**が含まれます。現物の `load_oracle_limits` は数値を現走行の資源上限へ射影し、`_validate_limits`（`s8b_budget.py:74–93`）で有限非負・共有性などを検査します。過去の性能値との比較ではありません。

ただし D1985 は `load_oracle_limits` という関数名を名指していません。**契約を維持する同値な実装変更まで禁止された、とは断定できません。** 本依頼にはその変更を必要とする不具合や目的がなく、契約ごとの撤去を授権する文もありません。

### R3：指定決定には明示的な撤去授権も、一律の撤去禁止もない

[D1984:59947–59950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/decisions.md:59947)：

> 「`assert_g1_floor_selection_identity` は g1 以外で何もせず返る。」  
> 「`reverify_published_freeze` は `ReverifiedFreeze` を指定するため選択検査の分岐に入らない。」

これは現用挙動の記録であり、撤去禁止の逐語ではありません。D1985 も R3 を名指していません。

一方、report:2548 は現用の選択検査です。既存 consumer test `test_s8b_oracle_report.py:1788` は実際の g1 選択規則不一致を扱い、:1827–1830 で拒否理由と出力不在を要求します。**撤去授権のないまま「残骸」として削除できる箇所ではありません。**

## 撤去済み 3 件の残骸

静的検索で確認した範囲は `orchestrator/` と `tools/` の Python ファイルです。

- `perf_sha_by_cell`：0 件。
- `floor_budget_snapshot_sha256`：`test_s8b_oracle_manifest.py:803` の旧 key 注入だけ。:797 のテストは意図した旧形拒否を検査しており、撤去漏れではありません。
- `expected_perf_sha256`：pipeline の引数・比較・内部転送と既存テストが残っています。

generic gate の位置は [pipeline.py:2091–2100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/orchestrator/campaign/pipeline.py:2091)。引数は:1565 と:2595、内部転送は:2682 です。**内部転送は存在しますが、外側から具体的期待値を与える production 供給元は検索上 0 件です。**

[D1985:60009–60010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1338-floor-residual/docs/decisions.md:60009)：

> 「**`pipeline` の generic gate も外す** — 決定 8 は名指していない。供給元を失うことは記録するが、本 wave で直す欠陥ではない。」

加えて:59978 は「引数も残す」と明示しています。「本 wave」は当時の wave を指すため永久禁止ではありませんが、**今回の依頼にも generic gate 撤去を新たに授権する記載はありません。今回も触れない判定です。**

この gate は API として無挙動ではありません。既存 `test_campaign.py` の:6892、:6909、:6917、:6932 が、不一致拒否・一致続行・不正値拒否・省略時続行をそれぞれ検査しています。削除すれば、引数を残す案では拒否入力の受理拡大、引数ごと消す案では API 破壊になります。

## 実装プラン (無い場合はその旨と根拠)

**今回の授権範囲で、必要な実装として提案できる部分集合はありません。**

- 名指しの 3 述語は撤去済み。再導入は D1985 と「新しい受入条件を増やさない」に反する。
- R1 の撤去は D811／D1985 の明示的残置と衝突する。
- R2 は現用の予算供給経路であり、契約撤去の授権も、同値変更を必要とする具体的不具合もない。
- R3 は現用の選択・再検証経路であり、撤去授権がない。
- generic gate と旧 key 拒否テストは意図した残置である。

編集 path・所有単位は空集合です。新しい gate・検査・台帳・一般化は提案しません。

親が T-1338 の閉じ方を裁定する際の選択肢は次のとおりです。ここでは実施しません。

| 選択肢 | 触れる既裁定・留意点 |
|---|---|
| **名指し 3 述語の完了を確認し、R1〜R3 の撤去要求を取り下げて閉じる** | D1985 の完了・残置を維持。D811 を維持。古い carry の撤去要求を取り下げる判断が必要。 |
| 名指し 3 述語だけ完了扱いにし、R1〜R3 は裁定待ちと明確化する | T-1338 全体は未完。R1 は D811／D1985、R2 は D1985、R3 は授権未確定として分ける。 |
| R1〜R3 の具体的範囲と変更後契約を新たに裁定する | R1／R2 は上記残置との関係を明示。R3 は report:2547–2560 のどこを変えるか確定する。generic gate まで含めるなら D1985 の残置判断も別途扱う。規律 2 は維持する。 |

## 親 brief への反論

**P1-d の「実装なし」という結論は支持しますが、根拠には次の訂正が必要です。**

1. **R1〜R3 全部が D811 に反する、は広すぎます。** D811 の明示的却下は floor-null の個別解除です。R2／R3 へそのまま拡張できません。
2. **D1984 の現用事実は撤去禁止の決定ではありません。** R3 は「明示的に禁止」ではなく「現用契約があり、撤去授権が確認できない」と書くべきです。
3. **R3 のアンカー 1 行は経路全体を表しません。** assertion:2548 と解決経路:2547–2560 を区別すべきです。
4. **「R1〜R3 の撤去はいずれも受理集合を広げる」は未立証です。** R1 は manifest 側にも null 拒否があり、直前 README:85–88 も後段拒否による過剰決定を記録しています。R2 は loader だけ消せば正常実行を壊します。局所述語の削除と、経路全体の受理集合拡大は同義ではありません。
5. **新しい床値系列が存在するだけでは古い撤去要求の失効を証明できません。** D1985 自身も床値系列と共存しながら 3 述語を撤去しています。本件の根拠は、具体的な残置文・現用 consumer・追加授権の不在に置くべきです。

## 総括

**名指し 3 述語は撤去済み。R1〜R3 は残存しますが、今回実装できる授権済みの後始末は確認できません。** 親には、古い撤去 carry を取り下げて閉じるか、範囲を明確にして裁定待ちにするかの判断を返します。

段 2 の静的照合のみ実施しました。編集・記録・テスト実走は行っておらず、テストの緑は主張しません。