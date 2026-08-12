# 親の独立棚卸し (段 2 の子と突き合わせるための基準)

段 2 の子成果物を読む**前**に親が独立に導出した。子の結論と食い違ったら、双方を実測で再検査する。

## 収支 (実測)

| 層 | 現在 | 上限 | 余白 | 必要 | 不足 |
|---|---|---|---|---|---|
| L0 入口 | 9,500 | 9,500 | 0 | 178 | **178** |
| L1 | 10,624 | 10,625 | 1 | 58 | **57** |
| L1.5 | 9,564 | 9,566 | 2 | 184 | **182** |

追記候補の最短形と実測 bytes:

- [T-925](2) `DW-O01` へ「中断した子の部分成果物は素性を明記して保全し、次の子に監査させる。」= **100 bytes**
- [T-925](3) `DW-O01` へ「編集量の大きい fix 巡は `--max-model-calls` を見積もって上げる。」= **84 bytes**
- [T-916](c) `DW-S01` へ「分類文を置かず実アンカー表だけを渡す。」= **58 bytes**
- [T-934](a) 入口へ「裁定停止 wave の再開は、裁定が結論だけを変え変更面の骨格が同一であることを
  確認し、変更面の再検査を段 6 レビューへ寄せる。」= **178 bytes**

## 構造的事実 (実装から確定)

1. **節の retire は docs-only では済まない。** 節一覧は `tools/check_docs.py:560`
   `REQUIRED_REFERENCE_SECTIONS` の定数であり、入口の段 dispatch 表と
   `.agents/skills/dev-wave/` にも写しがある。節を消すと実装面 diff が出る (D95 → Codex author)。
   **節本文から義務文だけを削るのは docs-only** で登録簿に触れない。
2. **「機械検査があるから散文は不要」はほぼ成立しない。** dev-wave の散文の大半は
   「この機械検査を回せ」という起動指示であり、検査の実在は起動を強制しない。
   例: `tools/check_codex_output.py` は `## 総括` と 500 bytes 下限を強制するが、
   親がそれを実行することは強制されない。→ 判定 A (無条件削除可) は稀。
3. **機械権威 3 行**: `DW-O01` の model 行、`DW-S06-A` / `DW-S06-C` の `reasoning=` 行。
   加えて `tools/check_docs.py:293` `DEV_WAVE_DW_O01_DISPATCH_ROUTE_LITERAL` が
   `DW-O01` の起動 route 行 (「model は全段、effort は…caller 指定は不可。」まで) を**逐語 pin**、
   `DEV_WAVE_DW_O01_WAITER_CONSUMER_LITERAL` が待機行を逐語 pin。**いずれも編集不可。**
4. `DEV_WAVE_WAITER_DISCLAIMER_RE` は `DW-O01` / `DW-C00` の節内に
   「参考例・任意・手動投入・してよい・使わない・実行しない・必須ではない・省略可」の語があると赤にする。
   → **`DW-O01` への追記文にこれらの語を入れてはならない。** 上記追記案 2 件は抵触しない (確認済み)。

## 削除候補 (親の独立導出)

| # | 層 | 対象 | 空く bytes | 根拠 | 判定 |
|---|---|---|---|---|---|
| P-a | L1.5 | `DW-O01`「prompt 非空を先に検査し、」 | 34 | `tools/dev_wave_codex.py` が `--prompt-file は non-empty file が必要` で argparse 段階に fail-closed。親の事前検査は機械代替済み | A 削除可 |
| P-b | L1.5 | `DW-M05` の `pgrep -f` 段落 (ERE/literal・worktree path 一意化) | 201 | 生存判定の機構が pid-file へ移行済み。`DW-O01` が `--pid-file` を義務化し `tools/dev_wave_wait.py producer` は `--pid \| --pid-file` の排他必須群しか受けない。`tools/mutation_harness.py` に `pgrep` の使用なし (grep 実測 0 件)。**superseded mitigation** | A 削除可 |
| P-c | L0 | 入口「読み込み契約」の fail-closed 文 | 170 | `DW-STOP` 第 1 文と実質同内容。`DW-STOP` は段 dispatch 表で「wave 開始」の U 節につき無条件読了 | A 削除可 (二重管理) |
| P-d | L0 | 入口「凍結境界」の「規定の停止条件…を迂回しない。」 | 95 | `DW-STOP` 末文と実質同内容。同上 | A 削除可 (二重管理) |

いずれも `tools/check_docs.py` / `orchestrator/tests/test_check_docs.py` の literal pin に**掛からない** (grep 実測 0 件)。

## 収支の見通し (親案)

- L1.5: 空き 2 + 34 + 201 = **237** ≥ 必要 184 → 閉じる (余り 53)
- L0: 空き 0 + 170 + 95 = **265** ≥ 必要 178 → 閉じる (余り 87)
- L1: 空き 1 + **候補未発見** < 必要 58 → **閉じない**

→ **L1 が唯一の未解決**。[T-916](c) の `DW-S01` 配置には L1 の空きが 57 bytes 要る。
台帳裁定の但し書き「読み込み導線が合わなければ (a) を棚卸し wave 経由で再提示」は
導線 (どこで読むか) の話だが、実際に塞いでいるのは**予算**である。
段 2/3 の子に L1 の削除候補を探させ、無ければ [T-916] は裁定パッケージへ戻す。
