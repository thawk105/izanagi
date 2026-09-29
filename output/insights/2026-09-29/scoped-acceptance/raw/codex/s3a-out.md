## 所見

- **実在する見逃し候補は B5 の event 群。** `test_b5_llm_round.py:22,36–54` は `PILOT` と `"ledgers/llm/events"` を連結し、`glob("*.json")` で実 repo の event を読み、複数の test が `_fixture()` を使う（同:109–156）。例えば `output/insights/2026-09-20/t2797-b5-contrast/ledgers/llm/events/000001-series-start.json` の完全 path と basename は test source にない。plan 自身も変数連結を偽陰性と認める（`s2-plan.md:25`）。**放置時:** この変更を許可し、directory 連結を選択器が解決できなければ、全受入で赤になる event 破損が縮小受入で緑のまま main に入る。**推奨:** 当該 prefix 全体を初版の許可集合から外すか、定数連結と glob の到達範囲を解決できない時点で全受入に倒す。これは静的な反例経路であり、赤の実走確認ではない。

- **索引・import 先経由の reader も test source の照合だけでは拾えない。** `test_plot_a1_sized_paired.py:32,461,584–595` は `PLOT.CAPTION_SOURCE` と `PLOT.ATTEMPT2_CAPTION_SOURCE` で実文書を読み、実 path は `tools/plotting/plot_a1_sized_paired.py:55–57` にある。`test_paper_story_a1_headline.py:30–35,91–108` も production 定数を通じて実文書と証明書を読む。**放置時:** production reader の除外が一つでも漏れると、文書の表・束縛を壊した変更が、対応 test を選ばず main に入る。**推奨:** これらの path を分類器の除外例として固定し、production 定数の連結を含む分類負例を作る。test 側の basename 照合を防壁と見なさない。

- **完了判定 (c) の親案は対象文書を指定しないと成立しない。** 存在しない D 番号・path の検査は `check_docs.py:1155–1159,6712–6775` の `LIVING_DOCS` 走査に限定される。insight、paper-story、一般の新規 `docs/*.md` は同:129–170 の説明・列挙上、その検査対象ではない。D 参照の正規表現も 1～3 桁に限る。**放置時:** 許可 doc に壊れた参照を書いても直接実行 `check_docs.py` が緑となり、(c) の赤を実証できない。**推奨:** `LIVING_DOCS` 内かつ縮小許可対象の文書を先に特定し、実際の検出結果を確認する。見つからなければ (c) は B5 event など実 reader の期待値破壊で実証する。pin 節の改変は plan の除外方針（`s2-plan.md:63`）と両立しない。

- **壊れた spool frontmatter は適切な負例だが、fold 後の赤とは別。** `spool_fold.py:518–537,1053–1093` が frontmatter を検証し、`check_docs.py:1298–1354` も spool guard を呼ぶ。`spool_fold.py --dry-run` は `plan_fold` の失敗を非ゼロで返す（同:3678–3710）。一方、正常な fragment が canonical 台帳へ及ぼす影響は dry-run 時点では未適用で、land は fold gate と適用後の `check_docs.py` を実行する（`dev_wave_land.py:4010–4069,5057–5079,5200–5210`）。**放置時:** 縮小受入だけを「fold 後も緑」の証拠と記すと検出力を過大評価する。**推奨:** frontmatter 負例は直接実行の赤、canonical 変化の検査は既存 land fold gate の赤として別々に記録する。後者を縮小受入時点の検出と主張しない。

- **growth hold の穴は直接実行で一部だけ補える。** `growth_test_holds.py:580–612` の `test_real_repo_clean` など docs_bytes 3 件は全受入でも skip される。直接実行 `check_docs.py` は現在の実 repo の finding と rc を検査でき、`spool_fold.py --dry-run` は fragment の schema と計画を検査できる。しかし held test の肯定的な assertion、特に checker が過剰拒否しない契約まで同一には補わない（`test_check_docs.py:9838,12660–12668`）。**放置時:** 「全受入と同じ検出力」という評価が誤る。**推奨:** 3 本それぞれの検査対象と hold による欠落を insight に明記する。

- **親の時間・メモリ観測は効果の予測値にならない。** `s3-parent-notes.md:5–11` の 138.92 秒／wall 173 秒は inventory 単独、短い queue の一走であり、選択される固定 file・追加 reader test・直接実行 3 本を含まない。135 passed＋41 skipped と「148 node」も、収集後の展開数が同じでないことを示す。headroom も同時 user の使用量による一点観測である。**放置時:** login 完結性や短縮幅を過大・過小に見積もる。**推奨:** 同一 tip の縮小／全受入を同時期に測り、queue、admission、test、直接 gate の時間を分ける。

## 代案

初版は **静的に到達範囲を証明できない `output/insights/` の部分木を除外**する。とくに B5 の event prefix は先に全受入へ倒す。選択規則を広げる案として、test source に `docs/` または `output/insights/` を含む file 全体を選ぶと、静的な文字列検索では **82 file／全405 test file** になる。B5 のような test 内の変数連結は拾いやすくなるが、文字列を持たない import・fixture 経由の reader は残り、対象 file 全体の実行時間も未測定である。採用するなら受入集合の安全策ではなく、保守的な分類除外に加える検出力として扱う。

## scope 外候補

production 定数、fixture、manifest、subprocess を跨いで実 repo の読取先を追う共通 dependency inventory は、初版の単純な literal selector より広い実装になる。今回それを実装済みと扱わず、未解決の許可 prefix を全受入へ倒した上で別課題として測定・設計する。

## 総括

現 plan のまま `output/insights/**` を広く許可するのは危険である。B5 event のように実 repo を読む test があり、提案された literal 選択では漏れ得る。許可集合を狭め、(c) は実際に赤になる対象で確認し、fold 後の保証と性能効果はそれぞれ land の検査・同一 tip の実測として示すべきである。今回は指定どおり静的調査のみで、テストは実行していない。