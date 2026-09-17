## 変更面 (file:line 表)

**stack 案を採用する。ただし、brief の P1・P2 と「production 4 sink covered」は現状の source では両立しない。段 4 での解消が必要であり、そのまま author に渡せる確定プランではない。**

以下、`T` は `orchestrator/tests/test_ccbench_spawn_sites.py`。行番号は読んだ checkout の変更前位置。

| 場所 | 変更案 |
|---|---|
| T:1218–1222 の直後 | injected 判定専用の error class 名・捕捉対象組込み名を定義。campaign helper binding visitor は変更しない |
| T:1561–1573 の近傍 | module 直下の `ImportFrom` / s1 自身の `ClassDef` から error 名を収集。既存 `module_assignments` は変更せず参照する |
| T:1583–1588 | `returned_evidence_checks` を `(lineno, result_name, unswallowed)` に変更。scope の flow 開始ごとに空の try stack を設定 |
| T:1700 の直前 | injected 専用の捕捉型判定、handler 末尾判定、stack 集約 helper を追加 |
| T:1723–1729 | call 記録時に第三要素を計算。1730 行以降の campaign 用状態更新は変更しない |
| T:1866–1869 | `statement.body` の flow 中だけ try を push。Python の `try/finally` で必ず pop |
| T:2175–2182 | 三要素を unpack し、既存一致条件に `and unswallowed` を追加 |
| T:2183–2187 | コメントを限定した保証内容へ修正。with 抑止・局所 alias・条件 guard の反転を保証しない旨を記す |
| T:2882 の後、または 2911 の前 | injected synthetic 正例・負例を追加 |
| T:2991 の後 | production injected 4 covered / floor 1 deferred の pin を追加。ただし上記不整合の解消が前提 |

production、既存分類ロジック、既存 campaign synthetic は変更しない。

## 1〜5 の判断と根拠

**1. 判定は `_record_expression` で記録する。**

stack は `_GateFlowState` に混ぜない。T:1586–1588 の `self.bodies` ごとの flow で空から開始し、T:1867 の body flow の間だけ enclosing try を保持する。

- 入れ子関数の本体は T:1779–1789 でその場では flow されず、別 scope で処理される。親の try stack を引き継がない。
- decorator・default 等の定義時式は T:1781–1782 で親 scope の stack を使う。
- handler body、orelse、finalbody は当該 try を pop した後に処理する。当該 try の handlers はこれらの例外を捕まえない。さらに外側の try stack は保持する。
- with body は T:1856–1865 の既存処理を維持し、外側 try stack を引き継ぐ。`__exit__` による抑止は証明しない。s1:1208 の production 自体が with 形なので、一律拒否は不変条件と両立しない。

`coverage_for_sink` での AST 再走査案でも、scope 境界と「try のどの field 内か」を追えば同じ判定を作れる。しかし、単なる `ast.walk` と行範囲では handler / else / finally を誤って含める。既存 flow と別の traversal を追加する必要があるため採らない。

campaign 不変性の根拠は次のとおり。

- `_GateFlowState.returned_evidence_names`（T:1171）、交差・kill 処理、T:1730–1760 の更新を変更しない。
- `_campaign_checked_root`（T:2046–2146）とその呼出し（2160–2163）を変更しない。
- 新 bool の読取先は injected 分岐だけ。stack 操作で既存 flow の入力・出力・継続判定を変更しない。
- したがって campaign の計算結果は構造上不変。実測による確認は親に残す。

**2. P1 の捕捉型判定。**

| handler 型 | 判定案 |
|---|---|
| bare except | 捕まえる |
| `BaseException` / `Exception` / `RuntimeError` | 捕まえる |
| s1 module から import した `DriverError` の束縛名 | 捕まえる |
| s1 自身の module 直下の `class DriverError` | 捕まえる |
| tuple | 要素を再帰判定。一つでも捕まえるなら対象 |
| `_SortSwoOracleRejected`、WAL 型等 | P1 の限定表では捕まえない |
| 表で扱えない式・循環 alias | 不明として、その check を被覆に数えない |
| `TryStar` | 通常 Try と同義に扱わず、その body 内 check は被覆に数えない案 |

import は文字列検索でなく `self.tree.body` の `ast.ImportFrom` を読む。n_pilot:49–56、driver:61–69 は複数行でも一つの AST node であり、`alias.asname or alias.name` から `S1DriverError` を取得できる。相対 import の `node.module` は `s1_direct_comparison`。

