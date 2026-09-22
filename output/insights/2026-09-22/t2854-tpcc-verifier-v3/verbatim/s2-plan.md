## 1. identity の表現

**採用案は、object 経路では `str | tuple[int, str]`、compact 経路では `(table, key_hex)` 単位の interning と token ごとの table 列である。** 生の `Read.key`、`Write.key`、`EdgeReason.key` は hex 文字列のままにする。設計の「table は別 field」とも整合する。

以下、`parse.py` 等は `orchestrator/verifier/`、`test_verifier.py` は `orchestrator/tests/` 配下を指す。`設計` は指定された [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/output/insights/2026-09-21/tpcc-trace-certification-design/README.md:38)、`brief` は指定された [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md:29) を指す。

### object 経路

`model.py` に identity helper を置く。

```python
ObjectIdentity = str | tuple[int, str]

# ReadV3 / WriteV3 だけ tuple にする。
object_identity(access) -> ObjectIdentity
```

| 箇所 | 変更 |
|---|---|
| `parse.py:354,370,381` | v3 だけ `TxnV3 / ReadV3 / WriteV3` を生成。key と table は別 field |
| `parse.py:788` | `_LegacyTrace.txns` に派生型を保持 |
| `dsg.py:357,365` | producer のキーを `(object_identity(w), commit)`、版列のキーを `object_identity(w)` にする |
| `dsg.py:650` | read の検索キーを `object_identity(r)` にする |
| `dsg.py:671` | `_add_ww_edges` の処理本体は変更不要。受け取る map のキーだけが v3 では tuple |
| `dsg.py:777,778,792,797` | `_reasons` 内の write map・read 照合も同じ identity にする |

`Txn.write_keys()` は生 hex の列を返す現仕様を維持し、identity 用に流用しない。静的検索では定義以外の呼出しは見つからなかった（`model.py:337`）。

### compact 経路

`_ParsedFileColumns` に次を追加する（`parse.py:181`）。

- `schema: int | None`：C がない file は `None`。
- `token_table: array("b")`：v3 の各 token に対応。object token は `0..10`、op token は `-1`。
- `txn_tx_type: array("b")`：v3 の txn row に対応。
- 後述する最初の C の位置情報。

v2 では追加 array は空とし、既存 token interning の内容・呼出し順を維持する。v3 は intern 辞書のキーを object なら `(table, raw_key)`、op なら従来の文字列とする。`token_blob` には引き続き生文字列だけを入れる。同じ hex が別表なら、異なる token ID と blob entry を持つ（`parse.py:559,563,590,595`）。

`_object_at(columns, token_id)` を `parse.py:514` 付近に追加し、v2 は `_token_at` の文字列、v3 は `(token_table[id], _token_at(...))` を返す。`_txn_from_columns` は v3 の table・tx_type を復元する（`parse.py:520`）。

| compact の箇所 | identity の扱い |
|---|---|
| `dsg.py:405,419` | `_object_at` で global `key_ids` を引く。v3 の op token（table=`-1`）は read-only token 解決の対象外 |
| `dsg.py:436` | 同じ表・key の token ID だけが同じ global key ID に対応 |
| `dsg.py:514` | tuple builder の producer・版列を `_object_at` で引く |
| `dsg.py:260` | tuple edge worker の read 検索も `_object_at` を使う |
| `dsg.py:231` | packed edge worker は従来どおり token ID → global key ID →版列範囲を読む |

**`_packed_read_position` の算術と境界処理は変更しない。** table は `lo/hi` の選択までに解決する（`dsg.py:50`）。

`_PackedVersions` と `_PackedProducer` の Mapping view もアルゴリズム変更不要。v3 の公開キーはそれぞれ `(table, key)` と `((table, key), version)` になる。`__iter__`、`get`、欠落時 `KeyError` を含め、object/tuple 経路と一致させる（`dsg.py:70,98`）。

### v2 互換のため保存する処理

- v2 の intern キー、read→write→op の登録順（`parse.py:563,590`）。
- winner の last-wins と txid 順（`parse.py:743,749`）。
- first-seen object 順、版の stable sort と最初の producer（`dsg.py:407,442`）。
- wr→rw→ww の生成順、task 順、set への追加方法（`dsg.py:238,267,549,624`）。
- `_add`、SCC、BFS、SCC の size 順（`dsg.py:641,686,738,831`）。
- v2 用の notes 書式と `EdgeReason` コンストラクタの結果（`dsg.py:361,489,520,788`）。
- `report.py` 全体。

