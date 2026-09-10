## 総括

**land 前に 2 点の修正を推奨します。**

1. **real:** entry token が 3 個以上ある filename で中間 token が無視され、filename の虚偽主張を通せる。
2. **real:** 欠番を許す既存 `spool_fold` 入力をローテーションすると、新 checker が拒否する archive を生成しうる。

既存 caller のシグネチャ回帰、既存 fixture の意図しない `malformed` 化、新規 I/O は確認できませんでした。pytest は実走していません。実 checker は `rc=0` でした。

### 1. 既存 caller と受理挙動

**判定: refuted**

grep 実測:

- `_check_backlog_guard(`: **2 箇所**。定義 1、caller 1。戻り値を受けるのは `main()` だけ。
- `_validate_next_action_items(`: **3 箇所**。定義 1、caller 2。外部 caller なし。
- 完全な `WORKLOG_ENTRY_TITLE_RE` 利用: **3 箇所**。定義、既存 full-match、追加された `group("order")`。
- `check_docs` を import するテスト: **4 ファイル**。
  - `test_check_docs.py`
  - `test_check_ai_provenance.py`
  - `test_s8b_selector_output.py`
  - `test_s8c_preregistration_invariant.py`
- `check_docs.main()` の直接呼出し: **1 箇所**。
- `test_check_docs.py` の `_run_check` は定義込み 100 箇所、すなわち呼出し 99 箇所。

戻り値変更は唯一の caller が回収済みです。追加引数は既定値付きで、内部 2 caller だけが利用します。named group 化も正規表現の受理文字列を変えず、`.groups()` を利用する既存 consumer はありません。

成果物影響: **既存 caller の破壊は確認されず、受理集合へのシグネチャ由来の影響なし。**

証拠: `tools/check_docs.py:769`, `tools/check_docs.py:1240`, `tools/check_docs.py:1805`, `tools/check_docs.py:5293`, `orchestrator/tests/test_check_docs.py:39`, `orchestrator/tests/test_s8c_preregistration_invariant.py:274`

### 2. 合成 archive fixture の三値分類

**判定: refuted**

意図しない `malformed` 化はありません。唯一の `malformed` は専用の負例です。

`test_check_docs.py`:

| filename | 分類 |
|---|---|
| `worklog-a-late.md` | unnumbered |
| `worklog-a.md` | unnumbered |
| `worklog-aa-newer.md` | unnumbered |
| `worklog-archive-later.md` | unnumbered |
| `worklog-archive-structure-later.md` | unnumbered |
| `worklog-archive-structure-malformed.md` | unnumbered |
| `worklog-archive-unreadable.md` | unnumbered |
| `worklog-external-unapproved.md` | unnumbered |
| `worklog-first.md` | unnumbered |
| `worklog-h2-collision.md` | unnumbered |
| `worklog-new.md` | unnumbered |
| `worklog-phase1-2.md` | unnumbered |
| `worklog-phase3-0722-0724.md` | unnumbered |
| `worklog-phase3-0730.md` | unnumbered |
| `worklog-phase3-0730-1.md` | numbered `(1,1)` |
| `worklog-phase3-0730-10-12.md` | numbered `(10,12)` |
| `worklog-phase3-0730-10.md` | numbered `(10,10)` |
| `worklog-phase3-0730-1000.md` | numbered `(1000,1000)` |
| `worklog-phase3-0730-106-110-copy.md` | malformed、専用負例 |
| `worklog-phase4-0729-1000.md` | numbered `(1000,1000)` |
| `worklog-phase4-0730-1001-0731-1003.md` | numbered `(1001,1003)` |
| `worklog-rotation-new.md` | unnumbered |
| `worklog-rotation-prelude.md` | unnumbered |
| `worklog-second.md` | unnumbered |
| `worklog-synthetic-latest.md` | unnumbered |
| `worklog-synthetic.md` | unnumbered |
| `worklog-tab-scope-replay.md` | unnumbered |
| `worklog-z-early.md` | unnumbered |
| `worklog-z.md` | unnumbered |
| `worklog-zz-older.md` | unnumbered |

`test_spool_fold.py`:

