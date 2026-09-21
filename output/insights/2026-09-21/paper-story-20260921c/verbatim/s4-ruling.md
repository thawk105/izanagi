# 段 4 裁定 — paper-story 2026-09-21c + fig3c (2026-09-21 14:17 JST (file mtime))

入力: 段 1 brief (`brief-s1.md`)、段 3 相談 1 本 (`codex/s3-consult.md`、read-only、gpt-6-astra / medium、2 レンズ 1 本、`check_codex_output.py` OK、
high 0 / mid 4 / low 5)。段 4 直前に裁定 inbox を再走査した — 本 wave の起点後に着地した D は無い (main は `d99c556df` のまま、14:03 JST 以後に
本 wave の対象へ触れる裁定の着地なし)。

## 所見の裁定

| # | 所見 (要約) | 裁定 | 採否と反映 |
|---|---|---|---|
| 1 | (項 1) 版名は現状で拒否される。日付部分だけ暦日検査、path 照合は接尾辞込み、`figure_created` は厳密日付のまま | real (P1 前半の支持) | 採用。変更は `load_states` の `story_version` の検査だけ |
| 2 | (項 2, mid) A-4 の旧 caption 文は 21b で偽 (§0 fig3b 注記・§8 A-4)。ただし任意自由文 key `caption_notes` は最小ではない。旧版だけ旧 `CAPTION` を完全保持し、他の版には状態に依存しない固定 caption を使えば足りる | real | **採用 — (P1) 後半を改める。** `caption_notes` は作らない。JSON key・schema・脚注・描画処理は変えない。`_caption` が `story_version == "2026-09-19"` のときだけ旧 `CAPTION` を返し、それ以外は新定数 `GENERIC_CAPTION` を返す |
| 3 | (項 2) B-7 の caption 文「neither promoted nor closed by this figure」は真 (この図による昇格・閉鎖の否定)。旧 JSON の B-7 副ラベルは現況と合わない | real (前半は P1 の射程を狭める根拠、後半は写しの注意) | 採用。汎用 caption は項目固有の文を持たないので影響しない。21c の JSON は B-7 を 21c 本文から写し直す |
| 4 | (項 3, low) anchor 形式と群サイズは 21b でも一意に当たる。ただし `§0 item N` の番号は版ごとに意味が変わる (旧 JSON の item 3 = Silo scope、21b の item 3 = B-5 試走) → 番号を流用せず 21c 本文から写し直す。§8 の範囲に `- **X-N ` 型の補足行を足すと anchor が 2 件になり拒否される → 本文の書き方で避ける | real | 採用 (JSON は 21c 本文から全 anchor を写し直す。21c §8 に `- **<ID>[ .(]` で始まる補足行を作らない) |
| 5 | (項 3) B-8 の obtained は定義と整合。副ラベルは短く、数量を入れない。結果稿 §4 の 11 項を本文へ運ぶときは「以下は結果稿 §4 の引用。引用内の節番号は同稿を指す」と明示する。旧 §8 B-8 の仕分け (2)・「3 要素のいずれも満たさず」等の現在形を、案 B の歴史記述と案 A の今回の判定に分けて書き直す | real | 採用 (差分事実表と §8 の起草指示へ入れる) |
| 6 | (P5, mid) 再生成条件が本文 bytes だけでは狭い。JSON・本文・生成器を確定してから生成し、生成後の変更時は記録入力との一致を確認する。生成中に生成器を編集しない。fig3c の provenance hash を 21c 本文に載せると循環参照 | real | 採用。**(P5 v2):** 最終図は、21c 本文・状態 JSON・生成器の 3 つを commit で確定した後に生成する。生成後にどれかを変えたら未 land の 3 成果物を捨てて再生成する。fig3c の hash と実走証跡は figures README と insight にだけ置き、21c 本文は図名・出所・役割までを書く |
| 7 | (項 4, low) D2202 項 5 は一項目のために版を作ることの却下であり、明示依頼の全面再導出を禁じない (D1858) | refuted (攻撃不成立 = P4 維持) | P4 維持 |
| 8 | (P6, mid) 「README」の対象を列挙し、親の反映と最終差分確認を明記する。入口 README の「積んでいる 2 件」と「着地する見込み」の不整合も直す | real | 採用。**(P6 v2):** 受入の owned-path から外すのは `docs/paper-story/README.md` と `docs/paper-story/figures/README.md` の 2 本 (他 wave が節・行を足す hot file)。`tools/plotting/README.md` は owned-path に入れる。親が 3 本とも本文を反映し、land 前に `git diff <main>` で自分の差分だけであることを確かめる。入口 README の stale 注記節は件数・移管先・将来形を一緒に書き直す |
| 9 | (項 5, mid) T7 は旧 caption の全文一致を保証しない。旧 caption 全文の独立 literal 一致を足す。境界 test: 不正暦日 (`2026-02-30c`)・接尾辞範囲 (大文字・複数字)・作成日への接尾辞・path 不一致。不正暦日の fixture は対応本文を用意して、日付検査を消すと「file 不在」でなく受理される形にする | real | 採用 (下の plan v2 の test 集合と変異登録) |
| 10 | (項 6) fig3c 節の中身 (入力・状態語・旧図との差・数量を描かない限定・`--states` 付き再現コマンド・caption・実走・proof chain)。`DEFAULT_STATES` は変えない。fig3b 節は正文を保持し fig3c への導線を短く足す | real | 採用 |
| 11 | (項 7, low) pin 棚卸しの全域性は未確認。旧 provenance の `generator.sha256` を書き換えない | real (棚卸しの限定) | 採用 — 棚卸しの範囲 (`git grep` の対象 = tracked 全体、`docs/archive` 除外の path 参照 + tracked 全体の旧 sha256 文字列) と結果を insight に書く。旧 provenance は不変 |