これは静的な互換設計であり、bytes 不変の実証は既存 golden を実行して初めて得られる（`test_verifier.py:1404,2653,2893`）。

## 2. parse の v3 分岐

### 各 tag

`_parse_file` の既存分岐を残し、v3 frame の場合だけ別の unpack・検査を行う（`parse.py:296`）。

| tag | 計画 |
|---|---|
| C | 5 token の専用拒否を保存。7 は v2、10 は v3。それ以外は拒否。v3 の `nS/nQ` は整数かつ値が 0、`tx_type` は整数 `1..5`。既存の非負 txid・nR/nW 検査を共用 |
| R | v2 は現行の5 token処理。v3 は6 token、table `0..10`、`ReadV3` を生成 |
| W | v2 は現行の6 token処理で op 無検査。v3 は7 token、table 検査、op=`U/I/D` のみ、`WriteV3` を生成 |
| X/I | v2 は4 token、v3 は5 token。table を検査し、件数には含めず違反リストへ |
| E | 既存処理をそのまま使用。宣言件数・duplicate-end・missing-end を維持 |
| P/A | 既存処理をそのまま使用。schema を決めず、frame 外でも受理 |
| S/Q | 未知 tag として引き続き `ParseError` |

根拠：`parse.py:321,365,371,382,393,402,430,443,455`、brief:47–51。

C の誤 token 数メッセージは、既存の `"expected exactly 7 fields"` を含む拒否を保存する。単に `"expected 7 or 10 fields"` へ置換すると既存テストが赤になる（`test_verifier.py:472,480`）。v3 の正しい10 token分岐を既存拒否の手前に設ければ、旧拒否文言を変更する必要はない。

table・tx_type・nS/nQ は **v3 の新 field に限り ASCII 十進整数の字句検査と `int(..., 10)`** を行う案とする。`1.0`、`0x1`、`1_0` は拒否。既存 v2 の整数変換や key 検査は変更しない（`parse.py:332,258`）。符号付き十進表記の扱いは §「brief への異議」で明示する。

### schema 状態と親のエラー順

単に `_ParsedFileColumns.schema` を比較するだけでは足りない。現在は **全 outcome の failure を先に処理してから merge** しているため、早い path の混在より遅い path の構文エラーが先に出る（`parse.py:827,835`）。

採用する実装は次のとおり。

1. `_parse_file` に任意の schema 状態引数を追加する。指定なしなら per-file の状態、legacy では run 共通状態を渡す。C の token 数が7/10と判定できた時点で schema を観測し、不一致ならその C 行で拒否する（`parse.py:321`）。
2. worker は最初の C の schema・行番号を、**成功・failure・NeedsLegacy の全 outcome** に残す。C がない場合は `None`。構文エラーの前に v3 の C を観測した情報を捨てない（`parse.py:182,205,216,547`）。
3. 親は sorted path 順に outcome を走査し、schema の観測と failure の処理を同じ順序で行う。worker 完了順は使用しない（`parse.py:487,687,827`）。
4. 同じ file に「run と異なる最初の C」と「その後の構文エラー」があれば、先行する混在を選ぶ。最初の C より前のエラーなら schema 情報はなく、そのエラーを選ぶ。
5. `_raise_parent_file_error` の再走査にも、それ以前の path が決めた schema を渡す。混在を親 scanner でも再現する。file 消失時は、保存済みの元エラー、または保存済み C 位置から決まる混在エラーを復元する。現在の OSError による優先順位逆転防止を残す（`parse.py:700`）。
6. `_merge_issues_and_winners` は schema 検査済み columns を受け取り、同じ検査 helper で成功結果間の混在も拒否する。issue・winner の merge 順は変更しない（`parse.py:716`）。
7. `_finish_legacy_parse` は全 path に同一 schema 状態を渡す。overflow fallback でも状態をリセットして最初から再読し、同じ拒否になる（`parse.py:788,830`）。

schema 状態は呼出しローカルとし、module global に置かない。並行 verify の隔離という既存要件にも合う（`test_verifier.py:2246`）。

