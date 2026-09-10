## 総括

**NO-GO。** §3.1〜§3.6 の主要防壁自体は静的には実装されているが、次の問題が残る。

- **実装上の受理集合拡大 1 件:** forged noop plan を `apply_fold()` が無検査で受理する。
- **契約を pin しないテスト 3 件:** recovery の `wave_ref`、commit diff 完全集合、transaction ID payload 全項目。
- **恒真に近い重複検査 1 件:** land recovery の `kind=="land"` 再検査。

pytest・build は実行していない。以下は差分の静的レビュー結果であり、緑とは報告しない。

### A6-SOL-01 — real / must-fix — forged noop plan を受理する

根拠: [tools/spool_fold.py:2932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2932)

`apply_fold()` は `plan.status == "noop"` だけで即 return し、transaction ID、closure、targets、fragments、gc_paths が空であることを検証しない。

再現入力:

```python
plan = spool_fold.plan_fold(repo_with_pending_fragment)
forged = dataclasses.replace(plan, status="noop")
result = spool_fold.apply_fold(repo, forged)
```

`result.status == "noop"` となり、state を書かず、canonical 更新も fragment GC もしない。新設テストは正規 noop のみを扱い、この負例を持たない。[test_spool_fold.py:2858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2858)

**成果物影響:** standalone/API consumer が pending fragment を fold 済み noop と誤認し、台帳への T/D/F 追記と receipt が欠落する。

### A6-SOL-02 — real / must-fix — recovery の `wave_ref` gate がテストされていない

実装は正しい位置にある: [tools/dev_wave_land.py:2372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2372)

しかし新設 recovery テストは正常 shape B、parent 不一致、standalone を扱うだけで、`kind="land"` かつ `origin.wave_ref != current wave_ref` の state がない。[test_dev_wave_land.py:3473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:3473)、[test_dev_wave_land.py:3532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:3532)、[test_dev_wave_land.py:3582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:3582)

再現する変異・状態:

- `origin.wave_ref != wave_ref` の拒否行だけを削除。
- transaction ID、closure、target/GC、fold commit identity は整合した land state を作る。
- `origin.wave_ref` だけを別の実在 branch ref にする。

後続の postcondition は現在の wave ref を request と比較するが、origin の ref とは比較しないため、この一行の削除を別層が確実には殺さない。

**成果物影響:** 別 wave ref を由来として記録した transaction/receipt を現 wave の fold として finalize し、台帳の provenance 参照が誤る。

### A6-SOL-03 — real / must-fix — commit identity 条件4を mode-only fixtureで代表させている

実装箇所: [tools/spool_fold.py:3104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:3104)

新設テストは mode `100755` の一形だけで拒否を確認する。[test_spool_fold.py:2069](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2069)

そのため、少なくとも以下の一行削除を個別には pin しない。

- actual path 集合と expected path 集合の完全一致
- target の `A` / `M` status
- new blob OID
- GC path の `D` status

再現する変異:

```text
if set(actual) != expected_paths: ...   を削除
```

または `new_oid != expected_oid` だけを削除する。mode-only fixture は引き続き `new_mode != "100644"` で落ちるため、削除した条件の検出力を証明しない。M07 の「diff 比較全体を消す」変異も、この過剰決定を解消しない。

**成果物影響:** identity gate の一部が将来脱落しても検査済みと記録され、state 外 path、誤 blob、誤 GC record を持つ fold commit の受理集合拡大を見逃す。

### A6-SOL-04 — real / must-fix — transaction ID payload の全項目が pin されていない

実装 payload: [tools/spool_fold.py:2173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2173)

対応テストは origin 全 field、closure、target の `before_exists` だけを変化させる。[test_spool_fold.py:1947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:1947)

具体例として次の一行を削除しても、同テストは `_plan_transaction_id()` の変更後結果を両辺で再計算するため静的には検出しない。

```python
"gc_paths": list(gc_paths),
```

同様に fragment 各 field、projected bytes、rotation path、target path/before/after SHA の独立変異がない。

**成果物影響:** payload field の束縛が脱落しても transaction ID 検査済みと報告され、異なる GC/target 宣言を同一 transaction と扱う回帰を certification が捕捉できない。

### A6-SOL-05 — real / nit — `origin.kind != "land"` の再検査は実 plan では恒真

根拠: [tools/dev_wave_land.py:2358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2358)

実 `load_active_plan()` は exact `FoldOrigin` を返し、kind は `land | standalone` の二択。直前で standalone を return 済みなので、続く

```python
if origin is None or origin.kind != "land":
```

は実 module では発火しない。fake module や壊れた interface に対する防御としてしか働かない。

**成果物影響:** なし。削除しても実 state の受理集合は変わらないため nit。

## 7 角度の確認結果

| 角度 | 静的結論 |
|---|---|
| §3.1 origin | exact 7 fields、Git HEAD/ref、base/rollback/cutoff commit、audited digest を確認。[spool_fold.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:375) |
| §3.2 closure | canonical、archive、fragment、両 engine、resume 正規化、HEAD/clean preflight がある。[spool_fold.py:2242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2242)、[spool_fold.py:2818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2818) |
| §3.3 state | exact top-level/nested schema、exact 型、ID 再計算、applied/committed を実装。[spool_fold.py:2492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2492)、[spool_fold.py:2598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2598) |
| §3.4 identity | parent、author、message、diff、既存 verifier の5条件は合成するとすべて有効。[spool_fold.py:3054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:3054) |
| §3.5 recovery | shape A/B、exact active ID、closure/complete shape、standalone 拒否を実装。[dev_wave_land.py:2358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2358) |
| §3.6 その他 | finalize は rollback try 外、GC/rollback fsync、dangling state、receipt cutover、`BaseException` を確認。[spool_fold.py:1143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1143)、[spool_fold.py:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:1559)、[spool_fold.py:2987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2987) |
| `check_docs.py` | flag 省略時の active 拒否、exact ID の伝播、dotted D 見出しへの統一はいずれも受理集合を意図どおり狭める。追加の fail-open は見つからない。[check_docs.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/check_docs.py:850)、[check_docs.py:4828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/check_docs.py:4828)、[check_docs.py:4866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/check_docs.py:4866) |