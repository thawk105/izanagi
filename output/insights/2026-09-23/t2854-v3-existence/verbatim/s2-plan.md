## 1. 規則の確定

**案 (b)：DSG の辺構築後、v3 だけに共通の存在履歴検査を行う。P1〜P3 を採用し、辺・producer・既存カウンタは変更しない。**

以下、`model.py` 等は `orchestrator/verifier/` 配下、`test_verifier.py` は `orchestrator/tests/` 配下を指す。資料の略称は次のとおり。

- [brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence/s1-brief.md:28)
- [設計](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-v3-existence/output/insights/2026-09-21/tpcc-trace-certification-design/README.md:81)
- [単位4記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-v3-existence/output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md:115)

**P1：初期存在。** object は `k=(table,key)`、genesis は `g=(1,0)`。その object の committed write を **commit の `(epoch,tid)` 辞書順**で並べる。txid 順・file 順・R/W 行順を版順として使わない。最初の op が I なら初期不存在、それ以外、または write が一度もなければ初期存在とする。これは段1に限定した推定規則であり、初期ロード集合の独立した証明ではない。（brief:38–39、設計:83、`model.py:20–26,360–361`）

**P3：書きの連鎖。** 直前の存在状態 `live` に対して以下を適用する。違反があっても、後続を再現可能に診断するため、当該 op が表明する事後状態へ進める。

| op | 違反条件 | 種別名（提案） | 事後状態 |
|---|---|---|---|
| I | `live=True` | `insert-on-live` | 存在 |
| U | `live=False` | `update-on-absent` | 存在 |
| D | `live=False` | `delete-on-absent` | 不存在 |

最初の I は P1 により合法。最初の U/D も初期存在からの操作として合法になる。`D→U` は U に1件、`D→D` は後者に1件、`D→I` は合法。P3 は「既存行への挿入／不存在行への更新・削除」を同じ存在状態で検査する範囲として採用する。（brief:41、設計:83–84、`model.py:321–324`）

**P2：読み。** 各 R 行について、読み手の commit 時点の最新状態ではなく、**指定された版そのもの**を解く。

| R の指定版 | 存在違反 |
|---|---|
| genesis、初期不存在 | `read-unborn-genesis` を1件 |
| producer があり、その版の op が D | `read-deleted-version` を1件 |
| genesis、初期存在 | なし |
| producer の op が I/U | なし |
| 非genesis、producer 不在 | 新件数は増やさず、既存 `orphan_reads` に任せる |

したがって、D の後でも、それ以前の I/U 版を読むことだけでは存在違反にしない。順序の問題は既存 DSG が扱う。R の重複行は既存 orphan と同様に行ごとに数える。（設計:83–86、`dsg.py:648–672,240–269`）

**既存 integrity との重なり。**

- `version_dups>0` または `genesis_commits>0` なら、**run 全体の新しい存在検査を省略**し、新件数は0とする。版列の意味が既に壊れているため、任意の producer/op を選んで二次的な違反を作らない。既存件数・notes・辺は残す。この0は「存在履歴が正常」の証明ではない。（`dsg.py:353–373,470–495,508–529`）
- orphan は上表のとおり存在件数へ重ねない。他の parse integrity、X/I/P、witness 不一致では、保持された winner trace の存在検査を続ける。既存違反を消さず、欠落した履歴を補完もしない。`clean()` を検査開始条件にはしない。DSG 構築時点では proof assessment 等がまだ設定されていないためである。（`core.py:38–62,68–179`）
- 同一取引・同一 object・同一 commit の W 重複は既存 `version_dups` に掛からない。同じ op の反復は一つの版として扱う。**異なる op が混在する群は `ambiguous-write-version` を群ごとに1件**とし、その object の P1〜P3 派生診断を省略する。異なる op の任意選択による認定を防ぐための、存在解決内の最小処理である。（`parse.py:418–429`、`dsg.py:364–373`、brief:33）

