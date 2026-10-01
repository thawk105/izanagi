# 段 1 brief — t2853-r2-fig2c (md_4 wave、2026-10-01 JST)

- 研究前進: 論文 (EA&B) の再現パッケージの R2 のうち fig2c (B-10 拡張格子の記述図) を、元の driver で計算ノードに測り直し、原 attempt と並べた表と同じ生成器の図を残す。完了判定 = 3 job 完走 (または失敗の記述的開示)・正しさ (verify) の集計・対照表・図 (または描画拒否の記録)。
- 承認済み裁定: D2305 項 9 (fig2c 2.98 node 時間、1 図 1 タスク、生成器対照の本走 izs4loop を追い越さない)。依頼 md_4 (前例 fig8b と同じ形)。
- 原 attempt (fig2c の provenance から): group `b10-backoff-grid-20260826T234647Z-783837`、job 951689/951690/951691、source commit `78c7a2c1408da05c9c6391451192d81963b84034`、CCBench `511c9538`、job script sha256 `9579690d…` (= `78c7a2c14:tools/pegasus/b10_backoff_grid.sh` を実測)、原データ `/work/1/SFC/tanab/b10-backoff-grid-runs5/` (現存)。
- 経路: `78c7a2c14` の detached checkout から `bash tools/pegasus/submit_b10_backoff_grid.sh --output-parent <新しい出力親>` (この版の driver は `--output-parent` だけ取る、run-kind 引数なし)。driver・job body・生成器は変えない。
- 投入前の実測 (login): 依存元 `/work/SFC/tanab/github/{gflags,glog}` は `78c7a2c14` の policy pin (`e171aa2d…`・`8f9ccfe7…`) と HEAD 一致・clean。生成器 `plot_b10_extended_backoff.py` の sha256 は原 provenance と同じ `04db851a…`。依存 `plot_backoff.py` は原図の `bdb3c223…` から `aa168498…` に変わっている (生成器は描画時の bytes を記録するだけ) → 原データを wrapper で描いて原 provenance の `artist_series` と一致するかの陽性対照で確かめる。
- 生成器は group・nonce・job 番号・入力 sha256 (`CANONICAL_SHA256`) を定数で固定 → 前例 fig8b と同じく repo 外の使い捨て wrapper (Codex author) で定数だけ差し替える。受理条件 (sha256 照合以外の検査・F718 の 1000 µs 除外・verify・レイアウト検査) は緩めない。
- 地位 (§0、投入前に commit): 再現パッケージの試行。原 attempt の置換でも合成でもない。結果にかかわらず報告。正しさ anomaly は即 reject。
- 不変条件: 規律 1 (計測は trace 無効 build、検証は job 内 trace 有効 build の別走)、規律 2 (検査を外さない)、原 attempt の成果物・既存図・driver・生成器の bytes 不変、external/ccbench gitlink 不動。
- 計算: 3 job × 約 3,580 s = 約 2.98 node 時間 (承認済み)。共通指示の「1 job 5 分」は、依頼が元 driver (1 workload = 1 job、31 variant を同一 campaign で測る設計) を指定し driver 変更が scope 外なので適用しない (md_N 優先)。開発検査として受入全走 1 回 (見積り約 0.25 node 時間、別勘定)。
- 投入直前に qstat で izs4loop 系の QUE を見て、あれば投入後に qalter -p で自分の job の優先度を下げる。
- 段構成: 軽量版。設計択一なし (前例と同形) のため段 2・3 を省く。実装面は repo 外 wrapper のみ (Codex author、段 5)。repo の実装面差分 0 → 変異 matrix 免除。段 6 は wrapper が受理検査に触れるため read-only 敵対レビュー 2 本 (A: 一次資料照合・正しさ境界、B: 過剰・誤読)。
- 成果物: `output/insights/2026-10-01/t2853-r2-fig2c/README.md` (+ figures/・verbatim/)、spool fragment。出力親 (repo 外、永続): `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/`。submit-tree は一時置き場 `/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/submit-tree` (wave の終わりに撤去)。
- (P1) 親の provisional 裁定・攻撃対象: 現行 main の CCBench pin `6810666` でなく原 source commit から投げる (生成器が `ccbench_commit 511c953` 等を固定検査し、前例の A′ と同じ理由)。
