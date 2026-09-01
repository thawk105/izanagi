# 段 6 裁定 (2 巡目) — 残る must-fix 1 件 (T-2115)

焦点再レビューが残した must-fix は 1 件。親が実測で再現を確認した。

## 親の実測

| 入力 | 結果 |
|---|---|
| 単純な dead `#if 0` の中のフック呼出し | False (1 巡目で閉じた) |
| **`#if 0` の中に別の `#if TRACE ... #endif` が入れ子であり、その後ろにフック呼出し** | **True (閉じていない)** |
| 実フック (正例) | True |

`#if 0` の除去が最初の `#endif` で終わるため、入れ子があると dead block の後半が残る。

## P-7 (must-fix)

`_protocol_source_has_trace_hook_evidence_only` の dead block 除去を**入れ子に対応させる**。

- 実装は**行単位の走査で `#if` 系の深さを数える**方式にする。`#if` / `#ifdef` / `#ifndef` で
  深さを増やし、`#endif` で減らす。`#if 0` で始まった深さに入っている間の行を捨てる。
- **一般のプリプロセッサ条件評価器を作らない。** literal `0` の `#if 0` だけを dead と扱う。
  `#elif` / `#else` の意味論も評価しない (dead block 内の `#else` 以降も dead 扱いのままでよい。
  そう扱う理由を 1 行コメントで書く)。
- docstring に、この検査が**プリプロセッサ条件を評価しないこと**、literal `#if 0` だけを
  dead として扱うことを明記する。既存の「証明しないこと」の列挙は残す。
- 負例 test を足す: `#if 0` の中に `#if TRACE ... #endif` が入れ子であり、その後ろに
  フック呼出しがある合成 source。
- **正例が壊れないことを必ず確かめる**: 実 submodule の silo が引き続き True であること、
  CMakeLists の SOURCES に載る file の実フックが True であること。

## 直さないこと

- 1 巡目の裁定 (`fix-ruling.md`) で「直さない」とした nit 3 件。
- 焦点レビューの所見 2 (output receipt と commit 状態の独立確認): **親が実測で解消済み**。
  fix 後の author worktree に untracked file は 0 件で、tracked 差分は許可された 16 file だけである。
  fix 子は何もしなくてよい。
- P-1〜P-6 は closed。触らない。