**自己版読み。** v3 parser は R の版と読み手 commit の一致を拒否しないので、**受理可能な trace としては起こりうる**。実 emitter が出すかは指定資料だけでは断定できない。自己版でも I/U は存在、D は不存在として同じ規則を使い、自己取引だから検査を省略しない。producer がなければ自己commitと一致しても orphan である。（`parse.py:411–429`、`dsg.py:659–664`）

**verdict の優先順位。** 現行は cycle が integrity に優先する。本依頼の「存在違反なら indeterminate」を文字どおり満たすため、`VerifyResult.verdict` に新件数が非ゼロなら indeterminate を返す分岐を、cycle 判定より前に追加する。`serializable`、cycle witness、`total_cycles` は保持する。新件数0の場合と v2 の優先順位は変更しない。（`model.py:543–560`。従来裁定との違いは「brief への異議」参照）

## 2. 実装位置

**`dsg.py` に共通検査と二つの薄い入力 adapter を置く。** 新 module、parser 変更、worker の状態拡張は不要とする。compact には既に op が保持されている。（`parse.py:647–663,595–600`、brief:15,30）

| 箇所 | 提案変更 |
|---|---|
| `DSG.__init__`、`dsg.py:321–332` | `_build()` 完了後、非空の v3 入力だけ共通検査を呼ぶ |
| `DSG.from_compact`、`dsg.py:335–346` | `_build_compact()` 完了後、v3 schema の場合だけ同じ検査を呼ぶ |
| `dsg.py` 内の新 helper | object／columns を共通の write/read レコードへ変換し、P1〜P3を集計 |
| `core.py:63–67` | 一律非認定の field 設定と note を削除。存在検査はここで再実行しない |

共通レコードは、W が `(txid, table, key, commit, op)`、R が `(txid, table, key, version, read_index)`。adapter は iterator とし、全 R のリストは作らない。compact は **winner 行だけ**を走査し、op は `_token_at(columns, write_op_id[index])` から読む。`_txn_from_columns` で全取引を object 化しない。（`parse.py:564–603,807–846`）

処理は次の三段であり、「厳密な一走査」ではなく**辺構築から独立した一つの検査工程**である。

1. W を object・版ごとに集め、重複／op 混在を解く。
2. object ごとの版列を辞書順に並べ、初期存在と書きの違反を求める。
3. R を一巡し、genesis または指定版の op を照合する。

詳細は最後に `(txid, table, key, version, kind, read_index)` を基準に整列する。同値の重複レコードは保持し、notes はこの列の先頭5件から作る。これで辞書挿入順や worker 完了順を見本選択に使わない。（基礎となる版順は `model.py:20–26`、winner 順は `parse.py:816–846,855–872`）

**触らない箇所。**

- object の `_build`／`_add_read_edges`／`_add_ww_edges`：`dsg.py:350–376,648–681`
- packed／tuple の既存 index 構築：`dsg.py:394–530`
- `_edge_candidates_for_task` と worker state：`dsg.py:143–156,200–303`
- 並列結果回収、逐次 fallback、隣接順の再現：`dsg.py:565–642`
- parser、schema 判定、last-wins、overflow fallback：`parse.py:347–429,783–922`
- `report.py` 全体。

検査は worker 終了後に親で一度だけ行うため、部分結果を破棄して逐次再計算しても二重計上しない。tuple builder を直接差し替える既存試験も、`from_compact` の後処理を通る。parse の legacy 落ちは object 側の同じ検査へ到達する。（`dsg.py:345,610–625`、`parse.py:898–899`、`test_verifier.py:3411–3435`）

v2 では adapter、存在 map、ソート、追加 notes を一切動かさない。既存の辺順・map・wire bytes を保つ。一方、入口の schema 分岐と新 field の初期化まで含む**実行時間の完全一致は保証できない**。保証するのは v2 に R/W 件数比例の追加処理を持ち込まないこと。（`dsg.py:321–345`、brief:29,44）

**計算量の見積り。** W件数を W、R件数を R、object ごとの版数を `wₖ`、違反数を V とすると、追加時間は概ね `O(W + R + Σwₖ log wₖ + V log V)`、追加メモリは `O(W + V)`。R は保持しない。36,156取引・R約50万・W約54万という依頼の規模では線形走査が中心と推測するが、Python map の追加メモリと wall time は未測定。検査を fork 後に置くので、その追加 map は edge worker に継承されない。（brief:8–9、`dsg.py:575–601`）

