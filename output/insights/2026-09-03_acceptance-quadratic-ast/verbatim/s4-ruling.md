# 段 4 裁定 — 受入全走の高速化 wave

親が段 2 プランと段 3 の 2 レンズを読み、real / refuted と採否を確定した。
本書が段 5 実装子の契約の正本である。

## 0. 名前の規約 (レンズ A 所見 6 を採用)

- **単位 A / B / C** = 本 wave が実装するもの。
- **鎖 X** = `real-repo` xdist group による 96 node の直列化 (303.7 秒)。本 wave では実装しない。
- **鎖 Y** = `certified_evidence` fixture の排他 lock による 17 test の直列化 (258.1 秒)。同上。

## 1. 親自身の誤りの訂正 (両レンズが指摘。すべて採用)

| 親の記述 | 訂正 |
|---|---|
| worker 48 で分散 | **既定上限は 32** (`tools/run_tests.py:65` `_NPROC_CAP = 32`)。親が現物で追認 |
| shard 3 本 | **既定 2 本**。3 は `IZANAGI_ACCEPTANCE_SHARDS=3` 明示時だけ (`:253-297`)。親が現物で追認 |
| CPU 総量 7.6% 減 | 台帳は node duration であり CPU 計測ではない。**worker-time** と呼ぶ |
| file 単位の束縛は効かない | worker への束縛にはならないが、**同一 shard = 同一ホストへの affinity としては効く** |
| 17 test 中 7 test が共有 evidence を書く | **字句 heuristic による過大評価。**共有 path を触ると現物で言えるのは M17 と M18 の 2 件 |
| guard 文字列が変わると受理集合が変わる (P1) | 受理集合・inventory・seal は不変。変わるのは `_proof_switchpoint` が選ぶ edge の証拠 JSON と digest だけ |
| `_load_static_modules()` は純粋計算 | filesystem を読む。ただし 2 回目は比較を伴わないので二重検査ではない |
| probe の出力 bytes を変えない (I1) | 時刻 (`:2073-2074`) と自己 hash (`:2077-2080`) が入るため字義どおりには不可能 |

## 2. 所見の裁定

### real・採用 (must-fix)

- **A1 (レンズ A 所見 5): 単位 C は配線を pin しないと、二乗が残ったまま緑になる。**
  提案されたテストは helper を直接呼ぶだけなので、`_analyze_source` が新 helper を使わず
  旧経路のままでも通る。**成果物影響:** 受入所要が 1 秒も改善しないのに緑の受領証が出る。
  → 単位 C を 4 本に割る (下記 plan v2)。**module あたり分割ちょうど 1 回**を spy で pin する。
- **A2 (レンズ A 所見 3 + 親の実測): 合成 fixture の境界テストは必須。**
  親が 45 module / `if` 3282 個を走査した結果、guard の `col_offset` より前に非 ASCII がある行は
  **0 件**、form feed 等を含む module も **0 件**。全 module 比較テストでは
  byte/文字取り違えも form feed 分割も殺せない。**合成 fixture が唯一の検出経路**である。
- **A3 (レンズ A 所見 2): `_splitlines_no_ff` の終端空要素を再現するか、helper の射程を狭く定義する。**
  CPython は末尾に空文字要素を持つ。プランの「末尾改行なら空要素なし」は完全再現ではない。
  → helper を「`ast.parse` 由来の valid node 専用」と docstring で明示し、
  空 source と終端空行を指す synthetic node を境界テストへ入れる。

### real・採用 (scope 内、既定の実装)

- **B1 (レンズ A 所見 4): 単位 B は安全であり、かつ潜在的な正しさ改善である。**
  2 回目の load は意図的な二重検査ではなく、**静的 graph B と runtime code A を混在させうる。**
  製品 `main` は同じ snapshot を渡している。単位 B はテストを製品へ揃える変更である。

### real・不採用 (本 wave の scope 外。裁定パッケージまたは次の一手へ)

