# [T-2853] R2 fig2c — B-10 拡張格子を元の driver で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-10-01 JST。wave `t2853-r2-fig2c` (背景 job、依頼 md_4)、着手時の基準 = local main `5f9e8c549`。
- 承認: D2305 項 9 (ユーザー裁定) — fig2c (2.98 node 時間) を 1 図 1 タスクとして投げる。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.1〜§3.3 (fig2c = B-10 拡張格子 3 job × 31 variant、元 job 951689〜951691、2.98 node 時間 = (a) Elapse)、
  前例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md` (同じ driver 系で fig8b を測り直した形)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 原 attempt (fig2c の元の測定) は事前登録を持たない記述的な測定
(provenance の `claim_boundary.claim_scope = descriptive_backoff_shape_only`、`prereg_frozen_comparison_rule: false`) であり、
追加の測定の地位と報告方法を結果より前に書いておくのは、前例 fig8b §0 と同じく、結果を見てから扱いを選ぶ余地を消すためである。

1. **地位。** R2 attempt は、fig2c の測定 (B-10 拡張格子: Silo・48 thread・100 万 record・Zipf 0.9・read 比 5 / 50 / 95%・workload あたり 31 variant
   (参照 2 = backoff なし・既定 adaptive、静的 29 点 = 0〜1000 µs)・5 反復、各 variant の正しさ検査つき) を固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt
   (group `b10-backoff-grid-20260826T234647Z-783837`、job 951689 / 951690 / 951691) の置換ではない。
2. **形。** 原 attempt と同じく 1 group × 3 job (write-heavy / balanced / read-heavy) を、元の driver `tools/pegasus/submit_b10_backoff_grid.sh` で同時に投げる。
   原 attempt が記録した source commit `78c7a2c1408da05c9c6391451192d81963b84034` (3 job の reservation.json の `repository_commit`、fig2c provenance の receipt chain) の
   detached checkout から投げる。CCBench は同 commit の gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec`。この版の driver は `--output-parent` だけを取る。
3. **合成しない。** R2 と原 attempt の標本・CI・判定を互いに合成しない。プール推定・統合判定を作らない。数値の近さを再現精度として評価しない。
4. **原 attempt は不変。** 原 attempt の job dir・fig2c の図 (`docs/paper-story/figures/fig2c_b10_extended_backoff.*`)・provenance は書き換えない。
   R2 の値は本 insight で原 attempt の値と並べて記録するだけである。
5. **結果にかかわらず報告する。** 完走・未完走・正しさ検査の失敗のいずれでも、そのまま本 insight に書く。失敗した job は取り下げず、
   得られた観測値と失敗理由を記述的に開示する。起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、
   新しい nonce・新しい request で同じ group 形のまま投げ直し、落ちた request ID と理由を記録する。
6. **正しさ。** anomaly が出た variant は即 reject とし (規律 2)、正しさ検査は原 attempt と同じく job 内の trace 有効 build で行う (規律 1、計測は trace 無効 build の別走)。
   検査を緩めて描く・記録することはしない。
7. **図が描けない場合。** 原 attempt と同じ生成器 (`tools/plotting/plot_b10_extended_backoff.py`、bytes 不変) が R2 の入力を検査で拒否した場合、
   検査を外して描かない。group id・job 番号・入力 sha256 などの原 attempt 固有の定数だけを repo 外の wrapper で差し替え、受理条件とレイアウト検査は差し替えない。
   生成器のレイアウト検査が R2 の値で拒否したら、図は作らずその事実と拒否理由を書き、表だけを残す (生成器の変更はこの wave の範囲外)。
8. **主張の範囲を増やさない。** 原 attempt と同じく記述的な形の図であり、性能は未認証、機序も採否も主張しない。
