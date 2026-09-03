# handoff — dev-wave 受入全走の高速化 (事故的二乗の除去)

- wave branch: `worktree-dev-wave-acceptance-quadratic-ast`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast`
- job dir: `/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_acceptance-quadratic-ast`
- 起点 main: c7ed56589
- 種別: クラス 3 / 実装面あり / 軽量版 (段 2・3・5・6 を使う)

## ユーザー依頼 (逐語)

受入全走の高速化。５分に収まらないという破滅的な状況を打破する。長時間を要するテストが
あるはずだが、それが妥当か検査しろ。多分妥当じゃない。

## 段 1 で親が実測した事実

一次資料は親が login node 上で直接実行した計測 (pytest は hook が拒否するため素の python)。

1. 最重量 file は `orchestrator/tests/test_p3_b4_wiring_probe.py` (台帳 903.6 秒 / 59 node)。
   **その 99.3% (897.0 秒) が 29 node に集中し、全て 22〜47 秒である。**
2. その 22〜47 秒の中身は `p3_b4_wiring_probe._load_static_modules()` で、実測 27.4 秒。
   profiler の内訳: `ast.parse` は 45 module 合計 **0.299 秒**、`_splitlines_no_ff` が
   **46.15 秒 (tottime)**、`builtins.len` が **2 億 4366 万回 / 10.4 秒**。
3. 原因は `orchestrator/campaign/p3_b4_wiring_probe.py:750` の 1 行。
   `visit_If` が `if` ごと (3023 回) に `ast.get_source_segment(self.source, ...)` を呼び、
   CPython の同関数は毎回 **module 全文を行分割し直す**。費用は 本文長 x if 個数 の二乗。
4. 行分割を 1 度だけにして計測すると **27.4 秒 → 1.07 秒 (26 倍)**。
5. 加えて test の 2 箇所 (`test_p3_b4_wiring_probe.py:378`, `:937`) が
   `P._load_runtime(guard)` を静的 module 無しで呼ぶため内部で `_load_static_modules()` が
   走り、その直後に test 自身がもう一度呼ぶ。**同じ純粋計算を 2 回**している。
   製品側 `main` (:1972-1973) は 1 回で正しく渡している。**テストだけが製品と違う呼び方**。
   台帳の 43〜47 秒帯 (9+1 node) はちょうどこの 2 関数であり、独立に裏付いた。

## scope (確定)

- 単位 A: `p3_b4_wiring_probe.py:750` 周辺の二乗を除去する。**guard 文字列を 1 byte も変えない。**
- 単位 B: test の 2 箇所を製品と同じ `_load_runtime(guard, static)` へ揃える。
- 単位 C: A の等価性を pin する正例テスト (全 45 module の全 `if` で
  新経路 == `ast.get_source_segment` を要求する)。

## 不変条件

- (I1) 受理集合・拒否集合を変えない。probe の出力 bytes を変えない。
- (I2) `ast.unparse` への置換は**禁止**。実測で `p3_s4_loop.py` の 162 個中 36 個の `if` で
  文字列が変わる (`"x"` が `'x'` に、暗黙結合が `and (...)` に)。これは受理集合の変更である。
- (I3) 既存テストの期待値を変えない。node を減らして速くしない (絶対規律 2)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) `visit_If` の guard 文字列は `ast.get_source_segment` と完全一致でなければならない。
  → 下流 (inventory / seal / 出力 hash) が文字列に依存すると読んだ。段 3 で検証させる。
- (P2) この二乗は `p3_b4_wiring_probe.py` 固有で、他の重量 file の律速は別原因である。
  → `get_source_segment` の repo 内利用は本 file の 1 行 + test 2 file だけと実測したが、
  同型 (走査中に全体を再計算する) の別パターンは未探索。
- (P3) 単位 A だけでは 5 分問題は解決しない。最長単体 node
  (`test_role_sink_bytes_vary_only_at_declared_declassifications` 140 秒) が床として残る。
  本 wave はそれに触れない (worklog 1231 が素朴な parametrize を reward hack と裁定済み)。

## 成果物の形

コード (campaign 1 file) + テスト (1 file) + insight + worklog/decisions fragment。

## 既存被覆 (純増の確認)

- worklog 1231 が受入 5 分問題を分解済み。最長単体 node と collection を挙げたが、
  **`test_p3_b4_wiring_probe.py` の二乗には到達していない** (同 wave の上位 file 表に
  903.6 秒で載っているが、原因は未特定)。
- [T-1933] は `test_s8b_oracle_driver.py` 系に cache 共有と grouping で 2 度負けた。別対象・別手段。
- 本 wave は純増。

## 段 2 実行中に親が追加で実測した事実 (scope 判断に影響する)

配分は `tools/run_tests.py` の既定 `--dist loadgroup`。**xdist_group マーカーの無い node は
worker へ個別に配られる**ため、「file 単位の束縛」は一般には効かない (worklog 1231 の
表現は正確でない)。critical path を決めるのは直列化される鎖である。親の走査結果:

| 直列化の源 | 秒 | 実体 |
|---|---:|---|
| `test_p3_b4_raw_record_producer.py::certified_evidence` の排他 lock 鎖 | **258.1** | 17 test。worker 数に無関係 |
| 最長単体 node (`test_role_sink_bytes_...`) | 140.0 | worklog 1231 が「床」と判定 |
| 最大 xdist group (`p3-b4-material-report`) | 122.3 | 42 node |

`certified_evidence` (:1174-1239) は共有 tmp に evidence を 1 度だけ作り file lock で
worker 間を直列化する fixture だが、**`yield` が `flock(LOCK_EX)` の内側にある**ため
lock を test 本体の実行中ずっと保持する。17 test が完全に直列化され、台帳で 258.1 秒。

**lock 自体は必要である。** 17 test のうち 7 test が共有 evidence を実際に書き換える
(`write_bytes` 5、`publish_` 3、`rename`/`unlink` 1)。単純に外すと worker 間で壊れる。
妥当でないのは lock ではなく「高価な共有物を作って全員で奪い合う」設計である。
方向は「test ごとに複製を渡す」だが、receipt に絶対 path が焼かれていれば複製は移設不能になる。
**未検証。**

同型 (lock 保持のまま yield する fixture) は repo 全体で**この 1 件だけ**であり、
`DW-G03` の族一般化は成立しない。局所修復の型である。

**帰結 (親の provisional 裁定。段 4 で確定する):**
単位 A の 903.6 秒は xdist_group が無いので 48 worker へ分散されており、
**CPU 総量は 7.6% 減るが wall への効きは小さい。**5 分の壁を決めているのは 258.1 秒の lock 鎖である。
段 3 の両レンズに「親の scope 選択そのもの」を攻撃させ、段 4 で scope を確定する。

## 段 3 実行中に親が確定させた critical path モデル

`REAL_REPO_RESOURCE_NODES` の 96 node は `conftest.py:2001` が一律に
`xdist_group("real-repo")` を付けるため 1 worker に固定される。台帳での合計 **303.9 秒**。
一方 `conftest.py:1152` の `{"read": LOCK_SH, "write": LOCK_EX}` により、
実行時の資源保護は既に読み書き lock で行われている。access を割ると
**書き手は 4 node・0.2 秒だけで、残り 92 node (303.7 秒) は読み取り専用**である。
読み手どうしが共有 lock で並行できるはずのところを、group 固定が 1 worker へ押し込めている。

走行外費用 78.2 秒 (前 wave 実測: 共通 56.3 + shard 固有 21.9) を足した見積り:

**名前の規約 (レンズ A 所見 6 に従い衝突を解消):** 本 wave が実装する単位を A / B / C、
直列化の鎖を **鎖 X (real-repo group)** と **鎖 Y (certified_evidence lock)** と呼ぶ。

| 筋書き | critical path | 合計 | 分 |
|---|---:|---:|---:|
| 現状 | 303.7 | 381.9 | 6.37 |
| 単位 A/B/C だけ (二乗の除去) | 303.7 | 381.9 | **6.37 (不変)** |
| 鎖 X を解く (real-repo 読み手を並行化) | 258.1 | 336.3 | 5.61 |
| 単位 A/B/C + 鎖 X | 258.1 | 336.3 | 5.61 |
| 単位 A/B/C + 鎖 X + 鎖 Y | 140.0 | 218.2 | 3.64 |

**現状の予測 382.1 秒に対し前 wave の実測最遅 shard は 388.3 秒で、誤差 1.6% で一致する。**
モデルの妥当性はこの一致で裏付く (ただし台帳は hint であり実測ではない。D104 決定 4)。

**帰結: 単位 A/B/C は wall を動かさない。** `test_p3_b4_wiring_probe.py` の 903.6 秒は
real-repo group を 0 秒しか含まず、48 worker へ完全に分散されるためである。
A の価値は CPU 総量 7.6% 減 = queue 回転率であって、5 分の壁ではない。
**5 分に入れるには (B) と (C) の両方が要る。**

**(B) は既存テストの期待値を変える設計変更である。**
`test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
と `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
が現行の grouping を意図的に検査している。`DW-S05-B` は実装子に期待値変更を禁じており、
排他の緩和は絶対規律 2 の射程でもある。よって **本 wave では実装せず、
`DW-S04` に従い裁定パッケージとしてユーザーへ返す。**

**(C) は fixture の実装詳細**であり、どのテストの期待値も変えない。ただし単独では
(B) が残る限り wall は下がらない。実装順序は (B) が先である。

## 変異の到達性 (段 4 の事前登録の前提。親が実データで実測)

対象 45 module / `if` node 3282 個を走査した結果:

| 変異 | 内容 | 実データでの到達 | 帰結 |
|---|---|---:|---|
| M-A1 | byte slice を文字 slice に取り違える | **0 件** | 等価変異。合成 fixture が要る |
| M-A2 | form feed でも行分割する (`str.splitlines` 相当) | **0 件** | 等価変異。合成 fixture が要る |
| M-A3 | 複数行 `if.test` の連結を誤る | 353 件 | 実データで殺せる |

45 module 中 36 個が非 ASCII を含むが、**`if` の `col_offset` より前に非 ASCII がある行は 1 つも無い。**
したがって「全 45 module の全 `if` を `ast.get_source_segment` と比較する」テストだけでは
M-A1 と M-A2 を殺せない。段 2 プランが別立てで提案した合成 fixture の境界テスト
(multibyte が offset の前と範囲内、LF / CRLF / CR / form feed、`padded` 両値、location 欠落) は
**装飾ではなく、3 故障型のうち 2 つの唯一の検出経路である。** 段 4 で必須として登録する。

`DW-M03` に従い、M-A3 は全 module 比較テストが単一理由で殺す。M-A1 / M-A2 は境界テストが
単一理由で殺す。前後に同じ入力を拒否する層は無い (guard 文字列は `_build_inventory` /
`seal` を通らず `_proof_switchpoint` 経由で証拠 JSON へ出るだけ。段 2 が file:line で追跡済み)。

## (C) の refinement — 複製は要らないかもしれない (親の追加実測)

`certified_evidence` の 17 test を厳密に数え直した (間接 fixture 依存の閉包込み、258.1 秒で一致)。
各 test 本体は 6.8〜19.0 秒で、**evidence の構築は既に cache 済み**である。
つまり lock 区間は構築ではなく test 本体そのものであり、
「lock を構築だけに縮める」では解けない。

しかし repo には既に `conftest.py:1369` の session fixture `real_repo_fixture_lock` があり、
`_real_repo_fixture_lock_context(parent, ccbench)` として読み書きを宣言できる。
`certified_evidence` を「読み手は共有 lock、書き手だけ排他」へ割れば、
複製を作らずに直列を解ける見込みがある。

親の静的走査では 17 test 中 7 test が共有 evidence を書き換える
(`write_bytes` / `publish_` / `rename` / `unlink`)。その 7 件の合計は 105.2 秒、
読み取り専用の 10 件は 152.9 秒である。直列は 258.1 秒から 105.2 秒へ落ちる。
**この走査は字句 heuristic であり、read/write の判定は現物確認が要る (未確認)。**

なお critical path 上は、(B) を解いた後は最長単体 node 140.0 秒が支配するため、
(C) は 105.2 秒まで落とせば十分で、0 まで落とす必要はない。

## dev-wave 改善候補

(段 8 で一度だけ裁定する。実測のない仮想的懸念は書かない。)

- 候補 1: 段 1 の「重い対象の律速特定」に、台帳の値そのものでなく
  **profiler で内訳を割る**手順が無い。親は今回 `cProfile` で 1 回測って原因に到達したが、
  worklog 1231 の親は台帳の hint から構造的結論を出して 2 度誤った (同 worklog が自認)。
  → `DW-S01` か `DW-G01` へ「時間の帰属は hint でなく profiler の内訳で決める」を候補として記録。
  実測根拠: 本 wave は 1 回の profile で 26 倍の改善余地に到達した。
