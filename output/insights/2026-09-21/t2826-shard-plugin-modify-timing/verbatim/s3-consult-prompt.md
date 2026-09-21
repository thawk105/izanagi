単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-shard-plugin-modify-timing

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/s1-brief.md — 親の段 1 brief (新事実 N1〜N5、(P1)〜(P5))。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/T-2826-origin.md — 依頼の逐語 (起動引数と起票本文)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/verbatim/D1936-item35.md、D2148-item6.md、D2185.md、D2200-items4-5-6-7.md — 既裁定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/verbatim/T2617-README-s3.2-s4.md — 既存被覆 (単独 process の plugin 費用と短縮の手の判定)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-shard-plugin-modify-timing/output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md — 一次資料 (§結論 3・5、§1.1、§3.1、§4、§5 (b)、§8)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/probe/t2817_probe_plugin.py と t2817_collection_stage_probe.sh と t2817_collection_stage_aggregate.py — 前 wave の probe 実体 (本 wave の雛形)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-shard-plugin-modify-timing/tools/acceptance_shards.py — shard plugin (`_canonical_item`、`records_from_items`、`allocate`、`_components`、`pytest_collection_modifyitems`、`pytest_collection_finish`、`_worker_payload`、`_controller_state`、`pytest_sessionfinish`)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-shard-plugin-modify-timing/orchestrator/tests/conftest.py — collection 期の hook。必要な範囲だけ grep で引く (`pytest_collection_modifyitems` の wrapper、`_validate_real_repo_shard_state`、`_strip_real_repo_loadgroup_suffix`、`_reorder_acceptance_items_by_duration`、`_ensure_flaky_test_holds_loaded`、`_start_early_memo_job`、`_wait_early_memo_job`、`_run_memo_prewarm_barrier`、`pytest_collection_finish`、`pytest_configure_node`、`_acceptance_reordering_enabled`)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-shard-plugin-modify-timing/orchestrator/tests/real_repo_receipt_memo.py — worker の早期 memo 待ち (`get(early_job=...)`、`.pending` の poll 間隔)。必要な範囲だけ。読めなければ即停止。
- /home/SFC/tanab/.local/lib/python3.10/site-packages/pluggy/ (1.6.0、`_hooks.py` の `HookImpl` と `_add_hookimpl` の並び、`_callers.py` の `_multicall`)、同 dir の `_pytest/main.py` (`perform_collect`、`genitems`)、`_pytest/pathlib.py` 不要、python3.10 の `pathlib.Path.resolve` (= `os.path.realpath` + `stat`)、`xdist/remote.py` (worker の collection_finish 送信) — 実行時の hook 順と区間の境界。必要な範囲だけ。読めなければ即停止。

## 目的

これは自分たちの受入 test 基盤の診断設計レビューである。[T-2826] 診断 wave の段 3 相談 (read-only、reasoning=medium) として、
**親の brief 自身を検査対象**とし、brief の新事実 N1〜N5・(P1)〜(P5)・前提実測の読み取りとその一般化・依頼との整合を点検し、
計算ノード job を投げる前に直すべき欠陥だけを根拠 (file:line または brief の節名) 付きで指摘せよ。
brief を守る側に立つな。見つからなければ「見つからない」と書け。短縮の実装は本 wave の範囲外 (D1936 項 35) なので、
短縮案の良否ではなく「関数別の内訳が正しく閉じるか」「worker 側の短縮量と `pre` の変化を別々に正しく測れるか」を点検せよ。

## 背景 (要点。資料を読んで確かめること)

- T-2817 (一次資料) は同 job・同 node の段階載せで、shard plugin を載せた段 (S2) に worker の modify 複合区間 (最後の `pytest_itemcollected` → `pytest_collection_finish` の probe wrapper 入口) が約 45 秒現れ、process 群の sys 時間 80 → 2108 秒、Lustre `md_stats:intent_lock` 5.2 M → 60.9 M を観測した。内部の関数別計時はしておらず、「shard plugin が全 item に 2 回掛ける `Path(item.path).resolve()` が Lustre 上で kernel 時間になる」は有力な解釈に留めた。早期 memo prewarm (44〜54 秒) は controller で並走し、`pre` は worker 側と memo の長い方で決まる構造 (§5 (b))。
- 本 wave の依頼: この区間を関数別に計時し S2 / S3 形の段階載せで内訳を閉じる。`pre` ≈ max(worker 側, 早期 memo) を事前登録し、worker 側の短縮量と `pre` の変化を別々に測る。短縮の実装は含めない。
- 親の設計 (brief (P1)〜(P5)): module 属性の差し替えによる観測 wrapper で関数別の wall / user / sys を worker ごとに取り、閉包基準で残差を判定。反実仮想 1 条件 (probe 内だけ、shard plugin の resolve を path 文字列で memo 化) で worker 側の短縮量と `pre` の変化を測る。

