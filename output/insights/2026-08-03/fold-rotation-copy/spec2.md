# plan v2 — T-352 / T-358 の確定仕様 (親の段 4 裁定)

段 2 プラン (`plan2.md`) と段 3 敵対相談 (`review2.md`) を親が裁定して確定した仕様である。
**この文書が実装の正本。**plan2.md と review2.md は根拠資料であり、食い違う場合は本書を優先する。

## 確定した設計

### T-352 — `完了` item に構造 field を必須化する

**field 契約**

- field 名 `remaining`、書式 `  remaining: none` (2-space indent、値は ASCII lowercase の `none` のみ)。
- **位置の束縛 (review2 所見 1 への対応)**: item block の**末尾から連続する「機械 field 行」の中**に
  ちょうど 1 つ存在すること。機械 field 行とは `^  [a-z][a-z0-9_-]*: .+$` に一致する行とする。
  item 末尾から遡り、この形に一致しなくなった行より前は本文であって field 群ではない。
  **本文中 (fenced code block、HTML comment、通常の散文) に現れる `remaining:` 形の行を
  field と数えてはならない。**これを数えると「初期処置だけ終了。後続作業は明日」+ code fence 内の
  `remaining: none` という decoy で完了が受理され、T-352 の目的そのものが破れる。
- 既存の `base:` 行も同じ末尾 field 群に属する。**`_strip_base` の既存契約 (error ID、cardinality、
  出力) は変更しない。**`remaining` は専用 helper で扱う。
- `remaining` を要求するのは `### 完了` の item だけ。`更新` / `見送り` / `carry` / `新規` には要求しない。
- canonical worklog へは出さない (`base:` と同じ authoring metadata として除去する)。
- 既存の禁制語検査 (`残件あり` / `一部完了`) は**残す**。field 除去後の本文に対して従来どおり適用する。
  削除すると「一部完了だが `remaining: none` と書いた」入力が新たに通る = 承認外の受理集合拡大になる。
- error ID: field の欠落・重複・値不正・書式不正はすべて `completion-remaining-field`。
  禁制語との矛盾は従来どおり `completion-remaining`。
- frontmatter の `schema: izanagi-spool-v1` は変えない (全 fragment の migration を起こさないため)。

### T-358 — `見送り追記` 節で既存の見送り台帳項目へ追記する

**fragment 形式**

- action H3 の順序を `carry` → `完了` → `更新` → `新規` → `見送り` → `見送り追記` とする
  (`見送り追記` は末尾。任意 section だが、置くなら 1 item 以上必要)。
- item は **1 物理行** `- [T-NNN] <suffix>`。`[T-NNN]` は既存の canonical T ID (placeholder 不可)。
  `base:` と category H4 は付けない。
- suffix は**空でなく、空白のみでもいけない** (`deferred-append-shape`)。
- suffix 内の placeholder 参照 (`{{D:...}}` 等) は許し、plan 時に解決する。
- fold は日付・発火回数・「発火記録:」という語を自動生成しない (見送り台帳の慣行を変えないため)。

**追記位置 (review2 所見 3 への対応 — 親の裁定)**

- **対象 item の先頭行 (ID を含む行) の行末に追記する。**
- plan2 が提案した「block 末尾 (最後の継続行) への連結」は**採らない**。対象 item の最終行が
  fenced code の閉じ行である場合に fence を破壊し、`docs/phase3.md` の後続節が壊れるため。
  既存の T-058 / T-059 の慣行 (1 行 item の行末に継ぎ足す) とも先頭行追記の方が一貫する。
- 追記は「行末の改行の直前へ suffix を挿入する」だけとし、既存 bytes の削除・並べ替え・
  正規化を一切行わない。

**対象の探索 (review2 所見 4 への対応)**

- 探索範囲は `## 見送り台帳` から `### 裁定・完了記録` の直前まで (既存 `_deferred_region` の範囲)。
- **fenced code block と HTML comment の内側を不可視化してから** top-level item を抽出すること。
  `tools/check_docs.py` の既存 tokenizer (同ファイル 1001 行付近) と**同じ可視性規則**にする。
  raw な行頭 regex だけで抽出すると、comment 内の decoy `- [T-058] example` を実項目と誤認し、
  重複拒否で fold 全体が止まるか、不可視領域へ追記してしまう。
- 対象 ID が見つからない → `deferred-append-missing`。
- 可視な top-level item に同じ ID が 2 つ以上 → `deferred-append-duplicate`。
- section があるのに item 0 件 → `deferred-append-empty`。

**適用の意味論 (review2 所見 6 への対応 — 親の裁定)**

- **逐次意味論を採る。**`Fragment.key` = `(wave, seq, ledger rank, path)` の順に fragment を処理し、
  各 fragment の `見送り追記` は**その時点の phase** に対して適用する。
  したがって、先行 fragment が同じ fold で見送り台帳へ移した項目にも追記できる。
- plan2 の「fold 開始時点から存在する項目だけ」案は**採らない**。裁定文が言う「既存項目へ追記」を
  超えて受理集合を縮小し、正当に順序づけられた入力を拒否するため。

