# docs/spool/ — 台帳 fragment と fold の正本

並行セッションが `docs/worklog.md` / `docs/decisions.md` / `docs/failures.md` の同じ行末を
奪い合うのをやめるための仕組み。**wave はこの下に fragment を書くだけで、canonical 台帳を
一切編集しない。** 台帳への書き込みは main 上で land lock の中で 1 回だけ行われる。

## なぜこうするか

同じ末尾へ 3 台帳を追記し合うため、main へ取り込むたびに衝突と T/D/F の手作業再採番が発生していた。
番号を書いた時点で予約したことにならない (D70 決定 5) 以上、**採番は統合の瞬間に行うしかない**。
fold はその「統合の瞬間」を機械化したものである。

## 構成

```
docs/spool/
  README.md            この文書 (形式の正本)
  FOLDED.md            fold 済み fragment の耐久 receipt (fold だけが追記する)
  worklog/README.md    + fragment
  decisions/README.md  + fragment
  failures/README.md   + fragment
```

**各 ledger の README も必ず読む。** 本書は共通規則 (命名・frontmatter・placeholder・fold の契約) の
正本で、action 節の文法と必須 field は ledger 別 README が正本である。共通規則だけを見て fragment を
書くと、新しい必須 field を落として fold 全体が止まる。

fragment のファイル名は **`<authored>-<wave>-<seq>.md`**。

- `authored` = `YYYY-MM-DD`。**provenance 専用**で、canonical の日付・エントリ番号には使わない
  (それらは fold が実行時点で採る)。
- `wave` = wave branch 名に由来する小文字 slug。一意性は branch 名が担保する。
- `seq` = 1 始まりの連番。1 wave が複数 fragment を持つときに使う。

## 共通 frontmatter

```
---
schema: izanagi-spool-v1
ledger: worklog | decisions | failures
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 1
title: ...            # worklog のみ必須。他 ledger では禁止
---
```

`ledger` はディレクトリ名と一致し、ファイル名は frontmatter から再構成した文字列と byte 一致
しなければならない。UTF-8 / LF / 末尾 newline 必須。未知 key・重複 key は拒否。

## placeholder (遅延採番)

新しい T / D / F 番号は **fragment に書かない**。書くのは名前 (slug) だけで、実番号は fold が付ける。

```
{{T:slug}}   {{D:slug}}   {{F:slug}}
```

- slug は `[a-z][a-z0-9]*(-[a-z0-9]+)*`。
- identity は **(wave, namespace, slug)**。同じ wave の fragment 間なら ledger を跨いで参照できる
  (worklog 本文から `{{D:...}}` を指す等)。**他 wave の slug は参照できない。**
- 既に land 済みの ID は placeholder でなく実番号 (`[T-304]`, `D118`, `F75`) で書く。
- fold 後に `{{` `}}` が 1 つでも残れば停止する。

## 運用

wave 中:

```bash
# fragment を書いたら形式を検査してから commit する
python3 tools/check_docs.py
# check_docs は base digest の不一致を検出しない (実測)。dry-run で確かめる。
# --dry-run は計画 JSON を出すだけで台帳を変えない = fold ではない。
# --show-diff を併せて渡すと、台帳へ挿入される bytes と削除される fragment を
# stderr の unified diff で land 前に目視できる (stdout の JSON は byte 単位で不変)。
python3 tools/spool_fold.py --dry-run --show-diff
git add -- docs/spool
```

`base:` が古いまま land すると、fold は land の協調 lock の**中で**赤になる。そこで止まると
`landed` を返せず、同じ wave 内へ巻き戻さず fresh context で再開することになる。
`--dry-run` はその赤を手前で出すためにある。

**wave 側で fold してはならない。** fold は `tools/dev_wave_land.py` が local main へ ff-only した
直後、同じ協調 lock を保持したまま実行する。これにより採番・追記・ローテーションが直列化され、
race も再採番も起きない。

fold が行うこと:

1. fragment を決定的順序 (`wave`, `seq`, ledger, path) で読む
2. T / D / F を D70 の採番規則 (現行 worklog のローテーション以後 + `docs/archive/worklog-*.md` +
   `docs/phase3.md` 見送り台帳の最大値 + 1) で採番し、placeholder を解決する
3. canonical 3 台帳へ**追記**する。既存 bytes の間へ挿入するのは、既存 F エントリへの `再発` 挿入、
   既存 F エントリへの `supersede 追記` の 1 行挿入、見送り台帳の既存項目への 1 行追記
   (`見送り追記`) だけで、いずれも挿入であって削除・並べ替えをしない
4. worklog の `### 次の一手` を「前エントリの順序を保存し、carry は
   `- [T-NNN] (参照先エントリ番号)`、新規は末尾追加」で全文再生成する。
   **描画済み worklog の読み方と carry 書式の正本は `docs/worklog.md` 冒頭**であり、
   本書は fragment 文法と fold producer 契約だけを持つ
5. `docs/worklog.md` が閾値を超えるなら過去エントリを `docs/archive/` へ移し、
   `docs/archive/README.md` の索引を更新する
6. fragment を削除 (GC) し、`FOLDED.md` へ receipt を追記する

## 不変条件

- canonical の**既存 bytes は不変**。fold が行うのは末尾への追記と、次の 4 種の挿入だけである。
  1. 既存 F エントリ末尾への `再発` payload の挿入
  2. 既存 F エントリの最後の非空行の直後への `supersede 追記` 1 行の挿入
  3. 見送り台帳への新規項目の挿入
  4. 見送り台帳の既存項目の**先頭行の行末**への 1 行追記 (`見送り追記`)
- `docs/failures.md` は描画後に **F 見出し列の postcondition** を通る。列が
  「元の列 + 本 fold が採番した新規 F の追加順」と一致しない、または重複があれば停止する。
  fragment 側の 1 経路が破れても、既存 F ID の偽造・重複はここで塞がる。
- fold は**決定的かつ冪等**。時刻・mtime・ディレクトリ列挙順を出力に使わない。
- **触れなかった active な T は自動的に carry される。** 脱落は
  「出力 active 集合 == 入力 active 集合 − 完了 − 見送り + 新規」の保存則検査が塞ぐ
  (D70 保存則の穴を塞ぐため)。fragment が全 ID を列挙する必要はない。
- 同一内容の fragment を再投入しても `FOLDED.md` の receipt が replay として拒否する。
- 適用は before/after hash を持つ transaction で行い、中断後は同じコマンドで resume する。
  第三の状態を見つけたら停止する。

## この仕組みが保証しないこと

- **wave branch を破棄すれば fragment も消える。** これは未 commit の worklog エントリを捨てるのと
  同じであり、fold 固有の新しい危険ではない。
- 意味の正しさは検査しない。`完了` の終端性は `remaining: none` という**構造 field の宣言**と、
  「残件あり」「一部完了」という語の検出までしか見ない。宣言が事実かどうかは書き手の責任である。
- `### 次の一手` の並び順は**優先度順ではない**。優先度は各項の本文に書く。
