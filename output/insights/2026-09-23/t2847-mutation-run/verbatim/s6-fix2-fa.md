[V20 の patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-published-version-mismatch.patch:13) を修正しました。UPDATE ごとに `UINT32_MAX` から epoch を 1 ずつ減らして公開し、tid は `2^28` に固定します。C/W 行と `changed`・`committed` の条件は変更していません。`#if` site 数も **4 のまま**で、登録表や既存テストの期待値への変更は不要です。

`transaction.cc` の TID 生成は、読んだ版と worker の直前の版をそれぞれ進めて最大を取ります。`tuple.hh` の epoch は 32 bit、tid は 29 bit です。このため公開版同士は epoch で区別され、W4 の 1 thread 実行で高い epoch の公開版を読んだ後の C/W 版は tid が `2^28+1` 以上となり、公開版の tid `2^28` と重なりません。通常の小さい epoch の C/W 版も公開版と重なりません。29 bit の巻き戻りには高い版からさらに `2^28` 回の増分が必要で、事前登録された 1 秒の W4 では到達しない前提です。実走による確認は親側に残ります。

確認結果は以下のとおりです。

- `git -C external/ccbench apply --check`、`git diff --check` ともに rc=0。
- `unifdef` はありません。patch を一時ファイルに適用し、マクロ未定義側を抽出した結果、pin の `transaction.cc` と `diff -u` で一致しました。一時ファイルは削除済みです。
- 修正版の `g++ -fsyntax-only` は生成物 `config.h` が無く停止しました。build・実走は未実施です。
- 変更した所有 path はこの patch だけです。commit は作成していません。

## 総括

固定公開版の再利用を解消しました。静的な適用・未定義側の一致は確認済みで、構文確認と W4 実走は未確認です。