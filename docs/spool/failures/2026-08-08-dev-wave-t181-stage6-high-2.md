---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t181-stage6-high
seq: 2
---

## 新規

### {{F:substring-pin-tautology}}. 契約 drift を止める pin を文字列の出現数で書き、3 巡続けて恒真だった [恒真ゲート] [テスト代表性]

- 事象: `docs/dev-wave/workers.md` の段 6 契約が黙って書き換わるのを止める pin を実装したが、
  段 6 敵対レビューと焦点再レビューが production 経路の probe で **3 巡続けて迂回を実測**した。
  (1) `visible_section.count("`reasoning=high`") == 1` — 規範文を消して
  `参考リンク: [例: \`reasoning=high\`](...)` や `参考値: outer=\`reasoning=high\`` に置換しても
  `findings=[]`。(2) 規範文**全文**の `count(sentence) == 1` — 全文を `> ...` (blockquote) や
  `参考（旧規範）: ...` へ移せば `findings=[]`。(3) `splitlines().count(sentence) == 1` —
  `参考（旧規範）:<U+2028><規範文>` で `findings=[]` (`splitlines()` は LF/CRLF/CR に加えて
  U+2028 / U+2029 / VT / FF / NEL も行境界として扱う)。
- 影響: いずれも「実行される命令」を削除して「参考引用」だけ残した docs が land できる状態だった。
  本 wave が主張する「docs 契約 + drift pin」が実質成立しておらず、
  **謳うだけで発火しない保証**を台帳へ記録するところだった。
- 根本原因: 「その文字列が節内に在る」ことと「その文が独立した規範として置かれている」ことを
  同一視した。**契約文の pin は存在検査ではなく位置・文脈の検査である。** markdown では
  同じ文字列を引用・例示・リンク・list item として無害化する手段が多数あり、
  substring 一致はそのすべてを通す。
- 恒久対応: `tools/check_docs.py` の `_check_dev_wave_reasoning_effort_pins()` は、
  CRLF を LF へ正規化したうえで `"\n"` で分割し、**規範文と完全一致する可視な行がちょうど 1 行**
  であることを要求する。値列検査 (`values != [expected]`) を相補層として併置する
  (前者は規範文の消失を、後者は節内の別値混入を捕まえる)。判断規律は
  {{D:stage6-reasoning-high}} が持つ。
- 再発検知: `orchestrator/tests/test_check_docs.py` の production-path 負例
  (`..._requires_independent_s06_lines_exact` = blockquote / list / 見出し prefix / 前後置 /
  末尾空白 / 重複、`..._rejects_unicode_line_separators_exact` = U+2028 / U+2029 / VT / FF / NEL、
  `..._rejects_s06_decoys_exact` = 例示リンク / 別 key) と、
  これらを無効化する変異 M9 / M13 / M14 の KILLED 記録。
- 併発した既知型: 同 wave で `_reference_id_sections()` が raw text を走査するため、
  H2 見出しから本文まで fence / HTML comment / **raw HTML block** へ入れると pin と
  必須 H2 inventory を同時に迂回できた (`<x>\n` の 4 bytes で足りる)。
  片側だけ可視化を直すともう一方が mask になるため、両側を raw HTML 対応の可視化へ揃えた。

## 再発

### F28

- **再発: 2026-08-08 (段 6 reasoning pin wave)。** 事前登録 8 件のうち **3 件の kill 意味論が
  成立していなかった**。M4 / M5 (可視化先行を片側だけ戻す) は他方の層が拒否を継続するため
  受理集合が変わらず、M6 (終端 allowlist だけ戻す) は canonical literal 層に mask される。
  **今回も段 3 の敵対相談をすり抜け、段 6 のレビューと焦点再レビューが実装後のコードを読んで
  検出した** (F28 本文の 2026-07-26 再発と同じ通過経路)。`DW-M03` / `DW-M04` に従って
  両層同時変異へ再照准し、v1 の登録は erratum として台帳に残した。
  本走では 15/15 が期待一致し、`DW-M08` に従って「受理集合を変える kill 12」
  「diagnostic sensitivity pin 2 (M4 / M5)」「SURVIVED 1 (M6、mask を事前登録済み)」に
  分けて記録した。**総数を 15 kill と書かないことが対応の本体である。**

### F154

- **再発: 2026-08-08 (段 6 reasoning pin wave)。新しい所在の変種。** 対象機構
  (`DW-S06-A` / `DW-S06-C` の reasoning) には既にユーザー裁定
  「値は `max`、引き下げは A/B の 10 run 再走後、当該測定は他段へ外挿しない」が存在したが、
  **その裁定は `docs/decisions.md` にも現行 `docs/worklog.md` にも無く、
  `docs/archive/worklog-phase3-0801-101.md` にしか無かった**。親の brief 前検索は
  decisions の索引と現行 worklog 末尾までで、archive を引かなかったため取りこぼした。
  結果、brief は「段 6 は未規定だから初回確定であり引き下げではない」という誤った前提で
  段 2・段 3 を走らせた。段 3 の敵対レンズが一次資料を見つけて反証し、親が裏を取って
  `DW-S04` に従いユーザー再裁定へ返した (ユーザーは既存裁定を supersede する選択をした)。
- 恒久対応: brief 前の裁定検索は、対象タスク ID と decisions の索引だけでなく、
  **対象機構名で `docs/archive/worklog-*.md` まで意味検索する**。
  F58 の「新規起票の前に archive まで含めて意味検索する」を、起票だけでなく
  **既存裁定の有無の確認にも適用する**。
- 再発検知: 段 3 の敵対レンズに「親 brief が置いた前提を一次資料で反証せよ」を必ず入れる。
  本件はそれで捕まった。
