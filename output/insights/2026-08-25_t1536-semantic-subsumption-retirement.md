# [T-1536] 意味的包含によるテスト退役 — 退役一覧と各件の実測根拠

2026-08-25。branch `worktree-dev-wave-t1536-semantic-subsumption`。
権威は 2026-08-23 /rulings 全件のユーザー裁定 (択 (a)、証拠水準を下げない) であり、
D693 と同型のユーザー直接指示である。RuleOps の候補 package 経路ではない。
手順の正本は本 wave が起票した decisions 項 (意味的包含による退役)。

## 退役した 2 件と退役先

| 退役 | 退役先 |
|---|---|
| `test_current_repository_c12_registry_reports_unwired_allocation_consumer` | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` |
| `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` | 同上 |

いずれも `orchestrator/tests/test_s8c_preregistration_predicates.py` 内。
退役 2 件は**変数名を除いて同型**で (一方は `c12`、他方は `result` へ束縛する)、
どちらも同じ module fixture の同じ `results` から C12 を引き、`status` と `reason_code` の
2 面だけを assert していた。名前が約束する registry 経路と allocation binding helper 経路を
本文は区別していない。構文木が完全一致しないため D692 の候補抽出 heuristic では拾えない組である。

## 最大の発見 — 退役先は候補を含意していなかった

**出発点だった「退役先が候補を包含する」という読みは、実測で偽と確定した。**

退役先は C01〜C12 の `(status, reason_code)` 対を dict 等価で固定しており、比較は `==` である。
一方、退役候補 2 件は `assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED` と
`is` で比較していた。`PredicateStatus` は `orchestrator/campaign/s8c_preregistration.py` で
`class PredicateStatus(str, enum.Enum)` と定義されているため、素の文字列
`"EVIDENCE_UNDEFINED"` は `==` を通り `is` を通らない。

この差は机上の話ではない。`_normalize_predicate_results` (同 file) は
`PredicateStatus(value.status)` で**変換可能性を検査するだけ**で、戻り値は元の値をそのまま返す。
worktree 内の直接評価で下流の挙動を測った結果が次である。

```
type(正常.status) = PredicateStatus   type(変異.status) = str
==  等価: True      is 同一: False
正常系 s8c_gate_report._status_counts -> {'SATISFIED': 0, ..., 'EVIDENCE_UNDEFINED': 1, ...}
変異系 s8c_gate_report._status_counts -> AttributeError: 'str' object has no attribute 'value'
```

**つまり退役候補 2 件は、gate レポートの生成を守る唯一の identity 検査だった。**
退役先はその面を持っていなかった。

C12 の status を読む consumer は `orchestrator/campaign/s8c_gate_report.py` (`_status_counts` と
report projection) と `orchestrator/campaign/s8c_preregistration.py` の素の CLI 出力である。
**`s8c_result_judge.py` は consumer ではない** — 同 file の `.status.value` は判定器内部の
別の型 (`_ConditionResult`) を読んでおり、`PredicateResult` を受け取らない。
段 6 レビュー A の指摘で訂正した。先行 commit の message はこの点を過大に主張している。

そこで退役の前に、この identity 検査を退役先へ移植した。記録上の正しい説明は
「元から意味的に包含されていた」ではなく、**「不足していた assert を退役先へ移植したうえで、
最終 suite の検出力が維持されることを削除前後の実測で確かめた」**である。

## negative control の設計

変異は 2 本とも `orchestrator/campaign/s8c_preregistration_evidence.py` の
`_evaluate_c12` 末尾 return を対象にする。

- anchor は直後の `def _c07_string_sequence(...)` 行まで含む multiline で、file 内 **1 箇所** (実測)。
  return 4 行だけの短い形は **10 箇所**あり使えない。
- 当該 return は `_evaluate_c12` の内部にしかなく、他 predicate は通らない。単一理由性が成立する。
- 到達性は観測値が示す。現行 snapshot の C12 は
  `(EVIDENCE_UNDEFINED, completion-proof-not-machine-checkable)` で、これはこの return
  だけが返す組である。手前の 2 つの return は `UNSATISFIED` を返す。
- **mask 層の不在。** `DW-M01` が問うのは「同じ入力を拒否して変異を覆い隠す層」の有無である。
  下流の gate report と CLI は snapshot テストの実行経路に無く、変異を覆い隠さない。
  壊れる consumer が実在することは mask ではなく影響の証拠である。

| ID | 変異 | 分類 |
|---|---|---|
| NC-S | `core.PredicateStatus.EVIDENCE_UNDEFINED` を `.value` (素の str) にする | **semantic kill** |
| NC-R | `ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE` を `ReasonCode.RESTART_GUARD_ABSENT` にする | diagnostic sensitivity pin |

NC-S は上の実測どおり gate レポート生成を fail-closed 方向へ倒すので `DW-M03` の kill 要件を満たす。
`DW-M03` が kill から除外しているのは「診断文字列だけの赤」であり、型契約を壊す本変異は該当しない。
NC-R は `is_satisfied` が `is SATISFIED` だけを見るので満足判定を変えず、別枠に置く。
**D692 (b)(c) の KILL 要件は NC-S 単独で満たしている。**

なお spec JSON の `expected_status: "KILLED"` は **harness の node 集合一致 label** であり、
`DW-M08` の semantic / diagnostic 分類とは別の軸である。JSON だけを読むと 2 変異とも
semantic kill と誤読しうるので、分類は本文書を正本とする。

## 実測 (すべて計算ノードへ dispatch)

### (a) collect-only ノード集合の差分

対象 2 file (`test_s8c_preregistration_predicates.py`、`test_real_repo_serialization.py`) の
実 node 数は **236 から 234** へ減った。before-only は退役 2 件ちょうど、after-only は 0 件。

- 生成物: `collect-before-c1.txt` / `collect-after.txt` (job dir)。
- **これらの file の 1 行目は node ID ではなく `IZANAGI_GROWTH_HOLD_V1` の受領証行**である。
  行数 (237 / 235) をそのまま node 数として引用してはならない。先行 commit の message は
  この 1 件過大な値を書いている (段 6 レビュー A の指摘で訂正)。

### (b)(c) 変異 matrix

| 版 | commit | 実行形 | baseline | NC-S | NC-R |
|---|---|---|---|---|---|
| wave base | `e40c47be` | `-n 0` | PASSED | KILLED {A,B} 一致 | KILLED {T,A,B} 一致 |
| identity 移植後 | `3404b721` | `-n 0` | PASSED | KILLED {T,A,B} 一致 | KILLED {T,A,B} 一致 |
| identity 移植後 | `3404b721` | loadgroup | PASSED | MISMATCH / 失敗 {T,A,B}@grp | MISMATCH / 失敗 {T,A,B}@grp |
| 退役後 | `3af5fe4e` | `-n 0` | PASSED | KILLED {T} 一致 | KILLED {T} 一致 |
| 退役後 | `3af5fe4e` | loadgroup | PASSED | MISMATCH / 失敗 {T}@grp | MISMATCH / 失敗 {T}@grp |
| 最終 tip | `8f55828d` | `-n 0` | PASSED | KILLED {T} 一致 | KILLED {T} 一致 |
| 最終 tip | `8f55828d` | loadgroup | PASSED | MISMATCH / 失敗 {T}@grp | MISMATCH / 失敗 {T}@grp |

T = 退役先、A・B = 退役候補。生成物は job dir の
`mutation-result-{base,c1,c2,final}-{serial,group}.json` と対応する `mutation-attempt-*.json`。

**wave base の行が (P1) 反証の実測である。** identity 移植前は NC-S が退役先を殺さない。
移植後は殺す。これが移植した assert の陽性対照であり、`DW-M08` が求める新旧両走に当たる。

### 実行形を 2 通り測った理由

対象 3 node は `xdist_group("s8c-predicate-snapshot")` を持つ。変異 harness は収集を `-n 0` で
行い実走を loadgroup で行うため、失敗 node に `@s8c-predicate-snapshot` が付いて完全一致しない
(F95 の再発、同型は F408)。正規化の設計は別 ID が所有しており、本 wave は harness を直していない。

- **run 1 (受入等価):** 既定の loadgroup。D692 項 6 が要求する「受入と同じ dispatch 環境」での
  失敗 node 集合を取る。harness label は MISMATCH のままで、**KILLED と読み替えていない。**
- **run 2 (機械照合):** runner へ `-n 0` を渡す。記録 node が bare になるので `DW-M08` の
  「同形式へ正規化した記録 node との完全一致」が構成によって成立し、harness が KILLED を機械判定する。
  `-n 0` は `tools/run_tests.py` の正規経路で (`_xdist_requested` が explicit `0` を見る)、
  `pytest.ini` に `addopts` は無く `-n` の注入元は runner だけである。迂回ではない。

**全 3 版で、2 走の失敗 node 集合は接尾辞を除いて完全一致した。**

## この結果が主張していないこと

- **環境非依存の同値性は主張しない。** D692 項 6 のとおり、保証するのは実測を行った環境
  (Pegasus 計算ノードへの dispatch、loadgroup と `-n 0` の 2 runner mode) における同値性だけである。
- **所要時間の短縮を退役の根拠にしていない** (D532、D692)。
  裁定文にあった「約 24 秒」は誤りで、実測は 0.01 秒未満だった (下記)。
- **重複実行による flake 検出の低下は正しさ契約に数えていない** (D692 項 5)。
- **退役先 docstring は安全の根拠に数えていない** (D692 項 4)。実行されず assert もされない。

## 裁定文の前提の訂正 — 「約 24 秒」は誤りだった

裁定文は退役で約 24 秒が消えるとしていたが、これは
`orchestrator/tests/acceptance_duration_ledger.json` の `32.0` という**日程並べ替え用の
placeholder 値**から導かれたもので実測ではない。

計算ノードで 5 node の焦点走を測ると (`--durations`)、0.005 秒以上として表示されたのは 2 件だけで、
どちらも退役対象ではなかった。

- `24.77s setup` — module scope fixture `current_commit_snapshot` の生成。5 node の共有であり、
  **退役後も残存 3 node が同じ fixture を使うので消えない。**
- `13.15s call` — `test_current_repository_snapshot_exactly_matches_head`。退役対象ではない。
- 退役候補 2 件と退役先を含む残り 13 durations はすべて 0.005 秒未満。走行全体は `5 passed in 41.40s`。

**この数値は当該 5 node を 1 回 loadgroup で走らせたその走行にしか適用できない。**
`-k` で候補だけを選ぶ走行、loadgroup 以外の xdist mode、全 suite では、fixture の生成回数や
collection・worker 間配送の所要が変わりうる。一般的な wall time 差として引用してはならない。

D532 と D692 は所要短縮を退役の根拠にすること自体を禁じているので、この訂正は裁定の論拠を崩さない。
裁定の論拠は「検出力を落とさずに減らせる形を 1 つ確立する」ことであり速度ではない。

## duration ledger を編集しなかった理由

`orchestrator/tests/acceptance_duration_ledger.json` の退役 2 node の entry はそのまま残した。

- validator (`conftest._validate_acceptance_duration_ledger_document`) は
  `nodeid_count == len(durations)` しか要求せず、未知 nodeid を拒否しない。
- reorder は live item 側から `durations.get(...)` で引くため、余った key は参照されない。
- coverage 検査も live collection を分母にするので、退役 2 node が分母から消えるだけである。
- 先例 `640d35f6` (2026-08-23 の退役 5 件) も同 ledger を触っておらず、
  退役済み 3 node の entry が現在も残ったまま suite は緑である。

## 親自身の誤りの記録

段 6 の敵対レビュー 2 本が、親の裁定と commit message から次を摘出した。いずれも採用した。

1. **「semantic kill を 1 件も主張しない」は過剰保守で誤りだった。** 段 3 の敵対レンズが
   1 回目と再投入で見解を割ったため保守側へ倒したが、`DW-M03` が除外するのは診断文字列だけの赤で、
   型契約を壊す NC-S は該当しない。上の実測で訂正した。
   親は D692 の KILL の読みについても自説 (実行可視性 probe という別概念) を取り下げ、
   レビューの読み (`DW-M03` と同一概念) を採用したうえで、NC-S が要件を満たすことを実測で示した。
   **争点は解釈ではなく事実だった。**
2. **collect の node 数を 1 件過大に書いた。** 受領証行を node と数えていた。正は 236 → 234。
3. **`s8c_result_judge` を C12 consumer と書いた。** 誤り。実際に壊れるのは gate レポートと素の CLI。

commit message は amend していない。最終 tip に束縛した変異証拠が壊れるためで、訂正は本文書と
worklog に残す。**先行 commit の message を読むときは本節の訂正を併せて読むこと。**
