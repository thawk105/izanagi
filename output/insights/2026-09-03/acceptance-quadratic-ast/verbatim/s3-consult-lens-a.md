## 所見

### 1. guard 完全一致は受理集合ではなく、一部の証拠出力だけの要件

**判定:** real

**根拠:** guard は `_StaticCall.guards` に保存される (`p3_b4_wiring_probe.py:142-146`, `:749-756`, `:823-824`)。一方、逆閉包は `edge.callee` だけを見る (`:1101-1122`)。従って inventory、seal、inventory hash は guard 非依存である (`:1137-1162`, `:551-570`, `:2051`)。static manifest も source bytes だけから作る (`:1027-1037`, `:1975-1977`)。

guard を出力へ渡すのは `_proof_switchpoint` が選ぶ二つの target pair の「最初の一致 edge」だけである (`:1061-1086`)。それが check の `static` (`:1550-1553`)、evidence の `checks` (`:2162`)、canonical JSON と digest (`:204-210`, `:1778-1794`)、CLI の digest (`:2171-2172`) へ流れる。

つまり、文字列が 1 byte 変わった場合は次の三分岐になる。

- 選択された proof edge の guard: JSON bytes、sidecar digest、CLI 表示 digest が変わる。
- その他の call edge の guard: 現コードで成果物は何も変わらない。
- helper が例外を出す場合: static preflight が失敗し、受理集合が変わりうる。

**成果物への影響:** 正常な文字列差だけなら受理集合、inventory、seal、manifest は不変であり、選択された proof edge に限って証拠 JSON と digest が変わる。

**推奨対応:** 出力契約を守るテストなら三 driver の proof edge を完全一致させれば足りる。全 45 module の全 `if` 比較は「汎用 helper の stdlib 等価性」という別契約として明記する。

### 2. 単位 A の主要アルゴリズムは正しいが、splitter の完全再現という記述は誤り

**判定:** real

**根拠:** プランは UTF-8 encode 後に byte slice するため、非 ASCII が offset より前または範囲内にあっても基本設計は正しい (`stage2-plan-out.md:11-17`)。CR、LF、CRLF だけで分割し、form feed や Unicode 行区切りで分割しない方針も正しい (`:8`)。単一行、複数行、`end_col_offset == 0` は記載された slice で stdlib と同じ結果になる。location 不足時の `None` と `or ast.unparse(node.test)` も保存される (`:16`, `:23-27`)。

ただし CPython 3.10 の `_splitlines_no_ff` は末尾の `$` による空 match を含むため、末尾要素として空文字を持つ。空 source も `[""]` であり、プランの「末尾改行なら空要素なし、空 source は空 list」は完全再現ではない (`stage2-plan-out.md:8`)。通常の `ast.parse` が生成する `If.test` はその終端空行を指さないため、対象 guard には通常影響しないが、synthetic node では `""` と `IndexError` の差になりうる。

`padded=True` は plan 上おおむね正しいが、`visit_If` は default の `False` しか使わないため、guard 保存には直接関係しない。

**成果物への影響:** 現在の valid parsed AST では影響しない見込みだが、helper の完全互換契約を放置すると synthetic node や将来の別 caller で fallback と例外の境界が変わる。

**推奨対応:** terminal empty element まで stdlib と合わせるか、helper を「`ast.parse` 由来の valid node 専用」と狭く定義する。境界テストには空 source と終端空行を指す synthetic node を追加する。

### 3. 指定された Unicode 改行境界と実 corpus の確認がプランから抜けている

**判定:** real はテスト欠落、疑いは対象 corpus の実在状況

**根拠:** プランの境界テストは UTF-8、LF、CRLF、CR、form feed までしか列挙していない (`stage2-plan-out.md:88`)。指定された `\x1c`、`\x85`、U+2028、U+2029、`end_col_offset == 0` は明記されていない。`str.splitlines` を誤用すれば、これらで `_splitlines_no_ff` と異なる結果になる。

また、45 module の source 内容は射影対象に含まれていない。従って「非 ASCII 行があるか」「特殊区切り文字があるか」は今回確認不能である。`45 module` 自体も親実測値と plan の pin 要求に依存する (`handoff.md:20-25`, `stage2-plan-out.md:87`)。