s1 自身は module 直下に helper 定義と `DriverError` 定義があることを確認し、その名前を使う。子 class 名を error 名集合へ追加しない。s1:125 の `_SortSwoOracleRejected(DriverError)` は base の直接送出を捕まえず、1218 の check では1321–1323 の `DriverError → raise` が選ばれる。

T:1561–1573 の `module_assignments` は `X = S1DriverError` を `ast.Name` として保持するので、訪問済み集合付きで module alias chain を引ける。ただし最後の代入を保持する表であり、実行順・shadow の証明ではない。**catch 対象を見落とさないための限定利用**とし、循環や解決不能を安全扱いしない。局所 alias の一般解析は追加しない。

未知名をすべて「捕まえない」と扱う P1 は、任意の実行時束縛まで保証するものではない。この限界を明記する。

`TryStar` は現在の Python に `ast.TryStar` が存在しなかった。既存 T:1866 と同じ `type(node).__name__ == "TryStar"` で識別し、直接属性参照を避ける。

**3. P2 は末尾 top-level `ast.Raise`。ただし production 全 enclosing try では不成立。**

直近の handler は静的に以下を確認できた。

| check | 対象 handler | 末尾 |
|---|---|---|
| s1:1218 | s1:1321 `except DriverError` | `Raise` |
| s1:1295 | s1:1305 `except DriverError`、外側1321 | ともに `Raise` |
| driver:1801 | driver:1811 `except S1DriverError` | `Raise` |
| n_pilot:1018 | n_pilot:1028 `except S1DriverError` | `Raise` |

しかし driver:1801 の enclosing try は **1730 と1660の二つ**。1660-try の `except Exception`（1841–1860）は末尾が `Break`。1842–1846 に `if evaluate_started: ... raise` があるが、P2 は条件付き raise を拒否する。

したがって P1 を全 enclosing try に適用すると、driver:1788 は covered を失う。直近だけを調べる、条件付き raise を認める、production 固有の例外を置く、といった回避はこのプランに入れない。

P2 単体では以下を拒否する。

- 末尾 `pass` / `return` / 代入。
- 末尾 `if ...: raise`。
- 末尾 `try/finally` の内部だけにある raise。
- 末尾 `with` の内部だけにある raise。

後二者の保守的拒否は問題ない。ただし「末尾が Raise」は、先行する条件付き return や外側 finally の抑止まで証明しない。全面的な例外伝播保証とは呼ばない。

**4. P3 は採用。import 真正性・shadow の流用はしない。**

T:1388–1392 は helper の関数定義を `False` binding として記録する。T:1627–1628 はその binding を拒否するため、helper を定義する s1 自身には `_has_unshadowed_returned_evidence_helper` を適用できない。

既存の suffix・第一引数・行範囲条件を維持し、新条件を AND する。import 真正性検査の追加は D1882 の却下事項でもある。

**5. P4 は独立した追加 gate としては採用しない。**

技術的には T:878–888 の `_production_build_sources()` から s1 source を取得できる。新 production pin の近傍で AST を parse し、次を assert する形になる。

- module 直下の `DriverError` の bases が `RuntimeError`。
- module 直下の helper を一意に取得。
- helper 内の `ast.Raise` が非空で、各 `exc` が `DriverError(...)`。
- 内部 `observed_requests` の raise も含める。

静的走査では **raise は8箇所**だった。369、371、376、379、384、392、396、403 行であり、brief の7箇所は訂正が必要。

ただし source の将来形を別途禁止する assert は、新しい検査義務になる。D1869 と今回の「追加 gate を入れない」に従い、**P4 の独立 assert は落とし、今回の前提確認と code comment に留める案を推す**。既存 node への埋込みだけで追加 gate でなくなるとは扱わない。

## synthetic test 案 (source 文字列と期待値)

正例は次の source。先頭空行なし、sink は6行目。

```python
relative = "orchestrator/campaign/synthetic_t2491_reraise.py"
source = """from orchestrator.campaign.s1_direct_comparison import (
    DriverError as X, require_returned_condition_evidence,
)
def build(build_fn, genome):
    marker = 'BACKOFF_FIXED'
    built = build_fn(genome)
    try:
        require_returned_condition_evidence(built)
    except ChildError:
        pass
    except X:
        raise
    except Exception:
        return None
    return built
"""
```

期待値：

```python
sink = _BuildSink(relative, "<module>.build", 6, "injected-build_fn")
_benchmark_build_sinks({relative: source}) == {sink}
classifications == {sink: Counter({"covered": 1})}
failures == []
```