P/A だけの file、空 file は schema=`None` として中立。C のない run は schema を推定せず、既存の `n_txns == 0 → indeterminate` を維持する（`parse.py:430,443`、`model.py:505`）。P/A/空 file を挟んでも、既に選ばれた run schema は解除しない。

既存の sorted path 優先、原因例外、親 scanner 経由という要件は維持できる設計である。ただし確認は実行待ち（`test_verifier.py:2329,2351,2760`）。

## 3. model の変更

**基底 dataclass は一切拡張せず、v3 専用の派生型を追加する。**

| 型 | v3 の追加情報 |
|---|---|
| `ReadV3(Read)` | 必須 keyword-only `table: int` |
| `WriteV3(Write)` | 必須 keyword-only `table: int` |
| `TxnV3(Txn)` | 必須 keyword-only `tx_type: int`、`schema=3` の `init=False` field |
| `EdgeReasonV3(EdgeReason)` | 必須 keyword-only `table: int`。基底と同じ frozen dataclass |
| `AnomalyV3(Anomaly)` | `cycle` と同順の必須 `cycle_tx_types: tuple[int, ...]` |
| `CycleEdge` | 変更なし。`reasons` に `EdgeReasonV3` を保持 |
| `VerifyResult` | 変更なし。`anomalies` に `AnomalyV3` を保持 |

keyword-only にするのは、`Txn`、`EdgeReason` の既定値付き field の後ろへ必須 field を追加するためである（`model.py:334,359`）。`VerifyResult` を派生型へ変えないのは capability が exact type を要求するためでもある（`core.py:254`）。

### tests の静的検索結果

repo 内の tests を対象に、型名・コンストラクタ、`repr(`、`str(`、`==`、read/write/anomaly 属性比較を `rg` で検索した。以下は verifier 型に関係する hit。これは静的検索であり、動的 alias を完全に証明するものではない。

| 対象 | hit と評価 |
|---|---|
| `Read / Write / Txn` の repr・str 固定 | 見つからなかった |
| `Read / Write / Txn` の非空 dataclass 値固定 | 見つからなかった。空 read/write リスト比較は `test_verifier.py:692`、空 txn リストは `:1091` |
| `EdgeReason` の str 固定 | `test_verifier.py:2654`、期待文字列 `:2658,2659,2662,2663` |
| `EdgeReason` の値比較 | `test_verifier.py:1785,1786,1787,1792,1796,1802,1806,1810,1816,1820,1826,1830`、最終比較 `:1834`。追加で `:2090,2091`、`:2727,2728` |
| `Anomaly / CycleEdge` の repr・str 固定 | 見つからなかった |
| anomaly の非空構造比較 | `test_verifier.py:2669,2674,2889,3367`。内部の `CycleEdge / EdgeReason` の eq も通る |
| `VerifyResult` 全体の比較 | `test_verifier.py:2951,2975,3006,3034,3068,3086,3187`。anomaly の eq が再帰的に対象になる |
| 他 test の生成箇所 | `test_campaign.py:5816,5818` の `CycleEdge`、`:5817,5819` の `EdgeReason`、`:5820` の `Anomaly` |
| 空 anomaly 比較 | `test_verifier.py:1726`、`orchestrator/tests/test_reflux_result_evidence.py:892` |

`CycleEdge` の追加生成箇所は `test_verifier.py:1565–1570`。ここは分類テストであり repr 固定ではない。

Read/Write/Txn の直接 golden が見つからなくても、基底 field を追加しないという brief の型・repr 互換条件を優先する（brief:41–56）。

## 4. anomaly への表・取引種別の付与と出力点

`_reasons` は identity を照合に使い、理由を生成する際だけ `(table, hex)` を分解する。v2 は現行 `EdgeReason`、v3 は `EdgeReasonV3(key=hex, table=table, ...)` を返す（`dsg.py:774`）。

- ww 理由の整列は v2 では現在の hex 順、v3 では `(table, hex)` の辞書順。
- wr/rw 理由は現在の read 行順を維持。
- cycle の選択は変更しない。

`anomalies` は選ばれた `nodes` に対して `_txn_for_id(node).tx_type` を取得し、`AnomalyV3.cycle_tx_types` に同順で格納する。compact でも `_txn_from_columns` が復元するため同じ結果になる（`dsg.py:764,838,847`、`parse.py:520`）。

