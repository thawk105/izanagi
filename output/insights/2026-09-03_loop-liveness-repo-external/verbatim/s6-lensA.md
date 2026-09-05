## 総括

- **real** — 静的レビューでは must-fix はありません。NFKC prefilter は AST 発見の必要条件を保ち、4 module の guard も完全入力時の assertion・受理条件を減らしていません。`_DRIVER_CONTRACTS` と直接 index も維持されています。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:133`, `orchestrator/tests/test_p3_exploration_namespace.py:389`, `orchestrator/tests/test_p3_exploration_namespace.py:483`
- **real（nit）** — `PYTEST_CURRENT_TEST` を継承した素 runner だけは、`skiputil.skip()` が `pytest.skip.Exception` を投げ、追加された `except Skip` では捕捉できません。通常の pytest 実行と通常の素 runner は正しく分類されますが、この混成経路は plan v2 の文言を完全には満たしません。根拠: `orchestrator/tests/skiputil.py:28`, `orchestrator/tests/test_b10_extended_figure_provenance.py:937`, `orchestrator/tests/test_plot_b10_extended_backoff.py:404`
- テスト実走はしておらず、緑は主張しません。

## 1 NFKC prefilter の必要条件

- **refuted — whole-source NFKC が AST-positive な識別子を取りこぼす**。AST 述語が認識するのは `ast.Name.id` または `ast.Attribute.attr` が ASCII の `exploration_campaign_layout` になる場合だけです。識別子 token の NFKC がこの値になるなら、構文上の token 境界は空白・ASCII punctuation などで遮られ、source 全体の NFKC にも同じ連続部分文字列が残ります。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:56`, `orchestrator/tests/test_p3_exploration_namespace.py:84`, `orchestrator/tests/test_p3_exploration_namespace.py:140`
- **refuted — 行継続やコメントで marker を分断した AST-positive 形がある**。明示行継続は識別子 token 自体を分割できず、コメントも識別子内部には置けません。dot と識別子の間を改行しても識別子本体は source 中に連続して残ります。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:56`, `orchestrator/tests/test_p3_exploration_namespace.py:64`
- **refuted — UTF-8 以外の encoding 宣言が prefilter と AST の解釈を分岐させる**。bytes は最初に固定 UTF-8 で `str` 化され、その同じ `str` が正規化判定と `ast.parse` の双方へ渡ります。実 bytes が非 UTF-8 なら prefilter 前に失敗し、silent miss にはなりません。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:139`, `orchestrator/tests/test_p3_exploration_namespace.py:147`
- **refuted — BOM 付き AST-positive driver が silent miss になる**。`utf-8` 読みでは BOM が U+FEFF として残りますが、marker があれば parse 経路へ進んで従来同様 fail-closed になります。marker がない BOM file の構文検査を省く点は、一般の marker-negative file と同じ、裁定済みの残存構文被覆穴です。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:139`, `orchestrator/tests/test_p3_exploration_namespace.py:145`
- **refuted — 2 個の隣接文字列リテラルが AST discovery 対象になる**。AST が定数を連結しても `_call_name()` は定数や `getattr(...)` を認識せず、`Name` / `Attribute` の call 名しか返しません。したがって prefilter 固有の取りこぼしではありません。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:56`, `orchestrator/tests/test_p3_exploration_namespace.py:84`
- **real — false positive は安全側**。コメントや文字列中の marker、または whole-source NFKC が余分に作った marker は AST parse を増やすだけで、最終的に `_is_campaign_root_creator()` が除外します。コメントだけの負例も bounded fixture にあります。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:147`, `orchestrator/tests/test_p3_exploration_namespace.py:541`, `orchestrator/tests/test_p3_exploration_namespace.py:585`

成果物影響: 現行 7 driver の発見集合・契約受理集合・参照は変わらず、変わるのは marker-negative file の走査コストだけです。

## 2 新 driver 登録漏れの検出可能性

- **refuted — 現行 driver の prefilter 取りこぼしで両辺が消え、緑になる**。発見名を独立した 7 件 literal tuple と比較しているため、現行 driver が 1 件でも消えれば registry exact とは独立に赤になります。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:514`, `orchestrator/tests/test_p3_exploration_namespace.py:589`
- **refuted — 正常な新 driver の登録漏れが緑になる**。AST-positive な新 driver は前節の必要条件により発見集合へ入り、7 件 pin と、契約集合との完全一致の双方を壊します。pin を新 driver に合わせても契約を足さなければ registry exact が赤です。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:155`, `orchestrator/tests/test_p3_exploration_namespace.py:514`, `orchestrator/tests/test_p3_exploration_namespace.py:589`
- **real — bounded fixture は恒真ではない**。同じ production helper を prefilter 有無で呼ぶ一方、期待集合は独立した literal です。さらに全角 `ｅ` の raw source 不一致と NFKC 後一致を個別に固定しており、生 source prefilter への退行を殺します。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:555`, `orchestrator/tests/test_p3_exploration_namespace.py:566`, `orchestrator/tests/test_p3_exploration_namespace.py:572`, `orchestrator/tests/test_p3_exploration_namespace.py:580`
- **real（裁定済み残存穴）** — bounded fixture は Unicode 全域の形式証明ではなく、marker-negative file の一般構文検査も行いません。ただし AST-positive 識別子に対する必要条件は実装から静的に成立しており、新 driver の登録漏れ穴にはなっていません。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:140`, `orchestrator/tests/test_p3_exploration_namespace.py:146`

成果物影響: 新しい AST-positive driver を追加して契約登録を忘れた場合、certified な driver 受理集合は更新されず、テストが赤になって成果物への編入を阻止します。

## 3 guard が検査を弱めていないか

- **refuted — ENOTDIR/ELOOP を欠落として skip する**。4 module とも `os.stat()` の `FileNotFoundError` だけを捕捉しています。途中 component が file の場合の `NotADirectoryError`、symlink loop の `OSError`、権限エラーは捕捉されず fail-closed です。根拠: `orchestrator/tests/test_t189_oracle_wiring_slice.py:62`, `orchestrator/tests/test_t1434_t1222_science_slice.py:64`, `orchestrator/tests/test_b10_extended_figure_provenance.py:124`, `orchestrator/tests/test_plot_b10_extended_backoff.py:42`
- **refuted — 完全入力環境で assertion が減る**。guard は欠落 tuple が空ならそのまま復帰し、既存 assertion や verifier 呼出しを迂回しません。減少は **0 件 / 0 node** です。根拠: `orchestrator/tests/test_t189_oracle_wiring_slice.py:119`, `orchestrator/tests/test_t1434_t1222_science_slice.py:124`, `orchestrator/tests/test_b10_extended_figure_provenance.py:324`, `orchestrator/tests/test_plot_b10_extended_backoff.py:194`
- **refuted — requirements exact test が guard factory と同じ値を比較する恒真形**。t189 と t1434 は artifact-derived factory に対して test-owned literal、B-10 provenance は `HASHES` に対して `SPECS/_paths`、B-10 plot は checked-in provenance に対して独立した group/campaign literal から期待集合を作っています。根拠: `orchestrator/tests/test_t189_oracle_wiring_slice.py:48`, `orchestrator/tests/test_t189_oracle_wiring_slice.py:132`, `orchestrator/tests/test_t1434_t1222_science_slice.py:49`, `orchestrator/tests/test_t1434_t1222_science_slice.py:409`, `orchestrator/tests/test_b10_extended_figure_provenance.py:120`, `orchestrator/tests/test_b10_extended_figure_provenance.py:884`, `orchestrator/tests/test_plot_b10_extended_backoff.py:37`, `orchestrator/tests/test_plot_b10_extended_backoff.py:330`
- **real — reader-A node は 1 file だけに束縛される**。3 系統の reader mutation test は artifact の reader-A output だけを stat/read し、残り 20 件を要求しません。専用対照もあります。根拠: `orchestrator/tests/test_t1434_t1222_science_slice.py:343`, `orchestrator/tests/test_t1434_t1222_science_slice.py:367`, `orchestrator/tests/test_t1434_t1222_science_slice.py:391`, `orchestrator/tests/test_t1434_t1222_science_slice.py:477`
- **real — symlink 負例は無 guard**。`test_physical_rejects_symlink_component` は直接 symlink fixture を verifier へ渡しており、外部内容 guard は付いていません。根拠: `orchestrator/tests/test_t1434_t1222_science_slice.py:508`
- **real — skip 理由は測定不能と緩和を区別できる**。理由は「pinned external inputs unavailable」、欠けた relative path、完全入力なら全 assertion が走る旨を含み、pytest/素 runner とも PASS ではなく SKIP に分類されます。根拠: `orchestrator/tests/test_t189_oracle_wiring_slice.py:72`, `orchestrator/tests/test_t1434_t1222_science_slice.py:82`, `orchestrator/tests/test_b10_extended_figure_provenance.py:142`, `orchestrator/tests/test_plot_b10_extended_backoff.py:60`

成果物影響: 完全入力時の certified selection・材料レポート・試行台帳の値、受理集合、参照は不変です。不在時は受理へ進まず「測定できなかった」という SKIP だけが残ります。

## 4 素の runner の skip 分類

- **real — catch 順は正しい**。両 `_run()` と先例はいずれも `except Skip` を一般 `Exception` より前に置いています。根拠: `orchestrator/tests/test_b10_extended_figure_provenance.py:946`, `orchestrator/tests/test_plot_b10_extended_backoff.py:413`, `orchestrator/tests/test_plot_backoff_ci.py:450`
- **real — 通常の素 runner では skip-only が rc=0**。`PYTEST_CURRENT_TEST` がないため `skiputil.skip()` は `Skip` を投げ、`skipped` だけが増え、`failed == 0` なら 0 を返します。根拠: `orchestrator/tests/skiputil.py:28`, `orchestrator/tests/test_b10_extended_figure_provenance.py:940`, `orchestrator/tests/test_b10_extended_figure_provenance.py:953`, `orchestrator/tests/test_plot_b10_extended_backoff.py:407`, `orchestrator/tests/test_plot_b10_extended_backoff.py:420`
- **real（nit） — pytest 環境を継承した素 runner では分類が食い違う**。`PYTEST_CURRENT_TEST` が残った subprocess では `pytest.skip.Exception` が投げられますが、runner はローカル `Skip` と通常の `Exception` しか捕捉しないため、skip-only が uncaught 非 0 になり得ます。先例にも同じ限界があります。根拠: `orchestrator/tests/skiputil.py:29`, `orchestrator/tests/test_b10_extended_figure_provenance.py:946`, `orchestrator/tests/test_plot_b10_extended_backoff.py:413`, `orchestrator/tests/test_plot_backoff_ci.py:450`

成果物影響: certified な値・受理集合・参照は変わりません。影響は、pytest から環境変数を継承して直接 runner を起動した場合の終了分類が `SKIP/0` ではなく uncaught/non-zero になることだけです。

## 5 spec からの逸脱

- **refuted — 登録簿 JSON または全走査メタ gate を追加した**。worktree status は指定 5 file の変更だけで、新規 file はありません。追加物はいずれも module-local helper/test です。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:133`, `orchestrator/tests/test_t189_oracle_wiring_slice.py:48`, `orchestrator/tests/test_t1434_t1222_science_slice.py:49`, `orchestrator/tests/test_b10_extended_figure_provenance.py:120`, `orchestrator/tests/test_plot_b10_extended_backoff.py:37`
- **refuted — `_DRIVER_CONTRACTS`、`_driver_contract`、registry exact を変更した**。3 箇所の本体は差分外で、直接 index と発見集合完全一致が維持されています。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:389`, `orchestrator/tests/test_p3_exploration_namespace.py:483`, `orchestrator/tests/test_p3_exploration_namespace.py:589`
- **refuted — 既存 assertion の期待値を変更した**。既存 assertion の削除・RHS 変更はありません。t1434 の reader test は入力 path の取得元を checked-in artifact へ合わせましたが、parser の期待と拒否条件は不変です。根拠: `orchestrator/tests/test_t1434_t1222_science_slice.py:343`, `orchestrator/tests/test_t1434_t1222_science_slice.py:361`
- **refuted — 揮発 payload を期待値へ焼き込んだ**。追加 literal は現在の driver 名、pinned relative path、固定 campaign/group reference であり、内容 payload や実行時観測値ではありません。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:514`, `orchestrator/tests/test_t1434_t1222_science_slice.py:409`, `orchestrator/tests/test_b10_extended_figure_provenance.py:884`, `orchestrator/tests/test_plot_b10_extended_backoff.py:330`
- **real（nit） — plan v2 の「`pytest.skip.Exception` で非 0 にしない」は混成環境で未完**。通常の二経路は満たしますが、前節の環境継承形は残ります。根拠: `orchestrator/tests/skiputil.py:29`, `orchestrator/tests/test_b10_extended_figure_provenance.py:946`, `orchestrator/tests/test_plot_b10_extended_backoff.py:413`

成果物影響: spec の主要編集面と成果物の受理集合・参照は不変です。唯一の逸脱は fail-closed な runner 終了分類で、成果物内容は変えません。

## must-fix 一覧

- なし。

## nit 一覧

- **real** — pytest 実行中に subprocess として素 runner を起動し、`PYTEST_CURRENT_TEST` を継承した場合の `pytest.skip.Exception` を分類できません。`_run()` 開始時に素 runner 用として当該環境変数を除くか、pytest の skip 型も明示的に分類する回帰テストを加える余地があります。根拠: `orchestrator/tests/skiputil.py:28`, `orchestrator/tests/test_b10_extended_figure_provenance.py:946`, `orchestrator/tests/test_plot_b10_extended_backoff.py:413`
- **real（裁定済み残存事項）** — marker-negative campaign file の一般構文検査は prefilter により行われません。これは plan v2 が受け入れた被覆損失で、今回実装の逸脱ではありません。根拠: `orchestrator/tests/test_p3_exploration_namespace.py:140`, `orchestrator/tests/test_p3_exploration_namespace.py:146`

両 nit とも certified な選択結果・材料レポート・試行台帳の値、受理集合、参照を変更しないため、must-fix には分類していません。