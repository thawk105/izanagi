# 段 1 brief — [T-2826] 受入 `pre` の worker 側 modify 複合区間 (約 45 秒) の関数別計時

wave `dev-wave-t2826-shard-plugin-modify-timing`、起点 local main `d99c556df` (fresh worktree、HEAD == main、clean、開始 gate rc 0 = 2026-09-21 14:08:04 JST。これを標本の as-of とする)。依頼の逐語は `T-2826-origin.md`、一次資料は `output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md` §5 (b) (および §結論 3・§3.1・§4)。

## 研究前進 (1 行)
土台: 受入全走の最遅 shard を 5 分以内へ (D2148 項 6)。研究を止めている実測は無い (依頼者の注記どおり) が、ユーザーが明示起動した。完了判定 = S2 / S3 形で modify 複合区間の関数別内訳が事前登録の残差基準で閉じ、反実仮想セルで worker 側の短縮量と `pre` の変化を別々に測った値が出ること。成果物影響 (DW-G05): 無ければ D2200 項 4 (受入門番の再提示条件) と項 7 (T-2382 の再提示条件) が「T-2617 の単一 process 値 (plugin +1.74 user CPU 秒、主因でない)」と「T-2817 の 48 並列複合区間 (+45 秒)」の食い違いを残したまま評価される。

## scope
- 計算ノード 1 job (同 node・同 checkout・同 tip) で T-2817 の S1 / S2 / S3 形に**関数別の観測 wrapper** (実物へ委譲、DW-O14) を載せ、modify 複合区間 (最後の `pytest_itemcollected` → `pytest_collection_finish` 入口) を関数別に wall と process user / sys で分解する。対象: shard plugin の `pytest_collection_modifyitems` 全体・`records_from_items` (内訳 `_canonical_item` / その中の `Path(item.path).resolve()`)・`allocate`・選択 (by_identity の `_canonical_item` 2 回目 + 分配 + `pytest_deselected`)・state 構築 (`_records_payload` / `_digest`)、conftest の modify wrapper の前段 (hold 処理) と後段 (`_validate_real_repo_shard_state`、`_strip_real_repo_loadgroup_suffix`、S3 の `_reorder_acceptance_items_by_duration`)。
- 反実仮想 1 条件 (probe 内だけ、repo の code は変えない): shard plugin の中の `Path(...).resolve()` を process 内で path 文字列ごとに memo 化する (結果は同値。`records_digest` / `selected_digest` と選択集合の byte 一致を同 job の無改変セルと照合して検査)。これで worker 側の短縮量と `pre` の変化を別々に測る。
- 診断のみ・repo の実装 0 行 (D1936 項 35)。probe は Codex author が書き job dir に置く。repo には逐語 `.txt` だけ。削減策の設計・効果見込みの表は書かない (測った量だけ)。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 確定済みユーザー裁定
D1936 項 35 (効果を先に測り未確認のまま実装しない)、D2148 項 6、D2185 (早期 memo prewarm 現行維持)、D532 (worker 数・配布順の変更は提案しない)、D1729 / D2047 / D2200 項 7 (受入 report schema に観測 field を足さず schema 外の診断走)、D2200 項 4・5。T-2617 §4 の判定 (`Path.resolve()` の字句化は不可、2 回目の置換は採らない) を覆す提案はしない — 測った値だけ記録する。

## brief 前の前提実測 (新事実)
- N1. T-2817 の計測 tip `2afb39768` → `d99c556df` で `tools/acceptance_shards.py`・`orchestrator/tests/conftest.py`・`tools/run_tests.py` の差分 0 行。所要台帳だけ +434 行 (`b820bbaa7`)。`allocate` の重みが変わるので shard-0 の選択集合は T-2817 と同一でない (resolve の回数は全 item 数 × 2 で選択に依らない)。
- N2. python3.10 の `Path.resolve()` は `os.path.realpath` (component ごとの `lstat`) + `stat` 1 回。受入 worktree の test path は 11 component → 1 回約 12 metadata syscall、worker あたり全 item (T-2817 で 26,407) × 2 回。test file は 369 本 (memo 化すると resolve は約 370 回/worker)。
- N3. 早期 memo は controller の thread (最初の `pytest_configure_node` 起点)。worker は conftest の `pytest_collection_finish` 内 `_wait_early_memo_job` で `.pending` の消滅を待つ。T-2817 は memo の**終了 epoch** を直接測っていない (`receipt_memo_s` のみ)。
- N4. T-2817: S2 worker modify median 45.66 / 45.55、S3 44.68 / 44.79、sys 80 → 2108 秒、`intent_lock` 5.2 M → 60.9 M。T-2617 (login 単独 process): plugin あり − なし = user +1.74 / sys +1.72 秒。
- N5. T-2825 (受入所要台帳の隣接対) は比較測定 7 走を 13:55 までに終え、最終受入 → land の段。land 後は所要台帳が変わる → 計測 tip は `d99c556df` に固定する。