- **X1 (レンズ B 所見 2): 鎖 X の素朴な修正は跨ホスト race を作る。**
  `real-repo` group は内側の worker 直列化と、外側の **shard affinity** を兼ねる。
  `REAL_REPO_GROUP_CONFLICT_EDGES` (`tools/acceptance_shards.py:74-84`) は
  「別 shard は別ホストになりうるので local flock では閉じない」ための契約である。
  **書き手 4 件だけを group に残すと読み手が別ホストへ移り、flock が書き手を守らなくなる。**
  正しい設計は「全 96 node の shard affinity を保ったまま、xdist の worker grouping だけを
  read/write で割る」であり、`ItemRecord`・component・closure gate に affinity 属性を足す必要がある。
  既存の単一 unit / 相対順序テストの期待値を変えるため、`DW-S04` に従い**裁定パッケージ**とする。
  両レンズとも親のこの進め方を妥当と判定した。
- **Y1 (レンズ B 所見 3): 鎖 Y は期待値変更なしで短縮できる見込みが高い。**
  fixture の二段初期化 (最初だけ EX で seed を作り解放、以後は SH) と、
  確認済み reader を SH・M17/M18 を EX にする案。移設 helper は既に存在する (`:562-702`, `:705-769`)。
  ただし本 wave は plan も敵対検査も持たない。**次の一手として起票**する。

### real・記録のみ

- **M1 (レンズ B 所見 4): 親の critical path モデルは下限の比較であって wall の決定因の証明ではない。**
  allocator は台帳時間でなく component の node 数を weight にする (`:343-355`)。
  → insight には「下限モデル」と明記し、予測と呼ばない。
- **M2 (レンズ B 所見 6): 「5 分」の測定面が未定義。**
  canonical command・K・worker 数・queue 待ちの有無・collection〜teardown の範囲が未固定。
  → 裁定パッケージへ含める。

## 3. 本 wave の達成条件 (明示的に縮める)

**本 wave は「受入全走 5 分以内」を達成しない。** 両レンズがこれを独立に指摘した。
本 wave が主張してよいのは次だけである。

1. `p3_b4_wiring_probe.py` の事故的二乗を除去し、約 850 worker-seconds/走 を削る。
   台帳 903.6 秒 → 予算 50 秒 (楽観 33 秒)。**実装後に実測で置換する。**
2. 単位 B により、テストの静的 snapshot と runtime code の混在可能性を解消する。
3. 受入 5 分問題の律速を鎖 X・鎖 Y として同定し、鎖 X の安全な修正設計と
   測定面の未定義を裁定パッケージとして返す。

wall への効果は**今日は 0 秒**である。ただし両鎖を解いた後は詰め下限を
186.8 → 173.5 秒 (K=2) へ下げるので、約 13 秒の価値が現れる。

## 4. plan v2 (段 5 実装子の契約)

### 単位 A — `orchestrator/campaign/p3_b4_wiring_probe.py`

段 2 プランの構造をそのまま採る。

- `_split_source_lines(source)` と `_get_source_segment(lines, node, *, padded=False)` を追加。
  CR / LF / CRLF だけで分割し、form feed や Unicode 行区切りでは分割しない。
  `col_offset` / `end_col_offset` は **UTF-8 encode 後の byte offset** として扱う。終端は exclusive。
- **A3 に従い**、helper の docstring に「`ast.parse` 由来の valid node 専用」と射程を明記する。
- `_FunctionCallVisitor` は `source_lines` を受け取り、**visitor ごとに分割しない**。
- `_analyze_source` で `ast.parse` 成功直後に **module あたり 1 回だけ** `_split_source_lines` を呼ぶ。
- `visit_If` (`:750`) は次の 1 行だけを差し替える。
  `guard = _get_source_segment(self.source_lines, node.test) or ast.unparse(node.test)`
- `guard.strip()`、else 側の `f"not ({guard.strip()})"`、`or ast.unparse(...)` の fallback を保存する。

**禁止 (個別に列挙する。契約文書に書いてあるだけでは足りない):**

- `ast.unparse` への置換を禁じる。親の実測で `p3_s4_loop.py` の 162 個中 36 個の `if` で
  文字列が変わる。これは証拠 JSON と digest を変える。