**成果物への影響:** synthetic 被覆がなければ、将来その文字を含む selected proof guard が追加された際に JSON/digest の変化または static preflight 失敗を見逃す。

**推奨対応:** 5 種すべてを synthetic source で stdlib と比較し、別途 45 module を byte/code-point scan して存在数と該当 path:line をテスト名またはコメントへ記録する。fallback は location 欠落だけでなく、空 segment による fallback も pin する。

### 4. 単位 B は通常の不変 source 下では seal の意味論を保つ

**判定:** real。ただし concurrent source mutation については疑いが残る

**根拠:** audit hook は通常 source の open 回数を記録しない。overlay の read path と protected root の read/write だけを台帳化する (`p3_b4_wiring_probe.py:490-517`)。compile/import も seal 前は mutation ledger に入らない (`:526-549`)。従って二回目の `_load_static_modules()` を除いても、質問にある audit 観測値は変わらない。

`attempts` は seal 後に inventory の code object が呼ばれた時だけ増える (`:594-612`)。対象 test の function 呼び出し順は変わらない (`test_p3_b4_wiring_probe.py:371-412`) ため、stable source なら `attempts == 1` は維持される。exec/import test も同様である (`:925-955`)。

二回目の load は preflight A と snapshot B を比較していない。実際の source hash 照合は `_load_runtime` 内で preflight と imported module file を比較して完結する (`p3_b4_wiring_probe.py:1178-1197`)。その後の load は意図的な二重検査ではなく、B の static graph と A の runtime code を混在させる可能性さえある。製品 `main` は同じ static snapshot を渡している (`:1972-1980`)。

ただし `_load_static_modules()` は filesystem を読むため、親 brief の「純粋計算」は厳密には誤りである。source が同時変更されれば、現行と変更後で観測する snapshot が違う。

**成果物への影響:** stable source では受理集合、attempts、seal、出力は不変。source 競合時だけ inventory または失敗境界が変わりうる。

**推奨対応:** 単位 B は採用してよい。source race も threat model に含めるなら、重複 parse ではなく preflight manifest と seal 直前 file hash の明示比較を別途設計する。

### 5. 単位 C の正例は helper を検査するが、配線と「一度だけの分割」を pin しない

**判定:** real

**根拠:** 提案された正例は `P._get_source_segment(...)` を直接呼ぶ (`stage2-plan-out.md:77-85`)。これは次の故障で赤になる。

- 文字 offset で slice する。
- UTF-8 byte 境界、単一行、複数行、CR/LF の処理を誤る。
- source segment に余分な文字を加える。
- corpus または synthetic case に存在する区切りを誤って分割する。

一方、次はすり抜ける。

- `_analyze_source` が新 helper を使わず、旧 `ast.get_source_segment` を使い続ける。
- visitor ごと、または `if` ごとに再分割して二乗を残す。
- `guard.strip()`、else の `not (...)`、fallback 配線を壊す。
- 全 module の直接比較だけ正しく、保存された `_StaticCall.guards` が別経路で変わる。

現配線の実体は `visit_If` と `_analyze_source` にある (`p3_b4_wiring_probe.py:749-759`, `:828-857`)。ここを直接観測する必要がある。

stdlib private splitterを先に保存し、その保存済み関数だけから reference cache を作るなら、正例は恒真ではない。ただし cache に `P._split_source_lines` を使ったり、expected を `P._get_source_segment` から作ったりすれば共通故障になる。

負例の記述は `_analyze_source` 後に何を `actual` として比較するかが不明確である (`stage2-plan-out.md:92`)。patched helper を直接再呼び出すだけなら、配線を検査できない。

**成果物への影響:** 放置すると等価性テストが緑でも二乗費用が残り、受入時間台帳が改善しない。また visitor 配線の差により selected guard の JSON/digest が変わりうる。

**推奨対応:** 次を分離する。

