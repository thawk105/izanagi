## プラン

### 単位 A — 二乗の除去

対象: `orchestrator/campaign/p3_b4_wiring_probe.py`

- `:720-722` に、private API を使わない `_split_source_lines(source)` と `_get_source_segment(lines, node, *, padded=False)` を追加する。
- `_split_source_lines` は source を一度だけ線形走査する。改行として扱うのは `\n`、`\r`、`\r\n` だけとし、改行文字を各要素に残す。form feed や他の Unicode 行区切り文字では分割しない。末尾が改行なら空要素を追加せず、空 source は空 list とする。これは CPython 3.10 の `_splitlines_no_ff` の結果を private API なしで再現する。
- `_get_source_segment` は CPython 3.10 の次の意味論をそのまま写す。

  - `lineno` と `end_lineno` は 1 origin なので list index 用に 1 を引く。
  - `col_offset` と `end_col_offset` は文字数ではなく、各行を UTF-8 encode した後の byte offset として扱う。終端は exclusive。
  - 単一行は `line.encode("utf-8")[col_offset:end_col_offset].decode("utf-8")`。
  - 複数行は先頭行を `col_offset:`、末尾行を `:end_col_offset` で byte slice し、中間行を改行込みで連結する。
  - `padded=True` は複数行だけに作用する。先頭行の `col_offset` より前を decode し、tab と form feed は保存、それ以外を ASCII space に置換して先頭断片へ付ける。単一行では `padded` を無視する。
  - location 属性が欠落している場合、または `end_lineno` / `end_col_offset` が `None` の場合は `None`。開始属性そのものが `None`、範囲外 index、UTF-8 code point の途中を指す不正 offset などについて独自補正は加えず、stdlib と同じ例外または slice 動作を保つ。
  - CRLF を一つの改行として保持し、CR 単独も保持する。複数行連結時にも改行 bytes を変えない。

- `_FunctionCallVisitor.__init__` の `:723-738` は `source: str` の代わりに `source_lines: Sequence[str]` を受け、`self.source_lines` に同じ list 参照を保持する。visitor ごとに分割してはいけない。
- `_analyze_source` の `:828-855` では、`ast.parse` 成功直後に `source_lines = _split_source_lines(source)` を一度だけ作り、同 module の全 `_FunctionCallVisitor` に渡す。これで module あたり一回になる。
- `visit_If` の `:749-759` は次の一行だけを置き換える。

```python
guard = _get_source_segment(self.source_lines, node.test) or ast.unparse(node.test)
```

- `guard.strip()`、else 側の `f"not ({guard.strip()})"`、および `or ast.unparse(node.test)` は現状どおり残す。空文字も従来同様 fallback 対象になる。

下流追跡、P1:

- guard は `_StaticCall.guards` (`:142-147`) に格納され、`visit_Call` (`:791-825`) で call edge に固定される。
- `_reason_paths` (`:1101-1122`) は `edge.callee` だけを使い、guard を見ない。したがって `_build_inventory` (`:1137-1162`) の対象関数集合、`guard.seal` (`:551-583`) の遮断対象、`inventory_sha256` (`:2051`) は guard 文字列に依存しない。
- `_static_module_manifest` (`:1027-1037`) とその hash (`:1975-1977`) も source bytes の hash であり、抽出された guard には依存しない。
- 一方、`_proof_switchpoint` は guard を `path` と `conditional_edges` に入れる (`:1069-1086`)。それが `_check_switchpoint` の `static` (`:1550-1553`)、evidence の `checks` (`:2162`) に入り、`_canonical_bytes` と SHA-256 (`:1778-1779`) を経て JSON と sidecar (`:1785-1801`) に出る。
- 結論は「guard 文字列だけでは受理集合は変わらないが、証拠 JSON とその digest は変わる」。完全一致は出力契約のため必要である。既存テストも `:132-142` と `:1103-1114` で代表 guard を逐語固定している。

### 単位 B — 重複呼び出しの解消

対象: `orchestrator/tests/test_p3_b4_wiring_probe.py`

`test_real_producer_entry_is_interdicted_before_body` の child literal `:378-379` を逐語的に次へ変更する。

```python
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
```

続く `inventory = ...` (`:380`) と `guard.seal(...)` (`:381`) は移動しない。したがって順序は audit install、static preflight、runtime import、inventory、seal、producer 呼び出しのままであり、`attempts == 1` (`:401-412`) も変わらない。

`test_exec_compile_and_new_import_are_rejected_after_seal` の child literal `:937-938` も逐語的に次へ変更する。

```python
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
```

`guard.seal(...)` (`:939`) はその後のままとし、seal 後に exec と import を拒否する順序や期待値 `["exec", "import"]` (`:940-955`) は変更しない。

P2 の全経路:

- 製品側は `_load_runtime` の省略時 fallback `p3_b4_wiring_probe.py:1178-1185` と、`main` の明示的な一回ロード `:1972-1973` の二経路。
- test の明示的 `_load_static_modules` は `test_p3_b4_wiring_probe.py:76,379,657,840,888,938` の6箇所。
- `_load_runtime` も `:77,378,658,841,889,937` の6箇所で、省略しているのは `:378` と `:937` だけ。
- 収集 node に展開すると、module fixture 利用が16 node、直接 child が13 node、`P.main` が static load まで到達するものが7 nodeで、単位 A の影響対象は計36 node。単位 B の重複解消対象は real producer の9 parameter nodeと exec/import の1 node、計10 node。
- 単一 process で file 全体を一回走らせる場合、module fixture を一回と数えると現状31回、B後は21回の static load になる。worker 分割時は module fixture が worker ごとに初期化される。
- 台帳 `:1103-1161` の29重量 nodeは、独立 child/main の20 nodeと、fixture setup が所要に計上された16中9 nodeに一致する。
- 22〜23秒帯の12 nodeは、fixture 経由9 node、`actual_main[base]`、module-swap、record-diff の3 nodeに分類でき、全て一回の static load 経路を持つ。静的経路上、名指しすべき未説明 node はない。24〜28秒帯も一回、43〜47秒帯はB対象の二回ロードと一致する。