`ChildError` は P1 の未知名扱いを確認する静的 fixture。実行しない。

負例は次の source。sink 位置は同じ。

```python
relative = "orchestrator/campaign/synthetic_t2491_swallowed.py"
source = """from orchestrator.campaign.s1_direct_comparison import (
    DriverError as X, require_returned_condition_evidence,
)
def build(build_fn, genome):
    marker = 'BACKOFF_FIXED'
    built = build_fn(genome)
    try:
        require_returned_condition_evidence(built)
    except X:
        pass
    return built
"""
```

期待値：

```python
sink = _BuildSink(relative, "<module>.build", 6, "injected-build_fn")
_benchmark_build_sinks({relative: source}) == {sink}
classifications == {sink: Counter({"failure-reachable": 1})}
failures == [("BACKOFF_FIXED", sink, "reachable")]
```

両方とも patch 集合は `frozenset({"BACKOFF_FIXED"})`。

T:715–717、749–760、823–824 により、関数引数名 **`build_fn`** と直接の `build_fn(...)` call が必要。`builder` 等へ変えない。代入先 `built` は T:2012–2018 で取得される。

`marker` に macro を含むので T:2554–2555 により `reachable`。marker を除き macro inventory が空なら injected は2556–2557で `unresolved` となる。

追加する parameterized test の node 案：

- `test_define_sink_cross_product_t2491_accepts_injected_reraise`
  - try なし、bare raise、変換 raise。
  - 子 class 風 handler → X raise → Exception swallow。
  - tuple、複数行 import、module alias。
- `test_define_sink_cross_product_t2491_rejects_injected_swallow`
  - IDs: `error-pass`, `bare-pass`, `exception-return`, `assignment`, `conditional-raise`。
  - 外側 handler が握り潰す形、with / try 内だけの raise も負例にする。
- scope 境界用 fixture。
  - 入れ子関数の本体へ親 stack が漏れない。
  - handler / else / finally 内の call に当該 try の handlers を適用しない。
  - その外側 try の handlers は適用する。

production pin の node 案は
`test_define_sink_cross_product_classifies_t2491_injected_production_sinks_exactly`。

`_production_build_sources()` と全 patch 集合で分類し、injected sink 集合を次の5件に固定する。

| path の末尾 | scope | line / kind | 期待 |
|---|---|---|---|
| s1_direct_comparison.py | `<module>.run_role` | 1208 / injected-prepare_cell_fn | covered 38 |
| s1_direct_comparison.py | `<module>.run_role` | 1288 / injected-evaluate_fn | covered 38 |
| s8b_oracle_driver.py | `<module>.run_block` | 1788 / injected-evaluate_fn | covered 38 |
| s8b_oracle_n_pilot.py | `<module>.build_binaries` | 997 / injected-build_fn | covered 38 |
| s8b_floor_campaign.py | `<module>.build_cells.invoke_build` | 4722 / injected-build_fn | deferred 38 |

さらに `failures == []` を assert する。**これは要求する受入形であり、現 P1/P2 で通るという予測ではない。**

## 変異 matrix 事前登録案 (anchor・期待 node)

M2〜M4 は未実装のため、新 helper の識別名と置換形をここで予約する。author 後に実 bytes で anchor の出現数が1であることを確認する。

**M0：等価コメント変異、期待 SURVIVED。**

T:2183–2186 の既存 anchor：

```python
        if matching_checks:
            # The validator compares the returned record macro set with the
            # concrete injected request.  Its dynamic coverage is therefore
```

最終実装ではここを保証限界コメントへ更新するため、その最終コメントと `if matching_checks:` を含む複数行を登録し、コメント1行だけを変更する。期待赤 node は空。

**M1：n_pilot の拒否握り潰し、期待 KILLED。**

`orchestrator/campaign/s8b_oracle_n_pilot.py:1028–1030`：

```python
            except S1DriverError as exc:
                raise PilotError(f"build condition evidence rejected: {exc}") from exc
            if getattr(built, "trace", None) is not False:
```

先頭2行を同じ indentation の次の2行へ置換する。

```python
            except S1DriverError:
                pass
```

