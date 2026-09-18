# 段 4 裁定 — [T-2710][T-2273] 段 2 plan と段 3 の 2 レンズに対する親の裁定 (plan v2、事前登録)

裁定日時: 2026-09-18 11:10 JST (date 実測)。対象: `s2-plan.md` (codex read-only、受理 rc=0)、`s3-lensA.md` (計測設計)、`s3-lensB.md` (解釈・裁定パッケージ)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: wave 開始後の新規は T-2724 (freeze g1 chain と t080 receipt live scan) 1 件で、本 wave の裁定 (第 22 回 項 3) を変えない。

## 所見の裁定表

| # | 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|---|
| A-M1 | B/C の変更を `pytest_collection_finish(trylast)` に置くと、xdist `remote.py:256-262` が `session.items` を controller へ送った後になる | real (親も現物で確認: `WorkerInteractor.pytest_collection_finish` は通常 impl、`-p` plugin より後に登録されるので LIFO で先に呼ばれる) | 採用 | 変更は worker の **`pytest_collection_finish(tryfirst=True)`**。controller 側で `pytest_xdist_node_collection_finished(node, ids)` を hook して各 worker から受信した ids の順を記録し、B の意図順と一致することを確認する |
| A-M2 / B-M3 | `max(L, D/48)+F` は下限 model。A の実測 wall から引くと相方まで改善に算入 | real | 採用 | A にも同じ式を当て `W_A_model` を出す。候補との差は model 同士で示し、`W_A − W_A_model` を残差として併記。「実装すれば X 秒」は書かない |
| A-M3 | 観測 overhead を未実測の限界にするだけでは本体/固定費の優劣を決められない | real (部分) | 採用 (限定) | runner が計算ノードで単価 (monotonic 取得・dict 追記・JSONL 書出) を microbench し、通過回数・採録数・bytes・flush 所要を記録して感度幅 H を出す。M node 内の wrapper は 1 node あたり ≤ 15 span、controller の report 記録は全 node 分 (≈12k 件) だが in-memory 追記のみ。結論が H の幅で反転する場合だけ観測 on/off の対比較を追加する (既定では追加しない) |
| A-S1 | replica の D357 適合と実受入への適用は別判定 | real | 採用 | 歴史照合は記述的診断 (min–max 包含 I、percentile、中央値比) と固定。「受入 shard-0 の値」とは呼ばず「replica shard-0 の同一 tip 反復」と書く。実受入形 ×3 は本 wave の予算に入れない (plan の限定を維持) |
| A-S2 | replica と実受入の I/O 条件差 | real | 採用 | runner は **TMPDIR を設定しない**・**`--basetemp` を渡さない** (受入 child = `tests` task の env 継承と同じ既定にする)。走前に `tempfile.gettempdir()`・その fstype・既存 `pytest-of-<user>` dir・空き容量・shared base の実 path を記録し、走後に残骸を記録する。argv/env/interpreter/plugin 集合を JSON に残す |
| A-S3 | Latin square は加法的効果の均衡化であって完全補正でない | real | 採用 | job 1 は S1,S,S1,S,S1,S の交互。表記は「均衡化」に限定し、位置・host を併記 |
| A-S4 | B は初期相方の軽量化と tail 短縮を分ける | real | 採用 | JSONL から最長 node の worker の全 unit 列 (初期 2 unit、3 個目以降) を出す。initial 追加配布は pending ≤ 2 の worker だけ (`loadscope.py:330-336`) |
| A-S5 | 母集団・完走状態の統一 | real | 採用 | insight の表は母集団 (n) と定義を各表に書く。95 session 表の worker 49 は `unobserved` entry |
| B-M1 | 固定費の帰属 (shared base の atexit 削除、session 層の項) | real | 採用 | node / session / 残差 の 3 層で表記。追加観測: `_T080SharedBases.close` の所要 (wrapper)、controller の sessionstart / 各 worker の collection finish (xdist hook) / 最初と最後の test / sessionfinish / subprocess の外側 wall。分けられない項は「未分離」と書く |
| B-M2 | 2+3 分割は同一複製での正例→変異後再検証を失う | real | 採用 | 裁定パッケージで「独立 2 node 分割 = 検出集合を縮める案」と明記。連続性を保つ包装 (同 root・同 process・同順) は並列化利得なし。model は独立分割にだけ適用し、その前提を表に書く |
| B-M4 | pairing の判定を「10% 未満」「3/3 同符号」だけで決めない | real | 採用 | 下の「事前登録: 判定と報告の規則」に固定 |
| B-S1 | base key は 5 種 (7/1/1/1/1) | real (brief の「f28 / g7 は別 key」は粗い) | 採用 | brief 訂正表へ。S1 は既定 key 1 種、S は 5 種を各 1 回 build |
| B-S2 | 縮約は「wall に効かない」だけを理由にしない | real | 採用 | 3 点併記 (床は下がらない / node 秒減 ≠ 資源節約 / 別 shard への利益は未測定)、失うもの = 3 欠陥型の stub-free 検出 |
| B-S3 | 既却下案 (D2068) と今回の観測対象を変更内容で区別 | real | 採用 | 裁定パッケージに区別表を置く |
| B-S4 | 裁定表の追加欄 (失うもの / 300 秒目標との関係 / 今回求める裁定 / 後続費用と終了条件 / 復旧) | real | 採用 | README §9 の表の列にする。4 行は排他でなく「今回どこへ投資するか」の択一と明記 |
| A-N1 / B-N1 | env 名・verify 回数 (5/2/2/1)・例外最長 node (`test_historical_oracle_nonadapter_reaches_current_semantics`) は plan が訂正済み | real | 採用 | brief の訂正表へ (原文は不変) |
| B 規律 2 射程 | (c) 一部射程内 | 採用 | wrapper の透過条件 (同じ引数を 1 回・返り値 identity・例外透過・記録失敗の走は不採用)、hold 不変、診断走を受入証跡に昇格させない、を author prompt と README に書く |
| plan §P1 | replica は案 (i) (本物の `tools.acceptance_shards` plugin + `create_session`) | — | 採用 | 走後に自分の session dir だけ job dir へ退避 (失敗時も)。corpus 集計からその集合を除く |
| plan §P2 C′ | 3 param 縮約の直接走は行わず model | — | 採用 | |
| plan §P4 平均負荷 | S / S1 は実 worker 数で表示 | — | 採用 | |
| brief P1〜P6 | | | | P1 限定採用 (replica 内)、P2 採用 (job 1 は交互)、P3 採用 (model 同士)、P4 名称修正 (3 層)、P5 flock 観測を追加、P6 hook 位置と cardinality sort を修正 |

