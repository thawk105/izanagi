# 段 1 brief — 論文ストーリー 2026-09-21c 版 + claim-evidence 次版 + 状態図 fig3c (2026-09-21 14:09 JST (file mtime)、起点 local main d99c556df = entry 1795 までの fold)

**研究前進:** 論文ストーリー最新版の §8 B-8 を「未取得」から「B-8 の別登録の 3 値判定 pass (限定付き)」へ進め、21b 版 §0 が「図は差し替えず本文が正本」
と置いていた第 3 幕の現況図を、21c 版 §0 / §8 から写した後継図 fig3c で埋める。完了判定 = 下の成果物 1〜6 が受入 child-green で local main に land。

**成果物:** (1) `docs/paper-story/2026-09-21c.md` (21b を複製 → 時点語の機械置換 → 正典全体から全節を再導出)。(2) `docs/paper-story/claim-evidence/2026-09-21b.md`
(同日 2 稿目、21c 版から再導出、旧現在形の併存を残さない)。(3) `docs/paper-story/README.md` (版の履歴 1 行・最新 =・訂正節・stale 注記 3 件の本文への移管と
0 件化・claim-evidence 表 1 行)。(4) `tools/plotting/arc_status_story_2026-09-21c.json` (人が 21c 版 §0 / §8 の実文から写す)。(5) fig3c 3 成果物
(`docs/paper-story/figures/fig3c_arc_status_2026-09-21.{png,pdf,provenance.json}`、login = 計測機の外で生成) + `figures/README.md` の節 + `tools/plotting/README.md` の追随。
(6) 生成器の最小修正 (Codex author、`tools/plotting/plot_arc_status.py` + `orchestrator/tests/test_plot_arc_status.py` のみ)。記録 = insight
`output/insights/2026-09-21/paper-story-20260921c/` + spool fragment。

**確定済み裁定・一次資料:** B-8 = D2194 項 1 (承認)・D2186 項 1 (2) (仕分け (2) の限定)・D2202 (発効と実施の形)、結果稿 `results/2026-09-21-b8-final-candidate-longrun-verify.md`、
insight `output/insights/2026-09-21/t2807-b8-effective/README.md`、entry 1791。他の起点後着地: D2200 (B-5 本走の段階認可ほか、entry 1782)、[T-2824] g1 候補文書削除 (entry 1787)、
[T-2812] 旧系列整合 (D2201、entry 1790)、[T-2344] closure 85→96 (D2203 / D2204、entry 1794)、[T-2795] K2 pair 修復 (D2205、entry 1795)、運用診断 (1780・1781・1783〜1786・1788・1789・1792)。

**(P1) 生成器の最小修正 (親の provisional 裁定・攻撃対象):** 生成器は `story_version` を `YYYY-MM-DD` に限定し `story_path == docs/paper-story/<版>.md` を要求するので
`2026-09-21c.md` を参照できない → `story_version` だけ英小文字 1 字の接尾辞を許す (日付部分は従来どおり ISO 検査、`figure_created` は不変)。加えて、キャプションの固定文が
2026-09-19 版の状態 (「A-4 is adopted by ruling but inactive pending human action」ほか) を持ち、21b 版自身が A-4 を「発効済み」と書くので 21c の図では偽になる →
JSON に任意 key `caption_notes` (自由文検査を掛ける) を足し、有れば状態依存の中間文をそれで置き換え、無ければ従来の固定文 (既定 JSON = fig3b の再現・T7 は不変)。
これ以外 (版名の一般化、図種の追加、配置・色・群サイズ・脚注の変更、既存 test の期待値の変更) はしない。
**(P2) 命名:** 版 = `2026-09-21c.md`、claim-evidence = `2026-09-21b.md`、JSON = `arc_status_story_2026-09-21c.json`、図 prefix = `fig3c_arc_status_2026-09-21` (図番号 3c)。
**(P3) B-8 の書き方:** 【状態】は「取得 — B-8 の別登録 (事前登録 v1) の 3 値判定 `pass`」。30 枠の pass を未観測の条件・別の日・別 node・長さ・反復数の効能・性能・S-1 の充足へ広げない。
限定は結果稿 §4 の 11 項を逐語で運ぶ (要約で縮めない)。図の状態は obtained (定義「判定の記録がある、主張支持ではない」)。
**(P4) D2202 項 5 (「新しい日付の版は作らない」) は T-2807 wave 自身の置き場の裁定であり、ユーザーが明示依頼した全面再導出の版を禁じない** (README 契約: 新しい版は正典全体からの導出)。
**(P5) 状態図は 21c 版の本文確定 (段 6 closed) の後に生成する。** 生成後に 21c の bytes を変えたら、未 land の 3 成果物を捨てて再生成する (provenance が story sha を束縛)。
**(P6) README は受入の owned-path に入れない** (hot file、先例)。

**不変条件:** 規律 1 / 2 / 7。凍結物 (旧版・claim-evidence 2026-09-21・results 稿・既存 figures と fig3b 3 成果物) の bytes 不変。既定 JSON に対する生成器の出力の表示内容 (drawn_items・caption) 不変。
新規計測ゼロ。gate・検査・台帳・一般化の追加なし。英語稿・2 本目論文は scope 外。

**pin 棚卸し (DW-O09):** 生成器の変更前 sha256 `cfcb64f0…` を持つのは `figures/fig3b_arc_status_2026-09-20.provenance.json` の記録だけ (検査なし、figures README が「着地後の一致を検査する
test は無い」と明記)。path 参照は test 1・plotting README・figures README・failures (F42/F521 再発の記録)・旧 insight の記録のみ。durable manifest なし。

**分割・環境:** 親 = docs 本文 (版・claim-evidence・README・JSON・figures README)。Codex author 1 (生成器 + test のみ、docs・commit しない)。段 3 read-only 相談 1 本 (P1〜P6 と
変更面)、段 6 read-only レビュー 2 本 (A = 版・claim-evidence の一次資料照合 / B = 生成器 diff・JSON と 21c の対応・figures README)、焦点再レビュー ≤ 3 巡。変異 matrix は生成器の変更行に事前登録。
作図と生成器の実走は login、焦点走・変異・受入は計算ノード (Pegasus、`run_tests.py` / `dev_wave_wait.py acceptance`)。

**変更面の実アンカー:** `plot_arc_status.py` の `load_states` (key 集合 `_keys(data, …)`・`story_version` / `figure_created` の ISO 検査・`story_path` 照合・自由文列挙)、`_caption` と `CAPTION` 定数;
test の `BAD_CASES` / `test_t3_invalid_json_without_drawing` / 新規の正例 1 本 (接尾辞版 + caption_notes)。