期待赤 node の既知名：

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
- 同ファイルの `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- 同ファイルの新 production pin。
- `orchestrator/tests/test_s8b_oracle_n_pilot.py::test_r33_successor_protocol_document_loads_from_repository`
- T-2154 m04 の負例2件。**射影台帳に node 名がなく、現時点で名前は確定できない。**

最後の digest pin は観測する赤集合には含めるが、帰属証拠から外す。

なお T:3013 の既存
`test_define_sink_cross_product_t2520_certify_entry_removal`
にも `failures == []` がある。M1 による n_pilot failure でこの node も赤になる見込み。brief の列挙だけを完全な期待集合として登録しない。

**M2：新 bool を恒真化、期待 KILLED。**

T:1727–1729 に置く予定 anchor：

```python
                self.returned_evidence_checks.setdefault(scope, []).append(
                    (call.lineno, result_name, self._injected_check_unswallowed())
                )
```

第三要素だけ `True` にする。

期待赤は新 `test_define_sink_cross_product_t2491_rejects_injected_swallow` の負例群。既存 synthetic にはこの新条件を要求する node がないので、既存 node の発火は必須にしない。

**M3：bare except を捕捉対象から落とす、期待 KILLED。**

T:1700 直前の新 helper に置く予定 anchor：

```python
    def _injected_handler_catches_error(self, exception_type):
        if exception_type is None:
            return True
```

ここだけ `return False` に置換。

期待赤：

`test_define_sink_cross_product_t2491_rejects_injected_swallow[bare-pass]`

ほかの負例に bare handler を含めた場合は、その node も probe 後に登録する。

**M4：末尾 Raise を「内部に Raise がある」へ緩める、期待 KILLED。**

T:1700 直前の新 helper に置く予定 anchor：

```python
    def _injected_handler_reraises(self, handler):
        return bool(handler.body) and isinstance(handler.body[-1], ast.Raise)
```

判定を `ast.walk(handler)` に `ast.Raise` が一つでもある形へ変更。

期待赤：

- `test_define_sink_cross_product_t2491_rejects_injected_swallow[conditional-raise]`
- handler 内の with / try にだけ raise を置く新負例。

M2〜M4 について、赤くなる既存 node があるとは現資料から主張しない。新負例が帰属証拠となる。

全変異は **無変異 baseline 成立後**に実施する。現 P1/P2 のままでは production pin が baseline から赤になるため、matrix 本走へ進めない。

## 波及と変更しない一覧

- 変更ファイルは T のみ。
- production 3 file は読むだけ。M1 は親の変異環境での一時置換であり、成果物差分に含めない。
- `_DEFERRED_GATE_MEMBERS` の8 entry、floor の deferral は不変。
- campaign 用 helper binding visitor、`returned_evidence_names`、`_campaign_checked_root`、既存 synthetic 群は不変。
- docs、新 gate、新台帳、一般化した例外解析は追加しない。
- fresh worktree 作成、実装、pytest、受入走、変異実測は親側の工程。本段では行わない。

`rg` で T 内の `returned_evidence_checks` は **1583、1727、2176 の3箇所**。1583 が宣言、1727 が書込み、2176 が唯一の読取 consumer。1727 と2176が二つの consumer という表現は正確ではない。

## 未確定事項

1. **P1/P2 と production 4 covered の衝突。**
   driver:1660、1841–1860 の外側 handler を brief が取り落としている。直近 handler だけを見る変更は「各 enclosing try」の要件を弱めるため、無断で採らない。production 変更も scope 外であり、段4で仕様の整合を取る必要がある。

2. **T-2154 m04 の完全一致登録。**
   射影台帳は「負例2件＋冗長gate」を記載するが、負例の正確な node 名も実置換文字列も掲載していない。上記 M1 は brief と現 source に基づく候補。親が元 spec と照合する必要がある。

3. **前提資料の訂正。**
   helper の raise は8箇所。s1 の内側 try は1279、driver の直近 try は1730であり、1281・1775は campaign call の行。

4. **限定保証。**
   with 抑止、局所 alias、guard の反転、finally による抑止、変換後例外の一般的追跡は証明しない。P1/P2 を完全な「握り潰しなし」の証明として説明しない。

静的 AST 確認のみ実施した。最初の確認スクリプトは `ast.TryStar` 不在で失敗し、既存実装と同じ型名判定に直して走査した。pytest・分類実行・変異実測は未実施。

## 総括

実装位置は **scope ごとの try stack → call 記録の第三要素 → injected coverage の AND 条件**を採る。campaign の状態計算を変えず、既存受理集合を狭める構造にできる。

ただし現 brief の P1/P2 では driver の外側 handler により production pin が成立しない。この不整合を解消するまでは、4 sink covered・baseline 緑・M1 KILLED を主張できない。