## 検査項目 1〜7 の結果

1. **受理集合: NG。**
   計画の `rfind("@") > rfind("]")` は nodeid 全体へ適用されるため、group 接尾辞だけでなく path 内の `@` も削る。`_safe_relpath` は `@` を拒否せず、`_normalize_node` は path と test 部を結合して返すため、この入力は比較器へ到達する。`stage2-plan.md:101-107`、`tools/mutation_harness.py:490-498,1223-1238`。

2. **F71 の恒久対応: 問題なし。**

   - (a) dispatch の receipt に束縛された job stdout 全文を読み、その値を `_failed_nodes` へ渡す経路は変更対象外。`tools/mutation_harness.py:1501-1598,2184-2187`。既存の実体テストもある。`orchestrator/tests/test_mutation_harness.py:2739-2793`。fanout も relocated stdout と ledger の全文一致を確認する。`tools/mutation_fanout_contract.py:1369-1378`。
   - (b) ` - ` が無い場合に行末まで採る分岐を維持すると明記されている。`stage2-plan.md:93-95`、`tools/mutation_harness.py:1247-1255`、`tools/mutation_fanout_contract.py:303-314`。
   - (c) `rc != 0 and not failed` は key 化より先に `PARSE_ERROR` になる。`tools/mutation_harness.py:2000-2013`、`tools/mutation_fanout_contract.py:340-352`。計画も明記し、専用負例を置いている。`stage2-plan.md:93-96,159-161`。接尾辞除去は非空 list の各要素を変換するだけなので、抽出件数が新たに 0 になる経路はない。

3. **完全一致: NG。**
   path 内の `@` で異なるテストが同じ key へ潰れる。また fanout 側には正規化後重複の拒否が計画されていない。詳細は所見 1、2。

4. **`SURVIVED` / `TIMEOUT`: 問題なし。**
   harness は `KILLED` の非空、`SURVIVED` / `TIMEOUT` の空を key 化前に検査する。`tools/mutation_harness.py:593-605`。fanout も同じ契約を持つ。`tools/mutation_fanout_contract.py:474-489`。計画は両者を変更しない。`stage2-plan.md:91-97`。

5. **flaky hold: 計画した結果契約は妥当。**
   既存テストは base 表記だけなので単独では不足する。`orchestrator/tests/test_flaky_test_holds_contract.py:697-719`。計画は base、suffix 付き、無関係 node の三者を検査するため、suffix 付き期待によるすり抜けを検出できる。`stage2-plan.md:117-119,167-169`。ただし所見 1 の path 衝突を残すと、別 path を誤って hold 扱いする方向には集合が広がる。

6. **production 経路: 問題なし。**
   harness 正例は実 runner を通して `MH.main` から ledger の `KILLED` を検査する設計であり、接尾辞なし期待の正例が実際の `_observed_status` 比較を必要とする。`stage2-plan.md:135-145`、`orchestrator/tests/test_mutation_harness.py:306-358`。fanout 側も production の `merge_group` を呼ぶ。`orchestrator/tests/test_mutation_fanout_contract.py:418-430`。

7. **負例の向き: fanout 側が NG。**
   harness には strict superset/subset の既存負例がある。`orchestrator/tests/test_mutation_harness.py:860-886`。一方、fanout の追加予定は「期待 one、失敗 two」という互いに素な singleton だけで、完全一致を包含へ緩めても赤にならない。`stage2-plan.md:171-177`。

## 所見一覧 (BLOCKER / MAJOR / MINOR、file:line 付き)

1. **BLOCKER — 接尾辞規則が path 内の `@` まで test identity から消す。**
   `stage2-plan.md:101-107,121-127` は、正規化済み nodeid 全体について最後の `@` 以降を削る。path は `@` を許し、後段で再度 `<path>::<name>` 形式を検査しない。`tools/mutation_harness.py:490-498,1223-1238`。

   具体例:

   - 期待: `tests@left/test_gate.py::test_case`
   - 失敗: `tests@right/test_gate.py::test_case`

   両方とも planned key は `tests` になる。したがって、本来 `MISMATCH` である組が `failed_keys == expected_keys` を満たして `KILLED` になる。`tools/mutation_harness.py:2011-2013`。collection 事前検査も同じ誤一致を許す。`stage2-plan.md:105-107`。既存の path 負例は `a.py` 対 `b.py` だけで、この衝突を検出しない。`orchestrator/tests/test_mutation_harness.py:889-935`。

   **変異 matrix の偽結論:** 期待したテストとは別 path のテストしか落ちていないのに、「期待完全集合を検出した」として偽 `KILLED` になる。

