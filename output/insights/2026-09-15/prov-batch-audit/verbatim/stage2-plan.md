## 設計

**`%s` / `%B` の取得だけを一括化する。判定・対象選択・trailer parser は変更しない。** 以下の行番号は現行ファイル基準。

### 1. 一括取得ヘルパを追加する

`tools/check_ai_provenance.py:1187` の `_git` 直後へ、`_batch_commit_messages(commits)` を追加する。

- 戻り値は `dict[str, _CommitMessage] | None`。
- `_CommitMessage(subject: str, message: str)` は `:1141` の `CommitAudit` 近傍へ frozen dataclass として追加。
- `None` は「既存の per-commit 取得を使う」。空 message と区別する。
- `_git` 自体の cwd・環境継承・text mode・例外文言は変更しない。

取得コマンド案：

```text
git log --no-walk=unsorted --stdin -z \
  --format=tformat:%H%x00%s%x0a%x00%B%x0a
```

stdin は、既存 `commits` から得た full OID の重複除去列。監査に渡す元の `commits` は変更しない。

- `HEAD` を再走査せず、**既に選択された commit 自身だけ**を取得する。
- `--stdin` で argv 長の制約を避ける。
- `%s` は Git に生成させる。
- `%s`・`%B` の後へ明示的に LF を置き、現在の各 `git show --format=…` の出力終端を再現する。
- subject フィールドだけ `.strip()`。message は加工せず保存する。
- `-z` と `tformat:` による最終 record の終端もテストで固定する。

**一括結果は全件検証できた場合だけ採用する。**

検証項目は、終端 NUL、フィールド数、OID の形式・一意性・要求集合との exact 一致。非 full OID の内部呼出し、取得失敗、decode 失敗、framing 不成立では、結果を全廃して `None` を返す。部分結果で監査しない。`KeyboardInterrupt` 等を握り潰す包括的 catch は設けない。

### 2. `_normal_commit_audit` の注入口

`tools/check_ai_provenance.py:1891`：

```python
commit_message: _CommitMessage | None = None
```

を keyword-only 引数として追加する。

`:1908–1909` は次の分岐へ変更する。

- `commit_message is None`：現行の `git show %s` → `.strip()`、`git show %B` をそのまま実行。
- 指定あり：格納済み subject / message を使う。
- `:1910` の label 生成以降は変更しない。

これは既存 `ancestry=:1896` と同型の依存注入である。ただし、取得と ancestry の独立性をテストできるよう、引数は別にする。

### 3. `_audit_history` の配線

`tools/check_ai_provenance.py:2096` の ancestry 構築後、`:2098` の `audit_one` 定義前で一括取得する。

- `ancestry is not None` の通常高速経路だけで一括取得。
- `ancestry is None` の逐次 oracle 経路では一括取得せず、既存の二つの `show` を使う。
- `:2104` 近傍で該当 `_CommitMessage` を渡す。
- 一括取得不成立なら全 worker へ `None` を渡す。
- 空集合の `:2079` 早期 return、`:2107` の並列度、`:2111` の `pool.map(..., commits)` を維持する。

`:1729` の対象選択、`:2112` 以降の correction・台帳照合・waiver、`:3134` 以降の HEAD 固定・出力・rc は変更しない。`:1590` の親取得も対象外。

### 4. `_ai_agent_values` は置換しない

`tools/check_ai_provenance.py:1276` を維持する。

主対象だけで親実測の **84.7%** を占める。一方、`%(trailers:only=true,unfold=true)` の mismatch 0 は、その実測履歴・設定での一致であり、受理言語全体の証明ではない。

現行 `--parse` の `--only-input` に直接対応する option が `%(trailers)` にない点、repo / global config、divider、継続行、設定による trailer 追加等の差を別途検証する必要がある。10.9% の追加削減のために本 wave の証明面を拡大しない。

`:1215` の隔離 parser と canonical env は完全に維持する。

### 5. 記憶量

10.4 MB の message 常駐は許容し、**本 wave では streaming にしない**。

ただし Python の文字列表現、subject、辞書、一括 stdout、分割中のコピーにより、peak は 10.4 MB より大きい。単純な実装でも数十 MB 級を見込み、親の受入実測で既存 ancestry を含む process / cgroup peak を確認する。解析後は一括 buffer への参照を残さない。

streaming は chunk 境界・decode・子プロセス終了・失敗時の再実行を複雑化するため、現時点では費用に見合わない。

## 等価性の論証

### 対象集合と順序

対象を決めるのは引き続き `tools/check_ai_provenance.py:1729`。一括取得の結果から対象を生成しない。

一括取得では重複を除去してよいが、監査は元の `commits` 列に対して実行する。したがって内部呼出しに重複・逆順・不連続集合があっても、監査回数と順序を維持できる。D908 の全史監査、D254 の land 関門を変更しない。

