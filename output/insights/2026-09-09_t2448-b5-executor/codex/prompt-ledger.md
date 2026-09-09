単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger

**あなたの編集対象 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger` である。**

必読事項の射影 (読めなければ即停止):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger/tools/update_acceptance_duration_ledger.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger/orchestrator/tests/acceptance_duration_ledger.json

## 役割と経緯

軸 B5 の新規 test 54 node の所要時間を、受入所要台帳へ入れ直す。

本 wave は一度この 54 行を入れたが、main の取り込みで台帳が競合した。親は
**merge 内で両親と異なる台帳を書かないため、競合解決で main 側の内容をそのまま採った。**
その結果 54 行が落ちているので、merge の後に正本 producer で入れ直す。

## やること (これだけ)

親が現 tip で実走して作った JUnit から、正本 producer を 1 回だけ走らせる。

```
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger
python3 tools/update_acceptance_duration_ledger.py --add-only /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/junit-b5-v2.xml
```

この JUnit は現 tip の 54 node (executor 34 + parser 20) で、失敗 0 件である。

実行後に次を確かめて報告する。

1. 追加された nodeid の件数 (54 のはず) と、既存 entry が byte exact に保たれたこと。
2. `orchestrator/tests/acceptance_duration_ledger.json` の総 entry 数。
3. 追加された nodeid に `axis_b5_search_executor` と `axis_b5_search_parsers` 以外が無いこと。
4. `python3 tools/update_acceptance_duration_ledger.py --add-only --check <同じ JUnit>` が
   生成 bytes の一致を報告すること (この確認 command の rc をそのまま報告する)。

## 所有 path (これ以外を編集してはならない)

- `orchestrator/tests/acceptance_duration_ledger.json`

**手書きの秒数を書かない。`0.0` の placeholder を入れない。JSON を手で整形し直さない。**
producer の出力をそのまま使う。

**編集してはならないもの:** 他の全 file。**commit してはならない。**
git の状態を変える操作をしてはならない。外部 network を使ってはならない。
出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。

## 実行した command
## 検算
## 未実走・未実装
## 総括