出力点は **`core.py` の新関数 `result_to_dict_v3(res)`** とする。既存 `result_to_dict(res)` が作る新しい dict を基に、`AnomalyV3` だけ拡張する。package 再 export、CLI 配線、receipt digest の変更は行わない（`core.py:25,256`、`__init__.py:20`、`cli.py:90`）。

返す dict の形は次のとおり。既存の全 top-level field はそのまま残る。

```python
{
    # trace_dir, verdict, certified, serializable, stats,
    # integrity, anomaly_count, total_cycles は既存出力と同じ
    "anomalies": [
        {
            "phenomenon": "G2",
            "length": 2,
            "cycle": [0, 1],
            "cycle_nodes": [
                {"txid": 0, "tx_type": 1},
                {"txid": 1, "tx_type": 2},
            ],
            "edges": [
                {
                    "from": 0,
                    "to": 1,
                    "types": ["rw"],
                    "reasons": [
                        {
                            "type": "rw",
                            "key": "aa",
                            "u_ver": [1, 0],
                            "v_ver": [2, 1],
                            "table": 0,
                        }
                    ],
                },
                # 閉じる辺も同形
            ],
        }
    ],
}
```

`u_ver/v_ver` の省略条件は旧 reporter と同じ。v2 の anomaly には field を追加しない。v3 anomaly の節点数不一致や基底 reason 混入は出力時に例外とし、`zip` で黙って切り捨てない（既存出力構造：`report.py:17,26,35,96`）。

cycle がない結果は旧 dict と同形でよい。この関数は run schema の宣言口ではなく、v3 anomaly の拡張射影とする。これにより空 run の schema を推定する必要もない。

## 5. X/I の tuple と core.py の notes

**3要素 tuple を維持し、第2要素を object identity にする。**

```python
# v2
(txid, "aa", reason)

# v3
(txid, (table, "aa"), reason)
```

これなら既存の `for t, k, r in ...` と reason 集計を維持できる。4要素 tuple 化はしない（`parse.py:391,400`、`core.py:124,128,142,146`）。

core の sample 文字列だけ条件分岐する。

```text
v2: txn0 key=aa (not-locked-at-entry)
v3: txn0 table=0 key=aa (not-locked-at-entry)
```

v2 の既存 f-string、違反件数、reason 別集計、notes の説明部分は保存する。X/I の table は parse issues と notes に残り、違反件数は従来の integrity へ入る（`core.py:121–154`）。

同様に version-dup notes は、v3 の場合だけ `table=... key=...` を出す。object・packed・tuple の3箇所で同じ書式にする。v2 の現行文字列は保存する（`dsg.py:361,489,520`、`test_verifier.py:2719,2979`）。

X/I は `_check_key` と `_expect` を引き続き通し、nR/nW に加算しない。循環のない fixture では違反により `indeterminate`、循環がある場合は現在の優先順位どおり `non-serializable` になる（`parse.py:388–401`、`model.py:511–514`）。

## 6. consumer の静的列挙

`orchestrator/` と `tools/` の Python ソースを検索した。型名を含む自然言語コメントや、hook の `"Read"/"Write"` は除外した。

| 対象 | consumer と影響 |
|---|---|
| `parse_trace_dir` | 定義 `parse.py:840`、再 export `__init__.py:41,60`。返り値の tuple 形は保存、v3 の txn 要素だけ派生型になる |
| `Read / Write` | `parse.py:42,370,381,531,538`、`model.py:334,335`、再 export `__init__.py:39`。v2 は従来型、v3 は table 付き派生型 |
| `Txn` | `parse.py:246,266,283,296,473,520,549,788,840`、`dsg.py:315,318,764`、再 export `__init__.py:39`。既存 API shape を維持 |
| `EdgeReason` | `dsg.py:774,788,793,802`、`model.py:379`、`report.py:13,17`、再 export `__init__.py:39`。旧 reporter は table を出さない |
| `Anomaly` | `dsg.py:826,847`、`model.py:485`、`report.py:13,35`、再 export `__init__.py:39`。旧 reporter は取引種別を出さない |
| `_CompactTrace` | `parse.py:230,250,719,775`、`dsg.py:32,144,316,329,388`、`core.py:23,38` |
| `_ParsedFileColumns` | `parse.py:182,225,233,514,520,602,717,833`。外部直接 consumer は検索で見つからなかった |
| tools | 上記 verifier API・型の直接 consumer は検索で見つからなかった |

