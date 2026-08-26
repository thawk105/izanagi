pytest は未実走。射影 4 ファイルの静的検査と、Python の無書込 probe だけを行った。

## CRLF の新規拒否は brief の「それ以外は変えない」と両立しない

**区分**: 正しさ境界

**根拠**: brief は変更を対象 6 式と U+2028 / U+2029 の受理に限定する (`brief.md:3-4`) 一方、plan 自身が bytes 5 箇所で CRLF を新規拒否すると認めている (`s2-plan.md:8-12,43`)。旧 `bytes.splitlines()` は CR を除去するため parser に届かないが、新しい `split(b"\n")` は CR を残し、`_decode_jsonl` と `strict_json_loads` が拒否する (`events.py:193-194,291-292`)。これは却下済みの U+2028 / U+2029 拒否と同一ではないが、変異を KILL するため別入力の拒否を新設する構造になっている。

live stdout は Codex の stdout を無変換の binary file に直結する (`codex_worker_launch.py:1847-1854,1855-1870`)。rollout writer の改行契約は射影内になく、任意指定可能な sessions root から file を発見する (`codex_worker_launch.py:1290-1306,4513`)。`fcntl` と `/proc` 依存から native Windows 実行は考えにくい (`codex_worker_launch.py:12,1499-1508`) が、既存・移送済み CRLF file の流入は否定できない。実際の corpus は射影外なので発生頻度は未確認。

**これが real なら何が壊れるか**: 旧版で complete と封印された CRLF artifact は、resume 監査で evidence や recorded 値が変わり、receipt 再検証に失敗する (`codex_worker_launch.py:4090-4124,4340-4353,4402-4409`)。

**提案**:

1. `events.py:316` だけ直し、bytes 5 箇所を据え置く。実不具合だけを直し観測挙動を保つため、これを推す。
2. 6 箇所変更を維持するなら、LF 分割後の末尾 CR 正規化を追加して CRLF 耐性を保つ。
3. LF-only を新しい公開境界として採るなら、CRLF 拒否と旧 receipt 非互換を段 4 で明示的に再裁定する。現 plan のまま暗黙採用してはならない。

## 「bytes 5 経路は F609 ではない」という親の一般化は 2 経路で誤り

**区分**: 整合・実効性

**根拠**: `:1273` の直後は `parse_jsonl` を呼ぶ (`codex_worker_launch.py:1273-1283`)。`:4097` も同じである (`codex_worker_launch.py:4097-4105`)。`parse_jsonl` は bytes を str に decode してから (`events.py:170-181`)、問題の `str.splitlines()` を通る (`events.py:314-316`)。従って `:1273` と `:4097` の site 自体は bytes でも、end-to-end 経路は現在の F609 に到達する。

一方、`:1406`, `:2335`, `:4119` は bytes 分割後に 1 行だけ decode し、直接 `strict_json_loads` へ渡す (`codex_worker_launch.py:1406-1417,2334-2345,4119-4131`)。この 3 経路には下流の str 行分割がない。

**これが real なら何が壊れるか**: 親 brief の「bytes 側 5 箇所は F609 の経路ではない」 (`brief.md:14-17`) を前提にすると、テストの失敗帰属と防護層の説明が誤る。

**提案**:

- 「局所原因ではない」と「経路上で影響を受けない」を分ける。
- `:1273` と `:4097` は downstream affected、残る 3 箇所は unaffected と記録する。これを推す。

## 6 テストと 6 変異の一対一帰属は成立しない

**区分**: 整合・実効性

**根拠**: plan の fixture と実制御フロー (`s2-plan.md:30-35`) から、変異と赤になる予定テストの対応は次になる。

| 戻す site | 赤になる予定テスト |
|---|---|
| `events.py:316` | parse_jsonl、drain stdout、recompute stdout |
| worker `:1273` | drain stdout |
| worker `:1406` | tail rollout |
| worker `:2335` | recorded summary |
| worker `:4097` | recompute stdout |
| worker `:4119` | recompute rollout |

drain stdout と recompute stdout の U+2028 / U+2029 branch は、各 bytes site ではなく downstream の `events.py:316` に依存する。従って `test_drain_stdout_keeps_unicode_separators_and_rejects_crlf` と `test_recompute_metering_stdout_keeps_unicode_separators_and_rejects_crlf` は別 site の変異でも赤になる。残る bytes 3 テストの対象文字 branch は、対応 site を戻しても挙動が同じで恒真であり、CRLF branch だけが KILL している (`s2-plan.md:37-42`)。

**これが real なら何が壊れるか**: 「対応 test の赤」が対象 site の回帰を示さず、特に `events.py:316` の変異で 3 本同時に落ちる。変異事前登録の帰属説明が虚偽になる。

**提案**:

- U+2028 / U+2029 の end-to-end 受理テストと、各 bytes site の改行方針テストを別関数にする。
- 変異ごとに期待する赤 nodeid の集合を登録し、一対一とは主張しない。これを推す。
- 一対一を必須にするなら、bytes site 用テストから対象文字 branch を外し、ASCII の区切り入力だけで検査する。

