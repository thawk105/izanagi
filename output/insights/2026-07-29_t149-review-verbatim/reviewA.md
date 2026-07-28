## 判定

must-fix 2件、should 3件。現状の「編集面ドリフトを封鎖」「期待 node 完全一致」は過大主張である。pytest は実行していない。

### [RA-1] must-fix — opened の positive control が片方向で、双条件の弱体化を見逃す

file: [test_s6_proposal_rounds.py:240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:240)、[s6_proposal_rounds.py:120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s6_proposal_rounds.py:120)

実装の

```python
if e["opened"] != (e["region"] in ebs):
```

を次の片方向検査へ壊しても、追加された2テストは両方緑のままになる。

```python
if e["opened"] and e["region"] not in ebs:
```

具体経路:

- 正常テストでは backoff/transaction は `opened=True` かつ EBS 内、util は `False`。したがって `[]`。
- positive control は util だけを `True` にし、EBS 外なので期待どおり util 1件だけを検出。
- しかし backoff/transaction が誤って `opened=False` でも検出しない。positive control が逆方向を一度も刺していない。

放置影響: freshness の受理集合に「designated source を `opened=False` とした射影」が加わり、その map が `build_payload()` から60本の凍結入力へ流れて proposer の参照・提案集合・最終レポートの適格率を変えうる。

### [RA-2] must-fix — SOURCE_REL の所属検査は、編集面内での軸取り違えを全通しする

file: [test_campaign.py:3024](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_campaign.py:3024)、[p3_s4_loop_sort.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/p3_s4_loop_sort.py:88)

T3 は3定数が EBS に「含まれる」ことしか見ていない。例えば単一変異:

```python
p3_s4_loop_sort.SOURCE_REL = "include/backoff.hh"
```

は緑のまま。backoff.hh も EBS 内だからである。

既存 sort テストも [test_p3_s4_loop_sort.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_p3_s4_loop_sort.py:59) で `_SRC_REL = S.SOURCE_REL` と追随し、同じ誤値の場所へ sort 用 fixture を作るため独立 golden にならない。一方、実 patch は [silo-sort-variant.patch:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/patches/silo-sort-variant.patch:30) の transaction.cc に marker を置く。driver は backoff.hh を読み、`silo-writeset-sort` marker 不在として malformed reject に落ちる。

放置影響: sort driver の certified 受理集合が全 reject に縮み、WAL は成功候補でなく `diff-quarantine/malformed` を記録し、選択・レポートが変わる。

### [RA-3] should — `_fake_silo_ls` は subprocess と実母集団を過剰に捨象している

file: [test_s6_proposal_rounds.py:206](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:206)、[s6_proposal_rounds.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s6_proposal_rounds.py:99)

- fake は `cmd` に文字列 `"ls-tree"` があることしか見ず、`-C`、SUBMODULE、`-r`、`--name-only`、`HEAD`、`cc/silo/`、`check=True` を全く検査しない。
- stdout も EBS の silo メンバと util.cc だけで、どちらも `.cc`。実凍結母集団に多数ある `cc/silo/include/*.hh` を含めない。
- したがって production の `or p.endswith(".hh")` を削除しても両テストは緑。実物では9個の `.hh` が再生成集合から消える。
- field 名 `"region"` / `"opened"` と bool 値自体は実物に合っており、ここは攻撃したが破れなかった。ただし現実装は `1 == True`、`0 == False` のため、schema が要求する boolean でなく整数でも freshness を通す。この型境界もテストされていない。

### [RA-4] should — V1/V5 の「期待外の既存テストなし」は証明されていない。V5 は静的に反証できる

file: [handoff-t149.md:108](/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/handoff-t149.md:108)、[mutation_harness.py:18](/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/mutation_harness.py:18)

harness は7 nodeだけを列挙して実行しているため、「期待 node 完全一致」はその閉じた集合内での自己一致にすぎない。

- V5: 既存 [test_p3_s4_loop.py:610](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_p3_s4_loop.py:610) は `sub/include` だけを作り、617行で `sub/L.SOURCE_REL` を開く。V5 の `cc/silo/util.cc` では親 directory がなく `FileNotFoundError`。よって「T3のみ」「既存テストは検出しない」は偽。
- V1: 例えば [test_campaign.py:3182](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_campaign.py:3182) の既存テストは、fake repoに追加された偽 EBS ファイルを作らない。3195行の `resolve()` → `assert_includes_match_head()` が当該ファイルを読めず赤になる。コンパイラ guard が skip されない受入環境では期待外赤になる。
- なお V1 の T1 は「関係式」より先に3013行の literal pin で停止し、関係式 assert 自体は実行されない。

### [RA-5] should — T4 は V1〜V5 のどの変異にも晒されていない

file: [test_s1_known_axes_freeze.py:248](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s1_known_axes_freeze.py:248)、[handoff-t149.md:108](/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/handoff-t149.md:108)

V1〜V5 は `SILO_CMAKE_REL` と `_PROTOCOL_CMAKE` のどちらも変えない。したがって matrix 5/5 KILLED は T4 の検出力について何も示さない。少なくとも片側を変える V6 が必要。

ただし静的には T4 自体は恒真ではない。`M.SILO_CMAKE_REL` は [s1_known_axes_freeze.py:541](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s1_known_axes_freeze.py:541) で実読取に使われ、`_PROTOCOL_CMAKE` は [source_digest.py:521](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/source_digest.py:521) から worktree/HEAD双方の define 読取へ流れる。この silo 関係そのものは攻撃したが破れなかった。

## V1〜V5 静的結論

| 変異 | 結論 |
|---|---|
| V1 | focused 期待 node は赤。ただし既存 source-digest テストにも期待外赤が出るため、完全一致主張は不可 |
| V2 | T1 + 既存 allowlist テスト。攻撃したが破れなかった |
| V3 | 新規 freshness 2 node が赤。親版既存テストは freshness を直接呼ばず、M08差分は成立 |
| V4 | 新規 freshness 2 node が赤。親版既存テストは freshness を直接呼ばず、M08差分は成立 |
| V5 | T3は赤だが既存 `test_drive_iteration_checkpoint_survives_across_calls` も赤。M08差分主張は不成立 |