`test_verifier.py` の `parse_trace_dir` 呼出しは、`:278,368,464,477,506,521,563,588,614,627,641,661,690,853,930,968,982,1048,1090,1155,1707,2096,2671,2826`。型の生成・比較箇所は §3 の一覧に記した。

compact の内部 consumer テストは、Mapping view（`test_verifier.py:2990,3051`）、配列のみを読む worker（`:3105`）、worker 間同値（`:3164`）、fallback（`:3299`）。table を packed worker 内で文字列から毎回復元する変更は、この既存設計を崩すため採用しない。

間接 consumer は次のとおり。

- `report.py:17,35`：派生型でも既存 field を読める。v3 情報が旧出力で省略される点は意図的な未配線。
- `core.py:254,256`：`VerifyResult` の exact type と旧出力 digest を維持する必要がある。
- `cli.py:70,90,99`：v3 は検証可能になるが、旧 JSON/text は表・取引種別を表示しない。
- `orchestrator/critic/digest.py:126,790,813`：dict の anomaly consumer。新出力の配線は後続。
- `test_campaign.py:5814`：基底型による既存 synthetic result は変更不要。
- `campaign_lock.py:58–63`：既存 module の内容変更は source digest を変えるが、closure の path・順序は変えない。

## 7. テスト計画

新規関数はすべて `test_verifier.py` に追加し、fixture は既存 `_tmp_trace` 形式にする。既存期待値は変更しない（`test_verifier.py:386,446`、brief:39）。

共通の比較では、同じ fixture を次の経路で通す。

- `_finish_legacy_parse → DSG(txns)`。
- compact packed、workers=`1,2`。
- 同じ compact を `_build_compact_tuple` へ通す経路、workers=`1,2`。
- 公開 `parse_trace_dir → DSG(txns)` の再構成経路。

full result の legacy 比較は core の parser をテスト内で差し替え、必ず復元する。tuple 強制の既存例は `test_verifier.py:2867`。辺集合だけでなく、integrity/notes、Mapping、anomaly の節点順・reason 順、新出力を比較する。