2. **MAJOR — fanout verifier が正規化後重複を拒否しない。**
   harness については正規化後重複を拒否する計画がある。`stage2-plan.md:113-115,163-165`。一方、fanout の spec 検査は raw 文字列の重複しか見ず、計画の fanout 変更にも同等の検査がない。`tools/mutation_fanout_contract.py:481-489`、`stage2-plan.md:121-127`。

   具体例:

   - expected: `test_gate[one]` と `test_gate[one]@mutation-group`
   - failed: `test_gate[one]@mutation-group` の一件だけ

   raw expected は二件として通るが、計画した二集合は一 key に潰れ、fanout は `KILLED` を再導出する。

   **変異 matrix の偽結論:** harness なら不正登録として停止する曖昧な完全集合を、独立 verifier が「完全一致した KILLED」として受理する。

3. **MAJOR — fanout の負例が包含への弱体化を検出しない。**
   計画の負例は expected=`[one]`、failed=`[two]@group` である。`stage2-plan.md:173-177`。比較を `expected_keys <= failed_keys` へ緩めても、この二集合は包含関係にないため引き続き `MISMATCH` となり、テストは緑のままになる。現在の fanout テストにも strict superset 負例はなく、status 再導出テストは rc=0、失敗 0 件への改変しか検査しない。`orchestrator/tests/test_mutation_fanout_contract.py:635-665`。

   反例は expected=`[one]`、failed=`[one]@group`, `[two]@group`。完全一致なら `MISMATCH`、包含なら偽 `KILLED` になる。

   **変異 matrix の偽結論:** 余計なテストまで落ちた非局所変異を、fanout merge が期待どおりの kill と認定できる。

MINOR 所見はない。

## 親の provisional 裁定 (P1)〜(P5) への評価

- **P1: 棄却。** parametrize ID は守れるが、規則を nodeid 全体へ適用すると path 内の `@` を group と誤認する。`handoff.md:80-82`、`stage2-plan.md:101-107`。
- **P2: 現 repo の複数 group 到達不能という限定では採用。** marker 数と group 名の閉包は根拠がある。`handoff.md:279-290`。ただし P2 は P1 の path 衝突を解消しない。
- **P3: 採用。** 記録値を変えず、比較の座だけで同形化する分離は F71 と DW-M08 を保つ。`stage2-plan.md:19-25,101-107`。
- **P4: 親の初期裁定は棄却、段 2 の修正を採用。** `mutation_fanout_contract.py` は独立比較器を持つため同形修正が必要。`handoff.md:251-277`。
- **P5: 条件付き採用。** 初回、resume、fanout の両側を同じ比較意味論へ通す必要はある。`stage2-plan.md:57-71,181-187`。ただし採用する key は所見 1 の衝突を起こしてはならない。

## 問題を見つけられなかった箇所

- F71 の job stdout 全文、行末 node、抽出 0 件 `PARSE_ERROR` の三契約。
- `SURVIVED` / `TIMEOUT` / `KILLED` の expected-node 空非空契約。
- raw `failed_nodes` / `collected_nodes` / registration 表記を台帳へ保持する方針。
- 大文字小文字、class 階層、通常の path 差、parametrize ID 差を区別する既存負例。`orchestrator/tests/test_mutation_harness.py:889-935`。
- parametrize ID 内の `@` を保持する計画上の負例。`stage2-plan.md:155-157`。
- harness の接尾辞なし期待正例と、fanout の production merge 経路。
- flaky hold の suffix 付き期待によるすり抜けに対する計画上の policy 対。

## 総括

静的検査では **BLOCKER 1 件、MAJOR 2 件**。現プランのまま実装へ進めると、path 中の `@` により別テストを同一視して偽 `KILLED` を作れる。また fanout verifier では、正規化後重複と strict superset の二つが防壁に固定されない。

pytest は実行しておらず、緑の主張はしていない。