## 2 つのレンズを 1 本で担え

## レンズ A — 計時・帰属・反実仮想の設計 (実効性)

1. **wrapper が実際に効くか**: shard plugin の `pytest_collection_modifyitems` は `records_from_items` / `allocate` / `_canonical_item` / `_records_payload` / `_digest` を module global 経由で呼ぶか (file:line)。hook impl 自体は plugin 登録時に pluggy へ関数 object として登録されるので、module 属性の差し替えでは hook の境界を取れない — pluggy 1.6.0 の `HookImpl.function` を委譲 wrapper に差し替える案は `_multicall` の呼び方 (argnames、wrapper / hookwrapper の区別) と整合するか。conftest の modify wrapper (`wrapper=True, tryfirst=True`、generator) の前段・後段の境界は何で取れるか (前段の先頭 `_ensure_flaky_test_holds_loaded`、後段の先頭 `_validate_real_repo_shard_state` を差し替えて境界にする案の穴)。conftest module object を probe から特定する方法 (pluginmanager 登録名・`__file__`) と、差し替えの時点 (初期 conftest の読込は configure より前か) を示せ。
2. **`Path.resolve` だけの計時**: `_canonical_item` 実行中に限って resolve の回数と wall を取る方法 (a) `pathlib.Path.resolve` を class 属性で包み flag で限定、(b) `acceptance_shards.Path` を memo なしの計時 subclass に差し替え — のどちらが shard plugin の他の `Path` 利用 (`Path.cwd().resolve()`、`_plugin_spec`、`_is_within`、`relative_to`) と型・結果を変えないか。conftest の growth hold の `Path(item.path).resolve()` を混ぜない方法。計器の自己費用 (呼出し 5 万回 × perf_counter) の見積り。
3. **user / sys の帰属**: `os.times()` は process 全体の CPU で、execnet の IO thread や probe 自身の thread が区間中に CPU を使うと混ざる。`resource.getrusage(resource.RUSAGE_THREAD)` (Linux、python3.10) で main thread に限る案の方が正しいか。区間の境界で 1 回ずつ呼ぶだけ (呼出しごとではない) にする必要性。
4. **閉包の網羅**: 「最後の `pytest_itemcollected` → cf 入口」には brief の列挙以外に何が入るか — 最後の module の `pytest_collectreport`、`perform_collect` の `pytest_collection_modifyitems` の他 impl (pytest の `mark` plugin の keyword / mark deselect、terminal、junitxml、xdist worker 側)、`pytest_deselected` (約 2.2 万 item) の各 impl、`pytest_collection_finish` の probe wrapper より外側 / 先に呼ばれる impl。hook の登録順 (`-p` plugin は初期 conftest より先に登録) を踏まえ、閉包に必要な境界点を過不足なく列挙せよ。閉包基準 (残差 median ≤ max(2 秒, 5 %)) は妥当か。
5. **反実仮想の正しさ**: resolve を path 文字列で memo 化した結果は非 strict の resolve と同値か (item.path の型は `Path` か `str` か、同じ file に複数の表記がありうるか、symlink alias の重複検出の意味 = T-2617 §4 の「不可」理由)。`records_digest` / `selected_digest` / 選択集合の byte 一致を同 job の無改変セル (S3-u) と照合する手段 (controller の report.json・worker payload のどの field) を file:line で示せ。memo が conftest や他の resolve に漏れない限定方法。
6. **`pre` の構造の測り方**: M (早期 memo 終了 epoch) を controller の memo thread の終了で取る案と、`.pending` の unlink 時刻の差。worker は `real_repo_receipt_memo.py` の `get(early_job=...)` で `.pending` を 10 ms 間隔で poll する — S3-cf で worker が memo より先に cf に着くと 48 worker の poll が Lustre metadata 負荷を足し、memo 自身を遅らせうる。これが事前登録の予測 (pre(S3-cf) ≈ max(W_w, M) + ε) の読みをどう歪めるか、M を各セルで測るだけで足りるか。ε ≤ 2 秒の根拠 (poll 間隔、controller の通知、junit timestamp の起点)。
7. **観測者効果の対照**: S3-u (T-2817 と同じ計器だけ) と S3-f の比較で計器の影響を割る設計は、反復 2・順序反転で足りるか。T-2817 の S3 (44.68 / 44.79) との比較は tip 差 (ledger +434 行、選択集合が変わる) を踏まえ参照に留めるべきか。
8. **セル構成と順序**: (P2) の 6 条件 × 2 走 (約 11〜13 セル、1 セル約 65 秒) で、段階載せとして何が言え何が言えないか。S1 と S2-f は必要か (依頼の「S2 / S3 形」との対応)。順序反転で page cache・Lustre 負荷の時間交絡を割れるか。