**冪等性 (review2 所見 7 への対応)**

- 既存の transaction (before/after hash)・resume・`FOLDED.md` の content replay 拒否に加えて、
  **対象 item に同一 suffix が既に存在する場合は拒否する** (`deferred-append-duplicate-suffix`)。
  fragment の wrapper bytes だけ変えた再投入が発火記録を二重挿入するのを、T-358 内で閉じるため。
- 一般 receipt schema / identity の改訂へは広げない (scope 外)。

**active 保存則からの分離**

- `見送り追記` を `_Operation` へ混ぜない。専用の `_DeferredAppend(task_id, suffix)` と
  専用挿入経路 (`_insert_deferred_appends`) を設け、`_insert_deferred` (新規見送り挿入) は
  そのまま残す。active 集合・完了集合・見送り集合を変えない操作である。

## 実装の分割 (review2 所見 10 への対応 — 親の裁定)

**実装子 2 本に分ける。所有は素集合。**

- **worker A**: `tools/spool_fold.py` のみ。
- **worker B**: `orchestrator/tests/test_spool_fold.py` のみ。

同じ仕様書 (本書) を両者に渡す。実装と oracle を同じ worker が書くと、本書が塞いだ decoy
(fence 内 field、comment 内 item) が実装とテストの両方から同時に漏れるため。

**docs は親が書く** (`docs/spool/README.md`、`docs/spool/worklog/README.md`)。実装子は触らない。

## テストで必ず固定すること (worker B の担当)

### T-352

1. 禁制語が無いだけの完了 (field 欠落) が拒否される。
2. `remaining: none` 以外の値 (`None`, `なし`, `some`, `0`, 末尾コメント付き) が拒否される。
3. `remaining` 行の重複が拒否される。
4. **decoy 負例**: item 本文中の fenced code block 内に `  remaining: none` を書いた完了 item が
   **拒否される** (field 群の外なので欠落扱い)。HTML comment 内の decoy も同様。
5. valid な `remaining: none` が canonical worklog から除去される (漏出しない)。
6. `base:` と `remaining:` の行順が入れ替わっても受理される。
7. `更新` / `見送り` には `remaining` を要求しない。
8. 既存 `test_n18_completion_with_remaining_work_is_rejected` の期待値 `completion-remaining` は維持。

### T-358

9. 1 行 item の対象へ追記され、**先頭行の行末**に入る。
10. **複数行 item** の対象へ追記しても、追記位置は**先頭行の行末**であり継続行を壊さない。
11. **fenced code を含む item** の対象でも fence が壊れない。
12. **byte-exact oracle** (review2 所見 5): 1 対象 / 同一対象へ複数追記 / 複数対象 / 複数行対象 の
    各ケースで `after == before[:offset] + exact_payload + before[offset:]` が成り立つ
    (許可された挿入以外の bytes が 1 byte も変わらない)。
13. 空 section が拒否される。
14. 複数行 item (継続行つき) の `見送り追記` item が拒否される (1 物理行限定)。
15. 空 / 空白のみ suffix が拒否される。
16. 対象 ID 不在が拒否される。
17. `### 裁定・完了記録` の中にある ID を対象にできない。
18. 可視な重複 ID が拒否される。
19. **comment / fence 内の decoy item** を対象と誤認しない (所見 4)。
20. action 順序違反 (`見送り追記` が `見送り` より前) が拒否される。
21. 同 fold 内で先行 fragment が見送りにした項目へ追記できる (**逐次意味論**)。
22. cross-ledger placeholder が解決される (`{{D:...}}` が raw のまま phase へ漏れない)。
23. 追記順序が `(wave, seq, item index)` で決まる。**`fold_date` を固定し、実 FS 列挙順や
    `PYTHONHASHSEED` に依存しない fixture にする** (所見 9)。
24. 同一 suffix の再投入が `deferred-append-duplicate-suffix` で拒否される。
25. active 保存則が変わらない (`見送り追記` だけの fragment は全 active を carry する)。

**既存テストの期待値・名前・helper の既定挙動は変更しない。**
既存 helper に引数を足す拡張は、既定値が現行挙動と同じであれば可とする。

## 禁止事項

- **T-347** (fold commit の tree を計画と blob 単位で照合) は scope 外。実装しない。
- **凍結ソース閉包に触れない。**
- 見送り台帳の慣行そのもの (何を書くか) を変えない。手段だけ補う。
- `/rulings` command、Rulings Skill、`docs/dev-wave/core.md` を編集しない (scope 外の裁定パッケージ)。
- 一般 receipt schema / identity を改訂しない。
- `tools/check_docs.py` を共有 tokenizer 化しない (spool 側に同型実装 + 整合テストで閉じる)。

## 環境の注意

この環境では codex sandbox から計算ノードへの dispatch が認証エラー
(`qstat -Q` → `[API EACCTAUTH] Unknown user-id`) で失敗する。
**pytest を走らせられない場合は「走らせていない」と正直に書くこと。**親が独立に実走する。
迂回を試みない。
