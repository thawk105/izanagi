新規 BLOCKER はありません。統合差分は裁定どおりで、裁定外の受理集合変更や既存テストの弱体化も見つかりませんでした。ただし、既知の残存所見と未完了の受入証拠が各 1 件あります。

### MAJOR — A2 の leading-dash symlink は未解決のまま

[tools/codex_reasoning_ab.py:1328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1328)

`Path.is_file()` は regular file を指す symlink にも真となり、1330 行はリンク先 bytes を hash します。段 4 で real・scope 外・実装しないと明示裁定済みなので、今回紛れ込んだ変更ではありませんが、所見自体は閉じていません。

**成果物影響:** custom `spec=` 経路では snapshot 外の可変 bytes を参照した oracle が valid となり、その snapshot に基づく certified 選択・レポート・台帳を成立させ得ます。

### MAJOR — B2 の replay consumer 検証はまだ閉じていない

[s4-adjudication.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s4-adjudication.md:39)

B2 は `test_codex_reasoning_ab.py` 全体走と受入全走で閉じる裁定ですが、提示済みの実測は新設 2 node の 2 passed のみです。コード上の回帰は見つかりませんが、段 6 の受入証拠としては未完了です。

**成果物影響:** 放置すると `aggregate` / `verify` replay の `valid`、終了コード、failure reference に潜む回帰を検出せず、レポート・台帳の受理結果を確定し得ます。

### 差分と受理集合

[tools/codex_reasoning_ab.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1330) は裁定どおり `"--"` を 1 個追加しただけです。通常名は親実測どおり同一 OIDで、先頭 `-` の literal path 化は A1/B1 の記録範囲内です。

差分は次だけでした。

- production: 1 行置換
- 新規テスト: 2 関数、36 行追加
- 既存 assertion・期待値の変更、反転、緩和、skip、xfail、削除: なし
- 裁定外の symlink／正規化／snapshot 内包 gate: 追加なし

### 追加テストの検出力

`"--"` を削除した `t904-drop-separator` では、登録済み 2 node はともに赤になります。

- [test_codex_reasoning_ab.py:1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1418): `-answer` が未知 option となり、最初の closure 呼び出しが rc=129 の `ValidationError` で赤になります。
- [test_codex_reasoning_ab.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1440): `--stdin` はファイルでなく stdin を hash します。登録された mutation harness は [tools/mutation_harness.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/mutation_harness.py:1387) で runner の stdin を `DEVNULL` に固定し、pytest の既定 FD capture も FD 0 を `/dev/null` に向けるため、Git は即 EOF、すなわち空 bytes を読みます。fixture の root object store に空 blob はなく、保存済みの非空 payload blobを検査しないため専用 reason が欠落して assertion failure になります。

したがって登録経路では hang せず、`hang_risk: false` は妥当です。Python の `sys.stdin` 用 pytest 擬似オブジェクトではなく、子 Git が継承する OS の FD 0 が効きます。

一方、mutation harness 外で `pytest -s` を対話 TTY から直接実行すれば Git が EOF 待ちで hang し得ます。その経路を正式採用するなら、runner の stdin を `DEVNULL` に固定するか、`hang_risk: true` として DW-M06 の個別 timeout に隔離すべきです。

fixture・並列実行・object store については、各 node が固有の `tmp_path` 内に root repo、child repo、submodule clone を作るためテスト間共有はありません。payload の root object store 共有は各テスト内で意図したものです。現在の環境に object-store を差し替える Git 環境変数もありません。

### 他分岐との相互作用

- `log --all -- relative`: 既に独立した `"--"` を持ち、変更なし。
- `cat-file -e`: 新たに literal path の正しい OIDを受け取るだけ。通常名は不変。
- filesystem allowlist: hash 検査後の集合比較で、変更なし。新しい例外や mask はありません。
- 段 3 の real 所見: A1・B1・B3 は実装／記録／事前登録で閉鎖。A2 は裁定済み scope 外として残存。B2 は全体走待ちです。

## 総括

新規の差分所見・BLOCKER・裁定外の受理集合変更はありません。  
追加 2 テストは separator 削除時にともに赤となり、正式 harness では stdin hang もしません。  
既存テストの反転・緩和・skip・削除はありません。  
未解決は既知 scope 外の A2 と、受入全走待ちの B2 です。  
Web 検索は使用していません。