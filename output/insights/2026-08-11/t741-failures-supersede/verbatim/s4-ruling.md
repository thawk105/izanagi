# 段 4 裁定 — dev-wave-t741-failures-supersede

段 2 プラン (`s2-plan.md`) と段 3 敵対 2 本 (`s3-lens-a.md` = 正しさ境界、`s3-lens-b.md` =
整合・実効性) を親が real/refuted・採否・scope 内外に裁定した結果。これが plan v2 の正本である。

## A. 所見の裁定

| # | 出所 | 判定 | 採否 | 理由 |
|---|---|---|---|---|
| A1 | lens-a 1 | **real** | **採用** | supersede 本文が `### Fnn.` になり canonical の F heading を偽造できる。採番・参照・監査対象集合が壊れる |
| A2 | lens-a 2 | **real** | **採用** | 実 canonical の境界 3 形 (次見出しの直前に空行なし / 空行あり / 最終 F の EOF) がテストされない |
| A3 | lens-a 3 | **real** | **採用** | 同一 fold で `再発` と supersede が同一 resolved line を出す場合の扱いが未裁定 |
| A4 | lens-a 4 | **real** | **scope 外** | `tools/dev_wave_land.py` の rollback 失敗時にも resume state を消す既存欠陥。別 tool・別族 |
| B1 | lens-b 1 | **real** | **採用 (記述訂正)** | 「表現できない」は誤り。`再発` payload は任意文字列なので**書けるが再発として誤記録される** |
| B2 | lens-b 2 | **real** | **採用** | 新節を足しても `再発` 経由で shape・重複検査を迂回できる。迂回できる gate は恒真に近い |
| B3 | lens-b 3 | **real** | **採用** | `docs/failures.md` の運用規則に再発と supersede の使い分けが無い |
| B4 | lens-b 4 | **real** | **採用** | 本文が opaque だと `- F196 stale` も通り、supersede と識別できない行が canonical に入る |
| B5 | lens-b 5 | **real** | **部分採用** | check_docs 経路と CLI dry-run 経路は採用。land lock 内 fold は既存 helper で無理なく書ける場合のみ |
| B6 | lens-b 6 | **real** | **採用** | 実 canonical (F196/F197 境界) の byte-exact 正例を入れる |
| B7 | lens-b 7 | **real** | **採用 (記述訂正)** | 親 brief 実測 4 の grep 説明が不正確 |
| B8 | lens-b 8 | **疑い** | **採用 (記述弱化)** | 「再訪を起票する」は断定できない。「F196 単体参照では誤読し得る」へ弱める |

### 親の記述訂正 (一次資料で再確認済み)

1. **実測 4 の訂正。** `grep -rln "spool_fold\|spool/README\|spool/failures/README" --include=*.py`
   の hit は 2 ファイルではなく **6 ファイル** (`tools/spool_fold.py`, `tools/check_docs.py`,
   `tools/dev_wave_land.py`, `orchestrator/tests/test_spool_fold.py`,
   `orchestrator/tests/test_dev_wave_land.py`, `orchestrator/tests/test_check_docs.py`)。
   結論 (SHA-256 pin なし) は変わらない — `FROZEN_MANIFEST` は
   `orchestrator/tests/test_frozen_artifacts.py:38` の 23 件だけで、対象 4 ファイルは含まない
   (`:141` が件数を pin)。**説明を一次資料の出力から取らなかった F1 型の near-miss**として記録する。
2. **実測 3 の行番号訂正。** `docs/failures.md:4819` は F196 の見出し行。stale な逐語は
   **`docs/failures.md:4839`**「runbook §7.3 の待ち手契約自体の改訂は本 wave の scope 外であり、
   裁定へ返す。」、F197 の是正記録は `:4854` 付近、F197 見出しは `:4843`。
3. **実測 2 の訂正。**「`見送り追記` と同型」が指すのは parser の 1 物理行性までであり、
   挿入位置は異なる (見送り = item 先頭行の行末、supersede = F エントリ末尾の独立行)。
4. **DW-G05 の弱化。**「後続 reviewer が再訪を起票する」→「**F196 単体を参照した場合に
   『runbook §7.3 は未改訂』と誤読し得る**」。F197 まで読む運用なら誤読は起きない。
5. **純増検出力の再集計。** 機械的検出力の純増は (i) failures 台帳に対する 1 物理行 shape、
   (ii) 同一行の再挿入拒否、(iii) 本裁定で足す本文 shape 契約と `再発` 側の排他、
   (iv) 本裁定で足す F topology postcondition。加えて**意味上の表現力**の純増 =
   supersede を再発と区別して記録できること。brief の「純増は 3 点」は機械検出力の
   過少計上だったので、上記へ差し替える。