### 文字列

各 commit について次を直接比較する。

```text
batch.subject == _git("show", "-s", "--format=%s", oid).strip()
batch.message == _git("show", "-s", "--format=%B", oid)
```

明示 LF は**decode 前の Git 出力内**に置く。後から Python で `"\n"` を足す設計では、message が CR で終わる場合に text mode の CRLF 正規化と順序が異なるためである。

Git の encoding 処理を利用し、独自の UTF-8 強制・置換 decode・改行除去を追加しない。

### 区切り

`\x01` は使わない。**commit object に NUL が絶対に存在しないという前提にも依存しない。**

要求した相異なる commit が N 件なら、正常な出力は各 record が三つの NUL 終端フィールドからなり、計 `3N` 個の NUL を持つ。

- message / subject に追加 NUL が出力されればフィールド数が増え、全件を既存経路へ戻す。
- NUL が Git の pretty 出力で切り詰められる等の場合は、既存 `show` との同一性を malformed object の固定 fixture で確認する。
- Git が要求した全 OID を各一回出力すること、最終終端、欠落・重複検出を固定テストで守る。
- SOH は通常の本文文字として保持する。

### 失敗と公開出力

一括取得で発生した `git log ... failed` を新しい公開診断にすると不変条件に反する。取得失敗・decode 失敗・framing 不成立は既存取得へ戻し、`:2111` の入力順で既存の例外を発生させる。

これにより、後方 commit の先行取得失敗が前方 commit の parser 失敗を追い越さない。正常取得時は同一文字列を同一判定へ渡すので、`CommitAudit`、集約結果、stdout / stderr、rc が一致する。

外部からの config 変更や一過性 I/O 障害まで、異なる subprocess スケジュール間で無条件に再現する保証はできない。等価性の検証条件は、同じ object・設定・環境で固定する。

## 境界ケース

現物確認は HEAD `0600887d92538b3f34d894f9674d202d0a29a578` の到達 commit **10,443 件**について、raw commit object を読み取って行った。親の監査対象 10,074 件とは母集合が異なる。性能の再測定・テスト実行はしていない。

| ケース | 現物確認結果 | 設計・固定 fixture |
|---|---|---|
| 空 message | 0 件 | 空 body を保持。`None` と混同しない |
| 巨大 message | 最大 6,410 bytes、`c170bee925d0…`。1 MiB 以上は 0 件 | 固定 1 MiB message で切詰め・サイズ上限がないことを確認 |
| 非 UTF-8 message | raw message の UTF-8 decode 失敗 0 件 | 不正 bytes を含む fixture。既存が失敗する場合は例外文言・rc まで一致 |
| `encoding` header | 0 件 | header 付き legacy encoding、および `i18n.logOutputEncoding` の固定組合せで旧 `show` と比較 |
| merge の `%s` | merge 3,399 件。例 `2a4b5d682997…` の `%s` は `merge(main): land 直前に local main を取り込む` | merge を除外しない。複数行の先頭段落を持つ merge も合成 |
| root | 1 件、`6ad3d7aa546c8…` | 親のない commit も直接取得 |
| message 末尾 LF | LF 1 個が 10,441 件、2 個が 2 件。LF なしは 0 件 | LF 0 / 1 / 2 個と末尾 CR を合成。`%B` 出力を逐語比較 |
| 複数行の先頭段落 | 1 件、`a3168d8552d4…` | Git の `%s` を使う。body の先頭行や独自空白畳込みで代用しない |
| NUL / SOH / CR | 各 0 件 | NUL の fallback、SOH 保持、CR / CRLF 正規化を合成 |

## 等価性テスト

追加先は `orchestrator/tests/test_check_ai_provenance.py`。既存期待値は変更しない。

### 常設の受入テスト：固定履歴だけを追加

1. **取得単体の differential test — `:146` の fixture helper 近傍**
   - 上表を含む固定 16 commit 程度の履歴を生成。
   - 通常の `git commit` が正規化する入力は、テスト内で raw commit object を生成する。
   - 各フィールドを既存二本の `show` と比較する。
   - `:131` のテスト用 `_git` は戻り値全体を `.strip()` するため、message oracle には使わない。production `_git` または同じ text mode の `subprocess.run` を使う。

2. **履歴結果 — `:6869` 近傍**
   - `:5018` の固定 `_mixed_history` を利用。
   - 現行の逐次 oracle／bitset 1・2・16 workers 比較を維持。
   - 「bitset + 旧取得」と「bitset + 一括取得」の比較も追加し、ancestry 差と取得差を独立に検査。
   - `findings` だけでなく `corrected`、`waived`、`known_violations` も exact 比較。
   - authoritative 経路の取得比較では ancestry を残し、一括取得だけを無効化する。