## brief の訂正表 (原文は不変)

| brief の記述 | 訂正 |
|---|---|
| 「91/92 で `[ccbench-current]`、例外は `_g7`」 | 93 session では 92/93、例外 1 走は `test_historical_oracle_nonadapter_reaches_current_semantics` (brief の集計は M 内だけを見ていた) |
| 「他 3 param は 2 回」 | known-artifact 2 / holdout-artifact 2 / unknownness-layer2 1 (`T:1898-1921` の分岐) |
| env 名 `PLUGIN_SPEC_ENV` | 現物の定数は `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` (`AS:51`)、コードは定数を参照 |
| 「f28 / g7 は別 key」 | key は 5 種: 既定 7 node (single_defects 4 + remaining + f28 modify-revert + f28 post-r-delete)、distinct_basis_blob (draft_finalize)、r_trailer=codex (f28 bad-trailer)、extra_r_path (f28 extra-r-path)、issue_receipt=False (g7) |
| 「S1 = `-n 1` は process memo 経路かもしれない」 | `-n 1` でも `PYTEST_XDIST_TESTRUNUID` は設定され shared base 経路 (`remote.py:416-425`) |
| 「A − S = 競合の膨らみ」 | 「実行 regime 差」。因果効果ではない |
| 「C = 分割 / 縮約の上限」 | 「最長候補 node を除いた診断条件」。上限の意味は固定 duration 仮定下だけ |
| 「固定費 66 秒 = collection + 起動 + 集約」 | 残差。既存 session では開始→最初の test ≈ 59〜60 秒、最後の test→終了 3〜8 秒、実行区間内の空白も含む |

## plan v2 (author への確定仕様の要点)

