# [T-2153] 意味 witness を 8 macro へ広げた — 所有 TU 全体の枝選択で観測する

- 日付: 2026-09-02
- branch: `worktree-dev-wave-t2153-meaning-witness`
- 実装 commit: `a2bcd3aed47c57f781067f250c85ee2860fb7e59`
- 対象: `orchestrator/campaign/condition_meaning_gate.py` の実行側の意味 (runtime-meaning) の節

## 何が変わったか

意味 witness を持つ macro が **1 件から 9 件**になった (供給 domain は 22 件のまま)。
新たに green へ動いたのは、`cc/silo/transaction.cc` に単一の `#if <MACRO>` を 1 箇所だけ持つ
positive control 8 件である。

- `IZANAGI_BREAK_PERMUTATION`
- `IZANAGI_BREAK_PERMUTATION_SWAP`
- `IZANAGI_BREAK_LOCK_COVERAGE`
- `IZANAGI_BREAK_EARLY_UNLOCK`
- `IZANAGI_BREAK_WRITE_INTENT_ERASE`
- `IZANAGI_BREAK_WRITE_INTENT_FORGE`
- `IZANAGI_BREAK_WRITE_INTENT_OPSWAP`
- `IZANAGI_BREAK_WRITE_INTENT_PTRSWAP`

配線した driver は `s3_lock_coverage` / `s5_permutation_coverage` / `t152_write_intent_coverage`
の 3 面。これらの admission の `unestablished_meaning_macros` が単要素から空へ変わる。

## 主張の境界 (正直に書く)

この witness が確立するのは「**所有 TU において、その define の値が宣言した枝の選択を決めている**」
ことだけである。次は主張しない。

- 動的な到達性 (その枝が実行時に通るか)。
- 実行時の意味 (positive control が期待する異常が実際に発火するか)。
- 選択された枝の本文が意図どおりの内容であること (本文 bytes の期待値は焼いていない)。

## 動かせなかった 13 件と理由

| 型 | macro | 理由 |
|---|---|---|
| `#else` + 入れ子 | `IZANAGI_BREAK_NOREAD_VALIDATION`、`IZANAGI_BREAK_HIGHKEY_VALIDATION` | `#else` を持ち、その内側に `#if ADD_ANALYSIS` の入れ子がある |
| 別条件の内側 | `IZANAGI_BREAK_TRIGGER_MISATTR` | `#if BACKOFF_TRIGGER_GATING` の内側にあり、かつ `#ifdef` なので実 build の対は「定義する / しない」で、gate の要求 1 / 0 では枝が変わらない |
| 複数箇所 | `IZANAGI_SILO_LADDER_RUNG1`、`BACKOFF_REQUESTED_US`、`BACKOFF_TRIGGER_GATING` | 条件指令が 3〜12 箇所に散る。代表 1 箇所だけを green にすると macro 全体の意味を過大主張する |
| selector / template / 診断の混在 | `SS2PL_LOCK_IMPL`、`SS2PL_LOCK_KIND`、`SS2PL_DLR`、`SS2PL_WFG_DIAG` | 分岐の実体が CMake 側にもあり、単一枝 witness では意味を確立できない |
| driver 配線が編集面を超える | `SORT_VARIANT`、`BACKOFF_NOINLINE` | 枝は単一だが、成果物へ届く driver (`p3_s4_loop_sort` / `s6_sort_sweep` / `paper_story_a2_certification` / `t1683_rr5_cost_probe`) の配線が本 wave の編集面を大きく超える |
| 同伴 define の再注入 | `IZANAGI_SILO_LADDER_RUNG1_REPORT` | 同伴 define を gate 側が再注入するため、実 build に `IZANAGI_SILO_LADDER_RUNG1=1` が無くても green になりうる |

## 変異による裏取り

`mutation-spec-final.json` / `mutation-final-report.json` が正本。baseline 緑、**7/7 KILLED**。

| 変異 | 検出したテスト数 |
|---|---|
| 所有 TU 全体でなく断片を前処理する形へ戻す | 6 |
| 開始指令の一意性を「1 箇所以上」へ緩める | 1 |
| 観測の厳密な組 `(1,1)/(0,1)` を緩める | 1 |
| 完了 marker の観測要求を外す | 1 |
| 旧宣言型の macro 固定を集合所属へ戻す | 2 |
| registry 外の macro にも宣言を返す | 1 |
| 非識別検査と厳密な組の**両層**を同時に壊す | 5 |

**最後の 1 本は冗長 gate の顕在化である。** 非識別検査 (`要求値と既定値の観測が同じなら赤`) は
単独で壊しても隣の厳密な組の検査が代わりに赤を出すため、単独変異では「効いている」証拠に
ならない。両層を同時に壊して初めて
`test_compile_time_branch_selection_rejects_non_discriminating_observation` が発火した。
DW-M03 に従い、この検査は単独変異の証拠から外し、両層変異で裏を取った。

probe 段 (`mutation-spec-probe.json` / `-probe2.json` と対応する report) は全件 SURVIVED 期待で
登録し、観測 node を集めるために回した。本走はその node 集合との完全一致だけを KILLED としている。

## 段ごとの一次資料

`verbatim/` に段 2 のプラン、段 3 の 2 レンズ、段 4 の親裁定、段 5 の実装子報告、
段 6 の 2 レビューと fix の報告を逐語で置く。

段 3 と段 6 が独立に同じ穴を指摘した点 (対応 macro 集合の拡張が旧復号器の受理面も広げる) と、
段 6 のレビュー A が witness の不健全性を具体的な入力で示した点が、本 wave の実質的な成果である。
