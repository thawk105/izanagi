---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2354-a5-prune-removal
seq: 2
---

## {{D:a5-cleanup-acceptance-split}}. A-5 cleanup の受理形は「静的な prune 不在」と「実 git 上の挙動」に分けて固定する

**決定:** A-5 job 本体の掃除について、契約テスト
(`orchestrator/tests/test_a5_second_boot_job_contract.py`) が静的に固定するのは
**実行可能な `worktree prune` が存在しないこと**だけとする。自 path の `worktree remove` が
実際に起きること、receipt の書式、remove 失敗時の rc 伝播と残置記録は、job 本体から
`remove_worktrees` と `cleanup_worktrees` を抽出して実 git repository 上で走らせる runtime test が
固定する。remove コマンドの逐語を `count(...) == 1` で pin する形は採らない。

**理由:**

- D1700 は「自 path の remove だけに限る」ことを求めており、`--` の追加や wrapper 化のような
  等価実装まで拒否する逐語 pin は、意図した 1 点 (prune 正例 → prune 不在) を超えて受理集合を
  狭める。
- 挙動側の検査は等価実装を許しつつ退行を捕まえる。実 git fixture は B-10 job 本体が既に
  採っている形 (`orchestrator/tests/test_backoff_extended_sweep.py` の
  `test_b10_job_exit_trap_removes_worktree_on_normal_and_abnormal_exit`) と同型である。
- 負例が実際に発火することを親が使い捨て repository で実測した。directory だけを消した兄弟登録は
  自 path の `remove --force` では残り、`prune --expire now` で消える。`worktree lock` した
  自 path への `remove --force` は rc=128 で失敗し、登録も directory も残る。

**限界:**

- 静的層は literal の `worktree prune` しか見ず、runtime 層は cleanup の 2 関数しか実行しない。
  その外側に置いた難読化 prune (例: `worktree "pr""une"`) は両層を通過する。変異として事前登録し、
  期待どおり SURVIVED することを実測した。
- ここへ bash token 解析の allowlist gate は足さない。D387 のとおり gate と検査を同じ主体が
  変更できる限り、repo 内の挙動検査は意図的な弱体化への完全な防壁にはならない。塞ぐべきは
  literal の再導入という退行であり、それは静的層が捕まえる。

**却下した選択肢:**

- remove の逐語 count を静的 pin にする — 等価実装を拒否し、受理集合を余分に狭める。
- 静的 pin を一切置かず runtime だけにする — literal の再導入が cleanup 関数の外に置かれた場合に
  何も残らない。安い側の防壁を捨てる理由がない。