1. **file 3 本** (job dir `probe/`、Codex author が worktree の `probe-t2710/` に書き親が退避): `t2710_probe_plugin.py` (pytest plugin)、`t2710_probe_runner.py` (計算ノードの条件列実行 + `--selftest`)、`t2710_probe_analyze.py` (集計・対比較・歴史照合・model)。
2. **plugin**: (a) worker `pytest_runtest_setup(tryfirst)` で M の item のときだけ wrapper 設置、teardown 後に復元。wrap 対象 = `item.module._build_t080_stub_free_e2e_repo` / `_T080SharedBases.get` / `_T080SharedBases.close` / `_t080_stub_free_e2e_repo` / helper 直下の `shutil.copytree` (T:1000 の呼出しだけ、再帰は除外) / `item.module.fcntl.flock` (get の context 内・`LOCK_EX` だけ) / `item.module.migration.verify_receipt`。すべて実物へ委譲 (同じ引数を 1 回、返り値 identity、例外透過)。(b) worker `pytest_collection_finish(tryfirst=True)` で条件別処理: S1/S = 何もしない (nodeid 直指定)、A = 何もしない、B = unit 化 → Q_A (cardinality 安定 sort 込み) → 先頭 48 固定 + 最小 cost 48 unit を 49〜96 位 → flatten → 再 sort で Q_B 保存を検算 (不成立なら fail-closed で走を止め「実現不能」を記録)、C = `[ccbench-current]` 1 node を deselect (`pytest_deselected` 通知、production の `selected` は不変)。(c) controller: `pytest_sessionstart` / `pytest_xdist_node_collection_finished(node, ids)` (受信順の記録) / `pytest_runtest_logreport` (nodeid, worker_id, when, start, stop, duration, outcome) / `pytest_sessionfinish` を記録。(d) JSONL は worker・pid ごと、M の span は node 終了時にまとめて書く。schema は plan §P5。
3. **runner** (計算ノード): 条件列を引数で受け、走ごとに新しい pytest subprocess。TMPDIR は設定しない、`--basetemp` は渡さない。A/B/C は `create_session(repo, 3)` + env `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` + `-p tools.acceptance_shards`、argv は `python3.10 -m pytest orchestrator/tests -n 48 --dist loadgroup --junitxml=<spec.junit_path> -p tools.acceptance_shards -p no:cacheprovider -p t2710_probe_plugin` (順序は受入 child に合わせ、probe だけ追加。`-B` は付けない。`PYTHONPATH` に probe dir を足す)。S1/S は `orchestrator/tests/test_s8b_oracle_driver.py::<nodeid>` を直指定、`-n 1` / `-n 11`。走前後の環境記録 (gettempdir・fstype・pytest-of dir・df・shared base path・残骸)、外側 wall、rc、自分の session dir の job dir への退避 (失敗時も)。overhead microbench。全 worker 終了を待ってから次走。
4. **analyze**: shard 表 (W/O/F/L/P/D/平均負荷/最忙 worker の内訳/terminal)、node 表 (M 11 node × 成分)、条件別 3 走 + 中央値、job 内 B−A / C−A と条件別中央値差、歴史照合 (I / percentile / 中央値比)、model 表 (A・分割・縮約・pairing を同じ式で)、B の配布確認表 (最長 node の worker の unit 列)、固定費 3 層表。
5. **selftest** (login、親が実走): plan §selftest の 4 群 + B の cardinality 再 sort 検算 + JSONL schema。held module は import しない。
6. **job 割り** (逐次、D357): job 1 = S1,S,S1,S,S1,S (walltime 90 分)、job 2 = A,B,C、job 3 = B,C,A、job 4 = C,A,B (各 60 分)。queue-wait-timeout 3600、overall-grace 1200。

## 事前登録: 判定と報告の規則 (結果を見る前に固定)

- **反復**: 各条件 3 走。中央値は指標ごとに取り、中央値同士を足さない。各走で先に分解・model を計算する。
- **歴史照合 (記述的診断)**: 指標 j ∈ {W, O, F, L}、A の各走 a_rj、93 session の h_ij。I = ∧_r ∧_j [min_i h_ij ≤ a_rj ≤ max_i h_ij]。percentile = (#{h<a} + 0.5 #{h=a}) / 93、中央値比 = med(a_j)/med(h_j)。I が真でも同等性の合格ではない。
- **pairing (B)**: 各 job で短縮量 = W_A − W_B (同 job)、3 値、差の中央値、各 A を分母にした短縮率、条件別中央値差 (med W_A − med W_B) を示す。3/3 で正なら「方向が一致した観測差」、JSONL で最長 node の worker の初期 2 個目 unit の cost が下がった事実 (発火) を別に確認。符号不一致または律速の移動 (最忙 worker が変わり wall が下がらない) があれば「採用効果は未確立」。約 20 秒・5.8% 級なら「replica で小さい短縮を観測、実受入での効果は未確認」。3/3 一致を有意差判定にしない。T-2766 を閉じる場合は効果ゼロではなく見送りとして諮る。
- **分割・縮約 (model)**: W_X_model = max(L_X, D_X/48) + F_A を A / 分割 / 縮約の 3 つに同じ式で当て、差は model 同士。残差 W_A − W_A_model を併記。分割の d_positive / d_defect は各走の実測成分から (get・copy・setup・teardown は両 node に計上、build 実作業は 1 回でも待ちは両方に現れうる)。
- **最長 node 除外 (C)**: W_A − W_C は診断値。上限とは書かない。
- **D357 の 10% 規則**: 1 走同士の差にだけ適用。3 走の中央値差には適用しない。
- **観測 overhead**: H = 通過回数 × 判定単価 + 採録数 × 記録単価 + 書込み所要 (律速 worker と controller を分ける)。結論が H の幅で反転するときだけ on/off 対比較を追加。
- **失敗走**: rc≠0・未完走・記録失敗の走は表に「除外 (理由)」として残し、置換の再走は同条件 1 回まで、置換したことを明記。

## 変異 matrix

実装面 commit なし (probe は job dir、repo へは `probe-source.md` の逐語だけ) → DW-S04 により免除。受入全走は免除しない (段 9 の land 前 1 回)。

## 段 5 / 6 の構成

author 1 本 (workspace-write、3 file を `probe-t2710/` に書く。docs・commit はしない)。親: 退避 → `--selftest` (login) → compute job 1〜4 (逐次) → analyze (login) → README。段 6: review 1 本 (数値の独立再計算: report duration と JUnit の定義、中央値の順、span の二重計上、C の allocation/実行集合差、B の実配布、最忙 worker と最長 node の一致)。fix は所見が実在した場合だけ。
