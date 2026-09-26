単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — 段 4 裁定 (plan v2・事前登録)。レビューの基準。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s5-author-out.md — 実装子の報告。
- レビュー対象 (commit `2ebf25e24`、作業木 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe): `tools/t2273_replica_runner.py`、`tools/t2273_replica_plugin.py`、`tools/t2273_replica_analyze.py`。第 4 回の実走版 `7f38ac7fd` との差分は `git diff 7f38ac7fd 2ebf25e24 -- tools/` で読める (read-only の git は可)。
- 対象コード (計測される側): 同作業木の `orchestrator/tests/test_s8b_oracle_driver.py` (847〜1000、1437〜1730)、`orchestrator/tests/conftest.py` (2368〜2470、2583〜2615)。

## レンズ A — 計測の正しさ (P の対照が (a) を写しているか、有効性判定が恒真・恒偽でないか)

これは repo に入れない対照診断 probe で、計算ノードで A (観測のみ) と P (collection 中に controller が局所の写しを作り、builder はそこから複製) を隣接に走らせる。次を攻撃せよ。

1. P の機構: controller 側 `pytest_configure_node` の中で `importlib.import_module('orchestrator.tests.test_s8b_oracle_driver')` を **main thread で**呼ぶ点 (worker 起動の遅れが P の pre に乗り、A にない費用を P に足すか。thread 内へ移すべきか)。identity の一致 (controller の `node.workerinput['testrunuid']` と worker の `PYTEST_XDIST_TESTRUNUID`)、ready / failed の書き順、待ち上限 180 秒、`pytest_unconfigure` での join と削除、hook 順 (`tryfirst`) と conftest の早期 memo job との関係。
2. `copy.digest` (`output_digest`) が directory も含む点: A (実関数の copytree、ignore あり) と P (写しからの copytree) で directory の size・mode・mtime_ns が一致する保証はあるか。一致しないなら有効性が恒偽になる。file だけに絞るべきか。逆に file の mtime・mode が P で変わっても通ってしまう経路 (恒真) はないか。digest を採る span が builder の所要・W_0 へ両条件対称に乗るか。
3. 発行 child の計測用 code 変換 (`instrument_publish_child`): `ast.unparse` による再生成で元の child の意味 (文字列・エスケープ・`sys.argv` の添字・`_CurrentSourceLoader` の検査・stdout の JSON) が変わらないか。phase の境界が意図した文に置かれるか (目印が複数文に当たる・順序の検査)。変換失敗時に未変換で走り、それが A/P の片方だけで起きたら対称性が崩れるか。
4. runner の `ab` mode: 順序・smoke・guard (clean・HEAD・others・stale・一時 dir 掃除) が 2 走の間で対称か。片方 rc≠0 のときの記録。
5. analyzer: s4-ruling §3 の有効性の全項目と判定量を正しく計算しているか。とくに Δ_i の符号、r_i の分母、中央値、「3 対すべて Δ>0 ∧ 中央値 ≥ 10 %」の判定、早期 memo 超過の走を対から外す処理、順序別対差、写しの完成時刻と最初の builder 開始の差の起点。第 4 回の既存出力 (`--pair-dir`・`--run-dir`) を変えていないか。
6. 実装子報告と実装の食い違い、「実装済み・未実走」を実走済みのように書いている箇所。

read-only で書込可能 tmp が無いので静的検査でよい。実走は親が計算ノードで行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` — ID (RA1, ...)、重大度 (must-fix / should / nit)、根拠 file:line、放置時に診断の結論 (効果の値・有効性・推奨) がどう変わるかを 1 行、推奨修正。
- `## 総括` (3〜6 行、GO / 修正後 GO / NO-GO)