| 新規 test 関数 | fixture と assertion |
|---|---|
| `test_v3_serial_trace_matches_all_paths` | 表0/9への write と同じ表の版を読む後続 txn。全経路で同一結果。取引種別1〜5、op U/I/D、table 0〜10の受理も小 fixture のループで確認 |
| `test_v3_table_identity_separates_edges` | 下記 fixture。辺集合が **`{(0,1)}` のみ**、version dup=0、writer object 数=2。各経路で参照辺集合に一致 |
| `test_v3_neworder_order_same_key` | NewOrder/Order の同じ hex を異なる表に置く。INSERT/DELETE/UPDATE の文字列を保持し、別 object の版列・producer・辺集合になる |
| `test_v3_same_version_in_different_tables_is_not_duplicate` | 別表・同hex・同commitの2 writer。dup=0。比較対照として同表へ変えた fixture は dup=1、先頭 producer を保持 |
| `test_v3_cycle_reports_tables_and_tx_types` | `T0:R table0/W table9`、`T1:R table9/W table0` の genesis G2。reason の table、生hex、cycle_nodes の tx_type を exact 比較 |
| `test_v3_reasons_preserve_ww_wr_rw_identity` | 同表の連続writer・その版のreaderと、別表同hexの対照を置く。`_reasons` の ww/wr/rw を各々 exact 比較 |
| `test_v3_packed_mapping_and_read_bounds` | tuple identity による iteration/get/KeyError、別表の版を読んだ場合の orphan。境界外 read tid、read-only token が別fileのwriterへ解決されることも確認 |
| `test_v3_tuple_and_legacy_fallback_preserve_metadata` | writer version=`2**32` で tuple fallback、`2**63` で parse legacy fallback。table・tx_type・schema拒否・結果を照合 |
| `test_v3_rejects_mixed_schema_in_one_file` | v2→v3、v3→v2。両方とも2番目のCで拒否。E欠落を併発しても混在を受理しない |
| `test_v3_rejects_mixed_schema_across_files` | 両順序、同じtxidのlast-wins、間にP/A/空file。workers=1/2とlegacyで拒否 |
| `test_v3_schema_error_preserves_path_priority` | 先のfileの混在＋後のfileの構文/I/Oエラー、逆順、同じfileの混在C＋後続不正行。path/行・原因例外・親scannerを比較 |
| `test_v3_schema_reread_preserves_saved_error` | worker後に失敗fileを消す。通常の構文エラーとschema混在の双方で、保存した優先エラーを保持 |
| `test_v3_c_token_counts_are_strict` | C token数5/6/8/9/11を拒否。7/10は各々正常fixtureで受理。5の専用文言と既存8の文言を保存 |
| `test_v3_rejects_invalid_table_and_tx_type` | R/W/X/Iでtable=`-1,11,x,1.0`、Cでtx_type=`0,6,x,1.0`を拒否。追加字句ケースも固定 |
| `test_v3_rejects_invalid_write_op` | `Z,u,INSERT`を拒否。対照のv2は従来のop受理を保存 |
| `test_v3_rejects_scan_counts_and_tags` | nS/nQ各々=`1,-1,x`を拒否。S/Qタグも拒否 |
| `test_v3_rejects_v2_records_inside_frame` | v3 C内のv2形R/W/X/Iを各々拒否。逆向きのv3形をv2 C内へ入れても拒否 |
| `test_v3_x_i_keep_table_and_make_indeterminate` | 0R/0W frame内のX/I。tuple第2要素、notes、件数、indeterminateを確認。unknown reasonも違反として保持 |
| `test_v3_framing_violations_are_preserved` | R/W件数の過不足、EOF時E欠落、次C時E欠落、duplicate E。構造化違反と結果を全経路で照合 |
| `test_v3_schema_neutral_files_and_empty_run` | P/Aのみ・空fileはschema中立。全体にCなしなら従来どおりindeterminate |
| `test_v3_output_does_not_change_v2_projection` | v2の新関数出力が旧出力とJSON bytesまで一致。v3出力後も元resultと旧出力が変わらない。max_report=0/1も確認 |

表識別の主 fixture は設計:249に従い、次の形とする。

```text
# trace_0.log: A は Warehouse を読み Item を書く
C 0 0 2 2 1 1 0 0 1
R 0 0 aa 1 0
W 0 9 aa U 2 2
E 0

# trace_1.log: B の commit は A より前
C 1 1 2 1 0 1 0 0 2
W 1 0 aa U 2 1
E 1
```

表ありでは `0→1` のrwだけ。表を落とすと `1→0` のwwが増える。この exact 辺集合を表識別の受入に使い、G2 fixtureだけでは代替しない（設計:249,251）。

NewOrder/Order の **個別の表番号は今回の射影本文には列挙されていない**。実装時に brief が指す pin の `tpcc_tables.hh:16–28` を確認して定数を選ぶ。推測で番号を固定しない（brief:26、設計:72）。

既存のJSON golden、EdgeReason repr、全fixture hash、worker障害・順序テストをそのまま回す（`test_verifier.py:1404,2576,2760,2893,3299`）。本段では実行していない。

## 8. 変異の候補

変異は一度に一つ適用し、以下の指定 test が期待した assertion で失敗することを確認する。

| # | 変異 | 殺す test |
|---|---|---|
| 1 | object helper からtableを落とす | `test_v3_table_identity_separates_edges` |
| 2 | compact interningをraw hexだけに戻す | `test_v3_table_identity_separates_edges`、`test_v3_same_version_in_different_tables_is_not_duplicate` |
| 3 | packedのread-only token解決だけtableを無視 | `test_v3_packed_mapping_and_read_bounds` |
| 4 | tuple builder/workerだけtableを無視 | `test_v3_serial_trace_matches_all_paths`、`test_v3_table_identity_separates_edges` |
| 5 | 親のfile跨ぎschema検査を外す | `test_v3_rejects_mixed_schema_across_files` |
| 6 | failureをschema検査より先に全file分処理する | `test_v3_schema_error_preserves_path_priority` |
| 7 | tx_typeの範囲検査を外す | `test_v3_rejects_invalid_table_and_tx_type` |
| 8 | nS/nQ非0を受理する | `test_v3_rejects_scan_counts_and_tags` |
| 9 | `_reasons`だけraw key照合へ戻す | `test_v3_reasons_preserve_ww_wr_rw_identity` |
| 10 | compact復元でtx_typeを固定値にする、または新出力でtableを省く | `test_v3_cycle_reports_tables_and_tx_types` |