## レンズ B — 依頼との整合・既裁定・scope・親の読み取りの誤り (過剰と逸脱)

1. **反実仮想セルは scope 内か**: 起動引数は「短縮の実装は含めない」「本題の計測だけ」と言い、同時に「worker 側の短縮量と pre の変化を別々に測る」とも言う。probe 内の反実仮想 (repo の code を変えない) で短縮量を測ることが (a) 許される、(b) 許されない (測るのは関数別の時間だけで、短縮量は関数別時間から読む)、(c) 条件付き、のどれか。(b)/(c) なら依頼の「別々に測る」をどう満たすか。
2. **依頼が名指しした量の落ち**: `records_from_items` / `_canonical_item` の `Path.resolve()` (全 item に 2 回) / `allocate` / 選択 / conftest の `_validate_real_repo_shard_state` / S2・S3 形 / `pre` ≈ max の事前登録 / 別々に測る / T-2825 と区間を重ねない / 標本の時点を固定。brief が落としている、または読み替えている要素を示せ。
3. **過剰**: brief に「仮想リスク向けの gate・検査・台帳・一般化」や「短縮策の設計・効果見込み」へ滑る要素、依頼に不要なセル・計器があれば指摘せよ。
4. **二重に数えない**: T-2617 §3.2 (単独 process の plugin 費用 +1.74 user CPU 秒)、T-2817 §3.1 / §4 (Δ21 = +45.9 秒、sys、intent_lock)、D2185 (早期 memo) と本 wave の測定量の重なり。本 wave が新しく測ると言える量を限定せよ。T-2617 §4 の判定 (resolve の字句化は不可、2 回目の置換は採らない、根拠は「1 秒級」) を本 wave の値でどう扱うべきか (覆す提案をしない範囲で、何を記録してよいか)。
5. **標本の時点**: 計測 tip を `d99c556df` に固定し、as-of を開始 gate 時刻に置く brief の案で足りるか。T-2825 の land (所要台帳の変更) 後に走る本 wave の最終受入 (post-claim merge で別 tip) を参照に使ってよいか・どう限定するか。
6. **外乱**: Lustre MDS は共有。他 wave の受入 (collection 段で同じ resolve を 48 並列 × 3 node で行う) がセル時間帯に重なった場合の検知 (受入共有 root の session 作成時刻の事後照合) と再計測の方針 (brief (P5)) に穴はないか。検知できない外乱 (他ユーザーの job) の書き方。
7. **規律 2 / 規律 7 / DW-O19**: probe と反実仮想が受理集合・hold・verifier・checkout に触れないこと (S2 / S3 の shard spec の `session_root` は job dir、report.json は create-only、pyc・`.pytest_cache`・memo cache・`output/` への書込み経路) を確認し、破る可能性のある操作を file:line で挙げよ。

## 出力形式 (この順で、見出しはこのまま。見出しはすべて `##` で書き、`###` を使わない)

## 所見

番号付き。各所見に **主張** / **根拠** (file:line か brief の節名) / **親の記述との差** / **重大度** (高・中・低) / **修正案** (1〜3 行)。
重大度「高」は「このまま実測すると計算ノード job 1 本 (queue 待ち + 15〜30 分) が無駄になる、または結論が誤る、または依頼との整合が崩れる」だけに付けよ。

## 反実仮想セルの判定

(a) / (b) / (c) のどれかと理由を 3〜6 行。(b)/(c) なら代わりの測り方。

## 測定行列と計時点の修正版 (差分だけ)

brief (P1)(P2) に対する追加・削除・置換を箇条書きで。増やすセル・計時点は理由と概算所要を付けよ。

## 見つからなかったこと

探したが見つからなかった欠陥を短く列挙 (何を grep したか)。

## 総括

3〜6 行。高の件数、実測に入ってよいか (GO / 修正後 GO / NO-GO)、最重要の 1 件。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 制約

- sandbox は read-only。書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を上の形式どおり書いて終われ (無出力が最悪)。