- `ast._splitlines_no_ff` など stdlib private への**製品コードからの依存**を禁じる。
- 既存テストの期待値の変更・反転・緩和・skip・削除を禁じる。赤なら実装側が誤りとする。
- node を減らす、検査を消す、parametrize を畳むことによる高速化を禁じる。
- `_build_inventory`、`seal`、`_static_module_manifest`、`_proof_switchpoint` の意味論変更を禁じる。
- docs の編集と commit を禁じる。commit は親だけが行う。

### 単位 B — `orchestrator/tests/test_p3_b4_wiring_probe.py`

`:378` と `:937` の子 process 本文を逐語で次へ変える。

```
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
```

後続の `inventory = ...`、`guard.seal(...)` は移動しない。`attempts == 1` と
exec/import の期待値 `["exec", "import"]` を変えない。

### 単位 C — `orchestrator/tests/test_p3_b4_wiring_probe.py` (A1 に従い 4 本に割る)

1. **helper oracle test:** 全 45 module の全 `if` で
   `P._get_source_segment(lines, node.test)` == `ast.get_source_segment(module.source, node.test)`。
   reference 側は**テスト内でだけ**保存した stdlib splitter を source ごとに cache して使う。
   `P._split_source_lines` を reference に使ってはならない (共通故障になる)。
2. **境界 test (A2 に従い必須):** 合成 source で stdlib と比較する。
   multibyte が offset の前にある場合と範囲内にある場合、単一行、複数行、
   LF / CRLF / CR / form feed / `\x1c` / `\x85` / U+2028 / U+2029、
   `end_col_offset == 0`、空 source、終端空行を指す node、location 欠落による `None`。
3. **配線 test (A1 の本体):** `if cond: target()` を含む小さい source を `_analyze_source` に通し、
   得られた `_StaticCall.guards` の中身を直接検査する。helper を直接呼ばない。
   fallback 側も pin する (helper が `None` / `""` を返す場合に `ast.unparse` の値が入ること)。
4. **分割回数 test (A1 の本体):** 複数 function・複数 `if` を含む source で
   `_split_source_lines` を spy し、**module あたりちょうど 1 回**であることを assert する。
   これが二乗の再発を殺す唯一の検査である。

## 5. 変異事前登録 (`DW-M01`。実装前に凍結する)

各変異は単一理由であることを実装後に確認する。前後に同じ入力を拒否する層は無い
(guard は `_build_inventory` / `seal` を通らず `_proof_switchpoint` 経由で証拠へ出るだけ。
段 2 が file:line で追跡し、レンズ A が独立に追認した)。

| ID | 変異位置 | 内容 | 期待 | 殺す検査 |
|---|---|---|---|---|
| M-A1 | `_get_source_segment` | byte slice を文字 slice にする | KILLED | 単位 C-2 (境界)。C-1 では殺せない (実データ 0 件) |
| M-A2 | `_split_source_lines` | form feed でも分割する | KILLED | 単位 C-2 (境界)。C-1 では殺せない (実データ 0 件) |
| M-A3 | `_get_source_segment` | 複数行の連結で改行を落とす | KILLED | 単位 C-1 (実データ 353 件) |
| M-A4 | `_analyze_source` | helper を使わず `ast.get_source_segment` に戻す | KILLED | **単位 C-4 のみ。**C-1/C-2/C-3 は通る |
| M-A5 | `_analyze_source` | 分割を visitor ごと (`if` ごと) に行う | KILLED | **単位 C-4 のみ** |
| M-A6 | `visit_If` | fallback の `or ast.unparse(...)` を落とす | KILLED | 単位 C-3 |
| M-B1 | test `:378` | `_load_runtime(guard)` へ戻す | SURVIVED | 受理集合を変えないため。**性能回帰であって正しさ回帰ではない**と明記する |

M-A4 と M-A5 は「テストが緑でも修正が入っていない」形を殺す変異であり、
本 wave の中心である。両方 SURVIVED なら単位 C-4 は無効であり、fix を要求する。

M-B1 は `DW-M08` に従い kill でなく **diagnostic sensitivity pin** の別枠に置く。
受理集合を変えない変異を kill と数えてはならない。
