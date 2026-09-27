# [T-2207] D1539 (動的入力の設定式を unresolved へ倒す) は字義どおりだと 715 セルが赤になり、この wave では実装しなかった

2026-09-27、dev-wave `dev-wave-t2207-closure-unresolved` (起点 local main `ad114fba0`、記録の commit 時 `cc2e9672a`)。
依頼の逐語は `verbatim/request.md`。段 1 brief・段 2 plan・段 3 相談 2 本・段 4 裁定は `verbatim/` にある。

## 1. 結論

- **D1539 は有効で、未実装のままである。[T-2207] は完了していない。**
- 止めた理由は、字義どおりの実装が既存テスト `test_define_sink_cross_product_has_no_unreviewed_ungated_member` に
  715 件の failure を出し、12 sink・715 セルのすべてを本題の範囲内で解消する案を、段 2 plan・段 3 相談 2 本のいずれも組めなかったためである。
  繰延べ台帳 12 entry や、呼び手を含む閉包証明器のような本題外の一般化は、本依頼の「これ以外の gate・検査・台帳・一般化の追加は scope 外」に当たる。
  S1 の flag 一致検査のように本題の一部と読める処置はありうるが (§4)、その対象は s1 の 57 セルに限られる。
  **到達不能を証明したから止めたのではない。**
- 依頼の (2) [T-2344]・(3) [T-734]・[T-733] の整理は、この wave では実行していない (§5)。

## 2. 実測 — 「18 セル」は 9/2 当時の数で、現行は 929 セルが同じ規則で到達不能に数えられている

対象は `orchestrator/tests/test_ccbench_spawn_sites.py` の `_sink_macro_reachability`。
現行は、sink の macro inventory (`source_macros`) が空でなければ、そこに無い macro を直ちに `proven-unreachable` にする。
設定式が関数の引数・自由変数に依存するか (既存の `_expression_depends_on_scope_parameter`) は、この分岐より後でしか見ない。

親が 2 通りで数えた (いずれも 2026-09-27、login、`PYTHONPATH=. python3 <job dir の probe>`、patch 追加 define は 61 個)。

1. **コード無変更の計算** (`verbatim/probe-predict.log`): buildcache / campaign の sink で、設定式が引数依存 (上記関数が真) かつ
   inventory が非空で、不在 macro が `proven-unreachable` になっているセルを数え、`unresolved` にした場合の行き先を既存の被覆・繰延べ台帳で振り分けた。
   **16 sink・929 セル。行き先は failure-unresolved 715 (12 sink)・既存の繰延べ台帳による deferred 214 (4 sink: b10 の 2 sink と t2187 probe の 2 sink)。**
2. **実編集** (`verbatim/probe-edit.log`): `_sink_macro_reachability` の `if source_macros:` の直前へ
   「buildcache / campaign で設定式が引数依存なら `unresolved`」を一時的に入れ、既存の分類関数をそのまま呼んだ。
   **failures は 0 → 715 (理由はすべて unresolved)。** 1 と一致した。編集は `git checkout --` で戻し、`git status --porcelain` が空であることを確かめた。

| sink (file:行) | kind | 現行の proven-unreachable → 実装後の行き先 |
|---|---|---|
| backoff_extended_sweep.py:348 / :1446 | buildcache / campaign | 60 / 60 → failure |
| backoff_profile.py:857 | buildcache | 59 → failure |
| backoff_repro.py:172 | campaign | 60 → failure |
| backoff_sweep.py:484 | campaign | 60 → failure |
| p3_s4_loop.py:2387 / :2604 / :2614 / :2639 | campaign / buildcache ×2 / campaign | 各 60 → failure |
| paper_story_a1_paired.py:7295 | campaign | 60 → failure |
| paper_story_a2_certification.py:3803 | campaign | 59 → failure |
| s1_direct_comparison.py:1281 | campaign | 57 → failure |
| b10_backoff_shape_sweep.py:3648 / :4474 | buildcache / campaign | 各 60 → deferred (既存台帳) |
| tools/pegasus/probes/t2187_adaptive_const_probe.py:3941 / :4334 | buildcache | 各 47 → deferred (既存台帳) |

file はすべて `orchestrator/campaign/` 配下 (最後の 2 行を除く)。行番号は起点 `ad114fba0` のもの。

**「18 セル」との関係:** D1539 と [T-2207] の本文が書く「18 セル」は、2026-09-02 の [T-2155] 時点 (patch 追加 define 22 個) の
s1 sink 1 本だけの数である (`output/insights/2026-09-02/t2155-closure-with-bindings/README.md`)。現行は define が 61 個で、s1 だけでも 57。
同じ日の D1502 は「同じ規則で落ちているセルは repo 全体に 900 件以上」と既に書いており、今回の 929 はこれと整合する。
当時の 18 は当時の測定として残る (規律 7)。

## 3. 12 sink の「動的入力」の実体 (段 2 plan と段 3 相談 A の照合、静的読解)

- 12 sink の多くは、引数で**値**は変わるが、genome の **macro 名**は同じ file の生成関数が固定している。
  既存の引数依存判定は構文上の判定なので、macro 集合の開放性の判定としては過剰である (plan 第 1 部)。
- 段 2 plan は「P3 の stock 経路 (`--reference-genome` の JSON) から任意の macro 名が入る」と書いたが、**誤りだった** (相談 A 所見 1)。
  `p3_s4_loop.py` の CLI は、この JSON の `flags` の鍵を `BACK_OFF`・`NO_WAIT_LOCKING_IN_VALIDATION`・`NO_WAIT_OF_TICTOC`・`WAL` の 4 つと完全一致させる
  (起点 `ad114fba0` の 3594〜3606 行、親が現物を確認)。
