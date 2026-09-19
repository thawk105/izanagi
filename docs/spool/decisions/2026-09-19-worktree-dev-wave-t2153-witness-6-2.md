---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: worktree-dev-wave-t2153-witness-6
seq: 2
---

## {{D:witness-registry-admission-by-real-tu}}. 枝選択 witness の登録簿は実 TU の実測で足し、複合行 1 本を macro の代表にせず、配線は admission が成果物へ載る driver だけに行う

**決定:** D1490 の compile-time 枝選択 witness を新しい macro へ広げるときは、(1) 実 patch を当てた所有 TU と
official と同形の依存供給 (env `CMAKE_PREFIX_PATH` + `FETCHCONTENT_BASE_DIR` + `FETCHCONTENT_SOURCE_DIR` 3 本) で
production の gate が supply green / meaning green (要求 (1,1)・既定 (0,1)) / admitted を返すことを実測してから登録簿へ
足す、(2) 所有 TU 内で一意な directive が macro 本来の意味を担う複数箇所のうちの 1 本 (複合条件行を含む) に過ぎない
場合は、機構上観測可能でも「代表 1 箇所で macro 全体の意味を過大主張する」ため足さない、(3) D1492 の配線は
admission が成果物 (JSON / receipt) へ載る driver だけに行い、返り値を捨てる driver や CLI 表示で終わる driver には
配線しない、とする。`SORT_VARIANT` と `IZANAGI_SILO_LADDER_RUNG1_REPORT` を足し (15 → 17)、`silo_ladder_rung1` だけを
配線した。`SS2PL_LOCK_IMPL` / `SS2PL_WFG_DIAG` (複合行 1 本、他 19 / 44 箇所は非一意) は観測可能だが足さず、
`SS2PL_DLR` (CMake の `DLR0`/`DLR1` marker が同時に変わり meaning arm も `compile-command-drift`) と
`SS2PL_LOCK_KIND` (所有 TU に directive なし) は既存機構では届かない。

**理由:**

- toy fixture の緑は実 TU の緑を含意しない。本 wave では toy fixture の所有 TU が `#if…#endif` だけで既定 0 の前処理
  出力が 0 byte になり supply が `preprocess-output-empty` で赤になった (fixture の代表性、F29 型)。実 TU + official
  同形供給での実測を登録の条件にすると、環境要因の偽赤で official の certified cell が拒否される経路を登録前に塞げる。
- 複合行 1 本の witness は「その行の枝選択」しか確立しないのに、consumer は `unestablished_meaning_macros` から
  macro 名が消えたことを macro 全体の意味確立と読む。entry 1195 が (c) 複数箇所を退けた理由と同じであり、
  複合行かどうかで区別できない (段 3 の敵対相談が指摘)。
- companion 付きの witness (REPORT) が主張できるのは「companion を含む compile argv の下での枝選択」までで、companion が
  実 build に在ることの保証は gate 単体に無く公開 driver 契約 (同時要求 + 実 compile argv 照合) にある。配線先を
  成果物へ載る driver に限ることで、この境界を成果物側で追跡できる。
- 探索 loop (`p3_s4_loop_sort` / `s6_sort_sweep`) は admission を永続化せず、capture に offline 供給引数も渡さない。
  配線すると meaning arm の導入が環境要因で探索の受理を変えうるため、配線と供給を同じ変更単位で扱う必要がある。

**却下した選択肢:**

- **複合行を代表として SS2PL 2 件も足す** — meaning arm は緑になるが、代表選択の過大主張であり、現行 patch は
  supply `dependency-closure-drift` で family が拒否のままなので成果物の未確立一覧も縮まない。
- **`owner_tus` を広げて LOCK_KIND を `wfg.cc` で観測する** — DefineSpec の意味変更で supply arm の対象 TU も動く。
- **探索 loop も 1 行で配線する** — 永続化されず、供給欠落の偽赤で探索を止めうる。別変更単位として起票する。
- **登録前に shadow 登録簿の結果を production 認証へ流用する** — D2141 のとおり shadow は機構診断であり、
  最終 production 登録簿での login / 計算ノード実走を完了条件にした。