### 単位 C — 等価性を pin する正例テスト

対象: `orchestrator/tests/test_p3_b4_wiring_probe.py`

- import 群 `:5-13` に `import ast` を追加する。
- fixture `:73-78` の後、または静的解析テスト群 `:126-255` に、全 module の比較 helper と正例テストを追加する。
- 正例は runtime を必要としないため、専用に `static = P._load_static_modules()` を一回だけ呼ぶ。
- untouched な `ast.get_source_segment` を全 nodeで素朴に呼ぶと、親計測から約27〜30秒が再発する。採る案は、テスト内だけで元の `ast._splitlines_no_ff` を保存し、source ごとの結果を cache する wrapper を `monkeypatch` で差すこと。元 private は各 source について一回実行されるため、reference の行分割意味論は変わらず、公開 `ast.get_source_segment` の byte slicing も通る。
- `sorted(static.values(), key=relative_path)` を走査し、各 module では `_split_source_lines(module.source)` を一回だけ作る。`ast.walk(module.tree)` の全 `ast.If` について次を要求する。

```python
actual = P._get_source_segment(lines, node.test)
expected = ast.get_source_segment(module.source, node.test)
assert actual == expected, (
    f"source segment mismatch: {module.relative_path}:{node.test.lineno}"
)
```

- `len(static) == 45` と比較件数が非ゼロであることも pin する。これにより45 module全部を走査し、visitor が現在到達しない module-level、class method、nested function 内の `if` まで含められる。
- 別の小さい境界テストで、UTF-8 multibyte が offset より前と範囲内にある場合、単一行、複数行、LF、CRLF、CR、form feed、`padded=False/True`、location 欠落による `None` を stdlib と比較する。
- test 内 private cache は CPython 3.10 固有の test harness 依存であり、製品依存ではない。private 名や signature が変わる interpreter 移行時には明示的に赤になる。これを避ける代替は、各 module 一個の代表 `if` だけを untouched public API と比較する案で、参考計算では reference 部分約0.4秒だが、同一 module 内の異なる UTF-8 offset、複数行範囲、末尾位置の検出力を失うため採らない。
- 所要見積りは、最適化後の static load 1.07秒に、45回の reference 分割と線形 walkを加えた約1.2〜2秒。未実測の推定である。

負例は同じ比較 oracleを再利用する。正例通過後に `P._get_source_segment` を monkeypatch し、最初の非 `None` 結果へ `"!"` を一文字追加する。その状態で小さい `_analyze_source` を通し、旧経路の結果と比較する。最初の `If.test` で `actual == expected` が偽になり、上記 `"source segment mismatch: path:line"` の assert が発火することを `pytest.raises(AssertionError, match="source segment mismatch")` で確認する。製品 helper 自体が同様に壊れた場合は、先行する全 module 正例の同じ assert が expectation wrapper より前に赤になる。

## 親 brief への異議

- P1 の「文字列が変わると受理集合も変わる」は、提示された実装では成立しない。inventory の閉包と seal は guard を参照しない。変わるのは静的証拠内容、JSON bytes、sidecar digest、および既存の逐語期待値である。
- I1 の「probe の出力 bytes を変えない」は文字どおりには達成不能である。出力には実行時刻 `p3_b4_wiring_probe.py:2073-2074` と、今回必ず変わる probe 自身の source hash `:2077-2080` が入る。要求は「guard 由来の値を変えず、許容済み可変 field 以外の意味論を変えない」と定義し直す必要がある。
- P2 の本 file 内の呼び出し分析は整合するが、「repo 内でこの file 固有」という広い主張は、指定された四資料以外を読めない今回の射影では検証不能である。
- P3 の140秒 node自体は台帳 `acceptance_duration_ledger.json:10065` に存在する。しかし140秒は300秒未満なので、それだけから「Aだけでは5分以内にならない」とは導けない。全走の並列度とA後の critical pathが必要である。
- 22〜23秒帯には静的に未説明の node はない。ただし台帳は scheduling hint なので、各 nodeの全 wall timeを解析費用だけへ排他的に帰属させたとは未確認である。

## 未実走・未確認

- pytest、`_load_static_modules`、probe main、profiler、性能測定は一切実走していない。
- 27.4秒、1.07秒、45 module、3023回は親 brief の実測値を使用した。
- 1.2〜2秒という新規テストの所要は計算量と親実測からの推定であり、実測ではない。
- CPython 3.10 の stdlib source 自体は射影外なので再読していない。上記意味論は、実装後に stdlib 比較テストで検証する前提である。
- repo 全体の同型二乗処理、および5分全走のA後 critical pathは未確認である。

## 総括

単位 A は `_analyze_source` で module ごとに一度だけ行分割し、private API を使わない CPython 3.10 等価 helperを visitorへ渡す案を採る。  
単位 B は二つの child literalを `static`、`runtime(guard, static)` の順へ直し、10 node分の重複を除く。  
単位 C は test内だけ reference splitterを cacheし、全45 moduleの全 `if` を約1〜2秒で比較する。  
最大の危険は UTF-8 byte offset、CRLF、form feed、`padded` の微妙な差と、test harnessだけが依存する stdlib private API のversion差である。  
guard完全一致は受理集合ではなく、証拠JSONの内容とdigestを守るための要件である。