- **今回、未閉包の具体的な入力列を示せたのは S1 の注入口だけである** (相談 A 所見 2、親が現物を確認)。他の sink についても、呼び手・policy を含めた閉包を証明したわけではない。`s1_direct_comparison.py` の `run_role` は `prepare_cell_fn` を引数で差し替えられる
  (1046〜1060 行、docstring は「subprocess 無しの positive control 用」)。返却 evidence の照合は freeze cell 側の `variant.flags` から作った期待 digest と
  返却物の一致を見るが (1210〜1225 行付近)、返却された `prepared.genome` の全 flag と freeze cell の flag の一致は見ない。
  したがって、差し替えた callable が別の patch macro を足した genome を返すと、静的検査の `proven-unreachable` と実行時の照合のどちらにも掛からない。
  **これは静的検査の穴であって、成果物 (certified 選択・レポート・台帳) の値が変わったという実証は無い。** CLI の通常経路は既定の `prepare_cell` を使う。

## 4. 比べた択 (段 2 plan 第 2 部、段 3 で攻撃済み)

| 択 | 帰結 | 判定 |
|---|---|---|
| A 字義どおり | 929 セルが移り、715 が failure。既存テストが赤 | 全緑に届かない |
| B A + 12 sink を繰延べ台帳へ | failure 0。台帳 12 entry と lineno pin が増え、以後の対象 file の編集ごとに追随が要る | 依頼が除いた「台帳の追加」 |
| C 動的の判定を絞る (呼び手・policy・注入口の閉包証明) | 閉包を示せた sink だけ残る。安全に外せる件数は未確定 | 依頼が除いた「一般化の追加」 |
| D 別分類で数え failure にしない | 受理集合が狭まらない | D1539 (受理集合を狭める向き) に反する |
| E この wave では実装しない | コード変更なし | **採用** (一時停止としてのみ) |

scope 内で D1539 に忠実かつ既存テストを赤にしない択は、plan・相談 2 本のいずれも組めなかった。
相談 A は「S1 の返却 genome と freeze cell の flag 一致検査のような処置は本題の一部と読める余地がある」と指摘したが、
S1 で処置の対象になるのは 57 セルで (その検査で分類上解消することは実装・実測していない)、残る 11 sink・658 セルにも処置が要る。

**択 E への最強の反対論:** D1539 は既に局所修正を命じ、2026-09-26 の持ち越し整理も実際の判定への影響を理由に [T-2207] を残した。
実装を延ばすと、S1 注入口の静的な穴が温存される。

**再開の受入条件:** D1539 の判定変更と同じ wave で、赤になる 12 sink それぞれの処置 (実際の gate 被覆、生成関数による macro 名の固定を検査が読める形にする、
S1 は返却 genome と freeze cell の flag 一致の検査) を本題として行うことが認められること。テスト期待値の反転・緩和・skip、理由のない台帳登録で緑にすることは規律 2 により不可。

## 5. 依頼 (2)(3) と [T-733] を実行しなかった理由

依頼 (14:28 JST 起動) の (2) [T-2344] 次段・exact-85/96 の再走査と撤去、(3) [T-734] 全 certified sink への source gate、[T-733] の 69 module の整理は、
同じ日の D2260 項 2 (07:52 JST 記録) が名指しで止めた対象と一致し、向きが逆である。D2260 項 2 は、ユーザーが反対意見 (続けるべき) を併記した提示を見て
「止める」を選び、exact-85 の歴史収載の扱いも行わず、撤去する wave も起こさないと書いている。

依頼の方が後なので、依頼がユーザーの最新の意思である可能性は否定できない (相談 B 所見 4)。依頼の起動直後の ListAgents では、開始から 3〜6 分の背景 session が 13 本あり (`verbatim/listagents-excerpt.md`)、
依頼文は D2260 以前の提案文の写しの可能性もあるが、出所は確かめられなかった。**どちらがユーザーの意思かを AI が推測で決めることはせず**、
撤去を含む向きを推測で実行しない。この wave では触らず、ユーザーに 1 問で確かめる。[T-733][T-734][T-2344] は D2260 で持ち越しから外れたままである。

## 6. 工数

codex 子 6 本 (段 2 plan 1、段 3 相談 2、記録の事実確認レビュー 1 (NO-GO・must-fix 2・should 1)、焦点再レビュー 2 巡 (1 巡目 NO-GO・新規 must-fix 1・should 1、2 巡目 GO)。所見はすべて採用。いずれも read-only・medium・受理)、Claude 子 1 本 (sonnet、wave 運用の記憶の要点抽出、read-only)。
実装面の変更は 0 (Codex author 0)。変異 matrix は実装差分 0 のため免除 (DW-S04)。

## 7. 逐語の正規化 (可逆、可視文字不変)

`git diff --check` の行末空白に当たった 2 file だけ、該当行末の半角空白 2 個を除いた。他の bytes は原文のまま。
復元はその行末へ半角空白 2 個を戻す。

| file | 行 | 原文 sha256 | 原文 bytes → 収載 bytes |
|---|---|---|---|
| `verbatim/s7-review-r1.md` | 11 | `5323a67f1fbe0bc9992f614d18bf599acf5ea72e2ef08945d3012e977d9a3e8a` | 3655 → 3653 |
| `verbatim/s7-focus-f1.md` | 19 | `aa7dc925cfcac93aebfc386a6124f613a8e7f8cba147f0d2e33c22a2689afcb4` | 4723 → 4721 |
