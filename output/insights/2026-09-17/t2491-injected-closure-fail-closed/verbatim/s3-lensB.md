## 誤拒否の追跡 (production 4 箇所、handler ごと)

**v1.1 を文字どおり適用すると、4 箇所とも covered に残る予測であり、親の v1.1 の追跡と食い違わない。** AST を独立に走査して enclosing try と handler の末尾を確認した。pytest・分類関数・変異は実行していない。

以下の略記を用いる。行番号は変更前 checkout のもの。

- **T**: [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py)
- **S**: [s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py)
- **O**: [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py)
- **N**: [s8b_oracle_n_pilot.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py)

| sink / check | 内側からの handler 追跡 | v1.1 の結果 |
|---|---|---|
| S:1208 / 1218 | 1204-try: 1311 WAL tuple は Attribute なので **MAYBE**、1313 bare `raise` → 次へ。1314 `_SortSwoOracleRejected` は module scope ClassDef（125）なので **NONE**、末尾代入でも読み飛ばす。1321 `DriverError` は **DEFINITE**、1323 bare `raise` → 外側へ。1324 `Exception` は先行 DEFINITE が捕捉するため調べない。1151-try は handler なし → 通過。 | covered 維持 |
| S:1288 / 1295 | 1279-try: 1302 WAL tuple は **MAYBE**、1304 bare `raise`。1305 `DriverError` は **DEFINITE**、1306 bare `raise` → 外側へ。1307 `Exception` は調べない。次に1204-tryを上と同じ順で通り、1151-tryを通過。 | covered 維持 |
| O:1788 / 1801 | 1730-try: 1808 WAL tuple は **MAYBE**、1810 bare `raise`。1811 `S1DriverError` は module import による **DEFINITE**、1812–1814 は `raise OracleDriverError(...) from exc` → 規則により追跡終了。1815 `Exception` と1660-tryは調べない。 | covered 維持 |
| N:997 / 1018 | 1017-try: 1028 `S1DriverError` は module import による **DEFINITE**、1029 は `raise PilotError(...) from exc` → 追跡終了。996-tryは sink を囲むが check を囲まない。 | covered 維持 |

補足：

- **(a)** `_SortSwoOracleRejected` は未知名ではない。S:125 の module scope ClassDef により NONE。ここを MAYBE とすると S の2 sinkを誤拒否する。
- **(b)** O:1730 の WAL tuple は NONE ではなく MAYBE。末尾は確かに bare `raise`。
- **(c)** 1151-tryは handler がないので、例外判定上は拒否理由を作らない。T:1891–1892 の既存 flow 状態合流を、新しい例外判定の拒否条件と混同してはいけない。finally の抑止は v1.1 の保証外。
- **(d)** T:1856–1865 は with body を同じ scope で `_flow_block` に渡す。try stackをそこで初期化しなければ、S:1218/1295 と O:1801 に enclosing tryが引き継がれる。`__exit__` の非抑止を証明するわけではない。

plan の「O:1660 の末尾 Break により production と両立しない」という結論は **v1 には適合するが、v1.1 では更新が必要**。ただし、変換再送出で止める規則自体には後述の問題がある。

## scope 逸脱の判定 (D1882 / D1869 / 追加 gate)

**共有 method に触れること自体は、D1869 違反とは判定しない。** D1882 自身が、対象を「族全体に効く共有機構の変更」と認識したうえで名指しの判定変更を認めている。境界は編集する method 名ではなく、変更する判定と検査義務である。

T:1583 の記録型、1727 の記録、1866 の stack 操作、2175 の injected 判定を変更する案は、次の条件を守れば名指し分の実装として説明できる。

- 新情報の利用先が injected 被覆判定だけ。
- T:1730以降の campaign 状態更新、`returned_evidence_names`、既存 flow の継続・合流結果を変更しない。
- stack は scope ごとに初期化し、当該 try の body処理中だけ保持する。
- campaign 用の import真正性・shadow検査を injected に流用しない。

**型の分類表と module import の束縛名取得**は、例外 handler を判定する局所的な材料であり、それだけで却下された import真正性検査にはならない。真正性や実行順を証明したと名乗るなら scope を超える。

**module Name alias chain**は境界に近い。既存 `module_assignments` の参照だけでも、新しい受理形を正当化する仕組みにはなる。production 4件にも M1 にも不要なので、最小形を優先するなら今回外し、alias は MAYBE とするのがよい。chain を残す場合も、最後の代入表を「その位置での実際の束縛」の証明と扱ってはいけない。

**変換再送出後の追跡停止**は一般的な例外追跡機構の追加ではなく、保証範囲を狭める選択である。scope 逸脱ではないが、「拒否が外まで伝播する」保証とは異なる。さらに MAYBE 分岐との合成に問題がある。

**P4 の独立 assert を落とす判断には賛成。** helper の全 raise形や基底 class を将来も固定する検査は、名指し判定とは別の source形状の義務を作る。

**新 production pin は、対象4 sinkの誤拒否を検出する回帰テストなら許容できる。** ただし plan の以下は分けて扱うべきである。

