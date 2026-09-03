# 受入全走の律速を測り直した — 「長時間かかるテスト」の正体は 3 つの実行のさせ方だった

ユーザー依頼: 「受入全走の高速化。5 分に収まらないという破滅的な状況を打破する。
長時間を要するテストがあるはずだが、それが妥当か検査しろ。多分妥当じゃない。」

**答え: 妥当ではなかった。3 件見つかり、いずれも検査の中身が重いのではなく実行のさせ方の問題である。**
本 wave はそのうち 1 件 (事故的な二乗) を実装で閉じ、残る 2 件は測って裁定パッケージへ送った。

**本 wave は「受入全走 5 分以内」を達成しない。** 実装した 1 件は wall を動かさない。
達成には裁定 1 と裁定 2 の両方が要る (下記)。段 3 の 2 レンズが独立にこの点を親へ突きつけ、
親は達成条件を明示的に縮めた。

## 1. 事故的な二乗 — 実装で閉じた

`orchestrator/campaign/p3_b4_wiring_probe.py:750` (修正前) の `_FunctionCallVisitor.visit_If` が
`if` 文ごとに `ast.get_source_segment(self.source, node.test)` を呼んでいた。
CPython の同関数は毎回 module 全文を行分割し直すので、費用は 本文長 x if 個数 になる。

親が `cProfile` で割った内訳 (login node、45 module):

```
_load_static_modules() 全体   27.4 s
  ast.parse                    0.299 s   <- 本来の構文解析
  _splitlines_no_ff           46.15 s (tottime, profiler 有効時)
  builtins.len            243,665,193 回 / 10.4 s
```

**本来の構文解析は 0.3 秒で、残りはすべて行分割のやり直しだった。**

行分割を module あたり 1 回にした後の実測:

| 対象 | 修正前 | 修正後 |
|---|---:|---:|
| `_load_static_modules()` | 27.4 s | **0.89 s** |
| 製品 `main` と同じ順序の準備 | 29.5 s | **1.74 s** |
| test の準備 (2 回 load していた node) | 56.8 s | **1.74 s** |

台帳上この file は 903.6 秒 / 59 node で受入全体の最重量であり、その **99.3% (897.0 秒) が
22〜47 秒の 29 node に集中**していた。修正後、新テスト 4 本を足したうえで
file 全体が計算ノードで **63 passed / 9.28〜10.49 秒**で終わる。

### 副産物 — テストだけが製品と違う呼び方をしていた

`test_p3_b4_wiring_probe.py` の 2 箇所が `P._load_runtime(guard)` を静的 module 無しで呼び、
内部で `_load_static_modules()` が走った直後に test 自身がもう一度呼んでいた。
製品 `main` (`:1972-1973`) は 1 回で渡している。

台帳でこの 2 関数の node だけが 43〜47 秒帯、他の重量 node が 22〜23 秒帯であり、
**source 読解から予測した「2 回払っている node」と台帳の帯が独立に一致した。**

段 3 のレンズ A が、これは所要だけの問題ではないと指摘した。2 回目の load は比較を伴わないため
**意図的な二重検査ではなく、静的 graph と runtime code が別 snapshot になりうる。**
製品と同じ順序へ揃えたことで、所要と併せてこの潜在的な食い違いも消えた。

## 2. 読み手どうしの直列化 — 裁定 1 として送る

`orchestrator/tests/conftest.py:2001` が `REAL_REPO_RESOURCE_NODES` の 96 node すべてへ
一律に `pytest.mark.xdist_group("real-repo")` を付ける。`--dist loadgroup` では
同じ group は 1 worker に固定されるため、96 node が直列に走る。台帳合計 **303.7 秒 (5.06 分)**。
うち 207.1 秒が `test_codex_reasoning_ab.py` に集中する。

一方 `conftest.py:1152` は `{"read": fcntl.LOCK_SH, "write": fcntl.LOCK_EX}` であり、
`_real_repo_locks` / `_real_repo_file_lock` が `pytest_runtest_protocol` (`:2070`) で
node ごとに P/S lock を掛けている。**実行時の資源保護はすでに読み書き lock として実装済みで、
読み手は共有 lock である** (`fcntl.flock(fd, LOCK_SH | LOCK_NB)`)。

親が `REAL_REPO_ACCESS_BY_NODE` を集計した結果:

| parent | ccbench | node 数 | 台帳秒 |
|---|---|---:|---:|
| read | read | 52 | 221.6 |
| read | (なし) | 34 | 78.5 |
| (なし) | read | 6 | 3.6 |
| read | **write** | 3 | 0.0 |
| (なし) | **write** | 1 | 0.2 |