## (P) 親の provisional 裁定・攻撃対象
- (P1) 計時の置き方: probe plugin が module 属性の差し替え (実物へ委譲する wrapper) で上記関数を包み、区間ごとに wall (`perf_counter`) と process user / sys (`os.times`) を worker ごとに `workeroutput` へ返す。`Path.resolve` は `_canonical_item` の実行中だけ回数と wall を計る。hook impl 全体の境界は pluggy の hookimpl 関数の差し替え (委譲) で取る。**閉包基準**: worker ごとに modify = Σ 区間 + 残差、残差の median ≤ max(2 秒, modify median の 5 %)。
- (P2) セル: `warm`、`S1`、`S2-f` (S2 + 関数計時)、`S3-u` (T-2817 と同じ計器だけ = 観測者効果の対照)、`S3-f`、`S3-cf` (S3 + 関数計時 + resolve memo)。各 2 走、順序反転 (a: warm S1 S2-f S3-u S3-f S3-cf / b: 逆順)。
- (P3) `pre` の構造の事前登録 (結果を見る前): W_w = max_w(cf_entry) − junit timestamp、M = 早期 memo 終了 epoch − junit timestamp (controller で memo thread の終了を in-memory 監視)。`pre_junit` ≈ max(W_w, M) + ε、ε ≤ 2 秒。S3-cf の読み: ΔW = W_w(S3-u) − W_w(S3-cf) と Δpre = pre(S3-u) − pre(S3-cf) を別々に書き、予測 pre(S3-cf) ≈ max(W_w(S3-cf), M(S3-cf)) + ε の成否を判定する。
- (P4) 観測者効果: S3-f と S3-u の worker modify median の差 ≤ 2 秒なら計器の影響は無視できると読み、超えたら絶対値を掲げず比と差だけ書く。
- (P5) 単独性・外乱: 各セル前後に others=0 / stale_pytest=0 / loadavg / Lustre client stats。MDS は共有なので、セル時間帯に他 wave の受入 (collection 段) が走ったかを受入共有 root の session 作成時刻で事後照合し、重なったセルに印を付ける (再計測は 1 回まで)。投入直前に T-2825 の比較測定が再開していないことを確認する。

## 不変条件
規律 2 (受理集合・hold・verifier に触れない)、規律 7 (T-2617 / T-2817 の値を無効化しない)、D1936 項 35 (実装しない)、tracked file の一時変異 0 件、probe は job dir (repo は逐語 `.txt`)、計測 tip = `d99c556df` (job 完了まで wave 木へ main を取り込まない)。

## 成果物
`output/insights/2026-09-21/t2826-shard-plugin-modify-timing/README.md` (結論・計測・関数別表・閉包・構造の判定・限界・再現)、機械集計 `.md` / `.json`、`raw/`、`verbatim/`。worklog fragment (failures は事故が出た場合だけ)。T-2826 の次の一手の更新。

## 分割方針 (軽量版 + 計算ノード診断 wave の型)
段 1 → 段 3 相談 1 本 (read-only、2 レンズを 1 本: (a) 計時・帰属・反実仮想の設計、(b) 依頼との整合と既存被覆) → 段 4 → 段 5 Codex author 1 本 (plugin + runner + 集計、job dir) → 親の login 生死確認 (`-n 2`) → 計算ノード job 1 本 → 親の README → 受入 1 走 → 段 6 read-only review 1 本 + 焦点再レビュー (上限 3 巡) → 7 → 8 → 9。段 2 は省く (設計択一は (P) に集約し段 3 に攻撃させる)。