## 3. model / 出力

次を **提案する field 定義**とする。件数欄は一つ、構造化詳細は別欄に保持する。（brief:33,42–43、既存詳細欄の先例は `model.py:471–478`）

```python
existence_violations: int = 0
existence_violation_details: Optional[List[ExistenceViolation]] = None
```

- `None` は v2／対象外。v3 の検査入口で `[]` にする。
- 構造的な既存違反によって省略した v3 でも `[]` と件数0にする。既存 `version_dups`／`genesis_commits` が省略条件を示す。
- `ExistenceViolation` は `model.py` 内の frozen dataclass。`txid: int`、`table: int`、`key: str`、`version: Version`、`kind: str`、`ops: tuple[str,...] = ()` を持つ。読みは `ops=()`、通常の書きは対象op一つ、曖昧版は混在opの整列済み列。
- 詳細は全件保持し、notes のみ5件に制限する。`max_report` では件数も詳細も削らない。

`model.py:487` の `v3_existence_unverified` を削除し、`:506` を `existence_violations == 0` に置き換える。`core.py:63–67` の設定と旧 note を削除する。witness の `replace()` は新 field を引き継ぐので別処理は不要。（`core.py:68–76`）

`result_to_dict_v3` は、`existence_violation_details is not None` の場合だけ `integrity` に以下を追加する。正常 v3 は `0` と `[]`、v2 は従来と同じ dict のままとする。cycle の有無で v3 を判定してはならない。（現出力点は `core.py:201–218`、v2 射影一致試験は `test_verifier.py:3841–3848`）

```json
{
  "existence_violations": 1,
  "existence_violation_details": [
    {
      "txid": 1,
      "table": 5,
      "key": "aa",
      "version": [1, 0],
      "kind": "read-unborn-genesis",
      "ops": []
    }
  ]
}
```

notes の提案文言：

```text
1 v3 existence violation(s): txn1 table=5 key=aa ver=(1, 0) kind=read-unborn-genesis
```

複数件では同じ形式を `; ` で連結し、5件を超えれば全件数と見本数を明記する。正常系では存在検査 note を追加しない。（既存 notes の集約方式：`core.py:129–143`）

**旧 JSON には、新しい integrity key は出ない。** `report.result_to_dict` は field の自動列挙ではなく明示的な辞書なので、存在検査の結果は integrity 内では `clean` と `notes` にだけ現れる。もちろん top-level の `verdict`／`certified` にも反映される。（`report.py:96–136`）

**repr／全 field 固定の静的検索結果。**

- `test_verifier.py` で `repr(`、`asdict(`、`__dict__`、`__dataclass_fields__`、Integrity の field 列挙による固定は見つからなかった。
- dataclass 全体の等価比較はある：`test_verifier.py:3024,3090`。新 field の既定値が両側で一致するため、既存 v2 期待値を変更しない。
- `test_verifier.py:323` の「全フィールド」はコメントであり、実 assert は `genesis_commits` 単体。
- repr 文字列が固定されているのは **EdgeReason**：`test_verifier.py:2658–2663`。この型には触らない。
- wire bytes／全 fixture hash の固定は `test_verifier.py:1404,2893`。これらも更新しない。

## 4. consumer の静的列挙

`rg` で `orchestrator/` と `tools/` を検索した。以下は指定識別子の直接参照と、`.clean()` の実呼び出し。今回の検索では `tools/` に該当 consumer はなかった。