- 4 sinkの covered確認：本変更に直接対応する。
- 全 injected sink集合を5件へ固定：将来の member追加に新たな更新義務を作る。
- floor の deferred固定：既存台帳検査と重複する。
- 全 production の `failures == []`：既存閉包検査と重複する。

最小形としては、対象4 sinkの結果だけを確認し、全体の閉包・台帳義務は既存 nodeに任せることを推奨する。

## 変異の帰属 (M1 の完全集合予測、M2〜M4 の既存 test 重複、新旧両走)

**M1 の新実装側の予測赤集合は、plan の新 production pinを含めて7 node。** baseline成立、v1.1どおりの実装、指定2ファイルの走行を前提とする。

| ファイル | 赤になる node | 発火する assertion |
|---|---|---|
| T | `test_define_sink_cross_product_has_no_unreviewed_ungated_member` | 2698: 全 production の `failures == []` |
| T | `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` | 2991: `failures == []`。2984/2990の campaign件数pinではない |
| T | `test_define_sink_cross_product_t2520_certify_entry_removal` | 3013: 台帳entryを外す前の `failures == []` |
| T | `test_define_sink_cross_product_classifies_t2491_injected_production_sinks_exactly` | N:997 の covered pin、または全体 failures assertion |
| `test_s8b_oracle_n_pilot.py` | `test_injected_build_fn_without_condition_records_is_rejected` | 782: `pytest.raises(PilotError, ...)` |
| 同上 | `test_build_binaries_uses_binding_flags_and_prepared_records_independently` | 819: 後半の不一致recordに対する `pytest.raises` |
| 同上 | `test_r33_successor_protocol_document_loads_from_repository` | 323: 現行driver bytesのdigest pin |

t2520 の3021も、到達すれば N の追加failureにより不一致になる。しかし実際の最初の失敗は3013であり、別nodeとして数えない。

他の `failures == []` は、T:2938、2964、3067、3310、3331、3478にある。いずれも source辞書をその場で組む syntheticであり、M1 の production変更を読まない。**M1 の追加赤nodeには数えない。** sink inventoryと台帳の生存確認も、同じ行数でhandlerだけを置換するM1では変化しない予測。

r33 は完全な観測赤集合には含めるが、**M1の意味的な検出証拠から除外する**。T-2154台帳どおり、driver bytes変更に反応する冗長gateである。

M2〜M4について、指定範囲の既存assertionを確認した結果は次のとおり。

| 既存test群 | assertion単位での確認 | M2〜M4への反応予測 |
|---|---|---|
| 2864 未登録injected | 2875 failure包含、2882非deferred。返却物check自体がない | 新bool恒真でも一致checkが増えず、不変 |
| 2885 gate支配 | 2903のbuildcache failure完全一致 | injected専用変更なら不変 |
| 2918/2941 with正例 | sink完全一致、failure空、covered件数、再度failure空 | campaign経路なので不変 |
| 2967 production pin | campaign件数2件、全体failure空 | productionに拒否対象の握り潰しがないbaselineでは不変 |
| 2994 t2520 | sink/台帳/14 macro、before空、台帳削除後のexact failure、件数、他sink不変 | M2〜M4だけなら不変 |
| 3030 opaque closure | marker不在、sink一致、unresolved分類・failure一致 | buildcacheなので不変 |
| 3049 local fixed shadow | marker不在、sink一致、unreachable分類、failure空 | buildcacheなので不変 |
| 3070〜3200の8負例 | 各sink一致と、各1件の `unresolved` failure一致 | すべてcampaign。新条件の緩和を検出しない |

従って、**既存syntheticがM2〜M4を既に落とすという根拠はない**。帰属は新injected負例に求める。

ただしM3/M4の予約anchorはv1.1に合わせ直す必要がある。plan:271–276のbool判定は三値分類と一致しない。M3は「bareをDEFINITEからNONEへ」の意味を固定する。M4も「末尾Raise条件だけを緩める」のか、bare/変換の区別まで変えるのかを分離しないと、意図した変異の帰属が成立しない。

**新旧両走のspecは、意味として次の4ケースが必要。** 以下は登録内容の仕様であり、未確認のharness JSON schemaを推測したものではない。

| case | Tの版 | Nの変更 | 期待 |
|---|---|---|---|
| old-baseline | `38353207f`のT | なし | baseline成立 |
| old-M1 | 同上 | M1 | 負例2件+r33の3赤。閉包nodeはPASSED |
| new-baseline | author後のT | なし | baseline成立 |
| new-M1 | 同上 | 同一M1 | 上表の7赤。閉包nodeはFAILED |

旧Tはgitから読み取り可能で、現在のcheckoutのTとbytes一致した。その他の入力を同一に保ち、Tの版だけを替える設計にできる。

runner argvは台帳と同じ次の形が妥当。

```text
python3 tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_s8b_oracle_n_pilot.py orchestrator/tests/test_ccbench_spawn_sites.py
```

ただし `-rf` の失敗一覧だけでは、旧閉包nodeの **PASSED** を積極的に示せない。node別結果を保存し、収集・実行済みでskipされていないことまで確認する必要がある。

