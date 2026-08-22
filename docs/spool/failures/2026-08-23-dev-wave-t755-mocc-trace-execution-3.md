---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t755-mocc-trace-execution
seq: 3
---

## 新規

### {{F:spool-title-quote-leak}}. spool worklog fragment の `title:` を引用符で囲むと canonical 見出しへ引用符ごと残る [手順漏れ]

- 事象: `docs/spool/worklog/` の fragment が `title: '[T-NNN] ...'` と単一引用符付きで書かれると、
  fold は引用符を剥がさずそのまま `## <日付> (<連番>) — '<題>'` という H2 見出しを描画する。
  main の `docs/worklog.md` に (826) (829) (831) の 3 件、`docs/archive/` に (135) (673) の 2 件が
  引用符付きで着地済みで、隣接エントリと不揃いになっている。canonical 台帳は fold だけが
  書けるため着地後は修復できない。
- 根本原因: `tools/spool_fold.py` の `_parse_frontmatter` は frontmatter を行単位の
  `([a-z]+): ([^\n]+)` で読み、値を逐語に取る。YAML として解釈しないので引用符を剥がさない。
  一方、書き手側は題が `[` で始まり `:` を含むため「YAML なら引用符が要る」と考えて付ける。
  `tools/check_docs.py` も `tools/spool_fold.py --dry-run` も引用符の有無を見ないため、
  検査は全部緑のまま通る。
- 恒久対応: memory `spool-title-no-quotes` (既存、本事象より前から存在するが着地を止められて
  いない) と、`docs/spool/README.md` 共通 frontmatter 節の明文 (本 wave で追記)。
  機械検査 (`tools/check_docs.py` の spool frontmatter lint) は gate 新設にあたり、
  本 wave の条件 dispatch 13 の最遅読了段を過ぎているため実装せず、裁定パッケージへ送る。
- 再発検知: fold 済み worklog の H2 見出し列に `— '` または `— "` が現れないことの機械走査
  (未実装、上記裁定待ち)。当面は fragment を書いた wave が land 前に
  `python3 tools/spool_fold.py --dry-run` の後で自分の `title:` 行を目視する。