対象となる分岐は `parse.py:547,827`、`dsg.py:198,344,388,492,774`。特に表識別変異は設計:249の参照辺集合で殺す。

## 9. 規模

以下は**静的読解による変更行数の見積り**。追加と既存行の書換えを合わせた概算であり、実測ではない。

| file | 見積り | 主な内容 |
|---|---:|---|
| `model.py` | 55〜85行 | 派生型5種、identity helper・型 |
| `parse.py` | 190〜280行 | v3分岐、schema状態/outcome、親エラー順、intern列と復元 |
| `dsg.py` | 65〜110行 | identity lookup、v3 notes、reason/anomaly復元 |
| `core.py` | 40〜70行 | X/I sample分岐、新構造化出力 |
| `test_verifier.py` | 450〜650行 | 合成fixture、経路比較、拒否・順序・出力テスト |
| **合計** | **800〜1,195行** | 新module・新fixture directoryなし |

**実装子1本で足りる。** identity の型、token列、復元、reason生成を同時に整合させる必要があり、4 implementation fileを分割する利点は小さい。親briefの1 author案を支持する（brief:65–77）。独立の敵対検証は別段の責務とする（brief:80）。

## brief への異議

1. **「mergeでschema比較」だけではエラー優先順位を保存できない。** `_ParsedFileFailure` と `_ParsedFileNeedsLegacy` にも最初のschema観測を持たせ、`parse.py:827` のfailure先行処理を改める必要がある。これはP1の補強であり、成功columnsだけの変更では不足する（`parse.py:205,216,827`）。

2. **C token数のエラー文言には既存pinがある。** 新しい形式を説明するための一括文言変更でも `test_verifier.py:480` が赤になる。旧文言を保存したまま10 token分岐を追加する。

3. **P2の「十進整数」の字句範囲が未確定。** Pythonの`int`任せでは underscore を含む表記も入りうる。計画ではv3新fieldだけASCII十進数字を検査し、符号は任意の`+/-`を許して値域で判定、先頭ゼロも許す案とする。これなら表0の`-0`も値として0になる。canonical表記まで要求するなら別の契約なので、段3で確定すべき（brief:48、既存変換 `parse.py:332`）。

4. **「certifiedを今より広げない」とP7は文言上衝突する。** これまで拒否していたv3を受理し、P7どおりcertifiedになりうるなら、全入力に対する認証集合は増える。「v2の認証集合を広げず、v3では既存integrity条件を緩めない」と限定すべきである（brief:30,36,57）。

5. **P7の先送りは、単位5の着手条件として残す必要がある。** 存在履歴を実装しなければ、insert前genesisやdelete版のlive readを本単位は検査しない。pipelineの拒否は直呼びAPI/CLIの保証を強めない。単位4完了を設計§3.3の完了と扱ってはならない（設計:83,84,252、`cli.py:70`、`model.py:518`）。本計画ではP7どおり実装しない。

## 総括

- identity はv2=`str`、v3=`(table, hex)`とし、生key fieldは維持する（`dsg.py:357`）。
- compactは組単位のinternとtoken別table列を採用し、packed検索本体を保存する（`parse.py:563`、`dsg.py:50`）。
- 基底dataclassは変更せず、v3専用派生型に表・取引種別を載せる（`model.py:314,352`）。
- schema検査はfailure/overflowも含むsorted path順で行い、親再走査と整合させる（`parse.py:700,827`）。
- `core.py`に新出力関数を置き、report・CLI・capabilityの旧出力経路は保存する（`core.py:25,256`）。
- 受入は参照辺集合、全経路同値、既存bytes golden、10種の変異で確認する（設計:249、`test_verifier.py:2893`）。
- 未決は新整数fieldの字句契約と、NewOrder/Orderの個別表番号確認。存在履歴はP7の明示的な未実装事項である。
- 本段は静的読解のみ。ファイル変更・テスト実行は行っていない。