また射影されたT-2154台帳にはm04の置換bytesがない。現在のN:1028–1029とplanの置換は確認できるが、**歴史的m04とのbytes完全一致は、この資料だけでは独立確認できない**。親の元spec照合を登録証拠に残すべきである。

「新テストだけが検出する差分」という表現も修正が必要。M1では、新test以外に**判定が強化された既存3 node**も新たに発火する。一方、M2〜M4の新しい拒否条件を守る役割は新syntheticに帰属する。

## synthetic test の実在条件

**planのsourceはsinkとして認識される。正例のcovered期待だけがv1.1と矛盾する。**

- T:715–717の `_INJECTABLE_NAMES` に `build_fn` がある。
- T:749–760で関数引数 `build_fn` がinjected集合へ入る。
- 複数行importは通常の1個の `ImportFrom`。`callable_aliases` に入るのは `X` と `require_returned_condition_evidence` であり、`build_fn` ではない。
- T:823–824で直接の `build_fn(genome)` が `injected-build_fn` になる。source先頭に空行がなければsinkは6行目。
- T:2002–2018で代入先 `built` が得られ、checkの第一引数と一致する。
- `orchestrator/campaign/` はT:594のproduction走査root内。さらにsynthetic辞書を直接渡す場合、T:891の列挙関数はproduction rootによる絞り込みを行わない。実ファイル作成は不要。
- `BACKOFF_FIXED` がsource macro inventoryに入り、T:2554–2555で reachable。checkを被覆に数えなければ `failure-reachable` になる。

plan:122–123の未知名 `ChildError` は **MAYBE + 末尾Pass**。v1.1なら、後続の `except X: raise` を見る前に拒否する。したがって正しい期待は、現sourceのままなら次である。

```python
classifications == {sink: Counter({"failure-reachable": 1})}
failures == [("BACKOFF_FIXED", sink, "reachable")]
```

covered正例にするには、import直後へmodule scopeの定義を加える。

```python
class ChildError(X):
    pass
```

これで `ChildError` がNONEとなる。空行なしでこの2行を追加するなら、sinkは**6から8行目**へ移るため `_BuildSink` も更新する。未知名の元sourceは、別のMAYBE負例として残す価値がある。

## 推奨 (real 最大 3 件、裁定パッケージ候補)

1. **real：正例がv1.1では負例になっている。**
   [s2-plan.md:122](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s2-plan.md:122)。`ChildError` をmodule scope ClassDefとして定義し、sink行番号を更新する。元sourceは未知handlerの拒否例にする。規則を未知名NONEへ戻して合わせるべきではない。

2. **real：MAYBEのbare再送出経路を、後続DEFINITEの変換で打ち切る規則は不完全。**
   v1.1のP1/P2、適用点はO:1808–1814と外側1838–1860。先行MAYBEがEを捕捉した場合、bare `raise` は後続DEFINITE handlerへ進まず、Eのまま外へ出る。後続DEFINITEが変換するのは、先行MAYBEが捕捉しなかった経路だけである。

   従って、**「MAYBE bareを通過 → DEFINITE変換なので全追跡終了」では、未変換Eの外側経路を捨てる**。これは変換後例外を保証外とするだけでは説明できない。是正案は、MAYBEのbare経路について外側追跡を残すこと。ただしその保守的規則ではOの外側末尾Breakが問題になるため、production coveredとの両立を段4で裁定する必要がある。本相談は現在のWAL型が実際にEを捕まえると主張しているわけではない。

3. **real：M1のKILLEDだけでは本修正の帰属にならず、予約変異も旧仕様のまま。**
   [s2-plan.md:238](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s2-plan.md:238)、同271/289。旧判定でも負例2件とdigest pinが赤になる。旧閉包PASSED／新閉包FAILEDのnode別証拠を登録し、完全赤集合と意味的帰属集合を分ける。M3/M4は三値分類とbare/変換の区別に対応するexact anchorへ改訂する。

裁定パッケージ候補：

- module alias chainを今回必要な最小形に含めるか。推奨は外してMAYBE。
- production pinを対象4件へ限定するか。推奨は全injected集合の固定と全体failure再assertを省く。
- MAYBEの未変換経路を追うために必要な精密化を認めるか、それとも保証限界として明示的に裁定するか。
- with、finally、handler内の先行return、helperの送出型変更に対する保証範囲。今回の判定を包括的な「握り潰しなし」の証明とは呼ばない。

## 総括

v1.1のproduction追跡は親と一致し、4箇所は規則上coveredに残る。ただし、**その規則にはMAYBEからの未変換再送出経路を落とす問題がある**。planの未知`ChildError`正例と変異登録も更新が必要である。

共有flowへの限定的な記録追加をscope違反とは判定しない。alias解析と全member固定は最小化すべきである。M1の予測赤集合は新側7件・旧側3件で、修正の証拠は閉包nodeの旧PASSED／新FAILEDに置く。すべて静的検査・予測であり、テスト成功や変異実測結果は主張しない。