3. **公開結果と失敗順 — `:3755`、`:5380`、`:7088` 近傍**
   - 固定合成履歴で rc 0 / 1 / 2 の stdout・stderr 全文を旧取得と比較。
   - log 失敗、欠落・重複・余分な NUL、decode 失敗を注入。
   - 前方 parser 失敗と後方取得失敗を共存させ、旧経路と同じ最初の例外を確認。

4. **配線・量 — `:6903`、`:7062` 近傍**
   - 空集合は一括取得も呼ばない。
   - 不連続集合、HEAD 外の root、逆順、重複を監査する。
   - 正常な bitset 経路は message 用 `log` が一回、`show %s/%B` がゼロ。
   - oracle は message 用 `log` がゼロ、二本の `show` を維持。
   - `%P` 等の scope 外の `show` は禁止しない。

件数・message サイズを固定し、追加テストは実 repo の `HEAD` 成長に追随させない。時間ではなく subprocess 呼出し数を常設の性能構造検査にする。

### 全史 10,074 件：本 wave 一回の移行受入証拠

**全史比較は省略せず、毎回走る pytest 項目には新設しない。**

親が測った HEAD・対象 SHA 列を固定し、変更前実装と変更後実装を同じ repository state・設定・worker 数で実行する。

比較するのは以下。

- 選択 SHA 列の exact 一致と 10,074 件という件数。
- 各 commit の subject / message、`CommitAudit`。
- `HistoryAudit` 全フィールド。
- CLI の stdout / stderr bytes と rc。

変更前側は現行の並列 bitset 経路を使い、全史を遅い ancestry oracle へ変更しない。変更前一走は親実測の 133.6 秒を要する前提とし、比較のために取得を共有して自己参照にしない。

この一回限りの差分ゼロ証拠と、固定合成履歴による常設受入を組み合わせる。新コマンドの時間は親の HEAD 走査 0.49 秒と同一とは断定せず、変更後一走で確認する。親実測の HEAD が特定できなければ、10,074 件での一致を達成済みとは報告しない。

## 変異事前登録候補

新規部分の注入点は、現行の挿入先行番号で指定する。

| # | 注入点 | 変異 | 期待 |
|---|---|---|---|
| 1 | `tools/check_ai_provenance.py:1187` 後の formatter | `%s` を body 先頭行へ置換 | **KILLED：出力差**。複数行 subject の label が不一致 |
| 2 | 同 parser | message を `.strip()` / `.rstrip()` | **KILLED：取得契約差**。末尾改行 fixture が不一致。受理差と混同しない |
| 3 | 同 formatter / parser | record 区切りを SOH へ変更 | **KILLED：受理集合・出力差**。本文 SOH fixture が破損 |
| 4 | 同 parser | NUL 数・OID 検証を省き部分結果を採用 | **KILLED：受理集合差**。欠落・偽 record を含む注入結果を受理 |
| 5 | `:2096` 後 | 一括結果の OID 列で監査対象を上書き | **KILLED：対象・順序差**。逆順・重複・HEAD 外 fixture |
| 6 | `:2107–2111` | `pool.map` を完了順収集へ変更 | **KILLED：出力・例外順差**。既存 `:6903`、`:7088` |
| 7 | `:1187` 後の fallback | log / decode の例外をそのまま公開 | **KILLED：rc 2 診断差**。旧 `show` の失敗文言との比較 |
| 8 | `:2096` 後 | 一括取得を常に無効化 | **構造 pin**。findings は同じでも message 用 subprocess 数が退行 |
| 9 | `:2096` 後 | ancestry oracle にも一括結果を渡す | **構造 pin**。oracle の二本の `show` 観測で検出 |

受理集合を変える変異、公開出力だけを変える変異、速度・独立性の構造 pin は別分類で記録する。

## 裁定パッケージ候補

- **将来の trailer 一括化**：`_ai_agent_values` を維持するか、ambient config を含む別の等価性証明を伴って置換するか。本 wave は維持を推奨。
- **記憶量の将来対応**：取得 buffer が実効メモリ予算を圧迫した時点で streaming を検討する。今回の 10.4 MB だけを理由に導入しない。
- **異常入力時の速度**：互換性優先の fallback は旧速度へ戻る。独自診断で早期拒否する案は stdout / stderr 不変条件に反するため、本 wave には入れない。

範囲限定・incremental・cache・受領証・関門 timeout 引上げは、本計画の成立に不要である。

## 総括

取得だけを一括化し、対象選択・判定・隔離 parser・出力順を維持する。  
最大の技術リスクは、Git pretty 出力の区切り・encoding・末尾改行を既存 `show` と取り違えることである。  
固定境界 fixture の文字列比較と、親の固定 10,074 件に対する旧新全史比較で潰す。  
常設テストは固定履歴に限定し、全史比較は本 wave の一回限りの移行受入証拠とする。  
ファイル変更・commit・テスト実行・性能再測定は行っていない。