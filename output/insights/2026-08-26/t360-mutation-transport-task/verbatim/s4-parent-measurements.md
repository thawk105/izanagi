# 段 4 のための親の追加実測 (2026-08-26 02:15 JST)

段 2 プランの主張を親が独立に裏取りした結果。段 4 の裁定はこれを一次資料とする。

## A. 実運用の変異呼び出しは fanout ではない (プランの推奨 (b) を支持)

稼働中 process の argv を実測した。**`mutation_fanout.py` を走らせている process は 1 本も無い。**
実在するのは次の 2 形だけである。

1. wrapper 経由 — `mutation_worktree.py --source-repo ... --runner-mode dispatch --detached -- python3 tools/run_tests.py <対象> -q -rf --force-dispatch`
   (実測: pid 3725177、dev-wave-t1721-a1-paired-reps)
2. **harness 直接** — `mutation_harness.py --repo ... --runner-mode dispatch --resume --detached -- python3 tools/run_tests.py --force-dispatch <対象> -rf`
   (実測: pid 3733595 = t1434、pid 3773165 = t1687)

**帰結 1:** fanout は D433 で「この機体では実行不能」と裁定済みであり、実際に誰も使っていない。
本 wave で fanout へ触れない。プランの実装順序 5 と fanout 系テストは scope 外へ出す。

**帰結 2 (プランへの反証):** プランは「mutation task の入口を wrapper に固定し、harness 直接起動を
許さない」(#1 の変更) と書くが、**harness 直接起動は現に実運用の主要形である** (3 本中 2 本)。
wrapper 固定は受理集合の縮小であり、現行の dev-wave 変異 matrix 経路を壊す。
段 4 でこの含意を明示的に裁定する。

## B. D131 #4 「canonical 全走 argv の固定」は現行運用と衝突する

実測した runner argv は**いずれも対象を絞った走行**である。

- `tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py orchestrator/tests/test_paper_story_a1_job_contract.py orchestrator/tests/test_p3_exploration_namespace.py -q -rf --force-dispatch`
- `tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_reasoning_ab.py -rf`
- `tools/run_tests.py --force-dispatch -n 0 orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py orchestrator/tests/test_calibration_freeze_authority_contract.py -q -rf`

プランの #4 は task 経路の runner tail を
`<同一 Python> tools/run_tests.py -rf -p no:cacheprovider` の exact 形だけに固定する。
**これを採ると、実在する変異 matrix の走行はどれ 1 つとして mutation task を通れない。**
fanout と同じく「実装したが誰も通れない」機構になる。D433 決定 3 が禁じた形
(「実データで 1 回通すまで完成と見なさない」) の再発である。

**「本走」の語義:** 実測の file 名は `mut-final` / `result-final2` / `probe2b` であり、
本走は「probe に対する最終走」の意味であって「全 suite 走」ではない。
D131 #4 の「全走」をプランのように exact full-suite と読むと語義がずれる。

**段 4 の論点:** #4 を「対象 file を tracked に限りつつ、selector (`-k` / `-m` / `::nodeid`) と
任意 plugin と `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` を拒否する」と読み、
tracked な test file 引数は許す形にするか。親の暫定はこちら。
exact full-suite 固定は採らない — 採れば成果物が誰にも使われず、D433 の再演になる。

## C. 変わらず確認できたこと

- D433 は実在し、fanout admission は `memory.peak` 不在で常に拒否される
  (`tools/mutation_fanout.py:401-418` の `_attest_measurement_cgroup` が `memory.peak` を必読)。
- 汎用 task の hook 迂回はプランの file:line どおり (段 3 レンズ B の結論と突き合わせる)。
