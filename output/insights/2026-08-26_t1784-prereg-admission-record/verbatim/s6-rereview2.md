## 総括

3 度目の欠陥はあります。§5 パーサに過剰受理 1 件、過剰拒否 1 件を確認しました。  
先頭 BOM で fence opener を見落とし、fence 内の §5 を受理できます。  
inline code、indented code、escape 内の `<!--` を comment と誤認し、正当な文書を拒否します。  
復元された 3 段の検査はすべて `closed` で、前段状態による過剰決定はありません。pytest は指示どおり再実走していません。

## パーサの所見

以下で `V` は `orchestrator/tests/test_p3_b4_admission_record.py:64-93` の `_section5_document()` が返す正常な bytes、`S = V[V.index(b"## 5."):]` とします。

### 1. 先頭 BOM で fence opener を見落とす

種別: **過剰受理**。同じ原因で、先頭が直接 §5 heading の文書には過剰拒否も発生します。

`document_blob.decode("utf-8")` は先頭 BOM を残したまま `splitlines()` へ渡します。そのため最初の行が `"\ufeff```markdown"` となり、fence の `fullmatch` に失敗します (`orchestrator/campaign/p3_b4_admission_record.py:539-545`, `:505-515`)。

実際に試した bytes:

```python
b"\xef\xbb\xbf```markdown\n" + V + b"\n```"
```

現実装は **受理**しました。CommonMark の入力処理では先頭 BOM が除去されるため、実際には `V` 全体が fence 内です。

逆方向も確認しました。

```python
b"\xef\xbb\xbf" + S
```

これは表示される正常な §5 ですが、現実装は heading を認識できず **拒否**しました。

成果物影響: 実際には描画されない §5 で admission を通し、certified 実走を開始できます。

修正案: `utf-8-sig` で decode するか、decode 直後に先頭の U+FEFF を 1 個だけ除去してから block 状態を解析する。

- 通る正例: `b"\xef\xbb\xbf" + S`
- 落ちる負例: `b"\xef\xbb\xbf```markdown\n" + V + b"\n```"`

### 2. code / escape 内の `<!--` を comment opener と誤認する

種別: **過剰拒否**。

comment opener は fence 外の全行に対して単純な `line.find("<!--")` で検索されています (`orchestrator/campaign/p3_b4_admission_record.py:516-526`)。inline code、4-space / tab indented code、backslash escape の区別がありません。

次のすべてを実際に試し、現実装が **拒否**することを確認しました。

```python
b"# Literal `<!--` token\n\n" + V
b"    <!--\n\n" + V
b"\t<!--\n\n" + V
b"\\<!-- literal\n\n" + V
```

いずれも `<!--` は CommonMark 上の HTML comment opener ではなく、後続の §5 は表示されます。

成果物影響: 説明文や code example に comment delimiter を含む正当な事前登録文書が admission を通りません。

修正案: fence、実 HTML comment、indented code、backtick run による code span、escape の順序を持つ状態機械にする。実 comment 中では `-->` を優先し、通常テキストでは code span・escape 内の `<!--` を無視する。

- 通る正例: 上記 4 入力
- 落ちる負例: `b"<!--\n" + V + b"\n-->"`

### 3. NFKC・label・sentinel

追加所見はありません。

- `_SECTION5_LABELS` は全 10 件が NFKC 後も不変かつ相互に一意でした。
- `driver` を全角互換文字にした label と正規 label の衝突は、正規化後の重複検査で拒否されました (`orchestrator/campaign/p3_b4_admission_record.py:578-585`)。
- 全角 `TBD` の UTF-8 bytes `b"\xef\xbc\xb4\xef\xbc\xa2\xef\xbc\xa4"` は NFKC 後に拒否されました。
- 独立した `N/A` と `status: TBD` は拒否されました。
- `TBD_1` と `1N/A` は受理されました。`_` と数字が `\w` なので、FIX2-C が指定した Unicode 語境界では sentinel が独立していないためです。指定された境界どおりの挙動なので欠陥とは判定しません。
- セル値 `b"T\xcc\x81BD"` は受理されましたが、NFKC 後も `TBD` と同一にならず、正規化順序による bypass ではありません。

## 復元された検査の判定

### 1. terminal だけ昇格

**closed**

on terminal の `evidence_class` だけを書き換えています (`orchestrator/tests/test_p3_b4_closed_critic.py:1786-1792`)。start bytes とその hash は未変更なので、唯一の不整合は `evidence_class` です。

assertion は `start and terminal receipt differ: evidence_class` を要求します (`:1793-1800`)。実装側の該当文言は `orchestrator/campaign/p3_b4_closed_critic.py:1410-1419` だけです。

### 2. on を整合昇格、off は test-only

**closed**

on start も昇格し、変更後 start bytes の hash を terminal に再設定しています (`orchestrator/tests/test_p3_b4_closed_critic.py:1802-1811`)。したがって第 1 段の start / terminal 不整合は解消済みです。

その後の assertion は `different evidence_class` を要求します (`:1812-1819`)。対応する腕間検査は `orchestrator/campaign/p3_b4_closed_critic.py:1598-1601` です。

### 3. 両腕を整合昇格

**closed**

off についても start、terminal、`start_receipt_sha256` を整合更新しています (`orchestrator/tests/test_p3_b4_closed_critic.py:1821-1836`)。

続く legacy gate が明示的に成功しており (`:1837-1840`)、前段 mutation や receipt 不整合が残っていないことを確認しています。その後 certified gate は `live production factory pair` で拒否されます (`:1841-1850`)。production seal 検査は admission path の読み取りより前です (`orchestrator/campaign/p3_b4_closed_critic.py:1659-1663`, `:1042-1047`)。

第 1 回再レビューで削除を指摘された前 2 段は、mutation の内容と拒否文言の双方が意味として復元されています。名前だけの復元ではありません。`_raises` は完全一致ではなく substring assertion ですが (`orchestrator/tests/test_p3_b4_closed_critic.py:95-101`)、各文字列に対応する実装分岐は一意です。

## 攻撃できなかった面

- backtick info に backtick を含む非 opener は受理され、通常の backtick / tilde fence 内の §5 は拒否されました。
- 短い内側 marker は外側 fence を閉じず、同種かつ十分な長さの marker だけが閉じました。
- 3-space indent の fence、閉じ marker の末尾 space / tab、CRLF は正しく処理されました。
- 4-space indent の見かけ上の fence は fence と誤認されませんでした。
- comment の同一行 close、close 無し、複数 comment、close 後の再 open は期待どおり追跡されました。
- fence 内の `<!--` は comment 状態を開始せず、comment 内の fence marker も fence 状態を開始しませんでした。
- NFKC 前後の sentinel 検査、正規化後 label 重複、固定 label 集合に bypass は見つかりませんでした。
- HTML comment 以外の raw HTML block は FIX2-D が保証対象外としているため、塞がれた面とは数えていません。