## B. plan v2 — 実装する形

段 2 プランを土台に、次の (R1)〜(R7) を確定する。段 2 プランのうち本節と矛盾する箇所は本節が優先する。

### (R1) 挿入行の list marker は fold が付ける — A1 の構造的閉塞

fragment item は `- F<n> <本文>` とし、**`<本文>` は先頭の `- ` を含まない**。
fold は canonical へ **`- ` + 解決後の本文** を 1 行として挿入する。
これにより挿入行は必ず `- ` で始まり、`FAILURE_ID_RE` (`^### F<n>\.`) に一致しえない。

- 逐語例 (受理): fragment `- F196 **supersede: 2026-08-10** — 恒久対応末尾は F197 で実施済み。`
  → canonical へ `- **supersede: 2026-08-10** — 恒久対応末尾は F197 で実施済み。`
- P4 は維持する。**fold が補うのは list marker (構造) だけ**であり、日付と `supersede:` ラベル
  (意味) は書き手が書く。

### (R2) 本文の shape 契約 — B4

解決前の raw 本文が次の署名に一致することを要求する。

```
**supersede: YYYY-MM-DD** — <空白以外を 1 文字以上含む本文>
```

- 日付は暦日として妥当であること (既存 `tools/spool_fold.py:250 _valid_date` を再利用する)。
- 区切りは `docs/failures.md` の既存 `- **再発: 日付** — ` 慣行に合わせ、
  半角空白 + `—` (U+2014) + 半角空白とする。
- **通る正例**: `- F196 **supersede: 2026-08-10** — 恒久対応末尾は F197 で実施済み。`
- **通らない例**: `- F196 stale` / `- F196 **supersede: 2026-13-45** — x` /
  `- F196 **supersede: 2026-08-10** —` (本文なし)

### (R3) F topology postcondition — A1 の系統的閉塞

`plan_fold` が `docs/failures.md` の描画結果に対し、次を postcondition として検査する。

> 描画後の `FAILURE_ID_RE` 一致列 (番号の並び) == 描画前の一致列 + 本 fold で採番した新規 F 番号の
> 追加順の列。重複はいずれの側にも無い。

不一致なら `SpoolValidationError` で停止する。issue code は `failure-topology`。
これは `再発` payload・`新規` payload・supersede のいずれが F 見出しを偽造しても発火する。

- **通る正例**: 新規 F 2 件 + 再発 1 件 + supersede 1 件の混在 fold が従来どおり通ること。
- **成果物影響**: これが無いと、fragment 側の 1 経路を破っただけで台帳の F-ID 集合・次回採番・
  `F<n>` 参照を偽造でき、監査レンズが別エントリを読む。
- 本 postcondition は `再発` 経由の既存の偽造経路も塞ぐ (本 wave の副次効果)。

### (R4) `再発` 節の supersede 誤用を拒否する — B2

`再発` region の可視行に `- **supersede:` で始まる list item があれば拒否する。
issue code は `failure-recurrence-supersede-misuse`。`_failure_symbols` (validate 経路) で検査し、
`tools/check_docs.py` の spool guard からも見えるようにする。

- **通る正例**: `- **再発: 2026-08-10** — supersede 追記の節が無かったため記録が遅れた。`
  (行頭が `- **supersede:` でなければ、本文中に語が出ても通る)
- 実 canonical に `- **supersede:` で始まる行は現時点で 0 件 (`grep` で確認済み) なので、
  既存 bytes への影響はない。

### (R5) `再発` と supersede の同一行は拒否する — A3

supersede は recurrence 適用**後**の failures テキストに対して重複判定を行う。したがって
同一 fold で `再発` が入れた行と byte 一致する supersede 行は
`failure-supersede-duplicate-line` で拒否される。**この挙動を裁定として確定し、テストで固定する。**

### (R6) 挿入位置と順序 (段 2 プランを維持)

- 挿入位置 = 対象 F エントリの末尾 (次の `### F<n>.` 見出しの直前、最終 F は EOF)。
- 同一 F に `再発` と supersede が来たら **再発 全件 → supersede 全件**。
- 複数 target への splice は canonical offset の降順。target ごとの payload は入力順を保存する。
- 入力順は `Fragment.key = (wave, seq, ledger rank, path)` と fragment 内の物理行順で決まる。

### (R7) target は literal `F<n>` のみ (段 2 プランを維持)

`{{F:slug}}` を target にはできない (raw parse で拒否、`failure-supersede-shape`)。
本文中の placeholder は従来どおり解決する。