| 対象 | 箇所 | 波及 |
|---|---|---|
| `v3_existence_unverified` 定義・参照 | `model.py:487,506`、`core.py:64` | field、clean 条件、設定を撤去 |
| 同 field の試験 | `test_verifier.py:3714,3726,3730,3755,3779` | 関数改名、件数・帰属・field 不在の検査へ変更 |
| `Integrity()` production | `dsg.py:331,344` | 新既定値を持つ。呼び出し引数の変更不要 |
| `Integrity(...)` verifier 試験 | `test_verifier.py:1362,2138,3024,3090` | v2 期待値を維持 |
| `Integrity(...)` 他試験 | `test_campaign.py:5805,5822`、`test_t1286_commit_receipt.py:356` | keyword 構築で新 field は既定値。変更不要 |
| `clean()` 判定 | `model.py:553,560` | 新件数で認定を拒否 |
| `clean()` report | `report.py:113,165` | JSON clean／テキストに自然に反映。編集不要 |
| `clean()` campaign | `orchestrator/campaign/reflux_result_evidence.py:724` | 既存の clean 必須条件に自然に反映。配線変更なし |
| `result_to_dict_v3` 定義 | `core.py:201` | 構造化存在違反を追加 |
| 同出力の試験 | `test_verifier.py:3445,3515,3529,3537,3788,3830,3843,3848,3857` | 経路一致・cycle 出力・v2 不変を維持し、新詳細の確認を追加 |

`clean()` の試験 consumer は次のとおり。

- `test_verifier.py:112,120,267,309,675,727,914,1194,1320,1331,1467,1725,1753,2048,2066,2077,3730`
- `test_reflux_result_evidence.py:879`
- `test_reflux_campaign_issuer.py:589,693`
- `test_reflux_formal_consumer.py:833,1610`

`test_verifier.py:1733` と `orchestrator/tests/fixtures/README.md:91,139,160` にもコメント／文書上の言及がある。`Integrity.clean` という完全修飾表記の直接呼び出しはなく、実体は上記の instance 呼び出しだった。

capability 経路は `verify_trace_dir` の結果を使うため新件数が効くが、digest は引き続き旧 `result_to_dict` の射影を使う。構造化詳細の receipt／CLI 配線は今回行わない。（`core.py:281–292,401–414`、単位4記録:121–122、brief:16）

## 5. テスト計画

すべて既存 `test_verifier.py` に追加・更新し、`_v3_frame`、`_tmp_trace`、`try/finally` による削除という既存形式を使う。正常対照は既存 wrapper の synthetic Silo proof source を使い、`expected_commits` も一致させる。（`test_verifier.py:41–62,3378–3386,3718–3758`）

以下で `A:I@v` は同じ `(5,"aa")` への W、`B:R(v)` はその版の R を表す。各負例は cycle を持たせず、`indeterminate`、非認定、件数、詳細全体、orphan=0、旧印不在を確認する。**違反の1行だけを修正した対照で certified を確認する。**

| test 関数名（提案） | fixture と期待 |
|---|---|
| `test_v3_existence_read_unborn_genesis` | `A:I@(2,1), B:R(1,0)` → 1件 `read-unborn-genesis`。R 行を `(2,1)` に直すと certified |
| `test_v3_existence_read_deleted_version` | `A:D@(2,1), B:R(2,1)` → 1件 `read-deleted-version`。W 行の D を U に直すと certified |
| `test_v3_existence_insert_on_live` | `A:U@(2,1), B:I@(2,2)` → 1件 `insert-on-live`。後者を U に直すと certified |
| `test_v3_existence_update_delete_on_absent` | `A:D@(2,1), B:U/D@(2,2)` の2例 → 後者に各1件。後者を I に直すと certified |
| `test_v3_existence_valid_histories` | 未書込み key の genesis、最初が U の key の genesis、I版読み、`D→I→R(I版)` を個別に certified。詳細 `[]`、noteなし |
| `test_v3_existence_self_version_reads` | 同一 frame に R(self commit) と W(I/U/D)。I/U は certified、D は読み違反1件。D→U の1行修正も確認 |
| `test_v3_existence_version_order` | txid／file 順と commit 順を逆転。例：txid0 が `U@(3,1)`、txid1 が `I@(2,9)`。正しい版順なら合法。tid優先順・txid順では誤検出する形にする |
| `test_v3_existence_table_isolation` | table5 の I と、同じ hex の table9 の genesis 読みは合法。R の表だけ5に直すと読み違反1件 |
| `test_v3_existence_existing_integrity_overlap` | 異取引の重複版、genesis以下commitでは新件数0。orphanと独立した存在違反を併置し、orphan=1・存在=1。last-wins 後だけを検査する例も含める |
| `test_v3_existence_same_txn_write_duplicates` | 同一opのW重複は一版扱い。I/D混在は `ambiguous-write-version` 1件。D行をIへ直すと certified |
| `test_v3_existence_output_and_samples` | 6件以上・逆順txidの違反。全詳細・件数・先頭5件notesの一致、旧JSONに新keyがないこと、`max_report=0`でも件数・詳細が残ること |
| `test_v3_existence_violation_with_cycle` | 既存 `_v3_cycle_files()` に独立objectの存在違反を追加。cycleとanomalyを保ったまま verdict は indeterminate。違反を直すと従来の non-serializable |

