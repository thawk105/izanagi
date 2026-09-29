## 変更内容 (file ごと)

`R/ccbench` の [cc/mocc/transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/cc/mocc/transaction.cc:113)、[cc/silo/transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/cc/silo/transaction.cc:366)、[include/trace.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/include/trace.hh) に clang-format 14 を実行しました。前処理差分を調べるため、前二者に `#line` を追加しました。**R1 の byte 一致が成立せず、変更は未完成です。** script 4 本には着手していません。所有外への編集、commit、push はありません。

## 足した #line の一覧

| file・行 | 値 | 理由 |
|---|---:|---|
| mocc `transaction.cc:113` | 116 | 冒頭の `#if TRACE` 区間が整形で 3 行短くなったため |
| silo `transaction.cc:366` | 365 | `clear_shadow()` の TRACE 区間が 1 行長くなったため |
| silo `transaction.cc:384` | 381 | 次の `clear_shadow()` の TRACE 区間も 1 行長くなったため |

## 実走した command と rc

- `/usr/bin/clang-format --version`: rc=0、14.0.0。
- `/usr/bin/clang-format -i`、対象は上記 3 file: rc=0。
- `g++ -E -dD -nostdinc -x c++ -DTRACE=0` による、`#include` 行を除いた C2′ と作業ツリーの比較: コマンド自体は rc=0。plain と指定の analysis+locks の両文脈で、mocc・silo は **byte 不一致**、trace.hh は一致。
- `git status --short`: rc=0、変更は clone 内の上記 3 file のみ。

## 未実走・残る懸念

追加した `#line` 自身が前処理出力に行番号マーカーを発生させました。例えば mocc では、C2′ の `# 124 "<stdin>"` に対し、作業ツリーは `# 116 "<stdin>"` と `# 125 "<stdin>"` を出力します。silo でも C2′ の空行が `#line` 由来のマーカーに置き換わります。このため、指定された位置への `#line` 追加と、行番号マーカー込みの byte 一致を同時に満たせていません。

format の全対象 dry-run、検証器、job script、CI build は未実走・未実装です。計算ノード用 script も未実走です。

## 総括

R1 の完了条件が実測で成立しなかったため、「失敗したら推測で進めず止まれ」という指示に従い、ここで停止しました。作業ツリーには上記の未完成な 3 file の変更が残っています。