### issue code 一覧 (確定)

| code | 拒否対象 | 検査層 |
|---|---|---|
| `failure-sections` (既存) | H2 の未知・重複・順序違反 | validate |
| `failure-supersede-empty` | 使用した節に非空 item がない | validate |
| `failure-supersede-shape` | 複数行・H3・`base:`・継続行・placeholder target・(R2) 署名不一致・不正日付 | validate |
| `failure-recurrence-supersede-misuse` | `再発` 節の supersede 誤用 (R4) | validate |
| `failure-supersede-missing` | literal target が canonical に不存在 | fold (plan_fold) |
| `failure-duplicate` (既存) | canonical F ID 重複 | fold |
| `failure-supersede-duplicate-line` | 対象エントリに同一行が既存 / 同一 fold の同一組 (R5 を含む) | fold |
| `failure-topology` | 描画後の F 見出し列が期待列と不一致 (R3) | fold postcondition |

## C. scope

### scope 内

- `tools/spool_fold.py` — (R1)〜(R7)
- `orchestrator/tests/test_spool_fold.py` — 段 2 プランのテスト表 + 本裁定の追加分
- `orchestrator/tests/test_check_docs.py` — supersede issue が check_docs finding になる経路 1 本
- `orchestrator/tests/test_dev_wave_land.py` — 既存 helper で無理なく書ける場合のみ lock 内 fold 1 本。
  書けない場合は**書かない**。実装子は「書いた / 書かず、理由」を完了報告に明記する
- `docs/spool/failures/README.md`、`docs/spool/README.md`、`docs/failures.md` の運用規則 (親が書く)
- 本 wave の failures fragment 1 件 (F196 への supersede 追記、親が書く)

### scope 外 (裁定パッケージでユーザーへ返す)

- **A4**: `tools/dev_wave_land.py` の rollback 失敗時にも fold の resume state を削除する既存欠陥。
- **`再発` payload 全般の shape 契約**: 本 wave は (R3) (R4) で最悪ケースだけを塞ぐ。
  任意文字列である `再発` payload 一般への shape 契約は別裁定とする。
- `--dry-run` が `after_bytes` を出さないため、実 canonical への splice を byte で目視できない点
  (本 wave は親が repo 外 probe で hash 照合して代替する)。

## D. 変異事前登録 (DW-M01)

対象は `tools/spool_fold.py` の実装。各変異の期待 kill は下表。
`受理集合を縮小する wave` なので過剰拒否を検出する正例も登録する。

| # | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | 挿入行の list marker `- ` を `* ` に変える | KILLED | byte-exact splice テストのみ。topology は発火しない |
| M2 | 最終 F 以外の挿入 offset を `len(failures)` (EOF) にする | KILLED | 実 canonical F196/F197 golden のみ |
| M3 | 最終 F の挿入 offset を `len(failures) - 1` にする | KILLED | EOF 境界テストのみ |
| M4 | supersede を recurrence より先に適用する | KILLED | 同一 target 順序テストのみ |
| M5 | 同一行判定を exact 行比較から `in` (substring) に変える | KILLED | 部分一致の正例 (既存行の substring となる新行は受理される) のみ |
| M6 | `_valid_date` 呼び出しを外し `\d{4}-\d{2}-\d{2}` だけにする | KILLED | 不正日付 shape テストのみ |
| M7 | (R3) topology postcondition を無効化する | KILLED | `再発` 偽造見出しテストのみ |
| M8 | (R4) 再発誤用検査を無効化する | KILLED | 再発誤用テストのみ |
| M9 | 挿入行を `- ` 無しの raw 本文にする (A1 の攻撃そのもの) | KILLED (**冗長 gate**) | byte-exact と topology の双方が発火する。単独変異の単一理由証拠からは外し、攻撃の再現として記録する |
| M10 | **正例**: supersede 節の受理条件に「`新規` 節が必須」を足す (過剰拒否) | KILLED | supersede 単独 fragment の受理テストのみ |

## E. 不変条件 (段 1 から変更なし + 追加)

- canonical の既存 bytes は不変 — 挿入のみで削除・並べ替えをしない。
- fold は決定的かつ冪等。時刻・mtime・ディレクトリ列挙順を出力に使わない。
- 既存の `新規` / `再発` / worklog / decisions の受理集合と出力 bytes は不変。
  **例外は (R4) だけ** — `再発` 節が `- **supersede:` で始まる行を持つ場合に限り拒否が増える。
  実 canonical・既存テストにこの形は 0 件。
- 実装子は `tools/spool_fold.py` と `orchestrator/tests/*.py` だけを編集し、docs 編集と commit をしない。