- helper oracle test: 保存済み stdlib splitterだけを reference に使う。
- integration test: `if cond: target()` の解析後、該当 `_StaticCall.guards` を直接検査する。
- call-count test: 複数 function、複数 `if` を含む source で `_split_source_lines` が module 当たり厳密に 1 回であることを spy する。
- fallback test: helper を `None` または `""` にし、`ast.unparse` の sentinel が保存されることを確認する。

### 6. 現 scope は局所最適化としては妥当だが、5 分達成の scope ではない

**判定:** real

**根拠:** 最新の親 brief 自身が、元の単位 A/B/C は wall critical path を動かさず、予測は 6.37 分のままとしている (`handoff.md:109-125`)。それでも冒頭では scope を「確定」として局所 A/B/C に限定している (`:33-38`)。

**成果物への影響:** この wave だけでは受入全走 5 分以内という利用者成果は達成されず、改善は主に CPU 総量と queue 回転率に留まる。

**推奨対応:** 本 wave の達成条件を「局所二乗除去」に明示的に縮めるか、real-repo grouping と certified evidence 鎖を別裁定として必須後続にする。親 brief 後半の `(B)/(C)` は単位 B/C と名前が衝突するため改名する。

## プランのうち採ってよい部分

- `_analyze_source` で module 当たり一度だけ CR/LF splitter を作り、全 visitor に同一 list を渡す構造。
- UTF-8 encode 後の byte slice、単一行と複数行の分岐、exclusive end offset。
- `guard.strip()`、else guard、`or ast.unparse(node.test)` の保存。
- 単位 B の二箇所を `static = ...`、`_load_runtime(guard, static)` の順に直すこと。
- stdlib の保存済み splitterを oracle とする方向。ただし helper、visitor 配線、分割回数のテストを分離すること。
- 全 45 module の walk は広い helper 回帰テストとしては有効。ただし現在の出力契約に必要な範囲より広い。

## 親 brief の誤り

- `ast.unparse` により guard が変わることを「受理集合の変更」とした `handoff.md:42-44` は誤り。現コードで変わるのは selected proof edge の証拠 JSON と digest であり、probe の pass 判定、inventory、seal は変わらない。
- 「probe の出力 bytes を変えない」も文字どおりには不可能。時刻が入る (`p3_b4_wiring_probe.py:2073-2074`) うえ、実装変更で `probe_sha256` が変わる (`:2077-2080`)。
- `_load_static_modules()` を「純粋計算」とした `handoff.md:27-30` は厳密には誤り。filesystem snapshot を読む。ただし二回目は比較を伴わないため、意図的な二重検査でもない。
- P1 は過剰である。全 guard の完全一致ではなく、現在の出力に届くのは `_proof_switchpoint` が選択する edge の guard だけである。
- `handoff.md:100-125` の critical path 数値と一般化は、射影外の台帳と `conftest.py` に依存しており、この consult では独立検証できない。「確定」ではなく、親の計測に基づくモデルとして扱うべきである。

## 未実走・未確認

- pytest、probe、`_load_static_modules()`、profiler、性能測定はすべて未実走。
- 対象 45 module は射影外のため、非 ASCII 行、`\x0c`、`\x1c`、`\x85`、U+2028、U+2029 の実在状況は未確認。
- CPython 3.10 の stdlib source は射影外のため、この場では直接再読していない。
- 27.4 秒、1.07 秒、3023 `if`、45 module、台帳時間、48 worker、critical path 数値は親 brief の値であり、独立再測定していない。
- concurrent source mutation が threat model に含まれるかは、指定資料から確定できない。

## 総括

単位 A の中心設計は valid parsed AST に対して guard を保存できるが、terminal empty line の stdlib 再現と境界テストを修正すべきである。  
guard の文字差は受理集合や seal を変えず、選択された proof edge の証拠 JSON と digest だけを変える。  
単位 B は stable source 下で安全であり、二回目の static load は意図的な source hash 二重検査ではない。  
単位 C は helper 比較に加え、visitor 配線、fallback、module 当たり一回という性能不変条件を直接 pin する必要がある。  
局所 A/B/C は採用可能だが、親自身の最新モデルでは受入全走 5 分以内を達成しない。