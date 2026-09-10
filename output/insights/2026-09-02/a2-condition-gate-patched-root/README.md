# A-2 certification が condition 関門で止まっていた原因と、その 3 層

日付: 2026-09-02 / wave: `dev-wave-a2-condition-gate-patched-root`

## 要点

A-2 の driver は関門へ **patch を当てていない CCBench** を渡していた。関門は「patch が供給した
define が実際に効いたか」を見るものなので、素の木を渡せば必ず落ちる。直すと、その裏に隠れていた
関門がもう 2 層出てきた。1 層は直し、最後の 1 層は関門本体の性質なので裁定へ返した
(`ruling-package.md`)。

## 3 層

1. **patch 未適用 (直した).** 素の木に `CCBENCH_BACKOFF_FIXED` / `_NOINLINE` が無いため、cmake が
   "Manually-specified variables were not used by the project" を **stderr** へ書く。
   `condition_meaning_gate._run_process` は rc=0 でも stderr 非空を失敗にするので
   `configure-failed`。素の `include/backoff.hh` には materialized 枝も無いので
   `materialized-branch-invalid`。
2. **masstree の `config.h` 不在 (直した).** owner TU の include chain にある
   `masstree_wrapper.hh` が `<config.h>` を要求する。この file は CCBench の
   `cmake/ThirdParty.cmake` が **build 時の custom command** で生成するため、configure しか
   しない関門の build tree には無い。`buildcache.prepare_masstree_fetchcontent` を
   関門文脈で 1 度呼び、`-DFETCHCONTENT_BASE_DIR` を関門へ渡して解消した。
3. **inert 比較の root path 依存 (裁定へ).** `ruling-package.md` を見よ。

## 一般化できる教訓

**「関門だけを通す」修正は偽の緑を作りうる.** 当初の既定方針は「patch 由来の cache 変数を、
定義しない木へ渡さない」だった。それを採ると requested と control の configure が構成上同一になり、
inert 比較が自明に緑になる。さらに関門だけを patch 文脈へ入れると、関門は patch 済みの木を検査し
campaign は素の木を build するという乖離が生まれる。**検査した木と build する木を一致させる**
ことが、この族の修正の不変条件である。

**共有木を書き換える設計は fan-out した job で採れない.** A-2 は rr5 / rr50 の 2 job が
同じ CCBench root を共有し、別ノードで走る (`submit_paper_story_a2_certification.sh:177-199`、
job body は `--ccbench-dir "$ccbench_root"` をそのまま渡す)。`patchharness._tree_lock` は
`TMPDIR` 上の flock なのでノードを跨いで排他にならない。`patchharness.checkout` は
「呼び出しごとに一意 path なので他の並行評価と原理的に競合しない」と契約で保証しており、
そこへ patch を当てるのが正しい形である (先例: `s1_direct_comparison.py:815,910-913`、
`backoff_repro.py:63-84`)。

**義務化された関門は、driver ごとに実際に通したことがあるとは限らない.** 関門は T-1999 / D1198 で
driver 全体へ義務化されたが、A-2 経路では 1 層目で落ちていたため 2 層目以降が一度も実行されて
いなかった。層を 1 つ剥がすたびに次が出た。同じ形の未実行が他 driver にも残っている可能性がある
(`backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の inert 経路は未実測)。

## 実測の出所

- 失敗 1 回目: attempt `a2gate-20260902a`、`968836.nqsv` (rr5) / `968837.nqsv` (rr50)、
  Elapse 32 秒、`driver_rc=2`。
- 失敗 2 回目: attempt `a2gate-20260902b`、`968849.nqsv` / `968850.nqsv`、
  Elapse 32 秒、`driver_rc=2`。
- いずれも commit は本 wave branch の `ebd14f999` および `e9b91eb76`。

## 副産物

拒否メッセージが各 record の `evidence.detail` を保持するようになった。以前は
`macro:arm:reason_code` だけで、計算ノード側の実際の stderr が捨てられていたため、
原因の切り分けに login node での再現が必要だった。`detail` を持たない unestablished record は
`.get` で `None` になる (添字参照すると `CertificationError` が `KeyError` に化ける)。