**書き手は 4 node で実質 0 秒、残り 92 node (303.7 秒) は読み取り専用である。**
鎖の最重量 10 node もすべて `parent='read'` で、最重量の 94.0 秒 node も純粋な読み手である。
読み手どうしは共有 lock で本来は並行に走れるのに、group 固定がそれを禁じている。

### なぜ本 wave で直さなかったか

**素朴な修正は跨ホストの競合を作る。**段 3 のレンズ B が指摘し、親が採用した。

`real-repo` group は 2 つの役割を兼ねている。内側の「1 worker への直列化」と、外側の
「同一 shard = 同一ホストへの affinity」である。`tools/acceptance_shards.py:74-84` の
`REAL_REPO_GROUP_CONFLICT_EDGES` は「別 shard は別ホストになりうるので local flock では
閉じられない」ために競合する group を同じ shard へ連結する契約である。

したがって「書き手 4 件だけを group に残す」と読み手が別ホストへ移りうる。そうなると
local の共有 lock は書き手との競合を閉じない。**速くするために防壁を外す形であり、
絶対規律 2 が禁じる変更である。**

さらに現行 grouping は
`test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
と `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
が意図的に検査している。直すには期待値を変える必要があり、`DW-S05-B` は実装子にこれを禁じている。

正しい設計は「全 96 node の shard affinity を保ったまま、xdist の worker grouping だけを
read/write で割る」であり、`ItemRecord`・component 構成・closure gate へ
`xdist_group` とは独立した affinity 属性を足すことになる。専用 wave が要る。

## 3. lock を握ったまま test 本体を走らせる fixture — 裁定 2 として送る

`orchestrator/tests/test_p3_b4_raw_record_producer.py:1174-1239` の `certified_evidence` は
共有 tmp に evidence を 1 度だけ作り file lock で worker 間を直列化するが、
**`yield` が `flock(LOCK_EX)` の内側にある**ため lock を test 本体の実行中ずっと保持する。
17 test (間接依存の閉包込みで厳密に 17 件) が完全に直列化され、台帳 **258.1 秒**。
各 test 本体は 6.8〜19.0 秒で、evidence の構築は cache 済みなので
**lock 区間は構築ではなく本体そのものである。**

repo には既に `conftest.py:1369` の session fixture `real_repo_fixture_lock` があり、
`_real_repo_fixture_lock_context(parent, ccbench)` として読み書きを宣言できる。
「最初だけ排他で seed を作って解放し、以後は確認済み reader を共有 lock、書き手だけ排他」にすれば
**どのテストの期待値も変えずに**直列を短くできる見込みがある。

親は最初「17 test 中 7 test が共有 evidence を書き換える」と数えたが、これは字句 heuristic による
**過大評価**だった。段 3 のレンズ B が現物で確認したところ、共有 path を触ると言えるのは
M17 と M18 の 2 件で、他は `tmp_path` 配下を書いている。

## 4. critical path モデル

配分は `tools/run_tests.py` の既定 `--dist loadgroup`。xdist_group マーカーの無い node は
worker へ個別に配られるので、**「file 単位の束縛」は worker については効かない**
(ただし file 全体は同一 component として同一 shard = 同一ホストに載る。レンズ B の訂正)。
wall を決めるのは直列化される鎖である。

走行外費用 78.2 秒 (前 wave 実測: 共通 56.3 + shard 固有 21.9) を足した下限:

| 筋書き | K=2 x 32 worker | K=3 x 32 worker |
|---|---:|---:|
| 現状 | 6.37 分 | 6.37 分 |
| 本 wave の実装だけ | **6.37 分 (不変)** | **6.37 分 (不変)** |
| + 鎖 X (real-repo 読み手を並行化) | 5.61 分 | 5.61 分 |
| + 鎖 X + 鎖 Y | **4.19 分** | **3.64 分** |

**現状の下限 381.9 秒に対し、前 wave の実測最遅 shard は 388.3 秒で誤差 1.6% で一致する。**
モデルの妥当性はこの一致で裏付く。

**これは下限の比較であって wall の決定因の証明ではない** (レンズ B の所見 4 を採用)。
allocator は台帳時間でなく component の node 数を weight にする
(`tools/acceptance_shards.py:343-355`) ため、実際の割付は偏る。台帳は scheduling hint であり
権威ある性能測定ではない (D104 決定 4)。

**本 wave の実装が wall を動かさない理由**は、`test_p3_b4_wiring_probe.py` が
real-repo group を 0 秒しか含まず、その 903.6 秒が worker へ完全に分散されるからである。
価値は約 850 worker-seconds/走 の削減 = 計算ノードの列の回転率であって、5 分の壁ではない。
ただし両鎖を解いた後は詰め下限を 186.8 → 173.5 秒 (K=2) へ下げるので、約 13 秒の価値が現れる。