P1/P2/P3 の根拠は設計:83–86、brief:38–41。既存の経路比較・cycle fixture・table分離を流用できる箇所は `test_verifier.py:3390–3448,3472–3489`。

**経路 matrix。** 上の意味検査を `_v3_paths` で object、packed/tuple、workers 1/2 に通す。現 helper は legacy だけ workers=1 なので、必要な比較を追加する。また `graph.integrity` 自体の比較と、`parse_trace_dir→DSG(txns)` の存在詳細比較を追加する。現 helper の末尾は辺しか比較していない。（`test_verifier.py:3417–3448`）

追加する `test_v3_existence_fallback_paths` は、違反を含む fixture で次を確認する。

- `epoch=2**32` の自然な tuple 落ち。
- `epoch=2**63` の自然な legacy 落ち。
- parse worker と edge worker の実 process 異常終了による逐次 fallback。
- 各経路で件数・詳細・notes・verdict が基準結果と一致。

既存の overflow／実worker終了の試験構造を再利用し、通常経路だけを mock で比較して完了とはしない。（`test_verifier.py:3605–3618,3784–3836`）

**旧印試験の書き換え。** `test_v3_existence_unverified_and_v2_control` を `test_v3_existence_violations_and_v2_control` に改名する。

- 現在は **U正常例も含む3例**。U は certified に変更。
- I+genesis、D版読みの2例は非認定を維持し、各1件の種別・詳細へ帰属させる。
- 負例で `replace(ig, existence_violations=0).clean()` を確認し、他の integrity が原因でないことを示す。実 fixture の1行修正による certified と併用する。
- capability の U は認定、負例2件は非認定。
- 同形 v2 の3例は certified・notes空を維持。削除したfieldの参照は `not hasattr(...)` と新件数0へ置換。
- `test_v3_framing_and_neutral_files:3779` も field 不在／新件数0へ変更。

根拠：`test_verifier.py:3714–3779`、brief:34–35。

既存 `test_v3_serial_tables_types_and_ops` は D版を3表分読むので、新件数3を追加確認できる。既存の `serializable=True` と辺数11は維持し、certified と混同しない。（`test_verifier.py:3494–3508`）

v2 の凍結JSON、全fixture hash、witness順の既存期待値は変更しない。（`test_verifier.py:1404,2576,2893,3848`）

## 6. 変異の候補

以下の10変異を事前登録する。いずれも上節の独立した期待値で殺し、正常対照も通す。対象箇所は新共通検査、`model.py:489–507,543–560`、`core.py:201` 周辺となる。

| 変異 | 殺す test |
|---|---|
| 初期存在を常に真にする | `test_v3_existence_read_unborn_genesis` |
| D版の読み検査を削除 | `test_v3_existence_read_deleted_version`、`test_v3_existence_self_version_reads` |
| P3 の前提条件検査を全部削除 | `test_v3_existence_insert_on_live`、`test_v3_existence_update_delete_on_absent` |
| D の後も live=True にする | `test_v3_existence_update_delete_on_absent`、`test_v3_existence_valid_histories` |
| `clean()` から新件数条件を削除 | `test_v3_existence_read_unborn_genesis` の非認定・clean検査 |
| compact 入口だけ共通検査を呼ばない | `_v3_paths` を使う各負例の件数・詳細一致 |
| v2 にも存在検査を適用 | `test_v3_existence_violations_and_v2_control` の I/D 対照 |
| 版順を `(tid,epoch)` または txid 順にする | `test_v3_existence_version_order` |
| 同一取引の異種op群を任意の一opへ潰す | `test_v3_existence_same_txn_write_duplicates` |
| existence 非ゼロ判定を cycle 分岐より後ろへ移す | `test_v3_existence_violation_with_cycle` |