## malformed JSON の新規通過はないが、stdout 経路の schema 閉包は証明されていない

**区分**: 正しさ境界

**根拠**: 全体 byte 上限と UTF-8/NUL/CR/NFC 検査は分割前に残る (`events.py:170-197`)。1 行上限、空行 skip、object 要求も残る (`events.py:314-331`)。`strict_json_loads` は重複 key、非有限数、BOM、NUL、CR、非 NFC、JSON parse failure を拒否する (`events.py:273-307`)。短い probe でも、`str.splitlines()` が追加分割する文字のうち raw JSON string 内で有効なのは U+0085、U+2028、U+2029 で、VT、FF、FS、GS、RS は JSON parse で拒否された。従って JSON として不正な入力を新規受理する穴は見つからない。

ただし完全な event schema 検証は `validate_event_stream` 側にある (`events.py:354-422`)。worker はそれを呼ばず、`parse_jsonl` 後の `_consume_stdout_event` が `thread.started` と `turn.completed` 以外を黙って無視する (`codex_worker_launch.py:1237-1258`)。従って plan の「schema まで閉じた」という一般化は成立しない。U+0085 と NEL は同じ文字なので、`s2-plan.md:7` の列挙も表現が不正確である。

**これが real なら何が壊れるか**: unknown stdout object を許容する設計でない場合、対象文字を含む unknown object が旧版では parse failure、新版では黙って無視され、evidence が complete になりうる。これは malformed JSON ではないが schema 境界の受理拡大である。

**提案**:

1. unknown stdout event の無視が仕様なら、その前提を明記し、本件に絶対規律 2 違反はないとする。
2. fail-closed が仕様なら別裁定パッケージにし、unknown event の扱いを直す。本件へ便乗実装しない。こちらは scope 外候補。

## CRLF 耐性を保っても bytes 5 変異は bare CR で KILL できる

**区分**: 整合・実効性

**根拠**: `split(b"\n")` 後に末尾 `b"\r"` だけを落とすと、CRLF 入力では旧 `splitlines()` と同じになるため、plan の CRLF branch は全て恒真になる。一方、2 個の正しい JSON object を bare CR だけで連結して最後を LF 終端にすれば、旧式は 2 行へ分けるが、新式は内部 CR を保持した 1 行とし、既存 parser が拒否する (`events.py:193-194,291-292`)。

**これが real なら何が壊れるか**: 「CRLF を保つと 5 変異を KILL 不能」という択一は偽。ただし CRLF と bare CR の両方を旧挙動どおり保つなら、5 変異は supported domain 上で等価になり、機能テストでは KILL 不能になる。

**提案**:

- CRLF は維持し bare CR 区切りだけ拒否する、と段 4 で裁定した上で bare CR fixture を使う。
- legacy の CRLF と bare CR を両方維持するなら、bytes 5 変異を事前登録から外す。
- 変異 score のために CRLF 拒否を採る案は推さない。

## 新規 test file と 6 変異登録の根拠が不足している

**区分**: 整合・実効性

**根拠**: 新規 file の理由は別 wave との編集衝突回避だけである (`brief.md:52-56`)。さらに plan は `test_codex_role_runtime.py` を「射影された参照」とするが (`s2-plan.md:67-70`)、今回の射影には含まれておらず、その harness や既存 fixture は検証不能だった。P4 の 6 変異中 5 本は対象文字の欠陥ではなく、未裁定の CRLF/bare CR 方針を検査する (`brief.md:58-60`, `s2-plan.md:39-43`)。

**これが real なら何が壊れるか**: 一時的な merge 回避が恒久的な test 配置となり、対象不具合と無関係な改行拒否が mutation contract として固定される。

**提案**:

1. 現時点では実欠陥の `events.py:316` 変異だけ登録する。これを推す。
2. bytes 方針が再裁定された場合だけ、対応する 5 変異を別契約として追加する。
3. test file の恒久配置は自然な既存 test file を読める段で再判定する。これは scope 外の裁定パッケージ候補。

## 総括

- 最重所見 1: bytes 5 変更は CRLF を新規拒否し、brief の限定 scope と衝突する。
- 最重所見 2: `:1273` と `:4097` は downstream で `events.py:316` を通るため、親の F609 経路一般化は誤り。
- 最重所見 3: 6 テスト対 6 変異の一対一帰属は成立せず、5 bytes 変異は未裁定の改行方針しか検査しない。
- 段 4 の第一択一は「実欠陥 1 箇所だけ直す」対「6 箇所を変え CRLF を正規化する」対「CRLF 拒否を明示承認する」。
- 推奨は実欠陥 1 箇所だけの変更。6 箇所を維持するなら CRLF 正規化を次善とする。
- unknown stdout event の許否と test file の恒久配置は、本件へ便乗せず別裁定候補にする。