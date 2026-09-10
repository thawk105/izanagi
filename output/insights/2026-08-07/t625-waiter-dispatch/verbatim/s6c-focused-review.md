| 所見 ID | 判定 (closed / partial / regressed) | 根拠 (file:line) |
|---|---|---|
| R1 | closed（コード側対応不要） | M4 の二層変異化・期待 kill node は親の変異事前登録事項。[s4-adjudication.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:80)。literal pin 自体は維持されている。[test_check_docs.py:4787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4787) |
| R2 | closed（コード側対応不要） | M3 の削除・再照準は親の変異表訂正であり、テスト弱体化による単一理由化は不要。[s4-adjudication.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:84)、[s6-lensC.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s6-lensC.md:12) |
| R3 | closed（コード側対応不要） | M1/M2 の期待 node 訂正は親の事前登録事項。guard は引き続き契約生成の合成入口を使う独立 positive control である。[test_check_docs.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:476)、[s4-adjudication.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:82) |
| R4 | closed | `condition_waiter_deleted` の literal membership が case 消失を直接検出し、case/needle の key 不一致も検出する。[test_check_docs.py:4720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4720)。期待件数側の冗長性は下記 nit。 |
| R5 | closed（非回帰） | `24 → DW-C00` は派生値でなく literal exact-set で固定され、`DW-CTX` 化・余分な pair・欠落を拒否する。[test_check_docs.py:4787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4787) |
| R6 | closed（非回帰） | 行削除 mutation、baseline、rc=1、違反件数、needle の検査がすべて存続。[test_check_docs.py:4328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4328)、[test_check_docs.py:5172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5172) |
| R7 | closed（非回帰） | 条件行は3列・backtick path/section の parser 契約を維持。[dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106)、[check_docs.py:3180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3180) |
| D-1 | closed | 本依頼および fix 指示が3要素の正確な行を確定し、現物が一致する。[s6-fix-prompt.txt:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s6-fix-prompt.txt:25)、[dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106) |
| D-2 | closed | 新 pin は条件24だけを参照し、`15`/`21`/`22` や非-operation key 完全集合を固定していない。[test_check_docs.py:4787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4787)。既存の条件15 pin は今回以前から存在する。[test_check_docs.py:4761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4761) |
| D-3 | partial（段7記録待ち） | 現差分と fix 報告は構造検査の射程だけを述べ、過大主張していない。[s6-fix.md:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s6-fix.md:4)。ただし最終 worklog は未作成なので、段7で「key・行数・参照pairの検査」と限定する必要がある。 |
| D-4 | closed | 現物は指定された表形式に一致し、fix 報告も「逐語」ではなく「指定の3要素」と記録している。[s6-fix.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s6-fix.md:3) |

## 新規所見

N-1（nit）— `_COMMAND_GUARD_EXPECTED_COUNTS` の key 同値節は現定義では恒真である。

期待件数表は `_COMMAND_GUARD_CASES` から直接内包表記で生成され、後続処理は既存 key の値を上書きするだけである。[test_check_docs.py:4712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4712)

実効検出力を持つのは次の部分である。

- waiter case の消失：literal membership assertion。[test_check_docs.py:4724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4724)
- case と needle の片側登録漏れ：両 key 集合の比較。[test_check_docs.py:4725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4725)
- mutation 分岐の欠落と期待件数値の誤り：parametrized positive control。[test_check_docs.py:5172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5172)

`set(_COMMAND_GUARD_EXPECTED_COUNTS)` との比較は独立した第三の登録検査ではなく、現構造では冗長節と明記すべきである。成果物の受理集合・検出 node は変わらず、R4 の root cause は literal assertion が閉じているため nit とし、削除目的の追加 fix は求めない。

## 両方向・回帰確認

D-2 は狭めすぎてもいない。`24 → DW-CTX`、余分な pair、key 欠落は exact-set assertion が失敗し、operations path への配線は非所属 assertion が失敗する。`_OPERATION_NUMBERS` だけへ24を足して後段で上書きする変異は、既存の operations 外延 pin が受け持つ。[test_check_docs.py:4732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4732)

fix 前 snapshot と現差分の比較では、次がすべて存続している。

- 入口行：[dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106)
- 契約 entry：[check_docs.py:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:497)
- mutation 分岐：[test_check_docs.py:4328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4328)
- case list：[test_check_docs.py:4596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4596)
- needle：[test_check_docs.py:4667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4667)

snapshot から消えたのは、FIX-1 の「待ち条件作成」と FIX-2 の広すぎる非-operation完全集合 pinだけで、いずれも意図された変更である。その他の削除はない。

入口行は指定どおりである。

```text
| 24 | 背景 producer・待ち手の生成 / 再利用 / 停止、通知処理の直前 | `docs/dev-wave/core.md`: `DW-C00` |
```

独立再計数はファイル全体 9035 B、最長137文字（[dev-wave.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:63)）。予算9500 B／140文字に対し余裕465 B／3文字である。[check_docs.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:169)

## 総括

- **GO**（コード fix の再投不要、段7へ進行可）。
- R1〜R3の変異 erratum は親が本走前に反映するコード外作業である。
- D-3は段7の限定表現で閉じる必要があり、現時点の即時 land 許可ではない。
- 新規所見は恒真な期待件数 key 節という nit 1件のみで、検出力の回帰はない。
- pytest／`check_docs` は未実走で、親の307 passedも本静的判定の根拠にしていない。