| filename | 分類 |
|---|---|
| `worklog-global-chain.md` | unnumbered |
| `worklog-global-duplicate.md` | unnumbered |
| `worklog-global-four-digit.md` | unnumbered |
| `worklog-global-future.md` | unnumbered |
| `worklog-global-gap.md` | unnumbered |
| `worklog-global-max.md` | unnumbered |
| `worklog-global-missing-task.md` | unnumbered |
| `worklog-global-substantive.md` | unnumbered |
| `worklog-global.md` | unnumbered |
| `worklog-impossible-date.md` | unnumbered |
| `worklog-legacy-a.md` | unnumbered |
| `worklog-legacy-b.md` | unnumbered |
| `worklog-old.md` | unnumbered |
| `worklog-phase3-2099-1.md` | unnumbered。`2099` が MMDD でないため |
| `worklog-rotated.md` | unnumbered |

成果物影響: **既存 fixture が予期せず新 finding を得る経路は確認されず、専用負例だけが malformed。**

証拠: `orchestrator/tests/test_check_docs.py:343`, `orchestrator/tests/test_check_docs.py:9099`, `orchestrator/tests/test_check_docs.py:9258`, `orchestrator/tests/test_spool_fold.py:248`, `orchestrator/tests/test_spool_fold.py:2146`

### 3. コスト

#### 3.1 新規 I/O

**判定: refuted**

追加行には `glob`、`iterdir`、`read_text`、`open`、`stat`、`_safe_read_text` の新規呼出しがありません。既存 archive glob・本文読取・README 読取の結果を再利用しています。

成果物影響: **ディスク I/O 回数の純増なし。**

証拠: `tools/check_docs.py:1959`, `tools/check_docs.py:1987`, `tools/check_docs.py:5293`

#### 3.2 carry と entry の保持・走査

**判定: refuted**

実 corpus は carry **201,855 行**、distinct target **506 件**でした。

- carry は既存 `_validate_next_action_items` の item loop 内で抽出され、全文の追加 pass はない。
- 保持は `setdefault` により target ごとに最初の `_CarryReference` 1 件。
- entry universe は entry 番号と位置に比例する。
- archive 本文の再読はない。
- 追加走査は、抽出済み `archive_entries` に対する番号集合生成 1 回と、採番 archive の位置登録 1 回。

成果物影響: **20 万 carry の list 保持は発生せず、保持量は約 506 target と entry universe に限定。**

証拠: `tools/check_docs.py:1280`, `tools/check_docs.py:1999`, `tools/check_docs.py:2011`

#### 3.3 README の list 化

**判定: real**

README は **82,790 bytes、1,397 行、436 bullet**です。`_archive_readme_items()` は `splitlines()` の全リストに加え、全 logical item を別 list に保持します。checker 1 回につき 1 回だけで、archive ごとの反復ではありませんが、これは明確に archive 履歴数へ比例する新規保持です。

generator 化すれば current item だけの保持にできます。

成果物影響: **現状の絶対量は小さいが、「履歴比例の保持を作らない」という v2 不変条件には厳密には不適合。**

証拠: `tools/check_docs.py:1415`, `tools/check_docs.py:1450`

#### 3.4 実時間・RSS

**判定: 疑い**

同一 host・同一 corpus の 3 回測定:

- base `4eb39c08`: 中央値 **5.24 秒、87,840 KiB**
- 実装版: 中央値 **5.62 秒、96,996 KiB**
- 差: 約 **+7.3%**、約 **+9.2 MiB**

base は `git show` した source を動的実行しており完全同型 harness ではないため、性能回帰値の確定ではありません。ただし純増が無視できるという証拠にもなっていません。

成果物影響: **land 後の全 docs gate と直接 `main()` テストの所要時間・peak RSSが増える疑い。**

証拠: `tools/check_docs.py:1280`, `tools/check_docs.py:1415`, `tools/check_docs.py:1999`

### 4. 診断品質

**判定: refuted**

実 helper で確認した結果:

- 100 件連続: `101〜200`
- 100 件連続欠番: `101〜200`
- 逆転 `(200)〜(101)`: `欠番=範囲逆転, 範囲外=101〜200`

連続欠番は 1 範囲へ圧縮されます。逆転時も「範囲逆転」が明示され、label には filename の path、README の file:line が入ります。`範囲外` の併記は多少冗長ですが修正対象は判別できます。carry、番号なし H2、重複 entry も file:line を持ちます。

成果物影響: **実 corpus 規模でも欠番表示は可読で、修正対象を特定可能。**

