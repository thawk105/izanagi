# 段 1 brief — [T-2273] (= [T-2560] の次の一手) 受入 shard-0 候補 (a) の実装 (2026-09-27)

- 研究前進 (土台): 受入全走の最遅 shard-0 の W_0 は 345〜368 秒 (D2242 の実受入 A) で 5 分上限を越え、全 wave の land 待ちを律している。最小差分 = D2253 の P の形を実装面へ移すことだけ。完了判定 = 下の事前登録どおりの実受入隣接 3 対。
- 確定裁定: D2253 (形 = 早期 memo prewarm と同じ controller の `pytest_configure_node` で背景 thread、実関数 `_copy_git_visible_output` を session で 1 回実 repo に呼んで session 所有の写し、builder は完成を待って写しから局所複製)、D2242 (「最初の builder が作る」形は不採用、流用しない)、D357 (隣接対・中央値・10 %)、D2068 の却下 3 案 (whitelist / alternates / 独立 index) に触れない。(b) 発行 subprocess は同じ wave で実装しない。[T-2604] (同 test file の fixture 絞り) は触らない。
- 前提の実測: 診断 tip `265cce13c` → 現 main `ad114fba0` で `test_s8b_oracle_driver.py`・`conftest.py`・`tools/run_tests.py`・`tools/acceptance_shards.py` は差分なし。対象 2 file は全 worktree で稼働中の未 commit 編集なし・未取り込み branch の 9-24 以降 commit なし。変更前 sha256 の pin hit 0 件 (path 参照は test_campaign_import_invariant / test_real_repo_serialization / test_s8b_binding_driftguards / hold 台帳 / acceptance_duration_ledger 等)。
- 変更面 (実アンカー): `orchestrator/tests/conftest.py` の `pytest_configure_node` (早期 memo の `_start_early_memo_job` 呼出し直後) と controller 終了処理 (`_finish_early_memo_job` 相当の join 位置)。`orchestrator/tests/test_s8b_oracle_driver.py` の `_build_t080_stub_free_e2e_repo` 内 `_copy_git_visible_output(ROOT, root / "output")` (現 1458 行)。
- 不変条件: `_copy_git_visible_output`・`_git_visible_output_paths` の本体、全件性の検査 2 か所 (`test_t080_output_copy_visibility_matches_production_enumeration`)、複製される集合・object store・index、`_T080SharedBases.get()` の key lock / `complete.json`、早期 memo の挙動、既存 test の期待値は不変。規律 2 を緩めない。仮想リスク向け gate・検査・台帳・一般化は足さない。
- 成果物: 実装 (Codex author)・最小の正例 test・変異・実受入隣接 3 対の insight・worklog / decisions fragment。

## 攻撃対象 (親の provisional 裁定)

- (P1) 写しの置き場と受け渡し: controller が `tempfile.gettempdir()` 下に `sha256([ROOT, testrunuid])` 由来の dir を作り、worker は workerinput 経由 (早期 memo と同型) で path を受け取る。env からの再計算 (probe の形) より明示的。
- (P2) controller での `_copy_git_visible_output` の取得: 背景 thread 内で test module を import して実関数を呼ぶ (probe の fix1 で main thread import は欠陥とされた)。関数の移設はしない。
- (P3) 発火条件: 早期 memo と同じ `_early_memo_selected(config)` のときだけ。shard 割付は worker の collection 時に決まるので、controller は 3 shard とも写しを作る (shard-1 / 2 の写しは使われず、背景 I/O が増える)。shard-1 / 2 の影響は W_max・W_1・W_2 で観測するだけにする。
- (P4) 写しが無い (単独走・-k 等で未発火) ときは従来どおり実 repo から直接複製。写しの生成失敗・待ち超過は builder を赤にする (直接複製へ黙って落とさない。測定の条件が混ざるため)。
- (P5) 待ち上限: 診断で写し生成 80.8〜103.3 秒、builder 開始は写し開始から 65.7〜70.7 秒、待ち 5.6〜27.1 秒。上限は probe と同じ 180 秒 (観測 max 27.1 秒の約 6.6 倍、regime = 受入 shard-0 の計算ノード)。
- (P6) 後始末: controller が終了時に thread を join して写しを消す (worker 全終了後)。
- (P7) 意味の差: 写しは configure_node 時点の output/ の 1 時点 (現行は builder 開始時点)。D2242 段 4 A1 と同じく受理集合は変えない — docstring で明記するだけ。
- (P8) test は最小: controller 側で実関数が session 1 回だけ呼ばれ写しができること、builder が写しから複製し (実 repo を直接読まない) 同じ集合・bytes・mtime を得ること。

## 受入・実測環境

受入 = `tools/dev_wave_wait.py acceptance` (Pegasus 計算ノード 3 shard)。隣接対 = 前回 (`dev-wave-t2273-shard0-local-copy/probe/`) の門番付き逐次投入・集計器を本 wave 用に移植 (Codex author、repo 外)。計算量 = 受入 1 回 ≈ 0.24 node 時間 (前回 29 shard job の Elapse 平均 287 秒) × 6 走 + 取り直し + 検査で 2 node 時間を超える見込み → 段 4 で見積りを出してユーザー確認。

## 分割方針

段 5: 単位 L (conftest.py + test_s8b_oracle_driver.py、Codex author) と単位 P (計測 probe 移植、repo 外) を素集合で並列。