## 5. 検出力 — 「緑だが直っていない」を殺せるか

段 3 のレンズ A が中心的な穴を突いた。**helper を直接呼ぶ等価性テストは、
`_analyze_source` が新 helper を使わず旧経路のままでも通る。二乗が残ったまま緑になる。**
親はこれを must-fix として採用し、単位 C を 4 本に割った。

さらに親が 45 module / `if` 3282 個を走査したところ:

| 故障型 | 実データでの到達 | 帰結 |
|---|---:|---|
| byte slice を文字 slice に取り違える | **0 件** | 全 module 比較では殺せない |
| form feed でも行分割する | **0 件** | 同上 |
| 複数行 `if.test` の連結を誤る | 353 件 | 実データで殺せる |

45 module 中 36 個が非 ASCII を含むのに、**`if` の `col_offset` より前に非 ASCII がある行は
1 つも無い。** 合成 fixture の境界テストは装飾ではなく、3 故障型のうち 2 つの唯一の検出経路である。

変異走 (固定 commit `ca8b14c61`、dispatch、6 変異 + baseline):

| ID | 内容 | 結果 | 殺した検査 |
|---|---|---|---|
| M-A1 | byte slice を文字 slice にする | KILLED | 境界 |
| M-A2 | form feed でも分割する | KILLED | 境界 |
| M-A3 | 複数行の連結で改行を落とす | KILLED | 全 module + 境界 |
| M-A4 | helper を使わず旧経路へ戻る | KILLED | 配線 + 分割回数 |
| M-A5 | 分割を `if` ごとに行う | KILLED | 分割回数 |
| M-A6 | `or ast.unparse(...)` の fallback を落とす | KILLED | 配線 |

**6/6 KILLED、SURVIVED 0、MISMATCH 0。** baseline は走行前後とも PASSED。
台帳は `mutation-ledger.json`、事前登録は `mutation-spec.json`。

## 6. 親の誤りと、レビューの誤り

### 親が段 3 で訂正されたもの (7 点)

- worker の既定上限は 48 でなく **32** (`tools/run_tests.py:65`)。shard の既定は 3 でなく **2**。
- 台帳は node duration であり CPU 計測ではない。「CPU 総量」と呼んだのは不正確。
- 「file 単位の束縛は効かない」は広すぎる。worker には効かないが shard/ホストには効く。
- 「17 test 中 7 test が共有 evidence を書く」は過大評価。現物で言えるのは 2 件。
- 「guard 文字列が変わると受理集合が変わる」は誤り。変わるのは `_proof_switchpoint` が選ぶ
  edge の証拠 JSON と digest だけで、受理集合・inventory・seal は不変。
- 「`_load_static_modules()` は純粋計算」は誤り。filesystem を読む。
- 「probe の出力 bytes を変えない」は字義どおりには不可能。時刻と自己 hash が入る。

### 親がレビューを反証したもの (1 点)

段 6 のレンズ D が「C-2 は無変異でも赤になる。splitter の最後で `source[start:]` を
無条件に追加せよ」と must-fix を出した。**親はこれを実測で反証し、不採用にした。**

- CPython 3.10 の `ast._splitlines_no_ff` は **終端空要素を作らない** (`if next_line:` のときだけ
  append する)。実測: `""` は `[]`、`"a\n"` は `["a\n"]`。
- C-2 の `assert_matches` は stdlib が例外を投げる入力では新 helper にも同じ例外型を要求する
  対称形であり、空 source も行数超過も両者とも `IndexError` になるので緑である。
  親が pytest 抜きで C-2 の全 25 ケースを再現し失敗 0 件を確認した。
- 段 6 のレンズ C も独立に小型 oracle を走らせ、同じ結論に達した。

**推奨に従っていれば stdlib との一致を壊し、guard 文字列と証拠 JSON を変えていた。**
段 3 のレンズ A も同じ「終端空要素」の誤りを書いており、**2 つのレンズが同じ誤った前提を
共有していた。** 独立性は完全ではない。

なお同じレンズ D が出したもう 1 件の must-fix (C-4 が splitter 出力の dataflow を pin していない)
は本物で、採用した。修正後の C-4 は `assert all(lines is split_results[0] for lines in segment_inputs)`
で同一性を要求する。

## 一次資料

- `measurements.md` — 親が取った実測値の逐語
- `mutation-spec.json` / `mutation-ledger.json` — 変異の事前登録と結果
- `verbatim/` — 段 2〜6 の子出力、親 brief、段 4 裁定、裁定パッケージ