## plan v2 (実装: Codex author 1 本、所有 = `tools/plotting/plot_arc_status.py` と `orchestrator/tests/test_plot_arc_status.py`)

1. `load_states`: `story_version` は `^\d{4}-\d{2}-\d{2}[a-z]?$` (英小文字 0〜1 字) を受理し、暦日検査 (`datetime.date.fromisoformat`) は先頭 10 字に掛ける。
   `figure_created` は従来どおり `^\d{4}-\d{2}-\d{2}$` + 暦日検査。`story_path == f"docs/paper-story/{story_version}.md"` (接尾辞込み) は不変。
2. `_caption`: `story_version == "2026-09-19"` なら既存 `CAPTION` (1 文字も変えない)、それ以外は新定数 `GENERIC_CAPTION` (下の逐語)。`build_provenance` の
   `caption` field はこの戻り値。他の関数・脚注・描画・schema は変えない。
3. `GENERIC_CAPTION` の逐語 (`{number}` と `{story_version}` の差込みだけ):
   `Figure {number}. Status of the paper-story arc read from the frozen {story_version} story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported; each item's sublabel carries the recorded judgment words and limitations. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. Recorded judgments keep the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen.`
4. test (既存 T1〜T8 の期待値は変えない。追加のみ):
   (a) 既定 JSON の provenance caption が旧 caption の**全文の独立 literal**と一致する。
   (b) 正例: tmp root に `docs/paper-story/2026-09-19c.md` (2026-09-19 版本文の複製) を置き、JSON の `story_version` = `2026-09-19c`・`story_path` 一致で
       `load_states` が通り、provenance caption が `GENERIC_CAPTION` の**独立 literal** (図番号・版名を差し込んだ全文) と一致し、旧 caption 固有の文
       (`A-4 is adopted by ruling but inactive pending human action`) を含まない。
   (c) 異常系 (いずれも期待理由で `FigureDataError`): 不正暦日 `2026-02-30c` (対応本文を tmp root に置く)、大文字接尾辞 `2026-09-19C`、複数字接尾辞
       `2026-09-19cc` (いずれも対応本文を置く)、`figure_created` = `2026-09-21c`、`story_version` = `2026-09-19c` で `story_path` = `docs/paper-story/2026-09-19.md`。
5. 自走 harness (`if __name__ == "__main__": pytest.main([__file__, "-x"])`) と subprocess env の `PYTHONDONTWRITEBYTECODE` は既存のまま (F42 / F521 の再発防止)。

## 変異の事前登録 (実装前、B-057)

対象 = 統合 commit の `tools/plotting/plot_arc_status.py`。単一理由性は実装後に確認し、成立しなければ実効 gate へ再照準する (DW-M01)。

| ID | 変異 | 期待 (KILLED させる test) |
|---|---|---|
| M0 | 対照: 無害な comment を 1 行足す | SURVIVED (runner の drift 核が無いことの確認) |
| M1 | `story_version` の正規表現を旧形 (接尾辞なし) に戻す | (b) 正例 |
| M2 | 接尾辞を複数字 (`[a-z]*`) まで許す | (c) `2026-09-19cc` |
| M3 | 接尾辞に大文字を許す (`[a-zA-Z]?`) | (c) `2026-09-19C` |
| M4 | `story_version` の暦日検査を外す | (c) `2026-02-30c` |
| M5 | `figure_created` にも接尾辞を許す | (c) `figure_created = 2026-09-21c` |
| M6 | `story_path` 照合を接尾辞を除いた日付部分で行う | (b) 正例 と (c) path 不一致 |
| M7 | `_caption` が常に旧 `CAPTION` を返す | (b) 正例 |
| M8 | `_caption` が常に `GENERIC_CAPTION` を返す | (a) 旧 caption 全文 と T7 |

## 不変条件 (段 5 以降)

規律 1 / 2 / 7。凍結物 (旧版・claim-evidence 2026-09-21・results 稿・既存 figures と fig3b の 3 成果物・`arc_status_story_2026-09-19.json`) の bytes 不変。
既定 JSON に対する生成器の出力の表示内容 (drawn_items・caption 全文) 不変。新規計測ゼロ。gate・検査・台帳・一般化の追加なし。

## DW-O13 (受理形の追加) の確認

追加する受理形は `story_version` の英小文字 1 字の接尾辞だけ。入力 field は状態 JSON の `story_version` で、要求値 `2026-09-21c` は実在する版 file
`docs/paper-story/2026-09-21c.md` (本 wave の成果物) と対になって到達可能 (同日 3 版目)。同日の版 file 名は `2026-09-20b.md` / `2026-09-21b.md` の先例が
英小文字 1 字で、複数字・大文字の実例は repo に無い (`ls docs/paper-story/`)。時間予算を持つ述語ではない。