出力・見本切捨て・table保持は `test_v3_existence_output_and_samples`／`test_v3_existence_table_isolation` で通常試験として押さえる。変異の実行・kill確認は本起草では行っていない。

## 7. 規模

以下は静的読解からの**追加・削除合計の見積り**であり、実測差分ではない。

| file | 見積り | 主な変更 |
|---|---:|---|
| `orchestrator/verifier/model.py` | 30〜50行 | 詳細型、件数・詳細欄、旧印撤去、clean／verdict |
| `orchestrator/verifier/dsg.py` | 140〜210行 | v3入口、二adapter、共通検査、決定的詳細／notes |
| `orchestrator/verifier/core.py` | 25〜40行 | 旧印設定撤去、v3 JSON拡張 |
| `orchestrator/verifier/parse.py` | 0行 | 既存op列・winner列を利用 |
| `orchestrator/verifier/report.py` | 0行 | 編集禁止 |
| `orchestrator/tests/test_verifier.py` | 350〜500行 | 意味検査、対照、経路一致、fallback、旧印試験更新 |
| 合計 | **545〜800行程度** | production は195〜300行程度 |

**実装子1本で足りる。** model の件数／詳細、DSG の生成、core の射影、帰属試験が密結合しており、分割する利点が小さい。brief:49–50 と一致する。実trace probe・変異実行は実装後の親側検証とし、本段では実装もテスト実行もしていない。

## brief への異議

1. **「既存 integrity があればどちらにしても indeterminate」は一般には成立しない。** 現行 `model.py:551–554` は cycle を優先し、D2224も cycle は non-serializable として残すと定める（`docs/decisions.md:71523–71525`）。本案は最新依頼の字義を採り、**新しい存在件数だけ**をcycleより優先させる。既存 integrity 全般の優先順位変更には広げない。

2. **P4の件数欄とnotesだけでは不変条件5を満たせない。** brief:33 は違反の構造化を要求するが、brief:42–43 は件数出力しか明記しない。型付き詳細欄と `result_to_dict_v3` の詳細出力を追加する必要がある。旧reportは明示列挙なので変更不要。（`report.py:112–133`）

3. **同一取引・同一版の異種opが未規定。** parser はそのまま保持し、version dup は異なるtxidだけを数えるため、既存違反に任せられない。（`parse.py:428–429`、`dsg.py:364–370`）本案は `ambiguous-write-version` として閉じる。これは新たな一般的trace検査ではなく、今回解こうとしている存在状態の曖昧さへの処理である。

4. **P1は初期集合の証明ではない。** 最初のIが「本当に初期不存在だった」かは、指定された入力だけでは判別できない。段1の採用契約として明記し、任意の初期ロードとの整合性まで認定したとは言わない。（brief:38–39、設計:83）

5. **v2の「時間不変」は字義どおりには約束できない。** 保持できるのは受理集合、既存値、wire bytes、辺／witness順、そして追加の全件走査をしないこと。新fieldと分岐の微小費用までゼロとは主張しない。（brief:29,44、`dsg.py:331–345`）

## 総括

- 採用案は、DSG構築後にv3だけで動く、両経路共通の存在検査。
- P1〜P3を採用し、版順は `(epoch,tid)`、読みは指定版の存在を照合する。
- orphanを重複計上せず、重複版／genesis以下commitでは既存診断を優先する。
- 同一取引の異種op同版は、曖昧な存在状態として非認定にする。
- 件数・全構造化詳細・決定的な5件見本を返し、旧印を撤去する。
- parser、辺worker、report.py、既存v2の期待値は変更しない。
- cycle併存時の新件数優先は依頼の字義に基づく提案で、従来裁定との差分を明記した。
- 実装子1本で対応可能。実装・試験・変異・実traceの再測定は未実施であり、認定到達は未確認。