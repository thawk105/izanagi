静的検査のみで判定した。pytest、`check_docs`、変異 harness は実走していない。

## Real 所見（修正必要）

### R1 — M4 は新 pin だけでは殺されず、純増検出力の主張が成立しない

- 主張: M4 が契約値だけを `DW-CTX` へ変える変異なら、入口は `DW-C00` のままなので、既存の `test_real_repo_clean` も実 repo の契約不一致を検出する設計である。変更前 HEAD にも同テストは存在するため、「旧テストは検出不能」「新 pin だけが検出」は成立しない。
- 根拠: 段4は M4 を pin 単独 kill とする [s4-adjudication.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:85)。入口は [dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106)、契約比較は [check_docs.py:3895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3895)、既存実 repo test は [test_check_docs.py:6393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:6393)、新 pin の pair assertion は [test_check_docs.py:4790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4790)。
- 成果物影響: 変異台帳の `kill node` と「新テストの純増検出力」が偽になる。単一理由化するなら、契約と入口を同時に `DW-CTX` へ変える二層変異として再登録すれば、構造検査を通し新 pin だけを失敗候補にできる。
- 深刻度: must-fix

### R2 — M3 は三重に過剰決定される

- 主張: 契約 entry `24` の削除は、(1) 実 repo 整合検査、(2) 新 pin の key 集合 assertion、(3) `condition_waiter_deleted` の fixture 書換前 assertion、の三経路に当たる。(3) は checker の拒否ではなく「削除対象行が最初からない」という fixture 構築失敗なので、kill と数えられない。
- 根拠: M3 の事前登録は [s4-adjudication.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:84)。合成入口は契約から生成される [test_check_docs.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:476)。行がなければ書換 helper が先に失敗する [test_check_docs.py:4163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4163)。新 pin は key 欠落を拒否する [test_check_docs.py:4788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4788)。
- 成果物影響: 変異台帳で単一の受理集合変化へ kill 理由を帰属できない。M3 は削除するか、pin と fixture を変えず `| 24 |` を重複させて `rows=2` だけを拒否させる変異へ差し替えるべきである。
- 深刻度: must-fix

### R3 — M1/M2 の期待 kill node に `condition_waiter_deleted` を含めるのは誤り

- 主張: M1/M2 は実ファイルの入口だけを変えるが、guard test は実入口をコピーせず、契約から別の合成入口を生成して自分で `24` 行を削除する。このため M1/M2 が `condition_waiter_deleted` node を失敗させる依存経路はない。静的な失敗候補は既存 `test_real_repo_clean` の契約不一致である。
- 根拠: 誤った期待は [s4-adjudication.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s4-adjudication.md:82)。合成入口生成は [test_check_docs.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:476)、guard の削除操作は [test_check_docs.py:4328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4328)、実 repo test は [test_check_docs.py:6393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:6393)。
- 成果物影響: 変異台帳の期待 node 集合が実際の依存グラフと食い違う。M1 は `rows=0/missing DW-C00`、M2 は `missing DW-C00/extra DW-CTX` による `test_real_repo_clean` 単独へ訂正し、guard case は独立 positive control として扱うべきである。
- 深刻度: must-fix

### R4 — guard case の collection 登録自体に独立 pin がない

- 主張: 現差分では case は pytest と素の `_run()` の双方へ動的に追加され、固定総件数との衝突はない。一方、`_COMMAND_GUARD_CASES` からこの一項だけ消すと、期待件数表も collection も一緒に縮み、mutation 分岐と needle が未使用のまま無検査で通る。
- 根拠: case 登録は [test_check_docs.py:4596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4596)、期待件数は list から導出される [test_check_docs.py:4712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4712)、pytest collection は [test_check_docs.py:5169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5169)、独自 runner も同じ list を使う [test_check_docs.py:6578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:6578)。
- 成果物影響: checker の受理集合は不変だが、受入レポート／変異台帳から条件24の positive-control node が無言で消えうる。literal membership と `CASES == NEEDLES == EXPECTED_COUNTS` の key 集合を固定する meta assertion が必要。
- 深刻度: must-fix

## Real 判定（修正不要）

### R5 — 新 pin は指定された三変異に対して恒真ではない

- 主張: literal `expected` が独立 oracle なので自己整合の穴はない。真に `24` を `_OPERATION_NUMBERS` へ移せば新 pin の key 集合 assertion、丸ごと削除しても同 assertion、参照先を `DW-CTX` にすれば pair assertion が失敗候補になる。
- 根拠: operation key は契約から導出される [test_check_docs.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:163)が、期待集合は literal [test_check_docs.py:4778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4778)。移動／削除は [test_check_docs.py:4788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4788)、`DW-CTX` 化は [test_check_docs.py:4790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4790)。なお `_OPERATION_NUMBERS` に追加するだけで後段の明示 `24` を残した場合、新 pin は通るが operation 外延 pin [test_check_docs.py:4735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4735)が検出する設計。
- 成果物影響: `24` の key 分類または `24 → DW-C00` 参照を壊した契約は、受入レポートで正当化されない。
- 深刻度: nit（修正不要）

### R6 — `condition_waiter_deleted` は診断文字列だけの検査ではない

- 主張: 合成 baseline の rc=0 を確認した後、行削除後に rc=1 と違反件数1を要求し、最後に needle を確認する。したがって主たる検出は「欠落入力を受理から拒否へ変える fail-closed」であり、診断だけではない。ただし診断文だけを変えて最後の assertion のみを落とす変異は kill ではない。
- 根拠: baseline は [test_check_docs.py:5175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5175)、rc と件数は [test_check_docs.py:5179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5179)、needle は [test_check_docs.py:5185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:5185)。
- 成果物影響: 合成入力の受理集合から「条件24欠落」を除外する証拠になる。診断文の固定は別枠の diagnostic sensitivity。
- 深刻度: nit（修正不要）

### R7 — 入口追加行は parser 契約と既存表形式に一致する

- 主張: 行頭 `| 24 |`、3列、backtick path、backtick section ID のすべてが parser に一致する。追加後は07欠番の23行で、既存22行と同形式である。
- 根拠: 追加行は [dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:106)。parser は3列以上と backtick path を要求する [check_docs.py:3180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:3180)、path/section token 定義は [check_docs.py:1668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:1668)。
- 成果物影響: dispatch 受理集合へ `24 → docs/dev-wave/core.md:DW-C00` が意図どおり追加され、参照 path の取りこぼしはない。
- 深刻度: nit（修正不要）

## Speculative 所見

なし。

## 総括

- blocker: なし。
- must-fix: M1/M2 の kill node、M3 の過剰決定、M4 の純増主張、collection 登録 pin の4点。
- 現状の land は非推奨。変異表の erratum と collection pin を入れてから親が実走すべき。
- 本レビューは静的検査のみで、pytest・`check_docs`・変異 matrix の実結果は未確認。