証拠: `tools/check_docs.py:1334`, `tools/check_docs.py:1349`, `tools/check_docs.py:1366`, `tools/check_docs.py:1408`, `tools/check_docs.py:1461`

### 5. filename token 解釈

#### 5.1 entry token が 3 個以上

**判定: real**

`worklog-phase10-0730-10-999-12.md` は **numbered `(10,12)`** になります。中間の `999` は収集されても、最終的に先頭と末尾しか使われません。

したがって本文が 10〜12、README も 10〜12なら、filename に露出した `999` を無視して通過できます。中間 token が範囲外、逆順、誤記でも同様です。

成果物影響: **filename の虚偽 entry token を検査済みと誤認し、archive 台帳の主張不一致を受理する。**

証拠: `tools/check_docs.py:1304`, `tools/check_docs.py:1327`

#### 5.2 先頭ゼロだが MMDD でない token

**判定: refuted**

`worklog-phase10-0730-0999-1000.md` は malformed になります。`0999` は MMDD に一致せず、entry token も先頭ゼロ禁止なので期待どおり拒否されます。

ただし `0231` のような実在しない暦日は現在の正規表現上 MMDD と見なされ、`worklog-phase10-0730-0231-1000.md` は numbered `(1000,1000)` になります。これは裁定済み regex 自体の許容範囲なので、実装逸脱ではありません。

成果物影響: **非 MMDD の先頭ゼロ token は遮断済み。暦日実在性は別 scope。**

証拠: `tools/check_docs.py:785`, `tools/check_docs.py:1305`

#### 5.3 phase が 2 桁以上

**判定: refuted**

`worklog-phase12-0730-10-12.md` は numbered `(10,12)` になります。`phase[0-9]+` が正しく機能しています。

成果物影響: **Phase 10 以降でも分類漏れなし。**

証拠: `tools/check_docs.py:784`, `tools/check_docs.py:1299`

### 6. 将来の fold

#### 6.1 次回の通常ローテーション文法

**判定: refuted**

producer は次を生成します。

- 同日: `worklog-phase3-<MMDD>-<lo>.md` または `...-<lo>-<hi>.md`
- 日跨ぎ: `worklog-phase3-<MMDD>-<lo>-<MMDD>-<hi>.md`
- README: ``- `<name>` — worklog の YYYY-MM-DD (lo)〜YYYY-MM-DD (hi) 分``
- 継続注記は 2 空白 indent

すべて新 filename 文法と README logical-item 文法に適合します。現行 worklog の entry は `(581)`〜`(585)` の連続 5 件なので、現 corpus の次回 fold について内部欠番は生じません。

成果物影響: **現在の canonical corpusからの次回通常 fold は、新 checker に適合する。**

証拠: `tools/spool_fold.py:2153`, `tools/spool_fold.py:2162`, `tools/spool_fold.py:2215`, `tools/spool_fold.py:2218`

#### 6.2 欠番を含む既存受理入力との閉包性

**判定: real**

`spool_fold` の既存テストは global ordinal の欠番を許し、次番号を max+1 にすると固定しています。一方 `_rotation_name()` は移動 entry の先頭・末尾だけを filename と README に書きます。

したがって、例えば現行 entry `(1)` と `(5)` を同時に移動すると producer は `(1)〜(5)` を名乗りますが、checker は `(2)〜(4)` の欠番として拒否します。

成果物影響: **`spool_fold` が受理する canonical 入力の一部で、land は rollbackし、直接 CLI は適用後に赤い台帳を残しうる。**

証拠: `orchestrator/tests/test_spool_fold.py:499`, `tools/spool_fold.py:2153`, `tools/spool_fold.py:2215`, `tools/check_docs.py:1375`

### 結論

既存 fixture・caller の即時回帰は見つかりませんでした。ただし land 前に少なくとも次を閉じるべきです。

- filename の entry token を **1 個または 2 個に限定**し、3 個以上を malformed にする。
- README logical item を list で返さず iterator 化する。
- 欠番を許す `spool_fold` 契約と、連続範囲しか許さない archive 契約のどちらを正とするか裁定し、producer が checker の受理集合に閉じるようにする。

pytest は未実走です。`python3 tools/check_docs.py` のみ実走し、`check_docs: 違反なし`、rc=0 を確認しました。